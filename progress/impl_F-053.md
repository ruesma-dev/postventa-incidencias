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

## Bloque 2 · `oficio.distintos` (T3, T4, T5 · R8–R17) · 2026-10-06

### Qué cambió

| Fichero | Cambio |
|---|---|
| `services/postventa-api/tests/test_f053_distintos_dominio.py` | **Nuevo.** 20 tests sobre `pares_distintos` (R9–R13) |
| `services/postventa-api/tests/test_f053_propuestas_distintos.py` | **Nuevo.** 13 tests por las rutas de verdad de `function_app` con los dobles de F-036 (R8, R10, R11, R12, R14, R15, R16, R17) y dos sobre `PropuestasDeOficios` (T5) |
| `services/postventa-api/tests/test_f036_catalogos_http.py` | **Dos líneas añadidas** (D-3): `"distintos": [],` en las igualdades de `test_f036_r87_las_propuestas_de_oficios_de_la_obra` y `test_f036_r12_una_obra_sin_oficios_no_propone_nada`. Ninguna quitada ni cambiada |
| `services/postventa-api/domain/models/equivalencias.py` | Función pura `pares_distintos(codigos, decisiones, catalogo)` sobre `_ultimas`; docstring del módulo (punto 4) |
| `services/postventa-api/application/pipelines/equivalencias.py` | `PropuestasDeOficios.distintos` (último campo, **sin defecto**); `propuestas_de_oficios` lo calcula con las `decisiones` que ya devuelve `_vigentes`; docstrings al día |
| `services/postventa-api/interface_adapters/api/equivalencias.py` | `leer_propuestas` añade `"distintos": [{"codigo_a", "codigo_b"}]` dentro de `oficio`, tras `propuestas`; docstring del módulo al día |
| `specs/F-053-datos-para-el-portal/tasks.md` | T3, T4 y T5 marcadas |

No se tocan `_grupos()`, `GruposVigentes`, el log de `propuestas_de_oficios`, `infrastructure/`,
`function_app.py`, `domain/ports` ni el front (ver «Alcance»).

### Decisiones (dentro de la spec)

- `pares_distintos` hace `frozenset(codigos)` una sola vez: la aplicación le pasa un generador
  (`(o.codigo for o in catalogo.oficios)`, design §4), que solo se puede recorrer una vez. Lo fija
  `test_f053_r9_los_codigos_pueden_llegar_en_un_generador`.
- El filtro de la obra exige **los dos** códigos (`par[0] in dados and par[1] in dados`), aunque el
  puerto ya filtre: la función no se fía de quien la llame (design §4).
- Lo que el doble de F-036 ya filtra (otro catálogo, un código de fuera de la obra) no se puede ver
  por HTTP; R9 (código fuera) y R13 se prueban en el dominio, como dice la cabecera del test HTTP.
- R10 por HTTP: `GET` → `POST` «distinto» con `T1` → `GET` → `POST` «mismo» con `T2` (`T2 > T1`)
  → `GET`, y al revés. El `POST` va por la ruta de verdad con un `ahora` propio por petición.

### Cómo se prueba cada requisito

| Requisito | Test(s) |
|---|---|
| R8 | `test_f053_r8_distintos_va_dentro_de_oficio_con_dos_claves_por_par` (claves de la raíz, de `oficio` y de cada par) |
| R9 | dominio: `…_r9_un_par_decidido_distinto_sale`, `…_r9_un_par_decidido_mismo_no_sale`, `…_r9_un_par_con_algun_codigo_fuera_de_la_obra_no_sale[b_fuera\|a_fuera\|los_dos_fuera]` (mata `and` → `or`), `…_r9_sin_codigos_de_la_obra…`, `…_r9_…generador` |
| R10 | dominio: «distinto, luego mismo» no; «mismo, luego distinto» sí; manda la fecha y no el orden de llegada; a igual fecha, la que llega después. HTTP: `test_f053_r10_distinto_y_despues_mismo_no_sale`, `test_f053_r10_mismo_y_despues_distinto_sale` |
| R11 | `test_f053_r11_el_par_de_la_0677_sale_como_textos_con_sus_ceros` (`0033` · `0133`, `isinstance(str)`, idénticos a `oficios[].codigo`); y en el dominio |
| R12 | dominio: cinco pares en orden inverso → ordenados; un par repetido sale una vez; `tuple` de `tuple`. HTTP: `test_f053_r12_ordenados_y_sin_repetidos_aunque_lleguen_al_reves` |
| R13 | dominio: un «distinto» de `proveedor` no cuenta; un «mismo» de `proveedor` posterior no deshace el «distinto» de `oficio`; el catálogo es el del argumento (no `oficio` fijo) |
| R14 | `test_f053_r14_…` (sin decisiones, solo «mismo», obra sin oficios) y las dos igualdades de F-036 (D-3) |
| R15 | `test_f053_r15_el_par_sale_a_la_vez_en_distintos_y_en_el_aviso` (`avisos` y `grupos` como en R82 de F-036) |
| R16 | `test_f053_r16_las_mismas_lecturas_una_llamada_a_ultimas_decisiones` (lista exacta de llamadas, una sola petición de decisiones) |
| R17 | `test_f053_r17_la_respuesta_de_decidir_no_lleva_distintos`, más la igualdad completa (sin tocar) de `test_f036_r88_la_respuesta_lleva_los_pares_y_los_grupos_resultantes` |
| T5 | `test_f053_t5_propuestas_de_oficios_devuelve_los_distintos`, `test_f053_t5_distintos_es_el_ultimo_campo_y_no_tiene_defecto` |

Nota: `test_f053_r17_…` **pasa ya en RED** (afirma una ausencia en la respuesta de `POST`, que no
cambia). Es lo esperado: protege contra meter `distintos` en `_grupos()`, no prueba el requisito
central.

### Fase RED (T3) · salida real

Comando, desde `services/postventa-api` (con `--continue-on-collection-errors` para que el
`ImportError` del test de dominio no tape el resto):

```
.venv/Scripts/python.exe -m pytest tests/test_f053_distintos_dominio.py tests/test_f053_propuestas_distintos.py tests/test_f036_catalogos_http.py -q --tb=line --show-capture=no -p no:cacheprovider --continue-on-collection-errors
```

Salida (commit `5f7b3a3`, antes de tocar el código):

```
FFFFFFFFFFFF.F.......F.................................................. [ 54%]
............................................................             [100%]
=================================== ERRORS ====================================
____________ ERROR collecting tests/test_f053_distintos_dominio.py ____________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_distintos_dominio.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f053_distintos_dominio.py:26: in <module>
    from domain.models.equivalencias import (
E   ImportError: cannot import name 'pares_distintos' from 'domain.models.equivalencias' (C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\domain\models\equivalencias.py)
================================== FAILURES ===================================
E   AssertionError: assert {'avisos', 'g... 'propuestas'} == {'avisos', 'd... 'propuestas'}
      
      Extra items in the right set:
      'distintos'
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_propuestas_distintos.py:123: AssertionError: assert {'avisos', 'g... 'propuestas'} == {'avisos', 'd... 'propuestas'}
E   KeyError: 'distintos'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_propuestas_distintos.py:142: KeyError: 'distintos'
E   KeyError: 'distintos'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_propuestas_distintos.py:157: KeyError: 'distintos'
E   KeyError: 'distintos'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_propuestas_distintos.py:178: KeyError: 'distintos'
E   KeyError: 'distintos'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_propuestas_distintos.py:206: KeyError: 'distintos'
E   KeyError: 'distintos'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_propuestas_distintos.py:219: KeyError: 'distintos'
E   KeyError: 'distintos'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_propuestas_distintos.py:225: KeyError: 'distintos'
E   KeyError: 'distintos'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_propuestas_distintos.py:235: KeyError: 'distintos'
E   KeyError: 'distintos'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_propuestas_distintos.py:253: KeyError: 'distintos'
E   KeyError: 'distintos'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_propuestas_distintos.py:269: KeyError: 'distintos'
E   AttributeError: 'PropuestasDeOficios' object has no attribute 'distintos'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_propuestas_distintos.py:290: AttributeError: 'PropuestasDeOficios' object has no attribute 'distintos'
E   AssertionError: assert 'propuestas' == 'distintos'
      
      - distintos
      + propuestas
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_propuestas_distintos.py:297: AssertionError: assert 'propuestas' == 'distintos'
E   AssertionError: assert {'obra': '067...': [...]}]}]}} == {'obra': '067...os': [], ...}}
      
      Omitting 1 identical items, use -vv to show
      Differing items:
      {'oficio': {'oficios': [{'codigo': '0046', 'nombre': 'Carpintería de madera', 'grupo': ['0046']}, {'codigo': '0085', '...], 'por_pares': False, 'motivos': ['plural'], 'pares': [{'codigo_a': '0085', 'codigo_b': '0166', 'motivos': [...]}]}]}} != {'oficio': {'oficios': [{'codigo': '0046', 'nombre': 'Carpintería de madera', 'grupo': ['0046']}, {'codigo': '0085', '...se, 'motivos': ['plural'], 'pares': [{'codigo_a': '0085', 'codigo_b': '0166', 'motivos': [...]}]}], 'avisos': [], ...}}
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_catalogos_http.py:232: AssertionError: assert {'obra': '067...': [...]}]}]}} == {'obra': '067...os': [], ...}}
E   AssertionError: assert {'oficios': [...opuestas': []} == {'oficios': [...sos': [], ...}
      
      Omitting 4 identical items, use -vv to show
      Right contains 1 more item:
      {'distintos': []}
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f036_catalogos_http.py:380: AssertionError: assert {'oficios': [...opuestas': []} == {'oficios': [...sos': [], ...}
=========================== short test summary info ===========================
FAILED tests/test_f053_propuestas_distintos.py::test_f053_r8_distintos_va_dentro_de_oficio_con_dos_claves_por_par
FAILED tests/test_f053_propuestas_distintos.py::test_f053_r10_distinto_y_despues_mismo_no_sale
FAILED tests/test_f053_propuestas_distintos.py::test_f053_r10_mismo_y_despues_distinto_sale
FAILED tests/test_f053_propuestas_distintos.py::test_f053_r11_el_par_de_la_0677_sale_como_textos_con_sus_ceros
FAILED tests/test_f053_propuestas_distintos.py::test_f053_r12_ordenados_y_sin_repetidos_aunque_lleguen_al_reves
FAILED tests/test_f053_propuestas_distintos.py::test_f053_r14_sin_decisiones_distintos_es_una_lista_vacia
FAILED tests/test_f053_propuestas_distintos.py::test_f053_r14_con_solo_decisiones_mismo_distintos_es_una_lista_vacia
FAILED tests/test_f053_propuestas_distintos.py::test_f053_r14_una_obra_sin_oficios_lleva_distintos_vacio
FAILED tests/test_f053_propuestas_distintos.py::test_f053_r15_el_par_sale_a_la_vez_en_distintos_y_en_el_aviso
FAILED tests/test_f053_propuestas_distintos.py::test_f053_r16_las_mismas_lecturas_una_llamada_a_ultimas_decisiones
FAILED tests/test_f053_propuestas_distintos.py::test_f053_t5_propuestas_de_oficios_devuelve_los_distintos
FAILED tests/test_f053_propuestas_distintos.py::test_f053_t5_distintos_es_el_ultimo_campo_y_no_tiene_defecto
FAILED tests/test_f036_catalogos_http.py::test_f036_r87_las_propuestas_de_oficios_de_la_obra
FAILED tests/test_f036_catalogos_http.py::test_f036_r12_una_obra_sin_oficios_no_propone_nada
ERROR tests/test_f053_distintos_dominio.py
14 failed, 118 passed, 1 error in 6.71s
```

Lectura: **1 error** de colección, el `ImportError` de `pares_distintos` (los 20 tests de dominio);
**14 fallos**, todos por `distintos` que falta: 10 `KeyError: 'distintos'`, la aserción de claves
de `oficio` de R8 («Extra items … 'distintos'»), el `AttributeError` de
`PropuestasDeOficios.distintos`, el último campo de `PropuestasDeOficios` (`'propuestas' ==
'distintos'`) y las dos igualdades de F-036 de D-3 (`{'distintos': []}` de más en lo esperado).
Ningún fallo por otra causa.

### Fase GREEN (T4, T5) · salida real

T4, desde `services/postventa-api` (commit `371d74c`):

```
.venv/Scripts/python.exe -m pytest tests/test_f053_distintos_dominio.py tests/test_f036_equivalencias_dominio.py -q --tb=short --show-capture=no -p no:cacheprovider
...
126 passed in 1.07s
```

T5, el `pytest` de T3 (commit `67b5541`):

```
.venv/Scripts/python.exe -m pytest tests/test_f053_distintos_dominio.py tests/test_f053_propuestas_distintos.py tests/test_f036_catalogos_http.py -q --tb=short --show-capture=no -p no:cacheprovider
...
152 passed in 6.69s
```

Suite completa (con el arreglo R26 del líder, `930b812`, ya dentro):

```
.venv/Scripts/python.exe -m pytest tests -q --tb=short --show-capture=no -p no:cacheprovider
...
6687 passed, 56 skipped in 897.52s (0:14:57)
```

En verde. 6687 = 6653 + 1 (el R26 que fallaba en el Bloque 1) + 33 nuevos de este bloque.

### Alcance (comprobado al cerrar el bloque)

```
git diff 349ba06 -- 'services/postventa-api/tests/test_f036_*.py'   (líneas +/- de contenido)
+            "distintos": [],
+        "distintos": [],
+    "importado_at_utc",
```

Tres líneas `+`, cero `-`: las tres de D-3 (dos de este bloque, una del Bloque 1).

```
git diff --stat 349ba06 -- services/postventa-front infra services/postventa-api/infrastructure services/postventa-api/function_app.py services/postventa-api/domain/ports
```

Vacío.

Lint: `ruff check` limpio en los cinco ficheros tocados; `ruff format --check` limpio en los tres de
código y en los dos tests nuevos (estos se formatearon con `ruff format` antes del commit de T3).
`test_f036_catalogos_http.py` no se reformatea (solo las dos líneas de D-3).

### `init.sh`

Al empezar el bloque se lanzó `bash harness/init.sh`: superó el límite de 10 minutos de la
herramienta y siguió en segundo plano; al cerrar el bloque iba por el 90 % de la suite, sin ningún
fallo hasta ahí. No se esperó a su final: la verificación de T5 es el `pytest tests -q` completo,
que sí terminó en verde (arriba). El `init.sh` en verde con la puerta de cobertura es T9 (Bloque 3).

### Commits

| Commit | Mensaje |
|---|---|
| `5f7b3a3` | `F-053 T3: fase RED de oficio.distintos (R8-R17) y "distintos": [] en las dos igualdades de F-036 (D-3)` |
| `371d74c` | `F-053 T4: pares_distintos en el dominio, sobre _ultimas (R9-R13)` |
| `67b5541` | `F-053 T5: oficio.distintos en GET /api/catalogos/propuestas (PropuestasDeOficios.distintos, R8-R17)` |

Sin push. Nada escrito en Sigrid, SharePoint ni la base: todos los tests usan dobles en memoria.

### Fuera de este bloque

Bloque 3 (T6 `docs/INTEGRACION.md`, T8 mutación y alcance, T9 `init.sh`), T7 (líder) y las
tareas MANUAL.

## Bloque 3 · documentación y evidencias (T6, T8, T9 · R18–R20) · 2026-10-06

T7 (`azure-apps`, R21) **no** es de este encargo: la hace el líder al desplegar (decisión del
humano del 2026-10-06). Queda sin marcar en `tasks.md`.

### Qué cambió

| Fichero | Cambio |
|---|---|
| `docs/INTEGRACION.md` | §8, «### Los endpoints, y qué hace cada uno»: **un párrafo sin encabezado** justo antes de «Los diecisiete quedan en nivel **anónimo**» (design §6). Dice: desde F-053, dos campos **aditivos**; `importado_at_utc` en `POST /api/importaciones` (UTC, `AAAA-MM-DDTHH:MM:SS.ffffff+00:00`, `null` sin zona, la **original** con `ya_importado: true`); `oficio.distintos` en `GET /api/catalogos/propuestas` (`{codigo_a, codigo_b}`, solo oficios de la obra, **última decisión** `distinto`, códigos como texto con sus ceros, `codigo_a < codigo_b`, ordenados); que `POST /api/catalogos/decisiones` no lo lleva (D-5); que un código con **guion** chocaría con el `a-b` del front y no se filtra (D-6); y el puntero a la spec |
| `services/postventa-api/tests/test_f053_documentacion.py` | **Nuevo.** 19 tests: los ocho textos de T6 en «## 8 · Qué exponemos nosotros» y, además, **todos en el mismo párrafo**; «F-053», «aditivos», las dos rutas y `null`; el párrafo va dentro del subapartado de endpoints, **antes** de «Los diecisiete», sin encabezado propio y sin ningún título con «F-053»; y el barrido de valores de `test_f005` (`hallazgos`) sobre el párrafo |
| `progress/mutacion_F-053.md` | **Nuevo.** Informe de la herramienta más el análisis del implementer (abajo) |
| `specs/F-053-datos-para-el-portal/tasks.md` | T6, T8 y T9 marcadas; T7 no |

Ningún fichero de código de producción tocado en este bloque. La cabecera de `docs/INTEGRACION.md`
(«Fecha: 2026-10-05», «Última feature que lo tocó: F-036») **no se ha tocado**: la fija
`test_f036_documentacion.py` (`FECHA` y el texto), y cambiarla añadiría líneas en tests de F-036 fuera
de las tres de D-3. Ver «Queda para cerrar».

### T6 · fase RED y GREEN (salida real)

Desde `services/postventa-api`, con el test escrito y el párrafo todavía sin escribir:

```
.venv/Scripts/python.exe -m pytest tests/test_f053_documentacion.py -q --tb=line --show-capture=no -p no:cacheprovider
...
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f053_documentacion.py:81: AssertionError: se esperaba un párrafo de F-053: 0
=========================== short test summary info ===========================
FAILED tests/test_f053_documentacion.py::test_f053_r20_la_seccion_ocho_dice_el_contrato_de_los_dos_campos[importado_at_utc]
FAILED tests/test_f053_documentacion.py::test_f053_r20_la_seccion_ocho_dice_el_contrato_de_los_dos_campos[+00:00]
FAILED tests/test_f053_documentacion.py::test_f053_r20_la_seccion_ocho_dice_el_contrato_de_los_dos_campos[ya_importado]
FAILED tests/test_f053_documentacion.py::test_f053_r20_la_seccion_ocho_dice_el_contrato_de_los_dos_campos[original]
FAILED tests/test_f053_documentacion.py::test_f053_r20_la_seccion_ocho_dice_el_contrato_de_los_dos_campos[oficio.distintos]
FAILED tests/test_f053_documentacion.py::test_f053_r20_la_seccion_ocho_dice_el_contrato_de_los_dos_campos[codigo_a]
FAILED tests/test_f053_documentacion.py::test_f053_r20_la_seccion_ocho_dice_el_contrato_de_los_dos_campos[\xfaltima decisi\xf3n]
FAILED tests/test_f053_documentacion.py::test_f053_r20_la_seccion_ocho_dice_el_contrato_de_los_dos_campos[guion]
FAILED tests/test_f053_documentacion.py::test_f053_r20_todo_va_en_el_mismo_parrafo[importado_at_utc]
FAILED tests/test_f053_documentacion.py::test_f053_r20_todo_va_en_el_mismo_parrafo[+00:00]
FAILED tests/test_f053_documentacion.py::test_f053_r20_todo_va_en_el_mismo_parrafo[ya_importado]
FAILED tests/test_f053_documentacion.py::test_f053_r20_todo_va_en_el_mismo_parrafo[original]
FAILED tests/test_f053_documentacion.py::test_f053_r20_todo_va_en_el_mismo_parrafo[oficio.distintos]
FAILED tests/test_f053_documentacion.py::test_f053_r20_todo_va_en_el_mismo_parrafo[codigo_a]
FAILED tests/test_f053_documentacion.py::test_f053_r20_todo_va_en_el_mismo_parrafo[\xfaltima decisi\xf3n]
FAILED tests/test_f053_documentacion.py::test_f053_r20_todo_va_en_el_mismo_parrafo[guion]
FAILED tests/test_f053_documentacion.py::test_f053_r20_el_parrafo_dice_que_los_dos_son_aditivos_y_desde_cuando
FAILED tests/test_f053_documentacion.py::test_f053_t6_el_parrafo_va_antes_de_los_diecisiete_y_sin_encabezado
FAILED tests/test_f053_documentacion.py::test_f053_t6_el_parrafo_no_lleva_valores
19 failed in 0.42s
```

Los 19 fallan por lo que falta: ninguno de los ocho textos estaba en §8 y el párrafo no existía. Con
el párrafo escrito, la verificación de T6:

```
.venv/Scripts/python.exe -m pytest tests/test_f053_documentacion.py tests/test_f036_documentacion.py tests/test_f019_documentacion.py -q --tb=short --show-capture=no -p no:cacheprovider
105 passed in 2.07s
```

Con los vecinos que leen §8 o barren valores (`test_f010_integracion_expuesto.py`,
`test_f012_documentacion.py` —cuenta las filas de la tabla—, `test_f005_integracion_sin_secretos.py`)
y los tres anteriores: `166 passed in 3.13s`. `ruff check` y `ruff format --check` limpios en el test
nuevo (formateado con `ruff format` antes del commit).

### T8 (a) · Mutación

Comando: `python -m harness.mutacion --feature F-053 --base 349ba06 --timeout 900` (4181,2 s; la
herramienta usó 5 workers). Informe literal y análisis completo: `progress/mutacion_F-053.md`.

Salida de la campaña (resumida: rutas sin `services/postventa-api/` y la línea mutada abreviada; la
literal está en el informe):

```
F-053: 4 fichero(s), 79 línea(s) de producción (origen rama, 349ba06..feature/F-053-datos-para-el-portal)
[1/5] muerto        domain/models/equivalencias.py:484 [entero]      par[1] -> par[2]
[2/5] timeout       domain/models/equivalencias.py:484 [comparacion] == DISTINTO -> != DISTINTO
[3/5] timeout       domain/models/equivalencias.py:484 [entero]      par[0] -> par[1]
[4/5] timeout       domain/models/equivalencias.py:484 [logico]      1.er and -> or
[5/5] timeout       domain/models/equivalencias.py:484 [logico]      2.º and -> or
Repaso en serie de 4 mutante(s) en timeout
repaso: 1.er and -> or  muerto; los otros tres, timeout otra vez
5 mutantes evaluados, 2 muertos, 0 supervivientes, 3 timeouts en 4181.2 s
```

**Cero supervivientes.** Los tres `timeout`, por familias completas:

- Por qué salen en `timeout`: cada evaluación lanza **la suite entera con `-x`**, y los tests que los
  cazan (`test_f053_*`) van al final por orden alfabético, tras ~6.600; durante la campaña la máquina
  corría a la vez otra campaña de mutación de otro repositorio (4 workers), la suite de otro proyecto y
  un `init.sh` de este repositorio ajeno al encargo. No es un cuelgue.
- Comprobación directa (worktree temporal en `a43623e`, ya retirado; los tests de F-053 y
  `test_f036_catalogos_http.py`, 152 tests; sin mutar, `152 passed in 40.98s`):
  - **Comparación** `==` → `!=`: **muerto**, `25 failed, 127 passed in 19.83s`.
  - **Índice** `par[0]` → `par[1]`: **muerto**, `1 failed, 151 passed in 21.38s`, por
    `test_f053_r9_un_par_con_algun_codigo_fuera_de_la_obra_no_sale[a_fuera]`, el caso que existe para
    eso. El otro de la familia (`par[1]` → `par[2]`) murió en la campaña.
  - **Lógico** 2.º `and` → `or`: **muerto**, `10 failed, 142 passed in 20.10s` (`b_fuera`, `a_fuera`,
    R10). El otro de la familia (1.er `and`) murió en el repaso.
- **13 mutantes a mano**, los «previsibles» de design §7 que la herramienta no genera (no muta `is
  None`, llamadas ni cadenas, así que en `importar.py` y en los bordes no hubo ninguno):
  `contexto.ahora` en vez del resultado, sin `timespec`, sin `astimezone(UTC)`, `is None` → `is not
  None`, sin la rama sin zona, sin la clave; sin `sorted`, `DISTINTO` → `MISMO`, `frozenset()` vacío;
  `codigo_a`/`codigo_b` cruzados, `distintos` siempre vacío; `Catalogo.PROVEEDOR` y sin decisiones en
  la aplicación. **Los 13, muertos** (tabla con la salida de cada uno en `progress/mutacion_F-053.md`).

Nada que justificar como equivalente y ningún test nuevo necesario. Si la review quiere el veredicto
`muerto` en la tabla de la propia herramienta, basta con relanzar la campaña con la máquina libre.

### T8 (b) · Alcance (R18, R19) · salida real

```
git diff --stat 349ba06 -- services/postventa-front infra services/postventa-api/infrastructure services/postventa-api/function_app.py services/postventa-api/domain/ports
```

Vacío (ni una línea de salida).

```
git diff 349ba06 -- 'services/postventa-api/tests/test_f036_*.py'
diff --git a/services/postventa-api/tests/test_f036_catalogos_http.py b/services/postventa-api/tests/test_f036_catalogos_http.py
index 652e51b..4df62c9 100644
--- a/services/postventa-api/tests/test_f036_catalogos_http.py
+++ b/services/postventa-api/tests/test_f036_catalogos_http.py
@@ -254,6 +254,7 @@ def test_f036_r87_las_propuestas_de_oficios_de_la_obra(monkeypatch):
                 }
             ],
             "avisos": [],
+            "distintos": [],
         },
     }
 
@@ -381,6 +382,7 @@ def test_f036_r12_una_obra_sin_oficios_no_propone_nada(monkeypatch):
         "grupos": [],
         "propuestas": [],
         "avisos": [],
+        "distintos": [],
     }
 
 
diff --git a/services/postventa-api/tests/test_f036_importar_http.py b/services/postventa-api/tests/test_f036_importar_http.py
index fa788ed..b3b5e3f 100644
--- a/services/postventa-api/tests/test_f036_importar_http.py
+++ b/services/postventa-api/tests/test_f036_importar_http.py
@@ -113,6 +113,7 @@ CLAVES = {
     "filas",
     "errores",
     "total_errores",
+    "importado_at_utc",
 }
 CLAVES_RESUMEN = {
     "leidas",
```

Líneas de contenido (sin las cabeceras `+++`/`---`): **3 `+`, 0 `-`**, las tres de D-3.

### T9 · `bash harness/init.sh` (salida real, sin las líneas de progreso de pytest)

Lanzado tal cual tras el commit de T8 (`99451f2`):

```
[OK] Arnés v1.5.2 (2026-08-18)
[OK] Python: Python 3.12.7
[OK] Existe CLAUDE.md
[OK] Existe CHECKPOINTS.md
[OK] Existe harness/features.json
[OK] Existe harness/rigor.json
[OK] Existe specs/SPECS.md
[OK] Existe progress/current.md
[OK] Existe progress/history.md
[OK] Existe docs/ARCHITECTURE.md
[OK] Existe docs/CONVENTIONS.md
    54 features, 29 abiertas, en curso: ['F-053'], bloqueadas: ninguna
[OK] features.json válido
[OK] BACKLOG.md al día
    niveles: critico, documental, estandar; por defecto critico; umbral de cobertura 80%
[OK] harness/rigor.json y niveles declarados: válidos
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 73 avisos (deuda previa, no bloquea). Detalle: python -m ruff check .
115 passed in 28.00s
[OK] pytest en verde (con medición de cobertura)
    2 servicio(s): api (python), front (python)
[OK] harness/servicios.json válido
6706 passed, 81 skipped in 3012.08s (0:50:12)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 100.0% de 8 líneas cambiadas cubiertas (8/8, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-053-datos-para-el-portal
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

**En verde.** 6706 = 6687 del Bloque 2 + 19 de `test_f053_documentacion.py`. Los omitidos pasan de
56 (pytest suelto, Bloque 2) a 81 (dentro de `init.sh`, con cobertura); ninguno es de F-053 y no se ha
investigado más. Los 50 minutos se deben a la carga de la máquina (ver T8).

### Commits

| Commit | Mensaje |
|---|---|
| `caf3b92` | `F-053 T6: importado_at_utc y oficio.distintos en docs/INTEGRACION.md §8 (R20) y test_f053_documentacion.py` |
| `99451f2` | `F-053 T8: campaña de mutación (5 generados, 0 supervivientes, 3 timeouts muertos por los tests de F-053) y 13 mutantes a mano del design §7` |
| siguiente | `F-053 T9: init.sh en verde; informe del Bloque 3 en progress/impl_F-053.md` |

Entre `caf3b92` y `99451f2` hay en la rama un commit **ajeno a este encargo**, `a43623e` («Backlog:
F-038 y F-040 pasan a prioridad 1 y 2…»: `BACKLOG.md`, `harness/features.json`,
`progress/current.md`), hecho durante la campaña. No toca código y no lo he modificado. Sin push.

### Queda para cerrar (fuera de este encargo)

- **T7** (líder, al desplegar): el mismo párrafo en `azure-apps/postventa_incidencias.md` §8 y una
  línea en «LO QUE CAMBIA EN ESTA REVISIÓN», con commit local en `azure-apps`.
- La cabecera de `docs/INTEGRACION.md` sigue diciendo F-036 / 2026-10-05. Cambiarla obliga a tocar
  `FECHA` y el texto de `test_f036_documentacion.py`, fuera de D-3: decisión del líder/humano.
- Review contra `CHECKPOINTS.md`, merge a `dev` y las MANUAL T10–T12.

## Evidencias

Finales (Bloques 1, 2 y 3).

| Evidencia | Valor |
|---|---|
| Tests ejecutados (suite del servicio api dentro de `init.sh`, T9) | **6706 pasan, 0 fallan, 81 omitidos**; servicio front en verde (caché) |
| Tests de F-053 | 69 nuevos (17 del Bloque 1, 33 del Bloque 2, 19 del Bloque 3), todos en verde |
| Cobertura de líneas cambiadas | **100,0 %** (8/8, umbral 80 %, nivel `critico`), `PUERTA COBERTURA` de `init.sh` |
| Mutantes | **5 generados, 0 supervivientes**: 2 muertos en la campaña y 3 en `timeout` que mueren en ~20 s con los tests de F-053 (comprobado uno a uno); más 13 a mano del design §7, los 13 muertos. Ver `progress/mutacion_F-053.md` |
| Tiempo de la suite | 3012,08 s (50 min 12 s) dentro de `init.sh`, con la máquina cargada por otras campañas; 897,52 s en el Bloque 2; 371,74 s en el Bloque 1 |
