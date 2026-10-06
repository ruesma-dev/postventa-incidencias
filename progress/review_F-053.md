<!-- progress/review_F-053.md -->
# F-053 · Dos datos que pide el portal — Review

- **Veredicto:** **APPROVED**
- **Rama:** `feature/F-053-datos-para-el-portal`, HEAD `2d58e19`. Base `349ba06` (`dev`).
- **Fecha:** 2026-10-06.
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura
  de las líneas cambiadas ≥ 80 %, campaña de mutación con **cero supervivientes** sin
  justificación aceptada por el humano, y las verificaciones `MANUAL (humano)` con su comando
  exacto.

No hay hallazgos bloqueantes. Las observaciones del final no bloquean. Dos de ellas son
propuestas de automejora del arnés y necesitan el visto bueno del humano.

## 1 · `init.sh`

Lo lancé tal cual: `bash harness/init.sh` → **ENTORNO LISTO**.

- `115 passed` en la raíz.
- Servicio api y servicio front en verde. La suite entera ya había pasado dentro de `init.sh`
  en el T9 del implementer (6706 pasan); esta vez salió de la caché, con el árbol sin cambios.
- `PUERTA COBERTURA: 100.0% de 8 líneas cambiadas cubiertas (8/8, umbral 80%, nivel critico)`.
- `ruff`: 73 avisos. Son los mismos 73 que en `349ba06`, así que F-053 no añade ninguno.
  `ruff check` desde la raíz sale limpio en los 4 ficheros de código y en los 4 tests nuevos.

## 2 · Comprobaciones pedidas por el líder

### 2.1 `importado_at_utc` (R1–R7)

- `serializar_importacion` lee `resultado.importacion.importado_at_utc` y nunca `contexto.ahora`,
  así que sirve para las dos rutas (R1, R2 y R6).
- `_instante_utc` devuelve `None` si `utcoffset() is None` (R5). Si no, devuelve
  `astimezone(UTC).isoformat(timespec="microseconds")`. Con `datetime.UTC` eso da siempre
  `…T…:…:….ffffff+00:00` (R3, R4).
  - El campo es `datetime` NOT NULL en el puerto (`domain/ports/bandeja.py:63`) y en el DDL, así
    que no hay ninguna ruta con `None` que acabe en un 500.
- La clave va dentro del literal del cuerpo 200. Los cuerpos de error los construye
  `function_app` sin pasar por el serializador. Los tests lo fijan para 400, 413, 409 y 503
  (R7).
- Encaja con el contrato del front (`progress/review_F-035.md`, bloque 12, puntos 1–4):
  - el instante va con desfase explícito de cuatro cifras, con `T` y con segundos;
  - nunca se quita la zona (R4 mata `replace(tzinfo=…)`, comprobado abajo);
  - la forma es exactamente la del caso de Node «con +00:00 y microsegundos (isoformat de
    Python)» (`f035_paginas.test.js:660`);
  - `null` se rotula sin fecha (`:664`).

### 2.2 `oficio.distintos` (R8–R16)

- `pares_distintos` reutiliza `_ultimas`, que aplica las reglas de F-036: manda la fecha, a igual
  fecha la que llega después, y otro catálogo no cuenta.
  - Filtra los **dos** códigos contra los oficios de la obra.
  - `DecisionPar.__post_init__` ya garantiza `codigo_a < codigo_b`, y `sorted` ordena la lista.
  - Como `_ultimas` devuelve un diccionario por par, no salen repetidos (R9–R13).
- `propuestas_de_oficios` lo calcula con la misma tupla de `decisiones` que devuelve `_vigentes`.
  No hay ninguna lectura nueva (R16). El test fija la lista exacta de llamadas y que
  `ultimas_decisiones` se pide una sola vez.
- `leer_propuestas` mete `"distintos"` **dentro** de `oficio`, con exactamente `codigo_a` y
  `codigo_b` (R8). `_grupos()` y `GruposVigentes` no se tocan, así que
  `POST /api/catalogos/decisiones` no cambia (R17, D-5).
- Encaja con el contrato del bloque 13 (puntos 1–9):
  - va dentro de `oficio`;
  - es una lista de `{codigo_a, codigo_b}` sin `oid` ni `decidido_por`;
  - los códigos van como textos idénticos a `oficios[].codigo` (`"0033"`/`"0133"`, comprobado con
    `isinstance` en R11);
  - cada par lleva dos códigos distintos y en orden;
  - el filtro por obra lo hace el backend;
  - «distinto, luego mismo» no sale y «mismo, luego distinto» sí, ambos por la ruta HTTP;
  - el par puede estar a la vez en `distintos` y en `avisos` (R15).
  - El punto 6, los guiones, consta en `docs/INTEGRACION.md` (D-6). El contrato admite que solo
    conste.

### 2.3 D-3: líneas cambiadas en `test_f036_*.py` respecto de `349ba06`

Lo comprobé con `git diff 349ba06 -- services/postventa-api/tests/test_f036_*.py`: **3 líneas `+`
y 0 líneas `-`**.

- `"importado_at_utc",` en `CLAVES` (`test_f036_importar_http.py`).
- `"distintos": [],` en las igualdades de `test_f036_r87_…` y `test_f036_r12_…`
  (`test_f036_catalogos_http.py`).

Es exactamente lo que se aprobó.

### 2.4 Alcance R18/R19

`git diff --stat 349ba06 -- services/postventa-front infra services/postventa-api/infrastructure
services/postventa-api/function_app.py services/postventa-api/domain/ports` sale **vacío**.

- No hay DDL ni variables de entorno nuevas.
- El código de producción tocado son 4 ficheros: los previstos en design §3.

### 2.5 Commits del líder ajenos a F-053

Revisé `72d4704`, `930b812`, `f068c1e`, `a43623e`, `a58b5cb` y `ee847d0` con `git show --stat`.
Entre los seis solo tocan:

- `BACKLOG.md`
- `harness/features.json`
- `progress/current.md`
- `progress/impl_F-053.md`
- `progress/review8_F-035.md`
- `specs/F-053-…/tasks.md`

**Ninguno toca código ni tests.** El tapado de `930b812` deja `<client-id>` en
`review8_F-035.md`.

### 2.6 Secretos y datos

Barrí con regex las líneas añadidas en todo el diff de la rama (`git diff 349ba06..HEAD -U0`,
solo las `+`). Patrones usados:

- GUID: `[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`
- `Ajustes\(`, `password`, `secret`, `AccountKey`, `client_secret`, `SharedAccess`, `Bearer `,
  `@ruesma` y direcciones IPv4
- en `services/` y `docs/`: `proveedor`, `S.L.`, `S.A.`, `NIF` y `CIF`

Resultado:

- **Cero GUID.**
- Ningún repr de `Ajustes` ni ningún valor de secreto.
- Las coincidencias de «secret» y «Ajustes» son solo nombres de features en `BACKLOG.md`, el
  nombre de fichero `test_f005_integracion_sin_secretos.py` y el comando de `review8_F-035.md` con
  `<client-id>`/`<secreto>` ya tapados.
- La única IP es `127.0.0.1`, en el título de F-054 (`BACKLOG.md`, del líder).
- «Proveedor» solo aparece como valor del enum `Catalogo.PROVEEDOR`, con los códigos inventados
  `P001`/`P002`.
- Ningún nombre ni código real de proveedor.
- Los nombres de oficio de la 0677 («Solados y Alicatados…») son oficios del catálogo, no
  proveedores, y ya estaban en la spec aprobada.
- Ningún fichero añadido es PDF ni documento ofimático (`git log --diff-filter=A`).

### 2.7 Puerta de cobertura: «8 líneas cambiadas»

**El número es correcto para el diff real.** Lo recalculé por mi cuenta: crucé las 79 líneas de
`harness.alcance` con las líneas de sentencia del AST, sin contar los docstrings. Salen 8:

| Fichero | Líneas que cuentan |
|---|---|
| `application/pipelines/equivalencias.py` | 175 `distintos: tuple[…]` (anotación de la dataclass) |
| `domain/models/equivalencias.py` | 466 `def pares_distintos`, 479 `dados = …`, 480 `return tuple(` |
| `interface_adapters/api/importar.py` | 264 `def _instante_utc`, 270 `if …`, 271 `return None`, 272 `return …` |
| `interface_adapters/api/equivalencias.py` | ninguna |

Por qué 79 se quedan en 8:

- coverage solo mide la **primera línea de cada sentencia**;
- el resto del diff son docstrings y comentarios;
- y hay líneas añadidas **dentro de sentencias de varias líneas que ya existían**:
  - la clave en el `dict` de `serializar_importacion`,
  - el `"distintos": [...]` del `return` de `leer_propuestas`,
  - el `distintos=pares_distintos(...)` del `return` de `propuestas_de_oficios`,
  - el `pares_distintos,` del `import`.

Esas líneas se ejecutan con su sentencia, así que coverage no las cuenta. Que los tests las ven
lo demuestran los mutantes a mano I6, E1, E2, A1 y A2, todos muertos (los comprobé E1 y A1, ver
§4). La propuesta de automejora O-4 viene de aquí.

## 3 · Checkpoints

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0 (§1).
- [x] Existen `CLAUDE.md`, `features.json`, `SPECS.md`, `current.md`, `history.md`,
  `ARCHITECTURE.md` y `CONVENTIONS.md` (lo comprueba `init.sh`).

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: `['F-053']`.
- [x] La rama es `feature/F-053-datos-para-el-portal`.
- [x] `progress/current.md` **empieza por el bloque vivo de F-053**. Es el mismo criterio que
  aplicó la review de F-036.
  - Sigue arrastrando bloques históricos. Viene de antes: la base ya tenía 4934 líneas y F-053
    añade 52.
  - El rótulo del bloque dice todavía «Bloque 1 encargado al implementer» (O-5).
- [x] Toda feature `done` tiene su resumen en `history.md`. F-053 no está `done`, y el diff no
  cambia el estado de ninguna otra.

### C3 — Arquitectura y convenciones

- [x] Hexagonal respetada:
  - `pares_distintos` es pura y vive en `domain/models` sin imports nuevos;
  - la aplicación importa del dominio;
  - el borde serializa;
  - nada en `infrastructure/` ni en `domain/ports`.
- [x] Primera línea con la ruta: en los 4 tests nuevos sí. Los 4 ficheros de producción ya la
  tenían y no cambia.
- [x] Sin `print()`, sin `TODO` y sin secretos (§2.6). No hay dependencias nuevas.
- [x] *El parte como unidad de trabajo.* N/A: F-053 no toca el circuito de partes.
- [x] *Nada se archiva ni se cierra sin validaciones; dry-run ante Sigrid.* N/A: F-053 no escribe
  en Sigrid ni archiva. Solo serializa dos campos que ya se leían.
- [x] *Lo manuscrito no se descarta.* N/A: no toca la extracción.
- [x] *Firmado no es conforme.* N/A: no toca la clasificación.
- [x] *Reprocesar no duplica.* No se toca. R6 deja fijado que una parcial reprocesada da la fecha
  de la nueva, que es el comportamiento de F-036.
- [x] *No hardcodear estados de Sigrid.* N/A: no hay consultas a Sigrid.
- [x] Ningún PDF ni escaneado en git (`git log --diff-filter=A 349ba06..HEAD`).

### C3 bis — Documentos de fuera

- N/A (justificado): la rama no añade ni modifica nada en `docs/referencia/`.

### C4 — La verificación es real

- [x] Cada requisito tiene un test trazable que pasa (tabla del §5).
  - R18, R19 y R21 son de alcance o de documentación externa. Se verifican con el diff de §2.3 y
    §2.4, y R21 es T7 del líder.
- [x] Los tests no tocan red ni BBDD: usan los dobles en memoria de F-036, con `function_app`
  parcheado por `monkeypatch`.
- [x] Las `MANUAL (humano)` están listadas con su comando exacto en `tasks.md` (T10 y T11).
  `current.md` las cita por referencia («tasks T1–T12») y apunta la precondición de T11. Es el
  mismo criterio que en F-036.

### C4 bis — El rigor declarado se cumple

- [x] `rigor: "critico"` declarado y válido.
- [x] **Fase RED** con salida real en `progress/impl_F-053.md`:
  - T1: 13 failed, todos por `KeyError`/aserción sobre `importado_at_utc`;
  - T3: `ImportError` de `pares_distintos` y 14 failed, todos por `distintos`;
  - T6: 19 failed.
  - Los commits RED (`7dcd3e5` y `5f7b3a3`) van antes que los GREEN.
- [x] **Cobertura**: `[OK]` 100 % (8/8). El número está comprobado en §2.7.
- [x] **Mutación**: existe `progress/mutacion_F-053.md`, generado por la herramienta. Los totales
  están **verificados de forma independiente**:
  - `harness.alcance` da 4 ficheros y 79 líneas, igual que el informe;
  - `generar_mutantes` da **5 mutantes**, todos en `domain/models/equivalencias.py:484`, con el
    mismo operador y el mismo texto original→mutado que el informe (comparación `==`→`!=`,
    `and`→`or` ×2, `par[0]`→`par[1]` y `par[1]`→`par[2]`);
  - los 3 en `timeout` son exactamente esos mismos.
- [x] **Los muertos, comprobados.** El «Tiempo total» es de 4181,2 s (unos 70 min), por encima de
  5 min, así que **la campaña no se reejecutó entera** y vale el recálculo puro.
  - Aun así, **reejecuté a mano los 3 `timeout` y el resto de mutantes de la línea 484** en una
    copia desechable (`git archive HEAD` en mi scratchpad), solo con los tests de F-053. Murieron
    todos (§4).
- [x] **Coste por mutante**: 4181,2 s × 5 workers ÷ 5 mutantes = **4181 s por mutante**. Está por
  encima del tiempo de la suite que declara el informe (897–3012 s), así que no es sospechoso.
- [x] Cero supervivientes. Los 3 `timeout` tienen su análisis completo y **los confirmé muertos
  por mi cuenta**, así que no hay nada que justificar como equivalente.
  - Los 13 mutantes a mano, todos muertos. Muestreé 8 de ellos (§4).
  - Ninguno se declaró equivalente, así que no hace falta aceptación del humano.
- [x] La sección «Evidencias» trae tests, cobertura, mutantes, supervivientes y tiempo de la
  suite.
  - Los **workers** (5) no están en la tabla de «Evidencias». Constan en «T8 (a)» del mismo
    informe y en la cabecera de `mutacion_F-053.md`. Es menor (O-2).
- [x] Ningún N/A sin justificar.
- **Orden (punto 7 del protocolo):** N/A, justificado. Ningún requisito central de F-053 es una
  puerta que deba ir **antes** de un colaborador.
  - R16 pide el **número** de lecturas, no su orden, y lo fija la lista exacta de llamadas del
    test.

### C4 ter — Rutas sensibles

- N/A (justificado): no existe `harness/rutas_sensibles.json`.

### C5 — La sesión se cerró bien

- [x] `tasks.md`: T1–T6, T8 y T9 marcadas `[x]`, cada una con su commit `F-053 Tn:` (8 commits).
  - **T7** es del líder al desplegar, por decisión del humano del 2026-10-06 que consta en
    `tasks.md`.
  - **T10–T12** son MANUAL o de cierre, posteriores a esta review por diseño.
  - Las cuatro quedan legítimamente sin marcar en este punto.
- [x] Sin ficheros temporales ni sin trackear: `git status` limpio.
- [x] `features.json` dice `in_progress`, que es lo real.

## 4 · Mutantes reejecutados por el reviewer

Los apliqué uno a uno en una copia desechable del árbol (`git archive HEAD` en el scratchpad,
nunca en el árbol de trabajo), y restauré después de cada uno.

- Sin mutar, en la copia:
  - tests de oficios (`test_f053_distintos_dominio.py` + `test_f053_propuestas_distintos.py`):
    `33 passed`;
  - test de importación (`test_f053_importado_at_utc.py`): `17 passed`.

| Mutante | Resultado (solo los tests de F-053) |
|---|---|
| L484 `== DISTINTO` → `!=` (timeout en la campaña) | **muerto**, 25 failed |
| L484 `par[0]` → `par[1]` (timeout en la campaña) | **muerto**, 1 failed (`[a_fuera]`) |
| L484 2.º `and` → `or` (timeout en la campaña) | **muerto**, 10 failed |
| L484 1.º `and` → `or` | **muerto**, 12 failed |
| I1 `_instante_utc(contexto.ahora)` | **muerto**, 4 failed |
| I2 `isoformat()` sin `timespec` | **muerto**, 3 failed |
| I3 sin `astimezone(UTC)` | **muerto**, 2 failed |
| I3b (mío) `replace(tzinfo=UTC)` en vez de `astimezone`: el error del punto 2 del contrato | **muerto**, 2 failed |
| I5 sin la rama sin zona | **muerto**, 1 failed |
| D1 `sorted(` → `list(` | **muerto**, 2 failed |
| A1 `Catalogo.OFICIO` → `PROVEEDOR` en la aplicación | **muerto**, 8 failed |
| E1 `codigo_a`/`codigo_b` cruzados en el borde | **muerto**, 7 failed |

Las cifras coinciden con las del informe del implementer en todos los que tienen pareja.

**Los 3 `timeout` los cazan tests de F-053 por sí solos.** No depende de una suite vecina.

**Por qué salieron en `timeout`:**

- la campaña usó `--timeout 900`, y la suite del servicio tarda **897 s** sin carga (Bloque 2) y
  3012 s con carga (T9);
- con `-x` y orden alfabético, un mutante que solo cazan tests tardíos (`test_f036_catalogos_*`,
  `test_f053_*`) no llega a ellos dentro del reloj.

La explicación del implementer es correcta. El texto que genera la herramienta, «sin nadie
compitiendo por la máquina», no lo es en este caso (O-3).

## 5 · Cobertura requisito → test

| Req. | Test(s) |
|---|---|
| R1 | `test_f053_r1_la_importacion_nueva_lleva_el_instante_guardado[completa\|parcial]` |
| R2 | `test_f053_r2_ya_importado_devuelve_el_instante_de_la_original`, `test_f053_r2_el_serializador_lee_el_resultado_y_no_el_ahora_del_contexto` |
| R3 | `test_f053_r3_con_microsegundo_cero_salen_igual_las_seis_cifras`, `test_f053_r3_con_microsegundos_la_forma_es_la_misma` |
| R4 | `test_f053_r4_una_importacion_con_otra_zona_sale_en_utc`, `test_f053_r4_la_original_leida_en_la_zona_de_la_sesion_sale_en_utc` |
| R5 | `test_f053_r5_un_instante_sin_zona_sale_null_con_200` |
| R6 | `test_f053_r6_reprocesar_una_parcial_da_el_instante_de_la_nueva` |
| R7 | `test_f053_r7_las_tres_respuestas_200_llevan_la_clave`, `test_f053_r7_ninguna_respuesta_de_error_lleva_la_clave[×6]`, `CLAVES` de F-036 |
| R8 | `test_f053_r8_distintos_va_dentro_de_oficio_con_dos_claves_por_par` |
| R9 | `test_f053_r9_*` del dominio (sale, `mismo` no sale, código fuera ×3, sin códigos, generador) |
| R10 | `test_f053_r10_*` del dominio (4, incluida la regla fecha/llegada) y por HTTP (`…distinto_y_despues_mismo_no_sale`, `…mismo_y_despues_distinto_sale`) |
| R11 | `test_f053_r11_el_par_de_la_0677_sale_como_textos_con_sus_ceros` (HTTP) y `test_f053_r11_los_codigos_salen_como_textos_con_sus_ceros` (dominio) |
| R12 | `test_f053_r12_*` del dominio (3) y `test_f053_r12_ordenados_y_sin_repetidos_aunque_lleguen_al_reves` (HTTP) |
| R13 | `test_f053_r13_*` del dominio (3) |
| R14 | `test_f053_r14_*` (3) y las dos igualdades de F-036 (D-3) |
| R15 | `test_f053_r15_el_par_sale_a_la_vez_en_distintos_y_en_el_aviso` |
| R16 | `test_f053_r16_las_mismas_lecturas_una_llamada_a_ultimas_decisiones` |
| R17 | `test_f053_r17_la_respuesta_de_decidir_no_lleva_distintos`; `test_f036_r88_…` sin tocar; los tests de plantilla y bandeja de F-036, sin tocar y en verde |
| R18 | los tests de F-036 en verde (6706 pasan en T9) y el diff de §2.3 (3 `+` y 0 `-`) |
| R19 | el diff de §2.4, vacío |
| R20 | `test_f053_documentacion.py` (19 tests) |
| R21 | T7, del líder al desplegar. Fuera de esta review por decisión del humano |
| V1, V2 | MANUAL (T11), después del merge y del despliegue |

## 6 · Cambios requeridos

Ninguno.

## 7 · Observaciones (no bloquean)

- **O-1 · La cabecera de `docs/INTEGRACION.md` ha quedado vieja.** Sigue diciendo «Fecha:
  2026-10-05. Última feature que lo tocó: F-036», y ahora la ha tocado F-053.
  - `test_f036_documentacion.py:74,200-201` fija esa cabecera, y cambiarla rompería la regla de
    D-3 (solo tres líneas en tests de F-036). Por eso el implementer no la tocó e hizo bien en
    avisar.
  - El párrafo nuevo ya fecha F-053 («Desde F-053 (2026-10-06)»), así que no engaña sobre el
    contrato. Solo engaña la línea de cabecera.
  - **Destino: el líder y el humano.** Opciones:
    - (a) cerrarlo dentro de F-053 con un D-3 bis aprobado: la cabecera y `FECHA` del test;
    - (b) dejarlo para la próxima feature que toque el documento, y de paso que el test de F-036
      deje de exigir «F-036» como última feature, porque esa aserción caduca con cualquier
      feature nueva.
  - Antes de copiarlo a `azure-apps` en T7, conviene haberlo decidido.
- **O-2 · Los workers no están en la tabla «Evidencias».** Constan en «T8 (a)» del mismo informe
  y en `mutacion_F-053.md`. CHECKPOINTS pide que estén en «Evidencias». Es menor: el dato existe y
  el coste por mutante se puede calcular (§3).
- **O-3 · Automejora de `harness.mutacion` (para `arnes-base`, requiere visto bueno).** Son dos
  cosas.
  - (1) El `timeout` por mutante (aquí 900 s) puede quedar **por debajo de la duración de la
    suite** (897 s sin carga). En ese caso todo mutante que solo cacen tests tardíos sale en
    `timeout` por construcción.
    - **Propuesta**: que la herramienta mida la suite sin mutar al empezar y avise o ajuste si
      `--timeout` < 1,5 × esa duración.
  - (2) El texto de la sección «Timeouts» dice «sin nadie compitiendo por la máquina: la
    contención ya no los explica». El repaso solo serializa *dentro* de la campaña y no sabe si
    hay otras cargas en la máquina.
    - **Propuesta**: cambiarlo por «sin otros workers de esta campaña», y que diga cuánto tarda la
      suite sin mutar.
- **O-4 · Automejora de la puerta de cobertura (para `arnes-base`, requiere visto bueno).** La
  puerta solo cuenta las líneas de inicio de sentencia, así que una línea añadida **dentro** de
  una sentencia de varias líneas que ya existía no cuenta (§2.7).
  - Aquí no esconde nada, porque los mutantes a mano lo cubren.
  - Pero una feature cuyo cambio sea solo una clave nueva en un `dict` o un argumento nuevo en
    una llamada larga saldría con «0 líneas cambiadas».
  - **Propuesta**: que `cobertura_lineas_cambiadas` lleve cada línea cambiada a la de inicio de
    su sentencia (con `ast`) antes de cruzarla con `executed_lines`, y que el informe diga
    «N líneas del diff → M sentencias».
- **O-5 · El rótulo de F-053 en `progress/current.md` está viejo.** Dice «`in_progress` · Bloque 1
  encargado al implementer». Lo actualiza el líder al cerrar.
- **Transparencia del reviewer.** Para comparar el número de avisos de `ruff` hice un
  `git checkout 349ba06` momentáneo en la carpeta principal: solo lectura, sin cambios. Volví a la
  rama enseguida y `git status` quedó limpio. Los mutantes se aplicaron solo en la copia del
  scratchpad.
