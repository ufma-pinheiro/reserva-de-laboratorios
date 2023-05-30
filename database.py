from peewee import *
from time import time as timestamp
from pydantic import BaseSettings


class DatabaseSettings(BaseSettings):
    database: str
    port: int
    password: str
    host: str
    user: str

    class Config:
        # `.env.prod` takes priority over `.env`
        env_file = '.env', '.env.prod'


db_settings = dict(DatabaseSettings())
database = PostgresqlDatabase(**db_settings)
FORMATTING_DATE = "%d-%m-%Y"


class BaseModel(Model):
    time_stamp = IntegerField(default=int(timestamp()), null=True)

    class Meta:
        database = database


