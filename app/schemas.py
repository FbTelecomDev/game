from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class JugadorBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    cedula: str = Field(..., min_length=5, max_length=32)
    telefono: str = Field(..., min_length=6, max_length=32)
    is_cliente: bool = False

    @field_validator("nombre", "cedula", "telefono")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return value.strip()


class JugadorCreate(JugadorBase):
    pass


class JugadorOut(JugadorBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PartidaCreate(BaseModel):
    jugador_id: int = Field(..., ge=1)
    puntaje: int = Field(..., ge=0)


class PartidaJuegoCreate(BaseModel):
    puntaje: int = Field(..., ge=0)
    jugador_id: int | None = Field(default=None, ge=1)


class PartidaOut(BaseModel):
    id: int
    jugador_id: int
    puntaje: int
    fecha_juego: datetime
    dia: date
    model_config = ConfigDict(from_attributes=True)


class PartidaDetalleOut(BaseModel):
    id: int
    jugador_id: int
    jugador_nombre: str
    cedula: str
    telefono: str
    is_cliente: bool
    puntaje: int
    fecha_juego: datetime
    dia: date


class PartidaPendienteOut(BaseModel):
    id: int
    puntaje: int
    fecha_juego: datetime
    dia: date
    estado: str
    model_config = ConfigDict(from_attributes=True)


class AsignarPartidaPendienteIn(BaseModel):
    jugador_id: int = Field(..., ge=1)


class JugadorDetalleOut(JugadorOut):
    partidas: list[PartidaOut] = []
    mejor_puntaje: int = 0
    cantidad_partidas: int = 0


class RankingItem(BaseModel):
    partida_id: int
    jugador_id: int
    nombre: str
    cedula: str
    telefono: str
    is_cliente: bool
    puntaje: int
    fecha_juego: datetime
    dia: date


class MejorPorJugadorItem(BaseModel):
    jugador_id: int
    nombre: str
    cedula: str
    telefono: str
    is_cliente: bool
    mejor_puntaje: int
