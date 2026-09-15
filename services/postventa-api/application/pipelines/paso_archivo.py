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

## Y la garantía de orden de F-019, que no es idempotencia sino precedencia

Antes de tocar el puerto de archivo se escribe la traza en estado
`pendiente`. Como `postventa.archivos.hash_parte` referencia a
`postventa.partes`, esa escritura **sólo puede hacerse si el parte ya consta
guardado**: es la misma restricción que el 2026-08-25 hizo fallar el proceso
*después* de subir el fichero, puesta a fallar *antes*. Ver
`_dejar_constancia_previa`.

«El mismo parte» es **el `hash` del parte troceado** que produce F-002 y que
F-005 usa como clave primaria de la tabla `archivos`. F-006 no define ningún
criterio propio: ni por nombre, ni por incidencia, ni por bytes. Dos criterios
del mismo concepto divergen siempre.
"""

from __future__ import annotations

from datetime import datetime

from domain.models.errores import (
    ArchivoFallido,
    ArchivoSinTraza,
    ErrorDePersistencia,
)
from domain.models.nombrado import componer_destino
from domain.models.persistencia import EstadoArchivo, TrazaArchivo
from domain.ports.archivo import ArchivoPort, ItemArchivado
from domain.ports.persistencia import RepositorioPartesPort

from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.puerta_de_estado import exigir_parte_aprobado

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

    1. **Puerta de aptitud** (R17, R18; F-026 R23). Antes de nombrar y antes
       de tocar el puerto: un parte que no es apto **ni consta aprobado** no
       crea ni la carpeta.
    2. **Nombrado** (R1–R9). `NombradoImposible` sale sin haber tocado nada.
    3. **Idempotencia por traza** (R14). La capa barata.
    4. **Traza previa en `pendiente`** (F-019, R19). La garantía de orden: si
       el parte no consta guardado, la clave ajena la rechaza y el archivado
       se aborta **sin haber llamado a nadie**.
    5. `asegurar_carpeta` (R11, R12).
    6. `buscar` el homónimo, para poder avisar del reemplazo (R16).
    7. `subir`, reemplazando (R15).
    8. **Traza final** (R23, R24), que se persiste tanto si fue bien como si
       no.

    Levanta `ParteNoApto`, `NombradoImposible`, `ArchivoFallido`,
    —desde F-019— `ReferenciaNoConsta` y `PersistenciaNoDisponible` de la
    traza previa, y —si la subida salió bien y la traza final no se pudo
    escribir— `ArchivoSinTraza`. Los traduce a HTTP el borde; aquí no se sabe
    de códigos de estado.
    """
    _exigir_admitido(ctx, repositorio)

    destino = componer_destino(
        carpeta_base=carpeta_base,
        codigo_obra=_campo(ctx, "codigo_obra"),
        numero_incidencia=_campo(ctx, "numero_incidencia"),
    )

    if _ya_archivado(ctx, traza_previa):
        ctx.avisos.append(AVISO_YA_ARCHIVADO)
        ctx.archivo = traza_previa
        return ctx

    _dejar_constancia_previa(repositorio, ctx, destino)

    try:
        item = _subir(ctx, archivador, destino)
    except ArchivoFallido as fallo:
        ctx.archivo = _traza_de_error(ctx, destino, motivo=fallo.motivo)
        repositorio.guardar_archivo(traza=ctx.archivo)
        raise

    ctx.archivo = _traza_de_exito(ctx, item, ahora=ahora)
    _dejar_constancia(repositorio, ctx)
    return ctx


def _dejar_constancia_previa(
    repositorio: RepositorioPartesPort, ctx: ContextoParte, destino
) -> None:
    """Escribe la traza en `pendiente` **antes de tocar el puerto** (F-019, R19).

    Es la garantía de orden de F-019, y **el orden es el requisito**: no se
    sube un byte a SharePoint de un parte que no conste guardado.

    Cómo funciona, y por qué así: `postventa.archivos.hash_parte` tiene una
    clave ajena contra `postventa.partes`. Si el parte no consta, esta
    escritura **no puede hacerse**, el error sube y el archivado se aborta sin
    haber llamado a nadie —ni carpeta, ni búsqueda, ni subida—. Es decir: la
    misma restricción que hasta el 2026-08-25 hacía fallar el proceso
    **después** de subir el fichero pasa a hacerlo fallar **antes**.

    No se añade una comprobación paralela (`consta_parte`) que pueda divergir
    de la restricción real: se usa la restricción. Entre una consulta previa y
    la escritura cabe todo —otro proceso borrando el parte por medio—, y
    además habría que tocar `RepositorioPartesPort`, que es de F-005.

    Va **después** de la idempotencia de F-006 a propósito: escribirla con el
    parte ya archivado lo degradaría a `pendiente`, y `pendiente` no corta el
    reintento (R14), así que el siguiente intento volvería a subir el fichero.

    Los errores suben **sin traducir**: el borde distingue `ReferenciaNoConsta`
    (→ 409 «guarda el parte primero») de `PersistenciaNoDisponible` (→ 503
    «no se ha subido nada, se puede reintentar»), y esas dos respuestas llevan
    a acciones opuestas. Aquí no se sabe de códigos de estado.
    """
    ctx.archivo = TrazaArchivo(
        hash_parte=ctx.parte.hash,
        estado=EstadoArchivo.PENDIENTE,
        nombre_fichero=destino.nombre_fichero,
        carpeta=destino.carpeta,
    )
    repositorio.guardar_archivo(traza=ctx.archivo)


def _dejar_constancia(repositorio: RepositorioPartesPort, ctx: ContextoParte) -> None:
    """Guarda la traza del parte **ya subido**, o dice que se quedó sin ella.

    Aquí arriba la subida ya ocurrió, y eso es lo que hace falta contar. Dejar
    salir el error de la persistencia tal cual —que es lo que pasaba hasta el
    defecto 14 de F-010— produce el mismo `PersistenciaNoDisponible` que sale
    cuando la base no responde y **no se ha subido nada**, y las dos lecturas
    llevan a acciones opuestas: reintentar, o ir a mirar la carpeta.

    Por eso se renombra a `ArchivoSinTraza`: no se traga el fallo —el llamante
    se entera y el motivo viaja entero— pero sí dice **en qué punto** ocurrió,
    que es lo único que el borde no puede deducir.

    El bloque `except ArchivoFallido` de arriba NO hace esto a propósito: allí
    la subida falló, así que su `PersistenciaNoDisponible` sí significa «no hay
    nada arriba» y el borde lo traduce como tal.
    """
    try:
        repositorio.guardar_archivo(traza=ctx.archivo)
    except ErrorDePersistencia as sin_traza:
        raise ArchivoSinTraza(sin_traza.motivo) from sin_traza


def _exigir_admitido(ctx: ContextoParte, repositorio: RepositorioPartesPort) -> None:
    """Solo se archiva el parte que está **`aprobado`** (F-028 R33).

    Hasta F-026 esta puerta miraba el veredicto y, si no bastaba, una
    aprobación suelta. Desde F-028 mira **el estado del parte**, que es lo que
    combina los tres hechos —el veredicto, la última decisión de una persona y
    la traza de cierre— con un criterio escrito una sola vez
    (`domain/models/estado.py`).

    Lo que eso cambia aquí, y es medio encargo de la feature: **desaparece el
    atajo del apto**. Hasta ahora el parte verde pasaba sin consultar nada, y
    mientras eso fuera así un parte apto rechazado por una persona se habría
    archivado igual (`design.md` §0.5 y §6). El coste —una consulta por parte
    y paso— está declarado y aceptado.

    Lo demás no se mueve: «no hay veredicto» sigue siendo un motivo propio y
    va primero, y la situación **se lee del repositorio y nunca del cuerpo**
    (R33). La explicación larga está en `puerta_de_estado.py`.
    """
    exigir_parte_aprobado(
        ctx,
        repositorio,
        sin_veredicto=(
            "no consta que este parte haya pasado la validación: no se "
            "archiva un parte del que nadie ha emitido veredicto"
        ),
        y_por_eso="no se archiva",
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
