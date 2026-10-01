# services/postventa-api/tests/test_f051_documentacion.py
"""F-051 T4 · la documentación dice `/`, no «vacía», y el corte mira la traza.

Lo que se fija:

- `docs/DESPLIEGUE.md` §9, paso 5: `$CarpetaBaseArchivo = "/"` y la línea que
  enseña el despliegue con `carpeta base '/'`;
- el paso 6 comprueba **lo que lee la aplicación**: la consulta KQL sobre
  `traces` que busca la línea de T2, de solo lectura, y la línea esperada
  es **exactamente** la que emite la fábrica (se genera aquí, no se copia);
- `docs/INTEGRACION.md` y su copia en `azure-apps` dicen `/` en la fila de la
  carpeta base, con un recuadro fechado del incidente;
- y ninguno de los tres lleva un identificador.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import infrastructure.sharepoint.fabrica as fabrica_sharepoint
import pytest
from config.settings import Ajustes

RAIZ = Path(__file__).resolve().parent.parent.parent.parent
DESPLIEGUE = RAIZ / "docs" / "DESPLIEGUE.md"
INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"
#: La copia del ecosistema. Vive en otro repositorio, hermano de este: si no
#: está en la máquina (una copia suelta, una CI), sus casos se saltan.
AZURE_APPS = RAIZ.parent / "azure-apps" / "postventa_incidencias.md"

CABECERA_DEL_RECUADRO = "Enmienda del 2026-10-01 (F-051)"

PATRON_GUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE
)


def _leer(documento: Path) -> str:
    return documento.read_text(encoding="utf-8")


def _normal(texto: str) -> str:
    return " ".join(texto.replace("*", "").replace("`", "").split())


def _seccion(texto: str, titulo: str) -> str:
    inicio = texto.index(titulo)
    nivel = len(titulo) - len(titulo.lstrip("#"))
    siguiente = re.compile(rf"^#{{1,{nivel}}} ", re.MULTILINE)
    fin = siguiente.search(texto, inicio + len(titulo))
    return texto[inicio : fin.start() if fin else len(texto)]


def _paso(seccion: str, numero: int) -> str:
    """Del `N. ` de la columna 0 al siguiente paso o subtítulo."""
    inicio = re.search(rf"^{numero}\. ", seccion, re.MULTILINE).start()
    fin = re.compile(r"^(?:\d+\. |#)", re.MULTILINE).search(seccion, inicio + 3)
    return seccion[inicio : fin.start() if fin else len(seccion)]


def _corte() -> str:
    return _seccion(_leer(DESPLIEGUE), "## 9 · El corte de F-013")


def _linea_que_emite_la_fabrica(monkeypatch, caplog) -> str:
    """La traza de T2 con la configuración del corte, generada por el código."""
    monkeypatch.setattr(
        fabrica_sharepoint, "AdaptadorSharePointGraph", lambda **_: object()
    )
    caplog.set_level(logging.INFO, logger=fabrica_sharepoint.__name__)
    fabrica_sharepoint.construir_archivador(
        Ajustes(
            _env_file=None,
            entorno="pro",
            archivo_habilitado=True,
            sharepoint_estructura="posventa",
            sharepoint_carpeta_base="/",
            sharepoint_drive_id="drive-inventado-doc-f051",
            graph_tenant_id="tenant-inventado",
            graph_client_id="cliente-inventado",
            graph_client_secret="secreto-inventado",
        )
    )
    (linea,) = [
        r.getMessage()
        for r in caplog.records
        if r.getMessage().startswith("F-051 destino efectivo")
    ]
    return linea


# --------------------------------------------------------------------------
# DESPLIEGUE §9 · paso 5: "/"
# --------------------------------------------------------------------------


def test_f051_t4_el_paso_5_declara_la_raiz_como_barra():
    paso = _normal(_paso(_corte(), 5))

    assert _normal('$CarpetaBaseArchivo = "/"') in paso
    assert "carpeta base '/'" in paso
    assert CABECERA_DEL_RECUADRO in paso


# --------------------------------------------------------------------------
# DESPLIEGUE §9 · paso 6: la traza, en Application Insights
# --------------------------------------------------------------------------


def test_f051_t4_el_paso_6_busca_la_traza_que_emite_la_fabrica(monkeypatch, caplog):
    """La línea que el guion da por buena es la que el código escribe, letra a letra."""
    linea = _linea_que_emite_la_fabrica(monkeypatch, caplog)

    assert linea == (
        "F-051 destino efectivo del archivo: estructura posventa, carpeta base raíz"
    )
    assert linea in _paso(_corte(), 6)


def test_f051_t4_la_consulta_kql_es_de_solo_lectura_y_busca_la_traza():
    paso = _paso(_corte(), 6)
    (consulta,) = re.findall(r"```kusto\n(.*?)```", paso.replace("\r\n", "\n"), re.DOTALL)
    lineas = [linea.strip() for linea in consulta.strip().splitlines()]

    assert lineas[0] == "traces"
    assert '| where message has "F-051 destino efectivo del archivo"' in lineas
    # En KQL, lo que escribe o administra empieza por punto (`.set`, `.drop`…).
    assert not any(linea.startswith(".") for linea in lineas)


def test_f051_t4_el_paso_6_dice_que_la_configuracion_no_basta():
    paso = _normal(_paso(_corte(), 6))

    assert "appi-postventa-dev" in paso
    assert "Pero eso no basta" in paso
    assert "Freno 1" in paso
    assert "carpeta base «Postventa»" in paso
    assert CABECERA_DEL_RECUADRO in paso


# --------------------------------------------------------------------------
# INTEGRACION y azure-apps · "/", con el recuadro del incidente
# --------------------------------------------------------------------------


def _documentos_de_integracion() -> tuple:
    return (
        pytest.param(INTEGRACION, id="INTEGRACION"),
        pytest.param(
            AZURE_APPS,
            id="azure-apps",
            marks=pytest.mark.skipif(
                not AZURE_APPS.exists(), reason="azure-apps no esta en esta maquina"
            ),
        ),
    )


@pytest.mark.parametrize("documento", _documentos_de_integracion())
def test_f051_t4_la_fila_de_la_carpeta_base_dice_barra(documento):
    texto = _leer(documento)
    (fila,) = [
        linea for linea in texto.splitlines() if linea.startswith("| Carpeta base |")
    ]

    assert "`SHAREPOINT_CARPETA_BASE=/`" in fila
    assert "Nunca vacía" in fila


@pytest.mark.parametrize("documento", _documentos_de_integracion())
def test_f051_t4_hay_dos_recuadros_fechados_del_incidente(documento):
    """Uno tras la tabla de §3 y otro tras la enmienda de F-013 en las variables."""
    texto = _leer(documento)
    recuadros = [
        linea for linea in texto.splitlines() if linea.startswith(f"> **{CABECERA_DEL_RECUADRO}")
    ]

    assert len(recuadros) == 2
    assert "Azure no pasa" in _normal(texto)


@pytest.mark.parametrize(
    "documento",
    (pytest.param(DESPLIEGUE, id="DESPLIEGUE"), *_documentos_de_integracion()),
)
def test_f051_t4_ningun_documento_lleva_un_guid(documento):
    assert PATRON_GUID.findall(_leer(documento)) == []
