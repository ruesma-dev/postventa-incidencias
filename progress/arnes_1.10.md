# Actualización del arnés 1.5.2 → 1.10.0 (2026-11-12)

Mantenimiento del arnés, no feature del backlog. Rama `feature/arnes-1.10`
del worktree `postventa-arnes` (sale de `dev` e9b9d23). Encima del commit del
instalador (902d1c9) van cuatro commits locales, sin push:

| Commit | Bloque |
|---|---|
| `e056af4` | 1 · capa local de rigor |
| `44372d3` | 2 · fusión de los mixtos (+ `BACKLOG.md` regenerado) |
| `b97c9a9` | 3 · arreglo local de `test_f063_r2` |
| `f031869` | 5 · `harness/ARNES_VERSION.md` |

En `arnes-base` (rama `main`, como el precedente 2709558): `01ef33c`, un encargo
pendiente. No hay push en ningún repositorio.

## 1. Lo propio que pisó el instalador

Método: cada genérico de `dev` se comparó con el payload de la **1.5.2**
(`arnes-base` 9224a5a), ignorando finales de línea. Lo que se aparta de ese
payload es la adaptación local o un parche llegado a mano.

| Fichero (en `dev`) | Diferencia con la 1.5.2 | Qué era | Destino |
|---|---|---|---|
| `harness/rigor.json` | `nivel_por_defecto: critico` (en 1.5.2 era el genérico; la 1.7.0 pasó a `estandar`) y `mutacion.workers: 8` | Ajuste propio (decisión del humano) | **`harness/rigor.local.json`** |
| `.claude/agents/reviewer.md` | punto 7 «una puerta que protege un ORDEN se prueba moviéndola» (F-034, F-013) | Mejora genérica nacida aquí | La 1.10 ya la trae como **RM7**: se deja |
| `.claude/agents/reviewer.md` | punto 4 «mutantes a mano: ¿los caza un test de la propia feature?» (F-060) | Mejora genérica nacida aquí | La 1.10 **no** la trae → `CHECKPOINTS.md` C4 bis (mixto) |
| `harness/alcance.py` | `harness` en `DIRECTORIOS_EXCLUIDOS` (1.7.8) | Parche portado | La 1.10 lo trae (con `alcance_incluye`): se deja |
| `harness/mutacion.py`, `mutacion_paralela.py` | parche 1.6.3 y piezas de la 1.7.8 | Parches portados | La 1.10 los trae rehechos: se deja |
| los otros 15 genéricos | idénticos a la 1.5.2 | — | nada |

`harness/rigor.local.json` (capa F-063): admite las dos claves (están en la
lista blanca `ESQUEMA_LOCAL` de `harness/rigor.py`: `nivel_por_defecto` texto y
`mutacion.workers` entero ≥ 1). Lleva cada motivo en su `$doc`, con la medición
de `progress/explore_F-009_timeouts.md` (38,7 s a solas, 131,6 s con 16 workers,
77,4 s con 8). Comprobado:

```
$ python -m harness.rigor --validar
    niveles: critico, documental, estandar, express; por defecto critico; umbral de cobertura 80%; pisan el global: critico 90%
    capa local (harness/rigor.local.json): mutacion.workers, nivel_por_defecto
```

**Cambios de conducta que trae la 1.10 por `rigor.json` y que NO se han
revertido** (son genéricos; el humano decide si alguno va a la capa local):
- `critico` exige **90 %** de cobertura de líneas cambiadas (antes 80) y, como
  es el nivel por defecto aquí, toda feature sin `rigor` declarado también.
- La mutación de `critico` va **uno por línea, el 60 % de los candidatos,
  acotado a [100, 300]**, semilla nueva: ya no mide la campaña entera (el
  humano la pide con `--max-mutantes 0`). No es comparable con las anteriores.
- `estandar` deja la mutación como informativa; aparecen `express` y la capa
  e2e informativa.

`tests/test_mutacion_informe_workers.py` (nacido aquí en la 1.7.8) no está en
el payload 1.10 y el instalador lo deja: **pasa** con el motor nuevo, se conserva.

## 2. Los 6 mixtos

Criterio: base = el fichero de la 1.10 (`arnes-base/arnes-base/<ruta>`), y
encima lo propio. Antes se midió qué era propio comparando el nuestro con la
1.5.2.

- **`harness/init.sh`**: el nuestro era el de la 1.5.2 **con solo tres líneas
  propias** (`REQUIERE_ENV=0` y las dos cabeceras `[ADAPTAR]` resueltas). Las
  suites de api y front, sus venv, la caché y la cobertura no viven en
  `init.sh` sino en `harness/servicios.json` (estado del proyecto, intacto). Se
  toma el de la 1.10 y se reaplican esas tres líneas: entran estados (§3/3 ter),
  aviso de capa local (§3b), caché (§7 bis), tamaño (§7 quater), carril
  (§7 quinquies), e2e (§7 sexies) y `RAMA_BASE`. `RAMA_BASE=dev` es correcto
  aquí: `git rev-list --count --no-merges dev..main` = 0.
- **`CLAUDE.md`**: base 1.10 (qa-e2e entre los subagentes, paradas con
  plantilla, prioridad de los ocho estados, regla «tal cual» con
  `ARNES_SIN_CACHE=1`, regla del push, protocolo de `azure-apps` del bloque de
  Ruesma). Propio reaplicado: título, mapa del monorepo (más una línea para
  `harness/rigor.local.json`), las cuatro prohibiciones (Sigrid, PostgreSQL
  compartido, SharePoint, partes escaneados) y el «LÍMITE DE SERVICIO» del
  monorepo en lugar del «LÍMITE DE MICROSERVICIO» genérico. Autorización de
  subagentes, ritmo de dos paradas y markitdown: el texto 1.10 los contiene
  (ampliados). La regla vieja «NO hacen push ni PRs» queda sustituida por la
  de la 1.10 (commits y merges sí; push nunca), que exige `test_f070_r30`.
- **`CHECKPOINTS.md`**: base 1.10. Propio reaplicado: las siete trampas de
  dominio en C3 (en lugar del `[ADAPTAR]`), la casilla de C3 bis sobre
  originales (no en git, sí en el árbol ignorados, con
  `tests/test_originales_no_versionados.py`), un párrafo en «Niveles de rigor»
  que dice que aquí el nivel por defecto es `critico` por la capa local, y en
  C4 bis las dos reglas de F-060 que la 1.10 no trae (el punto 4 de nuestro
  `reviewer.md` y la guarda por definiciones). El coste por mutante (1.6.3),
  los mutantes a mano equivalentes (F-013) y los workers en «Evidencias»
  (1.7.8), que el nuestro llevaba, la 1.10 ya los trae.
- **`docs/CONVENTIONS.md`**: el nuestro (PyMuPDF vs ReportLab, `.ps1` de
  `infra/` en ASCII y CRLF) más la sección Git de la 1.10 (quién hace cada merge
  y el push).
- **`.claude/settings.json`**: el nuestro era el de la 1.5.2 sin cambios (sin
  allowlist propia), así que se toma el de la 1.10 entero: fuera el hook
  `PostToolUse`, `model`/`effortLevel` y los permisos nuevos del reviewer.
- **`docs/referencia/README.md`**: la 1.10 no lo cambia respecto de la 1.5.2;
  se conserva el nuestro (índice real de documentos).

Ninguna marca `[ADAPTAR]` queda en los mixtos. También se regeneró
`BACKLOG.md` (`python harness/backlog.py`) con el orden de columnas de la 1.10.

## 3. Tests

Intérprete: el `python` del PATH, que es el que usa `init.sh` en la raíz
(`postventa-incidencias/.venv`, Python 3.12.7). Sin `.env`. Comando:
`python -m pytest tests -q -p no:cacheprovider`.

| Momento | Resultado |
|---|---|
| Tras el instalador + bloque 1 (mixtos aún conservados) | 56 failed, 2013 passed, 181 skipped (590,8 s) |
| Ficheros que fallaban, tras fusionar los mixtos | 3 failed, 548 passed, 34 skipped (50,4 s) |
| Suite completa final | **1 failed, 2201 passed, 48 skipped (595,4 s)**; el 1 se arregló después (ver abajo): 34 passed en su fichero |

Los 56 iniciales eran los rojos previstos por la guía para los mixtos
conservados (f004, f019_r26, f023, f028, f040, f058, f059, f063, f070, estados,
caché de `init.sh`, tamaño, documentos del arnés...). Los 3 que quedaron:

1. `test_backlog_md_existe_y_esta_al_dia`: hacía falta regenerar `BACKLOG.md`
   (lo avisa la guía). Regenerado: 65 passed.
2. `test_f063_r2_el_payload_no_trae_capa_local`: **defecto del arnés
   genérico**. Comprueba que el payload no trae `rigor.local.json`, pero se
   instala en los proyectos y ahí da rojo en cuanto uno usa la capa local,
   justo lo que la guía manda. Arreglo local mínimo (commit `b97c9a9`): la
   misma marca `es_el_taller` que ya usan `test_f023_textos`/`test_f026_textos`.
   Los tres ficheros f063: 115 passed, 1 skipped.
3. `test_f035_t20_ascii_crlf_sin_bom_y_su_ruta_en_la_linea_1`: no lo causa la
   actualización. **El worktree `postventa-arnes` salió con finales LF**
   (`git ls-files --eol`: 964 ficheros `w/lf` aquí frente a 132 en
   `postventa-incidencias`) y el test exige CRLF en `infra/publicar_maqueta.ps1`.
   Ese fichero se volvió a sacar con `git checkout` (sale `w/crlf`, sin cambio
   en git): 34 passed.

No se ejecutaron las suites de los servicios ni `bash harness/init.sh` (lo hace
el líder, según el encargo).

## 4. Propagación a arnes-base

- **`01ef33c`** (`main` de `arnes-base`, local, sin push):
  `ENCARGO_pendiente_test_f063_r2_rojo_en_proyectos_con_capa_local.md`, con el
  caso, el arreglo aplicado aquí y el criterio de hecho. Va como encargo, igual
  que el precedente 2709558 de otro proyecto, y no como arreglo en el payload:
  el payload se edita en una rama de feature del worktree `arnes-trabajo`, que
  este encargo prohíbe tocar, y en `main` no se commitea código.
- **Las dos reglas de F-060** (mutantes a mano de la propia feature; guarda por
  definiciones): ya estaban registradas en `arnes-base` como
  `ENCARGO_pendiente_mutantes_a_mano_de_la_propia_feature_y_guarda_de_modulo.md`
  (versionado). No se ha duplicado nada.
- RM7 (puerta de orden) y los parches 1.6.3/1.7.8, nacidos aquí, ya están en la
  1.10: nada que portar.

## 5. ARNES_VERSION.md

El instalador lo dejó incompleto: ponía como destino el worktree
`postventa-arnes` y no decía nada de lo hecho a mano. Se corrigió el destino a
`postventa-incidencias` y se añadió la sección «Lo que se hizo a mano tras el
instalador»: capa local, fusión de los mixtos, las dos reglas de C4 bis que hay
que conservar mientras el payload no las traiga y el arreglo local de
`test_f063_textos.py` (lo pisará la próxima actualización si no llega antes el
arreglo).

## Queda / para el líder

- **`bash harness/init.sh`** en este worktree (no lo he ejecutado). Ojo con los
  finales LF del worktree: algún test de las suites de api/front que exija CRLF
  (como el de f035) puede dar rojo **por el checkout**, no por la
  actualización. Se arregla volviendo a sacar el fichero con `git checkout`.
- **Decisión pendiente del humano: `depende_de` en `harness/servicios.json`.**
  La caché de suites (§7 bis) es nueva en este repo y su clave solo mira el
  árbol del servicio. Pero los tests de `api` leen `infra/`, `docs/`, `specs/`,
  `harness/`, `progress/` y `.gitignore` de la raíz, y los del front leen
  `harness/`. Sin declararlos, un cambio solo en `infra/` o `docs/` serviría el
  verde viejo de la caché. El cierre está a salvo (el reviewer usa
  `ARNES_SIN_CACHE=1`), pero un `init.sh` normal no. Opciones: declarar
  esas rutas en `depende_de` de cada servicio, o `depende_de: ["."]` (la caché
  casi nunca se serviría). No lo he tocado: es estado del proyecto y una
  decisión de coste frente a seguridad.
- Que el humano confirme o ajuste en la capa local los cambios de conducta de la
  1.10 en `critico` (cobertura 90 %, mutación muestreada).
- Tras actualizar no hay nada en `todo` (estados F-042): el líder tendrá que
  pedir qué comprometer. F-066 seguía aparcada en otra rama.

## Review · 2026-11-12

**Veredicto: APPROVED.** Rama `feature/arnes-1.10` (902d1c9..c2d9391) y
`arnes-base` 01ef33c. No es feature: no aplica `rigor` ni C1–C5 de feature; se
revisa la fusión. `bash harness/init.sh` no lo he ejecutado (lo corre el
líder en paralelo, según el encargo): **el merge queda condicionado a que salga
en verde.**

**1. Nada propio perdido.** Método: `dev` contra el payload 1.5.2 (9224a5a)
para aislar lo propio, y HEAD contra el payload 1.10 para ver que sigue.
- `CLAUDE.md`: título, mapa del monorepo, las cuatro prohibiciones (Sigrid,
  `psql-albaranes-rs9k2`, SharePoint, partes escaneados) y LÍMITE DE SERVICIO,
  reaplicados. Autorización de subagentes, dos paradas, markitdown, `azure-apps`
  y `arnes-base` vienen en el texto 1.10 (dev no los tenía distintos del
  genérico). La regla de push/PR queda en la 1.10 («push nunca; PRs solo con
  petición explícita»), coherente con el `CLAUDE.md` global. Cambio de conducta
  a conocer: los merges a `dev` pasan a ser sin preguntar (genérico 1.10).
- `CHECKPOINTS.md`: las siete trampas de C3, la casilla de originales de C3 bis,
  el párrafo del nivel `critico` local y las dos reglas de F-060 en C4 bis. Lo
  que llevábamos de 1.6.3/1.7.8/F-013 (coste por mutante, workers en
  Evidencias, equivalentes a mano) ya está en el 1.10.
- `reviewer.md`: RM7 (F-034) con el añadido de F-013 («sin `-x`»), en la 1.10.
- `init.sh`: solo `REQUIERE_ENV=0` y las dos cabeceras; idéntico al 1.10 en lo
  demás. `CONVENTIONS.md` (PyMuPDF, `.ps1` ASCII/CRLF) y
  `docs/referencia/README.md` (índice real) conservados.
- `settings.json`: dev era el genérico 1.5.2 sin allowlist propia; HEAD es el
  1.10 íntegro. Ningún fichero borrado en el diff; `features.json`,
  `servicios.json`, `ARCHITECTURE.md`, `specs/` y `progress/` sin tocar.
- Observación (no bloquea): la regla F-060 de mutantes a mano decía en dev
  «la campaña dio cero **o se quedó corta**»; en C4 bis cuelga del punto «dio 0
  mutantes». Es el alcance del encargo aprobado en `arnes-base`, y RM7 cubre los
  de orden, así que lo dejo como nota.

**2. Genérico 1.10 entero.** Los 120 ficheros del payload comparados sin finales
de línea: solo difieren los mixtos, el estado del proyecto y
`tests/test_f063_textos.py` (el arreglo). Agentes, `harness/*.py`,
`specs/SPECS.md` y `settings.json`, idénticos. Ninguna `[ADAPTAR]` en mixtos,
agentes ni `SPECS.md`.

**3. `test_f063_r2`.** Correcto: misma condición que `es_el_taller` de f023/f026
(`RAIZ.parent/politica_ficheros.json`); en el taller existe y el test sigue
corriendo; en `PycharmProjects/` no, y se salta. Anotado en `arnes-base` 01ef33c
con caso, propuesta y criterio de hecho, y en `ARNES_VERSION.md` para
reaplicarlo si la próxima versión no lo trae.

**4. Secretos.** Lo propio nuevo (capa local, mixtos, `ARNES_VERSION.md`, este
informe) no trae GUIDs, correos, IPs ni credenciales. Las IPs y correos que
salen en el diff son de los tests genéricos del payload (`10.0.0.5`,
`127.0.0.1`, `arnes@ejemplo.invalid`, `arnes@ruesma.es` como committer de
prueba), idénticos a `arnes-base`.

**Tests puntuales (sin `.env`, Python del PATH):** f063 (×3), backlog_md,
documentos_del_arnes, f070/f040/f058/f059_textos, f004_settings,
mutacion_informe_workers, originales_no_versionados: **313 passed, 12 skipped**.
`python -m harness.rigor --validar`: por defecto `critico`, capa local con
`mutacion.workers` y `nivel_por_defecto`. Decisiones del humano cumplidas.

**5. Los dos puntos para el humano.**
- **`depende_de` en `servicios.json` — no bloquea el merge, sí conviene antes
  de la próxima feature.** Verificado: 15 ficheros de tests de los servicios
  leen la raíz (`docs` 40 veces, `infra` 17, `specs` 16, `progress`, `harness`).
  El cierre no corre riesgo (C1 y el reviewer exigen `ARNES_SIN_CACHE=1`), pero
  el `init.sh` normal de inicio de sesión podría servir un verde viejo tras un
  cambio solo en `infra/` o `docs/`. Recomiendo **no** usar `depende_de` con
  `docs/specs/progress` (cambian en casi cada commit y anulan la caché, igual que
  `["."]`), sino `ejecutar_siempre` con esos ficheros de tests (es lo que el
  `$doc` de `servicios.ejemplo.json` propone para tests que barren el repo), más
  `depende_de: ["infra", "harness"]` en `api` y `["harness"]` en `front`. Es
  estado del proyecto: cambio aparte, con OK del humano.
- **Cobertura 90 % y mutación muestreada en `critico` — no bloquea.**
  Recomiendo aceptar las dos y no pisarlas en la capa local: el 90 % mide solo
  líneas cambiadas, y la muestra (uno por línea, 60 %, [100, 300]) es completa
  con ≤ 100 candidatos, que es lo habitual aquí. Para lo que escribe en Sigrid
  o protege un orden, el reviewer sigue teniendo RM7 a mano y la regla de los
  5 minutos, y el humano puede pedir `--max-mutantes 0`. Dejar dicho que las
  campañas nuevas no son comparables con las anteriores.

**Fuera de esta review:** en `arnes-base` hay ficheros sin seguimiento
(`codex/`, `instalar_arnes_dual.ps1` y tres `ENCARGO_pendiente_*`) que no son de
este trabajo; no los he tocado.

## Decisiones del humano y cierre (líder, 2026-11-13)

- **`harness/rigor.local.json`: OK explícito del humano el 2026-11-13** («ok» a la
  pregunta del líder): `nivel_por_defecto` `critico` y `mutacion.workers` 8.
- **`critico` de la 1.10 aceptado** el 2026-11-13: cobertura 90 % de las líneas
  cambiadas y mutación muestreada (uno por línea, 60 %, [100, 300]); no se pisan
  en la capa local. Las campañas de mutación nuevas **no son comparables** con
  las anteriores a la 1.10. Para lo que escribe en Sigrid se puede pedir
  `--max-mutantes 0`.
- **`servicios.json` (`depende_de` / `ejecutar_siempre`)**: aprobado como cambio
  aparte, antes de F-072, en su propia rama.
- **`init.sh` en verde** en `feature/arnes-1.10` tras traer el arreglo de dev
  `27555d0` (dos tests de cabecera de F-065 que fijaban la frase antigua de
  F-038; dev estaba en rojo desde `a7400a1`): raíz 2202 passed / 48 skipped,
  api 9932 passed / 457 skipped, front en verde.
- Los dos rojos previos del `init.sh` eran de finales de línea de la copia de
  trabajo (los `.ps1` necesitan CRLF; el JS del front, LF), no del arnés.
