from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from config import settings
from pydantic import BaseModel, EmailStr, Field
from datetime import date, time
from fastapi.exceptions import HTTPException
import email_sender
import database
from typing import List

app = FastAPI()


class Room(BaseModel):
    name: str
    location: str
    people_capacity: int
    description: str | None


class Reservation(BaseModel):
    responsible_user_email: EmailStr = Field(default="user@ufma.br")
    date: date
    start_time: time = Field(default="08:00")
    end_time: time = Field(default="18:00")
    reason: str
    id_room: int


class ReservationData(BaseModel):
    responsible_user_email: EmailStr = Field(default="user@ufma.br")
    date: date
    start_time: time = Field(default="08:00")
    end_time: time = Field(default="18:00")
    reason: str
    name: str
    location: str
    people_capacity: int
    description: str | None


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/info")
async def info():
    return {
        "app_name": settings.app_name,
        "admin_email": settings.admin_email
    }


@app.post("/room")
async def add_room(room: Room):
    db_room = database.add_room(**dict(room))
    if db_room:
        return HTTPException(200)


@app.get("/room/all", response_model=List[Room])
async def rooms():
    list_room: List[Room] = database.get_rooms()
    return list_room


@app.get("/reservation/all", response_model=List[ReservationData])
async def reservations():
    list_reservation: List[Reservation] = database.get_reservations()
    return list_reservation


@app.post("/reservation")
async def reserve(reservation: Reservation):
    if not reservation.responsible_user_email.endswith("@ufma.br"):
        raise HTTPException(401)
    try:
        db_reservation = database.add_reservation(**dict(reservation))
        email_sender.send(reservation.responsible_user_email,
                          "Token para validação da reserva.",
                          f"Token: {db_reservation.token}")
    except Exception as e:
        raise HTTPException(400, detail=str(e))


@app.post("/reservation/to-approve")
async def reserve_to_approve(token: str):
    reservation = database.validate_reservation(token)
    if reservation:
        room = database.get_room_by_id(reservation.id_room)
        email_sender.send(reservation.responsible_user_email,
                          "Reserva realizada com sucesso!",
                          f"""A sala({room.name}) na data {reservation.date} e 
                          horario {reservation.start_time} às {reservation.end_time},
                          está reservada para {reservation.responsible_user_email},
                          para verificar acesse o sistemas de reserva e verifique com o codigo: 
                          {reservation.token} """)
    else:
        raise HTTPException(404)


@app.post("/reservation/verify", response_model=ReservationData)
async def reserve_verify(token: str):
    reservation = database.verify_reservation(token)
    if reservation:
        if reservation["approved"]:
            room = database.get_room_by_id(reservation["id_room"])
            reservation.update(room.__dict__["__data__"])
            return reservation
        raise HTTPException(204)
    else:
        raise HTTPException(404)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.version,
        description="API de reserva de laboratorios automatizado.",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://portalpadrao.ufma.br/site/institucional/" +
               "superintendencias/sce/manual-da-marca/png-logo-ufma-colorido.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
