# services/postventa-api/domain/models/schemas.py
"""Registro de schemas: qué campos pide cada prompt (F-004, R5).

Existe por un obstáculo concreto de la vía B del diseño (`design.md` §2). El
adaptador de Gemini mandaba **siempre** el schema de los nueve campos del
parte, incrustado en la llamada, así que un segundo prompt —el de la firma—
habría recibido el schema equivocado y el modelo habría devuelto nueve campos
donde se le pedía uno.

Se arregla usando algo que ya existía y hasta ahora era decorativo:
`PromptSpec.schema` ya lleva el **nombre** del schema. El adaptador resuelve
ese nombre contra este registro y deja de saber de memoria cuál toca.

Lo que **no** cambia es la regla de F-003: la lista de campos vive en el
dominio y es fuente única, tanto para el contrato como para lo que se le manda
al modelo. Los campos no se declaran en el YAML: son contrato, no
configuración.
"""

from __future__ import annotations

from collections.abc import Mapping

from domain.models.errores import SchemaDesconocido
from domain.models.extraccion import CAMPOS_DEL_PARTE
from domain.models.firma import CAMPOS_DE_LA_FIRMA

#: Los schemas que el dominio conoce y los campos de cada uno.
#:
#: Las dos tuplas se **reutilizan**, no se copian: una tercera lista de campos
#: que mantener a mano es exactamente el fallo que F-003 evitó generando el
#: schema desde el dominio.
CAMPOS_POR_SCHEMA: Mapping[str, tuple[str, ...]] = {
    "parte_posventa": CAMPOS_DEL_PARTE,
    "firma_cliente": CAMPOS_DE_LA_FIRMA,
}


def campos_del_schema(nombre: str) -> tuple[str, ...]:
    """Los campos de ese schema, o `SchemaDesconocido` si no está registrado.

    No hay valor de consolación: devolver una tupla vacía ante un nombre mal
    escrito dejaría salir la llamada con un schema sin campos, que es el fallo
    silencioso y caro que este registro evita.
    """
    if nombre not in CAMPOS_POR_SCHEMA:
        raise SchemaDesconocido(
            f"el prompt pide el schema '{nombre}', que el dominio no registra; "
            f"registrados: {', '.join(sorted(CAMPOS_POR_SCHEMA))}"
        )
    return CAMPOS_POR_SCHEMA[nombre]
