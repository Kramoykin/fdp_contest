from pydantic import BaseModel

class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    password: str

class Team(TeamBase):
    id: int
    name: str
    password: str

    class Config:
        orm_mode = True

class BoreholeBase(BaseModel):
    name: str

class BoreholeCreate(BoreholeBase):
    file_path: str
    team_id: int
    bit_current_position: float