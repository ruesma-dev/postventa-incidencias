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
