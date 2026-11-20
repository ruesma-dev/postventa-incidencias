# Review · arreglo «nombre del proveedor recortado en la edición»

Revisión completa (pasada 1): `git diff ed9318e...HEAD` (HEAD `b705018`).

- **Veredicto: RECHAZADO** (CHANGES_REQUESTED).
- **Nivel de rigor:** arreglo sin spec ni entrada en `features.json`; `init.sh`
  declara N/A las puertas de cobertura, tamaño, carril y capa e2e («la rama no
  corresponde a ninguna feature declarada»). Se exige lo de un arreglo: RED
  real, test por cada comportamiento que cambia, convenciones y `init.sh` verde.

## 1. `bash harness/init.sh` (raíz del worktree): EN ROJO, ajeno al arreglo

```
2202 passed, 48 skipped in 1007.77s
[OK] servicio api (services/postventa-api): pytest en verde (caché: ... desde el verde del 2026-11-19 01:05; ejecutar_siempre: 38 rutas en verde)
FAILED tests/test_f007_dev_front_ps1.py::test_f007_r36_el_script_existe_y_va_en_utf8_con_bom_y_crlf
E   AssertionError: dev_front.ps1 tiene que ir con finales de línea CRLF
[KO] servicio front (services/postventa-front): pytest en rojo
1 comprobaciones fallidas. NO empieces a trabajar.
```

Causa: la nueva salida del front en LF ha arreglado los 16 tests JS de F-038,
pero se ha pasado: también ha sacado `dev_front.ps1` en LF, y la convención
(CONVENTIONS, «PowerShell: UTF-8 con BOM y CRLF») y su test exigen CRLF.
`git ls-files --eol`: en el worktree `i/lf w/lf`; en la carpeta principal
`i/lf w/crlf`. No es del arreglo (el diff no toca el front), pero con `init.sh`
en rojo no se aprueba. Arreglo del entorno: volver a sacar **solo**
`services/postventa-front/dev_front.ps1` con `core.autocrlf=true` (borrarlo y
`git checkout -- <ruta>`), sin cambio en git. A medio plazo, un
`.gitattributes` (`*.js eol=lf`, `*.ps1 eol=crlf`) evitaría repetirlo en cada
worktree: propuesta aparte (ya es el segundo arreglo, tras `fix(ajustes)`, que
choca con esto).

Nota: la suite de `postventa-api` salió por **caché** del verde de las 01:05
(el del implementer, mismo código). No la he relanzado sin caché: el rojo del
front ya impide aprobar y las cosas abajo piden otra pasada de todos modos. En
la siguiente, `ARNES_SIN_CACHE=1 bash harness/init.sh`.

## 2. Contra la propuesta

- [x] El cambio de `validar_valores` es el aprobado: el dict `pares` usa la
  regla de `pares_del_desplegable` (primer nombre no vacío, recortado).
- [x] **Hacer pública `nombre_recortado`: entra.** Es la forma de cumplir «la
  misma regla que la importación» sin duplicarla; tres renombres internos
  mecánicos, docstring nuevo. Búsqueda en todo el worktree (código, tests,
  scripts, `progress/`): ningún otro uso de `_nombre_recortado` en código; solo
  menciones históricas en `progress/impl_F-072.md:61` y
  `progress/review_F-072_bloque5.md:73`, que no se tocan. Los tests
  `test_f036_r8_nombre_recortado` y `test_f071_r13_etiqueta_con_nombre_recortado`
  solo coinciden en el nombre; no importan la función.
- [x] Dominio puro (ARCHITECTURE): `revision.py` ya importaba de
  `plantilla_incidencias.py`; dominio → dominio, sin infraestructura.
- [x] CONVENTIONS: primera línea con ruta, español, sin prints ni secretos.
- [x] Oficio y unidad fuera: bien dejados fuera y bien documentados en el
  informe del implementer como decisión del humano.
- [ ] **La propuesta estaba incompleta: el arreglo rompe un invariante escrito en
  el adaptador HTTP** (cambio requerido 2).

## 3. RED real

- [x] Reproducido en una copia del scratchpad (`git archive HEAD`), con el
  `revision.py` de `ed9318e` y el resto de HEAD: `2 failed, 1 passed`, los
  mismos dos fallos del informe (`('descripcion', 'proveedor') == ('descripcion',)`
  y `'Carpintería Ejemplo, S.L. ' == 'Carpintería Ejemplo, S.L.'`). Con el
  `revision.py` de HEAD: `3 passed`. El que pasa en RED es el control de la
  importación, como dice el informe.

## 4. Efecto lateral (primer no vacío; en blanco → `None`)

- [x] **Es correcto.** Es exactamente la regla de la importación, y
  `proveedor_nombre = None` con código ya existe hoy (lo produce la importación):
  los CHECK de `13_bandeja_incidencias.sql` y `15_revisiones_bandeja.sql` lo
  admiten (`proveedor_nombre IS NULL OR oficio_nombre IS NOT NULL`), y
  `conCodigo` del front lo pinta como código.
- [ ] **No está cubierto.** Dos mutantes en la copia del scratchpad, contra los
  8 ficheros `tests/*revision*.py` + el test nuevo (818 tests):
  - M1 `if pares.get(clave) is None:` → `if clave not in pares:` (vuelve a
    ganar la primera fila aunque traiga el nombre vacío): **sobrevive**,
    `818 passed`.
  - M2 `nombre_recortado(fila.proveedor_nombre)` →
    `(fila.proveedor_nombre or "").strip()` (en blanco → `""` y no `None`):
    **sobrevive**, `818 passed`.
  Ninguno es equivalente: con cualquiera de los dos, una edición sin tocar el
  proveedor vuelve a marcar `proveedor` en `cambios` (la importación guarda el
  nombre de la fila posterior, o `None`). Es el mismo defecto por otra puerta.

## 5. Datos del test

- [x] Ficticios: obra `9901`, proveedor `EJ07`, «Carpintería Ejemplo, S.L.»,
  «Promoción Ejemplo», «Villa Ejemplo 1». Ni personas, ni DNI, ni proveedores
  reales. «0046 · Carpintería de madera» es un oficio genérico, no un dato
  sensible.

## Cambios requeridos

1. **Cubrir el efecto lateral** en
   `services/postventa-api/tests/test_fix_proveedor_nombre_recortado.py`, con el
   mismo esquema (importación → editar sin tocar el proveedor → `cambios` solo
   `("descripcion",)` y el nombre igual al de la importación):
   a) un par cuya primera fila de `obrofc` trae nombre vacío (`""` o `None`) y
      una posterior lo trae → se guarda el de la posterior (mata M1);
   b) un par cuyo único nombre está en blanco (`"   "`) → se guarda `None`
      (mata M2).
   Que cada uno falle de verdad con su mutante, y su salida en el informe.
2. **`services/postventa-api/interface_adapters/api/revision.py:434-449`
   (`_pares`)**: su docstring dice «El primero, como hace la validación de una
   edición (R14): lo que se ofrece es lo que se guarda», y sigue haciendo
   `setdefault` con el nombre crudo. Tras el arreglo eso es falso: el
   desplegable de la edición ofrece «EJ07 · Carpintería Ejemplo, S.L. » (o solo
   «EJ07» si la primera fila viene vacía) y se guarda otro nombre. Hoy es
   cosmético (el front elige por código), pero es un invariante escrito que el
   diff rompe. Está fuera de la propuesta aprobada, así que el **líder lo lleva
   al humano** antes de tocarlo. Recomendación: alinear `_pares` con la misma
   regla (`nombre_recortado` + primer no vacío), que es lo que su docstring
   promete, con un test que compare lo ofrecido con lo guardado. Mínimo
   aceptable: corregir el docstring para que no mienta.
3. **Entorno, no código:** devolver `services/postventa-front/dev_front.ps1` a
   CRLF en el worktree (sección 1) y relanzar
   `ARNES_SIN_CACHE=1 bash harness/init.sh` hasta verde.

## Observaciones (no bloquean)

- Las incidencias ya editadas antes del arreglo guardaron el nombre con el
  espacio final; su próxima edición marcará `proveedor` una vez (crudo →
  recortado). Ruido de una sola vez, asumible; vale decírselo al humano.
- El oficio y la unidad tienen el mismo defecto (informe del implementer); si
  se arreglan, conviene que sea con la misma idea: la edición reutiliza las
  funciones del desplegable de la importación en vez de rehacer la regla.

## Automejora (propuesta, no aplicada)

- Para los arreglos sin spec, el líder podría pedir en la propuesta un `grep`
  de los otros sitios que aplican la misma regla (aquí, `setdefault` sobre
  `proveedor_nombre` aparecía dos veces: dominio y adaptador). Habría sacado el
  punto 2 antes de la aprobación.

## Segunda review

Revisión incremental desde `c5dde43` (pasada 2), HEAD `997d5f5`: diff
`d6be9d6^2..HEAD` (excluye el merge de `dev` d6be9d6, ya aprobado aparte).

- **Veredicto: APROBADO.**

### `ARNES_SIN_CACHE=1 bash harness/init.sh` (raíz del worktree): EN VERDE

Sin caché, como pedía la pasada 1. `exit=0`. Raíz `2202 passed, 48 skipped`;
api `10382 passed, 485 skipped in 2600.47s`; front `911 passed, 7 skipped`.
Puertas de cobertura, carril y capa e2e N/A (la rama no es una feature
declarada); solo avisos previos (ruff 113, features `blocked`). `git status`
limpio al terminar. `dev_front.ps1`: `i/lf w/crlf`; `js/revision.js`: `w/lf`.

### Los tres cambios requeridos

- [x] **1. M1 y M2 mueren.** La regla vive ahora en `nombres_de_los_pares`
  (dominio), así que los apliqué ahí, en una copia `git archive HEAD` del
  scratchpad, contra el test del arreglo + los 6 `tests/test_f0*_*revision*.py`
  (823 tests):
  - M1 `if nombres.get(pareja) is None:` → `if pareja not in nombres:`:
    `1 failed, 822 passed` (`..._toma_el_primer_nombre_no_vacio_del_par`).
  - M2 `nombre_recortado(fila.proveedor_nombre)` →
    `(fila.proveedor_nombre or "").strip()`: `2 failed, 821 passed`
    (el anterior y `..._nombre_en_blanco_se_guarda_none_...`).
  Restaurado con `cmp` idéntico al original; el worktree no se tocó.
- [x] **2. `_pares` alineado y cubierto.** Mutante: devolver a `_pares` el
  `setdefault` con el nombre crudo (el código de antes de 24acec3). Con
  `-k "revision or fix_proveedor"`: base de la copia `15 failed` (todos
  `*_documentacion.py`: la copia solo lleva `services/postventa-api`, sin
  `docs/` ni `specs/`); con el mutante `18 failed`, los 15 mismos + los tres
  casos de `test_fix_lo_que_ofrece_pares_es_lo_que_guarda_la_edicion`
  (`espacio-final`, `primera-fila-vacia`, `en-blanco`). Coincide con el RED
  del informe (b2768b8, `3 failed, 5 passed`).
- [x] **3. CRLF:** resuelto en el entorno, sin cambio en git (ver arriba).

### Resto de comprobaciones

- [x] **Dominio puro.** `nombres_de_los_pares` está en
  `domain/models/plantilla_incidencias.py`, cuyas importaciones son solo
  stdlib y `domain.*`. La usan `domain/models/revision.py` (dominio → dominio)
  y `interface_adapters/api/revision.py` (adaptador → dominio): la dirección
  correcta.
- [x] **Ningún otro uso roto.** `_pares` solo se llama en el `GET` del
  catálogo de la revisión (`revision.py:326`). El orden de los pares no cambia
  (el dict conserva el de la primera fila del par, igual que `setdefault`).
  El nombre `None` ya lo consumía el front: `conCodigo` en `js/revision.js`
  pinta el código, y `nombreDeProveedor` de `js/volcado.js` cae al código con
  `||`; los tests JS ya traen pares con `proveedor_nombre: null`. Suites api y
  front en verde.
- [x] **Docstrings veraces.** El de `_pares` dice que el nombre sale de
  `nombres_de_los_pares`, la misma función de `validar_valores`: cierto, y lo
  ata el test parametrizado. El de `nombres_de_los_pares` y el de
  `validar_valores` describen la regla tal como está.
- [x] **Datos ficticios:** los mismos de la pasada 1 (obra `9901`, `EJ07`,
  «Carpintería Ejemplo, S.L.», «Promoción Ejemplo»), más nombres `""` y `"   "`.
- [x] **CONVENTIONS:** primera línea con ruta, español, sin prints ni secretos.

### Observaciones (no bloquean)

- `pares_del_desplegable` (importación) no reutiliza `nombres_de_los_pares`:
  repite el bucle con un filtro de oficio. El nombre de cada par sale igual (el
  filtro no afecta al nombre) y los tests del arreglo comparan edición con
  importación en los tres casos, así que una divergencia futura se vería. Que
  la importación también la use sería un refactor menor, aparte.
- El test parametrizado compara `_pares` con la edición, no con la
  importación: por sí solo no cazaría M1/M2 (las dos partes se mueven juntas),
  pero los otros tests del fichero sí. Combinados, cubren la cadena entera.
- Comando: ejecuté `ARNES_SIN_CACHE=1 bash harness/init.sh` en vez de
  `bash harness/init.sh`, por la nota de la pasada 1 y el protocolo del reviewer.
