# services/postventa-api/tests_bbdd/__init__.py
"""La suite que necesita una base de datos de verdad (F-005, design §7.2).

Los tests viven en el subdirectorio `tests/`, y **eso no es un capricho de
organización**: `harness/alcance.py` decide qué es código de producción
—lo que se mide con la puerta de cobertura y lo que se muta en la campaña—
excluyendo las rutas en las que `tests` aparece como **segmento completo**.
Con los ficheros directamente en `tests_bbdd/` no lo aparece, así que 59 de
los 163 mutantes de la feature caían sobre tests que se saltan solos y
sobrevivían todos.

Sigue sin poder colgar de `services/postventa-api/tests/`, que es lo que
haría el arreglo obvio: allí rige el `conftest.py` con la guarda `sin_red` de
F-003, y esta suite necesita abrir una conexión. Un directorio propio con su
`tests/` dentro cumple las dos cosas sin tocar ni el arnés ni la guarda.

El arreglo de fondo —que `harness/alcance.py` reconozca cualquier suite y no
solo la llamada `tests`— es genérico, tocaría a todas las features y viajaría
a `arnes-base`: su sitio es **F-017**, no esta feature.
"""
