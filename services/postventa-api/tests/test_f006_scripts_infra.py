# services/postventa-api/tests/test_f006_scripts_infra.py
"""Los dos scripts de verificacion de F-006 cumplen su contrato (T16, T17, T18).

Mismo planteamiento que `test_f005_scripts_infra.py`, y por el mismo motivo:
son PowerShell, no entran en la cobertura ni en la campana de mutacion
—`harness/alcance.py` solo mide `.py`— y una revision a ojo no sobrevive a la
siguiente edicion. Lo que sobrevive es esto.

Lo que se fija aqui, y por que cada cosa:

- **El de T17 no escribe. Nunca.** Es la regla dura de `CLAUDE.md` metida en un
  test: la unica llamada que no es `GET` es la del token, que es la que Entra
  exige. Un `PUT` o un `DELETE` colandose ahi seria una escritura en el
  SharePoint de Posventa lanzada desde un puesto de trabajo.
- **Ninguno imprime el token ni el secreto.** Estos scripts los ejecuta una
  persona y su salida acaba pegada en un chat o en un ticket.
- **Ningun valor dentro.** Ni un GUID, ni una URL de despliegue, ni una
  credencial: todo sale de variables de entorno de la sesion de quien ejecuta.
- **Los dos admiten `-WhatIf`**, que es como se comprueban sin llamar a nada.

Este fichero no contiene ningun identificador: el control negativo del barrido
se compone en memoria a partir de trozos.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Raiz del repositorio, tres niveles por encima de este fichero.
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

#: El directorio de los scripts re-ejecutables.
INFRA = RAIZ / "infra"

#: Comprueba el destino de dev, **solo con lecturas** (T17).
SCRIPT_DESTINO = INFRA / "verificar_destino_sharepoint.ps1"

#: Ejercita el archivo end-to-end contra el servicio desplegado (T18).
SCRIPT_ARCHIVO = INFRA / "verificar_archivo_dev.ps1"

#: La forma de un GUID: identificadores de inquilino, sitio, biblioteca y
#: aplicacion. Ninguno puede estar en el repositorio.
PATRON_GUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

#: Una credencial escrita a mano: `secret = "loquesea"`.
PATRON_CREDENCIAL = re.compile(
    r"(?i)\b(?:password|pwd|passwd|secret|token|api[_-]?key|clave)\s*=\s*[\"'][^\"'$]",
)

#: Los verbos HTTP que escriben. En el script de solo lectura no puede haber
#: ninguno salvo el `Post` del token, que se cuenta aparte.
PATRON_VERBOS_QUE_ESCRIBEN = re.compile(r"-Method\s+(Put|Patch|Delete)", re.IGNORECASE)

#: Cualquier `-Method Post`, para poder contar los del script de solo lectura.
PATRON_POST = re.compile(r"-Method\s+Post", re.IGNORECASE)


@pytest.fixture
def destino() -> str:
    return SCRIPT_DESTINO.read_text(encoding="ascii")


@pytest.fixture
def archivo() -> str:
    return SCRIPT_ARCHIVO.read_text(encoding="ascii")


def test_f006_t16_los_dos_scripts_existen():
    """Sin scripts no hay verificacion manual que valga.

    T17 se ejecuta ahora y T18 esta diferida a F-010, pero **los dos ficheros
    se entregan dentro de F-006**: lo que se aplaza es ejecutar el segundo, no
    escribirlo.
    """
    assert SCRIPT_DESTINO.is_file()
    assert SCRIPT_ARCHIVO.is_file()


def test_f006_t16_cada_script_empieza_por_su_ruta_relativa(destino, archivo):
    """La convencion de `docs/CONVENTIONS.md`, tambien en PowerShell."""
    assert destino.startswith("# infra/verificar_destino_sharepoint.ps1")
    assert archivo.startswith("# infra/verificar_archivo_dev.ps1")


def test_f006_t17_el_script_del_destino_no_escribe_nada(destino):
    """T17 · **solo lecturas**, y esto es la regla dura escrita como test.

    La unica llamada que no es `GET` es la del token, porque Entra no da un
    token con un `GET`. Cualquier otra cosa —crear la carpeta «ya que
    estamos», subir un fichero «para probar»— seria una escritura en el
    SharePoint de Posventa lanzada desde un puesto de trabajo, que es
    exactamente lo que `CLAUDE.md` prohibe.
    """
    assert PATRON_VERBOS_QUE_ESCRIBEN.findall(destino) == []
    assert len(PATRON_POST.findall(destino)) == 1
    assert "oauth2/v2.0/token" in destino


def test_f006_t17_el_script_del_destino_lo_dice_en_su_cabecera(destino):
    """T17 · quien lo abra tiene que saber en la primera pantalla que no sube.

    Un script que no escribe pero no lo dice acaba siendo un script que
    alguien no se atreve a ejecutar, o peor, que alguien amplia sin pensarlo.
    """
    cabecera = destino[:1200]

    assert "NO SUBE NADA" in cabecera


def test_f006_t18_el_script_del_archivo_exige_la_url_del_despliegue(archivo):
    """T18 · sin `-BaseUrl` no se llama a nada, y se dice por que.

    Contra un servicio levantado en un puesto de trabajo no funcionaria ni
    debe: alli `ENTORNO` no es `dev` ni `pro` y el propio servicio responde
    503. El script lo explica en vez de fallar con un error de red.
    """
    assert "$BaseUrl" in archivo
    assert "Falta -BaseUrl" in archivo
    assert "503" in archivo


def test_f006_t18_el_pdf_de_prueba_es_sintetico(archivo):
    """T18 · nunca un parte real: llevan DNI y observaciones manuscritas.

    El PDF se genera en el propio script, asi que tampoco hay que versionar un
    binario que dentro de un ano nadie sabra de donde salio.
    """
    assert "New-Pdf-Sintetico" in archivo
    assert "%PDF-1.4" in archivo
    assert "muestras" not in archivo


def test_f006_t18_el_script_comprueba_lo_que_pide_el_criterio(archivo):
    """T18 · dos llamadas, mismo destino y **ningun** nombre con `(1)`.

    Es el `acceptance` 3 de F-006 comprobado contra una biblioteca de verdad,
    que es lo unico que la suite no puede demostrar.
    """
    assert "primera" in archivo and "segunda" in archivo
    assert "(1)" in archivo
    assert "mismo_destino" in archivo
    assert "sin_sufijo_1" in archivo


@pytest.mark.parametrize(
    "script", (SCRIPT_DESTINO, SCRIPT_ARCHIVO), ids=lambda ruta: ruta.name
)
def test_f006_t16_ningun_script_lleva_un_identificador(script):
    """T16 · ni un GUID: ni de inquilino, ni de sitio, ni de biblioteca, ni de app.

    Estos ficheros **si** se versionan, y el historial de git no suelta lo que
    entra. Todo sale de variables de entorno de la sesion de quien ejecuta.
    """
    assert PATRON_GUID.findall(script.read_text(encoding="ascii")) == []


@pytest.mark.parametrize(
    "script", (SCRIPT_DESTINO, SCRIPT_ARCHIVO), ids=lambda ruta: ruta.name
)
def test_f006_t16_ningun_script_lleva_una_credencial(script):
    """T16 · ninguna credencial escrita a mano, ni siquiera de dev."""
    assert PATRON_CREDENCIAL.findall(script.read_text(encoding="ascii")) == []


@pytest.mark.parametrize(
    "script", (SCRIPT_DESTINO, SCRIPT_ARCHIVO), ids=lambda ruta: ruta.name
)
def test_f006_t16_ningun_script_imprime_el_token_ni_el_secreto(script):
    """T16 · la salida de estos scripts se pega en un chat o en un ticket.

    Se revisa **linea a linea**: ninguna que imprima puede nombrar la variable
    del token ni la del secreto. Es mas estricto que buscar la palabra suelta,
    porque la palabra aparece legitimamente en los comentarios.
    """
    culpables = [
        linea.strip()
        for linea in script.read_text(encoding="ascii").splitlines()
        if "Write-Host" in linea
        and re.search(r"\$(token|clientSecret|ClientSecret|secreto)\b", linea)
    ]

    assert culpables == []


@pytest.mark.parametrize(
    "script", (SCRIPT_DESTINO, SCRIPT_ARCHIVO), ids=lambda ruta: ruta.name
)
def test_f006_t16_los_dos_admiten_whatif(script):
    """T16 · `-WhatIf` imprime la ayuda y **no llama a nada**.

    Es como se comprueban los dos scripts sin tocar ningun sistema, y es la
    verificacion que declara la propia tarea.
    """
    texto = script.read_text(encoding="ascii")

    assert "[switch]$WhatIf" in texto
    assert "no se ha llamado a nada" in texto


@pytest.mark.parametrize(
    "script", (SCRIPT_DESTINO, SCRIPT_ARCHIVO), ids=lambda ruta: ruta.name
)
def test_f006_t16_los_scripts_leen_del_entorno_y_no_de_constantes(script):
    """T16 · las variables se leen de la sesion, no se declaran aqui.

    Y se comprueba que las nombran por su nombre real: un script que pida
    `SHAREPOINT_ID` cuando el servicio lee `SHAREPOINT_DRIVE_ID` verifica un
    destino distinto del que se usa, que es peor que no verificar nada.
    """
    texto = script.read_text(encoding="ascii")

    assert "GetEnvironmentVariable" in texto
    assert "GRAPH_CLIENT_SECRET" in texto
    assert "SHAREPOINT_DRIVE_ID" in texto


def test_f006_t16_el_barrido_de_identificadores_caza_uno_inyectado():
    """Control negativo: un patron que nunca se ha visto saltar no protege nada.

    El valor vive **solo aqui**, compuesto en memoria a partir de trozos, para
    que ni este control escriba un identificador entero en un fichero.
    """
    inventado = "-".join(("f1e2d3c4", "b5a6", "4978", "8b1c", "2d3e4f5a6b7c"))  # noqa: FLY002
    # El `join` es deliberado: ruff propone escribir el literal, que es
    # justo lo que este fichero existe para prohibir en el repositorio.

    assert PATRON_GUID.findall(f"SHAREPOINT_DRIVE_ID={inventado}") == [inventado]


def test_f006_t16_el_barrido_de_credenciales_caza_una_inyectada():
    """Control negativo del segundo patron. El valor es inventado."""
    assert PATRON_CREDENCIAL.findall('$secret = "inventado-no-existe"')


def test_f006_t16_el_barrido_no_salta_con_lo_que_si_deben_decir():
    """Un guardian que grita con todo se acaba desactivando.

    Estas son frases que los scripts si tienen que poder escribir: leer la
    variable del entorno y nombrarla en la ayuda.
    """
    legitimos = (
        '$clientSecret = Get-Variable-De-Entorno "GRAPH_CLIENT_SECRET"',
        'Write-Host "El script NO imprime el token ni el secreto"',
        "client_secret = $ClientSecret",
    )

    for linea in legitimos:
        assert PATRON_CREDENCIAL.findall(linea) == []
        assert PATRON_GUID.findall(linea) == []
