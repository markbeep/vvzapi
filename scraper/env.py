from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    refresh_html: bool = False
    """If html files already present locally should be refetched"""
