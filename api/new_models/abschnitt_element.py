from sqlmodel import Field, JSON, Column
from api.new_models.base import BaseModel


class AbschnittElement(BaseModel, table=True):
    """WsAbschnittElement — synthetic PK added"""

    id: int = Field(primary_key=True)
    abschnittelementtyp: int = Field()
    abschnittdaten_id: int | None = Field(default=None)
    # abschnittdaten: AbschnittDaten | None = Relationship(
    #     back_populates="abschnittelemente"
    # )

    abschnittreferenz_id: int | None = Field(default=None)
    # abschnittreferenz: AbschnittsRefernz | None = Relationship(
    #     back_populates="abschnittelemente"
    # )

    lerneinheit_id: int | None = Field(default=None)
    # lerneiheit: Lerneinheit | None = Relationship(back_populates="abschnittelemente")

    # TODO: move to separate table for many-to-many relationship
    kinderelemente_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    # kinderelemente: list["AbschnittElement"] | None = Field(
    #     default=None, sa_column=Column(JSON)
    # )
