# services/postventa-api/tests/test_f072_volcado.py
"""El tipo del parte que va a Sigrid (F-072 T1, Bloque 1): `domain/models/volcado.py`.

`specs/F-072-tipo-reclamacion-sigrid/design.md` §4.3: dominio puro, sin red,
sin base y sin IA.

| Caso | Requisito |
|---|---|
| `parte_de` y `cuerpo_de_parte` llevan el tipo guardado | R28 |
| sin tipo guardado (anterior a F-072), `0002`, con cualquier `listado` | R28, R19 |
| `TIPO_RECLAMACION` sigue siendo `"0002"` y es el defecto del dominio | R28, §4.3 |
| una candidata anterior a F-072 sigue con la huella intacta | R26, §4.3 |
| un `tipo_no_valido` de la pasarela, en el ensayo y en el volcado: `rechazado` con su motivo | R29 (Bloque 6) |
| el volcado no lee los tipos: ni parámetro, ni fábrica, ni `auxtrcp` | R29 (Bloque 6) |

Los de R29 (T18) recorren la aplicación del volcado con los dobles en memoria
de F-059 (`tests/utiles_volcado.py`): sin red, sin base y sin IA.

Datos ficticios: obra `9901`, tipos `9001`…, proveedores `EJ07`; los
identificadores, `UUID(int=n)`.
"""

from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from application.pipelines import volcado as pipeline_volcado
from application.pipelines.volcado import (
    AjustesDelVolcado,
    PeticionDeEnsayo,
    PeticionDeVolcado,
)
from domain.models.plantilla_incidencias import TIPO_RECLAMACION_POR_DEFECTO, Listado
from domain.models.revision import (
    CandidataAlVolcado,
    EstadoRevision,
    Quien,
    ValoresIncidencia,
    estado_de,
    huella_de_valores,
)
from domain.models.situacion_volcado import EstadoEvento
from domain.models.volcado import (
    TIPO_RECLAMACION,
    PedidaAlVolcado,
    cuerpo_de_lote,
    cuerpo_de_parte,
    huella_intacta,
    parte_de,
)
from domain.ports.catalogo_obra import LecturaCatalogo

from tests.utiles_revision import AHORA, OBRA, incidencia
from tests.utiles_volcado import (
    BASE,
    PasarelaFalsa,
    RevisionConVolcado,
    UsuariosEnMemoria,
    VolcadosEnMemoria,
    responde,
)

APROBADA_AT = datetime(2026, 10, 15, 9, 0, tzinfo=UTC)


def valores(**cambios: object) -> ValoresIncidencia:
    base: dict[str, object] = {
        "unidad_codigo": "9901.03VILLA 1.",
        "unidad_nombre": "Villa Ejemplo Uno",
        "ubicacion": "Baño",
        "descripcion": "Ejemplo de grieta junto a la ventana del salón",
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": "EJ07",
        "proveedor_nombre": "Carpintería Ejemplo, S.L.",
        "proveedor_ambiguo": False,
        "urgencia": None,
        "listado": None,
    }
    base.update(cambios)
    return ValoresIncidencia(**base)  # type: ignore[arg-type]


def candidata(v: ValoresIncidencia, n: int = 1) -> CandidataAlVolcado:
    return CandidataAlVolcado(
        incidencia_id=UUID(int=n),
        obra_codigo="9901",
        valores=v,
        huella=huella_de_valores(v),
        aprobada_at_utc=APROBADA_AT,
        revision_id=10 + n,
    )


def test_f072_r28_tipo_reclamacion_sigue_siendo_0002_y_es_el_defecto() -> None:
    assert TIPO_RECLAMACION == "0002"
    assert TIPO_RECLAMACION == TIPO_RECLAMACION_POR_DEFECTO


@pytest.mark.parametrize("codigo", ["9001", "9002", "0004"])
def test_f072_r28_el_parte_lleva_el_tipo_guardado(codigo: str) -> None:
    parte = parte_de(candidata(valores(tipo_reclamacion=codigo)))
    assert parte.tipo == codigo


@pytest.mark.parametrize("codigo", ["9001", "9003"])
def test_f072_r28_el_cuerpo_lleva_el_tipo_guardado(codigo: str) -> None:
    cuerpo = cuerpo_de_parte(parte_de(candidata(valores(tipo_reclamacion=codigo))))
    assert cuerpo["tipo"] == codigo


@pytest.mark.parametrize("listado", [None, Listado.PRIMERO, Listado.SEGUNDO])
def test_f072_r28_sin_tipo_guardado_el_parte_va_con_0002(
    listado: Listado | None,
) -> None:
    parte = parte_de(candidata(valores(listado=listado)))
    assert parte.tipo == "0002"
    assert cuerpo_de_parte(parte)["tipo"] == "0002"


def test_f072_r28_el_listado_heredado_no_pisa_el_tipo_guardado() -> None:
    v = valores(listado=Listado.SEGUNDO, tipo_reclamacion="9001")
    assert parte_de(candidata(v)).tipo == "9001"


def test_f072_r28_cada_parte_del_lote_lleva_su_tipo() -> None:
    partes = [
        parte_de(candidata(valores(tipo_reclamacion="9001"), n=1)),
        parte_de(candidata(valores(), n=2)),
        parte_de(candidata(valores(tipo_reclamacion="9002"), n=3)),
    ]
    lote = cuerpo_de_lote(
        partes, obra="9901", usu="login_ficticio", commit=False, base="base_ficticia"
    )
    assert [p["tipo"] for p in lote["partes"]] == ["9001", "0002", "9002"]


def test_f072_r26_una_candidata_anterior_a_f072_sigue_intacta() -> None:
    c = candidata(valores())
    assert huella_intacta(c)
    assert parte_de(c).tipo == "0002"


def test_f072_r26_una_candidata_con_tipo_sigue_intacta() -> None:
    assert huella_intacta(candidata(valores(tipo_reclamacion="9001")))


# --------------------------------------------------------------------------
# R29 · el volcado no lee `auxtrcp`: un tipo de baja lo rechaza la pasarela
# --------------------------------------------------------------------------

_RAIZ = Path(__file__).resolve().parents[1]

#: Los ficheros del volcado (F-059): ninguno lee los tipos de reclamación.
_DEL_VOLCADO = (
    "application/pipelines/volcado.py",
    "domain/models/volcado.py",
    "interface_adapters/api/volcado.py",
)

QUIEN = Quien(oid="oid-de-prueba-del-volcado", correo="persona.revisora@ejemplo.invalid")
DE_BAJA = "9009"  # vigente al aprobar, de baja al mandar


class _SinReclamacionesEnSigrid:
    """La guarda de F-065 sin ninguna reclamación en Sigrid (como en F-059)."""

    def leer(self, *, codigo_obra: str, tip: int, unidades: Any = None) -> LecturaCatalogo:
        return LecturaCatalogo((), False)


class _Volcado:
    """La aplicación del volcado con los dobles de F-059 y una lista común."""

    def __init__(self) -> None:
        self.llamadas: list[str] = []
        self.revision = RevisionConVolcado(self.llamadas, (incidencia(1),))
        self.volcados = VolcadosEnMemoria(self.llamadas, self.revision)
        self.sigrid = PasarelaFalsa(self.llamadas, self.volcados)
        self.usuarios = UsuariosEnMemoria(self.llamadas)
        self._ids = iter(UUID(int=600_000 + i) for i in range(100))
        self.revision_id = self.revision.aprobar(1, tipo_reclamacion=DE_BAJA)

    def puertos(self) -> dict[str, Any]:
        return {
            "revision": self.revision,
            "volcados": self.volcados,
            "usuarios": self.usuarios,
            "sigrid": self.sigrid,
            "ajustes_volcado": AjustesDelVolcado(partes_por_llamada=5, base_datos=BASE),
            "nuevo_id": lambda: next(self._ids),
        }

    def ensayar(self):
        return pipeline_volcado.ensayar(
            PeticionDeEnsayo(obra_codigo=OBRA, quien=QUIEN, incidencias=(UUID(int=1),)),
            ahora=AHORA,
            reclamaciones=_SinReclamacionesEnSigrid(),
            tip=708,
            **self.puertos(),
        )

    def volcar(self, ensayo_id: UUID):
        return pipeline_volcado.volcar(
            PeticionDeVolcado(
                obra_codigo=OBRA,
                ensayo_id=ensayo_id,
                quien=QUIEN,
                pedidas=(PedidaAlVolcado(UUID(int=1), self.revision_id),),
            ),
            ahora=AHORA + timedelta(minutes=5),
            **self.puertos(),
        )

    def estado(self) -> EstadoRevision:
        return estado_de(self.revision.situacion(incidencia_id=UUID(int=1)))


def test_f072_r29_el_ensayo_manda_el_tipo_guardado_y_el_tipo_no_valido_sale_rechazado() -> None:
    mundo = _Volcado()
    mundo.sigrid.al_ensayar = responde(["rechazado"], motivo="tipo_no_valido")

    resultado = mundo.ensayar()

    assert [p["tipo"] for p in mundo.sigrid.ensayados[0]["partes"]] == [DE_BAJA]
    assert [(p.resultado.estado, p.resultado.motivo) for p in resultado.partes] == [
        (EstadoEvento.RECHAZADO, "tipo_no_valido")
    ]
    assert resultado.resumen["rechazados"] == 1
    assert mundo.estado() is EstadoRevision.APROBADA
    assert mundo.sigrid.volcados_mandados == []


def test_f072_r29_en_el_volcado_el_tipo_no_valido_es_un_rechazo_mas() -> None:
    mundo = _Volcado()
    ensayo = mundo.ensayar()
    mundo.sigrid.al_volcar = responde(["rechazado"], motivo="tipo_no_valido")

    resultado = mundo.volcar(ensayo.ensayo_id)

    assert [p["tipo"] for p in mundo.sigrid.volcados_mandados[0]["partes"]] == [DE_BAJA]
    assert [(p.resultado.estado, p.resultado.motivo) for p in resultado.partes] == [
        (EstadoEvento.RECHAZADO, "tipo_no_valido")
    ]
    assert mundo.estado() is EstadoRevision.APROBADA


def test_f072_r29_ninguna_llamada_del_volcado_lee_los_tipos() -> None:
    mundo = _Volcado()
    ensayo = mundo.ensayar()
    mundo.volcar(ensayo.ensayo_id)

    assert mundo.llamadas
    assert not [c for c in mundo.llamadas if "tipo" in c]


@pytest.mark.parametrize("funcion", ["ensayar", "volcar", "panel_de_volcado"])
def test_f072_r29_la_aplicacion_del_volcado_no_recibe_los_tipos(funcion: str) -> None:
    parametros = inspect.signature(getattr(pipeline_volcado, funcion)).parameters
    assert not [p for p in parametros if "tipo" in p]


@pytest.mark.parametrize("ruta", _DEL_VOLCADO)
def test_f072_r29_el_volcado_no_lee_auxtrcp(ruta: str) -> None:
    texto = (_RAIZ / ruta).read_text(encoding="utf-8")
    for prohibido in (
        "auxtrcp",
        "tipos_reclamacion",
        "construir_tipos_reclamacion",
        "FuenteTiposReclamacion",
        "TiposReclamacionPort",
    ):
        assert prohibido not in texto, f"{ruta} menciona {prohibido!r}"
