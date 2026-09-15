# services/postventa-api/application/pipelines/constancia.py
"""La regla de constancia del histórico de estado, en un solo sitio (F-028).

`design.md` §4 la escribe en una frase: **si el estado derivado no es el de la
última fila, se añade una fila**. De ahí salen las tres cosas que sostienen el
histórico —que un reproceso que no cambia nada no escriba nada, que la fila de
máquina vaya sin autor (R24), y que el relato no se llene de renglones
idénticos— y de ahí sale también que la regla no pueda estar escrita dos
veces.

## Por qué es un módulo y no una función privada en cada paso

La aplican **dos** pasos del pipeline: `paso_persistencia`, cuando se guarda un
veredicto, y `paso_cierre`, cuando la incidencia queda cerrada en el ERP. Es
exactamente el caso de `confianza.py` en F-004, y por los mismos dos motivos
que su cabecera escribió entonces: dos copias de una regla divergen el día que
alguien la corrija en una sola, y en una campaña de mutación **cada copia se
cuenta aparte**, con lo que la segunda se queda sin tests que la maten.

> `design.md` §8.2 no lista este fichero: lista los dos pasos. Es la única
> desviación de este bloque y va declarada en `progress/impl_F-028.md`.

## Constancia, nunca criterio (R26)

Lo que se escribe aquí **no decide nada**. El estado del parte se deriva de
`estado_del_parte`, que mira el veredicto, la última decisión humana y la traza
de cierre — nunca una fila de máquina. Si mañana faltara una de estas filas, el
estado seguiría siendo el correcto y lo único perdido sería una línea del
relato. Por eso `ultimo_estado_registrado` es lo único que se lee del histórico,
y se lee **solo** para no repetir fila.

## Y no decide la política de errores

Esta función deja subir lo que levante el repositorio. Los dos pasos tratan ese
fallo de forma **opuesta a propósito** —`paso_persistencia` lo deja salir,
`paso_cierre` se lo traga porque el ERP ya está escrito— y esa decisión es de
cada paso, no de la regla.
"""

from __future__ import annotations

from datetime import datetime

from domain.models.estado import DecisionEstado, EstadoParte, SituacionParte
from domain.ports.persistencia import RepositorioPartesPort

__all__ = ["anotar_estado"]


def anotar_estado(
    repositorio: RepositorioPartesPort,
    situacion: SituacionParte,
    *,
    hash_parte: str,
    estado: EstadoParte,
    ahora: datetime,
) -> DecisionEstado | None:
    """Añade la fila de constancia **solo si el estado cambió**.

    Devuelve la fila escrita, o `None` si no había nada que contar — que es el
    caso normal: en una remesa de 22 partes que se vuelve a subir, ninguno ha
    cambiado de estado y no se escribe ni una fila.

    La fila va **sin autor y sin motivo** (R23, R24): `decidido_por` a `None`
    **es** «lo decidió la máquina», y es toda la diferencia con una fila humana.
    Poner ahí `"sistema"` sería inventarse un autor y, peor, haría que una
    anotación pasara la puerta de `por_persona` y acabara decidiendo el estado
    de un parte.

    Tampoco lleva `huella_veredicto`: la huella dice **sobre qué veredicto
    exacto decidió una persona**, y es lo que hace que una aprobación deje de
    contar cuando el veredicto cambia (R19). Una constancia no concede nada, así
    que apuntarle una huella sería darle la forma de algo que sí.

    `situacion` llega de fuera y no se consulta aquí: quien llama suele
    necesitarla entera para derivar el estado, y preguntarla dos veces serían
    dos viajes más por parte a un servidor compartido.
    """
    if estado is situacion.ultimo_estado_registrado:
        return None

    fila = DecisionEstado(
        hash_parte=hash_parte,
        estado=estado,
        decidido_at_utc=ahora,
        estado_anterior=situacion.ultimo_estado_registrado,
        decidido_por=None,
        motivo=None,
    )
    repositorio.registrar_decision(decision=fila)
    return fila
