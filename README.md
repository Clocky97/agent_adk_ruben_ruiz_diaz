# Agente ADK — Asistente comercial de TecnoNova

Trabajo práctico de **Fundamentos de Agentes de Inteligencia Artificial**.

El proyecto implementa un agente de IA con **Python**, **Google Agent Development Kit (ADK)** y **LiteLLM** sobre un modelo servido por **Ollama**. El agente resuelve consultas comerciales reales: responde con datos de ventas, recupera políticas internas, busca información actual en internet y realiza cálculos. No es un chatbot que solo genera texto: decide qué herramienta usar, ejecuta la herramienta y arma la respuesta con el resultado obtenido.

## Problema que resuelve

TecnoNova es una distribuidora de tecnología que necesita responder preguntas como:

- *"¿Qué categoría facturó más en septiembre de 2026 y cuánto vendió?"*
- *"¿Cuál es el descuento por volumen para 25 unidades?"*
- *"¿Cuánto creció la categoría Redes respecto de agosto?"*
- *"¿A cuánto está el dólar hoy?"*
- *"Guardá que los envíos al sur demoran 7 días hábiles."*

La información está repartida entre una base SQLite de ventas, documentos internos y fuentes externas. El agente elige la herramienta adecuada para cada parte de la consulta, combina los resultados y valida los errores antes de responder.

## Componentes del agente

| Componente | Implementación |
| --- | --- |
| Modelo de IA | `LiteLlm` con un modelo de Ollama (`llama3.2:3b` por defecto) |
| Instrucciones | Rol, objetivo, reglas de derivación y restricciones en `asistente_ventas/agent.py` |
| Herramientas | 6 funciones con responsabilidades diferentes |
| Contexto | Esquema de la base y documentos internos indexados |
| Estado / memoria | Sesiones de ADK Web |
| Controles | Validación de SQL de solo lectura, límites de filas, expresiones y entradas |

## Herramientas

| Herramienta | Responsabilidad | Validaciones |
| --- | --- | --- |
| `consultar_ventas(sql)` | Ejecuta SQL de lectura sobre la base comercial | Solo `SELECT`/`WITH`, una sentencia, sin comentarios ni operaciones de escritura, máximo 50 filas, errores SQL explicados |
| `esquema_ventas()` | Devuelve tablas, columnas y valores disponibles | Respuesta estática y acotada |
| `buscar_en_documentos(consulta, cantidad)` | Búsqueda semántica (RAG) sobre políticas y manuales en Chroma | Consulta mínima, `cantidad` entre 1 y 10, colección existente, resultados vacíos informados |
| `indexar_documento(titulo, contenido)` | Guarda un documento nuevo en la base vectorial | Título de 3 a 120 caracteres, contenido de 40 a 20.000 caracteres, IDs determinísticos para no duplicar |
| `buscar_en_internet(consulta, max_resultados)` | Busca información actual con DuckDuckGo | Consulta mínima, máximo 10 resultados, errores de red controlados, listas vacías informadas |
| `calcular(expresion)` | Evalúa operaciones aritméticas de forma segura | Parser AST con operadores permitidos, sin nombres ni funciones, límites de tamaño y división por cero |

Cada herramienta devuelve un diccionario con `ok: true/false`. Ante un error o un resultado vacío, el agente lo explica y no inventa datos.

## Estructura del proyecto

```
agent_adk_ruben_ruiz_diaz/
├── asistente_ventas/
│   ├── __init__.py
│   ├── agent.py              # definición del agente, modelo e instrucciones
│   └── tools/
│       ├── __init__.py
│       ├── calculo.py        # calculadora segura
│       ├── documentos.py     # indexación y recuperación vectorial
│       ├── internet.py       # búsqueda web
│       ├── rutas.py          # rutas compartidas
│       └── ventas.py         # consultas SQL y esquema
├── documentos/               # políticas internas que se indexan
├── seed.py                   # crea la base y indexa los documentos
├── verificar_herramientas.py # prueba las herramientas y sus validaciones
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.11 o superior (probado con 3.12)
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/) activo en `http://localhost:11434`

## Instalación

```bash
uv venv --python 3.12 env
source env/bin/activate
uv pip install -r requirements.txt
```

En Windows la activación es:

```powershell
env\Scripts\activate
```

Descargá el modelo conversacional y el de embeddings:

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

Podés usar otro modelo de Ollama que soporte tool calling. Se cambia con la variable de entorno `MODELO_OLLAMA`, por ejemplo:

```bash
export MODELO_OLLAMA="ollama_chat/qwen2.5:7b"
```

## Preparar los datos

```bash
python seed.py
```

El script:

1. Genera `data/ventas.db` con 687 ventas de enero a septiembre de 2026 y las metas mensuales por categoría.
2. Indexa los archivos de `documentos/` en `vector_store/` con `nomic-embed-text`.

Si Ollama o el modelo de embeddings no están disponibles, la base se crea igual y el script indica cómo completar la indexación. Para crear solo la base:

```bash
python seed.py --sin-documentos
```

## Ejecutar el agente

```bash
adk web
```

Abrí `http://localhost:8000`, elegí el agente `asistente_ventas` y escribí la consulta.

También se puede usar la terminal:

```bash
adk run asistente_ventas
```

## Demostración del uso de herramientas

| Consulta | Herramienta esperada |
| --- | --- |
| `¿Qué categoría facturó más en septiembre de 2026 y cuánto?` | `consultar_ventas` |
| `¿Qué tablas tiene la base?` | `esquema_ventas` |
| `¿Cuál es el descuento por volumen para 30 unidades?` | `buscar_en_documentos` |
| `¿Cuánto creció Redes de agosto a septiembre?` | `consultar_ventas` + `calcular` |
| `Guardá que los envíos al sur demoran 7 días hábiles` | `indexar_documento` |
| `¿A cuánto está el dólar hoy?` | `buscar_en_internet` |

En la interfaz web de ADK se ven los eventos de cada llamada: qué herramienta se invocó, con qué argumentos y qué devolvió.

## Validación y manejo de errores

`verificar_herramientas.py` ejecuta casos válidos e inválidos de todas las herramientas sin necesidad de un modelo:

```bash
python verificar_herramientas.py
```

Casos incluidos:

- Consulta SQL correcta y consulta a una categoría inexistente (resultado vacío).
- Intento de `DELETE` y consulta vacía (rechazados).
- Cálculo válido, división por cero e intento de ejecutar código (rechazados).
- Búsqueda documental válida y consulta demasiado corta.
- Indexación con contenido inválido.
- Búsqueda en internet con resultados y con errores de red controlados.

Todas las funciones capturan sus excepciones y devuelven `{"ok": false, "error": ...}`, de modo que el agente pueda explicar el problema al usuario en lugar de interrumpirse.

## Solución de problemas

- **`ModuleNotFoundError: google.adk`**: activá el entorno virtual antes de ejecutar `adk`.
- **Error de conexión con Ollama**: verificá `ollama list` y que el servicio esté corriendo.
- **La búsqueda documental falla**: falta `nomic-embed-text` o se ejecutó `seed.py` sin Ollama. Ejecutá `ollama pull nomic-embed-text` y luego `python seed.py`.
- **La base no existe**: ejecutá `python seed.py`.
- **El modelo no llama herramientas**: usá un modelo con soporte de function calling, por ejemplo `llama3.2:3b`, `qwen2.5:7b` o `gemma3:4b`.

## Autor

Ruben Alejandro Ruiz Diaz — Fundamentos de Agentes de Inteligencia Artificial.
