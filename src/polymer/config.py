from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    email: str
    password: str
    nickname: str
    apikey: str
    download_dir: str


settings = Settings(
    email="sweeneytri@gmail.com",
    password="qj*T44viB1exY5ET",
    nickname="calcifer242",
    apikey="z2TNkBjluSamUQtdO7R19hkPo",
    download_dir="./tmp",
)
