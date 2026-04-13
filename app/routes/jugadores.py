from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.services.fibra_lookup import lookup_cliente_por_cedula

router = APIRouter(prefix="/api/jugadores", tags=["Jugadores"])


@router.post("", response_model=schemas.ApiResponse)
def create_or_update_jugador(payload: schemas.JugadorCreate, db: Session = Depends(get_db)):
    lookup = lookup_cliente_por_cedula(payload.cedula)
    resolved_payload = payload

    if lookup.get("available"):
        resolved_payload = schemas.JugadorCreate(
            nombre=lookup.get("nombre") or payload.nombre,
            cedula=payload.cedula,
            telefono=lookup.get("telefono") or payload.telefono,
            is_cliente=bool(lookup.get("is_cliente")),
        )

    jugador, created, updated = crud.upsert_jugador(db, resolved_payload)
    if created:
        message = "Jugador creado correctamente"
    elif updated:
        message = "Jugador existente actualizado correctamente"
    else:
        message = "Jugador ya existente"

    return {
        "success": True,
        "message": message,
        "data": {
            "jugador": schemas.JugadorOut.model_validate(jugador).model_dump(),
            "created": created,
            "updated": updated,
            "cliente_lookup": {
                "available": lookup.get("available", False),
                "is_cliente": lookup.get("is_cliente", False),
                "nombre": lookup.get("nombre"),
                "telefono": lookup.get("telefono"),
                "codigo_respuesta": lookup.get("codigo_respuesta"),
                "descripcion": lookup.get("descripcion"),
            },
        },
    }


@router.get("", response_model=schemas.ApiResponse)
def get_jugadores(
    q: str | None = Query(default=None, description="Buscar por nombre o cédula"),
    db: Session = Depends(get_db),
):
    jugadores = crud.list_jugadores(db, q)
    data = [schemas.JugadorOut.model_validate(j).model_dump() for j in jugadores]
    return {"success": True, "message": "Jugadores obtenidos correctamente", "data": data}


@router.get("/lookup/{cedula}", response_model=schemas.ApiResponse)
def lookup_jugador_by_cedula(cedula: str):
    lookup = lookup_cliente_por_cedula(cedula)
    return {
        "success": True,
        "message": "Consulta de cédula completada",
        "data": {
            "cedula": cedula,
            "available": lookup.get("available", False),
            "is_cliente": lookup.get("is_cliente", False),
            "nombre": lookup.get("nombre"),
            "telefono": lookup.get("telefono"),
            "codigo_respuesta": lookup.get("codigo_respuesta"),
            "descripcion": lookup.get("descripcion"),
        },
    }


@router.get("/{jugador_id}", response_model=schemas.ApiResponse)
def get_jugador(jugador_id: int, db: Session = Depends(get_db)):
    jugador = crud.get_jugador_by_id(db, jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    partidas = sorted(jugador.partidas, key=lambda p: p.fecha_juego, reverse=True)
    mejor_puntaje = max((p.puntaje for p in partidas), default=0)
    detalle = schemas.JugadorDetalleOut(
        id=jugador.id,
        nombre=jugador.nombre,
        cedula=jugador.cedula,
        telefono=jugador.telefono,
        is_cliente=jugador.is_cliente,
        created_at=jugador.created_at,
        partidas=[schemas.PartidaOut.model_validate(p) for p in partidas],
        mejor_puntaje=mejor_puntaje,
        cantidad_partidas=len(partidas),
    )
    return {
        "success": True,
        "message": "Detalle de jugador obtenido correctamente",
        "data": detalle.model_dump(),
    }
