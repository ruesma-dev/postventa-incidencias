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
