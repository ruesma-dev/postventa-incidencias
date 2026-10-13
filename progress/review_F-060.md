<!-- progress/review_F-060.md -->
# F-060 · Review final (antes de desplegar)

- **Veredicto:** **CHANGES_REQUESTED, solo en el texto del Bloque 6 de `tasks.md`** (C-1 y C-2). El código, los
  tests, la mutación y `docs/` quedan **aprobados**: no hace falta tocar nada de `services/` ni de `docs/` ni relanzar
  ninguna campaña. Con C-1 y C-2 aplicados (cambio solo de texto en `specs/F-060-normalizar-ubicaciones/tasks.md`),
  el veredicto pasa a **APPROVED condicionado a T7**: «58 passed», con **0 skipped y 0 failed**, en
  `infra\pruebas_bbdd_efimera.ps1` (58 = lo que recoge hoy `pytest --collect-only tests_bbdd`). El líder puede
  comprobar C-1 y C-2 leyendo el texto, sin otra review entera. Mismo patrón que la review final de F-056 (cambios
  solo en el texto de su T19).
- **Rama:** `feature/F-060-normalizar-ubicaciones`, HEAD `fca2589`. **Base fija `33d8938`.** Revisado el 2026-10-13.

## Nivel de rigor

`critico` (declarado en `harness/features.json`). Exige: fase RED con traza pegada en los centrales, cobertura de
las líneas cambiadas ≥ 80 %, campaña de mutación con **cero supervivientes** salvo aceptación **escrita** del
humano (también los mutantes a mano), RM7 (mover las puertas de orden) y las verificaciones `MANUAL (humano)` con su
comando exacto.

## Lo ejecutado (resultados reales)

| Qué | Resultado |
|---|---|
| `bash harness/init.sh`, tal cual | **ENTORNO LISTO**. Herramientas del arnés 115 passed; api y front en verde **por caché** («árbol sin cambios desde el último verde»: el de T23, 8147 passed, 123 skipped); **PUERTA COBERTURA 100,0 % de 324 líneas** (324/324, nivel crítico); `rigor` válido; una sola feature `in_progress` |
| Sin caché, `pytest -p no:cacheprovider tests/test_f060_*.py tests/test_f006_repo_sin_identificadores.py` | **521 passed** en 171 s |
| Sin caché, los colindantes: `-k "f056 or f036 or f010 or f053 or f012 or f019 or f038" tests/ -x` | **4048 passed, 37 skipped**, 0 failed, en 421,5 s (los skipped, de la familia de los 123 de siempre de T23: controles de diff de otras ramas) |
| `pytest --collect-only tests_bbdd` | 58 recogidos (incluye los 5 de `test_f060_bbdd_lote.py`): la cifra de la condición de T7 cuadra |
| `git diff --name-only 33d8938..HEAD` | Ni `services/postventa-front/`, ni `infra/`, ni ningún `.sql`, ni la plantilla (`config/plantilla_incidencias.yaml`, `infrastructure/documentos/`), ni `infrastructure/sigrid/`, ni `.env` |
| Barrido de líneas añadidas (GUID, correos, `print(`, `breakpoint`, `TODO`, `pdb`) | GUID: **ninguno**. Correos: solo `@ejemplo.invalid` y `persona.apellido@empresa.es`, que es el control negativo del barrido de correos (ya estaba en `test_f056_documentacion.py:187`, O-2 de la review de F-056). Depuración: ninguna. Ficheros añadidos: solo `.py` y `.md` (`git log --diff-filter=A`) |
| Ubicaciones | Solo genéricas o ficticias («Sala Ejemplo», «Baño Ejemplo», «Baño», «Cocina», «Terraza»); el «Baño 1» / «baño 1» de la ficha de `features.json` ya estaba en la base (texto del humano) |
| Recálculo puro de la mutación (`harness.alcance` + `generar_mutantes`, desde el temporal, sin ejecutar la suite) | Ver C4 bis: cuadra campaña a campaña |
| RM7 del Bloque 5 en una copia desechable | La base antes que Sigrid en `listar_revision` → **2 failed** de `test_f060_tiempos.py` (los de la propia feature). Copia borrada; árbol limpio |


## Lo que las reviews de bloque no podían ver

### 1 · La feature de punta a punta

Importar → normalizar tras importar → listar con motivos → normalizar a demanda con ensayo → aprobar:

- **Importar.** `importar_excel` (`interface_adapters/api/importar.py:217-221`) llama a la normalización **después**
  de `paso_excel_errores` y **solo** si `nuevas + duplicadas_en_fichero > 0`; con `ya_importado` no se llega. La
  captura amplia (`except Exception`, decisión del humano 2026-10-12) está en **un solo punto**
  (`_normalizar_tras_importar`), cubre componer y ejecutar, y el aviso lleva solo la obra y el tipo. La respuesta
  sale de `serializar_importacion`, que no cambia (R33; la guardia de T19 compara su cuerpo con la base).
- **Normalizar.** Dominio puro (`domain/models/normalizacion.py`), lista **permitida** (`nueva`, `editada`), unidad
  y ubicación **vigentes**, el exacto gana, la ambigua no elige, el resultado es el valor de la lista. El lote
  (`repositorio_revision_pg.py:116-221`) bloquea con el **mismo** `select_bloquear` que `registrar` de F-056: la
  acción humana y el lote se serializan sobre las mismas filas, así que la frescura por fila es real, y una
  desactualizada se salta sin abortar.
- **Listar.** El listado y la normalización usan **la misma** fuente de ubicaciones sobre el catálogo de
  `leer_catalogo` (`application/pipelines/revision.py:263-265` y `interface_adapters/api/normalizacion.py`), así
  que lo que una normaliza es exactamente lo que el otro deja de marcar.
- **Equivalencia que usa el guion de T26** (`no_exactas === por_motivo.ubicacion_fuera_de_lista`), comprobada en el
  código: F-056 marca `ubicacion_fuera_de_lista` si `ubicacion.strip()` no está en la lista, para **todos** los
  estados (`domain/models/revision.py:741`, `fila_de_revision` sin filtro de estado, y `resumen` cuenta la obra
  entera); F-060 cuenta en `no_exactas` lo que no está **tal cual**. Solo difieren en una vigente con blancos en los
  extremos cuyo recorte sí está, y eso es **inalcanzable**: la importación solo admite la etiqueta exacta del YAML
  (`domain/models/importacion.py:386`) y editar recorta (`revision.py:563`). Si algún día ocurre, el guion se para
  con su `Error('F060 para: …')`: falla hacia el lado seguro.
- **Aprobar.** R24 (la candidata lleva el texto de Sigrid) y R25 (sin normalizar, 409; editar con la variante, 400)
  tienen test; `domain/models/revision.py` no cambia (guardia de T19).
- **Compatibilidad hacia atrás de los datos.** Las revisiones del sistema son filas `editar` normales: el código de
  F-056 las lee sin cambio (`Revision` no valida el correo al leer) y caben en los `CHECK` de
  `15_revisiones_bandeja.sql` (correo 3–254, sin exigir `@`; ubicación ≤ 48, garantizado por la fuente filtrada de
  F-056). Volver a publicar la versión anterior **no rompe** nada de lo escrito (lo uso en C-2).

### 2 · Contratos de F-038 y F-059 (solo lectura; para el líder)

- **F-038** (`postventa-f038`, `specs/F-038-bandeja-revision/`): **ninguna forma cambia**. Lo que verá distinto:
  R4 pintará «editar por sistema:normalizar_ubicacion el …»; R8, una revisión `editar` del sistema con «llegó así»;
  R9, la ubicación normalizada casa con `catalogo.ubicaciones`; R12, una fila recién normalizada (también por una
  importación hecha en otra pestaña) da el 409 `revision_desactualizada` que F-038 ya maneja. R15 (solo las tres
  rutas de F-056) no se ve afectado: F-038 no llama a la ruta nueva. **Mejora opcional para su spec**, antes de que
  empiece: rotular «normalizada por el sistema» cuando el correo es `sistema:normalizar_ubicacion` (la marca es el
  correo, no el `oid`: INTEGRACION §7).
- **F-059** (`postventa-f040`, `specs/F-059-volcado-sigrid-backend/`): (a) la cuenta de anónimos pasa de
  «veintitrés» a **«veinticuatro»** (su design §8 y línea 464, R42, T de documentos líneas 153–161 y 200 de su
  `tasks.md`); (b) sus tests de documentación tendrán que ampliar como aquí: `test_f010` a 24,
  `test_f012` `NUMERALES` hasta 24, «Los veintiuno» a `not in` en `test_f019`, `test_f053` y
  `test_f056_documentacion` (r44 cuenta); (c) `test_f056_repositorio_revision.py::test_f056_r34_…` exige ahora el
  conjunto **exacto de siete** operaciones de `RevisionPort`: si F-059 añade alguna, ese test es suyo de ampliar;
  (d) su `estado_de` con `volcada` / `en_duda` deja esas filas fuera de la normalización sin hacer nada (lista
  permitida); (e) su `16_volcados_sigrid.sql` sigue siendo el 16 (F-060 no tiene DDL).
- **F-058**: al rehacer la importación debe conservar la llamada de `importar_excel` (o decir por qué sobra); ya
  está como `blocked_by` en su ficha.

### 3 · La documentación dice la verdad

Leídos contra el código: `INTEGRACION.md` cabecera (F-060, 2026-10-13, **sin desplegar**; F-056 y su despliegue
siguen), §1 (ninguna lectura nueva; cuándo se hace la tercera), §2 (sin DDL, el lote, el ensayo abre conexión pero no
inserta), §4 (ninguna variable), §6 (fila de la normalización tras importar), **§7** (la identidad del sistema no es
un dato personal; **la marca es el correo**, porque `validar_quien` admite cualquier `oid` de 1–128 y exige `@` en el
correo: verificado en `domain/models/revision.py:474-502`; la 200 de las acciones no lleva correo), **§8** (fila de
la ruta, «Los veintiuno quedan en nivel anónimo», «tampoco depende de ninguna ventana», fila de «Qué NO está
desplegado»), §9. `ARCHITECTURE.md`: la sección de F-060 (regla, constancia, cuándo, `editada`, la medición con los
nombres **reales** de los tramos, `bandeja.*`) y la enmienda del «No revisa». La cabecera de `function_app.py`
(veintiuno). Todo cuadra. Los «sin desplegar» los tendrá que cambiar el líder al cerrar (T36).

### 4 · Tests de otras features (diff contra `33d8938`)

Tocados fuera de F-060 exactamente los declarados en R39, `design.md` §12 y la cabecera de `tasks.md`, y vigilados
función a función por `test_f060_alcance_cerrado.py`:

| Test | Cambio | ¿Relaja? |
|---|---|---|
| `test_f010_endpoints_protegidos.py` | `ENDPOINTS` + `revision/normalizar`; `== 21` | No: amplía |
| `test_f053_documentacion.py` | `CUENTA_VIGENTE` «Los veintiuno» y «Los veinte» en `not in` | No: añade una aserción |
| `test_f012_documentacion.py` | `NUMERALES` gana el 21 | No |
| `test_f019_documentacion.py::test_f019_r32_…` | «Los veintiuno» `in`; «Los veinte» pasa a `not in` | No |
| `test_f056_documentacion.py::…_la_seccion_ocho_…` | «Los veintiuno»; «Los veinte» en `not in` | No |
| `test_f056_documentacion.py::…_la_cabecera_dice_que_f056_lo_toco` | De «F-056 es la última y la fecha es 2026-10-09» a «cabecera bien formada, que no retrocede, con F-056 y su despliegue» | **Cambia lo que exige** (declarado, decisión del **líder** con el criterio que el humano aprobó en F-056). Ver O-1 |
| `test_f056_repositorio_revision.py::test_f056_r34_…` | Conjunto exacto de siete | No: decisión escrita del humano 2026-10-10 |

### 5 · Alcance

Nada fuera de `services/postventa-api/`, `docs/`, `specs/F-060-…/`, `progress/`, `BACKLOG.md` y
`harness/features.json` (este último: la ficha de F-060 a `in_progress` y la de F-058 con las respuestas del humano y
su `blocked_by`, ya en el commit de la spec). Sin DDL (ningún `.sql` en el diff; R37 con test). Nada escribe en
Sigrid ni mira una ventana (R38 con test, con `importar.py` entero). Ni front, ni plantilla, ni `infra/`.

### 6 · El Bloque 6, comprobado nombre a nombre contra el código

| Lo que usa el guion | Dónde está en el código | ¿Cuadra? |
|---|---|---|
| `GET /api/revision?obra=&estado=todas&tamano=1` | `_filtro` admite `todas`; `_tamano` de 1 a 200 (`interface_adapters/api/revision.py:352-385`) | Sí |
| `resumen.por_motivo.ubicacion_fuera_de_lista`, `resumen.por_estado` | `listar_revision`, «resumen» (todas las claves del enum, también a 0) | Sí |
| `POST /api/revision/normalizar` `{obra, confirmado: true, ensayo}` | `function_app.py:1759`, `_peticion` en `normalizacion.py` (exactamente las tres claves) | Sí |
| Respuesta `normalizadas`, `conflictos`, `normalizables`, `no_exactas` | `normalizar_obra`, `respuesta` | Sí |
| `j.codigo` en un error | `_error_de_revision` y `_rechazo_de_obra` lo llevan; la 503 no (sale `''`, que el guion admite) | Sí |
| `estado=editada&tamano=200`, `incidencias`, `revisado_por`, `cambios`, `motivos_no_aprobable`, `importados.ubicacion`, `vigentes.ubicacion`, `incidencia_id` | `_fila` (`revision.py:615-638`); en el listado `motivos_no_aprobable` es siempre lista | Sí |
| `GET /api/revision/historial?incidencia_id=`, `revisiones[]`, `accion`, `correo`, `campos_cambiados`; la última es la más reciente | `historial_revision` (`revision.py:448-466`), de la más antigua a la más reciente | Sí |
| `'sistema:normalizar_ubicacion'` | `TEXTO_SISTEMA` | Sí |
| `requests | where name == "revision"` | `def revision` en `function_app.py:1618` (mismo patrón que `name == "archivar"` de `DESPLIEGUE.md`) | Sí |
| `traces | where message startswith "F-060 tiempos del listado"` | `Cronometro.linea` | Sí |
| `infra\24_ubicacion_sigrid.ps1 -CodigoObra 0677` | `param([string]$CodigoObra, …)`; solo `sql/read`; igual que en F-056 | Sí |
| `infra\desplegar_backend.ps1` sin parámetros | `param([switch]$SinPublicar, [switch]$VentanasCerradas, [switch]$WhatIf)`; sin parámetros = ventanas abiertas, que es el defecto decidido por el humano el 2026-09-23 y lo que se usó en F-056 | Sí (ver O-3) |
| El front no calienta la Function al abrir `importar.html` | `iniciar()` solo llama a `/.auth/me` | Sí |
| `/api/*` por la Static Web App | `staticwebapp.config.json`: comodín `/api/*` para `authenticated` | Sí |

Lo que **no** cuadra son C-1 y C-2.

## Checkpoints

**C1**
- [x] `bash harness/init.sh` termina en verde (ENTORNO LISTO).
- [x] Existen los ficheros del arnés.

**C2**
- [x] Una sola feature `in_progress` (F-060).
- [x] Rama `feature/F-060-normalizar-ubicaciones`.
- N/A · `progress/current.md` solo con la sesión activa. **Justificación:** lo mantiene el líder; arrastra el
  histórico de F-056 desde antes de esta rama y el líder lo limpia al cerrar (T36). No es trabajo del implementer.
- N/A · Feature `done` con resumen en `history.md`. **Justificación:** F-060 no está `done`; su resumen es T36.

**C3**
- [x] Hexagonal: el dominio nuevo solo importa del dominio; el puerto en `domain/ports`; el repositorio en
  `infrastructure`; la composición en el borde (`test_f005_arquitectura` y `test_f036_arquitectura` en verde).
- [x] Primera línea con la ruta en todos los ficheros nuevos (código y tests).
- [x] Sin `print`, `breakpoint`, `TODO` ni secretos; sin dependencias nuevas.
- N/A · El parte como unidad, firma, manuscrito, reprocesar, número de estado de Sigrid. **Justificación:** F-060 no
  toca partes, firmas, PDF ni estados de Sigrid; trabaja sobre la bandeja de incidencias.
- [x] Nada se escribe en Sigrid (R38 con test); la escritura propia tiene ensayo obligatorio antes (D-8).
- [x] Ningún PDF ni escaneado añadido (`git log --diff-filter=A`: solo `.py` y `.md`).

**C3 bis**
- N/A · **Justificación:** la rama no añade ni modifica nada en `docs/referencia/`.

**C4**
- [x] Cada requisito R1–R43 tiene ≥ 1 test `test_f060_rN_…` (tabla abajo) y pasan (521 sin caché).
- [x] Los unit tests no tocan red ni base (los de base van en `tests_bbdd`, T7).
- [x] Las `MANUAL (humano)` están listadas con su comando (T7, Bloque 6). **Pero** dos de ellas no se pueden
  ejecutar tal como están escritas, o les falta qué hacer si algo sale mal: C-1 y C-2.

**C4 bis**
- [x] `rigor: critico` declarado.
- [x] **Fase RED** pegada en los cinco bloques (T1, T4, T9, T13 y T13 bis, T17; T19 en copia aislada con 16
  fallos; T20 con 37), todas por aserción.
- [x] **Cobertura**: `[OK]` 100,0 % de 324 líneas.
- [x] **Mutación, recálculo independiente** (cálculo puro, `harness.alcance` + `generar_mutantes` a HEAD):
  | Campaña | Base | Líneas (informe / recalculado) | Mutantes (informe / recalculado) |
  |---|---|---|---|
  | Bloque 1 | `33d8938` | 211 / 211 (`normalizacion.py`) | 19 / 19 |
  | Bloque 2 | `66c981d` | 94 / 94 (38 + 56) | 4 / 4 (1 + 3) |
  | Bloque 3 | `91ad35d` | 308 / 308 (82 + 77 + 149) | 17 / 17 (5 + 6 + 6) |
  | Bloque 4 | `c8d60d1` | 111 / 123 hoy (los 12 de más son el docstring de T20, posterior a la campaña) | 6 / 6 |
  | Bloque 5 | `af84848` | 295 / 295 (12 + 115 + 168) | 10 / 10 (0 + 0 + 10) |
  | Feature | `33d8938` | — | **56** = 19 + 4 + 17 + 6 + 10 |
- [x] **Los muertos.** Las cinco campañas pasan de 5 minutos (744 s a 2769 s): **campaña no reejecutada**, me quedo
  en el recálculo puro (y el líder pidió no relanzar). Coste por mutante (tiempo × workers ÷ mutantes): 1166 s,
  744 s, 848 s, 1043 s y 1237 s: plausible para una suite que corta en el primer fallo.
- [x] Sin supervivientes en ninguna campaña. A mano: los tres equivalentes (X01, H11, I19) tienen la aceptación
  **escrita** del humano (commits `913ea8d`, `c8d60d1`, `c4ab836`); los dos vivos del Bloque 5 (T12, T22) se cerraron
  con tests.
- [x] **RM7 (orden).** Bloques 2–4, hechos por sus reviews. **Bloque 5, hecho aquí:** en una copia desechable de
  `services/postventa-api` en el temporal, `construir_revision` subido por encima de `construir_catalogo_obra` en
  `listar_revision` → `test_f060_tiempos.py`: **2 failed, 45 passed**
  (`test_f060_r40_el_listado_deja_una_linea_con_cada_tramo`,
  `test_f060_r41_con_y_sin_medicion_la_misma_respuesta_las_mismas_llamadas_y_el_mismo_orden`, «At index 0 diff:
  'revision' != 'catalogo'»). Lo caza la propia feature. Copia borrada.
- [x] «Evidencias» con los cuatro números y los workers de cada campaña.
- [x] Ningún N/A de este bloque sin motivo.

**C4 ter**
- N/A · **Justificación:** el repositorio no tiene `harness/rutas_sensibles.json`.

**C5**
- [x] T1–T6, T8–T23 `[x]`, con su commit `F-060 Tn: …` (T22 y T23 en uno, `fca2589`).
- N/A · T7 y T24–T36. **Justificación:** son MANUAL del humano, del líder (T29, T36) o condicionales (Bloque 7);
  T7 es la condición de este veredicto.
- [x] Árbol limpio (`git status`), sin temporales en el repositorio.
- [x] `features.json`: F-060 `in_progress`, que es lo real.

## Cobertura: requisito → test (uno por requisito; hay más)

| R | Test |
|---|---|
| R1 | `test_f060_normalizacion_dominio.py::test_f060_r1_la_clave_recorta_y_pliega_mayusculas` |
| R2 | `…::test_f060_r2_cada_fila_de_la_tabla` |
| R3 | `…::test_f060_r3_lista_vacia` |
| R4 | `…::test_f060_r4_lo_que_no_es_la_misma_palabra_no_coincide` |
| R5 | `…::test_f060_r5_el_resultado_es_el_valor_de_la_lista_caracter_a_caracter` |
| R6 | `…::test_f060_r6_sin_situaciones_el_plan_esta_vacio` (y los de unidad vigente) |
| R7 | `…::test_f060_r7_estados_normalizables_son_nueva_y_editada` |
| R8 | `…::test_f060_r8_la_identidad_del_sistema` |
| R9 | `…::test_f060_r9_la_esperada_es_la_ultima_revision_leida` |
| R10 | `…::test_f060_r10_el_recuento_de_una_obra_y_su_suma` |
| R11 | `…::test_f060_r11_validar_quien_rechaza_el_correo_del_sistema` |
| R12 | `test_f060_repositorio_lote.py` (bloqueo en orden fijo, las frescas en orden) |
| R13 | `test_f060_pipeline_normalizacion.py::test_f060_r13_r20_un_conflicto_se_cuenta_y_no_aborta_las_demas` y el lote |
| R14 | `…::test_f060_r14_un_fallo_de_la_base_en_el_lote_sube_sin_nada_escrito` y el lote |
| R15 | `test_f060_repositorio_lote.py::test_f060_r15_solo_inserta_en_revisiones_y_solo_bloquea_la_bandeja` |
| R16 | `…::test_f060_r16_lote_vacio_sin_transaccion` |
| R17 | `test_f060_pipeline_normalizacion.py::test_f060_r17_mas_del_tope_no_lee_ubicaciones_ni_escribe` |
| R18 | `…::test_f060_r18_una_lectura_de_ubicaciones_con_el_catalogo_recibido` |
| R19 | `test_f060_normalizar_http.py::test_f060_r19_el_ensayo_no_escribe_nada` |
| R20 | `…::test_f060_r20_la_real_escribe_revisiones_del_sistema_con_la_hora_de_la_peticion` |
| R21 | `test_f060_pipeline_normalizacion.py::test_f060_r21_dos_ejecuciones_la_segunda_no_tiene_nada_que_normalizar` |
| R22 | `…::test_f060_r22_la_fila_normalizada_en_el_listado_y_su_historial` |
| R23 | `…::test_f060_r7_r23_lo_que_no_se_normaliza_sigue_como_estaba` |
| R24 | `…::test_f060_r24_normalizar_y_aprobar_da_la_candidata_con_el_texto_de_sigrid` |
| R25 | `…::test_f060_r25_sin_normalizar_aprobar_sigue_siendo_409`, `…_editar_con_la_variante_sigue_siendo_400` |
| R26 | `test_f060_normalizar_http.py::test_f060_r26_la_ruta_responde_400_a_cada_cuerpo_malo_sin_construir_nada` |
| R27 | `…::test_f060_r27_la_ruta_responde_200_con_solo_numeros` |
| R28 | `…::test_f060_r28_la_ruta_responde_como_el_listado_sin_escribir` |
| R29 | `…::test_f060_r29_sigrid_antes_que_la_base_y_tres_lecturas` |
| R30 | `…::test_f060_r30_una_linea_con_la_obra_el_recuento_y_los_segundos` |
| R31 | `test_f060_importar_normaliza.py::test_f060_r31_con_filas_registradas_normaliza_una_vez_tras_el_excel_de_errores` |
| R32 | `…::test_f060_r32_ya_importado_no_normaliza` (y cero filas) |
| R33 | `…::test_f060_r33_la_respuesta_es_la_de_la_importacion_sin_normalizar` |
| R34 | `…::test_f060_r34_cualquier_excepcion_del_normalizador_se_avisa_por_su_tipo`, `…_una_interrupcion_no_es_un_fallo_y_sube` |
| R35 | `…::test_f060_r35_una_linea_con_el_recuento_y_los_segundos` |
| R36 | `test_f060_alcance_cerrado.py::test_f060_r36_las_funciones_que_responden_son_las_de_la_base` |
| R37 | `…::test_f060_r37_la_rama_no_toca_ningun_sql` |
| R38 | `…::test_f060_r38_ninguna_linea_anadida_al_codigo_nombra_una_escritura_ni_una_ventana` |
| R39 | `…::test_f060_r39_la_rama_solo_toca_los_tests_declarados` |
| R40 | `test_f060_tiempos.py::test_f060_r40_el_listado_deja_una_linea_con_cada_tramo` |
| R41 | `…::test_f060_r41_con_y_sin_medicion_la_misma_respuesta_las_mismas_llamadas_y_el_mismo_orden` |
| R42 | `…::test_f060_r42_ningun_registro_del_listado_lleva_correo_oid_ni_textos` |
| R43 | `test_f060_documentacion.py` (47 casos); la parte de `azure-apps` es T29 (líder) |
| V1–V3 | MANUAL, Bloque 6 (T26, T25/T27, T28) |

## Cambios requeridos

Los dos, **solo texto** de `specs/F-060-normalizar-ubicaciones/tasks.md` (Bloque 6). Ningún cambio de código.

1. **C-1 · La medición en frío de T28 no se puede ejecutar tal como está escrita**
   (`tasks.md:298-299`). Dice: «en una pestaña nueva con el mismo bloque `F060.medir` pegado:
   `console.log('En frío (s)', await F060.medir(1));`». En una pestaña nueva **`window.F060` no existe**: la
   primera línea del bloque (`F060.medir = async (n) => {`, `tasks.md:284`) revienta con
   `ReferenceError: F060 is not defined`, y `F060.medir` usa además `F060.exigir`, que se define en el paso 1 de
   T26. Lo natural para salir del paso es pegar el paso 1 de T26 en esa pestaña, y eso **estropea la medición**:
   hace un `GET /api/revision` y un `POST /api/revision/normalizar` antes, que despiertan la Function, y la medida
   «en frío» sale en caliente. Cambio pedido: sustituir esas dos líneas por un bloque **autocontenido** para la
   pestaña nueva, por ejemplo:
   ```js
   window.F060 = {};
   F060.exigir = (c, q) => { if (!c) throw new Error('F060 para: ' + q); };
   F060.medir = async (n) => { /* el mismo cuerpo de arriba */ };
   console.log('En frío (s)', await F060.medir(1));
   ```
   (con el cuerpo de `F060.medir` copiado entero, no por referencia), y una frase: «**en esa pestaña no se pega
   nada de T26**: cualquier otra llamada antes calienta la Function». Añadir qué esperar: en la traza de esa
   petición, `proceso_nuevo=True` si de verdad fue un proceso nuevo; si sale `False`, la medición no fue en frío y
   se anota así.

2. **C-2 · El Bloque 6 no dice qué hacer si algo sale mal** (`tasks.md:190-325`). Hace falta un párrafo «**Si algo
   sale mal**» (al principio del Bloque 6 o tras T24), con al menos:
   - **Antes del merge, anotar el commit de `dev`** (hoy `704cfca`): es la versión a la que se vuelve.
   - **Si tras publicar falla algo que antes funcionaba** (el listado, la importación, el historial, 5xx nuevos):
     no seguir con T25–T28 y volver a publicar la versión anterior con el mismo mecanismo, desde un worktree de
     ese commit:
     ```
     git worktree add --detach ..\postventa-publicar <commit anotado>
     powershell -ExecutionPolicy Bypass -File ..\postventa-publicar\infra\desplegar_backend.ps1
     git worktree remove ..\postventa-publicar
     ```
     y decir por qué es seguro: F-060 no tiene DDL y las revisiones del sistema son filas `editar` que el código de
     F-056 lee sin cambios (`domain/models/revision.py` no se ha tocado); con la versión anterior desaparecen la
     ruta, la normalización tras importar y la línea de tiempos, y lo ya normalizado sigue como `editada` por
     `sistema:normalizar_ubicacion`.
   - **Que la normalización tras importar no tiene interruptor**: si hubiera que pararla, la única vía es la vuelta
     atrás de arriba.
   - **Si el paso 2 de T26 escribe algo que no debía**: **no hay deshacer por la API** (las revisiones son
     append-only, y volver a la variante con `editar` da 400 `valores_no_validos`, R25/D-5). Parar, no relanzar
     nada, anotar los recuentos y volver al líder. Cualquier corrección en la base de producción es una escritura
     que necesita autorización expresa y su propio guion (nunca un `DELETE` improvisado); una persona sí puede
     corregir una a una con `editar` hacia otro valor **válido** de la lista.
   - **Si T27 no da la misma lectura que T25**: F-060 solo lee Sigrid (R38, con test), así que la diferencia es
     actividad de Posventa en el ERP; anotarla por unidad, sin textos, y llevarla al líder antes de cerrar.

## Observaciones (no bloquean; para el líder)

- **O-1 · Dos aceptaciones pendientes, a llevar al humano con nombre** (no bloquean desplegar, sí el cierre, T36):
  (a) la **desviación de los nombres de los tramos** (`construir.bandeja` / `bandeja.listar` en vez de
  `construir.revision` / `revision.listar`), anotada en `design.md` §11.3 como «pendiente de aceptación del líder y
  del humano»; conviene aceptarla **antes de T28**, porque es con esos nombres con los que se leerá M1; y (b) que
  `test_f056_documentacion.py::test_f056_r44_la_cabecera_dice_que_f056_lo_toco` **cambia lo que exige** por
  decisión del **líder** (no del humano), con el criterio que el humano aprobó en F-056: es la única ampliación que
  no es solo una cifra.
- **O-2 · `design.md` §11.2 y §11.3 siguen hablando de `construir.revision` y `revision.listar`** (líneas 432, 433,
  437, 459 y 468) en la tabla de hipótesis H1, H2 y H6 con la que se leerá M1. Con la desviación aceptada, cambiar
  esos nombres por `construir.bandeja` y `bandeja.listar` evita leer mal la medición.
- **O-3 · T24.** El comando es el mismo que en F-056 T18 (y funcionó), pero «con los mismos parámetros que el último
  despliegue» junto a un comando **sin** parámetros puede leerse como que falta algo. Mejor decir: «sin parámetros
  (las ventanas, abiertas, como en cada despliegue desde el 2026-09-23)». Y el «merge normal desde un worktree
  aparte» podría llevar sus comandos, como el resto del bloque.
- **O-4 · T28, qué esperar en Application Insights.** `host.json` tiene el muestreo activo para todo menos
  `Request`: puede haber **menos** líneas `F-060 tiempos del listado` en `traces` que peticiones en `requests`. Una
  frase («si faltan trazas, es el muestreo; se cruzan por `operation_Id` y se mide con las que haya») ahorra una
  falsa alarma. Esperado: 11 peticiones `revision` (10 + 1) con `resultCode` 200.
- **O-5 · Cabeceras de la spec.** `requirements.md` y `design.md` siguen diciendo «Estado: pendiente de aprobación
  del humano»; la aprobación (2026-10-09) solo consta en `tasks.md`. Al cerrar, alinearlas.
- **O-6 · Para el líder, al cerrar (T29, T36).** `azure-apps/postventa_incidencias.md` (la ruta, que la importación
  escribe revisiones del sistema, la marca por el correo, «veintiuno»); los «sin desplegar» de `INTEGRACION.md`
  (cabecera, §8 y «Qué NO está desplegado») y de `ARCHITECTURE.md` pasan a «desplegada»; y limpiar
  `progress/current.md` del histórico de F-056.

## Propuesta de automejora (para que la apruebe el humano; no aplicada)

**A `.claude/agents/reviewer.md`, en «Validación contra el nivel de rigor», un punto 8:** «Todo bloque `MANUAL
(humano)` con código para pegar (consola del navegador, PowerShell) se lee **como si se ejecutara en un entorno
vacío**: cada bloque que diga “en una pestaña nueva” o “en otra consola” tiene que definir todo lo que usa, y ninguno
puede depender de pegar antes otro que tenga efectos (llamadas a la API, escrituras). Y todo bloque MANUAL que
escriba en producción o publique tiene que traer su “si algo sale mal”: a qué versión se vuelve, con qué comando, y
qué no se puede deshacer.» Motivo: C-1 y C-2 de esta review; un guion que solo se lee de arriba abajo no ve que la
pestaña nueva empieza vacía. Vale para cualquier proyecto: candidato a `arnes-base`.

## Comprobación del líder (2026-10-13) · C-1 y C-2

Comprobado leyendo `specs/F-060-normalizar-ubicaciones/tasks.md` en `e852732` (solo cambió ese fichero y una línea
de `progress/impl_F-060.md`): **C-1** resuelto (bloque JS autocontenido para la pestaña nueva, con el cuerpo
entero de `F060.medir`, la advertencia de no pegar nada de T26 y qué esperar de `proceso_nuevo`); **C-2** resuelto
(párrafo «Si algo sale mal» antes de T24, con los cinco puntos). Como preveía esta review, el veredicto pasa a
**APPROVED condicionado a T7** («58 passed», 0 skipped y 0 failed en `infra\pruebas_bbdd_efimera.ps1`).
