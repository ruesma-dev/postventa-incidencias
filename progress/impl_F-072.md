<!-- progress/impl_F-072.md -->
# F-072 · Informe del implementer

> Rigor **`critico`**. Rama `feature/F-072-tipo-reclamacion-sigrid`, **base fija `dev` `6994cb0`**
> (entre la base y `1039b66` solo cambian specs, backlog y `progress/`: el código de
> `services/` es el de la base). Un bloque por encargo.

## Bloque 1 · Dominio: tipos, tipo efectivo, huella y parte

### T1 · RED

Tests nuevos: `services/postventa-api/tests/test_f072_dominio_tipos.py` (R6, R7, R16 tope,
R19, R26, `listas_con_tipos`) y `services/postventa-api/tests/test_f072_volcado.py` (R28 y
la huella intacta de R26 vista desde el volcado).

Literal de R26 medido con el código de `6994cb0` antes de tocar nada (script en el
scratchpad que llama a `huella_de_valores` de la base sobre la foto `valores()` del test):
`9eb4374f…8228f6` (con urgencia, listado y detalle) y `fe6ba32f…c7e871` (con los tres nulos).
Ese test **pasa** en la base a propósito: fija que la huella de lo anterior a F-072 no cambia.

Comando (desde `services/postventa-api`):
`.venv/Scripts/python.exe -m pytest tests/test_f072_dominio_tipos.py tests/test_f072_volcado.py -q -p no:cacheprovider`

```
=================================== ERRORS ====================================
______________ ERROR collecting tests/test_f072_dominio_tipos.py ______________
ImportError while importing test module '...\services\postventa-api\tests\test_f072_dominio_tipos.py'.
Traceback:
tests\test_f072_dominio_tipos.py:25: in <module>
    from domain.models.plantilla_incidencias import (
E   ImportError: cannot import name 'MAX_TIPO_RECLAMACION' from 'domain.models.plantilla_incidencias'
_________________ ERROR collecting tests/test_f072_volcado.py _________________
ImportError while importing test module '...\services\postventa-api\tests\test_f072_volcado.py'.
Traceback:
tests\test_f072_volcado.py:26: in <module>
    from domain.models.plantilla_incidencias import TIPO_RECLAMACION_POR_DEFECTO, Listado
E   ImportError: cannot import name 'TIPO_RECLAMACION_POR_DEFECTO' from 'domain.models.plantilla_incidencias'
=========================== short test summary info ===========================
ERROR tests/test_f072_dominio_tipos.py
ERROR tests/test_f072_volcado.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
2 errors in 0.62s
```

Razón esperada: no existen aún `TipoReclamacion`, `TIPO_RECLAMACION_POR_DEFECTO`,
`MAX_TIPO_RECLAMACION`, `tipos_del_desplegable`, `listas_con_tipos` ni `tipo_efectivo`.

Segunda traza, la de R26/R28 por comportamiento (la foto aún no admite el tipo), con el
código de la base:
`.venv/Scripts/python.exe -c "from domain.models.revision import ValoresIncidencia; ValoresIncidencia(..., listado=None, tipo_reclamacion='9001')"`

```
Traceback (most recent call last):
  File "<string>", line 3, in <module>
TypeError: ValoresIncidencia.__init__() got an unexpected keyword argument 'tipo_reclamacion'
```

### T2 · GREEN

- `domain/models/plantilla_incidencias.py`: `TIPO_RECLAMACION_POR_DEFECTO = "0002"`,
  `MAX_TIPO_RECLAMACION = 24`, `TipoReclamacion(codigo, nombre)`, `tipos_del_desplegable`
  (reutiliza `_nombre_recortado` y `_con_codigo` de F-071, así la etiqueta es la del oficio),
  `listas_con_tipos` (`replace` de `listados`) y `tipo_efectivo`; docstring de `ListasCerradas`.
- `domain/models/revision.py`: `ValoresIncidencia.tipo_reclamacion: str | None = None` (último
  campo) y `huella_de_valores`, que salta el campo y lo añade al final solo si no es nulo (R26).
- `domain/models/volcado.py`: `TIPO_RECLAMACION = TIPO_RECLAMACION_POR_DEFECTO` (alias) y
  `parte_de` con `tipo_efectivo(v.tipo_reclamacion)` (R28); docstrings sin «siempre `0002`».

**Aserción de otra feature que cambia** (citada con su R, como pide `design.md` §3.2):
`tests/test_f060_normalizacion_dominio.py::test_f060_r8_la_revision_cambia_solo_la_ubicacion_de_los_vigentes`
contaba `len(otros) == 12` campos de la foto aparte de `ubicacion`; con el campo nuevo son 13
(R26). Lo demás del test (que todos se copian y solo cambia `ubicacion`) sigue igual y ahora
cubre también la copia de `tipo_reclamacion` en la revisión del sistema (R23).

Verificación de T2 (comando de `tasks.md`, más los dos de F-060):
`.venv/Scripts/python.exe -m pytest tests/test_f060_normalizacion_dominio.py tests/test_f060_pipeline_normalizacion.py tests/test_f072_dominio_tipos.py tests/test_f072_volcado.py tests/test_f056_revision_dominio.py tests/test_f059_volcado_dominio.py -q -p no:cacheprovider`
→ `725 passed in 3.89s`.

Suite unitaria entera de `api` (`pytest tests -q`, sin `init.sh`, que es del líder), antes de
corregir la aserción de F-060: `1 failed, 9971 passed, 353 skipped in 730.04s`; el único rojo
era ese recuento, ya corregido y en verde. No hay más ficheros afectados.

Desviación: ninguna. Fuera del Bloque 1 (llega en el Bloque 2): `validar_valores` y la foto
desde la bandeja aún no copian `tipo_reclamacion` (hoy ninguna fila lo tiene: lo escribe la
importación del Bloque 5).

### T3 · campaña de mutación del Bloque 1 — BLOQUEADA (fallo inesperado del arnés)

Comando lanzado tal cual lo pidió el líder, desde la raíz:
`python -m harness.mutacion --feature F-072 --base 6994cb0 --timeout 1800 --salida progress/mutacion_F-072_bloque1.md`

Alcance que calculó: 3 ficheros, 93 líneas de producción (rama `6994cb0..feature/F-072…`),
muestreo `critico` (60 %, suelo 100, techo 300, semilla 20261030), 8 workers. **Abortó sin escribir
informe** (`progress/mutacion_F-072_bloque1.md` no existe), porque la línea base sale roja **en el
worktree del worker**, sin mutar nada:

```
LÍNEA BASE EN ROJO en C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_upct7sx9/wk_1/services/postventa-api: la suite falla SIN mutar nada.
Campaña abortada sin escribir informe: sobre una base roja TODO mutante saldría «muerto» y el cero de supervivientes sería falso.
  Tests que fallan sin mutar:
    - tests/test_f012_fabrica_grafico.py::test_f012_r40_la_tercera_puerta_nombra_todas_las_variables_que_faltan
    - tests/test_f012_fabrica_grafico.py::test_f012_r40_el_error_no_lleva_jamas_el_valor_de_ninguna_variable
    - tests/test_f013_ubicacion_sigrid.py::test_f013_t12_faltando_configuracion_nombra_todas_y_ningun_valor
    - tests/test_f036_adaptador_catalogo.py::test_f036_r11_faltando_configuracion_nombra_todas_y_ningun_valor
    - tests/test_f056_ubicaciones.py::test_f056_r46_la_fabrica_nombra_lo_que_falta_y_ningun_valor
    - tests/test_f059_fabrica.py::test_f059_r10_r16_la_configuracion_nombra_todas_las_que_faltan_y_ningun_valor[construir_ensayador]
    - tests/test_f059_fabrica.py::test_f059_r10_r16_la_configuracion_nombra_todas_las_que_faltan_y_ningun_valor[construir_volcador]
    - tests/test_f059_fabrica.py::test_f059_r30_la_configuracion_va_antes_que_n[construir_ensayador]
    - tests/test_f059_fabrica.py::test_f059_r30_la_configuracion_va_antes_que_n[construir_volcador]
    - tests/test_f059_volcado_http.py::test_f059_r10_r30_el_ensayo_sin_entorno_configuracion_o_n_es_503_sin_leer[sin-configuracion]
    - tests/test_f059_volcado_http.py::test_f059_r16_r37_r42_el_volcado_sin_sus_puertas_es_503_antes_de_abrir_la_base[sin-configuracion]
    - tests/test_f065_adaptador.py::test_f065_r2_la_fabrica_nombra_lo_que_falta_y_ningun_valor
    - tests/test_f065_http.py::test_f065_r2_sin_configuracion_503_nombrando_las_variables_y_nunca_sus_valores
```

Esos 13 tests pasan en la carpeta principal (están entre los 9971 verdes de la suite entera de T2).
**Diagnóstico** (leyendo código, sin abrir el `.env`, que no se toca):

- El arnés 1.10 trae `volcar_variables` (`harness/mutacion_paralela.py`, F-023 del arnés): antes de
  crear los worktrees vuelca el `.env` de la raíz **a `os.environ`** del coordinador, y los workers lo
  heredan. No existía en el arnés con el que se midió F-071 (`git show 6994cb0~5:harness/mutacion_paralela.py`
  no lo tiene); F-072 es la primera campaña con la 1.10.
- Los 13 tests comprueban que la fábrica **nombra la configuración que falta** (p. ej.
  `test_f056_r46…`: `_ajustes(ENTORNO="dev", SIGRID_API_KEY=…, SIGRID_BASE_DATOS="  ")` y espera
  `SIGRID_API_BASE_URL` en el error). Se aíslan del fichero `.env`, pero no de `os.environ`: con las
  variables ya volcadas al entorno, lo que debía faltar está, y el error no sale.
- No es del código de F-072 (ninguno de los 13 toca los ficheros mutados) ni de la máquina.

**Por qué no lo esquivo**: `--workers 1` lo evita (en serie no hay volcado de worktree), pero la suite
entera tarda **730 s** sin paralelizar y el muestreo pide ≥ 100 mutantes: más de 20 h. Exportar
variables vacías para tapar las del `.env`, tocar los tests de otras features o el arnés serían
workarounds que el protocolo prohíbe improvisar. Decisión para el líder/humano, opciones que veo:
(a) arreglar el aislamiento de esos 13 tests (que limpien también `os.environ` de las variables que
esperan ausentes) en una tarea de arnés/proyecto aparte; (b) que `volcar_variables` sea opt-in en
`rigor.local.json` (mejora del arnés genérico, a portar a `arnes-base`); (c) campaña con
`--con-seleccion` y `--workers 1` (no probado: la selección mide cobertura y podría bajar mucho
el coste, pero no lo he lanzado sin permiso).

Estado del Bloque 1: **T1 y T2 hechas y en verde** (commits `50efef2`, `0a3ed7e`); T3 sin hacer
(mutación bloqueada; la review la lanza el líder). La rama queda limpia y sin worktrees colgados
(`git worktree list` sin los de la campaña).

### T3 · campaña relanzada tras el desbloqueo (2026-11-15)

El humano eligió la opción (a): `conftest.py` aísla de `os.environ` los tests de configuración
ausente (`a18956e`, `dev` `05c8a5a`, traído a la rama en `299f21c`). Relanzada tal cual:
`python -m harness.mutacion --feature F-072 --base 6994cb0 --timeout 1800 --salida progress/mutacion_F-072_bloque1.md`

```
[base] .../wk_0..wk_4/services/postventa-api: en verde (1293.3 s a 1364.3 s)
[1/5] muerto  plantilla_incidencias.py:193 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)
[2/5] muerto  revision.py:826 [comparacion] if valores.tipo_reclamacion is not None: -> ... is None:
[3/5] muerto  revision.py:822 [comparacion] if campo.name == "tipo_reclamacion": -> ... != ...
[4/5] muerto  plantilla_incidencias.py:579 [comparacion] ... if codigo is None else codigo -> ... is not None ...
[5/5] muerto  plantilla_incidencias.py:66 [entero] MAX_TIPO_RECLAMACION = 24 -> 25
5 mutantes evaluados, 5 muertos, 0 supervivientes, 0 timeouts, 0 sin veredicto en 3989.2 s
```

Campaña completa (7 generados, 5 candidatos con uno por línea; sin muestreo), 5 workers. **Cero
supervivientes**: no hay huecos que matar ni tests nuevos. `volcado.py` (16 líneas en alcance) no
da mutantes; su declaración, con la prueba de control a mano (7 y 2 rojos al quitar el tipo
efectivo o cambiar el alias), está en `progress/mutacion_F-072_bloque1.md`, sin nada en
`PENDIENTE`. El `.json` de estado de la campaña queda sin versionar, como los de antes.
T3 no se marca: la review del Bloque 1 la lanza el líder.

## Evidencias (Bloque 1)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | suite unitaria `api` entera: 9971 passed, 353 skipped, 1 failed (aserción de F-060 corregida, citada arriba); dirigidos de T2: 725 passed |
| Cobertura de líneas cambiadas | sin medir: `init.sh` lo lanza el líder |
| Mutantes | 7 generados, 5 evaluados (uno por línea), 5 muertos, **0 supervivientes**, 0 timeouts (`progress/mutacion_F-072_bloque1.md`) |
| Tiempo de la suite | 730,04 s (`api` entera, en serie); dirigidos 3,89 s |
| Capa e2e | N/A en el Bloque 1 (dominio puro) |
