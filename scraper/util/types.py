from pydantic import BaseModel

from api.models.learning_unit import Department, Level


class UnitDepartmentMapping(BaseModel):
    department: Department
    unit_id: int


class UnitLevelMapping(BaseModel):
    level: Level
    unit_id: int
