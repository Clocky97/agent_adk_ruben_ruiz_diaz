import ast
import operator

OPERADORES = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

LIMITE_VALOR = 10**15
LIMITE_EXPONENTE = 12


def _evaluar(nodo):
    if isinstance(nodo, ast.Expression):
        return _evaluar(nodo.body)
    if isinstance(nodo, ast.Constant):
        if isinstance(nodo.value, bool) or not isinstance(nodo.value, (int, float)):
            raise ValueError("Solo se permiten números.")
        return nodo.value
    if isinstance(nodo, ast.UnaryOp) and type(nodo.op) in OPERADORES:
        return OPERADORES[type(nodo.op)](_evaluar(nodo.operand))
    if isinstance(nodo, ast.BinOp) and type(nodo.op) in OPERADORES:
        izquierda = _evaluar(nodo.left)
        derecha = _evaluar(nodo.right)
        if isinstance(nodo.op, ast.Pow) and abs(derecha) > LIMITE_EXPONENTE:
            raise ValueError("El exponente es demasiado grande.")
        return OPERADORES[type(nodo.op)](izquierda, derecha)
    raise ValueError("La expresión contiene operaciones no permitidas.")


def calcular(expresion: str) -> dict:
    """Calcula una expresión aritmética y devuelve el resultado numérico.

    Usala para variaciones porcentuales, márgenes, promedios, totales con
    descuento o cualquier operación sobre los datos obtenidos de otras
    herramientas. No reemplaza los cálculos mentales del modelo.

    Args:
        expresion: Operación con números y los operadores +, -, *, /, //, %,
            ** y paréntesis. Por ejemplo: "(1890000 - 1250000) / 1250000 * 100".
    """
    if not isinstance(expresion, str) or not expresion.strip():
        return {"ok": False, "error": "La expresión está vacía."}
    if len(expresion) > 300:
        return {"ok": False, "error": "La expresión supera los 300 caracteres."}

    try:
        arbol = ast.parse(expresion.strip(), mode="eval")
        resultado = _evaluar(arbol)
    except ZeroDivisionError:
        return {"ok": False, "error": "No se puede dividir por cero."}
    except (SyntaxError, ValueError, TypeError) as exc:
        return {"ok": False, "error": f"Expresión inválida: {exc}"}

    if not isinstance(resultado, (int, float)):
        return {"ok": False, "error": "El resultado no es un número."}
    if abs(resultado) > LIMITE_VALOR:
        return {"ok": False, "error": "El resultado es demasiado grande."}

    return {"ok": True, "expresion": expresion.strip(), "resultado": round(resultado, 4)}
