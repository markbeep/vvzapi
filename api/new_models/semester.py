from sqlmodel import Field
from api.new_models.abschnitt_element import AbschnittElement
from api.new_models.basemodel import BaseModel


class Semester(BaseModel, table=True):
    """WsSemester"""

    semkez: str = Field(max_length=5, primary_key=True)
    semesterkurz: str = Field(max_length=10)
    semesterlang: str = Field(max_length=25)
    semesterlangen: str = Field(max_length=25)
    semesterbeginn: str | None = Field(default=None)
    semestermitte: str | None = Field(default=None)
    semesterende: str | None = Field(default=None)
    semesterintervallende: str | None = Field(default=None)
    abschnittelemente: list[AbschnittElement] = Field(default_factory=list)
