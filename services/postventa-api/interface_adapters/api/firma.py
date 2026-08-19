# services/postventa-api/interface_adapters/api/firma.py
"""Handler de `POST /api/firma`, sin nada de Azure dentro.

Aquí se **compone el paso** —extractor y repositorio de prompts, con sus
adaptadores— y se serializa el resultado, como manda `docs/CONVENTIONS.md`: la
composición vive en el punto de entrada y nunca dentro de un paso.

Los dos parámetros inyectables son **la costura de test** del endpoint: con
ellos, la suite prueba el borde entero sin que aparezca un proveedor por
ninguna parte.

Una llamada = **un parte**, igual que en `/api/extraer`. Y las dos lecturas son
independientes, así que el front puede pedirlas **en paralelo**: componerlas en
una sola invocación sumaría dos timeouts de 120 s y la Function corta a los
230 s.

Lo que este endpoint publica es la lectura **cruda** del modelo. La
degradación de una `humana` dudosa a `ilegible` (R14 bis) es cosa de
`/api/validar`, que es quien emite el veredicto: aquí se registra qué se vio,
y perder eso dejaría sin forma de saber qué dijo el modelo.
"""

from __future__ import annotations

from typing import Any

from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_firma import paso_firma
from config.settings import obtener_ajustes
from domain.models.firma import LecturaFirma
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.ports.extractor import ExtractorPort
from domain.ports.prompts import RepositorioPromptsPort
from infrastructure.llm.fabrica import construir_extractor
from infrastructure.prompts.prompts_yaml import RepositorioPromptsYaml


def leer_firma(
    contenido: bytes,
    *,
    hash_parte: str = "",
    extractor: ExtractorPort | None = None,
    prompts: RepositorioPromptsPort | None = None,
) -> dict[str, Any]:
    """Clasifica la firma de **un** parte y devuelve el cuerpo de la respuesta.

    Levanta `ParteDemasiadoGrande` (→ 413) y `ExtraccionFallida` (→ 502) sin
    traducirlas: convertir eso en códigos HTTP es trabajo del borde.
    """
    ajustes = obtener_ajustes()
    contexto = paso_firma(
        ContextoParte(parte=_como_parte(contenido, hash_parte)),
        extractor if extractor is not None else construir_extractor(ajustes),
        prompts
        if prompts is not None
        else RepositorioPromptsYaml(ajustes.prompts_yaml),
        ajustes.prompt_key_firma,
    )
    return _serializar(contexto.lectura_firma)


def _como_parte(contenido: bytes, hash_parte: str) -> ParteTroceado:
    """Envuelve los bytes que llegan en el `ParteTroceado` que produce F-002.

    Igual que en `/api/extraer`, y a propósito por separado: al endpoint le
    llega un parte ya troceado y **suelto**, y quien conoce su origen y sus
    páginas es el front. Aquí solo hace falta lo que el paso usa —el contenido
    y el hash— y el resto se declara vacío en vez de inventarse.
    """
    return ParteTroceado(
        hash=hash_parte,
        origen="",
        paginas_origen=(),
        modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
        contenido=contenido,
    )


def _serializar(lectura: LecturaFirma) -> dict[str, Any]:
    """Pasa la lectura a JSON. Ni una clave más que las de R23.

    **No sale el nombre de quien firma, ni el DNI, ni ningún texto de la
    casilla**: el prompt ni siquiera los pide. Lo que viaja es una etiqueta y
    una confianza, que no son datos personales.
    """
    return {
        "hash_parte": lectura.hash_parte,
        "firma": {
            "clasificacion": lectura.clasificacion.value,
            "confianza_pct": lectura.confianza_pct,
        },
        "traza": {
            "proveedor": lectura.traza.proveedor,
            "modelo": lectura.traza.modelo,
            "prompt_key": lectura.traza.prompt_key,
            "version_prompt": lectura.traza.version_prompt,
            "huella_prompt": lectura.traza.huella_prompt,
        },
        "avisos": list(lectura.avisos),
    }
