from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from config import settings

app = FastAPI()


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/info")
async def info():
    return {
        "app_name": settings.app_name,
        "admin_email": settings.admin_email
    }


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
