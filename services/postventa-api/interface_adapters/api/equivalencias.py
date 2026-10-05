# services/postventa-api/interface_adapters/api/equivalencias.py
"""Handlers de `/api/catalogos/propuestas` y `/api/catalogos/decisiones` (F-036).

`specs/F-036-importar-excel/design.md` §8 y §15.5, R87 y R88. Aquí se
**componen los adaptadores** —el catálogo de Sigrid y las decisiones de
equivalencia— y se llama a `application/pipelines/equivalencias.py`; los
puertos inyectables son la costura de test. Las rutas se llaman `catalogos`
porque son el punto de entrada que reutilizarán F-050 y F-039, pero en F-036
el único catálogo es **`oficio`** (quinta enmienda).

## `GET /api/catalogos/propuestas?obra=`

La obra se normaliza **antes** de construir nada (R9 → 400). Responde
`{obra, oficio: {oficios, grupos, propuestas, avisos}}`: los oficios de la obra
con los códigos de su grupo vigente, los grupos con su etiqueta (R86), las
propuestas pendientes con sus motivos (R78, R79, R85) y las componentes que no
se aplican por contradicción (R82). No hay clave `proveedor`: esa agrupación es
de F-050.

## `POST /api/catalogos/decisiones`

Cuerpo `{obra, usuario_oid, confirmado: true, decisiones: [{catalogo, codigos,
decision}]}`. **Todo** lo que se puede mirar sin Sigrid se mira antes de
construir ningún adaptador, y es `PeticionDeDecisionInvalida` (→ 400):

1. el cuerpo es un objeto JSON;
2. `confirmado` es el booleano `true` de JSON —ni `"true"` ni `1`—, como en
   `POST /api/estado`: una decisión que cambia en qué oficio se da de alta una
   incidencia no sale de un cliente que serializa mal;
3. la obra es admisible (`CodigoDeObraInvalido`, R9);
4. `usuario_oid` es un texto de 1 a 128 caracteres (se guarda recortado; el
   motivo no lo repite);
5. `decisiones` es una lista no vacía de objetos, cada uno con un `catalogo`
   **disponible** (solo `oficio`: cualquier otro es «no disponible en esta
   versión»), una lista de códigos y `mismo` o `distinto` (las reglas de
   `DecisionPedida`), y ningún par dos veces.

Después, la aplicación comprueba contra Sigrid que todos los códigos son
oficios de la obra (→ 409) y registra en una transacción. Responde
`{obra, pares_guardados, grupos_vigentes: {oficio: {grupos, avisos}}}`.

Ninguno de los dos mira ninguna ventana de escritura del servicio (R48):
leer Sigrid y escribir en el esquema propio no abren nada ajeno.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from application.pipelines.equivalencias import (
    DecisionPedida,
    PeticionDeDecisiones,
    catalogo_disponible,
    exigir_peticion_decidible,
    propuestas_de_oficios,
    registrar_decisiones,
)
from config.settings import obtener_ajustes
from domain.models.equivalencias import DecisionPar, GruposVigentes, Propuesta
from domain.models.errores import PeticionDeDecisionInvalida
from domain.models.plantilla_incidencias import normalizar_codigo_obra
from domain.ports.catalogo_obra import CatalogoObraPort
from domain.ports.equivalencias import EquivalenciasPort
from infrastructure.persistencia.fabrica import construir_equivalencias
from infrastructure.sigrid.fabrica import construir_catalogo_obra

from interface_adapters.api.importar import MAX_USUARIO_OID

__all__ = ["decidir_equivalencias", "leer_propuestas"]


def _puertos(
    catalogo_obra: CatalogoObraPort | None, equivalencias: EquivalenciasPort | None
) -> tuple[CatalogoObraPort, EquivalenciasPort]:
    """Los adaptadores que no se inyectan, Sigrid primero (su puerta no abre nada)."""
    if catalogo_obra is None:
        catalogo_obra = construir_catalogo_obra(obtener_ajustes())
    if equivalencias is None:
        equivalencias = construir_equivalencias(obtener_ajustes())
    return catalogo_obra, equivalencias


def leer_propuestas(
    obra: Any,
    *,
    catalogo_obra: CatalogoObraPort | None = None,
    equivalencias: EquivalenciasPort | None = None,
) -> dict[str, Any]:
    """Las propuestas de oficios de la obra (R87)."""
    codigo = normalizar_codigo_obra(obra)
    catalogo_obra, equivalencias = _puertos(catalogo_obra, equivalencias)
    resultado = propuestas_de_oficios(
        codigo, catalogo_obra=catalogo_obra, equivalencias=equivalencias
    )
    grupos = resultado.grupos
    return {
        "obra": resultado.obra_codigo,
        "oficio": {
            "oficios": [
                {
                    "codigo": o.codigo,
                    "nombre": o.nombre,
                    "grupo": sorted(grupos.grupo_de(o.codigo).codigos),
                }
                for o in resultado.oficios
            ],
            **_grupos(grupos),
            "propuestas": [_propuesta(p) for p in resultado.propuestas],
        },
    }


def decidir_equivalencias(
    cuerpo: Any,
    *,
    catalogo_obra: CatalogoObraPort | None = None,
    equivalencias: EquivalenciasPort | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]:
    """Registra las decisiones del cuerpo (R88) y devuelve lo guardado."""
    peticion = _peticion(cuerpo)
    exigir_peticion_decidible(peticion)
    catalogo_obra, equivalencias = _puertos(catalogo_obra, equivalencias)
    resultado = registrar_decisiones(
        peticion,
        catalogo_obra=catalogo_obra,
        equivalencias=equivalencias,
        ahora=ahora if ahora is not None else datetime.now(UTC),
    )
    return {
        "obra": resultado.obra_codigo,
        "pares_guardados": [_par(p) for p in resultado.pares],
        "grupos_vigentes": {resultado.grupos.catalogo.value: _grupos(resultado.grupos)},
    }


# --- el cuerpo de la decisión -----------------------------------------------------


def _peticion(cuerpo: Any) -> PeticionDeDecisiones:
    """El cuerpo, comprobado entero sin tocar Sigrid ni la base (→ 400)."""
    if not isinstance(cuerpo, dict):
        raise PeticionDeDecisionInvalida(
            "el cuerpo tiene que ser un objeto JSON con 'obra', 'usuario_oid', "
            "'confirmado' y 'decisiones'"
        )
    if cuerpo.get("confirmado") is not True:
        raise PeticionDeDecisionInvalida(
            "el cuerpo no trae 'confirmado': true — decidir que dos oficios son "
            "el mismo o no lo son es un acto explícito, y se confirma con el "
            "booleano de JSON"
        )
    obra = normalizar_codigo_obra(cuerpo.get("obra"))
    oid = _usuario_oid(cuerpo.get("usuario_oid"))
    crudas = cuerpo.get("decisiones")
    if not isinstance(crudas, list) or not crudas:
        raise PeticionDeDecisionInvalida(
            "'decisiones' tiene que ser una lista con al menos una decisión"
        )
    return PeticionDeDecisiones(
        obra_codigo=obra,
        usuario_oid=oid,
        decisiones=tuple(_decision(cruda) for cruda in crudas),
    )


def _usuario_oid(crudo: Any) -> str:
    """El `oid` de quien decide, recortado, o 400 sin repetirlo (R47)."""
    oid = crudo.strip() if isinstance(crudo, str) else ""
    if not oid or len(oid) > MAX_USUARIO_OID:
        raise PeticionDeDecisionInvalida(
            f"falta 'usuario_oid' o no es un texto de 1 a {MAX_USUARIO_OID} "
            "caracteres: hace falta saber quién decide"
        )
    return oid


def _decision(cruda: Any) -> DecisionPedida:
    """Una decisión del cuerpo; las reglas de forma son las de `DecisionPedida`."""
    if not isinstance(cruda, dict):
        raise PeticionDeDecisionInvalida(
            "cada decisión es un objeto con 'catalogo', 'codigos' y 'decision'"
        )
    codigos = cruda.get("codigos")
    if not isinstance(codigos, list):
        raise PeticionDeDecisionInvalida("'codigos' tiene que ser una lista de códigos")
    return DecisionPedida(
        catalogo=catalogo_disponible(cruda.get("catalogo")),
        codigos=tuple(codigos),
        decision=cruda.get("decision"),
    )


# --- la respuesta -----------------------------------------------------------------


def _grupos(grupos: GruposVigentes) -> dict[str, Any]:
    return {
        "grupos": [
            {"etiqueta": g.etiqueta, "codigos": sorted(g.codigos)}
            for g in grupos.grupos
        ],
        "avisos": [{"codigos": sorted(c)} for c in grupos.no_aplicados],
    }


def _propuesta(propuesta: Propuesta) -> dict[str, Any]:
    return {
        "codigos": list(propuesta.codigos),
        "por_pares": propuesta.por_pares,
        "motivos": sorted(m.value for m in propuesta.motivos),
        "pares": [
            {
                "codigo_a": p.codigo_a,
                "codigo_b": p.codigo_b,
                "motivos": sorted(m.value for m in p.motivos),
            }
            for p in propuesta.pares
        ],
    }


def _par(par: DecisionPar) -> dict[str, Any]:
    return {
        "catalogo": par.catalogo.value,
        "codigo_a": par.codigo_a,
        "codigo_b": par.codigo_b,
        "decision": par.decision,
        "motivos": sorted(m.value for m in par.motivos),
    }
