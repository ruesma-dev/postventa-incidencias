# services/postventa-api/interface_adapters/api/cuerpos.py
"""Los parsers del cuerpo que comparten `/api/validar`, `/api/parte` y
`/api/aprobar`.

Salieron de `interface_adapters/api/validar.py` en F-019 **sin cambiar ni una
regla ni un mensaje de error**: `POST /api/parte` recibe *el mismo* cuerpo que
`POST /api/validar` más dos claves (`design.md` §6), y eso es deliberado —el
front ya lo compone y así no hay dos formas de describir el mismo parte, que
es como divergen los contratos—.

Tenerlos aquí es lo que hace que ese «el mismo cuerpo» sea verdad **por
construcción** y no por costumbre: si mañana `/api/validar` empieza a exigir
una clave más, `/api/parte` la exige el mismo día, y al revés. Copiarlos
habría dejado dos parsers que se parecen hoy y divergen en la primera
corrección.

F-026 añadió el tercer endpoint que recibe ese cuerpo —`POST /api/aprobar`,
que es el de `/api/parte` más `usuario_oid` y `confirmado`— y por eso bajaron
aquí `CLAVES_DEL_PARTE`, `a_remesa_id` y `a_parte_troceado`, que vivían en
`parte.py` como funciones privadas. **No cambia ni una regla ni un mensaje de
error**: es la misma mudanza que hizo F-019 con los parsers de `/api/validar`,
y por el mismo motivo — el día que aprobar y guardar describan el parte de dos
formas distintas, se aprueba un veredicto y se guarda otro.

Lo que aquí se comprueba es la **forma** del cuerpo, nunca el veredicto: quien
decide sigue siendo `domain/models/validacion.py`. Y los mensajes de error
dicen **qué falta** y jamás lo que sí venía: el cuerpo lleva los valores
leídos del parte, con el DNI y las observaciones manuscritas dentro, y estos
textos acaban en un log que sobrevive al parte.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from application.pipelines.confianza import sanear_confianza
from domain.models.errores import (
    CuerpoDeValidacionInvalido,
    PeticionDePersistenciaInvalida,
)
from domain.models.extraccion import (
    CAMPOS_DEL_PARTE,
    CampoExtraido,
    ExtraccionParte,
    TrazaExtraccion,
)
from domain.models.firma import LecturaFirma, clasificacion_desde_texto
from domain.models.remesa import ModoDeteccion, ParteTroceado

__all__ = [
    "CLAVES_DEL_PARTE",
    "CLAVES_DE_LA_EXTRACCION",
    "CLAVES_DE_LA_FIRMA",
    "CLAVES_DE_LA_TRAZA",
    "a_campo",
    "a_extraccion",
    "a_lectura_de_firma",
    "a_parte_troceado",
    "a_remesa_id",
    "a_traza",
    "bloque",
]

#: Lo que tiene que traer el bloque `parte` del cuerpo (F-019, F-026).
#:
#: Los cuatro, y no solo el `hash`: `origen` y `paginas_origen` son lo que
#: permite volver sobre la remesa sin reabrirla, y `modo_deteccion` es la
#: diferencia entre «este documento no tenía ningún parte de dos hojas» y «en
#: este documento no se ha podido mirar». Guardar un parte sin ellos deja una
#: fila que no se puede rastrear.
CLAVES_DEL_PARTE = ("hash", "origen", "paginas_origen", "modo_deteccion")

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


def bloque(
    cuerpo: Mapping[str, Any], nombre: str, obligatorias: tuple[str, ...]
) -> Mapping[str, Any]:
    """Un bloque del cuerpo, comprobado; o el error diciendo qué le falta."""
    hallado = cuerpo.get(nombre)
    if not isinstance(hallado, Mapping):
        raise CuerpoDeValidacionInvalido(
            f"el cuerpo no trae '{nombre}', que es lo que devuelve el endpoint "
            f"correspondiente"
        )
    faltan = [clave for clave in obligatorias if clave not in hallado]
    if faltan:
        raise CuerpoDeValidacionInvalido(
            f"el bloque '{nombre}' del cuerpo no trae: {', '.join(faltan)}"
        )
    return hallado


def a_extraccion(bloque_extraccion: Mapping[str, Any]) -> ExtraccionParte:
    """Reconstruye lo que devolvió `/api/extraer`.

    Los nueve campos son contrato: si falta uno, no se valida. Rellenarlo con
    un vacío de consolación sería inventarse que el papel estaba en blanco, y
    de ahí saldría un veredicto sobre un dato que nadie leyó.
    """
    campos = bloque_extraccion["campos"]
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
        hash_parte=str(bloque_extraccion["hash_parte"]),
        campos={
            nombre: a_campo(campos[nombre]) for nombre in CAMPOS_DEL_PARTE
        },
        traza=a_traza(bloque_extraccion["traza"]),
        avisos=(),
    )


def a_campo(crudo: Any) -> CampoExtraido:
    """Un campo del cuerpo, con la confianza saneada por la regla de siempre."""
    valores = crudo if isinstance(crudo, Mapping) else {}
    confianza, _ = sanear_confianza(valores.get("confianza_pct"))
    valor = valores.get("valor")
    return CampoExtraido(
        valor=None if valor is None else str(valor), confianza_pct=confianza
    )


def a_lectura_de_firma(bloque_firma: Mapping[str, Any]) -> LecturaFirma:
    """Reconstruye lo que devolvió `/api/firma`.

    La etiqueta se traduce con la **misma** función que el dominio: el cuerpo
    llega de fuera, y aquí tampoco se da por firmado lo que no diga
    literalmente `humana`.
    """
    firma = (
        bloque_firma["firma"] if isinstance(bloque_firma["firma"], Mapping) else {}
    )
    confianza, _ = sanear_confianza(firma.get("confianza_pct"))
    return LecturaFirma(
        hash_parte=str(bloque_firma["hash_parte"]),
        clasificacion=clasificacion_desde_texto(firma.get("clasificacion")),
        confianza_pct=confianza,
        traza=a_traza(bloque_firma["traza"]),
        avisos=(),
    )


def a_traza(crudo: Any) -> TrazaExtraccion:
    """La traza que llega, copiada tal cual. No decide nada del veredicto."""
    valores = crudo if isinstance(crudo, Mapping) else {}
    return TrazaExtraccion(
        **{clave: str(valores.get(clave, "")) for clave in CLAVES_DE_LA_TRAZA}
    )


def a_remesa_id(crudo: Any) -> str:
    """El `remesa_id` que devolvió `POST /api/remesa`. Obligatorio (R10, R11).

    Se comprueba que sea un UUID **aquí**: la columna es `uuid`, así que
    dejarlo pasar convertiría un error del llamante en un 503 que manda a
    mirar el servidor a quien tenía que corregir su petición.
    """
    if crudo is None:
        raise PeticionDePersistenciaInvalida(
            "el cuerpo no trae 'remesa_id': es el identificador que devolvió "
            "POST /api/remesa, y hay que registrar la remesa antes de guardar "
            "sus partes"
        )
    try:
        return str(UUID(str(crudo)))
    except (ValueError, AttributeError, TypeError) as mal_formado:
        raise PeticionDePersistenciaInvalida(
            "'remesa_id' no es un UUID: tiene que ser el que devolvió "
            "POST /api/remesa"
        ) from mal_formado


def a_parte_troceado(bloque_parte: Mapping[str, Any]) -> ParteTroceado:
    """Reconstruye lo que produjo `POST /api/split`, **sin los bytes** (R12).

    Ni `/api/parte` ni `/api/aprobar` reciben el PDF: lleva el DNI manuscrito,
    vive en SharePoint y el disco de este servidor es compartido y solo crece.
    Lo que se evita reconstruyendo `contenido` como `b""` es **ofrecer la
    vía**.
    """
    return ParteTroceado(
        hash=_texto(bloque_parte["hash"], "parte.hash"),
        origen=_texto(bloque_parte["origen"], "parte.origen"),
        paginas_origen=_paginas(bloque_parte["paginas_origen"]),
        modo_deteccion=_modo(bloque_parte["modo_deteccion"]),
        # R12: el PDF vive en SharePoint. Aquí no entra ni un byte.
        contenido=b"",
    )


def _texto(crudo: Any, nombre: str) -> str:
    """Un texto obligatorio y no vacío del bloque `parte`."""
    valor = str(crudo).strip() if isinstance(crudo, str) else ""
    if not valor:
        raise PeticionDePersistenciaInvalida(
            f"'{nombre}' tiene que ser un texto no vacío"
        )
    return valor


def _paginas(crudo: Any) -> tuple[int, ...]:
    """Las páginas del original de las que salió el parte, numeradas desde 1.

    Se exige que sean números: `paginas_origen` es lo que permite volver sobre
    la remesa sin reabrirla, y una lista de textos deja una fila que no
    localiza nada.
    """
    if isinstance(crudo, str) or not isinstance(crudo, Sequence):
        raise PeticionDePersistenciaInvalida(
            "'parte.paginas_origen' tiene que ser una lista de números de página"
        )
    paginas = []
    for pagina in crudo:
        if isinstance(pagina, bool) or not isinstance(pagina, int):
            raise PeticionDePersistenciaInvalida(
                "'parte.paginas_origen' tiene que traer solo números de página"
            )
        paginas.append(pagina)
    return tuple(paginas)


def _modo(crudo: Any) -> ModoDeteccion:
    """Cómo se decidió dónde empezaba el parte, con los valores del dominio.

    Un valor desconocido **no** se sustituye por el más común: guardaría una
    mentira sobre cómo se troceó la remesa, y esa columna es lo que distingue
    «no había partes de dos hojas» de «no se pudo mirar».
    """
    try:
        return ModoDeteccion(crudo)
    except ValueError as desconocido:
        admitidos = ", ".join(modo.value for modo in ModoDeteccion)
        raise PeticionDePersistenciaInvalida(
            f"'parte.modo_deteccion' no es uno de los valores admitidos "
            f"({admitidos})"
        ) from desconocido
