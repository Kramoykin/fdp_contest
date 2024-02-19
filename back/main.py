from typing import Annotated
import pandas as pd
import lasio 
import aiofiles

from fastapi import FastAPI, Request, Depends, HTTPException, Form, UploadFile, File, status
from fastapi.responses import HTMLResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import FileTarget, ValueTarget
from streaming_form_data.validators import MaxSizeValidator
import streaming_form_data
from starlette.requests import ClientDisconnect

from sqlalchemy.orm import Session

import crud, models, schema, utils
from database import SessionLocal, engine

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

ADMIN_SECRET = "aaaaaa"
CHUNK_SIZE = 1024
MAX_FILE_SIZE = 1024 * 1024 * 1024 * 4  # = 4GB
MAX_REQUEST_BODY_SIZE = MAX_FILE_SIZE + 1024

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

class MaxBodySizeException(Exception):
    def __init__(self, body_len: str):
        self.body_len = body_len

class MaxBodySizeValidator:
    def __init__(self, max_size: int):
        self.body_len = 0
        self.max_size = max_size

    def __call__(self, chunk: bytes):
        self.body_len += len(chunk)
        if self.body_len > self.max_size:
            raise MaxBodySizeException(body_len=self.body_len)
        
@app.post("/teams/", response_model=schema.Team)
def create_team(secret: str, team: schema.TeamCreate, db: Session = Depends(get_db)):
    if (secret != ADMIN_SECRET):
        raise HTTPException(status_code=403, detail="Недостаточно полномочий")
    
    db_team = crud.get_team_by_name(db, name=team.name)
    if db_team:
        raise HTTPException(status_code=400, detail="Команда уже зарегистрирована")
    
    return crud.create_team(db=db, team=team)        

@app.post('/teams/grid')
async def upload(request: Request,
                 db: Session = Depends(get_db)):
    body_validator = MaxBodySizeValidator(MAX_REQUEST_BODY_SIZE)
    filename = request.headers.get('Filename')
    
    if (request.query_params["secret"] != ADMIN_SECRET):
        raise HTTPException(status_code=403, detail="Недостаточно полномочий")

    db_team = crud.get_team_by_name(db, name=request.query_params["team_name"])
    if not db_team:
        raise HTTPException(status_code=400, detail="Нет такой команды")
    
    if request.query_params["password"] != db_team.password:
        raise HTTPException(status_code=401, detail="Неправильный пароль")
    
    if not filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail='Filename header is missing')
    try:
        filepath = f"data/grids/{db_team.name}.csv"
        file_ = FileTarget(filepath, validator=MaxSizeValidator(MAX_FILE_SIZE))
        data = ValueTarget()
        parser = StreamingFormDataParser(headers=request.headers)
        parser.register('data', data)
        parser.register('file', file_)
        
        async for chunk in request.stream():
            body_validator(chunk)
            parser.data_received(chunk)

        db_team.grid_file_path = filepath
        db.commit()
    except ClientDisconnect:
        print("Client Disconnected")
    except MaxBodySizeException as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, 
           detail=f'Maximum request body size limit ({MAX_REQUEST_BODY_SIZE} bytes) exceeded ({e.body_len} bytes read)')
    except streaming_form_data.validators.ValidationError:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, 
            detail=f'Maximum file size limit ({MAX_FILE_SIZE} bytes) exceeded') 
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail='There was an error uploading the file') 
   
    if not file_.multipart_filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='File is missing')

    print(file_.multipart_filename)
        
    return {"message": f"Successfuly uploaded {filename}"}

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(
        request=request, name="create_borehole.html"
    )

@app.post("/borehole/")
async def upload_borehole(team_name: Annotated[str, Form()]
                        , password: Annotated[str, Form()]
                        , borehole_name: Annotated[str, Form()]
                        , bit_current_position: Annotated[float, Form()]
                        , file: Annotated[UploadFile, File()]
                        , db: Session = Depends(get_db)):
    db_team = crud.get_team_by_name(db, name=team_name)
    if not db_team:
        raise HTTPException(status_code=400, detail="Нет такой команды")
    
    if password != db_team.password:
        raise HTTPException(status_code=401, detail="Неправильный пароль")
    
    if file.size < 100 or file.size > 1000000:
        raise HTTPException(status_code=400, detail=" Неподходящий размер файла")
    
    same_name_boreholes = [b for b in db_team.boreholes if b.name == borehole_name]
    if (same_name_boreholes):
        raise HTTPException(status_code=400, detail="Уже есть скважина с таким именем")
    
    if len(db_team.boreholes) > 9:
        raise HTTPException(status_code=409, detail="Превышен лимит числа скважин для команды")

    file_path = f"data/teams/{file.filename}_{db_team.name}_{len(db_team.boreholes) + 1}"
    with open(file_path, "wb+") as file_object:
        file_object.write(file.file.read())

    bh_create = schema.BoreholeCreate(name = borehole_name
                                    , bit_current_position = bit_current_position
                                    , file_path = file_path
                                    , team_id = db_team.id)
    db_borehole = crud.create_borehole(db, bh_create)
    db_team.boreholes.append(db_borehole)

    return {"borehole": db_borehole.id}


@app.post("/logging", response_class=Response)
async def download_logging(
                    team_name: Annotated[str, Form()]
                  , password: Annotated[str, Form()]
                  , db: Session = Depends(get_db)):
    db_team = crud.get_team_by_name(db, name=team_name)
    if not db_team:
        raise HTTPException(status_code=400, detail="Нет такой команды")
    
    if password != db_team.password:
        raise HTTPException(status_code=401, detail="Неправильный пароль")
    
    file_path = f"data/teams/Скважина_2_{db_team.name}_{db_team.borehole_count}"
    traj_df = utils.get_trajectory_df(file_path)

    grid_df = pd.read_csv('data/grid.csv')

    indices = utils.find_closest_indices_xyz(target_coords=traj_df[['X', 'Y', 'Z']].to_numpy(), 
                                   coords=grid_df[['X_UTME', 'Y_UTMN', 'Z_TVDSS']].to_numpy()
                                   )
                                   
    curve = grid_df.GAMMARAY.to_numpy()[indices]

    las = lasio.LASFile()
    las.insert_curve(0, "DEPT", traj_df['MD'], unit="m", descr="Depth")
    las.insert_curve(1, "GR", curve, unit="API", descr="Gamma Ray")
    logging_file_path = f"data/teams/{db_team.name}_gamma_ray_curve.las"
    with open(logging_file_path, 'w+') as fobj:
        las.write(fobj, version=2.0)

    return FileResponse(logging_file_path, filename=f"{db_team.name}_output.las", media_type="application/octet-stream")