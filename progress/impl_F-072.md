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
