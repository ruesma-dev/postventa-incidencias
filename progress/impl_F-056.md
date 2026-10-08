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

## Bloque 1 · El dominio (T1, T2, T3) · 2026-10-06 a 2026-10-08

**Estado: HECHO, pendiente de review.** T1, T2 y T3 marcadas en `tasks.md`. El bloqueo del 2026-10-06 (guardia
de F-012 contra el cursor base64url de `design.md` §4) se resolvió con la **opción (a)**, aprobada por el
humano el 2026-10-07 (sección «Bloqueo (resuelto)», abajo). Suite completa del servicio **en verde** (7071
passed, 56 skipped) y campaña de mutación **153/153 muertos, 0 supervivientes**.

**Retomado el 2026-10-07** por otro implementer: el anterior se cortó al cerrarse la sesión, con un test sin
commitear (`test_f056_r34_los_tipos_de_la_revision_son_inmutables`). Revisado: cubre los **doce** dataclass de
`revision.py` (todos los `@dataclass(frozen=True)` del módulo) y comprueba que asignar el primer campo lanza
`FrozenInstanceError`; mata los mutantes `frozen=True → frozen=False`. Solo se reordenaron alfabéticamente sus
imports nuevos. Pasa (364 tests de F-056) y se commiteó en `9bcb38b`.

### Commits

| Commit | Qué |
|---|---|
| `1dbb67d` | **T1 · RED**: `tests/test_f056_revision_dominio.py`, `tests/test_f056_paginacion.py` (y la cabecera de este informe) |
| `fe20189` | **T2 · GREEN**: `domain/models/revision.py` (nuevo) y los ocho errores en `domain/models/errores.py` (solo se añade); T1 y T2 marcadas en `tasks.md` |
| `ac03f9d` | **T3, antes de la campaña** (no se ha lanzado): se quitan constantes que solo darían mutantes equivalentes —el origen del reloj (`datetime.min` en vez de 1970-01-01) y el `0` para las filas sin `fila_origen` (`_orden` compara `(fila is None, fila)`)—; el tope del cursor pasa a «menos de 512» (un base64url sin relleno nunca mide 513 y el mutante 512→513 no se podría matar); tests nuevos del `oid` de 1 carácter y de los cursores de 511 y 512 |
| `7809334` | Bloqueo: la feature a `blocked` (choque con la guardia de F-012; sección «Bloqueo (resuelto)») |
| `217debf` | **T2 · opción (a)** del humano: `cursor_de`/`clave_de_cursor` pasan a `texto_de_clave`/`clave_de_texto` (JSON canónico sin codificar, tope `MAX_TEXTO_CLAVE = 384` sobre el texto); tests de paginación ajustados; enmiendas de una línea en `design.md` §4, R25 y T12 de `tasks.md`; feature desbloqueada |
| `9bcb38b` | **T3, antes de la campaña**: test de inmutabilidad de los doce tipos (`frozen=True`) |
| (este commit) | **T3**: `progress/mutacion_F-056.md`, T3 marcada en `tasks.md` y este informe |

### Qué cambió

| Fichero | Cambio |
|---|---|
| `services/postventa-api/domain/models/revision.py` | **Nuevo.** Enumeraciones (`AccionRevision`, `EstadoRevision`, `MotivoNoAprobable` en el orden de R21, `FiltroEstado`), constantes, los tipos de §4 y las funciones de la tabla de §4 |
| `services/postventa-api/domain/models/errores.py` | **Solo añadido**: `PeticionDeRevisionInvalida`, `ValoresNoValidos` (`errores`: pares `(campo, problema)`), `SinCambios`, `IncidenciaNoEncontrada`, `AccionNoPermitida` (`estado`, `acciones`), `RevisionDesactualizada`, `IncidenciaNoAprobable` (`motivos`), `BandejaDemasiadoGrande` (`total`); y un párrafo del docstring del módulo |
| `services/postventa-api/tests/test_f056_revision_dominio.py` | **Nuevo** (R1–R3, R5, R7, R9, R13–R16, R18–R22, huella, `campos_cambiados`, R34, R35, R47, R48) |
| `services/postventa-api/tests/test_f056_paginacion.py` | **Nuevo** (R23, R25–R27, `fila_de_revision`) |
| `specs/F-056-revision-bandeja-backend/tasks.md` | T1, T2 y T3 marcadas; T12 con la nota de la opción (a) |
| `specs/F-056-revision-bandeja-backend/design.md`, `requirements.md` | Enmienda de la opción (a): §4 (`texto_de_clave`/`clave_de_texto`) y nota en R25 |
| `progress/mutacion_F-056.md` | **Nuevo**: informe de la campaña T3 |

Nada fuera de `domain/` y `tests/`: ni puertos, ni SQL, ni aplicación, ni borde, ni front.

### Decisiones de diseño (dentro de la spec, salvo donde se dice)

1. **`listas`** se usa en `validar_valores` y `decidir`: la urgencia y el listado valen si son uno de los
   códigos que se ofrecen (`listas.urgencias`/`listados`, que el cargador del YAML ya obliga a ser del `Enum`):
   lo ofrecido es lo aceptado, como R28 pide para las ubicaciones. **`motivos_no_aprobable` no recibe
   `listas`** (la firma de §4 lo lleva): con D-4 ya no hay lista de ubicaciones de la plantilla y ningún motivo
   de R21 mira urgencias ni listados; un parámetro sin uso no se ha puesto. **Ajuste de contrato aceptado por
   el líder** (2026-10-07).
2. **`sin_oficio`** es «ni código ni oficio ambiguo»: un oficio ambiguo da solo `oficio_ambiguo` (los 47 de
   la 0677 no salen dos veces); el oficio ambiguo **cuenta** como oficio a efectos de `sin_oficio`. **Ajuste de
   contrato aceptado por el líder** (2026-10-07).
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
12. **La clave del cursor (opción (a), 2026-10-07)**: el dominio da `texto_de_clave(clave)`, un JSON compacto
    `{c, f, i}` **sin codificar**, y `clave_de_texto(texto)` solo acepta exactamente el texto que emitiría
    `texto_de_clave` (canónico), de hasta `MAX_TEXTO_CLAVE = 384` caracteres, con `f` entero ≥ 1 o nulo, `c`
    con zona e `i` UUID; cualquier otra cosa → `PeticionDeRevisionInvalida` sin repetirlo. El base64url y el
    tope del cursor codificado son del borde (T12, Bloque 3). `paginar` ordena él mismo (no depende de quien
    llama).

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
existían. La prueba de que cada test caza algo concreto la da la campaña de mutación (T3): los 153 mutantes de
`revision.py` mueren (sección «Mutación (T3)»).

### GREEN (T2)

```
.venv/Scripts/python.exe -m pytest tests/test_f056_revision_dominio.py tests/test_f056_paginacion.py tests/test_f005_arquitectura.py tests/test_f036_arquitectura.py
```

En `fe20189`: `366 passed in 16.92s`. Tras `ac03f9d` (dos tests más): `368 passed in 19.56s`; los dos de
F-056 solos, `350 passed`. Cobertura de líneas de `domain/models/revision.py` con esos dos ficheros
(`coverage run --include=domain/models/revision.py`): **454 sentencias, 0 sin cubrir, 100 %**.

### Suite completa

**Antes del desbloqueo** (`fe20189`), `.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider`:

```
FAILED tests/test_f012_arquitectura.py::test_f012_arquitectura_ni_domain_ni_application_nombran_base64
1 failed, 7054 passed, 56 skipped in 1200.41s (0:20:00)
```

```
>       assert culpables == []
E       AssertionError: assert ['domain/models/revision.py'] == []
```

**Con la opción (a) aplicada** (`9bcb38b`, el mismo comando, desde `services/postventa-api`), el 2026-10-07:

```
7071 passed, 56 skipped in 798.07s (0:13:18)
```

La guardia de F-012 pasa sin tocarla: `revision.py` ya no nombra `base64`.

### Bloqueo (resuelto el 2026-10-07: opción (a))

`test_f012_arquitectura_ni_domain_ni_application_nombran_base64` prohíbe la **palabra** `base64` en
`domain/` y `application/` («el transporte es cosa del adaptador»; busca el texto, no solo el `import`). Y
`design.md` §4 pone `cursor_de(clave) -> str` y `clave_de_cursor(texto)` —el cursor «base64url» de R25— en
`domain/models/revision.py`. Las dos cosas no caben a la vez. No se ha tocado el test ni se ha movido nada
(encargo del líder: «no improvises: anótalo y para»).

| Opción | Qué supone |
|---|---|
| **(a) recomendada y APROBADA por el humano (2026-10-07)** | El dominio da y valida la clave en un **texto canónico** (el JSON de hoy, sin codificar: `texto_de_clave` / `clave_de_texto`, con la misma comprobación de canónico y los mismos 400). El borde (`interface_adapters/api/revision.py`, Bloque 3) pone y quita el base64url. R25 se cumple igual: lo que ve el cliente sigue siendo un base64url opaco. Cambia **dónde** vive la codificación (enmienda de una línea en §4) y los tests del cursor se reparten: forma canónica y manipulación en el dominio; el base64url y `eyJjIjoi…`, en los del borde. El tope de longitud se queda en el borde, sobre el texto codificado |
| (b) | Codificar en el dominio con otra cosa (hex…): incumple el «base64url» de R25 |
| (c) | Ampliar la excepción del test de F-012: toca una guardia ajena que existe por los partes con DNI |

**Qué se aplicó** (`217debf`): `cursor_de`/`clave_de_cursor` se renombraron a `texto_de_clave`/`clave_de_texto`
y dejaron de codificar; el tope pasa a `MAX_TEXTO_CLAVE = 384` sobre el texto JSON (los que se emiten rondan
los 90 caracteres). Los tests de paginación se ajustaron (forma canónica, manipulación, tope de 384/385) y la
forma base64url (`eyJjIjoi…`) y su manipulación quedan para los tests del borde (T10/T12, Bloque 3), como dice
la nota nueva de T12. El test de F-012 no se tocó.

### Mutación (T3)

Comando, desde la raíz, con el árbol limpio en `9bcb38b`:

```
python -m harness.mutacion --feature F-056 --base f86d639 --timeout 1800
```

(lanzado con `services/postventa-api/.venv/Scripts/python.exe`; 8 workers, los de `harness/rigor.json`).
Salida final:

```
Repaso en serie de 2 mutante(s) en timeout: sin concurrencia, el reloj mide al mutante y no a la máquina.
repaso [1/2] muerto        services/postventa-api/domain/models/revision.py:475 [logico] or not local -> and not local
repaso [2/2] muerto        services/postventa-api/domain/models/revision.py:561 [comparacion] if detalle is not None and len(detalle) > MAX_DETALLE: -> if detalle is not None and len(detalle) >= MAX_DETALLE:
153 mutantes evaluados, 153 muertos, 0 supervivientes, 0 timeouts en 20961.1 s
Informe: progress/mutacion_F-056.md
```

- **Alcance**: `revision.py` (1047 líneas, 153 mutantes) y `errores.py` (108 líneas añadidas, 0 mutantes: solo
  clases de error con atributos, sin operadores mutables).
- **Supervivientes: 0.** No hay familias que analizar ni mutantes equivalentes que justificar.
- **Timeouts: 2 en paralelo, 0 al final.** Los dos agotaron los 1800 s con 8 workers mientras la máquina corría
  también las suites de otros proyectos; repasados en serie, **los dos murieron**: era contención, no un cuelgue.
- Los mutantes que se preparó el terreno para matar antes de lanzar (`ac03f9d`, `9bcb38b`) murieron: las
  constantes de tope (`MAX_OID`, `MAX_TEXTO_CLAVE`, `TAMANO_*`, `MAX_MOTIVO`, `MIN/MAX_CORREO`,
  `TOPE_LECTURA_OBRA`, ±1) y los doce `frozen=True → frozen=False`.
- Tiempo: 20961 s (5 h 49 min) con 8 workers; cada mutante vivo hasta `test_f056_*` recorre ~93 % de la suite
  (172 de 185 ficheros van antes), por eso cuesta casi una suite entera aunque muera.

### Verificaciones MANUAL pendientes

Ninguna en este bloque (dominio puro: sin red, BBDD ni IA).

### Fuera del alcance de este bloque

Puertos, SQL, DDL, aplicación, borde HTTP (incluido el base64url del cursor) y front: Bloques 2, 3 y 3 bis.

### Observación para el líder

Quedan **8 worktrees huérfanos** de la campaña que el implementer anterior lanzó y no terminó
(`%TEMP%/mutacion_F-056_s_f9l24k/wk_0..7`, en `217debf`, sin procesos vivos). Los de esta campaña se limpiaron
solos. No se han borrado (no son de este encargo): `git worktree remove --force` de cada uno, si se quiere.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de F-056 (`test_f056_revision_dominio.py`, `test_f056_paginacion.py`) | **364 passed** (6,3 s) |
| Suite completa del servicio | **7071 passed, 0 failed, 56 skipped**, 798,1 s |
| Cobertura de `revision.py` (sus tests, `coverage run --include`) | **100 %** (449/449 sentencias) |
| Cobertura de las líneas cambiadas (`PUERTA COBERTURA` de `init.sh`) | **100,0 %** (486/486 líneas cambiadas, umbral 80 %, nivel `critico`) |
| Mutantes | **153 generados, 153 muertos, 0 supervivientes, 0 timeouts** (2 repasados en serie, muertos); 20961 s, 8 workers |
| `bash harness/init.sh` | **ENTORNO LISTO** (2026-10-08): servicio api 7071 passed, 81 skipped en 1451,9 s (con medición de cobertura); front en verde por caché; arnés 115 passed; ruff 74 avisos de deuda previa, no bloquea |

## Bloque 2 · La tabla y el repositorio (T4–T7, T9; T8 MANUAL) · 2026-10-08

**Estado: EN CURSO.** Encargo del líder del 2026-10-08: T4 (RED), T5, T6, T7 y T9, más N-1, N-2, O-1, O-2 y O-4 de
la review del Bloque 1. T8 es MANUAL del humano. Base de la mutación del bloque: `b88b5ef` (el commit anterior al
bloque, fijado por el líder).

### O-1 · Fase RED (antes del código)

Comando, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f056_revision_dominio.py -q -k "candidata_con_ubicacion" -p no:cacheprovider
```

Salida real (cola), con `CandidataAlVolcado` todavía sin la comprobación:

```
tests\test_f056_revision_dominio.py:1745: Failed
=========================== short test summary info ===========================
FAILED tests/test_f056_revision_dominio.py::test_f056_r35_candidata_con_ubicacion_sin_recortar_o_larga[ Ba\xf1o]
FAILED tests/test_f056_revision_dominio.py::test_f056_r35_candidata_con_ubicacion_sin_recortar_o_larga[Ba\xf1o ]
FAILED tests/test_f056_revision_dominio.py::test_f056_r35_candidata_con_ubicacion_sin_recortar_o_larga[\tBa\xf1o]
FAILED tests/test_f056_revision_dominio.py::test_f056_r35_candidata_con_ubicacion_sin_recortar_o_larga[Ba\xf1o\n]
FAILED tests/test_f056_revision_dominio.py::test_f056_r35_candidata_con_ubicacion_sin_recortar_o_larga[]
FAILED tests/test_f056_revision_dominio.py::test_f056_r35_candidata_con_ubicacion_sin_recortar_o_larga[   ]
FAILED tests/test_f056_revision_dominio.py::test_f056_r35_candidata_con_ubicacion_sin_recortar_o_larga[xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx]
7 failed, 3 passed, 291 deselected in 0.83s
```

Los 7 casos de «sin recortar, vacía o de 49» fallan por `DID NOT RAISE ValueError`; los 3 de «recortada y de hasta
48» pasan (ya pasaban: son el control positivo).

### T4 · Fase RED

Con **esqueletos de valores neutros** (O-2): `domain/ports/revision.py` (un `Protocol` vacío),
`sentencias_revision.py` (cada función devuelve `("", ())` o `None`), `repositorio_revision_pg.py` (devuelve `()`,
`0` o `None`), `construir_revision` (devuelve un repositorio sin conexión) y `15_revisiones_bandeja.sql` (solo las
dos primeras líneas de cabecera, sin sentencias). Así cada test falla **por su aserción**, no por un
`ImportError` de recogida.

Comando, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f056_ddl.py tests/test_f056_repositorio_revision.py -q -p no:cacheprovider --tb=no -rfp
```

Salida real (motivos recortados a 150 caracteres):

```
.FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF..F.FFFFFFFFFFFFFFFFFFFFFFFFFFFFF. [ 54%]
..FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF.FFF            [100%]
=========================== short test summary info ===========================
FAILED tests/test_f056_ddl.py::test_f056_r36_la_guarda_real_acepta_cada_sentencia_y_son_dos
FAILED tests/test_f056_ddl.py::test_f056_r36_el_ddl_real_entero_se_carga_con_el_fichero
FAILED tests/test_f056_ddl.py::test_f056_r36_todo_es_idempotente - assert ()
FAILED tests/test_f056_ddl.py::test_f056_r37_ni_datos_ni_escrituras_ni_borrados_en_el_ddl
FAILED tests/test_f056_ddl.py::test_f056_r36_todo_cualificado_sin_public_ni_ambito_de_servidor
FAILED tests/test_f056_ddl.py::test_f056_r36_sin_columnas_binarias_ni_json - ...
FAILED tests/test_f056_ddl.py::test_f056_r36_un_esquema_configurado_distinto_se_sustituye_entero
FAILED tests/test_f056_ddl.py::test_f056_r36_la_cabecera_dice_que_construye_y_de_que_lee
FAILED tests/test_f056_ddl.py::test_f056_r36_la_cabecera_explica_la_tabla_y_el_correo[APPEND-ONLY]
FAILED tests/test_f056_ddl.py::test_f056_r36_la_cabecera_explica_la_tabla_y_el_correo[revision_id]
FAILED tests/test_f056_ddl.py::test_f056_r36_la_cabecera_explica_la_tabla_y_el_correo[NO SE GUARDA EL ESTADO]
FAILED tests/test_f056_ddl.py::test_f056_r36_la_cabecera_explica_la_tabla_y_el_correo[revisado_por]
FAILED tests/test_f056_ddl.py::test_f056_r36_la_cabecera_explica_la_tabla_y_el_correo[revisado_correo]
FAILED tests/test_f056_ddl.py::test_f056_r36_la_cabecera_explica_la_tabla_y_el_correo[empleado interno]
FAILED tests/test_f056_ddl.py::test_f056_r36_la_cabecera_explica_la_tabla_y_el_correo[NUNCA va a un log]
FAILED tests/test_f056_ddl.py::test_f056_r36_la_cabecera_explica_la_tabla_y_el_correo[GET /api/revision]
FAILED tests/test_f056_ddl.py::test_f056_r36_la_cabecera_explica_la_tabla_y_el_correo[ON DELETE CASCADE]
FAILED tests/test_f056_ddl.py::test_f056_r36_la_cabecera_explica_la_tabla_y_el_correo[F-040]
FAILED tests/test_f056_ddl.py::test_f056_r36_la_cabecera_explica_la_tabla_y_el_correo[F-048]
FAILED tests/test_f056_ddl.py::test_f056_r36_las_columnas_son_las_del_diseno_y_ninguna_mas
FAILED tests/test_f056_ddl.py::test_f056_r36_declaraciones_de_las_columnas - ...
FAILED tests/test_f056_ddl.py::test_f056_r36_el_check_de_accion_es_el_enum_del_dominio
FAILED tests/test_f056_ddl.py::test_f056_r36_los_check_de_urgencia_y_listado_son_los_de_la_bandeja[urgencia-Urgencia]
FAILED tests/test_f056_ddl.py::test_f056_r36_los_check_de_urgencia_y_listado_son_los_de_la_bandeja[listado-Listado]
FAILED tests/test_f056_ddl.py::test_f056_r36_los_check_de_ambiguedad_de_la_bandeja_se_repiten[CHECK (NOT oficio_ambiguo OR (oficio_codigo IS NULL AND oficio_nombre IS NOT NULL))]
FAILED tests/test_f056_ddl.py::test_f056_r36_los_check_de_ambiguedad_de_la_bandeja_se_repiten[CHECK (NOT proveedor_ambiguo OR (proveedor_codigo IS NULL AND proveedor_nombre IS NOT NULL))]
FAILED tests/test_f056_ddl.py::test_f056_r36_los_check_de_ambiguedad_de_la_bandeja_se_repiten[CHECK (proveedor_nombre IS NULL OR oficio_nombre IS NOT NULL)]
FAILED tests/test_f056_ddl.py::test_f056_r36_los_check_de_longitud_y_valor_son_los_de_la_bandeja[ubicacion]
FAILED tests/test_f056_ddl.py::test_f056_r36_los_check_de_longitud_y_valor_son_los_de_la_bandeja[descripcion]
FAILED tests/test_f056_ddl.py::test_f056_r36_los_check_de_longitud_y_valor_son_los_de_la_bandeja[detalle]
FAILED tests/test_f056_ddl.py::test_f056_r36_los_check_de_longitud_y_valor_son_los_de_la_bandeja[urgencia]
FAILED tests/test_f056_ddl.py::test_f056_r36_los_check_de_longitud_y_valor_son_los_de_la_bandeja[listado]
FAILED tests/test_f056_ddl.py::test_f056_r18_el_motivo_solo_va_en_descartar
FAILED tests/test_f056_ddl.py::test_f056_r36_la_tabla_lleva_exactamente_doce_check
FAILED tests/test_f056_ddl.py::test_f056_r36_ni_unique_ni_estado_guardado - A...
FAILED tests/test_f056_ddl.py::test_f056_r38_el_indice_da_la_ultima_revision_por_revision_id
FAILED tests/test_f056_ddl.py::test_f056_r12_la_unica_columna_de_correo_del_esquema_es_revisado_correo
FAILED tests/test_f056_repositorio_revision.py::test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5
FAILED tests/test_f056_repositorio_revision.py::test_f056_r24_listar_pide_tope_mas_uno_filas_de_la_obra
FAILED tests/test_f056_repositorio_revision.py::test_f056_r25_listar_en_el_orden_total_de_r25
FAILED tests/test_f056_repositorio_revision.py::test_f056_r22_r38_cada_situacion_trae_su_ultima_y_la_de_su_original[situaciones_de_obra]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r22_r38_cada_situacion_trae_su_ultima_y_la_de_su_original[situacion]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r22_r38_cada_situacion_trae_su_ultima_y_la_de_su_original[aprobadas]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_las_situaciones_leen_estas_columnas_en_este_orden[situaciones_de_obra]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_las_situaciones_leen_estas_columnas_en_este_orden[situacion]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_las_situaciones_leen_estas_columnas_en_este_orden[aprobadas]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_ninguna_lectura_selecciona_revisado_por[situaciones_de_obra]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_ninguna_lectura_selecciona_revisado_por[situacion]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_ninguna_lectura_selecciona_revisado_por[aprobadas]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_ninguna_lectura_selecciona_revisado_por[contar]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_ninguna_lectura_selecciona_revisado_por[bloquear]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_ninguna_lectura_selecciona_revisado_por[ultimas]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_ninguna_lectura_selecciona_revisado_por[revisiones]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_el_correo_si_se_lee[situaciones_de_obra]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_el_correo_si_se_lee[situacion]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_el_correo_si_se_lee[aprobadas]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_el_correo_si_se_lee[revisiones]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r23_situacion_por_su_id
FAILED tests/test_f056_repositorio_revision.py::test_f056_r34_aprobadas_solo_con_la_ultima_aprobar
FAILED tests/test_f056_repositorio_revision.py::test_f056_r24_contar_las_de_la_obra
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_el_bloqueo_es_for_update_de_la_bandeja_en_orden_fijo
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_r38_la_frescura_es_la_mayor_revision_id_de_cada_una
FAILED tests/test_f056_repositorio_revision.py::test_f056_r33_el_historial_de_la_mas_antigua_a_la_mas_reciente
FAILED tests/test_f056_repositorio_revision.py::test_f056_r4_el_insert_es_una_fila_con_la_foto_el_oid_y_el_correo
FAILED tests/test_f056_repositorio_revision.py::test_f056_r4_sin_urgencia_ni_listado_van_nulos
FAILED tests/test_f056_repositorio_revision.py::test_f056_o4_no_se_escribe_una_hora_sin_zona
FAILED tests/test_f056_repositorio_revision.py::test_f056_r17_r37_la_unica_escritura_es_el_insert_en_revisiones
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_cada_sentencia_con_el_esquema_configurado[aprobadas]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_cada_sentencia_con_el_esquema_configurado[bloquear]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_cada_sentencia_con_el_esquema_configurado[contar]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_cada_sentencia_con_el_esquema_configurado[insert]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_cada_sentencia_con_el_esquema_configurado[revisiones]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_cada_sentencia_con_el_esquema_configurado[situacion]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_cada_sentencia_con_el_esquema_configurado[situaciones_de_obra]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_cada_sentencia_con_el_esquema_configurado[ultimas]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_un_esquema_hostil_no_llega_al_sql[<lambda>0]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_un_esquema_hostil_no_llega_al_sql[<lambda>1]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_un_esquema_hostil_no_llega_al_sql[<lambda>2]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_un_esquema_hostil_no_llega_al_sql[<lambda>3]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_un_esquema_hostil_no_llega_al_sql[<lambda>4]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_un_esquema_hostil_no_llega_al_sql[<lambda>5]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_un_esquema_hostil_no_llega_al_sql[<lambda>6]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r36_un_esquema_hostil_no_llega_al_sql[<lambda>7]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r1_una_fila_sin_revisiones_ni_original
FAILED tests/test_f056_repositorio_revision.py::test_f056_r22_una_fila_con_su_ultima_y_su_original_con_la_suya
FAILED tests/test_f056_repositorio_revision.py::test_f056_r22_la_original_sin_revisiones
FAILED tests/test_f056_repositorio_revision.py::test_f056_r29_los_tipos_de_la_fila_web_y_los_enum
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_la_revision_leida_lleva_el_correo_y_los_enum
FAILED tests/test_f056_repositorio_revision.py::test_f056_r10_una_revision_admite_uuid_en_texto
FAILED tests/test_f056_repositorio_revision.py::test_f056_o4_las_fechas_vuelven_con_zona_y_en_utc
FAILED tests/test_f056_repositorio_revision.py::test_f056_o4_una_fecha_sin_zona_no_se_adivina[creada]
FAILED tests/test_f056_repositorio_revision.py::test_f056_o4_una_fecha_sin_zona_no_se_adivina[revisada]
FAILED tests/test_f056_repositorio_revision.py::test_f056_o4_una_fecha_sin_zona_no_se_adivina[creada_original]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r24_listar_devuelve_todo_lo_que_trae_la_base_sin_truncar
FAILED tests/test_f056_repositorio_revision.py::test_f056_r24_contar - Assert...
FAILED tests/test_f056_repositorio_revision.py::test_f056_r6_situacion_que_no_existe_es_none
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_situacion_con_su_ultima
FAILED tests/test_f056_repositorio_revision.py::test_f056_r4_r7_registrar_bloquea_comprueba_inserta_y_confirma
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_la_primera_revision_espera_ninguna
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_r22_bloquea_las_dos_en_orden_fijo_y_mira_las_dos
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_r22_si_no_cuadra_no_escribe_y_deshace[otra-guardo-la-primera]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_r22_si_no_cuadra_no_escribe_y_deshace[otra-guardo-despues]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_r22_si_no_cuadra_no_escribe_y_deshace[la-esperada-no-existe]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_r22_si_no_cuadra_no_escribe_y_deshace[la-original-gano-una]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_r22_si_no_cuadra_no_escribe_y_deshace[la-original-cambio]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_r22_si_no_cuadra_no_escribe_y_deshace[la-original-perdio-las-suyas]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_registrar_exige_la_frescura_de_la_propia
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_si_la_base_falla_es_503_y_nada_a_medias[FOR UPDATE]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_si_la_base_falla_es_503_y_nada_a_medias[max(revision_id)]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r7_si_la_base_falla_es_503_y_nada_a_medias[INSERT INTO]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r41_el_log_de_registrar_no_lleva_ni_oid_ni_correo_ni_textos
FAILED tests/test_f056_repositorio_revision.py::test_f056_r30_si_la_base_no_responde_al_leer_es_503[<lambda>0]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r30_si_la_base_no_responde_al_leer_es_503[<lambda>1]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r30_si_la_base_no_responde_al_leer_es_503[<lambda>2]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r30_si_la_base_no_responde_al_leer_es_503[<lambda>3]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r30_si_la_base_no_responde_al_leer_es_503[<lambda>4]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r33_historial_la_situacion_y_sus_revisiones_en_una_transaccion
FAILED tests/test_f056_repositorio_revision.py::test_f056_r32_historial_de_una_que_no_existe_es_none
FAILED tests/test_f056_repositorio_revision.py::test_f056_r34_r35_aprobadas_da_las_candidatas_al_volcado
FAILED tests/test_f056_repositorio_revision.py::test_f056_r34_si_la_base_devolviera_otra_cosa_que_un_aprobar_no_pasa[editar]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r34_si_la_base_devolviera_otra_cosa_que_un_aprobar_no_pasa[descartar]
FAILED tests/test_f056_repositorio_revision.py::test_f056_r34_si_la_base_devolviera_otra_cosa_que_un_aprobar_no_pasa[recuperar]
FAILED tests/test_f056_repositorio_revision.py::test_f056_t6_construir_revision_abre_fija_la_sesion_y_asegura_el_esquema
FAILED tests/test_f056_repositorio_revision.py::test_f056_t6_sin_contrasena_construir_revision_no_abre_nada
FAILED tests/test_f056_repositorio_revision.py::test_f056_t6_si_no_se_puede_conectar_es_503
PASSED tests/test_f056_ddl.py::test_f056_r36_el_fichero_va_detras_de_los_de_f036
PASSED tests/test_f056_ddl.py::test_f056_r36_las_acciones_son_las_cuatro_de_la_spec
PASSED tests/test_f056_ddl.py::test_f056_r36_las_longitudes_son_las_de_la_spec
PASSED tests/test_f056_repositorio_revision.py::test_f056_r34_el_repositorio_cumple_el_puerto
PASSED tests/test_f056_repositorio_revision.py::test_f056_r37_el_codigo_no_actualiza_ni_borra_ni_hace_ddl[sentencias_revision.py]
PASSED tests/test_f056_repositorio_revision.py::test_f056_r37_el_codigo_no_actualiza_ni_borra_ni_hace_ddl[repositorio_revision_pg.py]
PASSED tests/test_f056_repositorio_revision.py::test_f056_r37_el_control_del_codigo_caza_un_update
PASSED tests/test_f056_repositorio_revision.py::test_f056_r34_aprobadas_sin_ninguna
125 failed, 8 passed in 1.08s
```

Con `--tb=line`, los 125 fallos se reparten en **81 `AssertionError`, 32 `Failed: DID NOT RAISE …` y 12 `assert …`**:
ningún `ImportError`, `AttributeError` ni `IndexError` (tres tests se ajustaron para comprobar el tipo antes de
leer un atributo, y que fallaran por aserción).

**Los 8 que pasan en RED, y por qué no importa:**

| Test | Por qué pasa con el esqueleto |
|---|---|
| `test_f056_r36_el_fichero_va_detras_de_los_de_f036` | El esqueleto `15_…sql` ya existe con su nombre: el orden es del nombre, no del contenido |
| `test_f056_r36_las_acciones_son_las_cuatro_de_la_spec`, `…_las_longitudes_son_las_de_la_spec` | Fijan el dominio del Bloque 1 a mano (el control de los tests que comparan con el `.sql`) |
| `test_f056_r34_el_repositorio_cumple_el_puerto` | Un `Protocol` vacío lo cumple cualquiera; lo que muerde es `…_tiene_las_seis_operaciones_de_5`, que sí falla |
| `test_f056_r37_el_codigo_no_actualiza_ni_borra_ni_hace_ddl` (×2) | Un esqueleto sin SQL no tiene `UPDATE`: es una guarda negativa, que tiene que seguir en verde |
| `test_f056_r37_el_control_del_codigo_caza_un_update` | Control negativo de la guarda anterior, sobre un texto en memoria |
| `test_f056_r34_aprobadas_sin_ninguna` | Sin filas, `()` es la respuesta correcta y la neutra a la vez |

### Commits

| Commit | Qué |
|---|---|
| `916fa49` | **N-2**: `ruff --fix` (I001) de `tests/test_f056_paginacion.py` |
| `4a41ba4` | **N-1**: `design.md` §4 (firma de `motivos_no_aprobable` sin `listas`), §3.5 (recuadro «Aceptado por el líder el 2026-10-07» y las interpretaciones 3 y 4), §3.6 (interpretación 8) y §8 (la ubicación vacía es error) |
| `dd64e09` | **O-1**: `CandidataAlVolcado` exige la ubicación recortada y de ≤ 48, test primero; nota en `design.md` §10 |
| `6e30f73` | **T4 · RED**: `test_f056_ddl.py`, `test_f056_repositorio_revision.py`, esqueletos neutros (O-2) y la ampliación de los tests que enumeran los `.sql` |
| `47fdbe1` | **T5**: `15_revisiones_bandeja.sql` |
| `72a8c29` | **T6**: puerto, `sentencias_revision.py`, `repositorio_revision_pg.py`, `construir_revision` |
| `e15fcac` | **T6, antes de la mutación**: dos tests de ancho exacto de fila (`strict`) y la revisión ausente sin índice literal |
| `8a52dcc` | **T7**: `tests_bbdd/tests/test_f056_bbdd_revision.py` |
| `94c0482` | T4–T7 marcadas en `tasks.md` |
| (este commit) | **T9**: `progress/mutacion_F-056_bloque2.md`, T9 marcada y este informe |

### Qué cambió

| Fichero | Cambio |
|---|---|
| `services/postventa-api/infrastructure/persistencia/sql/15_revisiones_bandeja.sql` | **Nuevo.** La tabla de §6, tal cual, y su índice `(incidencia_id, revision_id DESC)`; cabecera de §6 y §9 (append-only, el estado no se guarda, `revisado_por` no sale, el correo de empleado interno que nunca va a un log, el `CHECK` de `accion` no se amplía —F-040 lleva su tabla—, sin cascada, listas para F-048). ASCII, como el resto de `.sql` |
| `services/postventa-api/domain/ports/revision.py` | **Nuevo.** `RevisionPort` con las seis operaciones de §5 |
| `services/postventa-api/infrastructure/persistencia/sentencias_revision.py` | **Nuevo, puro.** Las ocho sentencias (situaciones de la obra con `LIMIT tope + 1`, situación, aprobadas, contar, bloquear, frescura, insert, historial) y la traducción de filas a dominio |
| `services/postventa-api/infrastructure/persistencia/repositorio_revision_pg.py` | **Nuevo.** `RepositorioRevisionPostgres(_Transaccional)` |
| `services/postventa-api/infrastructure/persistencia/fabrica.py` | **Solo añadido**: `construir_revision` y una línea del docstring del módulo |
| `services/postventa-api/domain/models/revision.py` | O-1: la comprobación de la ubicación en `CandidataAlVolcado.__post_init__` y su docstring |
| `services/postventa-api/tests/test_f056_ddl.py`, `test_f056_repositorio_revision.py` | **Nuevos** (40 + 95 tests) |
| `services/postventa-api/tests/test_f056_revision_dominio.py` | O-1: 10 casos nuevos (7 imposibles, 3 válidos) |
| `services/postventa-api/tests/test_f056_paginacion.py` | N-2: orden de imports |
| `services/postventa-api/tests_bbdd/tests/test_f056_bbdd_revision.py` | **Nuevo** (28 casos; se saltan sin `POSTVENTA_PG_TEST_DSN`) |
| Tests que enumeran los `.sql` (**ampliados, sin quitar nada**) | `test_f005_ddl_idempotente_texto.py` (la lista entera, +1), `test_f036_ddl.py` (`nombres[-3:]` pasa a «lo que va tras el 11 es 12, 13, 14 y 15»), `test_f028_ddl_historico.py` (la cola tras el 11, +1) y `test_f030_veredicto_persistido.py`, `test_f031…f034_alcance_cerrado.py` (`DDL_DE_F056` junto a `DDL_DE_F036`, el patrón con que F-036 los amplió) |
| `specs/F-056-revision-bandeja-backend/design.md` | N-1 y la nota de O-1 en §10 |
| `specs/F-056-revision-bandeja-backend/tasks.md` | T4–T7 y T9 marcadas (T8 no) |

Nada del front, de `function_app.py`, de `application/` ni de `infrastructure/sigrid/`.

### Decisiones de diseño (dentro de la spec, salvo donde se dice)

1. **N-1, la redacción del encargo.** El encargo dice «en §3.5 di que el oficio ambiguo cuenta como `sin_oficio`»;
   lo aceptado el 2026-10-07 (decisión 2 del Bloque 1, N-1 de la review) y lo que hace el código es **lo
   contrario**: el oficio ambiguo **cuenta como oficio** a efectos de `sin_oficio` (da solo `oficio_ambiguo`). Se
   ha escrito lo aceptado, que es lo que fijan los tests y T19 (`oficio_ambiguo` = 47 sin inflar `sin_oficio`).
   **Que el líder lo confirme**; si de verdad se quería lo literal, es un cambio de contrato y de código, no de
   redacción.
2. **Las interpretaciones 3, 4 y 8** van en el design como «interpretaciones del implementer, revisadas en la
   review», **no** bajo el recuadro «Aceptado por el líder el 2026-10-07», que cubre solo los ajustes 1 y 2 (los
   que el líder aceptó ese día). La 3 y la 4 en §3.5 (y la 4 también en §8, el contrato con F-038); la 8 en §3.6.
3. **O-1 sin `CHECK` en el DDL.** No encaja con §6: un `CHECK` de recorte valdría para **todas** las acciones (una
   fila importada con blancos no se podría ni descartar), no se podría cambiar después, y `btrim` de PostgreSQL no
   recorta lo mismo que `str.strip()` (solo espacios). §6 deja «aprobar exige oficio y ubicación» en el dominio;
   la comprobación vive en `CandidataAlVolcado`. Nota en `design.md` §10.
4. **`construir_revision` no entra en `__all__` de `fabrica.py`**:
   `test_f036_t15_la_fabrica_exporta_las_tres_construcciones` fija la lista exacta y R45 pide no tocar los tests de
   F-036. Se importa por su nombre; su docstring lo explica.
5. **Tests de otras features tocados (R45).** `tasks.md` T4 manda ampliar «los tests que enumeran `.sql`» y cita
   `test_f005_ddl_idempotente_texto.py` y `test_f036_ddl.py`. Al añadir el `15_` caen **además** seis tests de
   F-028 y F-030…F-034 que fijan la lista de `.sql` (la mitad que no depende de `git`). Se han **ampliado** igual,
   sin relajar nada, con el patrón que usó F-036 (`DDL_DE_F036` → `+ DDL_DE_F056`). `test_f036_ddl.py` es el único
   de F-036 tocado, y lo autoriza T4 expresamente; ninguno de F-053.
6. **`_Transaccional` reutilizado** de `repositorio_bandeja_pg.py` (import de un nombre privado): la misma forma de
   transacción, `rollback` y 503 sin parámetros, sin duplicarla ni tocar el módulo de F-036.
7. **`registrar` exige la propia incidencia en `esperadas`** (`ValueError`, sin abrir nada): sin ella no hay
   frescura que comprobar. Bloquea y comprueba **todas** las esperadas (la propia y, al aprobar una duplicada, la
   original), en orden fijo y sin repetidas.
8. **`aprobadas`, doble defensa**: el filtro `u.accion = 'aprobar'` está en el SQL y, además, cada fila pasa por
   `candidata_de` del dominio, que lanza si no es una aprobación (y `CandidataAlVolcado`, si no es volcable). Un SQL
   equivocado no puede dar a F-040 algo que no se aprobó: falla en vez de colarse.
9. **`listar` no corta**: devuelve las `tope + 1` que da la base; el 409 de R24 lo decide la aplicación (Bloque 3)
   con `contar`.
10. **O-4, fechas**: `creada_at_utc` y `revisado_at_utc` vuelven en **UTC** (`astimezone`, el mismo instante) y una
    sin zona es `ValueError`; también al **escribir** una `revisado_at_utc` sin zona (en `timestamptz` se
    interpretaría en la zona de la sesión).
11. **Una revisión ausente** (el `LEFT JOIN LATERAL` sin fila) se reconoce porque **todas** sus columnas son nulas,
    no por la primera: con `ultima[0]`, el mutante `0 → 1` habría sido equivalente (`revision_id` e
    `incidencia_id` son nulos a la vez). Y las filas se leen con `zip(…, strict=True)`: una columna de más o de
    menos es un SQL que ya no casa con su traducción, y falla (dos tests lo fijan).
12. **El historial** lee la situación y las revisiones con dos `SELECT` en la misma transacción. En `READ
    COMMITTED` no es una sola foto, pero de la situación solo se usan los datos de la importación (R33), que no
    cambian.
13. **`tests_bbdd`: la limpieza borra filas.** Es lo único con `DELETE` de F-056, y solo contra la base efímera: sin
    vaciar `revisiones_bandeja`, la limpieza de `test_f036_bbdd_bandeja.py` chocaría con la clave ajena. R37 habla
    del código del servicio (el test de R37 de T4 mira `sentencias_revision.py` y `repositorio_revision_pg.py`);
    **para T13**, el alcance de R37 no debe barrer `tests_bbdd/`, igual que F-036 con su propia limpieza.
14. **Las 10.001 filas** de T7 se crean en la base con `generate_series` (con `CAST` explícitos), no desde Python.

### GREEN

T5, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f056_ddl.py tests/test_f005_ddl_idempotente_texto.py tests/test_f036_ddl.py tests/test_f028_ddl_historico.py tests/test_f026_ddl_aprobaciones.py tests/test_f005_ddl_seguro.py tests/test_f005_ddl_orden.py tests/test_f005_ddl_troceado.py -q -p no:cacheprovider
262 passed in 3.72s
```

T6:

```
.venv/Scripts/python.exe -m pytest tests/test_f056_repositorio_revision.py tests/test_f056_ddl.py -q -p no:cacheprovider
133 passed in 1.10s
```

(135 tras `e15fcac`.) Cobertura de los módulos nuevos con `test_f056_repositorio_revision.py` (`coverage run
--include`): `ports/revision.py` 14/14, `repositorio_revision_pg.py` 57/57, `sentencias_revision.py` 86/86: **100 %**;
en `fabrica.py`, ese fichero solo deja sin cubrir las tres construcciones de F-005/F-036, no la de F-056.

Guardias de arquitectura y vecinos, sin caché:

```
.venv/Scripts/python.exe -m pytest tests/test_f00*_arquitectura.py tests/test_f012_arquitectura.py tests/test_f013_arquitectura.py tests/test_f036_arquitectura.py tests/test_f036_repositorio_bandeja.py tests/test_f036_alcance_cerrado.py tests/test_f005_sentencias.py tests/test_f006_repo_sin_identificadores.py tests/test_f005_integracion_sin_secretos.py -q -p no:cacheprovider
457 passed, 9 skipped in 42.78s
```

T7, la verificación de la tarea:

```
.venv/Scripts/python.exe -m pytest --collect-only tests_bbdd/tests/test_f056_bbdd_revision.py -q -p no:cacheprovider
28 tests collected in 0.27s
```

(y sin DSN, `28 skipped`). `ruff check` (desde la raíz) de los ficheros nuevos o tocados de F-056: sin avisos
nuevos; los I001 de `test_f005_ddl_idempotente_texto.py` y `test_f028_ddl_historico.py` son **previos**
(comprobado con `git stash` sobre `HEAD`).

### Suite completa

`.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider`, desde `services/postventa-api`, en `94c0482`
(antes de la mutación):

```
7219 passed, 56 skipped in 510.73s (0:08:30)
```

### Mutación (T9)

Comando, desde la raíz, con el árbol limpio en `94c0482`:

```
python -m harness.mutacion --feature F-056 --base b88b5ef --timeout 1800 --salida progress/mutacion_F-056_bloque2.md
```

(con `services/postventa-api/.venv/Scripts/python.exe`; 8 workers, los de `harness/rigor.json`). Salida final:

```
17 mutantes evaluados, 17 muertos, 0 supervivientes, 0 timeouts en 1718.0 s
Informe: progress/mutacion_F-056_bloque2.md
```

- **Alcance** (base `b88b5ef`): 5 ficheros, 677 líneas de producción. `revision.py` 5 mutantes (O-1),
  `repositorio_revision_pg.py` 5, `sentencias_revision.py` 7; `ports/revision.py` y `fabrica.py`, 0 (un
  `Protocol` y una llamada, sin operadores mutables).
- **Supervivientes: 0. Timeouts: 0.** No hay familias que analizar ni equivalentes que justificar. El equivalente
  que se veía venir (`ultima[0] → ultima[1]`) se quitó **antes** de lanzar (decisión 11), y los dos
  `strict=True → False` se comprobaron a mano antes (los dos mueren con los tests de `e15fcac`).
- Operadores: comparación 3, lógico 2, `not` 2, entero 4, aritmético 4, booleano 2.

### Verificaciones MANUAL pendientes

**T8** (abajo). Ninguna otra en este bloque.

### Para el humano · T8

Con **Docker Desktop arrancado**, desde la raíz del repositorio (`C:\Users\pgris\PycharmProjects\postventa-incidencias`):

```
powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1
```

Qué hace: levanta una PostgreSQL desechable en `127.0.0.1:55432`, ejecuta `pytest tests_bbdd -q` con el `.venv` del
servicio y tira el contenedor. **No toca el servidor compartido** (el `conftest` aborta si el DSN no es local).

Qué debe verse: **53 tests, todos `passed` y ninguno `skipped`**:

| Fichero | Tests |
|---|---|
| `test_f005_bbdd_aislamiento.py` | 4 |
| `test_f005_bbdd_ddl_idempotente.py` | 4 |
| `test_f005_bbdd_reproceso.py` | 2 |
| `test_f036_bbdd_bandeja.py` (los de F-036, que **también** tienen que pasar: su limpieza vacía la bandeja, y con la tabla nueva colgando de ella es lo primero que se rompería) | 15 |
| `test_f056_bbdd_revision.py` | 28 |

Entre los de F-056, el de **dos conexiones** espera 1 s a propósito (B esperando al `FOR UPDATE` de A) y el de
**10.001 filas** crea la obra `9902` con `generate_series`: los dos tardan algo más que el resto.

Qué copiar aquí, debajo: **la línea final de `pytest`** (`53 passed in N s`) y **el tiempo total** que tarde el
script. Si algo falla: el bloque `FAILED …` y su traza, **sin** el DSN ni la contraseña (el script la genera al
vuelo y no la escribe, pero si apareciera en una traza, tápala). Si sale algún `skipped`, la suite no ha visto
`POSTVENTA_PG_TEST_DSN`: no vale como T8.

#### T8, primera ejecución (humano, 2026-10-08): `1 failed, 52 passed in 23.61s` — hay que repetirla

Salida que pegó el humano:

```
FAILED tests_bbdd/tests/test_f056_bbdd_revision.py::test_f056_r36_la_clave_ajena_exige_una_incidencia_de_la_bandeja
>           _insertar_crudo(preparada, inc, incidencia_id=uuid.uuid4())
E           TypeError: _insertar_crudo() got multiple values for argument 'incidencia_id'
```

**El fallo es del test, no del producto**: `_insertar_crudo(conexion, incidencia_id, **cambios)` chocaba cuando
la columna que se falsea es justo `incidencia_id`. **Arreglo** (`4bf2791`, commit propio): los dos primeros
parámetros pasan a **solo posicionales** (`/`), así que la fila se construye con la incidencia **buena** y luego
se sustituye su `incidencia_id` por una que no está en la bandeja, que es lo que prueba la clave ajena. Además: una
columna de `cambios` que no sea del `INSERT` hace fallar el propio test (antes habría dado un error de parámetros
de psycopg que podía pasar por el rechazo esperado), y tras el `ForeignKeyViolation` se comprueba que no queda
ninguna fila. Los otros tres usos (`inc` solo; `**cambios` de los dieciséis `CHECK`; `accion=`/`motivo=`) no
tenían el problema: ninguno pasa `incidencia_id`. Comprobado sin base: `--collect-only` → **28 recogidos**; sin
DSN, 28 skipped. En el mismo bloque, la O-1 de la review del Bloque 2 (`aa077d1`) amplía el test append-only.

**Hay que repetir T8** con el mismo comando. Lo esperado sigue siendo **53 passed, 0 skipped, 0 failed**.

#### T8, repetida (humano, 2026-10-08, tras `4bf2791` y `aa077d1`): **EN VERDE**

Salida que pegó el humano (sin nada que tapar):

```
==> Ejecutando la suite de base de datos (tests_bbdd)
.....................................................                    [100%]
53 passed in 31.76s
==> Destruyendo el contenedor
SUITE DE BASE DE DATOS EN VERDE.
```

**53 passed, 0 failed, 0 skipped**: se cumple la condición del veredicto de la review del Bloque 2. T8 marcada en
`tasks.md`.

### Fuera del alcance de este bloque

La aplicación (`application/pipelines/revision.py`), el borde HTTP y el base64url del cursor (Bloque 3), la lectura
de ubicaciones de Sigrid (Bloque 3 bis), la documentación y `azure-apps` (Bloque 4), el front (F-038). T8 es del
humano. La guardia de alcance con `git` (R37, R39, R45) es T13.

### Observaciones para el líder

- **N-1 (decisión 1)**: confirmar que la redacción escrita es la que se quería.
- **R45 (decisión 5)**: además de los dos tests que cita T4, se ampliaron seis de F-028 y F-030…F-034.
- **T13 (decisión 13)**: el alcance de R37 no debe barrer `tests_bbdd/` (la limpieza de la base efímera).
- `harness/init.sh` cuenta como «deuda previa» los I001 de varios tests de F-005/F-028/F-036; no son de F-056.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de F-056 (`test_f056_*.py`) | **509 passed (2,7 s): `test_f056_ddl.py` 40, `test_f056_repositorio_revision.py` 95, `test_f056_revision_dominio.py` y `test_f056_paginacion.py` 374** |
| Suite completa del servicio | **7219 passed, 0 failed, 56 skipped**, 510,7 s |
| Cobertura de los módulos nuevos (sus tests, `coverage run --include`) | **100 %** (157/157 sentencias de puerto, sentencias y repositorio) |
| Cobertura de las líneas cambiadas (`PUERTA COBERTURA` de `init.sh`) | **100,0 % (648/648 líneas cambiadas desde la base, umbral 80 %, nivel `critico`)** |
| Mutantes (T9, base `b88b5ef`) | **17 generados, 17 muertos, 0 supervivientes, 0 timeouts**; 1718 s, 8 workers |
| `tests_bbdd` de F-056 | 28 recogidos (T7); su ejecución es **T8, pendiente del humano** |
| `bash harness/init.sh` | **ENTORNO LISTO (2026-10-08, tras la mutación): servicio api 7219 passed, 109 skipped en 1244,9 s (con medición de cobertura); front en verde por caché; arnés 115 passed; ruff 73 avisos de deuda previa (eran 74: N-2 quitó uno)** |

## Bloque 3 · La aplicación y los tres endpoints (T10–T14) · 2026-10-08

**Estado: HECHO, pendiente de review.** Encargo del líder del 2026-10-08: T10 (RED), T11, T12, T13 y T14, más N-1 de
la review del Bloque 2 (opción (b)), O-3 y O-5 de la del Bloque 1, O-1 y O-5 de la del Bloque 2, y el base64url del
cursor en el borde (opción (a) del humano). En mitad del bloque, el arreglo del test de `tests_bbdd` que hizo fallar
la primera T8 (ver «Para el humano · T8», en el Bloque 2). Nada del Bloque 3 bis: las ubicaciones válidas llegan a la
aplicación como **parámetro** (`FuenteDeUbicaciones`) y los tests usan dobles. Base de la mutación: `e9e815f`.

### Commits

| Commit | Qué |
|---|---|
| `5a23429` | **N-1** (review del Bloque 2, opción (b)): `decidir`, al aprobar, aplica la puerta de `CandidataAlVolcado` (`_exigir_volcable`, compartida) y da 409 `ubicacion_fuera_de_lista`; test primero; nota en `design.md` §3.5 «Decisión del líder 2026-10-08» |
| `97df089` | **O-3** (review del Bloque 1): `paginar` rechaza un `tamano` booleano; test primero (el del borde va en T10) |
| `961d0ab` | **T10 · RED**: `test_f056_pipeline_revision.py`, `test_f056_revision_http.py`, `tests/utiles_revision.py`, esqueletos neutros de la aplicación y del borde; `test_f010_endpoints_protegidos.py` a veinte rutas |
| `e5fc0fa` | **T11**: `application/pipelines/revision.py`; en el dominio, `comprobar_sin_sigrid` (extraída de `decidir`) y `motivo_de_descarte` pública |
| `f9e7a37` | **T12**: `interface_adapters/api/revision.py` y las tres rutas, los ocho errores y la cabecera de `function_app.py` |
| `4bf2791` | Arreglo del test de la clave ajena de `tests_bbdd` (fallo de la primera T8) |
| `aa077d1` | **O-1** (review del Bloque 2): el append-only de `tests_bbdd` compara también la foto tras la segunda revisión |
| `a2817af` | T8 repetida por el humano en verde (53 passed) y marcada |
| `a853ba0` | **T13**: `tests/test_f056_alcance_cerrado.py` (con la **O-5** del Bloque 2 escrita) |
| `1c5da05` | **T14, antes de la mutación**: dos mutantes equivalentes quitados del código y cinco tests que cubren huecos |
| `738f583` | **T14**: tres tests de caminos de error que la primera `PUERTA COBERTURA` dio sin cubrir (solo tests) |
| (este commit) | **T14**: `progress/mutacion_F-056_bloque3.md`, T14 marcada y este informe |

### Qué cambió

| Fichero | Cambio |
|---|---|
| `services/postventa-api/application/pipelines/revision.py` | **Nuevo.** `listar_para_revisar`, `aplicar_accion`, `historial`, `candidatas_al_volcado` (§7), `PeticionDeListado`, `PaginaDeRevision`, `IncidenciaRevisada`, `HistorialDeRevision` y el tipo `FuenteDeUbicaciones` |
| `services/postventa-api/interface_adapters/api/revision.py` | **Nuevo.** `listar_revision`, `historial_revision`, `accion_de_revision`, `cursor_de`/`clave_de_cursor` (base64url), `MAX_CURSOR = 512`, `construir_fuente_de_ubicaciones` (sin componer hasta el 3 bis) |
| `services/postventa-api/function_app.py` | **Solo añadido**: tres entradas en la lista de la cabecera, el párrafo del tercer endpoint de dato de fuera acumulado («veinte»), los imports, `CODIGOS_DE_REVISION`, `_error_de_revision` y las rutas `revision`, `revision_historial` y `revision_acciones` |
| `services/postventa-api/domain/models/revision.py` | N-1 (`_exigir_volcable` y su uso en `decidir`), O-3 (`paginar`), `comprobar_sin_sigrid` (sin cambio de comportamiento: `decidir` la llama) y `motivo_de_descarte` pública |
| `services/postventa-api/tests/test_f056_pipeline_revision.py`, `test_f056_revision_http.py`, `utiles_revision.py`, `test_f056_alcance_cerrado.py` | **Nuevos** (80 + 176 tests, los dobles y 22 tests) |
| `services/postventa-api/tests/test_f056_revision_dominio.py`, `test_f056_paginacion.py` | N-1 (5 casos) y O-3 (2 casos) |
| `services/postventa-api/tests/test_f010_endpoints_protegidos.py` | **Ampliado sin quitar nada**: `ENDPOINTS` + `revision`, `revision/historial`, `revision/acciones`, la cuenta 17 → 20 y el comentario. Es el único test que cuenta rutas de `function_app.py`; los que cuentan los anónimos de `docs/INTEGRACION.md` (F-012, F-019, F-053) son del Bloque 4 |
| `services/postventa-api/tests_bbdd/tests/test_f056_bbdd_revision.py` | `_insertar_crudo` con parámetros solo posicionales (T8) y la O-1 |
| `specs/F-056-revision-bandeja-backend/design.md`, `tasks.md` | Nota de la N-1 en §3.5; T10–T14 marcadas |

Nada del front, de `infra/`, de `infrastructure/sigrid/` ni de ningún fichero de «No se toca» (§12): lo fija T13.

### Decisiones de diseño (dentro de la spec, salvo donde se dice)

1. **El correo en la respuesta de una acción (R8 frente a R11): a confirmar por el líder.** R8 dice que
   `POST /api/revision/acciones` devuelve «la incidencia en la forma de una fila de `GET /api/revision` (R29)», y en
   esa fila `revisado_por` es el correo de la última revisión; R11 dice que el correo no sale «en ninguna otra
   respuesta que las dos de R10». Se ha seguido **R8**: la respuesta de la acción **es** una fila del listado (la que
   el front sustituye en su tabla), con el correo de quien acaba de actuar —el mismo que mandó en el cuerpo—. El
   `oid` no sale nunca. Ningún **error** lleva el correo (`test_f056_r11_el_correo_no_sale_en_ningun_error`). Si se
   prefiere la lectura literal de R11, el cambio es una línea en `_fila_revisada` (`revisado_por` a `null` en la
   respuesta de la acción) y su test.
2. **Las ubicaciones válidas, como parámetro.** La aplicación recibe `ubicaciones: FuenteDeUbicaciones`, una función
   `CatalogoObra → {unidad_codigo: ubicaciones}` que llama **una vez**, justo después de `leer_catalogo`, en listar,
   editar y aprobar, y nunca en descartar, recuperar ni el historial. El puerto `UbicacionesValidasPort` de §16.3 es
   de T14b: el Bloque 3 bis compondrá la función con él. **En producción, hasta el 3 bis**,
   `construir_fuente_de_ubicaciones` no inventa una lista: la fuente responde `CatalogoNoDisponible` (→ 503) en
   cuanto se le pide, sin escribir nada. Descartar y recuperar funcionan. Lo fija
   `test_f056_t12_sin_la_lectura_de_ubicaciones_compuesta_es_503`, que el 3 bis tendrá que sustituir.
3. **El orden de `aplicar_accion` (O-5 del Bloque 1)**: `situacion` → `comprobar_sin_sigrid` (transición y frescura,
   la función del dominio que `decidir` también usa: una sola regla) → solo en editar y aprobar, `leer_catalogo` de la
   obra **de la incidencia** y las ubicaciones → `decidir` → `registrar`. Los tests de T10 anotan cada llamada en una
   lista común y fijan la secuencia exacta: subir Sigrid por encima de la transición o la frescura, o `registrar` por
   encima de `decidir`, los pone en rojo (`test_f056_r2_la_transicion_va_antes_que_sigrid_y_no_escribe`,
   `…_r7_la_frescura_va_antes_que_sigrid_y_no_escribe`, `…_r13_valores_no_validos_leen_sigrid_y_no_escriben`,
   `…_r16_sin_cambios_no_escribe`, `…_r20_no_aprobable_lee_sigrid_y_no_escribe`).
4. **Las `esperadas` de `registrar`**: siempre la propia; la original **solo al aprobar** una incidencia con
   `duplicada_de` y la original cargada (R22). Editar o descartar una duplicada no la espera.
5. **N-1, el motivo del 409.** La puerta de la candidata, sin motivos de R21, solo puede rechazar ya la forma de la
   ubicación guardada; el 409 lleva `motivos: ["ubicacion_fuera_de_lista"]` (el que se arregla editando, que guarda
   recortado), con un mensaje que no repite la ubicación. R47 no cambia: el listado sigue sin marcarla.
6. **`catalogo.oficios[].grupo`** es la **opción de la plantilla** que contiene el código (`opciones_de_la_obra`, la
   misma función que la plantilla y la importación): su etiqueta —con los códigos entre paréntesis si dos grupos solo
   difieren en una tilde, como hace F-036— es la que guardó la bandeja en `oficio_nombre` de un oficio ambiguo, y sus
   `codigos` son los del grupo **que están en la obra**, entre los que se elige.
7. **`catalogo.pares`**: un par oficio–proveedor una vez, con el nombre de su **primera** fila de `obrofc`, en el
   orden del catálogo: lo que se ofrece es lo que guarda una edición (R14).
8. **`catalogo.ubicaciones`**: una entrada por **cada unidad del catálogo** (las que no trae el mapa, `[]`; las del
   mapa que no son del catálogo, fuera): es el mismo mapa que validan los motivos y la edición.
9. **La forma del cuerpo de una acción (R5)**: `revision_previa` es **obligatoria como clave** (`null` vale; R5 la
   enumera entre las que «debe recibir»); `incidencia_id` es el texto con guiones de un UUID, en mayúsculas o
   minúsculas (sin llaves ni `urn:`); `valores` con exactamente sus ocho claves (la forma es 400
   `peticion_invalida`; los tipos y valores de dentro, 400 `valores_no_validos` del dominio); el motivo se comprueba
   ya en el borde con `motivo_de_descarte` («el cuerpo entero antes de construir nada», §8). Los mensajes nombran
   las claves **del contrato**, nunca las recibidas.
10. **Parámetros del listado**: `tamano` es `[1-9][0-9]*` hasta 200 (sin signo, blancos ni ceros delante; `True`
    llamando al handler, 400: O-3); `con_motivos`, `true` o `false` exactos; `estado`, uno de los seis en minúsculas.
    La obra mal es 400 con `codigo: "peticion_invalida"`, como el resto de los 400 de estas rutas.
11. **El cursor** (opción (a)): `cursor_de` = base64url sin relleno del texto canónico; `clave_de_cursor` rechaza,
    **sin decodificar**, lo que pasa de `MAX_CURSOR = 512` (los 4/3 de `MAX_TEXTO_CLAVE`) o lleva algo fuera del
    alfabeto base64url (relleno incluido); luego UTF-8 estricto, `clave_de_texto` y que el cursor sea **el que
    emitiría el sistema** (unos bits de cola distintos decodifican igual y no lo son). Dos tests con un espía de
    `base64.urlsafe_b64decode` fijan que lo largo y lo de otro alfabeto no se llegan a decodificar.
12. **Qué se construye**: el catálogo y la fuente de ubicaciones solo en listar, editar y aprobar (descartar y
    recuperar no pasan por la puerta de entorno de Sigrid: funcionan aunque falte su configuración); las
    equivalencias solo en listar; la revisión siempre. Sigrid primero, como `plantilla.py`.
13. **Logs**: el éxito lo registra el handler del borde —«`F-056 revision listada: obra= tamano= total_filtrado=
    devueltas=`» (R31), «`F-056 revision accion: incidencia= accion= resultado= revision=`» y
    «`F-056 revision historial: incidencia= revisiones=`»—; los rechazos, `function_app.py`, solo con su **código**
    (`peticion_invalida`, `revision_desactualizada`…), nunca el motivo. El test de R41 recorre editar, aprobar,
    descartar con motivo, recuperar con otra persona, un 409, dos 400, el listado y el historial con `caplog` a
    `DEBUG`, y busca el `oid`, el correo (de las dos personas), la descripción, el detalle, el motivo y los nombres de
    unidad y proveedor en cada registro.
14. **Instantes** en UTC con microsegundos y `+00:00` (la forma de `importado_at_utc` de F-053); uno en otra zona se
    convierte (test con `+02:00`).
15. **`candidatas_al_volcado`** normaliza la obra (`normalizar_codigo_obra`) antes de pedir `aprobadas`.
16. **T14, antes de la mutación** (`1c5da05`), del recálculo de los mutantes del alcance: dos eran **equivalentes por
    construcción** y se quitaron del código, no de los tests —`catalogo is not None and validas is not None` (los dos
    o ninguno: se guardan en una sola variable `leido`) y el `zip(..., strict=True)` del historial (la aplicación da
    un cambio por revisión: se empareja por índice)—; y se añadieron tests para lo que ningún test fijaba:
    inmutabilidad de los cuatro tipos de la aplicación, editar o aprobar sin sus lecturas (`ValueError`), una acción
    con la obra ambigua o al techo (409), un cursor fuera del alfabeto que no se decodifica, e ida y vuelta del
    cursor con las tres longitudes de cola (y un control de que las cubren).

### Fase RED

**N-1** (antes del código de `5a23429`), desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f056_revision_dominio.py -q -p no:cacheprovider -k "aprobar_una_ubicacion_sin_recortar or aprobar_la_misma_ubicacion" --tb=line
```

```
FFFF.                                                                    [100%]
================================== FAILURES ===================================
E   Failed: DID NOT RAISE IncidenciaNoAprobable
tests\test_f056_revision_dominio.py:1477: Failed: DID NOT RAISE IncidenciaNoAprobable
E   Failed: DID NOT RAISE IncidenciaNoAprobable
tests\test_f056_revision_dominio.py:1477: Failed: DID NOT RAISE IncidenciaNoAprobable
E   Failed: DID NOT RAISE IncidenciaNoAprobable
tests\test_f056_revision_dominio.py:1477: Failed: DID NOT RAISE IncidenciaNoAprobable
E   Failed: DID NOT RAISE IncidenciaNoAprobable
tests\test_f056_revision_dominio.py:1477: Failed: DID NOT RAISE IncidenciaNoAprobable
=========================== short test summary info ===========================
FAILED tests/test_f056_revision_dominio.py::test_f056_r35_aprobar_una_ubicacion_sin_recortar_no_es_aprobable[ Cocina]
FAILED tests/test_f056_revision_dominio.py::test_f056_r35_aprobar_una_ubicacion_sin_recortar_no_es_aprobable[Cocina ]
FAILED tests/test_f056_revision_dominio.py::test_f056_r35_aprobar_una_ubicacion_sin_recortar_no_es_aprobable[\tCocina]
FAILED tests/test_f056_revision_dominio.py::test_f056_r35_aprobar_una_ubicacion_sin_recortar_no_es_aprobable[Cocina\n]
4 failed, 1 passed, 301 deselected in 0.37s
```

Los cuatro de «sin recortar» fallan por `DID NOT RAISE`; el control positivo («Cocina» exacta) pasa.

**O-3** (antes del código de `97df089`):

```
.venv/Scripts/python.exe -m pytest tests/test_f056_paginacion.py -q -p no:cacheprovider -k "booleano" --tb=line
```

```
F.                                                                       [100%]
================================== FAILURES ===================================
E   Failed: DID NOT RAISE PeticionDeRevisionInvalida
tests\test_f056_paginacion.py:416: Failed: DID NOT RAISE PeticionDeRevisionInvalida
=========================== short test summary info ===========================
FAILED tests/test_f056_paginacion.py::test_f056_r23_tamano_booleano_no_es_un_entero[True]
1 failed, 1 passed, 73 deselected in 0.41s
```

(`False` ya era 400 por el rango; `True` pasaba por un 1.)

**T10** (`961d0ab`, con los esqueletos neutros de la aplicación y del borde y sin las rutas en `function_app.py`):

```
.venv/Scripts/python.exe -m pytest tests/test_f056_pipeline_revision.py tests/test_f056_revision_http.py -q -p no:cacheprovider --tb=line
```

Cola real de la salida y los motivos de los 227 fallos, agrupados (rutas absolutas del puesto quitadas, los UUID de
prueba tapados):

```
227 failed, 1 passed in 2.83s
```

```
1 tests\test_f056_pipeline_revision.py:220: AssertionError: assert [] == ['revision.si...on.registrar']
   1 tests\test_f056_pipeline_revision.py:236: AssertionError: assert [] == ['revision.si...on.registrar']
   2 tests\test_f056_pipeline_revision.py:256: AssertionError: assert [] == ['revision.si...on.registrar']
   2 tests\test_f056_pipeline_revision.py:278: AssertionError: assert [] == ['revision.si...on.registrar']
   4 tests\test_f056_pipeline_revision.py:296: Failed: DID NOT RAISE IncidenciaNoEncontrada
   6 tests\test_f056_pipeline_revision.py:323: Failed: DID NOT RAISE AccionNoPermitida
   1 tests\test_f056_pipeline_revision.py:334: Failed: DID NOT RAISE AccionNoPermitida
  12 tests\test_f056_pipeline_revision.py:351: Failed: DID NOT RAISE RevisionDesactualizada
   1 tests\test_f056_pipeline_revision.py:366: Failed: DID NOT RAISE ValoresNoValidos
   1 tests\test_f056_pipeline_revision.py:377: Failed: DID NOT RAISE ValoresNoValidos
   1 tests\test_f056_pipeline_revision.py:391: Failed: DID NOT RAISE SinCambios
   1 tests\test_f056_pipeline_revision.py:401: Failed: DID NOT RAISE IncidenciaNoAprobable
   1 tests\test_f056_pipeline_revision.py:412: Failed: DID NOT RAISE Exception
   1 tests\test_f056_pipeline_revision.py:428: assert [] == [()]
   3 tests\test_f056_pipeline_revision.py:452: Failed: DID NOT RAISE RevisionDesactualizada
   1 tests\test_f056_pipeline_revision.py:465: AssertionError: assert None == {UUID(<uuid de prueba>): 1}
   1 tests\test_f056_pipeline_revision.py:473: AssertionError: assert None == {UUID(<uuid de prueba>): None}
   1 tests\test_f056_pipeline_revision.py:488: AssertionError: assert <EstadoRevision.NUEVA: 'nueva'> is <EstadoRevision.APROBADA: 'apr
   1 tests\test_f056_pipeline_revision.py:496: Failed: DID NOT RAISE RevisionDesactualizada
   2 tests\test_f056_pipeline_revision.py:509: AssertionError: assert None == {UUID(<uuid de prueba>): None}
   1 tests\test_f056_pipeline_revision.py:515: Failed: DID NOT RAISE IncidenciaNoAprobable
   1 tests\test_f056_pipeline_revision.py:532: assert 0 == 1
   1 tests\test_f056_pipeline_revision.py:547: assert False
   1 tests\test_f056_pipeline_revision.py:559: AssertionError: assert [] == ['9901']
   6 tests\test_f056_pipeline_revision.py:579: Failed: DID NOT RAISE any of (CatalogoNoDisponible, CatalogoSinVerificar)
   1 tests\test_f056_pipeline_revision.py:594: AssertionError: assert [] == [UUID(<uuid de prueba>)...00000000001')]
   1 tests\test_f056_pipeline_revision.py:615: AssertionError: assert [] == [(UUID(<uuid de prueba>)...0000001'), 1)]
   1 tests\test_f056_pipeline_revision.py:643: AssertionError: assert [] == ['revision.li...'ubicaciones']
   1 tests\test_f056_pipeline_revision.py:659: AssertionError: assert 0 == 5
   1 tests\test_f056_pipeline_revision.py:683: AssertionError: assert {} is {'9901.03VILLA 1.': ('Baño', 'Cocina', 'cocina'), '9901.03V
   1 tests\test_f056_pipeline_revision.py:704: assert [] == [1, 3, 4]
   1 tests\test_f056_pipeline_revision.py:704: assert [] == [2, 5]
   1 tests\test_f056_pipeline_revision.py:704: assert [] == [3]
   1 tests\test_f056_pipeline_revision.py:704: assert [] == [4]
   1 tests\test_f056_pipeline_revision.py:725: assert [] == [1, 2, 3, 4, 5]
   1 tests\test_f056_pipeline_revision.py:739: Failed: DID NOT RAISE BandejaDemasiadoGrande
   1 tests\test_f056_pipeline_revision.py:762: AssertionError: assert 0 == 10000
   2 tests\test_f056_pipeline_revision.py:779: Failed: DID NOT RAISE CatalogoNoDisponible
   1 tests\test_f056_pipeline_revision.py:779: Failed: DID NOT RAISE CatalogoSinVerificar
   1 tests\test_f056_pipeline_revision.py:779: Failed: DID NOT RAISE PersistenciaNoDisponible
   1 tests\test_f056_pipeline_revision.py:787: Failed: DID NOT RAISE ObraSinUnidades
   1 tests\test_f056_pipeline_revision.py:799: Failed: DID NOT RAISE IncidenciaNoEncontrada
   1 tests\test_f056_pipeline_revision.py:815: assert [] == [1, 2, 3, 4]
   1 tests\test_f056_pipeline_revision.py:828: assert None is not None
   1 tests\test_f056_pipeline_revision.py:840: AssertionError: assert [(1, <AccionR...R: 'editar'>)] == [(1, <AccionR...: 'aprobar'>)]
  76 tests\test_f056_revision_http.py:209: AssertionError: function_app no publica la ruta «revision_acciones»
   7 tests\test_f056_revision_http.py:209: AssertionError: function_app no publica la ruta «revision_historial»
  49 tests\test_f056_revision_http.py:209: AssertionError: function_app no publica la ruta «revision»
   2 tests\test_f056_revision_http.py:761: Failed: DID NOT RAISE PeticionDeRevisionInvalida
   1 tests\test_f056_revision_http.py:821: AssertionError: assert '' == 'eyJjIjoiMjAy...DAwMDAwMDkifQ'
   8 tests\test_f056_revision_http.py:847: AssertionError: cursor_de no da ningún cursor
   1 tests\test_f056_revision_http.py:864: AssertionError: ningún cursor con bits sobrantes
   1 tests\test_f056_revision_http.py:917: assert 0 == 512
   4 tests\test_f056_revision_http.py:935: Failed: DID NOT RAISE PeticionDeRevisionInvalida
   1 tests\utiles_rutas.py:43: AssertionError: el host no publica ninguna ruta «revision_acciones»
   1 tests\utiles_rutas.py:43: AssertionError: el host no publica ninguna ruta «revision_historial»
   1 tests\utiles_rutas.py:43: AssertionError: el host no publica ninguna ruta «revision»
```

**Los 227 son de aserción**: 164 `AssertionError`, 52 `Failed: DID NOT RAISE …` y 11 `assert …`; ningún
`ImportError`, `AttributeError`, `IndexError` ni `TypeError` (las rutas que aún no existían se comprueban con un
`assert hasattr(function_app, …)`, y cuatro tests se ajustaron para leer sin reventar lo que el esqueleto no
devuelve). El que pasa, `test_f056_s8_las_situaciones_no_llevan_el_oid`, mira el tipo `SituacionDeRevision` del
Bloque 1: es un control de R10, verde desde antes. `test_f010_endpoints_protegidos.py` daba además 2 fallos (la
cuenta de veinte), que T12 pone en verde.

### GREEN

T11: `.venv/Scripts/python.exe -m pytest tests/test_f056_pipeline_revision.py` → `75 passed`.

T12: `.venv/Scripts/python.exe -m pytest tests/test_f056_revision_http.py tests/test_f010_endpoints_protegidos.py` →
`153 + 8 passed` (con el test del grupo de oficios confirmado, añadido en T12: 154 + 8).

T13: `.venv/Scripts/python.exe -m pytest tests/test_f056_alcance_cerrado.py tests/test_f036_alcance_cerrado.py` →
`41 passed, 7 skipped` (los 7 saltados son los controles con `git` de F-036, que viven en su rama).

Tras `1c5da05`: los cuatro ficheros de F-056 del bloque, `252 passed` (aplicación 80, borde 172) + 22 de alcance.
Cobertura de los dos módulos nuevos con sus tests (`coverage run --include`): `application/pipelines/revision.py`
92/92, `interface_adapters/api/revision.py` 177/177: **100 %**.

Guardias y vecinos, sin caché (todas las `test_f0*_arquitectura`, `test_f010_endpoints_protegidos`, los `*_http` de
F-036, `test_f036_alcance_cerrado`, `test_f036_documentacion`, `test_f028_estado_http`,
`test_f019_logs_sin_datos_personales`, `test_f006_repo_sin_identificadores`, `test_f005_integracion_sin_secretos` y
todos los `test_f056_*`), tras T12: `1517 passed, 9 skipped`. `ruff check` de los ficheros nuevos o tocados: limpio.

### Suite completa

`.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider`, desde `services/postventa-api`, en `1c5da05`
(antes de la mutación):

```
7502 passed, 56 skipped in 835.63s (0:13:55)
```

### Mutación (T14)

Comando, desde la raíz, con el árbol limpio en `a2817af` (el código, el de `1c5da05`):

```
python -m harness.mutacion --feature F-056 --base e9e815f --timeout 1800 --salida progress/mutacion_F-056_bloque3.md
```

(con `services/postventa-api/.venv/Scripts/python.exe`; 8 workers, los de `harness/rigor.json`). Salida final:

```
F-056: 4 fichero(s), 1247 línea(s) de producción (origen rama, e9e815f..feature/F-056-revision-bandeja-backend)
Campaña paralela: hasta 8 workers, uno por worktree.
77 mutantes evaluados, 77 muertos, 0 supervivientes, 0 timeouts en 10501.5 s
Informe: progress/mutacion_F-056_bloque3.md
```

- **Alcance** (base `e9e815f`): 4 ficheros, 1247 líneas. `interface_adapters/api/revision.py` 40 mutantes,
  `function_app.py` 15 (los códigos HTTP de cada rama), `application/pipelines/revision.py` 11 y
  `domain/models/revision.py` 11 (N-1 y O-3). Por operador: entero 23, comparación 15, lógico 15, `not` 11,
  booleano 7, aritmético 6.
- **Supervivientes: 0. Timeouts: 0.** No hay familias que analizar ni equivalentes que justificar: los dos
  equivalentes que se veían venir en el recálculo previo se quitaron **del código** antes de lanzar (decisión 16,
  `1c5da05`), y los huecos que dejaba (inmutabilidad, `or` de la guarda de lecturas, el 409 de la obra en una
  acción, el alfabeto del cursor, la cola del relleno) se cubrieron con tests. El pre-chequeo local (cada mutante
  contra los tests de F-056 solos) ya dio 77/77 muertos.
- La herramienta no muta el **orden** de las llamadas ni los literales: el orden de `aplicar_accion` (O-5 del
  Bloque 1) lo fijan las listas de llamadas de los tests de T10 (decisión 3), para la bajada a mano del reviewer.
- Tiempo: 10501,5 s (2 h 55 min) con 8 workers; ≈ 1091 s por mutante, del orden de la suite.

### T13 · lo que fija el alcance

Con la **base fija `f86d639`** (no `merge-base`) y las tres guardas de F-030: R39 (ninguna línea añadida al código
nombra una escritura de la pasarela; ningún módulo de F-056 importa las escrituras del ERP; de `infrastructure/sigrid`
solo se usa `construir_catalogo_obra`), R40 (ni «habilitado» ni lectura del entorno en el código de F-056; la rama no
toca la configuración), R37 (ni `UPDATE` —salvo el `FOR UPDATE`—, ni `DELETE`, ni `TRUNCATE`; DDL solo en el `15_` y
cualificado en `postventa`), R45 y §12 (ningún fichero de «No se toca»; ningún test de F-036 salvo `test_f036_ddl.py`,
que T4 autoriza, ni de F-053; ni el front ni `infra/`; las funciones de la plantilla, la importación, la bandeja y los
catálogos en `function_app.py`, idénticas a la base; en `infrastructure/sigrid/fabrica.py` solo se puede **añadir**)
y R12 (solo el `15_` declara una columna de correo; el único `.sql` que toca la rama es el suyo). **O-5 del Bloque 2**:
la cabecera y `test_f056_r37_o5_la_guardia_no_barre_las_suites_y_por_que` dejan escrito que la guardia de R37 no
barre `tests_bbdd/` —su limpieza es el único `DELETE` de F-056 y va contra la base efímera—, como F-036.

### Verificaciones MANUAL pendientes

- Ninguna de este bloque. **T8 ya está en verde**: la primera salió `1 failed, 52 passed` por un fallo **del
  test**, arreglado en `4bf2791`; el humano la repitió el 2026-10-08 con **53 passed, 0 failed, 0 skipped**
  («Para el humano · T8», Bloque 2), y T8 está marcada (`a2817af`).
- T18 y T19 (Bloque 5).

### Fuera del alcance de este bloque

La lectura de las ubicaciones de Sigrid y su composición (Bloque 3 bis: hasta entonces editar, aprobar y listar dan
503 en un entorno real), la documentación y `azure-apps` (Bloque 4), el front (F-038).

### Observaciones para el líder

- **Decisión 1** (el correo en la respuesta de la acción): confirmar R8 o pedir la lectura literal de R11.
- **Decisión 2**: el 503 de la fuente sin componer es deliberado y vive solo hasta el 3 bis.
- `function_app.py` sigue sin decir «veinte» en los documentos: `docs/INTEGRACION.md` y sus tests de recuento
  (F-012, F-019, F-053) son del Bloque 4.

### Evidencias

| Evidencia | Valor |
|---|---|
| Tests de F-056 del bloque | **278**: `test_f056_pipeline_revision.py` 80, `test_f056_revision_http.py` 176, `test_f056_alcance_cerrado.py` 22 (y 7 nuevos en los del dominio) |
| Suite completa del servicio | **7502 passed, 0 failed, 56 skipped**, 835,6 s |
| Cobertura de los módulos nuevos (sus tests, `coverage run --include`) | **100 %** (aplicación 92/92, borde 177/177) |
| Cobertura de las líneas cambiadas (`PUERTA COBERTURA` de `init.sh`) | **100,0 % (1002/1002 líneas cambiadas desde la base, umbral 80 %, nivel `critico`)**; la primera ejecución tras la campaña dio 99,1 % (993/1002: el 500 del YAML roto en el listado y en una acción y el 503 del historial sin base, sin test), cubiertos en `738f583` |
| `bash harness/init.sh` | **ENTORNO LISTO** (2026-10-08, en `738f583`): servicio api 7506 passed, 109 skipped en 2067,2 s (con medición de cobertura); front en verde por caché; arnés 115 passed; ruff 73 avisos de deuda previa, no bloquea |
| Mutantes (T14, base `e9e815f`) | **77 generados, 77 muertos, 0 supervivientes, 0 timeouts**; 10501,5 s, 8 workers |
| `tests_bbdd` (T8, humano) | **53 passed, 0 failed, 0 skipped** en 31,76 s (repetida tras `4bf2791`) |
