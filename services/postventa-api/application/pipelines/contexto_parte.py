# services/postventa-api/application/pipelines/contexto_parte.py
"""Objeto de contexto de los pasos que trabajan sobre **un** parte.

`ContextoRemesa` acompaña a la remesa mientras se trocea (F-002); a partir de
ahí la unidad de trabajo es el parte, no el fichero, y cada uno sigue su
camino por su cuenta: extracción (F-003), validación (F-004), archivo (F-006).

Por eso son dos contextos y no uno gordo: F-004 enganchó `paso_firma` y
`paso_validacion` detrás sin cambiar ninguna firma de las que ya existían.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.models.aprobacion import Aprobacion
from domain.models.cierre import ResultadoCierre
from domain.models.extraccion import ExtraccionParte
from domain.models.firma import LecturaFirma
from domain.models.grafico import ResultadoGrafico
from domain.models.persistencia import TrazaArchivo, TrazaGrafico
from domain.models.remesa import ParteTroceado
from domain.models.validacion import ResultadoValidacion


@dataclass
class ContextoParte:
    """Lo que un parte lleva encima según avanza por el pipeline.

    `parte` es lo que produjo F-002 y **no se toca**: los pasos añaden, no
    reescriben la entrada. `avisos` acumula lo que cada paso quiera decirle a
    quien revise el parte a mano.

    `extraccion` y `lectura_firma` son **independientes entre sí**: ninguna
    necesita el resultado de la otra, y por eso el front puede pedirlas en
    paralelo (`design.md` §2). `validacion` necesita las dos, y si le falta
    alguna no se inventa un veredicto: levanta `ValidacionSinDatos` (R21).

    `archivo` es la traza de F-005 que deja el paso de archivo (F-006). Va
    aquí y no en un contexto nuevo por lo mismo que `validacion`: enganchar un
    paso detrás no puede obligar a cambiar la firma de los que ya existían.

    `grafico` es lo que deja el paso del gráfico (F-012, paso 7a), que va
    **delante** del cierre: ninguna reclamación se cierra sin su parte dentro
    de Sigrid. Lleva el plan entero por lo mismo que `cierre`.

    `traza_grafico` es distinto, y la distinción es el requisito: no lo deja el
    paso del gráfico, lo **lee** el paso de cierre del repositorio (R49) para
    poder enseñar el estado del gráfico en su dry-run y para exigir que conste
    `adjuntado` antes del `commit` (R2). Viene de la base y **nunca del cuerpo
    de la petición**: si viniera del cuerpo, quien llama podría afirmar que
    adjuntó algo que no adjuntó, y con eso se cierra una reclamación sin su
    parte.

    `cierre` es lo que deja el paso de cierre (F-009), y lleva **el plan
    entero** y no solo el estado: quien recibe la respuesta necesita ver el
    dry-run —los dos estados legibles, con qué login se firmaría y el estado
    del gráfico— antes de confirmar (R9, R49). La traza que se guarda en la
    base es otra cosa y va aparte, porque guarda menos: el `oid` y nunca el
    login (R43).

    `aprobacion` es la decisión de una persona sobre un parte que F-004
    rechazó (F-026). Es el segundo caso de lo mismo que `traza_grafico`, y por
    la misma razón: **viene del repositorio y nunca del cuerpo de la
    petición** (R24). La leen los tres pasos del circuito dentro de su puerta
    de aptitud; si viniera del cuerpo, quien llama podría afirmar que alguien
    aprobó lo que nadie aprobó, y con eso se cierra en el ERP de producción
    una reclamación que la validación había rechazado.

    Que sea `None` significa exactamente «no consta que nadie lo haya
    aprobado», y una aprobación **revocada** llega hasta aquí diciendo que lo
    está: el paso necesita distinguir las dos cosas tan poco como la pantalla
    necesita distinguirlas mucho (R31).
    """

    parte: ParteTroceado
    extraccion: ExtraccionParte | None = None
    lectura_firma: LecturaFirma | None = None
    validacion: ResultadoValidacion | None = None
    archivo: TrazaArchivo | None = None
    grafico: ResultadoGrafico | None = None
    traza_grafico: TrazaGrafico | None = None
    cierre: ResultadoCierre | None = None
    aprobacion: Aprobacion | None = None
    avisos: list[str] = field(default_factory=list)
