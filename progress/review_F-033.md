<!-- progress/review_F-033.md -->
# F-033 · Review · L1 contra el duplicado en SharePoint, conectada desde el endpoint

- **Veredicto:** **APROBADO**
- **Fecha:** 2026-09-18
- **Rama:** `feature/F-033-l1-traza-archivo`, `29758f0`..`2c1047a` sobre `dev` `11dda9d`
- **Contra:** `specs/F-033-l1-traza-archivo/` (aprobada por el humano el 2026-09-18, D-1 a D-7 de `design.md` §10), `docs/CONVENTIONS.md`, `docs/ARCHITECTURE.md`, `CHECKPOINTS.md`
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED en los requisitos centrales, cobertura de las líneas cambiadas ≥ 80 %, campaña de mutación con **cero supervivientes** y las verificaciones MANUAL listadas con su comando exacto.

Ningún hallazgo bloquea. Hay cuatro de gravedad **baja** y tres observaciones (§6).

---

## 1 · Qué ejecuté yo mismo (no lo tomé del informe)

| Verificación | Resultado real |
|---|---|
| `bash harness/init.sh` | **ENTORNO LISTO**. Raíz 62 passed; servicios `api` y `front` en verde; `PUERTA COBERTURA: 100.0% de 65 líneas cambiadas cubiertas (65/65, umbral 80%, nivel critico)`; rama `feature/F-033-l1-traza-archivo`; ruff 61 avisos (deuda previa) |
| Suite completa del servicio en un worktree limpio (`--detach` en `2c1047a`, el `venv` del servicio, sin caché) | **2989 passed, 14 skipped**, 0 fallos (hay más *skipped* que en `init.sh` porque las mitades del control de alcance que dependen del diff se saltan fuera de la rama, que es lo que tienen que hacer) |
| Recálculo puro del alcance (`harness.alcance.alcance_de_feature`) y de los mutantes (`harness.mutacion.generar_mutantes`) | **7 ficheros, 474 líneas, 21 mutantes**: coincide con `progress/mutacion_F-033.md`. Los 21 recalculados coinciden uno a uno con los del informe (`paso_archivo.py` 14, `mapeo.py` 4, `repositorio_pg.py` 1, `sentencias.py` 2; y 0 en `estado.py`, `persistencia.py` y `archivar.py`, que solo cambian anotaciones, docstrings y un argumento con nombre) |
| **Campaña de mutación reejecutada entera**: el informe declaraba 253,0 s, por debajo de 5 min. `python -m harness.mutacion --feature F-033 --base dev --workers 8 --salida <scratchpad>` | **21 generados, 21 evaluados, 21 muertos, 0 supervivientes, 0 timeouts**, idéntico al informe. Tardó 876 s y hubo 6 timeouts que se repasaron en serie, todos muertos, porque compartía CPU con mis mutantes manuales. Salida fuera de `progress/`; `git status` limpio al terminar |
| Coste por mutante (informe del implementer) | 253,0 s × 8 ÷ 21 ≈ **96 s por mutante**, por encima de la suite (56 a 92 s). No es sospechoso |
| **Mutantes manuales** sobre las decisiones centrales, en el worktree aislado y con la suite entera (ver §4) | **10 de 10 muertos** |
| `git log --diff-filter=A dev..HEAD` buscando PDF o `muestras/` | vacío |
| `print(` o `TODO` añadidos en el diff | ninguno |
| Primera línea con la ruta relativa | presente en los 20 `.py` del diff |
| Árbol al terminar | limpio. Worktree temporal eliminado; `dev` sigue en `11dda9d` |

---

## 2 · Los puntos que el líder pidió mirar

### 2.1 D-impl-1 y D-impl-2: ¿cambian la forma o aflojan el test? **Cambian la forma. Aceptadas.**

- `test_f028_estado_dominio.py::test_f028_r2_…` y `test_f030_veredicto_persistido.py::test_f030_r2_…` fijan el **conjunto exacto** de campos de `SituacionParte`. El diff solo añade `"archivo"` a la colección esperada. La comparación **sigue siendo de igualdad exacta**: un sexto campo los volvería a poner en rojo, y en el de F-030 también un cambio de orden. El docstring del propio test de F-028 ya decía qué hacer (*«Un quinto campo lo pone en rojo igual que antes lo ponía el cuarto, y la enmienda del campo nuevo está escrita y fechada en la docstring de `SituacionParte`»*), y es lo que se ha hecho. R1, aprobado por el humano, exige ese campo, así que no había otra forma de implementarlo. Ninguna expectativa de comportamiento cambia. El único error es de `design.md` §7, que no los listaba.
- D-impl-2 (`test_f005_logs_sin_datos_personales.py::test_f030_r21_…`): se añaden ocho `None` a una fila literal. Los asertos sobre el log no cambian. Es el mismo cambio de forma que §7 ya autoriza para `_fila_de_lo_guardado`.
- D-impl-3: el ayudante `_fila_de_la_consulta` de F-030 alimenta a `fila_a_validacion_y_cierre`, que sigue siendo de diez columnas por diseño (§3.3). Dejarlo sin tocar es lo correcto; el error vuelve a ser de §7.

### 2.2 El `upsert` de `postventa.archivos` no pisa `archivado`, y no hay DDL. **Correcto.**

- `sentencias.upsert_archivo` lleva `WHERE {tabla}.estado <> %s`, y `_ESTADO_ARCHIVO_TERMINAL = "archivado"` va como **último parámetro**, no escrito en el SQL. Es el mismo patrón que `upsert_cierre` y `upsert_grafico` (`sentencias.py:304`, `:370`), que ya funcionan en producción. El `SET` usa `EXCLUDED.*`, así que ese parámetro es el único que se añade y el orden de los parámetros encaja.
- `repositorio_pg._escribir` ya traducía «ninguna fila de vuelta» a `SIN_CAMBIOS` (`:518`). Lo fija `test_f033_r17_sin_fila_de_vuelta_el_repositorio_responde_sin_cambios`.
- `RepositorioComoLaBase.guardar_archivo` copia esa semántica (`archivado` → `SIN_CAMBIOS`; `pendiente`/`error` → `ACTUALIZADO`). El circuito de doble archivado comprueba que la fila es **el mismo objeto** tras la segunda petición (`base.archivos[HASH] is traza_primera`).
- **Sin DDL**: el diff no toca `infrastructure/persistencia/sql/`. Lo vigilan `test_f033_la_rama_no_toca_el_ddl` y `test_f033_no_hay_ni_un_fichero_de_ddl_nuevo`. El `CHECK (estado IN (...))` de `05_archivos.sql:14` hace inalcanzable en la base el `ValueError` de R5; aun así está probado.
- Mutante manual M1 (quitar la línea `WHERE`): **muerto** por dos tests de R17. M9 (estado terminal `"pendiente"`): **muerto**.

### 2.3 La situación sigue costando dos sentencias. **Correcto.**

- `consultar_situacion` sigue con **dos** `_leer`. La traza de archivo entra como tercer `LEFT JOIN` anclado en `partes` dentro de `select_veredicto_y_cierre`, con las ocho columnas **al final**, sacadas de `_COLUMNAS_ARCHIVO[1:]`, la misma lista que escribe el `upsert`.
- `test_f033_r3_la_situacion_sigue_costando_dos_sentencias[con_traza|sin_traza]` cuenta `len(conexion.ejecutadas) == 2`. Los asertos de dos sentencias de F-028 (`:458`, `:1453`) **no se han tocado**.
- R8: el camino que corta por L1 hace **una** consulta de situación y ninguna escritura (`test_f033_r8_…`). En el circuito se ve `situaciones_consultadas == [HASH, HASH]`, una por petición.
- La única lectura adicional es la relectura de R18, solo en la carrera. Estaba declarada en `design.md` §8.3 y aprobada con D-7.

### 2.4 L1 corta de verdad desde `/api/archivar`, y `adjuntar.py`/`cerrar.py` no se tocan. **Correcto.**

- `archivar.py` añade **una línea de código**, `drive_id_vigente=ajustes.sharepoint_drive_id`. La traza la lee el paso de `situacion_leida(ctx, repositorio).archivo`, la situación que ya dejó la puerta. `traza_previa` ha desaparecido de la firma (R7), y ya no queda en código de producción ni un llamante que la pase.
- Hay un test de borde a borde: `test_f033_archivar_http.py` recorre `function_app.archivar` con el multipart real. `test_f033_circuito_archivar_dos_veces_sube_una`, sobre `RepositorioComoLaBase` (columnas pasadas por el mapeo de producción), da **una sola subida**, la segunda con `[AVISO_YA_ARCHIVADO]` exacto y la traza intacta. En la fase RED ese mismo test caía con `assert 2 == 1` (dos subidas), que es la prueba de que el defecto D-A1 existía. Los casos F-032 (nombre viejo) y F-013 (otra biblioteca) también pasan por el endpoint, sin ninguna subida.
- Mutante manual M2 (L1 inerte, `guardada = None`): **muerto**. M5 (`archivar.py` pasa `drive_id_vigente=None`): **muerto** por el caso F-013 del endpoint.
- `adjuntar.py`, `cerrar.py`, `paso_grafico.py`, `paso_cierre.py`, `nombrado.py`, `puerta_de_estado.py`, `infrastructure/sharepoint/**` y el front **no aparecen en el diff** (`git diff --stat dev...HEAD`, 29 ficheros). Lo vigila además `test_f033_la_rama_no_toca_d6_ni_el_nombrado`. Esos endpoints reciben ahora la traza dentro de la situación sin usarla; que la lean es F-034, fuera de alcance.

---

## 3 · Las siete desviaciones, una a una

| Id | Juicio | Motivo |
|---|---|---|
| **D-impl-1** | **Aceptada** | Ver §2.1. Cambio de forma, igualdad exacta conservada, procedimiento prescrito por el propio test |
| **D-impl-2** | **Aceptada** | Ver §2.1. Ocho `None` en una fila literal; asertos intactos |
| **D-impl-3** | **Aceptada** | El ayudante alimenta a la función que por diseño sigue siendo de diez columnas. El error estaba en §7 del diseño, no en la implementación |
| **D-impl-4** | **Aceptada** | Se corrige el **montaje** del caso (biblioteca vigente = `DRIVE_FALSO`, la que deja el doble al subir) y no la expectativa: siguen `subidas == 1`, `avisos == [AVISO_YA_ARCHIVADO]` exacto y la traza `is` intacta. La evidencia RED no cambia (el aserto que cayó, `:318`, va antes). Además, `test_f033_circuito_f013_…` demuestra que con otra biblioteca el aviso **sí** sale, así que el ajuste no esconde nada |
| **D-impl-5** | **Aceptada con hallazgo H-2 (baja)** | Un `pendiente` sin ruta avisa con `«None/None»`. En producción no pasa: `_dejar_constancia_previa` escribe siempre carpeta y nombre. Es cosmético |
| **D-impl-6** | **Aceptada con hallazgo H-3 (baja)** | `design.md` §4.5 pedía `PersistenciaNoDisponible`, y el borde la traduce a un 503 con texto genérico («no se ha podido hablar con la base de datos…»). En este caso ese texto no es exacto, pero el motivo propio sí lo es y **no se sube nada**. Solo se llega aquí con un borrado manual por medio. Tocar `function_app.py` habría salido del alcance |
| **D-impl-7** | **Aceptada** | `tasks.md` T10 permite fichero propio. El control tiene sus dos mitades y las tres guardas de F-032. No congelar el contenido de los cinco ficheros que F-034 y F-031 van a cambiar es la decisión correcta. La prueba de que no es un verde vacío (dos rojos con temporales sin versionar) está pegada en el informe |
| (8) Comandos de `tasks.md` | **Aceptada; hallazgo H-4 (baja, de la spec)** | Los comandos literales usan el Python global, que no tiene `pydantic`. Se ejecutaron con el `venv` del servicio, igual que `init.sh`. El defecto es de redacción de la spec |

---

## 4 · Mutación: verificación independiente y mutantes manuales

**Campaña de la herramienta.** Totales recalculados y campaña reejecutada: idénticos (§1). **Cero supervivientes**, así que no hay ningún análisis `PENDIENTE`.

**Por qué añadí mutantes a mano.** El generador del arnés no tiene operador para `is`/`is not`, ni para `if llamada():` sin `not`, ni para borrar sentencias. Por eso sus 21 mutantes **no tocan** varias de las decisiones centrales de esta feature: la condición de L1, el `SIN_CAMBIOS` de la traza previa, el `WHERE` del `upsert` y el argumento del endpoint. Siendo rigor `critico`, las rompí a mano en un worktree `--detach` aislado y pasé la suite entera cada vez:

| # | Mutación | Resultado | Test que la caza |
|---|---|---|---|
| M1 | Quitar `WHERE {tabla}.estado <> %s` de `upsert_archivo` | **muerto** | `test_f033_r17_el_upsert_no_actualiza_una_fila_archivada` (+1) |
| M2 | L1 inerte: `guardada = None` | **muerto** | `test_f006_r14_con_traza_archivada_no_se_vuelve_a_subir` (y los de F-033) |
| M3 | Ignorar el `SIN_CAMBIOS` de la traza previa (`if False:`) | **muerto** | `test_f033_r18_sin_cambios_en_la_previa_relee_y_no_sube` |
| M4 | R19 sin línea de log | **muerto** | `test_f033_r19_sin_cambios_en_la_final_se_registra_y_responde` |
| M5 | `archivar.py` pasa `drive_id_vigente=None` | **muerto** | `test_f033_circuito_f013_otra_biblioteca_no_se_sube_y_no_se_dice_cual` |
| M6 | La relectura de R18 usa `situacion_leida` (la de antes de la carrera) | **muerto** | `test_f033_r18_sin_cambios_en_la_previa_relee_y_no_sube` |
| M7 | El log de la situación sin el estado del archivo | **muerto** | `test_f033_r6_el_log_trae_el_estado_de_la_traza` |
| M8 | Quitar la llamada a `_avisar_del_intento_anterior` | **muerto** | `test_f033_r20_pendiente_en_otra_ruta_sigue_con_aviso_y_log[otra_carpeta]` |
| M9 | Estado terminal `"pendiente"` en lugar de `"archivado"` | **muerto** | `test_f033_r17_el_estado_terminal_va_como_parametro` |
| M10 | El adaptador no pasa `archivo=` a `SituacionParte` | **muerto** | `test_f033_r2_el_adaptador_devuelve_la_traza_con_sus_ocho_campos` |

---

## 5 · Recorrido de `CHECKPOINTS.md`

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` termina en verde (ejecutado por el reviewer).
- [x] Existen los ficheros obligatorios (lo confirma `init.sh`).

### C2 — El estado es coherente
- [x] Una sola feature `in_progress`: `['F-033']`.
- [x] Rama actual `feature/F-033-l1-traza-archivo`.
- [x] `progress/current.md` empieza por la sesión activa (F-033, bloques 1 a 3 y spec aprobada). **Observación O-1**: por debajo sigue el histórico acumulado desde agosto, heredado de `dev`. F-033 no lo introduce: se limita a añadir sus bloques arriba, como hace todo el repositorio. Ya lo señaló el review de F-032 §11.1.
- [x] Ninguna feature pasa a `done` en esta rama; F-033 todavía no necesita resumen en `history.md`.

### C3 — Arquitectura y convenciones
- [x] Hexagonal: el dominio (`estado.py`) importa solo dominio (`TrazaArchivo` de `domain.models.persistencia`). El SQL vive en `infrastructure/persistencia/sentencias.py`, el mapeo en `mapeo.py`, y el paso habla con puertos. `_en_otro_destino` vive en el paso y no en el dominio, como pide §4.3. El borde solo pasa configuración.
- [x] Primera línea con la ruta en los 20 `.py` del diff.
- [x] Sin `print()`, sin TODOs, sin dependencias nuevas. Sin secretos: los identificadores de biblioteca de los tests son inventados y reconocibles (`drive-inventado-it`, `DRIVE_FALSO`). Ningún valor interpolado en el SQL: el esquema pasa por `_tabla` y el estado terminal va como parámetro.
- [x] La unidad sigue siendo el **parte**: L1 corta por `hash_parte` + estado.
- [x] Nada se archiva sin validaciones: la puerta de estado sigue siendo lo primero, y L1 va después del nombrado y antes de la traza previa (R9, probado). Sin escrituras en Sigrid.
- [x] Lo manuscrito no se descarta: la feature no lo toca.
- [x] Firmado no es conforme: la feature no lo toca.
- [x] **Reprocesar no duplica**: es justo lo que arregla esta feature, demostrado de borde a borde.
- [x] Ningún número de estado de Sigrid: la feature no lo toca.
- [x] Ningún PDF ni parte escaneado entra en git (`git log --diff-filter=A dev..HEAD` → vacío).

### C3 bis — Documentos que entran de fuera
**N/A justificado**: la rama no añade ni modifica ningún fichero de `docs/referencia/`.

### C4 — La verificación es real
- [x] Trazabilidad: la tabla del §7 cubre los 27 requisitos. R22 lo cubren las suites existentes, sin tocar ningún aserto (§2.1). R25 es documental y lo verifiqué leyendo el diff (+17 −0). R26 y R27 son MANUAL.
- [x] Sin red ni BBDD: dobles en memoria (`ConexionFalsa`, `RepositorioFalso`, `RepositorioComoLaBase`, `ArchivoPortFalso`) y la guardia de red de la suite.
- [x] MANUAL listadas: `progress/current.md` nombra T13 (antes de desplegar) y T14 (después de desplegar) como pendientes del humano, y el comando exacto está en `tasks.md` T13/T14 y en `progress/impl_F-033.md` («Verificaciones MANUAL pendientes»), con el SQL completo de solo lectura. Ver el hallazgo **H-1**: el SQL no está copiado en `current.md` mismo.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: "critico"` declarado y válido.
- [x] **Fase RED** con la salida real pegada: T1 (35 de 39 en rojo) y T5 (40 de 54 en rojo, incluido `assert 2 == 1` del doble archivado desde el endpoint).
- [x] **Cobertura** `[OK]`: 100 % de 65 líneas cambiadas.
- [x] **Mutación**: `progress/mutacion_F-033.md` generado por la herramienta. Totales verificados de forma independiente (recálculo puro, idéntico).
- [x] **Los muertos están comprobados**: el informe declaraba menos de 5 min, así que **reejecuté la campaña entera**: totales idénticos, salida fuera de `progress/`, árbol limpio.
- [x] **Tiempo coherente**: unos 96 s por mutante con 8 workers, por encima de lo que tarda la suite.
- [x] Cero supervivientes; ninguna sección `PENDIENTE`.
- [x] La sección «Evidencias» trae los números: tests, cobertura, mutantes/supervivientes, tiempo de la suite y **workers (8)**.
- [x] Ningún punto de este bloque está marcado N/A.

### C4 ter — Rutas sensibles
**N/A justificado**: no existe `harness/rutas_sensibles.json` y `init.sh` no señaló ninguna ruta.

### C5 — La sesión se cerró bien
- [x] `tasks.md`: T1 a T12 en `[x]`, cada una con su commit `F-033 Tn: …`. T13 y T14 están en `[ ]` por diseño: son del humano y quedan fuera de la rama.
- [x] Sin ficheros temporales ni artefactos sin trackear (`git status` limpio).
- [x] `features.json`: F-033 en `in_progress`, que es lo que corresponde hasta que el líder la cierre. F-034 dada de alta y `blocked_by` F-033.

---

## 6 · Hallazgos (ninguno bloquea)

1. **H-1 · baja · `progress/current.md`.** El bloque de F-033 menciona T13 y T14 y remite a «los comandos listos para copiar en el informe», pero **no lleva el SQL**. En F-032 sí estaba copiado en `current.md`. **Acción (líder, al cerrar):** copiar al bloque vivo de `current.md` los dos `SELECT` de T13 y el de T14 desde `progress/impl_F-033.md` («Verificaciones MANUAL pendientes»), o enlazar la sección exacta. No toca código.
2. **H-2 · baja · `paso_archivo.py`, `_avisar_del_intento_anterior` (≈ l. 290-310).** Un `pendiente` con `carpeta`/`nombre_fichero` a `None` genera un aviso con el texto `«None/None»` (D-impl-5). En producción no ocurre. Si se quiere, basta una condición más (no avisar si los dos son `None`). Puede hacerse en F-034 o en una limpieza.
3. **H-3 · baja · 503 de la relectura sin `archivado` (R18, `paso_archivo.py` `_tomar_la_de_la_otra_peticion`).** El texto que ve el usuario es el genérico del borde, que en este caso no es exacto (la base sí respondió). El motivo interno es preciso y no se sube nada. Si algún día hace falta, lo correcto sería una excepción de dominio propia con su código. Hoy no merece ficha: solo se llega con un borrado manual por medio.
4. **H-4 · baja · `specs/F-033-l1-traza-archivo/tasks.md`.** Los comandos de verificación (`python -m pytest services/postventa-api/tests/...` desde la raíz) no funcionan con el Python global porque le falta `pydantic`. **Acción (spec-author, en adelante):** redactar los comandos con el `venv` del servicio, como hace `harness/servicios.json`.

### Observaciones

- **O-1** · `current.md` acumula el histórico (ver C2). Es deuda previa y la decide el humano.
- **O-2 · para F-013, y conviene que el humano lo sepa antes de desplegar.** Con D-1 (cortar siempre por `hash` + estado), una traza `archivado` en la biblioteca de IT **impide para siempre** subir ese parte a Posventa. El humano dijo el 2026-09-18 que *«lo que está en IT eran pruebas, se puede olvidar»*. F-033 hace lo que la spec aprobada manda, pero F-013 tendrá que decidir qué hace con esas trazas (y T13 dirá cuántas son: su primera consulta cuenta las `con_biblioteca`). El implementer ya lo anotó como pendiente para F-013.
- **O-3 · fragilidad prevista.** `test_f033_no_hay_ni_un_fichero_de_ddl_nuevo` fija a mano los once `.sql` de F-028. La próxima feature que añada DDL legítimo tendrá que ampliar esa lista. Es a propósito (la mitad sin `git` del control), pero conviene saberlo.

---

## 7 · Cobertura: requisito → test

| Req | Test(s) |
|---|---|
| R1 | `test_f033_r1_la_situacion_trae_archivo_a_none_por_omision`, `…_archivo_es_el_ultimo_de_cinco_campos`, `…_la_situacion_guarda_la_traza_que_se_le_da` |
| R2 | `test_f033_r2_*` (11 casos: sentencia, `LEFT JOIN` anclado, orden de columnas, lista única, adaptador con los ocho campos, cada `EstadoArchivo`, sin fila → `None`, convivencia con veredicto y cierre, doble como la base); `test_f033_circuito_la_traza_vuelve_por_columnas_y_corta` |
| R3 | `test_f033_r3_la_situacion_sigue_costando_dos_sentencias[con/sin]`, `…_el_corte_del_mapeo_coincide_con_la_sentencia`, `…_una_fila_de_otro_largo_revienta[17,19,10]` |
| R4 | `test_f033_r4_sin_ficha_los_tres_huecos_a_none_y_sin_error`, `test_f033_r4_el_doble_como_la_base_sin_ficha_no_trae_traza` |
| R5 | `test_f033_r5_un_estado_de_archivo_desconocido_revienta_en_el_mapeo`, `…_en_el_adaptador` |
| R6 | `test_f033_r6_el_log_trae_el_estado_de_la_traza`, `…_dice_que_no_hay_traza`, `…_no_trae_identificadores_de_biblioteca` |
| R7 | `test_f033_r7_el_paso_ya_no_acepta_la_traza_por_parametro`, `…_pasarle_una_traza_es_un_error_de_tipo`, `…_drive_id_vigente_es_opcional_y_por_palabra_clave`, `…_la_traza_archivada_de_la_situacion_corta` |
| R8 | `test_f033_r8_el_corte_cuesta_una_consulta_y_ninguna_escritura`, `…_el_camino_normal_tampoco_pregunta_de_mas`; circuito `situaciones_consultadas == [HASH, HASH]` |
| R9 | `test_f033_r9_*` (4: L1 antes de la previa, orden F-019 sin corte, puerta antes de L1, nombrado antes de L1) |
| R10 | `test_f033_r10_devuelve_la_traza_guardada_tal_cual`, `…_una_traza_archivada_de_otro_parte_no_corta`; `test_f033_circuito_archivar_dos_veces_sube_una` |
| R11 | `test_f033_r11_pendiente_y_error_no_cortan[pendiente,error]` |
| R12 | `test_f033_r12_un_parte_archivado_responde_200_con_la_traza_guardada` (vía `function_app.archivar`) |
| R13–R14 | `test_f033_r13_r14_corta_siempre_y_avisa_si_es_otro_destino` (tabla de §4.3), `test_f033_r14_el_aviso_dice_que_sigue_alli_y_que_no_se_subio`; circuitos F-032 y F-013 |
| R15 | `test_f033_r15_el_drive_id_no_sale_en_ningun_log_ni_aviso`, `…_sin_biblioteca_configurada_…`, `…_con_la_misma_biblioteca_…`; circuito F-013 |
| R16 | `test_f033_r16_lo_archivado_en_otro_destino_se_queda_donde_esta`, `…_el_paso_solo_usa_las_tres_operaciones_del_puerto` |
| R17 | `test_f033_r17_*` (7: `WHERE`, parámetro, lista única, `SIN_CAMBIOS`, log, doble como la base con y sin pisar) |
| R18 | `test_f033_r18_*` (4: relee y no sube, responde como L1 en otro destino, relectura sin `archivado` → error sin subir, sin carrera no hay relectura) |
| R19 | `test_f033_r19_*` (3: final `SIN_CAMBIOS`, error `SIN_CAMBIOS`, resultado normal sin línea) |
| R20 | `test_f033_r20_*` (6: aviso y log, antes de la previa, misma ruta no avisa, `error` no avisa, otro parte no avisa, sin identificadores) |
| R21 | `test_f033_r21_la_firma_no_ofrece_ninguna_forma_de_forzar`, `…_un_escaneo_nuevo_es_otro_parte_y_se_archiva`, `test_f033_r21_un_campo_forzar_en_el_cuerpo_no_abre_nada`; `test_f033_r23_el_cuerpo_de_archivar_pide_lo_mismo_de_siempre` |
| R22 | Suites existentes de F-006, F-019, F-028 y F-030 en verde sin tocar ningún aserto (§2.1); los atajos de F-006/F-019 solo **siembran** la traza en la situación (+7 −0 cada uno) |
| R23 | `test_f033_r23_el_contrato_es_el_mismo_con_corte_y_sin_el`, `…_la_rama_no_toca_ni_un_fichero_del_front`, `…_el_cuerpo_de_archivar_pide_lo_mismo_de_siempre` |
| R24 | Centinelas en `test_f033_circuito_f013_…` (cuerpo y `caplog`), `test_f033_r15_el_drive_id_no_sale_…`, `test_f033_r20_el_aviso_no_lleva_identificadores_de_biblioteca`, `test_f033_r6_el_log_no_trae_identificadores_de_biblioteca` |
| R25 | Documental. Verificado por el reviewer: `docs/ARCHITECTURE.md` +17 −0, «**Precisado por F-033 el 2026-09-18**», con los tres puntos que pide R25 |
| R26 | **MANUAL (humano)** · T13, antes de desplegar. Pendiente |
| R27 | **MANUAL (humano)** · T14, después de desplegar. Pendiente |

---

## 8 · Automejora propuesta (no aplicada; la decide el humano)

**Mutantes manuales sobre las decisiones centrales en nivel `critico`.** El generador de `harness.mutacion` no muta `is`/`is not`, las condiciones `if f():` sin `not` ni el borrado de sentencias. En esta feature eso dejó **fuera de la campaña** la condición de L1, el `SIN_CAMBIOS` de la traza previa y el `WHERE` del `upsert`, que son justo lo que se entrega. Aquí las cubrían los tests (§4), pero una campaña con «0 supervivientes» podía dar falsa seguridad. Hay dos propuestas, y ambas valen para cualquier proyecto, así que irían también a `arnes-base`:

1. En `.claude/agents/reviewer.md`, apartado de mutación: *«En nivel `critico`, identifica en `design.md` las decisiones centrales de la feature, comprueba si alguno de los mutantes generados las toca y, si no, rómpelas a mano en un worktree `--detach` aislado y pasa la suite entera. Anota la tabla en el informe.»*
2. En `harness/mutacion.py`: añadir los operadores `is`↔`is not` y `if cond:`→`if not cond:`.

---

## 9 · Qué falta para cerrar (para el líder)

- Aplicar **H-1** (copiar el SQL de T13/T14 a `current.md`) al pasar F-033 a `done`, con su resumen en `history.md`.
- **T13 (humano), antes de desplegar**: la lectura de `postventa.archivos` por estado. Además de lo que dice la spec, sirve para dimensionar **O-2** (cuántas trazas `archivado` apuntan a IT).
- **T14 (humano), después de desplegar**: re-archivar un parte ya archivado, con autorización y la ventana abierta.
- Merge a `dev` solo con petición del humano.
