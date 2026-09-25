# services/postventa-api/application/pipelines/destino_archivo.py
"""El resolutor del destino en la biblioteca de Posventa (F-013).

Decide **en qué carpeta va el parte** con la estructura de Posventa
—`<base>/<obra>/<INCIDENCIAS>/<unidad>/<FIRMADOS>`— y qué carpetas **habría**
que crear para llegar a ella. No crea ninguna: el resolutor es **puro respecto a
escrituras** y devuelve la lista; las crea el paso de archivo, un nivel por
llamada y **después** de la traza previa (`specs/F-013-archivo-posventa/design.md`
§5). Así ningún 409 deja una carpeta a medias (R38), y un parte que no llega a
subirse no deja nada creado.

## Qué lee, y en qué orden (el orden es el requisito)

1. **La reclamación en Sigrid** (R6, R7): con el nº de incidencia en la forma
   del ERP (`a_codigo_de_sigrid`, la misma conversión que usa el cierre). Cero
   filas, varias, o una sin unidad de posventa → 409, sin listar nada.
2. **La misma obra** (R8): la que dice Sigrid y la del parte, normalizadas, o
   409. Es la defensa contra el PDF con DNI en la carpeta de otra obra.
3. **Las unidades de las obras con ese número** (R44): una sola obra, y la
   respuesta sin cortar, o 409. Con el casado por número, dos obras de Sigrid
   con el mismo número irían a la misma carpeta de Posventa.
4. **Los cuatro niveles**, en orden, listando cada uno una vez: una que casa se
   usa; varias, 409 ambigua; ninguna pero alguna parecida, 409 parecida;
   ninguna y ninguna, se **anota** la creación —con el nombre compuesto,
   comprobado (R38) y que casaría consigo mismo (R46)— y los niveles de debajo
   se anotan **sin listar**: el padre es nuevo y no puede tener nada.
5. **La unidad, de una sola unidad de Sigrid** (R50), en cuanto está elegida o
   anotada y antes de mirar dentro de ella.

Lo que **no** hace, a propósito: recibir el contexto del parte. Los códigos le
llegan como dos cadenas —los **guardados**, que el paso ya calcula—, así que no
puede leer la extracción del papel ni nada que no le llegue (`design.md` §2.3,
§5 enmendado). Tampoco traduce los fallos de Sigrid ni los de la biblioteca:
suben tal cual, y el borde responde 503 o 502 (R41). Ni escribe logs: los
nombres de la ficha de la unidad no salen de aquí (R23), y lo que haya que
contar lo cuenta el paso.

## Cuando la biblioteca no tiene lo que se acaba de ver

`listar_carpetas` devuelve `None` si la carpeta no existe. Aquí solo se lista
la base y carpetas que el listado anterior acaba de dar, así que un `None` es
una base mal configurada o una carpeta que alguien borró o renombró entre dos
llamadas. No es un nivel que falte —la base no se crea nunca, y crear en una
carpeta que acaba de desaparecer sería crear a ciegas—: es `ArchivoFallido`, y
no se sube ni se crea nada.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from domain.models.cierre import a_codigo_de_sigrid
from domain.models.destino_posventa import (
    MotivoDestino,
    UbicacionReclamacion,
    UnidadDeObra,
    carpeta_con_nombre,
    carpetas_de_obra,
    carpetas_de_unidad,
    nombre_de_carpeta_admisible,
    nombre_de_obra_nueva,
    nombre_derivado_de_unidad,
    obras_del_mismo_numero,
    parecidas_de_obra,
    parecidas_de_tramo,
    parecidas_de_unidad,
    unidades_que_casan,
    unir_ruta,
)
from domain.models.errores import ArchivoFallido, DestinoNoResuelto
from domain.models.nombrado import DestinoArchivo, normalizar_codigo
from domain.ports.biblioteca import ExploradorBibliotecaPort
from domain.ports.ubicacion import UbicacionPort

__all__ = [
    "TECHO_DE_FILAS_DE_SIGRID",
    "DestinoResuelto",
    "resolver_destino_posventa",
]

#: R44 · el máximo de filas que sirve `sigrid-api` por petición
#: (`azure-apps/sigrid_api.md`). Una respuesta que llega a él puede venir
#: cortada, y con ella no se puede afirmar ni que la obra sea una (R44) ni que
#: la carpeta de unidad sea de una sola unidad (R50).
TECHO_DE_FILAS_DE_SIGRID = 1000


@dataclass(frozen=True)
class DestinoResuelto:
    """Dónde va el parte, y qué carpetas hay que crear antes para llegar.

    `carpetas_por_crear` son `(padre, nombre)` **en orden**: cada padre existe
    ya o es la carpeta anotada justo antes. El paso las crea una a una con
    `crear_subcarpeta` (R15) y solo tras una resolución completa.
    """

    destino: DestinoArchivo
    carpetas_por_crear: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class _Nivel:
    """Un nivel de la estructura: cómo casa, cómo se parece y cómo se llama si falta."""

    #: Cómo se nombra el nivel en el texto del 409.
    legible: str
    ambigua: MotivoDestino
    parecida: MotivoDestino
    sin_carpeta: MotivoDestino
    casan: Callable[[tuple[str, ...]], tuple[str, ...]]
    parecidas: Callable[[tuple[str, ...]], tuple[str, ...]]
    #: El nombre con el que se crearía, o `None` si no se puede derivar (R37).
    nombre_nuevo: Callable[[], str | None]


@dataclass
class _Camino:
    """El recorrido nivel a nivel: dónde se está y qué se ha anotado."""

    explorador: ExploradorBibliotecaPort
    crear_carpetas: bool
    ruta: str
    #: `True` en cuanto se anota un nivel: debajo de él ya no se lista.
    nuevo: bool = False
    por_crear: list[tuple[str, str]] = field(default_factory=list)

    def bajar(self, nivel: _Nivel) -> str:
        """Elige o anota la carpeta del nivel y baja a ella. Devuelve su nombre."""
        if self.nuevo:
            return self._anotar(nivel)
        hijas = self._listar()
        casan = nivel.casan(hijas)
        if len(casan) > 1:
            raise DestinoNoResuelto(
                nivel.ambigua,
                f"hay {len(casan)} carpetas de {nivel.legible} que casan en "
                f"{_donde(self.ruta)}: una persona tiene que dejar solo una "
                "(renombrando las demás) y volver a archivar",
                casan,
            )
        if casan:
            (elegida,) = casan
            self.ruta = unir_ruta(self.ruta, elegida)
            return elegida
        parecidas = nivel.parecidas(hijas)
        if parecidas:
            raise DestinoNoResuelto(
                nivel.parecida,
                f"no hay ninguna carpeta de {nivel.legible} en {_donde(self.ruta)}, "
                "pero sí alguna parecida, y no se crea otra al lado para no "
                "duplicar la de Posventa: una persona tiene que renombrarla o "
                "crear la buena y volver a archivar",
                parecidas,
            )
        if not self.crear_carpetas:
            raise DestinoNoResuelto(
                nivel.sin_carpeta,
                f"no existe la carpeta de {nivel.legible} en {_donde(self.ruta)} y "
                "crear carpetas está apagado (SHAREPOINT_CREAR_CARPETAS): una "
                "persona tiene que crearla y volver a archivar",
            )
        return self._anotar(nivel)

    def _listar(self) -> tuple[str, ...]:
        hijas = self.explorador.listar_carpetas(carpeta=self.ruta)
        if hijas is None:
            raise ArchivoFallido(
                f"la carpeta {_donde(self.ruta)} no existe en la biblioteca: o "
                "la base configurada no es la de Posventa, o alguien la ha "
                "borrado o renombrado mientras se resolvía. No se ha creado ni "
                "subido nada"
            )
        return hijas

    def _anotar(self, nivel: _Nivel) -> str:
        """Compone, comprueba y anota la creación del nivel (R34, R37, R38, R46)."""
        nombre = nivel.nombre_nuevo()
        if nombre is None:
            raise DestinoNoResuelto(
                MotivoDestino.UNIDAD_SIN_NOMBRE_DERIVABLE,
                f"no existe la carpeta de {nivel.legible} en {_donde(self.ruta)} "
                "y el código de la unidad en Sigrid no tiene la forma de la que "
                "se deriva «VILLA NN»: no se inventa un nombre; una persona "
                "tiene que crear la carpeta y volver a archivar",
            )
        if not nombre_de_carpeta_admisible(nombre):
            raise DestinoNoResuelto(
                MotivoDestino.NOMBRE_CARPETA_IMPOSIBLE,
                f"la carpeta de {nivel.legible} que habría que crear, «{nombre}», "
                "no vale para SharePoint (un carácter no admitido, blancos en "
                "los extremos o punto final) y no se corrige por nuestra "
                "cuenta: una persona tiene que crear la carpeta y volver a "
                "archivar",
                (nombre,),
            )
        if nivel.casan((nombre,)) != (nombre,):
            raise DestinoNoResuelto(
                MotivoDestino.NOMBRE_NO_CASARIA,
                f"la carpeta de {nivel.legible} que habría que crear, «{nombre}», "
                "no casaría con la regla con la que se busca, y el siguiente "
                "archivado no la encontraría: no se crea; una persona tiene "
                "que crear la carpeta buena y volver a archivar",
                (nombre,),
            )
        self.por_crear.append((self.ruta, nombre))
        self.ruta = unir_ruta(self.ruta, nombre)
        self.nuevo = True
        return nombre


def resolver_destino_posventa(
    *,
    codigo_obra: str,
    numero_incidencia: str,
    nombre_fichero: str,
    explorador: ExploradorBibliotecaPort,
    ubicaciones: UbicacionPort,
    base: str,
    incidencias: str,
    firmados: str,
    firmados_alternativa: str,
    crear_carpetas: bool,
) -> DestinoResuelto:
    """La carpeta del parte en la biblioteca de Posventa, y lo que falta crear.

    `codigo_obra` y `numero_incidencia` son los **guardados** del parte
    (F-031); `nombre_fichero`, el que ya compuso `nombrado.py` (R5). El resto
    lo fija el borde desde la configuración (`functools.partial`).

    Levanta `DestinoNoResuelto` con su motivo (R18) cuando no se puede decidir
    sin una persona; `ArchivoFallido` si la biblioteca no responde o no tiene
    lo que acaba de enseñar; y, **sin traducirlos**, los fallos de lectura de
    Sigrid (R41). En ningún caso ha escrito nada.
    """
    ubicacion = _ubicar(ubicaciones, numero_incidencia)
    _exigir_la_misma_obra(ubicacion, codigo_obra, numero_incidencia)
    unidades = _unidades_de_la_obra(ubicaciones, codigo_obra)

    camino = _Camino(explorador, crear_carpetas, ruta=unir_ruta(base))
    obra = camino.bajar(
        _Nivel(
            legible="obra",
            ambigua=MotivoDestino.OBRA_AMBIGUA,
            parecida=MotivoDestino.OBRA_PARECIDA,
            sin_carpeta=MotivoDestino.SIN_CARPETA_OBRA,
            casan=lambda hijas: carpetas_de_obra(hijas, codigo_obra=codigo_obra),
            parecidas=lambda hijas: parecidas_de_obra(hijas, codigo_obra=codigo_obra),
            nombre_nuevo=lambda: nombre_de_obra_nueva(codigo_obra, ubicacion.obra_nombre),
        )
    )
    tramo_incidencias = camino.bajar(
        _Nivel(
            legible=f"«{incidencias}»",
            ambigua=MotivoDestino.INCIDENCIAS_AMBIGUA,
            parecida=MotivoDestino.INCIDENCIAS_PARECIDA,
            sin_carpeta=MotivoDestino.SIN_CARPETA_INCIDENCIAS,
            casan=lambda hijas: carpeta_con_nombre(hijas, buscado=incidencias),
            parecidas=lambda hijas: parecidas_de_tramo(hijas, buscado=incidencias),
            nombre_nuevo=lambda: incidencias,
        )
    )
    unidad = camino.bajar(
        _Nivel(
            legible="unidad",
            ambigua=MotivoDestino.UNIDAD_AMBIGUA,
            parecida=MotivoDestino.UNIDAD_PARECIDA,
            sin_carpeta=MotivoDestino.SIN_CARPETA_UNIDAD,
            casan=lambda hijas: carpetas_de_unidad(hijas, ubicacion=ubicacion),
            parecidas=lambda hijas: parecidas_de_unidad(hijas, ubicacion=ubicacion),
            nombre_nuevo=lambda: nombre_derivado_de_unidad(
                ubicacion.unidad_codigo, codigo_obra=codigo_obra
            ),
        )
    )
    _exigir_una_sola_unidad(unidades, unidad)
    hoja = camino.bajar(
        _Nivel(
            legible=f"«{firmados}»",
            ambigua=MotivoDestino.FIRMADOS_AMBIGUA,
            parecida=MotivoDestino.FIRMADOS_PARECIDA,
            sin_carpeta=MotivoDestino.SIN_CARPETA_FIRMADOS,
            casan=lambda hijas: carpeta_con_nombre(
                hijas, buscado=firmados, alternativa=firmados_alternativa
            ),
            parecidas=lambda hijas: parecidas_de_tramo(
                hijas, buscado=firmados, alternativa=firmados_alternativa
            ),
            # R49: se crea siempre la principal, nunca la alternativa.
            nombre_nuevo=lambda: firmados,
        )
    )

    return DestinoResuelto(
        destino=DestinoArchivo(
            carpeta=unir_ruta(base, obra, tramo_incidencias, unidad, hoja),
            nombre_fichero=nombre_fichero,
        ),
        carpetas_por_crear=tuple(camino.por_crear),
    )


# --------------------------------------------------------------------------
# Las tres puertas de Sigrid, antes de listar nada
# --------------------------------------------------------------------------


def _ubicar(ubicaciones: UbicacionPort, numero_incidencia: str) -> UbicacionReclamacion:
    """R6, R7 · la única fila de la reclamación, con su unidad y su obra."""
    codigo = a_codigo_de_sigrid(numero_incidencia)
    filas = ubicaciones.leer_ubicacion(codigo_reclamacion=codigo)
    if not filas:
        raise DestinoNoResuelto(
            MotivoDestino.RECLAMACION_NO_LOCALIZADA,
            f"Sigrid no tiene ninguna reclamación con el código «{codigo}»: una "
            "persona tiene que revisar el nº de incidencia del parte, guardarlo "
            "corregido y volver a archivar",
        )
    if len(filas) > 1:
        raise DestinoNoResuelto(
            MotivoDestino.RECLAMACION_AMBIGUA,
            f"Sigrid tiene {len(filas)} reclamaciones con el código «{codigo}» y "
            "no se puede saber de qué vivienda es el parte: lo tiene que "
            "revisar una persona en el ERP",
        )
    (ubicacion,) = filas
    sin_unidad = not (
        _con_texto(ubicacion.unidad_codigo) or _con_texto(ubicacion.unidad_nombre)
    )
    if sin_unidad or not _con_texto(ubicacion.obra_codigo):
        raise DestinoNoResuelto(
            MotivoDestino.RECLAMACION_SIN_UNIDAD,
            f"la reclamación «{codigo}» no cuelga en Sigrid de ninguna unidad de "
            "posventa, o su unidad de ninguna obra, y sin eso no se sabe en qué "
            "carpeta va: una persona tiene que completarlo en el ERP y volver "
            "a archivar",
        )
    return ubicacion


def _exigir_la_misma_obra(
    ubicacion: UbicacionReclamacion, codigo_obra: str, numero_incidencia: str
) -> None:
    """R8 · la obra de Sigrid y la del parte, normalizadas, tienen que ser la misma."""
    de_sigrid = normalizar_codigo(ubicacion.obra_codigo)
    del_parte = normalizar_codigo(codigo_obra)
    if de_sigrid != del_parte:
        raise DestinoNoResuelto(
            MotivoDestino.OBRA_NO_COINCIDE,
            f"el parte es de la obra «{del_parte}» y Sigrid sitúa la reclamación "
            f"«{a_codigo_de_sigrid(numero_incidencia)}» en la obra «{de_sigrid}»: "
            "no se archiva en ninguna de las dos; una persona tiene que revisar "
            "el código de obra o el nº de incidencia del parte",
        )


def _unidades_de_la_obra(
    ubicaciones: UbicacionPort, codigo_obra: str
) -> tuple[UnidadDeObra, ...]:
    """R44 · las unidades de **la** obra con ese número: una obra, lista entera."""
    codigo = normalizar_codigo(codigo_obra)
    filas = ubicaciones.leer_unidades_del_numero(codigo_obra=codigo)
    if len(filas) >= TECHO_DE_FILAS_DE_SIGRID:
        raise DestinoNoResuelto(
            MotivoDestino.UNIDADES_SIN_VERIFICAR,
            f"Sigrid ha devuelto {len(filas)} unidades de posventa para las obras "
            f"con el número de «{codigo}», el máximo que sirve la pasarela, y la "
            "lista puede venir cortada: no se puede comprobar que la obra y la "
            "unidad sean únicas; lo tiene que revisar una persona",
        )
    obras = obras_del_mismo_numero(filas, codigo_obra=codigo)
    if len(obras) != 1:
        raise DestinoNoResuelto(
            MotivoDestino.OBRA_NUMERO_NO_UNICO,
            f"en Sigrid hay {len(obras)} obras con unidades de posventa con el "
            f"número de «{codigo}», y hace falta exactamente una: con el casado "
            "por número, todas irían a la misma carpeta de Posventa. Lo tiene "
            "que resolver una persona",
        )
    (obra,) = obras
    return tuple(fila for fila in filas if fila.obra_ref == obra)


def _exigir_una_sola_unidad(unidades: tuple[UnidadDeObra, ...], carpeta: str) -> None:
    """R50 · la carpeta de unidad casa con una y solo una unidad de la obra."""
    casan = unidades_que_casan(unidades, carpeta=carpeta)
    if len(casan) != 1:
        raise DestinoNoResuelto(
            MotivoDestino.UNIDAD_CARPETA_COMPARTIDA,
            f"la carpeta de unidad «{carpeta}» casa con {len(casan)} unidades de "
            "posventa de la obra en Sigrid, y hace falta exactamente una: el "
            "parte podría acabar en la carpeta de otra vivienda. Lo tiene que "
            "resolver una persona",
            (carpeta,),
        )


def _con_texto(valor: str | None) -> bool:
    return bool((valor or "").strip())


def _donde(ruta: str) -> str:
    return f"«{ruta}»" if ruta else "la raíz de la biblioteca"
