# API REST

Todos los endpoints cuelgan de `/api`, devuelven JSON y no requieren autenticación (ver [Seguridad](seguridad.md)).
FastAPI genera además la documentación interactiva en `/docs` y el esquema OpenAPI en `/openapi.json`. La referencia
de las funciones internas está en [Referencia del código](referencia.md).

| Método | Ruta | Descripción | Errores |
|---|---|---|---|
| `GET` | `/api/users` | Lista de usuarios (para el selector de la web) | — |
| `GET` | `/api/recommend/{user_id}` | Top 5 de películas recomendadas | 404 si el usuario no existe |
| `GET` | `/api/popularity` | Top 5 de películas más calificadas, con caché | — |
| `POST` | `/api/rate` | Agrega una calificación e invalida el caché | 422 si los datos no son válidos |
| `GET` | `/api/large-files/process` | Demostración del procesamiento de un CSV grande | 422 si `records` está fuera de rango |

Los ejemplos de abajo son respuestas reales de la aplicación con los datos de demostración.

## `GET /api/users`

```bash
curl http://localhost:8000/api/users
```

```json
{"users": [{"user_id": 101, "name": "Ana"}, {"user_id": 102, "name": "Beto"}, "..."]}
```

## `GET /api/recommend/{user_id}`

```bash
curl http://localhost:8000/api/recommend/101
```

```json
{
  "user_id": 101,
  "recommendations": ["The Matrix", "Parasite", "Forrest Gump", "The Shawshank Redemption", "Joker"]
}
```

Las recomendaciones están ordenadas de la mejor a la peor predicción. Con un usuario inexistente:

```json
{"detail": "Usuario no encontrado"}
```

(HTTP 404.)

## `GET /api/popularity`

```bash
curl http://localhost:8000/api/popularity
```

```json
{
  "popular_movies": [
    {"title": "Joker 2", "count": 9},
    {"title": "Interstellar", "count": 5},
    {"title": "Inception", "count": 5},
    {"title": "The Dark Knight", "count": 5},
    {"title": "La La Land", "count": 4}
  ]
}
```

`count` es la cantidad de calificaciones recibidas, no el promedio. El resultado se guarda en memoria hasta que
entra una calificación nueva.

## `POST /api/rate`

| Campo | Tipo | Restricción |
|---|---|---|
| `user_id` | entero | mayor que 0 |
| `movie_id` | entero | mayor que 0 |
| `rating` | número | entre 1 y 5, ambos incluidos |

```bash
curl -X POST http://localhost:8000/api/rate \
  -H "Content-Type: application/json" \
  -d '{"user_id": 101, "movie_id": 7, "rating": 4.5}'
```

```json
{"mensaje": "Valoración agregada exitosamente. Caché de popularidad invalidado."}
```

Con un puntaje fuera de rango, la API responde 422 y **no agrega nada**:

```json
{
  "detail": [
    {"type": "less_than_equal", "loc": ["body", "rating"], "msg": "Input should be less than or equal to 5",
     "input": 9, "ctx": {"le": 5.0}}
  ]
}
```

!!! note "Qué cambia y qué no"
    Una calificación nueva actualiza el ranking de popularidad, pero **no recalcula las similitudes**: las
    recomendaciones reflejan los datos del arranque hasta que se reinicia el servicio.

## `GET /api/large-files/process`

Demuestra el procesamiento de un archivo grande: genera un CSV de calificaciones (si no existe), lo procesa por
lotes en varios procesos y escribe un CSV con el promedio por película. Ver
[Diseño técnico](diseno-tecnico.md#5-archivos-grandes-buffer-lotes-y-procesos).

| Parámetro | Tipo | Por defecto | Restricción |
|---|---|---|---|
| `records` | entero | 200000 | entre 1 y 1.000.000 |

```bash
curl "http://localhost:8000/api/large-files/process?records=1000"
```

```json
{
  "status": "success",
  "records_processed": 1000,
  "movies_aggregated": 633,
  "source_file": "massive_ratings_sample.csv",
  "output_file": "massive_ratings_aggregated.csv",
  "techniques": [
    "Buffering (64 KB I/O)",
    "Batching (20.000 filas por chunk en memoria)",
    "Procesamiento Paralelo (ProcessPoolExecutor)"
  ]
}
```

- `records_processed` es lo que **realmente se procesó**: si el CSV ya existía con otro tamaño, se reutiliza y esta
  cifra lo refleja, no el valor pedido en `records`.
- Los archivos se escriben en el **directorio actual** del servicio, con nombres fijos.
- Un valor fuera de rango (por ejemplo `records=0`) responde 422 y no crea ningún archivo.

## Códigos de respuesta

| Código | Cuándo |
|---|---|
| 200 | La operación se realizó. |
| 404 | El usuario pedido no existe. |
| 422 | Los datos de entrada no cumplen las restricciones (rango, tipo o valor requerido). |
