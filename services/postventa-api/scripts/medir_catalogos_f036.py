# services/postventa-api/scripts/medir_catalogos_f036.py
"""Mide los oficios casi duplicados de una obra sobre el JSON de T2 (F-036 T8).

`specs/F-036-importar-excel/design.md` §15.7. Lee el catálogo que escribe
`infra/26_catalogos_plantilla_sigrid.ps1 -SalidaJson` (fuera del repositorio:
lleva nombres de proveedor), aplica `proponer_grupos` a los oficios de la obra
y a todo `auxofc`, calcula las opciones de la plantilla sin grupos y con todo
lo propuesto confirmado, e imprime **solo recuentos**: ni un nombre ni un
código, para poder anotarlos en `progress/explore_F-036.md`.

Uso, desde `services/postventa-api`:

    .venv/Scripts/python.exe scripts/medir_catalogos_f036.py --catalogo "<JSON de T2>"

Solo lee ese fichero: sin red, sin Sigrid y sin base de datos.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# Lanzado como `python scripts/…`, la raíz del servicio no está en la ruta.
sys.path.append(str(Path(__file__).resolve().parent.parent))

from domain.models.equivalencias import (
    MISMO,
    PERFILES,
    Candidato,
    Catalogo,
    DecisionPar,
    Motivo,
    Propuesta,
    grupos_de_proveedor,
    grupos_vigentes,
    proponer_grupos,
)
from domain.models.importacion import resolver_oficio_y_proveedor
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    OficioObra,
    ProveedorEnObra,
    opciones_de_oficio,
    opciones_de_proveedor,
)

OFICIO = PERFILES[Catalogo.OFICIO]
#: Las decisiones hipotéticas («si se confirmara todo») llevan una fecha fija:
#: todas son «mismo», así que cuál sea no cambia nada.
_CUANDO = datetime.min.replace(tzinfo=UTC)


@dataclass(frozen=True)
class RecuentoPropuestas:
    """Lo que propone `proponer_grupos` sobre un conjunto de oficios."""

    candidatos: int
    propuestas: int
    grupos_enteros: int  # componentes que son clique
    pares_sueltos: int  # propuestas de componentes que no lo son (R79)
    pares_por_motivo: Mapping[str, int]
    propuestas_por_tamano: Mapping[int, int]
    componentes_no_clique: int


@dataclass(frozen=True)
class RecuentoPlantilla:
    """Los desplegables de la plantilla de la obra con unos grupos dados."""

    opciones_oficio: int
    oficios_ambiguos: int  # opciones con más de un código en la obra (D-19)
    pares_proveedor: int
    oficios_que_r91_rellenaria: int  # un solo par, que resuelve (R91, R94)
    oficios_sin_proveedor: int


@dataclass(frozen=True)
class Medicion:
    oficios_obra: int
    filas_obrofc: int
    filas_sin_proveedor: int
    obra: RecuentoPropuestas
    catalogo: RecuentoPropuestas
    plantilla_sin_grupos: RecuentoPlantilla
    plantilla_con_obra: RecuentoPlantilla
    plantilla_con_catalogo: RecuentoPlantilla


def _catalogo_obra(datos: Mapping) -> CatalogoObra:
    filas = datos["oficios_obra"]
    oficios = {f["oficio_codigo"]: f["oficio_nombre"] for f in filas}
    return CatalogoObra(
        obra_codigo=datos["obra"]["codigo"],
        obra_nombre=None,
        unidades=(),
        oficios=tuple(OficioObra(c, n) for c, n in sorted(oficios.items())),
        proveedores=tuple(
            ProveedorEnObra(
                f["oficio_codigo"], f["proveedor_codigo"], f["proveedor_nombre"]
            )
            for f in filas
        ),
    )


def _componentes_no_clique(propuestas: Iterable[Propuesta]) -> int:
    """Cuántas componentes se propusieron por pares (no cuántos pares)."""
    componentes: list[set[str]] = []
    for propuesta in propuestas:
        if not propuesta.por_pares:
            continue
        tocadas = [c for c in componentes if c & set(propuesta.codigos)]
        unida = set(propuesta.codigos).union(*tocadas)
        componentes = [c for c in componentes if c not in tocadas] + [unida]
    return len(componentes)


def _recuento_propuestas(
    candidatos: tuple[Candidato, ...], propuestas: tuple[Propuesta, ...]
) -> RecuentoPropuestas:
    por_motivo = Counter(m for p in propuestas for par in p.pares for m in par.motivos)
    sueltos = sum(1 for p in propuestas if p.por_pares)
    return RecuentoPropuestas(
        candidatos=len({c.codigo for c in candidatos}),
        propuestas=len(propuestas),
        grupos_enteros=len(propuestas) - sueltos,
        pares_sueltos=sueltos,
        pares_por_motivo={m.value: por_motivo[m] for m in Motivo},
        propuestas_por_tamano=dict(
            sorted(Counter(len(p.codigos) for p in propuestas).items())
        ),
        componentes_no_clique=_componentes_no_clique(propuestas),
    )


def _confirmar_todo(propuestas: Iterable[Propuesta]) -> tuple[DecisionPar, ...]:
    """Las decisiones que habría si una persona dijera «son el mismo» a todo."""
    return tuple(
        DecisionPar(
            catalogo=Catalogo.OFICIO,
            codigo_a=par.codigo_a,
            codigo_b=par.codigo_b,
            decision=MISMO,
            motivos=par.motivos,
            obra_codigo="medicion",
            decidido_por="medicion",
            decidido_at_utc=_CUANDO,
        )
        for propuesta in propuestas
        for par in propuesta.pares
    )


def _recuento_plantilla(
    catalogo: CatalogoObra, decisiones: tuple[DecisionPar, ...]
) -> RecuentoPlantilla:
    uso = Counter(f.oficio_codigo for f in catalogo.proveedores)
    grupos = grupos_vigentes(
        (Candidato(o.codigo, o.nombre) for o in catalogo.oficios),
        decisiones,
        OFICIO,
        uso,
    )
    oficios = opciones_de_oficio(catalogo, grupos)
    proveedores = grupos_de_proveedor(
        Candidato(f.proveedor_codigo, f.proveedor_nombre)
        for f in catalogo.proveedores
        if f.proveedor_codigo is not None
    )
    pares = opciones_de_proveedor(catalogo, proveedores, oficios)
    pares_de = Counter(p.oficio for p in pares)
    rellenables = 0
    for par in pares:
        if pares_de[par.oficio] == 1:
            oficio, _ = resolver_oficio_y_proveedor(par.oficio, par)
            rellenables += not oficio.ambiguo  # type: ignore[union-attr]
    return RecuentoPlantilla(
        opciones_oficio=len(oficios),
        oficios_ambiguos=sum(1 for o in oficios if len(o.codigos_en_obra) > 1),
        pares_proveedor=len(pares),
        oficios_que_r91_rellenaria=rellenables,
        oficios_sin_proveedor=sum(1 for o in oficios if pares_de[o] == 0),
    )


def medir(datos: Mapping) -> Medicion:
    """Todos los recuentos a partir del JSON de T2 ya leído."""
    catalogo = _catalogo_obra(datos)
    en_obra = tuple(Candidato(o.codigo, o.nombre) for o in catalogo.oficios)
    en_auxofc = tuple(
        Candidato(f["codigo"], f["nombre"]) for f in datos["oficios_catalogo"]
    )
    propuestas_obra = proponer_grupos(en_obra, (), OFICIO)
    propuestas_auxofc = proponer_grupos(en_auxofc, (), OFICIO)
    return Medicion(
        oficios_obra=len(catalogo.oficios),
        filas_obrofc=len(catalogo.proveedores),
        filas_sin_proveedor=sum(
            1 for f in catalogo.proveedores if f.proveedor_codigo is None
        ),
        obra=_recuento_propuestas(en_obra, propuestas_obra),
        catalogo=_recuento_propuestas(en_auxofc, propuestas_auxofc),
        plantilla_sin_grupos=_recuento_plantilla(catalogo, ()),
        plantilla_con_obra=_recuento_plantilla(
            catalogo, _confirmar_todo(propuestas_obra)
        ),
        plantilla_con_catalogo=_recuento_plantilla(
            catalogo, _confirmar_todo(propuestas_auxofc)
        ),
    )


def _lineas_propuestas(titulo: str, r: RecuentoPropuestas) -> list[str]:
    motivos = ", ".join(f"{m} {n}" for m, n in r.pares_por_motivo.items())
    tamanos = ", ".join(f"{t} códigos: {n}" for t, n in r.propuestas_por_tamano.items())
    return [
        f"[{titulo}]",
        f"  candidatos: {r.candidatos}",
        (
            f"  propuestas: {r.propuestas} (grupos enteros: {r.grupos_enteros}, "
            f"pares sueltos: {r.pares_sueltos})"
        ),
        f"  pares propuestos por motivo: {motivos}",
        f"  propuestas por tamaño: {tamanos or 'ninguna'}",
        f"  componentes que no son clique: {r.componentes_no_clique}",
    ]


def _lineas_plantilla(titulo: str, r: RecuentoPlantilla) -> list[str]:
    return [
        f"[Plantilla de la obra · {titulo}]",
        f"  opciones de Oficio: {r.opciones_oficio}",
        (
            "  grupos con más de un código en la obra (futuros oficio_ambiguo): "
            f"{r.oficios_ambiguos}"
        ),
        f"  pares de la columna Proveedor: {r.pares_proveedor}",
        (
            "  oficios con un solo proveedor que resuelve (R91 los rellenaría): "
            f"{r.oficios_que_r91_rellenaria}"
        ),
        f"  oficios sin ningún proveedor en obrofc: {r.oficios_sin_proveedor}",
    ]


def formatear(m: Medicion) -> str:
    """El informe en texto: solo recuentos, sin nombres ni códigos."""
    lineas = [
        "Oficios casi duplicados (F-036 T8) · solo recuentos",
        (
            f"Obra: {m.oficios_obra} oficios, {m.filas_obrofc} filas de obrofc "
            f"({m.filas_sin_proveedor} sin proveedor)"
        ),
        "",
        *_lineas_propuestas("Oficios de la obra", m.obra),
        "",
        *_lineas_propuestas("Todo auxofc", m.catalogo),
        "",
        *_lineas_plantilla("sin grupos", m.plantilla_sin_grupos),
        "",
        *_lineas_plantilla(
            "con todo lo propuesto en la obra confirmado", m.plantilla_con_obra
        ),
        "",
        *_lineas_plantilla(
            "con todo lo propuesto en auxofc confirmado", m.plantilla_con_catalogo
        ),
    ]
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(
        description="Recuentos de oficios casi duplicados sobre el JSON de T2 (F-036 T8)."
    )
    analizador.add_argument(
        "--catalogo", required=True, help="JSON de T2, fuera del repo"
    )
    opciones = analizador.parse_args(argv)
    try:
        datos = json.loads(Path(opciones.catalogo).read_text(encoding="utf-8-sig"))
    except OSError:
        print("ERROR: no se puede leer el JSON del catálogo.", file=sys.stderr)
        return 2
    print(formatear(medir(datos)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
