# services/postventa-api/tests/test_f031_cotejo_de_codigos.py
"""Lo declarado tiene que ser lo guardado, o no se archiva (F-031 R3–R6, R9–R11).

Se prueba **desde `POST /api/archivar`**, con la petición `multipart/form-data`
construida a mano y los dos puertos sustituidos por dobles, igual que
`test_f006_archivar_http.py`: así se ejercita el borde entero —parseo, códigos
de estado, JSON— y por debajo corre el paso de verdad. **SharePoint no aparece
por ninguna parte** y no se abre ni un socket (R28).

## Qué separa este fichero de `test_f031_nombrado_persistido.py`

Aquél vigila **de dónde sale el nombre**; éste, **qué pasa cuando el cuerpo
dice otra cosa**. Son las dos mitades del mismo requisito y se rompen por
sitios distintos: el primero se rompería nombrando con el cuerpo, el segundo
dejando pasar una divergencia.

Y lo que de verdad importa de casi todos los casos de aquí no es el código
HTTP: es que **no se haya escrito ni subido nada**. Por eso los dobles cuentan
escrituras y llamadas, y no se limitan a devolver lo que el test esperaba.

**Ni un dato real.** El «PDF» lleva un DNI inventado —`00000000T` no es
válido— justamente para comprobar que no se cuela en ningún mensaje de error.
"""

from __future__ import annotations

from domain.models.errores import (
    CodigosNoCoinciden,
    NombradoImposible,
    ParteNoApto,
)

# --------------------------------------------------------------------------
# El error de dominio (T3) · por qué es propio y no `ParteNoApto` reutilizado
# --------------------------------------------------------------------------


def test_f031_errores_codigos_no_coinciden_lleva_su_motivo():
    """El `motivo` viaja en el objeto, como en sus hermanas.

    El borde lo lee para componer el cuerpo del 409, igual que hace con
    `ParteNoApto` y con `NombradoImposible`. Sin él, el error saldría como un
    409 mudo y quien lo recibiera tendría que ir a mirar la base a mano.
    """
    error = CodigosNoCoinciden("el código de obra de la petición no es el guardado")

    assert isinstance(error, Exception)
    assert error.motivo == "el código de obra de la petición no es el guardado"
    assert str(error) == error.motivo


def test_f031_errores_no_es_parte_no_apto_ni_nombrado_imposible():
    """Excepción propia, y la distinción **no es cosmética**.

    Los tres son 409, pero llevan a acciones **opuestas**: `ParteNoApto` se
    arregla decidiendo sobre el parte, `NombradoImposible` mandándolo a
    revisión manual, y esto **guardando la corrección** y volviendo a
    intentarlo. Si heredara de cualquiera de las otras dos, el `except` que ya
    existe en el borde se la tragaría y el mensaje que le llega a una persona
    sería el que no es.
    """
    assert not issubclass(CodigosNoCoinciden, ParteNoApto)
    assert not issubclass(CodigosNoCoinciden, NombradoImposible)
    assert not issubclass(ParteNoApto, CodigosNoCoinciden)
    assert not issubclass(NombradoImposible, CodigosNoCoinciden)


def test_f031_errores_el_docstring_dice_en_que_se_diferencia_de_sus_hermanas():
    """El porqué vive al lado del error, no solo en la spec.

    Es lo que ya hacen `ParteNoArchivado`, `ArchivoSinTraza` y
    `ReferenciaNoConsta`, cada una con su docstring diciendo por qué tiene
    nombre propio. Quien se encuentre este error dentro de seis meses lee el
    módulo, no `specs/F-031-nombrado-persistido/design.md`.
    """
    documentacion = CodigosNoCoinciden.__doc__ or ""

    assert "ParteNoApto" in documentacion
    assert "NombradoImposible" in documentacion
    assert "F-031" in documentacion
