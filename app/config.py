from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MyApp"
    environment: str = "development"
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()