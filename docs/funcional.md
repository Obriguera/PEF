# Documentación funcional

## Propósito

Un usuario quiere saber qué película ver. El sistema mira qué películas calificaron los usuarios con **gustos
parecidos** a los suyos y le recomienda las que todavía no vio.

- **Algoritmo:** filtrado colaborativo *user-user* con **similitud coseno** entre los vectores de calificaciones.
- **Predicción:** para cada película no vista, el promedio de las calificaciones de los demás usuarios, ponderado por
  su similitud con quien pide la recomendación.
- **Salida:** el Top 5 de películas recomendadas.

## Quién lo usa

| Actor | Qué hace |
|---|---|
| Persona usuaria | Elige su usuario en la web, ve sus recomendaciones y el ranking de populares, y envía calificaciones. |
| Cliente de la API | Consume los endpoints REST desde otra aplicación (ver [API](api.md)). |
| Equipo de desarrollo | Corre los controles de calidad y mantiene el sistema (ver [Mantenimiento](mantenimiento.md)). |

## Funcionalidades

| # | Funcionalidad | Cómo se accede |
|---|---|---|
| F1 | Listar los usuarios disponibles | `GET /api/users` |
| F2 | Recomendar las 5 mejores películas no vistas para un usuario | `GET /api/recommend/{user_id}` |
| F3 | Ver las 5 películas más calificadas (ranking de popularidad) | `GET /api/popularity` |
| F4 | Agregar una calificación nueva | `POST /api/rate` |
| F5 | Demostrar el procesamiento eficiente de un archivo grande | `GET /api/large-files/process` |
| F6 | Usar todo lo anterior desde el navegador | `index.html` |

La interfaz web (`index.html`) ofrece un selector de usuarios con sus recomendaciones, el gráfico del ranking de
popularidad y un formulario para enviar una calificación.

## Reglas de negocio

**Recomendación**

- Solo se recomiendan películas que el usuario **todavía no calificó**.
- Una película entra en el cálculo solo si la calificó al menos un usuario con **similitud positiva** respecto de
  quien pide la recomendación. Si ninguno la calificó, no se recomienda.
- La similitud de un usuario consigo mismo se define como 0, y la de un usuario sin calificaciones con cualquier
  otro, también.
- Si hay empate en la predicción, desempata el identificador de la película, de modo que el resultado es siempre el
  mismo para los mismos datos.
- Pedir recomendaciones de un usuario que no existe devuelve **404**.

**Popularidad**

- La popularidad de una película es la **cantidad de calificaciones** que recibió, no su promedio.
- El resultado se guarda en memoria y se **invalida** cada vez que entra una calificación nueva.
- Una película sin título conocido se muestra como «Desconocida».

**Calificaciones**

- El puntaje debe estar entre **1 y 5**, y los identificadores de usuario y de película deben ser positivos. Si no,
  la API responde **422** y no agrega nada.
- Agregar una calificación **actualiza el ranking de popularidad, pero no recalcula las similitudes**: las
  recomendaciones reflejan los datos del arranque hasta que el servicio se reinicia.

## Datos de ejemplo

El sistema arranca con datos de demostración en memoria (`data_models.py`): **20 películas, 10 usuarios y 75
calificaciones**. Los usuarios (Ana, Beto, Carlos, Diana, Emma, Frank, Grace, Henry, Isabel y Jack) tienen gustos
diferenciados por género, para que las recomendaciones sean fáciles de interpretar.

## Requisitos no funcionales

| Requisito | Cómo se cumple |
|---|---|
| **Escala:** que comparar a todos los usuarios entre sí siga siendo viable con miles de usuarios | Similitud vectorizada en C/BLAS: ver [Diseño técnico](diseno-tecnico.md) y [Rendimiento](rendimiento.md) |
| **Resultados reproducibles:** los mismos datos dan las mismas recomendaciones | Desempate determinístico y pruebas de caracterización con comparación exacta: ver [Pruebas](pruebas.md) |
| **Memoria acotada** al procesar archivos grandes | Lotes y procesos con contrapresión: ver [Diseño técnico](diseno-tecnico.md) |
| **Instalación reproducible** | Dependencias con versión exacta y hash: ver [Instalación](instalacion.md) |
| **Calidad verificable en cada cambio** | Pipeline de CI: ver [Mantenimiento](mantenimiento.md) |

## Fuera de alcance

- No hay autenticación ni cuentas: la API es una demostración (ver [Seguridad](seguridad.md)).
- Los datos viven en memoria: no hay base de datos y todo se pierde al reiniciar.
- No hay un recomendador híbrido ni basado en contenido: solo filtrado colaborativo *user-user*.
