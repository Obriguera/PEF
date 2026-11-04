# Mantenimiento

## Flujo de trabajo

1. Crear una rama desde `master`.
2. Hacer commits chicos, uno por cambio lógico, con un mensaje que explique el **porqué**.
3. Correr `python tasks.py ci` en local antes de subir.
4. Abrir un *pull request* hacia `master`. El CI corre solo; el check **Resultado** resume todos los controles.
5. Con el CI en verde y la revisión hecha, hacer el merge.
6. Etiquetar el estado como `parcial3-faseN` para poder volver a él.

## Correr en local los mismos controles que el CI

Cada job del CI llama a una tarea de `tasks.py`, desde `Ver-Optimizada/` con el entorno instalado
(ver [Instalación](instalacion.md)). Lo que falla en el CI se reproduce con el mismo comando.

| Job del CI | Comando | Rechaza si… |
|---|---|---|
| Calidad estática | `python tasks.py lint typecheck complexity sast` | error de Ruff o mypy, función peor que rango A o con más de 30 sentencias o 5 parámetros, hallazgo de Bandit de severidad y confianza medias o altas |
| Secretos | `python tasks.py secrets` | cualquier hallazgo en el historial |
| Pruebas | `python tasks.py test` | falla un test o la cobertura baja de 80 % |
| Dependencias | `python tasks.py audit` | vulnerabilidad conocida sin excepción vigente |
| Documentación | `python tasks.py docs-sphinx docs-mkdocs docs-links` | cualquier advertencia, enlace o ancla internos rotos, o un enlace externo roto (404, 410 o dominio inexistente) |
| Benchmarks | `BENCH_BASE_SHA=<commit> python tasks.py bench-vs-base` | el mínimo de algún benchmark empeora más de 25 % |
| Perfilado | `python tasks.py profile` | no bloquea: se aprueba si genera los reportes, y corre después de las pruebas |

`python tasks.py ci` corre todo lo bloqueante, salvo los benchmarks y el análisis de secretos, que dependen de la
máquina y de un binario externo. `python tasks.py` lista todas las tareas.

Los reportes quedan en `Ver-Optimizada/reports/` (SARIF, JSON, XML y HTML) y, en el CI, como artefactos de cada
ejecución. Cada job escribe además un resumen en la página de la ejecución.

## Si un control falla

| Falla | Qué hacer |
|---|---|
| **Ruff** | `python tasks.py format-code` corrige estilo y orden de imports. El resto se corrige a mano. |
| **mypy** | Anotar los tipos del código que falta. El núcleo exige funciones completamente anotadas. |
| **Xenon** (función peor que A) o **tamaño** (más de 30 sentencias o 5 parámetros) | Refactorizar: extraer funciones auxiliares. **Antes**, escribir una prueba de caracterización que fije el comportamiento, y después de refactorizar medir el rendimiento: un refactor limpio puede ser más lento. |
| **Bandit** | Corregir el patrón inseguro. Si es un falso positivo, marcar la línea con `# nosec BXXX` y registrarlo en [Seguridad](seguridad.md#registro-de-falsos-positivos-y-excepciones). |
| **Gitleaks** | Una credencial expuesta se considera comprometida aunque se borre en un commit posterior: hay que **rotarla**. Si es un falso positivo, agregar una excepción en la configuración de Gitleaks. |
| **pytest** | Leer qué test falla. Los de caracterización y los de memoria fallan por motivos específicos: ver abajo. |
| **Golden master** | Si cambió el orden de las sumas de `float` (por ejemplo, un `sum()`), el resultado cambia en el último bit. Si el cambio es intencional, regenerar con `python tests/golden.py` y justificarlo en el commit. |
| **Cobertura < 80 %** | Agregar tests de lo que se agregó o cambió. La tabla de `term-missing` indica las líneas. |
| **pip-audit** | Actualizar la dependencia: subir el piso en el archivo `.in` y correr `python tasks.py lock`. Solo si no hay arreglo, agregar una excepción con motivo y vencimiento en `AUDIT_EXCEPTIONS` (en `tasks.py`) y en el registro de [Seguridad](seguridad.md). |
| **Sphinx o MkDocs** | Corregir el docstring, el enlace o el ancla que indica el mensaje. Los builds fallan ante **cualquier** advertencia. |
| **Enlaces externos** | Corregir o quitar la URL. Solo un 404, un 410 o un dominio inexistente rechazan; un 403, un 429 o un timeout quedan como «no verificables» (muchos sitios bloquean a los robots) y no fallan el control. |
| **Benchmarks** | Reproducir con `bench-vs-base`. Si la lentitud es real, optimizar; si es intencional, mergear sabiéndolo (no hay una línea base guardada que actualizar). Si se cambió un benchmark, no pasa nada: ambos lados se miden con la definición actual. |
| **Resultado** | Es solo el resumen. Mirar qué job de la lista falló. |

## Tareas periódicas

| Tarea | Cómo |
|---|---|
| Actualizar dependencias | Subir el piso en el `.in`, correr `python tasks.py lock`, `python tasks.py install` y `python tasks.py ci`. Dependabot propone actualizaciones cada semana, pero puede dejar los hashes sin actualizar: el CI las rechaza de forma segura y se rehacen con el procedimiento de arriba. |
| Revisar excepciones de seguridad | Las de pip-audit vencen solas y hacen fallar la auditoría. Revisar también el registro de [Seguridad](seguridad.md). |
| Sumar una versión de Python | Agregarla a la matriz del job de pruebas en `.github/workflows/ci.yml`, **después** de instalarla y correr la suite en local. |
| Cambiar de máquina para medir | `python tasks.py bench-save` guarda una línea base propia; la versionada es de otro equipo. |

## Documentación

```bash
python tasks.py docs-mkdocs     # construye el sitio en ../site y falla ante cualquier advertencia
python tasks.py docs-serve      # lo sirve en http://127.0.0.1:8000 con recarga automática
```

- Las páginas están en `docs/` (Markdown). La referencia del código se genera sola de los docstrings.
- La página de [Seguridad](seguridad.md) incluye `SECURITY.md`, que debe vivir en la raíz para que GitHub lo muestre:
  se edita ese archivo, no la página.
- Los enlaces y anclas **internos** se validan en cada build (`docs-mkdocs`), y los **externos** con `docs-links`.
- Se publica en GitHub Pages con `.github/workflows/docs.yml` al hacer merge en `master`.

## Configuración que debe hacer el dueño del repositorio

Estos ajustes están en *Settings* de GitHub y no se pueden hacer desde el código:

| Ajuste | Para qué |
|---|---|
| *Branches*: proteger `master` y exigir el check **Resultado** | Sin esta regla el CI avisa pero no impide el merge. |
| *Pages*: origen «GitHub Actions», y la variable de repositorio `PUBLISH_DOCS` en `true` | Publicar la documentación. |
| *Code security*: Dependabot alerts, secret scanning y push protection | Ver [Seguridad](seguridad.md). |

## Riesgos conocidos

- **Material for MkDocs llega a su fin de vida el 5 de mayo de 2027** (lo anuncia el propio tema en cada build); su
  sucesor mantenido por el mismo equipo es Zensical, que declara compatibilidad con la configuración de MkDocs.
  Hasta esa fecha sigue recibiendo correcciones críticas y de seguridad.
- Los diagramas Mermaid se dibujan en el navegador con un script que el tema carga desde `unpkg.com` (ver
  [Seguridad](seguridad.md)). El build **no valida** la sintaxis de los diagramas: hay que mirarlos al cambiarlos.

## Trampas conocidas

- Los scripts que llaman a `process_large_file_parallel` necesitan el guard `if __name__ == "__main__":` (usa `spawn`).
- `POST /api/rate` modifica datos globales: los tests de la API los restauran con un *fixture*, y los nuevos deben
  hacerlo también.
- `coverage` no mide los subprocesos: el *worker* se prueba llamándolo directamente.
- Las líneas base de `metrics/benchmarks/` valen solo para la plataforma y la versión de Python donde se midieron.
- `pytest-benchmark` debe ser 5.3.1 o superior con `pytest` 9.2 o superior.
