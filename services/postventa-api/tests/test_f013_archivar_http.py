# services/postventa-api/tests/test_f013_archivar_http.py
"""F-013 T13 · el borde de `POST /api/archivar` con la estrategia `posventa`.

Cubre R2, R19, R23 y R41 de `specs/F-013-archivo-posventa/requirements.md`
**desde el endpoint**: la composición de `interface_adapters/api/archivar.py`
(`design.md` §2.2) y la traducción de errores de `function_app.py`.

## Lo que se afirma aquí y no en los tests del paso

El paso y el resolutor ya están probados con dobles (T9, T10). Lo que solo se
ve en el borde es **cómo se montan**:

- en `por_obra` —el valor por omisión— el borde hace **exactamente** lo de
  F-006: ni se construye el lector de Sigrid ni se lista una carpeta (R2);
- en `posventa`, el resolutor se compone con `functools.partial` y **toda** la
  configuración (`SHAREPOINT_CARPETA_BASE`, los dos tramos, la hoja
  alternativa y `SHAREPOINT_CREAR_CARPETAS`) llega a él;
- la **misma instancia** que devuelve `construir_archivador` es archivador y
  explorador (`design.md` §3.2; decisión 1 del cierre del bloque 2);
- `construir_ubicaciones` va **después** de `construir_archivador` (así, fuera
  de `dev`/`pro`, el error es el del archivo) y solo en `posventa`;
- `DestinoNoResuelto` → **409** `{"error", "motivo", "candidatas"}` (R19), y
  `UbicacionNoDisponible` / `ConfiguracionSigridIncompleta` → **503** (R41);
- ni el `con.res` de la unidad (`unidad_nombre`) ni la referencia de obra del
  ERP (`obra_ref`) salen en un log ni en una respuesta (R23).

Los dobles se inyectan por las costuras del handler (`archivador`,
`repositorio`, `explorador`, `ubicaciones`) o sustituyendo las fábricas que
`archivar.py` tiene importadas: nada de Graph, Sigrid ni PostgreSQL. Ni un
dato real: el árbol es el medido de la 0677 **sin nombres de persona**, y los
nombres de persona que aparecen aquí son inventados para comprobar que no
salen.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence

import azure.functions as func
import pytest
from config.settings import obtener_ajustes
from domain.models.destino_posventa import UbicacionReclamacion, UnidadDeObra
from domain.models.errores import (
    ConfiguracionSigridIncompleta,
    UbicacionNoDisponible,
)
from domain.models.estado import SituacionParte
from interface_adapters.api import archivar

from tests.utiles_destino import (
    ALTERNATIVA,
    CARPETA_OBRA_0677,
    FIRMADOS,
    INCIDENCIAS,
    RES_OBRA_0677,
    UNIDADES_0677,
    ExploradorFalso,
    UbicacionesFalsas,
    arbol_0677,
    reclamacion_0677,
    ubicacion_0677,
    ubicaciones_0677,
)
from tests.utiles_sharepoint import ArchivoPortFalso, BibliotecaFalsa, RepositorioFalso
from tests.utiles_validacion import veredicto_apto

_FRONTERA = "frontera-sintetica-de-test-f013"

HASH = "9f2b0013aabb"
PDF = b"%PDF-1.4 Fdo. Cliente Inventado DNI 00000000T"

OBRA = CARPETA_OBRA_0677
INC = f"{OBRA}/{INCIDENCIAS}"

#: El cuerpo del 409 de R19: estas tres claves y **ninguna más**.
CLAVES_DEL_409 = {"error", "motivo", "candidatas"}

#: R23 · lo que no puede salir en ningún log ni en ninguna respuesta. Son
#: **inventados** y reconocibles: si aparecen, el caso lo ve.
PERSONA_INVENTADA = "Fulanito Inventadez"
OTRA_PERSONA_INVENTADA = "Menganita Ficticia"
OBRA_REF_INVENTADA = "obra-ref-inventada-7c1"


def _villa(n: int) -> str:
    return f"{INC}/VILLA {n:02d}"


# --------------------------------------------------------------------------
# Material
# --------------------------------------------------------------------------


class ArchivadorDePosventa(ArchivoPortFalso):
    """`ArchivoPort` **y** `ExploradorBibliotecaPort` en una sola instancia.

    Es lo que es el adaptador de Graph en `posventa`: la subida va a la
    `BibliotecaFalsa` de F-006 y las carpetas al `ExploradorFalso` de T8.
    """

    def __init__(self, explorador: ExploradorFalso | None = None, **extra) -> None:
        self.explorador = explorador if explorador is not None else ExploradorFalso(arbol_0677())
        super().__init__(registro=self.explorador.registro, **extra)

    def listar_carpetas(self, *, carpeta: str) -> tuple[str, ...] | None:
        return self.explorador.listar_carpetas(carpeta=carpeta)

    def crear_subcarpeta(self, *, padre: str, nombre: str) -> None:
        self.explorador.crear_subcarpeta(padre=padre, nombre=nombre)


def _formulario(n: int) -> tuple[tuple[str, str], ...]:
    """El cuerpo de un parte apto de la villa `n` de la 0677, todo inventado."""
    return (
        ("hash", HASH),
        ("codigo_obra", "0677"),
        ("numero_incidencia", reclamacion_0677(n)),
        ("veredicto", "apto"),
        ("destino", "archivo_y_cierre"),
    )


def _repositorio(n: int) -> RepositorioFalso:
    """El veredicto **guardado** del parte de la villa `n` (F-030, F-031)."""
    return RepositorioFalso(
        situacion=SituacionParte(
            validacion=veredicto_apto(
                hash_parte=HASH, numero_incidencia=reclamacion_0677(n)
            )
        )
    )


def _peticion(campos: Sequence[tuple[str, str]]) -> func.HttpRequest:
    """Petición `multipart/form-data` con un PDF y esos campos."""
    cuerpo = (
        f"--{_FRONTERA}\r\n"
        'Content-Disposition: form-data; name="fichero"; filename="parte.pdf"\r\n'
        "Content-Type: application/pdf\r\n\r\n"
    ).encode() + PDF + b"\r\n"
    for nombre, valor in campos:
        cuerpo += (
            f"--{_FRONTERA}\r\n"
            f'Content-Disposition: form-data; name="{nombre}"\r\n\r\n{valor}\r\n'
        ).encode()
    cuerpo += f"--{_FRONTERA}--\r\n".encode()
    return func.HttpRequest(
        method="POST",
        url="/api/archivar",
        headers={"Content-Type": f"multipart/form-data; boundary={_FRONTERA}"},
        body=cuerpo,
    )


def _cuerpo(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


def _con_costuras(monkeypatch, **costuras) -> None:
    """La ruta de verdad de `function_app`, con las costuras del handler puestas."""
    import function_app

    def envoltura(contenido: bytes, **datos):
        return archivar.archivar_parte(contenido, **costuras, **datos)

    monkeypatch.setattr(function_app, "archivar_parte", envoltura)


def _archivar(n: int):
    import function_app

    return function_app.archivar(_peticion(_formulario(n)))


@pytest.fixture
def estrategia(monkeypatch):
    """Fija la estrategia y la configuración de destino **explícitas**.

    Todas las variables de destino se escriben aquí, con sus valores por
    omisión de la spec, para que ningún caso dependa del `.env` de quien
    ejecute la suite. Cada caso cambia solo lo que le importa.
    """

    def _fijar(valor: str = "posventa", **variables: str) -> None:
        base = {
            "SHAREPOINT_ESTRUCTURA": valor,
            "SHAREPOINT_CARPETA_BASE": "" if valor == "posventa" else "Postventa",
            "SHAREPOINT_CARPETA_INCIDENCIAS": INCIDENCIAS,
            "SHAREPOINT_CARPETA_FIRMADOS": FIRMADOS,
            "SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA": ALTERNATIVA,
            "SHAREPOINT_CREAR_CARPETAS": "true",
            "SHAREPOINT_DRIVE_ID": "drive-inventado-posventa",
        }
        base.update(variables)
        for nombre, contenido in base.items():
            monkeypatch.setenv(nombre, contenido)
        obtener_ajustes.cache_clear()

    return _fijar


@pytest.fixture
def fabricas(monkeypatch):
    """Sustituye las tres fábricas que usa `archivar.py` y apunta el orden.

    `construidas` es la lista de lo que se construyó, en orden; cada fábrica
    devuelve lo que el caso le haya dado (o falla con lo que le haya dado).
    """

    class _Fabricas:
        def __init__(self) -> None:
            self.construidas: list[str] = []
            self.archivador: object = ArchivadorDePosventa()
            self.repositorio: object = None
            self.ubicaciones: object = None
            self.fallo_ubicaciones: Exception | None = None

    estado = _Fabricas()

    def _archivador(ajustes):
        estado.construidas.append("archivador")
        return estado.archivador

    def _repositorio(ajustes):
        estado.construidas.append("repositorio")
        return estado.repositorio

    def _ubicaciones(ajustes):
        estado.construidas.append("ubicaciones")
        if estado.fallo_ubicaciones is not None:
            raise estado.fallo_ubicaciones
        return estado.ubicaciones

    monkeypatch.setattr(archivar, "construir_archivador", _archivador)
    monkeypatch.setattr(archivar, "construir_repositorio", _repositorio)
    monkeypatch.setattr(archivar, "construir_ubicaciones", _ubicaciones)
    return estado


# --------------------------------------------------------------------------
# R2 · en `por_obra`, el borde de siempre
# --------------------------------------------------------------------------


def test_f013_r2_en_por_obra_no_se_construye_la_ubicacion_ni_se_lista(
    estrategia, fabricas
):
    """R2 · `por_obra`: ni `construir_ubicaciones`, ni un listado, ni Sigrid.

    El archivador es capaz de listar —es el de `posventa`—, y precisamente por
    eso se ve que nadie se lo pide: la carpeta sale de `componer_destino` y se
    asegura con `asegurar_carpeta`, como en F-006.
    """
    import function_app

    estrategia("por_obra")
    fabricas.repositorio = _repositorio(5)

    respuesta = function_app.archivar(_peticion(_formulario(5)))

    assert respuesta.status_code == 200
    assert _cuerpo(respuesta)["carpeta"] == "Postventa/0677"
    assert fabricas.construidas == ["archivador", "repositorio"]
    assert fabricas.archivador.explorador.llamadas == []
    assert [nombre for nombre, _ in fabricas.archivador.llamadas] == [
        "asegurar_carpeta",
        "buscar",
        "subir",
    ]


def test_f013_r2_por_omision_es_por_obra(monkeypatch, fabricas):
    """R2 · sin `SHAREPOINT_ESTRUCTURA`, el borde es el de F-006.

    Es el caso del despliegue que no la escribe: el comportamiento desplegado
    no cambia hasta que alguien pone `posventa` a propósito.
    """
    import function_app

    monkeypatch.delenv("SHAREPOINT_ESTRUCTURA", raising=False)
    monkeypatch.setenv("SHAREPOINT_CARPETA_BASE", "Postventa")
    obtener_ajustes.cache_clear()
    fabricas.repositorio = _repositorio(5)

    respuesta = function_app.archivar(_peticion(_formulario(5)))

    assert respuesta.status_code == 200
    assert _cuerpo(respuesta)["carpeta"] == "Postventa/0677"
    assert "ubicaciones" not in fabricas.construidas
    assert fabricas.archivador.explorador.llamadas == []


def test_f013_r2_en_por_obra_las_costuras_nuevas_no_se_tocan(estrategia, monkeypatch):
    """R2 · aunque lleguen un explorador y unas ubicaciones, en `por_obra` no se usan."""
    estrategia("por_obra")
    explorador = ExploradorFalso(arbol_0677())
    ubicaciones = ubicaciones_0677()
    archivador = ArchivadorDePosventa()
    _con_costuras(
        monkeypatch,
        archivador=archivador,
        repositorio=_repositorio(5),
        explorador=explorador,
        ubicaciones=ubicaciones,
    )

    respuesta = _archivar(5)

    assert respuesta.status_code == 200
    assert explorador.llamadas == []
    assert ubicaciones.llamadas == []
    assert archivador.explorador.llamadas == []


# --------------------------------------------------------------------------
# La composición en `posventa`
# --------------------------------------------------------------------------


def test_f013_t13_posventa_archiva_en_la_carpeta_medida(estrategia, monkeypatch):
    """La villa 5 de la 0677: la ruta existe entera y se resuelve sin crear nada."""
    estrategia()
    archivador = ArchivadorDePosventa()
    _con_costuras(
        monkeypatch,
        archivador=archivador,
        repositorio=_repositorio(5),
        ubicaciones=ubicaciones_0677(),
    )

    respuesta = _archivar(5)

    assert respuesta.status_code == 200
    cuerpo = _cuerpo(respuesta)
    assert cuerpo["carpeta"] == f"{_villa(5)}/{FIRMADOS}"
    assert cuerpo["estado"] == "archivado"
    assert cuerpo["avisos"] == []
    assert archivador.biblioteca.subidas == 1
    assert archivador.explorador.creaciones == []
    assert archivador.explorador.listados == ["", OBRA, INC, _villa(5)]
    # R15 · en `posventa`, nunca `asegurar_carpeta`.
    assert "asegurar_carpeta" not in [nombre for nombre, _ in archivador.llamadas]


def test_f013_t13_posventa_crea_lo_que_falta_con_el_mismo_archivador(
    estrategia, fabricas
):
    """La villa 13: crea `VILLA 13` y su hoja, y **con la misma instancia** que sube.

    Sin costuras: el archivador sale de `construir_archivador` (sustituida),
    y es él quien lista, crea y sube. `construir_archivador` se llama **una**
    vez: un segundo adaptador para listar sería otra biblioteca posible.
    """
    import function_app

    estrategia()
    fabricas.repositorio = _repositorio(13)
    fabricas.ubicaciones = ubicaciones_0677()

    respuesta = function_app.archivar(_peticion(_formulario(13)))

    assert respuesta.status_code == 200
    cuerpo = _cuerpo(respuesta)
    assert cuerpo["carpeta"] == f"{_villa(13)}/{FIRMADOS}"
    archivador = fabricas.archivador
    assert fabricas.construidas.count("archivador") == 1
    assert archivador.explorador.creaciones == [
        (INC, "VILLA 13"),
        (_villa(13), FIRMADOS),
    ]
    assert archivador.biblioteca.subidas == 1
    assert len(cuerpo["avisos"]) == 2
    assert all("biblioteca de Posventa" in aviso for aviso in cuerpo["avisos"])


def test_f013_t13_el_orden_de_construccion_en_posventa(estrategia, fabricas):
    """(b) del bloque 3 · la ubicación, **después** del archivador (y del repositorio).

    El orden entre archivador y repositorio es el de F-006; la ubicación va
    detrás porque es lo nuevo y solo de `posventa`.
    """
    import function_app

    estrategia()
    fabricas.repositorio = _repositorio(5)
    fabricas.ubicaciones = ubicaciones_0677()

    function_app.archivar(_peticion(_formulario(5)))

    assert fabricas.construidas == ["archivador", "repositorio", "ubicaciones"]


def test_f013_t13_fuera_de_dev_y_pro_el_error_es_el_del_archivo(estrategia, monkeypatch):
    """(b) · con `ENTORNO=test` y nada inyectado: 503 del archivador, sin leer Sigrid.

    La fábrica de la ubicación, de verdad pero espiada, **no** se llega a
    llamar: la del archivo se niega antes.
    """
    import function_app

    estrategia()
    llamadas: list[str] = []
    real = archivar.construir_ubicaciones

    def espia(ajustes):
        llamadas.append("ubicaciones")
        return real(ajustes)

    monkeypatch.setattr(archivar, "construir_ubicaciones", espia)

    respuesta = function_app.archivar(_peticion(_formulario(5)))

    assert respuesta.status_code == 503
    assert llamadas == []
    assert "Sigrid" not in _cuerpo(respuesta)["error"]


def test_f013_t13_la_costura_del_explorador_se_usa_para_listar(estrategia, monkeypatch):
    """La costura `explorador` es lo que recibe el resolutor para listar.

    Otro árbol, reconocible, en el explorador inyectado: la carpeta sale de él
    y el del archivador no recibe ni un listado.
    """
    estrategia()
    otro = {**arbol_0677(), "": (OBRA, "OTRA CARPETA INVENTADA")}
    explorador = ExploradorFalso(otro)
    archivador = ArchivadorDePosventa()
    _con_costuras(
        monkeypatch,
        archivador=archivador,
        repositorio=_repositorio(5),
        explorador=explorador,
        ubicaciones=ubicaciones_0677(),
    )

    respuesta = _archivar(5)

    assert respuesta.status_code == 200
    assert explorador.listados == ["", OBRA, INC, _villa(5)]
    assert archivador.explorador.llamadas == []


@pytest.mark.parametrize(
    ("variables", "arbol", "carpeta"),
    [
        pytest.param(
            {"SHAREPOINT_CARPETA_BASE": "BASE INVENTADA"},
            {
                "": ("BASE INVENTADA",),
                "BASE INVENTADA": (OBRA,),
                f"BASE INVENTADA/{OBRA}": (INCIDENCIAS,),
                f"BASE INVENTADA/{INC}": ("VILLA 05",),
                f"BASE INVENTADA/{_villa(5)}": (FIRMADOS,),
            },
            f"BASE INVENTADA/{_villa(5)}/{FIRMADOS}",
            id="base",
        ),
        pytest.param(
            {
                "SHAREPOINT_CARPETA_INCIDENCIAS": "TRAMO INVENTADO",
                "SHAREPOINT_CARPETA_FIRMADOS": "HOJA INVENTADA",
            },
            {
                "": (OBRA,),
                OBRA: ("TRAMO INVENTADO",),
                f"{OBRA}/TRAMO INVENTADO": ("VILLA 05",),
                f"{OBRA}/TRAMO INVENTADO/VILLA 05": ("HOJA INVENTADA",),
            },
            f"{OBRA}/TRAMO INVENTADO/VILLA 05/HOJA INVENTADA",
            id="tramos",
        ),
        pytest.param(
            {"SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA": "HOJA ALTERNATIVA INVENTADA"},
            {
                "": (OBRA,),
                OBRA: (INCIDENCIAS,),
                INC: ("VILLA 05",),
                _villa(5): ("HOJA ALTERNATIVA INVENTADA",),
            },
            f"{_villa(5)}/HOJA ALTERNATIVA INVENTADA",
            id="alternativa",
        ),
    ],
)
def test_f013_t13_la_configuracion_de_destino_llega_al_resolutor(
    estrategia, monkeypatch, variables, arbol, carpeta
):
    """Cada variable de destino llega al `partial`, y no un valor fijo.

    Árboles inventados, con nombres que solo casan si la variable llegó: con
    el valor por omisión, el mismo caso daría 409.
    """
    estrategia(**variables)
    archivador = ArchivadorDePosventa(ExploradorFalso(arbol))
    _con_costuras(
        monkeypatch,
        archivador=archivador,
        repositorio=_repositorio(5),
        ubicaciones=ubicaciones_0677(),
    )

    respuesta = _archivar(5)

    assert respuesta.status_code == 200, _cuerpo(respuesta)
    assert _cuerpo(respuesta)["carpeta"] == carpeta
    assert archivador.explorador.creaciones == []


def test_f013_t13_crear_carpetas_apagado_llega_al_resolutor(estrategia, monkeypatch):
    """`SHAREPOINT_CREAR_CARPETAS=false`: la villa 13 da 409 y no se crea nada."""
    estrategia(SHAREPOINT_CREAR_CARPETAS="false")
    archivador = ArchivadorDePosventa()
    _con_costuras(
        monkeypatch,
        archivador=archivador,
        repositorio=_repositorio(13),
        ubicaciones=ubicaciones_0677(),
    )

    respuesta = _archivar(13)

    assert respuesta.status_code == 409
    assert _cuerpo(respuesta)["motivo"] == "sin_carpeta_unidad"
    assert archivador.explorador.creaciones == []
    assert archivador.biblioteca.subidas == 0


def test_f013_t13_alternativa_vacia_llega_al_resolutor(estrategia, monkeypatch):
    """Alternativa vacía: la `PARTES FIRMADO` de la villa 2 pasa a ser parecida (R49)."""
    estrategia(SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA="")
    archivador = ArchivadorDePosventa()
    _con_costuras(
        monkeypatch,
        archivador=archivador,
        repositorio=_repositorio(2),
        ubicaciones=ubicaciones_0677(),
    )

    respuesta = _archivar(2)

    assert respuesta.status_code == 409
    assert _cuerpo(respuesta)["motivo"] == "firmados_parecida"
    assert _cuerpo(respuesta)["candidatas"] == [ALTERNATIVA]


def test_f013_t13_una_estrategia_desconocida_no_se_adivina(estrategia, monkeypatch):
    """R3 · con el archivador inyectado, una estrategia desconocida es 503.

    En producción `construir_archivador` la rechaza antes; aquí se comprueba
    que el borde tampoco la toma por una de las dos: ni sube a `<base>/<obra>`
    ni lee Sigrid ni lista.
    """
    estrategia("posventa ")
    archivador = ArchivadorDePosventa()
    ubicaciones = ubicaciones_0677()
    _con_costuras(
        monkeypatch,
        archivador=archivador,
        repositorio=_repositorio(5),
        ubicaciones=ubicaciones,
    )

    respuesta = _archivar(5)

    assert respuesta.status_code == 503
    assert "SHAREPOINT_ESTRUCTURA" in _cuerpo(respuesta)["error"]
    assert archivador.llamadas == []
    assert archivador.explorador.llamadas == []
    assert ubicaciones.llamadas == []


def test_f013_t13_campos_obligatorios_no_cambian():
    """`CAMPOS_OBLIGATORIOS` sigue siendo el de F-006/F-031 (`design.md` §2.2)."""
    assert archivar.CAMPOS_OBLIGATORIOS == (
        "hash",
        "codigo_obra",
        "numero_incidencia",
        "veredicto",
        "destino",
    )


# --------------------------------------------------------------------------
# R19 · destino no resuelto → 409
# --------------------------------------------------------------------------


def test_f013_r19_destino_no_resuelto_responde_409_con_motivo_y_candidatas(
    estrategia, monkeypatch, caplog
):
    """R19 · dos carpetas de obra casan: 409, el código y los **nombres**.

    Ni se sube ni se crea nada, y la traza queda en `error` con el código del
    motivo (R18). El texto dice qué tiene que hacer una persona.
    """
    estrategia()
    arbol = {**arbol_0677(), "": (OBRA, "0677 SEGUNDA INVENTADA")}
    archivador = ArchivadorDePosventa(ExploradorFalso(arbol))
    repositorio = _repositorio(5)
    _con_costuras(
        monkeypatch,
        archivador=archivador,
        repositorio=repositorio,
        ubicaciones=ubicaciones_0677(),
    )

    with caplog.at_level(logging.INFO, logger="function_app"):
        respuesta = _archivar(5)

    assert respuesta.status_code == 409
    assert respuesta.mimetype == "application/json"
    cuerpo = _cuerpo(respuesta)
    assert set(cuerpo) == CLAVES_DEL_409
    assert cuerpo["motivo"] == "obra_ambigua"
    assert cuerpo["candidatas"] == [OBRA, "0677 SEGUNDA INVENTADA"]
    assert "no se ha subido nada" in cuerpo["error"]
    assert "una persona" in cuerpo["error"]
    assert archivador.biblioteca.subidas == 0
    assert archivador.explorador.creaciones == []
    assert repositorio.ultima_traza.estado.value == "error"
    assert repositorio.ultima_traza.motivo == "obra_ambigua"
    assert "motivo=obra_ambigua" in caplog.text


def test_f013_r19_sin_candidatas_la_lista_va_vacia(estrategia, monkeypatch):
    """R19 · `candidatas` va siempre, vacía si no hay carpeta implicada."""
    estrategia()
    _con_costuras(
        monkeypatch,
        archivador=ArchivadorDePosventa(),
        repositorio=_repositorio(5),
        ubicaciones=UbicacionesFalsas(unidades=UNIDADES_0677),
    )

    respuesta = _archivar(5)

    assert respuesta.status_code == 409
    cuerpo = _cuerpo(respuesta)
    assert set(cuerpo) == CLAVES_DEL_409
    assert cuerpo["motivo"] == "reclamacion_no_localizada"
    assert cuerpo["candidatas"] == []


# --------------------------------------------------------------------------
# R41 · Sigrid no responde o no está configurada → 503
# --------------------------------------------------------------------------


def test_f013_r41_la_ubicacion_no_disponible_responde_503(estrategia, monkeypatch):
    """R41 · Sigrid no dice dónde va: 503, sin listar, sin crear, sin subir, sin traza."""
    estrategia()
    archivador = ArchivadorDePosventa()
    repositorio = _repositorio(5)
    _con_costuras(
        monkeypatch,
        archivador=archivador,
        repositorio=repositorio,
        ubicaciones=ubicaciones_0677(
            fallo_al_ubicar=UbicacionNoDisponible("la pasarela no ha respondido")
        ),
    )

    respuesta = _archivar(5)

    assert respuesta.status_code == 503
    cuerpo = _cuerpo(respuesta)
    assert set(cuerpo) == {"error"}
    assert "Sigrid" in cuerpo["error"]
    assert "no se ha subido nada" in cuerpo["error"]
    assert "la pasarela no ha respondido" in cuerpo["error"]
    assert archivador.explorador.llamadas == []
    assert archivador.biblioteca.subidas == 0
    assert repositorio.archivos == []


def test_f013_r41_la_segunda_lectura_caida_tambien_es_503(estrategia, monkeypatch):
    """R41 · también si la que falla es la de las unidades del número."""
    estrategia()
    archivador = ArchivadorDePosventa()
    _con_costuras(
        monkeypatch,
        archivador=archivador,
        repositorio=_repositorio(5),
        ubicaciones=ubicaciones_0677(
            fallo_al_leer_unidades=UbicacionNoDisponible("tiempo agotado")
        ),
    )

    respuesta = _archivar(5)

    assert respuesta.status_code == 503
    assert archivador.explorador.llamadas == []


def test_f013_r41_sigrid_sin_configurar_responde_503(estrategia, fabricas):
    """R41 · falta configuración de `sigrid-api`: 503 y el nombre de la variable."""
    import function_app

    estrategia()
    fabricas.repositorio = _repositorio(5)
    fabricas.fallo_ubicaciones = ConfiguracionSigridIncompleta(
        "faltan variables para leer de Sigrid: SIGRID_API_KEY"
    )

    respuesta = function_app.archivar(_peticion(_formulario(5)))

    assert respuesta.status_code == 503
    cuerpo = _cuerpo(respuesta)
    assert "SIGRID_API_KEY" in cuerpo["error"]
    assert "no se ha subido nada" in cuerpo["error"]
    assert fabricas.archivador.llamadas == []
    assert fabricas.archivador.explorador.llamadas == []


def test_f013_r41_la_fabrica_real_de_la_ubicacion_se_niega_fuera_de_dev_y_pro(
    estrategia, monkeypatch
):
    """Con archivador y repositorio inyectados y `ENTORNO=test`, la fábrica real
    de la ubicación se niega (`ArchivoDeshabilitado`): 503 y nada listado."""
    estrategia()
    archivador = ArchivadorDePosventa()
    _con_costuras(monkeypatch, archivador=archivador, repositorio=_repositorio(5))

    respuesta = _archivar(5)

    assert respuesta.status_code == 503
    assert "Sigrid" in _cuerpo(respuesta)["error"]
    assert archivador.explorador.llamadas == []
    assert archivador.biblioteca.subidas == 0


# --------------------------------------------------------------------------
# R23 · ni `unidad_nombre` ni `obra_ref`, en ningún log ni respuesta
# --------------------------------------------------------------------------


def _ubicaciones_con_datos_sensibles(*, compartida: bool = False) -> UbicacionesFalsas:
    """La 0677 con un nombre de persona en el `con.res` de cada unidad y una
    referencia de obra reconocible. Las carpetas siguen casando por sufijo
    (`… Villa 5` → `VILLA 05`)."""
    unidades = [
        UnidadDeObra(
            obra_ref=OBRA_REF_INVENTADA,
            obra_codigo="0677",
            unidad_codigo=f"0677.03VILLA {n}.",
            unidad_nombre=f"Casa de {PERSONA_INVENTADA} Villa {n}",
        )
        for n in range(1, 16)
    ]
    if compartida:
        unidades.append(
            UnidadDeObra(
                obra_ref=OBRA_REF_INVENTADA,
                obra_codigo="0677",
                unidad_codigo="0677.04VILLA 5.",
                unidad_nombre=f"Casa de {OTRA_PERSONA_INVENTADA} Villa 5",
            )
        )
    return UbicacionesFalsas(
        {
            reclamacion_0677(n): (
                UbicacionReclamacion(
                    obra_codigo="0677",
                    obra_nombre=RES_OBRA_0677,
                    unidad_codigo=f"0677.03VILLA {n}.",
                    unidad_nombre=f"Casa de {PERSONA_INVENTADA} Villa {n}",
                ),
            )
            for n in range(1, 16)
        },
        unidades=unidades,
    )


@pytest.mark.parametrize(
    ("n", "compartida", "estado"),
    [
        pytest.param(5, False, 200, id="resuelve"),
        pytest.param(13, False, 200, id="crea"),
        pytest.param(5, True, 409, id="compartida"),
    ],
)
def test_f013_r23_ni_el_nombre_de_la_unidad_ni_la_referencia_de_obra_salen(
    estrategia, monkeypatch, caplog, n, compartida, estado
):
    """R23 · ni en el log (de cualquier logger, a cualquier nivel) ni en la respuesta."""
    estrategia()
    _con_costuras(
        monkeypatch,
        archivador=ArchivadorDePosventa(),
        repositorio=_repositorio(n),
        ubicaciones=_ubicaciones_con_datos_sensibles(compartida=compartida),
    )

    with caplog.at_level(logging.DEBUG):
        respuesta = _archivar(n)

    assert respuesta.status_code == estado
    salida = caplog.text + respuesta.get_body().decode("utf-8")
    for prohibido in (PERSONA_INVENTADA, OTRA_PERSONA_INVENTADA, OBRA_REF_INVENTADA):
        assert prohibido not in salida
    if compartida:
        assert _cuerpo(respuesta)["motivo"] == "unidad_carpeta_compartida"


def test_f013_r23_el_503_de_sigrid_no_lleva_la_referencia_de_obra(
    estrategia, monkeypatch, caplog
):
    """R23 · el 503 dice qué pasó con Sigrid y nada de lo que Sigrid devolvió."""
    estrategia()
    _con_costuras(
        monkeypatch,
        archivador=ArchivadorDePosventa(),
        repositorio=_repositorio(5),
        ubicaciones=UbicacionesFalsas(
            {reclamacion_0677(5): (ubicacion_0677(5),)},
            fallo_al_leer_unidades=UbicacionNoDisponible(
                "la respuesta no trae lo que el contrato promete"
            ),
        ),
    )

    with caplog.at_level(logging.DEBUG):
        respuesta = _archivar(5)

    assert respuesta.status_code == 503
    salida = caplog.text + respuesta.get_body().decode("utf-8")
    assert OBRA_REF_INVENTADA not in salida
    assert "00000000T" not in salida


def test_f013_r19_ninguna_respuesta_del_borde_lleva_el_parte_ni_la_biblioteca(
    estrategia, monkeypatch
):
    """R19, R23 · ni el PDF, ni el DNI, ni el `drive_id` en el 409."""
    estrategia()
    arbol = {**arbol_0677(), "": (OBRA, "0677 SEGUNDA INVENTADA")}
    _con_costuras(
        monkeypatch,
        archivador=ArchivadorDePosventa(ExploradorFalso(arbol)),
        repositorio=_repositorio(5),
        ubicaciones=ubicaciones_0677(),
    )

    texto = _archivar(5).get_body().decode("utf-8")

    assert "00000000T" not in texto
    assert "%PDF" not in texto
    assert "drive-inventado" not in texto


def test_f013_t13_la_biblioteca_falsa_de_f006_no_es_explorador():
    """Control del material: el `ArchivoPortFalso` de F-006 **no** sabe listar.

    Si lo supiera, los casos de `por_obra` de arriba no probarían que el borde
    no pide listados: el doble los respondería en silencio.
    """
    from domain.ports.biblioteca import ExploradorBibliotecaPort

    assert not isinstance(ArchivoPortFalso(BibliotecaFalsa()), ExploradorBibliotecaPort)
    assert isinstance(ArchivadorDePosventa(), ExploradorBibliotecaPort)
