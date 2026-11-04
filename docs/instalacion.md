# Instalación

La instalación es **reproducible**: las dependencias están fijadas con versión exacta y hash, y `pip` rechaza
cualquier paquete que no coincida.

## Requisitos

| Requisito | Detalle |
|---|---|
| Python | 3.11 o superior. Se probó con 3.11, 3.12 y 3.13. |
| Git | Para clonar el repositorio. El análisis de secretos necesita el historial completo. |
| Sistema operativo | Linux, macOS o Windows. Los locks son multiplataforma, pero el CI solo corre en Linux. |
| `uv` (opcional) | Solo para regenerar los locks con `python tasks.py lock`. |

## Pasos

```bash
git clone https://github.com/RicLagoria/PEF.git
cd PEF/Ver-Optimizada
```

=== "Linux / macOS"

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install --require-hashes -r requirements-dev.txt
    ```

=== "Windows (PowerShell)"

    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install --require-hashes -r requirements-dev.txt
    ```

Para **solo ejecutar la API**, sin las herramientas de desarrollo, alcanza con
`pip install --require-hashes -r requirements.txt`.

## Levantar la API y la web

```bash
uvicorn main:app --reload --port 8000
```

- La API queda en `http://localhost:8000` y la documentación interactiva que genera FastAPI, en
  `http://localhost:8000/docs`.
- La interfaz web se abre con `index.html` en el navegador y consume la API en `http://localhost:8000/api`.

## Configuración

El sistema **no usa variables de entorno ni archivos de configuración propios**: sus parámetros son constantes en el
código, y las herramientas de calidad se configuran en `pyproject.toml`.

| Qué | Dónde | Valor |
|---|---|---|
| Puerto y servidor | Argumentos de `uvicorn` | `--port 8000` (ver arriba) |
| URL de la API que usa la web | `API_BASE_URL` en `index.html` | `http://localhost:8000/api` |
| Orígenes permitidos (CORS) | `main.py` | todos (`*`): ver [Seguridad](seguridad.md) |
| Límites de entrada | `MAX_RECORDS`, `MIN_RATING`, `MAX_RATING` en `main.py` | 1.000.000 registros; puntaje de 1 a 5 |
| Buffer, lote y lotes en vuelo | `DEFAULT_BUFFER_SIZE`, `DEFAULT_BATCH_SIZE` y `MAX_IN_FLIGHT_FACTOR` en `large_file_handler.py` | 64 KB, 25.000 filas, 2 por proceso |
| Pruebas, cobertura, estilo, tipos y seguridad | `pyproject.toml` | umbral de cobertura 80 %, línea de 119 caracteres, complejidad máxima A, 30 sentencias y 5 parámetros por función |

Los archivos `massive_ratings_*.csv` que generan la demostración y el endpoint de archivos grandes se escriben en el
**directorio actual** y están en el `.gitignore`.

## Verificar la instalación

```bash
python tasks.py ci
```

Corre todos los controles bloqueantes (estilo, tipos, complejidad, seguridad, pruebas con cobertura, dependencias y
documentación). Si termina sin errores, el entorno está bien. `python tasks.py` sin argumentos lista todas las
tareas disponibles.

## Dependencias fijadas

| Archivo | Contenido | Se edita a mano |
|---|---|---|
| `requirements.in` | Dependencias directas de la API | Sí |
| `requirements-dev.in` | Herramientas de pruebas, calidad, seguridad, rendimiento y documentación | Sí |
| `requirements.txt` | Lock de ejecución, con hashes | No: lo genera `python tasks.py lock` |
| `requirements-dev.txt` | Lock de desarrollo, con hashes | No: lo genera `python tasks.py lock` |

Los locks se generan con `uv pip compile --universal --python-version 3.11 --generate-hashes`, así que valen para
cualquier plataforma con Python 3.11 o superior. Para actualizar una dependencia, se edita el archivo `.in`, se corre
`python tasks.py lock` y se vuelven a pasar los controles (ver [Mantenimiento](mantenimiento.md)).

## Gitleaks (opcional, para el control de secretos)

`python tasks.py secrets` necesita el binario de **Gitleaks**, que no es un paquete de Python. Descargalo de la
[página de releases](https://github.com/gitleaks/gitleaks/releases), verificá su checksum con el archivo
`*_checksums.txt` de la misma versión y dejalo en el `PATH`. El CI instala la versión 8.30.1 con un checksum fijado
en el workflow.

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `'gitleaks' no está instalado` | El binario no está en el `PATH` | Instalarlo como se explica arriba. |
| `AttributeError: ... _nodeid` al correr benchmarks | `pytest-benchmark` anterior a la 5.3.1 con `pytest` 9.2 o superior | Instalar desde el lock (`pip install --require-hashes -r requirements-dev.txt`), que ya exige la 5.3.1. |
| `BrokenProcessPool` o `FileNotFoundError: ... <stdin>` al usar `process_large_file_parallel` | El procesamiento paralelo usa `spawn`, que vuelve a importar el script principal en cada proceso hijo | Llamarlo desde un archivo `.py` con el guard `if __name__ == "__main__":`, no desde `python -` ni una consola interactiva. |
| `No se encontró el archivo ...` en `stream_ratings_in_batches` | La ruta del CSV no existe | Generarlo antes con `generate_large_ratings_csv`. |
| `python tasks.py lock` falla | Falta `uv` | Instalarlo (<https://docs.astral.sh/uv/>). |
