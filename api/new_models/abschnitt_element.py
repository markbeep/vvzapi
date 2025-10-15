from sqlmodel import Field
from api.new_models.abschnitt_daten import AbschnittDaten
from api.new_models.abschnitts_referenz import AbschnittsRefernz
from api.new_models.basemodel import BaseModel
from api.new_models.lehrneinheit import Lehrneinheit


class AbschnittElement(BaseModel, table=True):
    """WsAbschnittElement — synthetic PK added"""

    id: int = Field(primary_key=True)
    abschnittelementtyp: int = Field()
    abschnittdaten: AbschnittDaten | None = Field(default=None)
    abschnittreferenz: AbschnittsRefernz | None = Field(default=None)
    lerneiheit: Lehrneinheit | None = Field(default=None)
    kinderelemente: list["AbschnittElement"] | None = Field(default=None)
