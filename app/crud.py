from datetime import date, datetime, timedelta, timezone

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app import models, schemas

UTC_MINUS_5 = timezone(timedelta(hours=-5))


def now_utc_minus_5_naive() -> datetime:
    # Se guarda como hora local UTC-5 sin tzinfo para mantener compatibilidad con SQLite.
    return datetime.now(UTC_MINUS_5).replace(tzinfo=None)


def today_utc_minus_5() -> date:
    return datetime.now(UTC_MINUS_5).date()


def upsert_jugador(db: Session, payload: schemas.JugadorCreate):
    existing = db.execute(select(models.Jugador).where(models.Jugador.cedula == payload.cedula)).scalar_one_or_none()
    if existing:
        updated = False
        if existing.nombre != payload.nombre:
            existing.nombre = payload.nombre
            updated = True
        if existing.telefono != payload.telefono:
            existing.telefono = payload.telefono
            updated = True
        if existing.is_cliente != payload.is_cliente:
            existing.is_cliente = payload.is_cliente
            updated = True
        if updated:
            db.add(existing)
            db.commit()
            db.refresh(existing)
        return existing, False, updated

    jugador = models.Jugador(
        nombre=payload.nombre,
        cedula=payload.cedula,
        telefono=payload.telefono,
        is_cliente=payload.is_cliente,
    )
    db.add(jugador)
    db.commit()
    db.refresh(jugador)
    return jugador, True, False


def list_jugadores(db: Session, q: str | None = None):
    stmt = select(models.Jugador).order_by(desc(models.Jugador.created_at))
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(models.Jugador.nombre.ilike(term), models.Jugador.cedula.ilike(term)))
    return db.execute(stmt).scalars().all()


def get_jugador_by_id(db: Session, jugador_id: int):
    stmt = (
        select(models.Jugador)
        .where(models.Jugador.id == jugador_id)
        .options(joinedload(models.Jugador.partidas))
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def create_partida(db: Session, payload: schemas.PartidaCreate):
    jugador = db.execute(select(models.Jugador).where(models.Jugador.id == payload.jugador_id)).scalar_one_or_none()
    if not jugador:
        return None

    partida = models.Partida(
        jugador_id=payload.jugador_id,
        puntaje=payload.puntaje,
        fecha_juego=now_utc_minus_5_naive(),
        dia=today_utc_minus_5(),
    )
    db.add(partida)
    db.commit()
    db.refresh(partida)
    return partida


def create_partida_desde_juego(db: Session, payload: schemas.PartidaJuegoCreate):
    if payload.jugador_id is not None:
        partida = create_partida(
            db,
            schemas.PartidaCreate(jugador_id=payload.jugador_id, puntaje=payload.puntaje),
        )
        if not partida:
            return None, "jugador_no_encontrado"
        return partida, "asignada"

    pendiente = models.PartidaPendiente(
        puntaje=payload.puntaje,
        fecha_juego=now_utc_minus_5_naive(),
        dia=today_utc_minus_5(),
        estado="pendiente",
    )
    db.add(pendiente)
    db.commit()
    db.refresh(pendiente)
    return pendiente, "pendiente"


def list_partidas(db: Session, jugador_id: int | None = None, dia: date | None = None, limit: int = 200):
    stmt = select(models.Partida).options(joinedload(models.Partida.jugador)).order_by(desc(models.Partida.fecha_juego))
    if jugador_id:
        stmt = stmt.where(models.Partida.jugador_id == jugador_id)
    if dia:
        stmt = stmt.where(models.Partida.dia == dia)
    stmt = stmt.limit(limit)
    return db.execute(stmt).scalars().all()


def get_ranking_dia(db: Session, dias_atras: int = 0, is_cliente: bool | None = None, limit: int = 10, skip: int = 0):
    target_date = today_utc_minus_5() - timedelta(days=dias_atras)
    
    # Subconsulta para el mejor puntaje por jugador en el día
    sub_stmt = select(models.Partida.jugador_id, func.max(models.Partida.puntaje).label("max_puntaje")).where(models.Partida.dia == target_date).group_by(models.Partida.jugador_id)
    subquery = sub_stmt.subquery()

    stmt = (
        select(models.Partida)
        .join(subquery, (models.Partida.jugador_id == subquery.c.jugador_id) & (models.Partida.puntaje == subquery.c.max_puntaje))
        .join(models.Jugador, models.Partida.jugador_id == models.Jugador.id)
        .options(joinedload(models.Partida.jugador))
        .where(models.Partida.dia == target_date)
    )

    if is_cliente is not None:
        stmt = stmt.where(models.Jugador.is_cliente == is_cliente)

    stmt = stmt.group_by(models.Partida.jugador_id).order_by(desc(models.Partida.puntaje), models.Partida.fecha_juego.asc()).limit(limit).offset(skip)
    return db.execute(stmt).scalars().all()


def get_ranking_general(db: Session, is_cliente: bool | None = None, limit: int = 20, skip: int = 0):
    subquery = (
        select(models.Partida.jugador_id, func.max(models.Partida.puntaje).label("max_puntaje"))
        .group_by(models.Partida.jugador_id)
        .subquery()
    )
    stmt = (
        select(models.Partida)
        .join(subquery, (models.Partida.jugador_id == subquery.c.jugador_id) & (models.Partida.puntaje == subquery.c.max_puntaje))
        .join(models.Jugador, models.Partida.jugador_id == models.Jugador.id)
        .options(joinedload(models.Partida.jugador))
    )

    if is_cliente is not None:
        stmt = stmt.where(models.Jugador.is_cliente == is_cliente)

    stmt = stmt.group_by(models.Partida.jugador_id).order_by(desc(models.Partida.puntaje), models.Partida.fecha_juego.asc()).limit(limit).offset(skip)
    return db.execute(stmt).scalars().all()


def get_mejor_por_jugador(db: Session):
    subquery = (
        select(models.Partida.jugador_id, func.max(models.Partida.puntaje).label("mejor_puntaje"))
        .group_by(models.Partida.jugador_id)
        .subquery()
    )
    stmt = (
        select(
            models.Jugador.id,
            models.Jugador.nombre,
            models.Jugador.cedula,
            models.Jugador.telefono,
            models.Jugador.is_cliente,
            subquery.c.mejor_puntaje,
        )
        .join(subquery, subquery.c.jugador_id == models.Jugador.id)
        .order_by(desc(subquery.c.mejor_puntaje), models.Jugador.nombre.asc())
    )
    return db.execute(stmt).all()


def get_total_jugadores(db: Session) -> int:
    return db.execute(select(func.count(models.Jugador.id))).scalar_one()


def get_total_partidas_hoy(db: Session) -> int:
    return db.execute(select(func.count(models.Partida.id)).where(models.Partida.dia == today_utc_minus_5())).scalar_one()


def get_mejor_puntaje_hoy(db: Session) -> int:
    result = db.execute(select(func.max(models.Partida.puntaje)).where(models.Partida.dia == today_utc_minus_5())).scalar_one()
    return result or 0


def list_partidas_pendientes(db: Session, dia: date | None = None, limit: int = 200):
    stmt = select(models.PartidaPendiente).where(models.PartidaPendiente.estado == "pendiente")
    if dia:
        stmt = stmt.where(models.PartidaPendiente.dia == dia)
    stmt = stmt.order_by(desc(models.PartidaPendiente.fecha_juego)).limit(limit)
    return db.execute(stmt).scalars().all()


def assign_pending_partida(db: Session, partida_pendiente_id: int, jugador_id: int):
    pendiente = db.execute(
        select(models.PartidaPendiente).where(models.PartidaPendiente.id == partida_pendiente_id)
    ).scalar_one_or_none()
    if not pendiente or pendiente.estado != "pendiente":
        return None, "pendiente_no_encontrada"

    jugador = db.execute(select(models.Jugador).where(models.Jugador.id == jugador_id)).scalar_one_or_none()
    if not jugador:
        return None, "jugador_no_encontrado"

    partida = models.Partida(
        jugador_id=jugador_id,
        puntaje=pendiente.puntaje,
        dia=pendiente.dia,
        fecha_juego=pendiente.fecha_juego,
    )
    pendiente.estado = "asignada"
    db.add(partida)
    db.add(pendiente)
    db.commit()
    db.refresh(partida)
    db.refresh(pendiente)
    return {"partida": partida, "pendiente": pendiente}, "ok"
