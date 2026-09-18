# F-033 · Informe del implementer

> Rama `feature/F-033-l1-traza-archivo`. Rigor `critico`.
> Este informe crece por bloques: **Bloque 1 (T1–T4)** abajo.

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
