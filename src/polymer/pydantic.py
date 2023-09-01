from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    email: str
    password: str
    nickname: str
    apikey: str
