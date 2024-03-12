from typing import List

from sqlalchemy import Double, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from datetime import datetime


from database import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    password: Mapped[str] = mapped_column(unique=True)
    grid_file_path: Mapped[str] = mapped_column(unique=True, nullable = True)

    boreholes: Mapped[List["Borehole"]] = relationship(back_populates="team")

class Borehole(Base):
    __tablename__ = "boreholes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    file_path: Mapped[str] = mapped_column(unique=True)
    bit_current_position: Mapped[float] = mapped_column(default=0.0) # текущее положение долота в метрах
    creation_date: Mapped[datetime] = mapped_column()

    logging: Mapped["Logging"] = relationship("Logging", uselist=False, back_populates="borehole")

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    team: Mapped["Team"] = relationship(back_populates="boreholes")

class Logging(Base):
    __tablename__ = "loggings"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str] = mapped_column(unique=True)

    borehole_id: Mapped[int] = mapped_column(ForeignKey("boreholes.id"))
    borehole: Mapped["Borehole"] = relationship(back_populates="logging")