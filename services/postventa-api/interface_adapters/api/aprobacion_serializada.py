# services/postventa-api/interface_adapters/api/aprobacion_serializada.py
"""Cómo viaja una aprobación en una respuesta HTTP (F-026, R22, R38).

Un módulo propio para una sola función, y tiene motivo: **la comparten dos
endpoints**. `POST /api/aprobar` la devuelve porque acaba de escribirla, y
`POST /api/parte` la devuelve porque la pantalla tiene que saber qué partes
constan aprobados sin preguntarlo uno a uno (R22, y son 22 llamadas de más en
una remesa real).

Dos serializaciones del mismo hecho divergirían en la primera corrección, y lo
que divergiría es **qué se publica de una decisión que lleva dentro el `oid` de
una persona**. Así que vive en un sitio, y ese sitio no puede ser ninguno de
los dos handlers: `aprobar.py` ya importa de `parte.py` el envoltorio que
cuenta los resultados, y devolverle el favor los volvería mutuamente
dependientes.

No es dominio: el dominio no sabe de JSON ni de claves de respuesta. Es la
traducción del borde, que es justo lo que hace `interface_adapters`.
"""

from __future__ import annotations

from typing import Any

from domain.models.aprobacion import Aprobacion, esta_vigente

__all__ = ["ESTADO_APROBADO", "ESTADO_REVOCADO", "bloque_de_aprobacion"]

#: Cómo se llama, en la respuesta, una aprobación que sigue en pie.
ESTADO_APROBADO = "aprobado"

#: Y una que dejó de valer porque el veredicto cambió (R31).
#:
#: Se devuelve **distinta de «no hay aprobación»** a propósito: la pantalla
#: tiene que poder contar «se decidió y dejó de valer», que es lo que hace que
#: alguien vuelva a mirar el parte en vez de darlo por olvidado.
ESTADO_REVOCADO = "revocado"


def bloque_de_aprobacion(aprobacion: Aprobacion | None) -> dict[str, Any] | None:
    """El bloque `aprobacion` de la respuesta, o `None` si no la aprobó nadie.

    `None` y no la clave ausente: la clave está siempre y su valor dice qué
    pasa. Omitirla obligaría a la pantalla a distinguir «no consta aprobado» de
    «esta respuesta la emitió una versión del backend que no sabía de
    aprobaciones».

    Cuatro claves y ninguna más. **Ni el `oid`, ni el correo, ni el nombre de
    quien aprobó** (R38, R43): la pantalla no los necesita y quien audite los
    lee en la base. Tampoco el texto del papel, que no está ni en la fila. Lo
    que sí va es de dónde se rescató el parte y cuándo se decidió, que es lo
    que la pantalla tiene que enseñar (R37).
    """
    if aprobacion is None:
        return None
    return {
        "estado": ESTADO_APROBADO if esta_vigente(aprobacion) else ESTADO_REVOCADO,
        "destino_aprobado": aprobacion.destino_aprobado.value,
        "motivos_aprobados": [codigo.value for codigo in aprobacion.motivos_aprobados],
        "aprobado_at_utc": aprobacion.aprobado_at_utc.isoformat(),
    }
