<!-- progress/mutacion_F-036_bloque10ter.md -->
# F-036 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-036 --base becb693 --workers 6` el 2026-10-01 01:11.

## Alcance

Origen del diff: **rama** (`becb693f6b403369287deba5af1923fbf6a3b8d6` .. `feature/F-036-importar-excel`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/infrastructure/documentos/excel_openpyxl.py` | 84 |
| `services/postventa-api/scripts/contar_elementos_xml_f036.py` | 75 |
| **Total** | **159** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 22 |
| Mutantes evaluados | 22 |
| Muertos | 18 |
| Supervivientes | 4 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Tiempo total | 1436.5 s |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

> **Cierre (implementer, 2026-10-01).** Los 4 supervivientes de la campaña
> quedan cerrados con 2 tests nuevos (commit `F-036 T38`), comprobados a mano
> mutante a mutante: **22 mutantes, 18 muertos en la campaña + 4 muertos tras
> reforzar los tests, 0 equivalentes**. La campaña no se ha repetido entera.

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/infrastructure/documentos/excel_openpyxl.py:419` [entero]

- Original: `TROZO_DE_LECTURA = 64 * 1024`
- Mutado:   `TROZO_DE_LECTURA = 65 * 1024`

#### Análisis (implementer, 2026-10-01): hueco real, cerrado con un test nuevo

> Por qué ningún test lo cazaba: el tamaño del trozo no cambia el recuento ni
> dónde se corta (se corta por elemento, no por trozo), así que ningún test de
> comportamiento lo ve. Pero §5.2 fija la lectura «en trozos (`read(64 KiB)`)»,
> que es lo que garantiza el *streaming*: ninguna parte se descomprime entera.
> Decisión: **test nuevo**,
> `test_f036_r117_cada_parte_se_lee_por_trozos_de_64_kib` (un espía de
> `zipfile.ZipExtFile.read` exige que toda lectura del recuento sea de 64 KiB, y
> más de una por parte con la de 20 MiB). Comprobado a mano, aplicando el
> mutante sobre el árbol y pasando el test: **cae** (`1 failed`).

### 2. `services/postventa-api/infrastructure/documentos/excel_openpyxl.py:419` [entero]

- Original: `TROZO_DE_LECTURA = 64 * 1024`
- Mutado:   `TROZO_DE_LECTURA = 64 * 1025`

#### Análisis (implementer, 2026-10-01): hueco real, cerrado con un test nuevo

> Por qué ningún test lo cazaba: el tamaño del trozo no cambia el recuento ni
> dónde se corta (se corta por elemento, no por trozo), así que ningún test de
> comportamiento lo ve. Pero §5.2 fija la lectura «en trozos (`read(64 KiB)`)»,
> que es lo que garantiza el *streaming*: ninguna parte se descomprime entera.
> Decisión: **test nuevo**,
> `test_f036_r117_cada_parte_se_lee_por_trozos_de_64_kib` (un espía de
> `zipfile.ZipExtFile.read` exige que toda lectura del recuento sea de 64 KiB, y
> más de una por parte con la de 20 MiB). Comprobado a mano, aplicando el
> mutante sobre el árbol y pasando el test: **cae** (`1 failed`).

### 3. `services/postventa-api/infrastructure/documentos/excel_openpyxl.py:488` [booleano]

- Original: `target=object(), forbid_dtd=True, forbid_entities=True, forbid_external=True`
- Mutado:   `target=object(), forbid_dtd=True, forbid_entities=False, forbid_external=True`

#### Análisis (implementer, 2026-10-01): defensa redundante, fijada con un test nuevo

> Por qué ningún test lo cazaba: con `forbid_dtd=True` cualquier `<!DOCTYPE`
> se rechaza al empezar, y las declaraciones de entidades y las entidades
> externas solo pueden venir dentro de una DTD: la defensa de este parámetro no
> llega a actuar nunca y no se ve desde fuera (el mutante hermano,
> `forbid_dtd=False`, sí cae con el test `dtd`). Es defensa en profundidad, por
> si un día se relaja la primera.
> Decisión: en vez de pedir al humano que lo acepte como equivalente, **test
> nuevo** que fija la configuración del analizador,
> `test_f036_r117_el_analizador_lleva_las_tres_defensas_de_defusedxml` (los
> cuatro manejadores de `defusedxml` puestos, el de apertura como único en
> Python, y sin manejador por defecto, de texto ni de comentarios). Comprobado
> a mano, aplicando el mutante sobre el árbol y pasando el test: **cae**
> (`1 failed`).

### 4. `services/postventa-api/infrastructure/documentos/excel_openpyxl.py:488` [booleano]

- Original: `target=object(), forbid_dtd=True, forbid_entities=True, forbid_external=True`
- Mutado:   `target=object(), forbid_dtd=True, forbid_entities=True, forbid_external=False`

#### Análisis (implementer, 2026-10-01): defensa redundante, fijada con un test nuevo

> Por qué ningún test lo cazaba: con `forbid_dtd=True` cualquier `<!DOCTYPE`
> se rechaza al empezar, y las declaraciones de entidades y las entidades
> externas solo pueden venir dentro de una DTD: la defensa de este parámetro no
> llega a actuar nunca y no se ve desde fuera (el mutante hermano,
> `forbid_dtd=False`, sí cae con el test `dtd`). Es defensa en profundidad, por
> si un día se relaja la primera.
> Decisión: en vez de pedir al humano que lo acepte como equivalente, **test
> nuevo** que fija la configuración del analizador,
> `test_f036_r117_el_analizador_lleva_las_tres_defensas_de_defusedxml` (los
> cuatro manejadores de `defusedxml` puestos, el de apertura como único en
> Python, y sin manejador por defecto, de texto ni de comentarios). Comprobado
> a mano, aplicando el mutante sobre el árbol y pasando el test: **cae**
> (`1 failed`).

