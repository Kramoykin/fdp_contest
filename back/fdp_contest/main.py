from typing import Annotated

from fastapi import FastAPI, Request, Depends, HTTPException, Form
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
async def read_item(request: Request
                  , team_name: Annotated[str, Form()]
                  , password: Annotated[str, Form()]
                  , md: Annotated[float, Form()]
                  , db: Session = Depends(get_db)):
    db_team = crud.get_team_by_name(db, name=team_name)
    if not db_team:
        raise HTTPException(status_code=400, detail="Нет такой команды")
    
    if password != db_team.password:
        raise HTTPException(status_code=401, detail="Неправильный пароль")
    
    db_team.bit_current_position = md
    db.commit()

    return templates.TemplateResponse(
        request=request, name="create_borehole.html"
    )