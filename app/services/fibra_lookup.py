from typing import Any

import httpx

from app.config import settings


def lookup_cliente_por_cedula(cedula: str) -> dict[str, Any]:
    clean_cedula = cedula.strip()
    url = f"{settings.fibra_lookup_url}{clean_cedula}"

    try:
        response = httpx.get(url, timeout=settings.fibra_lookup_timeout_seconds)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        return {
            "available": False,
            "is_cliente": False,
            "nombre": None,
            "telefono": None,
            "codigo_respuesta": None,
            "descripcion": f"No se pudo consultar servicio externo: {exc}",
            "raw": None,
        }

    if not isinstance(payload, list) or not payload:
        return {
            "available": True,
            "is_cliente": False,
            "nombre": None,
            "telefono": None,
            "codigo_respuesta": None,
            "descripcion": "Respuesta sin datos",
            "raw": payload,
        }

    item = payload[0] if isinstance(payload[0], dict) else {}
    codigo_respuesta = item.get("codigoRespuesta")
    descripcion = item.get("descripcionRespueta") or item.get("descripcionRespuesta") or ""
    contratos = item.get("contratos") if isinstance(item.get("contratos"), list) else []
    contrato = contratos[0] if contratos and isinstance(contratos[0], dict) else {}

    nombre = contrato.get("cliente")
    telefono = contrato.get("telefono")
    is_cliente = bool(contrato)

    return {
        "available": True,
        "is_cliente": is_cliente,
        "nombre": nombre.strip() if isinstance(nombre, str) and nombre.strip() else None,
        "telefono": telefono.strip() if isinstance(telefono, str) and telefono.strip() else None,
        "codigo_respuesta": codigo_respuesta,
        "descripcion": descripcion,
        "raw": item,
    }
