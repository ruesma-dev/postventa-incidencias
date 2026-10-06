<!-- progress/impl_F-056.md -->
# F-056 · Revisión de la bandeja en el backend — Informe del implementer

Rama `feature/F-056-revision-bandeja-backend`. Rigor **`critico`**.
Spec: `specs/F-056-revision-bandeja-backend/` (aprobada el 2026-10-06).

**Base fija: `f86d639`** (el `dev` del que nace la rama, ya con F-053 cerrada; fijada por el líder el
2026-10-06). Las guardias de alcance y la mutación usan esa, no `349ba06`.

## T0 · Medición de la fuente de las ubicaciones (humano, 2026-10-06)

Copiada de `tasks.md` (solo recuentos, sin textos): en la 0677, 15 unidades de posventa, 0 sin
tipología, 3 tipologías distintas; `prmtpl.ubica` relleno en las 3, separado por `;`, con 35, 37 y 31
ubicaciones (58 distintas en la unión); las 44 ubicaciones distintas de `rcp.resubi` (tip 708) casan
exactas tras recortar (44/44) y cubren 1.261 de 1.261 reclamaciones. La lista trae alguna errata y
variantes de mayúsculas de Sigrid, que se respetan.

## Bloque 1 · El dominio (T1, T2, T3) · 2026-10-06

**Estado: BLOQUEADO** antes de T3. T1 y T2 hechas; la suite completa da **1 fallo**: una guardia de F-012
choca con `design.md` §4 (sección «Bloqueo», abajo). La feature está `blocked` en `harness/features.json`.

### Commits

| Commit | Qué |
|---|---|
| `1dbb67d` | **T1 · RED**: `tests/test_f056_revision_dominio.py`, `tests/test_f056_paginacion.py` (y la cabecera de este informe) |
| `fe20189` | **T2 · GREEN**: `domain/models/revision.py` (nuevo) y los ocho errores en `domain/models/errores.py` (solo se añade); T1 y T2 marcadas en `tasks.md` |
| `ac03f9d` | **T3, antes de la campaña** (no se ha lanzado): se quitan constantes que solo darían mutantes equivalentes —el origen del reloj (`datetime.min` en vez de 1970-01-01) y el `0` para las filas sin `fila_origen` (`_orden` compara `(fila is None, fila)`)—; el tope del cursor pasa a «menos de 512» (un base64url sin relleno nunca mide 513 y el mutante 512→513 no se podría matar); tests nuevos del `oid` de 1 carácter y de los cursores de 511 y 512 |

### Qué cambió

| Fichero | Cambio |
|---|---|
| `services/postventa-api/domain/models/revision.py` | **Nuevo.** Enumeraciones (`AccionRevision`, `EstadoRevision`, `MotivoNoAprobable` en el orden de R21, `FiltroEstado`), constantes, los tipos de §4 y las funciones de la tabla de §4 |
| `services/postventa-api/domain/models/errores.py` | **Solo añadido**: `PeticionDeRevisionInvalida`, `ValoresNoValidos` (`errores`: pares `(campo, problema)`), `SinCambios`, `IncidenciaNoEncontrada`, `AccionNoPermitida` (`estado`, `acciones`), `RevisionDesactualizada`, `IncidenciaNoAprobable` (`motivos`), `BandejaDemasiadoGrande` (`total`); y un párrafo del docstring del módulo |
| `services/postventa-api/tests/test_f056_revision_dominio.py` | **Nuevo** (R1–R3, R5, R7, R9, R13–R16, R18–R22, huella, `campos_cambiados`, R34, R35, R47, R48) |
| `services/postventa-api/tests/test_f056_paginacion.py` | **Nuevo** (R23, R25–R27, `fila_de_revision`) |
| `specs/F-056-revision-bandeja-backend/tasks.md` | T1 y T2 marcadas |

Nada fuera de `domain/` y `tests/`: ni puertos, ni SQL, ni aplicación, ni borde, ni front.

### Decisiones de diseño (dentro de la spec, salvo donde se dice)

1. **`listas`** se usa en `validar_valores` y `decidir`: la urgencia y el listado valen si son uno de los
   códigos que se ofrecen (`listas.urgencias`/`listados`, que el cargador del YAML ya obliga a ser del `Enum`):
   lo ofrecido es lo aceptado, como R28 pide para las ubicaciones. **`motivos_no_aprobable` no recibe
   `listas`** (la firma de §4 lo lleva): con D-4 ya no hay lista de ubicaciones de la plantilla y ningún motivo
   de R21 mira urgencias ni listados; un parámetro sin uso no se ha puesto.
2. **`sin_oficio`** es «ni código ni oficio ambiguo»: un oficio ambiguo da solo `oficio_ambiguo` (los 47 de
   la 0677 no salen dos veces).
3. **`par_fuera_de_la_obra`** solo se mira con código de oficio: con el oficio ambiguo no hay par que comprobar
   (y el motivo ya es `oficio_ambiguo`). Con un oficio fuera de la obra y proveedor, salen los dos motivos.
4. **La ubicación se recorta** (al validar, al guardar y al comparar en los motivos): R47 y §16.2 mandan sobre
   el «solo se recortan descripción, detalle, motivo y correo» de §4. Una ubicación `""` o de blancos es error
   (no se convierte en nula).
5. **Nombres de Sigrid** (R14): oficio y unidad sin nombre en Sigrid guardan su código (`unidad_nombre` es
   `NOT NULL`); el proveedor, el nombre de la **primera** fila de `obrofc` de su par (como hace
   `catalogo_obra.py` con dos nombres para un oficio). Consecuencia fijada en test: si Sigrid ha renombrado la
   unidad, editar con los mismos códigos **no** es `sin_cambios` (la foto refresca el nombre).
6. **Oficio no válido y proveedor**: solo el error del oficio; el par no se puede mirar.
7. **R15**: con el proveedor vigente se conserva su terna tal cual (código, nombre, ambigüedad); con otro, el
   error `("proveedor_codigo", "elige primero el código del oficio")`.
8. **Duplicada sin la original cargada** → motivo `duplicada` (lo que no se puede comprobar no se aprueba).
9. **La huella** es el `sha256` de la lista JSON de los 13 valores en el orden de los campos (UTF-8,
   `ensure_ascii=False`, separadores `,`/`:`, `Enum` por su valor): las comillas y el escapado son el
   «separador imposible» y `null` ≠ `""`. La receta está en el docstring para F-040; un test la recalcula.
10. **Tipos de más** respecto a §4, todos puros: `PeticionDeAccion` (el nombre de §7; con `valores` y `motivo`
    opcionales), `FilaDeRevision`, `Pagina`, `Resumen`, `fila_de_revision`, `candidata_de`, `CAMPOS_PEDIDOS`,
    `CAMPOS_LOGICOS` y `MAX_OID` (= `MAX_USUARIO_OID`, que vive en el borde y el dominio no puede importar; un
    test los iguala).
11. **`decidir`**, en este orden: misma incidencia (`ValueError`), forma (`valores` solo en editar y
    obligatorio en él; `motivo` solo en descartar → 400), transición (409), frescura (409), y solo en editar y
    aprobar el catálogo (sin él, `ValueError`: error de programación). Descartar y recuperar admiten
    `catalogo=None`. Las `esperadas` de `registrar` (la original en la aprobación de una duplicada, R22) son del
    Bloque 3.
12. **El cursor** tiene que ser exactamente el que emitiría `cursor_de` (canónico), de menos de 512
    caracteres, con `f` entero ≥ 1 o nulo, `c` con zona e `i` UUID; cualquier otra cosa →
    `PeticionDeRevisionInvalida` sin repetirlo. `paginar` ordena él mismo (no depende de quien llama).

### Fase RED (T1)

Comando, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f056_revision_dominio.py tests/test_f056_paginacion.py
```

Salida real (commit `1dbb67d`, antes de que existieran `revision.py` y los errores):

```
============================= test session starts =============================
platform win32 -- Python 3.12.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api
plugins: anyio-4.14.2
collected 0 items / 2 errors

=================================== ERRORS ====================================
____________ ERROR collecting tests/test_f056_revision_dominio.py _____________
ImportError while importing test module '...\services\postventa-api\tests\test_f056_revision_dominio.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f056_revision_dominio.py:39: in <module>
    from domain.models.errores import (
E   ImportError: cannot import name 'AccionNoPermitida' from 'domain.models.errores' (...\domain\models\errores.py)
_______________ ERROR collecting tests/test_f056_paginacion.py ________________
ImportError while importing test module '...\services\postventa-api\tests\test_f056_paginacion.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f056_paginacion.py:29: in <module>
    from domain.models.errores import PeticionDeRevisionInvalida
E   ImportError: cannot import name 'PeticionDeRevisionInvalida' from 'domain.models.errores' (...\domain\models\errores.py)
=========================== short test summary info ===========================
ERROR tests/test_f056_revision_dominio.py
ERROR tests/test_f056_paginacion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 2 errors in 2.06s ==============================
```

(Rutas absolutas del puesto acortadas con `...`.) Es un RED de recogida: ni el módulo ni los errores
existían. La prueba de que cada test caza algo concreto la dará la campaña de mutación (T3), pendiente.

### GREEN (T2)

```
.venv/Scripts/python.exe -m pytest tests/test_f056_revision_dominio.py tests/test_f056_paginacion.py tests/test_f005_arquitectura.py tests/test_f036_arquitectura.py
```

En `fe20189`: `366 passed in 16.92s`. Tras `ac03f9d` (dos tests más): `368 passed in 19.56s`; los dos de
F-056 solos, `350 passed`. Cobertura de líneas de `domain/models/revision.py` con esos dos ficheros
(`coverage run --include=domain/models/revision.py`): **454 sentencias, 0 sin cubrir, 100 %**.

### Suite completa: 1 fallo (el bloqueo)

`.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider` sobre `fe20189`:

```
FAILED tests/test_f012_arquitectura.py::test_f012_arquitectura_ni_domain_ni_application_nombran_base64
1 failed, 7054 passed, 56 skipped in 1200.41s (0:20:00)
```

```
>       assert culpables == []
E       AssertionError: assert ['domain/models/revision.py'] == []
```

### Bloqueo

`test_f012_arquitectura_ni_domain_ni_application_nombran_base64` prohíbe la **palabra** `base64` en
`domain/` y `application/` («el transporte es cosa del adaptador»; busca el texto, no solo el `import`). Y
`design.md` §4 pone `cursor_de(clave) -> str` y `clave_de_cursor(texto)` —el cursor «base64url» de R25— en
`domain/models/revision.py`. Las dos cosas no caben a la vez. No se ha tocado el test ni se ha movido nada
(encargo del líder: «no improvises: anótalo y para»).

| Opción | Qué supone |
|---|---|
| **(a) recomendada** | El dominio da y valida la clave en un **texto canónico** (el JSON de hoy, sin codificar: `texto_de_clave` / `clave_de_texto`, con la misma comprobación de canónico y los mismos 400). El borde (`interface_adapters/api/revision.py`, Bloque 3) pone y quita el base64url. R25 se cumple igual: lo que ve el cliente sigue siendo un base64url opaco. Cambia **dónde** vive la codificación (enmienda de una línea en §4) y los tests del cursor se reparten: forma canónica y manipulación en el dominio; el base64url y `eyJjIjoi…`, en los del borde. El tope de longitud se queda en el borde, sobre el texto codificado |
| (b) | Codificar en el dominio con otra cosa (hex…): incumple el «base64url» de R25 |
| (c) | Ampliar la excepción del test de F-012: toca una guardia ajena que existe por los partes con DNI |

**T3 no se ha lanzado**: la campaña recorre la suite completa por mutante (20 min solo, sin carga) y mutaría
`cursor_de`/`clave_de_cursor`, que la decisión va a cambiar.

### Pendiente para cerrar el Bloque 1

1. Decidir la opción (líder o humano) y aplicarla.
2. `.venv/Scripts/python.exe -m pytest tests -q` en verde.
3. **T3**: `python -m harness.mutacion --feature F-056 --base f86d639 --timeout 1800` →
   `progress/mutacion_F-056.md`, supervivientes por familias. Ya revisado de antemano (sin lanzar): se han
   quitado las tres fuentes de mutantes equivalentes que se veían (el origen del reloj, el `0` de las filas sin
   número y el 512→513 del tope del cursor).

### Evidencias (provisionales: falta T3)

| Evidencia | Valor |
|---|---|
| Tests de F-056 | 350 passed (9,0 s) |
| Suite completa del servicio | 7054 passed, **1 failed**, 56 skipped, 1200,4 s |
| Cobertura de `revision.py` (sus tests) | 100 % (454/454); la `PUERTA COBERTURA` de `init.sh` no se ha medido aún |
| Mutantes | **sin lanzar** (bloqueo) |
