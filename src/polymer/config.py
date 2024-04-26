from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", ".env.local"))

    db_url: str
    email: str
    password: str
    nickname: str
    apikey: str
    download_dir: str
    mmf_client_id: str
    mmf_client_secret: str


settings = Settings()
