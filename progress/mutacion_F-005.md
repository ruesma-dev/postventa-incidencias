<!-- progress/mutacion_F-005.md -->
# F-005 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-005` el 2026-08-19 23:09.

## Alcance

Origen del diff: **rama** (`e3f5fcda89c3d1842fce64eea9633d809232cdb4` .. `feature/F-005-persistencia`).

| Fichero | Líneas en alcance |
|---|---|
| `services/postventa-api/application/pipelines/paso_persistencia.py` | 63 |
| `services/postventa-api/config/settings.py` | 93 |
| `services/postventa-api/domain/models/errores.py` | 56 |
| `services/postventa-api/domain/models/persistencia.py` | 196 |
| `services/postventa-api/domain/ports/persistencia.py` | 131 |
| `services/postventa-api/infrastructure/persistencia/__init__.py` | 2 |
| `services/postventa-api/infrastructure/persistencia/arranque.py` | 130 |
| `services/postventa-api/infrastructure/persistencia/conexion.py` | 148 |
| `services/postventa-api/infrastructure/persistencia/ddl.py` | 466 |
| `services/postventa-api/infrastructure/persistencia/fabrica.py` | 89 |
| `services/postventa-api/infrastructure/persistencia/mapeo.py` | 230 |
| `services/postventa-api/infrastructure/persistencia/repositorio_pg.py` | 250 |
| `services/postventa-api/infrastructure/persistencia/sentencias.py` | 368 |
| `services/postventa-api/tests_bbdd/__init__.py` | 20 |
| **Total** | **2242** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 106 |
| Mutantes evaluados | 106 |
| Muertos | 103 |
| Supervivientes | 0 |
| Timeouts | 3 |
| Tiempo total | 330.4 s |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Timeouts

- `services/postventa-api/infrastructure/persistencia/ddl.py:131` services/postventa-api/infrastructure/persistencia/ddl.py:131 [entero] posicion = fin if salto == -1 else salto -> posicion = fin if salto == -2 else salto
- `services/postventa-api/infrastructure/persistencia/ddl.py:158` services/postventa-api/infrastructure/persistencia/ddl.py:158 [aritmetico] posicion += 1 -> posicion -= 1
- `services/postventa-api/infrastructure/persistencia/ddl.py:162` services/postventa-api/infrastructure/persistencia/ddl.py:162 [aritmetico] posicion += 1 -> posicion -= 1


### Análisis de los tres timeouts (T23, escrito a mano)

> Este bloque lo escribe el implementer y **el generador no lo conserva**: la
> sección «Timeouts» se regenera como lista pelada en cada campaña, a
> diferencia de la de supervivientes. Si se repite la campaña, hay que traerlo
> de vuelta. La copia durable vive en `progress/impl_F-005.md`.
>
> Traído de vuelta el 2026-08-19 tras la campaña de los dos arreglos de
> review. Los tres timeouts son **los mismos tres de siempre**, en las mismas
> tres líneas: no ha aparecido ninguno nuevo.

Los tres caen en el bucle del troceador de `ddl.sentencias` y los tres son el
**mismo defecto**: la mutación destruye el avance del escáner y el bucle deja
de terminar. No son mutantes que se escapen sin que nadie se entere —que es lo
que preocupa de un superviviente—, sino mutantes que **cuelgan la suite**: con
cualquiera de los tres aplicado, `bash harness/init.sh` no vuelve nunca, y eso
es tan visible como un test en rojo.

No se pueden «matar» con un test: un test no puede afirmar nada sobre una
función que no retorna. Se comprueban ejecutándolos con un reloj por fuera.

Comprobado el 2026-08-19 cargando `ddl.py` con la mutación aplicada en un
espacio de nombres aparte —sin tocar el repositorio— y ejecutándolo bajo
`timeout 15`. Los tres devuelven código de salida **124**, que es como
`timeout` dice «lo he matado yo, seguía corriendo»:

| Mutante | Por qué no termina | Caso que lo cuelga | Salida |
|---|---|---|---|
| `ddl.py:131` `salto == -1` → `salto == -2` | `str.find` devuelve `-1` cuando no encuentra, nunca `-2`. Con un `--` final sin salto de línea, `posicion` pasa a valer `-1` en vez de `fin`, y el bucle vuelve a entrar por el final del texto una y otra vez. | `CREATE SCHEMA IF NOT EXISTS postventa; -- cola` | exit 124 |
| `ddl.py:158` `posicion += 1` → `posicion -= 1` | Es el avance tras consumir un `;`. Retrocediendo, el escáner vuelve al carácter anterior al `;`, lo vuelve a leer, vuelve al `;`, y así siempre. | `CREATE SCHEMA postventa;CREATE TABLE postventa.x ()` | exit 124 |
| `ddl.py:162` `posicion += 1` → `posicion -= 1` | Es el avance del carácter suelto, el caso general. Retrocediendo, `posicion` no llega jamás a `fin`. | el mismo | exit 124 |

Los dos primeros ya estaban en la campaña de las 15:33 y el tercero apareció
en la de las 16:13, cuando los tests nuevos del troceado empezaron a recorrer
ese camino. Que aparezca un timeout **más** al añadir tests no es una
regresión: significa que ahora hay tests que entran por esa línea.

**Advertencia (observación O-C de la review):** la etiqueta `timeout` de
`harness/mutacion.py` también se dispara por **lentitud de la máquina bajo
carga**, no solo por no-terminación. Por eso el análisis de arriba no se apoya
en la etiqueta, sino en la comprobación con reloj externo. Los tres timeouts
de esta campaña coinciden línea a línea y operador a operador con los ya
verificados, así que no hace falta repetir la comprobación.
