# services/postventa-api/application/pipelines/sigrid_bandeja.py
"""Las reclamaciones de Sigrid en la revisión de la bandeja (F-065): la aplicación.

`specs/F-065-revision-sigrid-backend/design.md` §10.3; requisitos R3, R4, R8 y
R9. Aquí se **orquesta**: las reglas del cruce viven en
`domain/models/sigrid_bandeja.py` y los datos llegan por dos puertos —la
bandeja (`RevisionPort`, F-056, sin cambiarlo) y las reclamaciones de la obra
(`ReclamacionesObraPort`)—. La composición de los adaptadores es del borde.

## `mirar_sigrid`, en este orden (R3)

1. `revision.listar(tope=TOPE_LECTURA_OBRA)`: **la** lectura de la base. Si
   vuelven más de 10.000, `contar` y `BandejaDemasiadoGrande` (409) **sin leer
   Sigrid** (R4): nunca se recorta la bandeja en silencio.
2. `reclamaciones.leer`: **la** lectura de Sigrid, de todas las reclamaciones
   de la obra, de cualquier estado y fecha (R5).
3. Si llegó al techo o vino `truncated`, `ReclamacionesSinVerificar` (409) con
   el número de filas y **sin cruzar nada** (R8): nunca conflictos a medias.
4. Si las filas son de más de una obra (`obra_ref` distintos),
   `ObraAmbigua` (409), como el catálogo de F-036 (R9). Cero filas no es un
   error: se cruza igual, con la lista vacía.
5. `cruzar` del dominio, con la bandeja **entera** de la obra.
6. `veredictos` del dominio sobre ese cruce (R41, R42; Bloque A4 bis): el de
   cada candidata, en el orden de la bandeja (R25 de F-056). Es la **misma**
   función que usará el ensayo de F-059; aquí no se recalcula nada.

Nada más: ninguna otra operación de ningún puerto, ninguna escritura y nada
guardado entre peticiones (R28, R37). Si un puerto falla, su error sube tal
cual y no queda nada a medias.

## Lo que no sale de aquí

`obra_ref` sirve para contar obras y se queda aquí: la reclamación del dominio
no lo lleva (R6, R22). Ningún mensaje de error repite una fila (R40): dicen
la obra y recuentos.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.models.errores import (
    BandejaDemasiadoGrande,
    ObraAmbigua,
    ReclamacionesSinVerificar,
)
from domain.models.revision import TOPE_LECTURA_OBRA, SituacionDeRevision
from domain.models.sigrid_bandeja import (
    Cruce,
    ReclamacionSigrid,
    VeredictoDeVolcado,
    cruzar,
    veredictos,
)
from domain.ports.reclamaciones_obra import FilaReclamacionObra, ReclamacionesObraPort
from domain.ports.revision import RevisionPort

__all__ = ["VistaDeSigrid", "mirar_sigrid"]


@dataclass(frozen=True)
class VistaDeSigrid:
    """Lo que la ruta enseña: la bandeja leída y su cruce con Sigrid.

    `situaciones` es la bandeja entera de la obra (el borde saca de ahí los
    vigentes de las incidencias con hallazgos); `cruce`, el del dominio;
    `veredictos`, el de cada candidata, en el orden de `situaciones` (R41).
    """

    obra_codigo: str
    situaciones: tuple[SituacionDeRevision, ...]
    cruce: Cruce
    veredictos: tuple[VeredictoDeVolcado, ...]


def mirar_sigrid(
    obra_codigo: str,
    *,
    revision: RevisionPort,
    reclamaciones: ReclamacionesObraPort,
    tip: int,
) -> VistaDeSigrid:
    """La bandeja de la obra frente a todas sus reclamaciones de Sigrid (§10.3).

    `obra_codigo` llega ya normalizado por el borde (R1); `tip` es el tipo de
    concepto de las reclamaciones (`SIGRID_TIP_RECLAMACION`).
    """
    situaciones = revision.listar(obra_codigo=obra_codigo, tope=TOPE_LECTURA_OBRA)
    if len(situaciones) > TOPE_LECTURA_OBRA:
        total = revision.contar(obra_codigo=obra_codigo)
        raise BandejaDemasiadoGrande(
            f"la obra tiene {total} incidencias en la bandeja y la revisión lee "
            f"{TOPE_LECTURA_OBRA} como mucho: no se recorta la lista en silencio",
            total=total,
        )

    lectura = reclamaciones.leer(codigo_obra=obra_codigo, tip=tip)
    if lectura.llego_al_techo:
        raise ReclamacionesSinVerificar(
            f"Sigrid ha devuelto {len(lectura.filas)} reclamaciones de la obra "
            f"«{obra_codigo}» y la lista puede venir cortada: no se cruza nada, "
            "para no enseñar conflictos a medias",
            filas=len(lectura.filas),
        )
    obras = {fila.obra_ref for fila in lectura.filas}
    if len(obras) > 1:
        raise ObraAmbigua(
            f"las reclamaciones leídas son de {len(obras)} obras con el código "
            f"«{obra_codigo}» y el sistema no elige"
        )

    cruce = cruzar(situaciones, [_reclamacion_de(fila) for fila in lectura.filas])
    return VistaDeSigrid(
        obra_codigo=obra_codigo,
        situaciones=tuple(situaciones),
        cruce=cruce,
        veredictos=veredictos(situaciones, cruce),
    )


def _reclamacion_de(fila: FilaReclamacionObra) -> ReclamacionSigrid:
    """La fila del puerto como la ve el dominio: los campos de R6 sin `obra_ref`."""
    return ReclamacionSigrid(
        cod=fila.cod,
        estado=fila.estado_codigo,
        fecha=fila.fecha,
        unidad_codigo=fila.unidad_codigo,
        ubicacion=fila.ubicacion,
        oficio_codigo=fila.oficio_codigo,
        oficio_nombre=fila.oficio_nombre,
        tipo_codigo=fila.tipo_codigo,
        tipo_nombre=fila.tipo_nombre,
        descripcion=fila.descripcion,
        referencia=fila.referencia,
        ficha=fila.ficha,
    )
