from sqlalchemy.orm import Session

import models, schema

def get_team_by_name(db: Session, name: str):
    return db.query(models.Team).filter(models.Team.name == name).first()

def create_team(db: Session, team: schema.TeamCreate):
    db_team = models.Team(name=team.name, password=team.password)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team