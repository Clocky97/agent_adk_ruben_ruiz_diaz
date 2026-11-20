import re
import sqlite3

from .rutas import RUTA_BD

ESQUEMA = """
Tabla ventas:
  id INTEGER
  fecha TEXT (AAAA-MM-DD)
  categoria TEXT
  producto TEXT
  cantidad INTEGER
  precio_unitario REAL
  descuento REAL
  total REAL
  vendedor TEXT
  region TEXT

Tabla metas:
  categoria TEXT
  mes TEXT (AAAA-MM)
  objetivo REAL

Categorías disponibles: Notebooks, Monitores, Periféricos, Almacenamiento, Redes.
Regiones disponibles: Norte, Sur, Centro, Oeste.
El período cubierto por la base va del 2026-01-01 al 2026-09-30.
"""

PALABRAS_PROHIBIDAS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "replace",
    "attach",
    "detach",
    "pragma",
    "vacuum",
    "reindex",
    "trigger",
    "load_extension",
)

MAX_FILAS = 50


def _validar_sql(sql: str) -> str | None:
    if not isinstance(sql, str):
        return "La consulta debe ser un texto."
    limpio = sql.strip()
    if not limpio:
        return "La consulta está vacía."
    if len(limpio) > 2000:
        return "La consulta supera el máximo de 2000 caracteres."
    if "--" in limpio or "/*" in limpio:
        return "No se permiten comentarios dentro de la consulta."
    if limpio.endswith(";"):
        limpio = limpio[:-1].strip()
    if ";" in limpio:
        return "Solo se permite una sentencia SQL por consulta."
    if not re.match(r"(?is)^(select|with)\b", limpio):
        return "Solo se permiten consultas SELECT o WITH."
    for palabra in PALABRAS_PROHIBIDAS:
        if re.search(rf"\b{palabra}\b", limpio, re.IGNORECASE):
            return f"La consulta usa una operación no permitida: {palabra}."
    return None


def consultar_ventas(sql: str) -> dict:
    """Ejecuta una consulta SQL de solo lectura sobre la base comercial.

    Usala para responder cualquier pregunta con datos numéricos de ventas,
    productos, vendedores, regiones, fechas o cumplimiento de metas.

    Args:
        sql: Una única sentencia SELECT o WITH sobre las tablas ventas y metas.

    Returns:
        Las filas obtenidas (máximo 50), la cantidad de filas y si el resultado
        fue truncado. Si hay un error devuelve ok=False con una explicación.
    """
    error = _validar_sql(sql)
    if error:
        return {"ok": False, "error": error}

    limpio = sql.strip()
    if limpio.endswith(";"):
        limpio = limpio[:-1].strip()

    if not RUTA_BD.exists():
        return {
            "ok": False,
            "error": "No existe la base de datos. Ejecutá python seed.py para generarla.",
        }

    conexion = None
    try:
        conexion = sqlite3.connect(RUTA_BD)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA query_only = ON")
        cursor = conexion.execute(limpio)
        if cursor.description is None:
            return {"ok": False, "error": "La consulta no devolvió columnas."}
        columnas = [columna[0] for columna in cursor.description]
        filas = cursor.fetchmany(MAX_FILAS + 1)
        truncado = len(filas) > MAX_FILAS
        filas = filas[:MAX_FILAS]
        resultados = [dict(zip(columnas, fila)) for fila in filas]
    except sqlite3.Error as exc:
        return {
            "ok": False,
            "error": f"Error de SQL: {exc}",
            "sugerencia": "Revisá el esquema y volvé a intentar.",
            "esquema": ESQUEMA.strip(),
        }
    finally:
        if conexion is not None:
            conexion.close()

    if not resultados:
        return {
            "ok": True,
            "filas": [],
            "cantidad": 0,
            "truncado": False,
            "mensaje": "La consulta no devolvió resultados. Verificá el período, la categoría o los filtros usados.",
        }

    return {
        "ok": True,
        "filas": resultados,
        "cantidad": len(resultados),
        "truncado": truncado,
    }


def esquema_ventas() -> str:
    """Devuelve el esquema de la base comercial y los valores disponibles.

    Usala cuando no conozcas las tablas, columnas, categorías, regiones o el
    período cubierto, antes de escribir una consulta SQL.
    """
    return ESQUEMA.strip()
