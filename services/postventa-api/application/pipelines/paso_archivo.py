# services/postventa-api/application/pipelines/paso_archivo.py
"""Paso 6 del pipeline: archivar el parte en su sitio (F-006).

Habla con **puertos**, jamás con adaptadores: este módulo no sabe que debajo
hay SharePoint ni que hay PostgreSQL, y por eso se prueba entero con dobles en
memoria, sin red y sin subir nada. Es lo mismo que hace `paso_extraccion` con
`ExtractorPort` y `paso_persistencia` con `RepositorioPartesPort`.

`ahora` entra por parámetro y no se lee del reloj aquí, por lo mismo que en
F-005: un paso que consulta la hora no se puede probar dos veces con el mismo
resultado, y la traza que produce lleva fecha.

`paso_archivo` **no construye adaptadores**: la composición vive en el punto de
entrada (`docs/CONVENTIONS.md`). Aquí no se puede ni intentar subir desde
local, porque aquí no hay nada que sepa cómo hacerlo.

## Las tres capas de idempotencia, y qué tapa cada una

Reprocesar una remesa es lo normal, no la excepción: alguien corrige un campo
en el front y vuelve a lanzar. El `acceptance` de F-006 dice que eso no puede
producir un duplicado, y hacen falta tres capas porque cada una ve una cosa
que las otras no:

| Capa | Qué evita | Cómo |
|---|---|---|
| **L1 · traza** | Volver a subir el mismo parte | La traza en estado `archivado` corta **antes de llamar a nadie**: ni token, ni red, ni bytes |
| **L2 · reemplazo** | El `fichero (1).pdf` | La subida reemplaza siempre el homónimo; el puerto no ofrece otra opción |
| **L3 · carpeta** | Dos carpetas para la misma obra | `asegurar_carpeta` trata «ya existe» como éxito |

«El mismo parte» es **el `hash` del parte troceado** que produce F-002 y que
F-005 usa como clave primaria de la tabla `archivos`. F-006 no define ningún
criterio propio: ni por nombre, ni por incidencia, ni por bytes. Dos criterios
del mismo concepto divergen siempre.
"""

from __future__ import annotations

from datetime import datetime

from domain.models.errores import ArchivoFallido, ParteNoApto
from domain.models.nombrado import componer_destino
from domain.models.persistencia import EstadoArchivo, TrazaArchivo
from domain.models.validacion import Destino, Veredicto
from domain.ports.archivo import ArchivoPort, ItemArchivado
from domain.ports.persistencia import RepositorioPartesPort

from application.pipelines.contexto_parte import ContextoParte

__all__ = [
    "AVISO_REEMPLAZADO",
    "AVISO_YA_ARCHIVADO",
    "MIME_PDF",
    "paso_archivo",
]

#: Lo que se sube siempre: el PDF del parte troceado.
MIME_PDF = "application/pdf"

#: El parte ya constaba archivado y no se ha vuelto a subir (R14).
AVISO_YA_ARCHIVADO = (
    "este parte ya estaba archivado: se devuelve el destino que ya tenía y no "
    "se ha vuelto a subir"
)

#: Había un fichero con ese nombre y se ha pisado (R16).
#:
#: Aparece **solo** cuando de verdad había uno: un aviso que sale siempre es
#: un aviso que nadie lee, y este tiene que llamar la atención de quien revise
#: el archivo, porque significa que hubo una versión anterior del parte
#: conformado y ya no está.
AVISO_REEMPLAZADO = (
    "en la carpeta ya había un fichero con este nombre y se ha reemplazado por "
    "esta versión: si eran dos escaneos distintos, el anterior ya no está"
)


def paso_archivo(
    ctx: ContextoParte,
    archivador: ArchivoPort,
    repositorio: RepositorioPartesPort,
    *,
    carpeta_base: str,
    ahora: datetime,
    traza_previa: TrazaArchivo | None = None,
) -> ContextoParte:
    """Archiva el parte y deja constancia de lo que pasó.

    Los pasos, **en este orden**, y el orden es la mitad del requisito:

    1. **Puerta de aptitud** (R17, R18). Antes de nombrar y antes de tocar el
       puerto: un parte que no es apto no crea ni la carpeta.
    2. **Nombrado** (R1–R9). `NombradoImposible` sale sin haber tocado nada.
    3. **Idempotencia por traza** (R14). La capa barata.
    4. `asegurar_carpeta` (R11, R12).
    5. `buscar` el homónimo, para poder avisar del reemplazo (R16).
    6. `subir`, reemplazando (R15).
    7. **Traza** (R23, R24), que se persiste tanto si fue bien como si no.

    Levanta `ParteNoApto`, `NombradoImposible` o `ArchivoFallido`. Los tres
    los traduce a HTTP el borde; aquí no se sabe de códigos de estado.
    """
    _exigir_apto(ctx)

    destino = componer_destino(
        carpeta_base=carpeta_base,
        codigo_obra=_campo(ctx, "codigo_obra"),
        numero_incidencia=_campo(ctx, "numero_incidencia"),
    )

    if _ya_archivado(ctx, traza_previa):
        ctx.avisos.append(AVISO_YA_ARCHIVADO)
        ctx.archivo = traza_previa
        return ctx

    try:
        item = _subir(ctx, archivador, destino)
    except ArchivoFallido as fallo:
        ctx.archivo = _traza_de_error(ctx, destino, motivo=fallo.motivo)
        repositorio.guardar_archivo(traza=ctx.archivo)
        raise

    ctx.archivo = _traza_de_exito(ctx, item, ahora=ahora)
    repositorio.guardar_archivo(traza=ctx.archivo)
    return ctx


def _exigir_apto(ctx: ContextoParte) -> None:
    """Solo se archiva lo que F-004 declaró apto (R17, R18).

    Dos motivos distintos a propósito: «no hay veredicto» se arregla
    revalidando el parte; «el veredicto dice que no» se arregla volviendo al
    papel o decidiendo a mano. Un motivo genérico obligaría a mirar las dos
    cosas.

    El destino manda además del veredicto: un parte apto que F-004 mandara a
    otro sitio no se archiva aquí, porque el destino es lo que de verdad dice
    qué hacer con él.
    """
    if ctx.validacion is None:
        raise ParteNoApto(
            "no consta que este parte haya pasado la validación: no se "
            "archiva un parte del que nadie ha emitido veredicto"
        )
    if (
        ctx.validacion.veredicto != Veredicto.APTO
        or ctx.validacion.destino != Destino.ARCHIVO_Y_CIERRE
    ):
        raise ParteNoApto(
            f"el parte no es apto para archivo y cierre: la validación lo "
            f"manda a «{ctx.validacion.destino.value}»"
        )


def _campo(ctx: ContextoParte, nombre: str) -> str | None:
    """El valor leído de un campo del parte, o `None` si no se leyó nada.

    Que falte la extracción entera no es un caso del camino normal —F-004 no
    declara apto lo que no se ha leído—, pero si llegara, el nombrado se
    negará diciendo qué falta, que es mejor que reventar con un `AttributeError`
    a mitad del paso.
    """
    if ctx.extraccion is None:
        return None
    return ctx.extraccion.campo(nombre).valor


def _ya_archivado(ctx: ContextoParte, traza: TrazaArchivo | None) -> bool:
    """¿Consta ya archivado **este** parte? (R13, R14).

    Las dos condiciones hacen falta: que la traza sea de este `hash` —la de
    otro parte no dice nada de este— y que su estado sea `archivado`.
    `pendiente` y `error` **no** cortan: es lo que hace posible reintentar
    después de un fallo sin que el parte quede atascado para siempre.
    """
    return (
        traza is not None
        and traza.hash_parte == ctx.parte.hash
        and traza.estado == EstadoArchivo.ARCHIVADO
    )


def _subir(ctx: ContextoParte, archivador: ArchivoPort, destino) -> ItemArchivado:
    """Carpeta, homónimo y subida, en ese orden."""
    archivador.asegurar_carpeta(carpeta=destino.carpeta)

    if (
        archivador.buscar(
            carpeta=destino.carpeta, nombre=destino.nombre_fichero
        )
        is not None
    ):
        ctx.avisos.append(AVISO_REEMPLAZADO)

    return archivador.subir(
        carpeta=destino.carpeta,
        nombre=destino.nombre_fichero,
        contenido=ctx.parte.contenido,
        mime=MIME_PDF,
    )


def _traza_de_exito(
    ctx: ContextoParte, item: ItemArchivado, *, ahora: datetime
) -> TrazaArchivo:
    """La traza de R23: qué se subió, dónde y cuándo."""
    return TrazaArchivo(
        hash_parte=ctx.parte.hash,
        estado=EstadoArchivo.ARCHIVADO,
        nombre_fichero=item.nombre,
        carpeta=item.carpeta,
        drive_id=item.drive_id,
        item_id=item.item_id,
        web_url=item.web_url,
        archivado_at_utc=ahora,
    )


def _traza_de_error(ctx: ContextoParte, destino, *, motivo: str) -> TrazaArchivo:
    """La traza de R24: qué se intentó y por qué no salió.

    Sin `archivado_at_utc` y en estado `error`, que es lo que deja reintentar:
    si quedara como `archivado`, R14 cortaría el reintento y el parte se
    perdería sin que nadie lo notara.

    El `motivo` viene del adaptador y **nunca** lleva los bytes del parte ni
    ningún dato del papel: esto acaba en la base y en un log.
    """
    return TrazaArchivo(
        hash_parte=ctx.parte.hash,
        estado=EstadoArchivo.ERROR,
        nombre_fichero=destino.nombre_fichero,
        carpeta=destino.carpeta,
        motivo=motivo,
    )
