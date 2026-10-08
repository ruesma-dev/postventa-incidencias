<!-- progress/review_F-056.md -->
# F-056 · Review final (revisión de la bandeja en el backend)

- **Veredicto:** **CHANGES_REQUESTED.**
  - El **código**, los **tests** y los **documentos** (`docs/ARCHITECTURE.md` y `docs/INTEGRACION.md`) están bien.
    No pido ningún cambio en `services/` ni en `docs/`.
  - Lo que falla es el **Bloque 5 tal como está escrito en `tasks.md`**, que es lo que esta review tenía que dar por
    listo:
    - T19 espera en un paso un resultado que el código no da (C-1);
    - para una MANUAL de rigor `critico` le faltan los comandos exactos (C-2);
    - no comprueba de forma explícita que el 503 de las ubicaciones ya no existe (C-3);
    - y `progress/current.md` no recoge el Bloque 4 ni lista las MANUAL que quedan (C-4).
  - Son cambios **solo de texto**, en `specs/F-056-revision-bandeja-backend/tasks.md` y en `progress/current.md`. No
    hace falta otra campaña de mutación ni volver a pasar `init.sh` por ellos.
- **Fecha:** 2026-10-09 · reviewer (review final)
- **Rama:** `feature/F-056-revision-bandeja-backend`, HEAD `55696f0`. Base fija `f86d639`.
- **Alcance revisado:**
  - la feature entera (R1–R48), contra la spec (con sus decisiones posteriores), `docs/CONVENTIONS.md`,
    `docs/ARCHITECTURE.md` y todo `CHECKPOINTS.md`;
  - el contrato que consumen F-038 (`postventa-f038`, solo lectura) y F-059 (`postventa-f040`, solo lectura);
  - el Bloque 4;
  - los tests de otras features ampliados;
  - el alcance;
  - el Bloque 5.

## Nivel de rigor

El nivel es `critico`, declarado en `harness/features.json`. Exige:

- la fase RED con la traza pegada en los requisitos centrales;
- cobertura ≥ 80 % de lo cambiado;
- mutación con **cero supervivientes**, salvo justificación que acepte el humano;
- la regla de orden (punto 7);
- y las verificaciones **`MANUAL (humano)` con su comando exacto** y su resultado real.

Esta última puerta es la que no se cumple todavía en T19.

## Lo que se ha ejecutado (resultados reales)

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual) | **ENTORNO LISTO**, exit 0. El api y el front salen en verde **por caché** («árbol sin cambios desde el último verde»). PUERTA COBERTURA **[OK] 100,0 % de 1060 líneas** (umbral 80 %, nivel critico). `ruff`: 73 avisos de deuda previa, **ninguno en ficheros de F-056** (filtrado desde la raíz, como lo lanza `init.sh`) |
| Sin caché (`-p no:cacheprovider`): todos los `test_f056_*.py`, `test_f006_repo_sin_identificadores.py`, los diez tests de otras features que la rama amplía, `test_f012_*`, `test_f005_arquitectura.py` y `test_f036_arquitectura.py` | **1835 passed, 22 skipped, 0 failed** (76,9 s). Los 22 skipped son controles git de F-030 a F-034 que solo corren en su propia rama (`-rs`). **Ninguno es de F-056** |
| RED de T15 reproducido: `git archive f04a9da` en el scratchpad, `pytest tests/test_f056_documentacion.py` | **59 failed, 8 passed**, como dice el informe. Los 59 son `AssertionError`: ningún error de importación ni de nombre |
| Recálculo puro de la mutación (`harness.alcance` + `harness.mutacion.generar_mutantes`) | Base `c22e692`: **6 ficheros, 10 mutantes**, igual que `mutacion_F-056_bloque3bis.md`. Salen 342 líneas, una más que las 341 del informe: es la línea en blanco de PEP 8 de `3bb753a`, que no genera mutantes. Base `f86d639` (la feature entera hoy): **13 ficheros, 3359 líneas, 247 mutantes**. Las cuatro campañas suman 153 + 17 + 77 + 10 = 257: se solapan y las bases forman una partición sin huecos (b88b5ef, e9e815f y c22e692 son los commits de review que siguen a cada campaña). Las reviews de bloque ya recalcularon cada una y cuadraron |
| Código cambiado después de la última campaña (`git diff e5971fe HEAD` en producción) | **Solo una línea en blanco** (`application/pipelines/revision.py`, `3bb753a`). Lo demás son tests de documentación |
| Campañas | **No reejecutadas, como pide el encargo, y además todas pasan de 5 min**: 349 min, 29 min, 175 min y 63 min según sus informes. Me quedo en el recálculo puro. Coste por mutante, con 8 workers: ≈ 1096, 808, 1091 y 3011 s, del orden de la suite. **No son sospechosas** |
| Mutaciones de orden a mano | **No repetidas.** No ha cambiado código desde que se hicieron las 12 del Bloque 3 y las 13 del 3 bis, y todas dieron rojo. No he visto ningún hueco nuevo de orden |
| Barrido de la rama (`git diff f86d639...HEAD`, líneas añadidas): correos, GUID, IPv4, `print(`, `TODO`, `breakpoint`, ficheros binarios añadidos | **Correos:** solo `@ejemplo.invalid`, salvo `persona.apellido@empresa.es` en un control negativo (O-2). **GUID:** ninguno. **IP:** solo `127.0.0.1`. **Depuración:** ninguna. **Binarios:** ningún `.pdf`, `.xlsx` ni imagen añadidos (`git log --diff-filter=A`) |
| Alcance | La rama solo toca `services/postventa-api/`, `docs/ARCHITECTURE.md`, `docs/INTEGRACION.md`, `progress/`, `specs/F-056…`, `harness/features.json` y `BACKLOG.md`. **Nada** en `services/postventa-front/`, `infra/` ni `docs/referencia/`. El DDL es solo `CREATE TABLE IF NOT EXISTS` y `CREATE INDEX IF NOT EXISTS` sobre `postventa.` |
| Cabecera con la ruta en los ficheros nuevos | Todos la llevan |
| `git status` al terminar | Limpio. La copia del RED se hizo en el scratchpad |

## La feature de punta a punta

### Los tres endpoints frente a R6–R33

- **`POST /api/revision/acciones`** (`interface_adapters/api/revision.py:441`, `application/pipelines/revision.py:271`).
  - **Validación (R5).** Comprueba el cuerpo entero **antes** de construir nada: claves exactas por acción,
    `confirmado` es `True`, R9, UUID canónico, `revision_previa`, las 8 claves de `valores` y el motivo. Los tipos de
    los valores los comprueba `validar_valores`, campo a campo.
  - **Orden (§7).** `situacion` (404) → `comprobar_sin_sigrid` (transición 409, y luego frescura 409) → catálogo y
    ubicaciones, solo en editar y aprobar → `decidir` → `registrar` (segunda frescura dentro de la transacción; al
    aprobar una duplicada, también la de su original) → la fila de R29.
  - **Motivos (R8).** Son `None` en descartar y recuperar.
- **`GET /api/revision`**.
  - Valida antes de construir (R23).
  - El tope de 10.000 se comprueba **antes** de Sigrid (R24).
  - Lee catálogo, opciones y ubicaciones **una vez** (R30, R46).
  - El resumen sale sobre todas las filas y la página con los filtros en el servidor (R26, R27).
  - El cursor va en base64url **solo en el borde**.
  - `catalogo.ubicaciones` es **el mismo mapa** que valida (R28).
  - `_oficios` no puede dar `KeyError`: `opciones_de_oficio` reparte **todos** los oficios de la obra en grupos
    (`plantilla_incidencias.py:277-279`).
- **`GET /api/revision/historial`**.
  - Da 400 o 404 sin Sigrid.
  - Las revisiones van de la más antigua a la más reciente, con `correo` y `campos_cambiados` frente a la anterior.
  - Nunca lleva el `oid` (R32, R33).
- **`function_app.py`.**
  - Las tres rutas son `ANONYMOUS`.
  - `CODIGOS_DE_REVISION` cubre los ocho errores.
  - Los errores van al log **solo con su código** (R41).
  - Los errores del catálogo se traducen como en `GET /api/plantilla` (R30).
  - Las ubicaciones de F-036 y de F-056 casan por código exacto: las dos lecturas sacan `u.cod` de la misma columna y
    sin recortar (`consultas_catalogo.py:56`, `consultas_ubicaciones_validas.py`). El SQL es el de design §16.3
    carácter a carácter.

### El contrato que consume F-038 (`postventa-f038`, spec)

- Su design §1 enumera las claves de las tres rutas y los códigos de error de §4 y §3.5, y **coinciden** con lo
  implementado.
- Ya contempla `motivos_no_aprobable: null` tras descartar o recuperar («recarga para ver si se puede aprobar», su
  R12).
- Ya contempla la 200 de la acción como fila de R29.

No veo ninguna divergencia.

### El contrato que consume F-059 (`postventa-f040`, spec)

- **Lo que importa.** `candidatas_al_volcado`, `CandidataAlVolcado`, `huella_de_valores`, `estado_de`,
  `acciones_posibles`, `es_candidata`, `RevisionPort` y la tabla `revisiones_bandeja`. Todo existe con esos nombres.
- **Campos que lee.** `CandidataAlVolcado` tiene `incidencia_id`, `obra_codigo`, `valores`, `huella`,
  `aprobada_at_utc` y `revision_id`: lo que su §5 y su R7 usan.
- **Clave ajena.** Su DDL apunta a `revisiones_bandeja (revision_id)`, que es la clave primaria.
- **§12 de F-059.** Sobre `estado_de`, `acciones_posibles`, `es_candidata`, `sentencias_revision.py`,
  `repositorio_revision_pg.py` y el borde, encaja con la forma real: un `registrar` transaccional con
  `FOR UPDATE`, y el `CHECK` de `accion` cerrado a propósito.

Hay una observación para F-059 (O-3).

## El Bloque 4: ¿dicen la verdad los documentos?

`docs/INTEGRACION.md`:

- **§1.**
  - Hay **tres lecturas**, todas por `sql/read` y **ninguna escritura**, con `max_rows` a 1.000.
  - El techo da 409 `catalogo_sin_verificar` (el código real de `CODIGOS_DE_RECHAZO_DE_OBRA`) y lo cortado da 503.
  - Las puertas son `ENTORNO` y la configuración, como dice `construir_ubicaciones_validas`.
  - El texto de `ubica` no va al log: el adaptador registra solo la obra, los recuentos, el techo y los segundos.
- **§2.** La tabla está en el árbol, con la enmienda de «catorce» y el apartado «Con F-056», que cuadra con el DDL.
- **§4.** No hay variables nuevas.
- **§5.** Sin pasarela, descartar, recuperar y el historial siguen funcionando: es cierto, porque `accion_de_revision`
  no construye el catálogo para esas acciones.
- **§7.**
  - Habla del correo **corporativo de un empleado interno**, guardado en una sola columna de una sola tabla.
  - Dice que sale en **tres respuestas** y en ningún error, que nunca va a logs, que el `oid` no sale en ninguna
    respuesta y que no va al datamart sin otra decisión.
- **§8.**
  - Tiene tres filas nuevas.
  - Declara «Los veinte quedan en nivel anónimo».
  - Dice que no depende de ninguna ventana.
  - Explica la paginación y lo que hereda F-040.
- **§10.** Dice «sin desplegar».

`docs/ARCHITECTURE.md`:

- La sección nueva cuadra con el código: estados derivados, transiciones, la doble frescura, el orden de R25 y el
  cursor en el borde.
- Corrige el «Lo que no hacen» de F-036.

Los dos documentos dicen la verdad.

### Los tests de otras features ampliados (diff contra `f86d639`)

- **`test_f005_ddl_idempotente_texto.py`, `test_f028_ddl_historico.py` y `test_f030` a `test_f034`.** Añaden
  `15_revisiones_bandeja.sql` a listas de igualdad exacta. Siguen siendo igualdades.
- **`test_f036_ddl.py`.** Antes exigía `[-3:] == FICHEROS`. Ahora exige que **todo** lo que va tras el `11_` sea
  `FICHEROS + 15_`: es más estricto.
- **`test_f010_endpoints_protegidos.py`.** La cuenta pasa a 20, con las tres rutas nombradas. No se quita ninguna
  aserción.
- **`test_f019_documentacion.py` y `test_f053_documentacion.py`.** Exigen «veinte» y que «diecisiete» ya **no** esté.
  El párrafo de F-053 tiene que seguir antes de la cuenta.
- **`test_f036_documentacion.py`.**
  - Ya no exige que la última feature sea F-036.
  - A cambio exige **una** fecha y **una** última feature, que no retrocedan, y que F-036 siga constando.
  - Lleva cinco controles negativos y uno positivo. Es la decisión del líder anotada en R45.

Ninguno se relaja más allá de lo que R45 declara, y `test_f056_alcance_cerrado.py` lista los tres de F-036 y F-053
ampliados.

## El Bloque 5: ¿está listo?

- **T18.** Se publica desde un worktree limpio de `dev`. `desplegar_backend.ps1` encuentra el código por
  `$PSScriptRoot` (`infra/desplegar_backend.ps1:185-186`), así que publica lo del worktree y no la carpeta de trabajo.
  No escribe nada en Sigrid. Le faltan detalles (O-1), pero se puede ejecutar.
- **T19.** No está listo (C-1 a C-3).
  - Lo que lee y comprueba es lo correcto: el resumen con los recuentos esperados, el recorrido de páginas, el
    historial sin `oid`, App Insights sin `oid`, correo ni textos, y el antes y el después de
    `24_ubicacion_sigrid.ps1`, que es solo lectura.
  - Pero el paso 3 tiene un resultado esperado equivocado y no da los comandos.

## Checkpoints

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` exit 0.
- [x] Existen los ficheros de base (lo comprueba `init.sh`).

### C2 — El estado es coherente
- [x] Una sola feature `in_progress`: `['F-056']`.
- [x] Rama `feature/F-056-revision-bandeja-backend`.
- [x] `progress/current.md` **empieza por el bloque vivo de F-056**, con el mismo criterio que las reviews de F-036 y
  F-053. Arrastra bloques históricos de antes, y su bloque de F-056 está viejo (C-4).
- [x] Toda feature `done` tiene su resumen en `history.md`. El diff no cambia el estado de ninguna otra. En
  `features.json` solo cambian prioridades, que es lo que regenera `BACKLOG.md`.

### C3 — El código respeta arquitectura y convenciones
- [x] Hexagonal: `test_f005_arquitectura.py` y `test_f036_arquitectura.py` en verde sin caché. El dominio es puro, los
  puertos están en `domain/ports` y los adaptadores en `infrastructure/`. El base64 está solo en el borde (regla de
  F-012).
- [x] Primera línea con la ruta en todos los ficheros nuevos.
- [x] Sin `print()`, sin `TODO`, sin secretos y sin dependencias nuevas.
- [x] *El parte como unidad.* N/A: F-056 no toca el circuito de partes.
- [x] *Nada se cierra sin validar; dry-run ante Sigrid.* F-056 **no escribe en Sigrid**: R39 y
  `test_f056_r39_ninguna_linea_anadida_por_la_rama_nombra_una_escritura`. La puerta del volcado es `aprobar`, que
  valida contra Sigrid en vivo.
- [x] *Lo manuscrito / firmado no es conforme.* N/A: no toca la extracción ni la clasificación.
- [x] *Reprocesar no duplica.* N/A: no toca la importación. La revisión es append-only y la bandeja no cambia.
- [x] *Estados de Sigrid sin hardcodear.* N/A: no consulta ni escribe `con.est`.
- [x] Ningún PDF ni escaneado en git (`git log --diff-filter=A f86d639..HEAD`).

### C3 bis — Documentos de fuera
- N/A (justificado): la rama no añade ni modifica nada en `docs/referencia/`.

### C4 — La verificación es real
- [x] Cada requisito R1–R48 tiene al menos un test `test_f056_rN_*` y todos pasan (tabla de abajo). R44 incluye
  `azure-apps`, que es T16 del líder al desplegar.
- [x] Los unit tests no tocan red ni base: dobles y conexión falsa. `tests_bbdd` solo corre con la base efímera:
  T8, 53 passed.
- [ ] **Las `MANUAL (humano)` pendientes (T18, T19) no tienen su comando exacto completo, y `progress/current.md` no
  las lista.** Ver C-2 y C-4.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: "critico"` declarado y válido.
- [x] **Fase RED** con salida real pegada en `progress/impl_F-056.md` para los centrales: Bloques 1, 2, 3 y 3 bis,
  verificada en cada review de bloque. La de T15 (R44, que no es central) la he reproducido yo: 59 failed, 8 passed.
- [x] **Cobertura** `[OK]` 100 % de 1060 líneas.
- [x] **Mutación**: los cuatro informes existen y están generados por la herramienta. Recálculo puro coherente
  (arriba).
- [x] **Muertos**: campañas no reejecutadas, **349 / 29 / 175 / 63 min según sus informes**, todas de más de 5 min,
  y el encargo pide no relanzarlas. Vale el recálculo puro, más los mutantes de herramienta reejecutados y los propios
  de las reviews de bloque.
- [x] **Duración**: coste por mutante entre 808 y 3011 s. Coherente.
- [x] Cero supervivientes y cero timeouts tras el repaso. Ningún equivalente que justificar.
- [x] «Evidencias» con los cuatro números y los workers en los Bloques 1–3 bis. El Bloque 4 los da en línea (257
  passed, cobertura 100 %, sin mutación porque solo hay documentación y tests de documentación, suite de 1551 s). O-5.
- [ ] **Verificaciones `MANUAL (humano)` con su comando exacto** (exigencia propia de `critico`): T19, paso 3, no lo
  tiene y su resultado esperado es erróneo (C-1, C-2). Las de antes (T0 y T8) sí tienen comando y resultado real.
- [x] Ningún N/A sin justificar.

### C4 ter — Rutas sensibles
- N/A: el repositorio no tiene `harness/rutas_sensibles.json`.

### C5 — La sesión se cerró bien
- [x] `tasks.md`: T0–T15 y T17 marcadas, con commits `F-056 Tn:`. **T16, T18, T19 y T20 quedan sin marcar por
  diseño**: son del líder y del humano, posteriores a esta review (T16 por decisión del líder del 2026-10-08).
- [x] Sin ficheros temporales ni artefactos sin seguimiento (`git status` limpio).
- [x] `features.json` dice `in_progress`, que es lo real.

## Cobertura: requisito → test

Todos los tests pasan sin caché. Hay al menos un test por requisito; entre paréntesis, cuántos `test_f056_rN_*`
hay.

| R | Test (fichero) |
|---|---|
| R1 (10) | `test_f056_r1_una_fila_sin_revisiones_ni_original` (repositorio) y las tablas de §3.2 (dominio) |
| R2 (6) | `test_f056_r2_la_transicion_va_antes_que_sigrid_y_no_escribe` (pipeline) |
| R3 (3) | `test_f056_r3_editar_una_aprobada_la_saca_de_las_candidatas` (pipeline) |
| R4 (5) | `test_f056_r4_se_registra_la_foto_quien_y_la_hora` (pipeline) |
| R5 (11) | `test_f056_r5_el_oid_de_1_vale` (dominio) y las formas inválidas con fábricas prohibidas (http) |
| R6 (3) | `test_f056_r6_incidencia_que_no_esta_es_404_sin_sigrid_ni_escritura` (pipeline) |
| R7 (18) | `test_f056_r7_la_frescura_va_antes_que_sigrid_y_no_escribe` (pipeline), más dos conexiones en `tests_bbdd` |
| R8 (4) | `test_f056_r8_la_foto_nueva_es_la_situacion_con_la_revision_guardada` (pipeline) |
| R9 (5) | `test_f056_r9_validar_quien_recorta_y_conserva_mayusculas` (dominio) y `…r9_el_correo_se_guarda_recortado_y_sale_en_listado_e_historial` (http) |
| R10 (6) | `test_f056_r10_las_situaciones_leen_estas_columnas_en_este_orden` (repositorio) |
| R11 (1) | `test_f056_r11_el_correo_no_sale_en_ningun_error` (http) |
| R12 (3) | `test_f056_r12_solo_15_declara_una_columna_de_correo` (alcance) |
| R13 (38) | `test_f056_r13_editar_lee_sigrid_una_vez_entre_la_situacion_y_registrar` (pipeline) y los de campo a campo (dominio) |
| R14 (5) | `test_f056_r14_los_nombres_salen_de_sigrid_y_no_de_lo_guardado` (dominio) |
| R15 (7) | `test_f056_r15_oficio_ambiguo_y_oficio_nulo_lo_conserva_con_su_proveedor` (dominio) |
| R16 (5) | `test_f056_r16_sin_cambios_no_escribe` (pipeline) |
| R17 (2) | `test_f056_r17_r37_la_unica_escritura_es_el_insert_en_revisiones` (repositorio) |
| R18 (9) | `test_f056_r18_el_motivo_solo_va_en_descartar` (ddl) y los de 500/501 (dominio, http) |
| R19 (2) | `test_f056_r19_recuperar_no_lee_sigrid_y_motivos_es_none` (pipeline) |
| R20 (12) | `test_f056_r20_aprobar_lee_sigrid_una_vez_entre_la_situacion_y_registrar` (pipeline) |
| R21 (15) | `test_f056_r21_los_nueve_motivos_en_su_orden` (dominio) |
| R22 (18) | `test_f056_r22_aprobar_una_duplicada_espera_tambien_la_ultima_de_su_original` (pipeline) |
| R23 (14) | `test_f056_r23_r24_constantes` (paginación) y las validaciones previas (http) |
| R24 (8) | `test_f056_r24_mas_del_tope_es_bandeja_demasiado_grande_con_el_recuento` (pipeline) |
| R25 (24) | `test_f056_r25_clave_de_orden` (paginación) y `…r25_recorrer_las_paginas_da_cada_fila_una_vez_y_en_orden` (http) |
| R26 (7) | `test_f056_r26_filtro_de_estado` (paginación) |
| R27 (4) | `test_f056_r27_resumen_sobre_todas_las_filas` (paginación) |
| R28 (4) | `test_f056_r28_la_pagina_lleva_el_catalogo_leido_y_el_mismo_mapa_que_valida` (pipeline) |
| R29 (6) | `test_f056_r29_fila_de_revision_sin_revisiones` (paginación) |
| R30 (13) | `test_f056_r30_sin_sigrid_no_se_escribe` (pipeline) y `…r30_sin_sigrid_o_sin_base_el_listado_es_503` (http) |
| R31 (1) | `test_f056_r31_el_log_del_listado_solo_lleva_obra_tamano_y_recuentos` (http) |
| R32 (6) | `test_f056_r32_historial_de_una_que_no_esta_es_404` (pipeline) |
| R33 (8) | `test_f056_r33_historial_con_los_campos_cambiados_frente_a_la_anterior` (pipeline) |
| R34 (13) | `test_f056_r34_candidatas_solo_las_de_ultima_aprobar` (pipeline) |
| R35 (6) | `test_f056_r35_aprobar_una_ubicacion_sin_recortar_no_es_aprobable` (dominio) |
| R36 (28) | `test_f056_r36_el_fichero_va_detras_de_los_de_f036` (ddl) |
| R37 (7) | `test_f056_r37_el_codigo_de_f056_no_actualiza_ni_borra` (alcance) |
| R38 (1) | `test_f056_r38_el_indice_da_la_ultima_revision_por_revision_id` (ddl) |
| R39 (4) | `test_f056_r39_ninguna_linea_anadida_por_la_rama_nombra_una_escritura` (alcance) |
| R40 (4) | `test_f056_r40_el_codigo_de_f056_no_mira_ninguna_ventana_de_escritura` (alcance) |
| R41 (3) | `test_f056_r41_el_log_de_registrar_no_lleva_ni_oid_ni_correo_ni_textos` (repositorio) y los de `caplog` (http) |
| R42 (1) | `test_f056_r42_cualquiera_del_grupo_puede_actuar_sin_roles` (http) |
| R43 (1) | `test_f056_r43_la_identidad_sale_del_cuerpo_y_no_de_las_cabeceras` (http) |
| R44 (34) | `test_f056_r44_*` (documentación). La parte de `azure-apps` es T16, del líder |
| R45 (3) | `test_f056_r45_la_rama_no_toca_los_tests_de_f036_ni_de_f053` (alcance) |
| R46 (40) | `test_f056_r46_listar_lee_cada_cosa_una_vez_y_en_orden` (pipeline) y los de `test_f056_ubicaciones.py` |
| R47 (4) | `test_f056_r47_ubicaciones_que_difieren_en_mayusculas_o_letras_se_quedan` (dominio) |
| R48 (26) | `test_f056_r48_la_ubicacion_se_valida_contra_el_mapa_leido_de_su_unidad` (pipeline) |

Las reviews de bloque dejaron hallazgos y todos están resueltos en la rama:

- **Bloque 1:** N-1 `4a41ba4`, N-2 `916fa49`, O-1 `dd64e09` y O-3 `97df089`.
- **Bloque 2:** N-1 (b) `5a23429` y O-1 `aa077d1`.
- **Bloque 3:** N-1 `498be0d`, N-2 `6e9d02d`, O-1 `3d722a0` y O-2 `b05abce`.
- **Bloque 3 bis:** N-1 `2236ec6` y N-2 `3bb753a`.
- **O-1 de F-053:** `2861f4f`.

## Cambios requeridos

1. **C-1 · T19, paso 3: el 409 de `revision_previa` vieja no sale como está escrito, y el paso puede dejar viva la
   fila de prueba en producción.**
   - **El problema.**
     - `specs/F-056-revision-bandeja-backend/tasks.md:253-254` dice «Repetir una con una `revision_previa` vieja →
       409 `revision_desactualizada`».
     - Tras la sexta acción, la fila está `descartada`, y desde ahí solo se admite `recuperar`.
     - `comprobar_sin_sigrid` mira la **transición antes que la frescura**
       (`services/postventa-api/domain/models/revision.py:812-819`, antes de la línea 821). Así que repetir
       cualquier otra acción da **409 `accion_no_permitida`**.
     - Con «si algo falla, parar y volver al spec-author», eso para la verificación en falso.
     - Y si se repite `recuperar` con la `revision_id` **vigente** por error, la fila «PRUEBA F-056 - DESCARTAR»
       queda `editada`, activa y aprobable en la bandeja de producción. De ahí podría acabar en el volcado de F-040.
   - **Cambio.**
     - Que el paso diga **exactamente** que se manda `recuperar` con `revision_previa` igual a la `revision_id` de
       la **primera** respuesta (la del primer `editar`), y que se espera **409 `revision_desactualizada`**, sin
       escribir.
     - Después, comprobar que la fila sigue `descartada`: `GET /api/revision?obra=0677&estado=descartada` la
       contiene, y el historial del paso 4 tiene **seis** revisiones, la última `descartar`.
2. **C-2 · T19, paso 3: faltan los comandos exactos, que una MANUAL de rigor `critico` exige (design §0 y
   `CHECKPOINTS.md`).**
   - **El problema.** Hoy el paso describe en prosa el cuerpo de seis POST, y deja a quien prueba armar a mano:
     - las 8 claves de `valores`;
     - la identidad, «como la saca `identidadDe`».
   - **El riesgo.** Si la fila se importa con un oficio de un grupo de varios códigos, el `oficio_codigo` vigente es
     `null` (ambiguo). Si la primera edición no elige un código concreto, el `aprobar` siguiente da **409
     `incidencia_no_aprobable` con `oficio_ambiguo`**, y se para en falso.
   - **Cambio.** Pegar el JS exacto, para ejecutar en `importar.html`, que carga `js/api.js` y deja `window.Api`
     (`services/postventa-front/js/api.js:735-737`):
     - `const yo = Api.identidadDe(await (await fetch('/.auth/me')).json());`
     - una función `accion(cuerpo)` que hace el `fetch` POST con `confirmado: true`, `usuario_oid: yo.usuarioOid`
       y `usuario_correo: yo.correo`, y devuelve `{status, json}`;
     - la construcción de `valores` desde `fila.vigentes`, con las 8 claves de `CAMPOS_PEDIDOS`;
     - en la primera edición, una ubicación de `r.catalogo.ubicaciones[fila.vigentes.unidad_codigo]`, un
       `oficio_codigo` concreto (el vigente o, si es `null`, el primero de su `grupo.codigos` en
       `r.catalogo.oficios`) y `proveedor_codigo: null`;
     - en cada respuesta, la comprobación `!JSON.stringify(json).includes(yo.usuarioOid)` (R10, R41).
3. **C-3 · T19 no comprueba de forma explícita que el 503 de las ubicaciones ya no existe.**
   - **El problema.** El encargo lo pide, y hoy solo se deduce de que el paso 2 «funcione».
   - **Cambio.** Añadir al paso 2:
     - que `GET /api/revision` responde **200 y no 503**;
     - que `Object.keys(r.catalogo.ubicaciones).length` es **15**;
     - y que ninguna de esas 15 listas está vacía (T0: 0 unidades sin tipología).

     Añadir al paso 3 que el primer `editar`, con una ubicación de la lista, responde **200**. Así se ve, en el
     entorno desplegado, que la lectura real de las ubicaciones está compuesta: hasta el Bloque 3 esas dos
     llamadas daban 503.
4. **C-4 · `progress/current.md`: el bloque de F-056 se quedó en «Bloque 3 bis hecho, pendiente de review».**
   - **El problema.** No dice que el Bloque 4 (T15, T17) está hecho ni que viene la review final, y no lista las
     MANUAL que quedan. C4 pide que estén listadas en `current.md` con su comando exacto, o al menos citadas por
     referencia, que es el criterio que se aceptó en F-053.
   - **Cambio.** Añadir una línea con:
     - el Bloque 4 hecho (`55696f0`);
     - esta review;
     - y «pendientes: T16 (líder), T18 y T19 (MANUAL humano, comandos en `tasks.md`), T20 (líder)».

## Observaciones (no bloquean)

- **O-1 · T18 sin los comandos del merge ni la comprobación del commit.**
  - Dice «merge normal… desde un worktree aparte», pero no da los comandos.
  - Dice «con los mismos parámetros que el último despliegue». Hoy eso es **sin parámetros**: ventanas abiertas por
    defecto (decisión del 2026-09-23), y `DESPLEGAR` cuando lo pida.
  - Como en T10 de F-053, convendría añadir: «antes de lanzarlo, `git -C ..\postventa-publicar log -1 --oneline`
    tiene que ser el merge de F-056 en `dev`».
  - Si el líder entrega T18 como script más una línea, que es la costumbre del humano, basta con que el script lo
    haga.
- **O-2 · `persona.apellido@empresa.es`** en `services/postventa-api/tests/test_f056_documentacion.py:187`.
  - Es un control negativo del barrido de correos, no un dato real.
  - Pero `tasks.md` pide correos ficticios `@ejemplo.invalid`, y `empresa.es` es un dominio que puede existir.
  - Propuesta: `persona.apellido@ejemplo.invalid`. El control sigue cazando, porque lo que prueba es el punto en la
    parte local.
- **O-3 · Para F-059: duplicadas que vuelven a coincidir después de aprobar.**
  - Una fila con `duplicada_de` que se edita para distinguirla y se aprueba **sigue siendo candidata** aunque
    después alguien edite la original para que las claves vuelvan a coincidir.
  - R22 solo bloquea en el momento de aprobar, R34 mira solo la última acción, y el listado le enseñará el motivo
    `duplicada` mientras sigue en las candidatas.
  - Cumple la spec, y es el mismo caso que «Sigrid cambia entre aprobar y volcar», ya documentado en INTEGRACION §5.
  - Pero F-059 manda al ERP de producción, y su idempotencia por `referencia_externa` no lo caza, porque son
    incidencias distintas.
  - Propuesta para el spec-author de F-059: al ensayar, excluir con motivo propio las candidatas cuyos motivos de
    hoy no estén vacíos, o al menos las que tengan `duplicada`.
- **O-4 · Al desplegar (T20), quitar el «sin desplegar»** de:
  - la cabecera de `docs/INTEGRACION.md`;
  - «Lo nuevo de F-056» (§1);
  - el párrafo de §8 y la fila de §10;
  - y «Añadida el 2026-10-08 por F-056, implementada en su rama y sin desplegar» en `docs/ARCHITECTURE.md`.

  Ningún test de F-056 fija esa frase, así que se puede cambiar sin tocar tests.
- **O-5 · El Bloque 4 del informe no tiene una sección «Evidencias» con formato propio.** Los números están en el
  texto: 257 passed, cobertura 100 % de 1060, sin mutación (solo documentación y tests de documentación), suite de
  1551 s. Lo acepto, porque el bloque no tiene código de producción.
- **O-6 · `ruff` da I001 si se lanza desde `services/postventa-api`, pero no desde la raíz.** Lanzado desde
  `services/postventa-api`, salen 23 I001 en ficheros de la rama, porque el `known-first-party` cambia según el
  directorio. Lanzado desde la raíz, como lo hace `init.sh`, no sale ninguno. No hay que hacer nada; lo dejo anotado
  para que otro reviewer no lo confunda con deuda nueva.

## Propuesta de mejora del protocolo (para que la apruebe el humano)

**`reviewer.md`, sección «Validación contra el nivel de rigor», punto nuevo 8.** Propongo este texto:

> «En rigor `critico`, recorre cada paso de las `MANUAL (humano)` pendientes **contra el código**. Para cada
> resultado esperado, comprueba qué rama del código lo produce y en qué orden se evalúan las condiciones: por
> ejemplo, la transición antes que la frescura. Revisa también qué estado deja el paso si se ejecuta mal.»

Motivo: C-1 solo se ve leyendo `comprobar_sin_sigrid` con el paso de T19 delante. Un paso de verificación en
producción con un resultado esperado imposible para en falso la verificación. Y uno que admite un error plausible
deja datos de prueba vivos en producción.

Vale para cualquier proyecto con MANUAL contra producción: hay que portarlo a `arnes-base` si se aprueba.
