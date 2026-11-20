from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
RUTA_BD = BASE_DIR / "data" / "ventas.db"
RUTA_VECTORES = BASE_DIR / "vector_store"
RUTA_DOCUMENTOS = BASE_DIR / "documentos"
COLECCION = "documentacion_comercial"
