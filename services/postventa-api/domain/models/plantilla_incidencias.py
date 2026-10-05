# services/postventa-api/domain/models/plantilla_incidencias.py
"""El contrato de la plantilla de incidencias (F-036): dominio puro.

`specs/F-036-importar-excel/design.md` §4.1. Aquí vive lo que el generador del
Excel y el importador tienen que compartir **al carácter**: el identificador y
la versión que se reconocen, la cabecera, los topes, las enumeraciones y las
etiquetas que ve quien rellena. El importador compara lo que trae cada fila con
estas etiquetas **exactamente** (decisión 7 de `requirements.md`), así que dos
criterios de etiqueta —uno al generar y otro al importar— romperían la
importación sin que nadie lo viera: por eso salen de aquí y solo de aquí.

`opciones_de_oficio` y `opciones_de_proveedor` (T7; R71, R72, R86, R92)
calculan los desplegables de `Oficio` y `Proveedor` desde el catálogo de la
obra y los grupos vigentes de `domain/models/equivalencias.py`: los usan el
generador y el importador, así que salen de aquí y solo de aquí.
`TextosPlantilla` (T6) es la forma de los textos del YAML de §3.4, que carga
`infrastructure/documentos/plantilla_yaml.py`.

Sin `openpyxl`, sin red, sin base de datos y sin reloj.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from domain.models.equivalencias import Catalogo, Grupo, GruposVigentes
from domain.models.errores import CodigoDeObraInvalido
from domain.models.nombrado import normalizar_codigo

IDENTIFICADOR_PLANTILLA = "ruesma.postventa-incidencias.plantilla-incidencias"
VERSION_PLANTILLA = 1
VERSIONES_SOPORTADAS: frozenset[int] = frozenset({1})
COLUMNA_ERRORES = "Errores (lo rellena el sistema)"
CABECERA: tuple[str, ...] = (
    "Unidad",
    "Ubicación",
    "Descripción corta",
    "Detalle",
    "Oficio",
    "Proveedor",
    "Urgencia",
    "Listado",
    COLUMNA_ERRORES,
)
SEPARADOR_PAR = " · "  # entre oficio y proveedor en la columna Proveedor
MAX_DESCRIPCION = 128  # con.res y `descripcion` de sigrid-api §8.9
MAX_UBICACION = 48  # rcp.resubi
MAX_DETALLE = 2000  # propio (D-11)
MAX_FILAS = 1000
MAX_BYTES_FICHERO = 2 * 1024 * 1024  # 2 MiB (D-11, R15)
MAX_CODIGO_OBRA = 24  # `obra` de sigrid-api §8.9

#: Lo único que admite un código de obra una vez normalizado (R9).
_CODIGO_OBRA_ADMISIBLE = re.compile(r"[0-9A-Za-z._-]+")

#: Puntuación que la clave de duplicado quita del final (`design.md` §4.5).
_PUNTUACION_FINAL = ".,;: "


class Urgencia(StrEnum):
    URGENTE = "urgente"
    SEGURIDAD = "seguridad"


class Listado(StrEnum):
    PRIMERO = "primero"
    SEGUNDO = "segundo"


class OrigenIncidencia(StrEnum):
    EXCEL = "excel"
    WEB = "web"  # F-037 (D-13)


@dataclass(frozen=True)
class UnidadPosventa:
    codigo: str
    nombre: str | None


@dataclass(frozen=True)
class OficioObra:
    codigo: str
    nombre: str | None


@dataclass(frozen=True)
class ProveedorEnObra:
    """Una fila de `obrofc` de la obra: un oficio y, si lo hay, su proveedor."""

    oficio_codigo: str
    proveedor_codigo: str | None  # None: fila de obrofc sin proveedor
    proveedor_nombre: str | None


@dataclass(frozen=True)
class CatalogoObra:
    obra_codigo: str
    obra_nombre: str | None
    unidades: tuple[UnidadPosventa, ...]
    oficios: tuple[OficioObra, ...]
    proveedores: tuple[ProveedorEnObra, ...]


@dataclass(frozen=True)
class Opcion:
    etiqueta: str
    codigo: str


@dataclass(frozen=True)
class OpcionOficio:
    """Una entrada del desplegable de `Oficio` (R92): un grupo de oficios."""

    etiqueta: str
    grupo: Grupo
    codigos_en_obra: tuple[str, ...]


@dataclass(frozen=True)
class OpcionProveedor:
    """Un par `<grupo de oficio> · <proveedor>` de la columna `Proveedor` (R71).

    `filas_en_obra` son las filas de `obrofc` que casan con el par, como
    `(oficio_codigo, proveedor_codigo)`: con ellas se resuelven juntos el
    oficio y el proveedor (R94). Sin agrupación de proveedores (F-050),
    `grupo` es siempre de un código.
    """

    etiqueta: str
    oficio: OpcionOficio
    grupo: Grupo
    filas_en_obra: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ListasCerradas:
    ubicaciones: tuple[str, ...]
    urgencias: tuple[Opcion, ...]
    listados: tuple[Opcion, ...]


@dataclass(frozen=True)
class MensajeColumna:
    """Los mensajes de la validación de datos de una columna (R3, R4).

    Excel los enseña al pinchar la celda (`entrada`) y al teclear un valor que
    no vale (`error`); sus topes son 32 caracteres el título y 255 el texto.
    """

    titulo_entrada: str
    entrada: str
    titulo_error: str
    error: str


@dataclass(frozen=True)
class TextosPlantilla:
    """Los textos de la plantilla que lee la propiedad (R5, R12, §3.5).

    Salen del YAML de `design.md` §3.4. `ejemplos` son filas de ejemplo por
    nombre de columna, que van en «Instrucciones» y **nunca** en «Incidencias»;
    `mensajes`, los de cada columna con validación, en el orden de la cabecera.
    """

    titulo: str
    instrucciones: tuple[str, ...]
    sin_oficios: str  # R12: la línea para una obra sin oficios
    excel_errores: str  # §3.5: el párrafo que añade el Excel de errores
    ejemplos: tuple[Mapping[str, str], ...]
    mensajes: Mapping[str, MensajeColumna]


def normalizar_codigo_obra(bruto: object) -> str:
    """El código de obra de una petición o de los metadatos, normalizado (R9).

    Se normaliza como los demás códigos del proyecto (`nombrado.normalizar_codigo`,
    F-032: guiones al normal y ningún blanco) y luego se exige que no esté vacío,
    que no pase de `MAX_CODIGO_OBRA` y que solo lleve `[0-9A-Za-z._-]`. Lo que
    no es texto se rechaza igual. El mensaje **no** repite lo que llegó: puede
    ser cualquier cosa y acaba en un log.
    """
    if not isinstance(bruto, str):
        raise CodigoDeObraInvalido("Falta el código de obra.")
    codigo = normalizar_codigo(bruto)
    if not codigo:
        raise CodigoDeObraInvalido("Falta el código de obra.")
    if len(codigo) > MAX_CODIGO_OBRA:
        raise CodigoDeObraInvalido(
            f"El código de obra pasa de {MAX_CODIGO_OBRA} caracteres."
        )
    if not _CODIGO_OBRA_ADMISIBLE.fullmatch(codigo):
        raise CodigoDeObraInvalido(
            "El código de obra solo admite cifras, letras sin tilde, punto, "
            "guion y guion bajo."
        )
    return codigo


def plegar(texto: str) -> str:
    """Sin diacríticos, en minúsculas y con los blancos colapsados a uno.

    Para **buscar** en un texto o detectar etiquetas que chocarían (R8, R34),
    nunca para aceptar un valor tasado: esos se comparan exactos (§4.3).
    """
    descompuesto = unicodedata.normalize("NFKD", texto)
    sin_marcas = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return " ".join(sin_marcas.lower().split())


def normalizar_para_clave(texto: str) -> str:
    """La forma de un texto que entra en la clave de duplicado (R35).

    Sin diacríticos, en minúsculas, blancos colapsados y sin la puntuación del
    final (`.`, `,`, `;`, `:`), para que «Sellar sifón» y «Sellar sifon.» den
    la misma clave. `str.split()` trata el separador de la clave (`\\x1f`) como
    blanco, así que no puede sobrevivir.

    **Solo** para la clave: los valores tasados se comparan exactos (§4.3).
    """
    return plegar(texto).rstrip(_PUNTUACION_FINAL)


def etiquetas_de_unidades(unidades: Iterable[UnidadPosventa]) -> tuple[Opcion, ...]:
    """Las opciones del desplegable de `Unidad`, ordenadas por código (R8).

    La etiqueta es el nombre recortado; sin nombre, el código. Si dos unidades
    dan la misma etiqueta plegada (sin mayúsculas, tildes ni blancos de más),
    las que tienen nombre pasan a `<nombre> (<código>)` y las que no siguen con
    su código, que ya es único. Excel compara las listas sin distinguir
    mayúsculas al teclear: dos etiquetas que solo difieren en eso confundirían
    a quien rellena. Determinista: el mismo catálogo, en cualquier orden, da
    las mismas etiquetas.
    """
    ordenadas = sorted(unidades, key=lambda u: u.codigo)
    bases = [((u.nombre or "").strip(), u.codigo) for u in ordenadas]
    veces = Counter(plegar(nombre or codigo) for nombre, codigo in bases)
    opciones: list[Opcion] = []
    for nombre, codigo in bases:
        if not nombre:
            etiqueta = codigo
        elif veces[plegar(nombre)] > 1:
            etiqueta = f"{nombre} ({codigo})"
        else:
            etiqueta = nombre
        opciones.append(Opcion(etiqueta=etiqueta, codigo=codigo))
    return tuple(opciones)


def _con_codigos(etiqueta: str, codigos: Iterable[str]) -> str:
    return f"{etiqueta} ({', '.join(sorted(codigos))})"


def opciones_de_oficio(
    catalogo: CatalogoObra, grupos: GruposVigentes
) -> tuple[OpcionOficio, ...]:
    """Las opciones del desplegable de `Oficio`: una por grupo vigente (R92).

    Solo los grupos con algún oficio de la obra, cada uno con los códigos que
    tiene en ella (`codigos_en_obra`) y ordenados por el menor, como antes de
    agrupar (R8). La etiqueta es la del grupo (R86); si dos dan la misma
    —plegadas, como las unidades: Excel no distingue mayúsculas al teclear—,
    cada una lleva sus códigos de la obra entre paréntesis. Sin grupos
    confirmados, cada código es su propio grupo.

    `grupos` tiene que ser de oficios y cubrir todos los de la obra; si no, o
    si las etiquetas siguen chocando, `ValueError`: el importador compara
    etiquetas exactas y dos iguales harían ambigua una fila.
    """
    if grupos.catalogo is not Catalogo.OFICIO:
        raise ValueError("los grupos de las opciones de oficio son de otro catálogo")
    por_grupo: dict[Grupo, list[str]] = {}
    for codigo in sorted({o.codigo for o in catalogo.oficios}):
        por_grupo.setdefault(grupos.grupo_de(codigo), []).append(codigo)
    veces = Counter(plegar(g.etiqueta) for g in por_grupo)
    opciones = tuple(
        OpcionOficio(
            etiqueta=grupo.etiqueta
            if veces[plegar(grupo.etiqueta)] == 1
            else _con_codigos(grupo.etiqueta, codigos),
            grupo=grupo,
            codigos_en_obra=tuple(codigos),
        )
        for grupo, codigos in por_grupo.items()
    )
    _exigir_distintas(o.etiqueta for o in opciones)
    return opciones


def opciones_de_proveedor(
    catalogo: CatalogoObra,
    grupos: GruposVigentes,
    oficios: tuple[OpcionOficio, ...],
) -> tuple[OpcionProveedor, ...]:
    """Los pares `<grupo de oficio> · <proveedor>` de la columna `Proveedor`.

    Uno por cada grupo de oficio del desplegable y cada grupo de proveedor con
    alguna fila de `obrofc` de la obra que los una (R71). Una fila sin
    proveedor no da par, ni la de un oficio que no está en `oficios` (de baja,
    R13). La parte de oficio es **exactamente** la etiqueta de `Oficio`
    (§3.2.1); la del proveedor, su nombre (R72, sin agrupación de proveedores:
    `grupos` es la costura de §15.8), con su código entre paréntesis si otro
    del mismo oficio da el mismo nombre plegado. En el orden de `oficios` y,
    dentro de cada uno, por nombre. `filas_en_obra` son las filas que casan con
    el par, para resolver juntos oficio y proveedor (R94).
    """
    if grupos.catalogo is not Catalogo.PROVEEDOR:
        raise ValueError("los grupos de las opciones de proveedor son de otro catálogo")
    oficio_de = {c: opcion for opcion in oficios for c in opcion.codigos_en_obra}
    filas: dict[OpcionOficio, dict[Grupo, set[tuple[str, str]]]] = {
        opcion: {} for opcion in oficios
    }
    for fila in catalogo.proveedores:
        opcion = oficio_de.get(fila.oficio_codigo)
        if fila.proveedor_codigo is None or opcion is None:
            continue
        grupo = grupos.grupo_de(fila.proveedor_codigo)
        filas[opcion].setdefault(grupo, set()).add(
            (fila.oficio_codigo, fila.proveedor_codigo)
        )
    pares: list[OpcionProveedor] = []
    for opcion, por_proveedor in filas.items():
        veces = Counter(plegar(g.etiqueta) for g in por_proveedor)
        nombres = {
            g: g.etiqueta
            if veces[plegar(g.etiqueta)] == 1
            else _con_codigos(g.etiqueta, g.codigos)
            for g in por_proveedor
        }
        for grupo in sorted(
            por_proveedor, key=lambda g: (plegar(nombres[g]), nombres[g])
        ):
            pares.append(
                OpcionProveedor(
                    etiqueta=f"{opcion.etiqueta}{SEPARADOR_PAR}{nombres[grupo]}",
                    oficio=opcion,
                    grupo=grupo,
                    filas_en_obra=tuple(sorted(por_proveedor[grupo])),
                )
            )
    return tuple(pares)


def _exigir_distintas(etiquetas: Iterable[str]) -> None:
    plegadas = [plegar(e) for e in etiquetas]
    if len(set(plegadas)) != len(plegadas):
        raise ValueError("dos opciones del desplegable dan la misma etiqueta")
