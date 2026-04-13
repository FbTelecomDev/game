from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Jugador(Base):
    __tablename__ = "jugadores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    cedula: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    telefono: Mapped[str] = mapped_column(String(32), nullable=False)
    is_cliente: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    partidas: Mapped[list["Partida"]] = relationship(
        "Partida", back_populates="jugador", cascade="all, delete-orphan"
    )


class Partida(Base):
    __tablename__ = "partidas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    jugador_id: Mapped[int] = mapped_column(ForeignKey("jugadores.id"), nullable=False, index=True)
    puntaje: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    fecha_juego: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    dia: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    jugador: Mapped["Jugador"] = relationship("Jugador", back_populates="partidas")


class PartidaPendiente(Base):
    __tablename__ = "partidas_pendientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    puntaje: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    fecha_juego: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    dia: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente", nullable=False, index=True)
