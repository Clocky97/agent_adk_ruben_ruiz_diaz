import json
import random
import shutil
import sqlite3
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RUTA_BD = BASE_DIR / "data" / "ventas.db"
RUTA_DOCUMENTOS = BASE_DIR / "documentos"
RUTA_VECTORES = BASE_DIR / "vector_store"

CATALOGO = {
    "Notebooks": [
        ("Notebook Nova 14", 1250000.0),
        ("Notebook Nova Pro 16", 1890000.0),
        ("Notebook Lite 13", 890000.0),
    ],
    "Monitores": [
        ("Monitor Vision 24", 320000.0),
        ("Monitor Vision 27 QHD", 540000.0),
        ("Monitor UltraWide 34", 780000.0),
    ],
    "Periféricos": [
        ("Teclado Mecánico K2", 95000.0),
        ("Mouse Inalámbrico M3", 42000.0),
        ("Auriculares Studio", 130000.0),
    ],
    "Almacenamiento": [
        ("SSD NVMe 1TB", 145000.0),
        ("SSD NVMe 2TB", 260000.0),
        ("Disco Externo 4TB", 210000.0),
    ],
    "Redes": [
        ("Router WiFi 6 AX3000", 185000.0),
        ("Switch 8 Puertos", 120000.0),
        ("Repetidor Mesh", 98000.0),
    ],
}

VENDEDORES = ["Lucía Fernández", "Martín Gómez", "Sofía Ramírez", "Diego Torres", "Valentina Ruiz"]
REGIONES = ["Norte", "Sur", "Centro", "Oeste"]
PESOS_CATEGORIA = [0.28, 0.2, 0.22, 0.18, 0.12]
DESCUENTOS = [0.0, 0.0, 0.0, 0.05, 0.1]


def crear_base() -> None:
    RUTA_BD.parent.mkdir(parents=True, exist_ok=True)
    if RUTA_BD.exists():
        RUTA_BD.unlink()
    conexion = sqlite3.connect(RUTA_BD)
    conexion.executescript(
        """
        CREATE TABLE ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            categoria TEXT NOT NULL,
            producto TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            descuento REAL NOT NULL,
            total REAL NOT NULL,
            vendedor TEXT NOT NULL,
            region TEXT NOT NULL
        );
        CREATE TABLE metas (
            categoria TEXT NOT NULL,
            mes TEXT NOT NULL,
            objetivo REAL NOT NULL,
            PRIMARY KEY (categoria, mes)
        );
        """
    )

    random.seed(42)
    categorias = list(CATALOGO)
    dia = date(2026, 1, 1)
    fin = date(2026, 9, 30)
    while dia <= fin:
        for _ in range(random.randint(1, 4)):
            categoria = random.choices(categorias, weights=PESOS_CATEGORIA, k=1)[0]
            producto, precio = random.choice(CATALOGO[categoria])
            cantidad = random.randint(1, 4)
            descuento = random.choice(DESCUENTOS)
            total = round(precio * cantidad * (1 - descuento), 2)
            conexion.execute(
                "INSERT INTO ventas (fecha, categoria, producto, cantidad, precio_unitario, descuento, total, vendedor, region) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    dia.isoformat(),
                    categoria,
                    producto,
                    cantidad,
                    precio,
                    descuento,
                    total,
                    random.choice(VENDEDORES),
                    random.choice(REGIONES),
                ),
            )
        dia += timedelta(days=1)

    for categoria in categorias:
        for mes in [f"2026-{numero:02d}" for numero in range(1, 10)]:
            facturado = conexion.execute(
                "SELECT COALESCE(SUM(total), 0) FROM ventas WHERE categoria = ? AND substr(fecha, 1, 7) = ?",
                (categoria, mes),
            ).fetchone()[0]
            objetivo = round(facturado * random.uniform(0.85, 1.15), -4)
            conexion.execute(
                "INSERT INTO metas (categoria, mes, objetivo) VALUES (?, ?, ?)",
                (categoria, mes, objetivo),
            )
    conexion.commit()

    total_ventas = conexion.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
    facturacion = conexion.execute("SELECT SUM(total) FROM ventas").fetchone()[0]
    conexion.close()
    print(f"Base creada en {RUTA_BD}")
    print(f"Ventas: {total_ventas} registros | Facturación total: ARS {facturacion:,.2f}")


def embeddings_disponibles() -> bool:
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as respuesta:
            datos = json.load(respuesta)
    except Exception:
        return False
    modelos = [modelo.get("name", "") for modelo in datos.get("models", [])]
    return any(nombre.startswith("nomic-embed-text") for nombre in modelos)


def indexar_documentos() -> None:
    if not embeddings_disponibles():
        print("\nNo se indexaron los documentos: Ollama no está disponible o falta el modelo.")
        print("Ejecutá: ollama pull nomic-embed-text && python seed.py")
        return

    from asistente_ventas.tools.documentos import indexar_documento

    if RUTA_VECTORES.exists():
        shutil.rmtree(RUTA_VECTORES)

    print("\nIndexando documentos internos:")
    for archivo in sorted(RUTA_DOCUMENTOS.glob("*.md")):
        titulo = archivo.stem.replace("_", " ").capitalize()
        resultado = indexar_documento(titulo, archivo.read_text(encoding="utf-8"))
        estado = "OK" if resultado.get("ok") else f"ERROR: {resultado.get('error')}"
        print(f"  {archivo.name}: {estado}")


def main() -> None:
    crear_base()
    if "--sin-documentos" not in sys.argv:
        indexar_documentos()


if __name__ == "__main__":
    main()
