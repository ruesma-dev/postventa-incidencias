# services/postventa-api/tests/test_fix_ajustes_sin_secretos_en_repr.py
"""Los secretos de `Ajustes` no salen en su `repr` ni en su `str`.

Arreglo sin spec (2026-11-18): un traceback de pytest imprimió el `repr` de
`Ajustes` y, con él, parte de la clave de Gemini. Los cuatro secretos llevan
`repr=False` en su `Field`; siguen siendo legibles como atributo, porque los
adaptadores los necesitan tal cual.

Los valores son FALSOS y evidentes a propósito: aquí no hay ninguna clave real.
"""

from __future__ import annotations

import pytest
from config.settings import Ajustes

#: Campo -> valor falso, escritos a mano. Cada valor es único para que su
#: aparición en el texto no pueda venir de otro campo.
SECRETOS_FALSOS = {
    "gemini_api_key": "FALSO-gemini-clave-0001",
    "pg_password": "FALSO-pg-contrasena-0002",
    "graph_client_secret": "FALSO-graph-secreto-0003",
    "sigrid_api_key": "FALSO-sigrid-clave-0004",
}


@pytest.fixture
def ajustes(monkeypatch, tmp_path):
    """`Ajustes` aislados del `.env` y del entorno, con los secretos falsos."""
    for variable in (
        "GEMINI_API_KEY",
        "PG_PASSWORD",
        "GRAPH_CLIENT_SECRET",
        "SIGRID_API_KEY",
    ):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.chdir(tmp_path)
    return Ajustes(entorno="test", _env_file=None, **SECRETOS_FALSOS)


@pytest.mark.parametrize("campo", sorted(SECRETOS_FALSOS))
def test_fix_el_repr_no_contiene_el_secreto(ajustes, campo):
    """Ni `repr` ni `str` dejan ver el valor del secreto."""
    valor = SECRETOS_FALSOS[campo]
    assert valor not in repr(ajustes), f"{campo} aparece en repr(Ajustes)"
    assert valor not in str(ajustes), f"{campo} aparece en str(Ajustes)"


@pytest.mark.parametrize("campo", sorted(SECRETOS_FALSOS))
def test_fix_el_secreto_sigue_legible_como_atributo(ajustes, campo):
    """Ocultarlo del `repr` no cambia su valor: sigue siendo un `str` tal cual."""
    assert getattr(ajustes, campo) == SECRETOS_FALSOS[campo]


def test_fix_el_repr_sigue_mostrando_campos_que_no_son_secretos(ajustes):
    """El `repr` sigue siendo útil para depurar: solo se ocultan los secretos."""
    assert "entorno='test'" in repr(ajustes)
