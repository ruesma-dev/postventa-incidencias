# services/postventa-api/tests/test_f003_arquitectura.py
"""Tests de arquitectura de F-003 (R19, R13 y la segunda mitad de R8).

Tres invariantes que ningún test de comportamiento vigila, y que se degradan
solos en cuanto alguien tiene prisa:

- **R19**: la suite **no puede** abrir una conexión de red. No es una promesa
  («nadie llamará de verdad»): es la guardia autouse de `conftest.py`, y este
  test comprueba que está puesta y que muerde.
- **R13**: `domain/` y `application/` no importan `google`, `yaml`, `tenacity`
  ni `infrastructure/`. El día que se cambie de proveedor de IA, lo que hay
  por encima del puerto tiene que seguir en pie sin tocarse.
- **R8** (segunda mitad): el texto del prompt vive **solo** en
  `config/prompts.yaml`. Una copia incrustada en un módulo sería un prompt
  fantasma que nadie versiona ni evalúa.
"""

from __future__ import annotations

import socket

import pytest

#: Dirección de TEST-NET-1 (RFC 5737): no se enruta y no exige resolver DNS,
#: así que el test prueba la guardia y no la red de quien lo ejecuta.
_DIRECCION_INERTE = ("192.0.2.1", 80)


def test_f003_r19_la_suite_no_puede_abrir_conexiones_de_red():
    """R19 · intentar conectar desde un test falla de forma explícita.

    Sin la guardia esto sale por `socket.timeout` —un `OSError` de red de
    verdad— o, peor, llega a conectar. Con ella sale un `RuntimeError` que
    dice qué ha pasado, y por eso «ni una llamada real a la IA» deja de ser
    una promesa y pasa a ser imposible.
    """
    conector = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conector.settimeout(0.5)

    try:
        with pytest.raises(RuntimeError) as fallo:
            conector.connect(_DIRECCION_INERTE)
    finally:
        conector.close()

    assert "conexiones" in str(fallo.value)
