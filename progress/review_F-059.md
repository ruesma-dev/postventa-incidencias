<!-- progress/review_F-059.md -->
# F-059 · Volcado a Sigrid en el backend — Informe del reviewer

## Review del Bloque 1 (dominio) · 2026-10-16

- **Veredicto:** **CHANGES_REQUESTED** (3 hallazgos: C-B1-1, C-B1-2, C-B1-3)
- **Alcance revisado:** `git diff 3673aca..135dd6b` (T0 `477e596`, T1 `ffaf804`, T2 `c84e979`, T3 `e0e93db` y
  `135dd6b`), base fija `2d2efd7`. Spec `specs/F-059-volcado-sigrid-backend/` (aprobada el 2026-10-07,
  conciliada el 2026-10-15; F-1 (a) y F-2 (a)). Tareas T0–T3.
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED con traza pegada, cobertura
  ≥ 80 % de lo cambiado, campaña de mutación con **cero supervivientes** salvo justificación escrita aceptada por el
  humano (también los mutantes a mano), y la sección «Evidencias».

El bloque está bien hecho y los tres hallazgos son pequeños: son huecos de los tests, no defectos del código
contra la spec. Pero en `critico` un mutante a mano que sobrevive pide un test o una justificación que acepte el
humano por escrito, y el reviewer no puede aceptarla por su cuenta. Lo demás (RED, trazabilidad, tests ajenos,
convivencia con F-060, recálculo de la mutación, datos ficticios) está en orden.

### Qué he verificado yo, y cómo

Todo desde el scratchpad (sin `.env`), con `services/postventa-api/.venv/Scripts/python.exe -m pytest` y rutas
absolutas. Los mutantes y la RED, en worktrees desechables del scratchpad, ya retirados (`git worktree list` sin
ninguno y `git status` limpio al terminar).

| Verificación | Resultado |
|---|---|
| La de `tasks.md` T2 (los diez ficheros) **más** las dos guardias R26 de F-006 (`test_f006_arquitectura.py`, `test_f006_repo_sin_identificadores.py`) | **1209 passed in 24.78s** (1144 de T2 + 65 de las guardias) |
| RED reproducida en un worktree de `ffaf804` (T1), los dos ficheros de F-059 | **296 failed, 7 passed**, igual que la traza pegada; las trazas apuntan al `volcado.py` y al `situacion_volcado.py` **del worktree** (207 y 10), no al árbol de trabajo |
| Cobertura (`coverage run` con los dos ficheros de F-059) | `volcado.py` 280/280 y `situacion_volcado.py` 47/47: **100 %** |
| `ruff check` (desde la raíz, con la configuración de `init.sh`) sobre los cuatro módulos de `domain/models/` tocados y los seis tests tocados | `All checks passed!` |
| Recálculo puro del alcance (`harness.alcance.alcance_de_feature("F-059", base="477e596")`) | 4 ficheros, **1084** líneas: `errores.py` 120, `revision.py` 44, `situacion_volcado.py` 127, `volcado.py` 793. Coincide con el informe |
| Recálculo puro de los mutantes (`harness.mutacion.generar_mutantes`) | **85** (0 + 2 + 6 + 77). Coincide |
| Muestreo de mutantes de la tabla del informe | Los n.º 6, 21, 46, 66 y 80 salen idénticos (fichero, línea, operador, original → mutado) |
| Mutantes a mano míos (25), solo con los tests de F-059 | 22 muertos por F-059 y **3 supervivientes** (abajo) |
| Los 3 supervivientes, contra el conjunto entero de T2 (F-056, F-060, F-005 incluidos) | Los 3 **sobreviven**: 1144 passed. Ninguna suite vecina los ve |
| Barrido de datos sensibles en el diff y en cada commit del bloque | Ver «Datos sensibles» |

**Campaña no reejecutada: 217 min según el informe** (13042.6 s, por encima de los 5 minutos del protocolo). Me
quedo en el recálculo puro, en el muestreo y en mis propios mutantes a mano. El coste por mutante, 13042.6 × 8 ÷ 85
≈ **1227 s**, es coherente con una suite que, según el propio informe, tarda 1563 s bajo carga (con `-x` se para
antes): nada sospechoso. El control de «cero mutantes» no aplica (salen 85). Que `errores.py` dé 0 es lo esperable:
son definiciones de clase sin operadores que mutar.

### Hallazgos (cambios requeridos)

1. **C-B1-1 · `parte_de`, `services/postventa-api/domain/models/volcado.py:359`.** Si cambio
   `if v.proveedor_codigo is not None:` por `if v.proveedor_codigo:`, el mutante **sobrevive** a los 304 tests de
   F-059 y a los 1144 de T2. Ningún test fija qué pasa con un `proveedor_codigo` vacío (`""`), y
   `ValoresIncidencia` lo admite (`_comprobar_elegido`, `revision.py:208`, no mira si el texto está vacío). Hoy se
   mandaría `{"oficio": …, "proveedor": "", "causante": false}`; con el mutante, `[]`. **Qué hacer:** añadir a
   `tests/test_f059_volcado_dominio.py` un caso con `proveedor_codigo=""` que fije el comportamiento que elija el
   implementer dentro de R6 y D-9 (rechazarlo con un error de programación, o tratarlo como «sin proveedor»), y que
   ese mutante muera. Si se prefiere declararlo inalcanzable (el código sale siempre del par de `obrofc`), hay que
   escribir la justificación en `progress/impl_F-059.md` y conseguir que el humano la **acepte por escrito**
   (`critico`, CHECKPOINTS C4 bis).
2. **C-B1-2 · `cuerpo_de_parte`, `services/postventa-api/domain/models/volcado.py:397`.** Lo mismo con
   `if parte.descripcion_larga is not None:` → `if parte.descripcion_larga:`: **sobrevive** a F-059 y a T2. R6 dice
   que `descripcion_larga` va «**solo si no es nulo**»; con `detalle=""` el código actual manda
   `"descripcion_larga": ""` y el mutante no manda la clave, y no hay ningún test que distinga los dos casos.
   `validar_valores` convierte un `""` en `None` al editar (`revision.py:616`), pero `valores_importados`
   (`revision.py:448`) copia `incidencia.detalle` tal cual, así que depende de lo que normalice F-036. **Qué hacer:**
   un caso con `detalle=""` que fije el comportamiento (el que case con R6 y con lo que admite §8.9) y mate el
   mutante, o una justificación de que es inalcanzable con la aceptación escrita del humano.
3. **C-B1-3 · `posibles_duplicados`, `services/postventa-api/domain/models/volcado.py:729`.** Si cambio
   `parte.sigrid_ide != r.sigrid_ide` por `parte.sigrid_cod != r.sigrid_cod`, el mutante **sobrevive** a F-059 y a
   T2. R26 compara **por `sigrid_ide`** («otro `sigrid_ide`»), pero en todos los casos de los tests de R26 el `ide`
   y el `cod` cambian a la vez. **Qué hacer:** añadir a los tests de R26 un `creado` con el mismo `sigrid_ide` y
   otro `cod`, que no debe dar aviso, y/o uno con otro `ide` y el mismo `cod`, que sí debe darlo.

Con esos tres casos, repetir los tres mutantes (en una copia desechable) y anotar en el informe qué test de F-059 los
caza. No hace falta relanzar la campaña de la herramienta: los tres tocan líneas que ella no muta.

### Mutantes a mano del reviewer (sobre `135dd6b`, solo tests de F-059, `-x`)

Hay que repetir una muestra de los del implementer y añadir otros donde la herramienta no genera nada: `in`/`is`,
el orden de las comprobaciones, lo que se devuelve y la veracidad frente a `is not None`.

| Id | Mutación | Resultado | Primer test de F-059 que lo caza |
|---|---|---|---|
| R01 | `interpretar_respuesta`: el rango del `indice` con `len(partes)` en lugar de `len(mandados)` | muerto | `test_f059_r22_un_parte_que_no_vuelve_es_sin_respuesta_y_los_demas_valen` |
| R02 | Emparejar con el índice al revés (`len(mandados) - 1 - i`) | muerto | `test_f059_r22_creado_e_idempotente_con_su_ide_y_su_cod` |
| R03 | Ensayo: `ya_volcada` antes que `de_otra_obra` | muerto | `test_f059_r11_la_obra_se_mira_antes_que_lo_volcado` |
| R04 | Volcado: `no_es_de_la_bandeja` (la base) antes que lo del ensayo | muerto | `test_f059_r20_las_excluidas_en_el_orden_pedido` |
| R05 | Volcado: `revision_desactualizada` antes que `ya_volcada` | muerto | `test_f059_r20_ya_volcada_antes_que_la_revision` |
| R06 | `validar_ensayo` sin la comprobación de la obra | muerto | `test_f059_r17_de_otra_obra` |
| R07 | `interpretar_respuesta` sin la comprobación de `dry_run` | muerto | `test_f059_r23_dry_run_true_en_el_volcado` |
| R08 | `seleccionar_para_volcado` sin `_exigir_distintas` | muerto | `test_f059_r15_pedidas_repetidas` |
| R09 | Un elemento de `partes` que no es objeto se salta (`continue`) en vez de `None` | muerto | `test_f059_r22_r23_de_mas_o_indices_imposibles[partes0]` |
| R10 | `validar_ensayo` sin la comprobación de la persona | muerto | `test_f059_r17_de_otra_persona` |
| R11 | Un índice repetido se salta en vez de `None` | muerto | `test_f059_r22_r23_de_mas_o_indices_imposibles[indice_repetido]` |
| R12 | Volcado sin la comprobación de la huella | muerto | `test_f059_r7_r20_huella_no_coincide` |
| R13 | `parte_de` nunca pone interviniente | muerto | `test_f059_r6_el_parte_clave_a_clave` |
| **R14** | `parte_de`: `proveedor_codigo is not None` → veracidad | **sobrevive** (también a T2) | — (C-B1-1) |
| R15 | `estado_de_volcado`: `en_duda` antes que `volcada` | muerto | `test_f059_r1_volcada_gana_a_lo_que_diga_el_ultimo[enviado]` |
| R16 | `estado_de`: el volcado solo manda si hay revisiones | muerto | `test_f059_r1_volcada_gana_aunque_no_haya_revisiones` |
| R17 | `cuerpo_de_lote` admite 0 partes | muerto | `test_f059_r30_de_1_a_50_partes_por_cuerpo` |
| R18 | `cuerpo_de_lote` con `"clase": None` | muerto | `test_f059_r6_el_cuerpo_clave_a_clave` |
| R19 | `referencia_de` en mayúsculas | muerto | `test_f059_r5_la_referencia_es_pvi_y_el_uuid_canonico` |
| R20 | Posible duplicado con cualquier estado con parte (no solo `creado`) | muerto | `test_f059_r26_solo_un_creado[idempotente]` |
| **R21** | `cuerpo_de_parte`: `descripcion_larga is not None` → veracidad | **sobrevive** (también a T2) | — (C-B1-2) |
| R25 | `todos_sin_respuesta` en orden inverso | muerto | `test_f059_r23_todos_sin_respuesta` |
| **R26** | `posibles_duplicados` compara `sigrid_cod` en vez de `sigrid_ide` | **sobrevive** (también a T2) | — (C-B1-3) |
| R36 | El resumen del ensayo con `rechazados` y `no_procesados` cruzados | muerto | `test_f059_r12_el_resumen_del_ensayo` |

R03, R05, R06, R10, R15, R19, R20 y R25 repiten en sustancia los M58, M61, M12, M26, M79 y M77 del implementer, o
sus pruebas de orden; confirman su tabla. **Ninguno de los muertos lo caza solo una suite vecina**: todos caen con
los dos ficheros de F-059 solos.

**Orden (punto 7 del protocolo): N/A, justificado.** El Bloque 1 es dominio puro, sin colaboradores: no hay ninguna
puerta que vaya «antes de» hablar con la base o con Sigrid. Los órdenes centrales de F-059 (R16: puertas antes de
leer; R19: login antes de la escritura anticipada; R20: `enviado` y `COMMIT` antes de llamar; R2: la comprobación
dentro de la transacción) viven en los Bloques 2 a 4, y allí habrá que bajar cada puerta un paso.

### Tests ajenos tocados (R41, F-1 (a), grupo C de `design.md` §21.3), comparados con la base

Solo cuatro ficheros de test ajenos y la enmienda de `docs/ARCHITECTURE.md`, **todos del grupo C**. Ninguno de
F-009, F-012, F-036 ni F-053, y ninguno del grupo A ni del B (eso toca en T4/T5 y T15/T20). Línea a línea contra
`3673aca`, todo son **añadidos**:

| Fichero | Cambio | ¿Amplía sin relajar? |
|---|---|---|
| `test_f056_paginacion.py::test_f056_r23_filtros_de_estado` | + `"volcada"`, `"en_duda"` al final de la lista exacta | Sí: la igualdad exacta sigue, con seis |
| `test_f056_paginacion.py::test_f056_r27_resumen_sobre_todas_las_filas` | La igualdad de `por_estado` pasa de 4 claves a 6 (las dos nuevas a 0) | Sí: es más estricta; los cuatro recuentos de antes, iguales |
| `test_f056_pipeline_revision.py::test_f056_r27_…` | + `E.VOLCADA: 0`, `E.EN_DUDA: 0` | Sí |
| `test_f056_revision_dominio.py` | + `sit_volcada`, `sit_en_duda`; `SITUACIONES` y `PERMITIDAS` con las dos claves (`()`) | Sí: la parametrización sobre `list(EstadoRevision)` pasa de 16 a 24 casillas, y las 8 nuevas exigen 409 con `acciones: []` |
| `test_f056_revision_http.py::test_f056_r27_la_respuesta_lleva_lo_de_r27` | `por_estado` del listado con seis claves | Sí |
| `docs/ARCHITECTURE.md` (sección de F-056) | Párrafo «Enmienda de F-059 (2026-10-15): seis estados» | El test `test_f056_r44_nombra_cada_estado` **no se toca** |

Cada línea añadida lleva `F-059 (R41, F-1 (a); design.md §21.3 C)`. El mensaje de `_filtro` y
`test_f056_repositorio_revision.py` quedan, con razón, para T15 y T4/T6. El nombre
`test_f056_r2_las_dieciseis_casillas` se queda aunque ahora cubra 24 casillas: renombrarlo rompería la
trazabilidad, y me parece bien.

### Convivencia con F-060 (§21.5)

`domain/models/normalizacion.py` **no** sale en el diff. `test_f059_f060_la_normalizacion_no_toca_una_volcada_ni_una_en_duda`
y `…_ni_aunque_la_ultima_revision_no_fuera_un_aprobar` llaman a `planificar_normalizacion` tal como está: ninguna
revisión y las dos en `no_editables`, incluso con una última `editar` (defensa en profundidad).
`test_f059_f060_r9_r15_el_sistema_no_puede_ensayar_ni_volcar` comprueba que `validar_quien` rechaza el literal del
sistema. Los tests de F-060 de la verificación de T2 pasan.

### Datos sensibles

Patrones: GUID (`[0-9a-f]{8}-…-[0-9a-f]{12}`), correos, IPv4 y
`password|secret|apikey|api_key|token|connectionstring|AccountKey|Bearer`, sobre el diff entero y sobre cada commit
del bloque.

- **Correos:** solo `persona.estados@ejemplo.invalid` y `persona.volcado@ejemplo.invalid`. **IPs:** ninguna.
  **Claves:** ninguna.
- **Obras y proveedores:** `9901`/`9902`, `EJ07`/`EJ08`, «Ejemplo». Ninguna ubicación ni nombre real.
- **El GUID sintético de T1 (valoración pedida).** `ffaf804` **añade**
  la forma canónica de `UUID(int=0xABCDEF)` (dos `assert` de R5) y la de `UUID(int=1)` (el id de un
  caso parametrizado, en la traza RED), y `c84e979` los **quita**. En `HEAD` no queda ninguno (`git grep`), y las dos
  guardias R26 de F-006 pasan. Son `UUID(int=…)` escritos en hexadecimal: casi todo ceros, sin relación con ningún
  tenant, suscripción, objeto ni usuario real. **No son secretos ni identificadores reales, y no hace falta
  reescribir el historial.** Componer `CANONICO_ABCDEF` por partes es legítimo: R5 necesita un valor esperado
  independiente de `str(UUID)`, y escrito de una pieza la guardia lo rechaza. Me parece bien.

### Checkpoints

**C1 — Arnés completo y en verde**
- N/A · `bash harness/init.sh` exit 0: el líder lo deja fuera de este encargo («no hace falta `init.sh` completo en
  este bloque»). Es una review de bloque intermedio, y la puerta completa corresponde a T23 y al cierre. En su lugar,
  la verificación de T2 más las guardias de F-006: 1209 passed. Ojo: esto **no** sustituye al `init.sh` del cierre.
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`, `progress/current.md`,
  `progress/history.md`, `docs/ARCHITECTURE.md` y `docs/CONVENTIONS.md`.

**C2 — Estado coherente**
- [x] Una sola feature `in_progress` (F-059).
- [x] Rama `feature/F-059-volcado-sigrid-backend`.
- N/A · `progress/current.md` solo con la sesión activa: lo mantiene el líder y se exige al cierre. Lo dejo dicho
  para que conste: hoy arrastra entradas de F-060 ya cerrada, y el líder debería podarlo.
- N/A · Resumen en `history.md` de las `done`: F-059 no es `done`.

**C3 — Arquitectura y convenciones**
- [x] Hexagonal: `volcado.py` y `situacion_volcado.py` solo importan `domain.models` y la biblioteca estándar.
  `situacion_volcado.py` es una hoja de verdad: no importa `revision.py`. `test_f005_arquitectura.py` pasa.
- [x] Primera línea con la ruta en los dos módulos y en los dos tests nuevos.
- [x] Sin `print`, sin `TODO`, sin secretos y sin dependencias nuevas.
- [x] La unidad es el **parte**: un `ParteAVolcar` por incidencia, y el lote es una lista de partes.
- [x] Nada se escribe sin dry-run previo: en el dominio, `seleccionar_para_volcado` exige `previsto` en un ensayo
  vigente de la misma persona y la misma obra, de menos de 30 minutos (R17, R18). Que no se escriba sin
  confirmación lo cierran los Bloques 3 y 4.
- N/A · Lo manuscrito y «firmado no es conforme»: el bloque no toca partes escaneados.
- [x] **Reprocesar no duplica**: la referencia `PVI-<uuid>` sale de una sola función pura (R5), y `cuerpo_de_lote`
  rechaza referencias repetidas.
- [x] Ningún número de estado de Sigrid fijo: el parte nace en el estado inicial de la serie, que resuelve
  `sigrid-api`. `TIPO_RECLAMACION = "0002"` es el tipo (Q-1, lo decidió el humano), no un estado.
- [x] Ningún PDF ni escaneado: los ficheros añadidos en el bloque son dos módulos, dos tests y dos informes.

**C3 bis** — N/A: el bloque no toca `docs/referencia/`.

**C4 — Verificación real**
- [x] Los requisitos del Bloque 1 tienen test trazable y pasan (tabla de cobertura abajo). Los que dependen de
  puertos, adaptadores, HTTP o SQL (R8–R10, R13 al guardar, R15, R16, R19, R21, R25, R28, R29, R31–R34, R36–R43) son
  de los Bloques 2 a 6: N/A en este bloque, por alcance.
- [x] Sin red ni BBDD: dominio puro, y la guardia de red de `conftest.py` está activa.
- N/A · Las verificaciones `MANUAL (humano)` (T8, T25) son de bloques posteriores.

**C4 bis — Rigor declarado**
- [x] `rigor: critico` declarado.
- [x] **Fase RED**: la traza real está pegada (296 failed, 7 passed, contra un esqueleto neutro) y **la he
  reproducido** en `ffaf804`. Los 7 que pasan están explicados y no dependen de lo que faltaba.
- N/A · **Puerta `PUERTA COBERTURA` de `init.sh`**: fuera de este encargo (T23). La cobertura la he medido yo:
  100 % de `volcado.py` y de `situacion_volcado.py`; las líneas añadidas a `revision.py` y `errores.py` las recorren
  los tests de F-059.
- [x] **Mutación**: existe `progress/mutacion_F-059_bloque1.md`, generado por la herramienta, con 85/85/0/0.
  Alcance y número de mutantes **recalculados** y coinciden; cinco mutantes muestreados, idénticos.
- [x] **Los muertos, comprobados**: campaña de 217 min, **no reejecutada** (por encima de los 5 min), con el
  recálculo puro y mutantes a mano propios en su lugar. Coste por mutante ≈ 1227 s, coherente.
- [ ] **Cero supervivientes, también a mano**: la herramienta, 0; el implementer, 88/88; **los míos, 3
  supervivientes** sin test ni justificación aceptada (C-B1-1, C-B1-2, C-B1-3).
- [x] «Evidencias» con tests, cobertura, mutantes y supervivientes, tiempo de la suite y workers (8).
- N/A · Guarda por definiciones: ningún fichero sale de una lista de «no se toca» en este bloque.
- [x] Ningún N/A de este bloque sin su motivo escrito.

**C4 ter** — N/A: el repositorio no declara `harness/rutas_sensibles.json`.

**C5 — Cierre de la sesión**
- [x] T0–T3 en `[x]` en `tasks.md`, con sus commits `F-059 Tn: …`. T3 lleva dos commits (`e0e93db`, el test de
  inmutabilidad, y `135dd6b`, el informe), los dos con su prefijo: me vale.
- [x] Sin ficheros temporales ni artefactos sin seguimiento (`git status` limpio).
- [x] `features.json`: F-059 `in_progress`, que es su estado real.

### Cobertura: requisito → test (Bloque 1)

| Requisito | Tests (en `tests/test_f059_estados.py` = E, `tests/test_f059_volcado_dominio.py` = V) |
|---|---|
| R1 (§4.1, precedencia) | E `test_f059_r1_la_tabla_de_cuatro_uno`, `…_volcada_gana_a_lo_que_diga_el_ultimo`, `…_el_ultimo_enviado_o_sin_respuesta_deja_en_duda`, `…_volcada_y_en_duda_ganan_a_descartada`, `…_volcada_gana_aunque_no_haya_revisiones`, `…_seis_estados_en_su_orden` |
| R1/R13 (un `idempotente` de ensayo deja `volcada`) | E `test_f059_r1_r13_un_idempotente_de_ensayo_deja_volcada`; V `test_f059_r11_r13_ya_volcada_por_un_idempotente_de_ensayo` |
| R2 (sin acciones; dominio) | E `test_f059_r2_desde_volcada_y_en_duda_ninguna_accion`, `test_f059_r2_d14_accion_no_permitida_con_el_estado_y_sin_acciones` (la parte de la transacción es de T4/T6) |
| R3 | E `test_f059_r3_aprobada_y_en_duda_son_candidatas`, `…_una_volcada_no_es_candidata_nunca`, `…_candidata_de_rechaza_una_volcada`, `…_en_duda_sin_un_aprobar_detras_no_es_candidata` |
| R4 (b, c, d; dominio) y `SituacionDeRevision` sin `volcado` | E `test_f059_r4_resumen_con_seis_estados`, `…_d7_activas_sin_descartada_ni_volcada`, `…_d7_sin_filtro_es_activas`, `…_los_dos_filtros_nuevos`, `…_situacion_construida_sin_volcado_vale_none` (la parte (a), el objeto `volcado`, es de T15) |
| R5 | V `test_f059_r5_la_referencia_es_pvi_y_el_uuid_canonico`, `…_de_un_uuid_escrito_en_mayusculas_sale_en_minusculas`, `…_la_misma_incidencia_da_siempre_la_misma`, `…_solo_sale_de_un_uuid` |
| R6, Q-1, Q-2, D-9, D-10 | V `test_f059_r6_el_parte_clave_a_clave`, `…_q1_el_tipo_es_0002_con_cualquier_listado`, `…_el_cuerpo_clave_a_clave`, `…_commit_siempre_explicito`, `…_detalle_nulo_sin_la_clave_y_con_detalle_con_ella`, `test_f059_d9_…`, `test_f059_d10_ninguna_clave_de_mas` (huecos: C-B1-1, C-B1-2) |
| R7 | V `test_f059_r7_la_huella_intacta`, `…_un_valor_cambiado_con_la_huella_vieja`, `test_f059_r7_r11_huella_no_coincide`, `test_f059_r7_r20_huella_no_coincide` |
| R11, R27 | V `test_f059_r11_*` (cada exclusión, el orden pedido, la obra antes que lo volcado), `test_f059_r27_en_duda_y_aprobada_con_rechazo_se_vuelven_a_mandar` |
| R12, D-13 | V `test_f059_r12_d13_el_previsto_sin_cod_ni_ide_provisionales_ni_filas`, `test_f059_r12_el_resumen_del_ensayo` |
| R14, R24 (clase del código de lote) | V `test_f059_r14_r24_los_de_precondicion`, `test_f059_r24_todos_no_procesados_con_el_codigo_de_lote`, `test_f059_r24_r35_un_codigo_que_no_es_de_lote_no_se_guarda`, `test_f059_r14_dry_run_false_en_el_ensayo` |
| R17 | V `test_f059_r17_*` (29:59 vale; 30:00 caduca; cada motivo; el orden) |
| R18, R20 (la decisión), R21 (el orden del ensayo) | V `test_f059_r18_*`, `test_f059_r20_*`, `test_f059_r15_pedidas_repetidas` |
| R22 | V `test_f059_r22_*` (desordenados, de menos, de más, referencia cambiada, `previsto` en un volcado, `ide`/`cod` mal formados, `committed` nunca) |
| R23 | V `test_f059_r23_todos_sin_respuesta`, `…_sin_la_forma_de_la_pasarela_no_hay_interpretacion`, `…_dry_run_true_en_el_volcado` |
| R26 | V `test_f059_r26_*` (hueco: C-B1-3) |
| R30 | V `test_f059_r30_n_de_1_a_50`, `…_n_fuera_de_rango_o_no_entero`, `…_de_1_a_50_partes_por_cuerpo` |
| R32 (los `Enum`) y R35 | V `test_f059_r32_los_estados_y_los_modos_de_un_evento`, `test_f059_r22_r35_*`, `test_f059_r35_el_codigo_de_motivo_de_64_y_con_cifras_vale` |
| §7 (los ocho errores; la inmutabilidad) | V `test_f059_los_ocho_errores_del_volcado`, `test_f059_los_tipos_son_inmutables` |
| §21.5 (F-060) | E `test_f059_f060_*` |

### Decisiones de diseño del implementer (lo que pidió que mirase primero)

- **Decisión 1** (`seleccionar_para_ensayo` recibe `Mapping[UUID, SituacionDeRevision]`): **aceptada**. R11
  necesita saber si la incidencia está en la bandeja y de qué obra es, y eso no lo dice `SituacionDeVolcado`.
  Exigir las dos cosas, «en la lista **y** candidata en su situación», es más seguro que fiarse de una sola. El
  puerto no cambia.
- **Decisión 2** (`interpretar_respuesta` devuelve `None` si la respuesta entera no tiene la forma de §8.9):
  **aceptada**. Es lo conservador: todo acaba en `sin_respuesta` → `en_duda`, y reintentar es seguro por la
  referencia. Hay un coste asumible: si una 200 trae además un elemento basura, se pierde el `cod` de un `creado`
  válido de la misma respuesta, y lo recupera el siguiente ensayo como `idempotente`. El Bloque 4 debería registrar
  en el log, en ese camino, las referencias y los `cod` que sí venían, como hace R25.
- **Decisiones 3 a 12**: conformes con la spec. La 4 (`[0-9]` con `fullmatch`) es más estricta que §7 y tiene sus
  tests.
- **Observación sobre `envio` para T15**: de acuerdo. R6 y R12 mandan sobre el ejemplo de §11.

### Observaciones (no bloquean; para bloques posteriores)

- **O-B1-1 · R7 en el camino del volcado.** `seleccionar_para_volcado` compara la huella guardada en la última
  revisión con la del ensayo, y **no** recalcula `huella_de_valores` (`SituacionBloqueada` no lleva valores). Con la
  misma `revision_id` y una tabla append-only, eso basta para la coherencia, pero R20 pide «y R7» dentro de la
  transacción. El Bloque 4 tiene que aplicar `huella_intacta` a la candidata **de la que sale el parte que se manda**
  en el volcado, con un test «valor cambiado con la huella vieja → excluida en el **volcado** y no se manda». Lo
  miraré en esa review.
- **O-B1-2 · `EnsayoNoValido.causa`** se traduce en T15 a la clave `motivo` del cuerpo HTTP (§7). Hay que fijarlo en
  el test del borde.

### Propuestas de automejora (no aplicadas; para que el humano decida)

- **P-1 · Un operador de veracidad en `harness.mutacion`** (vale para cualquier proyecto: si se aprueba, se porta a
  `arnes-base`). Los tres hallazgos de esta review son el mismo patrón, `x is not None` frente a `x`, y la
  herramienta no lo genera. Propuesta: mutar `x is not None` → `x` y `x is None` → `not x`. Habría encontrado
  C-B1-1 y C-B1-2 sin que nadie tuviera que pensarlo a mano.
- **P-2 · `comando_de` debería escribir `--timeout`** cuando no es el valor de `rigor.json`. La cabecera de
  `progress/mutacion_F-059_bloque1.md` dice `--base 477e596 --workers 8`, pero la campaña se lanzó con
  `--timeout 1800`. Repetida con la cabecera tal cual (120 s por mutante) en una máquina donde la suite tarda 1563 s,
  saldrían todo timeouts. El docstring de `comando_de` ya da el mismo argumento para `--workers` y `--base`.

## Re-review del Bloque 1 · 2026-10-16

- **Veredicto:** **APPROVED**
- **Revisado:** `583e6d3` (código y tests) y `6c5b9d3` (cifras del informe), sobre `6864483`. Explicación del
  implementer en `progress/impl_F-059.md`, «Correcciones de la review del Bloque 1».
- **Nivel de rigor:** `critico`, con las mismas puertas que en la review.

### Corrección de una errata mía (el rojo de la guardia R26)

El implementer avisa de que `test_f006_repo_sin_identificadores.py::test_f006_r26_…` se ponía en rojo por **mi**
informe: al valorar el GUID sintético, escribí la forma canónica de los dos `UUID(int=…)` en el párrafo «Datos
sensibles». Lo he redactado en este mismo commit (ahora dice «la forma canónica de `UUID(int=0xABCDEF)`» y «la de
`UUID(int=1)`»). Con eso, las dos guardias de F-006 pasan (abajo). La valoración no cambia.

### El cambio de dominio, contra R6, D-9 y §8.9

`583e6d3` añade `_con_texto(texto)` en `domain/models/volcado.py`: devuelve `None` si el texto es nulo, vacío o
solo blancos, y si no, el texto **tal cual**. Lo usan tres sitios: si hay interviniente (`parte_de`), la
`descripcion_larga` del parte (`parte_de`) y si la clave va en el cuerpo (`cuerpo_de_parte`).

- **R6** («`descripcion_larga` = `detalle` solo si no es nulo; si lo es, la clave no va») y **§5/§8.9** (sin la
  clave, la pasarela pone la descripción, «como el alta manual»): tratar un detalle en blanco como nulo es la
  lectura que protege lo que R6 quiere, que es no dejar en `rcp.tex` una descripción larga en blanco. Además es la
  misma regla que ya aplica `validar_valores` al editar (`revision.py:616`, `strip() or None`). **Conforme.**
- **D-9** («`[]` sin proveedor»): un código vacío no identifica a ningún `obrofc`. Mandarlo provocaría
  `interviniente_no_esta_en_la_obra` en §8.9, es decir, un parte rechazado que se aprobó «sin proveedor».
  **Conforme.**
- **Lo que dice algo va sin recortar** (`" EJ07"`, `"  Ejemplo de detalle  "`): es coherente con R7 (lo aprobado
  es lo que se manda). La huella se calcula sobre los valores, no sobre el parte, así que no cambia.
- Tampoco cambia la lista de claves (D-10), el `tipo`, el `causante` ni el resto del cuerpo.
  `test_f059_r6_el_cuerpo_clave_a_clave` y `test_f059_d10_ninguna_clave_de_mas` siguen pasando.
- **C-B1-3**: sin cambio de código, dos tests nuevos que separan el `ide` del `cod`. **Conforme** con R26.

Los tests nuevos usan datos ficticios (`EJ07`, «Ejemplo de detalle»). He barrido el diff `6864483..6c5b9d3` en
busca de GUID, correos, IPs y claves, y no aparece nada.

### Mutantes, repetidos en una copia desechable

En un worktree desechable de `6c5b9d3` (ya retirado; el árbol de trabajo no se ha mutado y su `git status` queda
limpio), solo con `test_f059_volcado_dominio.py` y `test_f059_estados.py`, con `-x`.

**Mutantes de la herramienta en las líneas de la corrección.** He recalculado el alcance de `135dd6b..6c5b9d3`:
23 líneas de `volcado.py` y **2 mutantes** (`generar_mutantes`), los dos en `_con_texto`. He aplicado los dos
(`aplicar_mutante`):

| Mutación (herramienta) | Resultado | Test de F-059 que lo caza |
|---|---|---|
| `volcado.py:358` `or` → `and` | muerto | `test_f059_r6_el_parte_clave_a_clave` |
| `volcado.py:358` `not texto.strip()` → `texto.strip()` | muerto | `test_f059_r6_el_parte_clave_a_clave` |

**Mutantes a mano (13):**

| Id | Mutación | Resultado | Test de F-059 que lo caza |
|---|---|---|---|
| A1 | `_con_texto` sin `strip` (`not texto`) | muerto | `test_f059_d9_c_b1_1_un_codigo_de_proveedor_vacio_es_sin_proveedor[blancos]` |
| A2 | `_con_texto` devuelve el texto recortado | muerto | `test_f059_r6_c_b1_2_un_detalle_que_dice_algo_va_tal_cual` |
| A3 | Solo quita espacios: el tabulador cuenta como texto | muerto | `…_un_codigo_de_proveedor_vacio_es_sin_proveedor[tabulador]` |
| A4 | Proveedor: vuelta a `is not None` | muerto | `…_un_codigo_de_proveedor_vacio_es_sin_proveedor[vacio]` |
| A6 | Detalle: vuelta a `descripcion_larga=v.detalle` | muerto | `test_f059_r6_c_b1_2_un_detalle_vacio_no_es_descripcion_larga[vacio]` |
| A7 | Cuerpo: vuelta a `is not None` | muerto | `test_f059_r6_c_b1_2_el_cuerpo_no_manda_una_descripcion_larga_vacia[vacio]` |
| A9 | `_con_texto` rechaza también lo que tiene blancos alrededor | muerto | `test_f059_d9_c_b1_1_un_codigo_de_proveedor_que_dice_algo_va_tal_cual` |
| A10 | Proveedor por veracidad (mi C-B1-1) | muerto | `…_un_codigo_de_proveedor_vacio_es_sin_proveedor[blancos]` |
| A11 | Cuerpo por veracidad (mi C-B1-2) | muerto | `…_el_cuerpo_no_manda_una_descripcion_larga_vacia[blancos]` |
| A12 | Duplicado por `cod` (mi C-B1-3) | muerto | `test_f059_r26_c_b1_3_el_mismo_ide_con_otro_cod_no_lo_es` |
| A13 | Duplicado por `ide` **o** `cod` | muerto | `test_f059_r26_c_b1_3_el_mismo_ide_con_otro_cod_no_lo_es` |
| A5 | `proveedor=_con_texto(v.proveedor_codigo)` dentro de la rama | no cambia el programa | — |
| A8 | `cuerpo["descripcion_larga"] = _con_texto(…)` dentro de la rama | no cambia el programa | — |

**A5 y A8 no son supervivientes: no son mutantes.** Los dos aplican `_con_texto` a un valor dentro de una rama a la
que solo se entra si `_con_texto` de **ese mismo valor** no es `None`, y en ese caso `_con_texto` devuelve el texto
sin tocarlo (`return texto`). Para cualquier entrada, el resultado es el mismo que el del código original: no hay
comportamiento que un test pueda distinguir, ni que proteger. Por eso no los cuento como mutantes equivalentes que
necesiten la aceptación del humano (C4 bis), sino como reescrituras que no cambian nada, y los anoto aquí para que
se vean. Si el humano prefiere aplicar la regla al pie de la letra, basta con su visto bueno a este párrafo: el
implementer no tiene nada que cambiar.

Los 13 que cambian el programa (2 de la herramienta y 11 a mano) **mueren todos con un test de F-059**, y ninguno
lo caza solo una suite vecina. La corrección no abre ningún superviviente en las líneas que toca. Los 8 mutantes del
implementer (su tabla) coinciden con A1, A2, A4, A6, A7, A10, A11 y A12.

La campaña completa de la herramienta no se relanza (indicación del líder). Lo que la corrección añade se ha
evaluado entero con los dos mutantes de la herramienta de arriba, y el alcance de antes no ha cambiado fuera de
esas 23 líneas.

### Verificación

Desde el scratchpad, sin `.env`:

| Verificación | Resultado |
|---|---|
| Los diez ficheros de T2 + las dos guardias R26 de F-006 (con mi informe ya redactado) | **1221 passed in 30.46s** |
| Cobertura con los dos ficheros de F-059 | `volcado.py` 284/284 y `situacion_volcado.py` 47/47: **100 %** |
| `ruff check` de `volcado.py` y `test_f059_volcado_dominio.py` | `All checks passed!` |

### Checkpoints que cambian respecto a la review

- [x] **C4 bis · Cero supervivientes, también a mano**: la herramienta, 0 (85 + 2); el implementer, 88 + 8; el
  reviewer, 25 + 13, todos muertos con tests de F-059. A5 y A8, razonados arriba: no cambian el programa.
- [x] **C3** sigue en orden: `_con_texto` es privada, pura y lleva la ruta en la primera línea del módulo, y no hay
  dependencias nuevas.
- [x] **C5**: los commits de la corrección (`583e6d3`, `6c5b9d3`) no llevan `Tn` porque corrigen la review, no son
  una tarea nueva. Me vale: `tasks.md` sigue con T0–T3 en `[x]`.
- El resto de checkpoints, como en la review del Bloque 1 (los N/A, con su motivo allí).

### Observaciones que siguen abiertas (para bloques posteriores, no bloquean)

O-B1-1 (R7 recalculado en el camino del volcado, Bloque 4), O-B1-2 (`causa` → `motivo` en T15) y las propuestas
P-1 y P-2 siguen como se escribieron arriba.

## Review del Bloque 2 (la tabla y los repositorios) · 2026-10-16

- **Veredicto:** **APPROVED** (sin hallazgos que corregir; cuatro observaciones para el líder y para bloques
  posteriores).
- **Alcance revisado:** `git diff 9fdb222..cf1c451`, sin `harness/features.json`, `BACKLOG.md` ni
  `progress/current.md`, que son del líder. Commits: el bloqueo y su resolución (`2203879`, `3816511`, `238cfe6`, y
  `13f9f51`, la spec con B-1 (a) y B-2, decisión del humano «ok a b1 y b2»), T4 `f50281b`, T5 `54c3278`, T6
  `cf3b7a2`, T7 `9b4c8d5`, y T9 `64b25b8`, `42be797`, `55f27f5` y `cf1c451`.
- **Nivel de rigor:** `critico`. Las mismas puertas que en el Bloque 1.

### Qué he verificado yo, y cómo

Desde el scratchpad, sin `.env`, con `services/postventa-api/.venv/Scripts/python.exe -m pytest` y rutas
absolutas. Los mutantes, en un worktree desechable de `cf1c451`, ya retirado: `git worktree list` sin ninguno del
scratchpad y `git status` limpio.

| Verificación | Resultado |
|---|---|
| **Suite entera del servicio** (`tests` y `tests_bbdd`) | **8597 passed, 233 skipped in 704.37s**, las mismas cifras que el implementer. Los de base se saltan sin DSN |
| `tests_bbdd/tests/test_f059_bbdd_volcado.py`, `--collect-only` | **46 tests collected**, como dice el informe |
| `ruff check` (desde la raíz) sobre los 7 ficheros de producción del bloque, los 3 tests nuevos y `test_f056_repositorio_revision.py`/`test_f056_ddl.py` | `All checks passed!` |
| Recálculo puro del alcance (`alcance_de_feature("F-059", base="13f9f51")`) | 7 ficheros, **848** líneas (13 + 116 + 17 + 49 + 290 + 33 + 330). Coincide |
| Recálculo de los mutantes (`generar_mutantes`) | **26** (1 + 0 + 0 + 2 + 6 + 2 + 15). Coincide; los n.º 1, 3, 9, 15, 21 y 26 salen idénticos a la tabla del informe |
| Ocho mutantes de la herramienta (n.º 2, 4, 6, 10, 11, 13, 17 y 21), contra los tests de F-059 solos | 8/8 muertos, cada uno por el mismo test que da la tabla del implementer |
| Mutantes a mano del reviewer (21), contra los tests de F-059 solos | 21/21 muertos (abajo) |
| Barrido de datos sensibles en el diff | Ver «Datos sensibles» |

**Campaña no reejecutada: 75 min según el informe** (4484.1 s, por encima de los 5 minutos del protocolo). Me
quedo en el recálculo puro, en la reverificación de ocho mutantes de la herramienta y en mis mutantes a mano. El
coste por mutante, 4484.1 × 8 ÷ 26 ≈ **1380 s**, es coherente con una suite que tarda entre 700 y 1300 s según la
carga: nada sospechoso.

### Lo que el líder pidió mirar primero

**(1) `aprobadas` deja fuera solo la `volcada`, no filtra con `es_candidata` (§12). Es una desviación aceptable, y
no hace falta volver al spec-author por el fondo, pero sí por la letra (O-B2-1).** El razonamiento:

- Las filas que devuelve `select_aprobadas` tienen todas como última revisión un `aprobar` (lo filtra el SQL).
  Para ellas, `estado_de` solo puede dar `aprobada`, `en_duda` o `volcada`. Así que «no es `volcada`» y
  `es_candidata` **dan lo mismo en todo lo que el SQL puede devolver**: pasan la `aprobada` y la `en_duda`, y
  queda fuera la `volcada`. R3 se cumple al pie de la letra.
- Solo se diferencian ante una fila **imposible** (una última revisión que no es `aprobar`). Con `es_candidata` se
  la tragaría en silencio. Con el filtro estrecho llega a `candidata_de` y explota, que es lo que exige
  `test_f056_r34_si_la_base_devolviera_otra_cosa_que_un_aprobar_no_pasa`. Ese test no está en las excepciones de
  R41, así que la letra de §12 obligaba a **relajar** un test que R41 no deja tocar: la spec se contradecía, y el
  implementer ha elegido la lectura que cumple R3 y R41 a la vez. Me parece la correcta.
- Lo comprueban mis A01 (dejar fuera también la `en_duda`: muerto) y los A04 y A05 del implementer.
- Queda un matiz, sin efecto práctico: una fila imposible **y** `volcada` se descarta sin explotar, porque la
  precedencia de §4.1 la pone en `volcada` antes de mirar la revisión. El SQL no puede devolverla.

**(2) B-1 (a): R33 al pie de la letra y R17 entero.**
- **R33:** ninguna lista de columnas lee `actor_oid`. La única sentencia que lo nombra fuera de los `INSERT` es
  `select_ensayo`, y solo dentro de la comparación `(actor_oid = %s)`, con el `oid` de quien pide como
  **parámetro**. El orden de los parámetros es correcto: `(actor_oid, ensayo_id, modo)`, que casa con los tres
  `%s`; mi H07, que los cruza, muere. `test_f059_r33_ninguna_lectura_selecciona_actor_oid` mira cada lectura
  (las de F-059 y las tres de F-056 que ganan las `LATERAL`) **y su texto entero**, y tiene su control no ciego.
  Mis H08 (`ORDER BY …, actor_oid`) y H09 (`v.actor_oid` dentro de una `LATERAL`, sin que salga en la lista de
  fuera) **mueren**: el control no se deja engañar por un `actor_oid` escondido en una subconsulta. Ningún log ni
  mensaje lleva el `oid` (`test_f059_r34_ningun_log_del_repositorio_lleva_oid_ni_correo`, y el
  `PersistenciaNoDisponible` de `_Transaccional` no lleva parámetros).
- **R17:** siguen los cuatro motivos, en su orden (`test_f059_r17_el_orden_obra_persona_caducidad`; D02 del
  implementer), el 29:59 frente al 30:00 (`test_f059_r17_a_los_30_minutos_caduca`) y `de_otra_persona`, que sale
  ahora de `not ensayo.de_la_persona`. `de_la_persona` es la conjunción de **todas** las filas
  (`all(fila[2] …)`). Mis H05 (`is not None`, que daría por buena una comparación `False`) y H06 (`any`) mueren.
  `test_f059_r17_r33_b1_el_dominio_no_ve_ningun_oid` fija que ni `Ensayo` ni `validar_ensayo` tienen un `oid`.
  Los tests de R17 del Bloque 1 se han **adaptado** a la firma nueva (`de_la_persona`) sin quitar ningún caso: es
  lo que decidió el humano en B-1 (a).

**(3) V05d (`if estado:` en vez de `estado in _BLOQUEAN_LA_REVISION`).** Estoy de acuerdo: **no cambia el
programa.** `estado` sale de `estado_de_volcado`, que solo devuelve `None` o uno de los dos miembros de
`EstadoVolcado` (textos no vacíos, verdaderos), y los dos están en el conjunto. Es la misma categoría que A5 y A8
de la re-review del Bloque 1, y vale el mismo párrafo: si el humano quiere la regla literal, basta con su visto
bueno. Escribir los dos estados uno a uno, con sus mutantes V05a a V05c muertos, es mejor código que el
`estado is not None` de antes. Mi A02 (bloquear solo la `volcada`) también muere.

**(4) La primera campaña, parada con un mutante equivalente dado por muerto bajo carga.** El informe lo cuenta
sin maquillar, y la consecuencia está bien sacada: el veredicto «muerto» de la herramienta no dice **qué test**
lo mató, y bajo carga puede contar como muerto un fallo que no tiene que ver con el mutante. Ya pasó en el Bloque
1 con `PosibleDuplicado`. La defensa que ha aplicado el implementer, reverificar cada mutante contra los tests de
la feature, es la correcta, y la he comprobado con ocho muestras. El mutante en cuestión (`strict=False` en el
`zip` de `guardar_ensayo`) ya no existe en el código final: ese `strict` se quitó por redundante. Lo convierto en
una propuesta de mejora del arnés (P-3, abajo).

**(5) Excepciones de R41 (el grupo A y el r12 de B-2), comparadas con `9fdb222`.** Los once tests del grupo A más
el de B-2, y nada más. Cada cambio sustituye una igualdad exacta por otra igualdad exacta con el `16_` (o con
`volcados_sigrid.actor_correo`) añadido, y lleva su comentario
`F-059 (R41, F-1 (a); design.md §21.3 A)`:

| Test | Cambio | ¿Amplía sin relajar? |
|---|---|---|
| `test_f005_…::test_f005_r1_…`, `test_f028_…`, `test_f036_ddl.py::test_f036_t14_…` | + `"16_volcados_sigrid.sql"` al final de la lista exacta | Sí |
| `test_f030_…`, `test_f031_…`, `test_f032_…`, `test_f033_…`, `test_f034_…` (`no_hay_ni_un_fichero_de_ddl_nuevo`) | `== DDL_DE_F028 + DDL_DE_F036 + DDL_DE_F056 + ("16_…",)`, dentro de la función; las constantes, sin tocar | Sí |
| `test_f056_ddl.py::test_f056_r36_…` | `nombres[-1] == 15_` pasa a `nombres[-2] == 15_` **y** `nombres[-1] == 16_` | Sí: más estricta |
| `test_f056_ddl.py::test_f056_r12_la_unica_columna_de_correo_…` (B-2) | La igualdad exacta pasa a las dos columnas | Sí |
| `test_f056_alcance_cerrado.py::test_f056_r12_solo_15_…` | `== ["15_…", "16_…"]` | Sí |
| `test_f060_alcance_cerrado.py::test_f060_r37_los_sql_son_los_quince_de_antes` | `== (*SQL_DE_LA_BASE, "16_…")`; la constante, sin tocar | Sí |

`test_f056_repositorio_revision.py` (grupo C: «el ancho de las filas falsas de `_select_situaciones`, `aprobadas`
y `registrar`»): las cinco líneas que se quitan se sustituyen por la misma aserción con la cifra nueva o en la
posición nueva (`count("LEFT JOIN LATERAL") == 4`, `len(sql) == 4`, el `INSERT` en `sql[3]`), y cada una gana
además una aserción sobre lo nuevo. Los casos añadidos se llaman `test_f059_*`. Lo demás del fichero (la fila con
el ancho nuevo, `LEIDAS_DEL_VOLCADO` escrita a mano) es lo que R41 autoriza. `test_f056_r34_…` y
`test_f056_r7_r22_bloquea_las_dos_en_orden_fijo_y_mira_las_dos` **no** se tocan, y pasan. Ningún otro test ajeno
aparece en el diff.

### El código, contra la spec

- **`16_volcados_sigrid.sql`** es literal con `design.md` §9: las 16 columnas, los dos `CHECK` de dominio, los
  cuatro de fila y los dos índices. Lleva la cabecera de §9, solo el esquema `postventa`, nada de servidor y nada
  aplicado contra ninguna base. El `%` del `LIKE 'PVI-%'` es seguro: `arranque._aplicar` ejecuta cada sentencia
  **sin parámetros**, y psycopg 3 no interpreta los `%` sin parámetros. T8 lo confirmará contra la base.
- **`sentencias_volcado.py`** es puro y hoja. Ningún valor recibido se interpola; las dos `LATERAL` (el **primer**
  `creado`/`idempotente` de cualquier modo, por `evento_id` ascendente, y el **último** de modo `volcado`, por
  `evento_id` descendente) son §4.1 y R4.
- **`anotar_enviados`** hace R20 en **una** transacción: `select_bloquear` de F-056 (la misma sentencia y el mismo
  orden que `registrar` y `registrar_lote`, §21.5), después la lectura, la decisión **dentro**, los `INSERT` de los
  `enviado` y el `COMMIT`. Nunca `pg_advisory_lock`.
- **R2 en `_registrar`**: el orden es bloqueo → últimas → situación de volcado → R2 → frescura → `INSERT` (decisión
  2 del implementer). La lectura va tras el `FOR UPDATE` y dentro de la transacción, y R2 manda sobre la frescura,
  como pide §12. `registrar_lote` y `_registrar_lote` (F-060) no cambian.
- `RevisionPort` no cambia. Lo nuevo va en `RepositorioVolcadoPort`, con las cinco operaciones de §8.1 enmendado.
- La hexagonal se respeta: `domain/ports/volcado.py` solo importa del dominio, y la infraestructura importa de la
  infraestructura y del dominio. Todos los ficheros llevan la ruta en la primera línea, y no hay `print`, `TODO` ni
  dependencias nuevas.

### Orden (punto 7 del protocolo): aplicado

R2 y R20 son requisitos de **orden** en una feature `critico` («dentro de la transacción que bloquea», «solo tras el
`COMMIT` se llama a Sigrid»). He bajado cada puerta un paso por cada colaborador al que precede, en la copia
desechable y solo con los tests de F-059 (`-k test_f059` sobre los cinco ficheros del bloque):

| Id | Mutación de orden | Resultado | Test de F-059 que la caza |
|---|---|---|---|
| O01 | `_registrar` sin la comprobación de R2 | muerto | `test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[enviado]` |
| O02 | La lectura de R2 **antes** del `FOR UPDATE` | muerto | `test_f059_r2_se_lee_tras_el_bloqueo_y_solo_la_de_la_propia` |
| O03 | La lectura de R2 entre el bloqueo y la de las últimas | muerto | `test_f059_r2_se_lee_tras_el_bloqueo_y_solo_la_de_la_propia` |
| O07 | R2 **después** del `INSERT` de la revisión | muerto | `test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[enviado]` |
| O04 | `anotar_enviados`: leer antes de bloquear (el bloqueo después) | muerto | `test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma` |
| O06 | `anotar_enviados` sin bloquear | muerto | `test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma` |
| O05 | `anotar_enviados`: decidir **fuera** de la transacción (bloqueo y lectura en una, `INSERT` en otra) | muerto | `test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma` |

Los siete los caza un test **de F-059**, no una suite vecina. La serialización real entre conexiones (que el que
entra segundo espere y vea al primero) solo la puede probar T8.

### Mutantes a mano del reviewer (además de los de orden)

Incluyen el encargo pendiente del humano: `x is not None` → `x` y `x is None` → `not x` en las líneas nuevas.
Las líneas nuevas con esa forma son cuatro, todas en `sentencias_volcado.py`, y son H01 a H04:

| Id | Mutación | Resultado | Test de F-059 que lo caza |
|---|---|---|---|
| H01 | `fila_a_volcado`: `if ide is not None` → `if ide` | muerto | `test_f059_r1_lo_que_decide_que_haya_parte_es_la_fila_y_no_su_valor` |
| H02 | `fila_a_volcado`: `if estado is not None` → `if estado` | muerto | `test_f059_r1_lo_que_decide_que_haya_parte_es_la_fila_y_no_su_valor` |
| H03 | `fila_a_bloqueada`: `accion is None` → `not accion` | muerto | `test_f059_r20_una_accion_vacia_no_es_sin_revision` |
| H04 | `_con_zona`: `tzinfo is None` → `not tzinfo` | muerto | `test_f059_r32_lo_que_decide_la_zona_es_que_la_haya_y_no_su_veracidad` |
| H05 | `de_la_persona` con `is not None` (un `False` contaría) | muerto | `test_f059_r17_b1_de_la_persona_solo_si_lo_es_en_todas_las_filas[una-de-otra]` |
| H06 | `de_la_persona` con `any` | muerto | `…_de_la_persona_solo_si_lo_es_en_todas_las_filas[la-ultima-de-otra]` |
| H07 | `select_ensayo` con los parámetros cruzados | muerto | `test_f059_r17_b1_el_ensayo_compara_la_persona_en_la_base` |
| H08 | `ORDER BY evento_id, actor_oid` | muerto | `test_f059_r17_b1_el_ensayo_compara_la_persona_en_la_base` |
| H09 | `v.actor_oid` dentro de la `LATERAL` del último | muerto | `test_f059_r1_r4_la_situacion_de_volcado_con_dos_lateral_y_la_ultima_revision` |
| A01 | `aprobadas` deja fuera también la `en_duda` | muerto | `test_f059_r3_aprobadas_con_una_volcada_no_falla_y_no_la_devuelve` |
| A02 | R2 solo con la `volcada` | muerto | `test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar[enviado]` |
| A04 | El `enviado` con la referencia en minúsculas | muerto | `test_f059_r20_anotar_bloquea_lee_decide_inserta_y_confirma` |
| A05 | `situaciones` abre la base sin pedidas | muerto | `test_f059_t6_situaciones_de_ninguna_no_abre_nada` |

Hubo dos más que descarto por errata mía, no por equivalencia del código: un `[::-1][::-1]` y un diccionario por
comprensión sobre una lista vacía, que son la identidad y no mutan nada. Los he sustituido por O07 y A05.

**En total, 21 mutantes míos que cambian el programa, y los 21 mueren con un test de F-059.** Con los 83 a mano
del implementer y los 26 de la herramienta (reverificados: 26/26 contra F-059 solos, ocho de ellos comprobados
por mí), no queda **ningún superviviente** abierto. V05d está razonado en el punto (3).

### T7 y lo que necesita T8

T7 está lista para T8:
- Recoge 46 casos y se salta entero sin `POSTVENTA_PG_TEST_DSN`. El conftest aborta con un DSN que no sea local.
- `infra/pruebas_bbdd_efimera.ps1` ejecuta `pytest tests_bbdd` entero, así que lo incluye.
- Borra sus filas de `volcados_sigrid` antes y después de cada test, para no romper la limpieza de
  `test_f060_bbdd_lote.py`.
- Usa datos ficticios (obra `9904`, `uuid4`, `@ejemplo.invalid`).
- Los tres casos de dos conexiones esperan con `ESPERA = 1.0` y `join(timeout=10)`. El informe ya avisa de qué
  rojo es carga (repetir) y cuál es defecto (`DeadlockDetected`, o un hilo que no termina).

T8 sigue siendo MANUAL del humano y **bloquea el cierre**.

### Datos sensibles

Patrones: GUID, correos, IPv4 y `password|secret|token|AccountKey`, sobre el diff entero.
- **GUID:** ninguno.
- **Correos:** `persona.volcado@ejemplo.invalid` y `otra.persona@ejemplo.invalid`.
- **IPs:** ninguna.
- **«password»:** solo `contrasena-inventada` en los tests de la fábrica, la firma `conectar(dsn, *, password)` del
  doble y la línea del barrido del propio informe.
- **Obras:** `9901`, `9902` y `9904`.

### Checkpoints (los que cambian respecto al Bloque 1)

- N/A · **C1 `init.sh`**: fuera del encargo, por la regla del `.env`. La puerta completa es T23. En su lugar, la
  suite entera, en verde, desde un directorio sin `.env`.
- N/A · **C2 / C4 `progress/current.md`**: es del líder. **Para el líder:** T8 todavía no figura allí como MANUAL
  pendiente con su comando (`powershell -ExecutionPolicy Bypass -File infra\pruebas_bbdd_efimera.ps1`, 46 casos
  de F-059 esperados); hay que añadirla (O-B2-3).
- [x] **C3**: hexagonal, primeras líneas, sin `print` ni secretos, append-only (ningún `UPDATE`/`DELETE`/`TRUNCATE`
  en el código del servicio; R33), nunca consultivo, solo el esquema propio.
- [x] **C4**: R1–R4 (situación de volcado en la fila), R2/R29, R3, R13 y R22–R24 (guardar), R17 (B-1 (a)), R20,
  R32 y R33, cada uno con sus `test_f059_*`; los unit tests no tocan red ni base (`ConexionDoble`).
- [x] **C4 bis · RED**: traza pegada (171 failed, 328 passed, más los 12 del grupo A rojos por el `16_`).
- [x] **C4 bis · cobertura**: 100 % de lo nuevo según el informe; todas las líneas de F-059 de
  `repositorio_revision_pg.py` y `fabrica.py` cubiertas. La `PUERTA COBERTURA` es de T23.
- [x] **C4 bis · mutación**: informe de la herramienta 26/26/0/0, recalculado; los muertos, comprobados por
  muestreo y con mutantes propios; cero supervivientes abiertos.
- [x] **C4 bis · orden**: aplicado (siete mutantes de orden, todos muertos por F-059).
- [x] **C4 bis · «Evidencias»**: con los workers (8).
- N/A · **C4 ter**: no hay `harness/rutas_sensibles.json`.
- [x] **C5**: T4–T7 y T9 con sus commits `F-059 Tn:`; T8, MANUAL pendiente; árbol limpio.

### Observaciones (no bloquean)

- **O-B2-1 · `design.md` §12 tiene que decir lo que hace el código.** Que un spec-author cambie «`aprobadas` filtra
  con `es_candidata`» por «deja fuera la `volcada` antes de `candidata_de`; lo que no sea un `aprobar` sigue
  llegando a `candidata_de`, que lo rechaza (doble defensa de R34 de F-056, que R41 no deja relajar)». Es un cambio
  mecánico (R3 no cambia) y conviene hacerlo antes de T20.
- **O-B2-2 · Para el Bloque 4: `guardar_ensayo` no debe recibir un `sin_respuesta`.** El `CHECK` de fila lo
  rechaza en un ensayo (T7 lo prueba) y el resultado sería un `CheckViolation`, que `_Transaccional` traduce a
  503, cuando R14 pide **502 sin guardar nada**. La aplicación tiene que convertir antes cualquier `sin_respuesta`
  del ensayo en `EnsayoSinRespuesta` (la nota de `interpretar_respuesta` ya lo dice), con su test en el pipeline.
- **O-B2-3 · T8 en `progress/current.md`** (el punto de C2/C4 de arriba).
- **O-B1-1 sigue abierta.** `anotar_enviados` decide con `seleccionar_para_volcado`, que compara las huellas
  guardadas. El recálculo de R7 sobre los valores del parte que se manda es del Bloque 4.

### Propuesta de automejora (no aplicada)

- **P-3 · Que `harness.mutacion` anote el test que mata cada mutante** (vale para cualquier proyecto: si se
  aprueba, se porta a `arnes-base`). Por ejemplo, el primer `FAILED` de la salida de `pytest -x` en una columna
  del informe. Hoy un «muerto» no distingue entre lo que vigila un test y un fallo ajeno bajo carga; en este
  proyecto ha pasado ya dos veces (`PosibleDuplicado` en el Bloque 1 y `strict=False` en la primera campaña del
  Bloque 2). Con esa columna, la reverificación contra los tests de la feature, que hoy hace a mano el implementer
  y comprueba por muestreo el reviewer, pasaría a ser una lectura del informe. Complementa P-1 y P-2.

## Review del Bloque 3 (el adaptador de `sigrid-api` y las fábricas) · 2026-10-16

- **Veredicto:** **CHANGES_REQUESTED** (2 hallazgos: C-B3-1 y C-B3-2). Los dos son huecos de los tests,
  pequeños, y no defectos del código. El resto del bloque está en orden y responde bien a lo que pide la spec.
- **Alcance revisado:** `git diff 8e668b2..890e2f4`, sin lo del líder (`features.json`, `BACKLOG.md`,
  `current.md`). Commits: `5c0a6d2` (V05d, aceptado por escrito por el humano), T10 `9bdc35c`, T11 `7705354`,
  T12 `eb8d03b`, `93a3984` y `890e2f4`. He comprobado de paso `f7bcf9b` (O-B2-1): §12 dice ya lo que hace
  `aprobadas`, y el resto de la spec no cambia.
- **Nivel de rigor:** `critico`.

### Qué he verificado yo, y cómo

Desde el scratchpad, sin `.env`. Los mutantes, en dos worktrees desechables de `890e2f4`, ya retirados:
`git worktree list` sin ninguno del scratchpad y `git status` limpio.

| Verificación | Resultado |
|---|---|
| **Suite entera del servicio** (`tests` y `tests_bbdd`) | **8768 passed, 233 skipped in 589.09s**, las mismas cifras que el implementer |
| `ruff check` (desde la raíz) sobre los seis ficheros de producción y los dos tests nuevos | `All checks passed!` |
| Recálculo puro (`alcance_de_feature("F-059", base="5c0a6d2")`) | 6 ficheros, **509** líneas (5 + 32 + 16 + 69 + 78 + 309) y **25** mutantes (0 + 2 + 0 + 4 + 3 + 16). Coincide; los n.º 1, 5, 11, 16, 22 y 25 salen idénticos a la tabla |
| Ocho mutantes de la herramienta (n.º 7, 8, 9, 11, 18, 19, 20 y 23: los de la ventana, el `commit` y el 400), contra los dos ficheros de F-059 solos | 8/8 muertos, cada uno por el mismo test que da la tabla del implementer |
| Mutantes a mano del reviewer (17, dos de ellos con variante) | 15 muertos y **2 supervivientes**, que tampoco caza el conjunto de T11 (F-009 y F-012 incluidos): **1000 passed** con cada uno |
| Tests ajenos tocados | **Ninguno**: el diff de `tests/` son solo los dos ficheros de F-059 |
| Red | Ningún test llama a la red. `sin_red` (autouse, de sesión) sigue puesto; el adaptador se prueba con `ClienteFalso`; las fábricas construyen sin cliente y solo se llama a `volcar` sobre el ensayador, que se niega antes de componer nada |

**Campaña no reejecutada: 50 min según el informe** (3012.2 s, por encima de los 5 minutos del protocolo). El
coste por mutante, 3012.2 × 8 ÷ 25 ≈ **964 s**, es coherente con una suite que tarda entre 470 y 590 s.

### Hallazgos (cambios requeridos)

1. **C-B3-1 · Un 2xx que no es 200 ni 201 no está fijado. Mutante M05,
   `services/postventa-api/infrastructure/sigrid/volcado.py:247`.** Si cambio
   `if respuesta.status_code not in CORRECTOS:` por `if respuesta.status_code >= 300:`, el mutante **sobrevive** a
   los 170 tests de F-059 y a los 1000 de T11. Con él, un 202 o un 204 con un objeto JSON pasarían a `ok` en vez de
   a `sin_respuesta`. R23 dice «un código que no es 200 ni 400 → `sin_respuesta`», y
   `test_f059_r23_cualquier_otro_codigo_es_sin_respuesta` solo prueba `401, 403, 404, 409, 422` (los 5xx, 408 y 429
   salen en los de R21). **Qué hacer:** añadir a esa parametrización al menos un 2xx de fuera de `CORRECTOS` (202 o
   204) y, si se quiere, un 3xx, y comprobar que el mutante muere.
2. **C-B3-2 · `truncated` se decide por su veracidad, y ningún test lo fija. Mutantes M07 y M15,
   `services/postventa-api/infrastructure/sigrid/volcado.py:182`.** Si cambio `if datos.get("truncated"):` por
   `if datos.get("truncated") is True:` (o por `== True`), el mutante **sobrevive** a F-059 y a T11. Hoy cualquier
   valor verdadero (`1`, `"true"`) cuenta como truncado, que es lo conservador: una lectura truncada no decide el
   login. Pero ningún test lo dice: `test_f059_r8_una_lectura_sin_forma_o_truncada_no_decide_nada[truncada]` solo
   usa `True`. Es la clase de mutante del Bloque 1, al revés: la veracidad frente a la identidad. **Qué hacer:** un
   caso con un `truncated` verdadero que no sea `True` (por ejemplo, `1`) → `EnsayoSinRespuesta`. El cierre de F-009
   (`cliente.py:299`) tiene la misma línea, pero ese es su alcance y no se toca aquí.

Con los dos casos, repetir M05, M07 y M15 en una copia desechable y anotar qué test de F-059 los caza. No hace
falta relanzar la campaña: son líneas que la herramienta no muta así.

### Lo que el líder pidió mirar primero

**(1) `existe_usuario` sin respuesta → `EnsayoSinRespuesta` (502).** **Encaja con R14 y con §8.2. No hace falta
volver al spec-author para el código, pero sí que el contrato lo diga (O-B3-1).**
- En el **ensayo**, R14 dice: «si no responde, tarda más de su tiempo, responde otro código o algo que no es JSON
  → 502 sin guardar nada: es una lectura, repetirla es inocuo». La lectura del login es eso exactamente.
- En el **volcado**, R19 pone el login **antes** de la escritura anticipada, así que tampoco se ha escrito nada y
  un 502 «repetir es inocuo» es lo correcto. `VolcadoSinRespuesta` sería un error: dice «en duda» y lleva una
  lista de incidencias que no se han mandado.
- Lo que la spec no fija es el **código** que verá F-040 en ese caso de `volcar` (`ensayo_sin_respuesta`). Es una
  línea de contrato de §11 y de la tabla de errores de §7, y conviene que la escriba el spec-author antes de T15,
  que es quien lo traduce a HTTP.
- Nota al margen: los reintentos de la lectura (`SIGRID_REINTENTOS` × `SIGRID_TIMEOUT_S`) pueden pasar de los 45 s
  del proxy en el peor caso. Es lo que pide §8.2 («los reintentos de lectura de siempre») y no escribe nada, así
  que no lo cuento como hallazgo. El front vería un corte, y repetir es inocuo.

**(2) `VOLCADO_PARTES_POR_LLAMADA` como `int | str` (`left_to_right`).** **Desviación aceptable, y es para el
spec-author (O-B3-2).** §13 se contradecía consigo mismo y con R30: «`int`» frente a «el rango se valida en la
fábrica (503) y no al cargar los ajustes, `/health` tiene que arrancar igual», y R30 pide 503 para un `N` que no
sea entero. Con `int`, un «cinco» tumbaría la carga de los ajustes. La unión de izquierda a derecha da un entero
cuando lo es (`"12"` → 12) y deja lo demás como texto, que `validar_partes_por_llamada` rechaza con 503. Lo he
comprobado con mi M12b (solo `int`, sin la unión): **muere** con
`test_f059_r30_un_n_que_no_es_un_entero_no_impide_cargar_los_ajustes[cinco]`. Ese es también el test que faltaba
en la columna de C02 del informe. La letra de §13 tiene que decir `int | str` y por qué: es un cambio mecánico,
sin decisión que tomar.

**(3) `VolcadoDeshabilitado` envolviendo `exigir_entorno_con_cierre`.** **Correcto.** §8.2 pide la misma lista
(`dev`, `pro`), y la función la comprueba **llamando** a la del cierre, así que no hay dos listas que puedan
divergir. R16 pide «503 `volcado_deshabilitado`» si falla una de las puertas. Con el `CierreDeshabilitado` en
crudo, el código que vería F-040 sería el del cierre. Lo vigilan mis M04 y M14 (constructor sin el entorno, y
dejar subir el error del cierre), que mueren.

**(4) A09 (`json={**cuerpo, "commit": cuerpo.get("commit") is True}`).** **Coincido: no cambia el programa.** A esa
línea solo se llega desde `ensayar`, con `commit` idéntico a `False`, o desde `volcar`, con `commit` idéntico a
`True`. En los dos casos el valor que se reescribe es el que ya había, en la misma posición del diccionario (la
clave ya existe). El JSON es el mismo para cualquier entrada posible. Es la categoría de V05d; que el líder se lo
lleve al humano.

**(5) Que nada pueda mandar `commit: true` sin las tres barreras, y que ningún test toque la red.** Las barreras
son tres:
- **la fábrica**: el entorno y luego `VOLCADO_HABILITADO` (`construir_volcador`); el ensayador nunca lleva
  `escritura_habilitada=True`;
- **el adaptador**: el entorno en el constructor, y `escritura_habilitada` en `volcar`, **antes** de mirar el
  cuerpo;
- **el cuerpo**: `volcar` solo manda uno con `commit` idéntico a `True`.

Las cubren los mutantes de la herramienta 7, 8, 9, 19 y 20, los A01 a A04 y B01 a B04 del implementer, y mis M01,
M02, M03, M04, M09, M10 y M11, que mueren todos. Se cruza bien con §8.9: la clave va en `x-functions-key` y nunca en
la URL; `RUTA_PARTES_RECLAMACION` es la de §8.9; de un 400 solo se coge `details.codigo` (§8.9: «400
`{ok:false, error, details:{type, codigo}}`, nada escrito»); un 400 «Solicitud invalida.» sin código es `lote_400`
sin código, y lo resolverá la aplicación (O-B3-4). Queda un camino para saltarse la fábrica: construir
`AdaptadorVolcadoSigridApi(escritura_habilitada=True)` a mano. Esa es la guarda que tendrá que poner el test de
alcance de T16 (O-B3-3). Lo de la red está en la tabla de arriba.

### Mutantes a mano del reviewer

Incluyen el encargo pendiente del humano: `x is not None` → `x`. En las líneas nuevas son tres (N01 a N03); no hay
ningún `x is None` → `not x` que hacer aparte, porque el único `is None` es el de N03. Todos se lanzaron contra
los dos ficheros de F-059, con `-x`:

| Id | Mutación | Resultado | Test de F-059 que lo caza |
|---|---|---|---|
| N01 | `RespuestaDeLote`: datos por veracidad | muerto | `test_f059_t11_lo_que_decide_es_que_haya_datos_o_codigo_y_no_su_veracidad` |
| N02 | `RespuestaDeLote`: código por veracidad | muerto | ídem |
| N03 | `_cliente_http`: `is None` → `not` | muerto | `test_f059_t11_lo_que_decide_es_que_haya_cliente_y_no_su_veracidad` |
| M01 | `ensayar`: `is not False` → `!= False` (un `0` pasaría) | muerto | `test_f059_r6_ensayar_exige_commit_false_de_verdad[cero]` |
| M02 | `volcar`: `is not True` → `!= True` (un `1` pasaría) | muerto | `test_f059_r6_r16_volcar_exige_commit_true_de_verdad[uno]` |
| M03 | `volcar` sin la ventana | muerto | `test_f059_r16_sin_la_ventana_no_se_vuelca_y_no_se_llama` |
| M04 | Constructor sin el entorno | muerto | `test_f059_r10_r16_fuera_de_dev_y_pro_no_se_construye[True-test]` |
| **M05** | `not in CORRECTOS` → `>= 300` | **sobrevive** (también a T11) | — (C-B3-1) |
| M06 | El código de un 400 sin exigir texto | muerto | `test_f059_r14_r35_un_400_sin_codigo_de_texto_es_lote_400_sin_codigo[codigo-numero]` |
| **M07 / M15** | `truncated` con `is True` / `== True` | **sobreviven** (también a T11) | — (C-B3-2) |
| M08 | El login, con «uno o más» (`bool`) | muerto | `test_f059_r8_existe_usuario_solo_con_exactamente_uno[dos]` |
| M09 | La ventana del cierre abre el volcado | muerto | `test_f059_r37_ni_la_ventana_del_cierre_abre_el_volcado` |
| M10 | El ensayador con `escritura_habilitada` de la ventana | muerto | `test_f059_d4_el_ensayador_no_mira_la_ventana_y_no_puede_volcar[true]` |
| M11 | El volcador sin el entorno en la fábrica | muerto | `test_f059_r16_el_entorno_va_antes_que_la_ventana_y_la_configuracion[construir_volcador]` |
| M12b | `N` solo `int`, sin la unión | muerto | `test_f059_r30_un_n_que_no_es_un_entero_no_impide_cargar_los_ajustes[cinco]` |
| M13 | Solo los tiempos agotados son `sin_respuesta` | muerto | `test_f059_r21_r31_un_solo_post_tambien_ante_un_corte[conexion-volcar]` |
| M14 | Dejar subir `CierreDeshabilitado` | muerto | `test_f059_r10_r16_fuera_de_dev_y_pro_no_se_construye[True-test]` |

M12, el primer intento de M12b, murió por un `RuntimeError` de pydantic al importar (`union_mode` sobre un `int`).
Es un artefacto del mutante, y por eso lo repetí bien como M12b. Ninguno de los muertos lo caza solo una suite
vecina.

**Orden (punto 7): aplicado, con lo que hay en este bloque.** Las puertas de orden del adaptador y de las fábricas
son el entorno antes que la ventana, la ventana antes que la configuración y que el cuerpo, y la configuración
antes que `N`. Las bajan un paso B01 a B07 y A02 del implementer, y mis M03, M04 y M11, que mueren todos con tests de
F-059. Las de la aplicación (R16 antes de leer la base, R19, R20 antes de llamar a Sigrid) son del Bloque 4.

### Datos sensibles

Barrido del diff de `services/`:
- **GUID, correos, IPs:** ninguno.
- **URL:** solo `https://pasarela-inventada.invalido` y `https://ejemplo-volcado.invalido`.
- **Claves:** las inventadas de los tests (`clavedefuncioninventadaparaelvolcado`,
  `clave-de-mentira-para-el-volcado`).
- **DNI:** `00000000T`, el ficticio de todo ceros, como ruido de los 400 de prueba.
- **Ejemplos de entorno:** solo `false` y `5`.

### Checkpoints (los que cambian)

- N/A · **C1 `init.sh`**: fuera del encargo, por la regla del `.env`; T23. La suite entera está en verde.
- [x] **C3**: hexagonal (el puerto en `domain/ports/`, el adaptador en `infrastructure/sigrid/`, que **importa** de
  `cliente.py` y no copia), primeras líneas, sin `print` ni secretos. En `paso_cierre.py` (F-009) solo cambian la
  anotación y su importación (§8.4): mi lectura del diff lo confirma. Ningún número de estado de Sigrid
  (`_HTTP_DEL_LOTE` es un código HTTP).
- [x] **C4**: R6 (el `commit` explícito), R8, R10, R14, R16, R21, R22–R23 (las familias), R30, R31, R34–R37, con
  tests `test_f059_*`; ningún test toca la red.
- [x] **C4 bis · RED**: traza pegada (157 failed, 7 passed).
- [x] **C4 bis · cobertura**: 100 % de `infrastructure/sigrid/volcado.py` y de los puertos, según el informe; lo de
  F-059 en `fabrica.py` y `settings.py`, cubierto.
- [x] **C4 bis · mutación de la herramienta**: 25/25/0/0, recalculada y muestreada.
- [ ] **C4 bis · cero supervivientes, también a mano**: M05, M07 y M15 (C-B3-1, C-B3-2).
- [x] **C4 bis · «Evidencias»**: con los workers (8).
- N/A · **C4 ter**: no hay `harness/rutas_sensibles.json`.
- [x] **C5**: T10–T12 en `[x]`, con sus commits.

### Observaciones (no bloquean)

- **O-B3-1 · Para el spec-author, antes de T15.** Que §7 (la tabla de errores) y §11 digan que un login que no se
  puede verificar en `ensayo` **o en `volcar`** es `502 ensayo_sin_respuesta`, sin escribir nada.
- **O-B3-2 · Para el spec-author.** Que §13 diga `volcado_partes_por_llamada: int | str` (unión de izquierda a
  derecha), con el porqué (R30 y `/health`).
- **O-B3-3 · Para T16.** El test de alcance tiene que exigir que solo `infrastructure/sigrid/fabrica.py` construya
  `AdaptadorVolcadoSigridApi` con `escritura_habilitada=True`: es la única forma de saltarse la fábrica.
- **O-B3-4 · Para el Bloque 4.** Un `lote_400` sin código (el «Solicitud invalida.» de §8.9, «nada escrito») tiene
  que tener su camino en la aplicación: en el ensayo, 502; en el volcado, lo que se decida conforme a R23 y R24
  (`todos_no_procesados` no admite un código que no sea de lote). Siguen abiertas también O-B2-2 y O-B1-1.
- **O-B3-5 · `CORRECTOS` acepta 201 (§1) y R23 dice «no es 200».** La pasarela devuelve siempre 200 en §8.9, e
  `interpretar_respuesta` sigue exigiendo la forma completa, así que no tiene efecto práctico. Si el spec-author
  toca §11, que deje dicho que vale lo de `CORRECTOS`.

## Re-review del Bloque 3 · 2026-10-16

- **Veredicto:** **APPROVED**
- **Revisado:** `cd4b0d0` (C-B3-1 y C-B3-2, solo tests de F-059) y `74f3a94` (O-B3-1, O-B3-2, O-B3-4 y O-B3-5 en
  la spec), sobre `e7f059c`. A09 lo **aceptó por escrito el humano** (2026-10-16): queda cerrado.
- **Nivel de rigor:** `critico`.

### Las correcciones

- **C-B3-1.** `test_f059_r23_cualquier_otro_codigo_es_sin_respuesta` añade 202, 204, 301 y 302 (con un objeto
  JSON detrás) → `sin_respuesta`. `test_f059_r8_un_definitivo_no_se_reintenta` añade 202, 204 y 302 →
  `EnsayoSinRespuesta` sin reintentar. Es la misma línea de `CORRECTOS` en la lectura del login, un hueco gemelo que
  yo no había señalado y el implementer ha cerrado igual.
- **C-B3-2.** `truncated=1` y `truncated="true"` cuentan como truncado. Un test nuevo,
  `test_f059_r8_c_b3_2_una_lectura_no_truncada_si_decide`, fija el otro lado: con `False`, nulo, `0` o `""` el login
  sí se decide.
- Comparado con `e7f059c`, solo cambia `tests/test_f059_adaptador_volcado.py` (+17 −3): se amplían dos
  parametrizaciones y se añade un test, sin quitar ningún caso. **Ningún cambio en el código de producción** ni en
  ningún test ajeno.

### Los mutantes, repetidos

En un worktree desechable de `cd4b0d0` (ya retirado; el árbol de trabajo no se ha mutado y su `git status` queda
limpio), con los dos ficheros de F-059 del bloque y `-x`:

| Id | Mutación | Resultado | Test de F-059 que lo caza |
|---|---|---|---|
| M05 | El lote: `not in CORRECTOS` → `>= 300` | muerto | `test_f059_r23_cualquier_otro_codigo_es_sin_respuesta[202]` |
| M05b | La misma línea en `_leer_una_vez` (el login) | muerto | `test_f059_r8_un_definitivo_no_se_reintenta[202]` |
| M07 | `truncated` → `is True` | muerto | `test_f059_r8_una_lectura_sin_forma_o_truncada_no_decide_nada[truncada-uno]` |
| M15 | `truncated` → `== True` | muerto | `…_no_decide_nada[truncada-texto]` |
| M16 | `truncated` por presencia de la clave (`"truncated" in datos`) | muerto | `test_f059_r8_existe_usuario_lee_por_sql_read_con_el_login_como_parametro` |
| M17 | El lote: solo 200 es correcto (sin el 201) | muerto | `test_f059_r22_un_200_devuelve_los_datos_sin_interpretar[201]` |

Los seis mueren con un test de F-059: los cuatro pedidos y dos vecinos, el del otro lado de `truncated` y el de
O-B3-5.

### La enmienda de la spec (`74f3a94`)

- **O-B3-1** (§7, §11 y la nota bajo R8): un login sin verificar es 502 `ensayo_sin_respuesta` en `ensayo` y en
  `volcar`, sin escribir nada. Es lo que propuse. **Conforme.**
- **O-B3-2** (§13): `int | str` de izquierda a derecha, con el porqué (R30 y `/health`). **Conforme.**
- **O-B3-5** (§11 y la nota bajo R23): «200» se lee como `CORRECTOS`. **Conforme.**
- **O-B3-4** (§6.2, §11, la nota bajo R23 y T13): un `lote_400` sin código de lote, o con uno desconocido, va por
  R14 en el ensayo (502, sin guardar) y por R23 en el volcado (`sin_respuesta` para cada parte, `en_duda`, 502
  `volcado_sin_respuesta`). **Estoy de acuerdo en que es mecánico, y en el fondo:**
  - R23 ya cubría «no tiene la forma de §8.9», y el Bloque 1 dejó aprobada la misma regla en
    `clasificar_codigo_de_lote`: un código que no es de los de §8.9 no tiene clase, y quien llama lo trata como una
    respuesta que no se entiende.
  - R24 no puede aplicarse: `no_procesado` exige un código de motivo (el `CHECK` de §9) y de un 400 solo se guarda
    `details.codigo` (R35), que aquí no hay.
  - `en_duda` es el lado seguro. El coste está dicho en §6.2: quedan en duda hasta reintentar, y reintentar con la
    misma referencia no duplica.
  - Un matiz para el Bloque 4: un «Solicitud invalida.» (cuerpo mal formado) se repetiría en cada reintento. Como
    el cuerpo lo compone `cuerpo_de_lote`, eso sería un defecto nuestro y no un dato. Conviene que el log de ese
    camino lo deje claro (la familia y que no traía código), para que no se confunda con un corte de red.
- Datos sensibles: el diff no trae ningún GUID, correo ni IP.

### Verificación

Desde el scratchpad, sin `.env`:

| Verificación | Resultado |
|---|---|
| `test_f059_adaptador_volcado.py` + `test_f059_fabrica.py` en el worktree | **183 passed** |
| Los dos de F-059, los de F-009 y F-012 (la verificación de T11) y las dos guardias R26 de F-006 | **1078 passed in 85.00s** |
| `ruff check` del test tocado (desde la raíz) | `All checks passed!` |

No relanzo la suite entera: desde la review (8768 passed, 233 skipped) solo cambia un fichero de tests de F-059 y
la spec en Markdown.

### Checkpoints que cambian

- [x] **C4 bis · Cero supervivientes, también a mano**: M05, M05b, M07 y M15, muertos con tests de F-059; A09,
  aceptado por escrito por el humano; V05d (Bloque 2), aceptado antes.
- El resto, como en la review del Bloque 3 (los N/A, con su motivo allí).

### Observaciones que siguen abiertas (para bloques posteriores, no bloquean)

- **O-B3-3** (T16): que solo `fabrica.py` construya el adaptador con `escritura_habilitada=True`.
- **Bloque 4**: O-B2-2, O-B1-1 y el camino de O-B3-4, ya fijado en T13.
- **P-1 a P-3**: mejoras de `harness.mutacion`, pendientes del humano.

## Review del Bloque 4 (la aplicación y los tres endpoints) · 2026-10-17

- **Veredicto:** **CHANGES_REQUESTED** (1 hallazgo: C-B4-1, en la guarda de R41 de T16). Lo demás está bien hecho:
  la aplicación, el borde, el cierre de las seis observaciones y los mutantes. Los 15 equivalentes los confirmo
  yo, y quedan para que el humano los acepte por escrito.
- **Alcance revisado:** `git diff 560811b..cc49cba`, sin lo del líder (`features.json`, `BACKLOG.md`,
  `current.md`). Commits: T13 `590eb1a`, T14 `b5cc5c1`, T15 `930a5db`, T16 `1850984`, T17 `6b187a3`,
  `e8cb869`, `e7a3c64`, `bf68637`, `9db9847`, `70d611e` y `cc49cba`. Además, el arreglo de T8 que llegó
  durante la review: `324aff0`.
- **Nivel de rigor:** `critico`.

### Qué he verificado yo, y cómo

Todo desde el scratchpad, sin `.env` y sin `init.sh`. Los mutantes, en worktrees desechables, ya retirados:
`git worktree list` sin ninguno del scratchpad, y el árbol de trabajo solo con el `progress/current.md` del líder,
que no he tocado.

| Verificación | Resultado |
|---|---|
| **Suite entera del servicio** (`tests` y `tests_bbdd`), sobre `324aff0` | **9094 passed, 233 skipped in 675.90s**, las cifras del implementer |
| `ruff check` (desde la raíz) de los 4 ficheros de producción y de los 5 de tests del bloque, `test_f059_bbdd_volcado.py` incluido | `All checks passed!` |
| `tests_bbdd/tests/test_f059_bbdd_volcado.py --collect-only`, tras `324aff0` | **46 tests collected** |
| Recálculo puro (`alcance_de_feature("F-059", base="560811b")`) | 4 ficheros, **1374** líneas (719 + 196 + 6 + 453) y **66** mutantes (25 + 17 + 0 + 24). Coincide. Seis muestras (`volcado.py:160` frozen, `:339` strict, `:662`, `function_app.py:1880`, `api/volcado.py:332` y `:419`) están en la tabla del informe con el mismo operador |
| Los 15 equivalentes (13 de E-1 y 2 de E-2), contra los siete ficheros de tests de F-059 (sin el de alcance) | **Los 15 sobreviven** (831 passed con cada uno) |
| Siete mutantes de orden míos (regla 7) | 7/7 muertos por tests de F-059 |
| La guarda de R41 de T16, con un mutante de test (G1) y su control | **G1 sobrevive** (C-B4-1); el control cae |
| Datos sensibles en `560811b..HEAD` | Ningún GUID, ninguna IP; los correos son de `@ejemplo.invalid`; la única URL, `https://ejemplo-volcado-http.invalido` |

**Campaña no reejecutada: 323 min según el informe** (19405.7 s). Coste por mutante: 19405.7 × 8 ÷ 66 ≈
**2352 s**, coherente con una suite de unos 1180 s bajo carga, más los seis timeouts que se repasaron en serie. El
implementer reverificó los 66 contra los tests de F-059 solos y encontró el 49, que solo mataba una suite ajena; ya
lo cubre `70d611e`.

### Hallazgo (cambio requerido)

1. **C-B4-1 · `ASERCIONES_QUE_CAMBIAN` exime funciones enteras, y la guarda de R41 deja quitar aserciones que no
   tienen que ver con el cambio.** Está en `services/postventa-api/tests/test_f059_alcance_cerrado.py`: la tabla
   en las líneas 985 y siguientes, y la comprobación en `test_f059_r41_ningun_ampliado_pierde_una_asercion`,
   líneas 1084–1098.
   - **Qué pasa.** Para una función que está en `ASERCIONES_QUE_CAMBIAN`, la comprobación no mira **ninguna** de
     sus aserciones.
   - **Cómo lo he comprobado.** En un worktree de la rama (forzado, sin commit, ya retirado), quité
     `assert (conexion.commits, conexion.rollbacks) == (1, 0)` de
     `test_f056_repositorio_revision.py::test_f056_r4_r7_registrar_bloquea_comprueba_inserta_y_confirma`. Es una
     aserción que F-059 no cambia, pero la función está exenta. Resultado: **109 passed**, la guarda no lo ve. El
     control (quitar una aserción de `test_f056_r10_…`, que no está exenta) sí cae:
     `test_f059_r41_ningun_ampliado_pierde_una_asercion[tests/test_f056_repositorio_revision.py]`.
   - **Por qué importa.** R41, con F-1 (a), dice que cada excepción se declara «función a función en
     `test_f059_alcance_cerrado.py`, que vigila que no se pierde **ninguna** aserción», y que solo cambia «la
     cifra o el fichero vigente». Hoy hay 18 funciones exentas en 16 ficheros, y en cualquiera de ellas se podría
     relajar algo sin que salte nada. T20 añadirá más.
   - **Qué hacer.** Declarar las **aserciones** que desaparecen, no las funciones: por ejemplo
     `ASERCIONES_QUE_CAMBIAN: dict[str, dict[str, frozenset[str]]]`, con el texto normalizado de cada aserción de
     la base que se sustituye (`len(sql) == 3`, `sql[2].startswith(…)`, `nombres[-1] == FICHERO`…), y que la guarda
     exija `perdidas ⊆ declaradas` para cada función. Con un control negativo (una aserción no declarada que se
     quita → rojo), y repitiendo G1, que tiene que morir.

### Lo que el líder pidió mirar

**(1) El cierre de las seis observaciones.** Cada una tiene su test, y he comprobado que existen todos en los
ficheros que dice la tabla del informe:
- **O-B1-1**: `_decision_con_candidatas` dentro de `anotar_enviados`, con dos tests.
- **O-B1-2**: la clave `motivo` en HTTP.
- **O-B2-2**: un parte sin respuesta → 502 sin guardar **ninguno**.
- **O-B3-1**: el login sin verificar → 502 `ensayo_sin_respuesta`, en los dos endpoints.
- **O-B3-3**: por `ast`, solo `_adaptador_de_volcado` construye el adaptador, y solo `construir_volcador` pide
  `escritura_habilitada=True`.
- **O-B3-4**: con el aviso en el log.

**(2) Los 15 equivalentes.** Los he repetido todos y **coincido con los 15**. Ninguno lo caza un test de F-059.
Frases para llevar al humano:
- **H04, H15, A01 y A06** (`is None` → `not` sobre `SituacionDeRevision`, `CandidataAlVolcado`,
  `SituacionDeVolcado` y `UltimoEvento`): «son dataclasses sin `__bool__` ni `__len__`; cuando no son `None` son
  siempre verdaderas, así que las dos formas hacen lo mismo».
- **H06, H22 y H19** (`ClaseDeCodigoDeLote` y `MotivoExclusion`): «son `StrEnum` sin ningún valor vacío; cuando
  no son `None` son siempre verdaderos».
- **H08 y H24** (`resultados is None` → `not resultados`): «`interpretar_respuesta` devuelve un resultado por
  parte mandado, y a esa línea solo se llega con al menos un parte, así que la tupla nunca está vacía».
- **H25** (`fallo is not None` → `fallo`): «una excepción es siempre verdadera».
- **A10** (`volcado is None`): «`volcado_de` devuelve siempre un diccionario con cinco claves».
- **A24 y A25** (`UUID` y `datetime`): «los dos son siempre verdaderos, también `UUID(int=0)`».
- **E-2, los mutantes 16 y 24** (`zip(…, strict=True)` → `strict=False`): «partes y resultados tienen la misma
  longitud por construcción del dominio, así que `strict` no cambia nada; se queda como alarma por si un cambio
  futuro lo rompiera». Si el humano prefiere no aceptarlos, hay una alternativa barata: un test que sustituya
  `interpretar_respuesta` por una versión que devuelva un resultado de menos y exija el `ValueError`. Eso los
  mataría y además dejaría fijada la alarma.

**(3) Las formas del contrato que eligió el implementer (T15, decisiones 3 a 6).** Ninguna contradice un
requisito, y no veo ninguna que tenga que decidir el humano. Sí conviene que el spec-author las escriba en §11,
porque son lo que va a consumir F-040 (O-B4-1):
- **Los 409 del login** (`usuario_sigrid_no_mapeado` y `usuario_sigrid_inexistente`, con mensaje propio):
  **obligado por §15**. Los motivos de F-009 llevan el correo y el login, y §15 dice que el login no va en ninguna
  respuesta y el correo no va en mensajes de error. El cierre de F-009 los devuelve tal cual, y aquí no se podía
  copiar.
- **Los códigos de los 503** (`configuracion_sigrid_incompleta`, `base_de_datos_no_disponible`): §11 solo dice
  «503 entorno, configuración, base». Que todo el volcado responda `{error, codigo}` es coherente con §7.
- **`envio` es lo realmente mandado** (`cuerpo_de_parte`, con `referencia_externa` y sin la clave
  `descripcion_larga` si no hay detalle): manda R12 («los campos de R6 que se han mandado») sobre el ejemplo de
  §11. El spec-author tiene que **corregir el ejemplo**, que enseña `"descripcion_larga": null` y no lleva la
  referencia.
- **`ultimo_volcado` sin correo**: R28 no da su forma; §9 y §15 limitan el correo de quien vuelca a
  `GET /api/revision`, y F-2 (a) solo extendió eso a la respuesta de la acción. Es la lectura conservadora.
- De paso, que §11 diga también las formas de `excluidas` (`{incidencia_id, motivo, sigrid_cod}`) y de `avisos`
  (`{incidencia_id, referencia_externa, sigrid_cod_anterior, sigrid_cod}`), y que un ensayo sin nada que mandar
  devuelve `ensayo_id` y `caduca_at_utc` nulos.

**(4) O-B1-1 dentro de la transacción, y R26 leído después de la respuesta.**
- **O-B1-1.** `_decision_con_candidatas` envuelve `seleccionar_para_volcado` y se le pasa a `anotar_enviados`,
  que la llama con las filas bloqueadas (Bloque 2). La candidata se lee antes de la transacción, y es correcto:
  dentro se exige que la última revisión, con la fila bloqueada, sea la del ensayo, y que la candidata sea de esa
  misma revisión. Como la tabla es append-only, sus valores son los de esa revisión. Los partes se construyen
  después con esas mismas candidatas. La falseada no deja `enviado` (lo fija el test).
- **R26.** Leer las situaciones **después** de la respuesta y **antes** de guardar es lo que permite ver un
  `creado` de otro volcado concurrente, y si esa lectura falla es R25. Mi O8, que lee las situaciones antes de
  llamar a la pasarela, muere con `test_f059_s10_el_volcado_va_ensayo_base_login_anticipada_sigrid_y_base`, que
  fija el orden entero de las llamadas.

**(5) T16 y el grupo B de R41 con `AMPLIADOS_EN_EL_BLOQUE_5`.** El diseño es correcto. Los cinco ficheros de
documentación del grupo B están declarados con sus funciones; hasta T20 solo se exige que no cambie nada **no
declarado** (`<=`), y después, la igualdad. El grupo B de F-010 (la cuenta de 24) ya está en igualdad. Queda el
hueco de C-B4-1, que afecta también a lo que haga T20. **Para T20**: vaciar `AMPLIADOS_EN_EL_BLOQUE_5` y declarar
sus aserciones con el formato fino que pide C-B4-1 (O-B4-3).

**(6) Tests ajenos ampliados.**
- `test_f056_revision_http.py` solo añade `"volcado"` a `CLAVES_DE_FILA`, con su comentario.
- `test_f010_endpoints_protegidos.py` añade las tres rutas a `ENDPOINTS`, pone `== 24` en lugar de `== 21` (la
  cifra vigente, como pide R41) y añade un comentario.
- **Ninguna línea quitada** en ninguno de los dos, fuera de esa cifra. Ningún otro test ajeno en el diff.
- `interface_adapters/api/revision.py` gana la clave `volcado` (F-2 (a)) y el mensaje de `_filtro` con los dos
  estados. No añade ninguna importación directa de `infrastructure.sigrid`: la de `volcado_de` llega a las
  fábricas de forma transitiva, a través de `api/volcado.py`. `test_f056_r39_…` y
  `test_f060_importacion_diferida.py` siguen en verde.

**(7) El incidente de `init.sh` y el `.env`.** El `pytest` de la sección 7 bis de `init.sh` se lanza con
`cd "$RUTA"`, y `config/settings.py` declara `env_file=".env"`. Así que **cualquiera que ejecute `init.sh`**
—como mandan los protocolos del implementer y del reviewer— hace que la suite lea el `.env` del servicio. No pudo
pasar nada (la guardia `sin_red` impide abrir conexiones), pero la regla «ningún proceso lee el `.env`» y el
protocolo «ejecuta `init.sh`» chocan, y el agente que siga los dos al pie de la letra no puede. **Sí hace falta una
salvaguarda (P-4, abajo).** Mientras no esté, el encargo «sin `init.sh`» es la única defensa, y depende de que el
agente lea la nota a tiempo, que es justo lo que falló.

### Mutantes de orden (regla 7)

El orden es el requisito central del volcado (§10: puertas → base → login → escritura anticipada → Sigrid →
base). He bajado cada puerta un paso, en una copia desechable y solo con los tests de F-059:

| Id | Mutación | Resultado | Test de F-059 que la caza |
|---|---|---|---|
| O1 | `validar_ensayo` después de leer las candidatas | muerto | `test_f059_r17_un_ensayo_que_no_existe` |
| O2 | El login **después** de la escritura anticipada (R19) | muerto | `test_f059_s10_el_volcado_va_ensayo_base_login_anticipada_sigrid_y_base` |
| O3 | La pasarela con `commit: true` **antes** de la escritura anticipada (R20) | muerto | ídem |
| O5 | El login del ensayo antes de saber si queda algo que mandar | muerto | `test_f059_s10_el_ensayo_va_base_login_ensayo_y_base` |
| O6 | El volcado: la base antes que las puertas (R16) | muerto | `test_f059_r16_r37_r42_el_volcado_sin_sus_puertas_es_503_antes_de_abrir_la_base[entorno-test]` |
| O7 | El ensayo: la base antes que las puertas (R10) | muerto | `test_f059_r10_d4_el_ensayo_no_mira_la_ventana` |
| O8 | R26 leído **antes** de llamar a la pasarela | muerto | `test_f059_s10_el_volcado_va_ensayo_base_login_anticipada_sigrid_y_base` |

Los siete los caza un test **de F-059**.

### El arreglo de T8 (`324aff0`)

Solo cambia `tests_bbdd/tests/test_f059_bbdd_volcado.py`. `_resultado` acepta el parte ya construido (`_parte`), y
`test_f059_r1_la_derivacion_de_cuatro_uno_leida_de_la_base` lo captura **antes** del `creado`. El `KeyError` venía
de reconstruir el parte desde `aprobadas` cuando la incidencia ya era `volcada` y, con R3, había salido de ahí.
**Ninguna aserción cambia** (lo he leído en el diff), no hay código de producción tocado, recoge 46 casos y `ruff`
no da avisos. **Conforme.** T8 tiene que repetirla el humano con Docker.

### Checkpoints (los que cambian)

- N/A · **C1 `init.sh`**: fuera del encargo, por la regla del `.env` (ver (7) y P-4). La suite entera está en
  verde.
- [x] **C3**: hexagonal. La aplicación solo usa puertos y dominio; el borde compone las fábricas;
  `function_app.py` solo importa de `interface_adapters/api/volcado.py`. Primeras líneas, sin `print` ni secretos.
  Ningún `commit: true` sin dry-run previo de la misma persona.
- [x] **C4**: R8–R31 y R34–R35 de la aplicación y del borde, con `test_f059_*`. Sin red ni base:
  `PasarelaFalsa`, dobles de los repositorios y `sin_red`.
- [x] **C4 bis · RED**: traza pegada (169 failed, 187 passed; F-010, 2 failed).
- [x] **C4 bis · cobertura**: 100 % de la aplicación y de los dos bordes, y lo de F-059 en `function_app.py`.
- [x] **C4 bis · mutación de la herramienta**: 66/64/2, recalculada; el 49 se detectó y está resuelto.
- [x] **C4 bis · orden**: siete mutantes de orden, todos muertos por F-059.
- [ ] **C4 bis · cero supervivientes sin aceptación escrita**: los 15 equivalentes, que confirmo, siguen
  **pendientes de la aceptación del humano**. No los cuento como hallazgo para el implementer: es una decisión que
  el líder tiene que llevar.
- [ ] **C4 bis · la guarda de «no se toca» ve lo que tiene que ver**: C-B4-1.
- [x] **C5**: T13–T17 en `[x]`, con sus commits. T8, MANUAL pendiente.

### Observaciones (no bloquean)

- **O-B4-1 · Para el spec-author, antes de F-040.** Que §11 recoja las formas de (3): los dos 409 del login con
  su código, los códigos de los 503, `envio` igual a `cuerpo_de_parte` (corrigiendo el ejemplo), `ultimo_volcado`
  sin `volcado_por`, las formas de `excluidas` y `avisos`, y los nulos de un ensayo sin nada que mandar. Todo
  mecánico.
- **O-B4-2 · T8**: repetirla tras `324aff0` (46 casos de F-059).
- **O-B4-3 · Para T20**: vaciar `AMPLIADOS_EN_EL_BLOQUE_5` y declarar sus aserciones con el formato de C-B4-1.

### Propuesta de automejora (no aplicada)

- **P-4 · Que la suite no pueda leer el `.env`, para que «ejecuta `init.sh`» y «ningún proceso lee el `.env`» no
  choquen.** Tiene dos partes:
  - **En este proyecto:** un fixture de sesión en `tests/conftest.py` que anule `env_file` de `Ajustes` (por
    ejemplo, `Ajustes.model_config["env_file"] = None`, o `obtener_ajustes` con `_env_file=None` mientras corre
    pytest), con un test que lo compruebe: con un `.env` señuelo en el directorio, los ajustes no lo leen.
  - **Genérica, para `arnes-base`:** que `CHECKPOINTS.md` o `CONVENTIONS.md` exijan que ninguna suite lea secretos
    locales, y que `init.sh` (7 bis) avise si encuentra un `.env` en el directorio de un servicio sin esa
    neutralización.

  Con eso, el implementer y el reviewer podrían volver a ejecutar `init.sh` tal cual lo manda su protocolo.

## Re-review del Bloque 4 · 2026-10-17

- **Veredicto:** **APPROVED**
- **Revisado:** `b835d35..8b7790d`: `67d9c4e` (O-B4-1 en la spec), `4c8c309` y `ac5a867` (C-B4-1) y `8b7790d`
  (los mutantes 16 y 24). Ni el código de producción ni ningún test ajeno cambian; en `services/` solo cambian
  `test_f059_alcance_cerrado.py` y `test_f059_pipeline_volcado.py`.
- **Nivel de rigor:** `critico`.

### C-B4-1: corregido

`ASERCIONES_QUE_CAMBIAN` es ahora `dict[fichero, dict[función, frozenset[aserción]]]`, con el texto normalizado
(`ast.unparse`) de cada aserción de la base que se sustituye. La guarda,
`test_f059_r41_ningun_ampliado_pierde_una_asercion`, usa `_perdidas_no_declaradas`, que exige
`perdidas ⊆ declaradas` con multiplicidad (`Counter`): declarar una aserción permite perderla **una** vez. Añade
además:
- `test_f059_r41_c_b4_1_lo_declarado_es_lo_que_se_pierde`: no se puede declarar de más, que sería una puerta
  abierta para relajar después;
- `test_f059_r41_c_b4_1_quitar_una_asercion_no_declarada_da_rojo`: un control negativo sobre el fichero de verdad,
  con mi G1.

Lo he comprobado en un worktree de la rama (forzado, sin commit, ya retirado; `git status` limpio al terminar):

| Prueba | Resultado |
|---|---|
| La guarda, sin tocar nada | 67 passed (los `test_f059_r41*`) |
| **G1**: quitar `(conexion.commits, conexion.rollbacks) == (1, 0)` de `test_f056_r4_r7_…`, que tiene aserciones declaradas | **muerto**: `test_f059_r41_ningun_ampliado_pierde_una_asercion[tests/test_f056_repositorio_revision.py]` (y los dos nuevos) |
| **Control**: quitar una aserción de `test_f056_r10_…`, que no está declarada | **rojo** |
| **G2**: declarar de más (añadir a la tabla una aserción que sigue en el fichero) | **rojo**: `test_f059_r41_c_b4_1_lo_declarado_es_lo_que_se_pierde` |

He contrastado la tabla con los diffs de la review del Bloque 2: las aserciones declaradas son exactamente las
que cambiaron de cifra o de posición. **Conforme.** O-B4-3 sigue en pie: T20 vacía `AMPLIADOS_EN_EL_BLOQUE_5` y
declara las suyas con este formato.

### Los equivalentes, según lo que decidió el humano (2026-10-17, por escrito)

- **E-1, los 13 (H04, H06, H08, H15, H19, H22, H24, H25, A01, A06, A10, A24 y A25): aceptados por el humano.
  Cerrado.**
- **E-2, los mutantes 16 y 24: no aceptados.** `8b7790d` añade dos tests de F-059:
  `test_f059_t17_m16_el_ensayo_no_empareja_mal_un_parte_con_su_resultado` y
  `test_f059_t17_m24_el_volcado_no_empareja_mal_un_parte_con_su_resultado`. Sustituyen `interpretar_respuesta` por
  una que devuelve un resultado de menos, anulan el guardado (para que no salte antes `_exigir_que_casen`) y exigen
  el `ValueError` del `zip(..., strict=True)`. Repetidos en una copia desechable de `8b7790d`, con **solo** los
  tests de F-059:

| Mutante | Resultado | Test de F-059 que lo caza |
|---|---|---|
| 16 · `volcado.py:339` `strict=True` → `False` (ensayo) | **muerto** | `test_f059_t17_m16_el_ensayo_no_empareja_mal_un_parte_con_su_resultado` |
| 24 · `volcado.py:479` `strict=True` → `False` (volcado) | **muerto** | `test_f059_t17_m24_el_volcado_no_empareja_mal_un_parte_con_su_resultado` |

### O-B4-1 en la spec (`67d9c4e`): §11 coincide con lo implementado

Lo he cotejado contra `interface_adapters/api/volcado.py` y `CODIGOS_DEL_VOLCADO` y `HTTP_DEL_VOLCADO` de
`function_app.py`:
- **Los errores por ruta**, con su código y sus claves propias (`motivo`, `codigo_pasarela`, `en_duda` y
  `total`).
- **Los 409 del login**, con mensaje propio y sin el correo ni el login, por §15.
- **Los 503**, con `volcado_deshabilitado` para el entorno o la ventana, y `base_de_datos_no_disponible` también
  cuando la configuración de la base está incompleta.
- **`envio` = `cuerpo_de_parte`**, con el ejemplo corregido: la referencia está y no hay `descripcion_larga` sin
  detalle.
- **Los nulos de un ensayo sin nada que mandar.**
- **Las formas de `excluidas`, `avisos` y el panel**, con `ultimo_volcado` sin `volcado_por`.

Todo coincide. El registro va en §20 como mecánico. **Conforme.**

### Las demás

- **O-B4-2 (repetir T8): cerrado.** El líder la repitió sobre `324aff0` contra PostgreSQL efímera en Docker:
  **104 passed in 56.94s**.
- **P-4: no bloquea.** El humano lo deja como encargo pendiente en
  `arnes-base/ENCARGO_pendiente_la_suite_no_lee_el_env.md` (`d66f897`).

### Verificación

Desde el scratchpad, sin `.env` ni `init.sh`:

| Verificación | Resultado |
|---|---|
| Todos los `test_f059_*.py` (con el de alcance) y las guardias de F-006 y F-005 | **1030 passed in 110.45s** |
| `ruff check` de los dos tests tocados (desde la raíz) | `All checks passed!` |
| GUID en el diff | ninguno |

No relanzo la suite entera: desde la review (9094 passed) solo cambian dos ficheros de tests de F-059, y los he
ejecutado completos. El resto es spec e informes en Markdown.

### Checkpoints que cambian

- [x] **C4 bis · cero supervivientes sin aceptación escrita**: los 13 de E-1, aceptados por el humano; 16 y 24,
  muertos con tests de F-059; V05d y A09, aceptados antes.
- [x] **C4 bis · la guarda de «no se toca» ve lo que tiene que ver**: C-B4-1 corregido, con G1, el control y G2
  comprobados.
- [x] **C4 · MANUAL**: T8 en verde (104 passed, el líder, sobre `324aff0`).
- El resto, como en la review del Bloque 4.

## Review final (Bloque 5 y la feature entera) · 2026-10-17

- **Veredicto:** **CHANGES_REQUESTED** (2 hallazgos: C-F-1 para el implementer y C-F-2 para el líder).
- **Todavía NO es «apta para desplegar».** El código, los tests, la infra y la documentación están bien, y no veo
  ningún riesgo de escritura en el ERP. Lo que falta:
  - **C-F-1**: un checkpoint de C4 bis que la guarda de alcance de F-059 no cumple.
  - **C-F-2**: los pasos MANUAL del Bloque 6 no están en `progress/current.md` con su comando exacto.

  Corregidas las dos, la re-review será corta, y su APPROVED sí será «apta para desplegar» (T24).
- **Alcance revisado:** el Bloque 5, `8b7790d..0ea5fef` (T18 `2a198f7`/`42a2d9d`, T19 `c4874ea`/`1d7a1ed`, T20
  `a623bea`, T21 `de6d415` y `8f9a8a8` en `azure-apps`, T22 `44fcd21`/`43fb673`, T23 `0ea5fef`), y la feature
  entera desde `2d2efd7` contra `CHECKPOINTS.md`.
- **Nivel de rigor:** `critico`.

### Qué he verificado yo, y cómo

Todo desde el scratchpad, sin `.env` y sin `init.sh`. Los mutantes, en worktrees desechables, ya retirados:
`git worktree list` sin ninguno del scratchpad, y el árbol de trabajo solo con el `progress/current.md` del líder.

| Verificación | Resultado |
|---|---|
| Los tests del Bloque 5 y los vecinos: `test_f059_scripts_infra.py`, `test_f059_documentacion.py`, `test_f059_alcance_cerrado.py`, los cinco de documentación del grupo B, `test_f010_scripts_infra.py`, `test_f010_prompt_keys_infra.py`, `test_f012_scripts_infra.py`, `test_f051_scripts_infra.py` y las dos guardias de F-006 | **709 passed, 3 skipped in 99.25s** |
| T23 (el líder; no la repito) | `init.sh` sobre `a2ab36b`: 9199 passed, 233 skipped, PUERTA COBERTURA 100,0 % de 1122 líneas, ENTORNO LISTO. Desde `a2ab36b` solo cambia `tasks.md` (`0ea5fef`) |
| T8 (el líder) | 104 passed, sobre `324aff0`. Desde entonces, ningún cambio de producción |
| **T22, opción B**: cambios de producción desde `9db9847` | **Ninguno** (`git diff --name-only 9db9847 HEAD -- services/`, sin tests: vacío) |
| **T22, opción B**: la comparación mutante a mutante, recalculada por mí | Campaña entera (`2d2efd7..HEAD`): **203**. Bloques: 85 + 26 + 25 + 66 = 202, cada uno calculado sobre el commit de su campaña. **201 de 203 idénticos**, con la misma clave del informe (fichero, texto de la línea, columna, operador, original → mutado). Los **2** sin gemelo son los de `_con_texto` (`domain/models/volcado.py:364`). Y el único de los bloques sin gemelo en la final es `if ensayo.actor_oid != actor_oid:`, la línea que quitó B-1 (a). Coincide con `progress/mutacion_F-059.md` |
| **T22**: los 2 de `_con_texto`, sobre `HEAD`, con los tests de F-059 solos | **los 2 muertos**: `or` → `and`, por `test_f059_s10_el_ensayo_va_base_login_ensayo_y_base`; quitar el `not`, por `test_f059_r6_el_parte_clave_a_clave` |
| **T22**: muestra aleatoria (semilla fija) de 10 de los 201, sobre `HEAD` y contra los tests de F-059 | **10/10 muertos** por tests de F-059. Dos de ellos (`repositorio_revision_pg.py:236` y `:238`) los matan los `test_f059_*` que viven en `test_f056_repositorio_revision.py` |
| Los `.ps1` nuevos y `desplegar_backend.ps1` | ASCII, sin BOM, CRLF (como `19_ventana_escritura.ps1`) |
| Datos sensibles en `2d2efd7..HEAD` y en `8f9a8a8` de `azure-apps` | Ningún GUID ni IP. Los correos son todos de `.invalid`, y las URL, de `.invalido` |
| Ficheros binarios u ofimática añadidos en la feature | Ninguno |

### Hallazgos (cambios requeridos)

1. **C-F-1 (implementer) · La guarda de piezas de T16 no ve lo que no es una definición.** Está en
   `services/postventa-api/tests/test_f059_alcance_cerrado.py`, en `_definiciones`, líneas 174–196 («Los `import` no
   cuentan»), y en `test_f059_s12_en_cada_fichero_tocado_solo_cambia_lo_declarado`, líneas 396–409.
   - **Lo que exige el checkpoint.** El de C4 bis aprobado por el humano el 2026-10-14 (F-060, Bloque 7) dice que una
     guarda por definiciones tiene que ver también las importaciones y las sentencias de módulo, con su control no
     ciego. Es lo que hace `_resto_del_modulo` en `test_f060_alcance_cerrado.py`.
   - **Lo que he comprobado.** En un worktree forzado de la rama, sin commit y ya retirado:
     - **G5**: añadir al final de `domain/models/revision.py` `_PERMITIDAS[EstadoRevision.DESCARTADA] = ()`. Es una
       sentencia de módulo que cambia F-056, porque una `descartada` deja de poder recuperarse. La guarda lo deja
       pasar (130 passed). Solo lo cazan los tests de comportamiento de F-056.
     - **G6**: añadir un `import` a `repositorio_revision_pg.py`. 130 passed.
     - **G3**: registrar una ruta anónima nueva con una sentencia de módulo
       (`app.route(route="volcado/otra", …)(volcado)`). La guarda y `test_f010_endpoints_protegidos.py` la dejan
       pasar (130 y 8 passed). Esta vez cae por casualidad en los tests HTTP, al importar `function_app`.
   - **Qué hacer.** Para cada fichero de `PIEZAS_DE_F059`, comparar con la base lo que queda fuera de
     `_definiciones`: las importaciones y las sentencias de módulo (`Expr`, `If`, asignaciones a algo que no es un
     nombre…), y exigir que no cambie nada salvo lo **declarado**. Lo declarado son las importaciones que F-059 añade
     en cada fichero (las de `situacion_volcado`, `sentencias_volcado`, `volcado_de`, los errores y el
     `from interface_adapters.api.volcado import …` de `function_app.py`, …), escritas a mano como en
     `PIEZAS_DE_F059`. Con su control negativo, y repitiendo G3, G5 y G6, que tienen que morir.
2. **C-F-2 (líder) · Los pasos MANUAL que faltan no están en `progress/current.md` con su comando exacto.** C4 lo
   pide para que el humano pueda ejecutarlos. Hoy `current.md` solo dice «luego el Bloque 6 manual (T24 desplegar
   con la ventana cerrada)». **Qué hacer:** listar ahí T24, T25, T26 y T27 como pendientes del humano, con los
   comandos de `tasks.md`, Bloque 6:
   - `git worktree add --detach ..\postventa-publicar dev`;
   - `desplegar_backend.ps1` y `27_ventana_volcado.ps1` desde ese worktree;
   - `28_volcado_lectura_sigrid.ps1 -CodigoObra 0626` para las fotos, y con `-Referencia PVI-<id>` la de después;
   - `27_ventana_volcado.ps1 -Abrir` / `-Cerrar`;
   - la anulación desde la UI.

   Con la autorización expresa para **una** escritura como precondición de T25.

### Lo que el implementer pidió mirar (Bloque 5)

- **La codificación de los `.ps1` (ASCII sin BOM frente al «UTF-8 con BOM» de T18): desviación aceptable.**
  `test_f010_prompt_keys_infra.py` lee **todos** los `.ps1` como `ascii`, así que un BOM tumbaría la recolección, y
  tocar ese test no está en las excepciones de R41. Un fichero ASCII ya es UTF-8 válido, y es lo que hacen ya
  `19_ventana_escritura.ps1` y los scripts de F-013 y F-036. La excepción, eso sí, solo está escrita en las
  cabeceras de los tests, y `docs/CONVENTIONS.md` dice «UTF-8 con BOM (salvo excepciones documentadas)» sin
  documentarla (O-F-1).
- **La cabecera de F-060: conforme con R41** (F-1 (a), cuyo texto dice «una cabecera bien formada que no
  retroceda, con F-060 y su despliegue constando»). El test exige una sola fecha y una sola última feature, una
  fecha ≥ 2026-10-14, «F-060» en la cabecera, los textos del despliegue de F-060, que siguen intactos en su bucle,
  y «sin desplegar» fuera. Que «no retroceder» se mida por la fecha y no por el número de feature es correcto:
  F-059 toca el documento después que F-060. Las dos aserciones exactas que se quitan están declaradas, con el
  formato fino, en `ASERCIONES_QUE_CAMBIAN`, y la guarda de R41 lo vigila.
- **`28_volcado_lectura_sigrid.ps1`: solo `sql/read`, y no lee ni nombres, ni propietarios, ni personas.** Va por
  `08_lectura_sigrid_comun.ps1` (`Invoke-SigridLectura`, solo `POST /api/sql/read`). Sus seis `SELECT` leen solo
  `ide` y `cod` de la obra, el `MAX(cod)` de la serie, y de cada parte el `cod`, el código de estado (por `conest`,
  sin ningún número de estado fijo), los de tipo y oficio, `LEN(resubi)`, el número de intervinientes y causantes,
  si la UPV es de la obra y la referencia `PVI-`. Ni descripciones, ni `rcp.tex`, ni propietario, ni persona, ni
  nombres. Cumple R39. Hay una nota en O-F-2.
- **`27_ventana_volcado.ps1` y `desplegar_backend.ps1`: conformes con R38 y D-3.**
  - Sin parámetros, `27_` solo lee; `-Abrir` avisa y pide `ABRIR` antes de escribir; `-Cerrar` no pregunta; y tras
    escribir vuelve a leer. Una App Setting ausente cuenta como cerrada.
  - `desplegar_backend.ps1` fija `"VOLCADO_HABILITADO=false"` con el literal y en su propia línea, con y sin
    `-VentanasCerradas`, junto con `VOLCADO_PARTES_POR_LLAMADA=5`, y lo enseña antes de pedir `DESPLEGAR`.
- **La documentación (R40)**: la frase «Posventa lo pasa a PTE a mano» está en los cuatro documento: en
  `ARCHITECTURE.md`, `INTEGRACION.md` y `DESPLIEGUE.md` (partida en dos líneas), y en `azure-apps`. Con ella, la
  referencia `PVI-` en `RCPCLI`, el tipo `0002`, la anulación por la UI (NO PROCEDE, nunca `DELETE`),
  `VOLCADO_HABILITADO` y «Los veinticuatro quedan en nivel». La cabecera de `INTEGRACION.md` dice «no está
  desplegada». `azure-apps` va en un commit **local** (`8f9a8a8`, solo `postventa_incidencias.md`, sin push), y la
  fila de consumidores de `sigrid_api.md` §10 queda para el líder en T24 (Q-6). **Conforme.**
- **El grupo B de R41 (O-B4-3): cerrado.** `AMPLIADOS_EN_EL_BLOQUE_5` está vacío y lo exige un test; los cinco
  ficheros pasan a igualdad. Sus diffs solo añaden la cifra vigente en `in`, la anterior en `not in`, y las
  aserciones exactas que se sustituyen, declaradas una a una. La guarda de R41, con el formato de C-B4-1, pasa sobre
  el árbol real.

### T22 por la opción B: verificada

La decisión del humano (2026-10-17, por escrito) se cumple tal como está escrita. No hay producción nueva desde la
última campaña de bloque, la equivalencia de mutantes se sostiene (la he recalculado por mi cuenta) y los dos sin
gemelo mueren. La muestra de 10 sobre el código actual mueren todos con tests de F-059, así que la reutilización de
veredictos de bloque está respaldada también con los tests de hoy. **Conforme.**

### La feature entera contra `CHECKPOINTS.md`

**C1**
- [x] `init.sh` termina con exit 0: T23, el líder, sobre `a2ab36b`, «ENTORNO LISTO».
- [x] Están los ficheros del arnés.

**C2**
- [x] Una sola `in_progress` (F-059).
- [x] La rama es la de la feature.
- N/A · `current.md` solo con la sesión activa: F-059 no se cierra hasta T27, y es entonces cuando el líder pasa
  lo cerrado a `history.md`. Hoy arrastra sesiones de otras features, y conviene podarlo en T27.
- N/A · El resumen en `history.md`: la feature no es `done` (T27).

**C3**
- [x] Hexagonal: el dominio, puro; los puertos, en `domain/ports/`; los adaptadores, en `infrastructure/`;
  `function_app.py`, solo con el borde.
- [x] Primeras líneas con su ruta.
- [x] Sin `print`, sin secretos y sin dependencias nuevas.
- [x] La unidad es el parte: uno por incidencia, con su referencia `PVI-`.
- [x] **Ningún `commit` contra Sigrid sin dry-run ni confirmación**, con tres barreras:
  - un ensayo guardado de la misma persona y obra, de menos de 30 min, del que solo se vuelca lo `previsto`
    (R17, R18);
  - `confirmado: true` de JSON (R15);
  - la ventana propia, que se despliega cerrada, comprobada en la fábrica, en el adaptador y en el cuerpo
    (`commit is True`).
- N/A · Manuscrito y «firmado no es conforme»: la feature no toca partes escaneados.
- [x] **Reprocesar no duplica**: la referencia `PVI-<uuid>` da la idempotencia en `sigrid-api`, con la escritura
  anticipada y `en_duda`.
- [x] Ningún número de estado de Sigrid fijo: el parte nace en el estado inicial de la serie (lo resuelve
  `sigrid-api`), y el `28_` lee el código por `conest`. El `"0002"` es el **tipo**, que decidió el humano (Q-1).
- [x] Ningún escaneado ni PDF en el historial de la rama.

**C3 bis**
- N/A · La feature no toca `docs/referencia/`.

**C4**
- [x] Cada requisito tiene tests `test_f059_*`, todos en verde: R1–R42. R43 es MANUAL (T25).
- [x] Los unit tests no tocan red ni base: dobles, `sin_red`, y los de base en `tests_bbdd`, contra la efímera
  (T8).
- [ ] **Las MANUAL pendientes, en `current.md` con su comando exacto: C-F-2.**

**C4 bis**
- [x] `rigor: critico`.
- [x] Fase RED en cada bloque, con la traza pegada.
- [x] Cobertura: la puerta de `init.sh`, al 100,0 %.
- [x] Mutación: cuatro campañas de bloque recalculadas y reverificadas por muestreo, y T22 por la opción B,
  verificada.
- [x] Los muertos, comprobados.
- [x] Cero supervivientes sin aceptación: V05d, A09 y los 13 de E-1, aceptados por escrito por el humano; 16 y 24,
  muertos.
- [x] «Evidencias» en cada bloque.
- [ ] **La guarda por definiciones ve lo que no es una definición: C-F-1.**
- [x] Ningún N/A sin motivo.

**C4 ter**
- N/A · El repositorio no declara `harness/rutas_sensibles.json`.

**C5**
- [x] T0–T23 en `[x]`, con sus commits.
- N/A · T24–T27 son MANUAL o de cierre, y T24 tiene como precondición **esta** review aprobada, así que no pueden
  estar hechas antes.
- [x] Sin artefactos sin seguimiento.
- [x] `features.json`: F-059 `in_progress`, que es su estado real.

### Observaciones (no bloquean)

- **O-F-1 · `docs/CONVENTIONS.md`.** Escribir la excepción de `infra/`: ASCII sin BOM y CRLF, porque
  `test_f010_prompt_keys_infra.py` lee los `.ps1` como `ascii`. Hoy solo la explican las cabeceras de los tests de
  F-013, F-036 y F-059. Si vale para cualquier proyecto con esa guarda, se porta a `arnes-base`.
- **O-F-2 · El `MAX(cod)` del `28_` no filtra por `emp`.** Si la serie `RS<aa>.<mm>/` la comparten varias
  empresas, la foto de antes y después de T25 podría moverse por un alta de otra empresa. En el guion de T25, que
  el humano compare además el `cod` del parte creado con el `MAX(cod)` de después. La comprobación que vale, «1
  parte con esa referencia, de la UPV elegida», no depende de esto.
- **O-F-3 · Para T27.** Podar `progress/current.md` (pasar lo cerrado a `history.md`) y volver a lanzar
  `init.sh`.

## Re-review final · 2026-10-17

- **Veredicto:** **APPROVED**. **F-059 es apta para desplegar (T24).**
- **Revisado:** `cd57620` (C-F-2, el líder), `1e620de` (C-F-1, el implementer) y `3ecbbea` (las cifras del
  informe), sobre `2277707`.
- **Nivel de rigor:** `critico`.

### C-F-1: corregido

`test_f059_alcance_cerrado.py` añade lo que faltaba para cada fichero de `PIEZAS_DE_F059`:
- `IMPORTACIONES_DE_F059`: las importaciones que F-059 añade en cada fichero, escritas a mano como
  `(módulo, nombre, alias)`;
- `_importaciones`: nombre a nombre, con `Counter`;
- `_es_definicion`: una asignación a algo que no es un nombre no cuenta como definición, con el criterio de F-060;
- `_resto_del_modulo`.

Y cinco tests nuevos:
- que se declare cada fichero tocado;
- que solo se ganen las importaciones declaradas y no se pierda ninguna;
- que el resto del módulo quede igual que en la base;
- que lo declarado esté importado de verdad;
- y un control negativo compuesto en memoria, que ve G3, G5 y G6 y además un `if`, un `try`, un desempaquetado, un
  atributo, un nombre añadido a una línea `from` que ya estaba y un alias. No ve, como debe, ni las definiciones, ni
  los docstrings, ni el formato.

Repetido en un worktree forzado de la rama, sin commit y ya retirado; `git status` limpio al terminar:

| Prueba | Resultado |
|---|---|
| La guarda, sin tocar nada | **165 passed** (el control negativo, incluido) |
| **G3**: una ruta anónima registrada con una sentencia de módulo en `function_app.py` | **muerto**: `test_f059_c_f_1_el_resto_del_modulo_de_cada_fichero_tocado_no_cambia[function_app.py]` |
| **G5**: `_PERMITIDAS[EstadoRevision.DESCARTADA] = ()` en `domain/models/revision.py` | **muerto**: `…_el_resto_del_modulo_…[domain/models/revision.py]` |
| **G6**: `import os` en `repositorio_revision_pg.py` | **muerto**: `…_cada_fichero_tocado_solo_gana_las_importaciones_declaradas[infrastructure/persistencia/repositorio_revision_pg.py]` |
| **G7** (mío, aparte): `Mapping` importado de `typing` en vez de `collections.abc` en ese mismo fichero | **muerto**: el mismo test |

`ruff check` del fichero, desde la raíz: `All checks passed!` **Conforme**, y el checkpoint de C4 bis («la guarda
por definiciones ve también lo que no es una definición, con su control no ciego») pasa a `[x]`.

### C-F-2: hecho

`progress/current.md` tiene ahora «F-059 · Pendientes MANUAL del humano (Bloque 6 de `tasks.md`)». La
precondición es esta review aprobada y «apta para desplegar». Los pasos:
- **T24**: los cuatro comandos del worktree de publicación, **idénticos** a los de `tasks.md`, y que el tercero tiene
  que decir «cerrada».
- **T25**: la autorización expresa para una sola escritura, en la 0626, y los siete pasos con sus comandos (`28_`
  antes y después, `27_ -Abrir` y `-Cerrar` enseguida). **O-F-2 está dentro, en el paso 5**: comparar el `cod`
  del parte con el `MAX(cod)`.
- **T26**: `-Cerrar`, la anulación desde la UI (NO PROCEDE, nunca `DELETE` ni `sql/write`) y la comprobación con
  `28_`.
- **T27**: con O-F-3.

Los comandos coinciden con el Bloque 6 de `tasks.md`; aquí llevan además el prefijo
`powershell -ExecutionPolicy Bypass -File`. **Conforme.**

Hay un matiz, que no bloquea: el resumen de `current.md` abrevia algunas comprobaciones de `tasks.md`, que remite
como detalle. Por ejemplo:
- en T25.3, que el ensayo con la ventana cerrada da 200 con un `previsto` y el `envio` esperado;
- en T25.5, que el `MAX(cod)` avanzó en uno;
- en T26, los demás `PVI-` de la prueba y la vuelta al commit anterior con `-VentanasCerradas` si el defecto es
  del código.

**Durante T25 y T26 el guion que manda es el de `tasks.md`**, que el propio `current.md` cita.

### Sin cambios de producción desde T23

Desde `a2ab36b`, el commit sobre el que el líder lanzó T23, solo cambian:
- `services/postventa-api/tests/test_f059_alcance_cerrado.py` (C-F-1);
- `progress/current.md`, `progress/impl_F-059.md` y `progress/review_F-059.md`;
- y la marca de T23 en `tasks.md`.

**Ningún fichero de producción, ni de `infra/`, ni de `docs/`.** No hace falta repetir `init.sh` antes de desplegar:
el código que se publica es el que midió T23 (9199 passed, cobertura al 100,0 %). El único test nuevo pasa entero
(165 passed). T27 lo volverá a lanzar.

### Checkpoints que cambian respecto a la review final

- [x] **C4 · Las MANUAL pendientes, en `current.md` con su comando exacto**: C-F-2.
- [x] **C4 bis · La guarda por definiciones ve lo que no es una definición**: C-F-1.
- El resto, como en la review final: todos `[x]` o N/A justificados. T24–T27 quedan MANUAL o de cierre, y T24 tiene
  como precondición este APPROVED.

### Para el despliegue y lo que queda

- **Apta para desplegar (T24)**: merge a `dev` y publicación desde un worktree limpio de `dev`, con la ventana
  **cerrada**, que el `27_` sin parámetros tiene que confirmar.
- **T25 solo con la autorización expresa del humano para una escritura**, en la 0626, y la ventana cerrada
  enseguida.
- Siguen en pie las observaciones O-F-1 (la excepción ASCII de `infra/` en `CONVENTIONS.md`) y O-F-3 (podar
  `current.md` en T27), y las propuestas P-1 a P-4, que son del humano.
