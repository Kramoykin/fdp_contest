from sqlalchemy import Double, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    password = Column(String, unique=True)
    bit_current_position = Column(Double, default=0.0) # текущее положение долота в метрах
    borehole_count = Column(Integer, default = 0)