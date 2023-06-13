from peewee import *
from time import time as timestamp
from pydantic import BaseSettings
from secrets import token_hex
from typing import List
from datetime import date


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
    responsible_user_email = TextField(null=False)
    date = DateField(null=False)
    start_time = TextField(null=False)
    end_time = TextField(null=False)
    reason = TextField(null=False)
    token = TextField(default=token_hex(32), null=False, unique=True)
    approved = BooleanField(default=False)
    id_room = ForeignKeyField(Room, backref="Reservations", null=False)


database.create_tables([Room, Reservation])


def add_room(**kwargs) -> Room:
    room = Room(**kwargs)
    room.save()
    return room


def get_rooms() -> List[Room]:
    query = Room.select()
    rooms = []
    for room in query:
        rooms.append(room.__dict__["__data__"])
    return rooms


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


def get_reservations():
    query = Reservation.select().where(Reservation.date >= date.today())
    reservations = []
    for reservation in query:
        aux = reservation.__dict__["__data__"]
        room = get_room_by_id(reservation.id_room)
        aux.update(room.__dict__["__data__"])
        reservations.append(aux)
    return reservations


def validate_reservation(token: str) -> Reservation | None:
    try:
        reservation: Reservation = Reservation.get(Reservation.token == token)
        reservation.approved = True
        reservation.save()
        return reservation
    except DoesNotExist:
        return None


def verify_reservation(token: str) -> Reservation | None:
    try:
        reservation: Reservation = Reservation.get(Reservation.token == token)
        return reservation.__dict__["__data__"]
    except DoesNotExist:
        return None
