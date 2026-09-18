# F-033 · Informe del implementer

> Rama `feature/F-033-l1-traza-archivo`. Rigor `critico`.
> Este informe crece por bloques: **Bloque 1 (T1–T4)**, **Bloque 2 (T5–T8)** y **Bloque 3 (T9–T12)** abajo; al final, el **resumen para el reviewer**.

## Bloque 1 · La traza en la situación (persistencia)

### Fase RED · T1 (traza real, antes de tocar producción)

Comando, lanzado desde `services/postventa-api/` con el intérprete del
servicio (el del `harness/servicios.json`), sobre `9bcc92d` más solo el
fichero de tests nuevo:

```
.venv/Scripts/python.exe -m pytest tests/test_f033_situacion_con_archivo.py -q --tb=line -p no:cacheprovider
```

> El comando literal de `tasks.md` (`python -m pytest services/postventa-api/tests/...`
> desde la raíz) usa el Python global, que no trae `pydantic`: falla en la
> carga de `conftest.py` antes de ejecutar nada. Por eso se usa el `venv` del
> servicio, que es el mismo que usa `harness/init.sh`.

Salida completa:

```
FFFFFFF.FFFFFFFFFFFFFFFFFFFFF.FFF..FFFF                                  [100%]
================================== FAILURES ===================================
E   AttributeError: 'SituacionParte' object has no attribute 'archivo'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:137: AttributeError: 'SituacionParte' object has no attribute 'archivo'
E   AssertionError: assert ('decision_hu... 'validacion') == ('decision_hu...n', 'archivo')
      
      Right contains one more item: 'archivo'
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:144: AssertionError: assert ('decision_hu... 'validacion') == ('decision_hu...n', 'archivo')
E   TypeError: SituacionParte.__init__() got an unexpected keyword argument 'archivo'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:157: TypeError: SituacionParte.__init__() got an unexpected keyword argument 'archivo'
E   AttributeError: module 'infrastructure.persistencia.sentencias' has no attribute '_COLUMNAS_ARCHIVO'. Did you mean: '_COLUMNAS_GRAFICO'?
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:167: AttributeError: module 'infrastructure.persistencia.sentencias' has no attribute '_COLUMNAS_ARCHIVO'. Did you mean: '_COLUMNAS_GRAFICO'?
E   AssertionError: assert 'LEFT JOIN postventa.archivos AS a ON a.hash_parte = p.hash_parte' in 'SELECT v.veredicto, v.destino, v.clasificacion_firma, v.motivos,\n       v.avisos,\n       p.observaciones, p.observa... v.hash_parte = p.hash_parte\nLEFT JOIN postventa.cierres AS c ON c.hash_parte = p.hash_parte\nWHERE p.hash_parte = %s'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:185: AssertionError: assert 'LEFT JOIN postventa.archivos AS a ON a.hash_parte = p.hash_parte' in 'SELECT v.veredicto, v.destino, v.clasificacion_firma, v.motivos,\n       v.avisos,\n       p.observaciones, p.observa... v.hash_parte = p.hash_parte\nLEFT JOIN postventa.cierres AS c ON c.hash_parte = p.hash_parte\nWHERE p.hash_parte = %s'
E   AssertionError: assert () == ('a.estado', ...web_url', ...)
      
      Right contains 8 more items, first extra item: 'a.estado'
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:207: AssertionError: assert () == ('a.estado', ...web_url', ...)
E   AttributeError: module 'infrastructure.persistencia.sentencias' has no attribute '_COLUMNAS_ARCHIVO'. Did you mean: '_COLUMNAS_GRAFICO'?
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:222: AttributeError: module 'infrastructure.persistencia.sentencias' has no attribute '_COLUMNAS_ARCHIVO'. Did you mean: '_COLUMNAS_GRAFICO'?
E   AttributeError: 'SituacionParte' object has no attribute 'archivo'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:246: AttributeError: 'SituacionParte' object has no attribute 'archivo'
E   AttributeError: 'SituacionParte' object has no attribute 'archivo'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:259: AttributeError: 'SituacionParte' object has no attribute 'archivo'
E   AttributeError: 'SituacionParte' object has no attribute 'archivo'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:259: AttributeError: 'SituacionParte' object has no attribute 'archivo'
E   AttributeError: 'SituacionParte' object has no attribute 'archivo'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:259: AttributeError: 'SituacionParte' object has no attribute 'archivo'
E   AttributeError: 'SituacionParte' object has no attribute 'archivo'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:268: AttributeError: 'SituacionParte' object has no attribute 'archivo'
E   AssertionError: assert None == 'cerrado'
     +  where None = SituacionParte(decision_humana=None, ultimo_estado_registrado=None, estado_cierre=None, validacion=None).estado_cierre
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:278: AssertionError: assert None == 'cerrado'
E   AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_traza_archivo'. Did you mean: 'fila_a_traza_grafico'?
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:285: AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_traza_archivo'. Did you mean: 'fila_a_traza_grafico'?
E   AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_traza_archivo'. Did you mean: 'fila_a_traza_grafico'?
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:294: AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_traza_archivo'. Did you mean: 'fila_a_traza_grafico'?
E   AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_traza_archivo'. Did you mean: 'fila_a_traza_grafico'?
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:301: AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_traza_archivo'. Did you mean: 'fila_a_traza_grafico'?
E   AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_situacion_guardada'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:310: AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_situacion_guardada'
E   AssertionError: assert 0 == 1
     +  where 0 = veces_con('LEFT JOIN postventa.archivos AS a')
     +    where veces_con = <tests.utiles_pg.ConexionDoble object at 0x000001EE861DAB70>.veces_con
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:337: AssertionError: assert 0 == 1
E   AssertionError: assert 0 == 1
     +  where 0 = veces_con('LEFT JOIN postventa.archivos AS a')
     +    where veces_con = <tests.utiles_pg.ConexionDoble object at 0x000001EE861F1C40>.veces_con
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:337: AssertionError: assert 0 == 1
E   StopIteration
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:344: StopIteration
E   AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_situacion_guardada'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:361: AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_situacion_guardada'
E   AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_situacion_guardada'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:361: AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_situacion_guardada'
E   AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_situacion_guardada'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:361: AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_situacion_guardada'
E   AttributeError: 'SituacionParte' object has no attribute 'archivo'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:375: AttributeError: 'SituacionParte' object has no attribute 'archivo'
E   AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_traza_archivo'. Did you mean: 'fila_a_traza_grafico'?
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:390: AttributeError: module 'infrastructure.persistencia.mapeo' has no attribute 'fila_a_traza_archivo'. Did you mean: 'fila_a_traza_grafico'?
E   Failed: DID NOT RAISE ValueError
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:401: Failed: DID NOT RAISE ValueError
E   AssertionError: assert 'archivo=archivado' in 'INFO     infrastructure.persistencia.repositorio_pg:repositorio_pg.py:312 F-028 situación del parte leída: hash=hash-inventado-f033 decidida_por_persona=False ultimo_estado=None cierre=None destino=None\n'
     +  where 'INFO     infrastructure.persistencia.repositorio_pg:repositorio_pg.py:312 F-028 situación del parte leída: hash=hash-inventado-f033 decidida_por_persona=False ultimo_estado=None cierre=None destino=None\n' = <_pytest.logging.LogCaptureFixture object at 0x000001EE8622CDD0>.text
------------------------------ Captured log call ------------------------------
INFO     infrastructure.persistencia.repositorio_pg:repositorio_pg.py:312 F-028 situación del parte leída: hash=hash-inventado-f033 decidida_por_persona=False ultimo_estado=None cierre=None destino=None
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:417: AssertionError: assert 'archivo=archivado' in 'INFO     infrastructure.persistencia.repositorio_pg:repositorio_pg.py:312 F-028 situación del parte leída: hash=hash-inventado-f033 decidida_por_persona=False ultimo_estado=None cierre=None destino=None\n'
E   AssertionError: assert 'archivo=None' in 'INFO     infrastructure.persistencia.repositorio_pg:repositorio_pg.py:312 F-028 situación del parte leída: hash=hash-inventado-f033 decidida_por_persona=False ultimo_estado=None cierre=None destino=None\n'
     +  where 'INFO     infrastructure.persistencia.repositorio_pg:repositorio_pg.py:312 F-028 situación del parte leída: hash=hash-inventado-f033 decidida_por_persona=False ultimo_estado=None cierre=None destino=None\n' = <_pytest.logging.LogCaptureFixture object at 0x000001EE861DA870>.text
------------------------------ Captured log call ------------------------------
INFO     infrastructure.persistencia.repositorio_pg:repositorio_pg.py:312 F-028 situación del parte leída: hash=hash-inventado-f033 decidida_por_persona=False ultimo_estado=None cierre=None destino=None
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:427: AssertionError: assert 'archivo=None' in 'INFO     infrastructure.persistencia.repositorio_pg:repositorio_pg.py:312 F-028 situación del parte leída: hash=hash-inventado-f033 decidida_por_persona=False ultimo_estado=None cierre=None destino=None\n'
E   AssertionError: assert 'WHERE postventa.archivos.estado <> %s' in 'INSERT INTO postventa.archivos (hash_parte, estado, nombre_fichero, carpeta, drive_id, item_id, web_url, motivo, arch...do_at_utc = EXCLUDED.archivado_at_utc,\n    intentos = postventa.archivos.intentos + 1\nRETURNING (xmax = 0) AS creado'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:459: AssertionError: assert 'WHERE postventa.archivos.estado <> %s' in 'INSERT INTO postventa.archivos (hash_parte, estado, nombre_fichero, carpeta, drive_id, item_id, web_url, motivo, arch...do_at_utc = EXCLUDED.archivado_at_utc,\n    intentos = postventa.archivos.intentos + 1\nRETURNING (xmax = 0) AS creado'
E   AttributeError: module 'infrastructure.persistencia.sentencias' has no attribute '_ESTADO_ARCHIVO_TERMINAL'. Did you mean: '_ESTADO_GRAFICO_TERMINAL'?
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:471: AttributeError: module 'infrastructure.persistencia.sentencias' has no attribute '_ESTADO_ARCHIVO_TERMINAL'. Did you mean: '_ESTADO_GRAFICO_TERMINAL'?
E   AttributeError: module 'infrastructure.persistencia.sentencias' has no attribute '_COLUMNAS_ARCHIVO'. Did you mean: '_COLUMNAS_GRAFICO'?
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:483: AttributeError: module 'infrastructure.persistencia.sentencias' has no attribute '_COLUMNAS_ARCHIVO'. Did you mean: '_COLUMNAS_GRAFICO'?
E   AssertionError: assert <ResultadoGuardado.CREADO: 'creado'> is <ResultadoGuardado.SIN_CAMBIOS: 'sin_cambios'>
     +  where <ResultadoGuardado.SIN_CAMBIOS: 'sin_cambios'> = ResultadoGuardado.SIN_CAMBIOS
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:540: AssertionError: assert <ResultadoGuardado.CREADO: 'creado'> is <ResultadoGuardado.SIN_CAMBIOS: 'sin_cambios'>
E   AssertionError: assert <ResultadoGuardado.CREADO: 'creado'> is <ResultadoGuardado.ACTUALIZADO: 'actualizado'>
     +  where <ResultadoGuardado.ACTUALIZADO: 'actualizado'> = ResultadoGuardado.ACTUALIZADO
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:552: AssertionError: assert <ResultadoGuardado.CREADO: 'creado'> is <ResultadoGuardado.ACTUALIZADO: 'actualizado'>
E   AttributeError: 'SituacionParte' object has no attribute 'archivo'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:565: AttributeError: 'SituacionParte' object has no attribute 'archivo'
E   AttributeError: 'SituacionParte' object has no attribute 'archivo'
C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f033_situacion_con_archivo.py:574: AttributeError: 'SituacionParte' object has no attribute 'archivo'
=========================== short test summary info ===========================
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r1_la_situacion_trae_archivo_a_none_por_omision
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r1_archivo_es_el_ultimo_de_cinco_campos
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r1_la_situacion_guarda_la_traza_que_se_le_da
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_columnas_archivo_es_la_lista_de_la_tabla_en_su_orden
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_la_sentencia_hace_left_join_a_archivos_anclado_en_partes
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_las_ocho_columnas_nuevas_van_al_final_en_su_orden
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_las_columnas_nuevas_salen_de_la_misma_lista_que_escribe
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_el_adaptador_devuelve_la_traza_con_sus_ocho_campos
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_el_adaptador_traduce_cada_estado_de_archivo[pendiente]
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_el_adaptador_traduce_cada_estado_de_archivo[archivado]
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_el_adaptador_traduce_cada_estado_de_archivo[error]
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_sin_fila_en_archivos_la_traza_es_none
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_la_traza_convive_con_el_veredicto_y_el_cierre
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_fila_a_traza_archivo_toma_el_hash_por_palabra_clave
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_fila_a_traza_archivo_sin_estado_es_none
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_la_traza_con_campos_opcionales_a_none_se_lee_igual
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_fila_a_situacion_guardada_parte_la_fila_en_sus_dos_tramos
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r3_la_situacion_sigue_costando_dos_sentencias[True]
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r3_la_situacion_sigue_costando_dos_sentencias[False]
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r3_el_corte_del_mapeo_coincide_con_la_sentencia
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r3_una_fila_de_otro_largo_revienta[17]
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r3_una_fila_de_otro_largo_revienta[19]
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r3_una_fila_de_otro_largo_revienta[10]
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r4_sin_ficha_los_tres_huecos_a_none_y_sin_error
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r5_un_estado_de_archivo_desconocido_revienta_en_el_mapeo
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r5_un_estado_desconocido_revienta_en_el_adaptador
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r6_el_log_trae_el_estado_de_la_traza
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r6_el_log_dice_que_no_hay_traza
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r17_el_upsert_no_actualiza_una_fila_archivada
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r17_el_estado_terminal_va_como_parametro
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r17_el_insert_escribe_las_columnas_de_la_lista_unica
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r17_el_doble_como_la_base_no_pisa_una_traza_archivada
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r17_el_doble_como_la_base_si_pisa_una_traza_pendiente
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r2_el_doble_como_la_base_devuelve_la_traza_desde_columnas
FAILED tests/test_f033_situacion_con_archivo.py::test_f033_r4_el_doble_como_la_base_sin_ficha_no_trae_traza
35 failed, 4 passed in 0.86s
```

Lectura del rojo, contra lo que pedía T1:

- **`SituacionParte` sin `archivo`**: `AttributeError: 'SituacionParte' object has no attribute 'archivo'`
  y `TypeError: ... unexpected keyword argument 'archivo'` (R1, R2, R4).
- **Sentencia sin tercer `JOIN`**: `assert 'LEFT JOIN postventa.archivos AS a ON a.hash_parte = p.hash_parte' in 'SELECT ...'`
  y `assert () == ('a.estado', ...)` (R2, R3).
- **`upsert_archivo` sin `WHERE`**: `assert 'WHERE postventa.archivos.estado <> %s' in 'INSERT INTO postventa.archivos ...'`
  y `no attribute '_ESTADO_ARCHIVO_TERMINAL'` (R17).
- Mapeo inexistente: `no attribute 'fila_a_traza_archivo'` / `'fila_a_situacion_guardada'` (R2, R3, R5).
- Log sin el estado de la traza (R6): la línea real es
  `... cierre=None destino=None`, sin `archivo=`.
- El doble `RepositorioComoLaBase` pisa una traza `archivado` (`CREADO is SIN_CAMBIOS`) (R17).

**Los 4 que ya pasaban en rojo, y por qué** (no son falsos verdes, son
garantías que ya existían y que el test fija para que no se pierdan):

1. `test_f033_r2_el_hash_sigue_siendo_el_unico_parametro`: la sentencia ya
   llevaba un único `%s`; el caso vigila que el tercer `JOIN` no añada otro.
2. `test_f033_r6_el_log_no_trae_identificadores_de_biblioteca`: hoy el log no
   trae nada de la traza, así que tampoco sus identificadores; el caso vigila
   que al añadir el estado no se cuele nada más.
3. `test_f033_r17_sin_fila_de_vuelta_el_repositorio_responde_sin_cambios` y
4. `test_f033_r17_el_log_de_guardar_registra_sin_cambios`: `_escribir` ya
   traduce «sin fila» a `SIN_CAMBIOS` para cualquier escritura (lo usan
   `cierres` y `graficos`). Lo nuevo de R17 es que la sentencia **lo
   provoque** para `archivos`, y eso sí estaba en rojo (casos de la sentencia).

### Tareas del bloque 1 (commits)

| Tarea | Commit | Qué |
|---|---|---|
| T1 | `29758f0` | RED: `tests/test_f033_situacion_con_archivo.py` (39 casos) |
| T2 | `257456d` | `SituacionParte.archivo` (quinto campo, el último, `None` por omisión) + enmiendas fechadas |
| T3 | `60e61c7` | `sentencias.py`: `_COLUMNAS_ARCHIVO`, `WHERE … estado <> %s` en `upsert_archivo`, tercer `LEFT JOIN` |
| T4 | `9d0fc33` | `mapeo.py` + `repositorio_pg.py` + `RepositorioComoLaBase`; filas de diez → dieciocho |

### Qué cambió (ficheros tocados)

Producción (`services/postventa-api/`):

- `domain/models/estado.py`: `archivo: TrazaArchivo | None = None`, último
  campo; «**Cuatro cosas.**» → «**Cinco cosas.**», con enmienda fechada que
  cita la frase vieja (R1).
- `domain/ports/persistencia.py`: solo docstrings (`consultar_situacion`: la
  quinta cosa; `guardar_archivo`: no pisa `archivado`). Ningún método nuevo.
- `infrastructure/persistencia/sentencias.py`: `_COLUMNAS_ARCHIVO` (lista única
  para escribir y leer); `upsert_archivo` con `WHERE {tabla}.estado <> %s` y
  `_ESTADO_ARCHIVO_TERMINAL = "archivado"` como **último parámetro** (R17);
  `select_veredicto_y_cierre` con `LEFT JOIN postventa.archivos AS a ON
  a.hash_parte = p.hash_parte` y las ocho columnas `a.*` al final, generadas
  desde `_COLUMNAS_ARCHIVO[1:]` (R2, R3). Nombre de la función conservado.
- `infrastructure/persistencia/mapeo.py`: `COLUMNAS_ANTES_DE_LA_TRAZA = 10`,
  `COLUMNAS_DE_TRAZA_ARCHIVO = 8`, `fila_a_traza_archivo(columnas, *, hash_parte)`
  y `fila_a_situacion_guardada(fila, *, hash_parte)`. `fila_a_validacion_y_cierre`
  **sin tocar** (R2–R5).
- `infrastructure/persistencia/repositorio_pg.py`: `consultar_situacion` usa
  `fila_a_situacion_guardada`, rellena `archivo` y añade `archivo=<estado|None>`
  al log (R6). Siguen siendo **dos** `_leer`. Docstring de `guardar_archivo`.

Tests:

- Nuevo: `tests/test_f033_situacion_con_archivo.py`.
- `tests/utiles_pg.py::RepositorioComoLaBase`: `guardar_archivo` con semántica
  terminal (`archivado` → `SIN_CAMBIOS`; `pendiente`/`error` → `ACTUALIZADO`);
  la fila de la situación lleva las ocho columnas de la traza (sacadas de los
  parámetros de `sentencias.upsert_archivo`, u ocho `None`) y se parte con
  `mapeo.fila_a_situacion_guardada`, la función de producción.
- Cambios **de forma** listados en §7: `test_f005_sentencias.py` (3 casos:
  cuatro tablas; tres `JOIN`, todos `LEFT`, con aserto del tercero; tupla de
  dieciocho) y `test_f028_persistencia.py` (`_fila_de_lo_guardado` y la fila
  literal del caso `test_f028_r18_…`: de diez a dieciocho).
- Cambios de forma **fuera de la lista de §7**: ver «Desviaciones».

Ni una línea bajo `infrastructure/persistencia/sql/` (**sin DDL**), ni en el
paso, ni en `archivar.py`, ni en el front, ni en `harness/features.json`.

### Decisiones de diseño

1. **Nombre del corte.** El diseño pedía «constante con nombre» sin fijarlo.
   El primer nombre, `COLUMNAS_DE_VEREDICTO_Y_CIERRE`, hizo saltar el barrido
   de F-009 R3 (`test_f009_r3_ninguna_constante_de_estado_de_produccion_es_un_numero`,
   que busca `CIERRE`/`ESTADO` en constantes enteras). Se renombró a
   `COLUMNAS_ANTES_DE_LA_TRAZA` en vez de tocar ese barrido.
2. **El doble recompone la traza desde los parámetros de producción**
   (`sentencias.upsert_archivo`) y no desde una copia escrita a mano. Sigue
   guardando el objeto en `base.archivos`, porque
   `test_f030_circuito_borde_a_borde.py:309` lo lee así.
3. **El `ValueError`** de una fila de otro largo dice cuántas columnas trae y
   cuántas se esperaban; no lleva ningún valor de la fila.
4. El test del corte (R3) compara la constante con la **posición real** de la
   primera `a.` del `SELECT`, no con un 10 suelto.

### Desviaciones respecto a la spec (justificadas)

- **D-impl-1 · Dos tests fijaban el conjunto exacto de campos de
  `SituacionParte`** y no estaban en la lista cerrada de `design.md` §7:
  `test_f028_estado_dominio.py::test_f028_r2_la_situacion_trae_las_tres_cosas_que_hacen_falta_y_ninguna_mas`
  y `test_f030_veredicto_persistido.py::test_f030_r2_la_situacion_reune_las_cuatro_cosas_y_ninguna_mas`.
  R1 (aprobado) exige el quinto campo: no había implementación posible sin
  tocarlos. Se tratan como **cambio de forma**, análogo a la «tupla de
  columnas» que §7 sí lista: se añade `"archivo"` y se **mantiene la igualdad
  exacta** (un sexto campo los sigue poniendo en rojo). El propio caso de F-028
  prescribe el procedimiento («la enmienda del campo nuevo está escrita y
  fechada en la docstring de `SituacionParte`») y se ha seguido, con enmienda
  fechada también en la docstring de cada test. **Para el reviewer**: si lo
  considera cambio de expectativa, es esto lo que hay que mirar.
- **D-impl-2 · `test_f005_logs_sin_datos_personales.py::test_f030_r21_…`**
  prepara una fila literal de diez columnas para `consultar_situacion` y no
  estaba en §7. Se le añaden ocho `None` (sin traza). Mismo tipo de cambio que
  `_fila_de_lo_guardado`; los asertos, intactos.
- **D-impl-3 · El ayudante de fila de `test_f030_veredicto_persistido.py`
  (l. 859, `_fila_de_la_consulta`) NO se ha cambiado**, aunque §7 lo lista.
  Solo alimenta a `mapeo.fila_a_validacion_y_cierre`, que sigue siendo de diez
  columnas y no cambia (`design.md` §3.3). Alargarlo lo rompía (probado: 7
  rojos «too many values to unpack (expected 10)»). La única edición en ese
  fichero es la de D-impl-1.
- **Comandos de verificación**: los de `tasks.md` (`python -m pytest
  services/postventa-api/tests/...` desde la raíz) usan el Python global, sin
  `pydantic`; se han ejecutado con el `venv` del servicio desde
  `services/postventa-api/`, que es lo mismo que hace `harness/init.sh`.

### Qué se verificó, con el resultado real

- T2: `pytest tests -q -k "f028 or f030"` → `514 passed, 2 skipped` (tras
  D-impl-1; antes, 2 rojos: los dos casos del conjunto de campos).
- T3: `pytest tests/test_f005_sentencias.py -q` → `26 passed`. En
  `test_f033_…` pasaban ya los de la sentencia (R2 de forma, R17); seguían en
  rojo los que necesitan el mapeo (T4), como estaba previsto.
- T4: `pytest tests/test_f033_situacion_con_archivo.py -q` → `39 passed`
  (incluido R3 contado, `len(conexion.ejecutadas) == 2`, con traza y sin ella);
  `pytest tests -q -k "f005 or f028 or f030"` en verde; suite entera
  `2931 passed, 10 skipped`.
- `bash harness/init.sh` → **ENTORNO LISTO** (ver «Evidencias»).

### Verificaciones MANUAL pendientes

Ninguna de este bloque. T13 y T14 (humano) siguen pendientes, fuera de la rama.

### Qué queda fuera de este bloque

- **Bloque 2** (T5–T8): L1 en el paso y en el endpoint. Con solo este bloque
  `/api/archivar` **no cambia de comportamiento**: el paso sigue usando
  `traza_previa` y el endpoint no se la pasa. Lo que sí cambiaría al
  desplegar solo esto: la consulta de la situación trae ocho columnas más por
  un `LEFT JOIN`, y `upsert_archivo` deja de pisar una traza `archivado` (el
  paso aún no mira ese `SIN_CAMBIOS`; eso es R18/R19, bloque 2). No se
  recomienda desplegar el bloque 1 suelto.
- **Bloque 3** (T9–T12): `ARCHITECTURE.md`, control de alcance, mutación,
  `init.sh` final.

## Evidencias (bloque 1)

| Evidencia | Valor medido |
|---|---|
| Tests del servicio `api` (dentro de `bash harness/init.sh`) | **2931 passed, 20 skipped**, 0 fallos |
| Tests de la raíz (`init.sh`) | 62 passed |
| Tests nuevos de F-033 | 39 en `test_f033_situacion_con_archivo.py`, todos en verde |
| Cobertura de las líneas cambiadas | **100.0 % de 21 líneas** (21/21, umbral 80 %, nivel `critico`), línea `PUERTA COBERTURA` de `init.sh` |
| Tiempo de la suite del servicio | 105.54 s con cobertura (dentro de `init.sh`); 55.12 s sin cobertura |
| Mutantes generados / supervivientes | **No medido en este bloque, por plan**: la campaña es la tarea **T11** del bloque 3 (`python -m harness.mutacion --feature F-033`), sobre el diff completo de la feature. Lanzarla ahora obligaría a repetirla entera tras el bloque 2 |
| `ruff` sobre los ficheros tocados | los mismos 2 avisos previos (`PYI034` en `utiles_pg.py`), ninguno nuevo |

---

## Bloque 2 · L1 en el paso y en el endpoint (T5–T8)

### Fase RED · T5 (salida real, antes de tocar producción)

Comando, lanzado desde `services/postventa-api/` con el `venv` del servicio
(mismo motivo que en el bloque 1: el Python global no trae `pydantic`), sobre
`3cfe4c6` más solo los dos ficheros de tests nuevos (commit `b98ac7d`):

```
.venv/Scripts/python.exe -m pytest tests/test_f033_l1_desde_el_almacen.py tests/test_f033_archivar_http.py -q --tb=line -p no:cacheprovider --show-capture=no
```

Lo que interesa leer en la traza:

- **El defecto D-A1, cazado**: `test_f033_circuito_archivar_dos_veces_sube_una`
  cae en `test_f033_archivar_http.py:318: assert 2 == 1` — la biblioteca
  falsa recibió **dos subidas** del mismo parte con `RepositorioComoLaBase`.
  Es exactamente lo que `tasks.md` T5 exige ver en rojo.
- R7/R10/R13: con la traza `archivado` en la situación, el paso llamaba al
  archivador (`assert [('asegurar_c...')] == []`) y escribía la traza previa
  (`assert 2 == 0`, `'repositorio.guardar_archivo(pendiente)' not in [...]`).
- R12 desde el endpoint: el cuerpo de la respuesta no era el de la traza
  guardada y `avisos == []`.
- R7/R21: `traza_previa` seguía en la firma y `DID NOT RAISE TypeError`.
- R14/R15/R20: los avisos nuevos y `drive_id_vigente` no existían
  (`AttributeError`, `TypeError: ... unexpected keyword argument
  'drive_id_vigente'`); R18/R19: `RepositorioFalso` sin `resultados`.
- Los 14 que ya pasaban son **guardas de regresión** que tienen que seguir
  así: orden de F-019 sin corte, `pendiente`/`error` no cortan, un escaneo
  nuevo sube con aviso de reemplazo, el nombrado va antes que L1, etc.

Salida completa (solo se ha quitado el prefijo absoluto de las rutas):

```
FFFFF.F...F...FFFFFFFFFFFF.FFFFFFF.FFF...FF.F.FFFFFFFF                   [100%]
================================== FAILURES ===================================
E   assert 'traza_previa' not in mappingproxy(OrderedDict({'ctx': <Parameter "ctx: 'ContextoParte'">, 'archivador': <Parameter "archivador: 'ArchivoPor..., 'ahora': <Parameter "ahora: 'datetime'">, 'traza_previa': <Parameter "traza_previa: 'TrazaArchivo | None' = None">}))
tests\test_f033_l1_desde_el_almacen.py:187: assert 'traza_previa' not in mappingproxy(OrderedDict({'ctx': <Parameter "ctx: 'ContextoParte'">, 'archivador': <Parameter "archivador: 'ArchivoPor..., 'ahora': <Parameter "ahora: 'datetime'">, 'traza_previa': <Parameter "traza_previa: 'TrazaArchivo | None' = None">}))
E   Failed: DID NOT RAISE TypeError
tests\test_f033_l1_desde_el_almacen.py:194: Failed: DID NOT RAISE TypeError
E   KeyError: 'drive_id_vigente'
tests\test_f033_l1_desde_el_almacen.py:202: KeyError: 'drive_id_vigente'
E   AssertionError: assert [('asegurar_c...cation/pdf'})] == []
      
      Left contains 3 more items, first extra item: ('asegurar_carpeta', {'carpeta': 'Postventa/0677'})
      Use -v to get more diff
tests\test_f033_l1_desde_el_almacen.py:214: AssertionError: assert [('asegurar_c...cation/pdf'})] == []
E   AssertionError: assert 2 == 0
     +  where 2 = RepositorioQueCuenta(archivos=[TrazaArchivo(hash_parte='9f2b0011aabb', estado=<EstadoArchivo.PENDIENTE: 'pendiente'>, ...ta/centinela-f033', motivo=None, archivado_at_utc=datetime.datetime(2026, 9, 1, 9, 30, tzinfo=datetime.timezone.utc)))).llamadas_guardar_archivo
tests\test_f033_l1_desde_el_almacen.py:231: AssertionError: assert 2 == 0
E   AssertionError: assert 'repositorio.guardar_archivo(pendiente)' not in ['repositorio.guardar_archivo(pendiente)', 'archivador.asegurar_carpeta', 'archivador.buscar', 'archivador.subir', 'repositorio.guardar_archivo(archivado)']
tests\test_f033_l1_desde_el_almacen.py:256: AssertionError: assert 'repositorio.guardar_archivo(pendiente)' not in ['repositorio.guardar_archivo(pendiente)', 'archivador.asegurar_carpeta', 'archivador.buscar', 'archivador.subir', 'repositorio.guardar_archivo(archivado)']
E   TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
tests\test_f033_l1_desde_el_almacen.py:164: TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
E   TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
tests\test_f033_l1_desde_el_almacen.py:164: TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
E   TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
tests\test_f033_l1_desde_el_almacen.py:164: TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
E   TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
tests\test_f033_l1_desde_el_almacen.py:164: TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
E   TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
tests\test_f033_l1_desde_el_almacen.py:164: TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
E   TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
tests\test_f033_l1_desde_el_almacen.py:164: TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
E   TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
tests\test_f033_l1_desde_el_almacen.py:164: TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
E   TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
tests\test_f033_l1_desde_el_almacen.py:164: TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
E   TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
tests\test_f033_l1_desde_el_almacen.py:164: TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
E   TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
tests\test_f033_l1_desde_el_almacen.py:164: TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
E   AttributeError: module 'application.pipelines.paso_archivo' has no attribute 'AVISO_ARCHIVADO_EN_OTRO_DESTINO'
tests\test_f033_l1_desde_el_almacen.py:389: AttributeError: module 'application.pipelines.paso_archivo' has no attribute 'AVISO_ARCHIVADO_EN_OTRO_DESTINO'
E   TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
tests\test_f033_l1_desde_el_almacen.py:164: TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
E   TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
tests\test_f033_l1_desde_el_almacen.py:164: TypeError: paso_archivo() got an unexpected keyword argument 'drive_id_vigente'
E   TypeError: RepositorioFalso.__init__() got an unexpected keyword argument 'resultados'
tests\test_f033_l1_desde_el_almacen.py:112: TypeError: RepositorioFalso.__init__() got an unexpected keyword argument 'resultados'
E   TypeError: RepositorioFalso.__init__() got an unexpected keyword argument 'resultados'
tests\test_f033_l1_desde_el_almacen.py:112: TypeError: RepositorioFalso.__init__() got an unexpected keyword argument 'resultados'
E   TypeError: RepositorioFalso.__init__() got an unexpected keyword argument 'resultados'
tests\test_f033_l1_desde_el_almacen.py:112: TypeError: RepositorioFalso.__init__() got an unexpected keyword argument 'resultados'
E   TypeError: RepositorioFalso.__init__() got an unexpected keyword argument 'resultados'
tests\test_f033_l1_desde_el_almacen.py:112: TypeError: RepositorioFalso.__init__() got an unexpected keyword argument 'resultados'
E   TypeError: RepositorioFalso.__init__() got an unexpected keyword argument 'resultados'
tests\test_f033_l1_desde_el_almacen.py:112: TypeError: RepositorioFalso.__init__() got an unexpected keyword argument 'resultados'
E   TypeError: RepositorioFalso.__init__() got an unexpected keyword argument 'resultados'
tests\test_f033_l1_desde_el_almacen.py:112: TypeError: RepositorioFalso.__init__() got an unexpected keyword argument 'resultados'
E   TypeError: RepositorioFalso.__init__() got an unexpected keyword argument 'resultados'
tests\test_f033_l1_desde_el_almacen.py:112: TypeError: RepositorioFalso.__init__() got an unexpected keyword argument 'resultados'
E   AttributeError: module 'application.pipelines.paso_archivo' has no attribute 'AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA'
tests\test_f033_l1_desde_el_almacen.py:175: AttributeError: module 'application.pipelines.paso_archivo' has no attribute 'AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA'
E   AttributeError: module 'application.pipelines.paso_archivo' has no attribute 'AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA'
tests\test_f033_l1_desde_el_almacen.py:175: AttributeError: module 'application.pipelines.paso_archivo' has no attribute 'AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA'
E   AssertionError: assert 'Postventa/0678' in ''
     +  where '' = <_pytest.logging.LogCaptureFixture object at 0x00000201785FA5D0>.text
tests\test_f033_l1_desde_el_almacen.py:614: AssertionError: assert 'Postventa/0678' in ''
E   AttributeError: module 'application.pipelines.paso_archivo' has no attribute 'AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA'
tests\test_f033_l1_desde_el_almacen.py:175: AttributeError: module 'application.pipelines.paso_archivo' has no attribute 'AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA'
E   AssertionError: assert {'ahora', 'ar...traza_previa'} == {'ahora', 'ar...'repositorio'}
      
      Extra items in the left set:
      'traza_previa'
      Extra items in the right set:
      'drive_id_vigente'
      Use -v to get more diff
tests\test_f033_l1_desde_el_almacen.py:677: AssertionError: assert {'ahora', 'ar...traza_previa'} == {'ahora', 'ar...'repositorio'}
E   AssertionError: assert {'hash_parte'...chivado', ...} == {'hash_parte'...chivado', ...}
      
      Omitting 4 identical items, use -vv to show
      Differing items:
      {'web_url': 'https://ejemplo.invalido/postventa/Postventa/0677/0677%20-%20RS26.08%20-%200123%20PARTE%20FIRMADO.pdf'} != {'web_url': 'https://ejemplo.invalido/postventa/guardada-f033'}
      {'avisos': []} != {'avisos': ['este parte ya estaba archivado: se devuelve el destino que ya tenía y no se ha vuelto a subir']}
      Use -v to get more diff
tests\test_f033_archivar_http.py:234: AssertionError: assert {'hash_parte'...chivado', ...} == {'hash_parte'...chivado', ...}
E   AssertionError: assert [('asegurar_c...cation/pdf'})] == []
      
      Left contains 3 more items, first extra item: ('asegurar_carpeta', {'carpeta': 'Postventa/0677'})
      Use -v to get more diff
tests\test_f033_archivar_http.py:266: AssertionError: assert [('asegurar_c...cation/pdf'})] == []
E   AssertionError: assert [] == ['este parte ...elto a subir']
      
      Right contains one more item: 'este parte ya estaba archivado: se devuelve el destino que ya tenía y no se ha vuelto a subir'
      Use -v to get more diff
tests\test_f033_archivar_http.py:284: AssertionError: assert [] == ['este parte ...elto a subir']
E   AssertionError: assert [] == ['este parte ...elto a subir']
      
      Right contains one more item: 'este parte ya estaba archivado: se devuelve el destino que ya tenía y no se ha vuelto a subir'
      Use -v to get more diff
tests\test_f033_archivar_http.py:294: AssertionError: assert [] == ['este parte ...elto a subir']
E   assert 2 == 1
     +  where 2 = <tests.utiles_sharepoint.BibliotecaFalsa object at 0x00000201795E9F10>.subidas
tests\test_f033_archivar_http.py:318: assert 2 == 1
E   AssertionError: assert [('asegurar_c...cation/pdf'})] == []
      
      Left contains 3 more items, first extra item: ('asegurar_carpeta', {'carpeta': 'Postventa/0626'})
      Use -v to get more diff
tests\test_f033_archivar_http.py:352: AssertionError: assert [('asegurar_c...cation/pdf'})] == []
E   AssertionError: assert [('asegurar_c...cation/pdf'})] == []
      
      Left contains 3 more items, first extra item: ('asegurar_carpeta', {'carpeta': 'Postventa/0677'})
      Use -v to get more diff
tests\test_f033_archivar_http.py:383: AssertionError: assert [('asegurar_c...cation/pdf'})] == []
E   AssertionError: assert [('asegurar_c...cation/pdf'})] == []
      
      Left contains 3 more items, first extra item: ('asegurar_carpeta', {'carpeta': 'Postventa/0677'})
      Use -v to get more diff
tests\test_f033_archivar_http.py:406: AssertionError: assert [('asegurar_c...cation/pdf'})] == []
E   AssertionError: assert [('asegurar_c...cation/pdf'})] == []
      
      Left contains 3 more items, first extra item: ('asegurar_carpeta', {'carpeta': 'Postventa/0677'})
      Use -v to get more diff
tests\test_f033_archivar_http.py:406: AssertionError: assert [('asegurar_c...cation/pdf'})] == []
=========================== short test summary info ===========================
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r7_el_paso_ya_no_acepta_la_traza_por_parametro
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r7_pasarle_una_traza_es_un_error_de_tipo
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r7_drive_id_vigente_es_opcional_y_por_palabra_clave
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r7_la_traza_archivada_de_la_situacion_corta
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r8_el_corte_cuesta_una_consulta_y_ninguna_escritura
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r9_l1_va_antes_que_la_traza_previa
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r10_devuelve_la_traza_guardada_tal_cual
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r13_r14_corta_siempre_y_avisa_si_es_otro_destino[igual_en_todo]
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r13_r14_corta_siempre_y_avisa_si_es_otro_destino[otro_nombre_f032]
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r13_r14_corta_siempre_y_avisa_si_es_otro_destino[otra_carpeta]
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r13_r14_corta_siempre_y_avisa_si_es_otro_destino[otra_biblioteca_f013]
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r13_r14_corta_siempre_y_avisa_si_es_otro_destino[sin_drive_vigente]
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r13_r14_corta_siempre_y_avisa_si_es_otro_destino[traza_sin_drive]
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r13_r14_corta_siempre_y_avisa_si_es_otro_destino[ninguno_de_los_dos_drive]
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r13_r14_corta_siempre_y_avisa_si_es_otro_destino[traza_sin_nombre]
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r13_r14_corta_siempre_y_avisa_si_es_otro_destino[traza_sin_carpeta]
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r14_el_aviso_dice_que_sigue_alli_y_que_no_se_subio
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r15_el_drive_id_no_sale_en_ningun_log_ni_aviso
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r16_lo_archivado_en_otro_destino_se_queda_donde_esta
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r18_sin_cambios_en_la_previa_relee_y_no_sube
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r18_la_relectura_responde_como_l1_tambien_en_otro_destino
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r18_si_la_relectura_no_trae_archivado_no_se_sube_nada
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r18_sin_carrera_no_hay_relectura[creado]
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r18_sin_carrera_no_hay_relectura[actualizado]
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r19_sin_cambios_en_la_final_se_registra_y_responde
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r19_sin_cambios_en_la_de_error_deja_salir_el_fallo
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r20_pendiente_en_otra_ruta_sigue_con_aviso_y_log[otra_carpeta]
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r20_pendiente_en_otra_ruta_sigue_con_aviso_y_log[otro_nombre]
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r20_el_aviso_va_antes_de_escribir_la_traza_previa
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r20_el_aviso_no_lleva_identificadores_de_biblioteca
FAILED tests/test_f033_l1_desde_el_almacen.py::test_f033_r21_la_firma_no_ofrece_ninguna_forma_de_forzar
FAILED tests/test_f033_archivar_http.py::test_f033_r12_un_parte_archivado_responde_200_con_la_traza_guardada
FAILED tests/test_f033_archivar_http.py::test_f033_r21_un_campo_forzar_en_el_cuerpo_no_abre_nada
FAILED tests/test_f033_archivar_http.py::test_f033_r15_sin_biblioteca_configurada_solo_se_comparan_carpeta_y_nombre
FAILED tests/test_f033_archivar_http.py::test_f033_r15_con_la_misma_biblioteca_no_hay_aviso_de_otro_destino
FAILED tests/test_f033_archivar_http.py::test_f033_circuito_archivar_dos_veces_sube_una
FAILED tests/test_f033_archivar_http.py::test_f033_circuito_f032_el_nombre_viejo_se_queda_y_se_avisa
FAILED tests/test_f033_archivar_http.py::test_f033_circuito_f013_otra_biblioteca_no_se_sube_y_no_se_dice_cual
FAILED tests/test_f033_archivar_http.py::test_f033_circuito_la_traza_vuelve_por_columnas_y_corta[drive-inventado-posventa]
FAILED tests/test_f033_archivar_http.py::test_f033_circuito_la_traza_vuelve_por_columnas_y_corta[None]
40 failed, 14 passed in 3.32s
```

Y en verde, ya con T6–T8:

```
.venv/Scripts/python.exe -m pytest tests/test_f033_archivar_http.py tests/test_f033_l1_desde_el_almacen.py -q -p no:cacheprovider
......................................................                   [100%]
54 passed in 1.47s
```

### Tareas del bloque 2 (commits)

| Tarea | Commit | Qué |
|---|---|---|
| T5 | `b98ac7d` | RED: `tests/test_f033_l1_desde_el_almacen.py` (44 casos) y `tests/test_f033_archivar_http.py` (10 casos) |
| T6 | `dec048e` | `RepositorioFalso.resultados` (R18); los atajos de F-006 y F-019 siembran `traza_previa` en la situación **y** la siguen pasando (dos caminos durante la tarea) |
| T7 | `6f98f9b` | `paso_archivo.py`: fuera `traza_previa`, dentro `drive_id_vigente`; L1 desde `situacion_leida(...).archivo`; `_en_otro_destino`; los dos avisos; R18, R19, R20. Se quita el camino viejo de los atajos |
| T8 | `88eee31` | `archivar.py` pasa `drive_id_vigente=ajustes.sharepoint_drive_id` (R15) |

### Qué cambió (ficheros tocados)

Producción (`services/postventa-api/`):

- `application/pipelines/paso_archivo.py`
  - Firma: `traza_previa` desaparece; entra `drive_id_vigente: str | None = None`,
    por palabra clave (R7, R15, R21). No hay ningún parámetro de «forzar».
  - L1 lee `situacion_leida(ctx, repositorio).archivo`: la situación que ya
    dejó la puerta en `ctx.situacion`, **sin consulta propia** (R7, R8). El
    orden sigue siendo puerta → nombrado → L1 → previa → carpeta → homónimo →
    subida → final (R9).
  - `_devolver_la_guardada`: devuelve **la** traza guardada (`is`) con
    `AVISO_YA_ARCHIVADO` y, si `_en_otro_destino`, también
    `AVISO_ARCHIVADO_EN_OTRO_DESTINO` (R10, R13, R14).
  - `_en_otro_destino`: la función de `design.md` §4.3 tal cual (nombre,
    carpeta, y biblioteca solo si se conocen las dos).
  - `_avisar_del_intento_anterior`: traza `pendiente` de este `hash` con otra
    carpeta u otro nombre → `AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA` + `log.warning`
    con `hash`, carpeta y nombre, **antes** de la traza previa (R20).
  - `_dejar_constancia_previa` devuelve el `ResultadoGuardado`; si es
    `SIN_CAMBIOS`, `_tomar_la_de_la_otra_peticion` relee **una vez** con
    `repositorio.consultar_situacion` (no con `situacion_leida`, que daría la
    de antes de la carrera), actualiza `ctx.situacion` y responde como L1; si
    la relectura no trae `archivado`, `PersistenciaNoDisponible` sin subir (R18).
  - `_registrar_si_no_se_aplico`: `SIN_CAMBIOS` en la traza final o en la de
    error → `log.warning` con `hash`, estado y resultado; no es fallo (R19).
  - Docstrings: la tabla de las tres capas dice ya de dónde sale L1; enmienda
    fechada del 2026-09-18 en el módulo; la de la función, con los pasos 3, 4
    y 8 ampliados y el porqué de `drive_id_vigente`.
- `interface_adapters/api/archivar.py`: una línea de código
  (`drive_id_vigente=ajustes.sharepoint_drive_id`) y un apartado de docstring
  que dice que L1 sale de la situación que lee la puerta (R15). Nada más.

Tests:

- Nuevos: `tests/test_f033_l1_desde_el_almacen.py`, `tests/test_f033_archivar_http.py`.
- `tests/utiles_sharepoint.py::RepositorioFalso`: campo `resultados:
  dict[int, ResultadoGuardado]`; por omisión `CREADO`, como antes. Una
  llamada que vuelve `SIN_CAMBIOS` **no** se añade a `archivos` (ver
  «Decisiones»).
- `tests/test_f006_paso_archivo.py::archivar` y
  `tests/test_f019_orden_archivado.py::_archivar`: si reciben `traza_previa=`,
  la **siembran** en `repositorio.situacion.archivo` y ya no la pasan al paso.
  `git diff dev` de los dos ficheros: **+7 líneas cada uno, 0 borradas** (el
  atajo y un import). Ni un cuerpo de test ni un aserto tocados.

Ni una línea en `infrastructure/persistencia/sql/` (sin DDL), ni en
`paso_grafico.py`, `paso_cierre.py`, `adjuntar.py`, `cerrar.py`,
`nombrado.py`, `infrastructure/sharepoint/**`, `puerta_de_estado.py`, el
front, `azure-apps/` ni `harness/features.json`.

### Decisiones de diseño (bloque 2)

1. **R8 se mide contando consultas de situación**, con una subclase de
   `RepositorioFalso` en el propio fichero de tests (`RepositorioQueCuenta`),
   y en el circuito con `RepositorioComoLaBase.situaciones_consultadas ==
   [HASH, HASH]` (una por petición). Que cada consulta son **dos** sentencias
   ya lo fija R3 en el bloque 1 contra `ConexionDoble`.
2. **R18 «responde como L1» incluye R14**: si la traza que dejó la otra
   petición está en otra ruta, sale también el aviso de otro destino. Se
   reutiliza la misma función del corte (`_devolver_la_guardada`), para que
   los dos caminos no puedan divergir.
3. **El doble de la carrera vive en el fichero de tests**
   (`RepositorioEnCarrera`): `utiles_sharepoint.py` solo gana `resultados`,
   como pide `design.md` §1.2 («Nada más»). La subclase cambia la situación
   después de la primera escritura, que es lo que hace la otra petición.
4. **`RepositorioFalso` no guarda lo que devuelve `SIN_CAMBIOS`**: es la
   semántica de la base con el `WHERE` de R17, igual que ya hace
   `RepositorioComoLaBase`. Ningún test existente programa `resultados`, así
   que no cambia nada fuera de F-033.
5. **Los HTTP de F-033 construyen sus `Ajustes` con `_env_file=None`** y los
   inyectan en `interface_adapters.api.archivar.obtener_ajustes`: si no, el
   `SHAREPOINT_DRIVE_ID` del `.env` de quien ejecuta la suite decidiría si
   sale el aviso de otro destino (mismo motivo que `test_f006_fabrica.py`).
6. Los dos logs nuevos son `warning` (R19, R20): son rastro de algo que una
   persona puede querer mirar. Solo llevan `hash`, carpeta, nombre, estado y
   resultado; los tests comprueban con centinelas que no salen `drive_id`,
   `item_id` ni `web_url` (R15, R24).

### Desviaciones y puntos para el reviewer (bloque 2)

- **D-impl-4 · Corrección del caso de circuito después del RED.** Tras T8,
  `test_f033_circuito_archivar_dos_veces_sube_una` seguía en rojo, pero por
  otro motivo: la biblioteca vigente del caso era `drive-inventado-posventa`
  y la traza que deja el `ArchivoPortFalso` al subir lleva `drive-de-mentira`,
  así que la segunda petición salía —con razón— con el aviso de otro destino.
  Era el **montaje** del caso, no el código: en la vida real la biblioteca
  configurada y la de la traza recién escrita son la misma. Se fija la vigente
  a `DRIVE_FALSO` (con el porqué en la docstring, en el commit de T8). La
  expectativa **no se afloja**: siguen exigidos una subida, `avisos ==
  [AVISO_YA_ARCHIVADO]` exacto y la traza intacta. La evidencia RED no cambia:
  el aserto que cayó en T5 fue el de las subidas (`:318 assert 2 == 1`), que
  va antes que el de los avisos.
- **D-impl-5 · Un `pendiente` sin ruta (carpeta y nombre a `None`)** cuenta
  como «otra ruta» en R20 —misma regla que `design.md` §4.3 fija para R14— y
  el aviso sale como `«None/None»`. En producción no ocurre: la única que
  escribe `pendiente` es `_dejar_constancia_previa`, y siempre con carpeta y
  nombre. Sí ocurre en un test existente
  (`test_f006_r14_una_traza_que_no_es_archivado_no_corta[pendiente]`, que
  siembra un `pendiente` sin ruta y no mira los avisos). No se ha añadido un
  caso especial porque la spec no lo pide; si el reviewer prefiere que un
  `pendiente` sin ruta no avise, es una condición más en
  `_avisar_del_intento_anterior`.
- **D-impl-6 · El 503 de la relectura sin `archivado` (R18).** `design.md`
  §4.5 manda `PersistenciaNoDisponible`, y el borde la traduce a 503 con su
  texto de siempre («no se ha podido hablar con la base de datos … se puede
  reintentar»), que en este caso no es exacto: la base sí respondió. El
  motivo propio sí lo dice («no admitió el estado pendiente y, al releerla,
  no consta archivado: no se ha subido nada»). No se ha tocado
  `function_app.py` porque la spec no lo pide; es un camino que solo se abre
  con un borrado manual por medio.

### Qué se verificó, con el resultado real

- T5: los dos ficheros nuevos → `40 failed, 14 passed` (traza arriba).
- T6: `pytest tests/test_f006_paso_archivo.py tests/test_f019_orden_archivado.py tests/test_f006_archivar_http.py -q`
  → `61 passed`, con el paso todavía sin cambiar y los atajos pasando la traza
  por los dos caminos.
- T7: `pytest tests/test_f033_l1_desde_el_almacen.py -q` → `44 passed`;
  `pytest tests -q -k "f006 or f019 or f033"` → `477 passed` y 1 rojo
  esperado (el caso F-013 del endpoint, que necesita T8).
- T8: `pytest tests/test_f033_archivar_http.py tests/test_f033_l1_desde_el_almacen.py -q`
  → `54 passed` (tras D-impl-4).
- `bash harness/init.sh` → **ENTORNO LISTO** (ver «Evidencias (bloque 2)»).
- `ruff` desde la raíz sobre los ficheros tocados: sin avisos nuevos; total
  del repositorio 61, los mismos que antes (deuda previa).

### Verificaciones MANUAL pendientes

Ninguna de este bloque. **T13** (antes de desplegar, lectura de
`postventa.archivos` por estado) y **T14** (después de desplegar, re-archivo
de un parte ya archivado con la ventana abierta) siguen pendientes del
humano, fuera de la rama.

### Qué queda fuera de este bloque

- **Bloque 3** (T9–T12): precisión fechada en `docs/ARCHITECTURE.md`,
  control de alcance (T10), **campaña de mutación** (T11, sobre el diff
  completo de la feature) y `init.sh` final con números.
- Con los bloques 1 y 2, `/api/archivar` **ya no vuelve a subir** un parte
  que consta `archivado`. Aun así **no se recomienda desplegar** sin el
  bloque 3 (sin mutación no hay cierre de rigor `critico`) ni sin T13.
- Fuera de F-033, con dueña: que `adjuntar` y `cerrar` lean «consta
  archivado» del almacén es **F-034** (D-6); no se han tocado.

## Evidencias (bloque 2)

| Evidencia | Valor medido |
|---|---|
| Tests del servicio `api` (dentro de `bash harness/init.sh`) | **2985 passed, 20 skipped**, 0 fallos |
| Tests de la raíz (`init.sh`) | 62 passed |
| Tests nuevos del bloque 2 | 54 (44 en `test_f033_l1_desde_el_almacen.py`, 10 en `test_f033_archivar_http.py`), todos en verde; 40 de ellos en rojo en T5 |
| Cobertura de las líneas cambiadas | **100.0 % de 65 líneas** (65/65, umbral 80 %, nivel `critico`), línea `PUERTA COBERTURA` de `init.sh` |
| Tiempo de la suite del servicio | 116.33 s con cobertura (dentro de `init.sh`); ~91 s sin cobertura |
| Mutantes generados / supervivientes | **No medido en este bloque, por plan**: es la tarea **T11** del bloque 3, sobre el diff completo de la feature |
| `ruff` | 61 avisos en el repositorio, los mismos que antes del bloque; ninguno en los ficheros tocados |

---

## Bloque 3 · Documentación y cierre (T9–T12)

### Tareas del bloque 3 (commits)

| Tarea | Commit | Qué |
|---|---|---|
| T9 | `444a50c` | `docs/ARCHITECTURE.md`, paso 6, bajo «tres capas»: «**Precisado por F-033 el 2026-09-18**» (R25) |
| T10 | `801eb45` | `tests/test_f033_alcance_cerrado.py` (8 controles: dos mitades por frontera y las tres guardas del diff) |
| T11 | `ae698a1` | `progress/mutacion_F-033.md`: 21 mutantes, 21 muertos, **0 supervivientes** |
| T12 | último commit de la rama | `bash harness/init.sh` en verde; este informe y `progress/current.md` |

### T9 · `docs/ARCHITECTURE.md`

`git show --numstat` del commit: **`17 0 docs/ARCHITECTURE.md`**: solo se
añaden líneas; no se borra ni se cambia nada. La precisión va justo después
de la viñeta **carpeta** de las tres capas, con el formato de las demás del
documento («**Precisado por F-0xx el AAAA-MM-DD**»), y dice lo que pide R25:
L1 lee la traza del almacén **en la misma consulta** que la puerta (un
`LEFT JOIN` más, ninguna sentencia añadida); `archivado` no se pisa (y la
carrera se relee una vez); una traza `archivado` en otro destino corta igual y
avisa; el re-archivo del mismo parte no existe desde el circuito. Remite a
`specs/F-033-l1-traza-archivo/`.

### T10 · Control de alcance

**Fichero propio**, `tests/test_f033_alcance_cerrado.py`, como permite
`tasks.md` T10 («o fichero propio si crece»): son 8 controles con la
maquinaria de `git` de F-032, y dentro de `test_f033_l1_desde_el_almacen.py`
diluirían lo que ese fichero mide. Copia de F-032 las tres guardas
(`RAMA_DE_LA_FEATURE = "feature/F-033-l1-traza-archivo"`,
`_fuera_de_la_rama_de_la_feature`, `_la_rama_ya_esta_en_dev`) y el control de
los controles (el diff no está vacío y contiene `paso_archivo.py`).

| Frontera | Mitad del diff (`dev...HEAD`) | Mitad que no depende de `git` |
|---|---|---|
| `infrastructure/persistencia/sql/` | ni un fichero de `sql/` en el diff | los `.sql` son los once de F-028, lista escrita a mano |
| `services/postventa-front/` (R23) | ni un fichero del front en el diff | `archivar.CAMPOS_OBLIGATORIOS` sigue siendo los cinco de siempre (sin `forzar`, R21); las seis claves de salida ya las fija `test_f033_archivar_http.py` |
| D-6 (`paso_grafico.py`, `paso_cierre.py`, `adjuntar.py`, `cerrar.py`) y `nombrado.py` (F-031) | ninguno de los cinco en el diff | los nombres nuevos de F-033 (`drive_id_vigente`, `_en_otro_destino` y los dos avisos) aparecen en el código de producción **exactamente** en `paso_archivo.py` (y `drive_id_vigente` también en `archivar.py`), leídos con `tokenize` para no contar la prosa; y un control de que el recorrido de producción ve los cinco ficheros y ninguno de `tests/` |

**Decisión**: para D-6/F-031 la mitad sin `git` **no** congela el contenido
de esos cinco ficheros, porque F-034 y F-031 los van a cambiar legítimamente
y el test se pondría rojo en su rama sin motivo. Lo duradero es que L1 vive
en un solo sitio.

**Los controles cazan lo que dicen cazar.** No es fase RED de un requisito
(un control de ausencia pasa desde que se escribe): es la prueba de que no
son verdes vacíos. Con dos ficheros temporales **sin versionar**, borrados
justo después (`git status` limpio salvo el test nuevo):
`infrastructure/persistencia/sql/12_prueba_t10.sql` y
`application/pipelines/prueba_t10_temporal.py` con `drive_id_vigente = None`:

```
.venv/Scripts/python.exe -m pytest tests/test_f033_alcance_cerrado.py -q -p no:cacheprovider --tb=line
..F...F.                                                                 [100%]
================================== FAILURES ===================================
E   AssertionError: assert ('01_esquema....res.sql', ...) == ('01_esquema....res.sql', ...)
      
      Left contains one more item: '12_prueba_t10.sql'
      Use -v to get more diff
tests\test_f033_alcance_cerrado.py:230: AssertionError: assert ('01_esquema....res.sql', ...) == ('01_esquema....res.sql', ...)
E   AssertionError: assert {'drive_id_vi..._archivo.py'}} == {'drive_id_vi..._archivo.py'}}
      
      Omitting 3 identical items, use -vv to show
      Differing items:
      {'drive_id_vigente': {'application/pipelines/paso_archivo.py', 'application/pipelines/prueba_t10_temporal.py', 'interface_adapters/api/archivar.py'}} != {'drive_id_vigente': {'application/pipelines/paso_archivo.py', 'interface_adapters/api/archivar.py'}}
      Use -v to get more diff
tests\test_f033_alcance_cerrado.py:376: AssertionError: assert {'drive_id_vi..._archivo.py'}} == {'drive_id_vi..._archivo.py'}}
=========================== short test summary info ===========================
FAILED tests/test_f033_alcance_cerrado.py::test_f033_no_hay_ni_un_fichero_de_ddl_nuevo
FAILED tests/test_f033_alcance_cerrado.py::test_f033_lo_nuevo_de_l1_solo_vive_en_el_paso_y_su_endpoint
2 failed, 6 passed in 1.71s
```

(Solo se ha quitado el prefijo absoluto de las rutas.) Sin los temporales:
`8 passed`. Los números de línea citados son de antes de `ruff format`, que
partió una línea; el contenido es el mismo.

### T11 · Mutación

**Línea base verde comprobada antes, sin caché**: el `init.sh` de arranque
había dado verde **por caché**, así que se reejecutó la suite entera del
servicio con su `venv`:
`.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider` →
**`2993 passed, 10 skipped in 56.50s`**.

Campaña: `python -m harness.mutacion --feature F-033 --base dev`, desde la
raíz, **8 workers** (uno por worktree; el valor por defecto del arnés).
Alcance: 7 ficheros, 474 líneas de producción del diff
`11dda9d..feature/F-033-l1-traza-archivo`.

**21 mutantes generados, 21 evaluados, 21 muertos, 0 supervivientes, 0
timeouts, 253.0 s.** Informe completo en `progress/mutacion_F-033.md`. No
hay ningún superviviente que analizar. Qué se mutó: las condiciones de
`_en_otro_destino` (nombre, carpeta, biblioteca y sus `and`/`or`), las de
`_avisar_del_intento_anterior` (hash, estado `pendiente`, carpeta y nombre),
la negación de la relectura de R18, las dos constantes del corte y el
`len(fila) != esperadas` de `mapeo.py`, el `VALUES` y el `[1:]` de
`sentencias.py`, y el `filas[0]` de `repositorio_pg.py`.

Los worktrees de la campaña se limpiaron solos. El worktree
`.claude/worktrees/agent-a6e2f9bed1d46cdbc` que lista `git worktree list` ya
existía y no es de esta campaña: no se ha tocado.

### T12 · `bash harness/init.sh`

**ENTORNO LISTO**: servicio `api` **2993 passed, 20 skipped** en 91.84 s
(con cobertura y reejecutado de verdad, no por caché); raíz 62 passed; front
en verde (caché, árbol sin cambios); **PUERTA COBERTURA 100.0 % de 65 líneas
cambiadas** (65/65, umbral 80 %, `critico`); `ruff` 61 avisos, los mismos de
antes (deuda previa); el fichero nuevo, limpio en `ruff check` y
`ruff format --check`.

### Qué expone o consume el proyecto (para el líder, `azure-apps/`)

**Nada cambia.** Ningún endpoint nuevo ni cambiado (R23: misma entrada,
mismas seis claves y mismos códigos; solo dos textos posibles más dentro de
`avisos`). Ninguna variable de entorno nueva (`SHAREPOINT_DRIVE_ID` ya se
consumía; ahora también la lee el paso para comparar). Ninguna tabla ni
columna nueva (sin DDL: `postventa.archivos` ya se escribía y ahora además se
lee en la consulta de la situación). Ninguna base nueva. Coincide con
`design.md` §1.3. No se ha tocado `azure-apps/`.

### Verificaciones MANUAL pendientes (del humano, listas para copiar)

**T13 · antes de desplegar (R26).** Solo lectura, dentro del schema
`postventa`, con las credenciales del humano:

```sql
SET search_path TO postventa;

-- 1. Cuántas trazas hay en cada estado, y cuántas con biblioteca.
SELECT estado, count(*) AS trazas, count(drive_id) AS con_biblioteca
FROM postventa.archivos
GROUP BY estado
ORDER BY estado;

-- 2. Las que se quedaron en 'pendiente': posibles ficheros subidos
--    sin traza final (ArchivoSinTraza). Sin drive_id ni web_url.
SELECT hash_parte, carpeta, nombre_fichero, intentos
FROM postventa.archivos
WHERE estado = 'pendiente'
ORDER BY hash_parte;
```

Anotar el resultado en `progress/` **sin identificadores de biblioteca**. Lo
esperable: cero filas en la segunda. Si sale alguna, una persona mira esa
carpeta en SharePoint antes de desplegar.

**T14 · después de desplegar (R27).** Con autorización expresa para un parte
concreto que ya conste `archivado`, y la ventana `ARCHIVO_HABILITADO`
abierta solo para ello:

1. Anotar los tres valores de
   `SELECT estado, intentos, archivado_at_utc FROM postventa.archivos WHERE hash_parte = '<hash>';`
2. Volver a archivarlo desde el front (o `POST /api/archivar` con el mismo
   cuerpo).
3. Comprobar: la respuesta trae `AVISO_YA_ARCHIVADO` («este parte ya estaba
   archivado: se devuelve el destino que ya tenía y no se ha vuelto a
   subir»); en SharePoint el fichero conserva su fecha de modificación y no
   hay otro; y la consulta del paso 1 devuelve **los mismos tres valores**
   (`intentos` igual: no hubo ninguna escritura).
4. Cerrar la ventana.

## Evidencias (final, bloque 3)

| Evidencia | Valor medido |
|---|---|
| Tests del servicio `api` (`bash harness/init.sh`, reejecutados) | **2993 passed, 20 skipped**, 0 fallos |
| Tests del servicio `api` sin cobertura ni caché (línea base de T11) | 2993 passed, 10 skipped |
| Tests de la raíz (`init.sh`) | 62 passed |
| Tests nuevos de F-033 | **101**: 39 (`test_f033_situacion_con_archivo.py`) + 44 (`test_f033_l1_desde_el_almacen.py`) + 10 (`test_f033_archivar_http.py`) + 8 (`test_f033_alcance_cerrado.py`) |
| Cobertura de las líneas cambiadas | **100.0 % de 65 líneas** (65/65, umbral 80 %, `critico`), línea `PUERTA COBERTURA` |
| Mutantes generados / supervivientes | **21 / 0** (21 muertos, 0 timeouts, 8 workers, 253.0 s), `progress/mutacion_F-033.md` |
| Tiempo de la suite del servicio | 91.84 s con cobertura (dentro de `init.sh`); 56.50 s sin cobertura |
| `ruff` | 61 avisos en el repositorio, los mismos que antes; ninguno en ficheros de F-033 |

---

## Resumen para el reviewer

**Qué es F-033.** L1 (la capa **traza** del paso 6) deja de recibir la traza
por parámetro —el endpoint nunca se la pasaba, así que en el circuito real
no cortaba (defecto D-A1)— y la lee de la situación que ya consulta la
puerta de estado, con un tercer `LEFT JOIN` a `postventa.archivos` en la
misma sentencia. `upsert_archivo` no pisa una fila `archivado`. Traza
`archivado` en otro destino: corta y avisa. `pendiente` en otra ruta: sigue,
con aviso y log. Carrera en la traza previa: relee una vez y responde como L1.

**Commits** (rama `feature/F-033-l1-traza-archivo`, desde `dev` `11dda9d`):
T1 `29758f0` (RED) · T2 `257456d` · T3 `60e61c7` · T4 `9d0fc33` · informe
`3cfe4c6` · T5 `b98ac7d` (RED) · T6 `dec048e` · T7 `6f98f9b` · T8 `88eee31` ·
informe `7a32b13` · T9 `444a50c` · T10 `801eb45` · T11 `ae698a1` · T12 (el
último de la rama).

**Fase RED**: T1 (35 rojos de 39) y T5 (40 rojos de 54, con el defecto D-A1
cazado: `test_f033_archivar_http.py:318 assert 2 == 1`, dos subidas del
mismo parte). Trazas pegadas en los bloques 1 y 2.

**Números finales**: 2993 passed / 20 skipped; cobertura de líneas
cambiadas 100 % (65/65); mutación 21/21 muertos, 0 supervivientes.

**Todas las desviaciones (D-impl-*) de los tres bloques**:

1. **D-impl-1** (bloque 1) · Dos tests que fijaban el conjunto exacto de
   campos de `SituacionParte` (`test_f028_estado_dominio.py::test_f028_r2_…`
   y `test_f030_veredicto_persistido.py::test_f030_r2_…`) no estaban en la
   lista de `design.md` §7. Se tratan como cambio de **forma**: se añade
   `"archivo"` manteniendo la igualdad exacta, con enmienda fechada. **Es lo
   primero que hay que mirar** si se considera cambio de expectativa.
2. **D-impl-2** (bloque 1) · `test_f005_logs_sin_datos_personales.py::test_f030_r21_…`
   tenía una fila literal de diez columnas, fuera de §7: se le añaden ocho
   `None`. Asertos intactos.
3. **D-impl-3** (bloque 1) · El ayudante `_fila_de_la_consulta` de
   `test_f030_veredicto_persistido.py`, que §7 sí listaba, **no** se cambia:
   alimenta a `fila_a_validacion_y_cierre`, que sigue siendo de diez.
4. **D-impl-4** (bloque 2) · Tras el RED, el caso de circuito
   `test_f033_circuito_archivar_dos_veces_sube_una` se corrigió en su
   **montaje** (biblioteca vigente = `DRIVE_FALSO`, la que deja el doble al
   subir), sin aflojar ningún aserto.
5. **D-impl-5** (bloque 2) · Un `pendiente` sin ruta (carpeta y nombre a
   `None`) cuenta como «otra ruta» en R20 y avisa como «None/None». No ocurre
   en producción; si se prefiere que no avise, es una condición más.
6. **D-impl-6** (bloque 2) · El 503 de la relectura sin `archivado` (R18)
   lleva el texto genérico del borde («no se ha podido hablar con la base de
   datos…»), que en este caso no es exacto; el motivo propio sí es preciso.
   No se tocó `function_app.py` porque la spec no lo pide.
7. **D-impl-7** (bloque 3) · El control de alcance va en **fichero propio**
   (`test_f033_alcance_cerrado.py`), opción que `tasks.md` T10 permite. La
   mitad sin `git` de la frontera D-6/F-031 comprueba que lo nuevo de L1
   vive solo en el paso y su endpoint, y **no** congela el contenido de esos
   cinco ficheros, que F-034 y F-031 van a cambiar.
8. **Comandos de verificación** (los tres bloques) · Los de `tasks.md`
   (`python -m pytest services/postventa-api/tests/...` desde la raíz) usan
   el Python global, sin `pydantic`. Se han ejecutado con el `venv` del
   servicio desde `services/postventa-api/`, igual que `harness/init.sh`.

**Qué no se ha tocado** (medido por `test_f033_alcance_cerrado.py` y el
diff): `infrastructure/persistencia/sql/`, el front, `paso_grafico.py`,
`paso_cierre.py`, `adjuntar.py`, `cerrar.py`, `nombrado.py`,
`infrastructure/sharepoint/**`, `puerta_de_estado.py` y `azure-apps/`.
`harness/features.json` aparece en el diff de la rama solo por los commits
del líder (`1c54677`, `7f903c8`, `9bcc92d`); el implementer no lo ha tocado.

**Qué falta para cerrar**: la revisión contra `CHECKPOINTS.md`; T13
(humano, antes de desplegar) y T14 (humano, después de desplegar), listas
arriba. Fuera de F-033, con dueña: F-034 (D-6: que `adjuntar`/`cerrar` lean
«consta archivado» del almacén) y la decisión sobre las trazas `archivado`
que apuntan a IT (dato del humano del 2026-09-18, pendiente para F-013).
