from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Awesome API"
    admin_email: str
    items_per_user: int = 50
    version: str = "0.1.0"

    class Config:
        # `.env.prod` takes priority over `.env`
        env_file = '.env', '.env.prod'

settings = Settings()