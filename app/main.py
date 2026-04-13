from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine
from app.routes import health, jugadores, puntajes, ranking


def create_data_directory() -> None:
    db_path = settings.sqlite_file_path
    if db_path is None:
        return

    db_dir = db_path.parent
    if db_dir and str(db_dir) != ".":
        db_dir.mkdir(parents=True, exist_ok=True)


app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(jugadores.router)
app.include_router(puntajes.router)
app.include_router(ranking.router)


@app.on_event("startup")
def on_startup():
    if settings.database_url.startswith("libsql://") and not settings.turso_auth_token_clean:
        raise RuntimeError("Falta TURSO_AUTH_TOKEN para conexión libsql/Turso.")
    create_data_directory()
    Base.metadata.create_all(bind=engine)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "Error en la solicitud"
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": message, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Error de validación",
            "data": {"errors": exc.errors()},
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Error interno del servidor",
            "data": {"error": str(exc)},
        },
    )
