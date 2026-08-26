# services/postventa-api/tests/test_f010_integracion_expuesto.py
"""La seccion 8 de `docs/INTEGRACION.md` dice que exponemos y que NO (R26).

`test_f005_integracion_sin_secretos.py` ya vigila que en ese documento no entre
ningun valor. Lo que falta, y es lo que fija este fichero, es que la seccion 8
diga la verdad **completa**: no solo lo que el piloto hace, tambien lo que
todavia no hace.

El motivo no es documental. El entorno desplegado se le va a ensenar a
negocio, y hay dos ausencias que se notan en la primera sesion:

- **el cierre de la incidencia en Sigrid** (F-008, F-009), que es justo lo que
  el humano dejo fuera a proposito;
- **la cola persistida** (F-019): si el usuario recarga la pagina, pierde el
  trabajo en curso.

Descubrir eso durante la demostracion es caro. Que este escrito antes es
barato. De ahi que sea un test y no una buena intencion.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Raiz del repositorio, tres niveles por encima de este fichero.
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

#: La fuente de verdad de lo que este proyecto consume y expone.
INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"

#: Las features cuya ausencia se nota, y por eso tienen que constar.
NO_DESPLEGADAS = ("F-008", "F-009", "F-019")


@pytest.fixture
def documento() -> str:
    return INTEGRACION.read_text(encoding="utf-8")


@pytest.fixture
def seccion_ocho(documento: str) -> str:
    """De «Que exponemos nosotros» hasta la seccion siguiente."""
    hallado = re.search(
        r"^## 8 · Qué exponemos nosotros$(.*?)^## ", documento, re.DOTALL | re.MULTILINE
    )
    assert hallado is not None, "no se encuentra la seccion 8"
    return hallado.group(1)


def test_f010_r26_la_seccion_ocho_ya_no_esta_vacia(seccion_ocho):
    """R26 · decia «esta seccion se rellena en el mismo trabajo». Es este.

    La frase que anunciaba el hueco tiene que haber desaparecido: un documento
    que sigue prometiendo lo que ya se hizo confunde mas que uno incompleto.
    """
    assert "esta sección se rellena" not in seccion_ocho
    assert len(seccion_ocho.strip()) > 500


def test_f010_r26_la_seccion_ocho_dice_que_se_expone(seccion_ocho):
    """R26 · los dos recursos y los seis endpoints, con su efecto.

    Y sobre todo cual de ellos escribe: `archivar` es el unico con efecto
    sobre un sistema compartido, y es el que lleva la ventana de escritura.
    """
    for endpoint in ("/api/health", "/api/split", "/api/extraer", "/api/firma", "/api/validar", "/api/archivar"):
        assert endpoint in seccion_ocho

    assert "swa-postventa-ruesma" in seccion_ocho
    assert "func-postventa-dev" in seccion_ocho
    assert "posventa-usuarios" in seccion_ocho


@pytest.mark.parametrize("feature", NO_DESPLEGADAS)
def test_f010_r26_la_seccion_ocho_nombra_lo_que_no_esta_desplegado(seccion_ocho, feature):
    """R26 · F-008, F-009 y F-019, por su nombre y con su consecuencia.

    Nombrar la feature sin decir que se nota no sirve: quien lee el documento
    antes de una demostracion no sabe que es F-019.
    """
    assert feature in seccion_ocho


def test_f010_r26_dice_la_consecuencia_visible_de_cada_ausencia(seccion_ocho):
    """R26 · «no esta F-019» no le dice nada a nadie; «pierde el trabajo», si."""
    assert "Sigrid no se toca" in seccion_ocho
    assert "pierde el trabajo en curso" in seccion_ocho


def test_f010_r26_advierte_de_que_no_es_una_api_para_terceros(seccion_ocho):
    """Un documento del ecosistema que lista endpoints invita a llamarlos.

    Esto es una aplicacion de usuario: el contrato es interno y cambia con las
    features. Que nadie empiece a consumirlo sin hablarlo.
    """
    assert "no una API para terceros" in seccion_ocho or "no un servicio que otro proyecto deba llamar" in seccion_ocho


def test_f010_r32_la_seccion_ocho_explica_la_anonimidad_de_los_endpoints(seccion_ocho):
    """R32 · el aviso tambien aqui, porque este es el documento que se copia.

    `docs/INTEGRACION.md` es la fuente de verdad que viaja a `azure-apps/`.
    Alguien que lea alli «los seis endpoints son anonimos» sin la explicacion
    al lado abre un ticket, o peor, lo «arregla».
    """
    assert "anónimo" in seccion_ocho
    assert "deliberado" in seccion_ocho
    assert "rompe el front" in seccion_ocho
