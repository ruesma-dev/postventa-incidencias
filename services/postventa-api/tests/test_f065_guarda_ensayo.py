# services/postventa-api/tests/test_f065_guarda_ensayo.py
"""La guarda del ensayo: sincronizar antes de registrar (F-065, T15; R43–R49).

`specs/F-065-revision-sigrid-backend/design.md` §15.3–§15.7. El ensayo de F-059
(`POST /api/volcado/ensayo`) vuelve a mirar Sigrid **antes** del login y del
lote: lee las reclamaciones de la obra **solo de las unidades de lo que se va
a mandar**, sin datos personales; da a cada incidencia el veredicto de R41
(la misma función del dominio que la ruta de F-065) y excluye lo que ya existe
y lo que choca sin confirmar.

| Caso | Requisito |
|---|---|
| `conflictos_confirmados`: opcional, de objetos con exactamente `incidencia_id` (en `incidencias`, sin repetir) y `sigrid_cods` (1 a 50 códigos `RS…` distintos); si no, 400 **sin construir nada** y sin repetir lo recibido; `confirmado` y `commit` siguen siendo 400 | R43 |
| el orden: selección → Sigrid → login → lote; **sin** Sigrid si la selección no deja nada; solo las unidades de lo que se manda, por marcador | R44 |
| `ya_existe` → `duplicada_en_sigrid`; `choca` sin confirmar, a medias o con una reclamación nueva → `conflicto_sin_confirmar`; confirmada, se manda; la `NPR` emparejada, igual; la confirmación sobrante se ignora | R45 |
| Sigrid caída, `truncated` o al techo, dos obras: 503/409 **sin login, sin lote y sin ensayo guardado** | R46 |
| el bloque `sigrid`; `null` sin lectura; las claves de R12 de F-059 no cambian | R47 |
| una línea `F-065 guarda del ensayo` por lectura, sin códigos `RS` ni textos; y una por confirmada | R48 |
| sin la clave y sin nada que choque, lo mismo que hoy más `sigrid`; el veredicto del ensayo es el de la ruta | R49 |
| `veredictos` con las situaciones en el **orden pedido** (O-A4b-3) | R41, R47 |

Con dobles en memoria (`tests/utiles_volcado.py` y un lector de
reclamaciones propio): sin red, sin base y sin IA. Datos inventados (R39):
obra `9901`, unidades `9901.03VILLA n.`, códigos `RS…` de los ejemplos
ficticios de §5.4, textos «Ejemplo …»; los identificadores, `UUID(int=n)`.
"""

from __future__ import annotations

import inspect
import logging
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

import pytest
from application.pipelines import guarda_sigrid
from application.pipelines import volcado as pipeline
from application.pipelines.guarda_sigrid import (
    GuardaDelEnsayo,
    VeredictoDeLaGuarda,
    aplicar_guarda_de_sigrid,
)
from application.pipelines.volcado import AjustesDelVolcado, PeticionDeEnsayo
from domain.models.errores import (
    CatalogoNoDisponible,
    EnsayoSinRespuesta,
    ObraAmbigua,
    ReclamacionesSinVerificar,
)
from domain.models.revision import Quien
from domain.models.sigrid_bandeja import ReclamacionSigrid, Veredicto, cruzar, veredictos
from domain.models.situacion_volcado import EstadoEvento
from domain.models.volcado import MotivoExclusion
from domain.ports.catalogo_obra import LecturaCatalogo
from domain.ports.reclamaciones_obra import FilaReclamacionObra
from domain.ports.volcado import FamiliaDeRespuesta
from interface_adapters.api import volcado as modulo

from tests.test_f059_volcado_http import Mundo as MundoDelBorde
from tests.test_f059_volcado_http import _componer, _cuerpo_ensayo, _ensayo, _leer, _texto
from tests.utiles_revision import AHORA, CORREO, DESCRIPCION, OBRA, OID, U1, U2, U3, incidencia, prohibido
from tests.utiles_volcado import (
    BASE,
    PasarelaFalsa,
    RevisionConVolcado,
    UsuariosEnMemoria,
    VolcadosEnMemoria,
    responde_familia,
)

V = Veredicto
MX = MotivoExclusion
EV = EstadoEvento

TIP = 708
QUIEN = Quien(oid=OID, correo=CORREO)
AJUSTES = AjustesDelVolcado(partes_por_llamada=5, base_datos=BASE)
#: `upv.obride` inventados: solo sirven para contar obras (R9).
OBRA_REF = "7000123"
OTRA_OBRA_REF = "7000456"

#: Las claves de R12 de F-059, tal y como eran: R47 solo añade `sigrid`.
CLAVES_DE_R12 = {"ensayo_id", "obra", "caduca_at_utc", "resumen", "partes", "excluidas"}
CLAVES_DEL_RESUMEN = ["previstos", "idempotentes", "rechazados", "no_procesados", "excluidas"]
CLAVES_DE_SIGRID = {"leido_at_utc", "reclamaciones_leidas", "veredictos"}
CLAVES_DE_VEREDICTO = {"incidencia_id", "veredicto", "sigrid_cods", "confirmada"}

#: Lo que **no** puede ir a una línea de la guarda (R48): códigos `RS`, textos
#: de Sigrid y de la bandeja, unidades, ubicaciones, la persona.
TEXTO_DE_SIGRID = "Ejemplo de reclamacion secreta de Sigrid"
UBICACION_DE_SIGRID = "Ejemplo Ubicacion Secreta"


def ID(n: int) -> UUID:
    return UUID(int=n)


def pvi(n: int) -> str:
    return f"PVI-{UUID(int=n)}"


# --------------------------------------------------------------------------
# Los datos: filas de la guarda (12 columnas, sin ficha)
# --------------------------------------------------------------------------


def fila(
    cod: str,
    estado: str | None = "SAT",
    *,
    unidad: str = U1,
    ubicacion: str | None = "Baño",
    oficio: str | None = "0046",
    descripcion: str | None = DESCRIPCION,
    referencia: str | None = None,
    fecha: date | None = date(2026, 9, 15),
    obra_ref: str = OBRA_REF,
) -> FilaReclamacionObra:
    """Una fila de la lectura de la guarda. Por defecto, la misma unidad,
    oficio, ubicación y descripción que `incidencia(n)`: los dos criterios."""
    return FilaReclamacionObra(
        obra_ref=obra_ref,
        cod=cod,
        estado_codigo=estado,
        fecha=fecha,
        unidad_codigo=unidad,
        oficio_codigo=oficio,
        oficio_nombre="Ejemplo de oficio",
        tipo_codigo="GAR",
        tipo_nombre="Ejemplo de tipo",
        ubicacion=ubicacion,
        descripcion=descripcion,
        referencia=referencia,
        ficha=None,
    )


def ya_existe(cod: str, **cambios: Any) -> FilaReclamacionObra:
    """Los dos criterios con una abierta (R41, regla 2)."""
    return fila(cod, "SAT", **cambios)


def choca(cod: str, **cambios: Any) -> FilaReclamacionObra:
    """Solo la descripción, con una abierta (R41, regla 3)."""
    return fila(cod, "PTE", ubicacion=UBICACION_DE_SIGRID, oficio="0099", **cambios)


def emparejada(cod: str, n: int, estado: str = "SAT", **cambios: Any) -> FilaReclamacionObra:
    """La de `PVI-<n>`, sin nada en común con la incidencia (R41, reglas 0 y 1)."""
    return fila(
        cod, estado, ubicacion="Patio", oficio="0098", descripcion=TEXTO_DE_SIGRID, referencia=pvi(n), **cambios
    )


# --------------------------------------------------------------------------
# Los dobles
# --------------------------------------------------------------------------


class LectorDeLaGuarda:
    """Un `ReclamacionesObraPort` de mentira para la guarda: anota cada lectura
    en la lista común (así se ve el orden de R44) y lo que se le pidió."""

    def __init__(
        self,
        llamadas: list[str],
        filas: tuple[FilaReclamacionObra, ...] = (),
        *,
        al_techo: bool = False,
        fallo: Exception | None = None,
    ) -> None:
        self.llamadas = llamadas
        self.filas = filas
        self.al_techo = al_techo
        self.fallo = fallo
        self.pedidas: list[dict[str, Any]] = []

    def leer(
        self, *, codigo_obra: str, tip: int, unidades: Any = None
    ) -> LecturaCatalogo[FilaReclamacionObra]:
        self.llamadas.append("sigrid.reclamaciones")
        self.pedidas.append({"codigo_obra": codigo_obra, "tip": tip, "unidades": unidades})
        if self.fallo is not None:
            raise self.fallo
        return LecturaCatalogo(self.filas, self.al_techo)


class Mundo:
    """El ensayo de F-059 con sus dobles, y el lector de la guarda."""

    def __init__(self, *ns: int, **unidades: str) -> None:
        self.llamadas: list[str] = []
        incidencias = tuple(incidencia(n, unidad_codigo=unidades.get(f"u{n}", U1)) for n in ns)
        self.revision = RevisionConVolcado(self.llamadas, incidencias)
        self.volcados = VolcadosEnMemoria(self.llamadas, self.revision)
        self.sigrid = PasarelaFalsa(self.llamadas, self.volcados)
        self.usuarios = UsuariosEnMemoria(self.llamadas)
        self.lector = LectorDeLaGuarda(self.llamadas)
        self._ids = iter(UUID(int=500_000 + i) for i in range(1_000))

    def nuevo_id(self) -> UUID:
        return next(self._ids)

    def aprobar(self, *ns: int) -> None:
        for n in ns:
            self.revision.aprobar(n)

    def con(self, *filas: FilaReclamacionObra, **lector: Any) -> Mundo:
        self.lector.filas = filas
        for nombre, valor in lector.items():
            setattr(self.lector, nombre, valor)
        return self

    def ensayar(self, *ns: int, confirmados: dict[int, tuple[str, ...]] | None = None, tip: int = TIP):
        return pipeline.ensayar(
            PeticionDeEnsayo(
                obra_codigo=OBRA,
                quien=QUIEN,
                incidencias=tuple(ID(n) for n in ns),
                conflictos_confirmados={ID(n): frozenset(c) for n, c in (confirmados or {}).items()},
            ),
            revision=self.revision,
            volcados=self.volcados,
            usuarios=self.usuarios,
            sigrid=self.sigrid,
            reclamaciones=self.lector,
            tip=tip,
            ajustes_volcado=AJUSTES,
            ahora=AHORA,
            nuevo_id=self.nuevo_id,
        )

    def mandadas(self) -> list[UUID]:
        """Las incidencias del lote que llegó a la pasarela (una sola llamada)."""
        (lote,) = self.sigrid.ensayados
        return [UUID(p["referencia_externa"].removeprefix("PVI-")) for p in lote["partes"]]


def _aprobadas(*ns: int, **unidades: str) -> Mundo:
    mundo = Mundo(*ns, **unidades)
    mundo.aprobar(*ns)
    return mundo


def _excluidas(resultado) -> list[tuple[UUID, MotivoExclusion, str | None]]:
    return [(e.incidencia_id, e.motivo, e.sigrid_cod) for e in resultado.excluidas]


def _veredictos(resultado) -> list[tuple[UUID, Veredicto, tuple[str, ...], bool]]:
    return [(v.incidencia_id, v.veredicto, v.sigrid_cods, v.confirmada) for v in resultado.guarda.veredictos]


# ==========================================================================
# Los tipos y las firmas (§15.6)
# ==========================================================================


def test_f065_r45_los_dos_motivos_nuevos_al_final_de_los_de_f059() -> None:
    assert [m.value for m in MotivoExclusion][-2:] == ["duplicada_en_sigrid", "conflicto_sin_confirmar"]
    assert (MX.DUPLICADA_EN_SIGRID.value, MX.CONFLICTO_SIN_CONFIRMAR.value) == (
        "duplicada_en_sigrid",
        "conflicto_sin_confirmar",
    )


def test_f065_r43_la_peticion_sin_confirmaciones_es_un_mapa_vacio() -> None:
    peticion = PeticionDeEnsayo(obra_codigo=OBRA, quien=QUIEN, incidencias=(ID(1),))

    assert dict(peticion.conflictos_confirmados) == {}


def test_f065_r46_la_guarda_no_tiene_interruptor() -> None:
    """R46/R28: `ensayar` exige el lector y el tipo; no hay forma de no pasarlos."""
    parametros = inspect.signature(pipeline.ensayar).parameters

    for nombre in ("reclamaciones", "tip"):
        assert parametros[nombre].kind is inspect.Parameter.KEYWORD_ONLY
        assert parametros[nombre].default is inspect.Parameter.empty


def test_f065_r47_el_resultado_sin_guarda_por_defecto() -> None:
    """`ResultadoDeEnsayo` gana `guarda`, al final y con `None` por defecto:
    lo que ya se construía sin ella se sigue construyendo igual."""
    resultado = pipeline.ResultadoDeEnsayo(OBRA, None, None, (), (), {})

    assert resultado.guarda is None


# ==========================================================================
# R44 · el orden y lo que se lee
# ==========================================================================


def test_f065_r44_seleccion_sigrid_login_y_lote_en_ese_orden() -> None:
    mundo = _aprobadas(1, 2)

    mundo.ensayar(1, 2)

    llamadas = mundo.llamadas
    assert llamadas.count("sigrid.reclamaciones") == 1
    leida = llamadas.index("sigrid.reclamaciones")
    ultima_situacion = max(i for i, c in enumerate(llamadas) if c == "revision.situacion")
    assert llamadas.index("revision.aprobadas") < ultima_situacion < leida
    assert leida < llamadas.index("usuarios.resolver_login") < llamadas.index("sigrid.ensayar")
    assert llamadas.index("sigrid.ensayar") < llamadas.index("volcados.guardar_ensayo")


def test_f065_r44_si_la_seleccion_no_deja_nada_no_se_lee_sigrid() -> None:
    """Como hoy no hay login: sin nada que mandar, tampoco hay guarda."""
    mundo = Mundo(1)  # sin aprobar: no es candidata

    resultado = mundo.ensayar(1, 77)

    assert "sigrid.reclamaciones" not in mundo.llamadas
    assert "usuarios.resolver_login" not in mundo.llamadas
    assert resultado.ensayo_id is None
    assert resultado.guarda is None
    assert [m for _, m, _ in _excluidas(resultado)] == [MX.NO_ES_CANDIDATA, MX.NO_ES_DE_LA_BANDEJA]


def test_f065_r44_lee_solo_las_unidades_de_lo_que_se_manda_una_vez_cada_una() -> None:
    """La 3 está volcada (fuera por la selección): su unidad no se lee. Las
    unidades, distintas y por código; la obra y el tipo, los de la petición."""
    mundo = _aprobadas(1, 2, 3, 4, u2=U2, u3=U3, u4=U2)
    mundo.volcados.sembrar(3, EV.CREADO, ide=700_003, cod="RS26.09/0003")

    mundo.ensayar(4, 3, 1, 2)

    assert mundo.lector.pedidas == [{"codigo_obra": OBRA, "tip": TIP, "unidades": (U1, U2)}]


def test_f065_r44_el_tipo_de_la_lectura_es_el_que_recibe_el_ensayo() -> None:
    """Con otro que el de por defecto (708): un tipo fijo no pasaría."""
    mundo = _aprobadas(1)

    mundo.ensayar(1, tip=709)

    assert [p["tip"] for p in mundo.lector.pedidas] == [709]


def test_f065_r44_las_unidades_son_las_vigentes_tal_cual() -> None:
    """Las de lo aprobado (las que cruza `cruzar`), sin recortar: `u.cod` se
    compara tal cual (R14)."""
    mundo = Mundo(1)
    mundo.revision.aprobar(1, unidad_codigo="9901.03VILLA 9.  ")

    mundo.ensayar(1)

    assert mundo.lector.pedidas[0]["unidades"] == ("9901.03VILLA 9.  ",)


def test_f065_r44_veredictos_con_las_situaciones_en_el_orden_pedido(monkeypatch) -> None:
    """O-A4b-3: la **misma** función del dominio, con las situaciones de lo que
    se manda en el orden pedido (R47)."""
    vistas: list[list[UUID]] = []

    def espia(situaciones, cruce):
        vistas.append([s.incidencia.incidencia_id for s in situaciones])
        return veredictos(situaciones, cruce)

    assert guarda_sigrid.veredictos is veredictos
    assert guarda_sigrid.cruzar is cruzar
    monkeypatch.setattr(guarda_sigrid, "veredictos", espia)
    mundo = _aprobadas(1, 2, 3)

    mundo.ensayar(3, 77, 1, 2)

    assert vistas == [[ID(3), ID(1), ID(2)]]


# ==========================================================================
# R45 · lo que se excluye y lo que se manda
# ==========================================================================


def test_f065_r45_ya_existe_se_excluye_como_duplicada_con_su_primer_codigo() -> None:
    mundo = _aprobadas(1, 2).con(
        ya_existe("RS26.09/0123", fecha=date(2026, 9, 1)), ya_existe("RS26.09/0130", fecha=date(2026, 9, 20))
    )

    resultado = mundo.ensayar(1)

    # Los dos casan con las dos (misma unidad, oficio, ubicación y texto):
    # el primer código en el orden de R18 es el más reciente.
    assert _excluidas(resultado) == [(ID(1), MX.DUPLICADA_EN_SIGRID, "RS26.09/0130")]
    assert resultado.ensayo_id is None
    assert "sigrid.ensayar" not in mundo.llamadas


def test_f065_r45_ya_existe_no_se_puede_confirmar() -> None:
    """§15.8: un `ya_existe` no tiene salida en el ensayo."""
    mundo = _aprobadas(1).con(ya_existe("RS26.09/0123"))

    resultado = mundo.ensayar(1, confirmados={1: ("RS26.09/0123",)})

    assert _excluidas(resultado) == [(ID(1), MX.DUPLICADA_EN_SIGRID, "RS26.09/0123")]
    assert resultado.guarda.confirmaciones_sobrantes == 1


def test_f065_r45_choca_sin_confirmar_se_excluye_con_su_primer_codigo() -> None:
    mundo = _aprobadas(1, 2).con(choca("RS26.09/0123"))

    resultado = mundo.ensayar(1, 2)

    assert _excluidas(resultado) == [
        (ID(1), MX.CONFLICTO_SIN_CONFIRMAR, "RS26.09/0123"),
        (ID(2), MX.CONFLICTO_SIN_CONFIRMAR, "RS26.09/0123"),
    ]
    assert resultado.ensayo_id is None
    assert "usuarios.resolver_login" not in mundo.llamadas


def test_f065_r45_choca_confirmada_se_manda() -> None:
    mundo = _aprobadas(1).con(choca("RS26.09/0123"), choca("RS26.09/0124", fecha=date(2026, 9, 1)))

    resultado = mundo.ensayar(1, confirmados={1: ("RS26.09/0124", "RS26.09/0123")})

    assert _excluidas(resultado) == []
    assert mundo.mandadas() == [ID(1)]
    assert _veredictos(resultado) == [(ID(1), V.CHOCA, ("RS26.09/0123", "RS26.09/0124"), True)]


def test_f065_r45_la_confirmacion_parcial_excluye_con_el_primer_codigo_sin_confirmar() -> None:
    mundo = _aprobadas(1).con(
        choca("RS26.09/0123", fecha=date(2026, 9, 20)),
        choca("RS26.09/0124", fecha=date(2026, 9, 10)),
        choca("RS26.09/0125", fecha=date(2026, 9, 1)),
    )

    resultado = mundo.ensayar(1, confirmados={1: ("RS26.09/0123",)})

    assert _excluidas(resultado) == [(ID(1), MX.CONFLICTO_SIN_CONFIRMAR, "RS26.09/0124")]
    assert _veredictos(resultado) == [
        (ID(1), V.CHOCA, ("RS26.09/0123", "RS26.09/0124", "RS26.09/0125"), False)
    ]


def test_f065_r45_la_que_aparecio_despues_de_confirmar_exige_confirmarla() -> None:
    """§15.4: se confirmó con lo que se vio; la que llegó después, también."""
    mundo = _aprobadas(1).con(choca("RS26.09/0123"), choca("RS26.10/0200", fecha=date(2026, 10, 7)))

    resultado = mundo.ensayar(1, confirmados={1: ("RS26.09/0123",)})

    assert _excluidas(resultado) == [(ID(1), MX.CONFLICTO_SIN_CONFIRMAR, "RS26.10/0200")]


def test_f065_r45_confirmar_de_mas_no_estorba() -> None:
    """Un código confirmado que ya no choca no cambia nada: los que chocan, todos confirmados."""
    mundo = _aprobadas(1).con(choca("RS26.09/0123"))

    resultado = mundo.ensayar(1, confirmados={1: ("RS26.09/0123", "RS26.09/0999")})

    assert mundo.mandadas() == [ID(1)]
    assert resultado.guarda.confirmaciones_sobrantes == 0


def test_f065_r45_la_confirmacion_de_una_que_ya_no_choca_se_ignora_y_se_cuenta() -> None:
    mundo = _aprobadas(1, 2).con(choca("RS26.09/0123", unidad=U2))

    resultado = mundo.ensayar(1, 2, confirmados={1: ("RS26.09/0123",), 2: ("RS26.09/0555",)})

    assert mundo.mandadas() == [ID(1), ID(2)]
    assert _veredictos(resultado) == [(ID(1), V.VA, (), False), (ID(2), V.VA, (), False)]
    assert resultado.guarda.confirmaciones_sobrantes == 2


def test_f065_r45_la_emparejada_en_npr_sin_confirmar_se_excluye_con_su_codigo() -> None:
    """Enmienda del humano a S-3: mandarla la dejaría enlazada a un parte anulado."""
    mundo = _aprobadas(1).con(emparejada("RS26.10/0080", 1, "NPR"), ya_existe("RS26.09/0123"))

    resultado = mundo.ensayar(1)

    assert _excluidas(resultado) == [(ID(1), MX.CONFLICTO_SIN_CONFIRMAR, "RS26.10/0080")]
    assert _veredictos(resultado) == [(ID(1), V.CHOCA, ("RS26.10/0080",), False)]


def test_f065_r45_la_emparejada_en_npr_confirmada_se_manda() -> None:
    mundo = _aprobadas(1).con(emparejada("RS26.10/0080", 1, "NPR"))

    resultado = mundo.ensayar(1, confirmados={1: ("RS26.10/0080",)})

    assert mundo.mandadas() == [ID(1)]
    assert _veredictos(resultado) == [(ID(1), V.CHOCA, ("RS26.10/0080",), True)]


def test_f065_r45_se_enlaza_y_va_se_mandan_en_el_orden_pedido() -> None:
    """S-3: la emparejada no anulada se manda (la pasarela no puede crear otro
    parte con esa referencia); `va` también, aunque case con una cerrada."""
    mundo = _aprobadas(1, 2, 3).con(
        emparejada("RS26.10/0081", 2),
        fila("RS23.06/0300", "CER", fecha=date(2023, 6, 1)),
    )

    resultado = mundo.ensayar(3, 2, 1)

    assert mundo.mandadas() == [ID(3), ID(2), ID(1)]
    assert _excluidas(resultado) == []
    assert _veredictos(resultado) == [
        (ID(3), V.VA, (), False),
        (ID(2), V.SE_ENLAZA, ("RS26.10/0081",), False),
        (ID(1), V.VA, (), False),
    ]


def test_f065_r45_mezcla_en_el_orden_pedido() -> None:
    """Tres mandadas y tres excluidas (una por la selección, dos por la guarda),
    cada lista en el orden pedido."""
    mundo = _aprobadas(1, 2, 3, 4, u2=U2, u3=U3, u4=U2).con(
        emparejada("RS26.10/0081", 2, unidad=U2),
        choca("RS26.09/0123", unidad=U3),
        ya_existe("RS26.09/0140", unidad=U2, oficio="0046", ubicacion="Baño"),
    )
    mundo.revision.aprobar(4, ubicacion="Ejemplo otra ubicacion", descripcion="Ejemplo de otra cosa del todo")

    resultado = mundo.ensayar(3, 77, 1, 2, 4)

    assert mundo.mandadas() == [ID(1), ID(2), ID(4)]
    assert _excluidas(resultado) == [
        (ID(3), MX.CONFLICTO_SIN_CONFIRMAR, "RS26.09/0123"),
        (ID(77), MX.NO_ES_DE_LA_BANDEJA, None),
    ]
    assert [v[:2] for v in _veredictos(resultado)] == [
        (ID(3), V.CHOCA),
        (ID(1), V.VA),
        (ID(2), V.SE_ENLAZA),
        (ID(4), V.VA),
    ]


def test_f065_r45_si_tras_la_guarda_no_queda_nada_es_el_nada_que_mandar_de_f059() -> None:
    mundo = _aprobadas(1, 2).con(ya_existe("RS26.09/0123"))

    resultado = mundo.ensayar(1, 2)

    assert (resultado.ensayo_id, resultado.caduca_at_utc, resultado.partes) == (None, None, ())
    assert dict(resultado.resumen) == {
        "previstos": 0,
        "idempotentes": 0,
        "rechazados": 0,
        "no_procesados": 0,
        "excluidas": 2,
    }
    for prohibida in ("usuarios.resolver_login", "sigrid.existe_usuario", "sigrid.ensayar", "volcados.guardar_ensayo"):
        assert prohibida not in mundo.llamadas
    assert mundo.volcados.eventos == []
    # La guarda sí leyó: su bloque va (R47).
    assert resultado.guarda is not None


def test_f065_r45_lo_mandado_se_ensaya_y_se_guarda_como_siempre() -> None:
    mundo = _aprobadas(1, 2).con(ya_existe("RS26.09/0123", unidad=U2))
    mundo.revision.aprobar(2, unidad_codigo=U2)

    resultado = mundo.ensayar(1, 2)

    assert resultado.ensayo_id == UUID(int=500_000)
    assert [p.parte.incidencia_id for p in resultado.partes] == [ID(1)]
    assert [(e.incidencia_id, e.estado) for e in mundo.volcados.eventos] == [(ID(1), EV.PREVISTO)]
    assert dict(resultado.resumen)["excluidas"] == 1


# ==========================================================================
# R46 · si la guarda no puede leer, no se ensaya
# ==========================================================================


@pytest.mark.parametrize(
    ("lector", "error"),
    [
        ({"fallo": CatalogoNoDisponible("no se ha podido leer las reclamaciones de la obra en Sigrid: x")},
         CatalogoNoDisponible),
        ({"al_techo": True}, ReclamacionesSinVerificar),
        ({"filas": (choca("RS26.09/0123"), choca("RS26.09/0124", obra_ref=OTRA_OBRA_REF))}, ObraAmbigua),
    ],
    ids=["sigrid-caida", "al-techo-o-truncated", "dos-obras"],
)  # fmt: skip
def test_f065_r46_sin_lectura_valida_no_hay_login_ni_lote_ni_ensayo(lector: dict[str, Any], error: type) -> None:
    cambios = dict(lector)
    mundo = _aprobadas(1, 2).con(*cambios.pop("filas", ()), **cambios)

    with pytest.raises(error):
        mundo.ensayar(1, 2)

    for prohibida in ("usuarios.resolver_login", "sigrid.existe_usuario", "sigrid.ensayar", "volcados.guardar_ensayo"):
        assert prohibida not in mundo.llamadas
    assert mundo.volcados.eventos == []
    assert mundo.sigrid.ensayados == []


def test_f065_r46_al_techo_lleva_las_filas_y_no_se_cruza_nada(monkeypatch) -> None:
    monkeypatch.setattr(guarda_sigrid, "cruzar", prohibido("cruzar"))
    mundo = _aprobadas(1).con(choca("RS26.09/0123"), choca("RS26.09/0124"), al_techo=True)

    with pytest.raises(ReclamacionesSinVerificar) as fallo:
        mundo.ensayar(1)

    assert fallo.value.filas == 2
    assert "RS26" not in fallo.value.motivo


def test_f065_r46_la_obra_ambigua_no_se_cruza(monkeypatch) -> None:
    monkeypatch.setattr(guarda_sigrid, "cruzar", prohibido("cruzar"))
    mundo = _aprobadas(1).con(choca("RS26.09/0123"), choca("RS26.09/0124", obra_ref=OTRA_OBRA_REF))

    with pytest.raises(ObraAmbigua) as fallo:
        mundo.ensayar(1)

    assert OBRA_REF not in fallo.value.motivo and OTRA_OBRA_REF not in fallo.value.motivo


def test_f065_r46_cero_filas_no_es_un_error() -> None:
    mundo = _aprobadas(1)

    resultado = mundo.ensayar(1)

    assert mundo.mandadas() == [ID(1)]
    assert resultado.guarda.reclamaciones_leidas == 0


# ==========================================================================
# R47 · el bloque `sigrid` en la aplicación
# ==========================================================================


def test_f065_r47_la_guarda_dice_cuando_leyo_cuantas_y_cada_veredicto() -> None:
    mundo = _aprobadas(1, 2, 3).con(ya_existe("RS26.09/0123"), emparejada("RS26.10/0081", 2))
    mundo.revision.aprobar(3, ubicacion="Terraza", descripcion="Ejemplo de otra cosa")

    resultado = mundo.ensayar(3, 2, 1)

    guarda = resultado.guarda
    assert isinstance(guarda, GuardaDelEnsayo)
    assert guarda.leido_at_utc == AHORA
    assert guarda.reclamaciones_leidas == 2
    assert guarda.veredictos == (
        VeredictoDeLaGuarda(ID(3), V.VA, (), False),
        VeredictoDeLaGuarda(ID(2), V.SE_ENLAZA, ("RS26.10/0081",), False),
        VeredictoDeLaGuarda(ID(1), V.YA_EXISTE, ("RS26.09/0123",), False),
    )


# ==========================================================================
# R48 · la línea de la guarda
# ==========================================================================


def _lineas(caplog, prefijo: str) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.getMessage().startswith(prefijo)]


def _campos(linea: str) -> dict[str, str]:
    """`clave=valor` de una línea, después de los dos puntos."""
    return dict(par.split("=", 1) for par in linea.split(": ", 1)[1].split(" "))


LINEA = "F-065 guarda del ensayo: "
CONFIRMADA = "F-065 guarda del ensayo, conflicto confirmado: "
CLAVES_DE_LA_LINEA = [
    "obra", "llamada", "unidades", "reclamaciones", "va", "se_enlaza", "ya_existe", "choca",
    "duplicada_en_sigrid", "conflicto_sin_confirmar", "con_conflicto_confirmado",
    "confirmaciones_sobrantes", "segundos",
]  # fmt: skip


def _mundo_de_la_linea() -> Mundo:
    """Cinco candidatas en dos unidades: un veredicto de cada, una confirmada,
    una sin confirmar y una confirmación sobrante."""
    mundo = _aprobadas(1, 2, 3, 4, 5, u4=U2, u5=U2).con(
        ya_existe("RS26.09/0123"),
        emparejada("RS26.10/0081", 2),
        choca("RS26.09/0140", unidad=U2),
        choca("RS26.09/0141", unidad=U2, fecha=date(2026, 9, 1)),
    )
    mundo.revision.aprobar(2, ubicacion="Terraza", descripcion="Ejemplo de otra cosa")
    mundo.revision.aprobar(3, ubicacion="Terraza", descripcion="Ejemplo de otra cosa")
    return mundo


def test_f065_r48_una_linea_por_lectura_con_sus_cuentas(caplog) -> None:
    mundo = _mundo_de_la_linea()

    with caplog.at_level(logging.INFO):
        resultado = mundo.ensayar(
            1, 2, 3, 4, 5, confirmados={4: ("RS26.09/0140", "RS26.09/0141"), 3: ("RS26.09/0123",)}
        )

    (linea,) = _lineas(caplog, LINEA)
    campos = _campos(linea)
    assert list(campos) == CLAVES_DE_LA_LINEA
    assert {k: v for k, v in campos.items() if k != "segundos"} == {
        "obra": OBRA,
        "llamada": str(resultado.ensayo_id),
        "unidades": "2",
        "reclamaciones": "4",
        "va": "1",
        "se_enlaza": "1",
        "ya_existe": "1",
        "choca": "2",
        "duplicada_en_sigrid": "1",
        "conflicto_sin_confirmar": "1",
        "con_conflicto_confirmado": "1",
        "confirmaciones_sobrantes": "1",
    }
    assert 0 <= float(campos["segundos"]) < 60
    (confirmada,) = _lineas(caplog, CONFIRMADA)
    assert _campos(confirmada) == {"llamada": str(resultado.ensayo_id), "incidencia": str(ID(4)), "codigos": "2"}


def test_f065_r48_sin_ensayo_guardado_la_llamada_es_un_guion(caplog) -> None:
    mundo = _aprobadas(1).con(choca("RS26.09/0123"))

    with caplog.at_level(logging.INFO):
        mundo.ensayar(1)

    (linea,) = _lineas(caplog, LINEA)
    assert _campos(linea)["llamada"] == "-"


def test_f065_r48_si_el_ensayo_falla_despues_de_la_guarda_tambien_queda_su_linea(caplog) -> None:
    """«Una línea por lectura»: también si después no responde la pasarela."""
    mundo = _aprobadas(1).con(choca("RS26.09/0123"))
    mundo.sigrid.al_ensayar = responde_familia(FamiliaDeRespuesta.SIN_RESPUESTA)

    with caplog.at_level(logging.INFO), pytest.raises(EnsayoSinRespuesta):
        mundo.ensayar(1, confirmados={1: ("RS26.09/0123",)})

    (linea,) = _lineas(caplog, LINEA)
    assert _campos(linea)["llamada"] == "-"
    (confirmada,) = _lineas(caplog, CONFIRMADA)
    assert _campos(confirmada)["llamada"] == "-"


def test_f065_r48_sin_lectura_no_hay_linea_de_la_guarda(caplog) -> None:
    mundo = Mundo(1)

    with caplog.at_level(logging.INFO):
        mundo.ensayar(1)

    assert _lineas(caplog, "F-065 guarda") == []


def test_f065_r48_la_duracion_es_la_de_la_lectura(monkeypatch, caplog) -> None:
    """El reloj arranca en 10.000 s: sumar en vez de restar daría más de 20.000."""
    reloj = iter(10_000.0 + 0.25 * paso for paso in range(1_000))
    monkeypatch.setattr(guarda_sigrid, "monotonic", lambda: next(reloj))
    mundo = _aprobadas(1)

    with caplog.at_level(logging.INFO):
        mundo.ensayar(1)

    (linea,) = _lineas(caplog, LINEA)
    assert _campos(linea)["segundos"] == "0.25"


def test_f065_r48_ningun_codigo_rs_ni_texto_ni_unidad_ni_persona(caplog) -> None:
    mundo = _mundo_de_la_linea()

    with caplog.at_level(logging.DEBUG):
        mundo.ensayar(1, 2, 3, 4, 5, confirmados={4: ("RS26.09/0140", "RS26.09/0141")})

    texto = "\n".join(r.getMessage() for r in caplog.records if r.getMessage().startswith("F-065 guarda"))
    assert texto
    for prohibido_ in ("RS2", TEXTO_DE_SIGRID, UBICACION_DE_SIGRID, DESCRIPCION, "Baño", U1, U2, "VILLA",
                       "Ejemplo de oficio", "Ejemplo de tipo", OID, CORREO, "PVI-", OBRA_REF):  # fmt: skip
        assert prohibido_ not in texto, prohibido_


def test_f065_r48_el_detector_de_la_linea_no_es_ciego() -> None:
    assert _campos("F-065 guarda del ensayo: obra=9901 llamada=- unidades=1") == {
        "obra": "9901",
        "llamada": "-",
        "unidades": "1",
    }


# ==========================================================================
# R49 · lo mismo que hoy, y el mismo veredicto que la ruta
# ==========================================================================


def test_f065_r49_sin_la_clave_y_sin_nada_que_choque_es_el_ensayo_de_siempre() -> None:
    """Un mundo con la guarda vacía y otro con reclamaciones que no chocan (un
    aviso `CER` y otra unidad) dan el mismo ensayo."""
    vacio = _aprobadas(1, 2)
    con_avisos = _aprobadas(1, 2).con(
        fila("RS23.06/0300", "CER", fecha=date(2023, 6, 1)), choca("RS26.09/0123", unidad=U3)
    )

    uno, otro = vacio.ensayar(2, 1), con_avisos.ensayar(2, 1)

    assert (uno.partes, uno.excluidas, dict(uno.resumen)) == (otro.partes, otro.excluidas, dict(otro.resumen))
    assert vacio.sigrid.ensayados == con_avisos.sigrid.ensayados
    assert [v.veredicto for v in otro.guarda.veredictos] == [V.VA, V.VA]


def test_f065_r49_el_veredicto_del_ensayo_es_el_de_la_ruta_con_toda_la_obra() -> None:
    """La guarda cruza solo lo que se manda con solo sus unidades; la ruta, la
    bandeja entera con toda la obra. Mismo veredicto (salvo la excepción
    escrita de `test_f065_veredicto.py`: una `PVI-` en otra unidad)."""
    unidad_de_la_obra = choca("RS26.09/0300", unidad=U3)
    filas = (
        ya_existe("RS26.09/0123"),
        emparejada("RS26.10/0081", 2),
        choca("RS26.09/0140", unidad=U2),
        emparejada("RS26.10/0090", 5, "NPR", unidad=U2),
    )
    mundo = _aprobadas(1, 2, 3, 4, 5, 6, u4=U2, u5=U2, u6=U3).con(*filas)
    mundo.revision.aprobar(2, ubicacion="Terraza", descripcion="Ejemplo de otra cosa")
    mundo.revision.aprobar(3, ubicacion="Terraza", descripcion="Ejemplo de otra cosa")

    resultado = mundo.ensayar(1, 2, 3, 4, 5)

    bandeja = mundo.revision.listar(obra_codigo=OBRA, tope=10_000)
    toda_la_obra = [_reclamacion(f) for f in (*filas, unidad_de_la_obra)]
    de_la_ruta = {v.incidencia_id: v for v in veredictos(bandeja, cruzar(bandeja, toda_la_obra))}
    assert [(v.incidencia_id, v.veredicto, v.sigrid_cods) for v in resultado.guarda.veredictos] == [
        (de_la_ruta[i].incidencia_id, de_la_ruta[i].veredicto, de_la_ruta[i].sigrid_cods)
        for i in (ID(1), ID(2), ID(3), ID(4), ID(5))
    ]
    assert {v.veredicto for v in resultado.guarda.veredictos} == set(Veredicto)


def _reclamacion(f: FilaReclamacionObra) -> ReclamacionSigrid:
    return ReclamacionSigrid(
        cod=f.cod, estado=f.estado_codigo, fecha=f.fecha, unidad_codigo=f.unidad_codigo,
        ubicacion=f.ubicacion, oficio_codigo=f.oficio_codigo, oficio_nombre=f.oficio_nombre,
        tipo_codigo=f.tipo_codigo, tipo_nombre=f.tipo_nombre, descripcion=f.descripcion,
        referencia=f.referencia, ficha=None,
    )  # fmt: skip


def test_f065_r49_la_guarda_cruza_sin_ficha() -> None:
    """§15.2: la reclamación del dominio admite `ficha=None` y el cruce no la mira."""
    mundo = _aprobadas(1).con(ya_existe("RS26.09/0123"))

    resultado = mundo.ensayar(1)

    assert _excluidas(resultado) == [(ID(1), MX.DUPLICADA_EN_SIGRID, "RS26.09/0123")]


# ==========================================================================
# La guarda, directa
# ==========================================================================


def test_f065_r44_la_guarda_exige_algo_que_mandar() -> None:
    """Sin nada seleccionado no se llama (R44): llamarla así es un error de programación."""
    from domain.models.volcado import Seleccion

    with pytest.raises(ValueError):
        aplicar_guarda_de_sigrid(
            Seleccion(mandadas=(), excluidas=()),
            {},
            pedidas=(ID(1),),
            reclamaciones=LectorDeLaGuarda([]),
            obra=OBRA,
            tip=TIP,
            confirmados={},
            ahora=AHORA,
        )


def test_f065_r48_registrar_sin_guarda_no_escribe_nada(caplog) -> None:
    with caplog.at_level(logging.DEBUG):
        guarda_sigrid.registrar_la_guarda(None, llamada_id=None)

    assert caplog.records == []


# ==========================================================================
# El borde: `POST /api/volcado/ensayo` (R43, R46, R47)
# ==========================================================================


@pytest.fixture
def borde(monkeypatch) -> MundoDelBorde:
    """El mundo del borde de F-059, con el lector de la guarda en su fábrica."""
    mundo = MundoDelBorde(1, 2, 3)
    _componer(monkeypatch, mundo)
    mundo.lector = LectorDeLaGuarda(mundo.llamadas)

    def construir(_ajustes: object) -> LectorDeLaGuarda:
        mundo.construidos.append("reclamaciones")
        return mundo.lector

    monkeypatch.setattr(modulo, "construir_reclamaciones_obra", construir)
    return mundo


def _aprobar(mundo: MundoDelBorde, *ns: int) -> None:
    for n in ns:
        mundo.revision.aprobar(n)


@pytest.fixture
def nada_se_construye(monkeypatch) -> None:
    """R43: lo que no vale es 400 **antes** de construir ningún adaptador."""
    from tests.test_f059_volcado_http import _completos

    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: _completos())
    for nombre in (
        "construir_ensayador",
        "construir_reclamaciones_obra",
        "construir_volcador",
        "construir_revision",
        "construir_volcados",
        "construir_repositorio",
    ):
        monkeypatch.setattr(modulo, nombre, prohibido(nombre))


COD = "RS26.09/0123"
QUITAR = object()


def _confirmacion(n: int = 1, cods: Any = (COD,), **cambios: Any) -> dict[str, Any]:
    entrada: dict[str, Any] = {"incidencia_id": str(ID(n)), "sigrid_cods": list(cods)}
    entrada.update(cambios)
    return {k: v for k, v in entrada.items() if v is not QUITAR}


CUERPOS_INVALIDOS = [
    ("no-lista", "texto"),
    ("objeto", {"incidencia_id": str(ID(1)), "sigrid_cods": [COD]}),
    ("nulo", None),
    ("elemento-texto", [str(ID(1))]),
    ("sin-incidencia", [_confirmacion(incidencia_id=QUITAR)]),
    ("sin-sigrid-cods", [_confirmacion(sigrid_cods=QUITAR)]),
    ("clave-de-mas", [_confirmacion(confirmado=True)]),
    ("incidencia-no-uuid", [_confirmacion(incidencia_id="no-es-un-uuid-de-incidencia")]),
    ("incidencia-sin-guiones", [_confirmacion(incidencia_id=ID(1).hex)]),
    ("incidencia-numero", [_confirmacion(incidencia_id=1)]),
    ("incidencia-que-no-se-pide", [_confirmacion(9)]),
    ("incidencia-repetida", [_confirmacion(1), _confirmacion(1, ("RS26.09/0124",))]),
    ("cods-texto", [_confirmacion(cods=COD)]),
    ("cods-vacia", [_confirmacion(cods=())]),
    ("cods-51", [_confirmacion(cods=[f"RS26.09/{i:04d}" for i in range(51)])]),
    ("cod-mal-formado", [_confirmacion(cods=["RS26.9/123"])]),
    ("cod-minusculas", [_confirmacion(cods=["rs26.09/0123"])]),
    ("cod-con-blancos", [_confirmacion(cods=[" RS26.09/0123"])]),
    ("cod-de-mas", [_confirmacion(cods=["RS26.09/01234"])]),
    ("cod-numero", [_confirmacion(cods=[123])]),
    ("cod-repetido", [_confirmacion(cods=[COD, COD])]),
]


@pytest.mark.parametrize("confirmados", [c for _, c in CUERPOS_INVALIDOS], ids=[i for i, _ in CUERPOS_INVALIDOS])
def test_f065_r43_cada_confirmacion_invalida_es_400_sin_construir_nada(nada_se_construye, confirmados) -> None:
    respuesta = _ensayo(_cuerpo_ensayo(1, 2, conflictos_confirmados=confirmados))

    estado, datos = _leer(respuesta)
    assert (estado, datos.get("codigo")) == (400, "peticion_invalida")
    texto = _texto(respuesta)
    for prohibido_ in (OID, CORREO, "no-es-un-uuid-de-incidencia", "RS26", str(ID(9))):
        assert prohibido_ not in texto


@pytest.mark.parametrize(
    "cambio", [{"commit": False}, {"confirmado": True}, {"otra": "x"}], ids=["commit", "confirmado", "otra"]
)
def test_f065_r43_commit_confirmado_y_otras_siguen_siendo_400_con_la_clave_nueva(nada_se_construye, cambio) -> None:
    cuerpo = _cuerpo_ensayo(1, conflictos_confirmados=[_confirmacion()], **cambio)

    estado, datos = _leer(_ensayo(cuerpo))

    assert (estado, datos.get("codigo")) == (400, "peticion_invalida")


@pytest.mark.parametrize("cuerpo", ["sin-la-clave", "lista-vacia"])
def test_f065_r43_sin_la_clave_o_con_la_lista_vacia_se_ensaya(borde, cuerpo) -> None:
    _aprobar(borde, 1)
    extra = {} if cuerpo == "sin-la-clave" else {"conflictos_confirmados": []}

    estado, datos = _leer(_ensayo(_cuerpo_ensayo(1, **extra)))

    assert estado == 200, datos
    assert len(datos["partes"]) == 1


def test_f065_r43_r45_la_confirmacion_viaja_por_incidencia_con_sus_codigos(borde) -> None:
    _aprobar(borde, 1, 2)
    borde.lector.filas = (choca(COD), choca("RS26.09/0124", unidad=U2))
    borde.revision.aprobar(2, unidad_codigo=U2)
    cuerpo = _cuerpo_ensayo(
        1, 2, conflictos_confirmados=[_confirmacion(1, (COD,)), _confirmacion(2, ("RS26.09/0999",))]
    )

    estado, datos = _leer(_ensayo(cuerpo))

    assert estado == 200, datos
    assert [p["incidencia_id"] for p in datos["partes"]] == [str(ID(1))]
    assert datos["excluidas"] == [
        {"incidencia_id": str(ID(2)), "motivo": "conflicto_sin_confirmar", "sigrid_cod": "RS26.09/0124"}
    ]


def test_f065_r44_el_borde_construye_la_pasarela_el_lector_y_despues_la_base(borde) -> None:
    _aprobar(borde, 1)

    estado, _ = _leer(_ensayo(_cuerpo_ensayo(1)))

    assert estado == 200
    assert borde.construidos[:2] == ["ensayador", "reclamaciones"]
    assert "revision" in borde.construidos[2:]
    assert borde.lector.pedidas == [
        {"codigo_obra": OBRA, "tip": borde.ajustes.sigrid_tip_reclamacion, "unidades": (U1,)}
    ]


def test_f065_r46_sin_entorno_para_el_lector_es_503_antes_de_la_base(monkeypatch, borde) -> None:
    def fuera(_ajustes: object) -> object:
        raise CatalogoNoDisponible("ENTORNO='test' no lee Sigrid")

    monkeypatch.setattr(modulo, "construir_reclamaciones_obra", fuera)
    for nombre in ("construir_revision", "construir_volcados", "construir_repositorio"):
        monkeypatch.setattr(modulo, nombre, prohibido(nombre))

    estado, datos = _leer(_ensayo(_cuerpo_ensayo(1)))

    assert (estado, datos.get("codigo")) == (503, "sigrid_no_disponible")


@pytest.mark.parametrize(
    ("lector", "http", "codigo"),
    [
        ({"fallo": CatalogoNoDisponible("no se ha podido leer las reclamaciones de la obra en Sigrid: x")},
         503, "sigrid_no_disponible"),
        ({"al_techo": True, "filas": (choca(COD),)}, 409, "reclamaciones_sin_verificar"),
        ({"filas": (choca(COD), choca("RS26.09/0124", obra_ref=OTRA_OBRA_REF))}, 409, "obra_ambigua"),
    ],
    ids=["sigrid-caida", "al-techo", "dos-obras"],
)  # fmt: skip
def test_f065_r46_los_errores_de_la_guarda_con_su_http_y_sin_ensayo(borde, lector, http, codigo) -> None:
    _aprobar(borde, 1)
    for nombre, valor in lector.items():
        setattr(borde.lector, nombre, valor)

    respuesta = _ensayo(_cuerpo_ensayo(1))

    estado, datos = _leer(respuesta)
    assert (estado, datos.get("codigo")) == (http, codigo)
    assert set(datos) <= {"error", "codigo", "filas"}
    if codigo == "reclamaciones_sin_verificar":
        assert datos["filas"] == 1
    assert "RS26" not in _texto(respuesta)
    for prohibida in ("usuarios.resolver_login", "sigrid.ensayar", "volcados.guardar_ensayo"):
        assert prohibida not in borde.llamadas
    assert borde.volcados.eventos == []


def test_f065_r47_el_bloque_sigrid_y_las_claves_de_r12_sin_cambios(borde) -> None:
    _aprobar(borde, 1, 2, 3)
    borde.lector.filas = (ya_existe(COD), emparejada("RS26.10/0081", 2))
    borde.revision.aprobar(2, ubicacion="Terraza", descripcion="Ejemplo de otra cosa")
    borde.revision.aprobar(3, ubicacion="Terraza", descripcion="Ejemplo de otra cosa")

    respuesta = _ensayo(_cuerpo_ensayo(3, 1, 2, 77))

    estado, datos = _leer(respuesta)
    assert estado == 200, datos
    assert set(datos) == CLAVES_DE_R12 | {"sigrid"}
    assert list(datos["resumen"]) == CLAVES_DEL_RESUMEN
    assert all(set(e) == {"incidencia_id", "motivo", "sigrid_cod"} for e in datos["excluidas"])
    sigrid = datos["sigrid"]
    assert set(sigrid) == CLAVES_DE_SIGRID
    leido = datetime.fromisoformat(sigrid["leido_at_utc"])
    assert leido.utcoffset() is not None and leido.utcoffset().total_seconds() == 0
    assert sigrid["leido_at_utc"].endswith("+00:00")
    assert sigrid["reclamaciones_leidas"] == 2
    assert sigrid["veredictos"] == [
        {"incidencia_id": str(ID(3)), "veredicto": "va", "sigrid_cods": [], "confirmada": False},
        {"incidencia_id": str(ID(1)), "veredicto": "ya_existe", "sigrid_cods": [COD], "confirmada": False},
        {"incidencia_id": str(ID(2)), "veredicto": "se_enlaza", "sigrid_cods": ["RS26.10/0081"], "confirmada": False},
    ]
    assert all(set(v) == CLAVES_DE_VEREDICTO for v in sigrid["veredictos"])
    # Ni un texto de Sigrid, ni una ubicación (O-A4b-2): solo códigos.
    for texto in (TEXTO_DE_SIGRID, "Patio", "Ejemplo de oficio", "Ejemplo de tipo"):
        assert texto not in _texto(respuesta)


def test_f065_r47_la_confirmada_en_el_bloque(borde) -> None:
    _aprobar(borde, 1)
    borde.lector.filas = (choca(COD),)

    estado, datos = _leer(_ensayo(_cuerpo_ensayo(1, conflictos_confirmados=[_confirmacion()])))

    assert estado == 200, datos
    assert datos["sigrid"]["veredictos"] == [
        {"incidencia_id": str(ID(1)), "veredicto": "choca", "sigrid_cods": [COD], "confirmada": True}
    ]


def test_f065_r47_sin_lectura_el_bloque_es_null(borde) -> None:
    estado, datos = _leer(_ensayo(_cuerpo_ensayo(1, 77)))

    assert estado == 200
    assert set(datos) == CLAVES_DE_R12 | {"sigrid"}
    assert datos["sigrid"] is None
    assert borde.lector.pedidas == []


def test_f065_r47_los_codigos_de_la_guarda_en_function_app() -> None:
    import function_app

    assert function_app.CODIGOS_DEL_VOLCADO[CatalogoNoDisponible] == "sigrid_no_disponible"
    assert function_app.CODIGOS_DEL_VOLCADO[ReclamacionesSinVerificar] == "reclamaciones_sin_verificar"
    assert function_app.CODIGOS_DEL_VOLCADO[ObraAmbigua] == "obra_ambigua"
    assert function_app.HTTP_DEL_VOLCADO[CatalogoNoDisponible] == 503
    assert function_app.HTTP_DEL_VOLCADO[ReclamacionesSinVerificar] == 409
    assert function_app.HTTP_DEL_VOLCADO[ObraAmbigua] == 409
    assert {CatalogoNoDisponible, ReclamacionesSinVerificar, ObraAmbigua} <= set(function_app.ERRORES_DEL_VOLCADO)


def test_f065_r47_el_borde_exporta_su_costura() -> None:
    assert "construir_reclamaciones_obra" in modulo.__all__


def test_f065_r44_el_tipo_de_la_guarda_es_el_de_los_ajustes(borde) -> None:
    """`SIGRID_TIP_RECLAMACION` llega a la lectura tal cual, con otro valor que
    el de por defecto (708): un tipo fijo en el borde no pasaría."""
    from tests.test_f059_volcado_http import _completos

    borde.ajustes = _completos(SIGRID_TIP_RECLAMACION="709")
    _aprobar(borde, 1)

    estado, datos = _leer(_ensayo(_cuerpo_ensayo(1)))

    assert estado == 200, datos
    assert [p["tip"] for p in borde.lector.pedidas] == [709]


def test_f065_r44_el_instante_de_la_lectura_es_el_del_ensayo(borde) -> None:
    _aprobar(borde, 1)
    antes = datetime.now(UTC)

    _, datos = _leer(_ensayo(_cuerpo_ensayo(1)))

    despues = datetime.now(UTC)
    assert antes <= datetime.fromisoformat(datos["sigrid"]["leido_at_utc"]) <= despues
    assert datos["caduca_at_utc"] > datos["sigrid"]["leido_at_utc"]
