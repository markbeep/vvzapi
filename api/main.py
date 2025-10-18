from typing import Annotated
from fastapi import Depends, FastAPI, Query
from pydantic import BaseModel
from sqlmodel import Session, select
import uvicorn

from api.models.learning_unit import LearningUnit
from api.util.db import get_session

app = FastAPI()


@app.get("/units")
async def get_units(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(gt=0, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return session.exec(select(LearningUnit).offset(offset).limit(limit)).all()


class TitleResponseModel(BaseModel):
    id: int
    title: str


@app.get("/titles", response_model=list[TitleResponseModel])
async def get_titles(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(gt=0, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return session.exec(
        select(LearningUnit.id, LearningUnit.title).offset(offset).limit(limit)
    ).all()


if __name__ == "__main__":
    uvicorn.run(app, port=8000)
