from sqlmodel import Field

from api.models.base import BaseModel


class Lecturer(BaseModel, table=True):
    id: int = Field(primary_key=True)
    surname: str = Field()
    name: str = Field()
    golden_owl: bool = Field(default=False)
    """Whether the lecturer has received a Golden Owl award."""
