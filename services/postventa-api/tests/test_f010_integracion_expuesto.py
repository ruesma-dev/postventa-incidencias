# services/postventa-api/tests/test_f010_integracion_expuesto.py
"""La seccion 8 de `docs/INTEGRACION.md` dice que exponemos y que NO (R26).

`test_f005_integracion_sin_secretos.py` ya vigila que en ese documento no entre
ningun valor. Lo que falta, y es lo que fija este fichero, es que la seccion 8
diga la verdad **completa**: no solo lo que el piloto hace, tambien lo que
todavia no hace.

El motivo no es documental. El entorno desplegado se le va a ensenar a
negocio, y hay dos ausencias que se notan en la primera sesion:

- **el cierre de la incidencia en Sigrid** (F-009) y, dentro de el, el parte
  subido al ERP como grafico (F-012). Desde F-009 el cierre existe, pero su
  ventana de escritura se despliega APAGADA y no se ha ejecutado ni un cierre
  real: mientras siga asi, Sigrid no se toca, y eso hay que decirlo igual;
- **la sesion que no se rehidrata**: si el usuario recarga la pagina, pierde el
  trabajo en curso.

Descubrir eso durante la demostracion es caro. Que este escrito antes es
barato. De ahi que sea un test y no una buena intencion.

## Que cambio con F-019 (2026-08-26)

F-019 desplego los tres endpoints de persistencia, asi que **deja de ser una
ausencia**: la remesa se guarda, el parte se guarda y la cola sobrevive entre
sesiones. Lo que sigue faltando -y por eso sigue en la tabla, con otro nombre-
es **rehidratar la sesion al recargar**: volver a pintar el trabajo en curso
exige leer una remesa entera con sus partes, que es un metodo de lectura nuevo
en `RepositorioPartesPort` y quedo como **feature nueva** por decision del
humano (D4).

La consecuencia visible **no se ha borrado**, porque sigue siendo cierta: se
ha reatribuido a lo que de verdad la causa. Borrarla habria dejado el
documento prometiendo algo que la demostracion desmiente en la primera
recarga.
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
#:
#: F-019 **sale de la lista**: se desplego el 2026-08-26 y seguir diciendo que
#: falta seria peor que no decirlo, porque quien lea el documento antes de una
#: demostracion se preparara para explicar algo que ya funciona. Lo que sigue
#: faltando -rehidratar la sesion al recargar- no tiene numero de feature
#: todavia y se comprueba aparte, por su consecuencia.
#:
#: F-008 **sale tambien**: era una investigacion de solo lectura y termino;
#: lo que dejo escrito vive en docs/referencia/. Y F-012 **entra**: es lo que
#: falta para que el parte llegue a estar dentro del ERP, y es la ausencia que
#: mas se va a notar en una demostracion, porque la ficha de Sigrid quedara
#: cerrada sin el documento adjunto.
NO_DESPLEGADAS = ("F-009", "F-012")


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
    """R26 · los dos recursos y los **nueve** endpoints, con su efecto.

    Y sobre todo cuales de ellos escriben: `archivar` es el unico con efecto
    sobre un sistema **ajeno y compartido**, y es el que lleva la ventana de
    escritura; los tres de F-019 escriben en el esquema propio del proyecto.
    """
    for endpoint in (
        "/api/health",
        "/api/split",
        "/api/extraer",
        "/api/firma",
        "/api/validar",
        "/api/remesa",
        "/api/parte",
        "/api/cola",
        "/api/archivar",
    ):
        assert endpoint in seccion_ocho

    assert "swa-postventa-ruesma" in seccion_ocho
    assert "func-postventa-dev" in seccion_ocho
    assert "posventa-usuarios" in seccion_ocho


@pytest.mark.parametrize("feature", NO_DESPLEGADAS)
def test_f010_r26_la_seccion_ocho_nombra_lo_que_no_esta_desplegado(seccion_ocho, feature):
    """R26 · F-008 y F-009, por su nombre y con su consecuencia.

    Nombrar la feature sin decir que se nota no sirve: quien lee el documento
    antes de una demostracion no sabe que es F-009.
    """
    assert feature in seccion_ocho


def test_f010_r26_dice_la_consecuencia_visible_de_cada_ausencia(seccion_ocho):
    """R26 · «falta una feature» no le dice nada a nadie; «pierde el trabajo», si.

    La consecuencia de la recarga **se conserva** aunque F-019 este desplegada:
    lo guardado queda guardado, pero volver a pintarlo en pantalla sigue sin
    hacerse. Borrar la frase habria dejado el documento prometiendo algo que la
    demostracion desmiente en la primera recarga.
    """
    assert "Sigrid no se toca" in seccion_ocho
    assert "pierde el trabajo en curso" in seccion_ocho


@pytest.fixture
def tabla_de_ausencias(seccion_ocho: str) -> str:
    """La tabla de «Que NO esta desplegado», sola.

    Se acota a proposito: F-019 se sigue nombrando **arriba**, describiendo los
    endpoints que aporto, y eso es correcto. Lo que no puede es seguir en la
    lista de lo que falta.
    """
    hallado = re.search(
        r"^### Qué NO está desplegado.*?$(.*?)^### ",
        seccion_ocho,
        re.DOTALL | re.MULTILINE,
    )
    assert hallado is not None, "no se encuentra la tabla de ausencias"
    return hallado.group(1)


def test_f019_r32_la_tabla_de_ausencias_ya_no_atribuye_a_f019_lo_que_esta_hecho(
    tabla_de_ausencias,
):
    """R32 · F-019 dejo de ser una ausencia el 2026-08-26.

    Este es el test que impide el fallo mas probable de mantener esta tabla:
    dejarla como estaba. Un documento que sigue anunciando como pendiente lo
    que ya se desplego hace que quien lo lea desconfie del resto, y este
    documento es el que viaja a `azure-apps/`.

    Lo que sigue faltando **no se borra**: se reatribuye a su causa real, la
    rehidratacion de la sesion, que es feature nueva (D4).
    """
    assert "F-019" in tabla_de_ausencias, (
        "la fila tiene que citar F-019 como la decision que dejo fuera la "
        "rehidratacion, no como la feature que falta"
    )
    assert "Guardar la remesa y leer la cola" not in tabla_de_ausencias
    assert "Rehidratar la sesión" in tabla_de_ausencias
    assert "feature nueva" in tabla_de_ausencias


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
