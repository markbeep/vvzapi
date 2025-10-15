from sqlmodel import Field
from api.new_models.basemodel import BaseModel


class AbschnittsRefernz(BaseModel, table=True):
    """WsAbschnittsRefernz"""

    id: int = Field(primary_key=True)
    referenzierteabschnittsid: int | None = Field(default=None)  # FK expected
    homeabschnittid: int | None = Field(default=None)  # FK expected
    typ: int | None = Field(default=None)
    typstringkurz: str | None = Field(default=None)
    typstringkurzen: str | None = Field(default=None)
    typstringlang: str | None = Field(default=None)
    typstringlangen: str | None = Field(default=None)
    kommentar: str | None = Field(default=None, max_length=1000)
    kommentaren: str | None = Field(default=None, max_length=1000)
