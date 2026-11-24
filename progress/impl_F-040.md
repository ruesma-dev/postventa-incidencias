<!-- progress/impl_F-040.md -->
# F-040 · Volcar a Sigrid las incidencias aprobadas — informe de implementación (desde el 2026-11-19)

Lo anterior (Bloque 0, Bloque 1, T4, T5.1, T5.2, T6a, hasta el aparcamiento del
2026-11-05) está en `progress/impl_F-040_hasta_2026-11-05.md`, renombrado con
`git mv` por la decisión D-8 (`specs/F-040-volcado-sigrid/design.md` §12): pasaba
de la puerta TAMAÑO (520/220).

## Base fija

- **`4b1eb21`** (rama `feature/F-040-volcado-sigrid`, worktree `postventa-f040`):
  merge de `dev` `ed9318e`, que trae F-072 `done` (en producción desde el
  2026-11-18) y lo integrado durante el aparcamiento. Anotada por el líder en T8.

## T8 · líder, 2026-11-19

- El humano aprueba la spec puesta al día y D-1..D-8 con la opción recomendada
  («lo recomendado», 2026-11-19). Escritas en la columna «Decidido» de
  `design.md` §12.
- D-8 aplicada: `impl_F-040.md` → `impl_F-040_hasta_2026-11-05.md` y
  `review_F-040.md` → `review_F-040_bloque1.md`; este informe y
  `progress/review_F-040.md` son los nuevos.
- F-040 pasa de `blocked` a `in_progress`.

## Bloque 1 bis · implementer, 2026-11-19 (T9–T11)

Detalle completo, con las trazas RED de T9 sin recortar, en `progress/impl_F-040_bloque1bis.md` (movido allí el
2026-11-24 por la puerta TAMAÑO). Resumen: R63–R68 (tipo de reclamación con su etiqueta, recuento por tipo, textos
de Q-11, `opcionesDeListado`, miga como texto); RED con 20 casos JS y 11 pytest en rojo; GREEN en `288ee16`
(copia LF: 1149/1149 JS, 939 pytest); mutación 50/50 muertos, 0 supervivientes
(`progress/mutacion_F-040_bloque1bis.md`).

## T12 · publicación (humano) y comprobación (líder), 2026-11-21

- Merge del Bloque 1 bis a `dev` (`87e124e`, líder) junto con los arreglos de `Ajustes` y del proveedor;
  `ARNES_SIN_CACHE=1 bash harness/init.sh` en verde sobre `dev` `8ac908d` (2201 / 10382 / 920 passed).
- El humano publica backend y front desde una copia limpia de `dev`; `27_ventana_volcado.ps1` sin parámetros:
  **cerrada**.
- Comprobación del líder por el front, con la sesión del humano, solo lecturas: `GET /api/health` 200;
  `js/volcado.js` publicado sin `TEXTO_TIPO` y con `nombreDeTipo` y el recuento por tipo; `js/revision.js` con
  «Listado (tipo de reclamación)», los textos de D-1 y `tipo_fuera_de_sigrid`, sin «Sin listado»; la miga de
  `bandeja.html` con la página actual como `span`. `GET /api/revision` de la 0626 (200, 19,5 s) y la 0677
  (200, 14,7 s): 4 listados; 25 y 38 pares, ninguno con espacio final ni vacío (el arreglo del proveedor,
  publicado). Application Insights, 3 h: 0 excepciones, ninguna traza de aviso o superior, todas las
  peticiones 200.
- Siguiente: T5.3 (humano, 0626, ventana cerrada).

## T5.3 · confirmar con la ventana cerrada (líder, por encargo del humano), 2026-11-23

- El humano encarga al líder hacer las pruebas («haz tú las pruebas»); el clic de confirmar lo da el líder con la
  sesión del humano. Antes del clic, `VOLCADO_HABILITADO=false` leído en la Function (dos veces).
- Foto `28_` de la 0626, ANTES: 2 partes `PVI-` (`RS26.09/0439` SAT, `RS26.10/0074` NPR); MAX(cod) del mes
  `RS26.11/0083`. PASA.
- «Registrar»: una lectura de `revision/sigrid` (200); la fila «PRUEBA F-040 - ANULAR» sale en **choca** con
  `RS26.09/0439`. Con su casilla, `volcado/ensayo` 200: «Se crearía 1», columna Tipo «PRIMER LISTADO POSTVENTA
  (0002)» (R63, etiqueta y código).
- «Volcar 1 partes»: la confirmación dice «Se va a crear 1 parte en el ERP de producción de la obra 0626: 1 de
  <unidad>. Escribe 1 para confirmar.» Con el 1: **una** petición `POST volcado/volcar`, **503**; en Application
  Insights, `volcado/volcar no procede: volcado_deshabilitado (503)`. El panel dice «La ventana del volcado está
  cerrada. No se ha escrito nada.» y el resultado «Creados 0 · Sin volcar 1». Ningún reintento; después, solo
  la recarga de la bandeja.
- Foto `28_` DESPUÉS: idéntica (2 partes `PVI-`, MAX(cod) `RS26.11/0083`). PASA.
- Siguiente: T5.4, la única escritura real, con la autorización expresa del humano en el chat (R69).

## T5.4 · la escritura real (líder, con la autorización expresa del humano), 2026-11-24

- Autorización del humano en el chat para T5.4 entera («si», 2026-11-24). La ventana la abre **el humano**
  (`27_ -Abrir`, tecleando ABRIR): el control de permisos de la sesión no deja que el líder responda esa palabra.
- [D-6] La fila de prueba, editada a `0003` POST VENTA desde la página (queda «Registrada: PRIMER LISTADO
  POSTVENTA (0002)» en el detalle) y vuelta a aprobar. Ensayo de calentamiento con la ventana cerrada: «Se
  crearía 1», Tipo «POST VENTA (0003)».
- Con la ventana abierta (`VOLCADO_HABILITADO=true` leído): «Registrar», casilla de la fila (choca con
  `RS26.09/0439`), ensayo 200 (previstos 1, `con_conflicto_confirmado=1`), «Volcar 1 partes», el 1 y «Volcar en
  Sigrid»: **una** petición `POST volcado/volcar` 200; Application Insights: `creados=1 idempotentes=0
  rechazados=0 no_procesados=0 sin_respuesta=0`, `sigrid_cod=RS26.11/0091`. El panel: «Creados: 1» y el aviso
  de PTE (R59: el parte queda en SAT; pasarlo a PTE es de Posventa, a mano).
- **Enseguida** `27_ -Cerrar` (el líder): releída, `false`. La ventana estuvo abierta ~1 minuto.
- Foto `28_ -CodigoObra 0626 -Referencia PVI-<id>`: **un** parte con la referencia, ficha `rcp` 1, `RS26.11/0091`,
  estado **SAT**, tipo **0003**, oficio 0005, 1 interviniente, 0 causantes, UPV de la obra. PASA. **No se pasa a PTE.**
- Un «Registrar» más, sin ensayar: una lectura de `revision/sigrid`; «Ninguna candidata», volcadas 2.
- Nota: dos `TaskCanceledException` de `Functions.revision` a la hora de abrir la ventana: es el reinicio de la
  Function por el cambio de la App Setting, que corta la petición en vuelo; ninguna en el volcado.

## T5.5 · sin `oid` ni correo (líder), 2026-11-24

- Tras T5.4: `localStorage` y `sessionStorage` vacíos (sin `@` ni GUID). Consola: sin mensajes con `@`, `oid` ni
  GUID desde que se empezó a seguir (después del volcado; la carga de la página no quedó cubierta). La parte de
  la consola durante la carga la cubre la comprobación del 2026-11-02.
- Siguiente: T5.6, anular `RS26.11/0091` desde la UI de Sigrid (NO PROCEDE, sin correo), **humano**; luego la
  foto `28_` en `NPR` (líder).

## T6 y T6 bis · implementer, 2026-11-24

Encargo del líder: solo T6 y T6 bis. **Cambio del líder a mitad, por decisión del humano (2026-11-24)**: T5.6 hecha
sin anular `RS26.11/0091` (queda en SAT), y T6 como dice la spec: **F-040 `done` en su único commit**, sin desviación.

### Commits

| Commit | Qué |
|---|---|
| `03992e0` | `F-040 T5.6`: `tasks.md` T5.6 `[x]` con la nota del humano (commit propio, antes de T6) |
| `a0c15a8` | `F-040 T6`: cierre de R57 **y** F-040 `done` en `harness/features.json`, un solo commit (D-11 de F-038) |
| `8dbb559` | `F-040 T6 bis`: `docs/INTEGRACION.md` sin F-040 en futuro (R58) |
| `azure-apps` `be26951` | `postventa_incidencias.md`, commit aparte en `main`, **sin push** |

### T6 · RED (requisito central: R57)

Tests nuevos, escritos antes del código: `tests_js/portal.test.js` «f040 R57: sin los placeholders del volcado…» y
«…el componente etiqueta tipo, forma y oficio con los catálogos mudados…»; `tests_js/maqueta_datos.test.js` «f040 R57:
sin bloque volcado; tipos, formas y oficios mudados a incidencias.catalogos»; `tests/test_f040_front.py` R57 (las dos
tarjetas, ×2, y sin el recuadro de F-040). Y F-040 a `done` en `features.json` antes de tocar la maqueta:

```
$ python -m pytest tests/test_f035_placeholders_vivos.py -q
FAILED test_f035_r28_ninguna_ficha_done_deja_restos_en_la_maqueta
FAILED test_f035_r28_la_guardia_mira_una_ficha_que_pasa_a_done
FAILED test_f035_r28_el_escaner_cuenta_el_recuadro_en_construccion_de_una_ficha
E         F-040 está done y deja index.html:461   (y :481, :484, :487)
E         F-040 está done y deja js/portal.js:165  (y :172, :179)
E         F-040 está done y deja js/maqueta_datos.js:632
3 failed, 16 passed
$ node --test --test-name-pattern="f040 R57" services/postventa-front/tests_js/portal.test.js services/postventa-front/tests_js/maqueta_datos.test.js
  AssertionError [ERR_ASSERTION]: el bloque volcado (F-040) sale con su cierre
  AssertionError [ERR_ASSERTION]: bandeja.verVolcado sigue en PLACEHOLDERS
  AssertionError [ERR_ASSERTION]: estadoVolcado era del panel de ejemplo
$ python -m pytest services/postventa-front/tests/test_f040_front.py -q -k r57
E  AssertionError: #/inicio: la tarjeta no dice «volcar a Sigrid lo aprobado»
E  assert 'volcar a Sigrid lo aprobado' in '02 En producción Bandeja de revisión Lo importado, … con su historial. …'
E  AssertionError: #/bandeja: la tarjeta no dice «volcar a Sigrid lo aprobado»
E  assert 'data-en-construccion="F-040"' not in '<!-- servic…'
```

### T6 · GREEN (`a0c15a8`)

| Fichero | Qué |
|---|---|
| `index.html` | Fuera el recuadro `data-en-construccion="F-040"` (panel de ejemplo, 3 botones, resultados, pendientes). [D-4] sin enlace nuevo; las tarjetas «Revisar la bandeja» (`#/bandeja`) y 02 «Bandeja de revisión» (inicio, sigue «En producción») acaban en «, y volcar a Sigrid lo aprobado.» |
| `js/maqueta_datos.js` | Fuera el bloque `volcado`; `tipos`, `formas`, `oficios` **mudados** a `incidencias.catalogos` (F-041). `estados` y `motivos` se van (solo servían al panel). La fila «Volcado a Sigrid» del datamart (F-048) se queda |
| `js/portal.js` | Fuera `bandeja.verVolcado`, `bandeja.volcar`, `bandeja.reintentarVolcado`, `CLAVE_RESUMEN_VOLCADO`, `resumenVolcado`, `etiquetaEstadoVolcado` y `"F-040"` de `TITULOS_FICHAS` (la sección `bandeja` sigue `parcial`, por F-039 y F-043) |
| `js/portal_app.js` | `catalogos` = `datos.incidencias.catalogos`; fuera `estadoVolcado` y `resumenVolcado` |
| `css/portal.css` y las 5 páginas | Fuera `.rs-contadores` y `.rs-provisional`, que la guardia H-5 da por muertas sin el panel; `?v=` nueva (`0e5cdd88d0`) en las cinco, como pide T21 de F-035 |
| README del front, `docs/ARCHITECTURE.md` | El cierre contado; el recuadro de F-040, fuera de la lista de los de bloque |

Tests que solo servían al panel de ejemplo, quitados o ajustados, cada uno con su «Cierre de F-040 (R57)» en el
fichero: `maqueta_datos.test.js` (`BLOQUES` sin `volcado`; R24 sin las obras del dry-run; R26 sin los 3 pendientes del
alta; R39 lee `incidencias.catalogos`; fuera los 5 de R40 y `ETIQUETAS_VOLCADO`/`MOTIVOS_CONTRATO`); `portal.test.js`
(3 filas de `PLACEHOLDERS_ESPERADOS`; fuera «f035 R8: el volcado explica…» y los 4 de R40; R12 sin
`reintentarVolcado`; R57 con los 5 estados de conest y sin `p.estado`); `f035_paginas.test.js` (R65 sin F-040);
`test_f035_portal.py` (fuera el de los chips «Simulación»/«Hecho en Sigrid»; `CHIPS_DE_ESTADO` 4→3,
`CHIPS_DE_FICHA` 8→6); `test_f035_paginas.py` (`ENVOLTORIOS_DE_BLOQUE` sin F-040; recuadros 9→8).

Decisiones (para el reviewer): **adónde se mudan los catálogos** (el diseño no lo dice): a `incidencias` (F-041), la
ficha que edita esos campos; todo bloque de `MaquetaDatos` necesita una ficha no `done` (R23), así que no podían ir
sueltos. **No se tocan** (fuera de la lista de §4, y la guardia no los cuenta como restos): la nota «la forma exacta la
fija F-040» de `MaquetaDatos.incidencias.campos`, «(la forma exacta la fija el volcado)» de `index.html` (bloque de
F-039) y las reglas `[data-estado="previsto"…]` de `css/portal.css` (como las de revisión que dejó F-038).
**`css/portal.css` y el `?v=` de las cinco páginas** no están en la lista de §5: los exige la guardia H-5 al quitar el
panel, igual que en el cierre de F-038.

Verificación sobre `a0c15a8` (comandos del encargo):

```
$ python -m pytest tests/test_f035_placeholders_vivos.py services/postventa-front/tests     941 passed, 7 skipped in 16.28s
$ node --test services/postventa-front/tests_js        ℹ tests 1  ℹ fail 1  (Cannot find module …\tests_js: Node v24.14.1
                                                       no acepta un directorio; igual en la base, ver Bloque 1 bis)
$ cd services/postventa-front && node --test "tests_js/*.test.js"   ℹ tests 1144  ℹ pass 1144  ℹ fail 0  (6,1 s)
```

Finales de línea: el front de este worktree está ya en LF (`git ls-files --eol`: `w/lf` en todo lo tocado), así que
BN12 pasa. `docs/ARCHITECTURE.md` y `docs/INTEGRACION.md` estaban en CRLF en el worktree: se re-sacaron en LF
(`rm` + `git -c core.autocrlf=false checkout`) antes de editarlos; índice y worktree, LF.

### T6 bis (R58)

- `docs/INTEGRACION.md`: las frases de F-040 en futuro (l. 145, 212, 599, 652, 1952, 2072, 2074, 2075, 2076) dicen ya
  que el panel existe y vuelca por las rutas de F-059 (y «Registrar» usa la de F-065). La l. 160 («candidato al
  volcado de F-040») y la 1987 («la página … es F-040») ya estaban en presente.
- `azure-apps`: `git pull --rebase` («Current branch main is up to date», sin conflicto); solo
  `postventa_incidencias.md`, con las mismas frases que `INTEGRACION.md` (la copia dice `sigrid_api.md` donde el
  origen dice `azure-apps/sigrid_api.md`) y una línea en la cabecera: refrescada el 2026-11-24 con el cierre de F-040,
  consume las rutas de F-059 y la de F-065, nada nuevo fuera del proyecto. Commit `be26951` en `main`. **Sin push**;
  ojo: `main` queda 2 por delante de `origin` (el otro es `64f8ace`, de `dedicacion`, ajeno y anterior).
- Comprobación con los tests de documentación del API, que comparan la copia con el origen
  (`test_f065_c4_c6_las_filas_de_la_copia_son_las_de_integracion`): `.venv/Scripts/python.exe -m pytest tests -k
  "documentacion or integracion or identificadores or secretos or arquitectura"` → con solo `INTEGRACION.md` editado,
  2 failed (las filas «El volcado a Sigrid» y «Las reclamaciones…», justo lo que se refresca); con la copia al día,
  **1037 passed, 23 skipped**.
- Sin secretos, GUID, IP, host del SWA ni datos personales en ninguno de los dos documentos.

### `bash harness/init.sh`

En el worktree, sobre `8dbb559` (con este informe aún sin commitear), **exit 0, en verde**:

```
[OK] pytest en verde (con medición de cobertura)          2202 passed, 48 skipped in 956.30s
[OK] servicio api: pytest en verde (caché)                1604 passed, 77 skipped
[OK] servicio front: pytest en verde                      922 passed, 7 skipped in 27.02s
[OK] PUERTA COBERTURA: N/A (F-040 no cambia líneas Python de producción frente a dev)
[AVISO] PUERTA TAMAÑO: N/A (no hay papeleo abierto que medir: … ninguna activa)
[OK] PUERTA CARRIL: N/A (F-040 está cerrada)
[OK] CAPA E2E: N/A (sin feature en curso)
[AVISO] F-040 está done sin ok_humano: anota en harness/features.json el día en que el humano dio el OK al resumen
```
El aviso de `ok_humano` es del líder (PARADA 2). `BACKLOG.md`, regenerado por `init.sh`, va en el commit del informe.

### Evidencias (T6 y T6 bis)

| Evidencia | Valor |
|---|---|
| Tests JS del front | 1144/1144 (antes 1154: −13 del panel de ejemplo, +3 R57) |
| pytest del front + guardia de la raíz | 941 passed, 7 skipped (−1 del panel, +3 R57) |
| Cobertura de líneas cambiadas | N/A: ningún `.py` de producción tocado; ver `PUERTA COBERTURA` arriba |
| Mutantes | No lanzada: es de la pasada de campaña del líder, y el cambio es solo JS/HTML/CSS (la herramienta muta Python). Lo central de R57 lo fija la guardia de la raíz (R28), con sus controles |
| Tiempo de la suite | JS 6,1 s; pytest del front 16,3 s |
| Capa e2e | R57 y R58 son `unit`: N/A |

### Pendiente

- Review corta de T6 (si falla, se revierte `a0c15a8` entero) y T7 (líder). Push de la rama y de `azure-apps`
  (`pull` y después `push`), del humano. T5 bis sigue aparte (P-3).
