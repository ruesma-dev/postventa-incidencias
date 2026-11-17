# services/postventa-api/domain/models/importacion.py
"""La importación de la plantilla de incidencias (F-036): dominio puro.

`specs/F-036-importar-excel/design.md` §4.2–§4.5. Tres cosas, en el orden en
que las usa la importación:

1. **Reconocer** el libro leído (`reconocer_plantilla`, R17–R20): si no es la
   plantilla, se rechaza **entero** y no se mira ninguna fila (R21).
2. **Validar** cada fila (`validar_filas`, R23–R34, R73–R77, R93, R94, R99):
   las buenas entran en la bandeja y las malas vuelven en el Excel de errores
   (R33), con su `FilaLeida` entera para poder reescribirlas tal como llegaron.
3. **Agrupar** las válidas por su clave de duplicado (`clave_de_duplicado`,
   `agrupar_por_clave`, R35–R38): la primera de cada grupo manda.

**Todo valor tasado se compara exacto**, carácter a carácter y sin recortar
(decisión 7 de `requirements.md`): Excel compara las listas sin distinguir
mayúsculas al teclear y pegar se salta la validación, así que el único filtro
fiable es este. Solo los textos libres se tocan.

**Desviación anotada respecto de `design.md` §4.3** (T5, 2026-09-29):
`validar_filas` recibe las **opciones** de `Oficio` y `Proveedor` ya
calculadas (`opciones_oficio`, `opciones_proveedor`) en vez de los grupos
vigentes. Es lo que pide `tasks.md` (T5 se escribe contra opciones construidas
a mano; `opciones_de_oficio` y `opciones_de_proveedor` son de T7), y deja que
la importación calcule las opciones **una vez** y use las mismas en la
validación y en el Excel de errores (§7.3, paso 6).

F-072 (`specs/F-072-tipo-reclamacion-sigrid/design.md` §3.2): la celda
`Listado` se casa con las etiquetas de los tipos de reclamación de Sigrid que
trae `listas.listados` (R12) y la fila guarda su **código** en
`tipo_reclamacion`; en blanco, `0002` sin mirarlo en la lista (R14). El
`listado` de F-036 ya no se rellena: toda fila nueva lo lleva a `None` (R15).

Sin `openpyxl`, sin red, sin base de datos y sin reloj.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from domain.models.casado_con_lista import (
    Coincidencia,
    casar_con_lista,
    ubicacion_de_sigrid,
)
from domain.models.errores import CodigoDeObraInvalido, FicheroNoEsPlantilla
from domain.models.plantilla_incidencias import (
    CABECERA,
    IDENTIFICADOR_PLANTILLA,
    MAX_DESCRIPCION,
    MAX_DETALLE,
    MAX_FILAS,
    VERSION_ANTERIOR,
    TIPO_RECLAMACION_POR_DEFECTO,
    VERSIONES_SOPORTADAS,
    CatalogoObra,
    Listado,
    ListasCerradas,
    Opcion,
    OpcionOficio,
    OpcionOficioSigrid,
    OpcionProveedor,
    ParSigrid,
    UbicacionesPorUnidad,
    Urgencia,
    etiquetas_de_unidades,
    normalizar_codigo_obra,
    normalizar_para_clave,
    plegar,
    ubicaciones_de_la_plantilla,
)

# Nombres de columna, por legibilidad; salen de la cabecera del contrato.
(
    UNIDAD,
    UBICACION,
    DESCRIPCION,
    DETALLE,
    OFICIO,
    PROVEEDOR,
    URGENCIA,
    LISTADO,
    ERRORES,
) = CABECERA

#: Columnas de texto libre; las demás son tasadas.
_TEXTO_LIBRE = frozenset({DESCRIPCION, DETALLE})

#: Separador de los campos de la clave de duplicado (R35).
_SEPARADOR_CLAVE = "\x1f"

#: Palabras que, con `Urgencia` vacía, merecen un aviso (R34), ya plegadas.
PALABRAS_DE_URGENCIA: tuple[str, ...] = (
    "peligro",
    "seguridad",
    "urgente",
    "urgencia",
    "estructural",
)

#: Aviso de mayúsculas: al menos tantas letras, y más de este % en mayúscula.
MIN_LETRAS_MAYUSCULAS = 20
PORCENTAJE_MAYUSCULAS = 60

_DESCARGA = "Descarga la plantilla de la obra desde el portal."

# Textos de los problemas de fila (R24), en lenguaje llano.
FORMULA = "la celda lleva una fórmula: escribe el texto"
FECHA_EN_TEXTO = "la celda lleva una fecha o un valor verdadero/falso: escribe el texto"
FECHA_EN_TASADA = "la celda lleva una fecha o un valor verdadero/falso: elige un valor del desplegable"
NUMERO_EN_TASADA = "la celda lleva un número: elige un valor del desplegable"
FALTA_UNIDAD = "falta la unidad; en esta plantilla no se hereda de la fila de arriba"
FALTA_DESCRIPCION = "falta la descripción corta"
PROVEEDOR_DE_OTRO_OFICIO = (
    "ese proveedor no está dado de alta en la obra para ese oficio"
)
AVISO_URGENCIA = (
    "menciona peligro, seguridad o urgencia y la columna «Urgencia» está vacía: "
    "márcala si corresponde"
)
AVISO_MAYUSCULAS = (
    "la descripción corta va casi toda en mayúsculas: escríbela normal y marca la "
    "urgencia en su columna"
)

# Textos de F-071 (`design.md` §5.6): sin el valor tecleado ni la unidad.
UBICACION_FUERA_DE_LA_UNIDAD = (
    "esa ubicación no es de la unidad de esta fila: elígela del desplegable, "
    "que enseña solo las de su unidad (si has cambiado la unidad, vuelve a "
    "elegir la ubicación); si el sitio no está, deja la ubicación en blanco y "
    "explícalo en «Detalle»"
)
UNIDAD_SIN_UBICACIONES = (
    "esta unidad no tiene ubicaciones en Sigrid: deja la ubicación en blanco y "
    "explica el sitio en «Detalle»"
)
UBICACION_FUERA_DE_LA_OBRA = (
    "esa ubicación no es de ninguna unidad de la obra: elige primero la unidad "
    "y luego la ubicación del desplegable"
)
VERSION_ANTERIOR_MOTIVO = (
    "Esta plantilla es de una versión anterior: sus listas ya no son las de "
    "Sigrid. Descarga una nueva desde el portal y copia en ella tus filas."
)
_YA_NO_ESTA_EN_SIGRID = (
    "ese valor no está en Sigrid para esta obra (puede que haya cambiado desde "
    "que descargaste la plantilla): elígelo del desplegable de este fichero, que "
    "trae las listas de hoy"
)


def aviso_ubicacion_ajustada(texto: str) -> str:
    """El aviso de una ubicación casada con la de Sigrid (R28)."""
    return f"la ubicación se ha ajustado al texto de Sigrid: «{texto}»"


def aviso_valor_tomado(columna: str, opcion: str) -> str:
    """El aviso de un valor tasado casado con una opción no exacta (R36)."""
    return f"{columna}: se ha tomado «{opcion}»"


def ya_no_esta_en_sigrid(columna: str) -> str:
    """El problema de un valor de `columna` que no está en Sigrid hoy (R37).

    El texto es el mismo para `Unidad`, `Oficio` y `Proveedor`: el error ya va
    en su columna.
    """
    return _YA_NO_ESTA_EN_SIGRID


def _fuera_de_lista(lista: str) -> str:
    return (
        f"ese valor no está en la lista de {lista}: elígelo del desplegable "
        "(cuidado con mayúsculas, tildes y espacios)"
    )


# --------------------------------------------------------------------------
# §4.2 · el libro leído y el reconocimiento
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CeldaLeida:
    valor: str | int | float | None
    es_formula: bool
    es_fecha_o_booleano: bool
    texto_original: str | None  # lo que se reescribe en el Excel de errores (R63)


@dataclass(frozen=True)
class FilaLeida:
    numero: int  # número de fila de Excel (cabecera = 1)
    celdas: Mapping[str, CeldaLeida]  # por nombre de columna de CABECERA


@dataclass(frozen=True)
class LibroLeido:
    identificador: str | None
    version: int | None
    obra_codigo: str | None
    cabecera: tuple[str, ...]
    filas: tuple[FilaLeida, ...]  # solo filas con algún dato fuera de Errores (R23)
    parece_formato_antiguo: bool  # lo calcula el lector (§5.2)
    #: Algún dato en las columnas de datos de la fila MAX_FILAS + 2 (1002) o
    #: más abajo, visto sin recorrer la hoja (R115). Lo calcula el lector.
    datos_fuera_del_tope: bool = False


def _problemas_de_cabecera(cabecera: tuple[str, ...]) -> list[str]:
    """Qué columna falta, sobra, está repetida o movida (R19)."""
    leida = [(c or "").strip() for c in cabecera]
    while leida and not leida[-1]:
        leida.pop()
    problemas: list[str] = []
    for columna in CABECERA:
        veces = leida.count(columna)
        if veces == 0:
            problemas.append(f"falta la columna «{columna}»")
        elif veces > 1:
            problemas.append(f"la columna «{columna}» está repetida")
    for posicion, columna in enumerate(leida, start=1):
        if not columna:
            problemas.append(f"sobra una columna sin nombre (la {posicion}.ª)")
        elif columna not in CABECERA:
            problemas.append(f"sobra la columna «{columna}»")
    if problemas:
        return problemas
    # Aquí `leida` trae cada columna de CABECERA una sola vez y ninguna más.
    for posicion, esperada in enumerate(CABECERA, start=1):
        vista = leida[posicion - 1]
        if esperada != vista:
            return [
                f"la columna «{vista}» está movida: en la posición {posicion} va «{esperada}»"
            ]
    return []


def reconocer_plantilla(libro: LibroLeido) -> str:
    """Devuelve el código de obra normalizado, o levanta `FicheroNoEsPlantilla`.

    Por el orden de los requisitos (R17–R20): identificador (con el matiz del
    formato antiguo), versión, cabecera, número de filas —o datos por debajo
    del tope, R115— y código de obra de los metadatos. Ninguna fila se valida
    aquí.
    """
    if libro.identificador != IDENTIFICADOR_PLANTILLA:
        if libro.parece_formato_antiguo:
            raise FicheroNoEsPlantilla(
                "formato_antiguo",
                "Este fichero tiene el formato antiguo de incidencias, que ya no se "
                f"admite. {_DESCARGA}",
            )
        raise FicheroNoEsPlantilla(
            "no_es_la_plantilla",
            f"Este fichero no es la plantilla de incidencias. {_DESCARGA}",
        )
    if libro.version == VERSION_ANTERIOR:
        raise FicheroNoEsPlantilla("version_anterior", VERSION_ANTERIOR_MOTIVO)
    if libro.version not in VERSIONES_SOPORTADAS:
        raise FicheroNoEsPlantilla(
            "version_no_soportada",
            f"Esta versión de la plantilla ya no se admite. {_DESCARGA}",
        )
    problemas = _problemas_de_cabecera(libro.cabecera)
    if problemas:
        raise FicheroNoEsPlantilla(
            "cabecera_distinta",
            "La cabecera de la hoja «Incidencias» no es la de la plantilla: "
            + "; ".join(problemas)
            + ".",
        )
    if len(libro.filas) > MAX_FILAS:
        raise FicheroNoEsPlantilla(
            "demasiadas_filas",
            f"El fichero trae {len(libro.filas)} filas con datos y el máximo es "
            f"{MAX_FILAS}. Pártelo en varios ficheros.",
        )
    if libro.datos_fuera_del_tope:
        # R115 (sexta enmienda de R20): cualquier dato por debajo de la última
        # fila de la plantilla, aunque las filas con datos no lleguen a 1000.
        raise FicheroNoEsPlantilla(
            "demasiadas_filas",
            f"El fichero trae datos por debajo de la fila {MAX_FILAS + 1} y el "
            f"máximo es {MAX_FILAS}. Pártelo en varios ficheros.",
        )
    try:
        return normalizar_codigo_obra(libro.obra_codigo)
    except CodigoDeObraInvalido:
        raise FicheroNoEsPlantilla(
            "obra_invalida",
            f"El código de obra de la plantilla no es válido. {_DESCARGA}",
        ) from None


# --------------------------------------------------------------------------
# §4.3 · validación de filas
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ErrorDeFila:
    fila: int
    columna: str
    problema: str


@dataclass(frozen=True)
class Elegido:
    """Un oficio o un proveedor ya resuelto: `codigo` None ⇔ `ambiguo` (R93–R95)."""

    etiqueta: str
    codigo: str | None
    ambiguo: bool

    def __post_init__(self) -> None:
        if self.ambiguo == (self.codigo is not None):
            raise ValueError("un elegido lleva código si y solo si no es ambiguo")


@dataclass(frozen=True)
class IncidenciaValida:
    fila: int
    unidad: Opcion
    ubicacion: str | None
    descripcion: str
    detalle: str | None
    oficio: Elegido | None
    proveedor: Elegido | None  # proveedor ⇒ oficio (R99)
    urgencia: Urgencia | None
    listado: Listado | None
    avisos: tuple[str, ...]
    tipo_reclamacion: str | None = None  # F-072: el código de `dbo.auxtrcp` (R12, R14)

    def __post_init__(self) -> None:
        if self.proveedor is not None and self.oficio is None:
            raise ValueError("no hay proveedor sin oficio (R99)")


@dataclass(frozen=True)
class FilaConError:
    fila: FilaLeida
    errores: tuple[ErrorDeFila, ...]


def _elegido(etiqueta: str, codigos: set[str]) -> Elegido:
    if not codigos:
        raise ValueError("opción sin códigos en la obra")
    if len(codigos) == 1:
        return Elegido(etiqueta=etiqueta, codigo=next(iter(codigos)), ambiguo=False)
    return Elegido(etiqueta=etiqueta, codigo=None, ambiguo=True)


def resolver_oficio_y_proveedor(
    oficio: OpcionOficio | None, proveedor: OpcionProveedor | None
) -> tuple[Elegido | None, Elegido | None]:
    """Resuelve juntos el oficio y el proveedor de una fila (R93, R94, D-17).

    - Sin proveedor (R93): los códigos del grupo de oficio en la obra; uno →
      ese código, varios → ambiguo.
    - Con proveedor (R94): las filas de `obrofc` del par. Si todas comparten
      código de oficio, el oficio queda resuelto aunque R93 lo dejara ambiguo;
      igual con el proveedor. Así lo guardado es **una fila real de `obrofc`**.
    - Solo proveedor (D-17): el oficio es el del par.

    Nunca elige sola entre varios códigos (D-19). Un par de otro grupo de
    oficio no llega aquí: `validar_filas` lo da antes como error de fila.
    """
    if proveedor is None:
        if oficio is None:
            return None, None
        return _elegido(oficio.etiqueta, set(oficio.codigos_en_obra)), None
    if oficio is not None and oficio != proveedor.oficio:
        raise ValueError("el par del proveedor es de otro grupo de oficio")
    oficio_del_par = proveedor.oficio
    filas = proveedor.filas_en_obra
    return (
        _elegido(oficio_del_par.etiqueta, {o for o, _ in filas}),
        _elegido(proveedor.grupo.etiqueta, {p for _, p in filas}),
    )


def _vacia(celda: CeldaLeida | None) -> bool:
    """Sin valor, o solo blancos. Una fórmula nunca está vacía."""
    if celda is None:
        return True
    if celda.es_formula:
        return False
    valor = celda.valor
    return valor is None or (isinstance(valor, str) and not valor.strip())


def _es_fecha_o_booleano(celda: CeldaLeida) -> bool:
    return celda.es_fecha_o_booleano or isinstance(celda.valor, bool)


class _Fila:
    """Acumula los errores de una fila mientras se leen sus columnas."""

    def __init__(self, fila: FilaLeida) -> None:
        self.fila = fila
        self.errores: list[ErrorDeFila] = []
        self.avisos: list[str] = []  # los del casado, en el orden de las columnas

    def error(self, columna: str, problema: str) -> None:
        self.errores.append(
            ErrorDeFila(fila=self.fila.numero, columna=columna, problema=problema)
        )

    def celda(self, columna: str) -> CeldaLeida | None:
        celda = self.fila.celdas.get(columna)
        return None if _vacia(celda) else celda

    def texto(self, columna: str) -> str | None:
        """Texto libre: una fórmula, fecha o booleano es error; un número, texto."""
        celda = self.celda(columna)
        if celda is None:
            return None
        if celda.es_formula:
            self.error(columna, FORMULA)
            return None
        if _es_fecha_o_booleano(celda):
            self.error(columna, FECHA_EN_TEXTO)
            return None
        valor = celda.valor
        if isinstance(valor, float) and valor.is_integer():
            return str(int(valor))
        return str(valor)

    def _texto_tasado(self, columna: str) -> str | None:
        """El texto de una columna tasada, o None: vacía, o con su error (R38).

        Una fórmula, una fecha o un booleano, o un número, son error y no se
        comparan con ninguna lista.
        """
        celda = self.celda(columna)
        if celda is None:
            return None
        if celda.es_formula:
            self.error(columna, FORMULA)
        elif _es_fecha_o_booleano(celda):
            self.error(columna, FECHA_EN_TASADA)
        elif not isinstance(celda.valor, str):
            self.error(columna, NUMERO_EN_TASADA)
        else:
            return celda.valor
        return None

    def tasado(self, columna: str, etiquetas: Iterable[str], lista: str) -> str | None:
        """La opción de una columna tasada con el casado de F-060 (F-071, R36).

        La exacta, o la **única** con la misma clave, con el aviso
        `aviso_valor_tomado`; con dos o ninguna, el error `lista`.
        """
        valor = self._texto_tasado(columna)
        if valor is None:
            return None
        opcion = casar_con_lista(valor, etiquetas)
        if opcion is None:
            self.error(columna, lista)
            return None
        if opcion != valor:
            self.avisos.append(aviso_valor_tomado(columna, opcion))
        return opcion

    def ubicacion(
        self, lista: tuple[str, ...] | None, union: tuple[str, ...]
    ) -> str | None:
        """La ubicación de la fila contra la lista de su unidad (F-071 §5.3).

        `lista` es la de la unidad de la fila, o None si la unidad falta o no
        vale: entonces se compara con la `union` de la obra y no se guarda
        nada (R31). Con lista: la exacta tal cual (R27); la casada, el texto
        de Sigrid con aviso (R28); si no, error (R29, R30).
        """
        valor = self._texto_tasado(UBICACION)
        if valor is None:
            return None
        if lista is None:
            if ubicacion_de_sigrid(valor, union).coincidencia not in _CASAN:
                self.error(UBICACION, UBICACION_FUERA_DE_LA_OBRA)
            return None
        if not lista:
            self.error(UBICACION, UNIDAD_SIN_UBICACIONES)
            return None
        resultado = ubicacion_de_sigrid(valor, lista)
        if resultado.coincidencia is Coincidencia.EXACTA:
            return valor
        if resultado.coincidencia is Coincidencia.NORMALIZABLE:
            assert resultado.texto is not None
            self.avisos.append(aviso_ubicacion_ajustada(resultado.texto))
            return resultado.texto
        self.error(UBICACION, UBICACION_FUERA_DE_LA_UNIDAD)
        return None


#: Lo que casa con una lista: tal cual o por la clave de F-060.
_CASAN = frozenset({Coincidencia.EXACTA, Coincidencia.NORMALIZABLE})


def _avisos(
    descripcion: str, detalle: str | None, urgencia: Urgencia | None
) -> list[str]:
    avisos: list[str] = []
    plegado = plegar(f"{descripcion} {detalle or ''}")
    if urgencia is None and any(p in plegado for p in PALABRAS_DE_URGENCIA):
        avisos.append(AVISO_URGENCIA)
    letras = [c for c in descripcion if c.isalpha()]
    mayusculas = sum(1 for c in letras if c.isupper())
    if (
        len(letras) >= MIN_LETRAS_MAYUSCULAS
        and mayusculas * 100 > len(letras) * PORCENTAJE_MAYUSCULAS
    ):
        avisos.append(AVISO_MAYUSCULAS)
    return avisos


def _elegido_de_oficio(opcion: OpcionOficioSigrid) -> Elegido:
    """El oficio resuelto: su código y, como nombre, el de Sigrid (R32)."""
    return Elegido(
        etiqueta=opcion.nombre or opcion.codigo, codigo=opcion.codigo, ambiguo=False
    )


def _elegido_de_proveedor(par: ParSigrid) -> Elegido:
    """El proveedor resuelto: su código y su nombre de Sigrid (R33)."""
    return Elegido(
        etiqueta=par.proveedor_nombre or par.proveedor_codigo,
        codigo=par.proveedor_codigo,
        ambiguo=False,
    )


def _validar_fila(
    fila: FilaLeida,
    *,
    unidades: Mapping[str, Opcion],
    oficios: Mapping[str, OpcionOficioSigrid],
    pares: Mapping[str, ParSigrid],
    listas: ListasCerradas,
    ubicaciones_por_unidad: UbicacionesPorUnidad,
    union: tuple[str, ...],
) -> IncidenciaValida | FilaConError:
    f = _Fila(fila)

    etiqueta_unidad = f.tasado(UNIDAD, unidades, ya_no_esta_en_sigrid(UNIDAD))
    if f.celda(UNIDAD) is None:
        f.error(UNIDAD, FALTA_UNIDAD)

    lista_de_la_unidad = (
        None
        if etiqueta_unidad is None
        else tuple(ubicaciones_por_unidad.get(unidades[etiqueta_unidad].codigo, ()))
    )
    ubicacion = f.ubicacion(lista_de_la_unidad, union)

    texto_descripcion = f.texto(DESCRIPCION)
    descripcion = " ".join((texto_descripcion or "").split())
    if f.celda(DESCRIPCION) is None:
        f.error(DESCRIPCION, FALTA_DESCRIPCION)
    elif texto_descripcion is not None and len(descripcion) > MAX_DESCRIPCION:
        f.error(
            DESCRIPCION,
            f"la descripción corta tiene {len(descripcion)} caracteres y el máximo es "
            f"{MAX_DESCRIPCION}: deja lo esencial y pasa el resto a «Detalle»",
        )

    detalle = (f.texto(DETALLE) or "").strip() or None
    if detalle is not None and len(detalle) > MAX_DETALLE:
        f.error(
            DETALLE,
            f"el detalle tiene {len(detalle)} caracteres y el máximo es {MAX_DETALLE}",
        )

    etiqueta_oficio = f.tasado(OFICIO, oficios, ya_no_esta_en_sigrid(OFICIO))
    etiqueta_par = f.tasado(PROVEEDOR, pares, ya_no_esta_en_sigrid(PROVEEDOR))
    oficio = None if etiqueta_oficio is None else oficios[etiqueta_oficio]
    par = None if etiqueta_par is None else pares[etiqueta_par]
    if oficio is not None and par is not None and par.oficio.codigo != oficio.codigo:
        f.error(PROVEEDOR, PROVEEDOR_DE_OTRO_OFICIO)

    urgencias = {o.etiqueta: o.codigo for o in listas.urgencias}
    etiqueta_urgencia = f.tasado(URGENCIA, urgencias, _fuera_de_lista("urgencias"))
    listados = {o.etiqueta: o.codigo for o in listas.listados}
    etiqueta_listado = f.tasado(LISTADO, listados, _fuera_de_lista("listados"))

    if f.errores:
        return FilaConError(fila=fila, errores=tuple(f.errores))

    # Sin errores, las obligatorias están y todo lo tasado casa.
    assert etiqueta_unidad is not None
    urgencia = (
        None if etiqueta_urgencia is None else Urgencia(urgencias[etiqueta_urgencia])
    )
    # F-072: el código del tipo casado (R12) o, en blanco, el de por defecto
    # sin mirarlo en la lista (R14); el `listado` de F-036 ya no se escribe (R15).
    tipo_reclamacion = (
        TIPO_RECLAMACION_POR_DEFECTO
        if etiqueta_listado is None
        else listados[etiqueta_listado]
    )
    # Con proveedor, el oficio es el del par (R33, D-17 de F-036): con un
    # `Oficio` distinto ya habría salido el error de R34.
    opcion_oficio = par.oficio if par is not None else oficio
    return IncidenciaValida(
        fila=fila.numero,
        unidad=unidades[etiqueta_unidad],
        ubicacion=ubicacion,
        descripcion=descripcion,
        detalle=detalle,
        oficio=None if opcion_oficio is None else _elegido_de_oficio(opcion_oficio),
        proveedor=None if par is None else _elegido_de_proveedor(par),
        urgencia=urgencia,
        listado=None,
        avisos=tuple(f.avisos + _avisos(descripcion, detalle, urgencia)),
        tipo_reclamacion=tipo_reclamacion,
    )


def validar_filas(
    filas: Iterable[FilaLeida],
    *,
    catalogo: CatalogoObra,
    oficios: tuple[OpcionOficioSigrid, ...],
    pares: tuple[ParSigrid, ...],
    listas: ListasCerradas,
    ubicaciones_por_unidad: UbicacionesPorUnidad,
) -> tuple[tuple[IncidenciaValida, ...], tuple[FilaConError, ...]]:
    """Separa las filas válidas de las que tienen algún error (F-036; F-071 §5.3, §5.4).

    Se recorren **todas** las filas y todas sus columnas: el error de una no
    esconde el de otra (R33 de F-036, R39). Las filas vacías —sin contar
    `Errores`— se ignoran. Las unidades, las opciones de oficio, los pares y
    las ubicaciones de cada unidad salen de lo **recién leído** de Sigrid
    (R24): quien llama calcula `oficios` y `pares` con ese mismo catálogo
    (`oficios_del_desplegable`, `pares_del_desplegable`). Ninguna fila sale
    con oficio o proveedor ambiguo (R35).
    """
    unidades = {o.etiqueta: o for o in etiquetas_de_unidades(catalogo.unidades)}
    por_etiqueta_oficio = {o.etiqueta: o for o in oficios}
    por_etiqueta_par = {p.etiqueta: p for p in pares}
    union = ubicaciones_de_la_plantilla(catalogo.unidades, ubicaciones_por_unidad).union()
    validas: list[IncidenciaValida] = []
    con_error: list[FilaConError] = []
    for fila in filas:
        if all(_vacia(fila.celdas.get(c)) for c in CABECERA if c != ERRORES):
            continue
        resultado = _validar_fila(
            fila,
            unidades=unidades,
            oficios=por_etiqueta_oficio,
            pares=por_etiqueta_par,
            listas=listas,
            ubicaciones_por_unidad=ubicaciones_por_unidad,
            union=union,
        )
        if isinstance(resultado, FilaConError):
            con_error.append(resultado)
        else:
            validas.append(resultado)
    return tuple(validas), tuple(con_error)


# --------------------------------------------------------------------------
# §4.5 · duplicados y bandeja
# --------------------------------------------------------------------------


def clave_de_duplicado(
    *, obra_codigo: str, unidad_codigo: str, ubicacion: str | None, descripcion: str
) -> str:
    """sha256 hex de "obra\\x1funidad\\x1fubicación_norm\\x1fdescripción_norm" (R35).

    No lleva oficio ni proveedor (R77): la misma incidencia con otro industrial
    sigue siendo la misma. La ubicación vacía cuenta como cadena vacía.
    """
    partes = (
        obra_codigo,
        unidad_codigo,
        normalizar_para_clave(ubicacion or ""),
        normalizar_para_clave(descripcion),
    )
    return hashlib.sha256(_SEPARADOR_CLAVE.join(partes).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class GrupoDeClave:
    clave: str
    filas: tuple[IncidenciaValida, ...]  # en orden de aparición; la primera manda


def agrupar_por_clave(
    validas: Iterable[IncidenciaValida], *, obra_codigo: str
) -> tuple[GrupoDeClave, ...]:
    """Las válidas agrupadas por clave, en orden de primera aparición (R37).

    La primera de cada grupo es la que entra; las demás se guardan como
    duplicadas de ella. Si la clave ya está en la bandeja, se salta el grupo
    **entero** (R38): saltando solo la primera, reimportar duplicaría.
    """
    grupos: dict[str, list[IncidenciaValida]] = {}
    for valida in validas:
        clave = clave_de_duplicado(
            obra_codigo=obra_codigo,
            unidad_codigo=valida.unidad.codigo,
            ubicacion=valida.ubicacion,
            descripcion=valida.descripcion,
        )
        grupos.setdefault(clave, []).append(valida)
    return tuple(GrupoDeClave(clave=c, filas=tuple(f)) for c, f in grupos.items())


class EstadoFilaImportada(StrEnum):
    NUEVA = "nueva"
    DUPLICADA_EN_FICHERO = "duplicada_en_fichero"
    YA_EN_BANDEJA = "ya_en_bandeja"
    CON_ERROR = "con_error"


class EstadoImportacion(StrEnum):
    COMPLETA = "completa"
    PARCIAL = "parcial"


def _comprobar_elegido(
    que: str, codigo: str | None, nombre: str | None, ambiguo: bool
) -> bool:
    """¿Hay `que` en la fila? Y levanta si la combinación es imposible (R99)."""
    if ambiguo and (codigo is not None or nombre is None):
        raise ValueError(f"{que} ambiguo: sin código y con su nombre (R99)")
    if not ambiguo and codigo is None and nombre is not None:
        raise ValueError(f"{que} con nombre y sin código ni ambigüedad (R99)")
    return ambiguo or codigo is not None


@dataclass(frozen=True)
class IncidenciaEnBandeja:
    """Una fila de `GET /api/bandeja` (§8)."""

    incidencia_id: UUID
    importacion_id: UUID | None
    fila_origen: int | None
    unidad_codigo: str
    unidad_nombre: str
    ubicacion: str | None
    descripcion: str
    detalle: str | None
    oficio_codigo: str | None
    oficio_nombre: str | None
    oficio_ambiguo: bool
    proveedor_codigo: str | None
    proveedor_nombre: str | None
    proveedor_ambiguo: bool
    urgencia: Urgencia | None
    listado: Listado | None
    duplicada_de: UUID | None
    creada_at_utc: datetime
    tipo_reclamacion: str | None = None  # F-072: nulo = anterior a F-072 (R19)

    def __post_init__(self) -> None:
        hay_oficio = _comprobar_elegido(
            "oficio", self.oficio_codigo, self.oficio_nombre, self.oficio_ambiguo
        )
        hay_proveedor = _comprobar_elegido(
            "proveedor",
            self.proveedor_codigo,
            self.proveedor_nombre,
            self.proveedor_ambiguo,
        )
        if hay_proveedor and not hay_oficio:
            raise ValueError("no hay proveedor sin oficio (R99)")
