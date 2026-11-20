import os
import uuid

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .rutas import COLECCION, RUTA_VECTORES

MODELO_EMBEDDINGS = "nomic-embed-text"
MAX_CARACTERES = 20000


def _vector_store() -> Chroma:
    return Chroma(
        collection_name=COLECCION,
        embedding_function=OllamaEmbeddings(
            model=MODELO_EMBEDDINGS,
            base_url=os.getenv("OLLAMA_API_BASE", "http://localhost:11434"),
        ),
        persist_directory=str(RUTA_VECTORES),
        collection_metadata={"hnsw:space": "cosine"},
    )


def _error_embeddings(exc: Exception) -> dict:
    return {
        "ok": False,
        "error": f"No se pudo acceder a la base vectorial: {exc}",
        "sugerencia": (
            "Verificá que Ollama esté activo y que el modelo de embeddings esté "
            f"descargado con: ollama pull {MODELO_EMBEDDINGS}"
        ),
    }


def buscar_en_documentos(consulta: str, cantidad: int = 4) -> dict:
    """Busca en los documentos internos de la empresa y devuelve los fragmentos más relevantes.

    Usala para políticas comerciales, descuentos, garantías, devoluciones, envíos,
    condiciones de pago y cualquier procedimiento documentado.

    Args:
        consulta: Pregunta o tema a buscar en la documentación.
        cantidad: Cantidad de fragmentos a recuperar, entre 1 y 10.
    """
    if not isinstance(consulta, str) or len(consulta.strip()) < 3:
        return {"ok": False, "error": "La consulta debe tener al menos 3 caracteres."}
    try:
        cantidad = int(cantidad)
    except (TypeError, ValueError):
        return {"ok": False, "error": "cantidad debe ser un número entero."}
    cantidad = max(1, min(cantidad, 10))

    if not RUTA_VECTORES.exists():
        return {
            "ok": False,
            "error": "La base vectorial todavía no está creada.",
            "sugerencia": "Ejecutá python seed.py para indexar los documentos internos.",
        }

    try:
        resultados = _vector_store().similarity_search_with_relevance_scores(
            consulta.strip(), k=cantidad
        )
    except Exception as exc:
        return _error_embeddings(exc)

    if not resultados:
        return {
            "ok": True,
            "resultados": [],
            "mensaje": "No se encontraron documentos relacionados. Probá con otras palabras o usá buscar_en_internet.",
        }

    fragmentos = [
        {
            "titulo": documento.metadata.get("titulo", "Sin título"),
            "contenido": documento.page_content,
            "relevancia": round(float(puntaje), 3),
        }
        for documento, puntaje in resultados
    ]
    return {"ok": True, "resultados": fragmentos, "cantidad": len(fragmentos)}


def indexar_documento(titulo: str, contenido: str) -> dict:
    """Indexa un documento nuevo en la base vectorial para consultarlo después.

    Usala cuando el usuario pida guardar, registrar o documentar información,
    por ejemplo una política, una nota interna o un procedimiento.

    Args:
        titulo: Nombre corto del documento, entre 3 y 120 caracteres.
        contenido: Texto completo del documento, de al menos 40 caracteres.
    """
    if not isinstance(titulo, str):
        return {"ok": False, "error": "El título debe ser un texto."}
    titulo = titulo.strip()
    if not 3 <= len(titulo) <= 120:
        return {"ok": False, "error": "El título debe tener entre 3 y 120 caracteres."}
    if not isinstance(contenido, str):
        return {"ok": False, "error": "El contenido debe ser un texto."}
    contenido = contenido.strip()
    if len(contenido) < 40:
        return {"ok": False, "error": "El contenido debe tener al menos 40 caracteres."}
    if len(contenido) > MAX_CARACTERES:
        return {"ok": False, "error": f"El contenido supera los {MAX_CARACTERES} caracteres."}

    try:
        divisor = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        documentos = divisor.create_documents([contenido], metadatas=[{"titulo": titulo}])
        identificadores = [
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{titulo}|{documento.page_content}"))
            for documento in documentos
        ]
        _vector_store().add_documents(documents=documentos, ids=identificadores)
    except Exception as exc:
        return _error_embeddings(exc)

    return {
        "ok": True,
        "mensaje": f"Documento indexado correctamente: {titulo}",
        "fragmentos": len(identificadores),
    }
