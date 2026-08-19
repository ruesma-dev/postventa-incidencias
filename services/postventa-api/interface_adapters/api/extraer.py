# services/postventa-api/interface_adapters/api/extraer.py
"""Handler de `POST /api/extraer`, sin nada de Azure dentro.

Aquí se **compone el paso** —extractor y repositorio de prompts, con sus
adaptadores— y se serializa el resultado, como manda `docs/CONVENTIONS.md`: la
composición vive en el punto de entrada y nunca dentro de un paso.

Los dos parámetros inyectables son **la costura de test** del endpoint: con
ellos, la suite prueba el borde entero sin que aparezca un proveedor por
ninguna parte. Sin ellos, el handler construye lo de verdad, y es ahí —y solo
ahí— donde se exige la credencial.

Una llamada = **un parte**. Es lo que decidió `docs/ARCHITECTURE.md`: la
Function corta a los 230 s y una remesa de veintidós partes a una llamada de
IA por parte no cabe en una sola petición.
"""

from __future__ import annotations

from typing import Any

from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_extraccion import paso_extraccion
from config.settings import obtener_ajustes
from domain.models.extraccion import ExtraccionParte
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.ports.extractor import ExtractorPort
from domain.ports.prompts import RepositorioPromptsPort
from infrastructure.llm.fabrica import construir_extractor
from infrastructure.prompts.prompts_yaml import RepositorioPromptsYaml


def extraer_parte(
    contenido: bytes,
    *,
    hash_parte: str = "",
    extractor: ExtractorPort | None = None,
    prompts: RepositorioPromptsPort | None = None,
) -> dict[str, Any]:
    """Extrae los campos de **un** parte y devuelve el cuerpo de la respuesta.

    Levanta `ParteDemasiadoGrande` (→ 413) y `ExtraccionFallida` (→ 502) sin
    traducirlas: convertir eso en códigos HTTP es trabajo del borde.
    """
    ajustes = obtener_ajustes()
    contexto = paso_extraccion(
        ContextoParte(parte=_como_parte(contenido, hash_parte)),
        extractor if extractor is not None else construir_extractor(ajustes),
        prompts
        if prompts is not None
        else RepositorioPromptsYaml(ajustes.prompts_yaml),
        ajustes.prompt_key,
    )
    return _serializar(contexto.extraccion)


def _como_parte(contenido: bytes, hash_parte: str) -> ParteTroceado:
    """Envuelve los bytes que llegan en el `ParteTroceado` que produce F-002.

    Al endpoint le llega un parte ya troceado y **suelto**: quien conoce su
    origen y sus páginas es el front, que las recibió de `/split`. Aquí solo
    hace falta lo que el paso usa —el contenido y el hash— y el resto se
    declara vacío en vez de inventarse: `paginas_origen` no se deduce.
    """
    return ParteTroceado(
        hash=hash_parte,
        origen="",
        paginas_origen=(),
        modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
        contenido=contenido,
    )


def _serializar(extraccion: ExtraccionParte) -> dict[str, Any]:
    """Pasa la extracción a JSON. Ni una clave más que las de R17."""
    return {
        "hash_parte": extraccion.hash_parte,
        "campos": {
            nombre: {"valor": campo.valor, "confianza_pct": campo.confianza_pct}
            for nombre, campo in extraccion.campos.items()
        },
        "traza": {
            "proveedor": extraccion.traza.proveedor,
            "modelo": extraccion.traza.modelo,
            "prompt_key": extraccion.traza.prompt_key,
            "version_prompt": extraccion.traza.version_prompt,
            "huella_prompt": extraccion.traza.huella_prompt,
        },
        "avisos": list(extraccion.avisos),
    }
