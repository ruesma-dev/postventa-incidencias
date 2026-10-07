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

