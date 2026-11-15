<!-- progress/review_F-072_bloque1.md -->
Revisión incremental desde d52a89f (pasada 2): delta `d52a89f..3575aa0`. La pasada 1 revisó `6994cb0..d52a89f` entera, sin el merge `299f21c`.

# F-072 · Review del Bloque 1 (dominio: tipos, tipo efectivo, huella y parte)

- **Veredicto: APROBADO** (APPROVED) en `3575aa0`, condicionado a que el `init.sh` del líder
  salga verde. Pasada 1: CAMBIOS en `d52a89f`, por dos mutantes vivos que la reducción «uno por
  línea» había dejado fuera.
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura
  (90 %) y mutación con cero supervivientes salvo justificación escrita aceptada por el humano.

## Pasada 2 · verificación de `3575aa0`

- El delta solo toca tests y `progress/impl_F-072.md`: `test_f072_dominio_tipos.py` (añade `""`
  al `parametrize` de R19 y `test_f072_r26_un_tipo_vacio_no_es_el_nulo_y_va_al_final`) y el
  comentario de `test_f060_normalizacion_dominio.py:486`, ya preciso. No cambia ningún fichero de
  producción, así que el alcance de la campaña sigue igual (RM1) y no hace falta repetirla.
- Reproducido sobre una copia limpia de `3575aa0` en el scratchpad (`git archive`), con los tests
  del bloque (base: 699 passed). Los dos mutantes vivos **mueren**: `579` `not codigo` (1 rojo) y
  `826` veracidad (1 rojo). Mi variante `append(... or '0002')` también muere (1 rojo). Los otros
  8 mutantes a mano siguen muertos.
- La tabla antes/después del informe del implementer cuadra con lo que he medido.
- Árbol de trabajo: el comando de T2 más los dos de F-060 dan `727 passed`.
- Detalle de estilo, no bloqueante: antes de la `def` nueva (línea ~251) hay una sola línea en
  blanco y PEP 8 pide dos. `ruff` no está instalado en el `.venv`, así que no lo he podido pasar.
  Las reglas por defecto de ruff no incluyen E302.

## Pasada 1 (resumen)

**R26 (huella) — se cumple, verificado de forma independiente.** Extraje `domain/` de `6994cb0`
(`git archive`) y calculé `huella_de_valores` con el código de la base (13 campos): da
`9eb4374f…8228f6` y `fe6ba32f…c7e871`, los literales del test; y una tercera foto mía
(`listado=SEGUNDO`, `urgencia=None`) da la misma huella con la base y con HEAD
(`c7824857…d607c`). Con tipo nulo la lista es idéntica a la de F-056; con tipo, el código va al
final (`test_f072_r26_con_tipo_el_codigo_va_al_final_de_la_lista`). Las aprobadas antes de F-072
conservan la huella y `huella_intacta` las sigue dando por intactas.

**Aserción de F-060 de 12 a 13 — justificada, no debilita.** El recuento es un «cable trampa»
que obliga a repensar el test cuando la foto crece; R26 dice que la foto de F-056 tenía 13
valores y ahora son 14, así que «los demás salvo `ubicacion`» son 13. Lo fuerte del test (cada
campo se copia y solo cambia `ubicacion`, `== replace(vigentes, …)`) queda igual. Único reparo,
no bloqueante: el comentario dice que el test «cubre también la copia de `tipo_reclamacion`
(R23)», pero la fixture lleva el tipo nulo, así que copiar y no copiar dan lo mismo. La copia es
estructural (`revision_de_normalizacion` usa `replace`) y R23 tiene sus tests en el Bloque 2
(T4), que deben usar un tipo **no nulo**.

**Alcance (R31/R32) y secretos — limpio.** Fuera de `specs/`, `progress/`, `BACKLOG.md` y
`features.json` (estado `in_progress` y `spec_aprobada`), el diff solo toca los tres ficheros de
dominio previstos en T2, la aserción de F-060 y los dos tests nuevos. `conftest.py` y
`test_f059_volcado_http.py` son idénticos a `dev` `05c8a5a` (llegan por el merge). Nada en
`postventa-front/`, `infrastructure/`, `application/`, `function_app.py`, SQL, `config/`, `.env`
ni `.xlsx`; `rigor.local.json` sin tocar. Sin URLs, IPs, claves ni correos. Datos ficticios
(`9901`, `9001…`, «TIPO FICTICIO N»); la fixture `0046`/`EJ07` ya estaba en tests de F-036.

**Campaña de mutación — la medición es válida; el hueco no es del generador, es de la reducción.**
- Recálculo puro (`alcance_de_feature("F-072", base="6994cb0")` + `generar_mutantes`):
  3 ficheros, 93 líneas, 7 mutantes (4/3/0). Coincide con el informe.
- Prueba de control de `volcado.py` (0 mutantes): sobre el fichero entero el generador da **139**,
  así que funciona; las 16 líneas en alcance son docstrings, el import, el alias y la llamada a
  `tipo_efectivo`, que ningún operador sabe mutar. El cero es legítimo. Reproduje al pie de la
  letra las dos filas del control a mano del implementer: `tipo=TIPO_RECLAMACION` → 7 rojos;
  alias `"0003"` → 2 rojos. Cuadran.
- Los 5 evaluados, reproducidos sobre una copia en el scratchpad (RM4, tests del bloque, 697):
  24→25 (1 rojo), `frozen=False` (3), `is not None` en 579 (20), `!=` en 822 (21), `is None` en
  826 (5). Muertos de verdad.
- Los 2 que la regla «uno por línea» descartó son los de **veracidad**, y **sobreviven**:
  - `plantilla_incidencias.py:579` `if codigo is None` → `if not codigo`: 697 passed.
  - `revision.py:826` `if valores.tipo_reclamacion is not None:` → `if valores.tipo_reclamacion:`:
    697 passed.
  Ningún otro test del repo menciona `tipo_reclamacion` ni `tipo_efectivo` (grep sobre `tests/`
  y `tests_bbdd/`), así que también sobreviven a la suite entera. Los dos solo se distinguen con
  el código `""`: el contrato escrito dice que debe salir tal cual (`design.md` §4.1 «cualquier otro
  valor, tal cual»; docstring de `huella_de_valores`: «`null` no es `""`»; R26 «solo si no es
  nulo»), pero ningún test lo fija.
- Mis mutantes a mano para compensar lo que el generador no sabe hacer (quitar sentencias,
  cambiar llamadas o literales de texto) **mueren todos**: quitar el `continue` (3 rojos), el tipo
  al principio de la lista (1), defecto `"0003"` (15), nombre sin recortar (4), orden invertido (1)
  y `listas_con_tipos` sin sustituir (3). Uno más de la misma familia de `""` sobrevive:
  `append(valores.tipo_reclamacion or '0002')`. Lo mata el mismo test que el punto 2 de abajo.

## Checkpoints

- C1 `[x]` condicionado: `init.sh` lo ejecuta el líder en paralelo (orden del encargo); no lo he
  corrido. Los tests del bloque en el árbol de trabajo: `725 passed in 6.35s` (comando de T2 más
  los dos de F-060). **Si el `init.sh` del líder no sale verde, el veredicto es CAMBIOS igual.**
- C2 `[x]` una feature activa, rama `feature/F-072-tipo-reclamacion-sigrid`. `git status` limpio
  salvo `progress/mutacion_F-072_bloque1.json`, el estado de la campaña, sin versionar como los de antes.
- C3 `[x]` hexagonal: `volcado.py` importa de `plantilla_incidencias.py` (dominio a dominio);
  ruta en la primera línea; sin `print`; sin secretos. Puntos de partes/firmas/Sigrid: N/A, el
  bloque es dominio puro y no escanea, archiva ni escribe en Sigrid.
- C3 bis, C3 ter: N/A, no entra ningún documento ni acta. C3 quater: N/A en este bloque
  (`azure-apps` va en T25).
- C4 `[x]` R6, R7, R19, R26, R28 con test (tabla abajo); sin red, base ni IA; MANUAL de la
  feature en T13/T24/T26, fuera del bloque. Sin dobles nuevos.
- C4 bis:
  - `[x]` rigor declarado.
  - `[x]` fase RED con trazas reales: dos `ImportError` y el `TypeError` de la foto.
  - Cobertura: pendiente del `init.sh` del líder (`PUERTA COBERTURA`), sin medir en el informe.
  - `[x]` informe generado por la herramienta, totales verificados.
  - `[x]` RM1: medido en `0049d76`; de ahí a HEAD solo cambia `progress/`.
  - `[x]` RM2: media 797,8 s = 3989,2 / 5; con línea base de 1293–1364 s y `-x`, coherente.
  - `[x]` RM3: ninguno de los 5 muertos es equivalente.
  - RM5, RM6: N/A, no hay equivalentes declarados ni guardas quitadas.
  - RM7: N/A, ningún requisito del bloque protege un orden entre colaboradores.
  - Campaña no reejecutada: 66 min según el informe (más de 60 s); sustituida por el recálculo
    puro y la reproducción de los 5.
  - `[x]` cero supervivientes en `critico`. En la pasada 1 era `[ ]`: dos mutantes a mano
    sobrevivían. En `3575aa0` mueren los dos.
  - `[x]` «Evidencias» presente, capa e2e N/A justificada (dominio puro).
- C4 ter: N/A, no hay rutas sensibles en el diff del bloque.
- C5: T3 sin marcar, como manda el encargo (la marca el líder tras esta review). Sin temporales.

## Cobertura requisito → test

| Req | Tests |
|---|---|
| R6 | `test_f072_r6_*` (etiqueta, sin nombre, en blanco, recortado, orden, iterable, `listas_con_tipos`) |
| R7 | `test_f072_r7_sin_tipos_no_hay_opciones`, `…_listas_con_tipos_sin_tipos_deja_listados_vacio` |
| R16 (tope) | `test_f072_r16_el_tope_del_codigo_es_24` |
| R19 | `test_f072_r19_*` (nulo → 0002, guardado tal cual, el listado heredado no cuenta) |
| R26 | `test_f072_r26_*` en los dos ficheros (literal de la base, código al final, `0002` explícito ≠ nulo, intacta) |
| R28 | `test_f072_r28_*` (parte, cuerpo, lote, nulo → 0002 con cualquier listado, alias) |

## Cambios requeridos en la pasada 1 (los tres hechos en `3575aa0` y verificados)

1. `test_f072_dominio_tipos.py`, en el `parametrize` de R19: añadir `""`, porque `tipo_efectivo("")`
   devuelve `""` (§4.1). Mata `plantilla_incidencias.py:579`.
2. Mismo fichero, en R26: un test con `tipo_reclamacion=""` cuya huella difiera de `HUELLA_6994CB0` y
   lleve `""` al final de la lista. Mata `revision.py:826`.
3. En `impl_F-072.md`, la reproducción de los dos mutantes antes y después del cambio. Sin campaña
   nueva: solo cambian tests (RM1), y la campaña de T22 los vuelve a medir.

Además, la observación sobre el comentario de `test_f060_normalizacion_dominio.py:486` (la fixture no
ejerce la copia de un tipo no nulo) quedó resuelta en el mismo commit.

## Automejora (propuesta, no aplicada)

En `critico`, «uno por línea» recorta aunque haya pocos mutantes: aquí dejó 7 en 5, por debajo del
suelo de 100, y los 2 descartados eran justo los vivos. Para `arnes-base`: si los generados no pasan
del suelo, evaluarlos todos. Mientras tanto, en C4 bis, el reviewer reproduce a mano los descartados.
