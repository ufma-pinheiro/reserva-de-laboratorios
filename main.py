from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from config import settings
from pydantic import BaseModel, EmailStr, Field
from datetime import date, time
from fastapi.exceptions import HTTPException
from secrets import token_hex

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
    id_room: int


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
    return room


@app.post("/reservation")
async def reserve(reservation: Reservation):
    if not reservation.responsible_user_email.endswith("@ufma.br"):
        raise HTTPException(401)
    return reservation


@app.post("/reservation/to-approve")
async def reserve_to_approve(token: str):
    return token


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
        "url": "https://portalpadrao.ufma.br/site/institucional/superintendencias/sce/manual-da-marca/png-logo-ufma-colorido.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
