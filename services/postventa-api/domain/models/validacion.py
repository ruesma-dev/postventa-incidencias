# services/postventa-api/domain/models/validacion.py
"""Las reglas que deciden qué se hace con un parte (F-004, paso 4).

**Dominio puro.** Ni red, ni base de datos, ni IA, ni Sigrid: `validar_parte`
recibe lo que leyó F-003 y lo que se leyó de la casilla de la firma, y
devuelve un veredicto. Mismas entradas, mismo resultado. Eso es lo que permite
revalidar un parte cuando una persona corrija un campo (F-011) sin volver a
gastar una llamada al modelo.

## Dos destinos, y no es una sutileza

`docs/ARCHITECTURE.md` (semántica 3) exige que un parte sin firma humana no se
archive ni se cierre; la decisión (2) del humano dice que las observaciones
manuscritas son el único motivo de rechazo. Las dos cosas se sostienen a la
vez porque son **dos trabajos distintos para dos personas distintas**:

- `cola_validacion_humana` — el parte está completo y firmado, pero el cliente
  escribió algo. Alguien tiene que **decidir** si la reparación se da por
  buena, con la transcripción delante. Ahí solo entra quien trae
  observaciones, que es lo que dice el `acceptance`.
- `revision_manual` — al parte le faltan los mínimos: un dato decisivo
  ilegible o ninguna firma humana. Hay que **arreglarlo**, volviendo al papel.

## Lo que estas reglas NO hacen

No interpretan **qué dice** la observación (eso es F-016: aquí, cualquier
texto no vacío produce el mismo motivo diga lo que diga), no comprueban contra
Sigrid que la incidencia exista o esté abierta (F-008/F-009, que necesitan
red), no guardan la cola (F-005) y no exigen ningún formato al nº de
incidencia mientras F-008 no confirme qué es cada mitad.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.models.extraccion import CampoExtraido, ExtraccionParte
from domain.models.firma import UMBRAL_CONFIANZA, ClasificacionFirma, LecturaFirma

__all__ = [
    "CAMPOS_DECISIVOS",
    "UMBRAL_CONFIANZA",
    "CodigoMotivo",
    "Destino",
    "Motivo",
    "ResultadoValidacion",
    "Veredicto",
    "validar_parte",
]


class Veredicto(str, Enum):
    """¿Este parte reúne lo necesario para archivarse y cerrarse?"""

    APTO = "apto"
    NO_APTO = "no_apto"


class Destino(str, Enum):
    """Dónde va el parte, que es lo que de verdad dice qué hacer con él."""

    ARCHIVO_Y_CIERRE = "archivo_y_cierre"
    COLA_VALIDACION_HUMANA = "cola_validacion_humana"
    REVISION_MANUAL = "revision_manual"


class CodigoMotivo(str, Enum):
    """Por qué un parte no es apto. Es contrato: lo consumen F-005 y F-007."""

    CODIGO_OBRA_NO_LEGIBLE = "codigo_obra_no_legible"
    NUMERO_INCIDENCIA_NO_LEGIBLE = "numero_incidencia_no_legible"
    FIRMA_NO_HUMANA = "firma_no_humana"
    OBSERVACIONES_MANUSCRITAS = "observaciones_manuscritas"


#: Los únicos campos de texto que deciden (`ARCHITECTURE.md`, semántica 4 bis).
#:
#: El orden **es** el orden en el que salen los motivos (R18). Y la lista es
#: corta a propósito: la remesa real deja en blanco fecha, horas, nombre y DNI
#: en casi todos los partes, así que exigir más mandaría a revisión manual lo
#: que hoy se tramita a mano sin problema.
CAMPOS_DECISIVOS: tuple[str, ...] = ("codigo_obra", "numero_incidencia")

#: El campo manuscrito que decide «firmado no es conforme» (decisión del
#: humano del 2026-08-19). Es **uno**: ni la fecha, ni el DNI, ni las horas.
CAMPO_OBSERVACIONES = "observaciones"

#: Los textos de los motivos, en castellano llano y para Posventa (R6).
#:
#: Sin jerga y sin nombres de campo del código: quien los lee tiene que saber
#: qué hacer con el parte sin abrir un fichero fuente. Los de la firma son
#: tres y **distintos** a propósito: «no hay firma», «hay un aspa» y «no se ve»
#: piden cosas distintas —volver a pedir el parte firmado en el primer caso,
#: bastar con volver a escanearlo en el tercero—.
TEXTO_CODIGO_OBRA_NO_LEGIBLE = (
    "No se lee el código de obra del parte. Sin él no se sabe en qué carpeta "
    "va ni cómo se llama el fichero."
)
TEXTO_NUMERO_INCIDENCIA_NO_LEGIBLE = (
    "No se lee el nº de incidencia. Sin él no se puede nombrar el parte ni "
    "cerrar la incidencia."
)
TEXTO_FIRMA_CASILLA_VACIA = (
    "La casilla de la firma del cliente está vacía: no hay conformidad."
)
TEXTO_FIRMA_MARCA_SIMPLE = (
    "En la casilla de la firma hay una marca simple —un aspa o un trazo—, no "
    "una firma. Eso no es la conformidad del cliente."
)
TEXTO_FIRMA_ILEGIBLE = (
    "No se ha podido leer la casilla de la firma. Tiene que mirarlo una "
    "persona."
)
TEXTO_OBSERVACIONES_MANUSCRITAS = (
    "El parte trae observaciones escritas a mano. Firmado no es lo mismo que "
    "conforme: alguien tiene que leerlas y decidir si la reparación se da por "
    "buena."
)

#: Qué texto le corresponde a cada etiqueta que no es una firma humana.
_TEXTO_POR_ETIQUETA: dict[ClasificacionFirma, str] = {
    ClasificacionFirma.CASILLA_VACIA: TEXTO_FIRMA_CASILLA_VACIA,
    ClasificacionFirma.MARCA_SIMPLE: TEXTO_FIRMA_MARCA_SIMPLE,
    ClasificacionFirma.ILEGIBLE: TEXTO_FIRMA_ILEGIBLE,
}

#: Los textos de los campos decisivos, por campo.
_TEXTO_POR_DECISIVO: dict[str, tuple[CodigoMotivo, str]] = {
    "codigo_obra": (
        CodigoMotivo.CODIGO_OBRA_NO_LEGIBLE,
        TEXTO_CODIGO_OBRA_NO_LEGIBLE,
    ),
    "numero_incidencia": (
        CodigoMotivo.NUMERO_INCIDENCIA_NO_LEGIBLE,
        TEXTO_NUMERO_INCIDENCIA_NO_LEGIBLE,
    ),
}


@dataclass(frozen=True)
class Motivo:
    """Por qué el parte no es apto: un código para la máquina y un texto para
    la persona."""

    codigo: CodigoMotivo
    texto: str


@dataclass(frozen=True)
class ResultadoValidacion:
    """El veredicto de un parte, con todo lo que necesita quien lo reciba.

    `clasificacion_firma` es la etiqueta **efectiva** (R14 bis, decisión D4):
    una `humana` que no llega al umbral sale de aquí como `ilegible`, que es
    lo mismo que dice el motivo que la acompaña. La lectura cruda del modelo
    no se pierde: viaja entera en la respuesta de `/api/firma`.

    `observaciones` va siempre que las haya, aunque el parte acabe en revisión
    manual: quien lo recupere necesita saber qué se va a encontrar.
    """

    hash_parte: str
    veredicto: Veredicto
    destino: Destino
    motivos: tuple[Motivo, ...]
    clasificacion_firma: ClasificacionFirma
    observaciones: str | None
    confianza_observaciones: int
    avisos: tuple[str, ...] = ()
    #: Los dos campos decisivos, tal y como se leyeron. **No son decoración**:
    #: entran en la huella del veredicto (F-026 H-1, 2026-09-12), porque el
    #: número de incidencia decide sobre qué reclamación del ERP se escribe el
    #: cierre y el código de obra decide en qué carpeta acaba un PDF con el DNI
    #: manuscrito de un cliente. Van con valor por defecto para no romper a
    #: quien construya un veredicto a mano en un test, pero `validar_parte` los
    #: rellena siempre.
    codigo_obra: str = ""
    numero_incidencia: str = ""

    @property
    def es_apto(self) -> bool:
        """¿Se puede archivar y cerrar sin que lo mire nadie?"""
        return self.veredicto == Veredicto.APTO


def es_legible(campo: CampoExtraido) -> bool:
    """¿Este campo se ha leído de verdad? (R12).

    Dos condiciones, y las dos hacen falta: que traiga valor —«solo espacios»
    es vacío, que de un escaneo salen las dos cosas— y que la confianza llegue
    al umbral. Archivar con un código de obra que el modelo apenas distinguió
    es meter el parte en la carpeta de otra promoción.
    """
    return not campo.esta_vacio and campo.confianza_pct >= UMBRAL_CONFIANZA


def validar_parte(
    extraccion: ExtraccionParte, firma: LecturaFirma
) -> ResultadoValidacion:
    """El veredicto, el destino y los motivos de un parte. Función **pura**.

    Cinco pasos, en este orden:

    1. Se reúnen **todos** los motivos, sin cortar al primero (R18): un parte
       al que se le devuelve un fallo cada vez obliga a dos vueltas donde cabe
       una.
    2. Sin motivos → apto, a archivo y cierre.
    3. Un único motivo y es el de las observaciones → la cola de validación
       humana: hay algo que **decidir** (R9).
    4. Cualquier otro caso → revisión manual: hay algo que **arreglar** (R19).
    5. La transcripción de las observaciones viaja siempre que la haya, vaya
       el parte a la cola o al papel.
    """
    observaciones = extraccion.campo(CAMPO_OBSERVACIONES)
    motivos = _motivos(extraccion, firma, observaciones)

    return ResultadoValidacion(
        hash_parte=extraccion.hash_parte,
        veredicto=Veredicto.APTO if not motivos else Veredicto.NO_APTO,
        destino=_destino(motivos),
        motivos=motivos,
        clasificacion_firma=firma.clasificacion_efectiva,
        observaciones=None if observaciones.esta_vacio else observaciones.valor,
        confianza_observaciones=observaciones.confianza_pct,
        codigo_obra=extraccion.campo("codigo_obra").valor or "",
        numero_incidencia=extraccion.campo("numero_incidencia").valor or "",
    )


def _motivos(
    extraccion: ExtraccionParte,
    firma: LecturaFirma,
    observaciones: CampoExtraido,
) -> tuple[Motivo, ...]:
    """Todos los motivos del parte, en el orden declarado (R18)."""
    motivos = [
        Motivo(*_TEXTO_POR_DECISIVO[nombre])
        for nombre in CAMPOS_DECISIVOS
        if not es_legible(extraccion.campo(nombre))
    ]

    if not firma.es_conformidad_del_cliente:
        motivos.append(
            Motivo(
                codigo=CodigoMotivo.FIRMA_NO_HUMANA,
                texto=_TEXTO_POR_ETIQUETA[firma.clasificacion_efectiva],
            )
        )

    if not observaciones.esta_vacio:
        motivos.append(
            Motivo(
                codigo=CodigoMotivo.OBSERVACIONES_MANUSCRITAS,
                texto=TEXTO_OBSERVACIONES_MANUSCRITAS,
            )
        )

    return tuple(motivos)


def _destino(motivos: tuple[Motivo, ...]) -> Destino:
    """A dónde va el parte según lo que le pase.

    La cola de validación humana es **solo** para el parte completo y firmado
    al que le sobran observaciones: meter ahí uno incompleto haría que alguien
    decidiera sobre una reparación que el cliente ni siquiera dio por
    recibida.
    """
    if not motivos:
        return Destino.ARCHIVO_Y_CIERRE
    codigos = {motivo.codigo for motivo in motivos}
    if codigos == {CodigoMotivo.OBSERVACIONES_MANUSCRITAS}:
        return Destino.COLA_VALIDACION_HUMANA
    return Destino.REVISION_MANUAL
