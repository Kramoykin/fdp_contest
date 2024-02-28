from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

import models, schema

def get_team_by_name(db: Session, name: str):
    return db.query(models.Team).filter(models.Team.name == name).first()

def create_team(db: Session, team: schema.TeamCreate):
    db_team = models.Team(name=team.name, password=team.password)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

def create_logging(db: Session, logging: schema.Logging):
    db_logging = models.Logging(borehole_id = logging.borehole_id
                              , file_path = logging.file_path)
    db.add(db_logging)
    db.commit()
    db.refresh(db_logging)
    return db_logging

def create_borehole(db: Session, 
                    bh: schema.BoreholeCreate):
    db_borehole = models.Borehole(name = bh.name
                                , bit_current_position = bh.bit_current_position
                                , file_path = bh.file_path
                                , team_id = bh.team_id)
    db.add(db_borehole)
    db.commit()
    db.refresh(db_borehole)
    return db_borehole

def get_team_borehole_by_name(db: Session
                            , team_name: str
                            , borehole_name: str):
    
    return db.query(models.Borehole).filter(models.Borehole.team.name == team_name \
                                        and models.Borehole.name == borehole_name).first()