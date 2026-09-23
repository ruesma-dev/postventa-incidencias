# services/postventa-api/tests/test_f034_codigos_en_el_erp.py
"""Los dos códigos con los que se escribe en el ERP salen de lo guardado (F-034).

Este fichero crece por bloques (`tasks.md`):

- **Bloque 1** (este): las piezas compartidas. El error nuevo,
  `CodigoNoConsta` (R15, R28), y en qué se diferencia de sus tres hermanas
  de 409.
- **Bloques 2 y 3**: `POST /api/adjuntar` y `POST /api/cerrar` con los puertos
  inyectados (R8–R19, R24, R27).

**Sin red, sin base de datos, sin IA y sin tocar el ERP** (R37).
"""

from __future__ import annotations

import pytest
from domain.models.errores import (
    CodigoNoConsta,
    CodigosNoCoinciden,
    NombradoImposible,
    ParteNoApto,
    ParteNoArchivado,
)

# --------------------------------------------------------------------------
# R15, R28 · el error nuevo, y por qué es un error propio
# --------------------------------------------------------------------------

#: Las hermanas de 409 de las que `CodigoNoConsta` tiene que distinguirse
#: (`design.md` §3.2). Cada una manda a quien la lee a un sitio distinto.
HERMANAS_DE_409 = (CodigosNoCoinciden, ParteNoArchivado, NombradoImposible)


def test_f034_r15_errores_codigo_no_consta_lleva_su_motivo():
    """R15 · el `motivo` viaja en el objeto, como en sus hermanas.

    El borde lo lee para componer el cuerpo del 409 (`{"error": <motivo>}`,
    R27). Sin él, el error saldría mudo y quien lo recibiera no sabría **cuál**
    de los dos códigos falta.
    """
    error = CodigoNoConsta("no consta guardado el nº de incidencia de este parte")

    assert isinstance(error, Exception)
    assert error.motivo == "no consta guardado el nº de incidencia de este parte"
    assert str(error) == error.motivo


@pytest.mark.parametrize("hermana", HERMANAS_DE_409 + (ParteNoApto,))
def test_f034_r28_errores_codigo_no_consta_no_es_ninguna_hermana(hermana):
    """R28 · tres hechos, tres errores; la distinción **no es cosmética**.

    Si `CodigoNoConsta` heredara de cualquiera de ellas —o al revés—, un
    `except` del borde se la tragaría y a la persona le llegaría el mensaje de
    otro hecho, que se arregla de otra forma: guardar una corrección no sirve
    de nada si lo que falta es teclear el código.
    """
    assert not issubclass(CodigoNoConsta, hermana)
    assert not issubclass(hermana, CodigoNoConsta)


def test_f034_r28_errores_el_docstring_dice_en_que_se_diferencia():
    """R28 · el porqué vive al lado del error, no solo en la spec.

    Quien se encuentre este error dentro de seis meses lee el módulo, no
    `specs/F-034-archivo-persistido-en-erp/design.md`. Nombra las tres
    hermanas de las que se distingue y la ficha que lo introduce.
    """
    documentacion = CodigoNoConsta.__doc__ or ""

    for hermana in HERMANAS_DE_409:
        assert hermana.__name__ in documentacion
    assert "F-034" in documentacion


def test_f034_r28_errores_el_modulo_lo_cuenta_entre_los_409():
    """R28 · la cabecera de `errores.py` reparte cada error en su familia.

    Es el mapa que lee quien llega al módulo: si `CodigoNoConsta` no aparece
    ahí, el reparto 400/409/503 que el borde respeta queda incompleto.
    """
    from domain.models import errores

    assert "CodigoNoConsta" in (errores.__doc__ or "")
