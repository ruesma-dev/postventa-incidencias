# services/postventa-api/tests/test_f065_http.py
"""La ruta `GET /api/revision/sigrid` (F-065, T7; R1, R2, R20–R24, R26, R35, R38).

`specs/F-065-revision-sigrid-backend/design.md` §2, §7, §8 y §10.4. Por la ruta
de verdad de `function_app`, con los adaptadores sustituidos por dobles: se
parchean las **fábricas** que compone el borde
(`interface_adapters/api/sigrid_bandeja.py`), así que lo que se prueba es la
composición entera. Donde importa lo que hace el adaptador de verdad (el 503
de una respuesta que no dice si viene cortada, O-A3-2 de la review del Bloque
A3; el `truncated`), se compone **el adaptador real** con el `ClienteFalso`:
ninguna llamada de red.

| Caso | Requisito |
|---|---|
| la obra no vale → 400 `peticion_invalida` sin construir nada; los demás parámetros se ignoran | R1 |
| Sigrid se construye antes que la base; si falla, 503 y la base ni se construye | R2 |
| una lectura de la base y una de Sigrid por petición | R3 |
| 409 `bandeja_demasiado_grande`, `reclamaciones_sin_verificar`, `obra_ambigua`; 503 de Sigrid, su configuración, el entorno y la base; el 503 «no dice si viene cortada» sigue siendo 503 | R4, R8, R9, R23 |
| la forma de la respuesta: claves exactas, `guardado_cod` (`null` donde no toca), `ficha` con la lista cerrada, fechas, resumen | R20 |
| el orden de las reclamaciones y de los hallazgos, el del dominio; los `coincide` en el de R18 | R21 |
| ni `oid`, ni correo de quien revisa, ni `ide`, ni `obride`; los errores no repiten filas | R22 |
| la línea `F-065 sigrid de la bandeja`, con 200 y con error, sin textos ni códigos y con los bytes; su `proceso_nuevo` no toca el del listado de F-060 | R24 |
| el listado de F-056 no lee las reclamaciones | R26 |
| `Cache-Control: no-store` en esta ruta, con 200 y con error, y en ninguna otra | R35 |

Datos inventados (R39): obra `9901`, «Ejemplo …», `000 000 00n`,
`@ejemplo.invalid`; los identificadores, `UUID(int=n)`.
"""

from __future__ import annotations

import ast
import json
import logging
import re
from dataclasses import fields
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import azure.functions as func
import pytest
from config.settings import Ajustes
from domain.models.errores import (
    CatalogoNoDisponible,
    ConfiguracionPgIncompleta,
    ConfiguracionSigridIncompleta,
    PersistenciaNoDisponible,
)
from domain.models.revision import TOPE_LECTURA_OBRA, estado_de, valores_vigentes
from domain.models.sigrid_bandeja import (
    Criterio,
    EstadoSigrid,
    ReclamacionSigrid,
    TipoHallazgo,
    cruzar,
)
from domain.ports.reclamaciones_obra import FichaReclamacion
from interface_adapters.api import tiempos

from tests.test_f065_adaptador import SECRETOS as SECRETOS_DEL_ADAPTADOR
from tests.test_f065_adaptador import _adaptador, _fila, _lectura
from tests.test_f065_aplicacion import (
    OBRA,
    OBRA_REF,
    OTRA_OBRA_REF,
    BandejaSoloLectura,
    LectorDeReclamaciones,
    fila,
    obra_de_ejemplo,
)
from tests.test_f065_dominio import CORREO, sit
from tests.utiles_revision import prohibido

SERVICIO = Path(__file__).resolve().parents[1]
FUNCTION_APP = SERVICIO / "function_app.py"

#: `SIGRID_TIP_RECLAMACION` por defecto (R5).
TIP_POR_DEFECTO = 708

#: Las claves de la respuesta 200 (R20), exactamente estas.
CLAVES_DE_LA_RESPUESTA = {
    "obra",
    "leido_at_utc",
    "criterio",
    "reclamaciones",
    "hallazgos",
    "incidencias",
    "resumen",
}
CLAVES_DE_RECLAMACION = {
    "cod",
    "estado",
    "fecha",
    "unidad_codigo",
    "ubicacion",
    "oficio_codigo",
    "oficio_nombre",
    "tipo_codigo",
    "tipo_nombre",
    "descripcion",
    "referencia",
    "incidencia_id",
    "ficha",
}
CLAVES_DE_HALLAZGO = {
    "tipo",
    "severidad",
    "incidencia_id",
    "sigrid_cod",
    "sigrid_cods",
    "guardado_cod",
    "criterios",
    "parecido",
}
CLAVES_DE_INCIDENCIA = {
    "estado",
    "unidad_codigo",
    "ubicacion",
    "oficio_codigo",
    "descripcion",
    "coincidencias_total",
}
CLAVES_DEL_RESUMEN = {
    "reclamaciones",
    "por_estado",
    "emparejadas",
    "estados_desconocidos",
    "incidencias_evaluadas",
    "incidencias_con_conflicto",
    "incidencias_con_aviso",
    "por_tipo",
    "por_criterio",
}

INSTANTE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00")
LINEA = "F-065 sigrid de la bandeja"


# --------------------------------------------------------------------------
# El mundo de la prueba, compuesto por las fábricas del borde
# --------------------------------------------------------------------------


class Mundo:
    def __init__(self, situaciones=(), filas=(), **lector: Any) -> None:
        self.llamadas: list[str] = []
        self.construidos: list[str] = []
        self.situaciones = situaciones
        self.revision = BandejaSoloLectura(self.llamadas, situaciones)
        self.lector: Any = LectorDeReclamaciones(self.llamadas, filas, **lector)

    def con_la_bandeja(self, revision: Any) -> Mundo:
        self.revision = revision
        return self


def _modulo():
    from interface_adapters.api import sigrid_bandeja

    return sigrid_bandeja


def _componer(monkeypatch, mundo: Mundo) -> None:
    modulo = _modulo()

    def sigrid(_ajustes: object) -> object:
        mundo.construidos.append("sigrid")
        return mundo.lector

    def bandeja(_ajustes: object) -> object:
        mundo.construidos.append("bandeja")
        return mundo.revision

    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: Ajustes(_env_file=None))
    monkeypatch.setattr(modulo, "construir_reclamaciones_obra", sigrid)
    monkeypatch.setattr(modulo, "construir_revision", bandeja)


@pytest.fixture
def mundo(monkeypatch) -> Mundo:
    situaciones, filas = obra_de_ejemplo()
    mundo = Mundo(situaciones, filas)
    _componer(monkeypatch, mundo)
    return mundo


@pytest.fixture
def nada_se_construye(monkeypatch) -> None:
    """R1: lo que no vale es 400 **antes** de construir nada."""
    modulo = _modulo()
    for nombre in ("obtener_ajustes", "construir_reclamaciones_obra", "construir_revision"):
        monkeypatch.setattr(modulo, nombre, prohibido(nombre))


def _ruta(nombre: str = "revision_sigrid"):
    import function_app

    assert hasattr(function_app, nombre), f"function_app no publica la ruta «{nombre}»"
    return getattr(function_app, nombre)


def _get(params: dict[str, str] | None = None) -> func.HttpResponse:
    peticion = func.HttpRequest(
        method="GET",
        url="/api/revision/sigrid",
        params={"obra": OBRA} if params is None else params,
        body=b"",
    )
    return _ruta()(peticion)


def _leer(respuesta: func.HttpResponse) -> tuple[int, Any]:
    return respuesta.status_code, json.loads(respuesta.get_body().decode("utf-8"))


def _lineas(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.getMessage().startswith(LINEA)]


def _campos_de_la_linea(linea: str) -> dict[str, str]:
    return dict(par.split("=", 1) for par in linea.removeprefix(f"{LINEA}: ").split(" "))


def _todas_las_claves(valor: Any) -> set[str]:
    if isinstance(valor, dict):
        claves = set(valor)
        for hijo in valor.values():
            claves |= _todas_las_claves(hijo)
        return claves
    if isinstance(valor, list):
        claves: set[str] = set()
        for hijo in valor:
            claves |= _todas_las_claves(hijo)
        return claves
    return set()


# ==========================================================================
# R1 · la obra se mira antes de construir nada
# ==========================================================================

OBRAS_INVALIDAS = [
    ("sin-obra", {}),
    ("vacia", {"obra": ""}),
    ("blancos", {"obra": "   "}),
    ("porcentajes", {"obra": "%%"}),
    ("comilla", {"obra": "99'01"}),
    ("larguisima", {"obra": "9" * 200}),
]


@pytest.mark.parametrize(("caso", "params"), OBRAS_INVALIDAS, ids=[c for c, _ in OBRAS_INVALIDAS])
def test_f065_r1_la_obra_que_no_vale_es_400_sin_construir_nada(nada_se_construye, caso, params) -> None:
    estado, cuerpo = _leer(_get(params))

    assert estado == 400
    assert cuerpo["codigo"] == "peticion_invalida"
    assert set(cuerpo) == {"error", "codigo"}


def test_f065_r1_la_obra_se_normaliza_como_en_f036(mundo) -> None:
    estado, cuerpo = _leer(_get({"obra": " 99 01 "}))

    assert estado == 200
    assert cuerpo["obra"] == OBRA
    assert mundo.lector.pedidas == [{"codigo_obra": OBRA, "tip": TIP_POR_DEFECTO}]


def test_f065_r5_el_tipo_de_concepto_sale_de_la_configuracion(mundo, monkeypatch) -> None:
    """`SIGRID_TIP_RECLAMACION` manda: el 708 es su defecto, no un literal del borde (precriba)."""
    monkeypatch.setattr(
        _modulo(), "obtener_ajustes", lambda: Ajustes(_env_file=None, sigrid_tip_reclamacion=999)
    )

    estado, _ = _leer(_get())

    assert estado == 200
    assert mundo.lector.pedidas == [{"codigo_obra": OBRA, "tip": 999}]


def test_f065_r1_cualquier_otro_parametro_se_ignora(mundo) -> None:
    referencia = _leer(_get())[1]
    estado, cuerpo = _leer(
        _get({"obra": OBRA, "estado": "no-es-un-estado", "tamano": "0", "cursor": "%%", "otra": "x"})
    )

    assert estado == 200
    referencia.pop("leido_at_utc")
    cuerpo.pop("leido_at_utc")
    assert cuerpo == referencia


# ==========================================================================
# R2 · Sigrid antes que la base, con sus dos puertas
# ==========================================================================


def test_f065_r2_sigrid_se_construye_antes_que_la_base(mundo) -> None:
    assert _get().status_code == 200

    assert mundo.construidos == ["sigrid", "bandeja"]


@pytest.mark.parametrize(
    "fallo",
    [
        CatalogoNoDisponible("este entorno no lee Sigrid"),
        ConfiguracionSigridIncompleta("faltan SIGRID_API_BASE_URL"),
    ],
    ids=["entorno", "configuracion"],
)
def test_f065_r2_si_sigrid_no_se_construye_503_y_la_base_ni_se_construye(monkeypatch, fallo) -> None:
    modulo = _modulo()
    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: Ajustes(_env_file=None))

    def falla(_ajustes: object) -> object:
        raise fallo

    monkeypatch.setattr(modulo, "construir_reclamaciones_obra", falla)
    monkeypatch.setattr(modulo, "construir_revision", prohibido("construir_revision"))

    estado, cuerpo = _leer(_get())

    assert estado == 503
    assert set(cuerpo) == {"error"}


def test_f065_r2_fuera_de_dev_y_pro_503_con_la_fabrica_de_verdad_y_sin_abrir_nada(monkeypatch) -> None:
    """La fábrica real se niega en `local` antes de mirar la configuración."""
    modulo = _modulo()
    monkeypatch.setattr(
        modulo,
        "obtener_ajustes",
        lambda: Ajustes(
            _env_file=None,
            ENTORNO="local",
            SIGRID_API_BASE_URL="https://ejemplo.invalido",
            SIGRID_API_KEY="clave-de-mentira-para-el-test",
            SIGRID_BASE_DATOS="labase",
        ),
    )
    monkeypatch.setattr(modulo, "construir_revision", prohibido("construir_revision"))
    from infrastructure.sigrid import catalogo_obra

    monkeypatch.setattr(catalogo_obra, "construir_cliente_http", prohibido("construir_cliente_http"))

    respuesta = _get()
    estado, cuerpo = _leer(respuesta)

    assert estado == 503
    assert "clave-de-mentira-para-el-test" not in respuesta.get_body().decode("utf-8")
    assert "ejemplo.invalido" not in cuerpo["error"]


def test_f065_r2_sin_configuracion_503_nombrando_las_variables_y_nunca_sus_valores(monkeypatch) -> None:
    modulo = _modulo()
    monkeypatch.setattr(
        modulo,
        "obtener_ajustes",
        lambda: Ajustes(_env_file=None, ENTORNO="dev", SIGRID_API_KEY="clave-de-mentira-para-el-test"),
    )
    monkeypatch.setattr(modulo, "construir_revision", prohibido("construir_revision"))

    respuesta = _get()
    estado, cuerpo = _leer(respuesta)

    assert estado == 503
    assert "SIGRID_API_BASE_URL" in cuerpo["error"]
    assert "clave-de-mentira-para-el-test" not in respuesta.get_body().decode("utf-8")


def test_f065_r2_si_la_base_no_se_construye_503(monkeypatch) -> None:
    mundo = Mundo(*obra_de_ejemplo())
    _componer(monkeypatch, mundo)
    modulo = _modulo()

    def falla(_ajustes: object) -> object:
        mundo.construidos.append("bandeja")
        raise ConfiguracionPgIncompleta("faltan PG_HOST")

    monkeypatch.setattr(modulo, "construir_revision", falla)

    estado, _ = _leer(_get())

    assert estado == 503
    assert mundo.construidos == ["sigrid", "bandeja"]
    assert mundo.llamadas == []


# ==========================================================================
# R3 · una lectura de la base y como mucho una de Sigrid
# ==========================================================================


def test_f065_r3_una_lectura_de_cada_por_peticion(mundo) -> None:
    assert _get().status_code == 200
    assert _get().status_code == 200

    assert mundo.llamadas == ["revision.listar", "sigrid.leer"] * 2


# ==========================================================================
# R4, R8, R9, R23 · la traducción de los errores
# ==========================================================================


def test_f065_r4_bandeja_demasiado_grande_409_con_el_recuento_sin_sigrid(monkeypatch) -> None:
    mundo = Mundo()
    mundo.con_la_bandeja(
        BandejaSoloLectura(mundo.llamadas, (sit(1),) * (TOPE_LECTURA_OBRA + 1), total=10_400)
    )
    _componer(monkeypatch, mundo)

    estado, cuerpo = _leer(_get())

    assert estado == 409
    assert cuerpo["codigo"] == "bandeja_demasiado_grande"
    assert cuerpo["total"] == 10_400
    assert mundo.llamadas == ["revision.listar", "revision.contar"]


def test_f065_r8_al_techo_409_reclamaciones_sin_verificar_con_las_filas(monkeypatch) -> None:
    situaciones, filas = obra_de_ejemplo()
    mundo = Mundo(situaciones, filas, al_techo=True)
    _componer(monkeypatch, mundo)

    estado, cuerpo = _leer(_get())

    assert estado == 409
    assert cuerpo == {
        "error": cuerpo["error"],
        "codigo": "reclamaciones_sin_verificar",
        "filas": len(filas),
    }
    assert "hallazgos" not in cuerpo


def test_f065_r8_truncated_con_el_adaptador_de_verdad_es_409(monkeypatch) -> None:
    mundo = Mundo((sit(1),))
    mundo.lector, _ = _adaptador(_lectura([_fila()], truncada=True))
    _componer(monkeypatch, mundo)

    estado, cuerpo = _leer(_get())

    assert estado == 409
    assert cuerpo["codigo"] == "reclamaciones_sin_verificar"
    assert cuerpo["filas"] == 1


@pytest.mark.parametrize(
    "truncada", [None, "false", 0], ids=["sin-truncated", "texto", "cero"]
)
def test_f065_r8_o_a3_2_la_respuesta_que_no_dice_si_viene_cortada_es_503_y_no_409(
    monkeypatch, truncada
) -> None:
    """O-A3-2: el 503 «no dice si viene cortada» del adaptador no se convierte en 409."""
    mundo = Mundo((sit(1),))
    respuesta_sin_marca = _lectura([_fila()], truncada=truncada)
    if truncada is None:
        respuesta_sin_marca._cuerpo.pop("truncated")
    mundo.lector, _ = _adaptador(respuesta_sin_marca)
    _componer(monkeypatch, mundo)

    respuesta = _get()
    estado, cuerpo = _leer(respuesta)

    assert estado == 503
    assert "codigo" not in cuerpo
    assert "no dice si viene cortada" in cuerpo["error"]
    texto = respuesta.get_body().decode("utf-8")
    assert [s for s in SECRETOS_DEL_ADAPTADOR if s in texto] == []


def test_f065_r9_dos_obras_409_obra_ambigua(monkeypatch) -> None:
    filas = (fila("RS26.09/0123"), fila("RS26.09/0124", obra_ref=OTRA_OBRA_REF))
    mundo = Mundo((sit(1),), filas)
    _componer(monkeypatch, mundo)

    respuesta = _get()
    estado, cuerpo = _leer(respuesta)

    assert estado == 409
    assert cuerpo["codigo"] == "obra_ambigua"
    texto = respuesta.get_body().decode("utf-8")
    assert OBRA_REF not in texto and OTRA_OBRA_REF not in texto
    assert "RS26.09/0123" not in texto


def test_f065_r9_ninguna_fila_es_200_con_las_listas_vacias(monkeypatch) -> None:
    mundo = Mundo((sit(1),), ())
    _componer(monkeypatch, mundo)

    estado, cuerpo = _leer(_get())

    assert estado == 200
    assert cuerpo["reclamaciones"] == []
    assert cuerpo["hallazgos"] == []
    assert cuerpo["incidencias"] == {}
    assert cuerpo["resumen"]["reclamaciones"] == 0
    assert cuerpo["resumen"]["incidencias_evaluadas"] == 1
    # Las cuentas, con todas sus claves también a cero (precriba de mutación):
    # quien pinta el resumen no tiene que adivinar qué estado falta.
    resumen = cuerpo["resumen"]
    assert resumen["por_estado"] == {e.value: 0 for e in EstadoSigrid}
    assert resumen["por_tipo"] == {t.value: 0 for t in TipoHallazgo}
    assert resumen["por_criterio"] == {c.value: 0 for c in Criterio}
    assert resumen["emparejadas"] == resumen["estados_desconocidos"] == 0
    assert resumen["incidencias_con_conflicto"] == resumen["incidencias_con_aviso"] == 0


ERRORES_DE_LA_LECTURA = [
    ("sigrid", CatalogoNoDisponible("no se ha podido leer las reclamaciones de la obra en Sigrid: ConnectTimeout")),
    ("base", PersistenciaNoDisponible("la base no responde")),
]


@pytest.mark.parametrize(("donde", "fallo"), ERRORES_DE_LA_LECTURA, ids=[d for d, _ in ERRORES_DE_LA_LECTURA])
def test_f065_r23_sin_sigrid_o_sin_base_503_con_el_cuerpo_de_siempre(monkeypatch, donde, fallo) -> None:
    import function_app

    mundo = Mundo(*obra_de_ejemplo(), **({"fallo": fallo} if donde == "sigrid" else {}))
    if donde == "base":
        mundo.con_la_bandeja(BandejaSoloLectura(mundo.llamadas, fallo=fallo))
    _componer(monkeypatch, mundo)

    estado, cuerpo = _leer(_get())

    de_siempre = json.loads(
        function_app._sin_sigrid_o_sin_base("mirar las reclamaciones de Sigrid", fallo).get_body()
    )
    assert estado == 503
    assert set(cuerpo) == {"error"}
    assert fallo.motivo in cuerpo["error"]
    assert "no se ha escrito nada" in cuerpo["error"]
    assert cuerpo == de_siempre


# ==========================================================================
# R20 · la forma de la respuesta
# ==========================================================================


def test_f065_r20_las_claves_de_la_respuesta_y_el_criterio(mundo) -> None:
    estado, cuerpo = _leer(_get())

    assert estado == 200
    assert set(cuerpo) == CLAVES_DE_LA_RESPUESTA
    assert cuerpo["obra"] == OBRA
    assert INSTANTE.fullmatch(cuerpo["leido_at_utc"])
    assert cuerpo["criterio"] == {
        "abiertas": ["SAT", "PTE"],
        "cerradas": ["TER", "CER"],
        "umbral_parecido": 50,
        "tope": 500000,
    }


def test_f065_r20_leido_at_utc_es_el_instante_de_la_lectura_en_utc(mundo) -> None:
    from datetime import timedelta, timezone

    madrid = timezone(timedelta(hours=2))
    cuerpo = _modulo().sigrid_de_la_bandeja(
        OBRA,
        revision=mundo.revision,
        reclamaciones=mundo.lector,
        ahora=datetime(2026, 10, 29, 12, 30, 5, 7, tzinfo=madrid),
    )

    assert cuerpo["leido_at_utc"] == "2026-10-29T10:30:05.000007+00:00"


def test_f065_r20_cada_reclamacion_con_sus_campos_y_su_ficha(mundo) -> None:
    _, cuerpo = _leer(_get())
    _, filas = obra_de_ejemplo()
    de_la_fila = {f.cod: f for f in filas}

    assert len(cuerpo["reclamaciones"]) == len(filas)
    for r in cuerpo["reclamaciones"]:
        assert set(r) == CLAVES_DE_RECLAMACION
        f = de_la_fila[r["cod"]]
        assert r["estado"] == f.estado_codigo
        assert r["fecha"] == (None if f.fecha is None else f.fecha.isoformat())
        assert r["unidad_codigo"] == f.unidad_codigo
        assert r["ubicacion"] == f.ubicacion
        assert r["oficio_codigo"] == f.oficio_codigo
        assert r["oficio_nombre"] == f.oficio_nombre
        assert r["tipo_codigo"] == f.tipo_codigo
        assert r["tipo_nombre"] == f.tipo_nombre
        assert r["descripcion"] == f.descripcion
        assert r["referencia"] == f.referencia
        assert set(r["ficha"]) == {c.name for c in fields(FichaReclamacion)}
        for campo in fields(FichaReclamacion):
            valor = getattr(f.ficha, campo.name)
            esperado = valor.isoformat() if isinstance(valor, date) else valor
            assert r["ficha"][campo.name] == esperado, campo.name


def test_f065_r20_la_ficha_tiene_los_diecinueve_campos_de_r33_y_nulos_donde_no_hay(monkeypatch) -> None:
    vacia = FichaReclamacion(*([None] * len(fields(FichaReclamacion))))
    sin_nada = fila("RS26.09/0123")
    from dataclasses import replace

    mundo = Mundo((), (replace(sin_nada, ficha=vacia),))
    _componer(monkeypatch, mundo)

    _, cuerpo = _leer(_get())

    (r,) = cuerpo["reclamaciones"]
    assert len(r["ficha"]) == 19
    assert set(r["ficha"].values()) == {None}


def test_f065_r20_la_fecha_es_aaaa_mm_dd_o_null(mundo) -> None:
    _, cuerpo = _leer(_get())
    fechas = {r["cod"]: r["fecha"] for r in cuerpo["reclamaciones"]}

    assert fechas["RS26.09/0123"] == "2026-09-15"
    assert fechas["RS23.06/0300"] == "2023-06-01"
    assert fechas["RS26.08/0001"] is None


def test_f065_r20_incidencia_id_solo_en_las_emparejadas(mundo) -> None:
    _, cuerpo = _leer(_get())

    emparejadas = {r["cod"]: r["incidencia_id"] for r in cuerpo["reclamaciones"] if r["incidencia_id"]}
    assert emparejadas == {
        "RS26.10/0080": str(UUID(int=3)),
        "RS26.10/0081": str(UUID(int=4)),
        "RS26.10/0083": str(UUID(int=5)),
    }
    # La de la prueba de la pasarela (E8) lleva su referencia, sin emparejar.
    (prueba,) = [r for r in cuerpo["reclamaciones"] if r["cod"] == "RS26.09/0439"]
    assert prueba["referencia"] == "PVI-PRUEBA-0001"
    assert prueba["incidencia_id"] is None


def test_f065_r20_cada_hallazgo_con_sus_ocho_claves(mundo) -> None:
    _, cuerpo = _leer(_get())

    assert cuerpo["hallazgos"]
    for h in cuerpo["hallazgos"]:
        assert set(h) == CLAVES_DE_HALLAZGO
        assert h["tipo"] in {t.value for t in TipoHallazgo}
        assert h["severidad"] in {"conflicto", "aviso"}
        assert isinstance(h["sigrid_cods"], list)
        assert isinstance(h["criterios"], list)


def _por_tipo(cuerpo: dict, tipo: str) -> list[dict]:
    return [h for h in cuerpo["hallazgos"] if h["tipo"] == tipo]


def test_f065_r20_guardado_cod_solo_en_volcada_no_encontrada_y_codigo_distinto(mundo) -> None:
    """Enmienda del 2026-10-28: el código guardado viaja en `guardado_cod`, `null` en los demás."""
    _, cuerpo = _leer(_get())

    (no_encontrada,) = _por_tipo(cuerpo, "volcada_no_encontrada")
    assert no_encontrada == {
        "tipo": "volcada_no_encontrada",
        "severidad": "aviso",
        "incidencia_id": str(UUID(int=2)),
        "sigrid_cod": None,
        "sigrid_cods": [],
        "guardado_cod": "RS26.10/0090",
        "criterios": [],
        "parecido": None,
    }
    (distinto,) = _por_tipo(cuerpo, "codigo_distinto")
    assert distinto["sigrid_cod"] == "RS26.10/0080"
    assert distinto["guardado_cod"] == "RS26.10/0074"
    assert distinto["sigrid_cods"] == []
    otros = [h for h in cuerpo["hallazgos"] if h["tipo"] not in {"volcada_no_encontrada", "codigo_distinto"}]
    assert otros
    assert {h["guardado_cod"] for h in otros} == {None}
    assert all("guardado_cod" in h for h in otros)


def test_f065_r20_los_codigos_de_cada_hallazgo_son_los_de_la_tabla(mundo) -> None:
    _, cuerpo = _leer(_get())
    codigos = {r["cod"] for r in cuerpo["reclamaciones"]}

    (varias,) = _por_tipo(cuerpo, "varias_en_sigrid")
    assert varias["sigrid_cod"] == "RS26.10/0083"
    assert varias["sigrid_cods"] == ["RS26.10/0083", "RS26.10/0082"]
    (ya,) = _por_tipo(cuerpo, "ya_en_sigrid")
    assert (ya["sigrid_cod"], ya["severidad"], ya["incidencia_id"]) == ("RS26.10/0081", "conflicto", str(UUID(int=4)))
    (anulada,) = _por_tipo(cuerpo, "anulada_en_sigrid")
    assert anulada["sigrid_cod"] == "RS26.10/0080"
    (desconocida,) = _por_tipo(cuerpo, "referencia_desconocida")
    assert (desconocida["sigrid_cod"], desconocida["incidencia_id"]) == ("RS26.09/0439", None)
    # Invariantes: sigrid_cod de una reclamación de la respuesta; sigrid_cods solo en varias.
    for h in cuerpo["hallazgos"]:
        assert h["sigrid_cod"] is None or h["sigrid_cod"] in codigos
        assert (h["sigrid_cods"] != []) == (h["tipo"] == "varias_en_sigrid")
        assert set(h["sigrid_cods"]) <= codigos


def test_f065_r20_los_coincide_con_criterios_parecido_y_severidad(mundo) -> None:
    _, cuerpo = _leer(_get())

    pares = {(h["incidencia_id"], h["sigrid_cod"]): h for h in _por_tipo(cuerpo, "coincide")}
    conflicto = pares[(str(UUID(int=1)), "RS26.09/0123")]
    assert conflicto["severidad"] == "conflicto"
    assert conflicto["criterios"] == ["misma_unidad_oficio_ubicacion"]
    assert conflicto["parecido"] is None
    aviso = pares[(str(UUID(int=1)), "RS23.06/0300")]
    assert aviso["severidad"] == "aviso"


def test_f065_r20_el_parecido_viaja_con_el_criterio_de_la_descripcion(monkeypatch) -> None:
    """E2: la misma descripción normalizada es parecido 100."""
    situaciones = (sit(1, "nueva", ubicacion="Baño principal", oficio="0012", descripcion="Silicona negra en bañera"),)
    filas = (fila("RS26.08/0045", "SAT", ubicacion="Baño 1", oficio="0050", descripcion="Silicona negra en bañera."),)
    mundo = Mundo(situaciones, filas)
    _componer(monkeypatch, mundo)

    _, cuerpo = _leer(_get())

    (h,) = cuerpo["hallazgos"]
    assert h["criterios"] == ["misma_unidad_descripcion_parecida"]
    assert h["parecido"] == 100


def test_f065_r20_incidencias_solo_las_que_tienen_hallazgos_con_sus_vigentes(mundo) -> None:
    _, cuerpo = _leer(_get())
    situaciones, _ = obra_de_ejemplo()
    por_id = {str(s.incidencia.incidencia_id): s for s in situaciones}

    con_hallazgos = {h["incidencia_id"] for h in cuerpo["hallazgos"] if h["incidencia_id"]}
    assert set(cuerpo["incidencias"]) == con_hallazgos
    for incidencia_id, datos in cuerpo["incidencias"].items():
        assert set(datos) == CLAVES_DE_INCIDENCIA
        s = por_id[incidencia_id]
        vigentes = valores_vigentes(s)
        assert datos["estado"] == estado_de(s).value
        assert datos["unidad_codigo"] == vigentes.unidad_codigo
        assert datos["ubicacion"] == vigentes.ubicacion
        assert datos["oficio_codigo"] == vigentes.oficio_codigo
        assert datos["descripcion"] == vigentes.descripcion
    assert cuerpo["incidencias"][str(UUID(int=1))]["coincidencias_total"] == 2
    assert cuerpo["incidencias"][str(UUID(int=2))]["coincidencias_total"] == 0


def test_f065_r20_los_vigentes_de_una_editada_son_los_de_su_ultima_revision(monkeypatch) -> None:
    mundo = Mundo((sit(1, "editada"),), (fila("RS26.09/0123", "PTE"),))
    _componer(monkeypatch, mundo)

    _, cuerpo = _leer(_get())

    datos = cuerpo["incidencias"][str(UUID(int=1))]
    assert datos["estado"] == "editada"
    assert datos["descripcion"] == "Gotea el grifo"


def test_f065_r20_el_resumen(mundo) -> None:
    _, cuerpo = _leer(_get())
    resumen = cuerpo["resumen"]

    assert set(resumen) == CLAVES_DEL_RESUMEN
    assert resumen["reclamaciones"] == 10
    assert resumen["por_estado"] == {"SAT": 4, "PTE": 1, "TER": 1, "CER": 1, "NPR": 2}
    assert resumen["estados_desconocidos"] == 1
    assert sum(resumen["por_estado"].values()) + resumen["estados_desconocidos"] == resumen["reclamaciones"]
    assert resumen["emparejadas"] == 3
    assert resumen["incidencias_evaluadas"] == 3  # 1 nueva, 4 en_duda y 5 aprobada
    # Con algún conflicto: 1 (coincide PTE), 4 (ya_en_sigrid) y 5 (varias_en_sigrid).
    assert resumen["incidencias_con_conflicto"] == 3
    # Con algún aviso: 1 (CER), 2 (no encontrada) y 3 (distinto y anulada).
    assert resumen["incidencias_con_aviso"] == 3
    assert resumen["por_tipo"] == {
        "coincide": 2,
        "ya_en_sigrid": 1,
        "varias_en_sigrid": 1,
        "volcada_no_encontrada": 1,
        "codigo_distinto": 1,
        "anulada_en_sigrid": 1,
        "referencia_desconocida": 1,
    }
    assert resumen["por_criterio"] == {
        "misma_unidad_oficio_ubicacion": 2,
        "misma_unidad_descripcion_parecida": 0,
    }


def test_f065_r20_el_resumen_cuenta_los_hallazgos_que_viajan(monkeypatch) -> None:
    """Con más de 10 pares, `por_tipo` cuenta los 10 de `hallazgos`; el total real va en la incidencia."""
    filas = tuple(fila(f"RS26.09/{i:04d}", "SAT") for i in range(12))
    mundo = Mundo((sit(1),), filas)
    _componer(monkeypatch, mundo)

    _, cuerpo = _leer(_get())

    assert len(_por_tipo(cuerpo, "coincide")) == 10
    assert cuerpo["resumen"]["por_tipo"]["coincide"] == 10
    assert cuerpo["incidencias"][str(UUID(int=1))]["coincidencias_total"] == 12


# ==========================================================================
# R21 · el orden, el del dominio
# ==========================================================================


def _reclamaciones_del_dominio() -> list[ReclamacionSigrid]:
    _, filas = obra_de_ejemplo()
    return [
        ReclamacionSigrid(
            f.cod, f.estado_codigo, f.fecha, f.unidad_codigo, f.ubicacion, f.oficio_codigo,
            f.oficio_nombre, f.tipo_codigo, f.tipo_nombre, f.descripcion, f.referencia, f.ficha,
        )
        for f in filas
    ]  # fmt: skip


def test_f065_r21_las_reclamaciones_en_el_orden_del_dominio(mundo) -> None:
    _, cuerpo = _leer(_get())
    cruce = cruzar(obra_de_ejemplo()[0], _reclamaciones_del_dominio())

    assert [r["cod"] for r in cuerpo["reclamaciones"]] == [r.cod for r, _ in cruce.reclamaciones]
    # Fecha descendente, sin fecha al final; a igual fecha, código descendente.
    assert [r["cod"] for r in cuerpo["reclamaciones"]][-1] == "RS26.08/0001"


def test_f065_r21_los_hallazgos_en_el_orden_del_dominio(mundo) -> None:
    _, cuerpo = _leer(_get())
    cruce = cruzar(obra_de_ejemplo()[0], _reclamaciones_del_dominio())

    assert [(h["tipo"], h["incidencia_id"], h["sigrid_cod"]) for h in cuerpo["hallazgos"]] == [
        (h.tipo.value, None if h.incidencia_id is None else str(h.incidencia_id), h.sigrid_cod)
        for h in cruce.hallazgos
    ]
    severidades = [h["severidad"] for h in cuerpo["hallazgos"]]
    assert severidades == sorted(severidades, key=["conflicto", "aviso"].index)


def test_f065_r21_los_coincide_de_una_incidencia_en_el_orden_de_r18(monkeypatch) -> None:
    """El de código menor es el más reciente; uno sin fecha; dos de la misma fecha."""
    filas = (
        fila("RS26.01/0001", "SAT", fecha=date(2026, 10, 1)),
        fila("RS26.01/0009", "SAT", fecha=date(2026, 3, 1)),
        fila("RS26.01/0005", "SAT", fecha=None),
        fila("RS26.01/0007", "PTE", fecha=date(2026, 5, 1)),
        fila("RS26.01/0008", "PTE", fecha=date(2026, 5, 1)),
        fila("RS25.01/0002", "CER", fecha=date(2026, 12, 1)),
    )
    mundo = Mundo((sit(1),), filas)
    _componer(monkeypatch, mundo)

    _, cuerpo = _leer(_get())

    assert [h["sigrid_cod"] for h in _por_tipo(cuerpo, "coincide")] == [
        "RS26.01/0001",
        "RS26.01/0008",
        "RS26.01/0007",
        "RS26.01/0009",
        "RS26.01/0005",
        "RS25.01/0002",
    ]


# ==========================================================================
# R22 · nada de quien revisa, ni identificadores de Sigrid
# ==========================================================================


def test_f065_r22_ni_oid_ni_correo_ni_ide_ni_obride(mundo) -> None:
    respuesta = _get()
    texto = respuesta.get_body().decode("utf-8")
    _, cuerpo = _leer(respuesta)

    assert CORREO not in texto  # quien revisó y quien volcó (`sit`)
    assert OBRA_REF not in texto
    assert "700001" not in texto  # el `sigrid_ide` del parte volcado
    claves = _todas_las_claves(cuerpo)
    assert not claves & {"oid", "correo", "ide", "obride", "obra_ref", "sigrid_ide", "usuario_oid", "usuario_correo"}


def test_f065_r22_las_claves_son_solo_las_de_r20_y_r33(mundo) -> None:
    _, cuerpo = _leer(_get())

    permitidas = (
        CLAVES_DE_LA_RESPUESTA
        | CLAVES_DE_RECLAMACION
        | CLAVES_DE_HALLAZGO
        | CLAVES_DE_INCIDENCIA
        | CLAVES_DEL_RESUMEN
        | {"abiertas", "cerradas", "umbral_parecido", "tope"}
        | {c.name for c in fields(FichaReclamacion)}
        | {e.value for e in EstadoSigrid}
        | {t.value for t in TipoHallazgo}
        | {c.value for c in Criterio}
        | set(cuerpo["incidencias"])
    )
    assert _todas_las_claves(cuerpo) <= permitidas


# ==========================================================================
# R24 · la línea de la ruta
# ==========================================================================


def test_f065_r24_una_linea_con_200_con_los_tramos_los_recuentos_y_los_bytes(mundo, caplog) -> None:
    caplog.set_level(logging.INFO)

    respuesta = _get()

    (linea,) = _lineas(caplog)
    campos = _campos_de_la_linea(linea)
    assert list(campos)[:5] == ["obra", "resultado", "total", "proceso_nuevo", "segundos_de_proceso"]
    assert campos["obra"] == OBRA
    assert campos["resultado"] == "200"
    assert campos["proceso_nuevo"] in {"True", "False"}
    tramos = [
        "construir.sigrid",
        "construir.bandeja",
        "bandeja.listar",
        "sigrid.leer",
        "aplicacion",
        "calculo",
        "serializar",
    ]
    for tramo in ["total", *tramos]:
        assert re.fullmatch(r"\d+\.\d{3}", campos[tramo]), tramo
    assert list(campos).index("calculo") == list(campos).index("aplicacion") + 1
    assert re.fullmatch(r"\d+", campos["segundos_de_proceso"])
    assert campos["reclamaciones"] == "10"
    assert campos["evaluadas"] == "3"
    _, cuerpo = _leer(respuesta)
    conflictos = sum(1 for h in cuerpo["hallazgos"] if h["severidad"] == "conflicto")
    assert campos["conflictos"] == str(conflictos)
    assert campos["avisos"] == str(len(cuerpo["hallazgos"]) - conflictos)
    assert campos["bytes"] == str(len(respuesta.get_body()))
    assert list(campos)[-5:] == ["reclamaciones", "evaluadas", "conflictos", "avisos", "bytes"]


def test_f065_r24_los_bytes_son_los_del_cuerpo_tambien_con_acentos(monkeypatch, caplog) -> None:
    """Los bytes que viajan, en UTF-8: con `ensure_ascii` saldrían de más (precriba de mutación)."""
    caplog.set_level(logging.INFO)
    situaciones, filas = obra_de_ejemplo()
    filas = (*filas, fila("RS26.09/0998", descripcion="Ejemplo de baño con grieta en el alféizar"))
    _componer(monkeypatch, Mundo(situaciones, filas))

    respuesta = _get()

    cuerpo = respuesta.get_body()
    assert "alféizar".encode() in cuerpo, "el cuerpo tiene que llevar algo que no sea ASCII"
    (linea,) = _lineas(caplog)
    assert _campos_de_la_linea(linea)["bytes"] == str(len(cuerpo))


def test_f065_r24_un_proceso_recien_arrancado_dice_proceso_nuevo_true() -> None:
    """El indicador propio empieza apagado: la primera petición del proceso es la nueva.

    Con una copia **recién cargada** del módulo, como la de un proceso que arranca
    (los demás tests ponen el indicador a mano y no verían su valor inicial).
    """
    import importlib.util

    especificacion = importlib.util.find_spec("interface_adapters.api.sigrid_bandeja")
    assert especificacion is not None and especificacion.loader is not None
    recien_cargado = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(recien_cargado)

    assert [recien_cargado._es_primera_de_sigrid() for _ in range(3)] == [True, False, False]


@pytest.mark.parametrize(
    ("caso", "esperado"),
    [
        ("obra", "CodigoDeObraInvalido"),
        ("sigrid", "CatalogoNoDisponible"),
        ("techo", "ReclamacionesSinVerificar"),
        ("ambigua", "ObraAmbigua"),
    ],
)
def test_f065_r24_una_linea_tambien_con_error_con_el_tipo(monkeypatch, caplog, caso, esperado) -> None:
    caplog.set_level(logging.INFO)
    filas = obra_de_ejemplo()[1]
    if caso == "ambigua":
        filas = (*filas, fila("RS26.09/0999", obra_ref=OTRA_OBRA_REF))
    mundo = Mundo(
        (sit(1),),
        filas,
        al_techo=caso == "techo",
        fallo=CatalogoNoDisponible("sin red") if caso == "sigrid" else None,
    )
    _componer(monkeypatch, mundo)

    _get({"obra": "%%"} if caso == "obra" else None)

    (linea,) = _lineas(caplog)
    campos = _campos_de_la_linea(linea)
    assert campos["resultado"] == esperado
    assert campos["obra"] == ("-" if caso == "obra" else OBRA)
    assert campos["bytes"] == "-"
    if caso == "obra":
        assert "construir.sigrid" not in campos
        assert campos["reclamaciones"] == "-"


def test_f065_r24_la_linea_no_lleva_ningun_texto_ni_codigo(mundo, caplog) -> None:
    caplog.set_level(logging.DEBUG)

    _get()

    (linea,) = _lineas(caplog)
    situaciones, _ = obra_de_ejemplo()
    prohibidos = {"RS2", "PVI-", "Cocina", "Patio", "Terraza", "Gotea", "Fuga", "Ejemplo", "@", CORREO}
    for s in situaciones:
        prohibidos.add(str(s.incidencia.incidencia_id))
    assert [p for p in prohibidos if p in linea] == []
    for clave, valor in _campos_de_la_linea(linea).items():
        assert re.fullmatch(r"[a-z_.]+", clave), clave
        assert re.fullmatch(r"[0-9.\-]+|True|False|[A-Za-z]+", valor), (clave, valor)


def test_f065_r24_proceso_nuevo_es_propio_y_no_toca_el_del_listado(mundo, monkeypatch, caplog) -> None:
    """Pedir esta ruta no cambia el `proceso_nuevo` de la siguiente línea de F-060."""
    caplog.set_level(logging.INFO)
    modulo = _modulo()
    monkeypatch.setattr(tiempos, "_atendida", False)
    monkeypatch.setattr(modulo, "_atendida", False)

    _get()
    _get()

    nuevos = [_campos_de_la_linea(linea)["proceso_nuevo"] for linea in _lineas(caplog)]
    assert nuevos == ["True", "False"]
    # El indicador del listado sigue sin consumir: la próxima línea de F-060 dirá True.
    from infrastructure.documentos.plantilla_yaml import cargar_plantilla_yaml
    from interface_adapters.api import revision as modulo_revision

    from tests.utiles_importacion import EquivalenciasEnMemoria
    from tests.utiles_revision import (
        CatalogoDeLaObra,
        RevisionEnMemoria,
        UbicacionesQueCuentan,
        incidencia,
    )

    llamadas: list[str] = []
    modulo_revision.listar_revision(
        "9901",
        revision=RevisionEnMemoria(llamadas, (incidencia(),)),
        catalogo_obra=CatalogoDeLaObra(llamadas),
        equivalencias=EquivalenciasEnMemoria(llamadas),
        ubicaciones=UbicacionesQueCuentan(llamadas),
        configuracion=cargar_plantilla_yaml(),
    )
    (del_listado,) = [r.getMessage() for r in caplog.records if r.getMessage().startswith("F-060 tiempos del listado")]
    assert "proceso_nuevo=True" in del_listado


def test_f065_r24_el_borde_no_llama_al_indicador_del_listado() -> None:
    """La mitad estática: el módulo de la ruta no nombra `es_primera_peticion`."""
    fuente = (SERVICIO / "interface_adapters" / "api" / "sigrid_bandeja.py").read_text(encoding="utf-8")
    nombres = {n.id for n in ast.walk(ast.parse(fuente)) if isinstance(n, ast.Name)}
    importados = {
        a.name for n in ast.walk(ast.parse(fuente)) if isinstance(n, ast.ImportFrom) for a in n.names
    }

    assert "es_primera_peticion" not in nombres | importados
    assert "segundos_de_proceso" in importados


# ==========================================================================
# R26 · el listado de F-056 no cambia: no lee las reclamaciones
# ==========================================================================


def test_f065_r26_el_listado_y_las_acciones_no_construyen_el_lector_de_reclamaciones() -> None:
    fuente = (SERVICIO / "interface_adapters" / "api" / "revision.py").read_text(encoding="utf-8")

    assert "construir_reclamaciones_obra" not in fuente
    assert "sigrid_bandeja" not in fuente


def test_f065_r26_la_ruta_es_otra_funcion_y_get() -> None:
    from tests.utiles_rutas import ruta_registrada

    ajustes = ruta_registrada("revision_sigrid").get_trigger().get_dict_repr()
    assert ajustes["route"] == "revision/sigrid"
    assert [str(m.value).lower() for m in ajustes["methods"]] == ["get"]
    assert str(ajustes["authLevel"].value).lower() == "anonymous"
    assert ruta_registrada("revision").get_trigger().get_dict_repr()["route"] == "revision"


# ==========================================================================
# R35 · `Cache-Control: no-store` en esta ruta y en ninguna otra
# ==========================================================================


def test_f065_r35_la_respuesta_200_lleva_no_store(mundo) -> None:
    respuesta = _get()

    assert respuesta.status_code == 200
    assert respuesta.headers.get("Cache-Control") == "no-store"
    assert respuesta.mimetype == "application/json"


@pytest.mark.parametrize("caso", ["obra", "sigrid", "techo", "ambigua", "grande"])
def test_f065_r35_las_de_error_tambien(monkeypatch, caso) -> None:
    filas = obra_de_ejemplo()[1]
    if caso == "ambigua":
        filas = (*filas, fila("RS26.09/0999", obra_ref=OTRA_OBRA_REF))
    mundo = Mundo(
        (sit(1),),
        filas,
        al_techo=caso == "techo",
        fallo=CatalogoNoDisponible("sin red") if caso == "sigrid" else None,
    )
    if caso == "grande":
        mundo.con_la_bandeja(
            BandejaSoloLectura(mundo.llamadas, (sit(1),) * (TOPE_LECTURA_OBRA + 1), total=10_001)
        )
    _componer(monkeypatch, mundo)

    respuesta = _get({"obra": "%%"} if caso == "obra" else None)

    assert respuesta.status_code in {400, 409, 503}
    assert respuesta.headers.get("Cache-Control") == "no-store"


def test_f065_r35_ninguna_otra_ruta_lleva_no_store() -> None:
    import function_app

    salud = function_app.health(func.HttpRequest(method="GET", url="/api/health", body=b""))
    listado_mal_pedido = function_app.revision(
        func.HttpRequest(method="GET", url="/api/revision", params={"obra": "%%"}, body=b"")
    )

    assert salud.headers.get("Cache-Control") is None
    assert listado_mal_pedido.status_code == 400
    assert listado_mal_pedido.headers.get("Cache-Control") is None
    assert function_app._json({"a": 1}, 200).headers.get("Cache-Control") is None


def test_f065_r35_el_sin_cache_solo_lo_usa_esta_ruta() -> None:
    """La mitad estática: `_json_sin_cache` y `_sin_cache` solo se nombran en `revision_sigrid`."""
    arbol = ast.parse(FUNCTION_APP.read_text(encoding="utf-8"))
    quien_los_usa = {
        funcion.name
        for funcion in arbol.body
        if isinstance(funcion, ast.FunctionDef)
        for nodo in ast.walk(funcion)
        if isinstance(nodo, ast.Name) and nodo.id in {"_json_sin_cache", "_sin_cache"}
    }

    assert quien_los_usa == {"revision_sigrid", "_json_sin_cache"}
    assert "no-store" in FUNCTION_APP.read_text(encoding="utf-8")
    assert FUNCTION_APP.read_text(encoding="utf-8").count('"no-store"') == 1


# ==========================================================================
# R38 · la línea y el log de la ruta, sin textos (lo de las fichas, en datos_personales)
# ==========================================================================


def test_f065_r38_ningun_registro_de_la_ruta_lleva_un_texto_de_la_bandeja(mundo, caplog) -> None:
    caplog.set_level(logging.DEBUG)

    _get()

    texto = "\n".join(r.getMessage() for r in caplog.records)
    assert "Gotea el grifo" not in texto
    assert "Ejemplo de otra cosa" not in texto
    assert CORREO not in texto
