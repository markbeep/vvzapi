from sqlmodel import Field

from api.new_models.base import BaseModel


class Lehrveranstalter(BaseModel, table=True):
    """WsLehrveranstalter"""

    dozide: int = Field(primary_key=True)
    name: str = Field()
    vorname: str = Field()
    golden_owl: bool = Field(default=False)
