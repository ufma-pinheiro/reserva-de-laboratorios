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


class Room(BaseModel):
    name = TextField(null=False)
    location = TextField(null=False)
    people_capacity = IntegerField(null=False)
    description = TextField()


class Reservation(BaseModel):
    responsible_user_email = TextField(unique=True, null=False)
    date = DateField(null=False)
    start_time = TextField(null=False)
    end_time = TextField(null=False)
    approved = BooleanField(default=False)
    id_room = ForeignKeyField(Room, backref="Reservations", null=False)


def add_room(**kwargs) -> Room:
    room = Room(kwargs.get("name"), kwargs.get("location"),
                kwargs.get("people_capacity"), kwargs.get("description", ""))
    room.save()
    return room


def get_room_by_id(index: int) -> Room:
    room = Room.get(Room.id == index)
    return room


def del_room_by_id(index: int) -> None | bool:
    try:
        Room.delete().where(Room.id == index)
    except DoesNotExist:
        return False


def update_room(index: int, **kwargs) -> Room:
    room = Room.get(Room.id == index)
    room.name = kwargs.get("name", room.name)
    room.location = kwargs.get("location", room.location)
    room.people_capacity = kwargs.get("people_capacity", room.people_capacity)
    room.description = kwargs.get("description", room.description)
    room.save()
    return room


def add_reservation(**kwargs) -> Reservation:
    reservation = Reservation(**kwargs)
    reservation.save()
    return reservation
