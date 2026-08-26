# services/postventa-api/interface_adapters/api/validar.py
"""Handler de `POST /api/validar`: el veredicto de un parte, **sin IA**.

Este endpoint no abre nada. Recibe el cuerpo que emiten `/api/extraer` y
`/api/firma`, reconstruye las dos lecturas y llama a las reglas del dominio.
Ni modelo, ni PDF, ni red, ni base de datos.

Eso es lo que permite **revalidar**: cuando una persona corrija un campo
(F-011) o cuando F-016 reclasifique una observación, se vuelve a pedir el
veredicto sin gastar otra llamada multimodal.

**Solo se admite el cuerpo tal y como lo emiten los otros dos endpoints.** Un
cuerpo montado a mano es una puerta para que el front invente datos por el
camino, y lo que se decide aquí es si una incidencia del ERP se cierra.

Los parsers del cuerpo viven en `cuerpos.py` desde F-019, porque
`POST /api/parte` recibe **el mismo cuerpo** más dos claves y las dos
comprobaciones tienen que ser literalmente la misma. Aquí no cambió ni una
regla ni un mensaje al mudarlos.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from domain.models.errores import CuerpoDeValidacionInvalido
from domain.models.firma import LecturaFirma
from domain.models.validacion import ResultadoValidacion, validar_parte

from interface_adapters.api.cuerpos import (
    CLAVES_DE_LA_EXTRACCION,
    CLAVES_DE_LA_FIRMA,
    a_extraccion,
    a_lectura_de_firma,
    bloque,
)


def validar(cuerpo: Mapping[str, Any]) -> dict[str, Any]:
    """Devuelve el veredicto del parte que describe ese cuerpo.

    Levanta `CuerpoDeValidacionInvalido` (→ 400) diciendo **qué falta**: un 400
    que no lo dice obliga a leer el código del servidor para arreglar una
    petición que manda otro equipo.
    """
    if not isinstance(cuerpo, Mapping):
        raise CuerpoDeValidacionInvalido(
            "el cuerpo tiene que ser un objeto JSON con 'extraccion' y 'firma'"
        )

    extraccion = bloque(cuerpo, "extraccion", CLAVES_DE_LA_EXTRACCION)
    firma = bloque(cuerpo, "firma", CLAVES_DE_LA_FIRMA)

    lectura = a_lectura_de_firma(firma)
    return _serializar(
        validar_parte(a_extraccion(extraccion), lectura),
        lectura,
        _avisos(extraccion, firma),
    )


def _avisos(
    extraccion: Mapping[str, Any], firma: Mapping[str, Any]
) -> list[str]:
    """Los avisos de las dos lecturas, juntos y en ese orden.

    Quien lee el veredicto necesita saber si la lectura fue rara: un
    «confianza fuera de rango» cambia mucho cómo se mira un parte apto, y
    perderlo aquí lo dejaría enterrado en dos respuestas anteriores que nadie
    guarda.
    """
    return [
        str(aviso)
        for bloque_leido in (extraccion, firma)
        for aviso in bloque_leido.get("avisos", [])
    ]


def _serializar(
    resultado: ResultadoValidacion, lectura: LecturaFirma, avisos: list[str]
) -> dict[str, Any]:
    """Pasa el veredicto a JSON. Ni una clave más que las de R24.

    `firma.clasificacion` es la etiqueta **efectiva** (R14 bis, decisión D4):
    una `humana` que no llega al umbral sale de aquí como `ilegible`, que es
    lo mismo que dice el motivo que la acompaña.

    La confianza que acompaña a la etiqueta es la que **declaró el modelo**, no
    una degradada: es justo lo que explica por qué una `humana` dudosa se
    publica como `ilegible`.

    `observaciones` lleva la transcripción literal porque quien decide la
    necesita delante. Es el único dato personal de esta respuesta, y por eso
    **no entra en ningún log** (R25).
    """
    return {
        "hash_parte": resultado.hash_parte,
        "veredicto": resultado.veredicto.value,
        "destino": resultado.destino.value,
        "motivos": [
            {"codigo": motivo.codigo.value, "texto": motivo.texto}
            for motivo in resultado.motivos
        ],
        "firma": {
            "clasificacion": resultado.clasificacion_firma.value,
            "confianza_pct": lectura.confianza_pct,
        },
        "observaciones": None
        if resultado.observaciones is None
        else {
            "texto": resultado.observaciones,
            "confianza_pct": resultado.confianza_observaciones,
        },
        "avisos": avisos,
    }
