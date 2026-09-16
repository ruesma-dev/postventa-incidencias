# services/postventa-api/tests/utiles_rutas.py
"""Las rutas que el host publica, leídas **una sola vez por proceso**.

`function_app.app.get_functions()` **no es idempotente**: a la segunda llamada
levanta `ValueError: Function health does not have a unique function name`,
porque el `FunctionApp` vuelve a registrar lo que ya tenía. Con una caché por
fichero de test bastaría mientras solo un fichero mirase rutas; en cuanto son
dos, el segundo revienta y el fallo **no habla de ninguno de los dos** —dice
que `health` está repetida—, que es de los que cuestan media tarde.

Por eso la caché vive aquí y no en cada fichero: es del proceso, que es a lo
que pertenece el problema. F-026 lo descubrió con `/api/aprobar` y F-028 se lo
encontró al añadir `/api/estado`.

Lo que se lee aquí es **lo que se despliega**, y no el módulo: el decorador
`@app.route(...)` deja en `function_app` un `FunctionBuilder`, y la ruta, los
métodos y el nivel de autenticación de verdad son los que salen de
`get_functions()`.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

__all__ = ["ruta_registrada", "rutas_registradas"]


@lru_cache(maxsize=1)
def rutas_registradas() -> dict[str, Any]:
    """Lo que el host publica, por nombre de función. **Se construye una vez.**"""
    import function_app

    return {
        funcion.get_function_name(): funcion
        for funcion in function_app.app.get_functions()
    }


def ruta_registrada(nombre: str) -> Any:
    """La ruta que publica el host, o un fallo que dice que no existe."""
    registradas = rutas_registradas()
    assert nombre in registradas, f"el host no publica ninguna ruta «{nombre}»"
    return registradas[nombre]
