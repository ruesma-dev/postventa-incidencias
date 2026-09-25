# services/postventa-api/domain/models/destino_posventa.py
"""El destino del parte en la biblioteca de Posventa (F-013): dominio puro.

Aquí se decide **en qué carpeta acaba un PDF con el DNI manuscrito de un
cliente**, y el fallo típico —el parte en la carpeta de otra villa u otra
obra— no se ve desde nuestro lado. Por eso cada regla es la escrita en
`specs/F-013-archivo-posventa/design.md` §4, sin heurísticas de más, y ante la
duda la respuesta es **no archivar y decir por qué** (un 409), nunca acercarse.

La estructura de Posventa es `<obra>/<INCIDENCIAS>/<unidad>/<FIRMADOS>`. Las
carpetas de obra y de unidad las crea Posventa a mano, así que la carpeta **se
encuentra**, no se compone: por cada nivel, las carpetas hijas se reparten en
tres grupos (§4.5):

- **casan** (la regla estricta del nivel): una → se usa; varias → ambigua;
- **parecidas** (no casan, pero cumplen la regla amplia): impiden crear;
- **ninguna de las dos**: solo entonces se crea, con el nombre de §4.6.

Casan y parecidas son una **partición**: lo que casa no se mira con la amplia.

Lo que este módulo **no** hace: leer nada. Ni la biblioteca, ni Sigrid, ni la
extracción del papel (R9). Entran nombres de carpeta y filas del ERP como
cadenas y salen tuplas de cadenas; quien orquesta las lecturas y decide el 409
es el resolutor (`application/pipelines/destino_archivo.py`).

**Enmienda del 2026-09-24 (T2, T3 y la parada T4).** La medición desmintió el
casado literal de la obra: la carpeta de la 0677 es `677  MIRASIERRA`, sin el
cero y con dos blancos. Desde entonces la obra casa **por su número** (R10), la
unidad nueva se llama `VILLA NN` derivado del `con.cod` (R37; con **tres**
cifras desde F-049, 2026-09-25: `VILLA 008`), la hoja admite
**una** forma alternativa (R49) y las reglas amplias se ensancharon donde la
medición enseñó un hueco (§4.5).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum

from domain.models.nombrado import nombre_admisible, normalizar_codigo

__all__ = [
    "PATRON_CODIGO_UNIDAD",
    "EstructuraArchivo",
    "MotivoDestino",
    "UbicacionReclamacion",
    "UnidadDeObra",
    "carpeta_con_nombre",
    "carpetas_de_obra",
    "carpetas_de_unidad",
    "clave_de_unidad",
    "nombre_de_carpeta_admisible",
    "nombre_de_obra_nueva",
    "nombre_derivado_de_unidad",
    "numero_de_obra",
    "obras_del_mismo_numero",
    "parecidas_de_obra",
    "parecidas_de_tramo",
    "parecidas_de_unidad",
    "unidades_que_casan",
    "unir_ruta",
]


class EstructuraArchivo(StrEnum):
    """Cómo se compone la carpeta del parte (R1, `design.md` §3.1)."""

    #: F-006: `<base>/<cod obra>`. El valor por omisión (R2).
    POR_OBRA = "por_obra"
    #: F-013: `<base>/<obra>/<INCIDENCIAS>/<unidad>/<FIRMADOS>`.
    POSVENTA = "posventa"


class MotivoDestino(StrEnum):
    """Por qué no se resolvió el destino: el código que va a la traza (R18).

    Es una lista **cerrada**: la de R18, enmendada el 2026-09-24. Son texto
    para que la traza `error` y la respuesta 409 (R19) los lleven tal cual.
    """

    # R7 · la reclamación en Sigrid
    RECLAMACION_NO_LOCALIZADA = "reclamacion_no_localizada"
    RECLAMACION_AMBIGUA = "reclamacion_ambigua"
    RECLAMACION_SIN_UNIDAD = "reclamacion_sin_unidad"
    # R8 · dos fuentes independientes tienen que decir la misma obra
    OBRA_NO_COINCIDE = "obra_no_coincide"
    # R13 y R14 · más de una carpeta que casa
    OBRA_AMBIGUA = "obra_ambigua"
    INCIDENCIAS_AMBIGUA = "incidencias_ambigua"
    UNIDAD_AMBIGUA = "unidad_ambigua"
    FIRMADOS_AMBIGUA = "firmados_ambigua"
    # R35 · ninguna casa, pero hay parecidas: no se crea
    OBRA_PARECIDA = "obra_parecida"
    INCIDENCIAS_PARECIDA = "incidencias_parecida"
    UNIDAD_PARECIDA = "unidad_parecida"
    FIRMADOS_PARECIDA = "firmados_parecida"
    # R16 · el nivel falta y crear está apagado
    SIN_CARPETA_OBRA = "sin_carpeta_obra"
    SIN_CARPETA_INCIDENCIAS = "sin_carpeta_incidencias"
    SIN_CARPETA_UNIDAD = "sin_carpeta_unidad"
    SIN_CARPETA_FIRMADOS = "sin_carpeta_firmados"
    # R38 · el nombre que habría que crear no vale para SharePoint
    NOMBRE_CARPETA_IMPOSIBLE = "nombre_carpeta_imposible"
    # R37, R44, R46 y R50 · añadidos el 2026-09-24
    UNIDAD_SIN_NOMBRE_DERIVABLE = "unidad_sin_nombre_derivable"
    OBRA_NUMERO_NO_UNICO = "obra_numero_no_unico"
    UNIDADES_SIN_VERIFICAR = "unidades_sin_verificar"
    NOMBRE_NO_CASARIA = "nombre_no_casaria"
    UNIDAD_CARPETA_COMPARTIDA = "unidad_carpeta_compartida"


@dataclass(frozen=True)
class UbicacionReclamacion:
    """Lo que Sigrid dice de la reclamación (R6): `rcp → upv → obr`.

    Solo datos del ERP: la `unidad` que la IA leyó del papel no entra aquí ni
    en ningún casado (R9). `unidad_nombre` puede llevar texto libre de la
    ficha y **no se registra** en ningún log (R23).
    """

    obra_codigo: str | None
    #: El `con.res` de ESA obra (`upv.obride`), para crear su carpeta (R36).
    obra_nombre: str | None
    unidad_codigo: str | None
    unidad_nombre: str | None


@dataclass(frozen=True)
class UnidadDeObra:
    """Una unidad de posventa de las obras con el número del parte (R44, R50).

    `obra_ref` es una referencia **opaca** de la obra en el ERP (`upv.obride`)
    y sirve solo para contar obras distintas: dos obras con el mismo código
    literal no se distinguen de otra forma. Es un identificador y se trata como
    los de SharePoint (R23): fuera del `repr`, para que un log descuidado de
    la fila no lo saque.
    """

    obra_ref: str = field(repr=False)
    obra_codigo: str | None
    unidad_codigo: str | None
    unidad_nombre: str | None


#: R37 · el único patrón del que se deriva un nombre de unidad. Medido en T3:
#: `0677.03VILLA 13.` (`<obra>.<grupo>VILLA <n>.`). `VILLA` en mayúsculas, como
#: se midió; otra palabra (`CHALET`, `PORTAL`) exige medir cómo la nombra
#: Posventa, y es otra enmienda.
PATRON_CODIGO_UNIDAD = re.compile(
    r"(?P<obra>[0-9]+)\.(?P<grupo>[0-9]+)VILLA +(?P<n>[0-9]+)\."
)

#: Solo cifras ASCII. `str.isdigit` admitiría `²` o cifras de otras
#: escrituras, que `int()` convierte en silencio.
_SOLO_CIFRAS = re.compile(r"[0-9]+")

#: Una palabra de la clave: letras o cifras de cualquier escritura, sin `_`.
_PALABRA = re.compile(r"[^\W_]+")


# --------------------------------------------------------------------------
# Normalizaciones
# --------------------------------------------------------------------------


def _sin_marcas(texto: str) -> str:
    """NFKD sin marcas diacríticas: `Núñez` → `Nunez`, `６` → `6`."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def _palabras(texto: str | None) -> tuple[str, ...]:
    """Palabras en mayúsculas y sin tildes; todo lo no alfanumérico separa."""
    if not texto:
        return ()
    return tuple(_PALABRA.findall(_sin_marcas(texto).upper()))


def _es_numero(palabra: str) -> bool:
    return _SOLO_CIFRAS.fullmatch(palabra) is not None


def clave_de_unidad(texto: str | None) -> tuple[str, ...]:
    """La forma canónica de una unidad o un tramo (`design.md` §4.3).

    NFKD sin marcas, mayúsculas, todo lo no alfanumérico es separador, y los
    tokens **numéricos** pasan a `str(int(t))`: `'05'` → `'5'`. Así `VILLA 05`
    y `Villa 5` tienen la misma clave, `(VILLA, 5)`.
    """
    return tuple(
        str(int(palabra)) if _es_numero(palabra) else palabra
        for palabra in _palabras(texto)
    )


def _numeros_en(texto: str) -> set[int]:
    """Todas las secuencias de cifras del texto, como enteros (§4.5 enmendado).

    Se busca **después** de NFKD: una cifra de ancho completo cuenta, porque la
    regla amplia es generosa a propósito (su error cuesta un 409).
    """
    return {int(cifras) for cifras in _SOLO_CIFRAS.findall(_sin_marcas(texto))}


def numero_de_obra(codigo: str | None) -> int | None:
    """El número de la obra: el entero del código si es **solo cifras 0-9**.

    El código se normaliza antes (`normalizar_codigo`: sin blancos, guiones al
    normal), así que `0677`, ` 0677 ` y `06 77` son 677. Un código con
    cualquier otra cosa —letras, guiones— no tiene número (códigos
    administrativos) y se compara literal (R10).
    """
    normalizado = normalizar_codigo(codigo)
    if not _es_numero(normalizado):
        return None
    return int(normalizado)


# --------------------------------------------------------------------------
# §4.1 · La carpeta de obra (R10, R13)
# --------------------------------------------------------------------------


def _casa_con_la_obra(nombre: str, *, codigo: str, numero: int | None) -> bool:
    """La regla estricta de la obra, para un código ya normalizado y no vacío."""
    if numero is not None:
        palabras = nombre.split()
        return (
            bool(palabras)
            and _es_numero(palabras[0])
            and int(palabras[0]) == numero
        )
    recortado = nombre.strip()
    if recortado == codigo:
        return True
    # Si empieza por el código y no es el código, es más largo: el índice existe.
    return recortado.startswith(codigo) and recortado[len(codigo)].isspace()


def carpetas_de_obra(nombres: Iterable[str], *, codigo_obra: str | None) -> tuple[str, ...]:
    """Las carpetas que casan con la obra por la regla estricta (R10).

    Con código **numérico**: la primera palabra del nombre —partido por blancos
    de cualquier clase y cantidad— es solo cifras y su entero es el número de
    la obra; el resto del nombre no cuenta. `677  MIRASIERRA` casa con la
    `0677`; `06770 X`, `0677-MIRASIERRA`, `677MIRASIERRA` y `OBRA 0677`, no.

    Con código **no numérico**: la literal de siempre, el nombre recortado es
    el código o empieza por el código seguido de un blanco.

    Devuelve los nombres **tal y como existen** (R4), en el orden de entrada.
    Más de uno es `obra_ambigua` (R13): aquí no se elige.
    """
    codigo = normalizar_codigo(codigo_obra)
    if not codigo:
        return ()
    numero = numero_de_obra(codigo)
    return tuple(
        nombre
        for nombre in nombres
        if _casa_con_la_obra(nombre, codigo=codigo, numero=numero)
    )


def _contiene_seguidas(palabras: tuple[str, ...], buscadas: tuple[str, ...]) -> bool:
    """¿Aparecen `buscadas` seguidas dentro de `palabras`?

    Las palabras no llevan blancos (`_PALABRA`), así que unirlas con uno y
    rodearlas de otro convierte «seguidas y enteras» en una búsqueda de texto.
    """
    return f" {' '.join(buscadas)} " in f" {' '.join(palabras)} "


def parecidas_de_obra(nombres: Iterable[str], *, codigo_obra: str | None) -> tuple[str, ...]:
    """Las que no casan con la obra pero se le parecen: impiden crearla (R35).

    Con código numérico, alguna **secuencia de cifras** del nombre es el número
    de la obra (`0677-MIRASIERRA`, `677MIRASIERRA`, `OBRA 0677`, `LISTADO 677`);
    `06770 X` no, porque es otro número. Con código no numérico, las palabras
    del código aparecen seguidas entre las del nombre, sin mayúsculas ni
    tildes (`ADM-GENERAL`, `adm general` para `ADM`).
    """
    codigo = normalizar_codigo(codigo_obra)
    if not codigo:
        return ()
    numero = numero_de_obra(codigo)
    palabras_del_codigo = _palabras(codigo)

    def _se_parece(nombre: str) -> bool:
        if numero is not None:
            return numero in _numeros_en(nombre)
        return bool(palabras_del_codigo) and _contiene_seguidas(
            _palabras(nombre), palabras_del_codigo
        )

    return tuple(
        nombre
        for nombre in nombres
        if not _casa_con_la_obra(nombre, codigo=codigo, numero=numero)
        and _se_parece(nombre)
    )


# --------------------------------------------------------------------------
# §4.2 · Los tramos fijos y la hoja alternativa (R14, R16, R49)
# --------------------------------------------------------------------------


def _claves_del_tramo(buscado: str, alternativa: str) -> tuple[tuple[str, ...], ...]:
    """Las claves que casan con el tramo: la buscada y, si hay, la alternativa."""
    return tuple(
        clave
        for clave in (clave_de_unidad(buscado), clave_de_unidad(alternativa))
        if clave
    )


def carpeta_con_nombre(
    nombres: Iterable[str], *, buscado: str, alternativa: str = ""
) -> tuple[str, ...]:
    """Las carpetas cuyo nombre es el del tramo, por su clave (R14, R49).

    Casa lo que tenga la clave de `buscado` **o** la de `alternativa` (si no
    está vacía), y nada más: `Partes Incidencias` casa con `PARTES
    INCIDENCIAS`; con la alternativa de la hoja, `PARTES FIRMADO` casa con
    `PARTES FIRMADOS`. Se devuelve el nombre **tal y como existe**. Dos que
    casan —también la principal y la alternativa— son una ambigüedad (R14).
    Un tramo configurado vacío no casa con nada.
    """
    claves = _claves_del_tramo(buscado, alternativa)
    return tuple(nombre for nombre in nombres if clave_de_unidad(nombre) in claves)


def parecidas_de_tramo(
    nombres: Iterable[str], *, buscado: str, alternativa: str = ""
) -> tuple[str, ...]:
    """Las que no casan con el tramo pero llevan su palabra distintiva (R35).

    La palabra distintiva es la **última** de la clave de `buscado`, sin su `S`
    final (`FIRMADO`, `INCIDENCIA`), y una carpeta es parecida si alguna de sus
    palabras **empieza** por ella: `PARTE FIRMADO`, `FIRMADOS 2024`, `PARTES DE
    INCIDENCIAS`, `PARTES INCIDENCIA`. La alternativa entra solo para la
    partición: lo que casa con ella no es parecido.
    """
    clave_buscada = clave_de_unidad(buscado)
    if not clave_buscada:
        return ()
    # Sin su `S` final, una sola; y si la palabra es solo `S`, entera: un
    # prefijo vacío haría parecida cualquier carpeta.
    distintiva = clave_buscada[-1].removesuffix("S") or clave_buscada[-1]
    claves = _claves_del_tramo(buscado, alternativa)
    return tuple(
        nombre
        for nombre in nombres
        if clave_de_unidad(nombre) not in claves
        and any(palabra.startswith(distintiva) for palabra in clave_de_unidad(nombre))
    )


# --------------------------------------------------------------------------
# §4.3 · La carpeta de unidad (R11, R14; D-6)
# --------------------------------------------------------------------------


def _casa_con_la_unidad(
    carpeta: str, *, unidad_codigo: str | None, unidad_nombre: str | None
) -> bool:
    """La regla estricta de la unidad (`design.md` §4.3).

    La clave de la carpeta no está vacía, lleva al menos un número y es (1)
    la del código de la unidad o (2) un **sufijo contiguo** de la de su nombre.
    El número evita que `VILLA` a secas case con todas; el sufijo, que
    `VILLA 5` case con «Villa 51».
    """
    clave = clave_de_unidad(carpeta)
    # Sin número no casa; y una clave vacía no tiene ninguno.
    if not any(_es_numero(palabra) for palabra in clave):
        return False
    if clave == clave_de_unidad(unidad_codigo):
        return True
    # `clave` no está vacía; si es más larga que la del nombre, el corte da el
    # nombre entero, que no puede ser igual a ella.
    return clave_de_unidad(unidad_nombre)[-len(clave) :] == clave


def carpetas_de_unidad(
    nombres: Iterable[str], *, ubicacion: UbicacionReclamacion
) -> tuple[str, ...]:
    """Las carpetas que casan con la unidad de la reclamación (R11).

    Medido el 2026-09-24: los siete casos reales casan por el nombre
    (`VILLA 05` es sufijo de `Viviendas Bloque Villa 5`). Más de una es
    `unidad_ambigua` (R14).
    """
    return tuple(
        nombre
        for nombre in nombres
        if _casa_con_la_unidad(
            nombre,
            unidad_codigo=ubicacion.unidad_codigo,
            unidad_nombre=ubicacion.unidad_nombre,
        )
    )


def _numeros_de_la_unidad(ubicacion: UbicacionReclamacion) -> set[int]:
    """Los números que identifican a la unidad, para la regla amplia (§4.5).

    Los de la clave de su nombre y el `<n>` del patrón de R37 si el código lo
    cumple. **No** todos los del código: `0677.03VILLA 13.` lleva el número de
    la obra y el `03` del grupo, y con ellos `VILLA 03` sería parecida de la
    unidad 13 y bloquearía crear `VILLA 13` (T4-5). Solo si el código no cumple
    el patrón se usan los números de su clave, como antes de la enmienda.
    """
    numeros = {
        int(palabra)
        for palabra in clave_de_unidad(ubicacion.unidad_nombre)
        if _es_numero(palabra)
    }
    codigo = (ubicacion.unidad_codigo or "").strip()
    encaje = PATRON_CODIGO_UNIDAD.fullmatch(codigo)
    if encaje is not None:
        numeros.add(int(encaje["n"]))
    else:
        numeros |= {
            int(palabra) for palabra in clave_de_unidad(codigo) if _es_numero(palabra)
        }
    return numeros


def parecidas_de_unidad(
    nombres: Iterable[str], *, ubicacion: UbicacionReclamacion
) -> tuple[str, ...]:
    """Las que no casan con la unidad pero llevan su número: impiden crearla (R35).

    Alguna secuencia de cifras de la carpeta (`VILLA5`, `V-5`, `VILLA 05 -
    GARCIA`, `CHALET 5`) es un número de la unidad. `VILLA 07` y `VILLA 15`
    **no** lo son para la unidad 5: un número distinto es otra unidad, y es
    justo lo que se tiene que poder crear.
    """
    numeros = _numeros_de_la_unidad(ubicacion)
    return tuple(
        nombre
        for nombre in nombres
        if not _casa_con_la_unidad(
            nombre,
            unidad_codigo=ubicacion.unidad_codigo,
            unidad_nombre=ubicacion.unidad_nombre,
        )
        and bool(_numeros_en(nombre) & numeros)
    )


# --------------------------------------------------------------------------
# §4.6 · Con qué nombre se crea (R36–R38)
# --------------------------------------------------------------------------


def nombre_de_obra_nueva(codigo_obra: str | None, obra_nombre: str | None) -> str:
    """`<código> <con.res>`: el nombre de la carpeta de obra que se crea (R36).

    El código normalizado, ceros intactos; el `con.res` de esa obra literal,
    recortado y con los blancos interiores colapsados a uno. Nada más: ni
    mayúsculas forzadas ni abreviaturas. Sin `con.res`, el resultado acaba en
    blanco y R38 lo rechaza: no se inventa un nombre.
    """
    nombre = " ".join((obra_nombre or "").split())
    return f"{normalizar_codigo(codigo_obra)} {nombre}"


def nombre_derivado_de_unidad(unidad_codigo: str | None, *, codigo_obra: str | None) -> str | None:
    """`VILLA NNN`, derivado del `con.cod` de la unidad (R37).

    Solo si el código, recortado, cumple **entero** el patrón medido y el
    número de su `<obra>` es el de `codigo_obra`. `NNN` es `<n>` como entero
    con **al menos tres cifras** (`8` → `VILLA 008`, `13` → `VILLA 013`,
    `1000` → `VILLA 1000`): así llama Posventa a sus unidades desde que
    reorganizó la biblioteca (F-049, decisión del humano del 2026-09-25; hasta
    entonces eran dos cifras). El ancho solo es del nombre **que se crea**: el
    casado compara enteros, y `VILLA 01` sigue siendo la villa 1. El `<grupo>`
    no entra: Posventa no lo usa (y por eso R50). En cualquier otro caso,
    `None`: el sistema no inventa, y es un 409 solo si hay que crear.
    """
    encaje = PATRON_CODIGO_UNIDAD.fullmatch((unidad_codigo or "").strip())
    if encaje is None:
        return None
    numero = numero_de_obra(codigo_obra)
    if numero is None or int(encaje["obra"]) != numero:
        return None
    return f"VILLA {int(encaje['n']):03d}"


def nombre_de_carpeta_admisible(nombre: str) -> bool:
    """¿Se puede crear una carpeta con ese nombre? (R38).

    La misma regla que F-006 R7 aplica al fichero (`nombrado.nombre_admisible`,
    importada y no copiada): ni vacío, ni un carácter que SharePoint no admite,
    ni blancos en los extremos, ni punto final. Un nombre imposible es un 409
    `nombre_carpeta_imposible`; nunca se sanea.
    """
    return nombre_admisible(nombre)


# --------------------------------------------------------------------------
# §4.7 · Números repetidos en Sigrid (R44, R50)
# --------------------------------------------------------------------------


def obras_del_mismo_numero(
    filas: Iterable[UnidadDeObra], *, codigo_obra: str | None
) -> frozenset[str]:
    """Las obras distintas (`obra_ref`) con el número de la obra del parte (R44).

    Misma obra = mismo número (§4.1) o, si el código no es numérico, el mismo
    código normalizado. El SQL preselecciona de más (`%677` deja pasar `1677`);
    aquí se vuelve a filtrar. Si no sale **exactamente una**, el resolutor
    para con `obra_numero_no_unico`: dos obras de Sigrid irían a la misma
    carpeta de Posventa.
    """
    codigo = normalizar_codigo(codigo_obra)
    if not codigo:
        return frozenset()
    numero = numero_de_obra(codigo)

    def _es_la_misma(fila: UnidadDeObra) -> bool:
        if numero is not None:
            return numero_de_obra(fila.obra_codigo) == numero
        return normalizar_codigo(fila.obra_codigo) == codigo

    return frozenset(fila.obra_ref for fila in filas if _es_la_misma(fila))


def unidades_que_casan(
    filas: Iterable[UnidadDeObra], *, carpeta: str
) -> tuple[UnidadDeObra, ...]:
    """Las unidades de la obra con las que `carpeta` casa por la regla estricta (R50).

    El resolutor exige **exactamente una**: si dos unidades de Sigrid casan con
    `VILLA 05` —dos grupos con una villa 5 cada uno—, el DNI podría acabar en la
    villa del otro grupo (`unidad_carpeta_compartida`).
    """
    return tuple(
        fila
        for fila in filas
        if _casa_con_la_unidad(
            carpeta, unidad_codigo=fila.unidad_codigo, unidad_nombre=fila.unidad_nombre
        )
    )


# --------------------------------------------------------------------------
# §4.4 · La ruta (R17)
# --------------------------------------------------------------------------


def unir_ruta(*tramos: str) -> str:
    """Une los tramos con `/`, ignorando vacíos y barras de los extremos.

    Con la base vacía (la raíz, D-1) no sale `/677  MIRASIERRA` ni `//`. Cada
    tramo se recorta por sus extremos como la base de `carpeta_de_archivo`;
    los blancos **de dentro** se respetan: el nombre va tal y como existe (R4).
    """
    return "/".join(
        limpio for limpio in (tramo.strip().strip("/").strip() for tramo in tramos) if limpio
    )
