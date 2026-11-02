# Política de seguridad

Este documento describe cómo se controla la seguridad de `Ver-Optimizada/` (la versión que evalúa el Parcial 3),
qué hallazgos bloquean un cambio, qué excepciones están registradas y qué riesgos se aceptan a propósito.
`Ver-Base/` y `Ver-Eficiente/` son versiones históricas, ingenuas a propósito (grupo de control del experimento):
no pasan por los controles de código, pero el escaneo de secretos recorre todo el repositorio.

## Cómo reportar una vulnerabilidad

Usá **Security → Report a vulnerability** en la página del repositorio (aviso privado de GitHub), para que el
detalle no quede público antes de corregirlo. Esa opción debe estar activada en *Settings → Code security*
(ver [Configuración pendiente del dueño del repositorio](#configuración-pendiente-del-dueño-del-repositorio)).
Es un proyecto académico sin soporte de versiones: se corrige en `master`.

## Controles

Cada control tiene herramienta, comando reproducible, reporte y criterio de rechazo. Los comandos se ejecutan
desde `Ver-Optimizada/`. El pipeline de CI (Fase 4 del plan, todavía no implementado) llamará a las mismas tareas;
hoy solo CodeQL corre en GitHub.

| Control | Herramienta | Comando | Reporte | Rechaza si… |
|---|---|---|---|---|
| Código inseguro (SAST) | Bandit | `python tasks.py sast` | `reports/bandit.sarif` (SARIF 2.1.0) | hay un hallazgo de severidad **media o alta** con confianza **media o alta** |
| Código inseguro (flujo de datos) | CodeQL | workflow `.github/workflows/codeql.yml` | pestaña *Security → Code scanning* | hay alertas de severidad alta o crítica (ver nota) |
| Secretos | Gitleaks | `python tasks.py secrets` | `reports/gitleaks.sarif` | hay **cualquier** hallazgo, sin umbral |
| Dependencias vulnerables | pip-audit | `python tasks.py audit` | `reports/pip-audit-*.json` | hay **cualquier** vulnerabilidad conocida sin excepción vigente |
| Actualizaciones | Dependabot | `.github/dependabot.yml` | pull requests automáticos | no bloquea: propone cambios |

Nota sobre CodeQL: el workflow sube los resultados a *Code scanning*, pero que una alerta **bloquee** el merge
depende de una regla de protección de rama que solo puede configurar el dueño del repositorio.

### Política de bloqueo por severidad

| Severidad | Qué pasa |
|---|---|
| Alta o crítica | Bloquea siempre. No se mergea hasta corregirlo o registrar una excepción con motivo y vencimiento. |
| Media | Bloquea en Bandit si la confianza es media o alta. En pip-audit, toda vulnerabilidad bloquea (no se distingue severidad). |
| Baja | No bloquea, pero queda en el reporte. Si es un falso positivo, se registra más abajo. |
| Secretos | Bloquea cualquier hallazgo: una credencial expuesta se considera comprometida aunque se borre en un commit posterior; hay que **rotarla**. |

## Cómo correr los controles

`sast` y `audit` usan las dependencias del proyecto (`python tasks.py install`). `secrets` necesita el binario de
**Gitleaks**, que no es un paquete de Python: descargalo de <https://github.com/gitleaks/gitleaks/releases>,
verificá su checksum con el archivo `*_checksums.txt` de la misma versión y ponelo en el `PATH`.

```bash
python tasks.py sast secrets audit
```

El análisis de Gitleaks recorre el historial de git completo, así que hay que trabajar sobre un clon completo
(no `--depth 1`); en el CI futuro, con `fetch-depth: 0`.

## Registro de falsos positivos y excepciones

Toda excepción se decide con motivo, fecha y un criterio de revisión. Las de pip-audit llevan además vencimiento:
al vencer, `python tasks.py audit` falla hasta que se revisen (`AUDIT_EXCEPTIONS` en `tasks.py`).

| ID | Herramienta | Dónde | Tipo | Motivo | Decidido | Revisar si… |
|---|---|---|---|---|---|---|
| B311 (×3) | Bandit | `large_file_handler.py`, `generate_large_ratings_csv` | Falso positivo | `random` genera calificaciones **sintéticas** para un CSV de prueba. No hay ninguna función de seguridad (ni claves, ni tokens, ni sorteos con valor). Marcado con `# nosec B311`. | 2026-11-02 | `random` se use para algo que no sean datos de prueba |
| — | pip-audit | `requirements*.txt` | — | **Sin excepciones vigentes.** | 2026-11-02 | — |
| — | Gitleaks | todo el historial | — | **Sin hallazgos ni excepciones** (21 commits con cambios escaneados). | 2026-11-02 | — |

## Modelo de amenazas

La aplicación es una demostración académica: una API FastAPI con datos en memoria, sin base de datos, sin cuentas de
usuario y sin datos personales reales.

### Mitigado en la Fase 3

| Amenaza | Mitigación |
|---|---|
| Agotamiento de disco y CPU: `GET /api/large-files/process?records=N` aceptaba cualquier `N` y generaba un CSV de ese tamaño | `records` debe estar entre 1 y 1.000.000 (422 si no); no se crea ningún archivo |
| Datos falsos: `POST /api/rate` aceptaba cualquier puntaje (`1e308`, negativos) y alteraba el ranking | `rating` entre 1 y 5, `user_id` y `movie_id` positivos (422 si no) |
| Errores internos: un usuario inexistente en `/api/recommend/{id}` terminaba en HTTP 500 | Responde 404 |
| Procesos hijos trabados: `fork()` desde un proceso con hilos | `spawn` en el `ProcessPoolExecutor` (Fase 2) |
| Memoria sin tope en el procesamiento paralelo | Contrapresión: `2 × max_workers` lotes en vuelo (Fase 2) |
| Secretos en el repositorio | Gitleaks sobre todo el historial |
| Dependencias manipuladas o vulnerables | Locks con hashes (`--require-hashes`) y pip-audit; acciones de GitHub fijadas por SHA de commit |

### Riesgos aceptados

No se corrigen porque exceden el alcance de una demostración sin autenticación; deben conocerse antes de exponer
la API fuera de una red local.

| Riesgo | Por qué se acepta |
|---|---|
| No hay autenticación ni autorización: cualquiera puede llamar a todos los endpoints | La API es una demo local |
| `POST /api/rate` no tiene límite de tasa: se puede llenar la memoria con calificaciones | Los datos viven solo en memoria y se pierden al reiniciar |
| CORS abierto (`allow_origins=["*"]`) | La API no usa cookies ni credenciales, así que no se puede abusar de una sesión ajena |
| `GET /api/large-files/process` tiene efectos secundarios (escribe archivos) y usa nombres fijos en el directorio actual | Es la demostración del Punto 3. Dos pedidos simultáneos pueden pisarse el archivo |
| `POST /api/rate` agrega la calificación al ranking de popularidad, pero no recalcula las similitudes | Comportamiento heredado del Parcial 1 |

### Lo que estos controles no cubren

- **No hay pruebas dinámicas (DAST) ni pentest.** Todo el análisis es estático.
- Las herramientas detectan patrones conocidos: un secreto con formato inusual o una vulnerabilidad de lógica de
  negocio pasan desapercibidos.
- Que no haya hallazgos prueba que las reglas actuales no encontraron nada, no que el código sea seguro.

## Configuración pendiente del dueño del repositorio

Estos ajustes están en *Settings* de GitHub y no se pueden hacer desde el código:

- **Code security → Dependabot alerts** y **Dependabot security updates**: avisos por dependencias vulnerables.
- **Code security → Secret scanning** y **Push protection**: bloquea el push de credenciales conocidas.
- **Code security → Private vulnerability reporting**: habilita el aviso privado de la sección inicial.
- **Branches → Branch protection** sobre `master`: exigir los controles del CI y el resultado de Code scanning.

## Estado de verificación

Verificado localmente: Bandit, Gitleaks y pip-audit, con casos positivos y negativos (un token falso con formato de
GitHub en un commit ya borrado, `shell=True` y `pickle.loads`, y una dependencia con 12 avisos de vulnerabilidad).

**Todavía no ejecutado por GitHub:** el workflow de CodeQL y la configuración de Dependabot. Se validó su estructura
(SHAs de commit resueltos desde GitHub, permisos mínimos), pero la primera ejecución real puede revelar ajustes.
Dependabot tiene un riesgo conocido con los locks con hashes, explicado en `.github/dependabot.yml`.
