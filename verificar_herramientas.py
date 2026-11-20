import json
import sys

from asistente_ventas.tools import (
    buscar_en_documentos,
    buscar_en_internet,
    calcular,
    consultar_ventas,
    esquema_ventas,
    indexar_documento,
)

CASOS = [
    ("consultar_ventas", consultar_ventas, ("SELECT categoria, ROUND(SUM(total), 2) AS facturado FROM ventas WHERE fecha LIKE '2026-09%' GROUP BY categoria ORDER BY facturado DESC",)),
    ("consultar_ventas", consultar_ventas, ("SELECT * FROM ventas WHERE categoria = 'Impresoras'",)),
    ("consultar_ventas", consultar_ventas, ("DELETE FROM ventas",)),
    ("consultar_ventas", consultar_ventas, ("",)),
    ("esquema_ventas", esquema_ventas, ()),
    ("calcular", calcular, ("(1890000 - 1250000) / 1250000 * 100",)),
    ("calcular", calcular, ("10 / 0",)),
    ("calcular", calcular, ("__import__('os').system('ls')",)),
    ("buscar_en_documentos", buscar_en_documentos, ("descuento por volumen",)),
    ("buscar_en_documentos", buscar_en_documentos, ("x",)),
    ("indexar_documento", indexar_documento, ("Nota de prueba", "corto")),
    ("buscar_en_internet", buscar_en_internet, ("precio del dolar hoy Argentina", 3)),
]


def main() -> None:
    for nombre, funcion, argumentos in CASOS:
        print(f"\n=== {nombre}{argumentos} ===")
        try:
            resultado = funcion(*argumentos)
        except Exception as exc:
            print(f"EXCEPCIÓN NO CONTROLADA: {exc}")
            sys.exit(1)
        print(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
