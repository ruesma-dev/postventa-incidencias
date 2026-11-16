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

- `plantilla_incidencias.py`: `TIPO_RECLAMACION_POR_DEFECTO = "0002"`, `MAX_TIPO_RECLAMACION = 24`,
  `TipoReclamacion`, `tipos_del_desplegable` (reutiliza `_nombre_recortado`/`_con_codigo` de F-071),
  `listas_con_tipos` y `tipo_efectivo`. `revision.py`: `ValoresIncidencia.tipo_reclamacion = None` (último
  campo) y `huella_de_valores`, que lo añade al final solo si no es nulo (R26). `volcado.py`: alias
  `TIPO_RECLAMACION` y `parte_de` con `tipo_efectivo` (R28).

**Aserción de otra feature que cambia** (§3.2): `test_f060_r8_la_revision_cambia_solo_la_ubicacion_de_los_vigentes`
contaba 12 campos aparte de `ubicacion`; ahora 13 (R26); cubre además la copia del tipo (R23).

Verificación de T2 (F-060 ×2, F-072 ×2, F-056 dominio, F-059 dominio): `725 passed in 3.89s`. Suite `api` entera
antes de corregir esa aserción: `1 failed, 9971 passed, 353 skipped in 730.04s` (el único rojo, ese recuento).
Desviación: ninguna.

### T3 · campaña de mutación del Bloque 1 (detalle en `progress/mutacion_F-072_bloque1.md`)

Primer intento bloqueado por 13 tests de configuración que veían el `.env` volcado (arreglados en `a18956e`,
`progress/impl_fix_tests_config_entorno.md`). Relanzada: 7 generados, 5 evaluados, **5 muertos, 0 supervivientes**.

### Cambios de la review del Bloque 1 (`3575aa0`; detalle en `progress/review_F-072_bloque1.md`)

Los 2 mutantes de veracidad que la reducción «uno por línea» descartó sobrevivían (`plantilla_incidencias.py:579`
`not codigo`, `revision.py:826` `if valores.tipo_reclamacion:`): `39 passed` antes; con `""` en el `parametrize` de
R19 y `test_f072_r26_un_tipo_vacio_no_es_el_nulo_y_va_al_final`, `1 failed` cada uno. Verificado por la review.

## Evidencias (Bloque 1)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | suite unitaria `api` entera: 9971 passed, 353 skipped, 1 failed (aserción de F-060 corregida, citada arriba); dirigidos de T2: 725 passed |
| Cobertura de líneas cambiadas | sin medir: `init.sh` lo lanza el líder |
| Mutantes | 7 generados, 5 evaluados (uno por línea), 5 muertos, **0 supervivientes**, 0 timeouts (`progress/mutacion_F-072_bloque1.md`) |
| Tiempo de la suite | 730,04 s (`api` entera, en serie); dirigidos 3,89 s |
| Capa e2e | N/A en el Bloque 1 (dominio puro) |

## Bloque 2 · Dominio de la revisión (T4, T5 y la campaña de T6)

### T4 · RED (`143802a`)

`services/postventa-api/tests/test_f072_revision_dominio.py` (70 casos): R21, R22, R23 (con tipo **no nulo**,
en editar, aprobar, descartar, recuperar y `revision_de_normalizacion`), R24 (orden, `""`, sin `tipos`, en su sitio,
aprobar → 409, fila y resumen) y R25 (`cambios`, `sin_cambios`, estado). Tipos `9001`, `9002`, `9009` (de baja); la
lista vigente **no** trae `0002`.

Comando: `.venv/Scripts/python.exe -m pytest tests/test_f072_revision_dominio.py -q -p no:cacheprovider`

```
tests\test_f072_revision_dominio.py:41: in <module>
    from domain.models.revision import (
E   ImportError: cannot import name 'TIPO_NO_VALIDO' from 'domain.models.revision'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.43s
```

Segunda traza, por comportamiento: la misma suite con solo la constante inyectada desde fuera
(`python -c "import domain.models.revision as r; r.TIPO_NO_VALIDO = '...'; pytest.main([..., '--tb=line'])"`,
sin tocar el código). Extracto:

```
E   ValueError: '9001' is not a valid Listado
E   AssertionError: assert ('urgencia',) == ('urgencia', 'listado')
E   AssertionError: assert <EstadoRevision.EDITADA: 'editada'> is <EstadoRevision.NUEVA: 'nueva'>
FAILED ...::test_f072_r21_un_codigo_vigente_exacto_se_guarda[9001]
FAILED ...::test_f072_r22_listado_nulo_guarda_0002_sin_mirar_la_lista[None]
FAILED ...::test_f072_r24_no_se_puede_aprobar
FAILED ...::test_f072_r25_volver_a_lo_importado_con_0002_deja_la_incidencia_nueva
(...)
49 failed, 21 passed in 0.22s
```

Razón esperada: `validar_valores` pasaba el código por `Listado(...)`, no existían motivo ni `tipos`, y `cambios`
y estado miraban el heredado. Los 21 verdes, a propósito: la copia de R23 ya es estructural en la base.

### T5 · GREEN (`fd0673d`)

`domain/models/revision.py` (§4.2): `TIPO_NO_VALIDO` (sustituye a `LISTADO_NO_VALIDO`, sin usos);
`_tipo_pedido` (R21, R22) y `listado=vigentes.listado` (R23) en `validar_valores`;
`MotivoNoAprobable.TIPO_FUERA_DE_SIGRID` entre `PROVEEDOR_AMBIGUO` y `DUPLICADA`;
`motivos_no_aprobable(..., tipos=None)` y `fila_de_revision(..., tipos=None)` (sin `tipos` no se
calcula, §4.2); `decidir` aprobar pasa `tipos={o.codigo for o in listas.listados}` (los mismos con que
valida editar, §4.2); `CAMPOS_LOGICOS` igual, pero `listado` sale de `tipo_efectivo` (R25).

**Decisión que la spec no escribe (para la review):** `_mismos_valores` compara fotos con el tipo efectivo en
`estado_de` (R1 de F-056) y `sin_cambios` (R16 de F-056). Sin ella, R22 rompe las dos para las 289 incidencias
anteriores a F-072 (guardar sin cambiar nada escribiría una revisión vacía; volver a lo importado dejaría `editada`).
Es R25 aplicada a los otros dos sitios que comparan fotos; la huella sí las distingue (R26). Tests: `test_f072_r25_*`.

**Aserciones de F-056 que cambian** (`tests/test_f056_revision_dominio.py`, ninguna borrada; detalle en el diff de
`fd0673d`): r13 ×3 y r16 (foto con `0002`, R22; `tipo_reclamacion == "segundo"`, R21/R23), r21 (10 motivos, R24) y r33 ×2
(`tipo_reclamacion="9001"` en vez de `listado=PRIMERO`, R25/R19).

Verificación de T5 (comando de `tasks.md`, los cuatro ficheros): `499 passed in 2.49s`.
### Bloqueo de la suite entera y opción (b) del humano (`d8ae988` → `435dd49`)

Con T5, `pytest tests` de api daba `7 failed, 10038 passed` (HTTP de F-056 o2, r10, r42 → 409 por R22+R24; r27 y r29
por R24/R25; dos de documentación). Opción (b) del humano, en `0fb864e`: o2/r10/r42 editan con `listado="primero"`
(comentario R22/R24; el Bloque 6 los vuelve a tocar); r29 con `tipo_reclamacion="9001"`; r27 con
`TIPO_FUERA_DE_SIGRID: 0`; `docs/ARCHITECTURE.md` (F-056) y `test_f056_documentacion.py` con el motivo nuevo (R24).

Suite de api entera tras `0fb864e`: **`10045 passed, 353 skipped in 856.35s`**. T4 y T5 marcadas (`9b22088`).

### T6 · campaña de mutación (`progress/mutacion_F-072_bloque2.md`)

A mano antes (24 mutantes): un superviviente real, `revision.py:856` `tipos is not None` → `tipos`, que mata `85d3c36`.
`python -m harness.mutacion --feature F-072 --base 6994cb0 --timeout 1800 --salida progress/mutacion_F-072_bloque2.md`:

```
[base] .../wk_0..wk_7/services/postventa-api: en verde (1669.5 s a 1780.6 s)
[15/16] muerto  revision.py:856 [veracidad] tipos is not None -> tipos
16 mutantes evaluados, 16 muertos, 0 supervivientes, 0 timeouts, 0 sin veredicto en 5450.4 s
```

24 generados → 16 con uno por línea; los **8 descartados**, reproducidos a mano: **8 muertos** (tabla en el informe de
campaña). **Cero supervivientes**, ningún equivalente.

### Bloque 2 · ajuste del heredado (opción (a) del humano, 2026-11-16; review del Bloque 2, punto 2 y Obs. 1)

Desde F-072 solo el tipo efectivo cuenta para el estado (R1 de F-056) y `sin_cambios` (R16): el `listado`
heredado, tampoco. RED: `test_f072_r25_el_listado_heredado_no_cuenta_para_el_estado` (importado `primero`, una
revisión que solo lo pone a nulo: `cambios == ()` y debe salir `nueva`; con `9001`, `editada`) y
`..._para_sin_cambios` (reeditar esa foto con lo mismo → `SinCambios`).
`.venv/Scripts/python -m pytest tests/test_f072_revision_dominio.py -q -k heredado_no_cuenta`

```
>       assert estado_de(sit) is EstadoRevision.NUEVA
E       AssertionError: assert <EstadoRevision.EDITADA: 'editada'> is <EstadoRevision.NUEVA: 'nueva'>
tests\test_f072_revision_dominio.py:614: AssertionError
FAILED tests/test_f072_revision_dominio.py::test_f072_r25_el_listado_heredado_no_cuenta_para_el_estado
1 failed, 1 passed, 71 deselected in 0.78s
```

El de `sin_cambios` pasa ya en rojo, a propósito: editar copia el heredado de los vigentes (R23), así que en esa
comparación nunca difiere; queda como test de coherencia.

GREEN (`639245a`): `_mismos_valores` compara las dos fotos con `listado=None` además del tipo efectivo (`revision.py`
510–511). La huella no se toca: R26 (`-k r26` en `test_f072_dominio_tipos.py` y `test_f072_volcado.py`) `8 passed`.

Mutantes obvios a mano (quitar `listado=None` de un lado; los cinco ficheros dirigidos, restaurado con `git checkout`):

| Mutante | Antes (test sin parametrizar) | Después (parametrizado en los dos sentidos) |
|---|---|---|
| M1 · `:510` sin `listado=None` (lado vigente) | `530 passed`: **sobrevivía** | `2 failed` (`[None-segundo]`, `[primero-segundo]`) |
| M2 · `:511` sin `listado=None` (lado importado) | `1 failed` | `2 failed` (`[primero-None]`, `[primero-segundo]`) |

M1 era hueco real (el test solo ponía el heredado en lo importado): el test pasa a cubrir `primero→nulo`,
`nulo→segundo` y `primero→segundo`.

Tests dirigidos (desde `services/postventa-api`, `.venv/Scripts/python -m pytest ... -q -p no:cacheprovider`):
`test_f072_revision_dominio`, `test_f072_dominio_tipos`, `test_f056_revision_dominio`, `test_f060_normalizacion_dominio`,
`test_f060_pipeline_normalizacion` → **`532 passed in 5.26s`**; `tests/test_f056_*.py` → **`988 passed, 9 skipped in
14.51s`**. `init.sh` y la suite entera, no lanzados (del líder). Specs sin tocar: R1/R16 de F-056 y R25 de F-072 deben
recoger la decisión (encargo del spec-author).

## Evidencias (Bloque 2)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | api entera: 10045 passed, 353 skipped (antes de `85d3c36`, que añade 1 test que pasa) |
| Cobertura de líneas cambiadas | sin medir: `init.sh` lo lanza el líder |
| Mutantes | 24 generados, 16 evaluados + 8 a mano, **24 muertos, 0 supervivientes**, 0 timeouts |
| Tiempo de la suite | 856,35 s (api entera, en serie); dirigidos de T5 2,49 s; campaña 5450,4 s |
| Capa e2e | N/A (dominio puro) |
