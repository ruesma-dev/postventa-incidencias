<!-- specs/F-040-volcado-sigrid/tasks.md -->
# F-040 · Volcar a Sigrid las incidencias aprobadas (el panel de volcado) — Tareas

> Aprobado el 2026-10-07; conciliado el 2026-10-27/28 (C-1..C-6) y el 2026-10-31 con F-065 (P-1..P-3). Solo
> `services/postventa-front` y documentos; **no se toca `services/postventa-api/`** (F-059, F-065, F-072).
> **Puesta al día del 2026-11-18** (spec-author, base `4b1eb21`): una tarea por línea; lo hecho se conserva con su
> evidencia condensada (texto anterior: `git show 4b1eb21:specs/F-040-volcado-sigrid/tasks.md`); nuevo el
> **Bloque 1 bis** (tipo de F-072, textos de su Q-11, miga) y T12; T5 partida en T5.1–T5.6. Orden al retomar
> (D-5, recomendado): T8 → T9–T11 → review → T12 → T5.3–T5.6 → T6 → T6 bis → T7; T5 bis cuando el humano registre la
> 0677 (el cierre no la espera, P-3). Las decisiones abiertas D-1..D-8 están en `design.md` §12.
> Rigor **`critico`**: RED con traza en el informe; cobertura N/A con motivo (sin `.py` de producción); mutación a
> mano por familias, cada mutante con su test asesino. Un commit por tarea (`F-040 Tn: …`). **Un bloque por encargo,
> y parar.** Datos ficticios en tests: obras `99NN`, correos `@ejemplo.invalid`, proveedores `EJnn`, tipos `9001`….
> **Nada contra Sigrid desde local ni desde tests**: lo que escribe (T5.3, T5.4) se hace en el entorno desplegado,
> con ensayo previo y la confirmación explícita del humano.

## Bloque 0 · La base

- [x] **T0**: la rama trae `dev` con F-065 (`f97ec6e`) y la spec se concilia con su contrato implementado; P-1..P-3 respondidas el 2026-10-31. | Verificación: `bash harness/init.sh` en verde sobre el merge (líder)

## Bloque 1 · El panel de volcado (hecho, APPROVED tras C-B1-1 y C-B1-2)

- [x] **T1 · RED**: `tests_js/volcado.test.js`, los cuatro endpoints nuevos en `tests_js/api.test.js` (20 → 24, sin reintento) y `tests/test_f040_front.py`; traza en `progress/impl_F-040.md`. | Verificación: `python -m pytest services/postventa-front/tests/test_f040_front.py services/postventa-front/tests/test_f007_js.py` falla
- [x] **T2 · GREEN**: `js/volcado.js`, el panel en `bandeja.html`, las cuatro funciones de `js/api.js`, la composición en `js/revision.js`, README del front y `docs/ARCHITECTURE.md`; tests de F-036/F-038 citados. | Verificación: `python -m pytest services/postventa-front/tests` y `node --test services/postventa-front/tests_js`
- [x] **T3 · Mutación** a mano por familias: 82 mutantes, 1 vivo (V3) equivalente, aceptado por el humano. | Verificación: `progress/mutacion_F-040.md`

## Bloque 1 bis · El tipo de reclamación, los textos de Q-11 y la miga (2026-11-18)

- [x] **T8 · líder** (2026-11-19): con D-1..D-8 decididas (escritas en «Decidido» de `design.md` §12), anotar la base fija `4b1eb21` y aplicar D-8 a los informes de `progress/`. | Verificación: `python -m harness.tamano --feature F-040` sale con 0
- [x] **T9 · RED**: tests de R63–R68 (`design.md` §7: tipo con etiqueta y código desconocido, recuento por tipo [D-2], textos de `tipo_no_valido` y `tipo_fuera_de_sigrid` [D-1], diez motivos, `opcionesDeListado` sin `option value=""` [D-3], migas con la actual como `span`) y las aserciones de F-038 que cambian (`tests_js/revision.test.js`, `tests_js/volcado.test.js`, `tests/test_f038_front.py`), citadas con el R que las sustituye; traza pegada. | Verificación: `node --test services/postventa-front/tests_js` y `python -m pytest services/postventa-front/tests` fallan solo en esos tests
- [ ] **T10 · GREEN**: `js/volcado.js` (fuera `TEXTO_TIPO`, tipo por `catalogo.listados`, `recuentoPorTipo`), `js/revision.js` y `bandeja.html` según `design.md` §3.4, y README del front y `docs/ARCHITECTURE.md` con el tipo (R63) y sin «sin publicar todavía». | Verificación: `node --test services/postventa-front/tests_js` y `python -m pytest services/postventa-front/tests tests/test_f035_placeholders_vivos.py` en verde
- [ ] **T11 · Mutación** a mano por familias de lo cambiado en T10 (etiqueta del tipo y su respaldo, recuento por tipo con uno y dos tipos, orden de los motivos, opción del tipo no vigente, migas). | Verificación: `progress/mutacion_F-040_bloque1bis.md` con cada mutante y su test asesino; ninguno vivo sin aceptación escrita del humano

**Parar. Review del Bloque 1 bis.**

## Bloque 2 · Publicar y verificar el panel (MANUAL, humano)

- [x] **T4 · MANUAL (humano)**: merge del Bloque 1 a `dev` (`b9a66db`) y front publicado con `-SoloFront` desde una copia limpia el 2026-11-02; ventana cerrada. | Verificación: MANUAL (humano)
- [ ] **T12 · MANUAL (humano)**: merge del Bloque 1 bis a `dev` (líder, worktree aparte, `init.sh` en verde) y publicar el front desde una copia limpia: `git worktree add --detach ..\postventa-publicar dev`, `powershell -ExecutionPolicy Bypass -File ..\postventa-publicar\infra\desplegar_front.ps1 -SoloFront`, `git worktree remove ..\postventa-publicar`; después `infra\27_ventana_volcado.ps1` sin parámetros dice `cerrada`. | Verificación: MANUAL (humano)
- [x] **T5.1** (0626, solo lectura, 2026-11-02): el panel cuadra con `GET /api/volcado?obra=0626` (aprobadas 1, volcadas 1, «1 candidata, en 1 trozo de 5»). | Verificación: MANUAL (humano), en `progress/impl_F-040.md`
- [x] **T5.2** (2026-11-02): «Registrar» hace una sola lectura de `revision/sigrid` y ninguna de `volcado/ensayo`; la fila «PRUEBA F-040 - ANULAR» sale en **choca** con `RS26.09/0439`; con su casilla, un ensayo 200 con «Se crearía 1» y la cuenta atrás. | Verificación: MANUAL (humano), en `progress/impl_F-040.md`
- [ ] **T5.3 · MANUAL (humano)**, 0626, con el front de T12 y la ventana **cerrada** (`27_` sin parámetros): «Registrar», casilla de la fila de prueba, ensayo (la columna Tipo con su etiqueta, R63) y confirmar con el número (texto con el recuento por unidad): 503 `volcado_deshabilitado`, el panel para, dice que la ventana está cerrada y no reintenta (en Red, **una** petición a `volcado/volcar`); foto `powershell -ExecutionPolicy Bypass -File infra\28_volcado_lectura_sigrid.ps1 -CodigoObra 0626` sin cambios. El clic de confirmar lo hace **el humano**. | Verificación: MANUAL (humano)
- [ ] **T5.4 · MANUAL (humano)**, la **única escritura real**, con **autorización expresa en el chat para esa escritura** (R69): [D-6] editar la fila de prueba a `0003` POST VENTA y volver a aprobarla; un ensayo de calentamiento; `infra\27_ventana_volcado.ps1 -Abrir`; «Volver a registrar», casilla, ensayo (`envio.tipo` `0003`) y volcar desde la página → la fila «Volcada como RS…» y el aviso de PTE (R59); **enseguida** `27_ -Cerrar`; foto `28_ -CodigoObra 0626 -Referencia PVI-<id>`: **un** parte, en SAT, tipo `0003`; **no se pasa a PTE**; un «Registrar» más, sin ensayar: ya no es candidata. | Verificación: MANUAL (humano)
- [ ] **T5.5 · MANUAL (humano)**: tras T5.4, sin `oid` ni correo en `console` ni en el almacenamiento (la parte de antes, hecha el 2026-11-02). | Verificación: MANUAL (humano)
- [ ] **T5.6 · MANUAL (humano)**, salga bien o mal: ventana cerrada; el parte de prueba se **anula desde la UI de Sigrid** (NO PROCEDE, sin correo), nunca con `DELETE` ni `sql/write`; foto `28_` en `NPR`; la fila queda `volcada`. Si algo falla en T5.3–T5.6, parar y volver al spec-author. | Verificación: MANUAL (humano)
- [ ] **T5 bis · MANUAL (humano)**, la T-A18 de F-065 (P-3: aparte, en la 0677, **solo ensayos**, con autorización del humano en ese momento; se anota cuando empiece a registrar la 0677 y el cierre no la espera): (1) [D-7] un `choca` ensayado sin confirmar (por la API del front con la sesión del humano) sale excluido `conflicto_sin_confirmar` con su `sigrid_cod`; (2) con su casilla, `previsto` y `confirmada: true` en el bloque `sigrid`; (3) en Application Insights, la línea `F-065 guarda del ensayo` con sus recuentos y `segundos` y la de conflicto confirmado con `codigos=` un número, sin códigos `RS` ni texto; (4) no se vuelca (C-2). | Verificación: MANUAL (humano); solo motivos, estados, recuentos y segundos en `progress/`

## Bloque 3 · El cierre de la ficha

- [x] **T6a** (adelantada, 2026-11-04): pestañas, pasos 02 y 03 y tarjeta de la portada a `bandeja.html` en las cuatro barras; publicada el 2026-11-05 (`ed935ad`); M4 y M5 aceptados. | Verificación: `node --test services/postventa-front/tests_js` y `python -m pytest tests/test_f035_placeholders_vivos.py services/postventa-front/tests`
- [ ] **T6**: por encargo del líder, tras T5.3–T5.6 y el APROBADO del Bloque 1 bis (F-038 ya `done`), **un solo commit** con el cierre de R57 (`design.md` §4: restos de F-040 fuera de la maqueta, catálogos mudados, [D-4] sin enlace nuevo y los textos de las dos tarjetas, la tarjeta 02 sigue «En producción») **y** F-040 `done` en `harness/features.json`; review corta; si falla, se revierte entero. | Verificación: `python -m pytest tests/test_f035_placeholders_vivos.py services/postventa-front/tests` y `node --test services/postventa-front/tests_js` en verde sobre ese commit
- [ ] **T6 bis**: R58 — en la rama, `docs/INTEGRACION.md` sin F-040 en futuro (`design.md` §5); en `azure-apps`, `git pull --rebase`, lo mismo en `postventa_incidencias.md` (el panel existe; consume las rutas de F-059 y la de F-065, sin nada nuevo fuera del proyecto) en un commit aparte; ante un conflicto, parar; el push es del humano. | Verificación: `git -C ..\azure-apps log -1` con el commit y ninguna frase de F-040 en futuro en los dos documentos
- [ ] **T7**: resumen de F-040 en `progress/history.md` (el líder) y `bash harness/init.sh` en verde. | Verificación: `bash harness/init.sh`
