<!-- progress/mutacion_F-072.md -->
# F-072 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-072 --base 6994cb0 --workers 1` el 2026-11-18 04:43.

## Alcance

Origen del diff: **rama** (`6994cb0fc2d5ad2d9dddeda4d00c849e8d3dd87d` .. `feature/F-072-tipo-reclamacion-sigrid`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/postventa-api/application/pipelines/contexto_importacion.py` | 8 | 1 |
| `services/postventa-api/application/pipelines/paso_importacion.py` | 20 | 0 — sin mutantes |
| `services/postventa-api/application/pipelines/plantilla.py` | 15 | 0 — sin mutantes |
| `services/postventa-api/application/pipelines/revision.py` | 45 | 11 |
| `services/postventa-api/application/pipelines/tipos_reclamacion.py` | 77 | 10 |
| `services/postventa-api/domain/models/importacion.py` | 18 | 2 |
| `services/postventa-api/domain/models/plantilla_incidencias.py` | 64 | 4 |
| `services/postventa-api/domain/models/revision.py` | 111 | 20 |
| `services/postventa-api/domain/models/volcado.py` | 16 | 0 — sin mutantes |
| `services/postventa-api/domain/ports/tipos_reclamacion.py` | 58 | 2 |
| `services/postventa-api/infrastructure/documentos/plantilla_yaml.py` | 15 | 1 |
| `services/postventa-api/infrastructure/persistencia/sentencias_bandeja.py` | 10 | 1 |
| `services/postventa-api/infrastructure/persistencia/sentencias_revision.py` | 15 | 0 — sin mutantes |
| `services/postventa-api/infrastructure/sigrid/consultas_tipos_reclamacion.py` | 71 | 9 |
| `services/postventa-api/infrastructure/sigrid/fabrica.py` | 42 | 0 — sin mutantes |
| `services/postventa-api/infrastructure/sigrid/tipos_reclamacion.py` | 51 | 0 — sin mutantes |
| `services/postventa-api/interface_adapters/api/bandeja.py` | 6 | 0 — sin mutantes |
| `services/postventa-api/interface_adapters/api/importar.py` | 16 | 2 |
| `services/postventa-api/interface_adapters/api/plantilla.py` | 18 | 2 |
| `services/postventa-api/interface_adapters/api/revision.py` | 35 | 5 |
| **Total** | **711** | **70** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 70 |
| Mutantes evaluados | 41 |
| Muertos | 38 |
| Supervivientes | 3 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 30924.4 s |
| SHA de HEAD medido | `43b472c1230d8f6178c16c1bd1cdf6549c679ec3` |
| Línea base (s) — `services/postventa-api` | 1474.7 |
| Media por mutante evaluado (s) | 754.3 |
| Timeout efectivo por mutante (s) | 3600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 3600 |
| Workers | 1 |
| Un mutante por línea | sí — 70 generados → 41 candidatos, uno por línea |
| Muestreo | no: campaña completa (41 candidatos ≤ tope 100 del nivel `critico`) |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 718.2 (41 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/postventa-api/domain/models/importacion.py:604` [veracidad]

- Original: `if etiqueta_listado is None`
- Mutado:   `if not etiqueta_listado`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/postventa-api/interface_adapters/api/importar.py:218` [veracidad]

- Original: `if tipos is None:`
- Mutado:   `if not tipos:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/postventa-api/interface_adapters/api/plantilla.py:92` [veracidad]

- Original: `if tipos is None:`
- Mutado:   `if not tipos:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

## No muertos: código de salida

| Fichero:línea | Operador | Veredicto | Código |
|---|---|---|---|
| `services/postventa-api/domain/models/importacion.py:604` | veracidad | superviviente | 0 |
| `services/postventa-api/interface_adapters/api/importar.py:218` | veracidad | superviviente | 0 |
| `services/postventa-api/interface_adapters/api/plantilla.py:92` | veracidad | superviviente | 0 |

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/postventa-api/application/pipelines/paso_importacion.py` — 20 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/postventa-api/application/pipelines/plantilla.py` — 15 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/postventa-api/domain/models/volcado.py` — 16 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/postventa-api/infrastructure/persistencia/sentencias_revision.py` — 15 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/postventa-api/infrastructure/sigrid/fabrica.py` — 42 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/postventa-api/infrastructure/sigrid/tipos_reclamacion.py` — 51 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/postventa-api/interface_adapters/api/bandeja.py` — 6 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

## Análisis de supervivientes

Lo escribe el implementer el 2026-11-18 (T22, rigor `critico`) sobre la campaña serie de arriba (`--base 6994cb0 --sin-seleccion --timeout 3600 --workers 1`: 41 evaluados, 38 muertos, 3 supervivientes, 0 timeouts). Lo generado por la herramienta no se toca; los bloques «Análisis (PENDIENTE del implementer)» de cada superviviente se completan **aquí**.

### Reproducción a mano (C4 bis)

Cada mutante se aplicó al fichero con la sustitución exacta de la tabla, byte a byte, sobre la línea indicada. Después se corrieron **35 ficheros de test**: los once `tests/test_f072_*.py` y todos los que importan o llaman a `importar_excel`, `descargar_plantilla`, `models.importacion`, `validar_filas` o `_validar_fila` (F-036, F-053, F-056, F-059, F-060, F-065 y F-071, más los `utiles_*`). Por último se restauraron los bytes originales. Orden: `services/postventa-api/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider <los 35>`, desde `services/postventa-api`.

| Fichero:línea | Original → mutado | Código | Resultado |
|---|---|---|---|
| `domain/models/importacion.py:604` | `if etiqueta_listado is None` → `if not etiqueta_listado` | 0 | 2790 passed, 71 skipped in 442.25s |
| `interface_adapters/api/importar.py:218` | `if tipos is None:` → `if not tipos:` | 0 | 2790 passed, 71 skipped in 442.07s |
| `interface_adapters/api/plantilla.py:92` | `if tipos is None:` → `if not tipos:` | 0 | 2790 passed, 71 skipped in 402.71s |

Los tres se reproducen: no son supervivientes falsos de caché ni de entorno. Tras la reproducción, `git status --short` solo muestra `progress/mutacion_F-072.json` y `progress/mutacion_F-072.md` (sin versionar). El árbol de código queda limpio.

### 1. `domain/models/importacion.py:604`: EQUIVALENTE

**Por qué ningún test lo caza.** El original y el mutante solo se separan si `etiqueta_listado == ""`, y `etiqueta_listado` sale de `f.tasado(LISTADO, listados, …)`, que devuelve `None` o una clave de `listados`. Para que valga `""` haría falta una de estas dos cosas, y ninguna es alcanzable:

- **La celda.** `_Fila.celda` pasa por `_vacia`, que trata una cadena vacía o con solo blancos (`str.strip()`, que incluye `\t`, `\n` y el espacio duro) como celda en blanco. Entonces `_texto_tasado` da `None` y `tasado` sale por `None` antes de casar nada. A `casar_con_lista` solo llega un texto no blanco.
- **La lista.** En producción, `listados` sale únicamente de `listas_con_tipos(listas, tipos)` (`paso_importacion.py:247` y `:328`; el YAML rechaza la clave `listados`, `plantilla_yaml.py:209`). Sus etiquetas las fabrica `tipos_del_desplegable`: `_con_codigo(nombre, codigo)` es `codigo` o `"<nombre> (<codigo>)"`. Y `leer_tipos_reclamacion` descarta todo código nulo o en blanco tras `strip()`. **Quien construye el dato** garantiza, por tanto, que ninguna etiqueta está vacía. Aunque la hubiera, un valor no blanco no casa con `""`: ni es igual a ella, ni su `clave_de_ubicacion` (NFC + `strip` + `casefold`) es `""`.

**Decisión.** Equivalente: no hay test no artificioso que lo mate, y uno que inyectara un `ListasCerradas` con una etiqueta `""` probaría un estado imposible. No se quita ningún código defensivo, así que RM6 no aplica. `is None` es la forma de las convenciones.

### 2. `interface_adapters/api/importar.py:218` y 3. `interface_adapters/api/plantilla.py:92`: EQUIVALENTES

**Por qué ningún test lo caza.** `tipos` es `FuenteTiposReclamacion | None`, y `FuenteTiposReclamacion = Callable[[], tuple[TipoReclamacion, ...]]` (`application/pipelines/tipos_reclamacion.py:38`). `not tipos` y `tipos is None` solo se separan con una fuente falsa en contexto booleano, es decir, un invocable con `__bool__` que devuelve `False` o con `__len__ == 0`.

- En producción, `function_app.py:1391` (`descargar_plantilla(req.params.get("obra"))`) y `:1453` (`importar_excel(ficheros, req.form.get("usuario_oid"))`) no pasan `tipos`: llega `None` y se construye `fuente_de_tipos(...)`, que es un `functools.partial`. `partial` no define `__bool__` ni `__len__` y siempre es verdadero.
- Los tests pasan funciones o lambdas, también verdaderas siempre.

**Decisión.** Equivalentes, por el mismo patrón que los parámetros vecinos (`catalogo_obra`, `ubicaciones`, `bandeja`, `lector`), que también se comparan con `is None`. Un test con un invocable falso a propósito sería artificioso: ese invocable no existe en el sistema. RM6 no aplica.

### Demostración ejecutable (RM5)

Se lanzó el guion siguiente desde `services/postventa-api` con `PYTHONPATH=. .venv/Scripts/python.exe equivalentes.py` (guion en el scratchpad de la sesión, copiado aquí entero para que el reviewer lo reproduzca):

```python
# equivalentes.py: demostración ejecutable de los tres supervivientes de F-072 (RM5).
import itertools
from functools import partial

from domain.models.casado_con_lista import casar_con_lista
from domain.models.importacion import LISTADO, CeldaLeida, FilaLeida, _Fila
from domain.models.plantilla_incidencias import tipos_del_desplegable
from domain.ports.catalogo_obra import LecturaCatalogo
from domain.ports.tipos_reclamacion import FilaTipoReclamacion
from application.pipelines.tipos_reclamacion import (
    fuente_de_tipos,
    leer_tipos_reclamacion,
)

print("== Superviviente 1: importacion.py:604 ==")
for valor in ("", " ", "\t", " ", "  \n "):
    f = _Fila(FilaLeida(numero=2, celdas={LISTADO: CeldaLeida(valor, False, False, valor)}))
    print(f"_texto_tasado({valor!r}) -> {f._texto_tasado(LISTADO)!r}")


class Puerto:
    def __init__(self, filas):
        self.filas = filas

    def leer(self):
        return LecturaCatalogo(filas=tuple(self.filas), llego_al_techo=False)


codigos = (None, "", " ", "\t", "0001", " 0002 ", " ")
nombres = (None, "", "  ", "Humedades", " Grietas ")
filas = [
    FilaTipoReclamacion(codigo=c, nombre=n, posicion=i)
    for i, (c, n) in enumerate(itertools.product(codigos, nombres))
]
tipos = leer_tipos_reclamacion(Puerto(filas))
etiquetas = [o.etiqueta for o in tipos_del_desplegable(tipos)]
print(f"filas leídas={len(filas)} tipos={len(tipos)} etiquetas={etiquetas!r}")
print(f"alguna etiqueta vacía o en blanco: {any(not e.strip() for e in etiquetas)}")
print(f"casar_con_lista('x', ['']) -> {casar_con_lista('x', [''])!r}")

print("== Supervivientes 2 y 3: importar.py:218 y plantilla.py:92 ==")
fuente = fuente_de_tipos(Puerto([]))
print(f"type={type(fuente).__name__} bool(fuente)={bool(fuente)}")
print(f"partial define __bool__: {hasattr(partial, '__bool__')}; __len__: {hasattr(partial, '__len__')}")
print(f"bool(lambda: ())={bool(lambda: ())}")
```

Salida real:

```
== Superviviente 1: importacion.py:604 ==
_texto_tasado('') -> None
_texto_tasado(' ') -> None
_texto_tasado('\t') -> None
_texto_tasado('\xa0') -> None
_texto_tasado('  \n ') -> None
filas leídas=35 tipos=2 etiquetas=['0001', '0002']
alguna etiqueta vacía o en blanco: False
casar_con_lista('x', ['']) -> None
== Supervivientes 2 y 3: importar.py:218 y plantilla.py:92 ==
type=partial bool(fuente)=True
partial define __bool__: False; __len__: False
bool(lambda: ())=True
```

Cómo se lee: de las 35 combinaciones de código y nombre, las que traen código nulo o en blanco (incluido el espacio duro) se descartan. Quedan dos tipos, y ninguna etiqueta está en blanco. Ninguna celda en blanco llega a casarse, y la fuente de producción es siempre verdadera.

### Veredicto y aceptación pendiente

| Superviviente | Veredicto | Test nuevo |
|---|---|---|
| `importacion.py:604` | equivalente (demostrado arriba) | no |
| `importar.py:218` | equivalente (demostrado arriba) | no |
| `plantilla.py:92` | equivalente (demostrado arriba) | no |

En rigor `critico`, cada equivalente necesita la **aceptación escrita del humano** (C4 bis) y que el reviewer reproduzca una muestra de uno (RM5). Las dos cosas quedan pendientes. Las declaraciones de «Ficheros sin mutantes» siguen en `PENDIENTE`: quedan fuera de este encargo.

### RM7 (verificación del líder)

El líder aplicó a mano tres mutantes de orden que adelantan la llamada a `tipos()` antes de `leer_catalogo` y corrió cada fichero de test con `pytest -x`:

| Fichero mutado | Mutante | Test | Resultado |
|---|---|---|---|
| `application/pipelines/paso_importacion.py` | `tipos()` antes de `leer_catalogo` | `tests/test_f072_importacion.py` | 1 failed / 11 passed: muerto |
| `application/pipelines/revision.py` | `tipos()` antes de `leer_catalogo` | `tests/test_f072_revision_http.py` | 1 failed / 2 passed: muerto |
| `application/pipelines/plantilla.py` | `tipos()` antes de `leer_catalogo` | `tests/test_f072_plantilla.py` | 1 failed / 13 passed: muerto |

Los tres murieron con un test de la propia feature, y el líder restauró el árbol.
