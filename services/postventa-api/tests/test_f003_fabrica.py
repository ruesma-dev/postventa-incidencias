# services/postventa-api/tests/test_f003_fabrica.py
"""Tests de la fábrica de extractores (R11, R12).

La fábrica es **el único sitio del servicio que sabe qué proveedores de IA
existen**. Añadir uno nuevo tiene que ser una función privada y una entrada en
un diccionario, sin que el pipeline se entere (criterio `acceptance` 1), y eso
es lo que se prueba aquí.

Los `Ajustes` se construyen a mano con `_env_file=None` y con las variables de
IA borradas del entorno. No es manía: el `.env` local del servicio **tendrá**
`GEMINI_API_KEY` en cuanto el humano ejecute las verificaciones manuales, y un
test que dependiera de eso empezaría a fallar justo entonces.
"""

from __future__ import annotations

import pytest
from config.settings import Ajustes
from domain.models.errores import ConfiguracionIaIncompleta, ProveedorNoSoportado
from infrastructure.llm.fabrica import PROVEEDORES, construir_extractor
from infrastructure.llm.gemini import AdaptadorGeminiVision

#: Un valor con forma de credencial que no lo es, y que se nota que no lo es.
CREDENCIAL_FALSA = "no-es-una-credencial"

#: Las variables de IA que se borran del entorno antes de cada caso.
VARIABLES_DE_IA = (
    "IA_PROVIDER",
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "IA_TIMEOUT_S",
    "IA_REINTENTOS",
)


def _ajustes(monkeypatch, **valores) -> Ajustes:
    """Ajustes deterministas: ni entorno heredado, ni `.env` de quien ejecuta."""
    for variable in VARIABLES_DE_IA:
        monkeypatch.delenv(variable, raising=False)
    return Ajustes(entorno="test", _env_file=None, **valores)


def test_f003_r11_la_fabrica_devuelve_gemini_por_defecto(monkeypatch):
    """R11 · sin tocar nada: proveedor `gemini` y modelo `gemini-3.7-flash`.

    El modelo por defecto lo decidió el humano el 2026-08-18 y es
    **configuración**, no diseño: cambiarlo no toca ni el puerto, ni el paso
    del pipeline, ni el schema.
    """
    extractor = construir_extractor(
        _ajustes(monkeypatch, gemini_api_key=CREDENCIAL_FALSA)
    )

    assert isinstance(extractor, AdaptadorGeminiVision)
    assert extractor.modelo == "gemini-3.7-flash"
    assert list(PROVEEDORES) == ["gemini"]


def test_f003_r11_el_modelo_sale_de_gemini_model(monkeypatch):
    """R11 · `GEMINI_MODEL` manda, y no se toca nada más para cambiarlo."""
    extractor = construir_extractor(
        _ajustes(
            monkeypatch,
            gemini_api_key=CREDENCIAL_FALSA,
            gemini_model="gemini-de-otra-generacion",
        )
    )

    assert isinstance(extractor, AdaptadorGeminiVision)
    assert extractor.modelo == "gemini-de-otra-generacion"


def test_f003_r12_proveedor_no_soportado_falla_listando_los_validos(monkeypatch):
    """R12 · un proveedor inventado falla diciendo cuáles hay.

    Un error de configuración que no dice las opciones obliga a leer el código
    para arreglarlo, y en Azure el código no se lee: se despliega.
    """
    ajustes = _ajustes(
        monkeypatch, ia_proveedor="inventado", gemini_api_key=CREDENCIAL_FALSA
    )

    with pytest.raises(ProveedorNoSoportado) as fallo:
        construir_extractor(ajustes)

    assert "inventado" in fallo.value.motivo
    assert "gemini" in fallo.value.motivo


def test_f003_r12_sin_credencial_falla_sin_revelarla(monkeypatch):
    """R12 · falta la clave: se nombra **la variable**, nunca su valor."""
    ajustes = _ajustes(monkeypatch, gemini_api_key=None)

    with pytest.raises(ConfiguracionIaIncompleta) as fallo:
        construir_extractor(ajustes)

    assert "GEMINI_API_KEY" in fallo.value.motivo
    assert "None" not in fallo.value.motivo


def test_f003_r12_una_credencial_en_blanco_es_como_no_tenerla(monkeypatch):
    """R12 · una variable puesta a espacios no es una credencial.

    Es el caso real de un App Setting creado y sin rellenar: el servicio
    arrancaría y fallaría contra el proveedor con un 401 indescifrable.
    """
    ajustes = _ajustes(monkeypatch, gemini_api_key="   ")

    with pytest.raises(ConfiguracionIaIncompleta) as fallo:
        construir_extractor(ajustes)

    assert "GEMINI_API_KEY" in fallo.value.motivo


def test_f003_r12_el_extractor_no_expone_la_credencial_en_su_repr(monkeypatch):
    """R12 · la credencial no sale ni por accidente en un `repr`.

    Un `@dataclass` en el adaptador imprimiría la clave entera en cualquier
    traza de excepción. Este test es lo que impide que eso llegue a pasar.
    """
    extractor = construir_extractor(
        _ajustes(monkeypatch, gemini_api_key=CREDENCIAL_FALSA)
    )

    assert CREDENCIAL_FALSA not in repr(extractor)
    assert CREDENCIAL_FALSA not in str(vars(extractor).get("modelo", ""))


def test_f003_r11_los_valores_por_defecto_de_los_ajustes_de_ia(monkeypatch):
    """R11 · lo que trae la configuración cuando nadie la toca.

    Los cuatro números están escritos por un motivo y no son intercambiables:
    **120 s** porque la Function corta a los 230 y una llamada colgada no
    puede comérselos; **3 intentos** porque más es insistir contra un
    proveedor que ya dijo que no; y la clave y la ruta del prompt porque son
    las que se despliegan.
    """
    ajustes = _ajustes(monkeypatch)

    assert ajustes.ia_proveedor == "gemini"
    assert ajustes.gemini_model == "gemini-3.7-flash"
    assert ajustes.ia_timeout_s == 120
    assert ajustes.ia_reintentos == 3
    assert ajustes.prompt_key == "parte_posventa_es"
    assert ajustes.prompts_yaml == "config/prompts.yaml"


def test_f003_r11_los_ajustes_de_ia_llegan_al_adaptador(monkeypatch):
    """R11 · timeout y reintentos también son configuración, no constantes.

    La Function corta a los 230 s: una llamada colgada no puede comérselos, y
    el número de reintentos decide cuánto se insiste antes de rendirse (R14).
    """
    ajustes = _ajustes(
        monkeypatch,
        gemini_api_key=CREDENCIAL_FALSA,
        ia_timeout_s=42,
        ia_reintentos=7,
    )

    extractor = construir_extractor(ajustes)

    assert vars(extractor)["_timeout_s"] == 42
    assert vars(extractor)["_reintentos"] == 7
