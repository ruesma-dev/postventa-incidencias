<!-- progress/impl_F-003.md -->
# F-003 · Extracción multimodal del parte — Informe de implementación

> Rama `feature/F-003-extraccion`. Rigor **`critico`**: fase RED con traza
> real pegada, cobertura de las líneas cambiadas, campaña de mutación con
> cero supervivientes y las verificaciones `MANUAL (humano)` con su comando
> exacto.
>
> **Ni un dato personal en este informe**: los valores que aparecen son
> inventados (el DNI `00000000T` no es válido). Ninguna credencial, ni su
> valor ni un fragmento.

## Fase RED · trazas reales

Las ocho tareas RED de `tasks.md` (T2, T4, T6, T7, T9, T11, T13, T15). Cada
bloque es la **salida literal** del comando que lo precede, ejecutado antes de
que existiera el código que lo pone en verde.

### T2 · R19 — la guardia de red no existía

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_arquitectura.py -q
```

```
FAILURES
___________ test_f003_r19_la_suite_no_puede_abrir_conexiones_de_red ___________
        conector = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conector.settimeout(0.5)

        try:
            with pytest.raises(RuntimeError) as fallo:
>               conector.connect(_DIRECCION_INERTE)
E               TimeoutError: timed out

tests\test_f003_arquitectura.py:42: TimeoutError
=========================== short test summary info ===========================
FAILED tests/test_f003_arquitectura.py::test_f003_r19_la_suite_no_puede_abrir_conexiones_de_red - TimeoutError: timed out
1 failed in 0.77s
```

Lo que demuestra el `TimeoutError`: **la conexión se intentaba de verdad**. No
es que faltara un mensaje de error; es que la suite podía salir a la red.

### T4 · R1, R3, R5 — el dominio de la extracción no existía

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_extraccion_dominio.py -q
```

```
=================================== ERRORS ====================================
___________ ERROR collecting tests/test_f003_extraccion_dominio.py ____________
ImportError while importing test module '...\tests\test_f003_extraccion_dominio.py'.
Traceback:
tests\test_f003_extraccion_dominio.py:13: in <module>
    from domain.models.extraccion import (
E   ModuleNotFoundError: No module named 'domain.models.extraccion'
=========================== short test summary info ===========================
ERROR tests/test_f003_extraccion_dominio.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.30s
```
