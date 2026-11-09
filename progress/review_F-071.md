<!-- progress/review_F-071.md -->
# F-071 · Review de los Bloques 1 a 3 (opción (d))

- **Veredicto:** **CHANGES_REQUESTED**, por un solo motivo de proceso (C-1): los tres mutantes
  equivalentes siguen **pendientes de la aceptación escrita del humano**, y en rigor `critico` eso es
  un `[ ]` de C4 bis (`CHECKPOINTS.md:184-191`). **No hay ningún cambio de código ni de tests que
  pedir.** En cuanto conste esa aceptación, este bloque queda en APPROVED sin otra pasada de código
  (mismo precedente que C-3 de `progress/review_F-060_bloque1.md`).
- **Reviewer:** subagente reviewer, 2026-11-06.
- **Worktree / rama:** `postventa-f071`, `feature/F-071-plantilla-desde-sigrid`, HEAD `74a851a`.
- **Base fija:** `dev` `ed935ad`. Rango revisado: `ed935ad..74a851a` (19 commits).
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige: fase RED con la traza
  pegada, cobertura de las líneas cambiadas ≥ 80 %, campaña de mutación con **cero supervivientes**
  salvo aceptación escrita del humano, y mutantes de orden a mano (regla 7 del protocolo).

## Lo que se ha comprobado (resultados reales)

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual, en el worktree) | Código de salida 0, `ENTORNO LISTO`. `PUERTA COBERTURA: [OK] 100.0% de 232 líneas cambiadas cubiertas (232/232, umbral 80%, nivel critico)`. El pytest del servicio salió por caché («árbol sin cambios desde el último verde») |
| Suite del servicio, lanzada aparte por el reviewer para no fiarse de la caché (`pytest -q -x`) | **9860 passed, 447 skipped** en 13 min 46 s, exit 0 |
| Alcance recalculado con `harness.alcance` | 14 ficheros, **773** líneas de producción: coincide con `progress/mutacion_F-071.md` |
| Mutantes recalculados con `harness.mutacion.generar_mutantes` (cálculo puro) | **66**: coincide. Los 4 supervivientes existen como mutantes reales con el mismo operador y el mismo texto: `excel_openpyxl.py:401` `entero` (`+ 2`→`+ 3`), `:405` `aritmetico` (`- 1`→`+ 1`), `:405` `entero` (`- 1`→`- 2`), `:426` `entero` (`+= 3`→`+= 4`) |
| Producción entre `c633a14` (campaña) y HEAD | sin cambios (`git diff --stat c633a14..HEAD`: solo `progress/`, `tasks.md` y `tests/test_f071_generador.py`). La campaña vale para HEAD |
| Campaña reejecutada | **No**: 26 408,9 s (7 h 20 min) según el informe, muy por encima de 5 min, y el encargo prohíbe relanzarla. **Verificación aplicada: recálculo puro + los mutantes dudosos a mano** |
| Coste por mutante | 26 408,9 × 8 ÷ 66 ≈ **3 201 s**, coherente con una suite de 25–65 min: no sospechoso |
| Mutantes de `excel_openpyxl.py` repetidos **a mano** por el reviewer (copia desechable en el scratchpad, `test_f071_generador.py` + `test_f036_excel_generador.py`) | control `263 passed`; `:405 +1` **muerto** (`1 failed, 262 passed`, `assert ((None, None), (None, None)) == ((None, None),)`, el test de `d0dc548`); `:405 −2` vivo (`263 passed`); `:401 +3` vivo (`263 passed`); `:426 +=4` vivo (`263 passed`) |
| Mutantes de **orden** a mano (regla 7), solo con `test_f071_pipelines.py` y `test_f071_http.py` | tabla en «Orden» abajo: todos en rojo salvo O2, que lo caza un test de F-036 adaptado por F-071 |
| Secretos, GUID, IP, `print`, binarios en el diff | ninguno (`git diff ed935ad..HEAD` filtrado por GUID, `password=`, `AccountKey`, IP privadas, `print(`, `.xlsx/.pdf/.env`) |
| Escritura en Sigrid / red / BBDD en tests | ninguna: el diff no toca `infrastructure/sigrid/**` ni `infrastructure/persistencia/**`; los tests usan dobles (`UbicacionesEnMemoria`, `UbicacionesQueCuentan`) y `monkeypatch` de `construir_fuente_de_ubicaciones` |
| Primera línea con la ruta en los ficheros añadidos o modificados de `services/` | todos la llevan |
| Scratchpad | las dos copias (`git worktree add --detach`) se retiraron; `git status` del worktree de trabajo limpio salvo este informe |

## 1 · Requisitos de los Bloques 1 a 3 → código y test

R42, R43 y R45 (su test de alcance), R46 y R47 son del Bloque 4 y 5 (T11, T16): fuera de esta review,
salvo lo que T9 adelantó de R45.

| R | Código | Tests (F-071 salvo que se diga) |
|---|---|---|
| R1 | `application/pipelines/plantilla.py` `generar_plantilla`; `interface_adapters/api/plantilla.py:73-82` | `test_f071_r1_catalogo_y_despues_una_lectura_de_ubicaciones`, `test_f071_r1_descargar_plantilla_con_las_ubicaciones_inyectadas`, `test_f071_r1_por_defecto_la_fuente_de_la_revision_construida_tras_el_catalogo`; F-036 `test_f036_r1_la_plantilla_lee_el_catalogo_las_ubicaciones_y_genera` |
| R2 | sin `EquivalenciasPort` en plantilla (borde y aplicación) | `test_f071_r2_la_plantilla_no_lee_equivalencias`, `test_f071_r2_descargar_plantilla_sin_equivalencias_y_con_ubicaciones` |
| R3 | errores suben de `leer_ubicaciones_validas` | `test_f071_r3_la_lectura_de_ubicaciones_que_falla_no_da_fichero` (×2), `test_f071_r3_la_ruta_de_la_plantilla_sin_fichero` (409/503) |
| R4 | sin cambio | `test_f071_r4_unidad_sin_cambio` |
| R5–R7 | `excel_openpyxl.py` `_ubicaciones` y `_validacion` | `test_f071_r5_*` (×2), `test_f071_r6_*`, `test_f071_r7_*` (×3, con el refuerzo de `d0dc548`) |
| R8 | `plantilla_incidencias.py` `ubicaciones_de_la_plantilla` | 14 `test_f071_r8_*` (dominio y libro, determinista con barajados) |
| R9–R11 | `_catalogos`, nombres, `_texto` | `test_f071_r9_*` (×4), `test_f071_r10_*`, `test_f071_r11_*` |
| R12–R15 | `oficios_del_desplegable`, `pares_del_desplegable`, `_exigir_distintas` (dominio y generador) | `test_f071_r12_*` (×4), `r13` (×4), `r14` (×10), `r15` (×4) |
| R16–R19 | `config/plantilla_incidencias.yaml`, `plantilla_yaml.py` | `test_f071_r16_*` (×2), `r17` (×2), `r18` (×5), `r19` (×2) |
| R20 | medido: 66 KiB, 12 entradas, 0,8 MiB, 29 085 elementos XML | `test_f071_r20_*` |
| R21, R22 | `plantilla_yaml.py` rechaza `ubicaciones`; `ListasCerradas` sin el campo | `test_f071_r21_*` (×3), `test_f071_r22_*` (×2) |
| R23 | `importacion.py` `reconocer_plantilla` (`version_anterior`) | `test_f071_r23_*` (×6, dominio y borde, con el texto literal) |
| R24, R25 | `paso_catalogo`, `importar.py:201-213` | `test_f071_r24_*` (×7), `test_f071_r25_*` (×2) |
| R26–R31 | `_Fila.ubicacion` | `test_f071_r26`…`r31` (14 en total) |
| R32–R35 | `_elegido_de_oficio`, `_elegido_de_proveedor`, `_fila` | `test_f071_r32_*` (×2), `r33` (×3), `r34`, `r35` (recorre las 30 combinaciones) |
| R36–R39 | `_Fila.tasado` con `casar_con_lista` | `test_f071_r36_*` (×20, incluidos los de `casado_con_lista`), `r37` (×6), `r38`, `r39` (×4) |
| R40 | `paso_excel_errores` con lo del contexto | `test_f071_r40_*` (×2); F-036 `test_f036_r62_el_excel_de_errores_usa_el_mismo_catalogo_y_opciones` |
| R41 | clave sin cambio | `test_f071_r41_*` (×2) |
| R44 | logs con recuentos | `test_f071_r44_*` (×2, con `caplog`) |
| R45 (T9) | 5 ficheros retirados con `git rm`; nota en `docs/ARCHITECTURE.md:922-930` | F-036 `test_f036_r46_los_bloques_7_y_8_tambien_estan_en_el_control` (los dos scripts no existen) |

No se ha adelantado lógica de fuera del alcance: ni `Listado` de `auxtrcp` (F-072), ni urgencias
internas, ni cambios en revisión, volcado, equivalencias, persistencia, `infrastructure/sigrid/**` ni
`services/postventa-front/**` (ninguno aparece en `git diff --stat ed935ad..HEAD`).
`opciones_de_la_obra` se queda solo para la revisión, como manda `design.md` §6.3.

## 2 · Tests de F-036, F-053, F-056 y F-060 adaptados o retirados

Recorrido con `comm` de las funciones `test_*` de `ed935ad` frente a HEAD, fichero a fichero, y el diff
de las aserciones.

- **`test_f036_configuracion_plantilla.py`: 17 tests retirados.** Coinciden uno a uno con la lista de
  `progress/impl_F-071.md` (tanda 1, «Retirados»). Todos fijaban **la lista de ubicaciones del YAML**
  (contenido de la 0677, fusiones, añadidas de T6/T25, orden «General»/«Otra») o **la validación de la
  sección `ubicaciones`** (48 caracteres, vacías, repetidas, `origen`, `revisar`). `design.md` §3.2
  permite retirar sin sustituta justamente esas («salvo las de la lista del YAML (R21)»). La regla que
  protegían y sigue viva tiene sustituto: el tope de 48, vacía y blancos pasan al dominio
  (`ubicaciones_de_la_plantilla`, `test_f071_r8_*` con 48/49, vacía y blancos) y a F-056
  (`ubicaciones_de_tipologia`, que ya filtraba). La clave `ubicaciones` tumba la carga
  (`test_f071_r21_*`). **Nada debilitado.**
- **`test_f036_importacion_dominio.py`.** Cada caso que sale de un `parametrize` sale porque ahora casa
  por R36/R28 y pasa a un test positivo nuevo (`test_f036_r26_unidad_casada`,
  `test_f036_r29_ubicacion_casada`, `test_f071_r36_*`). Los motivos cambian por R37 o R29 con su
  comentario. Los de ambigüedad (R93, R75) se sustituyen por aserciones **más fuertes** (código
  concreto, `ambiguo=False`, avisos vacíos, y P2 en dos oficios da dos pares resueltos). En
  `test_f036_r24_r33_…` los valores que ya casarían se cambian por otros que no casan («Patio», «Muy
  urgente»), para que la fila siga con error en todas sus columnas. Es correcto.
- **`test_f036_pipeline_importacion.py`, `test_f036_plantilla_http.py`, `test_f036_importar_http.py`.**
  10 tests renombrados con su sustituto en el mismo fichero (tablas de la tanda 2 del informe). Las
  aserciones de grupos pasan a «por código aunque haya grupo», que es justo lo que R12 y D-14 cambian.
  `test_f036_r82_…` sigue probando la misma regla directamente sobre `opciones_de_la_obra`, que solo
  usa la revisión. `test_f036_r11_sin_sigrid_o_sin_base_es_503` pierde el caso de la base porque la
  plantilla ya no la lee (R2), y lo sustituye el de ubicaciones caídas.
- **`test_f036_excel_lector.py`:** `test_f036_r18_version_2_no_soportada` →
  `test_f036_r18_version_3_no_soportada` (la 2 es la soportada; la 1 la cubre `test_f071_r23_*`).
- **`test_f056_revision_dominio.py`, `tests/utiles_revision.py`:** solo quitan `ubicaciones=` de
  `ListasCerradas` (R22).
- **`test_f060_importar_normaliza.py`, `test_f060_importacion_diferida.py`:** `equivalencias=` →
  `ubicaciones=`, con una fuente propia para la validación (`UBICACIONES_AL_IMPORTAR`). La de la
  normalización posterior (`LISTAS_DE_SIGRID`) no cambia, y las aserciones de F-060 no cambian.
- **`test_f053_importado_at_utc.py`:** sin cambios, y en verde.
- **Migración (T9, R45).** `test_f036_migracion.py` y `test_f036_migracion_contenido.py` se retiran con
  sus scripts, que es lo que decide R45/D-6. En `test_f036_alcance_cerrado.py` la aserción «los
  scripts están en el control» pasa a «no existen y no están en la lista» (`:357-359`), que es la
  forma correcta tras retirarlos. La nota de `docs/ARCHITECTURE.md:922-930` es exacta: los scripts
  existen en `4a0bdaa` y no en su padre, y siguen en `ed935ad`.

## 3 · La lectura de Sigrid en la importación (T8)

- Es la fuente de F-056 sin una letra cambiada: `construir_fuente_de_ubicaciones` de
  `interface_adapters/api/revision.py:182-190` → `leer_ubicaciones_validas`
  (`application/pipelines/revision.py:147-172`), sobre el adaptador `infrastructure/sigrid/ubicaciones_validas.py`
  (lee por `POST /api/sql/read`, `max_rows` 1 000) y `catalogo_obra.py:212`, que mira `truncated`.
  `llego_al_techo` → `CatalogoSinVerificar` (409); cortada o caída → `CatalogoNoDisponible` (503).
  **Solo lectura; ningún fichero de `infrastructure/sigrid/` tocado.**
- La fuente se construye en `importar.py:206`, dentro de `if not contexto.ya_importado:` y después de
  `paso_reconocimiento` (`:200`): ni con un fichero que no es la plantilla, ni con una v1, ni con
  `ya_importado`. Lo prueban los mutantes O1 y O6 (abajo).
- Tests sin red, BBDD ni Sigrid: dobles inyectados o `monkeypatch` de las fábricas en todos los
  `test_f071_http.py` que no inyectan la fuente.

## 4 · Orden (regla 7 del protocolo): mutantes a mano del reviewer

Copia desechable en el scratchpad, solo con `test_f071_pipelines.py` y `test_f071_http.py` (control:
`26 passed`).

| # | Mutación | Resultado |
|---|---|---|
| O1 | `importar.py`: la fuente se construye **antes** de `paso_reconocimiento` | **rojo**: `3 failed` (`assert [namespace(entorno='test')] == []`, los dos de `test_f071_r24_sin_reconocer_no_se_construye_la_fuente` y el de `ya_importado`) |
| O2 | `importar.py`: la fuente se construye **antes** que el catálogo | **verde con las de F-071** (`26 passed`); **rojo** con `test_f036_importar_http.py::test_f036_t18_sin_puertos_inyectados_se_construyen_los_de_verdad` (`1 failed`), aserción adaptada en esta feature y etiquetada «F-071 R24» (ver O-1) |
| O3 | `plantilla.py` (borde): la fuente antes que el catálogo | **rojo**: `1 failed` (`test_f071_r1_por_defecto_…_construida_tras_el_catalogo`) |
| O4 | `paso_catalogo`: la puerta `ya_importado` bajada por debajo de `leer_catalogo` | **rojo**: `1 failed` (`test_f071_r24_con_ya_importado_ni_catalogo_ni_ubicaciones`) |
| O5 | `paso_catalogo`: la puerta bajada por debajo de `ubicaciones(catalogo)` | **rojo**: `1 failed` (ídem) |
| O6 | `importar.py`: sin la puerta `if not contexto.ya_importado` del borde | **rojo**: `1 failed` (`test_f071_r24_con_ya_importado_no_se_construye_la_fuente`) |

El orden de lectura catálogo → ubicaciones en `generar_plantilla` y en `paso_catalogo` es dependencia
de datos (la fuente recibe el catálogo) y además lo fija `test_f071_r24_paso_catalogo_lee_el_catalogo_y_una_vez_las_ubicaciones`
(`llamadas == ["catalogo.leer_unidades", "catalogo.leer_oficios", "ubicaciones"]`).

## 5 · Los tres mutantes equivalentes: **confirmados**

- **`:405` `- 1` → `- 2`: equivalente estricto, confirmado.** `fila` solo conserva ese valor si la obra
  no tiene unidades; entonces `ultima = max(PRIMERA_FILA - 2, PRIMERA_FILA) = PRIMERA_FILA`, igual que
  con `- 1`. El `fila` del bucle de listas (`:434-437`) se reasigna por `enumerate` antes de usarse.
  Ninguna entrada da otro libro. A mano: `263 passed`.
- **`:401` `+ 2` → `+ 3` y `:426` `+= 3` → `+= 4`: equivalentes en lo observable, confirmados.** Mueven
  en bloque la tabla, `ubicaciones_ninguna` y las listas una columna a la derecha dentro de
  `_catalogos` (`veryHidden`, protegida). Todo lo que las usa va por nombre de rango (la fórmula de
  `Ubicación` con `VLOOKUP`/`INDIRECT`, el lector no lee `_catalogos`, `design.md` §3.4). `design.md`
  §4.2 pide «a la derecha de las cinco listas fijas y con una columna en blanco de separación», y
  `test_f071_r9_disposicion_a_la_derecha_de_las_fijas_con_un_separador` exige F en blanco y lo demás
  en `columna > 6`. Con el mutante hay **dos** columnas en blanco en vez de una: la letra de §4.2 lo
  admite («una columna en blanco» como separación, no «exactamente una»), y no cambia nada que vea
  Excel, la importación o quien rellena. Fijar columnas concretas sobreespecificaría. A mano:
  `263 passed` los dos.
- **`:405` `- 1` → `+ 1`: hueco real, cerrado.** El test de `d0dc548`
  (`tests/test_f071_generador.py:284-286`, `_celdas(wb, TABLA) == ((None, None),)`) lo mata a mano en
  la copia del reviewer: `1 failed, 262 passed`. Sin mutar, verde.

## 6 · Desviación de «Instrucciones» (dos párrafos)

Trazada en los tres sitios: `design.md` §7.3 (nota «Texto final (aceptado por el humano el
2026-11-06)»), `progress/impl_F-071.md` («Desviación respecto a §7.3») y `progress/current.md`. El YAML
lleva los dos párrafos literales (`config/plantilla_incidencias.yaml:35-36`) y los fija
`test_f071_r16_*` y `test_f071_r18_*` (≤ 255, sin «General»/«Otra»/«en la revisión»).

## Checkpoints

### C1
- [x] `bash harness/init.sh` con exit 0.
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`, `progress/current.md`, `CHECKPOINTS.md` (init.sh los lista en `[OK]`).

### C2
- [x] Una sola `in_progress` (F-071); F-038, F-040 y F-066 `blocked`, ya conocidas.
- [x] Rama `feature/F-071-plantilla-desde-sigrid`.
- [x] `progress/current.md` describe la sesión activa de F-071 (con su historia de bloqueos resueltos, marcada como tal).
- [x] Features `done` con su resumen: no cambia en este rango.

### C3
- [x] Hexagonal: `casado_con_lista.py` no importa nada del dominio (lo fija `test_f071_r36_casado_con_lista_no_importa_nada_del_dominio`); la aplicación importa dominio y puertos; el borde compone. La importación diferida de `interface_adapters.api.revision` en `interface_adapters/api/plantilla.py:79` es entre adaptadores de la misma capa, para romper un ciclo, y está comentada.
- [x] Primera línea con la ruta en todo fichero añadido o modificado.
- [x] Sin `print()`, sin TODO sin contexto, sin secretos.
- [x] Unidad de trabajo / archivado / manuscrito / firmado / reprocesar: N/A justificado, son reglas del flujo de partes y F-071 no lo toca.
- [x] Nada contra Sigrid hardcodea un estado: no hay escritura ni estado en F-071.
- [x] Ningún parte escaneado ni PDF en git (ningún binario en el diff).

### C3 bis
- [x] N/A justificado: F-071 no incorpora ningún documento de fuera a `docs/referencia/`.

### C4
- [x] Cada requisito con su test: sí para R1–R41 y R44, y la parte de R45 que adelantó T9 (tabla de la sección 1). R42, R43, el test de alcance de R45, R46 y R47 son de T11 y T16 (Bloques 4 y 5) y no entran en esta review.
- [x] Sin red ni BBDD en los unit tests.
- [x] Verificaciones `MANUAL (humano)`: T0 hecha con su tabla; T14 y T16 listadas con sus pasos en `tasks.md` (Bloque 5).

### C4 bis
- [x] `rigor: critico` declarado.
- [x] Fase RED con la salida real pegada: T1 (`ImportError` de colección, 3 módulos), T4 (`29 failed, 9 passed`, con el porqué de los 9) y T7 (`24 failed, 2 passed`, con el porqué de los 2).
- [x] Cobertura: `[OK] 100.0% de 232 líneas cambiadas`.
- [x] Mutación: informe generado por la herramienta; alcance (773) y mutantes (66) recalculados por el reviewer y coinciden; supervivientes muestreados (los 4) y existen tal cual.
- [x] Muertos: campaña de 7 h 20 min, más de 5 min: **campaña no reejecutada (26 408,9 s según el informe; además lo prohíbe el encargo)**; vale el recálculo puro, completado con los 4 supervivientes y 6 mutantes de orden a mano.
- [x] Coste por mutante ≈ 3 201 s con 8 workers: no sospechoso.
- [ ] **Cero supervivientes sin aceptación escrita del humano: NO.** Los tres equivalentes (`excel_openpyxl.py:401` `+3`, `:405` `−2`, `:426` `+=4`) están confirmados por el reviewer, pero en `critico` necesitan la aceptación **escrita** del humano y siguen «pendientes» (`progress/mutacion_F-071.md:55`, `:75`, `:86`; `progress/impl_F-071.md:1108-1109`). → **C-1**.
- [x] «Evidencias» con tests, cobertura, mutantes y supervivientes, tiempo de la suite y workers (`progress/impl_F-071.md:1127-1135`).
- [x] Guarda por definiciones: N/A justificado, ningún fichero sale de una lista de «no se toca» en este rango.
- [x] Ningún N/A sin justificar.

### C4 ter
- [x] N/A justificado: el repositorio no declara `harness/rutas_sensibles.json` (solo el `.ejemplo.json`), así que no hay rutas sensibles que comprobar.

### C5 (bloque intermedio)
- [x] T1, T2, T4, T5, T7, T8, T9 y T10 con su commit `F-071 Tn:` (`89a01d1`, `bb93d19`, `84672a6`, `a320231`, `80abee2`, `862b384`, `266e384`, `d0dc548`). T3, T6 y T10 son una sola campaña por la opción (d), con su informe en `046a3ff`; anotado en `tasks.md`. T11–T18 son de bloques posteriores.
- [x] Sin temporales ni artefactos sin trackear (`git status` limpio antes de este informe; las copias del scratchpad retiradas).
- [x] `features.json`: F-071 `in_progress`, `critico`, coherente.

## Cambios requeridos

1. **C-1 · Aceptación escrita del humano de los 3 equivalentes** (`excel_openpyxl.py:401` `+ 2`→`+ 3`,
   `:405` `- 1`→`- 2`, `:426` `+= 3`→`+= 4`). El reviewer los confirma (sección 5). Lo lleva el
   líder: que el humano lo acepte por escrito y que se anote en `progress/mutacion_F-071.md` (las tres
   «Decisión») y en `progress/impl_F-071.md:1108`. **Sin cambios de código ni de tests**, y sin
   relanzar la campaña: la producción no cambia.

## Observaciones (no bloquean)

- **O-1 · El orden «catálogo antes que la fuente» en el borde de la importación lo protege solo un test
  de F-036.** El mutante O2 (`importar.py:204-206` con las dos construcciones intercambiadas) pasa los
  26 tests de `test_f071_pipelines.py` y `test_f071_http.py`; lo caza
  `test_f036_importar_http.py:826-830`, que esta feature adaptó con el comentario «F-071 R24». En la
  plantilla sí hay test propio (`test_f071_r1_por_defecto_…`, O3). No cambia nada observable fuera
  del orden de las fábricas (las dos dan 503 fuera de `dev`/`pro`), así que no se pide: si T11 toca
  `test_f071_http.py`, un `vistos == [("catalogo", …), ("ubicaciones", …)]` en la importación lo dejaría
  simétrico.
- **O-2 · R6 en Excel de escritorio.** Con la `Unidad` vacía, Excel acepta lo tecleado en `Ubicación`
  (T0, punto 3). El humano lo aceptó al decidir D-1 = a1 (lo rechaza la importación, R31). Queda así
  trazado; T16 lo verá en Excel web si se hace.
- **O-3 · R45: el `.yaml` retirado no tiene guarda.** `test_f036_alcance_cerrado.py:357-359` comprueba
  que no vuelvan los dos `.py`, no `scripts/migracion_f036_correcciones.yaml`. T11
  (`test_f071_alcance_cerrado.py`, R45) es el sitio para cerrarlo.

## Propuesta de automejora (para que la apruebe el humano; no aplicada)

- **`CHECKPOINTS.md` C4 bis / `reviewer.md`:** cuando el implementer declara equivalentes «pendientes de
  aceptación», que el líder recoja la aceptación del humano **antes** de encargar la review. Así la
  review no sale CHANGES_REQUESTED solo por el orden de los pasos (ya pasó en F-060 Bloque 1 y aquí).
  Vale para cualquier proyecto: candidata a `arnes-base`.

## Suite independiente

Lanzada por el reviewer en el worktree, sin caché (`.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider -x`
desde `services/postventa-api`): **`9860 passed, 447 skipped in 825.97s (0:13:45)`**, código de salida 0. Coincide
con el `init.sh` final del implementer (9860 passed, 447 skipped).

## Re-review 2026-11-09 (Bloques 1 a 3, solo C-1)

- **Veredicto:** **APPROVED** (Bloques 1 a 3).
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`); exige fase RED, cobertura,
  mutación con cero supervivientes salvo aceptación escrita del humano, y «Evidencias». Todo lo demás
  quedó verificado en la review anterior (`8d5a3ed`); esta pasada solo cierra C-1.
- **Código sin cambios desde la review:** `git diff 8d5a3ed..HEAD -- services tests` sale **vacío**.
  Desde `8d5a3ed` solo entran `1c12464` (backlog: altas de F-073/F-074, `BACKLOG.md` y
  `harness/features.json`) y `7d411e0` (`progress/current.md`, `progress/mutacion_F-071.md`). La
  campaña y la suite independiente de la review anterior siguen valiendo: la producción no ha cambiado.
- **C-1 resuelto:** `progress/mutacion_F-071.md:55`, `:75` y `:86` (supervivientes 1, 3 y 4:
  `excel_openpyxl.py:401` `+3`, `:405` `−2`, `:426` `+=4`) dicen ahora «**aceptado por escrito por
  el humano el 2026-11-09**», y `progress/current.md` lo recoge con la misma fecha. El superviviente 2
  (`:405` aritmético) sigue cerrado por el test de `d0dc548`. Ningún análisis en `PENDIENTE`.
- **C4 bis:** el `[ ]` de «cero supervivientes sin aceptación escrita del humano» pasa a **`[x]`**. El
  resto de C1–C5, C3 bis y C4 bis quedan como en la review anterior, todos `[x]` o `N/A` justificado.
- **Tests de F-071 relanzados por el reviewer** (sin `.env`, desde `services/postventa-api`,
  `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_f071_*.py`):
  **`210 passed in 58.25s`**. `init.sh` no se ejecuta aquí: lo lanza el líder, por encargo.

### Observación nueva (no bloquea)

- **O-4 · `progress/impl_F-071.md:1108-1109` sigue diciendo «Pendiente del humano».** C-1 pedía anotar
  la aceptación también ahí y no se hizo. No bloquea: la fuente que mira C4 bis es
  `progress/mutacion_F-071.md`, y está al día. Que el implementer lo actualice en su próxima tanda
  (Bloque 4) para que el informe no parezca abierto.

Siguen vigentes O-1, O-2 y O-3 (a resolver en T11) y la propuesta de automejora de la review anterior.
