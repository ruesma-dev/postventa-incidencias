<!-- progress/review_F-056_bloque1.md -->
# F-056 · Review del Bloque 1 (el dominio)

- **Veredicto:** **APPROVED** (sin hallazgos bloqueantes; dos menores y varias observaciones para los bloques siguientes)
- **Fecha:** 2026-10-08 · reviewer
- **Rama:** `feature/F-056-revision-bandeja-backend`, HEAD `3083303`, base fija `f86d639`
- **Alcance revisado:** T1–T3 (`domain/models/revision.py`, los ocho errores de `domain/models/errores.py`,
  `tests/test_f056_revision_dominio.py`, `tests/test_f056_paginacion.py`), los informes
  `progress/impl_F-056.md` (Bloque 1) y `progress/mutacion_F-056.md`, y las enmiendas de la spec por la opción (a).

## Nivel de rigor

`critico`, declarado en `harness/features.json` (`"rigor": "critico"`). Exige: fase RED con traza pegada,
cobertura de lo cambiado ≥ 80 %, campaña de mutación con **cero supervivientes** sin justificación aceptada por
el humano, y las `MANUAL (humano)` con su comando exacto (no hay ninguna en este bloque: dominio puro).

## Lo que se ha ejecutado (resultados reales)

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` | **ENTORNO LISTO**, exit 0. `PUERTA COBERTURA: [OK] 100.0 % de 486 líneas cambiadas (486/486, umbral 80 %, nivel critico)`. El servicio api salió verde **por caché** (árbol sin cambios desde el último verde); ruff 74 avisos |
| Tests de F-056 + todas las guardias de arquitectura (`test_f00*_arquitectura`, `test_f012/f013/f036_arquitectura`) + barridos `test_f006_repo_sin_identificadores`, `test_f005_integracion_sin_secretos`, sin caché | **678 passed, 2 skipped** en 48 s |
| Recálculo puro del alcance (`harness.alcance.alcance_de_feature('F-056', base='f86d639')`) | 2 ficheros, **1155 líneas** (errores.py 108, revision.py 1047): coincide con el informe |
| Recálculo de mutantes (`harness.mutacion.generar_mutantes` sobre ese alcance) | **153** (revision.py 153, errores.py 0): coincide. Operadores: lógico 42, entero 28, booleano 27, not 25, comparación 25, aritmético 6 |
| Muestreo de los mutantes citados en el informe | Existen tal cual: `revision.py:475 [logico] or not local -> and not local` y `revision.py:561 [comparacion] > MAX_DETALLE -> >= MAX_DETALLE` |
| Control del cero de `errores.py` | Sin la exclusión de alcance, el fichero entero da 1 mutante (fuera de las líneas de F-056): el generador funciona; las 108 líneas añadidas son clases con asignaciones, sin operadores mutables. Cero **legítimo** |
| Campaña completa | **No reejecutada**: 20961 s (5 h 49 min) según el informe, > 5 min; vale el recálculo puro y se dice aquí. Coste por mutante = 20961 × 8 / 153 ≈ **1096 s**, coherente con una suite de 800–1450 s: no sospechosa |
| Mutantes **a mano** en copia de scratchpad (37, ver abajo) | **36 muertos, 1 equivalente** (X4) |
| `git status` tras todo | Limpio (el trabajo de mutación se hizo en una copia del scratchpad, nunca en el árbol) |

### Mutantes a mano (copia en scratchpad, tests de F-056 —los únicos que importan `revision.py`—)

Elegidos por riesgo, fuera de lo que generan los operadores de `harness.mutacion` (semántica, orden, borrado de
guardas). Todos mueren salvo X4, que es **equivalente** por construcción.

| # | Mutación | Test que la caza |
|---|---|---|
| M1 | motivos: la ubicación vigente sin `strip()` | `test_f056_r47_la_ubicacion_vigente_se_recorta_al_comparar` |
| M2 | pares de `obrofc`: gana el último nombre | `test_f056_r3_editar_una_aprobada_hacia_los_importados_la_deja_nueva` |
| M3 | orden: sin la marca «sin fila al final» | `test_f056_r25_el_orden_es_total_y_estable` |
| M4 | `paginar`: corte con `>=` | `test_f056_r25_recorrer_todas_las_paginas…[1]` |
| M5 | `siguiente` con `>=` | `test_f056_r25_recorrer_todas_las_paginas…[1]` |
| M6 | **orden**: frescura después de exigir el catálogo | `test_f056_r7_la_frescura_va_antes_que_sigrid` |
| M7 | **orden**: frescura antes que la transición | `test_f056_r2_accion_no_permitida_antes_que_la_frescura` |
| M8 | `clave_de_texto` sin la comprobación de canónico | `test_f056_r23_clave_manipulada…` |
| M9 | duplicada sin original cargada → no duplicada | `test_f056_r22_sin_la_original_cargada_no_se_aprueba` |
| M10 | `sin_oficio` también con oficio ambiguo | `test_f056_r21_oficio_ambiguo_solo` |
| M11 | `es_candidata` acepta cualquier última | `test_f056_r3_…_fuera_de_las_candidatas` |
| M12 | `CandidataAlVolcado` sin exigir ubicación | `test_f056_r35_candidata_imposible[cambio2]` |
| M13 | correo con blancos admitido | `test_f056_r9_correo_no_admisible[per sona@…]` |
| M14 | R15 acepta cualquier proveedor | `test_f056_r15_otro_proveedor_pide_elegir_primero_el_oficio` |
| M15 | estado: nunca `editada` | `test_f056_r1_editar_o_recuperar_con_valores_distintos_es_editada` |
| M16 | ubicación validada contra la unidad **vigente** | `test_f056_r14_unidad_sin_nombre_en_sigrid_guarda_el_codigo` |
| M17 | ubicación contra la unión de todas las unidades | `test_f056_r48_ubicacion_valida_en_otra_unidad_no_vale` |
| M18 | huella con `ensure_ascii=True` | `test_f056_r20_la_huella_es_sha256_de_los_13_valores_en_json` |
| M19 | `par_fuera` también con oficio ambiguo | `test_f056_r21_oficio_ambiguo_con_proveedor_no_da_par_fuera` |
| M20 | original descartada sigue haciendo duplicada | `test_f056_r22_original_descartada_ya_no_es_duplicada` |
| M21 | `sin_cambios` desactivado | `test_f056_r16_editar_con_los_vigentes_es_sin_cambios` |
| M22 | `total_filtrado` = lo que queda tras el cursor | `test_f056_r25_una_pagina_y_la_siguiente` |
| M23 | `ubicaciones_de_tipologia` deduplica sin mayúsculas | `test_f056_r47_ubicaciones_que_difieren_en_mayusculas…` |
| M24 | el motivo de descarte no se recorta | `test_f056_r18_motivo_vacio_es_nulo` |
| M25 | aprobar refresca el nombre de la unidad | `test_f056_r20_aprobar_guarda_los_vigentes_sin_cambiarlos_y_su_huella` |
| M26 | `activas` incluye las descartadas | `test_f056_r26_filtro_de_estado[activas]` |
| M27 | `resumen.con_motivos` cuenta motivos, no filas | `test_f056_r27_resumen_sobre_todas_las_filas` |
| M28 | aprobar altera el detalle | `test_f056_r20_aprobar_guarda_los_vigentes…` |
| X1 | cursor con `f: true` | `test_f056_r23_clave_manipulada…["f":true]` |
| X2 | el `oid` no se recorta al guardar | `test_f056_r9_validar_quien_recorta_y_conserva_mayusculas` |
| X3 | candidata con proveedor ambiguo | `test_f056_r35_candidata_imposible[cambio3]` |
| X4 | candidata: quitar `or v.oficio_ambiguo` | **sobrevive — equivalente**: `ValoresIncidencia` ya impide «ambiguo con código» (R99), así que `oficio_codigo is None` cubre el caso. No necesita aceptación del humano porque no es un superviviente de la campaña ni un mutante de orden: es una guarda redundante, y la rama sigue cubierta por `test_f056_valores_con_las_invariantes_de_la_bandeja` |
| X5 | cursor sin zona admitido | `test_f056_r23_clave_manipulada…[sin zona]` |
| X6 | `con_motivos=false` no filtra | `test_f056_r26_filtro_con_motivos[False]` |
| X7 | R15 conserva el proveedor aun pidiendo `null` | `test_f056_r15_oficio_ambiguo_y_proveedor_nulo_lo_quita` |
| X8 | duplicada compara los importados | `test_f056_r22_editar_la_propia_para_distinguirla` |
| X9 | `cambios` contra los vigentes | `test_f056_r29_fila_de_revision_editada` |

**Regla de orden (RM7).** En este bloque el dominio no habla con ningún colaborador (el catálogo entra por
parámetro), así que la regla de «bajar la puerta un paso por colaborador» **no aplica todavía**: es N/A
justificado y se aplicará a `aplicar_accion` en la review del Bloque 3. Aun así se movieron las dos puertas de
orden que sí viven en `decidir` (M6 y M7): las dos caen, cada una con un test **de F-056**.

## Verificación de las decisiones posteriores a la spec

- **Opción (a) del cursor** (humano, 2026-10-07): **reflejada**. `design.md` §4 (tabla de funciones con
  `texto_de_clave`/`clave_de_texto` y la nota de la decisión), R25 (nota) y T12 de `tasks.md` (el borde pone y
  quita el base64url, con tope sobre el texto codificado y los tests `eyJjIjoi…`). `revision.py` no nombra
  `base64`; la guardia de F-012 pasa sin tocarla. Los casos de cursor manipulado que se quitaron de los tests
  al mover el base64url se reescribieron sobre el texto JSON (26 casos), y la forma base64url queda anotada
  para T10/T12.
- **`motivos_no_aprobable` sin `listas`**: coherente con D-4 (ya no hay lista de ubicaciones de la plantilla;
  ningún motivo de R21 mira urgencias ni listados). `validar_valores` y `decidir` sí reciben `listas`
  (urgencia y listado: lo ofrecido es lo aceptado). **Pero el design no lo recoge** (hallazgo N-1).
- **`sin_oficio` cuenta el oficio ambiguo como oficio** (un ambiguo da solo `oficio_ambiguo`): coherente con
  R99 de F-036 (`hay_oficio = ambiguo or código`), con §11 (los 47 se ven como `oficio_ambiguo`), con el
  recuento esperado en T19 (`por_motivo.oficio_ambiguo = 47`, sin inflar `sin_oficio`) y con el contrato hacia
  F-040 (§10): una ambigua sigue sin ser aprobable porque `oficio_ambiguo` bloquea, y `CandidataAlVolcado`
  rechaza ambiguos. Con D-5 no interfiere (la duplicada se evalúa aparte). **El design tampoco lo recoge**
  (N-1).

## Checkpoints

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` exit 0 (ENTORNO LISTO).
- [x] Existen los siete ficheros (init.sh los comprueba).

### C2 — El estado es coherente
- [x] Una sola feature `in_progress` (F-056).
- [x] Rama `feature/F-056-revision-bandeja-backend`.
- N/A `progress/current.md` solo con la sesión activa: es del líder y se evalúa al **cierre** de la feature,
  no en un bloque intermedio. Se anota (O-6) que hoy aún lleva el histórico de F-053.
- [x] Toda `done` con su resumen en `history.md` (init.sh en verde; F-056 no es `done`).

### C3 — Arquitectura y convenciones
- [x] Hexagonal: `revision.py` solo importa `hashlib`, `json`, `collections.abc`, `dataclasses`, `datetime`,
  `enum`, `uuid` y módulos de `domain/`; sin red, BBDD, IA, reloj ni `base64`. Las guardias de arquitectura
  (F-002…F-036) pasan.
- [x] Primera línea con la ruta en los cuatro ficheros de código.
- [x] Sin `print()`, sin TODOs, sin secretos, sin dependencias nuevas.
- N/A Unidad de trabajo «parte», archivar/cerrar con validaciones, manuscrito, firmado ≠ conforme, reprocesar
  no duplica, estados de `conest`: el bloque no toca partes, remesas, archivo, cierre ni estados de Sigrid; es
  la revisión de incidencias de la bandeja. Las escrituras en Sigrid de esta línea de trabajo son de F-040.
- [x] Ningún PDF ni escaneado en git: `git log --diff-filter=A f86d639..HEAD` solo añade `.py`, `.md` de
  spec y de `progress/`.

### C3 bis — Documentos de fuera
- N/A: el bloque no añade ni toca nada en `docs/referencia/`.
- Barrido de los ficheros nuevos o cambiados de la rama (hecho por el reviewer), patrones: correos
  `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}` (solo `@ejemplo.invalid` y la atribución de commits), GUID
  `[0-9a-f]{8}-…-[0-9a-f]{12}` (**ninguno**; los tests usan `UUID(int=n)`), razones sociales `S.L.|S.A.|SLU`
  (solo «Carpintería Ejemplo, S.L.», «Maderas Ejemplo, S.A.», ficticias), obras (`9901`, ficticia) y códigos
  de proveedor (`EJ07`, `EJ08`, ficticios). Los códigos de oficio `0046`/`0143` son los del ejemplo ya aprobado
  en `design.md` §8, y `0200` es un código de cuatro cifras sin nombre ni proveedor asociado. Además pasan `test_f006_repo_sin_identificadores` y
  `test_f005_integracion_sin_secretos`.

### C4 — La verificación es real
- [x] Cada requisito del bloque tiene test trazable `test_f056_rN_*` y todos pasan (tabla de cobertura abajo).
  Los requisitos de los Bloques 2–4 (R4, R6, R8, R10–R12, R17, R24 en la lectura, R28–R33 en el borde,
  R36–R48 de persistencia, Sigrid y documentos) no son de este bloque.
- [x] Sin red ni BBDD: dominio puro, datos construidos en memoria.
- N/A `MANUAL (humano)` en `current.md`: el bloque no tiene ninguna (T8 y T18–T19 son de los Bloques 2 y 5).

### C4 bis — El rigor declarado se cumple
- [x] `rigor: critico` declarado.
- [x] **Fase RED**: traza real pegada (commit `1dbb67d`): `ImportError` de recogida, porque ni `revision.py`
  ni los errores existían (comprobado: `1dbb67d` no tiene `revision.py` y su `errores.py` no define
  `AccionNoPermitida`). Es un RED de recogida, no uno test a test (O-2); la especificidad de cada test la
  prueban la campaña (0 supervivientes) y los 37 mutantes a mano de esta review.
- [x] **Cobertura**: `PUERTA COBERTURA [OK] 100.0 %` (486/486).
- [x] **Mutación**: `progress/mutacion_F-056.md` generado por la herramienta; alcance (1155 líneas) y mutantes
  (153) **recalculados** y coincidentes; dos mutantes muestreados existen tal cual.
- [x] **Muertos comprobados**: campaña > 5 min (5 h 49 min) → **no reejecutada**, vale el recálculo puro, y se
  complementa con 37 mutantes a mano reejecutados aquí.
- [x] **Tiempo plausible**: ≈ 1096 s por mutante con 8 workers, del orden de la suite.
- [x] **Supervivientes**: 0 en la campaña. Del trabajo a mano, X4 es equivalente (guarda redundante con una
  invariante del tipo, no una puerta de orden): se deja anotado; si el humano quiere el rigor literal de
  «cada equivalente a mano con su aceptación escrita», basta con que lo confirme o con borrar la guarda
  redundante.
- [x] **Evidencias**: tests (364 de F-056; suite 7071 passed), cobertura (100 %), mutantes (153/153, 0
  supervivientes, 8 workers) y tiempo de la suite (798 s).
- [x] Ningún N/A sin justificar.

### C4 ter — Rutas sensibles
- N/A: no existe `harness/rutas_sensibles.json` (solo el `.ejemplo`), e `init.sh` no señala rutas.

### C5 — La sesión se cerró bien
- [x] T1, T2 y T3 `[x]`, con commits `F-056 T1:`, `F-056 T2:` (dos) y `F-056 T3:` (tres). Los dos de
  bloqueo/desbloqueo y los del líder (`326b9c6`, `59862c0`) solo tocan `BACKLOG.md`, `features.json`,
  `current.md` y la spec: **ningún código** (comprobado con `git show --stat`).
- [x] Sin temporales sin trackear (`git status` limpio). Los 8 worktrees huérfanos que cita el informe ya no
  aparecen en `git worktree list`.
- [x] `features.json`: F-056 `in_progress`, coherente con un bloque intermedio.

## Cobertura · requisito → test (Bloque 1)

| R | Tests |
|---|---|
| R1 | `test_f056_r1_*` (9: importados, vigentes, nueva, editada, aprobada, descartada, un solo campo) |
| R2 | `test_f056_r2_acciones_posibles_de_cada_estado`, `test_f056_r2_las_dieciseis_casillas`, `test_f056_r2_accion_no_permitida_antes_que_la_frescura` |
| R3 | `test_f056_r3_editar_una_aprobada_la_deja_editada_y_fuera_de_las_candidatas`, `…_hacia_los_importados_la_deja_nueva` |
| R5 (dominio) | `test_f056_r5_*` (oid 1/128/129, `MAX_OID` = el de la importación, `valores`/`motivo` fuera de su acción) |
| R7 (dominio) | `test_f056_r7_sin_revisiones_la_previa_es_nula`, `…_la_previa_tiene_que_ser_la_ultima`, `…_la_frescura_va_antes_que_sigrid` |
| R9 | `test_f056_r9_*` (recorta y conserva mayúsculas, 3 y 254, no admisibles, el error no repite) |
| R13 | `test_f056_r13_*` (campo a campo, exacto, todos los errores a la vez y en orden, no repiten lo recibido) |
| R14 | `test_f056_r14_*` (nombres de Sigrid, unidad y oficio sin nombre, par repetido → el primero) |
| R15 | `test_f056_r15_*` (7) |
| R16 | `test_f056_r16_*` (incluido el colapso de blancos y el nombre renombrado) |
| R18 | `test_f056_r18_*` (vacío → nulo, recorte, 500/501, no texto, sin Sigrid) |
| R19 | `test_f056_r19_recuperar_guarda_los_vigentes_sin_leer_sigrid` |
| R20 | `test_f056_r20_*` (409 con todos los códigos, vigentes sin cambiar, huella sha256 recalculada, nulo ≠ vacío) |
| R21 | `test_f056_r21_*` (cada motivo solo, todos juntos en orden en tres variantes, vigentes y no importados) |
| R22 | `test_f056_r22_*` (10) |
| R23 (dominio) | `test_f056_r23_*` (filtros, clave manipulada, tope 384/385, error sin repetir, `tamano`) |
| R25 | `test_f056_r25_*` (orden total con empates y sin fila, ida y vuelta, JSON canónico, recorrer todas las páginas con 8 tamaños) |
| R26 | `test_f056_r26_*` (estado, `activas` por defecto, `con_motivos`, los dos juntos, paginar filtradas) |
| R27 | `test_f056_r27_resumen_sobre_todas_las_filas`, `…_vacio_lleva_todas_las_claves_a_cero` |
| R29/R33 (dominio) | `test_f056_r29_*`, `test_f056_r33_*` (`campos_cambiados`, `fila_de_revision`) |
| R34 | `test_f056_r34_*` (solo última `aprobar`, `candidata_de`, inmutabilidad de los doce tipos) |
| R35 | `test_f056_r35_candidata_valida`, `test_f056_r35_candidata_imposible` |
| R47, R48 | `test_f056_r47_*`, `test_f056_r48_*` (partir, recortar, vacíos, > 48, repetidos exactos, mayúsculas, otra unidad, cambiar la unidad revalida, unidad sin tipología o sin entrada) |

## Hallazgos

Ninguno bloquea. Para resolver **antes de la review final** de F-056 (pueden ir en el encargo del Bloque 2):

1. **N-1 (menor) · El design no recoge los dos ajustes de contrato aceptados por el líder.**
   `specs/F-056-revision-bandeja-backend/design.md` l.192 sigue con
   `motivos_no_aprobable(situacion, *, catalogo, ubicaciones, listas)` (el código no lleva `listas`), y l.100
   (§3.5) define `sin_oficio` como «no hay oficio» sin decir que el oficio ambiguo cuenta como oficio. Como §3.5
   y §8 son el contrato que consume F-038 (y §10 el de F-040/F-059), añadir una línea en cada sitio, con la fecha
   de la aceptación (2026-10-07). Conviene anotar a la vez las interpretaciones 3, 4 y 8 del informe del
   implementer (el par solo se mira con código de oficio; la ubicación `""` o de blancos es error y no nula;
   duplicada sin la original cargada → `duplicada`), que hoy solo constan en `progress/`.
2. **N-2 (menor) · Un aviso de ruff nuevo en un fichero de F-056.**
   `services/postventa-api/tests/test_f056_paginacion.py` l.49–51: `I001` (imports desordenados:
   `clave_de_texto` antes de `clave_de_orden`), introducido por el renombrado de `217debf`. `init.sh` lo cuenta
   dentro de los 74 «de deuda previa», pero es de esta rama. `ruff check --fix` sobre ese fichero.

## Observaciones (no son cambios requeridos)

- **O-1 · `CandidataAlVolcado` no comprueba la forma de la ubicación.** Exige que la haya (R35) pero no que mida
  ≤ 48 ni que venga sin blancos en los extremos. Aprobar compara la ubicación **recortada** y guarda los
  vigentes **sin cambiar** (R20), así que una vigente `" Baño "` se aprobaría y llegaría así a F-040/`rcp.resubi`.
  Hoy es inalcanzable (la importación compara exacto contra la plantilla y editar guarda recortado), pero la
  candidata es la última defensa antes del ERP: valorar en el Bloque 2 (o en F-059) un
  `ubicacion == ubicacion.strip() and len ≤ 48` en `__post_init__`, o el `CHECK` equivalente.
- **O-2 · RED de recogida.** La traza es un `ImportError` de colección, no un fallo test a test. Se acepta por
  la campaña con 0 supervivientes y los mutantes a mano de esta review; en los Bloques 2 y 3, con módulos que
  ya existen a medias, conviene un RED con fallos de aserción.
- **O-3 · `paginar(tamano=True)`** pasa la validación (`bool` es `int`). Inalcanzable desde el borde si este
  convierte la query a `int`; que lo fije un test de R23 en el Bloque 3.
- **O-4 · Fechas sin zona.** `_orden` resta contra un origen con zona: una `creada_at_utc` ingenua lanzaría
  `TypeError`. `IncidenciaEnBandeja` no lo impide; el repositorio del Bloque 2 debe devolver `timestamptz` con
  zona y un test lo debe fijar.
- **O-5 · Regla de orden (RM7) en el Bloque 3.** `aplicar_accion` habla con `situacion`, `leer_catalogo`, la
  lectura de ubicaciones y `registrar`: en esa review hay que bajar a mano la transición y la frescura por
  debajo de cada lectura de Sigrid, y el `registrar` por encima de `decidir`, y exigir rojo con tests de F-056.
- **O-6 · `progress/current.md`** aún lleva el histórico de F-053: limpieza del líder al cerrar.
- **O-7 · `init.sh` dio el servicio api en verde por caché.** El informe del implementer trae la suite completa
  real (7071 passed); aquí se reejecutaron sin caché los tests de F-056 y todas las guardias de arquitectura y
  de identificadores (678 passed). Es el patrón que F-055 ya tiene apuntado.

## Propuesta de automejora (para el humano; no aplicada)

En `CHECKPOINTS.md`, C4 bis, punto «Fase RED»: aclarar si un **RED de recogida** (`ImportError` porque el
módulo no existe) vale como traza de los requisitos centrales en nivel `critico`. Propuesta: vale **solo** si
la campaña de mutación del mismo bloque sale con cero supervivientes; si no, se exige además un RED con fallos
de aserción para los requisitos centrales (por ejemplo, con un esqueleto del módulo que devuelva valores
neutros). Hoy cada reviewer lo decide por su cuenta. Vale para cualquier proyecto: si se aprueba, portarla a
`arnes-base`.
