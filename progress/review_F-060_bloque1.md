<!-- progress/review_F-060_bloque1.md -->
# F-060 · Review del Bloque 1 (la regla y el plan, dominio puro)

- **Veredicto:** **CHANGES_REQUESTED**. Hay dos hallazgos bloqueantes (C-1 y C-2), dos mutantes a mano de la regla
  que sobreviven y se arreglan con unos pocos casos de test, y uno que necesita decisión del humano (C-3). El código
  de producción **no** hay que cambiarlo: la regla, el plan y la foto del sistema son correctos en todo lo probado.
- **Fecha:** 2026-10-09 · reviewer
- **Rama:** `feature/F-060-normalizar-ubicaciones`, HEAD `af72c5b`, base fija `33d8938`
- **Alcance revisado:** T1–T3. Ficheros: `services/postventa-api/domain/models/normalizacion.py` (nuevo) y
  `services/postventa-api/tests/test_f060_normalizacion_dominio.py` (nuevo). Informes: `progress/impl_F-060.md`
  (Bloque 1) y `progress/mutacion_F-060.md`. Contraste con `requirements.md` (R1–R11 y la parte de dominio de
  R21–R23), `design.md` §3, §4.2–§4.4, §6 y §15 (D-3, D-4, D-6, Q-1, Q-2, Q-4), `docs/CONVENTIONS.md`,
  `docs/ARCHITECTURE.md` y `CHECKPOINTS.md`.

## Nivel de rigor

`critico`, declarado en `harness/features.json` (`"rigor": "critico"`). Exige fase RED con la traza pegada,
cobertura de lo cambiado, mutación con **cero supervivientes** salvo justificación escrita aceptada por el humano
(también para los mutantes a mano, `CHECKPOINTS.md` C4 bis) y las `MANUAL (humano)` con su comando. En este bloque
no hay ninguna `MANUAL`: es dominio puro.

## Lo que se ha ejecutado (resultados reales)

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` | **ENTORNO LISTO**. Suite del servicio api ejecutada de verdad (no por caché): **7767 passed, 31 skipped en 2027.64 s** (33 min 47 s). `PUERTA COBERTURA: [OK] 100.0 % de 76 líneas cambiadas (76/76, umbral 80 %, nivel critico)`. `RUTAS SENSIBLES: [OK]`, ninguna tocada. ruff: 73 avisos de deuda previa, que no bloquean |
| Sin caché (`-p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`), desde `services/postventa-api`: `test_f060_normalizacion_dominio.py`, `test_f056_revision_dominio.py`, `test_f005_arquitectura.py`, `test_f036_arquitectura.py`, `test_f006_repo_sin_identificadores.py` | **452 passed in 27.15s** |
| RED reproducido: el test y el esqueleto **del commit `2c92a10`** en una copia del scratchpad | **58 failed, 22 passed**, igual que el informe. 112 líneas `AssertionError`/`DID NOT RAISE` y **0** `ImportError`/`TypeError`/`AttributeError`/`ValueError`. El test no ha cambiado de `2c92a10` a HEAD (`git diff` vacío): el RED es del mismo test que hoy pasa |
| `ruff check` de los dos ficheros desde la raíz | `All checks passed!`. Desde `services/postventa-api` sale un `I001` (orden de imports) que sale igual en `test_f056_revision_dominio.py`: depende de dónde se lance, no es un hallazgo |
| Recálculo puro del alcance (`harness.alcance.alcance_de_feature('F-060', base='33d8938')`) | 1 fichero, **211 líneas** (`normalizacion.py`): coincide con el informe |
| Recálculo de los mutantes (`harness.mutacion.generar_mutantes` sobre ese alcance) | **19**: booleano 3 (`frozen`), comparación 2, `not` 1, entero 7, aritmético 6. Coinciden en número, líneas y texto con lo que describe el informe. No hay supervivientes que muestrear |
| Campaña completa | **No reejecutada**: 2768.9 s (46 min) según el informe, más de 5 min, así que vale el recálculo puro (y así lo pedía el encargo). Coste por mutante = 2768.9 × 8 / 19 ≈ **1166 s**, coherente con una suite de unos 35 min parada en el primer fallo: no es sospechosa |
| Mutantes **a mano** en una copia del scratchpad (54, ver abajo) | **51 muertos, 3 vivos** (M11, X01 y X07) |
| `git diff 33d8938..HEAD` de `domain/models/revision.py`, `tests/test_f056*`, `tests/test_f036*` y `*.sql` | **Vacío**: F-056 no se toca y sus tests no se relajan |
| `git status` tras todo | Limpio: los mutantes se aplicaron en una copia del scratchpad, nunca en el árbol de trabajo |

## Hallazgos bloqueantes (CHANGES_REQUESTED)

### C-1 · La suite no distingue NFC de NFKC (M11 sobrevive)

Mutante: en `normalizacion.py:107`, `unicodedata.normalize("NFC", texto)` → `unicodedata.normalize("NFKC", texto)`.
Con él, **los 80 tests pasan**.

No es un mutante equivalente: es justo lo que D-3 y Q-4 descartan («NFC: no es quitar tildes, es la misma letra
escrita de dos formas»). NFKC pliega los caracteres de compatibilidad, y en castellano eso mueve letras y blancos.
Comprobado contra el código real:

| Texto | Lista | Hoy (NFC) | Con NFKC | Por qué está mal con NFKC |
|---|---|---|---|---|
| `"DORMITORIO 1O"` | `("Dormitorio 1º",)` | `sin_coincidencia` | `normalizable` → «Dormitorio 1º» | «º» pasa a «o»: es **otra letra** (R4) |
| `"PLANTA 1A"` | `("Planta 1ª",)` | `sin_coincidencia` | `normalizable` | igual con «ª» |
| `"SALA EJEMPLO"` (espacio duro en medio) | `("Sala Ejemplo",)` | `sin_coincidencia` | `normalizable` | **un blanco interior distinto** (R4) |
| `"ＳＡＬＡ EJEMPLO"` (ancho completo) | `("Sala Ejemplo",)` | `sin_coincidencia` | `normalizable` | no es la misma palabra con otra caja |

«1º» y «1ª» son habituales en ubicaciones de vivienda. Es el primer riesgo de `design.md` §0 («se cambia una
ubicación por **otra** de Sigrid»), y R1 fija la forma NFC: tiene que quedar clavada por un test.

**Cambio requerido** (`tests/test_f060_normalizacion_dominio.py`, solo tests): añadir casos que caigan con NFKC.
Por ejemplo, en `test_f060_r4_lo_que_no_es_la_misma_palabra_no_coincide` (línea 341 y siguientes), contra
`("Sala Ejemplo",)`, el texto `"SALA EJEMPLO"`. Y un test nuevo `test_f060_r4_la_forma_de_compatibilidad_no_coincide`
con `ubicacion_de_sigrid("SALA EJEMPLO 1O", ("Sala Ejemplo 1º",))` y
`ubicacion_de_sigrid("SALA EJEMPLO 1A", ("Sala Ejemplo 1ª",))`, que deben dar `sin_coincidencia`, y en R1
`clave_de_ubicacion("Sala Ejemplo 1º") != clave_de_ubicacion("SALA EJEMPLO 1O")`. Con los datos ficticios de
siempre. Verificación: reaplicar M11 en una copia y ver el test en rojo, con la traza pegada en
`progress/impl_F-060.md`.

### C-2 · El paso 2 de R2 solo está probado con espacios (X07 sobrevive)

Mutante: en `normalizacion.py:122`, `recortado = texto.strip()` → `recortado = texto.strip(' ')`. Con él, **los
80 tests pasan**.

El paso 2 de R2 (normalizable hacia el valor igual al texto **recortado por los extremos**) solo se distingue del
paso 3 cuando el paso 3 sería `ambigua`. El único test que lo separa
(`test_f060_r2_el_exacto_tras_recortar_gana_a_la_ambiguedad`, líneas 290–296) usa **espacios** en los extremos.
Con un tabulador, un salto de línea o un espacio duro en un extremo y una lista con dos variantes, el mutante cae
al paso 3 y da `ambigua` en vez de `normalizable`. Es una regresión real, y la suite no la ve. Además, F-056
compara con `strip()` (R47), así que con el mutante las dos reglas dejarían de recortar igual.

**Cambio requerido** (`tests/test_f060_normalizacion_dominio.py:290-296`): añadir al menos
`ubicacion_de_sigrid("\tPatio Ficticio\n", L_AMBIGUA) == UbicacionDeSigrid(C.NORMALIZABLE, "Patio Ficticio")` y
`ubicacion_de_sigrid("patio ficticio ", L_AMBIGUA) == UbicacionDeSigrid(C.NORMALIZABLE, "patio ficticio")`.
Verificación: reaplicar X07 en una copia, ver el rojo y pegar la traza.

### C-3 · X01 sobrevive y no es equivalente del todo: lo decide el humano

Mutante: en `normalizacion.py:107`, `unicodedata.normalize("NFC", texto).strip().casefold()` →
`unicodedata.normalize("NFC", texto.strip().casefold())` (NFC **después** del plegado). Con él, **los 80 tests
pasan**.

He buscado por fuerza bruta (832.839 textos: todos los códigos asignados de Unicode, más letras especiales
seguidas de marcas combinantes) dónde agrupan distinto la clave de R1 y la del mutante. Salen **90 clases**, todas
con caracteres exóticos: la «s» larga «ſ» seguida de una marca combinante (U+017F U+0301 frente a «ś»), griego con
diéresis y tilde, y algún carácter cirílico histórico. Es el matiz de Unicode por el que la comparación canónica
sin mayúsculas recomienda normalizar **también después** de `casefold`. En esos casos el mutante es *más* fiel a
Unicode que R1 tal como está escrito, y para el castellano el resultado es el mismo (Á, É, Í, Ó, Ú, Ü y Ñ pliegan a
su minúscula ya compuesta).

Por `CHECKPOINTS.md` C4 bis, en `critico` un mutante a mano que no se mata necesita la **aceptación escrita del
humano**; no basta con mi juicio. **Cambio requerido (una de las dos cosas, la elige el líder con el humano):**

- (a) **Recomendada.** El humano acepta por escrito que X01 queda vivo: la diferencia solo aparece con caracteres
  ajenos al castellano, y R1 se queda como se aprobó. Se anota en `progress/impl_F-060.md` con la fecha.
- (b) Clavar R1 tal como está escrito con un test, por ejemplo
  `clave_de_ubicacion("ſ́") == "ś"`. Es fijar a propósito un comportamiento que Unicode considera
  incompleto, así que solo tiene sentido si el humano quiere R1 al pie de la letra. (Si prefiere el comportamiento
  canónico, sería una enmienda de R1, fuera de este bloque.)

## Observaciones (no bloquean)

- **O-1 · Efectos de `casefold` más allá de las mayúsculas.** Comprobado: `"Strasse Ejemplo"` contra
  `("Straße Ejemplo",)` da `normalizable`, y `"ﬁnca Ejemplo"` (con ligadura) contra `("Finca Ejemplo",)` también.
  Al pie de la letra, R4 dice que una letra distinta no coincide, pero R1 y D-3 piden `casefold` expresamente, y
  `test_f060_r1_casefold_y_no_lower` lo fija a propósito. En castellano no pasa. La «ı» turca sin punto **no**
  coincide con la «i» (`sin_coincidencia`), como debe ser. No hay nada que cambiar; queda dicho para el humano.
- **O-2 · El `oid` del sistema sí lo puede enviar una persona.** `validar_quien` admite cualquier `oid` de 1 a
  128 caracteres, así que `usuario_oid = "sistema:normalizar_ubicacion"` con un correo válido pasa. El correo no
  pasa (R11, probado con tres variantes, recortado incluido). No hace daño: la revisión leída solo lleva el correo
  (F-056 R10), y la marca que miran F-038 y F-048 es `revisado_correo` (`design.md` §10.3). Pero D-4 dice «el `oid`
  y el correo… que ninguna persona puede enviar». **Para T20:** que `docs/INTEGRACION.md` §7 diga que la marca es
  el **correo**, no el `oid`.
- **O-3 · Más de 48.** `ubicacion_de_sigrid` no comprueba la longitud del valor de la lista: con una lista hecha a
  mano con un valor de 53 caracteres, propone ese valor (comprobado). En producción no puede pasar, porque
  `ubicaciones_de_tipologia` (F-056 R48) descarta lo que pasa de 48. Si pasara, el `CHECK (char_length(ubicacion)
  <= 48)` de `15_revisiones_bandeja.sql` haría fallar el `INSERT`, y con él **el lote entero** (ROLLBACK y 503).
  **Para el Bloque 3:** que un test de `normalizar_ubicaciones` fije que las listas salen de la fuente de F-056 (ya
  filtradas), o que el plan descarte un valor de más de 48. Un texto de partida de más de 48 que solo lo es por
  los blancos de los extremos sí se normaliza al valor de la lista (comprobado): eso cierra el caso N-1 de F-056,
  como dice `design.md` §3.
- **O-4 · `progress/current.md`** (es del líder). La cabecera de F-060 dice «Bloque 1 HECHO», pero conserva el
  párrafo «Lo que debe validar el humano… bloquean empezar» de antes de la aprobación, y debajo sigue todo el
  histórico de F-056 (C2: «describe SOLO la sesión activa»). Conviene ordenarlo antes de cerrar la feature.

## Lo que se ha comprobado y está bien

- **La regla (R1–R5)**, con casos límite ejecutados contra el código real:
  - ß/ss (`casefold`), NFD frente a NFC en el texto y en la lista: NFD → valor NFC y NFC → valor NFD, y en los
    dos casos se conserva la forma **de la lista** (R5).
  - Blancos interiores, tildes y puntuación → `sin_coincidencia`.
  - Una lista con dos valores que solo difieren en mayúsculas: `ambigua`, salvo que el texto sea exactamente uno
    de los dos (`exacta`), o uno de los dos tras recortar (`normalizable`, el paso 2 gana al 4).
  - Un valor repetido tal cual no es ambiguo (`dict.fromkeys`).
  - Una ubicación ya exacta, vacía (`""`) o solo con blancos → `exacta`, `sin_coincidencia` y `sin_coincidencia`.
    Es coherente con F-056: para `motivos_no_aprobable`, `""` también es `ubicacion_fuera_de_lista`.
  - `None` no llega a la regla: el plan lo cuenta en `examinadas` y nada más.
  - Lista vacía y unidad sin entrada → `sin_coincidencia` (R3).
- **Solo `nueva` y `editada` (R7, D-6).** `ESTADOS_NORMALIZABLES` es una lista **permitida**. `aprobada` y
  `descartada` normalizables van a `no_editables` sin revisión. Si son `ambigua` o `sin_coincidencia`, cuentan
  ahí y no en `no_editables`. Una `recuperar` vuelve a `nueva` y se normaliza. Los mutantes M24–M29 (invertir la
  condición, quitarla, pasarla a lista prohibida, añadir `APROBADA` o `DESCARTADA`, quitar `EDITADA`) mueren todos.
- **La foto del sistema cambia solo la ubicación (R8).** Es `replace(valores_vigentes(situacion), ubicacion=texto)`.
  El test compara uno a uno los otros doce campos sobre una `editada` con descripción y urgencia cambiadas, y
  `campos_cambiados` da `("ubicacion",)`. Los mutantes de la foto mueren todos: partir de los importados, no cambiar
  la ubicación, la huella vieja, un motivo no nulo, otra acción, otra hora, otro `oid` o correo.
- **El «quién» del sistema.** `QUIEN_SISTEMA` lleva `oid` y correo iguales a `sistema:normalizar_ubicacion`. Cabe en
  los límites de F-056 (correo de 3 a 254, `oid` de 1 a 128). `validar_quien` rechaza ese correo tal cual, con
  otro `oid` y con blancos alrededor (R11). Con un literal con `@` (M47) el test cae. Lo que sí admite está en O-2.
- **La esperada (R9) y el orden** por `incidencia_id`, con entradas desordenadas, y la `revision_id` de la última
  leída o `None`.
- **El recuento (R10)**: las seis cifras y la suma, con un caso de catorce incidencias.
- **Coherencia con F-056** (Q-1, R21–R23 en el dominio): tras aplicar el plan, la incidencia queda `editada`, sin
  `ubicacion_fuera_de_lista` y con `campos_cambiados == ("ubicacion",)`; una segunda pasada da `normalizables = 0`.
- **Arquitectura (C3).** `normalizacion.py` importa solo la biblioteca estándar y `domain.models.revision`. Sin red,
  sin base y sin reloj: la hora entra por parámetro. Las guardias de arquitectura de F-005 y F-036 están en verde.
  Primera línea con la ruta en los dos ficheros. Sin `print`, sin TODO, sin secretos, sin dependencias nuevas.
  Datos ficticios (`9901`, «Sala Ejemplo», `@ejemplo.invalid`, `UUID(int=n)`), y `test_f006` en verde.

## Mutantes a mano (copia del scratchpad, `pytest tests/test_f060_normalizacion_dominio.py -x`)

`harness.mutacion` no muta las condiciones con `in`, `not in`, `is` ni `is not`, ni los argumentos de llamadas.
Hay un mutante por cada rama de esas y por cada pieza de la regla y de la foto:

| Id | Mutación | Resultado |
|---|---|---|
| M01, M02 | `texto in lista` → `not in` / `False` | muertos |
| M03, M04, M05, M45 | paso 2: rama a `False`, `not in`, devolver el texto sin recortar, quitar el paso | muertos |
| M46 | `exacta` compara el texto recortado | muerto |
| M06–M10, M12 | clave sin NFC, con NFD, sin `strip`, con `lower`, sin `casefold`, colapsando blancos interiores | muertos |
| X02, X03, X04, X05, X06 | clave con `strip(' ')`, solo `rstrip`, `upper`, NFKD, sin marcas combinantes | muertos |
| **M11** | clave con **NFKC** | **VIVO → C-1** |
| **X01** | NFC **después** de `casefold` | **VIVO → C-3** |
| **X07** | paso 2 con `strip(' ')` | **VIVO → C-2** |
| M13, M14, M15, M16 | sin quitar repetidos, sin la rama `ambigua`, devolver el texto de partida, `exacta` con texto | muertos |
| M17, M18 | `ubicacion is None` → `is not` / quitar la rama | muertos |
| M19, M20 | `is EXACTA` del plan: quitar / `is not` | muertos |
| M21, M22, M23 | `is AMBIGUA` a `False` / cambiado por `SIN_COINCIDENCIA`; `is SIN_COINCIDENCIA` a `False` | muertos |
| M24–M29 | estado: `in`, `False`, lista prohibida, `+APROBADA`, `+DESCARTADA`, `-EDITADA` | muertos |
| M30, M31 | esperada siempre `None` / `is not` | muertos |
| M32, M33 | la lista de la unidad **importada** / la ubicación **importada** | muertos |
| M34, M35 | sin ordenar / orden inverso | muertos |
| M36–M43 | foto: importados, sin cambiar la ubicación, huella vieja, motivo `''`, correo u `oid` del sistema cambiados, `aprobar`, hora de creación | muertos |
| M44 | las `no_editables` también reciben revisión | muerto |
| M47 | `TEXTO_SISTEMA` con `@` | muerto |

Tras todo, el original restaurado da **80 passed**. Los scripts están en el scratchpad, fuera del repositorio.

## Checkpoints (lo que aplica a un bloque intermedio)

### C1
- [x] `bash harness/init.sh` termina con exit code 0 (ver tabla).
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`, `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`.

### C2
- [x] Una sola feature `in_progress` (F-060); `init.sh` lo valida.
- [x] Rama `feature/F-060-normalizar-ubicaciones`.
- [x] `progress/current.md` describe la sesión activa (con el matiz de O-4, que es del líder y no bloquea este bloque).
- [x] Las features `done` tienen su resumen en `history.md` (no cambia en este bloque).

### C3
- [x] Hexagonal: dominio puro, sin imports de infraestructura.
- [x] Primera línea con la ruta.
- [x] Sin `print`, sin TODO, sin secretos y sin dependencias nuevas.
- N/A · Parte, archivo/cierre, manuscritos, firma, reprocesar, `conest`: F-060 no trata partes escaneados, ni cierra, ni archiva, ni escribe en Sigrid.
- [x] Ningún PDF ni parte escaneado en git (el diff del bloque son dos `.py` y Markdown).

### C3 bis
- N/A · El bloque no añade ni modifica nada en `docs/referencia/`.

### C4
- [x] Cada requisito del bloque (R1–R11, y R21–R23 en el dominio) tiene al menos un test `test_f060_rN_*` en verde (tabla de abajo).
- [x] Sin red ni base: dominio puro (y la guardia de red del `conftest`).
- N/A en este bloque · Las `MANUAL (humano)` (T7, T24–T28) son de los Bloques 2 y 6 y ya están en `tasks.md` con su comando exacto. Se exigen en `current.md` en la review del bloque que las tenga.

### C4 bis
- [x] `rigor: "critico"` declarado.
- [x] Fase RED: traza real pegada, **reproducida** por el reviewer desde `2c92a10` (58 failed, 22 passed, todo por aserción).
- [x] Cobertura: `normalizacion.py` al 100 % de sentencias y ramas según el informe; la `PUERTA COBERTURA` de `init.sh`: ver tabla.
- [x] Mutación: `progress/mutacion_F-060.md` generado por la herramienta; alcance (211) y mutantes (19) recalculados y coinciden.
- [x] Muertos: campaña de 46 min, más de 5, así que **no se reejecuta** y vale el recálculo puro (dicho arriba).
- [x] Coste por mutante ≈ 1166 s con 8 workers: no sospechoso.
- [ ] **Cero supervivientes sin aceptación escrita del humano: NO.** La campaña da 0, pero de los mutantes a mano sobreviven tres (M11, X07 y X01): C-1, C-2 y C-3.
- [x] «Evidencias» con los cuatro números y los workers.
- [x] Ningún N/A sin justificar.

### C4 ter
- N/A · `init.sh` imprime `RUTAS SENSIBLES: [OK] ninguna ruta sensible tocada por el diff de F-060`.

### C5 (bloque intermedio)
- [x] T1, T2 y T3 marcadas `[x]`, con commits `F-060 T1:`, `F-060 T2:` y `F-060 T3:` (`2c92a10`, `fda8418`, `af72c5b`). El resto de tareas son de bloques posteriores.
- [x] Sin temporales ni artefactos sin trackear (`git status` limpio).
- [x] `features.json`: F-060 `in_progress`, coherente.

## Cobertura · requisito → test

| R | Tests |
|---|---|
| R1 | `test_f060_r1_la_clave_recorta_y_pliega_mayusculas`, `_casefold_y_no_lower`, `_nfc_frente_a_nfd`, `_la_clave_no_toca_nada_mas` (falta NFKC: C-1) |
| R2 | `test_f060_r2_cada_fila_de_la_tabla`, `_el_exacto_gana_aunque_otro_tenga_la_misma_clave`, `_el_exacto_tras_recortar_gana_a_la_ambiguedad` (falta un blanco que no sea espacio: C-2), `_ambigua_con_tres_candidatos`, `_ambigua_por_la_forma_unicode_de_la_lista`, `_un_valor_repetido_tal_cual_no_es_ambiguo`, `_nfd_frente_a_nfc`, `_casefold_en_la_clasificacion` |
| R3 | `test_f060_r3_lista_vacia`, `test_f060_r6_una_unidad_sin_lista_no_normaliza` |
| R4 | `test_f060_r4_lo_que_no_es_la_misma_palabra_no_coincide`, `test_f060_r2_cada_fila_de_la_tabla` (filas `sin_coincidencia`) |
| R5 | `test_f060_r5_el_resultado_es_el_valor_de_la_lista_caracter_a_caracter`, `_conserva_la_forma_unicode_de_la_lista` |
| R6 | `test_f060_r6_*` (siete: vacío, una normalizable, unidad vigente, ubicación vigente, otra unidad, sin lista, sin ubicación o exacta, ambigua) |
| R7 | `test_f060_r7_estados_normalizables_son_nueva_y_editada`, `_nueva_y_editada_se_normalizan`, `_aprobada_y_descartada_son_no_editables`, `_no_editable_solo_cuenta_las_normalizables` |
| R8 | `test_f060_r8_la_identidad_del_sistema`, `_la_revision_cambia_solo_la_ubicacion_de_los_vigentes`, `_la_revision_del_plan_es_la_de_normalizacion` |
| R9 | `test_f060_r9_la_esperada_es_la_ultima_revision_leida`, `_las_revisiones_van_en_orden_de_incidencia_id` |
| R10 | `test_f060_r10_el_recuento_de_una_obra_y_su_suma`, `_el_plan_acepta_un_iterable_de_una_pasada` |
| R11 | `test_f060_r11_validar_quien_rechaza_el_correo_del_sistema` (×3) |
| R21–R23 (dominio) | `test_f060_r21_una_segunda_pasada_no_tiene_nada_que_normalizar`, `test_f060_r22_la_normalizada_queda_editada_y_sin_el_motivo`, `test_f060_r23_ambigua_y_sin_coincidencia_siguen_fuera_de_lista` |
| R12–R20, R24–R43 | De los Bloques 2 a 5: fuera de esta review |

## Cambios requeridos (resumen)

1. **C-1** · `tests/test_f060_normalizacion_dominio.py`: casos que distingan NFC de NFKC (`"SALA EJEMPLO"` en
   el test de R4, y «1º»/«1ª» contra «1O»/«1A»). Traza del rojo con M11 aplicado, pegada en el informe.
2. **C-2** · `tests/test_f060_normalizacion_dominio.py:290-296`: el paso 2 con tabulador, salto de línea o espacio
   duro contra `L_AMBIGUA`. Traza del rojo con X07 aplicado.
3. **C-3** · X01: aceptación escrita del humano (recomendado) o un test que clave R1 tal como está escrito. Lo lleva
   el líder.

Sin cambios en `normalizacion.py`. Tras (1) y (2), la campaña del Bloque 1 **no** hace falta relanzarla: solo cambian
tests, y el alcance de producción y sus 19 mutantes son los mismos.

## Propuesta de automejora (para que la apruebe el humano; no aplicada)

- **Para `arnes-base` (`harness/mutacion.py`).** Añadir operadores para `in` ↔ `not in` e `is` ↔ `is not` en las
  condiciones, y para el literal de forma de `unicodedata.normalize` (NFC ↔ NFKC/NFD) y `.strip()` → `.strip(' ')`.
  En este bloque, las ramas que más importan (la `exacta`, el recorte, la lista permitida de estados) y los dos
  supervivientes de la regla solo salieron con mutantes a mano. La herramienta los daba por cubiertos con 19/19
  muertos.
- **Para `CHECKPOINTS.md` C4 bis.** Cuando el requisito central es una **regla de comparación de texto**
  (normalizar, plegar mayúsculas, recortar), exigir que el reviewer pruebe a mano las variantes vecinas de cada
  transformación (forma Unicode, plegado, qué blancos se recortan), y no solo quitar la transformación: quitar
  `strip` muere, pero cambiar **qué** recorta sobrevivió.
