<!-- progress/impl_F-072_bloque3.md -->
# F-072 · Bloque 3 · La lectura de Sigrid (T7, T8 y la campaña de T9)

> Detalle del bloque; el resumen está en `progress/impl_F-072.md`. Rigor **`critico`**, base fija
> `dev` `6994cb0`. Rama `feature/F-072-tipo-reclamacion-sigrid`.

## Qué cambió

| Fichero (bajo `services/postventa-api/`) | Qué |
|---|---|
| `domain/ports/tipos_reclamacion.py` (nuevo) | `FilaTipoReclamacion(codigo, nombre, posicion)` (`nombre` fuera del `repr`, R30) y `TiposReclamacionPort.leer() -> LecturaCatalogo[...]` |
| `infrastructure/sigrid/consultas_tipos_reclamacion.py` (nuevo) | `SQL_TIPOS_RECLAMACION` (R2), `select_tipos_reclamacion()` → `(SQL, ())`, `fila_a_tipo_reclamacion` (3 columnas o `ValueError` sin la fila; `pos` a entero o `ValueError` sin el valor) |
| `infrastructure/sigrid/tipos_reclamacion.py` (nuevo) | `AdaptadorTiposReclamacionSigridApi(AdaptadorCatalogoSigridApi)`: solo `leer()`; hereda puerta de entorno, techo de 1.000, 503 y reintentos |
| `application/pipelines/tipos_reclamacion.py` (nuevo) | `leer_tipos_reclamacion` (R4, R5, R30), `FuenteTiposReclamacion`, `fuente_de_tipos` (`partial`, sin caché, R1) |
| `infrastructure/sigrid/fabrica.py` | `construir_tipos_reclamacion` (entorno → configuración, como `construir_ubicaciones_validas`) y su enmienda en el docstring; CRLF conservado |
| `tests/test_f072_lectura_sigrid.py` (nuevo) | 79 casos: R1–R5, R30, R31 |

Ninguna consulta existente de `infrastructure/sigrid/` cambia (R32): `git diff 6994cb0 -- infrastructure/sigrid/`
solo toca `fabrica.py` (añadido) y crea los dos ficheros nuevos.

### Decisión: la línea de R30 la escribe la aplicación, no el adaptador

`design.md` §3.1 dice «adaptador: `leer()` y el log de R30»; §6.1 dice «Log de R30 en la aplicación» y da el formato.
Los recuentos `sin_codigo` y `repetidos` salen de filtrar y deduplicar, que es de la aplicación (§5; el adaptador «no
decide»). Se sigue §6.1: **una** línea, en `application/pipelines/tipos_reclamacion.py`, y el adaptador no registra
nada (`test_f072_r30_el_adaptador_no_registra_nada_con_el_nombre`). La línea se escribe **antes** del 409 del techo, para
que `al_techo=True` conste (`test_f072_r30_al_techo_tambien_se_registra_antes_del_409`). Para la review.

### Otras decisiones menores

- `nombre` de `FilaTipoReclamacion` va con `field(repr=False)`, como `ubica` en F-056: es `res` (R30).
- `pos` se convierte a entero (la pasarela puede dar `4.0` o `"3"`); lo que no lo es, `ValueError` → 503 sin la fila.
  `posicion` no se usa: el orden lo da el `ORDER BY` de R2.
- El nombre se guarda sin recortar en `TipoReclamacion`: lo recorta `tipos_del_desplegable` (Bloque 1).

## T7 · RED (`daca1b9`)

Comando (desde `services/postventa-api`):
`.venv/Scripts/python.exe -m pytest tests/test_f072_lectura_sigrid.py -q -p no:cacheprovider`

```
_____________ ERROR collecting tests/test_f072_lectura_sigrid.py ______________
ImportError while importing test module '...\services\postventa-api\tests\test_f072_lectura_sigrid.py'.
Traceback:
tests\test_f072_lectura_sigrid.py:37: in <module>
    from application.pipelines import tipos_reclamacion as modulo_aplicacion
E   ImportError: cannot import name 'tipos_reclamacion' from 'application.pipelines' (...\application\pipelines\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_f072_lectura_sigrid.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.41s
```

Segunda traza, por comportamiento: en un worktree desechable de `daca1b9` (scratchpad, nada versionado), los cinco
nombres como esqueletos (`SQL_TIPOS_RECLAMACION = ""`, funciones con `raise NotImplementedError`, la fila como
dataclass sin `repr=False`, `construir_tipos_reclamacion` añadida al final de `fabrica.py` sin tocar `__all__`).
Mismo comando con `--tb=line`; líneas de error distintas:

```
E   AssertionError: assert '' == 'SELECT cod, ...R BY pos, cod'
E   NotImplementedError
E   AssertionError: assert 'TIPO FICTICIO RESERVADO' not in 'FilaTipoRec... posicion=1)'
E   AssertionError: assert 'construir_tipos_reclamacion' in ['ENTORNOS_CON_CIERRE', 'VARIABLES_OBLIGATORIAS', ...]
E   AttributeError: <module 'infrastructure.sigrid.fabrica' ...> has no attribute 'AdaptadorTiposReclamacionSigridApi'
72 failed, 7 passed in 1.12s
```

Razón esperada: no existían el puerto, la consulta, el adaptador, la aplicación ni la fábrica. Los 7 verdes son
estructurales: la puerta de entorno que el esqueleto ya hereda de `AdaptadorCatalogoSigridApi` y las comprobaciones de
forma (protocolo, módulos sin rutas de escritura).

## T8 · GREEN (`a7d959c`; T7 y T8 marcadas en `a0f93d6`)

`.venv/Scripts/python.exe -m pytest tests/test_f072_lectura_sigrid.py tests/test_f056_ubicaciones.py -q -p no:cacheprovider`
→ **`171 passed in 2.86s`**.

Arquitectura y alcance (`test_f006_arquitectura`, `test_f013_arquitectura`, `test_f036/f056/f071_alcance_cerrado`,
`test_f005_repo_sin_datos_personales`, `test_f006_repo_sin_identificadores`): **`354 passed, 28 skipped in 53.38s`**.

Suite `api` entera (`.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider`):
**`10133 passed, 353 skipped in 863.08s (0:14:23)`**. Nada de otros bloques se rompe.

## Mutantes a mano (antes de la campaña)

Sobre un worktree desechable de `a0f93d6`, cada mutante aplicado, `pytest tests/test_f072_lectura_sigrid.py
tests/test_f056_ubicaciones.py -x` y restaurado (script en el scratchpad). **28 de 28 muertos**:

| Id | Fichero | Mutante | Lo mata |
|---|---|---|---|
| M01 | consultas | `COLUMNAS_TIPOS = 4` | `r2_cada_fila...[lista]` |
| M02 | consultas | sin `not isinstance(...) or` | `r2_una_fila_sin_tres_columnas...[nula]` |
| M03/M04 | consultas | `!=` → `>` / `<` | `...[dos-columnas]` / `...[cuatro-columnas]` |
| M05 | consultas | `_texto`: `is None` → `is not None` | `r2_cada_fila...[lista]` |
| M06 | consultas | `_entero` sin el `if valor is None` | `r2_cada_fila...[nulos]` |
| M07/M08 | consultas | `except` solo `ValueError` / solo `TypeError` | `r2_una_posicion...[lista]` / `[texto]` |
| M09 | consultas | `return valor` (sin `int`) | `r2_cada_fila...[no-textos]` |
| M10 | consultas | parámetros `(None,)` | `r2_sin_parametros` |
| M11 | aplicación | sin `.strip()` | `r5_codigos_vacios_fuera...` |
| M12 | aplicación | `if not codigo` → `if codigo` | `r5_codigos_vacios_fuera...` |
| M13/M14 | aplicación | `not in` → `in` / `else:` | `r5_codigos_vacios_fuera...` |
| M15 | aplicación | `sin_codigo = 1` | `r30_la_linea_de_log...` |
| M16/M17 | aplicación | `repetidos`: signos cambiados | `r30_la_linea_de_log...` |
| M18 | aplicación | `if not lectura.llego_al_techo` | `r5_codigos_vacios_fuera...` |
| M19 | aplicación | `monotonic() + arranque` | `r30_la_linea_registra_la_duracion...` |
| M20 | aplicación | `nombre=None` | `r5_codigos_vacios_fuera...` |
| M21 | aplicación | resultado invertido | `r5_codigos_vacios_fuera...` |
| M22 | aplicación | `al_techo` del log a `False` | `r30_al_techo_tambien_se_registra...` |
| M23 | aplicación | `sin_codigo` del log a `0` | `r30_la_linea_de_log...` |
| M24 | adaptador | texto de la operación | `r3_cortada_por_debajo...[0]` |
| M25 | adaptador | mapeo identidad | `r1_leer_es_un_post...` |
| M26 | fábrica | sin la puerta del entorno | `r31_la_fabrica_se_niega...[test]` |
| M27 | fábrica | sin `_exigir_configuracion` | `r31_la_fabrica_nombra_lo_que_falta...` |
| M28 | puerto | `nombre` en el `repr` | `r30_la_fila_es_inmutable...` |

## T9 · campaña de mutación

`python -m harness.mutacion --feature F-072 --base 6994cb0 --timeout 1800 --salida progress/mutacion_F-072_bloque3.md`
(8 workers por defecto), sobre `a0f93d6`:

```
[base] .../mutacion_F-072_5dj18dfg/wk_0..wk_7/services/postventa-api: en verde (1867.8 s a 2236.6 s)
[25/30] muerto        .../consultas_tipos_reclamacion.py:61 [veracidad] ... -> return None if not valor else str(valor)
Repaso abortado: la línea base del worktree del repaso no está verde. La campaña se entrega tal cual, con sus timeouts sin aclarar.
CAMPAÑA NO VÁLIDA: La línea base estaba VERDE al empezar y ROJA al terminar en .../wk_0/services/postventa-api
(tests/test_f036_excel_lector.py::test_f036_r115_celda_con_estilo_lejana_en_los_metadatos_es_barata[1-16384]). [...]
30 mutantes evaluados, 20 muertos, 0 supervivientes, 10 timeouts, 0 sin veredicto en 9346.3 s
```

**La campaña NO VALE para cerrar** (lo dice el propio arnés). Causa, ajena a F-072: `test_f036_r115_...` es un test de
**tiempo** de F-036 (`TOPE_SEGUNDOS = 1.0`) que con 8 suites enteras a la vez pasa del segundo; solo pasa
(`-k r115`: `65 passed in 161.57s`) y en la suite en serie también. Los 10 timeouts, mismo origen: las líneas base
tardaron **1867,8–2236,6 s**, más que el `--timeout 1800`.

**Segunda campaña** (orden del líder: `--timeout 3600 --workers 4`, sobre `ae15470`): **30 evaluados, 30 muertos, 0
supervivientes, 0 timeouts** en 14281,0 s (bases 2292,8–2363,7 s), pero **otra vez NO VÁLIDA**: al terminar, la base de
`wk_2` falló en `test_f036_r115_rango_que_openpyxl_expande_al_cargar_se_lee_en_menos_de_un_segundo[combinado-A-H-_plantilla]`,
otro test de tiempo de F-036 (tope de un segundo). Parado aquí como mandó el líder, **sin tocar el test**. El informe de
campaña es el de la segunda, con el análisis a mano de la primera añadido al final.

**Veredicto a mano** (tabla completa en `progress/mutacion_F-072_bloque3.md`, «Análisis del implementer»): los **21**
mutantes que el generador del arnés saca de los cuatro ficheros nuevos (13 evaluados + 8 descartados por «uno por
línea»; 45 generados en total, por debajo del suelo de 100) y los 3 de las dos líneas del Bloque 1 en timeout,
aplicados con `generar_mutantes`/`aplicar_mutante` en un worktree desechable y los tests dirigidos.

**Un superviviente real que la campaña dio por muerto**: `consultas_tipos_reclamacion.py:61` `valor is None` →
`not valor` (`171 passed`). Con él, un `cod` numérico `0` saldría `None` (R5 lo tiraría) y un `res` `""`, `None`: no es
equivalente. Lo mata el caso `falsos-no-nulos` (`[0, "", 0]`) de `test_f072_r2_cada_fila_es_codigo_nombre_y_posicion`
(`26c6f36`): con el mutante `1 failed, 171 passed`; sin él `172 passed`. Resultado: **24 de 24 muertos a mano, 0
supervivientes, ningún equivalente**. Declaraciones de `volcado.py`, `fabrica.py` y `tipos_reclamacion.py` (sin mutantes)
escritas. No había `progress/mutacion_F-072_bloque3.json` de estado en el árbol: nada que mover a `%TEMP%`.

## Evidencias (Bloque 3)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | `api` entera: **10133 passed, 353 skipped** (en `a0f93d6`); dirigidos de T8: 171 passed; tras `26c6f36`: 172 passed |
| Cobertura de líneas cambiadas | sin medir: `init.sh` lo lanza el líder |
| Mutantes | dos campañas **no válidas** (base rota por tests de tiempo de F-036): 1.ª 30 evaluados, 20 muertos, 10 timeouts; 2.ª 30 evaluados, 30 muertos, 0 timeouts; a mano, 28 propios (M01–M28) + 24 del generador: **todos muertos, 0 supervivientes** tras `26c6f36` (1 real, cerrado) |
| Tiempo de la suite | 863,08 s (`api` entera, en serie); dirigidos 2,86 s; campañas 9346,3 s y 14281,0 s |
| Capa e2e | N/A (lectura con dobles; sin front) |

## Pendiente

T9 sin marcar. **Decisión del líder/humano**: los tests de tiempo de F-036 rompen la base en paralelo; repetir en serie, tratar esos tests, o aceptar el
veredicto a mano. La suite entera no se ha relanzado tras `26c6f36` (solo añade un caso que pasa); `init.sh`, del líder.
Nada en Sigrid, ni `.env`, ni push.
