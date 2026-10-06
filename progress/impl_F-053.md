<!-- progress/impl_F-053.md -->
# F-053 · Dos datos que pide el portal — Informe del implementer

Rama `feature/F-053-datos-para-el-portal`. Rigor **`critico`**.
Spec: `specs/F-053-datos-para-el-portal/` (aprobada el 2026-10-06).

## Bloque 1 · `importado_at_utc` (T1, T2 · R1–R7) · 2026-10-06

### Qué cambió

| Fichero | Cambio |
|---|---|
| `services/postventa-api/tests/test_f053_importado_at_utc.py` | **Nuevo.** 17 tests (R1–R7) por la ruta de verdad de `function_app` con los dobles de F-036, con un `ahora` distinto en cada subida, más uno directo sobre `serializar_importacion` |
| `services/postventa-api/tests/test_f036_importar_http.py` | **Una línea añadida** (D-3): `"importado_at_utc",` en `CLAVES`. Ninguna quitada ni cambiada |
| `services/postventa-api/interface_adapters/api/importar.py` | `_instante_utc(valor) -> str \| None` (privada); `serializar_importacion` añade `"importado_at_utc": _instante_utc(resultado.importacion.importado_at_utc)`; docstring del módulo («La respuesta (R43)») al día |
| `specs/F-053-datos-para-el-portal/tasks.md` | T1 y T2 marcadas |

Nada fuera de `services/postventa-api`; nada en `infrastructure/`, `function_app.py`, `domain/ports`,
el front ni `infra/` (ver «Alcance» abajo).

### Decisiones de diseño (dentro de la spec)

- El dato sale **siempre** de `contexto.resultado.importacion.importado_at_utc`, nunca de
  `contexto.ahora` (design §2): en `ya_importado` es la original.
- `_instante_utc` es exactamente la firma de design §4: `None` si `utcoffset() is None`; si no,
  `astimezone(UTC).isoformat(timespec="microseconds")` (D-1, D-2).
- La clave va dentro del `dict` literal del cuerpo, así sale en las tres 200 (completa, parcial,
  `ya_importado`). Las respuestas de error las construye `function_app` sin pasar por el
  serializador, así que no la llevan (R7) sin tocar nada más.

### Cómo se prueba cada requisito

| Requisito | Test(s) | Qué mata |
|---|---|---|
| R1 | `test_f053_r1_la_importacion_nueva_lleva_el_instante_guardado[completa\|parcial]` | igualdad literal y con el `RegistroImportacion` que guardó la bandeja |
| R2 | `test_f053_r2_ya_importado_devuelve_el_instante_de_la_original`, `test_f053_r2_el_serializador_lee_el_resultado_y_no_el_ahora_del_contexto` | serializar `contexto.ahora` (T1 en la primera subida, T2 en la segunda) |
| R3 | `test_f053_r3_con_microsegundo_cero_salen_igual_las_seis_cifras` (`AHORA` → `2026-09-30T08:15:00.000000+00:00`), `test_f053_r3_con_microsegundos_la_forma_es_la_misma` | quitar `timespec="microseconds"`; la regex de R3 |
| R4 | `test_f053_r4_una_importacion_con_otra_zona_sale_en_utc`, `test_f053_r4_la_original_leida_en_la_zona_de_la_sesion_sale_en_utc` | quitar `astimezone(UTC)`: `01:30+02:00` del 15/07 → `2026-07-14T23:30:00.000000+00:00`, con `timezone(timedelta(hours=2))` |
| R5 | `test_f053_r5_un_instante_sin_zona_sale_null_con_200` | quitar la rama sin zona (la original de la bandeja se cambia a *naive*; 200, `null`, mismo `importacion_id` y resumen) |
| R6 | `test_f053_r6_reprocesar_una_parcial_da_el_instante_de_la_nueva` | parcial con T1 y otra vez con T2 → T2 |
| R7 | `test_f053_r7_las_tres_respuestas_200_llevan_la_clave`; `test_f053_r7_ninguna_respuesta_de_error_lleva_la_clave[sin_oid\|grande\|no_es_xlsx\|obra_sin_unidades\|sin_sigrid\|sin_base]` (400, 413, 400, 409, 503, 503) | la clave en las tres 200 con la forma de R3; ausente en los cuerpos de error |

Nota sobre R7: los seis casos de error **pasan ya en RED** (afirman una ausencia, y el código de
antes no ponía la clave). Es lo esperado: protegen contra meterla en los cuerpos de error, no son
la prueba del requisito central.

### Fase RED (T1) · salida real

Comando, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests/test_f053_importado_at_utc.py tests/test_f036_importar_http.py -q --tb=line --show-capture=no
```

Salida (commit `7dcd3e5`, antes de tocar `importar.py`):

```
FFFFFFFFFFF......F.F.................................................... [ 96%]
...                                                                      [100%]
================================== FAILURES ===================================
E   KeyError: 'importado_at_utc'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_importado_at_utc.py:111: KeyError: 'importado_at_utc'
E   KeyError: 'importado_at_utc'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_importado_at_utc.py:111: KeyError: 'importado_at_utc'
E   KeyError: 'importado_at_utc'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_importado_at_utc.py:131: KeyError: 'importado_at_utc'
E   KeyError: 'importado_at_utc'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_importado_at_utc.py:146: KeyError: 'importado_at_utc'
E   KeyError: 'importado_at_utc'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_importado_at_utc.py:159: KeyError: 'importado_at_utc'
E   KeyError: 'importado_at_utc'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_importado_at_utc.py:166: KeyError: 'importado_at_utc'
E   KeyError: 'importado_at_utc'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_importado_at_utc.py:181: KeyError: 'importado_at_utc'
E   KeyError: 'importado_at_utc'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_importado_at_utc.py:198: KeyError: 'importado_at_utc'
E   AssertionError: assert 'importado_at_utc' in {'importacion_id': '<uuid de prueba>', 'obra': '0677', 'ya_importado': True, 'estado': 'completa', ...}
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_importado_at_utc.py:221: AssertionError: assert 'importado_at_utc' in {'importacion_id': '<uuid de prueba>', 'obra': '0677', 'ya_importado': True, 'estado': 'completa', ...}
E   KeyError: 'importado_at_utc'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_importado_at_utc.py:242: KeyError: 'importado_at_utc'
E   KeyError: 'importado_at_utc'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_importado_at_utc.py:267: KeyError: 'importado_at_utc'
E   AssertionError: assert {'errores', '...resumen', ...} == {'errores', '..., 'obra', ...}
      
      Extra items in the right set:
      'importado_at_utc'
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_importar_http.py:220: AssertionError: assert {'errores', '...resumen', ...} == {'errores', '..., 'obra', ...}
E   AssertionError: assert {'errores', '..., 'obra', ...} == {'errores', '..._at_utc', ...}
      
      Extra items in the right set:
      'importado_at_utc'
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_importar_http.py:259: AssertionError: assert {'errores', '..., 'obra', ...} == {'errores', '..._at_utc', ...}
=========================== short test summary info ===========================
FAILED tests/test_f053_importado_at_utc.py::test_f053_r1_la_importacion_nueva_lleva_el_instante_guardado[completa]
FAILED tests/test_f053_importado_at_utc.py::test_f053_r1_la_importacion_nueva_lleva_el_instante_guardado[parcial]
FAILED tests/test_f053_importado_at_utc.py::test_f053_r2_ya_importado_devuelve_el_instante_de_la_original
FAILED tests/test_f053_importado_at_utc.py::test_f053_r2_el_serializador_lee_el_resultado_y_no_el_ahora_del_contexto
FAILED tests/test_f053_importado_at_utc.py::test_f053_r3_con_microsegundo_cero_salen_igual_las_seis_cifras
FAILED tests/test_f053_importado_at_utc.py::test_f053_r3_con_microsegundos_la_forma_es_la_misma
FAILED tests/test_f053_importado_at_utc.py::test_f053_r4_una_importacion_con_otra_zona_sale_en_utc
FAILED tests/test_f053_importado_at_utc.py::test_f053_r4_la_original_leida_en_la_zona_de_la_sesion_sale_en_utc
FAILED tests/test_f053_importado_at_utc.py::test_f053_r5_un_instante_sin_zona_sale_null_con_200
FAILED tests/test_f053_importado_at_utc.py::test_f053_r6_reprocesar_una_parcial_da_el_instante_de_la_nueva
FAILED tests/test_f053_importado_at_utc.py::test_f053_r7_las_tres_respuestas_200_llevan_la_clave
FAILED tests/test_f036_importar_http.py::test_f036_r43_una_importacion_completa_responde_200_con_su_resumen
FAILED tests/test_f036_importar_http.py::test_f036_r33_la_importacion_parcial_es_200_con_errores_y_excel
13 failed, 62 passed in 39.00s
```

Las 13 fallan **solo por la clave que falta**: 10 `KeyError: 'importado_at_utc'`, una aserción
`'importado_at_utc' in …` (R5) y las dos igualdades de `CLAVES` de F-036 («Extra items in the
right set: 'importado_at_utc'»). Ningún fallo por otra causa. (Los GUID de la salida son los
`UUID(int=1)` sintéticos de los dobles.)

### Fase GREEN (T2) · salida real

```
.venv/Scripts/python.exe -m pytest tests/test_f053_importado_at_utc.py tests/test_f036_importar_http.py -q --tb=short --show-capture=no
...
75 passed in 32.95s
```

Suite completa, desde `services/postventa-api`:

```
.venv/Scripts/python.exe -m pytest tests -q --tb=short --show-capture=no
...
FAILED tests/test_f006_repo_sin_identificadores.py::test_f006_r26_ningun_fichero_del_repositorio_incrusta_un_identificador
1 failed, 6653 passed, 56 skipped in 371.74s (0:06:11)
```

### Pendiente para el líder: un fallo previo, ajeno a F-053

**La suite completa NO está en verde**, y no por F-053:
`test_f006_r26_ningun_fichero_del_repositorio_incrusta_un_identificador` encuentra **un**
identificador con forma de GUID en `progress/review8_F-035.md` (línea 93, dentro del comando de
ejemplo de `staticwebapp appsettings set … AZURE_CLIENT_ID=…`). El valor no se copia aquí.

Comprobado que es previo:

- `git diff --stat 349ba06 -- services/postventa-api/tests/test_f006_repo_sin_identificadores.py progress/review8_F-035.md`
  sale **vacío**: ni el test ni el fichero han cambiado desde la base de la rama (`dev`). El
  fichero entró en `fc06596` («F-035: review 8 APROBADA»).
- El barrido solo lee ficheros; F-053 no toca ninguno de los dos.

No lo he corregido: es un fichero de F-035, tocarlo está fuera del alcance del Bloque 1 (y de
R18/R19), y si ese GUID es un identificador real de una aplicación de Entra, la decisión
(redactarlo en una línea de `progress/`, o si además hay que tratar el historial) es del humano.
T2 queda marcada porque su propio criterio (el `pytest` de T1 en verde) se cumple y las 6653
restantes pasan; **T9 (`init.sh` en verde) no podrá cerrarse hasta que se resuelva**.

### Alcance (comprobado al cerrar el bloque)

```
git diff 349ba06 -- 'services/postventa-api/tests/test_f036_*.py'   (líneas +/- de contenido)
+    "importado_at_utc",
```

Una línea `+`, cero `-` (D-3, la parte del Bloque 1).

```
git diff --stat 349ba06 -- services/postventa-front infra services/postventa-api/infrastructure services/postventa-api/function_app.py services/postventa-api/domain/ports
```

Vacío.

Lint: `ruff check` limpio en los dos ficheros tocados por F-053 y `ruff format --check` limpio en
`importar.py` y en el test nuevo. (`test_f036_importar_http.py` ya tenía dos avisos de
`ruff format` en las líneas ~992 y ~1006, previos; no se reformatea para no tocar más líneas que
la de D-3.)

### Commits

| Commit | Mensaje |
|---|---|
| `7dcd3e5` | `F-053 T1: fase RED de importado_at_utc (R1-R7) y la clave en CLAVES de F-036 (D-3)` |
| `1d64c31` | `F-053 T2: importado_at_utc en la respuesta de POST /api/importaciones (_instante_utc, R1-R7)` |

Sin push. Nada escrito en Sigrid, SharePoint ni la base: todos los tests usan dobles en memoria.

### Fuera de este bloque

Bloque 2 (`oficio.distintos`, T3–T5), Bloque 3 (INTEGRACION, mutación, `init.sh`, T6, T8, T9) y
las tareas MANUAL. La cobertura de líneas cambiadas y la mutación se miden en T8/T9.

## Evidencias

Parciales (solo Bloque 1); la sección se completa en T8/T9.

| Evidencia | Valor |
|---|---|
| Tests ejecutados (suite completa) | 6653 pasan, 1 falla (previo, ajeno: ver arriba), 56 omitidos |
| Tests de F-053 | 17 nuevos, 17 en verde (75 con los de `test_f036_importar_http.py`) |
| Cobertura de líneas cambiadas | se mide en T9 (`PUERTA COBERTURA` de `init.sh`) |
| Mutantes | se mide en T8 (`python -m harness.mutacion --feature F-053 …`) |
| Tiempo de la suite | 371.74 s (6 min 11 s) |
