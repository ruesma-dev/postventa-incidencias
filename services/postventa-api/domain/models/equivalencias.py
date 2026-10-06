# services/postventa-api/domain/models/equivalencias.py
"""Equivalencias entre códigos casi duplicados de un catálogo de Sigrid (F-036).

`specs/F-036-importar-excel/design.md` §15. El catálogo de oficios de Sigrid
(`auxofc`) tiene entradas casi iguales —en la 0677, «Carpinteria de madera» /
«Carpintería de madera», «Mobiliario de cocinas» / «Mobiliario cocina» y
«Solados y Alicatados M.O.» / «Solados y Alicatados»— y un desplegable con una
entrada por código enseña el mismo oficio dos veces. Aquí:

1. **La propuesta** (§15.2, R78, R79, R85): la clave de un nombre, los motivos
   de un par (`mismo_nombre`, `plural`, `errata`, `incluido`) y los grupos que
   se proponen (cliques; si no, por pares).
2. **Los grupos vigentes** (§15.4, R81, R82, R84, R86): la unión de los pares
   cuya última decisión humana es «mismo», sin las componentes contradichas.
3. **La costura de proveedores** (§15.8): sin agrupación de proveedores
   (F-050), cada código es su propio grupo (`grupos_de_proveedor`).
4. **Los pares decididos como distintos** (F-053, R9–R13): los de unos
   códigos cuya última decisión es «distinto» (`pares_distintos`), con la
   misma regla de «manda la última» que los grupos vigentes.

Nada se agrupa solo (R80): proponer no cambia los grupos vigentes, que solo
salen de decisiones humanas.

**`Catalogo.PROVEEDOR` existe sin perfil (T7, 2026-09-29).** `design.md` §15.2
y §15.8 dicen que en F-036 `Catalogo` solo tiene `OFICIO`, pero la misma
§15.8 pide grupos de proveedor («cada código, su propio grupo») y
`OpcionProveedor.grupo` es un `Grupo`, que lleva catálogo; R95 exige además
que un código de oficio y otro de proveedor escritos igual no se confundan. El
valor `proveedor` ya está en el `CHECK` de la tabla (§15.4). Lo que F-050
añade sigue fuera: el `Perfil` de proveedores (formas jurídicas), el motivo
`mismo_cif` y la lectura de grupos de la tabla. `PERFILES` solo tiene
`OFICIO`, así que nada puede **proponer** grupos de proveedores.

Dominio puro: sin red, sin base de datos, sin IA y sin reloj.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Literal


class Catalogo(StrEnum):
    """El catálogo de Sigrid al que pertenecen los códigos de un grupo.

    Los valores son los del `CHECK` de `postventa.decisiones_equivalencia`
    (§15.4). `PROVEEDOR` es el discriminador de la costura (§15.8): no tiene
    perfil hasta F-050. F-039 añadirá `ACTIVIDAD_OFICIO`.
    """

    OFICIO = "oficio"
    PROVEEDOR = "proveedor"


class Motivo(StrEnum):
    """Por qué se propone un par (R78). F-050 añadirá `mismo_cif`."""

    MISMO_NOMBRE = "mismo_nombre"
    PLURAL = "plural"
    ERRATA = "errata"
    INCLUIDO = "incluido"


#: Lo que puede decidir una persona sobre un par (R81).
MISMO = "mismo"
DISTINTO = "distinto"
Decision = Literal["mismo", "distinto"]
_DECISIONES = frozenset({MISMO, DISTINTO})

#: Palabras que no distinguen un nombre de otro (§15.2 a).
PALABRAS_VACIAS: frozenset[str] = frozenset(
    {"de", "del", "la", "las", "el", "los", "y", "e"}
)

#: Umbrales de D-22 (opción por defecto; se revisan en la PARADA T9).
ERRATA_MAX_DISTANCIA = 2
ERRATA_MAX_PORCENTAJE = 10  # de la longitud de la clave más larga
ERRATA_MIN_LONGITUD = 8  # caracteres de la clave más corta
INCLUIDO_MIN_PALABRAS = 2  # palabras de la clave más corta
SINGULAR_MIN_LETRAS = 5  # «más de 4 letras» (§15.2 b)

_VOCALES = frozenset("aeiou")

#: Una sigla con puntos: dos o más letras sueltas separadas por punto, con o
#: sin el punto final (`m.o.`, `s.a.t`). «p. baja» no lo es: una sola letra.
_SIGLA = re.compile(r"(?<!\w)((?:[^\W\d_]\.)+[^\W\d_])\.?(?!\w)")
#: Lo que no es letra, cifra ni blanco (el `_` cuenta como puntuación).
_PUNTUACION = re.compile(r"[^\w\s]|_")


@dataclass(frozen=True)
class Perfil:
    """Lo único que distingue a un catálogo en la propuesta (R96).

    `palabras_ignoradas` está vacío en oficios; F-050 pondrá las formas
    jurídicas sin tocar las funciones.
    """

    catalogo: Catalogo
    palabras_ignoradas: frozenset[str]


#: Un perfil por catálogo que admite propuestas: en F-036, solo oficios.
PERFILES: Mapping[Catalogo, Perfil] = MappingProxyType(
    {Catalogo.OFICIO: Perfil(Catalogo.OFICIO, frozenset())}
)


@dataclass(frozen=True)
class Candidato:
    """Un código del catálogo con su nombre de Sigrid (`None` si no lo tiene)."""

    codigo: str
    nombre: str | None


@dataclass(frozen=True)
class Grupo:
    """Varios códigos de **un mismo** catálogo que se enseñan como uno.

    Sin decisiones confirmadas, cada código es su propio grupo. `etiqueta` es
    el nombre que ve quien rellena (R86); los códigos son los de Sigrid, y
    pueden incluir alguno que no esté en la obra (una equivalencia vale para
    todas, R84): los de la obra los dice `OpcionOficio.codigos_en_obra`.
    """

    catalogo: Catalogo
    codigos: frozenset[str]
    etiqueta: str


@dataclass(frozen=True)
class DecisionPar:
    """Una decisión humana sobre un par, tal como se guarda (§15.4, R81, R83).

    El par va en orden (`codigo_a < codigo_b`, como el `CHECK` de la tabla), y
    se identifica por (`catalogo`, `codigo_a`, `codigo_b`) (R95).
    """

    catalogo: Catalogo
    codigo_a: str
    codigo_b: str
    decision: Decision
    motivos: frozenset[Motivo]
    obra_codigo: str
    decidido_por: str
    decidido_at_utc: datetime

    def __post_init__(self) -> None:
        if not self.codigo_a < self.codigo_b:
            raise ValueError("el par de una decisión va en orden y sin repetir código")
        if self.decision not in _DECISIONES:
            raise ValueError("una decisión es «mismo» o «distinto»")


@dataclass(frozen=True)
class ParPropuesto:
    """Un par que se parece, con sus motivos (`codigo_a < codigo_b`)."""

    codigo_a: str
    codigo_b: str
    motivos: frozenset[Motivo]


@dataclass(frozen=True)
class Propuesta:
    """Lo que se enseña a una persona para que decida (§15.3).

    Un grupo entero (una componente que es un clique) o, si la componente no lo
    es, uno de sus pares (`por_pares`, R79). `pares` son los pares con motivo
    que la persona confirma al decir «son el mismo».
    """

    catalogo: Catalogo
    codigos: tuple[str, ...]
    pares: tuple[ParPropuesto, ...]
    por_pares: bool

    @property
    def motivos(self) -> frozenset[Motivo]:
        return frozenset(m for par in self.pares for m in par.motivos)


@dataclass(frozen=True)
class GruposVigentes:
    """Los grupos que se aplican en un catálogo, por orden de su menor código.

    `no_aplicados` son las componentes que no se aplican porque contienen un
    par cuya última decisión es «distinto» (R82): la pantalla las avisa.
    """

    catalogo: Catalogo
    grupos: tuple[Grupo, ...]
    no_aplicados: tuple[frozenset[str], ...]

    def __post_init__(self) -> None:
        vistos: set[str] = set()
        for grupo in self.grupos:
            if grupo.catalogo is not self.catalogo:
                raise ValueError("grupo de otro catálogo")
            if not grupo.codigos or grupo.codigos & vistos:
                raise ValueError("grupo vacío o con un código de otro grupo")
            vistos |= grupo.codigos

    def grupo_de(self, codigo: str) -> Grupo:
        """El grupo de un código, o `ValueError` si no tiene."""
        for grupo in self.grupos:
            if codigo in grupo.codigos:
                return grupo
        raise ValueError("código sin grupo vigente")


# --- a) y b): la clave de un nombre ------------------------------------------


def clave_de_nombre(nombre: str, perfil: Perfil) -> str:
    """La forma de un nombre con la que se comparan dos códigos (§15.2 a).

    Sin diacríticos, en minúsculas, `&` como `y`, las siglas sin sus puntos
    (`M.O.` → `mo`), el resto de la puntuación como blanco, los blancos
    colapsados y sin las `PALABRAS_VACIAS` ni las del perfil. «Mobiliario de
    cocinas» da `mobiliario cocinas`.
    """
    descompuesto = unicodedata.normalize("NFKD", nombre)
    texto = "".join(c for c in descompuesto if not unicodedata.combining(c)).lower()
    texto = texto.replace("&", " y ")
    texto = _SIGLA.sub(lambda m: m.group(1).replace(".", ""), texto)
    texto = _PUNTUACION.sub(" ", texto)
    fuera = PALABRAS_VACIAS | perfil.palabras_ignoradas
    return " ".join(p for p in texto.split() if p not in fuera)


def _singular(palabra: str) -> str:
    if len(palabra) < SINGULAR_MIN_LETRAS:
        return palabra
    if palabra.endswith("es") and palabra[-3] not in _VOCALES:
        return palabra[:-2]
    if palabra.endswith("s"):
        return palabra[:-1]
    return palabra


def clave_singular(clave: str) -> str:
    """Cada palabra de más de 4 letras, sin su plural (§15.2 b).

    Pierde la `s` final, o `es` si la palabra acaba en consonante + `es`. Es
    burdo a propósito («muebles» → «muebl»): solo **propone**, y lo propuesto
    lo mira una persona.
    """
    return " ".join(_singular(p) for p in clave.split())


def distancia_edicion(a: str, b: str) -> int:
    """Distancia de Levenshtein: inserciones, borrados y sustituciones."""
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        actual = [i]
        for j, cb in enumerate(b, start=1):
            actual.append(
                min(anterior[j] + 1, actual[j - 1] + 1, anterior[j - 1] + (ca != cb))
            )
        anterior = actual
    return anterior[-1]


# --- c): los motivos de un par ------------------------------------------------


def _es_errata(clave_a: str, clave_b: str) -> bool:
    corta, larga = sorted((clave_a, clave_b), key=len)
    if len(corta) < ERRATA_MIN_LONGITUD:
        return False
    distancia = distancia_edicion(clave_a, clave_b)
    return (
        distancia <= ERRATA_MAX_DISTANCIA
        and distancia * 100 <= len(larga) * ERRATA_MAX_PORCENTAJE
    )


def _incluida(clave_a: str, clave_b: str) -> bool:
    corta, larga = sorted((clave_a.split(), clave_b.split()), key=len)
    return len(corta) >= INCLUIDO_MIN_PALABRAS and larga[: len(corta)] == corta


def motivos_del_par(a: Candidato, b: Candidato, perfil: Perfil) -> frozenset[Motivo]:
    """Por qué dos códigos **podrían** ser el mismo (R78, D-22).

    - `mismo_nombre`: la misma clave; entonces es el único motivo.
    - `plural`: solo las claves en singular son iguales.
    - `errata`: si no es plural, distancia entre claves ≤ 2 y ≤ 10 % de la más
      larga, con la más corta de ≥ 8 caracteres.
    - `incluido`: las palabras de una clave, de al menos dos, son el principio
      de la otra («solados alicatados» / «solados alicatados mo»).

    Un código sin nombre, o con un nombre que se queda sin clave, no se
    parece a nada.
    """
    if a.nombre is None or b.nombre is None:
        return frozenset()
    clave_a = clave_de_nombre(a.nombre, perfil)
    clave_b = clave_de_nombre(b.nombre, perfil)
    if clave_a == clave_b:
        # Dos nombres sin clave no son «el mismo»; uno sin clave frente a otro
        # con ella no cumple ningún motivo (0 caracteres, 0 palabras).
        return frozenset({Motivo.MISMO_NOMBRE}) if clave_a else frozenset()
    motivos: set[Motivo] = set()
    if clave_singular(clave_a) == clave_singular(clave_b):
        motivos.add(Motivo.PLURAL)
    elif _es_errata(clave_a, clave_b):
        motivos.add(Motivo.ERRATA)
    if _incluida(clave_a, clave_b):
        motivos.add(Motivo.INCLUIDO)
    return frozenset(motivos)


# --- d): la propuesta ---------------------------------------------------------


def _por_codigo(candidatos: Iterable[Candidato]) -> dict[str, Candidato]:
    """Un candidato por código, en orden de código; si se repite, el primero."""
    unicos: dict[str, Candidato] = {}
    for candidato in candidatos:
        unicos.setdefault(candidato.codigo, candidato)
    return dict(sorted(unicos.items()))


def _ultimas(
    decisiones: Iterable[DecisionPar], catalogo: Catalogo
) -> dict[tuple[str, str], DecisionPar]:
    """La última decisión de cada par del catálogo (R81, R95).

    Manda la fecha; a igual fecha, la que llega después. Las de otro catálogo
    no cuentan aunque tengan los mismos códigos.
    """
    ultimas: dict[tuple[str, str], DecisionPar] = {}
    for decision in decisiones:
        if decision.catalogo is not catalogo:
            continue
        par = (decision.codigo_a, decision.codigo_b)
        vigente = ultimas.get(par)
        if vigente is None or decision.decidido_at_utc >= vigente.decidido_at_utc:
            ultimas[par] = decision
    return ultimas


def _componentes(
    nodos: Iterable[str], aristas: Iterable[tuple[str, str]]
) -> list[frozenset[str]]:
    """Componentes conexas, cada una una vez, por orden de su menor código."""
    vecinos: dict[str, set[str]] = {n: set() for n in nodos}
    for a, b in aristas:
        vecinos.setdefault(a, set()).add(b)
        vecinos.setdefault(b, set()).add(a)
    componentes: list[frozenset[str]] = []
    vistos: set[str] = set()
    for inicio in sorted(vecinos):
        if inicio in vistos:
            continue
        componente = {inicio}
        pendientes = [inicio]
        while pendientes:
            for vecino in vecinos[pendientes.pop()] - componente:
                componente.add(vecino)
                pendientes.append(vecino)
        vistos |= componente
        componentes.append(frozenset(componente))
    return componentes


def proponer_grupos(
    candidatos: Iterable[Candidato],
    decisiones: Iterable[DecisionPar],
    perfil: Perfil,
) -> tuple[Propuesta, ...]:
    """Los grupos que se proponen entre los candidatos (§15.2 d, R78, R79, R85).

    Un grafo con una arista por par con algún motivo, **sin** los pares ya
    decididos (con cualquier decisión). Cada componente que es un clique de
    ese grafo se propone entera; si no lo es, cada una de sus aristas por
    separado. Determinista: por orden de códigos.
    """
    por_codigo = _por_codigo(candidatos)
    decididos = _ultimas(decisiones, perfil.catalogo)
    codigos = list(por_codigo)
    aristas: dict[tuple[str, str], frozenset[Motivo]] = {}
    for i, a in enumerate(codigos):
        for b in codigos[i + 1 :]:
            if (a, b) in decididos:
                continue
            motivos = motivos_del_par(por_codigo[a], por_codigo[b], perfil)
            if motivos:
                aristas[(a, b)] = motivos
    propuestas: list[Propuesta] = []
    for componente in _componentes((), aristas):
        pares = tuple(
            ParPropuesto(a, b, m) for (a, b), m in aristas.items() if a in componente
        )
        n = len(componente)
        if len(pares) * 2 == n * (n - 1):
            propuestas.append(
                Propuesta(perfil.catalogo, tuple(sorted(componente)), pares, False)
            )
        else:
            propuestas.extend(
                Propuesta(perfil.catalogo, (p.codigo_a, p.codigo_b), (p,), True)
                for p in pares
            )
    return tuple(propuestas)


# --- §15.4: los grupos vigentes -----------------------------------------------


def _etiqueta(candidato: Candidato) -> str:
    return (candidato.nombre or "").strip() or candidato.codigo


def grupos_vigentes(
    candidatos: Iterable[Candidato],
    decisiones: Iterable[DecisionPar],
    perfil: Perfil,
    uso_en_obra: Mapping[str, int],
) -> GruposVigentes:
    """Los grupos que se aplican a los candidatos de una obra (§15.4).

    Las componentes conexas de los pares cuya **última** decisión es «mismo»
    (R81, R84: da igual desde qué obra se decidió). Una componente con un par
    cuya última decisión es «distinto» no se aplica y va a `no_aplicados`
    (R82). Cada candidato sin grupo es el suyo. Solo salen los grupos con
    algún candidato; su etiqueta es la del candidato con más filas en
    `obrofc` de la obra y, a igualdad, la del de código menor (R86): su
    nombre recortado o, sin nombre, su código.
    """
    por_codigo = _por_codigo(candidatos)
    ultimas = _ultimas(decisiones, perfil.catalogo)
    mismos = [par for par, d in ultimas.items() if d.decision == MISMO]
    distintos = [par for par, d in ultimas.items() if d.decision == DISTINTO]
    grupos: list[Grupo] = []
    no_aplicados: list[frozenset[str]] = []
    for componente in _componentes(por_codigo, mismos):
        de_la_obra = sorted(c for c in componente if c in por_codigo)
        if not de_la_obra:
            continue
        if any(a in componente and b in componente for a, b in distintos):
            no_aplicados.append(componente)
            grupos.extend(
                Grupo(perfil.catalogo, frozenset({c}), _etiqueta(por_codigo[c]))
                for c in de_la_obra
            )
            continue
        cabeza = min(de_la_obra, key=lambda c: (-uso_en_obra.get(c, 0), c))
        grupos.append(Grupo(perfil.catalogo, componente, _etiqueta(por_codigo[cabeza])))
    grupos.sort(key=lambda g: min(g.codigos))
    return GruposVigentes(perfil.catalogo, tuple(grupos), tuple(no_aplicados))


# --- F-053: los pares decididos como distintos ----------------------------------


def pares_distintos(
    codigos: Iterable[str],
    decisiones: Iterable[DecisionPar],
    catalogo: Catalogo,
) -> tuple[tuple[str, str], ...]:
    """Los pares cuya última decisión es «distinto» entre unos códigos (F-053, R9).

    La última, con la regla de `_ultimas` (manda la fecha; a igual fecha, la
    que llega después; las de otro catálogo no cuentan, R13). Solo los pares
    con **los dos** códigos en `codigos`, aunque quien llame ya lo filtre: la
    función no se fía. Cada par en orden (`codigo_a < codigo_b`, como
    `DecisionPar`), una vez, y la lista ordenada (R12).
    """
    dados = frozenset(codigos)
    return tuple(
        sorted(
            par
            for par, decision in _ultimas(decisiones, catalogo).items()
            if decision.decision == DISTINTO and par[0] in dados and par[1] in dados
        )
    )


# --- §15.8: la costura de proveedores -----------------------------------------


def grupos_de_proveedor(candidatos: Iterable[Candidato]) -> GruposVigentes:
    """Los grupos de proveedor en F-036: cada código, su propio grupo (§15.8).

    Sin agrupación de proveedores (F-050) ni decisiones que leer: la etiqueta
    es el nombre recortado o, sin nombre, el código. Un código repetido (el
    mismo proveedor con varios oficios en `obrofc`) cuenta una vez.
    """
    grupos = tuple(
        Grupo(Catalogo.PROVEEDOR, frozenset({codigo}), _etiqueta(candidato))
        for codigo, candidato in _por_codigo(candidatos).items()
    )
    return GruposVigentes(Catalogo.PROVEEDOR, grupos, ())
