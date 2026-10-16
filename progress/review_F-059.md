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
  `00000000-0000-0000-0000-000000abcdef` (dos `assert` de R5) y `00000000-0000-0000-0000-000000000001` (el id de un
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
