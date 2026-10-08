<!-- progress/review_F-056_bloque3.md -->
# F-056 · Review del Bloque 3 (la aplicación y los tres endpoints)

- **Veredicto:** **APPROVED.** No hay bloqueantes. Hay dos hallazgos menores (N-1, una decisión de spec que debe
  tomar el líder; N-2, un hueco de test barato) y varias observaciones para los Bloques 3 bis y 4.
- **Bloque 2:** queda **APPROVED sin condición**. T8 está repetida por el humano tras `4bf2791` con **53 passed,
  0 failed, 0 skipped** (anotada en `progress/impl_F-056.md`, «T8, repetida», y marcada en `a2817af`). Es justo la
  condición de `progress/review_F-056_bloque2.md`. La O-1 de aquella review también está hecha (`aa077d1`).
- **Fecha:** 2026-10-08 · reviewer
- **Rama:** `feature/F-056-revision-bandeja-backend`, HEAD `5e2a281`. Base de la feature `f86d639`; base del bloque
  `e9e815f`.
- **Alcance revisado:** T10–T14; N-1 opción (b) de la review del Bloque 2 (`5a23429`); O-3 (`97df089`) y O-5 de la
  del Bloque 1; O-1 (`aa077d1`) y O-5 de la del Bloque 2; la opción (a) del humano (el base64url del cursor vive en
  el borde). Ficheros: `application/pipelines/revision.py`, `interface_adapters/api/revision.py`, el diff de
  `function_app.py` y de `domain/models/revision.py`, `tests/utiles_revision.py`, `test_f056_pipeline_revision.py`,
  `test_f056_revision_http.py`, `test_f056_alcance_cerrado.py`, los añadidos de `test_f056_revision_dominio.py` y
  `test_f056_paginacion.py`, `test_f010_endpoints_protegidos.py`, el arreglo de
  `tests_bbdd/tests/test_f056_bbdd_revision.py`, `design.md` §3.5 y `tasks.md`.

## Nivel de rigor

`critico`, declarado en `harness/features.json`. Pide fase RED con la traza pegada, cobertura de lo cambiado ≥ 80 %,
mutación con **cero supervivientes** (salvo justificación aceptada por el humano) y las `MANUAL (humano)` con su
comando exacto. Además, la regla de orden (punto 7 del protocolo y O-5 del Bloque 1): bajar a mano la transición y
la frescura por debajo de cada lectura de Sigrid, y subir `registrar` por encima de `decidir`, y exigir rojo con los
tests de F-056.

## Lo que se ha ejecutado (resultados reales)

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` | **ENTORNO LISTO**, exit 0. `PUERTA COBERTURA: [OK] 100.0% de 1002 líneas cambiadas cubiertas (1002/1002, umbral 80%, nivel critico)`. Los servicios api y front salieron en verde **por caché**. ruff: 73 avisos de deuda previa |
| Sin caché (`-p no:cacheprovider`), desde `services/postventa-api`: todos los `test_f056_*`, `test_f006_repo_sin_identificadores.py`, `test_f010_endpoints_protegidos.py`, `test_f036_alcance_cerrado.py`, `test_f019_logs_sin_datos_personales.py`, `test_f005_integracion_sin_secretos.py` y todas las `test_f0*_arquitectura*` | **1150 passed, 9 skipped** en 93 s. Con `-rs` sobre los F-056, F-006, F-010 y F-036: **869 passed, 7 skipped**. Los 7 son los controles con `git` de F-036 («vive en feature/F-036… mientras no esté mergeada»). **Ningún** test de F-056 se salta: los controles con `git` de T13 se ejecutan |
| `ruff check` de los 9 ficheros nuevos o tocados del bloque | **All checks passed** |
| RED de T10 reproducido: `git archive 961d0ab` en el scratchpad, `pytest test_f056_pipeline_revision.py test_f056_revision_http.py` | **227 failed, 1 passed**, igual que el informe. **0** `ImportError`/`AttributeError`/`TypeError`/`IndexError`: son todos fallos de aserción o `DID NOT RAISE`, con los mismos grupos que pega el informe (76/49/7 de rutas, 8 de `cursor_de`…). La O-2 del Bloque 1 queda resuelta en este bloque |
| Recálculo puro: `harness.alcance.alcance_de_feature('F-056', base='e9e815f')` + `harness.mutacion.generar_mutantes` | 4 ficheros, **1247 líneas**, **77 mutantes**: borde 40, `function_app.py` 15, aplicación 11, dominio 11. Por operador: entero 23, comparación 15, lógico 15, `not` 11, booleano 7, aritmético 6. **Coincide** con el informe |
| Campaña de mutación | **No se ha reejecutado: 175 min según el informe (10501,5 s), más de 5 min**, y el encargo pide no relanzarla. Me quedo en el recálculo puro y en los mutantes a mano de abajo. Coste: 10501,5 × 8 / 77 ≈ **1091 s por mutante**, del orden de la suite en serie (836 s) con 8 workers compitiendo: coherente. Sin supervivientes, no hay ninguno que muestrear |
| `git status` al terminar | limpio. Todo se hizo en copias del scratchpad (`orden/` y `red/`), y comprobé con `diff` que la copia quedó restaurada tras cada mutante |

### Regla de orden (punto 7; O-5 del Bloque 1): 12 mutaciones de orden a mano

En una copia de `services/postventa-api` en el scratchpad. Para cada una, **solo los tests de F-056** y **sin `-x`**
(todos los `test_f056_*` salvo `test_f056_alcance_cerrado.py`, que necesita `git` y en la copia no lo hay; la línea
base de la copia da **772 passed**). Los dobles (`tests/utiles_revision.py`) anotan cada colaborador —`situacion`,
`leer_unidades`, `leer_oficios`, `ubicaciones`, `registrar`— en una lista común, y los tests fijan la secuencia
entera.

| # | Mutación | Resultado | Primeros tests de F-056 que caen |
|---|---|---|---|
| O1 | La puerta entera (`comprobar_sin_sigrid`: transición + frescura) baja **un paso**, por debajo de `leer_catalogo` | **ROJO**, 9 failed | `test_f056_r2_la_transicion_va_antes_que_sigrid_y_no_escribe[descartar-editar]`, `…r7_la_frescura_va_antes_que_sigrid…[None-editar]` |
| O2 | La puerta, por debajo de las **ubicaciones** (justo antes de `decidir`) | **ROJO**, 9 failed | los mismos |
| O3 | Solo la **transición** baja por debajo de Sigrid (la frescura se queda arriba) | **ROJO**, 3 failed | `test_f056_r2_la_transicion_va_antes_que_sigrid…` (`descartar-editar`, `descartar-aprobar`, `aprobar-aprobar`) |
| O4 | Solo la **frescura** baja por debajo de Sigrid (la transición se queda arriba) | **ROJO**, 6 failed | `test_f056_r7_la_frescura_va_antes_que_sigrid…` (editar y aprobar × `None`/2/7) |
| O5 | La frescura baja por debajo de `registrar` (fuera de `comprobar_sin_sigrid`; solo queda la de la transacción) | **ROJO**, 19 failed | `test_f056_r7_la_frescura_va_antes_que_sigrid…` (las cuatro acciones) |
| O6 | La transición baja por debajo de `registrar` (desaparece antes de escribir) | **ROJO**, 18 failed | `test_f056_r2_la_transicion_va_antes_que_sigrid…` (los seis casos) |
| O7 | `registrar` **por encima de `decidir`** (con una foto provisional de los vigentes) | **ROJO**, 14 failed | `…r13_valores_no_validos_leen_sigrid_y_no_escriben`, `…r16_sin_cambios_no_escribe`, `…r20_no_aprobable_lee_sigrid_y_no_escribe`, `…r18_motivo_de_501_no_escribe` |
| O8 | `registrar` por encima de **Sigrid** (y de `decidir`) | **ROJO**, 34 failed | `…r13_editar_lee_sigrid_una_vez_entre_la_situacion_y_registrar`, `…r20_aprobar_lee_sigrid_una_vez…` |
| L1 | En el listado, Sigrid **antes** del tope de 10.000 (R24: el 409 no debe leer Sigrid) | **ROJO**, 6 failed | `…r46_listar_lee_cada_cosa_una_vez_y_en_orden`, `…r24_mas_del_tope_es_bandeja_demasiado_grande_con_el_recuento` |
| E1 | `POST /api/revision/acciones` construye la revisión **antes** de comprobar el cuerpo (R5) | **ROJO**, 48 failed | `test_f056_r5_cuerpo_invalido_es_400_sin_construir_nada[…]` |
| E2 | `GET /api/revision` construye el catálogo **antes** de validar los parámetros (R23) | **ROJO**, 35 failed | `test_f056_r23_parametros_invalidos_son_400_sin_consultar[…]` |
| E3 | El historial construye la revisión **antes** de validar el UUID (R32) | **ROJO**, 4 failed | `test_f056_r32_historial_sin_uuid_es_400_sin_construir[…]` |

**Las 12 dan rojo con tests de F-056.** La puerta se ha bajado un paso por cada colaborador que dice preceder
(catálogo, ubicaciones, `registrar`) y la transición y la frescura se han bajado **por separado**. Ningún orden
depende de una suite vecina.

### Mutantes a mano (no de orden): lo más arriesgado

Misma copia, mismos tests.

| Mutante | Resultado | Lo mata |
|---|---|---|
| El log de la acción lleva el correo | muerto | `test_f056_r41_ningun_registro_lleva_oid_correo_ni_textos` |
| El log de la acción lleva el `oid` | muerto | el mismo |
| La fila de la acción lleva el `oid` | muerto | `test_f056_r10_el_oid_no_sale_en_ninguna_respuesta` |
| `clave_de_cursor` sin comprobar que es el cursor emitido | muerto | `…r25_un_cursor_manipulado…[bits-de-relleno-distintos]`, `[ultimo-caracter-cambiado]` |
| Sin el tope antes de decodificar | muerto | `…r25_un_cursor_mas_largo_que_el_tope_no_se_llega_a_decodificar[513…]` (el espía de `urlsafe_b64decode`) |
| Sin la comprobación del alfabeto | muerto | `…r25_un_cursor_fuera_del_alfabeto_no_se_llega_a_decodificar[relleno]` |
| `MAX_CURSOR = 1024` | muerto | `…r25_el_tope_del_cursor_es_el_del_texto_codificado` |
| `revision_previa` booleana admitida | muerto | `…r5_cuerpo_invalido…[previa-booleana]` |
| Claves de más admitidas | muerto | `…r5_cuerpo_invalido…[descartar-con-valores]` |
| El motivo no se comprueba en el borde | muerto | `…r5_cuerpo_invalido…[motivo-501]` |
| `_esperadas` sin la original al aprobar (R22) | muerto | `…r22_aprobar_una_duplicada_espera_tambien_la_ultima_de_su_original` |
| Tope `>` → `>=` | muerto | `…r24_justo_el_tope_no_es_demasiado` |
| `catalogo.ubicaciones` con el mapa entero, no por unidad del catálogo | muerto | `…r28_el_catalogo_para_editar` |
| `motivos` `()` en vez de `None` en descartar/recuperar (R8) | muerto | `…r18_descartar_no_lee_sigrid_y_motivos_es_none` |
| **`_uuid` sin exigir la forma canónica** (acepta llaves, `urn:` y sin guiones) | **SOBREVIVE** | ninguno: ver **N-2** |
| **El rechazo se registra con su motivo**, no solo con el código | **SOBREVIVE** | equivalente en la práctica: ver O-3 |

Además, **9 mutantes de los que genera la herramienta**, reejecutados uno a uno con `aplicar_mutante`: aplicación
6 y 10 (`leido[0]→[1]`; `APROBAR and → or` en las esperadas), dominio 5 (`> MAX_UBICACION → >=`), `function_app`
8 (`400 → 401` del cuerpo que no es JSON) y borde 3, 8, 22, 25 y 32 (`len(cursor) >= MAX_CURSOR`, `% 4 → % 5`, `<=`
→ `<` en las claves, `and → or` en la previa). **Los 9, muertos**, cada uno por un test de F-056.

## Lo que pedía comprobar el encargo

- **Orden de `aplicar_accion` (O-5 del Bloque 1).** ✔ El código sigue §7: `situacion` (404) →
  `comprobar_sin_sigrid` (409 transición, 409 frescura) → solo en editar y aprobar, `leer_catalogo` de la obra de la
  incidencia y la fuente de ubicaciones → `decidir` → `registrar` (segunda frescura) → la foto
  (`application/pipelines/revision.py` l.225–273). `comprobar_sin_sigrid` es la misma función que `decidir` repite:
  una sola regla. Las 12 mutaciones de orden dan rojo (tabla de arriba).
- **El cursor base64url (opción (a)).** ✔ `cursor_de` = base64url **sin relleno** del texto canónico, y el test fija
  la forma `eyJjIjoi…` y que no lleva `=`, `+` ni `/`. `clave_de_cursor` rechaza **antes de decodificar** lo que no
  es texto, pasa de `MAX_CURSOR = 512` (los 4/3 de `MAX_TEXTO_CLAVE` = 384, fijado por un test con la clave más larga
  posible) o se sale del alfabeto. Después: UTF-8 estricto, `clave_de_texto` y que el cursor sea **exactamente** el
  que emitiría el sistema (los bits de cola distintos se rechazan). Doce manipulaciones dan 400 y ninguna repite el
  cursor en la respuesta. `base64` no aparece en `domain/` ni en `application/`: la guardia de F-012 sigue en verde
  sin tocarse.
- **`tamano` booleano (O-3).** ✔ En el dominio (`paginar`, con test RED pegado) y en el borde: el borde solo acepta un
  `str` `[1-9][0-9]*` ≤ 200, y `test_f056_r23_o3_un_tamano_booleano_es_400_en_el_borde` lo fija llamando al handler
  con `True` y con `False`.
- **R5.** ✔ 48 cuerpos inválidos, uno por forma (incluidos `"true"`, `1`, `revision_previa: 0`, booleana y decimal,
  correo sin `@`, con blanco, con dos `@` y de 255, clave de otra acción, `valores` sin una clave o con una de más,
  motivo de 501). Todos dan 400 `peticion_invalida` con los **cuatro** constructores sustituidos por funciones que
  fallan si se llaman (`nada_se_construye`). Ningún mensaje repite el `oid`, el correo ni los textos. E1–E3 lo
  confirman.
- **R6–R11.** ✔ R6: 404 sin Sigrid ni escritura, en las cuatro acciones. R7: primera frescura sin Sigrid; segunda en
  `registrar`, con «otra persona» que guarda justo antes (editar, descartar y aprobar). R8: forma de fila; `motivos`
  calculados en editar y aprobar y `None` en descartar y recuperar, con los puertos de Sigrid **prohibidos**. R9:
  correo recortado, guardado y devuelto en el listado y en el historial. R10: el `oid` no está en ninguna de las seis
  respuestas (200, 409, 400, listado e historial); `SituacionDeRevision` no tiene campo donde llevarlo. R11: el
  correo no sale en ningún error (409, 409, 409, 400, 404). Ver **N-1** sobre la respuesta 200 de una acción.
- **R23–R33.** ✔ Ver la tabla de cobertura. R24: 10.001 → 409 con el recuento de `contar` y sin leer Sigrid;
  10.000 justos no es 409. R25: recorrer las páginas da cada fila **una vez** y en orden, y lee el catálogo una vez
  por página. R26: los filtros vuelven en la respuesta y se aplican en el servidor. R27: `resumen` sobre toda la obra,
  con los cuatro estados y los nueve motivos. R28: `catalogo.ubicaciones` es el mismo mapa que valida, por cada unidad
  del catálogo. R30: `ObraSinUnidades` 404, `ObraAmbigua` y `CatalogoSinVerificar` 409, y 503 sin Sigrid o sin base,
  en el listado **y** en las acciones. R31: el log del listado es exactamente
  `F-056 revision listada: obra=9901 tamano=2 total_filtrado=4 devueltas=2`.
- **R41 con `caplog`.** ✔ A nivel `DEBUG`, recorre editar, aprobar, editar, descartar con motivo, recuperar con otra
  persona, un 409, dos 400, el listado, el historial y un historial con un UUID inválido. Busca en cada registro el
  `oid` y el correo **de las dos personas**, la descripción, el detalle, el motivo y los nombres de unidad y de
  proveedor. Los rechazos se registran en `function_app.py` solo con su **código**.
- **R42, R43.** ✔ Dos personas actúan sin roles. La identidad sale del cuerpo y **no** de `x-ms-client-principal`
  aunque venga con otra persona.
- **Rutas en los tests que las enumeran.** ✔ `test_f010_endpoints_protegidos.py` ampliado sin quitar nada
  (`ENDPOINTS` + las tres rutas, 17 → 20, comentario explicado). `test_f056_s8_las_tres_rutas_anonimas_con_su_metodo`
  fija ruta, método y `ANONYMOUS` de cada una. Es el único test que cuenta las rutas de `function_app.py` (lo he
  buscado). Los que cuentan los anónimos **de `docs/INTEGRACION.md`** son del Bloque 4: ver **O-1**.
- **T13.** ✔ `test_f056_alcance_cerrado.py` sigue el patrón de F-036. Usa la base fija `f86d639`, el diff hasta el
  árbol de trabajo y las tres guardas de F-030. Tiene una mitad con `git` y otra sin él, y controles negativos de
  cada detector (lista vacía, docstrings, `FOR UPDATE`). Qué fija cada requisito:
  - R39: ninguna escritura de la pasarela en las líneas añadidas ni en el código de F-056; no importa
    `escrituras`/`graficos`; de `infrastructure/sigrid` solo usa `construir_catalogo_obra`.
  - R40: ni «habilitado» ni `environ`/`getenv`, y la rama no toca la configuración.
  - R37: ni `UPDATE` (salvo `FOR UPDATE`), ni `DELETE`, ni `TRUNCATE`; DDL solo en el `15_` y en `postventa`.
  - R45 y §12: los intocables sin cambios, ningún test de F-036 salvo `test_f036_ddl.py`, ni de F-053, ni el front,
    ni `infra/`; las funciones de F-036/F-053 en `function_app.py` idénticas a la base; la fábrica de Sigrid solo
    puede ganar funciones.
  - R12: solo el `15_` declara una columna de correo.
  - **La nota de O-5 del Bloque 2** está escrita en la cabecera y en `test_f056_r37_o5_la_guardia_no_barre_las_suites_y_por_que`:
    `tests_bbdd/` no es código, y su `DELETE` de limpieza va contra la base efímera. El test fija que ese `DELETE`
    existe y que `_es_codigo` no lo cuenta.
- **Ningún GUID, secreto, correo ni proveedor real.** ✔ He barrido las líneas añadidas desde `e9e815f` buscando
  GUIDs, correos, IPs, `password`/`secret`, `ruesma`, `S.L.` y `S.A.`. Solo salen nombres de tests y los ficticios
  «Carpintería Ejemplo, S.L.», «Maderas Ejemplo, S.A.» y «Otro nombre, S.L.». Los correos son `@ejemplo.invalid`,
  los identificadores `UUID(int=n)` y los `oid` opacos sin forma de GUID. `test_f006_repo_sin_identificadores` y
  `test_f005_integracion_sin_secretos` están en verde sin caché.
- **N-1 del Bloque 2, opción (b).** ✔ `decidir`, al aprobar y tras los motivos, aplica `_exigir_volcable` (la misma
  función que `CandidataAlVolcado.__post_init__`) y lo traduce a 409 `incidencia_no_aprobable` con
  `ubicacion_fuera_de_lista`, sin repetir la ubicación. Hay RED pegado con 4 casos de «sin recortar» y un control
  positivo. En la aplicación, `test_f056_n1_…` fija que el listado sigue sin motivos (R47 no cambia), que no se llama
  a `registrar` y que `candidatas_al_volcado` no revienta. En el borde da 409 y no 200. Nota en `design.md` §3.5.

## Checkpoints (lo que aplica a un bloque intermedio)

**C1**
- [x] `init.sh` termina con exit 0.
- [x] Existen los ficheros del arnés.

**C2**
- [x] Una sola feature `in_progress` (F-056).
- [x] La rama es la de la feature.
- N/A `progress/current.md` solo con la sesión activa: es una exigencia de cierre y este es un bloque intermedio.
  Sigue arrastrando el bloque de F-053; es la O-6 del Bloque 1, que limpia el líder al cerrar.
- N/A Resumen en `history.md`: F-056 no está `done`.

**C3**
- [x] Arquitectura hexagonal. `application/pipelines/revision.py` solo importa del dominio, de sus puertos y de otros
  pipelines (`catalogo_obra`, `plantilla`). La composición de adaptadores (`construir_*`, `obtener_ajustes`, el YAML)
  vive en `interface_adapters/api/revision.py`. El base64url está en el borde. Las guardias de arquitectura pasan sin
  caché.
- [x] Primera línea con la ruta en los 6 ficheros nuevos.
- [x] Sin `print`, sin TODOs ni FIXMEs en las líneas añadidas, sin secretos y sin dependencias nuevas.
- N/A Unidad «parte», «nada se archiva sin validaciones», lo manuscrito, firmado ≠ conforme, reprocesar no duplica y
  `conest`: este bloque no toca partes, firmas, archivo ni estados de Sigrid. Lee Sigrid solo por las dos lecturas de
  F-036 y no escribe en él (R39, fijado por T13).
- [x] Ningún escaneado, PDF ni ofimática añadido (`git log --diff-filter=A e9e815f..HEAD`: ninguno).

**C3 bis** · N/A: el bloque no toca `docs/referencia/` (no hay nada bajo `docs/` en el diff).

**C4**
- [x] Cada requisito de este bloque tiene su test y todos pasan (tabla de abajo).
- [x] Los unit tests no tocan red ni BBDD: dobles en memoria (`RevisionEnMemoria`, `CatalogoDeLaObra`,
  `UbicacionesQueCuentan`), con las fábricas del borde sustituidas.
- [x] MANUAL listadas. T8 está hecha y en verde. Las de este bloque: ninguna. T18 y T19 siguen pendientes en
  `tasks.md` con su comando exacto.

**C4 bis**
- [x] `rigor: critico` declarado.
- [x] Fase RED: pegada (N-1, O-3 y T10) y **reproducida** la de T10 (227 failed, 1 passed, todos de aserción).
- [x] Cobertura: `[OK]` 100 % (1002/1002) en `init.sh`. El informe cuenta además que la primera ejecución dio 99,1 %
  y cómo se cubrieron los tres caminos (`738f583`, solo tests).
- [x] Mutación: existe `progress/mutacion_F-056_bloque3.md`, generado por la herramienta. Alcance (4 ficheros,
  1247 líneas) y número de mutantes (77, por fichero y por operador) recalculados: coinciden.
- [x] Muertos: **campaña no reejecutada, 175 min según el informe (más de 5 min)**. Me quedo con el recálculo puro, 9
  mutantes de la herramienta reejecutados a mano (los 9 muertos) y 28 mutantes propios (12 de orden y 16 de riesgo).
  De los propios sobreviven dos: N-2 y O-3. Los dos quedan **fuera** de lo que genera la herramienta.
- [x] Duración: ≈ 1091 s por mutante con 8 workers, del orden de la suite. Coherente.
- [x] Cero supervivientes y cero timeouts en la campaña. Los dos equivalentes que se veían venir se quitaron **del
  código** antes de lanzarla (decisión 16), no de los tests. Ninguno queda pendiente de justificar.
- [x] «Evidencias» con los cuatro números (tests, cobertura de lo cambiado, mutantes y supervivientes, tiempo de la
  suite) y los workers (8).
- [x] Ningún N/A sin motivo.

**C4 ter** · N/A: el repositorio no tiene `harness/rutas_sensibles.json`.

**C5** (de bloque)
- [x] T10–T14 marcadas, cada una con su commit `F-056 Tn:`. N-1, O-3, el arreglo de T8 y la O-1 van en commits
  `F-056:` aparte, como en los bloques anteriores. N/A «todas las tareas `[x]`»: T14a en adelante son de otros
  bloques.
- [x] Sin ficheros temporales ni sin trackear (`git status` limpio).
- [x] `features.json`: F-056 `in_progress`, que es lo que corresponde.

## Cobertura: requisito → test (los de este bloque)

| R | Test(s) de F-056 |
|---|---|
| §7 orden | `test_f056_r13_editar_lee_sigrid_una_vez_entre_la_situacion_y_registrar`, `…r20_aprobar_lee_sigrid_una_vez…`, `…r2_la_transicion_va_antes_que_sigrid_y_no_escribe`, `…r7_la_frescura_va_antes_que_sigrid_y_no_escribe`, `…r13_valores_no_validos_leen_sigrid_y_no_escriben`, `…r16_sin_cambios_no_escribe`, `…r20_no_aprobable_lee_sigrid_y_no_escribe` |
| R2 | `…r2_la_transicion_va_antes_que_sigrid…`, `…r2_accion_no_permitida_dice_el_estado_y_las_posibles`, `…r2_accion_no_permitida_es_409_con_estado_y_acciones` (http) |
| R3, R34 | `…r3_editar_una_aprobada_la_saca_de_las_candidatas`, `…r34_candidatas_solo_las_de_ultima_aprobar` |
| R4 | `…r4_se_registra_la_foto_quien_y_la_hora` |
| R5 | `…r5_cuerpo_invalido_es_400_sin_construir_nada` (48 casos), `…r5_un_cuerpo_que_no_es_json_es_400`, `…r5_motivo_de_500_y_nulo_valen`, `…r5_incidencia_id_en_mayusculas_vale` |
| R6 | `…r6_incidencia_que_no_esta_es_404_sin_sigrid_ni_escritura` (aplicación, 4 acciones), `…r6_…_404_sin_sigrid` (http) |
| R7, R22 | `…r7_si_otra_persona_guarda_entre_medias_no_se_escribe`, `…r7_registrar_espera_la_ultima_de_la_propia`, `…r7_la_primera_revision_espera_ninguna`, `…r22_aprobar_una_duplicada_espera_tambien…`, `…r22_si_la_original_cambia_entre_medias_no_se_aprueba`, `…r22_solo_aprobar_espera_la_original`, `…r22_la_duplicada_con_la_original_viva_no_se_aprueba`, `…r7_previa_vieja_es_409…` (http) |
| R8 | `…r8_la_foto_nueva_es_la_situacion_con_la_revision_guardada`, `…r8_editar_devuelve_la_fila_con_motivos`, `…r8_descartar_y_recuperar_dan_motivos_null_sin_construir_sigrid`, `…r8_aprobar_da_la_aprobada_con_motivos_vacios`, `…r18/r19_…_motivos_es_none` |
| R9–R11 | `…r9_el_correo_se_guarda_recortado_y_sale_en_listado_e_historial`, `…r10_el_oid_no_sale_en_ninguna_respuesta`, `…s8_las_situaciones_no_llevan_el_oid`, `…r11_el_correo_no_sale_en_ningun_error` |
| R13–R16 (aplicación y borde) | `…r13_valores_no_validos_es_400_con_todos_los_campos`, `…r13_ubicacion_vacia_es_error_y_no_nula`, `…r48_la_ubicacion_se_valida_contra_el_mapa_leido_de_su_unidad`, `…r16_sin_cambios_es_400`, `…r13_el_catalogo_se_pide_para_la_obra_de_la_incidencia` |
| R18, R19 | `…r18_descartar_no_lee_sigrid…`, `…r19_recuperar_no_lee_sigrid…`, `…r18_motivo_de_501_no_escribe` |
| R20, N-1 | `…r20_no_aprobable_es_409_con_sus_motivos`, `…r20_aprobar_guarda_los_vigentes_sin_cambiarlos`, `…n1_aprobar_una_ubicacion_sin_recortar_es_409…` (aplicación y http) |
| R23 | `…r23_parametros_invalidos_son_400_sin_consultar` (20 casos), `…r23_sin_obra_es_400`, `…r23_o3_un_tamano_booleano_es_400_en_el_borde`, `…r23_tamanos_validos` |
| R24 | `…r24_mas_del_tope_es_bandeja_demasiado_grande_con_el_recuento`, `…r24_justo_el_tope_no_es_demasiado`, `…r24_mas_de_diez_mil_es_409_con_el_recuento` |
| R25 | `…r25_el_cursor_es_base64url_sin_relleno_de_la_clave`, `…r25_cursor_de_y_clave_de_cursor_son_inversos`, `…r25_recorrer_las_paginas_da_cada_fila_una_vez_y_en_orden`, `…r25_un_cursor_manipulado_es_400_sin_consultar` (12), `…r25_el_tope_del_cursor_es_el_del_texto_codificado`, `…r25_un_cursor_mas_largo_que_el_tope_no_se_llega_a_decodificar`, `…r25_un_cursor_fuera_del_alfabeto…`, `…r25_ida_y_vuelta_del_cursor_con_cualquier_relleno`, `…r25_los_cursores_de_prueba_cubren_todas_las_colas` |
| R26, R27 | `…r26_los_filtros_los_aplica_el_servidor`, `…r26_los_filtros_vuelven_en_la_respuesta`, `…r27_resumen_de_toda_la_obra_y_pagina_filtrada`, `…r27_la_respuesta_lleva_lo_de_r27` |
| R28, R48 | `…r28_la_pagina_lleva_el_catalogo_leido_y_el_mismo_mapa_que_valida`, `…r28_el_catalogo_para_editar`, `…r28_un_grupo_de_oficios_confirmado…`, `…r48_lo_que_se_ofrece_es_lo_que_se_valida` |
| R29 | `…r29_una_fila_sin_revisiones`, `…r29_una_fila_revisada_y_duplicada` |
| R30 | `…r30_los_rechazos_de_la_obra`, `…r30_sin_sigrid_o_sin_base_el_listado_es_503`, `…r30_una_sola_lectura_del_catalogo_por_peticion`, `…r30_una_accion_con_la_obra_sin_unidades_es_404`, `…r30_una_accion_con_la_obra_ambigua_o_al_techo_es_409`, `…r30_sin_sigrid_no_se_escribe`, `…r30_sin_configuracion_editar_es_503_sin_escribir`, `…r30_descartar_no_necesita_la_configuracion_de_sigrid`, `…r30_la_configuracion_de_la_plantilla_rota_es_500` |
| R31 | `…r31_el_log_del_listado_solo_lleva_obra_tamano_y_recuentos` |
| R32, R33 | `…r32_historial_sin_uuid_es_400_sin_construir`, `…r32_historial_sin_parametro_es_400`, `…r32_historial_de_una_que_no_esta_es_404_sin_sigrid`, `…r32_el_historial_sin_base_es_503`, `…r33_historial_completo`, `…r33_historial_sin_revisiones`, `…r33_historial_con_los_campos_cambiados_frente_a_la_anterior` |
| R41 | `…r41_ningun_registro_lleva_oid_correo_ni_textos` (`caplog` a `DEBUG`) |
| R42, R43 | `…r42_cualquiera_del_grupo_puede_actuar_sin_roles`, `…r43_la_identidad_sale_del_cuerpo_y_no_de_las_cabeceras` |
| R46 (parte del Bloque 3) | `…r46_listar_lee_cada_cosa_una_vez_y_en_orden`, `…r25_recorrer_las_paginas_lee_sigrid_una_vez_por_pagina`, `…r46_editar_y_aprobar_sin_sus_lecturas_es_un_error_de_programacion`, `…t12_sin_la_lectura_de_ubicaciones_compuesta_es_503` |
| R12, R37, R39, R40, R45, §12 | los 22 de `test_f056_alcance_cerrado.py` (T13) |
| §8 rutas | `…s8_las_tres_rutas_anonimas_con_su_metodo`, `test_f010_endpoints_protegidos.py` (20) |

## Hallazgos

### Bloqueantes

Ninguno.

### Menores (no bloquean este bloque)

1. **N-1 · R8 y R11 se contradicen sobre el correo en la respuesta de una acción, y la spec aún no lo resuelve.**
   - R8 pide que `POST /api/revision/acciones` devuelva «la incidencia en la forma de una fila de `GET /api/revision`
     (R29)», y esa fila lleva `revisado_por` = correo.
   - R11 dice que el correo no sale «en ninguna otra respuesta que las dos de R10», y R10 solo nombra el listado y
     el historial.
   - El implementer siguió R8 (`interface_adapters/api/revision.py` l.599, `_fila`, que también usa
     `_fila_revisada` l.573) y lo dejó abierto al líder (decisión 1 del informe). `test_f056_r9_…` (l.615) fija
     ya `fila["revisado_por"] == CORREO` en la respuesta 200.

   La lectura de R8 me parece la buena: el correo que vuelve es el de quien acaba de actuar, el mismo que mandó en el
   cuerpo, y ningún **error** lo lleva. Pero es una contradicción de la spec, y la documentación del Bloque 4 (R44,
   `INTEGRACION.md` §7 «quién lo ve») tiene que contar una de las dos.
   **Qué hacer:** que el líder decida, **antes del Bloque 4**, y que se anote en la spec:
   - si se mantiene R8, una nota en `design.md` §9 («Lo que cambia») y en R11 que añada la respuesta 200 de
     `POST /api/revision/acciones` como tercera respuesta con correo (el de quien actúa);
   - si se prefiere R11 literal, `revisado_por: null` en `_fila_revisada` y cambiar la aserción de `test_f056_r9_…`.

2. **N-2 · La forma canónica del `incidencia_id` (decisión 9) no la fija ningún test.**
   `interface_adapters/api/revision.py` l.537–547 (`_uuid`) acepta solo el texto con guiones, en mayúsculas o
   minúsculas: rechaza `{…}`, `urn:uuid:…` y los 32 hexadecimales sin guiones, con `str(identificador) == crudo.lower()`.
   He sustituido esa comprobación por `True` y la suite de F-056 sigue en verde (772 passed). La herramienta solo
   generó `== → !=` (muerto), así que la campaña no lo ve. Es un comportamiento que el informe declara y que comparten
   `POST /api/revision/acciones` y `GET /api/revision/historial`.
   **Qué hacer** (en el Bloque 3 bis, en un commit `F-056:` aparte; es barato):
   - añadir a `CUERPOS_INVALIDOS` de `test_f056_revision_http.py` (l.289 y siguientes) los casos
     `incidencia-con-llaves` (`"{" + str(UUID(int=1)) + "}"`), `incidencia-urn` (`UUID(int=1).urn`) e
     `incidencia-sin-guiones` (`UUID(int=1).hex`);
   - añadir los mismos tres valores a la parametrización de `test_f056_r32_historial_sin_uuid_es_400_sin_construir`
     (l.1205–1206).

### Observaciones (no son cambios requeridos)

- **O-1 · Choque que llega en el Bloque 4: «diecisiete» → «veinte» en `docs/INTEGRACION.md` §8 frente a R45.**
  T15 manda escribir «veinte» en §8. Pero hay tests de **otras features** que fijan la frase actual:
  - `test_f053_documentacion.py` l.42 (`DIECISIETE = "Los diecisiete quedan en nivel"`) y l.118 (`assert DIECISIETE in
    endpoints`);
  - `test_f019_documentacion.py` l.180;
  - `test_f012_documentacion.py` l.170–180.

  R45 dice que los tests de F-053 «siguen en verde **sin tocarse**», y `test_f056_r45_la_rama_no_toca_los_tests_de_f036_ni_de_f053`
  lo hará cumplir. T15 solo prevé citar los de **F-036**. Así que, tal como está escrita, T15 no puede cumplir a la
  vez «veinte» y R45. El líder debe decidir **antes de encargar el Bloque 4**: o una excepción escrita en R45 y en
  `TESTS_DE_F036_AMPLIADOS` para `test_f053_documentacion.py` (ampliar sin relajar, como hizo T4 con
  `test_f036_ddl.py`), o una redacción de §8 que conserve la frase de F-053.
- **O-2 · Lo que el Bloque 3 bis tiene que sustituir, no solo añadir.** Hasta el 3 bis, en un entorno real,
  `construir_fuente_de_ubicaciones` da 503 en listar, editar y aprobar (decisión 2, deliberada y fijada por
  `test_f056_t12_sin_la_lectura_de_ubicaciones_compuesta_es_503`). Esa rama no se puede publicar sin el 3 bis. Al
  componer el puerto real, el 3 bis tiene que **reemplazar** ese test y ampliar en T13 `NUEVOS_DE_F056` y
  `test_f056_r39_de_sigrid_solo_se_usa_el_catalogo_de_f036`, que hoy fija que de `infrastructure/sigrid` solo se usa
  `construir_catalogo_obra`. La review del 3 bis debe comprobar que el 503 ha desaparecido de producción.
- **O-3 · El rechazo se registra solo con su código, pero ningún test lo distingue de registrarlo con su motivo.**
  `function_app.py`, `_error_de_revision`: `log.info("%s no procede: %s", que, codigo)`. Si se le añade
  `error.motivo`, la suite sigue en verde. Hoy es **equivalente en la práctica**: todos los motivos de
  `PeticionDeRevisionInvalida`, `ValoresNoValidos` y compañía son constantes del dominio que no repiten nada de lo
  recibido (lo he revisado en `domain/models/revision.py`), y el test de R41 ya busca el `oid`, el correo y los
  textos en cada registro. No pido cambio. Lo dejo escrito por si algún día un motivo empieza a llevar lo recibido.
- **O-4 · `init.sh` dio los servicios en verde por caché** (el patrón de F-055). Por eso aquí se han reejecutado sin
  caché todos los tests de F-056 y las guardias (1150 passed). La suite completa sin caché es la del informe
  (7502 passed en `1c5da05`, y 7506 en el `init.sh` de `738f583`).
- **O-5 · Arrastradas.** La O-6 del Bloque 1 (`progress/current.md` con el bloque de F-053) sigue para el cierre.
  La O-2 del Bloque 2 (`_Transaccional` privado) no cambia.

## Propuestas de automejora (para el humano; no aplicadas)

1. **`reviewer.md`, punto 7 (regla de orden).** Ampliarlo a la puerta de **«validar antes de construir»**:
   «comprobar la petición entera antes de construir ningún adaptador» (R5, R23 y R32 aquí) es también un orden entre
   colaboradores, y la herramienta tampoco lo ve. En este bloque, E1–E3 (subir un `construir_*` por encima de la
   validación) son lo único que demuestra que los tests con fábricas prohibidas protegen ese orden. Vale para
   cualquier proyecto: si se aprueba, portarla a `arnes-base`.
2. **`spec-author.md` (o `specs/SPECS.md`).** Cuando una spec cambia una frase de un documento compartido (aquí, la
   cuenta de endpoints anónimos de `INTEGRACION.md`) y a la vez exige que los tests de otras features sigan «sin
   tocarse», el spec-author debería buscar (`grep`) qué tests fijan esa frase y declarar la excepción en la propia
   spec, como hizo T4 con `test_f036_ddl.py`. Si no, el choque aparece a mitad del trabajo (O-1). También es
   genérica: si se aprueba, va a `arnes-base`.
