# PEF · Motor de recomendaciones de películas

**Programación Eficiente · Universidad Blas Pascal** · Octavio Briguera y Ricardo Lagoria

Un sistema de recomendación de películas por filtrado colaborativo, optimizado en tres etapas y medido en cada una
con perfiladores. Esta documentación describe la **versión optimizada** (`Ver-Optimizada/`), que es la que evalúa el
Parcial 3.

| | Versión Base | Versión Optimizada |
|---|---:|---:|
| Tiempo del benchmark (Scalene) | 171,5 s | **20,3 s** (8,5× más rápido) |
| Memoria pico (Scalene) | 230,5 MB | **36,4 MB** (−84 %) |
| Cálculo de similitudes | ~15–20 s | **0,06 s** |

Los números salen de `scalene-profile.json` en cada carpeta de versión; el detalle y sus límites están en
[Rendimiento](rendimiento.md).

## Cómo está organizada

| Sección | Qué responde |
|---|---|
| [Funcional](funcional.md) | ¿Qué hace el sistema, para quién y con qué reglas? |
| [Arquitectura](arquitectura.md) | ¿De qué piezas se compone y cómo se hablan? (con diagrama de componentes) |
| [Instalación](instalacion.md) | ¿Cómo lo dejo funcionando, de forma reproducible? |
| [Diseño técnico](diseno-tecnico.md) | ¿Por qué está hecho así y qué alternativas se descartaron? |
| [API](api.md) | ¿Qué endpoints expone y qué devuelven? ([referencia del código](referencia.md)) |
| [Pruebas](pruebas.md) | ¿Cómo sé que sigue funcionando? |
| [Rendimiento](rendimiento.md) | ¿Qué tan rápido es, cómo se mide y cómo se evita empeorarlo? |
| [Seguridad](seguridad.md) | ¿Qué se controla, qué bloquea un cambio y qué riesgos se aceptan? |
| [Mantenimiento](mantenimiento.md) | ¿Cómo corro los controles del CI en local y qué hago cuando uno falla? |

## Las tres versiones

Las tres exponen la misma interfaz (mismos módulos y funciones), así que el «antes y después» es un cambio de
implementación y no una reescritura, y cada etapa se mide con el mismo benchmark.

- **Base:** deliberadamente ingenua. Es el grupo de control del experimento.
- **Eficiente (Parcial 1):** sets, heap para el Top N, diccionarios O(1), caché de popularidad y una API FastAPI.
- **Optimizada (Parcial 2 y 3):** matriz NumPy en `float32`, similitud calculada en C/BLAS, archivos grandes con
  buffer, lotes y procesos, y, desde el Parcial 3, un pipeline de calidad que corre en cada cambio.

!!! note "Qué cubren los controles de calidad"
    El CI y los controles de calidad se aplican **solo a `Ver-Optimizada/`**. Base y Eficiente se conservan sin tocar
    para poder comparar.

## Colaborar

Esta documentación vive en el repositorio, junto al código. Cada página tiene un botón de edición que abre una
propuesta de cambio: los cambios pasan por revisión y por el CI antes de llegar a `master`, igual que el código.
La guía para contribuir está en [Mantenimiento](mantenimiento.md).
