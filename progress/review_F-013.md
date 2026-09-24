<!-- progress/review_F-013.md -->
# F-013 · Archivo en la biblioteca de Posventa — Review

- **Rama**: `feature/F-013-archivo-posventa`, HEAD `4492ec6`, base `fadb678` (`dev`).
- **Reviewer**: agente `reviewer`, 2026-09-25.
- **Veredicto: APROBADO (APPROVED)**, con cuatro hallazgos de gravedad baja
  u observación que **no bloquean** (§8). Ninguno toca código de producción
  de forma obligatoria.

## 1 · Nivel de rigor

`critico`, declarado en `harness/features.json` (decisión D-R del humano,
2026-09-18). Exige: C1–C5, C3 bis, tests trazables (C4), **fase RED** en los
requisitos centrales, **cobertura** de las líneas cambiadas ≥ 80 %, **campaña
de mutación** con **cero supervivientes** salvo justificación escrita aceptada
por el humano, verificaciones `MANUAL (humano)` listadas con su comando, y el
punto 7 del protocolo (las puertas que protegen un orden se prueban
moviéndolas).

## 2 · Lo que he ejecutado yo (no copiado del informe)

| Qué | Resultado real |
|---|---|
| `bash harness/init.sh`, tal cual | **ENTORNO LISTO**. Arnés 62 passed; api y front en verde (**por caché**: árbol sin cambios desde el último verde); `PUERTA COBERTURA: 100.0% de 551 líneas cambiadas cubiertas (551/551, umbral 80%, nivel critico)`; rama correcta; una sola `in_progress` (F-013) |
| Suite **completa** del servicio api, sin caché, en un clon desechable del repositorio en mi scratchpad (`git clone` local, intérprete del `.venv` del servicio) | **4.284 passed, 35 skipped in 114.52s**, exit 0: los mismos números que declara el implementer |
| Recálculo puro del alcance (`harness.alcance.alcance_de_feature("F-013")`) y de los mutantes (`harness.mutacion.generar_mutantes`) | **14 ficheros, 2.291 líneas, 109 mutantes**; reparto por fichero idéntico al del informe (destino_posventa 39, destino_archivo 25, paso_archivo 5, consultas_ubicacion 10, graph 14, ubicacion 8, sharepoint/fabrica 3, function_app 2, archivar 2, settings 1, resto 0) |
| El superviviente, contra los mutantes generados | Existe tal cual: `destino_archivo.py:102 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)`. Es el único, así que el muestreo «dos o tres» se reduce a él |
| Código de producción entre la campaña (`50b9cd2`) y HEAD | `git diff --stat 50b9cd2..HEAD`: solo `progress/`, `tasks.md` y dos ficheros de tests. La campaña sigue valiendo para HEAD |
| Punto 7: 14 mutaciones de orden a mano, en el clon desechable (nunca en el árbol) | **14 de 14 muertas** (§5) |
| Barrido de datos sensibles sobre todo lo añadido en la rama | 0 GUID, 0 hosts `*.sharepoint.com`/`*.onmicrosoft.com`, 0 IP, 0 correos, 0 cadenas tipo clave; el único DNI es el inventado `00000000T` de los tests. Ningún PDF/ofimática/CSV añadido (`git log --diff-filter=A`) |
| `git status` del repositorio al terminar | limpio (el clon vive fuera, en el scratchpad) |

## 3 · Checkpoints

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` termina en verde (ENTORNO LISTO).
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md` (los comprueba el propio `init.sh`).

### C2 — El estado es coherente
- [x] Una sola `in_progress`: F-013.
- [x] Rama `feature/F-013-archivo-posventa`.
- [x] `progress/current.md` empieza por la sesión activa (F-013, bloques 0–7).
      **Observación O-1**: por debajo sigue el histórico acumulado heredado de
      `dev` (4.799 líneas). Deuda previa, ya señalada en los reviews de F-032 y
      F-033; F-013 solo añade sus bloques arriba.
- [x] Toda feature `done` tiene resumen en `history.md` (comprobado por
      script: ninguna falta).

### C3 — Arquitectura y convenciones
- [x] Hexagonal: `destino_posventa.py` y los dos puertos solo importan de
      `domain`/stdlib; `destino_archivo.py` solo de `domain`; los adaptadores
      (`graph.py`, `sigrid/ubicacion.py`, `consultas_ubicacion.py`) en
      `infrastructure`; la composición en el borde (`archivar.py`). Lo fija
      además `test_f013_arquitectura.py`.
- [x] Primera línea con la ruta en todos los `.py`, `.ps1` y `.md` añadidos o
      modificados (comprobado fichero a fichero).
- [x] Sin `print()` ni TODO en lo añadido; sin secretos (barrido de §2); sin
      dependencias nuevas (`requirements*.txt` fuera del diff).
- [x] La unidad de trabajo sigue siendo el parte: el resolutor recibe los
      códigos **guardados** de un parte, nunca un PDF.
- [x] Nada se archiva sin validaciones: la puerta de estado, el cotejo de
      F-031 y L1 van **antes** del resolutor (probado moviéndolos, §5). Contra
      Sigrid, **solo lectura** (`/api/sql/read`, con test que prohíbe
      `sql/write`); ningún commit contra el ERP.
- [x] Lo manuscrito / firmado ≠ conforme: F-013 no toca validación ni
      extracción; el resolutor no puede leer `ctx.extraccion` (no recibe el
      contexto; control de F-031 en verde).
- [x] Reprocesar no duplica: L1 intacta y antes de resolver (R45); carpetas
      con `conflictBehavior=fail` y 409 = ya existe (R39); hoja homónima con
      `replace`.
- [x] Ningún número de estado hardcodeado: el tipo de concepto de la
      reclamación sale de `SIGRID_TIP_RECLAMACION` (parámetro `?`).
- [x] Ningún parte escaneado ni PDF en git (`git log --diff-filter=A` de la
      rama: ninguno).

### C3 bis — Documentos que entran de fuera
- N/A — **justificado**: la rama no añade ni modifica nada en
  `docs/referencia/` (`git diff --name-only fadb678...HEAD -- docs/referencia`
  vacío). El barrido de datos sensibles lo he ejecutado igualmente sobre todo
  el diff (§2).

### C4 — La verificación es real
- [x] Cada requisito EARS tiene ≥ 1 test `test_f013_rN_*` que pasa (tabla
      §4), con una salvedad de **nomenclatura** en R24: su contenido lo
      verifican tests con nombre de R25/R45 y R48, pero ninguno lleva `r24` en
      el nombre (hallazgo **H-2**, baja). Lo marco `[x]` porque el requisito
      **está** probado y es localizable desde aquí; el hallazgo pide dejarlo
      trazable por nombre.
- [x] Los unit tests no tocan red ni BBDD: dobles `ExploradorFalso`,
      `UbicacionesFalsas`, repositorio en memoria y transporte `httpx` falso;
      los scripts PowerShell se ensayan con red falsa.
- [x] Verificaciones `MANUAL (humano)`: R31, R33 y R42 con su **comando
      exacto** en `tasks.md` («Después del merge: el corte», pasos 2, 6–8) y
      en `docs/DESPLIEGUE.md` §9; R32 (T3) y T2 **hechas**, con su resultado
      en `progress/explore_F-013.md`. **Hallazgo H-1** (baja): el bloque vivo
      de `current.md` no las copia ni enlaza la sección exacta.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: "critico"` declarado y válido.
- [x] **Fase RED** con salida real en `progress/impl_F-013.md`: T5 (27
      failed, `DID NOT RAISE`, `KeyError`), T6/T8/T9/T12 (`ImportError` en la
      recogida, completado con mutación que demuestra que las aserciones
      muerden), T10 (**46 failed**, `TypeError ... resolver_destino`), T11 (39
      failed), T13/T14 (commits RED `ee7e675`, `f91095c`). T15 pasó a la
      primera y demuestra que muerde con 10 mutantes a mano. **Observación
      O-2**: el RED por `ImportError` de recogida es la forma débil; aquí se
      acepta porque cada uno va acompañado de su mutación.
- [x] **Cobertura**: `[OK]` 100,0 % de 551 líneas cambiadas (mi ejecución).
- [x] **Mutación**: `progress/mutacion_F-013.md` generado por la herramienta;
      totales verificados de forma independiente (§2): alcance, nº de mutantes
      y superviviente coinciden.
- [x] **Muertos comprobados**: «Tiempo total» **2.407,1 s (40 min)**, por
      encima de 5 min. **Campaña no reejecutada: 40 min según el informe**;
      se aplica el recálculo puro de §2, y como verificación adicional del
      orden, mis 14 mutaciones de §5.
- [x] **La campaña tardó lo que tenía que tardar**: 2.407,1 s × 6 workers ÷
      109 = **132,5 s por mutante**. La herramienta lanza la suite con `-x`
      (se corta en el primer fallo) y sin cobertura, así que es normal que
      quede por debajo de los 242 s de la suite completa con cobertura de
      `init.sh`; está a dos órdenes de magnitud del umbral de sospecha (1 s).
- [x] Superviviente con análisis completado y **aceptado por el humano**
      (`_Nivel`, «si», 2026-09-24; nota del líder en `impl_F-013.md`). Ninguna
      sección en `PENDIENTE`. Juicio propio: el equivalente se sostiene —
      `_Nivel` es privado y sus cuatro instancias se construyen en línea sin
      ninguna asignación posterior—.
- [x] Sección **«Evidencias»** con los cuatro números y los workers (6):
      4.284 passed / 35 skipped en 242,55 s; cobertura 100 % de 551; 109
      generados, 108 muertos, 1 superviviente aceptado; workers 6.
- [x] Ningún punto de este bloque en N/A.

### C4 ter — Rutas sensibles
- N/A — **justificado**: el repositorio no tiene `harness/rutas_sensibles.json`
  (solo el `.ejemplo.json`), y sin declaración el bloque no aplica.

### C5 — La sesión se cerró bien
- [x] `tasks.md`: T1–T21 `[x]`, 0 casillas vacías. Commits `F-013 Tn:` por
      tarea. **Observación O-3**: T18 y T19 no tienen commit `F-013 T18:` /
      `F-013 T19:` propio, y está justificado: el entregable de T18 es un
      párrafo del informe (commit `f94351f`, y el líder lo pegó en F-018 en
      `50b9cd2`), y T19 vive en **otro repositorio** (`azure-apps`, commit
      local `9ed8957`, que he comprobado: sin GUID ni hosts del inquilino).
      T2/T3 son MANUAL con su medición commiteada (`32ddd42`).
- [x] Sin temporales ni ficheros sin trackear (`git status` limpio).
- [x] `features.json`: F-013 `in_progress`, que es el estado real antes de
      este veredicto.

## 4 · Cobertura: requisito → test

Nº de tests `test_f013_rN_*` distintos (sin contar parametrizaciones) y uno de
ejemplo. Todos pasan.

| Req. | Tests | Ejemplo |
|---|---|---|
| R1 | 8 | `test_f013_r1_las_estrategias_son_dos_y_solo_dos` |
| R2 | 11 | `test_f013_r2_en_por_obra_no_se_construye_la_ubicacion_ni_se_lista` |
| R3 | 6 | `test_f013_r3_estrategia_desconocida_falla_antes_de_construir_el_adaptador` |
| R4 | 5 | `test_f013_r4_archiva_en_la_hoja_de_su_unidad_con_el_orden_entero` |
| R5 | 4 | `test_f013_r5_archivo_port_conserva_sus_tres_operaciones` |
| R6 | 10 | `test_f013_r6_usa_la_misma_conversion_del_codigo_que_el_cierre` |
| R7 | 10 | `test_f013_r7_cero_filas_es_reclamacion_no_localizada` |
| R8 | 2 | `test_f013_r8_otra_obra_en_sigrid_es_obra_no_coincide` (4 casos) |
| R9 | 2 | `test_f013_r9_la_ubicacion_solo_trae_lo_de_sigrid` |
| R10 | 6 | `test_f013_r10_numero_de_obra` |
| R11 | 8 | `test_f013_r11_clave_de_unidad` |
| R12 | 19 | `test_f013_r12_listar_la_raiz_pide_sus_hijos_con_nombre_y_faceta_de_carpeta` |
| R13 | 2 | `test_f013_r13_dos_carpetas_con_el_mismo_numero_se_devuelven_las_dos` |
| R14 | 5 | `test_f013_r14_incidencias_no_tiene_alternativa_y_dos_que_casan_son_ambigua` |
| R15 | 9 | `test_f013_r15_la_unidad_que_falta_se_crea_tras_la_traza_previa_y_en_orden` |
| R16 | 2 | `test_f013_r16_con_crear_apagado_falta_un_nivel_es_sin_carpeta` |
| R17 | 8 | `test_f013_r17_unir_ruta_con_base_vacia` |
| R18 | 5 | `test_f013_r18_los_motivos_son_exactamente_los_de_la_spec` |
| R19 | 7 | `test_f013_r19_destino_no_resuelto_responde_409_con_motivo_y_candidatas` |
| R20 | 1 | `test_f013_r20_tras_crear_la_carpeta_a_mano_el_reintento_archiva` |
| R21 | 5 | `test_f013_r21_el_homonimo_se_reemplaza_y_se_avisa` |
| R22 | 7 | `test_f013_r22_un_parte_no_aprobado_no_llega_a_sigrid_ni_a_la_biblioteca` |
| R23 | 16 | `test_f013_r23_nada_del_next_link_ni_de_la_biblioteca_en_los_logs` |
| R24 | 0 por nombre | Cubierto por `test_f013_r25_r45_archivado_en_it_no_lee_sigrid_ni_lista_ni_crea_ni_sube` (ni subida, ni creación, ni escritura de traza para un parte de IT) y `test_f013_r48_el_explorador_tiene_exactamente_dos_metodos` + `test_f013_r5_archivo_port_conserva_sus_tres_operaciones` (no hay operación de mover, copiar ni borrar). Ver **H-2** |
| R25 | 2 | `test_f013_r25_r45_archivado_en_it_no_lee_sigrid_ni_lista_ni_crea_ni_sube` |
| R26 | 2 | `test_f013_r26_integracion_dice_que_los_133_se_quedan_en_it` |
| R27 | 7 | `test_f013_r27_el_de_graph_solo_hace_get_mas_el_token` |
| R28 | 3 | `test_f013_r28_los_ficheros_se_cuentan_sin_nombrarlos` |
| R29 | 6 | `test_f013_r29_los_recuadros_citan_literal_la_premisa` |
| R30 | 8 | `test_f013_r30_ningun_fichero_del_repositorio_lleva_el_host_del_inquilino` |
| R31 | MANUAL (+3 tests del ensayo local) | `test_f013_r31_el_arbol_medido_resuelve_obra_e_incidencias` |
| R32 | MANUAL, hecha (T3) (+5 tests) | `test_f013_r32_el_de_sigrid_solo_lee_por_sql_read` |
| R33 | MANUAL, tras el corte | `tasks.md` paso 7; `docs/DESPLIEGUE.md` §9 |
| R34 | 1 | `test_f013_r34_se_anota_lo_que_falta_y_bajo_lo_nuevo_no_se_lista` |
| R35 | 16 | `test_f013_r35_0677_guion_mirasierra_impide_crear_la_obra` |
| R36 | 3 | `test_f013_r36_nombre_de_la_obra_que_se_crea` |
| R37 | 6 | `test_f013_r37_el_patron_es_el_medido` |
| R38 | 2 | `test_f013_r38_nombres_imposibles` |
| R39 | 6 | `test_f013_r39_si_ya_existe_es_un_exito_y_no_se_crea_otra` |
| R40 | 3 | `test_f013_r40_el_aviso_de_carpeta_creada_lleva_la_ruta_y_ningun_identificador` |
| R41 | 15 | `test_f013_r41_la_ubicacion_no_disponible_responde_503` |
| R42 | MANUAL, tras el corte | `tasks.md` paso 8; `docs/DESPLIEGUE.md` §9 |
| R43 | 3 (documental) | `test_f013_r43_integracion_lleva_el_procedimiento_para_deshacer_una_carpeta` |
| R44 | 29 | `test_f013_r44_la_0677_medida_es_una_sola_obra` |
| R45 | 8 | `test_f013_r25_r45_archivado_en_it_no_lee_sigrid_ni_lista_ni_crea_ni_sube` |
| R46 | 4 | `test_f013_r46_cada_villa_creada_casa_con_su_unidad` |
| R47 | 3 | `test_f013_r47_el_intento_pendiente_queda_en_el_log_antes_de_la_traza_error` |
| R48 | 5 | `test_f013_r48_el_explorador_tiene_exactamente_dos_metodos` |
| R49 | 7 | `test_f013_r49_tabla_4_2_la_hoja_y_su_alternativa` |
| R50 | 6 | `test_f013_r50_unidades_que_casan` |

Criterios `acceptance` de la ficha: (1) la ruta es configuración
(`SHAREPOINT_ESTRUCTURA` y compañía; R1, R2, tests de fábricas y del borde);
(2) lo de IT «queda localizable o migrado» — **enmendado** por el humano el
2026-09-18/22 a «se queda en IT, no se migra, no se borra» (R24–R26, recuadro
de §8 de la spec); (3) `init.sh` en verde.

## 5 · Punto 7 · las puertas que protegen un orden, movidas por mí

Método: clon desechable del repositorio en mi scratchpad (`git clone` local a
`4492ec6`, rama `dev` local creada **en el clon** para los controles de diff),
script con sustitución de un ancla **única** (`assert count == 1`),
restauración byte a byte en `finally`, y suite `tests/test_f013_*`,
`test_f033_*`, `test_f031_*`, `test_f019_*` y `test_f006_paso_archivo.py`. Base
restaurada al final: **1.360 passed, 8 skipped**. Para los que caían por un test
ajeno a F-013 o por uno poco obvio, repetí sin `-x` solo con `test_f013_*`
para ver que los caza **el test de F-013 que corresponde**.

| # | Qué se bajó (un paso por colaborador) | Resultado | Lo caza (test de F-013) |
|---|---|---|---|
| A | Puerta de estado por debajo del resolutor (la situación se lee sin juzgarla) | **muere** | `test_f013_r22_un_parte_no_aprobado_no_llega_a_sigrid_ni_a_la_biblioteca` |
| B | Cotejo de F-031 por debajo del resolutor | **muere** | `test_f013_r22_un_cuerpo_que_no_cuadra_no_llega_a_sigrid_ni_a_la_biblioteca` |
| C | L1 por debajo del resolutor | **muere** | `test_f013_r25_r45_archivado_en_it_no_lee_sigrid_ni_lista_ni_crea_ni_sube` |
| D | Resolutor por debajo de una escritura `pendiente` en el repositorio | **muere** (15 tests) | `test_f013_r18_sin_destino_queda_la_traza_error_con_el_codigo_y_no_se_sube`, `test_f013_r41_la_ubicacion_no_disponible_responde_503`… |
| E | Crear carpetas **antes** de la traza previa | **muere** | `test_f013_r15_la_unidad_que_falta_se_crea_tras_la_traza_previa_y_en_orden` |
| F | Crear carpetas **después** de subir | **muere** | ídem |
| G | Aviso del intento anterior antes de resolver (contra la carpeta de la traza) | **muere** | `test_f013_r22_el_aviso_del_intento_anterior_compara_con_la_carpeta_resuelta` |
| H | Log de R47 **después** de la traza `error` que lo pisa | **muere** | `test_f013_r47_el_intento_pendiente_queda_en_el_log_antes_de_la_traza_error` |
| I1 | R8 por debajo de la segunda lectura de Sigrid (R44) | **muere** | `test_f013_r8_otra_obra_en_sigrid_es_obra_no_coincide` (4 casos) |
| I2 | R8 por debajo del listado de la raíz | **muere** | ídem |
| K | R44 por debajo del listado de la raíz | **muere** (72 tests) | `test_f013_r44_sin_exactamente_una_obra_es_obra_numero_no_unico`, `test_f013_r22_el_orden_completo_de_una_resolucion`… |
| L | R50 por debajo del listado de dentro de la unidad | **muere** | `test_f013_r50_una_carpeta_existente_de_dos_unidades_es_compartida` |
| L0 | Sin R50 (control) | **muere** | `test_f013_r23_..._salen[compartida]` y los de R50 |
| N | `construir_ubicaciones` antes que el archivador en el borde | **muere** | `test_f013_t13_el_orden_de_construccion_en_posventa` |

**14 de 14 muertas.** Los dobles anotan cada llamada (ubicaciones, explorador,
archivador, repositorio) y los tests comparan el registro entero: el caso de
origen de la regla (F-034, un doble que no anotaba) **no** se repite aquí.

### Los equivalentes a mano del bloque 2 (P2, M19, M20): mi juicio

Siguen **sin aceptación del humano registrada**. No son supervivientes de la
campaña del arnés (esa tiene uno, aceptado), así que no bloquean el nivel
`critico`; pero el humano debería dejar su aceptación escrita, y esto es lo
que le recomiendo:

- **P2 · se sostiene, equivalente estricto.** Mover R44 por debajo de
  `_Camino(explorador, crear_carpetas, ruta=unir_ruta(base))` no cruza ningún
  colaborador: construir `_Camino` no llama a nadie y `unir_ruta` es pura y
  no levanta con una cadena. No es una puerta de orden del punto 7. Mi
  mutación K (R44 por debajo del **primer listado**) sí cruza al explorador, y
  muere.
- **M20 · se sostiene, equivalente estricto.** Tras R8,
  `normalizar_codigo(obra de Sigrid) == normalizar_codigo(obra del parte)`, y
  `nombre_de_obra_nueva` normaliza su argumento: el nombre sale idéntico
  byte a byte.
- **M19 · se sostiene en la práctica, pero no es estrictamente equivalente.**
  `destino_archivo.py:296` compone la carpeta final con
  `unir_ruta(base, obra, tramo_incidencias, unidad, hoja)`, mientras los
  padres de `carpetas_por_crear` salen de `camino.ruta` (`:144`, `:206–207`),
  construida uniendo tramo a tramo. Coinciden para todo nombre que Graph puede
  devolver (sin `/` ni blancos en los extremos) y para cualquier base
  razonable, pero **divergen** con una base patológica cuyo primer tramo,
  recortado, empiece por `/` (p. ej. `"/ /x"`: la carpeta final sería
  `/x/…` y los padres `x/…`). Recomiendo aceptarlo **o**, mejor, eliminar la
  duplicación (hallazgo **H-3**).

## 6 · Lo que he revisado del diseño y está bien

- El orden del paso es exactamente el que pide el líder: puerta → cotejo →
  nombre → L1 → resolver → aviso → traza previa → crear (un nivel por
  llamada) → buscar → subir → traza final (`paso_archivo.py:346–407`).
- El resolutor no escribe: devuelve `carpetas_por_crear` y el paso las crea
  solo tras la traza previa; ningún 409 deja una carpeta a medias (R38),
  probado con E/F de §5.
- R50 es sólido: con R44 garantizando una sola obra, la unidad de la
  reclamación está entre las filas leídas, y la carpeta elegida casa con ella
  por construcción (`carpetas_de_unidad` / R46), así que «casa con
  exactamente una» implica «casa con la suya».
- La traza `error` de un destino no resuelto lleva `carpeta=None`; la columna
  `postventa.archivos.carpeta` es anulable (`05_archivos.sql`), así que no se
  convierte en un 503.
- `DestinoNoResuelto` y `UbicacionNoDisponible` heredan de `Exception` y se
  traducen en `function_app.py` a 409 y 503 sin que un `except` anterior los
  intercepte; hay tests que pasan por `function_app.archivar`.
- El SQL es parametrizado y solo por `sql/read`. Hasta el corte lo desplegado
  sigue en `por_obra`/`Postventa` (`infra/00_vars_postventa.ps1`), y el
  runbook (`docs/DESPLIEGUE.md` §9, paso 6) ya prevé que el vacío de
  `SHAREPOINT_CARPETA_BASE` no llegue al App Setting (la base volvería al
  defecto `Postventa` y cada archivado daría 502 sin subir nada: falla
  cerrado).
- Las decisiones tomadas durante la implementación (T10 bis aprobada por el
  humano; excepción con nombre de `test_f006_repo_sin_identificadores.py`,
  que solo añade y que otro control obliga a solo crecer; fallar cerrado sin
  configuración de `sigrid-api` incluso con un parte ya archivado,
  documentado; `<regla_del_23>` en el test) están documentadas y ninguna
  relaja una garantía.

## 7 · Verificaciones MANUAL pendientes del humano (no las ejecuta ningún agente)

Todas son del corte, **después del merge**, y tienen el comando exacto en
`specs/F-013-archivo-posventa/tasks.md` («Después del merge») y en
`docs/DESPLIEGUE.md` §9:

- **R31** (paso 2): `24_ubicacion_sigrid.ps1 -CodigoObra 0677 … -SalidaCsv` y
  `23_destino_posventa.ps1 -UrlSitio … -CodigoObra 0677 -DesdeKeyVault
  -UnidadesCsv …`; tiene que salir exactamente lo de R31.
- **R33** (paso 7) y **R42** (paso 8), el mismo día del corte.

## 8 · Hallazgos

Ninguno bloquea. Numerados por gravedad.

1. **H-1 · baja · `progress/current.md`.** El bloque vivo de F-013 no lista
   las verificaciones `MANUAL (humano)` R31, R33 y R42 con su comando: están
   en `tasks.md` («Después del merge», pasos 2, 7 y 8) y en
   `docs/DESPLIEGUE.md` §9. **Acción (líder, al cerrar):** copiar esos tres
   pasos al bloque de F-013 de `current.md`, o enlazar la sección exacta.
   Es el mismo hallazgo que el H-1 de F-033.
2. **H-2 · baja · trazabilidad de R24.** Ningún test lleva `r24` en el
   nombre. El contenido está probado (§4, fila R24), pero no se encuentra
   buscando `test_f013_r24`. **Acción (implementer o líder, en un commit de
   tests):** renombrar
   `test_f013_r25_r45_archivado_en_it_no_lee_sigrid_ni_lista_ni_crea_ni_sube`
   (`services/postventa-api/tests/test_f013_archivar_http.py:939`) a
   `test_f013_r24_r25_r45_…` y citar R24 en su docstring. Además, la tabla de
   `design.md` §11 no asigna R24 a ningún fichero: es el origen del hueco.
3. **H-3 · baja · `application/pipelines/destino_archivo.py:296`.** La
   carpeta final se compone por un camino distinto que los padres de las
   creaciones (`camino.ruta`): hoy dan lo mismo, pero son dos fuentes para un
   mismo valor, y es lo que deja vivo a M19. **Propuesta:** construir
   `DestinoArchivo(carpeta=camino.ruta, …)` (una sola fuente), o que el
   humano acepte M19 como equivalente con la salvedad de §5. No cambia ningún
   comportamiento observable con configuración real.
4. **H-4 · observación · `infrastructure/sigrid/consultas_ubicacion.py`,
   `SQL_UNIDADES_DEL_NUMERO`.** La preselección del SQL
   (`LTRIM(RTRIM(o.cod)) LIKE '%677'`) es **más estrecha** que la noción de
   «mismo número» del dominio para un código de obra de Sigrid con un blanco
   **interior**: `numero_de_obra("06 77")` da 677 (`normalizar_codigo` quita
   todos los blancos), pero el `LIKE` no lo trae. Una segunda obra así sería
   invisible a R44. Medido que no ocurre con la 0677 (T3: una sola obra), y es
   improbable en `con.cod`; `design.md` §4.7 solo contempla el caso contrario
   («aunque el SQL dejara pasar de más»). **Propuesta:** dejarlo anotado como
   riesgo en `design.md` §10; si algún día aparece, enmienda con medición.

Observaciones sin acción en F-013: **O-1** (`current.md` acumula histórico,
deuda previa), **O-2** (RED por `ImportError` de recogida, compensado con
mutación), **O-3** (T18/T19 sin commit `F-013 Tn:` propio, justificado).

## 9 · Automejora del protocolo (propuesta, no aplicada)

- **Al punto 7 del reviewer**: añadir que las mutaciones de orden se lancen
  sin `-x` sobre los tests de la feature cuando el primer fallo lo da un test
  de otra feature, para confirmar que **la feature** ve el orden y no solo
  una suite vecina. Aquí la mutación A la cazó primero un test de F-006; sin
  repetirla no se habría sabido si F-013 tenía su propio test (lo tiene).
- **A `CHECKPOINTS.md` C4**: aclarar si los supervivientes **a mano**
  declarados equivalentes (fuera de la campaña del arnés) necesitan también
  la aceptación del humano en nivel `critico`. Hoy la regla solo nombra los
  de «esa campaña», y F-013 ha tenido que llevarlos aparte.
