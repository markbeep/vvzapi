from sqlmodel import JSON, Field, Column
from api.new_models.base import BaseModel
from api.new_models.lehrveranstaltungen import Lehrveranstaltung


class Lerneinheit(BaseModel, table=True):
    """WsLerneinheit"""

    id: int = Field(primary_key=True)
    code: str | None = Field(default=None, max_length=12)
    titel: str | None = Field(default=None, max_length=100)
    titelenglisch: str | None = Field(default=None, max_length=100)
    semkez: str = Field(max_length=5)
    kreditpunkte: float | None = Field(default=None)
    url: str | None = Field(default=None, max_length=1000)
    # urlvon: str | None = Field(default=None)
    # urlbis: str | None = Field(default=None)
    # reihenfolge: int | None = Field(default=None)
    # lkeinheitid: int | None = Field(default=None)  # FK expected
    literatur: str | None = Field(default=None, max_length=4000)
    literaturenglisch: str | None = Field(default=None, max_length=4000)
    lernziel: str | None = Field(default=None, max_length=4000)
    lernzielenglisch: str | None = Field(default=None, max_length=4000)
    inhalt: str | None = Field(default=None, max_length=4000)
    inhaltenglisch: str | None = Field(default=None, max_length=4000)
    skript: str | None = Field(default=None, max_length=4000)
    skriptenglisch: str | None = Field(default=None, max_length=4000)
    besonderes: str | None = Field(default=None, max_length=4000)
    besonderesenglisch: str | None = Field(default=None, max_length=4000)
    diplomasupplement: str | None = Field(default=None, max_length=4000)
    diplomasupplementenglisch: str | None = Field(default=None, max_length=4000)
    angezeigterkommentar: str | None = Field(default=None, max_length=1000)
    angezeigterkommentaren: str | None = Field(default=None, max_length=1000)
    sternkollonne: str | None = Field(default=None)
    belegungMaxPlatzzahl: int | None = Field(default=None)
    belegungTermin2Wl: str | None = Field(default=None)
    belegungTermin3Ende: str | None = Field(default=None)
    # NOTE: Not listed in doc, but listed on vvz
    belegungsTerminStart: str | None = Field(default=None)
    vorrang: str | None = Field(default=None)

    # lehrveranstaltungen: list[Lehrveranstaltung] = Field(
    #     default_factory=list, sa_column=Column(JSON)
    # )

    def overwrite_with(self, other: "Lerneinheit"):
        for field in other.model_fields_set:
            value = getattr(other, field)
            if value is not None:
                setattr(self, field, value)
