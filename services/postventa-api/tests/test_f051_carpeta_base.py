# services/postventa-api/tests/test_f051_carpeta_base.py
"""F-051 · la carpeta base ausente, según la estrategia (incidente del 2026-10-01).

## El incidente, en una línea

Desde el corte de F-013 el App Setting `SHAREPOINT_CARPETA_BASE` se dejó
**vacío** a propósito (D-1: vacío = la raíz de la biblioteca de Posventa).
Azure **no pasa a la aplicación un App Setting de valor vacío**, así que la
variable no llegaba, pydantic tomaba el valor por defecto del campo
(`Postventa`) y el resolutor listaba `Postventa` en la raíz de la biblioteca de
Posventa, que no existe: `ArchivoFallido`, 502, y ningún parte archivado ni
cerrado.

## Lo que se fija aquí (los `acceptance` de F-051)

- con `posventa` y **sin** la variable, la base es la raíz: el primer listado
  es `""`, no `Postventa` (el caso del incidente, reproducido desde el handler);
- con `por_obra` y sin la variable, sigue siendo `Postventa` (F-006 intacto);
- `/` y vacía son la raíz en `posventa` y se siguen rechazando en `por_obra`
  (F-013 R17);
- y la regla, escrita una vez, en `carpeta_base_efectiva`.

Los ajustes se construyen con `_env_file=None`: el caso es precisamente
«la variable no está», y el `.env` de quien ejecuta la suite podría ponerla.
Ni Graph, ni Sigrid, ni PostgreSQL: los dobles de F-013.
"""

from __future__ import annotations

from datetime import UTC, datetime

import infrastructure.sharepoint.fabrica as fabrica_sharepoint
import pytest
from config.settings import Ajustes
from domain.models.errores import ConfiguracionSharePointIncompleta
from domain.models.estado import SituacionParte
from interface_adapters.api import archivar

from tests.utiles_destino import (
    CARPETA_OBRA_0677,
    FIRMADOS,
    INCIDENCIAS,
    ExploradorFalso,
    arbol_0677,
    reclamacion_0677,
    ubicaciones_0677,
)
from tests.utiles_sharepoint import ArchivoPortFalso, RepositorioFalso
from tests.utiles_validacion import veredicto_apto

HASH = "9f2b0051aabb"
PDF = b"%PDF-1.4 parte inventado F-051"
AHORA = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)

OBRA = CARPETA_OBRA_0677
VILLA_5 = f"{OBRA}/{INCIDENCIAS}/VILLA 05"

#: Las variables de destino que el caso NO quiere heredar del entorno de quien
#: ejecuta la suite. `SHAREPOINT_CARPETA_BASE` se quita siempre: cada caso la
#: pone solo si la necesita.
VARIABLES_DE_DESTINO = (
    "SHAREPOINT_ESTRUCTURA",
    "SHAREPOINT_CARPETA_BASE",
    "SHAREPOINT_CARPETA_INCIDENCIAS",
    "SHAREPOINT_CARPETA_FIRMADOS",
    "SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA",
    "SHAREPOINT_CREAR_CARPETAS",
)


class ArchivadorDePosventa(ArchivoPortFalso):
    """`ArchivoPort` y `ExploradorBibliotecaPort` en una instancia, como Graph."""

    def __init__(self) -> None:
        self.explorador = ExploradorFalso(arbol_0677())
        super().__init__(registro=self.explorador.registro)

    def listar_carpetas(self, *, carpeta: str) -> tuple[str, ...] | None:
        return self.explorador.listar_carpetas(carpeta=carpeta)

    def crear_subcarpeta(self, *, padre: str, nombre: str) -> None:
        self.explorador.crear_subcarpeta(padre=padre, nombre=nombre)


@pytest.fixture
def entorno(monkeypatch):
    """Fija la estrategia y, si se pide, la base; nada más del destino.

    `archivar.obtener_ajustes` se sustituye por unos ajustes **sin `.env`**:
    así «la variable no está» es cierto también en el puesto de quien ejecuta
    la suite, que puede tener un `.env` con la base puesta.
    """

    def _fijar(estructura: str, base: str | None = None) -> None:
        for variable in VARIABLES_DE_DESTINO:
            monkeypatch.delenv(variable, raising=False)
        monkeypatch.setenv("SHAREPOINT_ESTRUCTURA", estructura)
        monkeypatch.setenv("SHAREPOINT_DRIVE_ID", "drive-inventado-f051")
        if base is not None:
            monkeypatch.setenv("SHAREPOINT_CARPETA_BASE", base)
        monkeypatch.setattr(
            archivar, "obtener_ajustes", lambda: Ajustes(_env_file=None)
        )

    return _fijar


def _archivar_villa_5(archivador: ArchivadorDePosventa) -> dict:
    """Un parte apto de la villa 5 de la 0677, por el handler de verdad."""
    return archivar.archivar_parte(
        PDF,
        hash=HASH,
        codigo_obra="0677",
        numero_incidencia=reclamacion_0677(5),
        veredicto="apto",
        destino="archivo_y_cierre",
        archivador=archivador,
        repositorio=RepositorioFalso(
            situacion=SituacionParte(
                validacion=veredicto_apto(
                    hash_parte=HASH, numero_incidencia=reclamacion_0677(5)
                )
            )
        ),
        ubicaciones=ubicaciones_0677(),
        ahora=AHORA,
    )


def _ajustes(**cambios) -> Ajustes:
    """Ajustes completos e inventados, **sin** base salvo que el caso la ponga."""
    base = {
        "entorno": "dev",
        "archivo_habilitado": True,
        "sharepoint_drive_id": "drive-inventado-f051",
        "graph_tenant_id": "tenant-inventado-f051",
        "graph_client_id": "cliente-inventado-f051",
        "graph_client_secret": "secreto-inventado-f051",
    }
    base.update(cambios)
    return Ajustes(_env_file=None, **base)


@pytest.fixture
def espia(monkeypatch):
    """La fábrica, con el adaptador de Graph cambiado por un espía que cuenta."""
    construcciones: list[dict] = []

    class _Espia:
        def __init__(self, **argumentos) -> None:
            construcciones.append(argumentos)

    monkeypatch.setattr(fabrica_sharepoint, "AdaptadorSharePointGraph", _Espia)
    return construcciones


# --------------------------------------------------------------------------
# Acceptance 1 · `posventa` sin la variable = la raíz (el incidente)
# --------------------------------------------------------------------------


def test_f051_a1_posventa_sin_la_variable_lista_la_raiz_y_archiva(entorno):
    """El incidente del 2026-10-01, reproducido desde el handler.

    Con la variable ausente —que es como llega un App Setting vacío a la
    Function—, el primer listado tiene que ser la **raíz** (`""`). Antes de
    F-051 era `Postventa`, que no existe en la biblioteca de Posventa: 502.
    """
    entorno("posventa")
    archivador = ArchivadorDePosventa()

    cuerpo = _archivar_villa_5(archivador)

    assert archivador.explorador.listados[0] == ""
    assert "Postventa" not in archivador.explorador.listados
    assert cuerpo["carpeta"] == f"{VILLA_5}/{FIRMADOS}"
    assert cuerpo["estado"] == "archivado"
    assert archivador.biblioteca.subidas == 1


def test_f051_a1_la_fabrica_construye_con_posventa_y_sin_la_variable(espia):
    """La fábrica no se queja de una base ausente en `posventa`: es la raíz."""
    fabrica_sharepoint.construir_archivador(_ajustes(sharepoint_estructura="posventa"))

    assert len(espia) == 1


# --------------------------------------------------------------------------
# Acceptance 2 · `por_obra` sin la variable = `Postventa`, como siempre
# --------------------------------------------------------------------------


def test_f051_a2_por_obra_sin_la_variable_sigue_en_postventa(entorno):
    """F-006 intacto: sin la variable, `por_obra` archiva en `Postventa/<obra>`."""
    entorno("por_obra")
    archivador = ArchivadorDePosventa()

    cuerpo = _archivar_villa_5(archivador)

    assert cuerpo["carpeta"] == "Postventa/0677"
    assert archivador.explorador.llamadas == []


def test_f051_a2_la_fabrica_construye_con_por_obra_y_sin_la_variable(espia):
    """Sin la variable, `por_obra` no es «base vacía»: es `Postventa` (R17 no salta)."""
    fabrica_sharepoint.construir_archivador(_ajustes(sharepoint_estructura="por_obra"))

    assert len(espia) == 1


# --------------------------------------------------------------------------
# Acceptance 3 · «/» y vacía: la raíz en `posventa`, rechazadas en `por_obra`
# --------------------------------------------------------------------------


@pytest.mark.parametrize("base", ("/", ""), ids=("barra", "vacia"))
def test_f051_a3_barra_y_vacia_son_la_raiz_en_posventa(entorno, base):
    """La mitigación del 2026-10-01 («/») y la decisión D-1 (vacía), desde el handler."""
    entorno("posventa", base)
    archivador = ArchivadorDePosventa()

    cuerpo = _archivar_villa_5(archivador)

    assert archivador.explorador.listados[0] == ""
    assert cuerpo["carpeta"] == f"{VILLA_5}/{FIRMADOS}"


@pytest.mark.parametrize("base", ("/", ""), ids=("barra", "vacia"))
def test_f051_a3_barra_y_vacia_se_rechazan_en_por_obra(monkeypatch, espia, base):
    """F-013 R17, leída del entorno como en Azure: «/» o vacía en `por_obra`, no.

    Que la ausencia sea `Postventa` en `por_obra` no puede convertir una base
    **puesta** a la raíz en algo admitido: dejaría las carpetas por código
    sueltas en la raíz de la biblioteca.
    """
    monkeypatch.setenv("SHAREPOINT_ESTRUCTURA", "por_obra")
    monkeypatch.setenv("SHAREPOINT_CARPETA_BASE", base)

    with pytest.raises(ConfiguracionSharePointIncompleta) as fallo:
        fabrica_sharepoint.construir_archivador(_ajustes())

    assert "SHAREPOINT_CARPETA_BASE" in fallo.value.motivo
    assert espia == []


# --------------------------------------------------------------------------
# La regla, en un sitio: `carpeta_base_efectiva`
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("estructura", "base", "efectiva"),
    (
        pytest.param("posventa", None, "", id="posventa-ausente-raiz"),
        pytest.param("por_obra", None, "Postventa", id="por_obra-ausente-postventa"),
        pytest.param("posventa", "/", "/", id="posventa-barra-tal-cual"),
        pytest.param("posventa", "", "", id="posventa-vacia-tal-cual"),
        pytest.param("por_obra", "/", "/", id="por_obra-barra-tal-cual"),
        pytest.param("posventa", "OTRA BASE", "OTRA BASE", id="posventa-con-nombre"),
        pytest.param("por_obra", "OTRA BASE", "OTRA BASE", id="por_obra-con-nombre"),
        # Una estrategia desconocida no llega a archivar (la rechaza la
        # fábrica, R3); si llegara, la ausencia es la de siempre, no la raíz.
        pytest.param("otra", None, "Postventa", id="desconocida-ausente-postventa"),
    ),
)
def test_f051_la_base_efectiva_por_estrategia(estructura, base, efectiva):
    """Solo la **ausencia** depende de la estrategia; un valor puesto pasa tal cual.

    Recortar barras y blancos es cosa de quien compone la ruta (`unir_ruta`,
    `carpeta_de_archivo`) y del control de R17, como antes de F-051.
    """
    cambios = {"sharepoint_estructura": estructura}
    if base is not None:
        cambios["sharepoint_carpeta_base"] = base

    assert fabrica_sharepoint.carpeta_base_efectiva(_ajustes(**cambios)) == efectiva


def test_f051_la_base_ausente_se_lee_como_ausente():
    """El campo distingue «no está» de «está vacía»: es lo que permite la regla.

    Con un valor por defecto en el campo, la ausencia se confundía con
    `Postventa` antes de que nadie supiera la estrategia: el incidente.
    """
    assert Ajustes(_env_file=None).sharepoint_carpeta_base is None
