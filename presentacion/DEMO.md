# Demo del pipeline (5 minutos)

**Idea:** dos pull requests abiertos a la vez. Uno rompe un control y el pipeline lo rechaza; el otro pasa todo y se
publica en GitHub Pages. Los dos corren **en paralelo** y se abren **antes** de presentar, así que no hay que esperar nada.

| Rama | Contiene | Resultado esperado |
|---|---|---|
| `demo/con-error` | una nota en la documentación **y** una función con 7 parámetros (el límite es 5) | **Calidad estática** en rojo en ≈ 45 s; **Resultado** en rojo; merge bloqueado |
| `demo/sin-error` | solo la nota en la documentación | los 10 jobs en verde en ≈ 2,5 min; **Resultado** en verde |

Reparto sugerido: una persona narra y otra maneja el navegador.

---

## Antes de presentar (≈ 15 minutos antes)

Hace falta tener el repositorio clonado y poder hacer `git push` a RicLagoria/PEF. **No hace falta el entorno de Python.**

1. En una terminal, dentro del repositorio y en `master`:

   ```bash
   git checkout master
   git pull origin master
   ./presentacion/preparar_demo.sh
   ```

   Crea y sube las dos ramas, y al final imprime dos links.

2. Abrir **los dos links** en el navegador y apretar **Create pull request** en cada uno.
3. Esperar a que terminen los dos pipelines (unos 3 minutos) y **dejar abiertas estas pestañas**:
   - el PR `demo/con-error`, con el check rojo;
   - el PR `demo/sin-error`, con todo en verde;
   - https://riclagoria.github.io/PEF/evolucion/ (todavía sin la nota);
   - la pestaña **Actions** del repositorio.

Si alguno de los dos no da lo esperado (rojo / verde), ver «Si algo sale mal».

## Guion (≈ 4 minutos)

| Min | Acción | Qué decir |
|---|---|---|
| 0:00 | PR **con error**: abrir **Calidad estática** → paso «Ruff» o «Radon y Xenon» y mostrar `PLR0913 Too many arguments (7 > 5)`. | «Subimos una función con 7 parámetros a propósito; el límite es 5.» |
| 0:45 | En ese PR, mostrar **Resultado** en rojo y el botón **Merge** bloqueado. **No apretarlo.** | «Sin el check Resultado en verde, no se puede mergear. El enunciado pide que el CI rechace.» |
| 1:30 | PR **sin error**: mostrar los 10 jobs en verde y **Resultado**. Señalar el orden: lo barato primero, benchmarks y perfilado al final, y las pruebas en Python 3.11, 3.12 y 3.13. | «Mismo pipeline, otro cambio: todo pasa.» |
| 2:30 | Apretar **Merge pull request** en el PR sin error. | «Con todo en verde se mergea.» |
| 2:40 | Pestaña **Actions**: aparece **Documentación**. Esperar ≈ 1 minuto. | «Al mergear a master la documentación se publica sola.» |
| 3:40 | Pestaña de Pages: recarga forzada (**Ctrl+Shift+R**). Se ve la nota «Demo en vivo». | «Está publicada, sin subir nada a mano.» |

## Después

1. Cerrar el PR `demo/con-error` **sin mergear** (botón **Close pull request**).
2. Limpiar las ramas:

   ```bash
   git checkout master
   git pull origin master
   ./presentacion/preparar_demo.sh limpiar
   ```

## Ensayo

Hacer **todo lo de arriba menos el merge**: abrir los dos PRs, mirar rojo y verde, y cerrarlos sin mergear; después
`./presentacion/preparar_demo.sh limpiar`. Lo único sin ensayar queda el merge, y la publicación en Pages ya funcionó
después de cada merge anterior.

## Si algo sale mal

| Problema | Qué hacer |
|---|---|
| El script dice «La rama ... ya existe» | `./presentacion/preparar_demo.sh limpiar` y volver a correrlo. |
| El script dice «Hay cambios sin commitear» | Estás en una copia con cambios. `git stash` y volver a correrlo. |
| `git push` pide usuario o contraseña | Resolverlo en el ensayo (SSH o credencial guardada de GitHub). |
| El PR con error **no** se pone en rojo | Mostrar el PR #9, donde CodeQL rechazó un cambio real, y explicar que la regla es la misma. |
| El botón **Merge** está habilitado en el PR rojo | La protección no se aplica a administradores. Mostrar el check rojo y **no usar el botón**. |
| Pages demora o no muestra la nota | Recarga forzada; si no, mostrar la ejecución anterior de **Documentación** en **Actions**, que está en verde. |
| El pipeline tarda más de lo previsto | Por eso se abren los PRs unos 15 minutos antes. |
| No hay internet | Mostrar capturas de las cuatro pestañas, tomadas en el ensayo. |
