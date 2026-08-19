<!-- progress/impl_F-004.md -->
# F-004 · Validación del parte y clasificación de la firma — informe de implementación

> Rama `feature/F-004-validacion`. Rigor **`critico`**: fase RED obligatoria en
> los requisitos centrales, cobertura de las líneas cambiadas por encima del
> 80 % y campaña de mutación con cero supervivientes o justificación escrita.
>
> **Ni un dato real en este informe.** Todos los valores citados son
> inventados; los recuentos de la verificación manual son recuentos, no
> valores.

## Estado

EN CURSO.

---

## Evidencias de la fase RED

Cada bloque trae el **comando exacto** y la **salida real** del fallo previo a
escribir el código, tal y como exige `CHECKPOINTS.md` C4 bis. Todas las
ejecuciones son desde `services/postventa-api/`.

### T1 · el dominio de la firma (R1, R2, R14, R14 bis)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f004_firma_dominio.py -q
=================================== ERRORS ====================================
______________ ERROR collecting tests/test_f004_firma_dominio.py ______________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f004_firma_dominio.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_firma_dominio.py:19: in <module>
    from domain.models.firma import (
E   ModuleNotFoundError: No module named 'domain.models.firma'
=========================== short test summary info ===========================
ERROR tests/test_f004_firma_dominio.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.28s
```

### T3 · el prompt de la firma y el registro de schemas (R4, R5)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f004_prompts_firma.py -q
=================================== ERRORS ====================================
______________ ERROR collecting tests/test_f004_prompts_firma.py ______________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f004_prompts_firma.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_prompts_firma.py:25: in <module>
    from domain.models.schemas import CAMPOS_POR_SCHEMA, campos_del_schema
E   ModuleNotFoundError: No module named 'domain.models.schemas'
=========================== short test summary info ===========================
ERROR tests/test_f004_prompts_firma.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.32s
```

### T6 · las reglas de validación (R6 a R19)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f004_reglas_validacion.py -q
=================================== ERRORS ====================================
____________ ERROR collecting tests/test_f004_reglas_validacion.py ____________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f004_reglas_validacion.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_reglas_validacion.py:30: in <module>
    from domain.models.validacion import (
E   ModuleNotFoundError: No module named 'domain.models.validacion'
=========================== short test summary info ===========================
ERROR tests/test_f004_reglas_validacion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.92s
```

### T8 · los pasos del pipeline (R2, R3, R21, y la mitad de R23)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f004_paso_firma.py tests/test_f004_paso_validacion.py -q
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_paso_firma.py:20: in <module>
    from application.pipelines.paso_firma import MIME_PDF, paso_firma
E   ModuleNotFoundError: No module named 'application.pipelines.paso_firma'
_____________ ERROR collecting tests/test_f004_paso_validacion.py _____________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f004_paso_validacion.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_paso_validacion.py:19: in <module>
    from application.pipelines.paso_validacion import paso_validacion
E   ModuleNotFoundError: No module named 'application.pipelines.paso_validacion'
=========================== short test summary info ===========================
ERROR tests/test_f004_paso_firma.py
ERROR tests/test_f004_paso_validacion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
2 errors in 2.03s
```

### T11 · los dos endpoints (R23, R24, R14 bis)

```
$ .venv/Scripts/python.exe -m pytest tests/test_f004_firma_http.py tests/test_f004_validar_http.py -q
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_firma_http.py:28: in <module>
    from interface_adapters.api.firma import leer_firma
E   ModuleNotFoundError: No module named 'interface_adapters.api.firma'
______________ ERROR collecting tests/test_f004_validar_http.py _______________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\postventa-incidencias\services\postventa-api\tests\test_f004_validar_http.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_validar_http.py:25: in <module>
    from interface_adapters.api.validar import validar
E   ModuleNotFoundError: No module named 'interface_adapters.api.validar'
=========================== short test summary info ===========================
ERROR tests/test_f004_firma_http.py
ERROR tests/test_f004_validar_http.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
2 errors in 0.61s
```
