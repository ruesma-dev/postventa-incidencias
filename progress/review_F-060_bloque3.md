<!-- progress/review_F-060_bloque3.md -->
# Review · F-060 · Bloque 3 · La normalización de una obra y su endpoint (T9–T12)

- **Veredicto:** **APPROVED** (2026-10-11, tras la aceptación escrita del humano de H11, anotada en `progress/impl_F-060.md`). Antes: **CHANGES_REQUESTED**, por **un solo** punto y **sin tocar código ni tests**: el mutante a mano
  **H11**, declarado equivalente, necesita la **aceptación escrita del humano**. Es lo que pide `CHECKPOINTS.md`
  C4 bis en nivel `critico`, y es lo mismo que se hizo con la C-3 del Bloque 1. Mi juicio es que H11 **sí es
  equivalente** (ver C-1). En todo lo demás el bloque está aprobable tal como está: el código, los tests, RM7, la
  mutación y las evidencias se han comprobado de forma independiente. Cuando la aceptación quede anotada en
  `progress/impl_F-060.md`, el veredicto pasa a APPROVED. La re-review solo tiene que comprobar esa anotación.
- **Rama:** `feature/F-060-normalizar-ubicaciones`, HEAD `5e51c7a`. Base del bloque: `91ad35d`. Base fija de la
  feature: `33d8938`.
- **Commits revisados:** `0c7d9e9` (T9), `6a4c889` (T10), `97a33ff` (T11) y `5e51c7a` (T12).
- **Fecha:** 2026-10-10 · reviewer.

## Nivel de rigor

`critico`, declarado en `harness/features.json`. Exige:

- la fase RED con la traza pegada;
- cobertura de lo cambiado;
- mutación con cero supervivientes, salvo aceptación escrita del humano, **también para los mutantes a mano
  declarados equivalentes**;
- RM7, porque los requisitos centrales del bloque son órdenes: validar antes de construir, Sigrid antes que la
  base, el tope antes de leer las ubicaciones y el ensayo antes del lote.

## Lo comprobado (resultados reales)

| Qué | Resultado |
|---|---|
| Sin caché (`-p no:cacheprovider`), desde `services/postventa-api`: todos los `test_f060_*` (dominio, lote, pipeline y HTTP), todos los `test_f056_*` (pipeline, borde, ubicaciones, alcance, repositorio, dominio, paginación, DDL y documentación), `test_f010_endpoints_protegidos.py`, `test_f006_repo_sin_identificadores.py` y los de arquitectura de F-005 y F-036 | **1264 passed, 9 skipped** en 13,0 s. Los 9 son los controles de diff de `test_f056_alcance_cerrado.py`, que solo corren en la rama de F-056 (motivo impreso por pytest) |
| Colindantes sin caché: los 44 `tests/test_*.py` que nombran `function_app`, más la documentación de F-012, F-019 y F-053 | **1848 passed, 29 skipped** en 44,4 s |
| RED reproducida con `git archive 0c7d9e9` (el commit de T9) en una copia en `%TEMP%` | **123 failed, 11 passed**, como dice el informe. Ninguna línea con `ImportError`, `AttributeError`, `TypeError`, `IndexError` ni `NameError`. Entre T9 y HEAD los tests solo cambian en **+23 líneas** de `test_f060_normalizar_http.py`: es el test de la costura que se añadió en GREEN, y está declarado |
| Cobertura, medida por el reviewer en la copia (`coverage run --branch`, solo los dos tests nuevos) | `interface_adapters/api/normalizacion.py`: **42/42 sentencias y 12/12 ramas**. En `application/pipelines/revision.py` (desde la 395) y en `function_app.py` (desde la 1759), **ninguna** línea ni rama de F-060 queda sin cubrir. Lo que sale sin cubrir es todo código de F-056. Coincide con el informe |
| Ficheros de producción del diff `91ad35d..HEAD` | Solo los tres que prevé el design: `application/pipelines/revision.py` (solo añadidos), `interface_adapters/api/normalizacion.py` (nuevo) y `function_app.py` (la ruta, su import y la cabecera). `interface_adapters/api/revision.py`, `tests/utiles_revision.py`, los `.sql`, los tests de F-036 y F-056 y `services/postventa-front/` **no aparecen** |
| `test_f010_endpoints_protegidos.py` | **Solo se amplía**: `revision/normalizar` entra en `ENDPOINTS`, la cuenta pasa de `== 20` a `== 21` y cambian el comentario y el docstring. No desaparece ninguna aserción. R39 lo permite |
| `git status` al terminar | Limpio. Las copias y los scripts de mutación estaban en `%TEMP%`, fuera del repositorio, y se han borrado |

### El código frente a §8, §9.1, §9.3 y R17–R30

- **Aplicación (§8).** Lee `listar(tope=10.000)`. Si vuelven más, hace `contar` y levanta `BandejaDemasiadoGrande`,
  sin leer las ubicaciones. Después hace **una** lectura de ubicaciones con el catálogo que recibe y llama a
  `planificar_normalizacion` del dominio. Solo hay lote con `not ensayo and plan.revisiones`. El resultado se
  calcula con lo que **devuelve el lote**, no con lo que decía el plan. `ResultadoNormalizacion` es `frozen` y solo
  lleva recuentos. Lo que ya había en el módulo no cambia.
- **Validar antes de construir (R26).** `_peticion` exige:
  - un `dict` con **exactamente** `obra`, `confirmado` y `ensayo`;
  - `confirmado is True`;
  - `ensayo` de tipo `bool`, sin valor por defecto;
  - la obra pasada por `normalizar_codigo_obra`.

  Todo eso ocurre **antes** de `obtener_ajustes` y de cualquier `construir_*`. Ningún mensaje repite lo recibido:
  los de `normalizar_codigo_obra` ya no lo repetían en F-036.
- **Sigrid antes que la base (R29).** El orden es `construir_catalogo_obra`, después `construir_fuente_de_ubicaciones`
  (la de F-056, **importada y sin sustituir**) y después `construir_revision`. Los adaptadores de Sigrid son los de
  F-036 y F-056, que solo usan `RUTA_LECTURA = "/api/sql/read"`. El diff no nombra ninguna ruta de escritura ni
  ninguna ventana (`*_HABILITADO`).
- **El ensayo no escribe (R19).** El lote no se llama: lo prueban la aplicación (`llamadas` sin `registrar_lote`,
  `lotes == []`) y el borde. Tampoco toca Sigrid: solo hay tres `sql/read`. Ver la O-4 sobre la conexión a la base.
- **Errores (R28).** La traducción es la misma que la de `GET /api/revision`, salvo `ConfiguracionPlantillaInvalida`,
  y eso es correcto: este endpoint no carga la plantilla. Un fallo del lote (por ejemplo, un `CHECK`) da 503 con «no
  se ha escrito nada», y es verdad: el `ROLLBACK` del Bloque 2 deshace el lote entero. Lo fijan
  `…_r28_…[lote-caido]` (handler y ruta) y `test_f060_r14_…` del pipeline. **O-3 del Bloque 2: cerrada.**
- **Las listas ya filtradas (O-3 del Bloque 1).** Hay un valor de Sigrid de 49 caracteres con la misma clave que
  un texto de 48 («Straße…»/«Strasse…»). No llega al plan, ni en la aplicación
  (`test_f060_o3_las_listas_salen_de_la_fuente_de_f056_ya_filtradas`) ni en el borde, donde se compone la fuente
  real de F-056 y solo se sustituye su lector (`test_f060_o3_el_endpoint_compone_la_fuente_de_f056_con_su_filtro`).
  Además hay un control de que el detector no es ciego: sin el filtro, la regla lo propondría. **O-3 del Bloque 1:
  cerrada.**
- **Sin `oid` ni correo (R27, R30).** La respuesta tiene diez claves exactas, enteros salvo `obra` y `ensayo`. Hay
  una sola línea de log, con la obra normalizada, `ensayo`, los recuentos y los segundos. Las rutas de error solo
  registran el código, o el `motivo` de disponibilidad de siempre. `SECRETOS` incluye el `oid`, el correo, el literal
  del sistema, los textos de ubicación, la descripción, el nombre de la unidad, el del proveedor y los
  `incidencia_id`. Se comprueba contra la respuesta y contra `caplog` en el éxito, en los 400 y en los nueve errores
  de R28.
- **Datos.** Todo es ficticio: obra `9901`, «Baño», «Cocina», «Terraza», «Sala Ejemplo», «Straße Ejemplo»,
  `@ejemplo.invalid` y `UUID(int=n)`. `test_f006_repo_sin_identificadores.py` está en verde.

## Mutación (C4 bis)

- **Recálculo puro** con `harness.alcance.alcance_de_feature("F-060", base="91ad35d")` y
  `harness.mutacion.generar_mutantes`:

  | Fichero | Líneas | Mutantes |
  |---|---|---|
  | `revision.py` | 82 | 5 |
  | `function_app.py` | 77 | 6 |
  | `normalizacion.py` | 149 | 6 |
  | **Total** | **308** | **17** |

  Coincide con el informe en el alcance, en el número de mutantes y en el reparto por fichero. Los operadores
  también coinciden con los que lista el informe: `frozen`, `>`, el `0` inicial de los contadores, `not` y `and`
  en `revision.py`; los seis códigos HTTP en `function_app.py`; `-`, `not`, `or`, `!=`, `is not True` y `not
  isinstance` en `normalizacion.py`.
- **Campaña no reejecutada.** El informe declara 1801,1 s (30 min), por encima de los 5 minutos, y además el líder
  pidió no relanzarla.
- **Coste por mutante:** 1801,1 × 8 ÷ 17 = **848 s**. La suite dura 883 s y el ejecutor usa `-x`, así que la cifra
  es plausible y no es sospechosa. Que el total sea 1801 s con `--timeout 1800` es una coincidencia: el timeout es
  por mutante y no hubo ninguno.
- **Muertos comprobados, no solo contados.** Apliqué los **17** mutantes de la herramienta con `aplicar_mutante`
  en una copia desechable. Contra **solo** `test_f060_pipeline_normalizacion.py`, `test_f060_normalizar_http.py` y
  `test_f010_endpoints_protegidos.py`, sin `-x`, **mueren los 17**, con entre 1 y 62 fallos cada uno.
- **Mutantes a mano del implementer:** 28 de 29 muertos. El vivo es **H11**: ver C-1. Los dos que no se ejecutaron
  están bien razonados. H4 es inalcanzable, porque el control de las claves exactas va antes. H13 no aporta nada,
  porque el cuerpo solo puede llevar la obra y dos booleanos.

### RM7 · bajar cada puerta de orden (copia desechable, solo los tests de F-060)

| Mutación | Resultado | Primer test que cae |
|---|---|---|
| R1 · `construir_catalogo_obra` por encima de `_peticion` | **ROJO** | `…_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada[lista]` |
| R2 · solo `construir_fuente_de_ubicaciones` por encima de la validación | **ROJO** | el mismo |
| R3 · solo `construir_revision` por encima de la validación | **ROJO** | el mismo |
| R4 · `obtener_ajustes()` por encima de la validación | **ROJO** | el mismo |
| O1 · la base antes que el catálogo de Sigrid | **ROJO** | `test_f060_r29_sigrid_antes_que_la_base_y_tres_lecturas[True]` |
| O2 · la base entre el catálogo y las ubicaciones | **ROJO** | el mismo |
| T1 · leer las ubicaciones antes de comprobar el tope | **ROJO** | `test_f060_r17_mas_del_tope_no_lee_ubicaciones_ni_escribe[True]` |
| T2 · sin el tope | **ROJO** | el mismo |
| T3 · en un ensayo se llama al lote (vacío) | **ROJO** | `test_f060_r17_justo_en_el_tope_si_se_normaliza` |
| E1 · el handler no pasa `ensayo` (siempre la real) | **ROJO** | `test_f060_r27_responde_la_obra_el_ensayo_y_el_recuento[True]` |
| O3 · `leer_catalogo` **antes** de `construir_revision` | verde | ninguno. **No es un hueco**: ver la O-3 |

Cada puerta cae con un test **de la propia feature**: ninguna depende de una suite vecina.

## Checkpoints (lo que aplica a un bloque intermedio)

**C1**
- N/A · `bash harness/init.sh` completo. **Justificación:** es un bloque intermedio, y el líder pidió no lanzarlo y
  ejecutar sin caché los tests de F-060, los de F-056 del pipeline y del borde, los de endpoints y `test_f006`.
  Están todos en verde (ver arriba). El informe trae `init.sh` en verde al empezar el bloque (7785 passed). La
  puerta completa se pasa en T23.
- [x] El arnés está completo (`CLAUDE.md`, `features.json`, `specs/SPECS.md`, `CHECKPOINTS.md` y `docs/`).

**C2**
- [x] Como mucho una `in_progress`, y es F-060.
- [x] La rama es `feature/F-060-normalizar-ubicaciones`.
- N/A en este bloque · `progress/current.md` solo con la sesión activa. **Justificación:** lo mantiene el líder, no
  el implementer. Sigue la deuda de la O-4 del Bloque 1: hay restos de F-056, F-051, F-049, F-013… y el apartado de
  F-060 todavía dice «Bloque 1 … pendiente de review». Se exige en la review final (ver la O-6).
- N/A · resumen en `history.md`. **Justificación:** F-060 no está `done`; se hace en T36.

**C3**
- [x] Hexagonal. La aplicación solo importa del dominio. El handler compone las fábricas de infraestructura en el
  borde, igual que `interface_adapters/api/revision.py` de F-056. `test_f005_arquitectura.py` y
  `test_f036_arquitectura.py` están en verde.
- [x] La primera línea de cada fichero nuevo o tocado es un comentario con su ruta.
- [x] Sin `print`, sin TODO, sin secretos y sin dependencias nuevas. El logging es el `logging` estándar, como el
  resto del servicio y como F-056.
- [x] **Nada contra Sigrid sin dry-run.** No hay ninguna escritura en Sigrid: solo `sql/read`. Lo que se escribe
  (en el esquema propio) tiene su `ensayo` obligatorio delante (D-8).
- N/A · reglas de partes (unidad de trabajo, manuscrito, firmado, reprocesar, estados de Sigrid y escaneados).
  **Justificación:** el bloque no toca partes, SharePoint, estados de Sigrid ni escaneados. Revisa la bandeja de
  incidencias de F-036 y F-056.

**C3 bis**
- N/A. **Justificación:** el bloque no trae ningún documento de fuera ni toca `docs/referencia/`.

**C4**
- [x] R17–R30 tienen test, y todos pasan (tabla de abajo).
- [x] Los tests unitarios no tocan red ni base: dobles en memoria y fábricas sustituidas.
- [x] Lo `MANUAL (humano)` sigue listado: T7 del Bloque 2, con su comando. Este bloque no añade ninguno.

**C4 bis**
- [x] `rigor: critico` declarado.
- [x] Fase RED: la traza está pegada y la he **reproducido** (123 failed, todos por aserción; 11 passed con su
  justificación).
- [x] Cobertura de lo cambiado: 100 %, medida por el reviewer. La línea `PUERTA COBERTURA` es de T23.
- [x] Mutación: el informe existe, con totales reales, recalculados y coincidentes.
- [x] Muertos comprobados: los 17, aplicados en la copia contra solo los tests del bloque. Campaña no reejecutada
  (30 min según el informe).
- [x] Duración plausible: 848 s por mutante con 8 workers y `-x`.
- [ ] **Cero supervivientes sin aceptación escrita del humano: NO.** La herramienta deja 0, pero el mutante a mano
  **H11** se declara equivalente y en `critico` eso necesita la aceptación **escrita** del humano, no solo el juicio
  del reviewer. → **C-1**.
- [x] RM7: las diez mutaciones de puerta dan rojo con tests de la propia feature.
- [x] «Evidencias» del bloque, con tests, cobertura, mutantes (herramienta y a mano) y workers (8). El tiempo de la
  suite completa es el de la precondición (883 s), y el informe dice que la de cierre es de T23.

**C4 ter**
- N/A. **Justificación:** no hay `harness/rutas_sensibles.json` en el repositorio.

**C5**
- [x] En `tasks.md`, T9–T12 están `[x]`, con commits `F-060 T9/T10/T11/T12: …`. T7, del Bloque 2, sigue `[ ]`
  porque es MANUAL del humano y no es de este bloque.
- [x] No hay temporales ni ficheros sin trackear.
- [x] `features.json` dice `in_progress`, que es el estado real.

## Cobertura: requisito → test

| Requisito | Tests |
|---|---|
| R17 | `test_f060_r17_mas_del_tope_no_lee_ubicaciones_ni_escribe` (×2), `…_justo_en_el_tope_si_se_normaliza`, `…_un_fallo_de_la_base_al_listar_sube_sin_leer_sigrid` |
| R18 | `test_f060_r18_una_lectura_de_ubicaciones_con_el_catalogo_recibido`, `…_mira_la_lista_de_la_fuente_y_no_otra`, `test_f060_r10_r18_el_recuento_de_la_obra_y_su_suma` (×2) |
| R19 | `test_f060_r19_el_ensayo_no_llama_al_lote_ni_escribe` (pipeline), `test_f060_r19_el_ensayo_no_escribe_nada` (HTTP) |
| R20 (y R9 y R13 vistos desde la aplicación) | `test_f060_r20_la_real_registra_el_lote_del_plan`, `test_f060_r9_r20_la_esperada_es_la_ultima_leida`, `test_f060_r13_r20_un_conflicto_se_cuenta_y_no_aborta_las_demas`, `test_f060_r20_un_plan_vacio_no_llama_al_lote`, `…_la_real_escribe_revisiones_del_sistema_con_la_hora_de_la_peticion`, `…_sin_hora_inyectada_es_la_de_ahora_en_utc` |
| R21 | `test_f060_r21_dos_ejecuciones_la_segunda_no_tiene_nada_que_normalizar` |
| R22 | `test_f060_r22_la_fila_normalizada_en_el_listado_y_su_historial`, `…_el_resumen_baja_en_las_normalizadas` |
| R23 (y R7) | `test_f060_r7_r23_lo_que_no_se_normaliza_sigue_como_estaba` |
| R24 | `test_f060_r24_normalizar_y_aprobar_da_la_candidata_con_el_texto_de_sigrid` |
| R25 | `test_f060_r25_sin_normalizar_aprobar_sigue_siendo_409`, `…_editar_con_la_variante_sigue_siendo_400` (×2) |
| R26 | `test_f060_r26_el_handler_rechaza_cada_cuerpo_malo_sin_construir_nada` (×30), `…_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada` (×30), `…_un_cuerpo_que_no_es_json_es_400_sin_construir_nada`, `…_la_obra_se_normaliza_como_en_f036` |
| R27 | `test_f060_r27_responde_la_obra_el_ensayo_y_el_recuento` (×2), `…_la_ruta_responde_200_con_solo_numeros`, `test_f060_el_resultado_no_lleva_textos` |
| R28 (y R14 en el borde) | `test_f060_r28_el_handler_deja_subir_el_error_sin_escribir` (×9), `…_la_ruta_responde_como_el_listado_sin_escribir` (×9), `…_un_fallo_de_las_ubicaciones_sube_sin_escribir` (×2), `test_f060_r14_un_fallo_de_la_base_en_el_lote_sube_sin_nada_escrito` |
| R29 | `test_f060_r29_sigrid_antes_que_la_base_y_tres_lecturas` (×2), `…_sin_sigrid_no_se_llega_a_construir_la_base` (×4), `…_los_adaptadores_inyectados_no_se_construyen` |
| R30 | `test_f060_r30_una_linea_con_la_obra_el_recuento_y_los_segundos` (×2), `…_los_segundos_son_los_de_la_peticion` |
| D-4 | `test_f060_d4_la_identidad_es_la_del_sistema_aunque_vengan_cabeceras` |
| §9.1 (la ruta) | `test_f060_s9_la_ruta_es_post_y_anonima`, y `test_f010_r32_…` con veintiuno |
| O-3 de los Bloques 1 y 2 | `test_f060_o3_las_listas_salen_de_la_fuente_de_f056_ya_filtradas`, `…_el_detector_no_es_ciego…`, `…_el_endpoint_compone_la_fuente_de_f056_con_su_filtro`, y `[lote-caido]` |

## Cambios requeridos

1. **C-1 · H11: aceptación escrita del humano (`CHECKPOINTS.md` C4 bis, nivel `critico`).** No se toca ni código
   ni tests.
   - **El mutante.** En `services/postventa-api/interface_adapters/api/normalizacion.py:94`,
     `leer_catalogo(catalogo_obra, obra)` se cambia por `leer_catalogo(catalogo_obra, cuerpo["obra"])`.
   - **Mi juicio: es equivalente.** `leer_catalogo` (`application/pipelines/catalogo_obra.py:73`) aplica ella misma
     `normalizar_codigo_obra` a lo que recibe. Esa función es idempotente: quita blancos y unifica guiones.
     Además, `cuerpo["obra"]` ya ha pasado por ella en `_peticion`, que rechaza lo que no vale. Con cualquier obra
     que llegue a esa línea, Sigrid recibe el mismo código. El resto de la petición (la bandeja, la respuesta y el
     log) usa la obra ya normalizada en los dos casos. No hay ningún comportamiento observable que los distinga,
     así que tampoco hay test que añadir.
   - **Qué falta.** El protocolo pide que la equivalencia la **acepte el humano por escrito**. Basta con anotarla
     en `progress/impl_F-060.md`, como «C-1 de la review del Bloque 3 · aceptación del humano», con fecha y con su
     respuesta literal, igual que la C-3 del Bloque 1. Con eso, el veredicto pasa a APPROVED.

## Observaciones (no bloquean este bloque)

- **O-1 · El Bloque 5 (T20) va a chocar con tests que la spec no deja tocar.** Hay que llevarlo al humano
  **antes** de encargar el Bloque 5. T20 cambia `docs/INTEGRACION.md` §8 a «Los veintiuno» y solo prevé ampliar
  `test_f053_documentacion.py`. Pero hay otros tres tests que fijan la cuenta de veinte y caerán:
  - `tests/test_f056_documentacion.py:438-447`, `test_f056_r44_la_seccion_ocho_dice_la_cuenta_y_las_ventanas`,
    exige el literal **«Los veinte quedan en nivel»**. Es un test de **F-056**, y R39 solo permite ampliar
    `test_f010`, `test_f053` y el r34 del puerto. Es el mismo tipo de choque que paró el Bloque 2.
  - `tests/test_f019_documentacion.py:185`, `test_f019_r32_la_seccion_ocho_ya_habla_de_todos_los_endpoints`, exige
    el literal **«Los veinte quedan en nivel»**.
  - `tests/test_f012_documentacion.py:171-183`: `NUMERALES` acaba en 20. Con 21 filas en la tabla de §8, el test da
    «amplía NUMERALES: hay 21».

  Recomendación: que el humano decida ya la ampliación de los tres, sin relajarlos, cada uno con la cifra nueva y
  sin quitar las viejas de sus `not in`. La decisión se escribe en `design.md` §12, en R39, en T19, en T20 y en la
  cabecera de `tasks.md`, como la del 2026-10-10. Una precisión sobre `progress/impl_F-060.md:1075-1078`: dice que
  esos tests «cuentan las filas de la tabla de §8». Es cierto que no miran `function_app.py`, y por eso hoy están
  en verde. Pero `test_f019`, `test_f053` y `test_f056` fijan además el literal de la cifra, y ese literal es el
  que T20 tiene que cambiar.
- **O-2 · Spec de F-059 (worktree `postventa-f040`, rama `feature/F-040-volcado-sigrid`, `5357586`; leída sin
  tocarla).** Dice «veintitrés» en `design.md:464`, en `design.md:637`, en `requirements.md:333` (R42), en
  `tasks.md:161` y en `tasks.md:200`. Tras F-060 son **veinticuatro** (21 + 3). Al llevarla a su rama, el líder
  tiene que ajustar esas cinco menciones y prever en F-059 lo mismo que en la O-1:
  - `test_f010` a `== 24`;
  - `NUMERALES` de `test_f012` hasta 24;
  - los literales de `test_f019`, `test_f053` y `test_f056_documentacion`, que serán entonces de F-059 y F-056.

  `design.md` §10.2 de F-060 ya le asigna este ajuste al líder.
- **O-3 · RM7: `leer_catalogo` antes de `construir_revision` no la ve ningún test, y no hace falta.** R29 y §9.1
  solo ordenan la **construcción** (Sigrid antes que la base). El momento de la lectura del catálogo no lo fija
  ningún requisito, y el código sigue el orden del listado de F-056. Si algún día se quiere ahorrar la conexión a la
  base en los 404 y 409 de la obra, se puede adelantar la lectura, pero sería una decisión nueva, no un arreglo.
- **O-4 · «El ensayo no escribe nada» quiere decir que no escribe filas.** El ensayo construye igualmente el
  repositorio. Abre una conexión y, en la primera petición del proceso, ejecuta la guarda de DDL idempotente
  (`asegurar_esquema`), exactamente igual que `GET /api/revision`. R19 se cumple: el lote no se llama y no se
  escribe ninguna revisión. Conviene que T20 lo diga así en `INTEGRACION.md` §2, para que nadie entienda «no abre
  la base».
- **O-5 · Desfase esperado entre bloques.** `docs/INTEGRACION.md:1347` dice «Los veinte» y el código tiene ya
  veintiuna rutas anónimas. Lo cierra T20 (sujeto a la O-1). `azure-apps/postventa_incidencias.md` lo cierra T29.
  La cabecera de `function_app.py` está bien: conserva «Con él los anónimos son veinte» como historia de F-056 y
  añade «Con él los anónimos son veintiuno».
- **O-6 · `progress/current.md` desactualizado.** El apartado de F-060 sigue en «Bloque 1 HECHO … pendiente de
  review» y «Bloque 2 en curso». Además arrastra restos de otras features. Es del líder. No bloquea un bloque
  intermedio, pero sí la review final (C2).

## Propuesta de automejora (para que la apruebe el humano; no aplicada)

- **`.claude/agents/spec-author.md` (o `specs/SPECS.md`), sección de alcance.** Cuando una feature añade una ruta,
  la spec debería listar **todos** los tests que fijan la cuenta de endpoints, no solo los que «enumeran rutas»:
  ```
  grep -rn "quedan en nivel\|NUMERALES\|== len(ENDPOINTS)" tests/
  ```
  Y debería pedir la excepción al humano en la PARADA 1, no a mitad de la feature. En F-060 ha pasado dos veces: el
  r34 del puerto en el Bloque 2 y estos tres en el Bloque 5. Vale para cualquier proyecto con el arnés que cuente
  sus rutas en la documentación: si se aprueba, se porta a `arnes-base`.
