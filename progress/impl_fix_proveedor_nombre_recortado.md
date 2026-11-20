# Arreglo · nombre del proveedor recortado en la edición

Arreglo sin spec, aprobado por el humano el 2026-11-18. Rama
`fix/proveedor-nombre-recortado` (desde `dev` ed9318e), worktree
`postventa-fix-proveedor`.

## Qué y por qué

Defecto visto en producción (T26 de F-072, `progress/impl_F-072_despliegue.md`
paso 4): al **editar** una incidencia sin tocar el proveedor, `cambios` marcaba
`proveedor`. Sigrid devuelve el nombre con espacio final; la importación lo
guarda recortado (`pares_del_desplegable`: «primero no vacío, recortado») y
`validar_valores` lo tomaba tal cual (`setdefault` con `fila.proveedor_nombre`).

Arreglo: `validar_valores` arma el nombre de cada par con la **misma regla** que
la importación, reutilizando la función de `plantilla_incidencias.py`, que pasa
de `_nombre_recortado` a `nombre_recortado` (pública, con docstring; sus tres
usos internos renombrados). Sin lógica duplicada.

Efecto lateral, coherente con la importación: si la primera fila de `obrofc` de
un par trae el nombre vacío y una posterior lo trae, ahora se toma el de la
posterior (antes, el vacío); un nombre en blanco se guarda `None`.

## Ficheros

- `services/postventa-api/domain/models/plantilla_incidencias.py`: `nombre_recortado` pública.
- `services/postventa-api/domain/models/revision.py`: el dict `pares` de `validar_valores`; docstring.
- `services/postventa-api/tests/test_fix_proveedor_nombre_recortado.py`: 3 tests nuevos.

## RED → GREEN

Commit RED `881f204`, commit GREEN `b0963ad`.

RED (`.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_fix_proveedor_nombre_recortado.py`):

```
.FF                                                                      [100%]
E       AssertionError: assert ('descripcion', 'proveedor') == ('descripcion',)
E         Left contains one more item: 'proveedor'
tests\test_fix_proveedor_nombre_recortado.py:106: AssertionError
E       AssertionError: assert 'Carpintería Ejemplo, S.L. ' == 'Carpintería Ejemplo, S.L.'
tests\test_fix_proveedor_nombre_recortado.py:111: AssertionError
FAILED tests/test_fix_proveedor_nombre_recortado.py::test_fix_editar_sin_tocar_el_proveedor_no_lo_marca_en_cambios
FAILED tests/test_fix_proveedor_nombre_recortado.py::test_fix_la_edicion_guarda_el_nombre_del_proveedor_recortado
2 failed, 1 passed in 1.60s
```

(El que pasa es el control: la importación ya recortaba.)

GREEN, mismo comando: `3 passed in 0.68s`.

Suite del servicio (`-m pytest -q -p no:cacheprovider` desde `services/postventa-api`):
`10368 passed, 485 skipped in 1509.30s (0:25:09)`.

## Mismo problema en el oficio y la unidad (NO arreglado, no estaba en la propuesta)

En el mismo `validar_valores`:

- **Oficio**: guarda `oficios[codigo].nombre or codigo`, sin recortar; la
  importación guarda `oficios_del_desplegable` → `nombre_recortado(...)`. Con un
  nombre de oficio con espacio final en Sigrid, `cambios` marcaría `oficio`.
  Además, la importación toma el primer nombre no vacío por código y la
  edición el de la última entrada del catálogo con ese código (dict por código).
- **Unidad**: guarda `unidad.nombre or unidad.codigo`, sin recortar; la
  importación guarda la **etiqueta** del desplegable (`etiquetas_de_unidades`):
  nombre recortado y, si dos unidades chocan plegadas, `<nombre> (<código>)`.
  Así que la unidad puede salir en `cambios` por el espacio final **o** por esa
  desambiguación, aunque no se toque.

Queda a decisión del humano si se arreglan (el de la unidad necesita decidir
qué nombre es el canónico: el de Sigrid o la etiqueta).

## `bash harness/init.sh` (desde la raíz del worktree): EN ROJO, ajeno al arreglo

```
2202 passed, 48 skipped in 1404.76s        (servicio postventa-api, primera pasada)
10368 passed, 485 skipped in 2493.02s      (servicio postventa-api)
FAILED tests/test_f007_js.py::test_f007_r32_la_suite_de_javascript_esta_en_verde
[KO] servicio front (services/postventa-front): pytest en rojo
1 comprobaciones fallidas. NO empieces a trabajar.
```

Fallan 16 tests JS de control de mutantes de F-038 (`tests_js/revision.test.js`),
p. ej. «el control no encuentra una sola vez: `!v.proveedor_ambiguo &&` …
1 !== 2». No toco el front (`git diff --stat ed9318e -- services/postventa-front`
vacío).

Causa comprobada: **finales de línea del checkout del worktree.** Con
`core.autocrlf=true`, el worktree tiene el front en CRLF
(`js/revision.js: ... with CRLF line terminators`) y la carpeta principal en LF.
Esos tests buscan fragmentos de varias líneas con `\n`. Prueba, en una copia en
el scratchpad (no en el worktree):

- copia con CRLF (`git archive HEAD`): `pass 1116`, `fail 16`;
- misma copia pasada a LF: `pass 1132`, `fail 0`.

No lo he arreglado: sería un workaround del entorno (renormalizar el worktree o
añadir `.gitattributes`), fuera de la propuesta. Opciones para el líder/humano:
volver a sacar el front del worktree en LF (p. ej. `git -c core.autocrlf=false
checkout` de esos ficheros, sin cambio en git) y relanzar `init.sh`; o un
`.gitattributes` con `eol=lf` para el front (cambio de repo, para otra
propuesta). Con eso, el resto de `init.sh` ya está en verde.

## Pendiente

- `init.sh` en verde tras resolver el CRLF del worktree.
- Decidir si se arreglan oficio y unidad.
- Nada de push (lo hace el humano).

## Correcciones del review

Review: `progress/review_fix_proveedor_nombre_recortado.md` (RECHAZADO). En esta
pasada solo el cambio requerido 1. El 2 (`_pares` del adaptador HTTP y su
docstring) **no se toca**: espera la decisión del humano. El 3 (`dev_front.ps1`
en CRLF) ya estaba hecho en el worktree (`git ls-files --eol`: `i/lf w/crlf`);
no he tocado el front.

### Cambio 1: dos tests nuevos (commit `0827ad6`)

En `services/postventa-api/tests/test_fix_proveedor_nombre_recortado.py`, con el
mismo esquema (importación → editar sin tocar el proveedor). Los helpers aceptan
ahora un catálogo (`_catalogo_con(...)`, por defecto el de siempre):

- `test_fix_la_edicion_toma_el_primer_nombre_no_vacio_del_par`: filas de
  `obrofc` del par EJ07 con nombre `""` y luego `"Carpintería Ejemplo, S.L. "`;
  la importación y la edición guardan `"Carpintería Ejemplo, S.L."` y
  `cambios == ("descripcion",)`.
- `test_fix_el_nombre_en_blanco_se_guarda_none_como_en_la_importacion`: único
  nombre `"   "`; la importación y la edición guardan `None` y
  `cambios == ("descripcion",)`.

Con el código actual: `5 passed in 0.42s`.

Mutantes, aplicados con `sed` sobre `domain/models/revision.py`, ejecutando
`.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_fix_proveedor_nombre_recortado.py`
y revertidos con `git checkout -- domain/models/revision.py`:

M1 `if pares.get(clave) is None:` → `if clave not in pares:`:

```
E       AssertionError: assert ('descripcion', 'proveedor') == ('descripcion',)
E         Left contains one more item: 'proveedor'
FAILED tests/test_fix_proveedor_nombre_recortado.py::test_fix_la_edicion_toma_el_primer_nombre_no_vacio_del_par
1 failed, 4 passed in 0.81s
```

M2 `pares[clave] = nombre_recortado(fila.proveedor_nombre)` →
`pares[clave] = (fila.proveedor_nombre or "").strip()`:

```
E       AssertionError: assert ('descripcion', 'proveedor') == ('descripcion',)
E         Left contains one more item: 'proveedor'
E       AssertionError: assert ('descripcion', 'proveedor') == ('descripcion',)
E         Left contains one more item: 'proveedor'
FAILED tests/test_fix_proveedor_nombre_recortado.py::test_fix_la_edicion_toma_el_primer_nombre_no_vacio_del_par
FAILED tests/test_fix_proveedor_nombre_recortado.py::test_fix_el_nombre_en_blanco_se_guarda_none_como_en_la_importacion
2 failed, 3 passed in 0.65s
```

(M2 también lo caza el primero: con `""` en la primera fila, `pares.get` ya no
es `None` y se queda el vacío.)

Tras revertir, `git diff -- services/postventa-api/domain/models/revision.py`
sale **vacío**; `git status --short` solo mostraba el test, que es el que se
commiteó.

### `ARNES_SIN_CACHE=1 bash harness/init.sh` (raíz del worktree): EN VERDE

```
2202 passed, 48 skipped in 885.77s (0:14:45)
[OK] pytest en verde (con medición de cobertura)
10370 passed, 485 skipped in 1650.57s (0:27:30)
[OK] servicio api (services/postventa-api): pytest en verde
911 passed, 7 skipped in 24.01s
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: N/A (la rama fix/proveedor-nombre-recortado no corresponde a ninguna feature declarada)
[AVISO] PUERTA TAMAÑO: N/A (no hay papeleo abierto que medir ...)
[OK] PUERTA CARRIL: N/A (la rama fix/proveedor-nombre-recortado no corresponde a ninguna feature declarada)
[OK] CAPA E2E: N/A (sin feature en curso ...)
ENTORNO LISTO. Puedes trabajar.
```

(10370 = 10368 + los 2 tests nuevos.)

### Pendiente

- Cambio requerido 2 (`_pares` de `interface_adapters/api/revision.py`):
  decisión del humano entre alinearlo con `nombre_recortado` + primer no vacío
  (con test de ofrecido = guardado) o solo corregir el docstring.
- Oficio y unidad: siguen a decisión del humano.
- Nada de push.

## Segunda corrección: `_pares`

Punto 2 del review, decidido por el humano: alinear `_pares`
(`interface_adapters/api/revision.py`) con la importación y `validar_valores`.
Merge de `dev` d6be9d6 (trae 5e44232), RED b2768b8, GREEN 24acec3.

- `domain/models/plantilla_incidencias.py`: nueva `nombres_de_los_pares(proveedores)`
  (primer nombre no vacío del par con `nombre_recortado`; en blanco, `None`).
- `domain/models/revision.py`: `validar_valores` la usa (sale su bucle).
- `interface_adapters/api/revision.py`: `_pares` la usa; docstring corregido.
- `pares_del_desplegable` no se toca (filtra antes por oficio; misma regla).

RED (`.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_fix_proveedor_nombre_recortado.py`),
test parametrizado `test_fix_lo_que_ofrece_pares_es_lo_que_guarda_la_edicion`:

```
E         {'proveedor_nombre': 'Carpintería Ejemplo, S.L. '} != {'proveedor_nombre': 'Carpintería Ejemplo, S.L.'}
E         {'proveedor_nombre': ''} != {'proveedor_nombre': 'Carpintería Ejemplo, S.L.'}
E         {'proveedor_nombre': '   '} != {'proveedor_nombre': None}
FAILED ...[espacio-final]
FAILED ...[primera-fila-vacia]
FAILED ...[en-blanco]
3 failed, 5 passed in 3.71s
```

GREEN: `8 passed in 3.39s`; ficheros `*revision*`, `f036`, `f071` y el del arreglo:
`3004 passed, 24 skipped in 724.04s`.

Mutante (vuelta al `setdefault` con `fila.proveedor_nombre` crudo en `_pares`):
los mismos 3 fallos, `3 failed, 5 passed in 3.27s`. Revertido con
`git checkout --`; `git status --short` y `git diff --stat` vacíos.

`ARNES_SIN_CACHE=1 bash harness/init.sh`: EN VERDE. `2202 passed, 48 skipped`;
api `10382 passed, 485 skipped in 2562.97s`; front `911 passed, 7 skipped`;
COBERTURA, CARRIL y E2E N/A (rama sin feature); `ENTORNO LISTO`.
Incidencia: el venv del API estaba vacío; lo reconstruyó el líder.
Pendiente: review de esta corrección; oficio y unidad, a decisión del humano.
