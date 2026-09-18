# services/postventa-api/tests/test_f033_archivar_http.py
"""L1 desde el borde: `POST /api/archivar` con un parte que ya consta archivado (F-033).

Cubre R12, R14, R15, R21, R23 y R24 de
`specs/F-033-l1-traza-archivo/requirements.md` recorriendo
`function_app.archivar` de verdad —parseo del multipart, códigos, JSON—, con
los dos puertos sustituidos por dobles en la costura de `archivar_parte`.

Y los **tres recorridos de circuito** de `design.md` §6, sobre
`RepositorioComoLaBase` (`tests/utiles_pg.py`), que guarda columnas y no
objetos: la traza que L1 lee vuelve **recompuesta** por el mapeo de
producción, no es la misma que entró.

1. **El doble archivado**: el mismo parte, dos veces. Una sola subida, la
   segunda con `AVISO_YA_ARCHIVADO`, y la traza intacta. Antes de F-033 este
   caso **subía dos veces**: es la prueba de que el defecto D-A1 existía.
2. **El caso F-032**: la traza `archivado` lleva el nombre de antes de limpiar
   el código (`RS 26.09`, con espacio) y el formulario trae el limpio. Cero
   subidas, aviso de otro destino, y la respuesta con el nombre viejo.
3. **El caso F-013**: la traza lleva otra biblioteca que la configurada. Cero
   subidas, aviso de otro destino, y la biblioteca no sale en la respuesta.

Ni un dato real: los identificadores de biblioteca son inventados y
reconocibles (`drive-inventado-it`, `drive-inventado-posventa`).
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import application.pipelines.paso_archivo as paso
import azure.functions as func
import interface_adapters.api.archivar as modulo_archivar
import pytest
from config.settings import Ajustes
from domain.models.estado import SituacionParte
from domain.models.persistencia import EstadoArchivo, TrazaArchivo
from interface_adapters.api.archivar import archivar_parte

from tests.utiles_pg import RepositorioComoLaBase
from tests.utiles_sharepoint import (
    HOST_FALSO,
    ArchivoPortFalso,
    BibliotecaFalsa,
    RepositorioFalso,
    contexto_apto,
    parte_de_prueba,
)

_FRONTERA = "frontera-sintetica-de-test-f033"

#: El contrato de la respuesta (F-006 R30): estas seis claves y **ninguna más**.
CLAVES_DE_LA_RESPUESTA = {
    "hash_parte",
    "nombre_fichero",
    "carpeta",
    "estado",
    "web_url",
    "avisos",
}

PDF = b"%PDF-1.4 de mentira para F-033"

HASH = "9f2b0011aabb"
CARPETA_ESPERADA = "Postventa/0677"
NOMBRE_ESPERADO = "0677 - RS26.08 - 0123 PARTE FIRMADO.pdf"

#: Los campos del formulario de un parte apto, todos **inventados**.
FORMULARIO = (
    ("hash", HASH),
    ("codigo_obra", "0677"),
    ("numero_incidencia", "RS26.08/0123"),
    ("veredicto", "apto"),
    ("destino", "archivo_y_cierre"),
)

#: El caso F-032 (`design.md` §6): el nombre de antes de limpiar el código,
#: con el espacio de `RS 26.09`, y el formulario con el código ya limpio.
NOMBRE_VIEJO_F032 = "0626 - RS 26.09 - 0178 PARTE FIRMADO.pdf"
CARPETA_F032 = "Postventa/0626"
FORMULARIO_F032 = (
    ("hash", HASH),
    ("codigo_obra", "0626"),
    ("numero_incidencia", "RS26.09/0178"),
    ("veredicto", "apto"),
    ("destino", "archivo_y_cierre"),
)

DRIVE_IT = "drive-inventado-it"
DRIVE_POSVENTA = "drive-inventado-posventa"
ITEM_GUARDADO = "item-guardado-f033"
WEB_URL_GUARDADA = f"{HOST_FALSO}/guardada-f033"
ARCHIVADO_EN = datetime(2026, 9, 1, 9, 30, tzinfo=UTC)
AHORA = datetime(2026, 9, 18, 11, 0, tzinfo=UTC)


# --------------------------------------------------------------------------
# El borde
# --------------------------------------------------------------------------


def _peticion(campos: Sequence[tuple[str, str]] = FORMULARIO) -> func.HttpRequest:
    """Petición `multipart/form-data` con un parte y esos campos."""
    cuerpo = (
        f"--{_FRONTERA}\r\n"
        f'Content-Disposition: form-data; name="fichero"; filename="parte.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
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


def _con_dobles(monkeypatch, archivador, repositorio) -> None:
    """La ruta de verdad, con los dos puertos sustituidos por dobles.

    Se sustituye lo que `function_app` tiene importado y no el handler: por
    debajo corre `archivar_parte` entero, que es quien pasa el `drive_id`
    vigente al paso (R15).
    """
    import function_app

    def envoltura(contenido: bytes, **datos):
        return archivar_parte(
            contenido, archivador=archivador, repositorio=repositorio, ahora=AHORA,
            **datos,
        )

    monkeypatch.setattr(function_app, "archivar_parte", envoltura)


def _archivar(campos: Sequence[tuple[str, str]] = FORMULARIO) -> func.HttpResponse:
    import function_app

    return function_app.archivar(_peticion(campos))


def _cuerpo(respuesta: func.HttpResponse) -> dict:
    return json.loads(respuesta.get_body())


def _con_biblioteca_vigente(monkeypatch, drive_id: str | None) -> None:
    """La configuración que lee `archivar_parte`, con **esta** biblioteca.

    Los `Ajustes` se construyen a mano con `_env_file=None` y los campos que
    importan explícitos: sin esto, el `.env` de quien ejecuta la suite podría
    traer su `SHAREPOINT_DRIVE_ID` y el caso pasaría o fallaría según el
    puesto (mismo motivo que `test_f006_fabrica.py`).
    """
    ajustes = Ajustes(
        _env_file=None,
        entorno="test",
        sharepoint_drive_id=drive_id,
        sharepoint_carpeta_base="Postventa",
    )
    monkeypatch.setattr(modulo_archivar, "obtener_ajustes", lambda: ajustes)


def _archivada(**cambios) -> TrazaArchivo:
    """La traza que ya consta `archivado` del parte del formulario."""
    valores = {
        "hash_parte": HASH,
        "estado": EstadoArchivo.ARCHIVADO,
        "nombre_fichero": NOMBRE_ESPERADO,
        "carpeta": CARPETA_ESPERADA,
        "drive_id": DRIVE_POSVENTA,
        "item_id": ITEM_GUARDADO,
        "web_url": WEB_URL_GUARDADA,
        "archivado_at_utc": ARCHIVADO_EN,
    }
    valores.update(cambios)
    return TrazaArchivo(**valores)


def _repositorio_falso(archivo: TrazaArchivo | None) -> RepositorioFalso:
    """El veredicto apto guardado y, si se pasa, la traza de archivo."""
    return RepositorioFalso(
        situacion=SituacionParte(
            validacion=contexto_apto(hash_parte=HASH).validacion, archivo=archivo
        )
    )


def _base_con_el_parte_apto(archivo: TrazaArchivo | None = None) -> RepositorioComoLaBase:
    """`RepositorioComoLaBase` con la ficha y el veredicto apto de este parte.

    Es lo que habría en `postventa.partes` y `postventa.validaciones` tras
    `POST /api/parte`. Si se pasa `archivo`, se escribe por `guardar_archivo`,
    como lo haría el paso: vuelve **por columnas** en la situación.
    """
    ctx = contexto_apto(hash_parte=HASH)
    base = RepositorioComoLaBase()
    base.guardar_parte(
        parte=parte_de_prueba(hash_parte=HASH),
        extraccion=ctx.extraccion,
        remesa_id=str(uuid.uuid4()),
        ahora=AHORA,
    )
    base.guardar_validacion(resultado=ctx.validacion, ahora=AHORA)
    if archivo is not None:
        base.guardar_archivo(traza=archivo)
    return base


# ==========================================================================
# R12, R23 · un parte ya archivado, desde el endpoint
# ==========================================================================


def test_f033_r12_un_parte_archivado_responde_200_con_la_traza_guardada(monkeypatch):
    """R12 · 200, las seis claves, los valores **de la traza guardada**."""
    _con_biblioteca_vigente(monkeypatch, DRIVE_POSVENTA)
    archivador = ArchivoPortFalso()
    _con_dobles(monkeypatch, archivador, _repositorio_falso(_archivada()))

    respuesta = _archivar()

    assert respuesta.status_code == 200
    cuerpo = _cuerpo(respuesta)
    assert set(cuerpo) == CLAVES_DE_LA_RESPUESTA
    assert cuerpo == {
        "hash_parte": HASH,
        "nombre_fichero": NOMBRE_ESPERADO,
        "carpeta": CARPETA_ESPERADA,
        "estado": "archivado",
        "web_url": WEB_URL_GUARDADA,
        "avisos": [paso.AVISO_YA_ARCHIVADO],
    }
    assert archivador.llamadas == []


def test_f033_r23_el_contrato_es_el_mismo_con_corte_y_sin_el(monkeypatch):
    """R23 · mismas seis claves y mismo 200 en los dos caminos."""
    _con_biblioteca_vigente(monkeypatch, DRIVE_POSVENTA)
    _con_dobles(monkeypatch, ArchivoPortFalso(), _repositorio_falso(None))
    sin_corte = _archivar()
    _con_dobles(monkeypatch, ArchivoPortFalso(), _repositorio_falso(_archivada()))
    con_corte = _archivar()

    assert sin_corte.status_code == con_corte.status_code == 200
    assert set(_cuerpo(sin_corte)) == set(_cuerpo(con_corte)) == CLAVES_DE_LA_RESPUESTA


def test_f033_r21_un_campo_forzar_en_el_cuerpo_no_abre_nada(monkeypatch):
    """R21 · ni campo del cuerpo: `forzar` se ignora y L1 corta igual."""
    _con_biblioteca_vigente(monkeypatch, DRIVE_POSVENTA)
    archivador = ArchivoPortFalso()
    _con_dobles(monkeypatch, archivador, _repositorio_falso(_archivada()))

    respuesta = _archivar((*FORMULARIO, ("forzar", "true"), ("reemplazar", "1")))

    assert respuesta.status_code == 200
    assert archivador.llamadas == []
    assert paso.AVISO_YA_ARCHIVADO in _cuerpo(respuesta)["avisos"]


# ==========================================================================
# R15 · el borde pasa la biblioteca vigente
# ==========================================================================


def test_f033_r15_sin_biblioteca_configurada_solo_se_comparan_carpeta_y_nombre(
    monkeypatch,
):
    """R15 · sin `SHAREPOINT_DRIVE_ID`, otra biblioteca en la traza no avisa."""
    _con_biblioteca_vigente(monkeypatch, None)
    _con_dobles(monkeypatch, ArchivoPortFalso(), _repositorio_falso(_archivada(drive_id=DRIVE_IT)))

    cuerpo = _cuerpo(_archivar())

    assert cuerpo["avisos"] == [paso.AVISO_YA_ARCHIVADO]


def test_f033_r15_con_la_misma_biblioteca_no_hay_aviso_de_otro_destino(monkeypatch):
    """R15 · la configurada y la de la traza coinciden: un solo aviso."""
    _con_biblioteca_vigente(monkeypatch, DRIVE_POSVENTA)
    _con_dobles(monkeypatch, ArchivoPortFalso(), _repositorio_falso(_archivada()))

    cuerpo = _cuerpo(_archivar())

    assert cuerpo["avisos"] == [paso.AVISO_YA_ARCHIVADO]


# ==========================================================================
# El circuito · 1 · archivar dos veces el mismo parte
# ==========================================================================


def test_f033_circuito_archivar_dos_veces_sube_una(monkeypatch):
    """R10, R12 · **D-A1**: la segunda petición no sube y la traza no cambia.

    Antes de F-033 la segunda subía otra vez: el endpoint no pasaba la traza
    al paso y L1 no cortaba nunca. Lo tapaba L2 porque el nombre coincidía.
    """
    _con_biblioteca_vigente(monkeypatch, DRIVE_POSVENTA)
    biblioteca = BibliotecaFalsa()
    base = _base_con_el_parte_apto()
    _con_dobles(monkeypatch, ArchivoPortFalso(biblioteca), base)

    primera = _archivar()
    traza_primera = base.archivos[HASH]
    segunda = _archivar()

    assert primera.status_code == segunda.status_code == 200
    assert biblioteca.subidas == 1
    assert len(biblioteca.elementos) == 1
    assert _cuerpo(primera)["avisos"] == []
    assert _cuerpo(segunda)["avisos"] == [paso.AVISO_YA_ARCHIVADO]
    # La traza, intacta: mismo elemento y la fecha del primer archivado.
    assert base.archivos[HASH] is traza_primera
    assert base.archivos[HASH].item_id == traza_primera.item_id
    assert base.archivos[HASH].archivado_at_utc == traza_primera.archivado_at_utc
    # Y la respuesta de la segunda es la de la primera.
    assert {
        clave: valor for clave, valor in _cuerpo(segunda).items() if clave != "avisos"
    } == {clave: valor for clave, valor in _cuerpo(primera).items() if clave != "avisos"}
    # R8: una consulta de situación por petición, ninguna más.
    assert base.situaciones_consultadas == [HASH, HASH]


# ==========================================================================
# El circuito · 2 · el caso F-032: el nombre de antes de limpiar el código
# ==========================================================================


def test_f033_circuito_f032_el_nombre_viejo_se_queda_y_se_avisa(monkeypatch):
    """R13, R14 · cero subidas, aviso de otro destino, respuesta con el viejo."""
    _con_biblioteca_vigente(monkeypatch, DRIVE_POSVENTA)
    archivador = ArchivoPortFalso()
    base = _base_con_el_parte_apto(
        _archivada(nombre_fichero=NOMBRE_VIEJO_F032, carpeta=CARPETA_F032)
    )
    _con_dobles(monkeypatch, archivador, base)

    respuesta = _archivar(FORMULARIO_F032)

    assert respuesta.status_code == 200
    cuerpo = _cuerpo(respuesta)
    assert archivador.llamadas == []
    assert archivador.biblioteca.subidas == 0
    assert cuerpo["nombre_fichero"] == NOMBRE_VIEJO_F032
    assert cuerpo["carpeta"] == CARPETA_F032
    assert cuerpo["estado"] == "archivado"
    assert cuerpo["avisos"] == [
        paso.AVISO_YA_ARCHIVADO,
        paso.AVISO_ARCHIVADO_EN_OTRO_DESTINO,
    ]
    assert base.archivos[HASH].nombre_fichero == NOMBRE_VIEJO_F032


# ==========================================================================
# El circuito · 3 · el caso F-013: la traza está en otra biblioteca
# ==========================================================================


def test_f033_circuito_f013_otra_biblioteca_no_se_sube_y_no_se_dice_cual(
    monkeypatch, caplog
):
    """R14, R15, R23, R24 · cero subidas, aviso, y ningún `drive_id` fuera."""
    _con_biblioteca_vigente(monkeypatch, DRIVE_POSVENTA)
    archivador = ArchivoPortFalso()
    base = _base_con_el_parte_apto(_archivada(drive_id=DRIVE_IT))
    _con_dobles(monkeypatch, archivador, base)

    with caplog.at_level(logging.DEBUG):
        respuesta = _archivar()

    assert respuesta.status_code == 200
    cuerpo = _cuerpo(respuesta)
    assert archivador.llamadas == []
    assert cuerpo["avisos"] == [
        paso.AVISO_YA_ARCHIVADO,
        paso.AVISO_ARCHIVADO_EN_OTRO_DESTINO,
    ]
    serializado = json.dumps(cuerpo)
    for centinela in (DRIVE_IT, DRIVE_POSVENTA, ITEM_GUARDADO):
        assert centinela not in serializado
        assert centinela not in caplog.text
    assert "drive" not in serializado.lower()
    assert base.archivos[HASH].drive_id == DRIVE_IT


@pytest.mark.parametrize("drive_vigente", (DRIVE_POSVENTA, None))
def test_f033_circuito_la_traza_vuelve_por_columnas_y_corta(monkeypatch, drive_vigente):
    """R2 + R10 · la traza que corta es la **recompuesta**, no la que entró."""
    _con_biblioteca_vigente(monkeypatch, drive_vigente)
    archivador = ArchivoPortFalso()
    base = _base_con_el_parte_apto(_archivada())
    _con_dobles(monkeypatch, archivador, base)

    cuerpo = _cuerpo(_archivar())

    assert archivador.llamadas == []
    assert cuerpo["web_url"] == WEB_URL_GUARDADA
    assert cuerpo["avisos"] == [paso.AVISO_YA_ARCHIVADO]
