from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_path: str = "data/db.sqlite"
    cache_expiry: int = 3600  # in seconds
