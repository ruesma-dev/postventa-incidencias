<!-- progress/review_F-060_bloque2.md -->
# Review · F-060 · Bloque 2 · El lote en la base (T4–T8)

- **Veredicto:** **APPROVED condicionado a T7.** El bloque queda aprobado cuando T7 (MANUAL del humano) dé
  **«58 passed», con 0 skipped y 0 failed**. Si T7 falla, o sale algún `skipped`, el veredicto pasa a
  CHANGES_REQUESTED y se vuelve a revisar.
- **Rama:** `feature/F-060-normalizar-ubicaciones`, HEAD `8f4962d`. Base del bloque: `66c981d`. Base fija de la
  feature: `33d8938`.
- **Commits revisados:** `e259f23` (T4), `3df8399` (bloqueo), `fabbd7f` (decisión del humano), `29bb77b` (T5),
  `5bf9686` (T6), `be10cf2` (T8) y `8f4962d` (hash de T8).
- **Fecha:** 2026-10-10.

## Nivel de rigor

`critico`, declarado en `harness/features.json`. Exige fase RED con la traza pegada, cobertura de lo cambiado,
mutación con cero supervivientes salvo aceptación escrita del humano, y RM7 (mover la puerta de orden) porque el
requisito central del bloque es un orden: «bloquear → comprobar frescura → insertar».

## Lo comprobado (resultados reales)

| Qué | Resultado |
|---|---|
| Sin caché (`-p no:cacheprovider`), desde `services/postventa-api`: `test_f060_repositorio_lote.py`, `test_f060_normalizacion_dominio.py`, `test_f056_repositorio_revision.py`, `test_f006_repo_sin_identificadores.py` y `test_f056_ddl.py` | **296 passed** en 6,70 s |
| Colindantes sin caché: `test_f056_pipeline_revision.py`, `test_f056_revision_http.py`, `test_f056_alcance_cerrado.py`, `test_f005_arquitectura.py` y `test_f036_arquitectura.py` | **293 passed, 9 skipped** en 5,70 s. Los 9 son los controles de diff de F-056, que solo corren en su propia rama |
| `tests_bbdd` sin DSN | **58 skipped** (el fusible de `requiere_base`). `--collect-only`: **58 tests**, la cifra que el informe anuncia para T7 |
| `ruff check` de los cinco ficheros tocados, desde la raíz (como `init.sh`) | `All checks passed!`. Desde `services/postventa-api` sale `I001` en los cinco, también en la parte de `test_f056_repositorio_revision.py` que no se tocó: es un efecto del directorio (sin `pyproject.toml`, cambia qué cuenta como paquete propio). No es un hallazgo |
| Cobertura, medida por el reviewer en la copia con `coverage run --include` | `domain/ports/revision.py` **20/20** y `repositorio_revision_pg.py` **82/82**: **100 %**. Coincide con el informe |
| `sentencias_revision.py`, `*.sql` y `services/postventa-front/` desde `33d8938` | **Sin cambios** (`git diff --name-only` vacío) |
| Tests de F-036 y F-056 cambiados desde `33d8938` (incluidos `tests_bbdd` y `tests/utiles_*`) | **Solo** `tests/test_f056_repositorio_revision.py`, con **+4/−0** |
| Producción cambiada en el bloque | Solo `domain/ports/revision.py` y `infrastructure/persistencia/repositorio_revision_pg.py`, los dos ficheros que prevé §7 |
| `git status` al terminar | Limpio. Las mutaciones se hicieron en una copia en `%TEMP%`, fuera del árbol |

### La excepción del humano (opción (a), 2026-10-10)

`git diff 66c981d..HEAD -- tests/test_f056_repositorio_revision.py`: un docstring de tres líneas que cita la
decisión y **una** entrada nueva, `"registrar_lote"`, en la lista. La aserción sigue siendo una igualdad con la
lista **exacta** de los públicos de `RevisionPort` (`publicos == [...]`), así que **no se ha relajado**: un octavo
método, o la desaparición de uno de los seis, la siguen poniendo en rojo. Es la única aserción de F-056 que cambia. La
excepción está escrita con fecha en `design.md` §12 y en la fila R37–R39 de §13, en R39, en T19 y en la cabecera
de `tasks.md`. T19 tendrá que admitir este fichero en su lista de excepciones.

### El código frente a §7 y R12–R16

- **Las sentencias de F-056 se reutilizan sin cambiarlas.** `_registrar_lote` llama a `select_bloquear`,
  `select_ultimas_revisiones` e `insert_revision`, y nada más. El fichero de sentencias no aparece en el diff, y
  `test_f060_r15_el_repositorio_no_escribe_sql_propio` vigila que el repositorio no lleve SQL propio.
  `test_f060_r12_bloquea_todas_mira_todas_inserta_en_orden_y_confirma` compara la secuencia entera, texto y
  parámetros, contra lo que devuelven esas funciones.
- **Append-only.** No hay ningún `UPDATE`, `DELETE` ni `TRUNCATE`. Contra `bandeja_incidencias` solo va el bloqueo,
  y la única escritura es `INSERT INTO postventa.revisiones_bandeja` (`test_f060_r15_solo_inserta_en_revisiones…`,
  con lotes frescos y con desactualizados).
- **`FOR UPDATE` en orden fijo, sin bloqueos consultivos.** El orden lo pone `_en_orden` de F-056 (`sorted(set(…))`),
  con `ORDER BY incidencia_id FOR UPDATE`. `ADVISORY` no aparece ni en el SQL ejecutado ni en el código.
- **Las desactualizadas se saltan y las demás se escriben, en la misma transacción.** Hay un cursor y un `COMMIT`,
  y no hay `ROLLBACK`. Está probado con cinco variantes de desactualizada y con el caso «todas desactualizadas»
  (cero `INSERT`).
- **`ROLLBACK` y mensaje sin parámetros.** El bloque usa el `_en_transaccion` de F-036. Se prueba un fallo en cada
  uno de los cuatro puntos posibles (al bloquear, al leer las últimas, en el primer `INSERT` y en el último). El
  mensaje lleva `registrar_lote` y el tipo del error, y no lleva textos, ni el literal del sistema, ni
  `incidencia_id`, ni el texto del error. Un fallo que no viene de la base (una hora sin zona) hace `ROLLBACK` y
  sube tal cual.
- **Lote vacío:** ningún cursor, nada ejecutado, ni `COMMIT` ni `ROLLBACK`.
- **Precondiciones:** una revisión sin su esperada, o una incidencia repetida, dan `ValueError` sin abrir nada.
- **Las esperadas sobrantes se ignoran** (decisión de T5). Es coherente con F-056: allí la original solo entra en
  `esperadas` al **aprobar** una duplicada (`application/pipelines/revision.py::_esperadas`), y la normalización
  siempre es `editar`. Además, `planificar_normalizacion` da exactamente una esperada por revisión. Ver O-1.
- **Arquitectura:** `ResultadoDelLote` es un dataclass puro dentro de `domain/ports/`, y la infraestructura importa
  el puerto, no al revés. `test_f005_arquitectura.py` y `test_f036_arquitectura.py` están en verde.

### `tests_bbdd/tests/test_f060_bbdd_lote.py` (por lectura; lo ejecuta T7)

- **Prueba lo que pide T6.** (1) Un lote de tres, con el plan sacado del dominio sobre `listar`, escribe tres filas
  `editar` con el literal del sistema en `revisado_por` y en `revisado_correo`; los `revision_id` devueltos son los
  de la base y la bandeja queda igual con `SELECT *` fila a fila. (2) Con **dos conexiones**, una edición humana
  entre el plan y el lote: esa se salta y su última sigue siendo la humana. (3) Un lote repetido con las esperadas
  viejas: las tres desactualizadas, la tabla igual, y un plan nuevo vacío. Hay además dos casos extra que suman: la
  esperada de una incidencia ya revisada, y **el lote que espera al `FOR UPDATE`** de otra conexión.
- **El test de espera también vigila el orden contra PostgreSQL.** Si el lote leyera las últimas antes de bloquear,
  vería la bloqueada como fresca y la insertaría, y la aserción `desactualizadas == {bloqueada}` caería. El
  `lock_timeout` de la sesión es de 5 s (`config/settings.py`) y el test duerme 1 s, con margen suficiente.
- **No puede tocar el servidor compartido.** Los cinco tests llevan `@requiere_base`. Tanto la conexión del fixture
  como `_otra_conexion` pasan por `dsn_de_pruebas()`, que hace `pytest.exit` si el host no es local. Los `DELETE`
  de `_limpiar` son de la limpieza de la base efímera, igual que en `test_f056_bbdd_revision.py`, y el docstring lo
  dice. Todos los datos son ficticios (obra `9903`, `@ejemplo.invalid`, `uuid4`).

## Mutación (C4 bis)

- **Recálculo puro** con `harness.alcance.alcance_de_feature("F-060", base="66c981d")` y
  `harness.mutacion.generar_mutantes`: **2 ficheros, 94 líneas** (38 + 56) y **4 mutantes**, con los mismos
  operadores y los mismos textos original→mutado que el informe (`frozen=True→False` en `revision.py:55`;
  `not` en `:123`; `!=`→`==` en `:126` y en `:216`). **Coinciden.**
- **Campaña no reejecutada: 744,4 s (12,4 min) según el informe**, por encima de los 5 minutos, y además el líder
  pidió no relanzarla. Coste por mutante: 744,4 × 4 workers ÷ 4 = **744 s**. Es plausible y no es sospechoso: el
  ejecutor usa `-x`, los cuatro mutantes mueren, y con cuatro suites en paralelo se tarda en llegar a los tests
  `f056`/`f060`, que van al final por orden alfabético.
- **Muertos comprobados, no solo contados.** Aplicando los **4 mutantes de la herramienta** con `aplicar_mutante`
  en una copia desechable, **solo** `tests/test_f060_repositorio_lote.py` los mata a los cuatro (1, 23, 20 y 13
  fallos). Reproduje también tres mutantes a mano del informe: **H8** (bloquear las claves de `esperadas`) muere en
  `…_se_bloquean_solo_las_del_lote_aunque_sobre_una_esperada`; **H9** (`desactualizadas` como `set`) y **H3** (sin
  `como_uuid`) mueren en `…_una_desactualizada_se_salta…` (×2). Coincide con la tabla del implementer.
- **Supervivientes:** ninguno, ni de la herramienta ni a mano (10/10 según el informe; 3/3 reproducidos aquí).

### RM7 · bajar la puerta de orden

Apliqué tres mutaciones a mano en la copia desechable, una cada vez, y ejecuté **solo los tests de la feature**
(`tests/test_f060_repositorio_lote.py`, sin `-x`):

| Mutación | Resultado | Tests que caen |
|---|---|---|
| O1 · bloquear **después** de leer las últimas (la frescura antes del bloqueo) | **ROJO**, 1 failed | `test_f060_r12_bloquea_todas_mira_todas_inserta_en_orden_y_confirma` |
| O2 · bloquear **al final**, después de los `INSERT` | **ROJO**, 3 failed | el anterior, `…_se_bloquean_solo_las_del_lote…` y `…_si_la_base_falla…[al-bloquear]` |
| O3 · insertar **antes** de comprobar la frescura | **ROJO**, 7 failed | los siete casos de R13 (`…_una_desactualizada_se_salta…` ×2, `…_la_frescura_es_la_de_cada_una` ×3, `…_si_todas_estan_desactualizadas…` ×2) |
| Original restaurado | 28 passed | — |

Los tests de la propia feature ven los tres colaboradores del orden. O1 solo lo caza un test unitario (ver O-2).

## Checkpoints (lo que aplica a un bloque intermedio)

**C1**
- N/A · `bash harness/init.sh` completo. **Justificación:** es un bloque intermedio, y el líder pidió no lanzarlo y
  ejecutar sin caché los tests de F-060, los de F-056 del repositorio y `test_f006`. Están todos en verde (arriba).
  La puerta completa se pasa en T23.
- [x] El arnés está completo (`CLAUDE.md`, `features.json`, `specs/SPECS.md`, `CHECKPOINTS.md`).

**C2**
- [x] Como mucho una `in_progress`, y es F-060.
- [x] La rama es `feature/F-060-normalizar-ubicaciones`.
- [x] `progress/current.md` refleja la sesión, con la decisión del humano. La deuda de orden de la O-4 del Bloque 1
  sigue abierta, es del líder y no bloquea un bloque intermedio.
- N/A · resumen en `history.md`. **Justificación:** F-060 no está `done`; se hace en T36.

**C3**
- [x] Hexagonal: un dataclass puro en `domain/ports`, y la infraestructura depende del puerto. Los tests de
  arquitectura están en verde.
- [x] La primera línea de cada fichero tocado es un comentario con su ruta.
- [x] Sin `print`, sin `breakpoint`, sin TODO y sin secretos. El diff solo nombra `psql-albaranes-rs9k2` para decir
  que T7 no lo toca: es un nombre de servidor que ya está en `CLAUDE.md`, no una credencial.
- N/A · reglas de partes (unidad de trabajo, archivado, manuscrito, firmado, reprocesar, estados de Sigrid,
  escaneados). **Justificación:** el bloque no toca partes, Sigrid, SharePoint ni escaneados; solo escribe
  revisiones en el esquema propio.

**C3 bis**
- N/A. **Justificación:** el bloque no trae ningún documento de fuera.

**C4**
- [x] Cada requisito del bloque (R12–R16 y las precondiciones de §7) tiene su test (tabla de abajo).
- [x] Los tests unitarios no tocan red ni base (`ConexionDoble`; la guarda de sockets de F-003 sigue activa).
- [x] Lo `MANUAL (humano)` está listado: T7, con el comando y la cifra esperada en el informe.

**C4 bis**
- [x] `rigor: critico` declarado.
- [x] Fase RED: la traza real está pegada (24 failed, todos por aserción, y 3 passed con su justificación).
- [x] Cobertura de lo cambiado: 100 %, verificado por el reviewer. La línea `PUERTA COBERTURA` de `init.sh` es de
  T23.
- [x] Mutación: el informe existe con totales reales, recalculados y coincidentes.
- [x] Muertos comprobados: los 4 se aplicaron en la copia y los tests de F-060 los matan. Campaña no reejecutada
  (12,4 min).
- [x] Duración plausible: 744 s por mutante con `-x`.
- [x] Cero supervivientes, ni de la herramienta ni a mano.
- [x] RM7 hecho: las tres mutaciones de orden dan rojo con los tests de la propia feature.
- [x] «Evidencias» del bloque con tests, cobertura, mutantes y workers (4). El tiempo de la suite completa queda
  para T23, y el informe lo dice.

**C4 ter**
- N/A. **Justificación:** no hay `harness/rutas_sensibles.json` en el repositorio.

**C5**
- [x] En `tasks.md`, T4, T5, T6 y T8 están `[x]`, con commits `F-060 T4/T5/T6/T8: …`. **T7 sigue `[ ]` porque es
  MANUAL y está pendiente**: de ahí la condición del veredicto.
- [x] No hay temporales ni ficheros sin trackear en el árbol.
- [x] `features.json` dice `in_progress`, que es el estado real.

## Cobertura: requisito → test

| Requisito | Tests (unitarios en `tests/test_f060_repositorio_lote.py`; los de base, en `tests_bbdd/…/test_f060_bbdd_lote.py`) |
|---|---|
| R12 (puerto y resultado) | `…_el_puerto_gana_registrar_lote_y_conserva_las_seis`, `…_registrar_lote_solo_por_nombre`, `…_el_resultado_del_lote_es_inmutable`, `…_el_repositorio_cumple_el_puerto` |
| R12 (transacción y orden) | `…_bloquea_todas_mira_todas_inserta_en_orden_y_confirma`, `…_el_bloqueo_es_for_update_y_en_orden_fijo`, `…_lo_escrito_es_la_revision_del_sistema`, `…_se_bloquean_solo_las_del_lote_aunque_sobre_una_esperada`; base: `…_un_lote_de_tres…`, `…_la_esperada_de_una_ya_revisada…`, `…_el_lote_espera_al_for_update…` |
| R13 | `…_una_desactualizada_se_salta_y_las_demas_se_escriben` (×2), `…_la_frescura_es_la_de_cada_una` (×3), `…_si_todas_estan_desactualizadas…` (×2); base: `…_una_revision_humana_entre_el_plan_y_el_lote_se_salta`, `…_el_lote_espera_al_for_update…`, `…_el_lote_repetido_no_escribe_nada` |
| R14 | `…_si_la_base_falla_rollback_y_503_sin_parametros` (×4), `…_un_fallo_que_no_es_de_la_base…` |
| R15 | `…_solo_inserta_en_revisiones_y_solo_bloquea_la_bandeja` (×2), `…_el_repositorio_no_escribe_sql_propio`; base: la bandeja intacta en `…_un_lote_de_tres…` |
| R16 | `…_lote_vacio_sin_transaccion` |
| §7 paso 2 | `…_precondiciones_value_error_sin_abrir_nada` (×4) |
| R39 (la excepción) | `test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5`, con la lista exacta de siete |

## Observaciones (no bloquean)

- **O-1 · Las esperadas sobrantes se ignoran sin avisar.** Es una decisión de T5 dentro de la spec, que no dice
  nada de este caso. Está probada y es coherente con F-056 (la original solo entra en `esperadas` al aprobar). Pero
  el docstring de `RevisionPort.registrar_lote` no lo dice, y un uso futuro (F-059 amplía la misma costura) podría
  pasar la esperada de una original creyendo que se comprueba. Recomendación para cuando se toque el puerto: o
  decirlo en el docstring del puerto, o convertirlo en `ValueError` como las otras dos precondiciones. Lo decide el
  líder; no hace falta para este bloque.
- **O-2 · O1 de RM7 lo caza un solo test unitario**: la igualdad de la secuencia entera en
  `…_bloquea_todas_mira_todas_inserta_en_orden_y_confirma`. Es una aserción fuerte, y contra PostgreSQL la refuerza
  `…_el_lote_espera_al_for_update…`, pero ese test solo corre en T7. Si algún día se relaja esa igualdad, conviene
  añadir antes una aserción de orden explícita (el índice de `FOR UPDATE` menor que el de `max(revision_id)`).
- **O-3 · Un `CHECK` que falla en un `INSERT` tumba el lote entero**, por diseño (R14, `ROLLBACK` y 503). Enlaza con
  la O-3 del Bloque 1 (más de 48 caracteres): **en el Bloque 3** hay que fijar que las listas salen ya filtradas de
  la fuente de F-056, o que el plan descarta los valores de más de 48, para que un solo valor raro no impida
  normalizar la obra.
- **O-4 · El test de espera usa `time.sleep(1.0)`.** En una máquina muy cargada, el `is_alive()` podría verse antes
  de que el hilo llegara al bloqueo. Aun así, la prueba real es la aserción final sobre `desactualizadas`, que no
  depende del tiempo. El margen frente al `lock_timeout` de 5 s es suficiente. Si T7 diera un falso rojo aquí, el
  remedio es subir el `sleep`, no tocar el código.

## Cambios requeridos

Ninguno. Queda **una condición**: **T7** (humano) tiene que dar **«58 passed», con 0 skipped y 0 failed**, en la
ejecución de `infra\pruebas_bbdd_efimera.ps1`, y el resultado tiene que anotarse en `progress/impl_F-060.md`.

## Propuesta de automejora (para que la apruebe el humano; no aplicada)

- **`CHECKPOINTS.md` C4 bis, «muertos comprobados».** Cuando la campaña pase de 5 minutos pero tenga **pocos**
  mutantes (por ejemplo, ≤ 10), pedir al reviewer que los aplique con `aplicar_mutante` contra **solo** los tests de
  la feature, en una copia desechable. Cuesta segundos, y demuestra que los muertos lo están sin relanzar la
  campaña; el recálculo puro solo prueba el recuento. En este bloque llevó menos de 3 s. Vale para cualquier
  proyecto con el arnés: si se aprueba, se porta a `arnes-base`.
