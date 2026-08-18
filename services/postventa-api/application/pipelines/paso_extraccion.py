# services/postventa-api/application/pipelines/paso_extraccion.py
"""Paso 3 del pipeline: leer el parte con un modelo multimodal.

Este paso **no sabe qué proveedor hay debajo**: habla con `ExtractorPort` y
con `RepositorioPromptsPort`, y por eso se prueba entero con dobles (R13). Lo
que sí sabe, y es lo que decide el contrato de F-003, es que el resultado
tiene que traer **siempre las nueve claves declaradas** con la confianza ya
dentro de rango.

La clave del diseño está en una línea: se recorre `CAMPOS_DEL_PARTE`, **no**
las claves que devolvió el modelo. Así R2 —no puede faltar ninguna— y R7 —no
puede sobrar una inventada— son la misma línea de código, y no dos reglas que
alguien tenga que acordarse de mantener sincronizadas.

Y lo que este paso **no** hace: no reagrupa páginas (eso es F-014), no juzga
la firma (F-004) y no normaliza ningún valor (F-006 nombrará el fichero).
"""

from __future__ import annotations

from collections.abc import Mapping

from domain.models.errores import ParteDemasiadoGrande
from domain.models.extraccion import (
    CAMPOS_DEL_PARTE,
    CampoBruto,
    CampoExtraido,
    ExtraccionParte,
    RespuestaModelo,
    TrazaExtraccion,
)
from domain.models.prompt import PromptSpec
from domain.ports.extractor import ExtractorPort
from domain.ports.prompts import RepositorioPromptsPort

from application.pipelines.contexto_parte import ContextoParte

#: Lo que se le manda al modelo: el PDF del parte, sin rasterizar.
MIME_PDF = "application/pdf"

#: Tope de lo que se envía en línea al modelo (R16). Un parte troceado son
#: 1–2 páginas: lo que se pase de aquí no es un parte, es otra cosa.
MAX_BYTES_PARTE = 15 * 1024 * 1024

#: Extremos de la confianza declarada (R3).
CONFIANZA_MINIMA = 0
CONFIANZA_MAXIMA = 100


def paso_extraccion(
    ctx: ContextoParte,
    extractor: ExtractorPort,
    prompts: RepositorioPromptsPort,
    prompt_key: str,
) -> ContextoParte:
    """Extrae los campos del parte y los deja saneados en el contexto."""
    tamano = len(ctx.parte.contenido)
    if tamano > MAX_BYTES_PARTE:
        raise ParteDemasiadoGrande(
            f"el parte ocupa {tamano} bytes y el máximo admitido para enviarlo "
            f"al modelo es {MAX_BYTES_PARTE}"
        )

    prompt = prompts.obtener(prompt_key)
    respuesta = extractor.extraer(
        documento=ctx.parte.contenido, mime=MIME_PDF, prompt=prompt
    )
    campos, avisos = _completar_y_sanear(respuesta.campos)

    ctx.extraccion = ExtraccionParte(
        hash_parte=ctx.parte.hash,
        campos=campos,
        traza=_traza(respuesta, prompt_key, prompt),
        avisos=tuple(avisos),
    )
    ctx.avisos.extend(avisos)
    return ctx


def _traza(
    respuesta: RespuestaModelo, prompt_key: str, prompt: PromptSpec
) -> TrazaExtraccion:
    """Quién leyó el parte y con qué texto (R6, R10)."""
    return TrazaExtraccion(
        proveedor=respuesta.proveedor,
        modelo=respuesta.modelo,
        prompt_key=prompt_key,
        version_prompt=prompt.version,
        huella_prompt=prompt.huella,
    )


def _completar_y_sanear(
    brutos: Mapping[str, CampoBruto],
) -> tuple[dict[str, CampoExtraido], list[str]]:
    """Los nueve campos declarados, saneados, y los avisos que hayan salido."""
    campos: dict[str, CampoExtraido] = {}
    avisos: list[str] = []

    for nombre in CAMPOS_DEL_PARTE:
        bruto = brutos.get(nombre)
        if bruto is None:
            campos[nombre] = CampoExtraido(valor=None, confianza_pct=0)
            avisos.append(f"{nombre}: el modelo no devolvió el campo")
            continue
        confianza, aviso = _sanear_confianza(bruto.confianza_pct)
        if aviso is not None:
            avisos.append(f"{nombre}: {aviso}")
        campos[nombre] = CampoExtraido(valor=bruto.valor, confianza_pct=confianza)

    avisos.extend(
        f"{sobrante}: el modelo devolvió un campo que no está en el contrato, "
        "y se ha descartado"
        for sobrante in brutos
        if sobrante not in CAMPOS_DEL_PARTE
    )
    return campos, avisos


def _sanear_confianza(declarada: object) -> tuple[int, str | None]:
    """La confianza dentro de `0–100`, y el aviso si hubo que tocarla (R4).

    Nunca se descarta el valor leído por culpa de la confianza: una confianza
    mal formada no invalida lo leído, lo hace **sospechoso**.
    """
    entero = _a_entero(declarada)
    if entero is None:
        return CONFIANZA_MINIMA, "la confianza declarada no es un entero, se deja en 0"
    if entero < CONFIANZA_MINIMA:
        return CONFIANZA_MINIMA, f"confianza {entero} fuera de rango, se ajusta a 0"
    if entero > CONFIANZA_MAXIMA:
        return CONFIANZA_MAXIMA, f"confianza {entero} fuera de rango, se ajusta a 100"
    return entero, None


def _a_entero(valor: object) -> int | None:
    """El entero que declara ese valor, o `None` si no declara ninguno.

    Un `bool` **no** cuenta: en Python es un `int`, y `True` colaría como
    confianza 1. Un entero escrito como texto (`"85"`) sí, porque los modelos
    lo devuelven así más a menudo de lo que reconocen y tirar por eso una
    lectura buena sería absurdo. Un decimal (`"85.0"`, `85.5`) no: redondearlo
    sería inventarse una regla que el schema no declara, y el schema dice
    `integer`.
    """
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str) and valor.strip().lstrip("-").isdigit():
        return int(valor.strip())
    return None
