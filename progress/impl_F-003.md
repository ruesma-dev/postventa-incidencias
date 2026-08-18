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

### T6 · R2 bis — el noveno campo no estaba declarado

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_extraccion_dominio.py -q -k r2bis
```

```
================================== FAILURES ===================================
_____________ test_f003_r2bis_el_numero_de_pagina_se_lee_del_pie ______________
    def test_f003_r2bis_el_numero_de_pagina_se_lee_del_pie():
>       assert "numero_pagina" in CAMPOS_DEL_PARTE
E       AssertionError: assert 'numero_pagina' in ('promocion', 'codigo_obra', 'unidad', 'numero_incidencia', 'fecha_servicio', 'descripcion', ...)

tests\test_f003_extraccion_dominio.py:85: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f003_extraccion_dominio.py::test_f003_r2bis_el_numero_de_pagina_se_lee_del_pie - AssertionError: assert 'numero_pagina' in ('promocion', 'codigo_obra', 'uni...
1 failed, 13 deselected in 0.68s
```

Y el segundo test de R2 bis, el que vigila que **no se reagrupe**:

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_paso_extraccion.py -q
```

```
Traceback:
tests\test_f003_paso_extraccion.py:12: in <module>
    from application.pipelines.contexto_parte import ContextoParte
E   ModuleNotFoundError: No module named 'application.pipelines.contexto_parte'
=========================== short test summary info ===========================
ERROR tests/test_f003_paso_extraccion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.24s
```

**Nota de orden, deliberada y escrita en la propia spec.** Tras T6 el primero
de los dos queda en verde (14 tests del dominio) y el segundo **sigue en rojo
hasta T10**, que es cuando existe el paso del pipeline. No es un descuido: la
verificación de T10 lo dice con estas palabras —«en verde, **incluido el
`test_f003_r2bis_la_extraccion_no_reagrupa_paginas` de T6**»—. El mismo ritmo
que T7→T8 y T9→T10: el test se escribe en su tarea y se pone verde en la
siguiente.

### T7 · R8, R9, R10 — el repositorio de prompts no existía

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_prompts_yaml.py -q
```

```
Traceback:
tests\test_f003_prompts_yaml.py:21: in <module>
    from infrastructure.prompts.prompts_yaml import RepositorioPromptsYaml
E   ModuleNotFoundError: No module named 'infrastructure.prompts'
=========================== short test summary info ===========================
ERROR tests/test_f003_prompts_yaml.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.23s
```

### T9 · R2, R4, R6, R7, R13, R16 — el paso del pipeline no existía

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_paso_extraccion.py -q
```

```
Traceback:
tests\test_f003_paso_extraccion.py:15: in <module>
    from application.pipelines import paso_extraccion as modulo_paso
E   ImportError: cannot import name 'paso_extraccion' from 'application.pipelines' (...\application\pipelines\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_f003_paso_extraccion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.23s
```

### T11 · R14, R15 — el adaptador de Gemini no existía

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_adaptador_gemini.py -q
```

```
Traceback:
tests\test_f003_adaptador_gemini.py:24: in <module>
    from infrastructure.llm.gemini import PROVEEDOR, AdaptadorGeminiVision
E   ModuleNotFoundError: No module named 'infrastructure.llm'
=========================== short test summary info ===========================
ERROR tests/test_f003_adaptador_gemini.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.22s
```

### T13 · R11, R12 — la fábrica no existía

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_fabrica.py -q
```

```
Traceback:
tests\test_f003_fabrica.py:20: in <module>
    from infrastructure.llm.fabrica import PROVEEDORES, construir_extractor
E   ModuleNotFoundError: No module named 'infrastructure.llm.fabrica'
=========================== short test summary info ===========================
ERROR tests/test_f003_fabrica.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.25s
```

### T13 bis · R13 y R8 — los dos guardianes, rotos a propósito en una copia

Los otros dos tests de T13 —`test_f003_r13_dominio_y_aplicacion_no_importan_proveedores`
y `test_f003_r8_ningun_modulo_incrusta_el_texto_del_prompt`— **no tienen
código de producción cuyo fallo previo enseñar**: el entregable es el propio
test, y en un árbol sano pasan desde el primer minuto. Es exactamente el caso
que `CHECKPOINTS.md` C4 bis contempla: la fase RED se demuestra **rompiendo
deliberadamente lo que el test vigila, en una copia aislada y nunca en el
árbol real**.

Copia del servicio (sin `.venv`) en `%TEMP%\f003-red-arquitectura`, dos
violaciones inyectadas —`import yaml` e `import tenacity` en
`domain/models/extraccion.py`, y la primera frase larga del prompt copiada
dentro de `infrastructure/llm/gemini.py`— y la suite lanzada **desde la
copia**, con el intérprete del venv real:

```bash
cd "$TEMP/f003-red-arquitectura" && <venv>/python.exe -m pytest tests/test_f003_arquitectura.py -q -k "r13 or r8"
```

```
>       assert culpables == {}
E       AssertionError: assert {'domain\\mod...ity', 'yaml']} == {}
E
E         Left contains 1 more item:
E         {'domain\\models\\extraccion.py': ['tenacity', 'yaml']}

>       assert incrustados == {}
E       AssertionError: assert {'infrastruct...venta de una'} == {}
E
E         Left contains 1 more item:
E         {'infrastructure\\llm\\gemini.py': 'Eres un extractor de datos de PARTES DE '
E                                            'TRABAJO de posventa de una'}

tests\test_f003_arquitectura.py:152: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f003_arquitectura.py::test_f003_r13_dominio_y_aplicacion_no_importan_proveedores - AssertionError: assert {'domain\\mod...ity', 'yaml']} == {}
FAILED tests/test_f003_arquitectura.py::test_f003_r8_ningun_modulo_incrusta_el_texto_del_prompt - AssertionError: assert {'infrastruct...venta de una'} == {}
2 failed, 1 deselected in 2.31s
```

La copia se borró después y el árbol real quedó limpio (`git status` sin
rastro de ella). Nótese que el test de R8 **no lleva escrita ninguna frase del
prompt**: las saca del YAML en tiempo de ejecución, así que sigue valiendo
cuando el prompt se reescriba.

### T15 · R17, R18 — el endpoint no existía

```bash
cd services/postventa-api && .venv/Scripts/python.exe -m pytest tests/test_f003_extraer_http.py -q
```

```
Traceback:
tests	est_f003_extraer_http.py:27: in <module>
    from interface_adapters.api.extraer import extraer_parte
E   ModuleNotFoundError: No module named 'interface_adapters.api.extraer'
=========================== short test summary info ===========================
ERROR tests/test_f003_extraer_http.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.34s
```
