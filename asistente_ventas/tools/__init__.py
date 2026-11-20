from .calculo import calcular
from .documentos import buscar_en_documentos, indexar_documento
from .internet import buscar_en_internet
from .ventas import consultar_ventas, esquema_ventas

__all__ = [
    "buscar_en_documentos",
    "buscar_en_internet",
    "calcular",
    "consultar_ventas",
    "esquema_ventas",
    "indexar_documento",
]
