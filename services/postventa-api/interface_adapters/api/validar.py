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
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from application.pipelines.confianza import sanear_confianza
from domain.models.errores import CuerpoDeValidacionInvalido
from domain.models.extraccion import (
    CAMPOS_DEL_PARTE,
    CampoExtraido,
    ExtraccionParte,
    TrazaExtraccion,
)
from domain.models.firma import LecturaFirma, clasificacion_desde_texto
from domain.models.validacion import ResultadoValidacion, validar_parte

#: Lo que tiene que traer el bloque `extraccion` del cuerpo.
CLAVES_DE_LA_EXTRACCION = ("hash_parte", "campos", "traza")

#: Lo que tiene que traer el bloque `firma` del cuerpo.
CLAVES_DE_LA_FIRMA = ("hash_parte", "firma", "traza")

#: Las claves de la traza, que se copian tal cual llegan.
CLAVES_DE_LA_TRAZA = (
    "proveedor",
    "modelo",
    "prompt_key",
    "version_prompt",
    "huella_prompt",
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

    extraccion = _bloque(cuerpo, "extraccion", CLAVES_DE_LA_EXTRACCION)
    firma = _bloque(cuerpo, "firma", CLAVES_DE_LA_FIRMA)

    lectura = _a_lectura_de_firma(firma)
    return _serializar(
        validar_parte(_a_extraccion(extraccion), lectura),
        lectura,
        _avisos(extraccion, firma),
    )


def _bloque(
    cuerpo: Mapping[str, Any], nombre: str, obligatorias: tuple[str, ...]
) -> Mapping[str, Any]:
    """Un bloque del cuerpo, comprobado; o el error diciendo qué le falta."""
    bloque = cuerpo.get(nombre)
    if not isinstance(bloque, Mapping):
        raise CuerpoDeValidacionInvalido(
            f"el cuerpo no trae '{nombre}', que es lo que devuelve el endpoint "
            f"correspondiente"
        )
    faltan = [clave for clave in obligatorias if clave not in bloque]
    if faltan:
        raise CuerpoDeValidacionInvalido(
            f"el bloque '{nombre}' del cuerpo no trae: {', '.join(faltan)}"
        )
    return bloque


def _a_extraccion(bloque: Mapping[str, Any]) -> ExtraccionParte:
    """Reconstruye lo que devolvió `/api/extraer`.

    Los nueve campos son contrato: si falta uno, no se valida. Rellenarlo con
    un vacío de consolación sería inventarse que el papel estaba en blanco, y
    de ahí saldría un veredicto sobre un dato que nadie leyó.
    """
    campos = bloque["campos"]
    if not isinstance(campos, Mapping):
        raise CuerpoDeValidacionInvalido(
            "el bloque 'extraccion' trae unos 'campos' que no son un objeto"
        )
    faltan = [nombre for nombre in CAMPOS_DEL_PARTE if nombre not in campos]
    if faltan:
        raise CuerpoDeValidacionInvalido(
            f"al bloque 'extraccion' le faltan campos: {', '.join(faltan)}"
        )
    return ExtraccionParte(
        hash_parte=str(bloque["hash_parte"]),
        campos={
            nombre: _a_campo(campos[nombre]) for nombre in CAMPOS_DEL_PARTE
        },
        traza=_a_traza(bloque["traza"]),
        avisos=(),
    )


def _a_campo(crudo: Any) -> CampoExtraido:
    """Un campo del cuerpo, con la confianza saneada por la regla de siempre."""
    valores = crudo if isinstance(crudo, Mapping) else {}
    confianza, _ = sanear_confianza(valores.get("confianza_pct"))
    valor = valores.get("valor")
    return CampoExtraido(
        valor=None if valor is None else str(valor), confianza_pct=confianza
    )


def _a_lectura_de_firma(bloque: Mapping[str, Any]) -> LecturaFirma:
    """Reconstruye lo que devolvió `/api/firma`.

    La etiqueta se traduce con la **misma** función que el dominio: el cuerpo
    llega de fuera, y aquí tampoco se da por firmado lo que no diga
    literalmente `humana`.
    """
    firma = bloque["firma"] if isinstance(bloque["firma"], Mapping) else {}
    confianza, _ = sanear_confianza(firma.get("confianza_pct"))
    return LecturaFirma(
        hash_parte=str(bloque["hash_parte"]),
        clasificacion=clasificacion_desde_texto(firma.get("clasificacion")),
        confianza_pct=confianza,
        traza=_a_traza(bloque["traza"]),
        avisos=(),
    )


def _a_traza(crudo: Any) -> TrazaExtraccion:
    """La traza que llega, copiada tal cual. No decide nada del veredicto."""
    valores = crudo if isinstance(crudo, Mapping) else {}
    return TrazaExtraccion(
        **{clave: str(valores.get(clave, "")) for clave in CLAVES_DE_LA_TRAZA}
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
        for bloque in (extraccion, firma)
        for aviso in bloque.get("avisos", [])
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
