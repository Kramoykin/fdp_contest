from pydantic import BaseModel

class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    password: str

class Team(TeamBase):
    id: int
    name: str
    password: str
    bit_current_position: float

    class Config:
        orm_mode = True