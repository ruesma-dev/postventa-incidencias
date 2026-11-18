# F-072 · Bloque 6 · La revisión: aplicación y HTTP (T18, T19)

Rama `worktree-agent-ae890f60fa6b55ed9`, sobre `ecbfb0a` (integración del Bloque 5).
Commits: T18 `ca86fd2` (RED), T19 `46b0abe` (GREEN), `03b1e3d` (test que pide la mutación
a mano, M9), más el commit de este informe. Fuera de alcance por encargo: T20 (campaña y
review) y `bash harness/init.sh`, que los lanza el líder.

## Hecho

La revisión lee ya los tipos de reclamación de Sigrid: el listado, editar y aprobar hacen
**una** lectura por petición, tras el catálogo y las ubicaciones (R1); descartar y recuperar,
ninguna (R27). Lo leído sustituye a los `listados` del YAML (vacíos desde el Bloque 5), así
que `catalogo.listados` ofrece los tipos (R20), editar acepta sus códigos (R21, R22) y
`tipo_fuera_de_sigrid` se calcula en el listado, al aprobar y en la respuesta de cada acción
(R24; las dos llamadas sin `tipos` que señaló la review del Bloque 2, `revision.py:267` y
`:337`, ya los pasan). El `listado` de `importados`, `vigentes` y `GET /api/bandeja` es el
**tipo efectivo**, nunca `null` (R20, §8). La lectura caída es 503 y al techo 409, sin escribir
(R3, R4). El volcado sigue sin leer tipos (R29).

**Puente del Bloque 5, resuelto**: `test_f056_revision_http.py` ya no mete tipos ficticios en
`CONFIG` (vuelve a ser el YAML real); los sirve la fábrica del borde,
`construir_tipos_reclamacion` → `PuertoTiposEnMemoria`. o2/r10/r42 editan con `"9001"`, un
código vigente leído de la fuente, con el comentario puesto al día (R21, R22, R24).

## Ficheros (bajo `services/postventa-api/` salvo `docs/`)

Producción:
- `application/pipelines/revision.py`: `listar_para_revisar(..., tipos)` y
  `aplicar_accion(..., tipos)`; `listas_con_tipos` con lo leído; `_codigos` para R24; editar o
  aprobar sin `tipos` es `ValueError` («necesitan leer Sigrid»), como sin catálogo.
- `interface_adapters/api/revision.py`: parámetro `tipos` en `listar_revision` y
  `accion_de_revision`; por defecto `fuente_de_tipos(construir_tipos_reclamacion(...))`,
  construida tras las ubicaciones y antes de la base, solo al listar, editar y aprobar;
  `_valores_de` serializa `listado = tipo_efectivo(tipo_reclamacion)`. Tramos nuevos en la línea
  de F-060: `construir.tipos` y `tipos`.
- `interface_adapters/api/bandeja.py`: `listado` = tipo efectivo.
- `domain/models/revision.py`: **una línea**, `valores_importados` copia `tipo_reclamacion`
  (ver «Desviaciones»).
- `docs/ARCHITECTURE.md`: en «La medición del listado» (F-060), los dos tramos nuevos.

`function_app.py` sin cambios (sus docstrings siguen siendo ciertas). Sin tocar (R32): el
front, `infrastructure/sigrid/**`, el volcado, SQL, `config/`.

Tests nuevos: `tests/test_f072_revision_http.py` (40 casos) y la sección R29 de
`tests/test_f072_volcado.py` (9 casos). Utilidad: `TIPOS_CON_EL_DEFECTO` en
`tests/utiles_revision.py` (`9001` y `0002`, «TIPO FICTICIO N»).

## Desviaciones (para la review)

1. **`valores_importados` no copiaba `tipo_reclamacion`** (fallo del Bloque 2 que nadie había
   visto porque la revisión no leía tipos). Sin él, una incidencia importada con `9001` y sin
   revisar se veía en la revisión como `0002`, editarla conservando su tipo de baja daba 400
   (R21) y, aprobada sin editar, se volcaría con `0002` (R28). El fichero no está en la lista
   de T19, pero R19/R20/R21 lo exigen y el cambio es de una línea. Lo matan M22 y M23. La huella
   (R26) no cambia para las anteriores a F-072 (tipo nulo).
2. **Tramos de tiempo nuevos**: medir la lectura de los tipos (`tipos`) y su construcción
   (`construir.tipos`), como las ubicaciones. Si no, su tiempo caería en `calculo`, que dejaría
   de ser «la aplicación menos los puertos». `test_f060_documentacion` exige que la sección de
   ARCHITECTURE nombre cada tramo, de ahí la frase en `docs/` (T21 escribe la sección de F-072).
3. **Tipos de los tests de F-056/F-060**: los dobles de la aplicación sirven
   `TIPOS_CON_EL_DEFECTO`, con `0002` vigente como en el `auxtrcp` medido en T0, para que editar
   con `listado` nulo siga siendo aprobable y no cambien las secuencias de esos tests. Las dobles
   de tipos **no** anotan en `llamadas` ni en `construidos` en los tests anteriores; el orden lo
   fija `test_f072_revision_http.py`.

## Aserciones anteriores cambiadas (con su R), ninguna borrada

- `test_f056_revision_http`: `CONFIG` = YAML real (puente fuera); `catalogo.listados` son los
  tipos leídos (R20); r29 sin revisiones `listado: "0002"` (antes `None`) y duplicada `"9001"`
  (antes `"segundo"`) (R20); r8 `motivos_no_aprobable == ["tipo_fuera_de_sigrid"]` (antes `[]`,
  R22+R24: editar con nulo guarda `0002`, no vigente); `nada_se_construye` y r30 descartar
  incluyen `construir_tipos_reclamacion` (R1, R27); o2/r10/r42 solo el comentario.
- `test_f036_bandeja_http`: `listado` `"0002"` en vez de `"primero"` y de `None` (§8, R19).
- `test_f056_pipeline_revision`: r28 `resultado.listas == listas_con_tipos(LISTAS, …)` (R20);
  r46 «sin sus lecturas» parametriza también `tipos` (R1).
- `test_f060_tiempos`: la línea exacta con `construir.tipos=0.250` y `tipos=0.250` (total
  10.625 → 11.125, `aplicacion` 6.250 → 6.500; 11.625 → 12.125); `construidos` con `"tipos"`;
  «cuatro puertos» → cinco; excepciones con `tipos` (R1).
- `test_f056_alcance_cerrado::r39_de_sigrid_solo…`: el borde importa también
  `construir_tipos_reclamacion` (R1).
- `test_f056_ubicaciones`, `test_f060_pipeline_normalizacion`, `test_f059_volcado_http`,
  `test_f065_http`: solo inyectan o componen la fuente de los tipos (R1).

## Fase RED (T18, commit `ca86fd2`)

Desde `services/postventa-api` (sin `.venv` en el worktree, el de la carpeta principal):

```
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_f072_revision_http.py tests/test_f072_volcado.py --tb=line -o log_cli=false --show-capture=no
```

Salida real, una línea por motivo distinto (la traza entera, en el scratchpad de la sesión):

```
tests/test_f072_revision_http.py:256: AssertionError: assert ['catalogo.le...'ubicaciones'] == ['catalogo.le... 'tipos.leer']
tests/test_f072_revision_http.py:269: assert 0 == 2
tests/test_f072_revision_http.py:287: assert 400 == 200
tests/test_f072_revision_http.py:287: assert 409 == 200
tests/test_f072_revision_http.py:308: AssertionError: assert ['catalogo', ...quivalencias'] == ['catalogo', ...quivalencias']
tests/test_f072_revision_http.py:317: AssertionError: assert ['catalogo', ...', 'revision'] == ['catalogo', ...', 'revision']
tests/test_f072_revision_http.py:332: assert 200 == 503
tests/test_f072_revision_http.py:342: TypeError: aplicar_accion() got an unexpected keyword argument 'tipos'
tests/test_f072_revision_http.py:393: TypeError: accion_de_revision() got an unexpected keyword argument 'tipos'
tests/test_f072_revision_http.py:410: AssertionError: assert [] == [{'codigo': '...IO 2 (9002)'}]
tests/test_f072_revision_http.py:444: AssertionError: assert {1: ('primero... (None, None)} == {1: ('0002', ...002', '9001')}
tests/test_f072_revision_http.py:454: assert 400 == 200
tests/test_f072_revision_http.py:544: AssertionError: assert None == '0002'
tests/test_f072_revision_http.py:562: AssertionError: assert 'tipo_fuera_de_sigrid' in []
tests/test_f072_revision_http.py:574: assert 200 == 409
tests/test_f072_revision_http.py:606: assert 409 == 200
tests/test_f072_revision_http.py:628: assert 200 == 503
tests/test_f072_revision_http.py:639: AssertionError: assert (400, 'valores_no_validos') == (409, 'catalo...in_verificar')
tests/test_f072_revision_http.py:639: KeyError: 'codigo'
tests/test_f072_revision_http.py:671: AssertionError: assert ['segundo', None, 'primero'] == ['0002', '9001', '9009']
33 failed, 27 passed in 4.02s
```

Los 27 que ya pasaban: los 22 de `test_f072_volcado.py` (los 13 del Bloque 1 y los 9 de R29,
que fija un comportamiento que **no cambia**: el volcado ya mandaba el tipo guardado y ya
trataba `tipo_no_valido` como rechazo) y 5 de la revisión cuyo resultado coincide con el de
hoy por accidente: R27 al descartar y recuperar (hoy nadie lee tipos), «sin tipos vigentes,
ninguno» y los dos 400 de R21 (hoy los `listados` del YAML están vacíos, así que todo código
es inválido). Los mantiene la mutación (M9, M15, M7).

## GREEN (T19, commits `46b0abe` y `03b1e3d`)

- Verificación de tasks.md (los cinco ficheros de T19): **359 passed in 5.40s**; con el test
  de M9, `test_f072_revision_http.py` **40 passed** (38 + los 2 casos del nuevo).
- Suite `api` completa (`… -m pytest -q -p no:cacheprovider tests --tb=line`), primera vuelta:
  **1 failed, 10248 passed, 369 skipped in 1117.92s**. El fallo era
  `test_f056_alcance_cerrado::test_f056_r39_de_sigrid_solo_se_usa_el_catalogo_de_f036` (lista
  cerrada de importaciones de Sigrid del borde); corregido en `46b0abe` (ver arriba) y
  relanzado con la verificación: `372 passed, 9 skipped`. Ningún `test_f036_r115_*` falló. **La
  suite entera no se relanzó tras esa corrección ni tras `03b1e3d`**, que añade un test y no toca
  producción: la cifra final de la suite la da el `init.sh` del líder.
- `ruff check --select F` (pyflakes) sobre los 15 ficheros tocados: sin avisos. El `ruff` de
  `init.sh` no está en este `.venv`.

## Mutación a mano dirigida (líneas nuevas con lógica)

Script en el scratchpad: aplica el mutante, lanza el test con `-x`, restaura los bytes
originales. **24 mutantes, 24 muertos, 0 supervivientes**. M9 sobrevivió en la primera vuelta:
el borde no pasa la fuente al descartar, así que el test HTTP no podía verlo. Se añadió
`test_f072_r27_la_aplicacion_no_lee_los_tipos_al_descartar_ni_al_recuperar` (`03b1e3d`) y
murió. M24 se aplicó a mano (el fichero tiene CRLF y el script no lo casaba). Árbol limpio al
final (`git status` vacío antes de escribir este informe).

| mutante | test que lo mata | resultado |
|---|---|---|
| M1 pipeline, listar: una lectura de tipos de más (R1) | `r1_listar_lee_los_tipos_una_vez_tras_catalogo_y_ubicaciones` | muerto |
| M2 pipeline, listar: tipos antes que ubicaciones (R1) | ídem | muerto |
| M3 pipeline, listar: motivos de la fila sin tipos (R24) | `r24_un_tipo_guardado_fuera_de_sigrid_es_motivo_en_la_fila` | muerto |
| M4 pipeline, listar: la página con las listas del YAML (R20) | `r20_catalogo_listados_son_los_tipos_leidos` | muerto |
| M5 pipeline, acción: tipos antes que ubicaciones (R1) | `r1_editar_y_aprobar_leen_los_tipos_una_vez_antes_de_escribir` | muerto |
| M6 pipeline, acción: sin la guarda `tipos is None` | `r1_editar_sin_la_fuente_de_los_tipos_es_un_error_de_programacion` | muerto |
| M7 pipeline, acción: decidir con las listas del YAML (R21) | `r21_editar_con_un_tipo_vigente_lo_guarda` | muerto |
| M8 pipeline, acción: respuesta sin tipos (R24, `:337`) | `r24_la_respuesta_de_editar_lleva_el_motivo` | muerto |
| M9 pipeline, acción: descartar/recuperar leen tipos (R27) | `r27_la_aplicacion_no_lee_los_tipos_al_descartar_ni_al_recuperar` | muerto (tras `03b1e3d`) |
| M10 pipeline, acción: 503 tragado como lista vacía (R3) | `r3_si_la_lectura_de_tipos_falla_es_503_sin_escribir` | muerto |
| M11 pipeline, listar: 409 tragado como lista vacía (R4) | `r4_si_los_tipos_llegan_al_techo_es_409_sin_escribir` | muerto |
| M12 borde, listar: la fuente se construye antes que las ubicaciones | `r1_al_listar_los_tipos_se_construyen_tras_catalogo_y_ubicaciones` | muerto |
| M13 borde, listar: la lectura sin medir | `test_f060_r40_el_listado_deja_una_linea_con_cada_tramo` | muerto |
| M14 borde, listar: la construcción sin su tramo | ídem | muerto |
| M15 borde, acción: la fuente se construye también al descartar (R27) | `r27_descartar_y_recuperar_ni_construyen_ni_leen_los_tipos` | muerto |
| M16 borde, acción: la fuente se construye tras la base | `r1_al_actuar_los_tipos_se_construyen_tras_catalogo_y_ubicaciones` | muerto |
| M17 borde, acción: no pasa la fuente a la aplicación | `r21_editar_con_un_tipo_vigente_lo_guarda` | muerto |
| M18 borde, fila: `listado` con el heredado (R20) | `r20_listado_de_importados_y_vigentes_es_el_tipo_efectivo` | muerto |
| M19 borde, fila: el tipo guardado sin efectivo (R20) | ídem | muerto |
| M20 bandeja: `listado` con el heredado (§8) | `s8_la_bandeja_lleva_el_tipo_efectivo_en_listado` | muerto |
| M21 bandeja: el tipo guardado sin efectivo (§8) | ídem | muerto |
| M22 dominio: `valores_importados` sin el tipo (R20) | `r20_listado_de_importados_y_vigentes_es_el_tipo_efectivo` | muerto |
| M23 dominio: ídem, conservar el de baja (R21) | `r21_el_tipo_que_ya_tiene_se_conserva_aunque_este_de_baja` | muerto |
| M24 `api/volcado.py` importa `construir_tipos_reclamacion` (R29) | `test_f072_volcado::r29_el_volcado_no_lee_auxtrcp` | muerto |

Lo que estos mutantes no prueban: `tipos=tipos if lee_sigrid else None` en el borde, cambiado
a `tipos=tipos`, es **equivalente**, porque la aplicación solo lee en `_LEEN_SIGRID` (M9 lo
cubre por dentro). No se generó.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (suite `api` completa) | 10248 passed, 369 skipped, 1 failed (alcance R39, corregido y relanzado aparte: 372 passed) |
| Verificación dirigida de T19 | 359 passed |
| Cobertura de las líneas cambiadas | no medida: sale de `PUERTA COBERTURA` de `init.sh`, que lanza el líder |
| Mutantes (a mano, dirigidos) | 24 generados, 24 muertos, 0 supervivientes (M9 vivo en la primera vuelta, cerrado con un test) |
| Campaña `harness.mutacion` | no lanzada: es T20, del líder |
| Tiempo de la suite | 1117.92 s (dirigida: 5.40 s) |
| Capa e2e | N/A (el front no cambia, R32) |

## Pendiente

- T20 (campaña de mutación del bloque y review) y `bash harness/init.sh`: los lanza el líder.
  Esa ejecución es la primera de la suite entera tras `46b0abe` y `03b1e3d`.
- La review decide sobre las tres desviaciones, sobre todo la 1 (`valores_importados`).
- T21 (Bloque 7) escribe la sección de F-072 en ARCHITECTURE; aquí solo están los dos tramos.
