from fastapi import APIRouter, Depends
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
def ranking_hoy(db: Session = Depends(get_db)):
    partidas = crud.get_ranking_hoy(db)
    data = [_to_ranking_item(p) for p in partidas]
    return {"success": True, "message": "Ranking del día obtenido correctamente", "data": data}


@router.get("/hoy/top10", response_model=schemas.ApiResponse)
def ranking_hoy_top10(db: Session = Depends(get_db)):
    partidas = crud.get_ranking_hoy(db, limit=10)
    data = [_to_ranking_item(p) for p in partidas]
    return {"success": True, "message": "Top 10 del día obtenido correctamente", "data": data}


@router.get("/general", response_model=schemas.ApiResponse)
def ranking_general(db: Session = Depends(get_db)):
    partidas = crud.get_ranking_general(db, limit=20)
    data = [_to_ranking_item(p) for p in partidas]
    return {"success": True, "message": "Ranking general obtenido correctamente", "data": data}


@router.get("/general/top10", response_model=schemas.ApiResponse)
def ranking_general_top10(db: Session = Depends(get_db)):
    partidas = crud.get_ranking_general(db, limit=10)
    data = [_to_ranking_item(p) for p in partidas]
    return {"success": True, "message": "Top 10 general obtenido correctamente", "data": data}


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
