from sqlmodel import JSON, Column, Field
from api.new_models.base import BaseModel
from api.new_models.belegungsserie_ort import BelegungsserieOrt
from api.new_models.lehrveranstalter import Lehrveranstalter


class Lehrveranstaltung(BaseModel, table=True):
    """WsLehrveranstaltung"""

    id: int = Field(primary_key=True)
    nummer: str | None = Field(default=None)
    titel: str | None = Field(default=None)
    semkez: str | None = Field(default=None, max_length=5)
    typ: str | None = Field(default=None, max_length=1)
    semesterbezug: int | None = Field(default=None)
    semesterbezugstringkurz: str | None = Field(default=None)
    semesterbezugstringkurzen: str | None = Field(default=None)
    semesterbezugstringlang: str | None = Field(default=None)
    semesterbezugstringlangen: str | None = Field(default=None)
    lehrumfang: float | None = Field(default=None)
    lehrumfangtyp: int | None = Field(default=None)
    lehrumfangtypstringkurz: str | None = Field(default=None)
    lehrumfangtypstringkurzen: str | None = Field(default=None)
    lehrumfangtypstringlang: str | None = Field(default=None)
    lehrumfangtypstringlangen: str | None = Field(default=None)
    findetstatt: int | None = Field(default=None)
    findetstattstringkurz: str | None = Field(default=None)
    findetstattstringkurzen: str | None = Field(default=None)
    findetstattstringlang: str | None = Field(default=None)
    findetstattstringlangen: str | None = Field(default=None)
    servicetyp: int | None = Field(default=None)
    servicetypstringkurz: str | None = Field(default=None)
    servicetypstringkurzen: str | None = Field(default=None)
    servicetypstringlang: str | None = Field(default=None)
    servicetypstringlangen: str | None = Field(default=None)
    periodizitaet: int | None = Field(default=None)
    periodizitaetstringkurz: str | None = Field(default=None)
    periodizitaetstringkurzen: str | None = Field(default=None)
    periodizitaetstringlang: str | None = Field(default=None)
    periodizitaetstringlangen: str | None = Field(default=None)
    nachvereinbarung: bool | None = Field(default=None)
    dozentauswaehlen: bool | None = Field(default=None)
    lehrsprache: str | None = Field(default=None, max_length=2)
    spezialbewilligung: bool | None = Field(default=None)
    externehoerer: bool | None = Field(default=None)
    angezeigterkommentar: str | None = Field(default=None, max_length=1000)

    lehrveranstalter: list[Lehrveranstalter] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    belegungsserien: list[BelegungsserieOrt] = Field(
        default_factory=list, sa_column=Column(JSON)
    )

    # NOTE: veranstalter is excluded
    # veranstalter: list[Veranstalter] = Field(
    #     default_factory=list, sa_column=Column(JSON)
    # )
