# Demo del pipeline (5 minutos)

**Qué se muestra:** el CI rechaza un cambio que rompe un control, se corrige, el pipeline pasa en verde, se mergea y la
documentación se publica sola en GitHub Pages. Es la prueba en vivo de lo que hicimos en el Parcial 3.

**Reparto sugerido:** Ricardo en la terminal, Octavio en el navegador (GitHub).

Tiempos medidos en el último PR: **Calidad estática** ≈ 40 s · CI completo hasta **Resultado** ≈ 2 min 26 s · publicación
en Pages tras el merge ≈ 1 min. El resto es narración sobre lo que se ve.

---

## 1. Preparación (una sola vez, antes del ensayo)

Hace falta Linux (o macOS), Git y Python 3.11 o superior.

```bash
git clone https://github.com/RicLagoria/PEF.git
cd PEF/Ver-Optimizada
python -m venv .venv
source .venv/bin/activate
pip install --require-hashes -r requirements-dev.txt
python tasks.py ci
```

El último comando corre todos los controles locales; tiene que terminar sin errores (tarda unos 2 minutos la primera vez).
Si falla acá, el problema es del entorno y hay que resolverlo antes de la demo.

Para tener los scripts de la demo (todavía están en una rama, hasta que se mergee el PR que los incluye):

```bash
git fetch origin claude/charming-bell-op205i
git checkout claude/charming-bell-op205i
```

Conviene tener hecho `git config user.name` y `git config user.email`, y poder hacer `git push` a RicLagoria/PEF sin pedir
contraseña (SSH o credencial guardada).

## 2. Ensayo (con la rama `demo/ensayo`)

El ensayo hace todo lo de la demo, incluido el merge. **Su nota queda publicada en Pages**: es inofensivo, pero hay que
saber que pasa. Antes del día de la presentación:

1. Preparar la rama (una vez; el script la crea desde `master`, la sube y vuelve a la rama donde estabas):

   ```bash
   ./presentacion/preparar_demo.sh demo/ensayo
   ```

2. Seguir el guion de la sección 3 completo, con un reloj, y anotar cuánto tardó cada paso en su conexión.
3. Limpiar:

   ```bash
   git push origin --delete demo/ensayo
   git branch -D demo/ensayo
   ```

Tras el merge del ensayo, `master` ya tiene la nota del ensayo. **Para la demo real se crea otra rama** (es otro nombre, y
el script parte del `master` ya actualizado):

```bash
./presentacion/preparar_demo.sh demo/romper-calidad
```

Hacerlo **antes de empezar a presentar**: el script tarda unos segundos.

## 3. Guion de la demo en vivo

| Min | Quién | Acción | Qué decir |
|---|---|---|---|
| 0:00 | Ricardo | En `Ver-Optimizada/` con el entorno activo: `python tasks.py lint typecheck complexity sast` | «Estos son los mismos comandos que corre el CI. Lo que falla allá se reproduce acá.» |
| 0:20 | Octavio | En GitHub, banner **Compare & pull request** de la rama `demo/romper-calidad` → **Create pull request** | «Subimos un cambio que rompe un control a propósito: una función con 7 parámetros, y el límite es 5.» |
| 0:30 | Octavio | Bajar a la lista de checks del PR. En unos 45 s **Calidad estática** pasa a rojo y **Resultado** también. Mostrar que **Merge** está bloqueado. | «El enunciado pide que el CI rechace. Acá rechaza, y no se puede mergear.» |
| 1:15 | Octavio | Abrir el detalle de **Calidad estática** y mostrar la línea `PLR0913 Too many arguments (7 > 5)`. | «El mensaje dice qué regla falló y dónde.» |
| 1:30 | Ricardo | `git checkout demo/romper-calidad && git revert --no-edit HEAD && git push` | «Deshacemos el cambio roto. Se vuelve a correr todo el pipeline.» |
| 1:40 | Octavio | Mientras corre: señalar el orden (lo barato primero; benchmarks y perfilado al final), la matriz de 3 versiones de Python y el check **Resultado** que resume todo. | «Cada fase de hoy es un job de este pipeline.» |
| 4:10 | Octavio | Con **Resultado** en verde: **Merge pull request**. | «Con todo en verde, se mergea.» |
| 4:15 | Octavio | Pestaña **Actions**: aparece **Documentación**. Esperar ≈ 1 min a que termine. | «Al hacer merge a master, la documentación se construye y se publica sola.» |
| 5:15 | Octavio | Abrir https://riclagoria.github.io/PEF/evolucion/ con recarga forzada (**Ctrl+Shift+R**): se ve la nota «Demo en vivo». | «Está publicada, sin subir nada a mano.» |

Después, para volver al estado normal:

```bash
git checkout master
git pull origin master
git branch -D demo/romper-calidad
```

(La rama remota se borra desde el botón de GitHub al hacer el merge.)

## 4. Si algo sale mal

| Problema | Qué hacer |
|---|---|
| El pipeline tarda más de lo previsto | Tener abierta en otra pestaña la última ejecución verde (pestaña **Actions** del repo) y mostrar eso mientras tanto. |
| Pages no muestra la nota | Recarga forzada (**Ctrl+Shift+R**); si no aparece, mirar si el job de **Documentación** terminó en la pestaña **Actions**. |
| El botón **Merge** no está bloqueado con el check en rojo | La protección de `master` no se aplica a administradores. Mostrar igualmente que **Resultado** está en rojo y no usar el botón de omisión. |
| `git push` pide credenciales | Resolverlo en el ensayo (SSH o credencial guardada); en vivo se pierde tiempo. |
| No hay internet | Mostrar solo `python tasks.py ci` en local y un video de respaldo de 1 minuto. |

## 5. Qué hace `preparar_demo.sh`

Crea la rama desde `origin/master` con dos commits: (1) una nota visible en `docs/evolucion.md`; (2) una función con 7
parámetros en `recommender_core.py`. Sube la rama y vuelve a la rama donde estabas. **Sin pull request no corre el CI**
(solo se dispara con un push a `master` o un PR hacia `master`), así que la rama puede esperar subida sin gastar nada.
`git revert HEAD` deshace solo el segundo commit y deja la nota.
