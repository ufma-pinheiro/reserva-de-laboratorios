from fastapi import FastAPI, Depends
from fastapi.openapi.utils import get_openapi
from config import settings
from pydantic import BaseModel, EmailStr, Field
from datetime import date, time
from fastapi.exceptions import HTTPException
import email_sender
import database
from typing import List
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.config import Config
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

security = HTTPBasic()
templates = Jinja2Templates(directory="templates")

app.add_middleware(SessionMiddleware, secret_key=settings.secret_token)
config = Config('.env')
oauth = OAuth(config)

CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)


class Room(BaseModel):
    name: str
    location: str
    people_capacity: int
    description: str | None


class RoomWithID(Room):
    id: int


class Reservation(BaseModel):
    responsible_user_email: EmailStr = Field(default="user@ufma.br")
    date: date
    start_time: time = Field(default="08:00")
    end_time: time = Field(default="18:00")
    reason: str
    id_room: int


class ReservationData(Reservation):
    name: str
    location: str
    people_capacity: int
    description: str | None


@app.get("/")
async def root(request: Request):
    user = request.session.get('user')
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.get('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get('/auth')
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    user = token.get('userinfo')
    if user:
        request.session['user'] = dict(user)
    return RedirectResponse(url='/reserve')


@app.get('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')


@app.get("/reserve")
async def root(request: Request):
    user = request.session.get('user')
    if user:
        return templates.TemplateResponse("reserve.html", {"request": request, "user": user})
    return RedirectResponse(url='/')


@app.get("/confirmation")
async def confirmation(request: Request):
    return templates.TemplateResponse("confirmation.html", {"request": request})


@app.get("/verify/{token}")
async def verify(token: str, request: Request):
    reservation = database.verify_reservation(token)
    if reservation:
        if reservation["approved"]:
            room = database.get_room_by_id(reservation["id_room"])
            reservation.update(room.__dict__["__data__"])
            return templates.TemplateResponse("verify.html", {"request": request,
                                                              "reservation": reservation})
    return RedirectResponse("/")


@app.get("/info")
async def info():
    return {
        "app_name": settings.app_name,
        "admin_email": settings.admin_email
    }


@app.post("/room")
async def add_room(room: Room, credentials: HTTPBasicCredentials = Depends(security)):
    if not (credentials.username == settings.admin_email and
            credentials.password == settings.admin_password):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    db_room = database.add_room(**dict(room))
    if db_room:
        return HTTPException(200)


@app.get("/room/all", response_model=List[RoomWithID])
async def rooms():
    list_room: List[RoomWithID] = database.get_rooms()
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
        raise HTTPException(200)
    except Exception as e:
        raise HTTPException(400, detail=str(e))


@app.post("/reservation/to-approve")
async def reserve_to_approve(token: str):
    """Endpoint responsavel pela auto-aprovação de uma reserva"""
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


@app.get("/reservation/verify/{token}", response_model=ReservationData)
async def reserve_verify(token: str):
    """Endpoint responsavel por demonstrar que a determinada reserva é valida\n
    Retorna um json com os dados da reserva"""
    reservation = database.verify_reservation(token)
    if reservation:
        if reservation["approved"]:
            room = database.get_room_by_id(reservation["id_room"])
            reservation.update(room.__dict__["__data__"])
            return reservation
        raise HTTPException(204)
    else:
        raise HTTPException(404)


@app.get("/time-block-list")
async def time_block_list(id_room: int, reservation_date: date):
    """Retorna uma lista pares de inicio e fim de horarios já reservados"""
    return database.time_block_list(id_room, reservation_date)


@app.get("/check-time-collision")
async def check_time_collision(id_room: int, reservation_date: date, start_time: time,
                               end_time: time):
    """Retorna True caso o horario esteja disponivel"""
    return database.check_time_collision(str(start_time), str(end_time),
                                         database.time_block_list(id_room, reservation_date))


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
