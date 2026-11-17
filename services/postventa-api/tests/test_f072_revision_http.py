# services/postventa-api/tests/test_f072_revision_http.py
"""La revisión lee los tipos de reclamación de Sigrid (F-072 T18, Bloque 6).

`specs/F-072-tipo-reclamacion-sigrid/design.md` §5 y §8: el borde HTTP de la
revisión (`interface_adapters/api/revision.py`, por las rutas de verdad de
`function_app`), la aplicación (`application/pipelines/revision.py`) y
`GET /api/bandeja`. Puertos inyectados por las fábricas del borde: ni red, ni
base, ni IA.

| Caso | Requisito |
|---|---|
| listar, editar y aprobar leen los tipos **una vez**, tras catálogo y ubicaciones; sin caché | R1 |
| la fuente de los tipos se construye tras el catálogo y las ubicaciones, antes de la base | R1 |
| descartar y recuperar ni construyen ni leen los tipos | R27 |
| `catalogo.listados` son los tipos leídos; `listado` de importados y vigentes, el tipo efectivo | R20, §8 |
| editar con un tipo vigente, con el que ya tiene (de baja) o con otro (400 en `listado`) | R21 |
| editar con `listado` nulo guarda `0002` | R22 |
| `tipo_fuera_de_sigrid` en la fila, en el resumen, en la respuesta de una acción y al aprobar | R24 |
| la lectura falla (503) o llega al techo (409): nada escrito | R3, R4 |
| `GET /api/bandeja` con el tipo efectivo en `listado` | §8 |

Datos ficticios: obra `9901`, tipos `9001`, `9002` y `9009` («TIPO FICTICIO N»),
correos `@ejemplo.invalid`; los identificadores, `UUID(int=n)`.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import azure.functions as func
import pytest
from application.pipelines.revision import aplicar_accion
from domain.models.errores import CatalogoNoDisponible, ConfiguracionSigridIncompleta
from domain.models.plantilla_incidencias import (
    TIPO_RECLAMACION_POR_DEFECTO,
    Listado,
    TipoReclamacion,
)
from domain.models.revision import (
    AccionRevision,
    PeticionDeAccion,
    Quien,
    ValoresPedidos,
)
from domain.ports.catalogo_obra import LecturaCatalogo
from domain.ports.tipos_reclamacion import FilaTipoReclamacion
from infrastructure.documentos.plantilla_yaml import cargar_plantilla_yaml
from interface_adapters.api import bandeja as modulo_bandeja
from interface_adapters.api import revision as modulo

from tests.utiles_importacion import (
    TIPOS_FICTICIOS,
    BandejaEnMemoria,
    EquivalenciasEnMemoria,
    TiposEnMemoria,
)
from tests.utiles_revision import (
    AHORA,
    CORREO,
    DESCRIPCION,
    OBRA,
    OID,
    U1,
    CatalogoDeLaObra,
    RevisionEnMemoria,
    UbicacionesQueCuentan,
    incidencia,
    prohibido,
)

A = AccionRevision

#: La configuración de verdad: desde el Bloque 5 el YAML no trae `listados`
#: (R9); los que se ofrecen y se aceptan son los leídos de Sigrid (R20, R21).
CONFIG = cargar_plantilla_yaml()

#: Un tipo que una incidencia tiene guardado y que ya no está vigente.
DE_BAJA = "9009"

ID1 = str(UUID(int=1))

#: Las lecturas de Sigrid, tal y como las anotan los dobles.
_DE_SIGRID = ("catalogo.", "ubicaciones", "tipos.")


# --------------------------------------------------------------------------
# El mundo de la prueba, compuesto por las fábricas del borde
# --------------------------------------------------------------------------


class PuertoDeTipos:
    """Un `TiposReclamacionPort` que anota cada lectura en la lista común.

    Lo devuelve `construir_tipos_reclamacion`: así el borde compone la fuente
    de verdad (`fuente_de_tipos` → `leer_tipos_reclamacion`) sobre él.
    """

    def __init__(
        self,
        llamadas: list[str],
        tipos: tuple[TipoReclamacion, ...] = TIPOS_FICTICIOS,
        *,
        fallo: Exception | None = None,
        al_techo: bool = False,
    ) -> None:
        self.llamadas = llamadas
        self.tipos = tipos
        self.fallo = fallo
        self.al_techo = al_techo
        self.lecturas = 0

    def leer(self) -> LecturaCatalogo[FilaTipoReclamacion]:
        self.lecturas += 1
        self.llamadas.append("tipos.leer")
        if self.fallo is not None:
            raise self.fallo
        return LecturaCatalogo(
            tuple(
                FilaTipoReclamacion(codigo=t.codigo, nombre=t.nombre, posicion=n)
                for n, t in enumerate(self.tipos, start=1)
            ),
            self.al_techo,
        )


class Mundo:
    def __init__(self, *incidencias) -> None:
        self.llamadas: list[str] = []
        self.revision = RevisionEnMemoria(self.llamadas, incidencias or (incidencia(),))
        self.catalogo = CatalogoDeLaObra(self.llamadas)
        self.ubicaciones = UbicacionesQueCuentan(self.llamadas)
        self.equivalencias = EquivalenciasEnMemoria(self.llamadas)
        self.tipos = PuertoDeTipos(self.llamadas)
        self.construidos: list[str] = []

    def de_sigrid(self) -> list[str]:
        return [c for c in self.llamadas if c.startswith(_DE_SIGRID)]


def _fabrica(mundo: Mundo, nombre: str, atributo: str):
    def construir(_ajustes: object) -> object:
        mundo.construidos.append(nombre)
        return getattr(mundo, atributo)

    return construir


@pytest.fixture
def mundo(monkeypatch) -> Mundo:
    mundo = Mundo()
    _componer(monkeypatch, mundo)
    return mundo


def _componer(monkeypatch, mundo: Mundo) -> None:
    monkeypatch.setattr(modulo, "obtener_ajustes", lambda: object())
    monkeypatch.setattr(modulo, "construir_revision", _fabrica(mundo, "revision", "revision"))
    monkeypatch.setattr(
        modulo, "construir_catalogo_obra", _fabrica(mundo, "catalogo", "catalogo")
    )
    monkeypatch.setattr(
        modulo, "construir_equivalencias", _fabrica(mundo, "equivalencias", "equivalencias")
    )
    monkeypatch.setattr(
        modulo, "construir_fuente_de_ubicaciones", _fabrica(mundo, "ubicaciones", "ubicaciones")
    )
    monkeypatch.setattr(
        modulo, "construir_tipos_reclamacion", _fabrica(mundo, "tipos", "tipos"), raising=False
    )
    monkeypatch.setattr(modulo, "configuracion_de_la_plantilla", lambda: CONFIG)


def _con(monkeypatch, *incidencias) -> Mundo:
    mundo = Mundo(*incidencias)
    _componer(monkeypatch, mundo)
    return mundo


def _ruta(nombre: str):
    import function_app

    return getattr(function_app, nombre)


def _listar(**params: str) -> func.HttpResponse:
    peticion = func.HttpRequest(
        method="GET", url="/api/revision", params={"obra": OBRA} | params, body=b""
    )
    return _ruta("revision")(peticion)


def _post(cuerpo: object) -> func.HttpResponse:
    peticion = func.HttpRequest(
        method="POST",
        url="/api/revision/acciones",
        body=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    return _ruta("revision_acciones")(peticion)


def _cuerpo(accion: str = "descartar", **cambios: object) -> dict[str, object]:
    cuerpo: dict[str, object] = {
        "incidencia_id": ID1,
        "accion": accion,
        "usuario_oid": OID,
        "usuario_correo": CORREO,
        "confirmado": True,
        "revision_previa": None,
    }
    if accion == "editar":
        cuerpo["valores"] = _valores()
    cuerpo.update(cambios)
    return cuerpo


def _valores(**cambios: object) -> dict[str, object]:
    valores: dict[str, object] = {
        "unidad_codigo": U1,
        "ubicacion": "Cocina",
        "descripcion": DESCRIPCION,
        "detalle": None,
        "oficio_codigo": "0046",
        "proveedor_codigo": "EJ07",
        "urgencia": None,
        "listado": None,
    }
    valores.update(cambios)
    return valores


def _leer(respuesta: func.HttpResponse) -> tuple[int, Any]:
    return respuesta.status_code, json.loads(respuesta.get_body().decode("utf-8"))


def _fila(datos: dict[str, Any], n: int) -> dict[str, Any]:
    (fila,) = [f for f in datos["incidencias"] if f["incidencia_id"] == str(UUID(int=n))]
    return fila


def _guardado(mundo: Mundo) -> str | None:
    return mundo.revision.guardadas[-1].revision.valores.tipo_reclamacion


# --------------------------------------------------------------------------
# R1 · una lectura por petición, tras el catálogo y las ubicaciones
# --------------------------------------------------------------------------


def test_f072_r1_listar_lee_los_tipos_una_vez_tras_catalogo_y_ubicaciones(mundo) -> None:
    estado, _ = _leer(_listar())

    assert estado == 200
    assert mundo.de_sigrid() == [
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "ubicaciones",
        "tipos.leer",
    ]
    assert mundo.tipos.lecturas == 1


def test_f072_r1_cada_listado_vuelve_a_leer_los_tipos(mundo) -> None:
    _listar()
    _listar()

    assert mundo.tipos.lecturas == 2


@pytest.mark.parametrize("accion", ["editar", "aprobar"])
def test_f072_r1_editar_y_aprobar_leen_los_tipos_una_vez_antes_de_escribir(
    mundo, accion: str
) -> None:
    cuerpo = _cuerpo(accion)
    if accion == "editar":
        cuerpo["valores"] = _valores(listado="9001")
    else:
        mundo.revision.sembrar(
            UUID(int=1), A.EDITAR, _vigentes_con(tipo_reclamacion="9001"), motivo=None
        )
        cuerpo["revision_previa"] = 1

    estado, _ = _leer(_post(cuerpo))

    assert estado == 200
    assert mundo.de_sigrid() == [
        "catalogo.leer_unidades",
        "catalogo.leer_oficios",
        "ubicaciones",
        "tipos.leer",
    ]
    assert mundo.llamadas.index("tipos.leer") < mundo.llamadas.index("revision.registrar")
    assert mundo.tipos.lecturas == 1


def test_f072_r1_cada_accion_vuelve_a_leer_los_tipos(mundo) -> None:
    assert _leer(_post(_cuerpo("editar", valores=_valores(listado="9001"))))[0] == 200
    assert _leer(_post(_cuerpo("aprobar", revision_previa=1)))[0] == 200

    assert mundo.tipos.lecturas == 2


def test_f072_r1_al_listar_los_tipos_se_construyen_tras_catalogo_y_ubicaciones(mundo) -> None:
    _listar()

    assert mundo.construidos == ["catalogo", "ubicaciones", "tipos", "revision", "equivalencias"]


@pytest.mark.parametrize("accion", ["editar", "aprobar"])
def test_f072_r1_al_actuar_los_tipos_se_construyen_tras_catalogo_y_ubicaciones(
    mundo, accion: str
) -> None:
    _post(_cuerpo(accion))

    assert mundo.construidos == ["catalogo", "ubicaciones", "tipos", "revision"]


@pytest.mark.parametrize("donde", ["listar", "editar", "aprobar"])
def test_f072_r1_sin_la_configuracion_de_los_tipos_es_503_sin_construir_la_base(
    monkeypatch, mundo, donde: str
) -> None:
    def falla(_ajustes: object) -> object:
        mundo.construidos.append("tipos")
        raise ConfiguracionSigridIncompleta("falta SIGRID_API_URL")

    monkeypatch.setattr(modulo, "construir_tipos_reclamacion", falla, raising=False)

    respuesta = _listar() if donde == "listar" else _post(_cuerpo(donde))

    assert respuesta.status_code == 503
    assert mundo.construidos == ["catalogo", "ubicaciones", "tipos"]
    assert mundo.revision.guardadas == []


def test_f072_r1_editar_sin_la_fuente_de_los_tipos_es_un_error_de_programacion() -> None:
    llamadas: list[str] = []
    revision = RevisionEnMemoria(llamadas, (incidencia(),))

    with pytest.raises(ValueError, match="necesitan leer Sigrid"):
        aplicar_accion(
            PeticionDeAccion(
                UUID(int=1),
                A.EDITAR,
                Quien(oid=OID, correo=CORREO),
                None,
                ValoresPedidos(**_valores(listado="9001")),  # type: ignore[arg-type]
                None,
            ),
            revision=revision,
            catalogo_obra=CatalogoDeLaObra(llamadas),
            listas=CONFIG.listas,
            ahora=AHORA,
            ubicaciones=UbicacionesQueCuentan(llamadas),
            tipos=None,
        )

    assert llamadas == ["revision.situacion"]


# --------------------------------------------------------------------------
# R27 · descartar y recuperar no leen los tipos
# --------------------------------------------------------------------------


def test_f072_r27_descartar_y_recuperar_ni_construyen_ni_leen_los_tipos(
    monkeypatch, mundo
) -> None:
    monkeypatch.setattr(
        modulo, "construir_tipos_reclamacion", prohibido("construir_tipos_reclamacion"),
        raising=False,
    )

    descartada = _leer(_post(_cuerpo("descartar")))
    recuperada = _leer(_post(_cuerpo("recuperar", revision_previa=1)))

    assert (descartada[0], recuperada[0]) == (200, 200)
    assert mundo.tipos.lecturas == 0
    assert "tipos" not in mundo.construidos
    assert descartada[1]["motivos_no_aprobable"] is None
    assert recuperada[1]["motivos_no_aprobable"] is None


@pytest.mark.parametrize("accion", ["descartar", "recuperar"])
def test_f072_r27_una_fuente_inyectada_no_se_llama_al_descartar_ni_al_recuperar(
    mundo, accion: str
) -> None:
    if accion == "recuperar":
        mundo.revision.sembrar(UUID(int=1), A.DESCARTAR, _vigentes_con(), motivo="Ejemplo")
    fuente = TiposEnMemoria()

    modulo.accion_de_revision(
        _cuerpo(accion, revision_previa=1 if accion == "recuperar" else None),
        revision=mundo.revision,
        tipos=fuente,
    )

    assert fuente.lecturas == 0


# --------------------------------------------------------------------------
# R20 · el catálogo y el tipo efectivo de cada fila
# --------------------------------------------------------------------------


def test_f072_r20_catalogo_listados_son_los_tipos_leidos(mundo) -> None:
    _, datos = _leer(_listar())

    assert datos["catalogo"]["listados"] == [
        {"codigo": "9001", "etiqueta": "TIPO FICTICIO 1 (9001)"},
        {"codigo": "9002", "etiqueta": "TIPO FICTICIO 2 (9002)"},
    ]


def test_f072_r20_sin_tipos_vigentes_no_se_ofrece_ninguno(mundo) -> None:
    mundo.tipos.tipos = ()

    estado, datos = _leer(_listar())

    assert (estado, datos["catalogo"]["listados"]) == (200, [])


def test_f072_r20_listado_de_importados_y_vigentes_es_el_tipo_efectivo(monkeypatch) -> None:
    mundo = _con(
        monkeypatch,
        incidencia(1, listado=Listado.PRIMERO),  # anterior a F-072: tipo nulo
        incidencia(2, tipo_reclamacion="9002"),
        incidencia(3, tipo_reclamacion="9002"),
    )
    mundo.revision.sembrar(
        UUID(int=3),
        A.EDITAR,
        _vigentes_con(n=3, tipo_reclamacion="9001"),
        motivo=None,
    )

    _, datos = _leer(_listar(estado="todas"))

    listados = {
        n: (_fila(datos, n)["importados"]["listado"], _fila(datos, n)["vigentes"]["listado"])
        for n in (1, 2, 3)
    }
    assert listados == {
        1: (TIPO_RECLAMACION_POR_DEFECTO, TIPO_RECLAMACION_POR_DEFECTO),
        2: ("9002", "9002"),
        3: ("9002", "9001"),
    }


def test_f072_r20_la_respuesta_de_una_accion_lleva_el_tipo_efectivo(mundo) -> None:
    estado, fila = _leer(_post(_cuerpo("editar", valores=_valores(listado="9002"))))

    assert estado == 200
    assert (fila["importados"]["listado"], fila["vigentes"]["listado"]) == (
        TIPO_RECLAMACION_POR_DEFECTO,
        "9002",
    )


# --------------------------------------------------------------------------
# R21, R22 · editar el tipo
# --------------------------------------------------------------------------


def test_f072_r21_editar_con_un_tipo_vigente_lo_guarda(mundo) -> None:
    estado, _ = _leer(_post(_cuerpo("editar", valores=_valores(listado="9002"))))

    assert estado == 200
    assert _guardado(mundo) == "9002"


def test_f072_r21_otro_tipo_es_400_en_listado_sin_repetirlo(mundo) -> None:
    pedido = "TIPO-QUE-NO-EXISTE-9876"

    respuesta = _post(_cuerpo("editar", valores=_valores(listado=pedido)))
    estado, datos = _leer(respuesta)

    assert estado == 400
    assert [e["campo"] for e in datos["errores"]] == ["listado"]
    assert pedido not in respuesta.get_body().decode("utf-8")
    assert mundo.revision.guardadas == []


def test_f072_r21_una_etiqueta_no_es_un_codigo(mundo) -> None:
    estado, datos = _leer(
        _post(_cuerpo("editar", valores=_valores(listado="TIPO FICTICIO 1 (9001)")))
    )

    assert (estado, [e["campo"] for e in datos["errores"]]) == (400, ["listado"])


def test_f072_r21_el_tipo_que_ya_tiene_se_conserva_aunque_este_de_baja(monkeypatch) -> None:
    mundo = _con(monkeypatch, incidencia(1, tipo_reclamacion=DE_BAJA))

    estado, fila = _leer(_post(_cuerpo("editar", valores=_valores(listado=DE_BAJA))))

    assert estado == 200
    assert _guardado(mundo) == DE_BAJA
    assert fila["vigentes"]["listado"] == DE_BAJA


def test_f072_r21_los_vigentes_son_los_leidos_en_esa_peticion(mundo) -> None:
    assert _leer(_post(_cuerpo("editar", valores=_valores(listado="9002"))))[0] == 200
    mundo.tipos.tipos = (TipoReclamacion(codigo="9001", nombre="TIPO FICTICIO 1"),)

    estado, datos = _leer(
        _post(
            _cuerpo(
                "editar",
                revision_previa=1,
                valores=_valores(listado="9002", ubicacion="Baño"),
            )
        )
    )

    # 9002 lo tiene ya guardado: se conserva (R21). Otro que ya no se lee, no.
    assert estado == 200
    estado, datos = _leer(
        _post(
            _cuerpo(
                "editar",
                revision_previa=2,
                valores=_valores(listado="9003", ubicacion="Cocina"),
            )
        )
    )
    assert (estado, [e["campo"] for e in datos["errores"]]) == (400, ["listado"])


def test_f072_r21_un_vigente_que_no_se_ha_leido_en_esta_peticion_no_vale(mundo) -> None:
    mundo.tipos.tipos = (TipoReclamacion(codigo="9001", nombre="TIPO FICTICIO 1"),)

    estado, datos = _leer(_post(_cuerpo("editar", valores=_valores(listado="9002"))))

    assert (estado, [e["campo"] for e in datos["errores"]]) == (400, ["listado"])


def test_f072_r22_editar_con_listado_nulo_guarda_0002(mundo) -> None:
    estado, fila = _leer(_post(_cuerpo("editar", valores=_valores(listado=None))))

    assert estado == 200
    assert _guardado(mundo) == TIPO_RECLAMACION_POR_DEFECTO
    assert fila["vigentes"]["listado"] == TIPO_RECLAMACION_POR_DEFECTO


# --------------------------------------------------------------------------
# R24 · el motivo `tipo_fuera_de_sigrid`
# --------------------------------------------------------------------------


def test_f072_r24_un_tipo_guardado_fuera_de_sigrid_es_motivo_en_la_fila(monkeypatch) -> None:
    mundo = _con(
        monkeypatch,
        incidencia(1, tipo_reclamacion=DE_BAJA),
        incidencia(2, tipo_reclamacion="9001"),
        incidencia(3),  # sin tipo guardado: no se mira (R24)
    )

    _, datos = _leer(_listar(estado="todas"))

    assert "tipo_fuera_de_sigrid" in _fila(datos, 1)["motivos_no_aprobable"]
    assert "tipo_fuera_de_sigrid" not in _fila(datos, 2)["motivos_no_aprobable"]
    assert "tipo_fuera_de_sigrid" not in _fila(datos, 3)["motivos_no_aprobable"]
    assert datos["resumen"]["por_motivo"]["tipo_fuera_de_sigrid"] == 1
    assert mundo.tipos.lecturas == 1


def test_f072_r24_aprobarla_es_409_con_el_motivo_y_sin_escribir(monkeypatch) -> None:
    mundo = _con(monkeypatch, incidencia(1, tipo_reclamacion=DE_BAJA))

    estado, datos = _leer(_post(_cuerpo("aprobar")))

    assert estado == 409
    assert "tipo_fuera_de_sigrid" in datos["motivos"]
    assert mundo.revision.guardadas == []


def test_f072_r24_la_respuesta_de_editar_lleva_el_motivo(monkeypatch) -> None:
    _con(monkeypatch, incidencia(1, tipo_reclamacion=DE_BAJA))

    estado, fila = _leer(_post(_cuerpo("editar", valores=_valores(listado=DE_BAJA))))

    assert estado == 200
    assert "tipo_fuera_de_sigrid" in fila["motivos_no_aprobable"]


def test_f072_r24_con_un_tipo_vigente_se_aprueba(mundo) -> None:
    assert _leer(_post(_cuerpo("editar", valores=_valores(listado="9001"))))[0] == 200

    estado, fila = _leer(_post(_cuerpo("aprobar", revision_previa=1)))

    assert (estado, fila["estado"], fila["motivos_no_aprobable"]) == (200, "aprobada", [])
    assert _guardado(mundo) == "9001"


def test_f072_r24_el_0002_de_un_nulo_se_aprueba_si_esta_vigente(mundo) -> None:
    mundo.tipos.tipos = (
        *TIPOS_FICTICIOS,
        TipoReclamacion(codigo=TIPO_RECLAMACION_POR_DEFECTO, nombre="TIPO FICTICIO 3"),
    )
    assert _leer(_post(_cuerpo("editar", valores=_valores(listado=None))))[0] == 200

    estado, _ = _leer(_post(_cuerpo("aprobar", revision_previa=1)))

    assert estado == 200


# --------------------------------------------------------------------------
# R3, R4 · la lectura falla o llega al techo: nada escrito
# --------------------------------------------------------------------------


def _peticion(donde: str) -> func.HttpResponse:
    if donde == "listar":
        return _listar()
    if donde == "editar":
        return _post(_cuerpo("editar", valores=_valores(listado="9001")))
    return _post(_cuerpo("aprobar"))


@pytest.mark.parametrize("donde", ["listar", "editar", "aprobar"])
def test_f072_r3_si_la_lectura_de_tipos_falla_es_503_sin_escribir(mundo, donde: str) -> None:
    mundo.tipos.fallo = CatalogoNoDisponible("Sigrid no responde")

    estado, _ = _leer(_peticion(donde))

    assert estado == 503
    assert mundo.revision.guardadas == []
    assert "revision.registrar" not in mundo.llamadas


@pytest.mark.parametrize("donde", ["listar", "editar", "aprobar"])
def test_f072_r4_si_los_tipos_llegan_al_techo_es_409_sin_escribir(mundo, donde: str) -> None:
    mundo.tipos.al_techo = True

    estado, datos = _leer(_peticion(donde))

    assert (estado, datos["codigo"]) == (409, "catalogo_sin_verificar")
    assert mundo.revision.guardadas == []
    assert "revision.registrar" not in mundo.llamadas


# --------------------------------------------------------------------------
# §8 · GET /api/bandeja con el tipo efectivo
# --------------------------------------------------------------------------


def test_f072_s8_la_bandeja_lleva_el_tipo_efectivo_en_listado(monkeypatch) -> None:
    import function_app

    doble = BandejaEnMemoria(
        [],
        incidencias=(
            incidencia(1, listado=Listado.SEGUNDO),  # anterior a F-072
            incidencia(2, tipo_reclamacion="9001"),
            incidencia(3, tipo_reclamacion=DE_BAJA, listado=Listado.PRIMERO),
        ),
    )

    def envoltura(obra, limite=None):
        return modulo_bandeja.leer_bandeja(obra, limite, bandeja=doble)

    monkeypatch.setattr(function_app, "leer_bandeja", envoltura)
    respuesta = function_app.bandeja(
        func.HttpRequest(method="GET", url="/api/bandeja", params={"obra": OBRA}, body=b"")
    )

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.get_body())
    assert [i["listado"] for i in cuerpo["incidencias"]] == [
        TIPO_RECLAMACION_POR_DEFECTO,
        "9001",
        DE_BAJA,
    ]


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------


def _vigentes_con(n: int = 1, **cambios: object):
    from dataclasses import replace

    from domain.models.revision import valores_importados

    return replace(valores_importados(incidencia(n)), ubicacion="Cocina", **cambios)
