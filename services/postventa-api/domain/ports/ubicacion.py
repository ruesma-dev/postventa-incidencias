# services/postventa-api/domain/ports/ubicacion.py
"""El puerto de la ubicación: dónde está la reclamación en Sigrid (F-013).

Para archivar en la biblioteca de Posventa hay que saber **en qué obra y en qué
unidad** está la reclamación, y eso lo dice el ERP: `rcp.upvide → upv` y
`upv.obride → obr` (`specs/F-013-archivo-posventa/design.md` §1). La `unidad`
que la IA leyó del papel **no** sirve ni para casar ni para componer ninguna
carpeta (R9): es una lectura con confianza, y la de Sigrid es el dato del ERP
de la reclamación que se va a cerrar.

## Dos lecturas, y ninguna escritura

- `leer_ubicacion` — la de la reclamación (R6, R7).
- `leer_unidades_del_numero` — las unidades de posventa de las obras con el
  **número** de la obra del parte (R44, R50). La obra se casa por su número
  (`677  MIRASIERRA` es la de la 0677), así que todo lo que en Sigrid tenga el
  mismo número va a la misma carpeta de Posventa, y hay que poder comprobar que
  es **una** obra y que la carpeta de unidad no la comparten dos unidades.

Las dos son lecturas por `sql/read`: nada de este puerto escribe en el ERP de
producción. Su fábrica **no** exige `CIERRE_HABILITADO`, que es la ventana de
la escritura del cierre: con ella cerrada se tiene que poder archivar.

## Por qué un puerto aparte y no un método más de `ErpPort`

Por lo mismo que F-012 hizo `GraficoPort`: `ErpPort` documenta «tres métodos y
ni uno más», su doble y sus tests siguen tal cual, y su fábrica exige la ventana
del cierre (`design.md` §3.3, §6.2).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.models.destino_posventa import UbicacionReclamacion, UnidadDeObra

__all__ = ["UbicacionPort"]


@runtime_checkable
class UbicacionPort(Protocol):
    """Quien sabe situar una reclamación de Sigrid en su obra y su unidad."""

    def leer_ubicacion(
        self, *, codigo_reclamacion: str
    ) -> tuple[UbicacionReclamacion, ...]:
        """Todas las filas de la reclamación con ese código (en forma de ERP).

        Una sola consulta parametrizada, acotada por el tipo de concepto de la
        reclamación. Devuelve **todas** las filas: el dominio decide qué es
        cero, una o varias (R7). Una fila con la unidad o la obra a `None` es
        una reclamación que no cuelga de ninguna unidad de posventa.

        Si la lectura falla —red, tiempo o configuración—, levanta y no
        devuelve nada a medias: con `posventa`, archivar depende de
        `sigrid-api`, y sin la ubicación no se sube nada (R41, 503).
        """
        ...

    def leer_unidades_del_numero(
        self, *, codigo_obra: str
    ) -> tuple[UnidadDeObra, ...]:
        """Las unidades de posventa de las obras con el número de `codigo_obra`.

        O, si el código no es numérico, las de las obras con ese mismo código.
        El SQL **preselecciona** —`%677` deja pasar `1677`— y el dominio
        vuelve a filtrar por número (`obras_del_mismo_numero`, §4.7). Cada fila
        lleva `obra_ref`, una referencia **opaca** de su obra que solo sirve
        para contar obras distintas y que no sale nunca de la lectura (R23).

        Si la respuesta llega al techo de filas de la pasarela, puede venir
        cortada, y quien la usa lo trata como «sin verificar» (R44). Si la
        lectura falla, levanta, igual que `leer_ubicacion` (R41).
        """
        ...
