from sqlmodel import Field
from api.new_models.basemodel import BaseModel


class Lehrveranstalter(BaseModel, table=True):
    """WsLehrveranstalter"""

    id: int = Field(primary_key=True)
    name: str = Field()
    vorname: str = Field()
    rufname: str = Field()
    dozide: int | None = Field(default=None)  # FK expected
    hauptverantwortlicher: bool | None = Field(default=None)
    typ: int | None = Field(default=None)
    typstringkurz: str | None = Field(default=None)
    typstringkurzen: str | None = Field(default=None)
    typstringlang: str | None = Field(default=None)
    typstringlangen: str | None = Field(default=None)
    lehrgebiet: str | None = Field(default=None)
    lehrveranstaltungsid: int | None = Field(default=None)  # FK expected
    geschlecht: str | None = Field(default=None)
    email: str | None = Field(default=None)
    titel: str | None = Field(default=None)
