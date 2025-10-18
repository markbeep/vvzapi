from sqlmodel import Field
from api.models.base import BaseModel


class Section(BaseModel, table=True):
    id: int = Field(primary_key=True)
    parent_id: int | None = Field(default=None)
    semkez: str
    name: str | None = Field(default=None)
    name_english: str | None = Field(default=None)
    level: int | None = Field(default=None)
    comment: str | None = Field(default=None)
    comment_english: str | None = Field(default=None)

    def overwrite_with(self, other: "Section"):
        """
        Overwrites all fields that are not None from the other instance.
        Used to merge german and english scraped data.
        """
        for field in other.model_fields_set:
            value_other = getattr(other, field)
            if value_other is not None:
                setattr(self, field, value_other)
