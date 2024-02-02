from typing import Annotated
import pandas as pd
import lasio 

from fastapi import FastAPI, Request, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.post("/teams/", response_model=schema.Team)
def create_team(secret: str, team: schema.TeamCreate, db: Session = Depends(get_db)):
    if (secret != ADMIN_SECRET):
        raise HTTPException(status_code=403, detail="Недостаточно полномочий")
    db_team = crud.get_team_by_name(db, name=team.name)
    if db_team:
        raise HTTPException(status_code=400, detail="Команда уже зарегистрирована")
    return crud.create_team(db=db, team=team)

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(
        request=request, name="create_borehole.html"
    )

@app.post("/borehole/", response_class=HTMLResponse)
async def upload_borehole(request: Request
                  , team_name: Annotated[str, Form()]
                  , password: Annotated[str, Form()]
                  , md: Annotated[float, Form()]
                  , file: Annotated[UploadFile, File()]
                  , db: Session = Depends(get_db)):
    db_team = crud.get_team_by_name(db, name=team_name)
    if not db_team:
        raise HTTPException(status_code=400, detail="Нет такой команды")
    
    if password != db_team.password:
        raise HTTPException(status_code=401, detail="Неправильный пароль")
    
    if file.size < 100 or file.size > 1000000:
        raise HTTPException(status_code=400, detail=" Неподходящий размер файла")
    
    if db_team.borehole_count > 9:
        raise HTTPException(status_code=409, detail="Превышен лимит числа скважин для команды")

    file_location = f"data/teams/{file.filename}_{db_team.name}_{db_team.borehole_count+1}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    db_team.bit_current_position = md
    db_team.borehole_count += 1
    db.commit()

    return templates.TemplateResponse(
        request=request, name="download_logging.html"
    )

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

