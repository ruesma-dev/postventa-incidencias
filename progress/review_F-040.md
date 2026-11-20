<!-- progress/review_F-040.md -->
# F-040 · Reviews (desde el 2026-11-19)

Las reviews del Bloque 1, T4 y T6a (hasta el 2026-11-05, veredicto final
APPROVED) están en `progress/review_F-040_bloque1.md`, renombrado con `git mv`
por la decisión D-8 (`specs/F-040-volcado-sigrid/design.md` §12): pasaba de la
puerta TAMAÑO (457/140).

## Bloque 1 bis (T9–T11)

Revisión incremental desde be97272 (T8 del líder; base fija 4b1eb21), commits `d1a0e5d` T9, `288ee16` T10, `fc7f986` T11.
Reviewer, 2026-11-20.

**Veredicto: APROBADO.**

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige RED con salida real, cobertura (N/A por
lenguaje, abajo), mutación con cero supervivientes sin aceptación escrita y las reglas RM1–RM7.

### C1 · `ARNES_SIN_CACHE=1 bash harness/init.sh` en el worktree `postventa-f040`, sobre `fc7f986`

Exit 0, «ENTORNO LISTO». Raíz 2202 passed / 48 skipped (24 min 58 s); API 10365 passed / 485 skipped (43 min, sin
caché); front 920 passed / 7 skipped (46,7 s; incluye `test_f007_js`, la suite JS entera: BN12 de F-038 en verde
ahora que el front está en LF). `PUERTA COBERTURA: N/A (F-040 no cambia líneas Python de producción frente a dev)`;
`PUERTA TAMAÑO` dentro de los topes; `CAPA E2E: N/A`. Avisos: ruff 112 (deuda previa) y el de `spec_aprobada` (obs. 1).

### Trazabilidad R63–R68 → código → test

| R | Código (T10) | Tests (y mutantes que he matado yo) |
|---|---|---|
| R63 | `volcado.js` `nombreDeTipo` (etiqueta de `catalogo.listados`, si no el código; sin código `""`), fila con `tipo` y `tipo_codigo`; `TEXTO_TIPO` fuera | `f040_tipo.test.js` «R63» ×5 (incl. 2 de T11) y `volcado.test.js` R51 enmendados. `grep TEXTO_TIPO`: solo `TEXTO_TIPO_PENDIENTE` de `portal.js`, ajeno |
| R64 [D-2] | `recuentoPorTipo` (solo `previsto`), `textoPorTipo` (vacío con < 2), `textoConfirmacion(..., porTipo)` solo con > 1, `volcadoPorTipo()`; `<p x-show x-text="volcadoPorTipo()">` | `f040_tipo` «R64» ×6; `test_f040_r64_el_resumen_del_ensayo…` |
| R65 [D-1] | `TEXTO_MOTIVO_VOLCADO.tipo_no_valido` con el literal exacto de R65 | `f040_tipo` «R65» ×2 (no suma a N ni a `porTipo`); `TEXTOS_DE_PARTE` |
| R66 [D-1] | `MOTIVOS` con `tipo_fuera_de_sigrid` entre `proveedor_ambiguo` y `duplicada`; texto exacto de R66 | `f040_tipo` «R66» ×2; `revision.test.js` R4 (a) y R5 |
| R67 [D-1, D-3] | `opcionesDeListado(catalogo, actual)`; `opciones().listados` con `f.vigentes.listado`; `textoDeCampo("listado")` = etiqueta o código; rótulo «Listado (tipo de reclamación)»; fuera `<option value="">Sin listado</option>` | `f040_tipo` «R67» ×4; `test_f040_r67_…` ×2 |
| R68 | Miga `<span aria-current="page">Bandeja de revisión</span>` | `test_f040_r68_…` + 3 controles no ciegos |
| R58 (parte de T10) | README del front y `ARCHITECTURE.md`: «publicado el 2026-11-02», el tipo (R63–R67) | `test_f040_r58_r63_…` ×2; `grep "sin publicar todavía"` en ambos: 0 |

Comprobaciones del encargo: literales D-1 idénticos a R65–R67 (letra a letra) ✔; recuento por tipo solo con > 1
tipo (D-2) ✔; en el campo del listado no queda `option value=""` y la opción del no vigente sale de
`opcionesDeListado` con «(ya no vigente en Sigrid)» (D-3) ✔ (los demás `value=""` de `bandeja.html`, l. 628–668,
son de unidad, ubicación, oficio, proveedor y urgencia, fuera de R67); ningún `href` nuevo en el diff (D-4) ✔;
miga como texto (R68) ✔; `TEXTO_TIPO` fuera ✔; README y ARCHITECTURE sin «sin publicar todavía» ✔. Las 8
aserciones de F-038/F-040 que cambian citan el R que las sustituye en el propio test (R66, R65, R63, R68) ✔.
«Historial»: `presentarHistorial` solo da nombres de campo, no valores; el valor del listado sale por `detalleDe`,
que es lo que fija el test ✔. Datos de test ficticios (obra 9901, VILLA 9N, OF01, EJ11, etiquetas «…EJEMPLO»,
tipo 9001); `grep` del diff añadido sin correos, DNI, obras reales ni secretos ✔.

**Alcance tocado:** `services/postventa-front/` (js, `bandeja.html`, README, tests), `docs/ARCHITECTURE.md` y, como
rastro del arnés, `progress/impl_F-040.md`, `progress/mutacion_F-040_bloque1bis.md` y las casillas T9–T11 de
`tasks.md`. Nada en `services/postventa-api/`, nada contra Sigrid ni producción ✔.

### Checkpoints

- C1 [x] init.sh sin caché en verde (arriba); ficheros base presentes.
- C2 [x] una sola activa (F-040 `in_progress`); rama `feature/F-040-volcado-sigrid`. Ver obs. 1 y 2 (del líder).
- C3 [x] primera línea con ruta en `f040_tipo.test.js` y en los tocados; sin `console.*`/`debugger`/TODO/`print`
  añadidos; sin secretos ni dependencias nuevas. Arquitectura: el front no añade rutas ni toca el backend. Los
  puntos de dominio de C3 (partes, firmas, Sigrid, `conest`) N/A: el bloque es presentación pura. Sin PDFs ni
  `muestras/` en el diff.
- C3 bis N/A: no entra ningún documento de fuera. C3 ter N/A: no se registra ninguna conversación.
- C3 quater N/A en este bloque: no cambia lo que se expone ni consume; `azure-apps` de R58 es T6 bis.
- C4 [x] suites ejecutadas por mí (init.sh); tests de cada R presentes y en verde.
- C4 bis:
  - [x] nivel declarado (`critico`).
  - [x] **RED real**: `d1a0e5d` solo trae tests (`git show --stat`); traza pegada en `impl_F-040.md` §T9. La he
    reproducido en una copia `git archive d1a0e5d`: `node --test tests_js/f040_tipo.test.js` → 17 tests, 16 fail,
    1 pass (la guarda «con un solo tipo, no cambia», que debe pasar antes y después).
  - [x] cobertura: N/A con motivo impreso por la puerta (sin `.py` de producción; justificado por el lenguaje).
  - [x] `harness.mutacion`: 0 mutantes legítimo. Recalculado con `alcance.parsear_diff(be97272...HEAD)`: los únicos
    `.py` son `tests/test_f038_front.py` (6 l.) y `tests/test_f040_front.py` (99 l.), `es_produccion` = False.
    Control: `generar_mutantes` sobre `test_f040_front.py` sin la exclusión da 50 → el generador funciona; el cero es
    por diseño (JS/HTML).
  - [x] campaña MANUAL con una fila por mutante y el texto exacto original → mutado (50 filas, 5 familias A–E = las
    5 de T11: etiqueta y respaldo, recuento con uno y dos tipos, orden de motivos, opción no vigente, migas). Falta
    la línea y el nº de fallos por fila (obs. 3); los suplo con mi muestreo.
  - [x] **muestreo de 8 mutantes en el worktree** (≥ 5 pedidos), cada uno sustitución única, suite JS entera
    (`node --test "tests_js/*.test.js"`) y, en D9 y E2, `pytest` de `test_f040_front.py` + `test_f038_front.py`;
    base 0 fallos en ambas; fichero restaurado byte a byte tras cada uno. **Todos muertos, y todos por un test
    de F-040**:

    | Mutante | Fallos | Test asesino de la feature |
    |---|---|---|
    | A1 `return String(codigo);` | node 5 | f040 R63 «sale con su etiqueta…», R64, R51 |
    | A6 sin `Array.isArray` | node 1 | f040 R63 (T11) «…no es una lista no rompe» |
    | B8 `tipos.length > 0` | node 3 | f040 R64 «con un solo tipo…no cambia», R52 D-12 |
    | B13 sin `vista.porTipo` | node 1 | f040 R64 «el componente pasa el recuento…» |
    | C3 `tipo_fuera_de_sigrid` antes de `proveedor_ambiguo` | node 3 | f040 R66 ×2, f038 R4 (a) [F-040 R66] |
    | D1 sin `actual &&` | node 2 | f040 R67 `opcionesDeListado` ×2 |
    | D9 `listados: catalogo.listados \|\| []` | node 1 + pytest 1 | f040 R67 «el formulario…», `test_f040_r67_opciones_listados…` |
    | E2 `<span>` sin `aria-current` | pytest 4 | `test_f040_r68_la_miga_actual…` (+ controles) |

    Al final, `git status --short` y `git diff --stat` vacíos.
  - [x] RM1: el código de producción medido es el de `288ee16`; `fc7f986` solo añade tests y documentos, así que el
    alcance medido es el revisado. RM2 N/A: la campaña a mano no declara tiempos de la herramienta.
  - [x] RM3: ningún equivalente declarado ni muerto sospechoso. RM5 N/A: 0 equivalentes. RM6 [x]: ningún mutante
    se mató quitando código defensivo; los 4 vivos de la 1.ª pasada (A5–A8) se cerraron con tests, no borrando
    guardas. RM7 N/A: ningún requisito del bloque protege un orden entre colaboradores.
  - [x] «Evidencias» con los cuatro números y la fila «Capa e2e» (R63–R68 son `unit`).
- C4 ter N/A: el bloque no toca rutas sensibles declaradas.
- C5 N/A para la feature entera (quedan T12, T5.3–T5.6, T6…); del bloque: T9–T11 `[x]` en `tasks.md`, un commit
  `F-040 Tn:` por tarea; sin temporales sin trackear.

### Observaciones (no bloquean)

1. **Del líder (T8):** `init.sh` avisa «F-040 tiene sdd: true y estado in_progress sin spec_aprobada»: falta
   `"spec_aprobada": "2026-11-19"` en la entrada de F-040 de `harness/features.json`.
2. **Del líder:** `progress/current.md` arrastra entradas de F-072 ya cerrada (C2 pide solo la sesión activa).
3. `progress/mutacion_F-040_bloque1bis.md` no trae la línea ni el nº de fallos de cada fila, como pide C4 bis para
   las campañas a mano; el texto exacto sí está y la he reproducido (arriba). Para T12 y siguientes, añadirlos.
4. Literal de R64: «…; por tipo, 2 X y 1 Y.» en vez del boceto «y n₁ X, n₂ Y» de `design.md` §2. R64 no fija el
   literal y el implementer lo justifica (evita una lista ambigua tras la de unidades). Aceptado; que el humano lo
   vea en la publicación (T12).
5. `textoPorTipo` y `textoConfirmacion` repiten el `t.n + " " + t.etiqueta`; deuda menor, no se pide cambio.

### Automejora (propuesta, no aplicada)

Ninguna nueva: la obs. 3 ya la cubre C4 bis; basta con exigirla.
