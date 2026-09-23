<!-- progress/mutacion_F-034.md -->
# F-034 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-034 --workers 8` el 2026-09-23 16:21.

## Alcance

Origen del diff: **rama** (`e2e5d7a8543f38389dc53e0551f684bce131fa36` .. `feature/F-034-archivo-persistido-en-erp`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/codigos_del_parte.py` | 254 |
| `services/postventa-api/application/pipelines/paso_archivo.py` | 32 |
| `services/postventa-api/application/pipelines/paso_cierre.py` | 111 |
| `services/postventa-api/application/pipelines/paso_grafico.py` | 108 |
| `services/postventa-api/application/pipelines/puerta_de_estado.py` | 62 |
| `services/postventa-api/domain/models/errores.py` | 53 |
| `services/postventa-api/function_app.py` | 20 |
| `services/postventa-api/interface_adapters/api/adjuntar.py` | 46 |
| `services/postventa-api/interface_adapters/api/archivar.py` | 4 |
| `services/postventa-api/interface_adapters/api/cerrar.py` | 48 |
| **Total** | **738** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 12 |
| Mutantes evaluados | 12 |
| Muertos | 12 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 359.8 s |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Nota del implementer · T15 (Bloque 6), la campaña de la feature entera

> Lanzada el 2026-09-23 con los Bloques 0–5 cerrados (T1–T14). Dos vueltas:
> la **1**, con un superviviente; la **2**, esta, con **cero**, tras un test
> nuevo que lo mata. El informe de arriba es el de la vuelta 2, generado por la
> herramienta sin retocar.

### Comando real y por qué lleva `--timeout`

```
python -m harness.mutacion --feature F-034 --base dev --workers 8 --timeout 600
```

La cabecera generada no enseña `--base dev` (es el valor por defecto) ni
`--timeout 600` (la herramienta no lo imprime). El `--timeout` se subió de 120
a 600 s **solo como margen**: la suite del servicio `api` tarda hoy **127 s**
en solitario (3.235 tests, medido al empezar este bloque), por encima de los
120 s de `rigor.json`, así que un superviviente —que ejecuta la suite
entera— habría salido `timeout` en vez de dar veredicto. No hizo falta en la
práctica: **0 timeouts** en las dos vueltas. `rigor.json` no se ha tocado
(ver «Para el líder» al final).

### Línea base verde antes de mutar (sin caché)

Antes de la vuelta 1, las tres suites reejecutadas a mano, sin caché de
pytest ni de `init.sh`:

| Suite | Comando | Resultado |
|---|---|---|
| api | `.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider` (en `services/postventa-api`) | **3235 passed, 18 skipped in 126.96s** |
| front, Python | `python -m pytest tests -q -p no:cacheprovider` (en `services/postventa-front`) | **256 passed in 5.97s** |
| front, JavaScript | `node --test "tests_js/*.test.js"` (Node v24.14.1) | **322 pass, 0 fail** (1,38 s) |

Los 18 saltados frente a los 28 de `init.sh` son la diferencia entre lanzar
`pytest tests` a mano y lanzarlo bajo `coverage` desde `init.sh`; ningún test
de F-034 se salta en la rama.

**Control contra muertes falsas.** La campaña paralela ejecuta la suite dentro
de `git worktree` desechables y **no** hace una pasada sin mutar: si algo de la
suite dependiera de ficheros no versionados, todo saldría «muerto» sin serlo
(`harness/mutacion_paralela.py`, «Limitaciones conocidas»). Se comprobó a mano:
worktree `--detach` de `HEAD` (`97ea9d3`) en el scratchpad, suite del servicio
con el intérprete del venv principal y los mismos flags que la campaña (`-x -q
-p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`):

```
3229 passed, 35 skipped in 122.43s (0:02:02)
```

Verde: las muertes de la campaña no son del entorno. (Más saltados porque se
lanzó `pytest` sobre la carpeta del servicio entera y, en un `HEAD` separado,
los controles de `diff` de los alcances se saltan, como tienen que hacer fuera
de su rama.) Worktree retirado al terminar.

### Vuelta 1 · 12 generados, 11 muertos, 1 superviviente (340,1 s, 8 workers)

El único superviviente:

- `services/postventa-api/application/pipelines/codigos_del_parte.py:185`
  [booleano] `strict=True,` → `strict=False,`

**Por qué ningún test lo cazaba.** Es el `zip(..., strict=True)` con el que
`exigir_codigos_declarados` empareja lo declarado con lo guardado. Las dos
listas salen de `_a_mirar` con el **mismo** `solo_incidencia`, así que hoy
tienen siempre el mismo largo (1 o 2) y el `strict` nunca se dispara: con el
código de hoy, el mutante es **equivalente**.

**Decisión: test nuevo, no mutante equivalente.** El `strict` no es
decoración: impide que el cotejo se dé por bueno **mirando menos códigos de
los que toca** si un día alguien toca `_a_mirar` o empareja otra cosa. Sin él,
`zip` se calla en la lista más corta y el código que se queda fuera no se
coteja: un nº de incidencia distinto pasaría el 1 bis sin 409 (R11). Es una
propiedad de «fallar cerrado» que merece test, y un test evita pedir al humano
que acepte una justificación (nivel `critico`).

Test nuevo (commit `97ea9d3`):
`tests/test_f034_codigos_en_el_erp.py::test_f034_r11_codigos_si_las_dos_listas_no_casan_falla_en_vez_de_cotejar_a_medias`.
Sustituye `_a_mirar` (con `monkeypatch`) por uno que, para lo declarado,
devuelve solo la obra, con una incidencia declarada distinta de la guardada, y
exige el `ValueError` de `zip`: que **no pase en silencio**.

RED del test contra el mutante (aplicado a mano en el árbol y deshecho con
`git checkout --` al terminar; `git status` limpio después), desde
`services/postventa-api`:

```
$ .venv/Scripts/python.exe -m pytest "tests/test_f034_codigos_en_el_erp.py::test_f034_r11_codigos_si_las_dos_listas_no_casan_falla_en_vez_de_cotejar_a_medias" -q -p no:cacheprovider --tb=short
F                                                                        [100%]
================================== FAILURES ===================================
_ test_f034_r11_codigos_si_las_dos_listas_no_casan_falla_en_vez_de_cotejar_a_medias _
tests\test_f034_codigos_en_el_erp.py:294: in test_f034_r11_codigos_si_las_dos_listas_no_casan_falla_en_vez_de_cotejar_a_medias
    with pytest.raises(ValueError, match="zip"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE ValueError
=========================== short test summary info ===========================
FAILED tests/test_f034_codigos_en_el_erp.py::test_f034_r11_codigos_si_las_dos_listas_no_casan_falla_en_vez_de_cotejar_a_medias
1 failed in 2.90s
```

Verde con el código de verdad, mismo comando: `1 passed in 2.01s`.

### Vuelta 2 · 12 generados, 12 muertos, 0 supervivientes (359,8 s, 8 workers)

Es el informe de arriba.

### Quién mata a cada mutante (sonda, no versionada)

Para saber que cada muerte es **de esta feature** y no de un test lejano que
cae por casualidad con `-x`, cada mutante se aplicó en un worktree separado de
`HEAD` y se ejecutaron **solo** los cuatro ficheros de F-034 (sonda
`quien_mata.py` en el scratchpad, con las mismas funciones del arnés
—`alcance_de_feature`, `generar_mutantes`, `aplicar_mutante`—; worktree
retirado al terminar):

| Mutante | Tests de F-034 que caen | Uno de ellos |
|---|---|---|
| `codigos_del_parte.py:71` `frozen=False` | 1 | `test_f034_codigos_del_parte_es_inmutable` |
| `codigos_del_parte.py:140` default `solo_incidencia=True` (cotejo) | 6 | `test_f034_r11_codigos_divergentes_dicen_cual_y_llevan_la_cola[otra obra]` |
| `codigos_del_parte.py:185` `strict=False` | 1 | el test nuevo |
| `codigos_del_parte.py:187` quitar el `not` del cotejo | 64 | `test_f034_r3_control_positivo_el_mismo_mundo_con_archivo_si_adjunta` |
| `codigos_del_parte.py:205` `==` → `!=` (H-4: qué criterio para qué código) | 13 | `test_f034_h4_codigos_incidencia_sin_tramos_es_lo_guardado_incompleto[False-/]` |
| `codigos_del_parte.py:206` quitar el `not` (falta la incidencia) | 81 | `test_f034_r3_control_positivo_…_si_adjunta` |
| `codigos_del_parte.py:207` quitar el `not` (falta la obra) | 44 | `test_f034_r3_control_positivo_…_si_adjunta` |
| `codigos_del_parte.py:211` default `solo_incidencia=True` (completos) | 4 | `test_f034_r15_codigos_incompletos_dicen_cual_falta[obra …]` |
| `paso_cierre.py:328` completos con `solo_incidencia=False` | 1 | `test_f034_r16_cerrar_no_coteja_ni_exige_la_obra[sin …]` |
| `paso_cierre.py:333` cotejo con `solo_incidencia=False` | 21 | `test_f034_r3_control_positivo_el_mismo_mundo_con_archivo_si_cierra` |
| `puerta_de_estado.py:210` `and` → `or` | 23 | `test_f034_r3_puerta_sin_archivado_guardado_no_pasa[None-ninguno]` |
| `puerta_de_estado.py:210` `==` → `!=` | 43 | `test_f034_r1_puerta_pasa_con_la_traza_guardada_en_archivado` |

Los doce los cazan los tests de F-034 por sí solos.

### Lo que la campaña no mide

- **El `if` de `_codigo_de_incidencia`** (en `paso_grafico.py` y
  `paso_cierre.py`), inalcanzable por construcción desde H-4
  (`progress/impl_F-034.md` §7.4): **no ha generado ningún mutante**. Sus dos
  líneas (`codigo = a_codigo_de_sigrid(...)` y `if not codigo:`) no cambian
  respecto de `dev` —el diff solo toca el docstring de la función, comprobado
  con `git diff dev`: salen como contexto— y la herramienta muta únicamente
  líneas cambiadas. El aviso de los Bloques 3 y 5 («sus mutantes serán
  equivalentes») no llegó a materializarse. Si se mutara, quitar el `not` lo
  cazaría cualquier caso positivo (lanzaría con un código bueno); lo que
  ningún operador de esta herramienta alcanza es la **rama del `raise`**, que
  es precisamente la inalcanzable. Se conserva como última guarda
  (`design.md` §4.2).
- **Lo JavaScript de la feature** (`services/postventa-front/js/app.js`,
  `reintentarCierre`, T11): `harness.mutacion` solo muta Python, y del servicio
  `front` solo ve `dev_server.py`, que esta feature no toca. **La campaña no
  muerde el JS.** Lo sostienen los 12 tests de
  `tests_js/reintento_vaciado.test.js`, con su RED real (5 fallos) en
  `progress/impl_F-034.md` §8.2: las dos ramas del `if (!vaciado.ok)` tienen
  test, pero el arnés no tiene ni mutación ni cobertura de JS.
- **Muchas líneas y pocos mutantes** (738 y 12): la herramienta solo tiene
  operadores de comparación, aritméticos, lógicos, `not`, booleanos y enteros,
  y el grueso de lo cambiado son docstrings, mensajes, llamadas y firmas, donde
  no aplica ninguno. Eso lo vigilan los tests de mensaje literal, de firma
  (R19), de alcance (T13) y de llamadas al repositorio (T12).

### Para el líder

`rigor.json` fija `timeout_por_mutante_s: 120` y la suite `api` ya tarda
122–127 s en solitario (medido hoy). Con ese tope, un superviviente futuro
saldría `timeout` hasta en el repaso en serie. No lo he cambiado (no es de esta
feature); es una mejora candidata del arnés —y, si vale para cualquiera, de
`arnes-base`— subir el tope o hacerlo relativo a la duración de la suite.

