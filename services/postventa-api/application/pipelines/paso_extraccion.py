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

Y lo que este paso **no** hace: no reagrupa páginas (eso es F-014) y no juzga
la firma (F-004).

> **Enmienda del 2026-09-17 · F-032 (R11, R15).** Hasta hoy esta cabecera decía
> también que el paso «**no normaliza ningún valor**», y dejó de ser verdad: los
> dos **códigos** —`codigo_obra` y `numero_incidencia`— salen de aquí ya sin
> blancos, con `sanear_valor_leido`, la regla del dominio.
>
> El motivo tiene fecha: el 2026-09-17 la IA leyó `RS 26.09/0178` —con el
> espacio dentro del primer tramo—, el cierre murió en
> `ReclamacionNoLocalizada` y hubo que editar el parte a mano. Lo que sale de
> aquí es lo que ve el front y lo que la persona devuelve en el cuerpo: si
> saliera sucio, la pantalla estaría enseñando un código que no es el que se va
> a usar para buscar la reclamación.
>
> **Los otros siete campos se siguen copiando tal cual**, y ahí la frase vieja
> sigue entera: quitarle los espacios a una observación manuscrita la
> convertiría en otra cosa. Qué campo es un código lo decide el dominio
> (`CAMPOS_DE_CODIGO`), no este paso. Y el saneo **no es silencioso**: cuando
> cambia el valor deja aviso (R15), porque si no taparía una lectura mala del
> modelo sin que nadie se entere.
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
    sanear_valor_leido,
)
from domain.models.prompt import PromptSpec
from domain.ports.extractor import ExtractorPort
from domain.ports.prompts import RepositorioPromptsPort

from application.pipelines.confianza import sanear_confianza
from application.pipelines.contexto_parte import ContextoParte

#: Lo que se le manda al modelo: el PDF del parte, sin rasterizar.
MIME_PDF = "application/pdf"

#: Tope de lo que se envía en línea al modelo (R16). Un parte troceado son
#: 1–2 páginas: lo que se pase de aquí no es un parte, es otra cosa.
MAX_BYTES_PARTE = 15 * 1024 * 1024


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
        confianza, aviso = sanear_confianza(bruto.confianza_pct)
        if aviso is not None:
            avisos.append(f"{nombre}: {aviso}")
        # F-032 R11 · los dos códigos salen sin blancos; los otros siete
        # campos, tal cual. Qué es un código lo decide el dominio.
        valor = sanear_valor_leido(nombre, bruto.valor)
        if valor != bruto.valor:
            # R15 · el saneo no es silencioso: quien mire el parte tiene que
            # poder ver que el valor guardado no es letra por letra el del
            # papel. Ni el código de obra ni el nº de incidencia son un dato
            # personal: ya viven en claro en sus propias columnas.
            avisos.append(
                f"{nombre}: el modelo leyó «{bruto.valor}» y se ha guardado "
                f"sin espacios como «{valor}»"
            )
        campos[nombre] = CampoExtraido(valor=valor, confianza_pct=confianza)

    avisos.extend(
        f"{sobrante}: el modelo devolvió un campo que no está en el contrato, "
        "y se ha descartado"
        for sobrante in brutos
        if sobrante not in CAMPOS_DEL_PARTE
    )
    return campos, avisos
