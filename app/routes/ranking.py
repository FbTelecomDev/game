from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/ranking", tags=["Ranking"])


def _to_ranking_item(partida):
    return schemas.RankingItem(
        partida_id=partida.id,
        jugador_id=partida.jugador_id,
        nombre=partida.jugador.nombre,
        cedula=partida.jugador.cedula,
        telefono=partida.jugador.telefono,
        is_cliente=partida.jugador.is_cliente,
        puntaje=partida.puntaje,
        fecha_juego=partida.fecha_juego,
        dia=partida.dia,
    ).model_dump()


@router.get("/hoy", response_model=schemas.ApiResponse)
def ranking_hoy(
    limit: int = Query(default=10, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    is_cliente: bool | None = Query(default=None),
    db: Session = Depends(get_db)
):
    partidas = crud.get_ranking_dia(db, dias_atras=0, is_cliente=is_cliente, limit=limit, skip=skip)
    data = [_to_ranking_item(p) for p in partidas]
    return {"success": True, "message": "Ranking de hoy obtenido", "data": data}


@router.get("/ayer", response_model=schemas.ApiResponse)
def ranking_ayer(
    limit: int = Query(default=10, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    is_cliente: bool | None = Query(default=None),
    db: Session = Depends(get_db)
):
    partidas = crud.get_ranking_dia(db, dias_atras=1, is_cliente=is_cliente, limit=limit, skip=skip)
    data = [_to_ranking_item(p) for p in partidas]
    return {"success": True, "message": "Ranking de ayer obtenido", "data": data}


@router.get("/general", response_model=schemas.ApiResponse)
def ranking_general(
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    is_cliente: bool | None = Query(default=None),
    db: Session = Depends(get_db)
):
    partidas = crud.get_ranking_general(db, is_cliente=is_cliente, limit=limit, skip=skip)
    data = [_to_ranking_item(p) for p in partidas]
    return {"success": True, "message": "Ranking general obtenido", "data": data}


@router.get("/general/mejor-por-jugador", response_model=schemas.ApiResponse)
def ranking_mejor_por_jugador(db: Session = Depends(get_db)):
    rows = crud.get_mejor_por_jugador(db)
    data = [
        schemas.MejorPorJugadorItem(
            jugador_id=row.id,
            nombre=row.nombre,
            cedula=row.cedula,
            telefono=row.telefono,
            is_cliente=row.is_cliente,
            mejor_puntaje=row.mejor_puntaje,
        ).model_dump()
        for row in rows
    ]
    return {
        "success": True,
        "message": "Mejor puntaje por jugador obtenido correctamente",
        "data": data,
    }
