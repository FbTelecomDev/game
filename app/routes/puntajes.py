from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/puntajes", tags=["Puntajes"])


@router.post("", response_model=schemas.ApiResponse)
def create_puntaje(payload: schemas.PartidaCreate, db: Session = Depends(get_db)):
    partida = crud.create_partida(db, payload)
    if not partida:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    return {
        "success": True,
        "message": "Puntaje guardado correctamente",
        "data": schemas.PartidaOut.model_validate(partida).model_dump(),
    }


@router.post("/juego", response_model=schemas.ApiResponse)
def create_puntaje_desde_juego(payload: schemas.PartidaJuegoCreate, db: Session = Depends(get_db)):
    result, mode = crud.create_partida_desde_juego(db, payload)
    if mode == "jugador_no_encontrado":
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    if mode == "asignada":
        return {
            "success": True,
            "message": "Puntaje guardado y asignado al jugador",
            "data": {
                "tipo": "asignada",
                "partida": schemas.PartidaOut.model_validate(result).model_dump(),
            },
        }

    return {
        "success": True,
        "message": "Puntaje guardado como pendiente de asignación",
        "data": {
            "tipo": "pendiente",
            "pendiente": schemas.PartidaPendienteOut.model_validate(result).model_dump(),
        },
    }


@router.get("", response_model=schemas.ApiResponse)
def list_puntajes(
    jugador_id: int | None = Query(default=None, ge=1),
    dia: date | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    partidas = crud.list_partidas(db, jugador_id=jugador_id, dia=dia, limit=limit)
    data = [
        schemas.PartidaDetalleOut(
            id=p.id,
            jugador_id=p.jugador_id,
            jugador_nombre=p.jugador.nombre,
            cedula=p.jugador.cedula,
            telefono=p.jugador.telefono,
            is_cliente=p.jugador.is_cliente,
            puntaje=p.puntaje,
            fecha_juego=p.fecha_juego,
            dia=p.dia,
        ).model_dump()
        for p in partidas
    ]
    return {"success": True, "message": "Partidas obtenidas correctamente", "data": data}


@router.get("/pendientes/count", response_model=schemas.ApiResponse)
def count_puntajes_pendientes(
    dia: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    count = db.execute(
        select(func.count(models.PartidaPendiente.id))
        .where(models.PartidaPendiente.estado == "pendiente")
        .where(models.PartidaPendiente.dia == (dia or crud.today_utc_minus_5()))
    ).scalar_one()
    return {"success": True, "message": "Conteo de pendientes obtenido", "data": {"count": count}}


@router.get("/pendientes", response_model=schemas.ApiResponse)
def list_puntajes_pendientes(
    dia: date | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    pendientes = crud.list_partidas_pendientes(db, dia=dia, limit=limit)
    data = [schemas.PartidaPendienteOut.model_validate(p).model_dump() for p in pendientes]
    return {"success": True, "message": "Partidas pendientes obtenidas correctamente", "data": data}


@router.post("/{partida_pendiente_id}/asignar", response_model=schemas.ApiResponse)
def asignar_puntaje_pendiente(
    partida_pendiente_id: int,
    payload: schemas.AsignarPartidaPendienteIn,
    db: Session = Depends(get_db),
):
    result, status = crud.assign_pending_partida(db, partida_pendiente_id, payload.jugador_id)
    if status == "pendiente_no_encontrada":
        raise HTTPException(status_code=404, detail="Partida pendiente no encontrada")
    if status == "jugador_no_encontrado":
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    return {
        "success": True,
        "message": "Partida pendiente asignada correctamente",
        "data": {
            "partida": schemas.PartidaOut.model_validate(result["partida"]).model_dump(),
            "pendiente": schemas.PartidaPendienteOut.model_validate(result["pendiente"]).model_dump(),
        },
    }
