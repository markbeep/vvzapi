from sqlmodel import Field
from api.new_models.basemodel import BaseModel


class Veranstalter(BaseModel, table=True):
    """WsVeranstalter"""

    id: int = Field(primary_key=True)
    veranstaltername: str | None = Field(default=None)
    typ: int | None = Field(default=None)
    typstringkurz: str | None = Field(default=None)
    typstringlang: str | None = Field(default=None)
    extvarid: int | None = Field(default=None)
    vaid: int | None = Field(default=None)  # FK expected
    leitzahl: str | None = Field(default=None)
    persid: int | None = Field(default=None)  # FK expected
