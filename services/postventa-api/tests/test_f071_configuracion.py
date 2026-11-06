# services/postventa-api/tests/test_f071_configuracion.py
"""La configuración de la plantilla v2 (F-071 T4).

`specs/F-071-plantilla-desde-sigrid/design.md` §7.2 y §7.3, sobre
`config/plantilla_incidencias.yaml` (el **real**) y
`infrastructure/documentos/plantilla_yaml.py`:

| Caso | Requisito |
|---|---|
| urgencias y listados siguen en el YAML, con sus códigos; no se dice que salgan de Sigrid | R16 |
| la ubicación depende de la unidad, en el mensaje y en «Instrucciones» | R18 |
| ningún texto nombra «General», «Otra» ni «en la revisión»; todos caben en 255 | R18 |
| ejemplos indicativos en `Ubicación`, `Oficio` y `Proveedor` | R19 |
| sin lista de ubicaciones; la clave `ubicaciones` tumba la carga | R21 |

Sin red, sin Sigrid y sin base de datos. El YAML roto se escribe en `tmp_path`.
"""

from __future__ import annotations

import copy
import dataclasses
from pathlib import Path

import pytest
import yaml
from domain.models.errores import ConfiguracionPlantillaInvalida
from infrastructure.documentos.plantilla_yaml import (
    ConfiguracionPlantilla,
    cargar_plantilla_yaml,
)

SERVICIO = Path(__file__).resolve().parents[1]
YAML_REAL = SERVICIO / "config" / "plantilla_incidencias.yaml"

PROHIBIDOS = ("General (toda la unidad)", "Otra (explicar en el detalle)", "en la revisión")


@pytest.fixture(scope="module")
def real() -> ConfiguracionPlantilla:
    return cargar_plantilla_yaml()


@pytest.fixture(scope="module")
def crudo() -> dict:
    return yaml.safe_load(YAML_REAL.read_text(encoding="utf-8"))


def _todos_los_textos(real: ConfiguracionPlantilla) -> list[str]:
    t = real.textos
    textos = [t.titulo, t.sin_oficios, t.excel_errores, *t.instrucciones]
    for mensaje in t.mensajes.values():
        textos += [mensaje.titulo_entrada, mensaje.entrada, mensaje.titulo_error, mensaje.error]
    for ejemplo in t.ejemplos:
        textos += list(ejemplo.values())
    return textos


# --------------------------------------------------------------------------
# R16 · urgencia y listado
# --------------------------------------------------------------------------


def test_f071_r16_urgencias_y_listados_del_yaml_con_sus_codigos(
    real: ConfiguracionPlantilla,
) -> None:
    assert [o.codigo for o in real.listas.urgencias] == ["urgente", "seguridad"]
    assert [o.codigo for o in real.listas.listados] == ["primero", "segundo"]


def test_f071_r16_instrucciones_no_dicen_que_urgencia_o_listado_salgan_de_sigrid(
    real: ConfiguracionPlantilla,
) -> None:
    for parrafo in real.textos.instrucciones:
        if "Sigrid" in parrafo:
            minusculas = parrafo.lower()
            assert "urgencia" not in minusculas, parrafo
            assert "listado" not in minusculas, parrafo
            assert "las listas salen" not in minusculas, (
                "«las listas» incluiría Urgencia y Listado"
            )


# --------------------------------------------------------------------------
# R18 · textos
# --------------------------------------------------------------------------


def test_f071_r18_el_mensaje_de_ubicacion_dice_que_depende_de_la_unidad(
    real: ConfiguracionPlantilla,
) -> None:
    entrada = real.textos.mensajes["Ubicación"].entrada
    assert "primero la unidad" in entrada
    assert "vuelve a elegir la ubicación" in entrada
    assert "en blanco" in entrada
    assert "«Detalle»" in entrada
    assert len(entrada) <= 255


def test_f071_r18_instrucciones_dicen_que_depende_de_la_unidad(
    real: ConfiguracionPlantilla,
) -> None:
    (parrafo,) = [p for p in real.textos.instrucciones if "«Ubicación»" in p]
    assert "depende de la unidad" in parrafo
    assert "elige primero la unidad" in parrafo
    assert "vuelve a elegir la ubicación" in parrafo
    assert "en blanco" in parrafo
    assert "«Detalle»" in parrafo
    instrucciones = list(real.textos.instrucciones)
    previo = next(i for i, p in enumerate(instrucciones) if p.startswith("Todo lo que tiene desplegable"))
    assert instrucciones[previo + 1] == parrafo, "va tras «Todo lo que tiene desplegable…»"


def test_f071_r18_ningun_texto_nombra_general_otra_ni_la_revision(
    real: ConfiguracionPlantilla,
) -> None:
    for texto in _todos_los_textos(real):
        for prohibido in PROHIBIDOS:
            assert prohibido not in texto, texto


def test_f071_r18_oficio_lleva_su_codigo_de_sigrid(real: ConfiguracionPlantilla) -> None:
    mensaje = real.textos.mensajes["Oficio"]
    assert "código de Sigrid" in mensaje.entrada
    assert "en blanco" in mensaje.entrada


def test_f071_r18_mensajes_e_instrucciones_caben_en_255(
    real: ConfiguracionPlantilla,
) -> None:
    for columna, mensaje in real.textos.mensajes.items():
        assert len(mensaje.entrada) <= 255, columna
        assert len(mensaje.error) <= 255, columna
    for parrafo in real.textos.instrucciones:
        assert len(parrafo) <= 255, parrafo


# --------------------------------------------------------------------------
# R19 · ejemplos indicativos
# --------------------------------------------------------------------------


def test_f071_r19_ejemplos_indicativos(real: ConfiguracionPlantilla) -> None:
    ubicaciones = [e["Ubicación"] for e in real.textos.ejemplos if "Ubicación" in e]
    assert ubicaciones
    assert set(ubicaciones) == {"Estancia (elígela de la lista de su unidad)"}
    for ejemplo in real.textos.ejemplos:
        for columna in ("Oficio", "Proveedor"):
            if columna in ejemplo:
                assert "(elíge" in ejemplo[columna], ejemplo[columna]


# --------------------------------------------------------------------------
# R21 · sin ubicaciones en el YAML
# --------------------------------------------------------------------------


def test_f071_r21_el_yaml_real_no_trae_ubicaciones(crudo: dict) -> None:
    assert "ubicaciones" not in crudo
    assert "ubicaciones:" not in YAML_REAL.read_text(encoding="utf-8")


def test_f071_r21_la_configuracion_ya_no_tiene_ubicaciones() -> None:
    campos = {f.name for f in dataclasses.fields(ConfiguracionPlantilla)}
    assert campos == {"listas", "textos"}


@pytest.mark.parametrize("valor", [[{"etiqueta": "Estancia A-01", "origen": []}], [], None])
def test_f071_r21_yaml_con_ubicaciones_falla(
    tmp_path: Path, crudo: dict, valor: object
) -> None:
    datos = copy.deepcopy(crudo)
    datos["ubicaciones"] = valor
    ruta = tmp_path / "plantilla.yaml"
    ruta.write_text(yaml.safe_dump(datos, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ConfiguracionPlantillaInvalida) as exc:
        cargar_plantilla_yaml(ruta)
    motivo = exc.value.motivo
    assert "`ubicaciones`" in motivo
    assert "Sigrid" in motivo
    assert "F-071" in motivo
