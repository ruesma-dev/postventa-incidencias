# services/postventa-api/infrastructure/sharepoint/graph.py
"""El adaptador de SharePoint sobre Microsoft Graph (F-006).

Único módulo del servicio que conoce Graph, igual que
`infrastructure/llm/gemini.py` es el único que conoce el SDK de Gemini.

## La puerta 1: el constructor muerde

`CLAUDE.md` prohíbe sin matices subir nada al SharePoint de Posventa desde
local, y esa regla no se cumple por disciplina: se cumple porque **este
constructor se niega** cuando `ENTORNO` no es `dev` ni `pro`.

Está aquí y no solo en la fábrica **a propósito** (`design.md` §5): quien
componga las piezas de otra manera —un script suelto, un `python -c`, un test
«solo para probar»— se topa igual con la puerta. Y como `tests/conftest.py`
fija `ENTORNO=test` para toda la suite, dentro de los tests este adaptador
**no se puede construir**. Ese es el mecanismo, y tiene su test en
`tests/test_f006_fabrica.py`.
"""

from __future__ import annotations

from domain.models.errores import ArchivoDeshabilitado

__all__ = ["ENTORNOS_CON_ARCHIVO", "AdaptadorSharePointGraph", "exigir_entorno_con_archivo"]

#: Los únicos entornos desde los que se archiva de verdad.
#:
#: `local` y `test` **no** están, y añadir cualquier otro es abrir la puerta a
#: subir desde un sitio nuevo: que cueste un cambio visible en un test es
#: justamente el punto.
ENTORNOS_CON_ARCHIVO: tuple[str, ...] = ("dev", "pro")


def exigir_entorno_con_archivo(entorno: str) -> None:
    """Se niega si este no es sitio para archivar (R19).

    Vive aquí, junto al adaptador, y no en la fábrica, para que la fábrica lo
    importe de un solo sitio: dos listas de entornos permitidos divergen, y la
    que se quedara corta sería la que dejara subir desde donde no se debe.
    """
    if entorno not in ENTORNOS_CON_ARCHIVO:
        raise ArchivoDeshabilitado(
            f"el archivo en SharePoint solo se permite en "
            f"{', '.join(ENTORNOS_CON_ARCHIVO)}; aquí ENTORNO={entorno!r}. "
            f"Subir a SharePoint desde un puesto de trabajo está prohibido: "
            f"la única subida real se hace desde el entorno desplegado"
        )


class AdaptadorSharePointGraph:
    """Archiva partes en una biblioteca de SharePoint a través de Graph.

    Las operaciones llegan en T10; lo que ya está en pie es la puerta de
    entorno, que es lo que impide que exista una instancia de esta clase en
    una máquina de desarrollo.
    """

    def __init__(
        self,
        *,
        entorno: str,
        drive_id: str,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        timeout_s: int = 60,
        reintentos: int = 3,
    ) -> None:
        exigir_entorno_con_archivo(entorno)
        self._drive_id = drive_id
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._timeout_s = timeout_s
        self._reintentos = reintentos
