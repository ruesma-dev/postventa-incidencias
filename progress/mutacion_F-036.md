<!-- progress/mutacion_F-036.md -->
# F-036 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-036 --workers 4` el 2026-09-29 15:33.

## Alcance

Origen del diff: **rama** (`a468367f31f1c552556c45f5cea2cfdebb2e5c03` .. `feature/F-036-importar-excel`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/domain/models/equivalencias.py` | 43 |
| `services/postventa-api/domain/models/errores.py` | 176 |
| `services/postventa-api/domain/models/importacion.py` | 621 |
| `services/postventa-api/domain/models/plantilla_incidencias.py` | 250 |
| `services/postventa-api/infrastructure/documentos/plantilla_yaml.py` | 259 |
| **Total** | **1349** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 153 |
| Mutantes evaluados | 153 |
| Muertos | 148 |
| Supervivientes | 5 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 4162.9 s |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

> **Cierre (implementer, 2026-09-29).** Los 5 son huecos reales de los tests de T6 y los cierran tests nuevos, comprobados mutante a mutante a mano (sin repetir la campaña, de 69 min). Detalle en `progress/impl_F-036.md`, Bloque 1.

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/infrastructure/documentos/plantilla_yaml.py:56` [entero]

- Original: `MIN_EJEMPLOS = 2`
- Mutado:   `MIN_EJEMPLOS = 3`

#### Análisis (implementer, 2026-09-29)

> Por qué ningún test lo caza: Hueco real: ningún test cargaba un YAML con exactamente **2** ejemplos (el real trae 3; el test de bordes probaba 1 y 5). Test nuevo `test_f036_r5_dos_ejemplos_se_admiten_cuatro_no` (2 valen).
> Decisión: **test nuevo**. Comprobado a mano: con el mutante aplicado, `tests/test_f036_configuracion_plantilla.py` da 1 failed, 101 passed; sin él, 102 passed.

### 2. `services/postventa-api/infrastructure/documentos/plantilla_yaml.py:57` [entero]

- Original: `MAX_EJEMPLOS = 3`
- Mutado:   `MAX_EJEMPLOS = 4`

#### Análisis (implementer, 2026-09-29)

> Por qué ningún test lo caza: Hueco real: se probaba 5 ejemplos, no **4**, así que un tope de 4 pasaba. El mismo test nuevo exige que 4 se rechacen con «de 2 a 3».
> Decisión: **test nuevo**. Comprobado a mano: con el mutante aplicado, `tests/test_f036_configuracion_plantilla.py` da 1 failed, 101 passed; sin él, 102 passed.

### 3. `services/postventa-api/infrastructure/documentos/plantilla_yaml.py:157` [comparacion]

- Original: `if not isinstance(crudo, list) or not MIN_EJEMPLOS <= len(crudo) <= MAX_EJEMPLOS:`
- Mutado:   `if not isinstance(crudo, list) or not MIN_EJEMPLOS < len(crudo) <= MAX_EJEMPLOS:`

#### Análisis (implementer, 2026-09-29)

> Por qué ningún test lo caza: Hueco real, el mismo borde que el 1: `<` rechaza 2 ejemplos. Lo mata el test nuevo de 2 ejemplos.
> Decisión: **test nuevo**. Comprobado a mano: con el mutante aplicado, `tests/test_f036_configuracion_plantilla.py` da 1 failed, 101 passed; sin él, 102 passed.

### 4. `services/postventa-api/infrastructure/documentos/plantilla_yaml.py:167` [entero]

- Original: `for numero, ejemplo in enumerate(crudo, start=1):`
- Mutado:   `for numero, ejemplo in enumerate(crudo, start=2):`

#### Análisis (implementer, 2026-09-29)

> Por qué ningún test lo caza: Hueco real: ningún test miraba el número del ejemplo en el motivo. Test nuevo `test_f036_t6_el_error_de_ejemplo_dice_cual` («ejemplo 1:», «ejemplo 2:»).
> Decisión: **test nuevo**. Comprobado a mano: con el mutante aplicado, `tests/test_f036_configuracion_plantilla.py` da 1 failed, 101 passed; sin él, 102 passed.

### 5. `services/postventa-api/infrastructure/documentos/plantilla_yaml.py:184` [comparacion]

- Original: `if len(fila["Descripción corta"]) > MAX_DESCRIPCION:`
- Mutado:   `if len(fila["Descripción corta"]) >= MAX_DESCRIPCION:`

#### Análisis (implementer, 2026-09-29)

> Por qué ningún test lo caza: Hueco real: no había ejemplo con descripción de **128** exactos. Test nuevo `test_f036_r5_ejemplo_con_descripcion_de_128_se_admite`.
> Decisión: **test nuevo**. Comprobado a mano: con el mutante aplicado, `tests/test_f036_configuracion_plantilla.py` da 1 failed, 101 passed; sin él, 102 passed.

