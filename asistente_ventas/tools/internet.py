from ddgs import DDGS

MAX_RESULTADOS = 10


def buscar_en_internet(consulta: str, max_resultados: int = 5) -> dict:
    """Busca información actual en internet y devuelve título, URL y resumen.

    Usala solo cuando la documentación interna o la base de datos no alcancen,
    por ejemplo para cotizaciones, noticias del sector o información pública.

    Args:
        consulta: Tema o pregunta a buscar.
        max_resultados: Cantidad de resultados deseados, entre 1 y 10.
    """
    if not isinstance(consulta, str) or len(consulta.strip()) < 3:
        return {"ok": False, "error": "La consulta debe tener al menos 3 caracteres."}
    try:
        max_resultados = int(max_resultados)
    except (TypeError, ValueError):
        return {"ok": False, "error": "max_resultados debe ser un número entero."}
    max_resultados = max(1, min(max_resultados, MAX_RESULTADOS))

    try:
        respuesta = DDGS().text(query=consulta.strip(), max_results=max_resultados)
        resultados = list(respuesta) if respuesta else []
    except Exception as exc:
        return {
            "ok": False,
            "error": f"No se pudo completar la búsqueda: {exc}",
            "sugerencia": "Reintentá con otra consulta más corta o verificá la conexión.",
        }

    if not resultados:
        return {
            "ok": True,
            "resultados": [],
            "mensaje": "La búsqueda no devolvió resultados. Probá con otros términos.",
        }

    limpios = [
        {
            "titulo": item.get("title") or "Sin título",
            "url": item.get("href") or "",
            "resumen": item.get("body") or "",
        }
        for item in resultados
    ]
    return {"ok": True, "resultados": limpios, "cantidad": len(limpios)}
