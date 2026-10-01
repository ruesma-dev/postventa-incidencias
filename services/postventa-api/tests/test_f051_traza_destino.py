# services/postventa-api/tests/test_f051_traza_destino.py
"""F-051 T2 · la traza del destino efectivo al construir el archivador.

El corte de F-013 se dio por bueno mirando la **configuración** de Azure
(`az functionapp config appsettings list`): el App Setting estaba, vacío, como
se quería. Lo que nadie miró es lo que **leía la aplicación**, que era otra
cosa: Azure no le pasaba el vacío y la base acababa siendo `Postventa`.

Por eso, desde F-051, la fábrica deja una línea `INFO` con la estrategia y la
base **efectiva** —la que de verdad se va a listar— cada vez que construye el
archivador, y el guion del corte (`docs/DESPLIEGUE.md` §9, paso 6) la busca en
Application Insights. Lo que se fija aquí:

- el texto exacto, que es lo que busca la consulta KQL del guion;
- `raíz` cuando la base efectiva es la raíz (ausente, vacía o `/` en
  `posventa`), y el nombre entre comillas angulares cuando no;
- que no lleva **ningún identificador**: ni la biblioteca, ni el tenant, ni la
  aplicación, ni —obviamente— el secreto;
- y que si la fábrica se niega, no hay traza de un destino que no existe.

Todo inventado; el adaptador de Graph se sustituye por un espía.
"""

from __future__ import annotations

import logging

import infrastructure.sharepoint.fabrica as fabrica_sharepoint
import pytest
from config.settings import Ajustes
from domain.models.errores import ConfiguracionSharePointIncompleta

#: El principio de la línea, tal cual lo busca la consulta de
#: `docs/DESPLIEGUE.md` §9, paso 6. Cambiarlo obliga a cambiar el guion.
PREFIJO = "F-051 destino efectivo del archivo:"

DRIVE = "drive-inventado-traza-f051"
TENANT = "tenant-inventado-traza-f051"
CLIENTE = "cliente-inventado-traza-f051"
SECRETO = "secreto-inventado-traza-f051"


def _ajustes(**cambios) -> Ajustes:
    base = {
        "entorno": "dev",
        "archivo_habilitado": True,
        "sharepoint_drive_id": DRIVE,
        "sharepoint_site_id": "sitio-inventado-traza-f051",
        "graph_tenant_id": TENANT,
        "graph_client_id": CLIENTE,
        "graph_client_secret": SECRETO,
    }
    base.update(cambios)
    return Ajustes(_env_file=None, **base)


@pytest.fixture
def espia(monkeypatch):
    """El adaptador de Graph, cambiado por algo que no abre nada."""
    construcciones: list[dict] = []

    class _Espia:
        def __init__(self, **argumentos) -> None:
            construcciones.append(argumentos)

    monkeypatch.setattr(fabrica_sharepoint, "AdaptadorSharePointGraph", _Espia)
    return construcciones


def _trazas(caplog) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.getMessage().startswith(PREFIJO)]


@pytest.mark.parametrize(
    ("estructura", "base", "dice"),
    (
        pytest.param("posventa", None, "raíz", id="posventa-ausente"),
        pytest.param("posventa", "/", "raíz", id="posventa-barra"),
        pytest.param("posventa", "", "raíz", id="posventa-vacia"),
        pytest.param("posventa", " / ", "raíz", id="posventa-barra-con-blancos"),
        pytest.param("posventa", "OTRA BASE", "«OTRA BASE»", id="posventa-con-nombre"),
        pytest.param("por_obra", None, "«Postventa»", id="por_obra-ausente"),
        pytest.param("por_obra", " Postventa/ ", "«Postventa»", id="por_obra-recortada"),
    ),
)
def test_f051_t2_la_fabrica_traza_el_destino_efectivo(
    caplog, espia, estructura, base, dice
):
    """Una línea INFO, con la estrategia y la base efectiva, al construir."""
    cambios = {"sharepoint_estructura": estructura}
    if base is not None:
        cambios["sharepoint_carpeta_base"] = base
    caplog.set_level(logging.INFO, logger=fabrica_sharepoint.__name__)

    fabrica_sharepoint.construir_archivador(_ajustes(**cambios))

    (traza,) = _trazas(caplog)
    assert traza.levelno == logging.INFO
    assert traza.name == fabrica_sharepoint.__name__
    assert traza.getMessage() == (
        f"{PREFIJO} estructura {estructura}, carpeta base {dice}"
    )
    assert len(espia) == 1


def test_f051_t2_el_incidente_se_habria_visto_en_la_traza(caplog, espia):
    """Con la base de antes de F-051 en `posventa`, la traza dice `Postventa`.

    Es exactamente lo que el paso 6 del corte habría cazado el 2026-09-25: la
    línea **no** dice `raíz`.
    """
    caplog.set_level(logging.INFO, logger=fabrica_sharepoint.__name__)

    fabrica_sharepoint.construir_archivador(
        _ajustes(sharepoint_estructura="posventa", sharepoint_carpeta_base="Postventa")
    )

    (traza,) = _trazas(caplog)
    assert traza.getMessage().endswith("carpeta base «Postventa»")
    assert "raíz" not in traza.getMessage()


def test_f051_t2_la_traza_no_lleva_ningun_identificador(caplog, espia):
    """Ni la biblioteca, ni el sitio, ni el tenant, ni la aplicación, ni el secreto.

    La traza acaba en Application Insights: lo que identifica el destino vive
    en el Key Vault y ahí se queda.
    """
    caplog.set_level(logging.DEBUG)

    fabrica_sharepoint.construir_archivador(_ajustes(sharepoint_estructura="posventa"))

    assert _trazas(caplog)
    for registro in caplog.records:
        mensaje = registro.getMessage()
        for valor in (DRIVE, "sitio-inventado-traza-f051", TENANT, CLIENTE, SECRETO):
            assert valor not in mensaje


def test_f051_t2_si_la_fabrica_se_niega_no_hay_traza(caplog, espia):
    """Un destino rechazado no se traza como si fuera el efectivo."""
    caplog.set_level(logging.INFO, logger=fabrica_sharepoint.__name__)

    with pytest.raises(ConfiguracionSharePointIncompleta):
        fabrica_sharepoint.construir_archivador(
            _ajustes(sharepoint_estructura="por_obra", sharepoint_carpeta_base="/")
        )

    assert _trazas(caplog) == []
    assert espia == []
