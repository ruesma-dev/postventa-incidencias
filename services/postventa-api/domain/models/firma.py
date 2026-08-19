# services/postventa-api/domain/models/firma.py
"""Qué hay en la casilla de la firma del cliente (F-004).

La firma no está en ningún campo de texto: hay que **mirarla**. Lo que este
módulo define es el vocabulario con el que se describe esa casilla —cuatro
etiquetas y nada más— y cómo viaja esa lectura por el sistema.

Dos reglas que no son de estilo, y las dos empujan en la misma dirección:

- **La duda nunca cae del lado de `HUMANA`.** Una etiqueta que el modelo se
  invente, o que no devuelva, se traduce a `ILEGIBLE` (R2). Dar por firmado lo
  que no se entendió es el fallo caro de esta feature: da por conforme una
  reparación que el cliente no firmó.
- **Una `HUMANA` dudosa se publica como `ILEGIBLE`** (R14 y R14 bis, decisión
  D4 del humano del 2026-08-19). La lectura cruda no se pierde —sigue en
  `clasificacion` y viaja entera en la respuesta de `/api/firma`—, pero lo que
  sale al mundo es la etiqueta degradada: publicar `humana` al lado de un
  destino «revisión manual» es incomprensible para quien lo lea en Posventa.

Aquí no hay proveedor, ni SDK, ni HTTP: el dominio no sabe **quién** miró la
casilla. Y no se transcribe nada de lo que hay en ella —ni el nombre, ni el
DNI—, porque es lo más identificativo del papel; el prompt ni siquiera lo pide.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.models.extraccion import TrazaExtraccion

#: Por debajo de esto, un dato no se considera leído (R12, R14).
#:
#: **Es una constante del dominio, no configuración.** Aflojarla por variable
#: de entorno sería aflojar una regla de negocio sin revisión. El valor sale
#: del dato real: los seis campos impresos de la remesa de Mirasierra vinieron
#: con confianzas medias de 98,8 a 99,2, así que 50 está a un abismo de lo
#: normal y solo dispara ante una lectura de verdad dudosa.
#:
#: Vive aquí, y no en `validacion.py` como decía el diseño, por una razón
#: mecánica: `LecturaFirma` la necesita y `validacion.py` importa este módulo,
#: así que declararla allí sería un import circular. `validacion.py` la importa
#: de aquí, de modo que hay **una sola definición** y sigue estando disponible
#: como `domain.models.validacion.UMBRAL_CONFIANZA`.
UMBRAL_CONFIANZA = 50


class ClasificacionFirma(str, Enum):
    """Qué hay en la casilla. Es una **descripción**, no un juicio del parte.

    `marca_simple` existe separada de `humana` porque es justo la distinción
    que pide el negocio (`CHECKPOINTS.md` C3): un aspa o un tick no son la
    conformidad del cliente por mucho que la casilla no esté vacía.
    """

    HUMANA = "humana"
    MARCA_SIMPLE = "marca_simple"
    CASILLA_VACIA = "casilla_vacia"
    ILEGIBLE = "ilegible"


#: El único campo que se le pide al modelo sobre la firma.
CAMPO_CLASIFICACION = "clasificacion_firma"

#: Los campos del schema `firma_cliente`: uno, y por eso el prompt es corto.
CAMPOS_DE_LA_FIRMA: tuple[str, ...] = (CAMPO_CLASIFICACION,)


def clasificacion_desde_texto(texto: str | None) -> ClasificacionFirma:
    """La etiqueta que dice el modelo, o `ILEGIBLE` si no es una de las cuatro.

    Normaliza mayúsculas y espacios sobrantes, y nada más: un `"Humana"` o un
    `" humana\\n"` son la misma etiqueta, y degradarlos mandaría a revisión
    manual partes correctamente firmados.

    Lo que **nunca** hace es devolver `HUMANA` ante algo que no lo diga
    literalmente (R2).
    """
    if texto is None:
        return ClasificacionFirma.ILEGIBLE
    try:
        return ClasificacionFirma(str(texto).strip().lower())
    except ValueError:
        return ClasificacionFirma.ILEGIBLE


@dataclass(frozen=True)
class LecturaFirma:
    """Lo que se leyó de la casilla de un parte: etiqueta, certeza y traza.

    Se reutiliza `TrazaExtraccion` en vez de inventar una traza gemela: es
    exactamente el mismo dato —proveedor, modelo, prompt, versión y huella— y
    dos clases idénticas se desincronizan solas.
    """

    hash_parte: str
    clasificacion: ClasificacionFirma
    confianza_pct: int
    traza: TrazaExtraccion
    avisos: tuple[str, ...] = ()

    @property
    def es_conformidad_del_cliente(self) -> bool:
        """¿Esto es la firma del cliente? `HUMANA` y sin dudas; nada más.

        La confianza mide la certeza sobre **la etiqueta**, no sobre la
        conformidad: estar muy seguro de que hay un aspa es estar muy seguro
        de que no hay firma.
        """
        return (
            self.clasificacion == ClasificacionFirma.HUMANA
            and self.confianza_pct >= UMBRAL_CONFIANZA
        )

    @property
    def clasificacion_efectiva(self) -> ClasificacionFirma:
        """La etiqueta que se **publica** (R14 bis, decisión D4).

        `ILEGIBLE` si una `HUMANA` no llega al umbral; en cualquier otro caso,
        la que dijo el modelo. Fuera del caso degradado no se toca nada:
        degradar también un `marca_simple` de confianza baja borraría
        información útil para quien revise el parte.
        """
        if (
            self.clasificacion == ClasificacionFirma.HUMANA
            and not self.es_conformidad_del_cliente
        ):
            return ClasificacionFirma.ILEGIBLE
        return self.clasificacion
