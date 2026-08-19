# services/postventa-api/application/pipelines/paso_firma.py
"""Paso que mira la casilla de la firma del cliente (F-004).

Es el gemelo pequeño de `paso_extraccion`: mismo puerto, mismo tope de tamaño,
mismo saneo de confianza y misma traza. Lo único propio que hace es traducir
**un** campo de texto a la enumeración del dominio.

Se apoya en el mismo `ExtractorPort` a propósito (`design.md` §2): no hay
adaptador nuevo, ni proveedor nuevo, ni dependencia nueva. Lo que cambia es el
prompt —`firma_parte_es`, con su propio schema de un campo— y eso permite
reintentar, cambiar o apagar la lectura de la firma **sin rozar** el prompt de
extracción, cuya calidad se midió a mano sobre 22 partes reales.

Este paso y el de extracción son **independientes**: ninguno necesita el
resultado del otro, así que el front puede pedirlos en paralelo. Componerlos
en una sola invocación sumaría dos timeouts de 120 s y la Function corta a los
230 s.
"""

from __future__ import annotations

from collections.abc import Mapping

from domain.models.errores import ParteDemasiadoGrande
from domain.models.extraccion import CampoBruto, RespuestaModelo, TrazaExtraccion
from domain.models.firma import (
    CAMPO_CLASIFICACION,
    ClasificacionFirma,
    LecturaFirma,
    clasificacion_desde_texto,
)
from domain.models.prompt import PromptSpec
from domain.ports.extractor import ExtractorPort
from domain.ports.prompts import RepositorioPromptsPort

from application.pipelines import paso_extraccion
from application.pipelines.confianza import sanear_confianza
from application.pipelines.contexto_parte import ContextoParte

#: El mismo mime que la extracción: el PDF del parte, sin rasterizar.
MIME_PDF = paso_extraccion.MIME_PDF


def paso_firma(
    ctx: ContextoParte,
    extractor: ExtractorPort,
    prompts: RepositorioPromptsPort,
    prompt_key: str,
) -> ContextoParte:
    """Clasifica la firma del parte y deja la lectura en el contexto.

    El tope de tamaño se lee de `paso_extraccion` **en cada llamada**, y no se
    copia aquí: es el mismo límite del mismo modelo, y dos constantes con el
    mismo número se desincronizan solas.
    """
    tamano = len(ctx.parte.contenido)
    if tamano > paso_extraccion.MAX_BYTES_PARTE:
        raise ParteDemasiadoGrande(
            f"el parte ocupa {tamano} bytes y el máximo admitido para enviarlo "
            f"al modelo es {paso_extraccion.MAX_BYTES_PARTE}"
        )

    prompt = prompts.obtener(prompt_key)
    respuesta = extractor.extraer(
        documento=ctx.parte.contenido, mime=MIME_PDF, prompt=prompt
    )
    clasificacion, confianza, avisos = _leer_clasificacion(respuesta.campos)

    ctx.lectura_firma = LecturaFirma(
        hash_parte=ctx.parte.hash,
        clasificacion=clasificacion,
        confianza_pct=confianza,
        traza=_traza(respuesta, prompt_key, prompt),
        avisos=tuple(avisos),
    )
    ctx.avisos.extend(avisos)
    return ctx


def _traza(
    respuesta: RespuestaModelo, prompt_key: str, prompt: PromptSpec
) -> TrazaExtraccion:
    """Quién miró la casilla y con qué texto.

    Se reutiliza la traza de F-003 porque es exactamente el mismo dato: dos
    clases idénticas se desincronizan solas.
    """
    return TrazaExtraccion(
        proveedor=respuesta.proveedor,
        modelo=respuesta.modelo,
        prompt_key=prompt_key,
        version_prompt=prompt.version,
        huella_prompt=prompt.huella,
    )


def _leer_clasificacion(
    brutos: Mapping[str, CampoBruto],
) -> tuple[ClasificacionFirma, int, list[str]]:
    """La etiqueta, su confianza saneada y los avisos que hayan salido.

    Todo lo que no se entiende acaba en `ILEGIBLE` **y con aviso**. Sin el
    aviso, un modelo que empezara a devolver otra etiqueta mandaría la remesa
    entera a revisión manual sin que nadie supiera por qué.
    """
    avisos: list[str] = []
    bruto = brutos.get(CAMPO_CLASIFICACION)

    if bruto is None:
        avisos.append(f"{CAMPO_CLASIFICACION}: el modelo no devolvió el campo")
        return ClasificacionFirma.ILEGIBLE, 0, avisos

    clasificacion = clasificacion_desde_texto(bruto.valor)
    if clasificacion == ClasificacionFirma.ILEGIBLE and not _dijo_ilegible(bruto.valor):
        avisos.append(
            f"{CAMPO_CLASIFICACION}: el modelo devolvió '{bruto.valor}', que no "
            "es una de las cuatro etiquetas, y se ha tomado como ilegible"
        )

    confianza, aviso = sanear_confianza(bruto.confianza_pct)
    if aviso is not None:
        avisos.append(f"{CAMPO_CLASIFICACION}: {aviso}")

    avisos.extend(
        f"{sobrante}: el modelo devolvió un campo que no está en el contrato, "
        "y se ha descartado"
        for sobrante in brutos
        if sobrante != CAMPO_CLASIFICACION
    )
    return clasificacion, confianza, avisos


def _dijo_ilegible(valor: object) -> bool:
    """¿El modelo dijo `ilegible` de verdad, o se le tradujo a eso?

    Distinguirlo es lo que evita un aviso en el caso normal —el prompt manda
    responder `ilegible` ante la duda— y lo conserva cuando la etiqueta era
    otra cosa.
    """
    return (
        isinstance(valor, str)
        and valor.strip().lower() == ClasificacionFirma.ILEGIBLE.value
    )
