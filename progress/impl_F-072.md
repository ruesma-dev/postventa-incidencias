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
