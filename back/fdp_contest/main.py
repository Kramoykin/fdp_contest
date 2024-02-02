from typing import Annotated

from fastapi import FastAPI, Request, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

import crud, models, schema
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
        request=request, name="create_borehole.html"
    )

