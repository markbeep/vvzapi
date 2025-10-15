from sqlmodel import Field
from api.new_models.basemodel import BaseModel


class AbschnittDaten(BaseModel, table=True):
    """WsAbschnittDaten"""

    id: int = Field(primary_key=True)
    titel: str | None = Field(default=None, max_length=250)
    titelen: str | None = Field(default=None, max_length=250)
    nummer: str | None = Field(default=None, max_length=8)
    typ: int | None = Field(default=None)
    typstringkurz: str | None = Field(default=None)
    typstringkurzen: str | None = Field(default=None)
    typstringlang: str | None = Field(default=None)
    typstringlangen: str | None = Field(default=None)
    semkez: str | None = Field(default=None, max_length=5)
    uebergeordneteabschnittid: int | None = Field(default=None)  # FK expected
    reihenfolge: int | None = Field(default=None)
    angezeigterkommentar: str | None = Field(default=None)
    angezeigterkommentaren: str | None = Field(default=None)
