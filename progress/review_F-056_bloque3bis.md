<!-- progress/review_F-056_bloque3bis.md -->
# F-056 · Review del Bloque 3 bis (la lectura de ubicaciones válidas)

- **Veredicto:** **APPROVED.** No hay bloqueantes. Hay dos hallazgos menores (N-1 es una frase de la spec que se
  ha quedado vieja; N-2 es una línea en blanco que falta) y unas observaciones. Ninguno pide tocar la lógica.
- **Fecha:** 2026-10-08 · reviewer
- **Rama:** `feature/F-056-revision-bandeja-backend`, HEAD `e5971fe`. Base de la feature `f86d639`; base del bloque
  `c22e692`.
- **Alcance revisado:**
  - T14a–T14c (`846b844`, `89e1a9f`, `4a65bcc`, `e5971fe`);
  - O-2 (`b05abce`), N-1 (`498be0d`) y N-2 (`6e9d02d`) de `progress/review_F-056_bloque3.md`;
  - los tres módulos nuevos, el añadido a `infrastructure/sigrid/fabrica.py`, el diff de
    `application/pipelines/revision.py` y de `interface_adapters/api/revision.py`;
  - `test_f056_ubicaciones.py` (nuevo) y los diffs de `test_f056_revision_http.py` y `test_f056_alcance_cerrado.py`;
  - R11, design §9, §16 y `tasks.md`.

## Nivel de rigor

El nivel es `critico`, declarado en `harness/features.json`. Exige:
- la fase RED con la traza pegada;
- cobertura de lo cambiado ≥ 80 %;
- mutación con **cero supervivientes**, salvo justificación que acepte el humano;
- la regla de orden (punto 7 / RM7).

El encargo amplía RM7 a la puerta de «validar antes de construir»: subir a mano un `construir_ubicaciones_validas`
por encima de la validación, y meterlo en descartar, recuperar y el historial, tiene que poner la suite en rojo.

## Lo que se ha ejecutado (resultados reales)

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` | **ENTORNO LISTO**, exit 0. `PUERTA COBERTURA: [OK] 100.0% de 1060 líneas cambiadas cubiertas (1060/1060, umbral 80%, nivel critico)`. Los servicios api y front salieron en verde **por caché**. ruff: 73 avisos de deuda previa. Arnés: 115 passed |
| Sin caché (`-p no:cacheprovider`), desde `services/postventa-api`: todos los `test_f056_*.py` y `test_f006_repo_sin_identificadores.py` | **940 passed**, 0 failed, 0 skipped, en 37,9 s |
| `ruff check` (desde la raíz) de los 6 ficheros de producción y los 3 de tests del bloque | **All checks passed** |
| RED de T14a reproducido: `git archive 846b844` en el scratchpad y `pytest tests/test_f056_ubicaciones.py` | **76 failed, 15 passed**, igual que el informe. **0** `ImportError`, `AttributeError`, `KeyError`, `TypeError` o `NameError`: todos son fallos de aserción o `DID NOT RAISE` |
| Recálculo puro: `harness.alcance.alcance_de_feature('F-056', base='c22e692')` + `harness.mutacion.generar_mutantes` | **6 ficheros, 341 líneas, 10 mutantes**. Por fichero: puerto 2, consultas 4, adaptador 4; aplicación, fábrica y borde 0. Por operador: booleano 2, entero 2, `not` 2, lógico 2, comparación 1, aritmético 1. **Coincide** con el informe. Los dos repasados en serie que cita el informe (`ubicaciones_validas.py:78 [entero] sum(1…)→sum(2…)` y `ubicaciones_validas.py:50 [booleano] field(repr=False)→field(repr=True)`) existen en la lista con ese operador y ese texto |
| Campaña de mutación | **No se ha reejecutado: 63 min según el informe (3763,6 s), más de 5 min.** El encargo también pide no relanzarla. Me quedo en el recálculo puro, en 4 mutantes de la herramienta reejecutados a mano y en 25 mutantes propios (abajo). Coste por mutante: 3763,6 × 8 / 10 ≈ **3011 s**, del orden de la suite en serie (770 s) con 8 workers compitiendo y dos mutantes en timeout. **No es sospechosa**: está muy por encima de un segundo y del tiempo de la suite |
| Cero mutantes en aplicación, fábrica y borde | No es un cero de campaña: son 0 de 10 mutantes, no 0 en total. Lo cubro con 25 mutantes a mano. Esas líneas no tienen comparaciones, operadores ni constantes; `if lectura.llego_al_techo:` no lo muta ningún operador de la herramienta |
| `git status` al terminar | limpio. Todo se hizo en copias desechables del scratchpad (`git archive HEAD` en `copia/`, y `846b844` en `red/`). Cada mutante se deshizo tras su ejecución |

### RM7 · «validar antes de construir» y el orden de las lecturas: 13 mutaciones de orden a mano

Todas sobre `copia/`, con los tests de F-056: `test_f056_ubicaciones.py`, `…_revision_http.py`,
`…_pipeline_revision.py` y `…_alcance_cerrado.py`. Primero con `-x`, y después **solo con
`test_f056_ubicaciones.py`** (los tests del bloque).

| # | Mutación | F-056 | Solo `test_f056_ubicaciones.py` |
|---|---|---|---|
| M1 | `construir_ubicaciones_validas(obtener_ajustes())` **por encima de `_peticion(cuerpo)`** en `accion_de_revision` | **rojo** (86 failed sin `-x`; entre ellos los 51 de `test_f056_r5_cuerpo_invalido_es_400_sin_construir_nada`, por `nada_se_construye`) | **rojo** (`…r46_sin_cache_entre_peticiones`, `…r46_descartar_recuperar_e_historial_no_leen_ubicaciones`) |
| M2 | Lo mismo, tras validar pero **sin mirar la acción** (descartar y recuperar también la construyen) | **rojo** (35 failed) | **rojo** (`…r46_descartar_recuperar_e_historial_no_leen_ubicaciones`) |
| M3 | `construir_ubicaciones_validas(obtener_ajustes())` **por encima de `PeticionDeListado(`** en `listar_revision` | **rojo** (65 failed; entre ellos `…r23_parametros_invalidos_son_400_sin_consultar`, `…r23_sin_obra_es_400`, `…r25_un_cursor_manipulado_es_400_sin_consultar`, `…r23_o3_…`: 35 de 35) | **rojo** (`…r46_sin_cache_entre_peticiones`) |
| M4 | `construir_ubicaciones_validas(...)` **por encima de `_uuid`** en `historial_revision` | **rojo** | **rojo** (`…r46_descartar_recuperar_e_historial_no_leen_ubicaciones`) |
| M5 | Lo mismo, **tras `_uuid`** (un historial válido la construye) | **rojo** | **rojo** (ídem) |
| M6 | En listar, la fuente **por debajo de `construir_revision`** | **rojo** | **rojo** (`…r46_sin_configuracion_de_sigrid_es_503_antes_de_la_base`) |
| M7 | En la acción, la fuente **por debajo de `construir_revision`** | **rojo** | **rojo** (ídem) |
| M8 | `construir_fuente_de_ubicaciones` **perezosa** (construye al primer uso, ya tras la base) | **rojo** | **rojo** (`…r46_el_borde_compone_la_lectura_de_sigrid`) |
| M9 | **Caché** de la fuente entre peticiones (global de módulo) | **rojo** | **rojo** (`…r28_el_listado_ofrece_el_mapa_leido_una_lectura_por_peticion`) |
| M10 | Fábrica: **configuración antes que entorno** | **rojo** | **rojo** (`…r46_la_fabrica_se_niega_fuera_de_dev_y_pro_antes_que_la_configuracion[test]`) |
| M11 | Aplicación: catálogo + ubicaciones **antes de `comprobar_sin_sigrid`** | **rojo** (9 failed, `test_f056_pipeline_revision.py::…r2_la_transicion_va_antes_que_sigrid_y_no_escribe`) | verde. El orden de la transición frente a Sigrid es del Bloque 3, y lo fijan sus tests (misma feature) |
| M12 | Aplicación (listar): las ubicaciones **antes que las equivalencias** | **rojo** (`…r46_listar_lee_las_ubicaciones_una_vez_tras_el_catalogo`) | **rojo** |
| M13 | Aplicación (listar): **dos lecturas** por petición | **rojo** (ídem) | **rojo** |

Ninguna sobrevive. Ninguna la caza solo una suite de otra feature.

Matiz sobre M1 y M3: con solo `test_f056_ubicaciones.py`, el primero que cae es el recuento de construcciones de
`…sin_cache_entre_peticiones`. La puerta «400 sin construir nada» la protegen los tests del Bloque 3, por
`nada_se_construye`, que prohíbe `obtener_ajustes`. Lo he comprobado sin `-x`:
- con M1, caen 53 de los 54 tests de `-k "r5_cuerpo_invalido or r5_un_cuerpo or r8_descartar_y_recuperar"`;
  - caen los 51 de `r5_cuerpo_invalido`;
  - el que pasa es `…r5_un_cuerpo_que_no_es_json_es_400`, porque ese cuerpo lo rechaza `function_app.py` antes de
    llegar a `accion_de_revision`;
- con M3, caen los 35 de R23 y R25.

### Mutantes a mano (no de orden): lo más arriesgado

**De la herramienta**, reejecutados a mano. Los 4 mueren:

| # | Mutación | Lo caza |
|---|---|---|
| T1 | `frozen=True → False` | `…r48_la_fila_es_inmutable_y_su_ubica_no_sale_en_el_repr` |
| T2 | `repr=False → True` | ídem |
| T3 | `or → and` en la forma de la fila | `…una_fila_mal_formada…[nula]` |
| T4 | `sum(1 → 2` | `…r46_el_log_dice_obra_unidades_y_sin_tipologia_y_nunca_el_texto` |

**Propios**, donde la herramienta no genera nada. Los 12 mueren, también con solo `test_f056_ubicaciones.py`:

| # | Mutación | Lo caza |
|---|---|---|
| H1 | `if lectura.llego_al_techo:` → `if False:` | `…r46_al_techo_es_catalogo_sin_verificar_sin_el_texto` |
| H2 | Techo → `CatalogoNoDisponible` (503 en vez de 409) | ídem |
| H3 | El mapa sale de las **filas** y no de las unidades del catálogo (entran las ajenas, faltan las sin fila) | `…r48_cada_unidad_del_catalogo_con_las_ubicaciones_de_su_tipologia` |
| H4 | Casar el código de unidad **recortado** | `…r48_la_unidad_se_casa_exacta_sin_recortar_el_codigo` |
| H5 | Casar el código **sin mayúsculas** | ídem |
| H6 | Leer con el **nombre** de la obra en vez de su código | `…r48_cada_unidad_del_catalogo…` (`puerto.obras == [OBRA]`) |
| H7 | `_texto` recorta | `…r46_leer_es_un_post_a_sql_read_con_su_cuerpo` |
| H8 | `_texto` sin `None` (`None → "None"`) | `…cada_fila_es_una_unidad_y_su_ubica[ubica-nula]` |
| H9 | El texto de `ubica` a un `log.debug` | `…r46_el_log_dice_obra_unidades_y_sin_tipologia_y_nunca_el_texto` |
| H10 | La forma de la fila solo por `isinstance` (sin contar columnas) | `…una_fila_mal_formada…[una-columna]` |
| H11 | `ubica` vacía → `None` en el mapeo | `…cada_fila_es_una_unidad_y_su_ubica[ubica-vacia]` |
| H12 | `sin_tipologia` sin recortar (los blancos cuentan como tipología) | `…r46_el_log_dice_obra_unidades…` |

**N-2 del Bloque 3, reproducido**: con `str(identificador) == crudo.lower()` → `True` en `_uuid`, sale
`test_f056_revision_http.py` **6 failed, 176 passed**. Deshecho, sale 182 passed.

## Lo que pedía comprobar el encargo

- **La consulta**, frente a design §16.3 y `azure-apps/sigrid_tablas.md`. ✔
  - **Texto.** `SQL_UBICACIONES_DE_LAS_UNIDADES` es carácter a carácter la de §16.3. Hay un test que lee el bloque
    `sql` del propio `design.md` (`…r48_la_consulta_es_la_de_design_16_3`).
  - **Tablas y columnas.** Las columnas existen en el diccionario:
    - `upv` («Propiedades de con», así que `v.ide = u.ide`) tiene `obride` y `obrtplide` («Tipología unidad
      postventa», índice a `prmtpl`);
    - `prmtpl.ubica` es «Ubicaciones · Texto ilimitado», y por eso lleva el `CAST(… AS nvarchar(max))`;
    - `con.cod` también está.
  - **Filtro de obra.** Es el de `SQL_UNIDADES_DE_LA_OBRA`, con el código literal
    (`…r46_el_filtro_de_obra_es_el_de_las_unidades_de_f036`).
  - **Solo lectura y parametrizada.** Un único `?`, y el código nunca va en el texto: un caso con `' OR 1=1 --`
    (`…r46_un_solo_parametro…`). Es un `SELECT` puro, por `POST /api/sql/read` y por ninguna otra ruta: el cuerpo
    se fija entero en `…r46_leer_es_un_post_a_sql_read_con_su_cuerpo`. Ni `sql/write` ni las rutas de dominio
    aparecen en los dos módulos (`…solo_lee_y_no_mira_ningun_interruptor`).
  - **Límites.** `max_rows` es 1.000. Con 1.000 filas o más, `llego_al_techo` y la aplicación da 409. Cortada por
    debajo del techo, o mal formada, es 503. Lo transitorio (408/429/5xx y los cortes de red) se reintenta; un 4xx
    definitivo no. Todo es heredado de `AdaptadorCatalogoSigridApi._leer`, sin tocarlo, y lo fijan tests propios del
    bloque.
- **El parseo de `ubica`**. ✔ Lo hace `ubicaciones_de_tipologia` (dominio, Bloque 2):
  - parte por `;`, recorta los extremos y quita vacíos y valores de más de 48;
  - quita solo los repetidos exactos, conservando el orden;
  - `None` da `()`.

  `ESPERADO[U1]` lo fija con un texto que lleva blancos, `;;`, un repetido exacto, una variante en minúsculas y uno
  de 49 caracteres. La comparación con la ubicación es exacta tras recortar (`…editar_valida_contra_la_lista_leida_de_su_unidad`:
  `" Terraza "` en U2 vale y `"Terraza"` en U1 no).
- **O-2 del Bloque 3.** ✔
  - **El 503 deliberado ha desaparecido.** `_sin_lectura_de_ubicaciones` está borrada, y `grep` no encuentra ni el
    nombre ni el texto «aún no está disponible» en el servicio.
  - **La fuente real está compuesta en la aplicación y en el borde.** En la aplicación, `leer_ubicaciones_validas`
    y `fuente_de_ubicaciones`; en el borde, `construir_fuente_de_ubicaciones` llama a
    `construir_ubicaciones_validas`. `test_f056_o2_la_fuente_por_defecto_lee_las_ubicaciones_de_sigrid` sustituye
    al test del 503 y pasa sin parchear la fuente.
  - **Una lectura por petición, compartida.** Listar hace una lectura para tres filas (M13). La edición y la
    aprobación leen una vez cada una.
  - **Ninguna lectura en descartar, recuperar e historial** (M2, M4 y M5).
  - **Sin caché** (M9).
  - **`catalogo.ubicaciones` es el mapa que valida.** El borde serializa `resultado.ubicaciones`, que es el mismo
    `validas` con el que se calculan los motivos (`…r48_lo_que_se_ofrece_es_lo_que_se_acepta`).
- **Logs y datos reales.** ✔
  - **Logs.** El texto de `ubica` no va a ningún registro: se busca a nivel `DEBUG` en listar, editar, aprobar, al
    techo, cortada y con el adaptador real, y H9 lo confirma. Tampoco va en el `repr` (T2) ni en los mensajes de
    error. El log del adaptador dice la obra, cuántas unidades, cuántas sin tipología, si llegó al techo y los
    segundos.
  - **Datos reales.** He barrido las líneas añadidas del diff `c22e692..HEAD` en busca de `0677`, `Mirasierra`,
    `@ruesma`, GUIDs, URLs reales y `print(`: ninguno. Los datos de los tests son ficticios: obra `9901`, unidades
    `9901.03VILLA n.`, `@ejemplo.invalid`, `https://ejemplo.invalido` y ubicaciones genéricas. Pasa
    `test_f006_repo_sin_identificadores.py`.
- **R39 y el paquete `infrastructure/sigrid`.** ✔ en el código.
  - **Lo que cambió.** `git diff --stat f86d639..HEAD -- infrastructure/sigrid/` da solo los dos módulos nuevos y
    `fabrica.py` con **41 inserciones y 0 borrados**: la función, su entrada en `__all__`, dos imports y la
    enmienda en la cabecera.
  - **Lo que se importa.** `test_f056_r39_de_sigrid_solo_se_usa_el_catalogo_de_f036` fija a mano lo que cada
    módulo de F-056 toma de `infrastructure/sigrid`. El borde toma solo los dos constructores de lectura. El
    adaptador toma solo `AdaptadorCatalogoSigridApi` y sus dos funciones de consultas. Nada de `cliente`,
    `escrituras` ni `graficos`.
  - **Lo intocable.** Lo vigilan `INTOCABLES` y `…s12_la_fabrica_de_sigrid_solo_puede_ganar_funciones`.
  - **El texto de R39 en la spec se ha quedado viejo** (N-1).
- **N-1 del Bloque 3** (redacción de R11 y §9). ✔ R11 nombra una «tercera respuesta con correo», la 200 de la
  acción, con el correo de quien actúa; ningún error lo lleva y el `oid` no sale en ninguna. §9 lo repite y cita el
  test. Es coherente con R8 y R10.
- **N-2 del Bloque 3.** ✔ Hay tres cuerpos más en `CUERPOS_INVALIDOS` (`incidencia-con-llaves`, `incidencia-urn`,
  `incidencia-sin-guiones`) y los mismos tres valores en `…r32_historial_sin_uuid_es_400_sin_construir`. El mutante
  muere (arriba).
- **Decisiones 1 y 2 del implementer.** De acuerdo con las dos.
  - **Decisión 1: heredar el adaptador del catálogo.** Es lo que pide §16.3 («la misma puerta de entorno y el mismo
    cliente»), sin una copia que diverja. El coste es que depende del método privado `_leer` de un módulo
    `INTOCABLE`. Si F-036 lo cambiara, lo cazarían los 36 tests del adaptador de este bloque (O-1).
  - **Decisión 2: `unidad_codigo` admite `None`.** Es coherente con `FilaUnidadCatalogo` y con «una fila ajena se
    ignora».

## Checkpoints (lo que aplica a un bloque intermedio)

**C1**
- [x] `init.sh` termina con exit 0.
- [x] Existen los ficheros del arnés.

**C2**
- [x] Una sola feature `in_progress` (F-056).
- [x] La rama es la de la feature.
- N/A `progress/current.md` solo con la sesión activa: es una exigencia de cierre, y este es un bloque intermedio.
  Sigue arrastrando el bloque de F-053; es la O-6 del Bloque 1, que limpia el líder al cerrar.
- N/A Resumen en `history.md`: F-056 no está `done`.

**C3**
- [x] **Arquitectura hexagonal.**
  - El puerto nuevo está en `domain/ports/` y solo importa del dominio.
  - La aplicación importa el puerto, no el adaptador.
  - La composición (`construir_ubicaciones_validas`, `obtener_ajustes`) vive en el borde.
  - El adaptador está en `infrastructure/sigrid/`, y la consulta, en un módulo puro aparte.
  - Las guardias de arquitectura pasan (en `init.sh` y en la ejecución sin caché).
- [x] Primera línea con la ruta en los 3 ficheros nuevos.
- [x] Sin `print`, sin TODOs ni FIXMEs en las líneas añadidas, sin secretos y sin dependencias nuevas.
  - La clave, la URL y la base de los tests son inventadas.
  - **Estilo**: PEP 8 pide dos líneas en blanco antes de `def leer_ubicaciones_validas` y hay una (N-2). Es cosmético.
- N/A Unidad «parte», «nada se archiva sin validaciones», lo manuscrito, firmado ≠ conforme, reprocesar no duplica y
  `conest`: el bloque no toca partes, firmas, archivo ni estados de Sigrid. Solo añade una lectura `sql/read` y no
  escribe en Sigrid (R39, fijado por T13).
- [x] Ningún escaneado, PDF ni ofimática añadido. El diff solo trae `.py` y `.md`.

**C3 bis** · N/A: el bloque no toca `docs/referencia/` (no hay nada bajo `docs/` en el diff).

**C4**
- [x] Cada requisito del bloque (R46–R48, más R28 y R41 en lo que tocan) tiene su test, y todos pasan (tabla de
  abajo).
- [x] Los unit tests no tocan red ni BBDD.
  - El adaptador se prueba con el `ClienteFalso`.
  - La aplicación y el borde, con puertos en memoria y las fábricas sustituidas.
  - La guardia de red de `conftest.py` sigue por debajo.
- [x] MANUAL listadas. Las de este bloque: ninguna. La comprobación en vivo es T19 (Bloque 5): queda en `tasks.md`
  con su comando, y el informe dice qué mirar.

**C4 bis**
- [x] `rigor: critico` declarado.
- [x] **Fase RED**: pegada (T14a, O-2 y N-2), y **reproducida** la de T14a: 76 failed, 15 passed, todos de aserción.
- [x] **Cobertura**: `[OK]` 100 % (1060/1060) en `init.sh`.
- [x] **Mutación**: existe `progress/mutacion_F-056_bloque3bis.md`, generado por la herramienta. El alcance (6
  ficheros, 341 líneas) y los mutantes (10, por fichero y por operador) están recalculados y coinciden.
- [x] **Muertos**: **campaña no reejecutada, 63 min según el informe (más de 5 min)**. Me quedo con:
  - el recálculo puro;
  - 4 mutantes de la herramienta reejecutados a mano, los 4 muertos;
  - 25 mutantes propios: 13 de orden y 12 de lógica. Mueren los 25.
- [x] **Duración**: ≈ 3011 s por mutante con 8 workers. Es coherente con una suite de 770 s en serie y no es
  sospechosa.
- [x] Cero supervivientes y cero timeouts tras el repaso en serie (2 en timeout en paralelo, muertos en serie).
  Ningún equivalente que justificar.
- [x] «Evidencias» con los cuatro números y los workers (8).
- [x] Ningún N/A sin motivo.

**C4 ter** · N/A: el repositorio no tiene `harness/rutas_sensibles.json`.

**C5** (de bloque)
- [x] T14a, T14b y T14c marcadas, cada una con su commit `F-056 Tn:`. O-2, N-1 y N-2 van en commits `F-056:` aparte.
- N/A «Todas las tareas `[x]`»: T15 en adelante son de otros bloques.
- [x] Sin ficheros temporales ni sin trackear (`git status` limpio).
- [x] `features.json`: F-056 `in_progress`, que es lo que corresponde.

## Cobertura: requisito → test (los de este bloque)

Todos los tests son de `test_f056_ubicaciones.py`, salvo donde se dice otro fichero.

| R | Test(s) |
|---|---|
| R46 · la consulta | `…r48_la_consulta_caracter_a_caracter`, `…r48_la_consulta_es_la_de_design_16_3`, `…r46_el_filtro_de_obra_es_el_de_las_unidades_de_f036`, `…r48_la_tipologia_va_con_left_join_y_el_texto_entero`, `…r46_un_solo_parametro_el_codigo_de_obra_y_nunca_en_el_texto` (3) |
| R46 · el adaptador (solo `sql/read`, `max_rows`, techo, cortada, reintentos, puerta de entorno) | `…r46_leer_es_un_post_a_sql_read_con_su_cuerpo`, `…cero_filas…`, `…mil_filas_o_mas…` (4), `…novecientas_noventa_y_nueve…`, `…cortada_por_debajo_del_techo…` (3), `…lo_transitorio_se_reintenta` (6), `…un_corte_de_red…`, `…agotados_los_reintentos…`, `…un_definitivo_no_se_reintenta` (4), `…una_respuesta_sin_la_forma_esperada…` (4), `…se_niega_fuera_de_dev_y_pro` (4), `…en_dev_y_pro_se_construye` (2), `…solo_lee_y_no_mira_ningun_interruptor` |
| R46 · la fábrica | `…la_fabrica_exporta…`, `…se_niega_fuera_de_dev_y_pro_antes_que_la_configuracion` (2), `…nombra_lo_que_falta_y_ningun_valor`, `…construye_con_los_interruptores_como_esten` (4), `…pasa_la_configuracion_al_adaptador` |
| R48 · el mapeo | `…r48_cada_fila_es_una_unidad_y_su_ubica` (6), `…una_fila_mal_formada…` (7), `…la_fila_es_inmutable_y_su_ubica_no_sale_en_el_repr` |
| R46–R48 · la composición | `…r48_cada_unidad_del_catalogo_con_las_ubicaciones_de_su_tipologia`, `…una_unidad_sin_fila_tiene_la_lista_vacia_y_una_ajena_no_entra`, `…la_unidad_se_casa_exacta…`, `…r46_al_techo_es_catalogo_sin_verificar_sin_el_texto`, `…sin_sigrid_el_error_del_puerto_sube_tal_cual`, `…la_fuente_compuesta_lee_el_puerto_una_vez_por_llamada`, `…listar_lee_las_ubicaciones_una_vez_tras_el_catalogo`, `…editar_valida_contra_la_lista_leida_de_su_unidad`, `…una_unidad_sin_tipologia_no_acepta_ninguna_ubicacion`, `…editar_al_techo_es_409_sin_escribir` |
| R28, R46, R48 · el borde | `…el_borde_compone_la_lectura_de_sigrid`, `…r28_el_listado_ofrece_el_mapa_leido_una_lectura_por_peticion`, `…sin_cache_entre_peticiones`, `…r48_lo_que_se_ofrece_es_lo_que_se_acepta`, `…aprobar_lee_una_vez`, `…descartar_recuperar_e_historial_no_leen_ubicaciones`, `…al_techo_la_accion_es_409_sin_escribir` (2), `…al_techo_el_listado_es_409`, `…sin_sigrid_es_503_sin_escribir` (3), `…sin_configuracion_de_sigrid_es_503_antes_de_la_base`, `…por_la_ruta_una_sola_sql_read_con_la_consulta`, `…por_la_ruta_mil_filas_son_409_y_cortada_503`; `test_f056_o2_la_fuente_por_defecto_lee_las_ubicaciones_de_sigrid` (`…_revision_http.py`) |
| R41 y §16.3 · el texto de `ubica` | `…r41_el_texto_de_ubica_no_va_a_ningun_registro`, `…r46_el_log_dice_obra_unidades_y_sin_tipologia_y_nunca_el_texto`, `…el_log_registra_la_duracion_y_no_la_hora` |
| R5, R32 · N-2 | `test_f056_r5_cuerpo_invalido_es_400_sin_construir_nada[incidencia-con-llaves / -urn / -sin-guiones]`, `test_f056_r32_historial_sin_uuid_es_400_sin_construir` (3 valores más) |
| R39 y §12 | `test_f056_r39_de_sigrid_solo_se_usa_el_catalogo_de_f036`, `NUEVOS_DE_F056` y `FUNCIONES_DE_F056` ampliados, `…s12_la_fabrica_de_sigrid_solo_puede_ganar_funciones` (`test_f056_alcance_cerrado.py`) |

## Hallazgos

### Bloqueantes

Ninguno.

### Menores (no bloquean este bloque)

1. **N-1 · R39 todavía dice «solo las dos lecturas de F-036».**
   - **Dónde.** `specs/F-056-revision-bandeja-backend/requirements.md` l.278–279: «Nada de F-056 escribe en Sigrid:
     solo las dos lecturas de F-036 por `POST /api/sql/read`».
   - **El problema.** Desde este bloque hay una **tercera** lectura (R46, §16.3). El docstring de
     `test_f056_alcance_cerrado.py` ya se puso al día, y R46 ya habla de «una lectura más», pero el requisito sigue
     diciendo «solo las dos». El Bloque 4 redacta la documentación desde la spec (R44: `INTEGRACION.md`,
     `ARCHITECTURE.md` y `azure-apps`), y esta frase ya ha confundido una vez.
   - **Qué hacer.** Cambiar R39 a «Nada de F-056 escribe en Sigrid: solo lee, por `POST /api/sql/read`: las dos
     lecturas de F-036 y la de las ubicaciones válidas (R46, §16.3); ningún módulo nuevo nombra una ruta de
     escritura». Va en un commit `F-056:` aparte, **antes del Bloque 4**. Es un cambio de spec: lo decide el líder.
2. **N-2 · Falta una línea en blanco antes de `def leer_ubicaciones_validas`.**
   - **Dónde.** `services/postventa-api/application/pipelines/revision.py` l.128–130: entre el alias
     `FuenteDeUbicaciones = …` y la función hay una línea en blanco, y PEP 8 pide dos (`docs/CONVENTIONS.md`:
     «PEP8»).
   - **Por qué no lo vio nadie.** La configuración de ruff del repositorio no activa E302; con
     `ruff check --select E302 --preview` sale este único aviso. Antes del bloque, el fichero estaba limpio en esa
     regla.
   - **Qué hacer.** Añadir la línea, en el mismo commit que N-1 o en el siguiente del Bloque 4.

### Observaciones (no son cambios requeridos)

- **O-1 · Herencia de un método privado de un módulo intocable.**
  - `AdaptadorUbicacionesValidasSigridApi` usa `AdaptadorCatalogoSigridApi._leer` y `_mapear`.
  - Es la decisión 1 y me parece la buena: §16.3 pide la misma puerta y el mismo cliente, y una copia divergiría.
  - El acoplamiento queda vigilado por los tests del adaptador de este bloque (techo, cortada, reintentos, forma,
    entorno).
  - Efecto secundario: el mensaje de la puerta de entorno heredada habla de «la lectura del catálogo de la obra».
    Es un motivo interno del 503 y no se ve en la respuesta como texto de negocio. No pido cambio.
- **O-2 · `nada_se_construye` no nombra `construir_ubicaciones_validas`.**
  - Hoy protege igual: prohíbe `obtener_ajustes` y `construir_fuente_de_ubicaciones`, y M1 y M3 lo demuestran.
  - Si algún día el borde recibiera los ajustes de otra forma, convendría añadir el nombre a esa lista (una línea en
    `test_f056_revision_http.py` l.198–205).
  - No pido cambio.
- **O-3 · La campaña se lanzó con `--timeout 1800`, no con los 900 de `tasks.md`.** Está anotado en la marca de T14c
  y en el informe. Con 8 workers y dos timeouts repasados en serie, es razonable.
- **O-4 · `init.sh` dio los servicios en verde por caché**, como en los bloques anteriores. Por eso aquí se han
  reejecutado sin caché todos los tests de F-056 y `test_f006_repo_sin_identificadores.py` (940 passed). La suite
  completa sin caché es la del informe: 7607 passed en `4a65bcc`.
- **O-5 · Para el Bloque 4.** Lo que el implementer deja anotado es correcto y lo confirmo:
  - R44 tiene que contar **tres** lecturas de Sigrid y **tres** respuestas con correo, en `INTEGRACION.md` §7 y en
    `azure-apps/postventa_incidencias.md`;
  - siguen abiertas la O-1 del Bloque 3 («diecisiete» → «veinte» frente a R45) y la O-6 del Bloque 1
    (`current.md`).

## Propuestas de automejora (para el humano; no aplicadas)

1. **`reviewer.md`, punto 7.**
   - **La propuesta.** Ya estaba propuesta en la review del Bloque 3 la ampliación a «validar antes de construir»,
     y este bloque la ha aplicado por encargo. Se le puede añadir un caso concreto: **la caché y la construcción
     perezosa también son orden** (M8 y M9). «Una lectura por petición, sin caché» y «el adaptador se construye
     antes de la base» no los ve ningún operador de `harness.mutacion`, y solo se demuestran bajando o guardando la
     construcción a mano.
   - **Alcance.** Vale para cualquier proyecto. Si se aprueba, se porta a `arnes-base`.
2. **`harness.mutacion` (o `CHECKPOINTS.md` C4 bis).**
   - **El hueco.** La herramienta no muta la condición de un `if` sin operadores (`if lectura.llego_al_techo:`).
     Aquí eso deja la aplicación, la fábrica y el borde con **0 mutantes**, aunque contienen la lógica del techo y
     la composición.
   - **La propuesta.** O un operador «condición → `False`/`True`» en `if`/`while`, o una línea en C4 bis: «si un
     fichero de producción del alcance sale con 0 mutantes y tiene ramas, el reviewer mete al menos un mutante a
     mano por rama».
   - **Alcance.** Es genérica. Si se aprueba, va a `arnes-base`.
