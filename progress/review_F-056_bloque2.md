<!-- progress/review_F-056_bloque2.md -->
# F-056 · Review del Bloque 2 (la tabla y el repositorio)

- **Veredicto:** **APPROVED condicionado a T8.** No hay hallazgos que bloqueen. Hay uno menor (N-1) y varias
  observaciones. El bloque queda aprobado **cuando** el humano ejecute T8 y salga
  **«53 passed», con 0 skipped y 0 failed**. Si T8 sale con algún `failed` o `skipped`, este veredicto
  **no vale** y el bloque vuelve a review.
- **Fecha:** 2026-10-08 · reviewer
- **Rama:** `feature/F-056-revision-bandeja-backend`, HEAD `b5371f9`. Base de la feature `f86d639`; base del bloque
  `b88b5ef`.
- **Alcance revisado:** T4–T7 y T9 (T8 es MANUAL y está pendiente), y N-1, N-2, O-1, O-2 y O-4 de
  `progress/review_F-056_bloque1.md`. Ficheros: `15_revisiones_bandeja.sql`, `domain/ports/revision.py`,
  `sentencias_revision.py`, `repositorio_revision_pg.py`, `construir_revision` en `fabrica.py`, el `__post_init__` de
  `CandidataAlVolcado`, `test_f056_ddl.py`, `test_f056_repositorio_revision.py`, los 10 casos de O-1 en
  `test_f056_revision_dominio.py`, `tests_bbdd/tests/test_f056_bbdd_revision.py` (revisado leyéndolo, sin
  ejecutarlo), los seis tests de otras features que se ampliaron, `design.md` (N-1 y nota de O-1) y
  `tasks.md`.

## Nivel de rigor

`critico`, declarado en `harness/features.json`. Pide cuatro cosas: fase RED con la traza pegada, cobertura de lo
cambiado ≥ 80 %, mutación con **cero supervivientes** (salvo justificación aceptada por el humano) y las
`MANUAL (humano)` con su comando exacto. Además, por la regla de orden (punto 7 del protocolo), hay que bajar a mano
la puerta de R7 (`FOR UPDATE` → frescura → `INSERT`) y comprobar que la suite se pone en rojo.

## Lo que se ha ejecutado (resultados reales)

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` | **ENTORNO LISTO**, exit 0. `PUERTA COBERTURA: [OK] 100.0% de 648 líneas cambiadas cubiertas (648/648, umbral 80%, nivel critico)`. Los servicios api y front salieron en verde **por caché** (árbol sin cambios desde el último verde). ruff: 73 avisos de deuda previa |
| Sin caché (`-p no:cacheprovider`), desde `services/postventa-api`: los cuatro `test_f056_*`, `test_f006_repo_sin_identificadores.py`, `test_f005_integracion_sin_secretos.py`, todas las guardias `test_f00*_arquitectura`, `test_f012/f013/f036_arquitectura`, los seis tests ampliados (`f005_ddl_idempotente_texto`, `f028_ddl_historico`, `f030_veredicto_persistido`, `f031…f034_alcance_cerrado`), `test_f036_ddl.py`, `test_f036_alcance_cerrado.py` y `test_f036_repositorio_bandeja.py` | **1156 passed, 31 skipped** en 61 s. Los 31 saltados son los controles con `git` de F-030…F-036 («vive en feature/F-0xx… mientras no esté mergeada»): ya se saltaban antes y no tienen que ver con F-056 |
| `pytest --collect-only tests_bbdd` | **53** recogidos, 28 de ellos de `test_f056_bbdd_revision.py` (4+4+2+15+28, lo que anuncia el informe para T8) |
| `ruff check` sobre los 10 ficheros de F-056 nuevos o tocados | **All checks passed** (N-2 resuelta) |
| RED reproducido: `git archive 6e30f73` en el scratchpad, `pytest test_f056_ddl.py test_f056_repositorio_revision.py` | **125 failed, 8 passed**, lo mismo que el informe. Todos los fallos son `AssertionError` o `Failed: DID NOT RAISE …`; ningún `ImportError` ni `AttributeError` (O-2 resuelta) |
| Cobertura de los módulos nuevos (`coverage run --include` en la copia, con `test_f056_repositorio_revision.py`) | puerto 14/14, repositorio 57/57, sentencias 86/86: **157/157, 100 %**. Coincide con el informe |
| Recálculo puro: `harness.alcance.alcance_de_feature('F-056', base='b88b5ef')` + `harness.mutacion.generar_mutantes` | 5 ficheros, **677 líneas**, **17 mutantes**: `revision.py` 5, `repositorio_revision_pg.py` 5, `sentencias_revision.py` 7, puerto y fábrica 0. Por operador: comparación 3, lógico 2, `not` 2, entero 4, aritmético 4, booleano 2. **Coincide** con el informe |
| Campaña de mutación | **No se ha reejecutado.** El informe declara 1718 s (28,6 min), más de 5 minutos, y el encargo pide no relanzarla. Me he quedado en el recálculo puro y en 20 mutantes a mano (abajo). Coste por mutante: 1718 × 8 / 17 ≈ **808 s**. Es más que la suite en serie (510 s), lo esperable con 8 workers compitiendo: nada sospechoso |
| `git status` al terminar | limpio. Todo se hizo en copias del scratchpad |

### Mutantes a mano (copia del scratchpad, `pytest -x` sobre los cuatro `test_f056_*`)

La herramienta solo genera 17 mutantes para 677 líneas. No muta los literales SQL, ni `is None`, ni `not in`, ni el
orden de las llamadas, y ahí es justo donde está el riesgo de este bloque. Por eso apliqué a mano estos 20.
**Murieron los 20**, y en todos los casos el primer test que cae es de F-056:

| # | Mutación | Lo caza |
|---|---|---|
| M1 | **Orden**: la frescura (`max(revision_id)`) antes del `FOR UPDATE` | `test_f056_r4_r7_registrar_bloquea_comprueba_inserta_y_confirma` |
| M2 | **Orden**: el `INSERT` antes de comprobar la frescura | `test_f056_r7_r22_si_no_cuadra_no_escribe_y_deshace[otra-guardo-la-primera]` |
| M3 | `select_bloquear` sin `FOR UPDATE` | `test_f056_r7_el_bloqueo_es_for_update_de_la_bandeja_en_orden_fijo` |
| M4 | `_en_orden` sin ordenar (solo quita repetidas) | ídem |
| M5 | Frescura solo de la propia, no de la original | `…si_no_cuadra…[la-original-gano-una]` |
| M6 | Sin exigir la propia en `esperadas` | `test_f056_r7_registrar_exige_la_frescura_de_la_propia` |
| M7 | `_con_zona` admite una hora sin zona | `test_f056_o4_no_se_escribe_una_hora_sin_zona` |
| M8 | `_con_zona` sin `astimezone(UTC)` | `test_f056_o4_las_fechas_vuelven_con_zona_y_en_utc` |
| M9 | Revisión ausente con `any` en vez de `all` | `test_f056_r22_una_fila_con_su_ultima_y_su_original_con_la_suya` |
| M10 | `aprobadas` sin filtrar por `u.accion` | `test_f056_r34_aprobadas_solo_con_la_ultima_aprobar` |
| M11 | La última por `revisado_at_utc` y no por `revision_id` | `test_f056_r22_r38_cada_situacion_trae_su_ultima…` |
| M12 | `oid` y correo cruzados en el `INSERT` | `test_f056_r4_el_insert_es_una_fila_con_la_foto_el_oid_y_el_correo` |
| M13 | El correo en el log de `registrar` | `test_f056_r41_el_log_de_registrar_no_lleva_ni_oid_ni_correo_ni_textos` |
| M14 | O-1 con `rstrip` (solo recorta por la derecha) | `test_f056_r35_candidata_con_ubicacion_sin_recortar_o_larga[ Baño]` |
| M15 | `listar` sin `LIMIT` | `test_f056_r24_listar_pide_tope_mas_uno_filas_de_la_obra` |
| M16 | `NULLS FIRST` | `test_f056_r25_listar_en_el_orden_total_de_r25` |
| M17 | El `FOR UPDATE` sobre `revisiones_bandeja` en vez de la bandeja (sin revisiones no bloquearía nada) | `test_f056_r7_el_bloqueo_es_for_update…` |
| M18 | La original se construye siempre | `test_f056_r1_una_fila_sin_revisiones_ni_original` |
| M19 | El historial sin `ORDER BY revision_id` | `test_f056_r33_el_historial_de_la_mas_antigua_a_la_mas_reciente` |
| M20 | O-1 deja pasar 49 caracteres | `test_f056_r35_candidata_con_ubicacion_sin_recortar_o_larga[x×49]` |

M1 y M2 son la prueba de orden del punto 7 del protocolo para R7. El colaborador es el cursor, y el doble
(`ConexionDoble`) anota cada sentencia, así que los tests de la propia feature ven el orden.

## Lo que pedía la review del Bloque 1

| Punto | Estado | Comprobación |
|---|---|---|
| **N-1** (el design no recogía los ajustes aceptados) | Resuelto | `design.md` §3.5 lleva el recuadro «Aceptado por el líder el 2026-10-07» (el oficio ambiguo **cuenta como oficio**: da solo `oficio_ambiguo`) y la firma de §4 ya no trae `listas`. Las interpretaciones 3, 4 y 8 están en §3.5, §3.6 y §8, marcadas como del implementer. La duda que plantea el implementer (decisión 1) tiene respuesta: lo que ha escrito es lo que pedía la N-1 y lo que fijan los tests y T19. La frase del encargo («cuenta como `sin_oficio`») estaba invertida |
| **N-2** (I001 en `test_f056_paginacion.py`) | Resuelto | `916fa49`; ruff limpio en los ficheros de F-056 |
| **O-1** (forma de la ubicación en `CandidataAlVolcado`) | Hecho | Exige que la ubicación venga recortada, no vacía y con ≤ 48 caracteres. Hay RED pegado (7 fallos y 3 controles positivos), M14 y M20 mueren y la nota está en `design.md` §10. No añadir el `CHECK` en el DDL está bien razonado. **Pero deja la incoherencia que describe la N-1 de esta review** |
| **O-2** (RED con fallos de aserción) | Hecho | Esqueletos neutros. Lo he reproducido: 125/8, todo aserciones |
| **O-4** (fechas con zona) | Hecho | `_con_zona` al leer y al escribir. Tres tests unitarios: vuelven en UTC, una sin zona no se adivina y una sin zona no se escribe. En `tests_bbdd` hay además `creada_at_utc.tzinfo is UTC`. M7 y M8 mueren. Las dos columnas son `timestamptz` (`13_…` l.58 y `15_…`) |

## Lo que pedía comprobar el encargo

- **DDL solo en `postventa`, idempotente y sin nada a nivel de servidor.** Son dos sentencias, `CREATE TABLE IF NOT
  EXISTS` y `CREATE INDEX IF NOT EXISTS`, las dos cualificadas. La guarda real (`ddl.validar`, `cargar_ddl`) las
  acepta. Con otro esquema configurado se sustituye todo, también el `REFERENCES`. No aparece ninguno de
  `ddl.VERBOS_PROHIBIDOS`, ni `public.`, ni `CASCADE`. En `tests_bbdd`, el DDL se aplica dos veces con la misma
  definición y no deja nada en `public`. ✔
- **Append-only.** No hay `UPDATE`, `DELETE` ni `TRUNCATE` en el SQL generado (`test_f056_r17_r37…`) ni en el
  código de los dos módulos fuera de los docstrings (`test_f056_r37_el_codigo…`, con su control negativo). Tampoco en
  `infrastructure/` ni en `application/`: lo he buscado con grep, y el único `update_` que sale es el de F-036 sobre
  `importaciones`. El único `DELETE` de F-056 está en la limpieza de `tests_bbdd`, contra la base efímera. ✔
- **`FOR UPDATE` en orden fijo, nunca bloqueos consultivos.** `ORDER BY incidencia_id FOR UPDATE` sobre la bandeja,
  con el parámetro ordenado y sin repetidas. `ADVISORY` está prohibido en el SQL y en el código. ✔
- **Concurrencia optimista con `revision_previa`.** Bloqueo, luego `max(revision_id)` contra **todas** las
  esperadas, luego `INSERT … RETURNING`, todo en una transacción. Si algo no cuadra, `RevisionDesactualizada` y
  `ROLLBACK`. La conexión trabaja en `READ COMMITTED`, el nivel por defecto (nada lo cambia en `conexion.py` ni en
  `fabrica.py`). Así, B, al conseguir el bloqueo, ve la revisión que A ha confirmado. El test de dos conexiones de
  T7 lo demuestra: sin `FOR UPDATE`, B guardaría y acabaría habiendo dos filas. ✔ (pendiente de T8)
- **El correo nunca en logs y el `oid` nunca en respuestas.** `Revision` no lleva `oid`, y ninguna lectura
  selecciona `revisado_por` (lo cubren 7 parametrizaciones). El único log del repositorio lleva la incidencia, la
  acción y la `revision_id`, y M13 muere. Los mensajes de `PersistenciaNoDisponible` llevan la operación y el tipo de
  error, nunca los parámetros. ✔
- **`timestamptz` con zona (O-4).** ✔ (arriba)
- **O-1 en `CandidataAlVolcado`.** ✔, con la N-1.
- **RED con fallos de aserción (O-2).** ✔, reproducido.
- **`tests_bbdd` no puede tocar el servidor compartido.** Cada conexión pasa por `dsn_de_pruebas()`, que hace
  `pytest.exit` si el host no es local. `_otra_conexion` también, y el script levanta la base en
  `127.0.0.1:55432`. Sin `POSTVENTA_PG_TEST_DSN`, todo se salta. Los 28 casos cubren lo que pide T7, uno a uno: el
  DDL dos veces y nada en `public`; append-only con la última por `revision_id` aunque la hora sea anterior; la
  clave ajena; los `CHECK` (descripción de 129, motivo fuera de `descartar`, oficio ambiguo con código, correo de
  255, y otros doce); las dos conexiones; la duplicada cuya original cambia; `aprobadas`; las 10.001 filas. ✔

## Checkpoints (lo que aplica a un bloque intermedio)

**C1**
- [x] `init.sh` termina con exit 0.
- [x] Existen los ficheros del arnés.

**C2**
- [x] Una sola feature `in_progress` (F-056).
- [x] La rama es la de la feature.
- N/A `progress/current.md` solo con la sesión activa: es una exigencia de cierre, y este es un bloque intermedio.
  Sigue arrastrando el histórico de F-053: es la O-6 del Bloque 1, que limpia el líder al cerrar.
- N/A Resumen en `history.md`: F-056 no está `done`.

**C3**
- [x] Arquitectura hexagonal: el puerto en `domain/ports/` solo importa del dominio, y el SQL y el adaptador están
  en `infrastructure/persistencia/`. Las guardias de arquitectura pasan sin caché.
- [x] Primera línea con la ruta en todos los ficheros nuevos (`.py` y `.sql`).
- [x] Sin `print`, sin TODOs, sin secretos (`test_f006_repo_sin_identificadores` y `test_f005_integracion_sin_secretos`
  en verde) y sin dependencias nuevas. Los datos de prueba son ficticios (`9901`/`9902`, «Ejemplo»,
  `@ejemplo.invalid`).
- N/A Unidad «parte», «nada se archiva sin validaciones», lo manuscrito, firmado ≠ conforme, reprocesar no duplica y
  `conest`: este bloque no toca partes, firmas, archivo ni estados de Sigrid. No escribe en Sigrid ni lo lee.
- [x] Ningún escaneado ni PDF en git (`git log --diff-filter=A f86d639..HEAD`: ninguno).

**C3 bis** · N/A: no toca `docs/referencia/` (el diff no tiene nada bajo `docs/`).

**C4**
- [x] Cada requisito de este bloque tiene su test y todos pasan (tabla de abajo).
- [x] Los unit tests no tocan red ni BBDD: `ConexionDoble`, y la guarda de sockets de `tests/conftest.py` sigue
  en pie. Lo que necesita base está en `tests_bbdd/`, que se salta sin DSN.
- [x] MANUAL listadas: T8 está en `tasks.md` y en `progress/impl_F-056.md` («Para el humano · T8») con su comando
  exacto, y en `progress/current.md` como pendiente. Ver O-3, sobre la forma en que aparece en `current.md`.

**C4 bis**
- [x] `rigor: critico` declarado.
- [x] Fase RED: pegada y reproducida (T4 y O-1).
- [x] Cobertura: `[OK]` 100 % (648/648). Lo he comprobado aparte en los módulos nuevos (157/157).
- [x] Mutación: existe `progress/mutacion_F-056_bloque2.md`, generado por la herramienta. Alcance y número de
  mutantes recalculados: coinciden.
- [x] Muertos: **campaña no reejecutada, 28,6 min según el informe (más de 5 min)**. Me quedo con el recálculo puro
  y con 20 mutantes a mano, todos muertos.
- [x] Duración: unos 808 s por mutante con 8 workers, del orden de la suite. Coherente.
- [x] Cero supervivientes, cero timeouts y ningún equivalente a mano que justificar.
- [x] «Evidencias» con los cuatro números y los workers (8).
- [x] Ningún N/A sin motivo.

**C4 ter** · N/A: el repositorio no tiene `harness/rutas_sensibles.json`.

**C5** (de bloque)
- [x] T4–T7 y T9 marcadas, cada una con su commit `F-056 Tn:`. N-1, N-2 y O-1 van en commits `F-056:` aparte,
  como en el Bloque 1. N/A «todas las tareas `[x]`»: T8 es MANUAL y pendiente, y T10 en adelante son de otros
  bloques.
- [x] Sin ficheros temporales ni sin trackear (`git status` limpio).
- [x] `features.json`: F-056 `in_progress`, que es lo que corresponde.

## Cobertura: requisito → test (los de este bloque)

| R | Tests |
|---|---|
| R4 | `test_f056_r4_el_insert_es_una_fila_con_la_foto_el_oid_y_el_correo`, `…_r4_sin_urgencia_ni_listado_van_nulos`, `…_r4_r7_registrar_bloquea_comprueba_inserta_y_confirma`; bbdd: `…_r4_r38_append_only_y_la_ultima_por_revision_id` |
| R6 | `test_f056_r6_situacion_que_no_existe_es_none` |
| R7 | `…_r7_el_bloqueo_es_for_update_de_la_bandeja_en_orden_fijo`, `…_r7_r38_la_frescura_es_la_mayor_revision_id_de_cada_una`, `…_r7_la_primera_revision_espera_ninguna`, `…_r7_r22_si_no_cuadra_no_escribe_y_deshace` (×6), `…_r7_registrar_exige_la_frescura_de_la_propia`, `…_r7_si_la_base_falla_es_503_y_nada_a_medias` (×3); bbdd: `…_r7_dos_conexiones_con_la_misma_previa_solo_guarda_una`, `…_r7_dos_acciones_seguidas_con_la_misma_previa` |
| R10 | `…_r10_ninguna_lectura_selecciona_revisado_por` (×7), `…_r10_el_correo_si_se_lee` (×4), `…_r10_las_situaciones_leen_estas_columnas_en_este_orden`, `…_r10_la_revision_leida_lleva_el_correo_y_los_enum` |
| R12 | `test_f056_r12_la_unica_columna_de_correo_del_esquema_es_revisado_correo` |
| R17 | `…_r17_r37_la_unica_escritura_es_el_insert_en_revisiones`; bbdd: `…_r17_la_bandeja_no_cambia` |
| R18 | `test_f056_r18_el_motivo_solo_va_en_descartar`; bbdd: `…_r18_el_motivo_si_entra_en_descartar`, `…[motivo-en-editar]` |
| R22 | `…_r22_r38_cada_situacion_trae_su_ultima_y_la_de_su_original`, `…_r22_una_fila_con_su_ultima_y_su_original_con_la_suya`, `…_r22_la_original_sin_revisiones`, `…_r7_r22_bloquea_las_dos_en_orden_fijo_y_mira_las_dos`; bbdd: `…_r22_la_duplicada_cuya_original_cambia_entre_medias` |
| R24 | `…_r24_listar_pide_tope_mas_uno_filas_de_la_obra`, `…_r24_listar_devuelve_todo_lo_que_trae_la_base_sin_truncar`, `…_r24_contar`, `…_r24_contar_las_de_la_obra`; bbdd: `…_r24_listar_con_10001_filas_devuelve_tope_mas_uno` |
| R25 | `test_f056_r25_listar_en_el_orden_total_de_r25` |
| R30 (503 de la base) | `test_f056_r30_si_la_base_no_responde_al_leer_es_503` (×5), `test_f056_t6_si_no_se_puede_conectar_es_503` |
| R32, R33 | `…_r32_historial_de_una_que_no_existe_es_none`, `…_r33_el_historial_de_la_mas_antigua_a_la_mas_reciente`, `…_r33_historial_la_situacion_y_sus_revisiones_en_una_transaccion` |
| R34, R35 | `…_r34_el_puerto_tiene_las_seis_operaciones_de_5`, `…_r34_aprobadas_solo_con_la_ultima_aprobar`, `…_r34_r35_aprobadas_da_las_candidatas_al_volcado`, `…_r34_si_la_base_devolviera_otra_cosa_que_un_aprobar_no_pasa` (×3), `…_r35_candidata_con_ubicacion_sin_recortar_o_larga` (×10, O-1); bbdd: `…_r34_aprobadas_solo_con_la_ultima_aprobar` |
| R36 | Los 40 de `test_f056_ddl.py` (la guarda real, idempotente, cualificado, columnas, los 12 `CHECK`, `CHECK` = `Enum`, ni binarias ni JSON, la cabecera) y `…_r36_cada_sentencia_con_el_esquema_configurado`, `…_r36_un_esquema_hostil_no_llega_al_sql`; bbdd: el DDL dos veces, nada en `public`, la clave ajena, los 16 rechazos |
| R37 | `…_r37_el_codigo_no_actualiza_ni_borra_ni_hace_ddl` (×2) con su control, `…_r37_ni_datos_ni_escrituras_ni_borrados_en_el_ddl` |
| R38 | `…_r38_el_indice_da_la_ultima_revision_por_revision_id`, `…_r22_r38_…`; bbdd: `…_r4_r38_append_only_y_la_ultima_por_revision_id` (con la hora atrasada) |
| R41 (log de `registrar`) | `test_f056_r41_el_log_de_registrar_no_lleva_ni_oid_ni_correo_ni_textos` |
| O-4 | `…_o4_las_fechas_vuelven_con_zona_y_en_utc`, `…_o4_una_fecha_sin_zona_no_se_adivina` (×3), `…_o4_no_se_escribe_una_hora_sin_zona` |
| T6 (`construir_revision`) | `…_t6_construir_revision_abre_fija_la_sesion_y_asegura_el_esquema`, `…_t6_sin_contrasena_…`, `…_t6_si_no_se_puede_conectar_es_503` |

R1–R3, R5, R8, R9, R11, R13–R16, R19–R21, R23, R26–R29, R31, R39–R48 son del dominio (Bloque 1) o de los Bloques 3,
3 bis y 4.

## Hallazgos

### Bloqueantes

Ninguno.

### Menor (no bloquea; a resolver en el Bloque 3, o a decidir por el líder)

1. **N-1 · Con la O-1, la puerta de la candidata es más estricta que la de la aprobación.**
   `domain/models/revision.py` l.336–344 (`CandidataAlVolcado.__post_init__`) rechaza una ubicación sin recortar o de
   más de 48 caracteres. En cambio, `motivos_no_aprobable` (l.730) compara `v.ubicacion.strip()` contra la lista, y
   `decidir` aprueba guardando los vigentes **sin cambiarlos** (R20). El caso concreto: una vigente `" Cocina"` pasa
   `aprobar` (200) y queda guardada como `aprobar`, pero después `RepositorioRevisionPostgres.aprobadas()`
   (`repositorio_revision_pg.py` l.138, vía `candidata_de`) lanza `ValueError` para **toda la obra**. F-040 se
   quedaría sin ninguna candidata por una sola fila, y el fallo saldría al volcar, no al aprobar.
   Hoy es inalcanzable: la importación compara exacto contra la plantilla y editar guarda recortado. Por eso no
   bloquea. Pero la idea era que la última defensa avisara antes, no que tirara el lote entero.
   **Qué hacer en el Bloque 3 (T10/T11)**, y elige el líder:
   - (a) que `motivos_no_aprobable` dé `ubicacion_fuera_de_lista` cuando `v.ubicacion != v.ubicacion.strip()` o
     pase de `MAX_UBICACION`, con su test. Así el rechazo es un 409 al aprobar. Ojo: matiza R47 («exacta tras
     recortar») y habría que anotarlo en `design.md` §3.5;
   - (b) que `decidir`, al aprobar, construya la `CandidataAlVolcado` (o llame a la misma comprobación) antes de
     devolver la `RevisionNueva`, y traduzca el `ValueError` a `IncidenciaNoAprobable`.

   En los dos casos hay que añadir un test con una vigente `" Cocina"` válida tras recortar: el aprobar tiene que
   dar 409 y no 200.

### Observaciones (no son cambios requeridos)

- **O-1 · El test de append-only de `tests_bbdd` solo compara la primera fila.**
  `test_f056_bbdd_revision.py` l.299 y l.318 (`despues[:1] == antes`): la foto de `antes` se toma tras la primera
  revisión. Valdría la pena guardar también la foto tras la segunda y compararla con `despues[:2]`. Pesa poco, porque
  el código no tiene ningún `UPDATE` y eso ya lo vigilan los tests de R37, pero es lo que promete el nombre del test.
- **O-2 · `_Transaccional` se importa como nombre privado** de `repositorio_bandeja_pg.py` (decisión 6). Es correcto,
  porque §12 no deja tocar ese módulo y así no se duplica la transacción. Si algún día se toca ese módulo, conviene
  hacerlo público (por ejemplo, en `persistencia/transaccion.py`). Detalle: su `log.warning` dice «F-036 no se pudo
  deshacer» también cuando falla una operación de F-056.
- **O-3 · `progress/current.md` describe T8 como «Docker + `infra\pruebas_bbdd_efimera.ps1`»**, no con el comando
  exacto. El comando exacto (`powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`) está en
  `tasks.md` y en el informe. El líder puede copiarlo a `current.md` cuando actualice la sesión.
- **O-4 · La cabecera del informe de mutación** dice `--base b88b5ef --workers 8` y no lleva el `--timeout 1800`
  con el que se lanzó (lo dice el informe del implementer). Es cosa de `comando_de` en `harness/mutacion.py`, no de
  F-056. Ver la propuesta de automejora.
- **O-5 · Para T13 (Bloque 3).** La decisión 13 del implementer es correcta: la guardia de alcance de R37 no debe
  barrer `tests_bbdd/`, porque su limpieza es el único `DELETE` y va contra la base efímera. Hay que dejarlo escrito
  en el test de T13, como hizo F-036.
- **O-6 · R45 (decisión 5).** Además de los dos tests que nombra T4, se ampliaron seis de F-028 y F-030…F-034. He
  revisado los diffs: solo añaden `15_revisiones_bandeja.sql` a listas cerradas, sin relajar ninguna aserción. De
  F-036 solo se tocó `test_f036_ddl.py`, que T4 autoriza expresamente, y la nueva aserción es más fuerte que la
  anterior (fija toda la cola tras el 11). No se ha tocado nada de F-053.
- **O-7 · T8 es la única prueba real de dos cosas que los dobles no pueden demostrar**: la carrera de dos conexiones
  bajo `READ COMMITTED` y el `generate_series` de 10.001 filas (21 columnas con `CAST`, que he cotejado a mano contra
  `COLUMNAS_BANDEJA`). Si T8 falla en cualquiera de las dos, el bloque vuelve a review.

## Condición del veredicto

**APPROVED condicionado a T8.** Pasa a APPROVED sin condiciones cuando el humano anote en
`progress/impl_F-056.md` (sección «Para el humano · T8») la salida de
`powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1` con **«53 passed»**, **0 skipped** y
**0 failed**. Con cualquier otro resultado, review de nuevo.

## Propuestas de automejora (para el humano; no aplicadas)

1. **`reviewer.md`, punto 4 (mutación), o `CHECKPOINTS.md` C4 bis.** Cuando la herramienta genere muy pocos
   mutantes para el tamaño del alcance (aquí 17 para 677 líneas, uno por cada 40), el reviewer de nivel `critico`
   debería aplicar **a mano** mutantes sobre lo que `harness.mutacion` no ve: literales SQL dentro de `.py` (tablas,
   `FOR UPDATE`, `ORDER BY`, `LIMIT`, filtros del `WHERE`), comparaciones `is None` / `not in` y el orden de las
   llamadas. También debería anotar cuáles aplicó y qué test los mata. En este bloque, lo que de verdad protege R7
   (M1–M5, M17) y R38 (M11) no lo genera la herramienta. Propuesta de umbral: menos de 1 mutante por cada 20 líneas
   en alcance. Vale para cualquier proyecto: si se aprueba, portarla a `arnes-base`.
2. **`harness/mutacion.py`, `comando_de`.** Incluir `--timeout N` en la línea «Generado por …» cuando no sea el valor
   por defecto, para que el informe diga con qué se lanzó de verdad (O-4). También es genérica: va a `arnes-base`.
