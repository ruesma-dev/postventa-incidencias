# services/postventa-api/tests/test_f006_arquitectura.py
"""Invariantes de F-006 que ningún test de comportamiento vigila (R21, R22, R26, R29, R32).

Cinco cosas que se degradan solas en cuanto alguien tiene prisa un viernes, y
que si se degradan **no se nota** hasta que es tarde:

- **R21**: la suite no puede abrir conexiones, y ningún test puede construir un
  adaptador real capaz de llegar a la red.
- **R22**: ni el dominio ni la aplicación conocen Microsoft Graph. El único
  paquete que lo conoce es `infrastructure/sharepoint/`.
- **R26**: ni un identificador con forma de GUID entra en el servicio.
- **R29**: los ejemplos de entorno llevan placeholders y ningún valor.
- **R32**: `docs/INTEGRACION.md` declara qué consumimos de SharePoint.

Va aparte de `test_f005_arquitectura.py` a propósito, por lo mismo que aquel
fue aparte de `test_f003_arquitectura.py`: un fallo aquí dice de qué feature es.
"""

from __future__ import annotations

import ast
import re
import socket
from pathlib import Path

import pytest

#: Raíz del servicio (este fichero vive en `<servicio>/tests/`) y del repo.
SERVICIO = Path(__file__).resolve().parent.parent
RAIZ = SERVICIO.parent.parent

#: Carpetas que no son código del servicio.
_IGNORADAS = (".venv", "__pycache__", ".pytest_cache", ".ruff_cache")

#: Lo que ni el dominio ni la aplicación pueden importar (R22).
#:
#: Los tres clientes HTTP que se barajaron para hablar con Graph —`httpx` es
#: el que se usa desde la decisión del humano del 2026-08-20, `msal` y
#: `requests` eran los de la spec— y la capa de infraestructura entera. Se
#: nombran los tres aunque solo uno esté instalado: el día que alguien meta
#: otro por la puerta de atrás, este test ya está escrito.
PROHIBIDOS_ARRIBA_DEL_PUERTO = ("httpx", "msal", "requests", "infrastructure")

#: El único paquete del servicio que puede conocer el cliente de Graph (R22).
PAQUETE_DE_GRAPH = "infrastructure/sharepoint"

#: Los paquetes de infraestructura que pueden hablar HTTP con un sistema ajeno.
#:
#: Eran uno hasta F-009, que añadió `infrastructure/sigrid/` para el ERP. La
#: lista crece con cada sistema externo nuevo, y crecer así **es** el
#: invariante: cada uno vive aislado en su paquete, y ninguna otra parte del
#: servicio —ni un handler, ni un paso del pipeline— puede abrir una conexión.
#: `test_f009_arquitectura.py` fija lo mismo desde el lado del ERP.
PAQUETES_CON_CLIENTE_HTTP = ("infrastructure/sharepoint", "infrastructure/sigrid")

#: Los ficheros de la suite autorizados a nombrar el adaptador real (R21).
#:
#: Son **dos**, y cada uno por un motivo distinto:
#:
#: - `test_f006_fabrica.py` lo construye para comprobar que **se niega** con
#:   `ENTORNO=test`. Es la prueba de la puerta 1 de `design.md` §5.
#: - `test_f006_adaptador_graph.py` es el fichero cuyo objeto **es** el
#:   adaptador: no hay forma de probarlo sin construirlo, y siempre lo
#:   construye con el cliente falso inyectado, lo que comprueba
#:   `test_f006_r21_el_adaptador_de_los_tests_siempre_lleva_un_cliente_falso`.
#:
#: `tasks.md` (T13) decía **uno**, porque se escribió antes que el fichero que
#: la propia T9 obliga a crear. La desviación está anotada en
#: `progress/impl_F-006.md`.
FICHEROS_QUE_PUEDEN_NOMBRAR_EL_ADAPTADOR = (
    "test_f006_fabrica.py",
    "test_f006_adaptador_graph.py",
)

#: El nombre de la clase, **compuesto en memoria y nunca escrito entero**.
#:
#: No es un capricho: si este fichero —que es el que vigila— llevara el
#: literal dentro, se delataría a sí mismo y habría que meterlo en su propia
#: lista de excepciones. Un guardián que necesita una excepción para sí mismo
#: es un guardián con un agujero del tamaño de un fichero.
NOMBRE_DEL_ADAPTADOR = "Adaptador" + "SharePoint" + "Graph"

#: Un identificador de tenant, suscripción, aplicación, sitio o biblioteca.
PATRON_GUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

#: Los **dos** ficheros que ya llevaban un GUID inventado antes de F-006.
#:
#: Son controles negativos declarados de F-005: existen para demostrar que los
#: barridos de aquella feature saltan, y sus valores están inventados.
#:
#: Se toleran **por ruta y nunca por valor**: escribir aquí los GUID para
#: excluirlos sería meter en el repositorio exactamente lo que este test
#: prohíbe. Lo que sí se acota es **cuántos** puede haber en cada uno, más
#: abajo, para que la excepción no se convierta en un desagüe.
FICHEROS_CON_CONTROL_NEGATIVO_DE_F005 = (
    "tests/test_f005_integracion_sin_secretos.py",
    "tests/test_f005_repo_sin_datos_personales.py",
)

#: Las variables de destino y credencial que F-006 añade (R29).
VARIABLES_DE_F006 = (
    "ARCHIVO_HABILITADO",
    "SHAREPOINT_SITE_ID",
    "SHAREPOINT_DRIVE_ID",
    "SHAREPOINT_CARPETA_BASE",
    "GRAPH_TENANT_ID",
    "GRAPH_CLIENT_ID",
    "GRAPH_CLIENT_SECRET",
    "GRAPH_TIMEOUT_S",
    "GRAPH_REINTENTOS",
)

#: Los ficheros de ejemplo de entorno, que nunca llevan un valor (R29).
EJEMPLOS = (
    SERVICIO / ".env.example",
    SERVICIO / "local.settings.json.example",
)

#: El documento del ecosistema, que crea F-005 y al que F-006 añade su sección.
INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"


def _modulos_python() -> list[Path]:
    """Todos los módulos del servicio, sin el venv ni las cachés."""
    return sorted(
        fichero
        for fichero in SERVICIO.rglob("*.py")
        if not any(parte in _IGNORADAS for parte in fichero.parts)
    )


def _modulos_importados(fichero: Path) -> set[str]:
    """Módulos raíz que importa un fichero, sea al principio o dentro.

    Con `ast` y no con una búsqueda de texto: un `import` dentro de una
    función también cuenta, y uno citado en un comentario o en un docstring
    no.
    """
    arbol = ast.parse(fichero.read_text(encoding="utf-8"))
    modulos: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name.split(".")[0] for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module.split(".")[0])
    return modulos


def _ficheros_de(*capas: str) -> list[Path]:
    """Los módulos de las capas pedidas, por nombre de directorio raíz."""
    return [
        fichero
        for fichero in _modulos_python()
        for capa in capas
        if fichero.is_relative_to(SERVICIO / capa)
    ]


def _relativa(fichero: Path) -> str:
    return fichero.relative_to(SERVICIO).as_posix()


# --------------------------------------------------------------------------
# R21 · Ni una conexión, ni un adaptador real que pueda abrirla
# --------------------------------------------------------------------------


def test_f006_r21_la_suite_no_puede_abrir_conexiones():
    """R21 · la guardia de red de F-003 sigue mordiendo, y F-006 no la toca.

    Es la tercera puerta de `design.md` §5, y la última red de seguridad: si
    algún día alguien saltara la del entorno y la del interruptor, la conexión
    **no llega a abrirse**.

    Se prueba contra el host de Graph, que es exactamente al que iría el
    adaptador de esta feature.
    """
    with pytest.raises(RuntimeError) as fallo:
        socket.socket().connect(("graph.microsoft.com", 443))

    assert "no puede abrir conexiones" in str(fallo.value)


def test_f006_r21_la_guardia_de_red_no_se_ha_aflojado():
    """R21 · y sigue instalada, no solo «funcionando en este test».

    Aflojarla para que algún test de F-006 «pruebe de verdad» sería destruir
    la mejor defensa del proyecto. `tests/conftest.py` no se toca en esta
    feature.
    """
    assert socket.socket.connect.__name__ == "_conexion_prohibida"


def test_f006_r21_ningun_test_construye_el_adaptador_real():
    """R21 · solo los dos ficheros autorizados nombran el adaptador.

    Una construcción suelta del adaptador en cualquier otro test sería un
    intento de subida real esperando a que alguien cambie una variable de
    entorno.
    """
    aguja = f"{NOMBRE_DEL_ADAPTADOR}("
    culpables = [
        _relativa(fichero)
        for fichero in (SERVICIO / "tests").glob("*.py")
        if aguja in fichero.read_text(encoding="utf-8")
        and fichero.name not in FICHEROS_QUE_PUEDEN_NOMBRAR_EL_ADAPTADOR
    ]

    assert culpables == []


def test_f006_r21_el_adaptador_de_los_tests_siempre_lleva_un_cliente_falso():
    """R21 · y en el fichero que sí lo construye, **nunca** con cliente real.

    Esta comprobación no la pedía la spec y es más fuerte que la lista de
    ficheros: lo que de verdad importa no es qué fichero puede nombrar la
    clase, sino que **ninguna construcción de la suite pueda llegar a la
    red**. Sin `cliente=`, el adaptador se fabricaría un `httpx.Client` de
    verdad en la primera llamada.
    """
    fichero = SERVICIO / "tests" / "test_f006_adaptador_graph.py"
    arbol = ast.parse(fichero.read_text(encoding="utf-8"))

    construcciones = [
        nodo
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Name)
        and nodo.func.id == NOMBRE_DEL_ADAPTADOR
    ]

    assert construcciones, "se esperaba al menos una construcción que revisar"
    for construccion in construcciones:
        claves = {argumento.arg for argumento in construccion.keywords}
        assert "cliente" in claves
        assert "entorno" in claves


# --------------------------------------------------------------------------
# R22 · Arriba del puerto no se sabe que debajo hay Graph
# --------------------------------------------------------------------------


def test_f006_r22_dominio_y_aplicacion_no_conocen_graph():
    """R22 · ni `httpx`, ni `msal`, ni `requests`, ni `infrastructure`.

    Es lo que permite probar el paso de archivo entero con un doble en memoria
    —sin red y sin subir nada— y lo que impide que el cliente HTTP se cuele en
    el dominio por la puerta de atrás.
    """
    ficheros = _ficheros_de("domain", "application")

    assert ficheros, "no se ha encontrado ningún módulo que revisar"

    culpables = {
        _relativa(fichero): sorted(
            _modulos_importados(fichero).intersection(PROHIBIDOS_ARRIBA_DEL_PUERTO)
        )
        for fichero in ficheros
        if _modulos_importados(fichero).intersection(PROHIBIDOS_ARRIBA_DEL_PUERTO)
    }

    assert culpables == {}


def test_f006_r22_solo_infrastructure_sharepoint_importa_graph():
    """R22 · el cliente HTTP vive en un solo paquete del código de producción.

    Si mañana Graph se sustituye por otra cosa, esa es la única pieza que hay
    que reescribir. Un `httpx` suelto en un handler sería un adaptador
    escondido que nadie mira antes de que escriba en un sistema compartido.
    """
    culpables = [
        _relativa(fichero)
        for fichero in _modulos_python()
        if "httpx" in _modulos_importados(fichero)
        and not _relativa(fichero).startswith(PAQUETES_CON_CLIENTE_HTTP)
        and not _relativa(fichero).startswith("tests/")
    ]

    assert culpables == []


def test_f006_r22_el_puerto_del_archivo_es_dominio_puro():
    """R22 · el puerto no puede importar nada de fuera del dominio.

    Un puerto que importara el cliente HTTP para tipar algo dejaría de ser una
    frontera y pasaría a ser un envoltorio.
    """
    importados = _modulos_importados(SERVICIO / "domain" / "ports" / "archivo.py")

    assert importados.intersection(PROHIBIDOS_ARRIBA_DEL_PUERTO) == set()


# --------------------------------------------------------------------------
# R26 · Ni un identificador dentro del servicio
# --------------------------------------------------------------------------


def test_f006_r26_ningun_fichero_del_servicio_incrusta_un_identificador():
    """R26 · ni un GUID: ni de tenant, ni de sitio, ni de biblioteca, ni de app.

    Da igual que el repositorio sea privado: el historial de git no suelta lo
    que entra. Y da igual que el GUID sea inventado: quien lo lea no puede
    distinguirlo de uno de verdad, así que aquí no entra ninguno de los dos.

    Si esto falla, **no se relaja el patrón**: se saca el valor del fichero. Y
    si ya está commiteado, se avisa al humano.
    """
    hallazgos = {
        _relativa(fichero): PATRON_GUID.findall(fichero.read_text(encoding="utf-8"))
        for fichero in _ficheros_del_servicio()
        if _relativa(fichero) not in FICHEROS_CON_CONTROL_NEGATIVO_DE_F005
        and PATRON_GUID.findall(fichero.read_text(encoding="utf-8"))
    }

    assert hallazgos == {}


def test_f006_r26_la_excepcion_de_f005_no_crece_sin_que_se_vea():
    """R26 · dos ficheros, **un** GUID cada uno, y ni uno más.

    Una lista de excepciones que se puede ampliar en silencio deja de ser una
    defensa al tercer viernes. Ampliarla obliga a cambiar estos números y a
    explicar por qué en la revisión.

    Se acota el número y no el valor a propósito: escribir los valores aquí
    para poder excluirlos sería meter en el repositorio justo lo que el
    barrido prohíbe.
    """
    assert len(FICHEROS_CON_CONTROL_NEGATIVO_DE_F005) == 2

    for ruta in FICHEROS_CON_CONTROL_NEGATIVO_DE_F005:
        fichero = SERVICIO / ruta
        assert fichero.is_file(), f"{ruta} ya no existe: sobra la excepción"
        assert len(PATRON_GUID.findall(fichero.read_text(encoding="utf-8"))) == 1


def test_f006_r26_el_barrido_de_guids_caza_uno_inyectado():
    """R26 · control negativo: un patrón que nunca se ha visto saltar no protege.

    El valor vive **solo aquí**, compuesto en memoria a partir de trozos, para
    que ni siquiera este control escriba un GUID entero en un fichero del
    repositorio.
    """
    inventado = "-".join(("a1b2c3d4", "e5f6", "4a7b", "8c9d", "e0f1a2b3c4d5"))  # noqa: FLY002
    # El `join` es deliberado: ruff propone escribir el literal, que es
    # justo lo que este fichero existe para prohibir en el repositorio.

    assert PATRON_GUID.findall(f"SHAREPOINT_SITE_ID={inventado}") == [inventado]


def _ficheros_del_servicio() -> list[Path]:
    """Los ficheros de texto del servicio que se barren buscando valores."""
    sufijos = (".py", ".md", ".json", ".txt", ".yaml", ".yml", ".example", ".sql")
    return sorted(
        fichero
        for fichero in SERVICIO.rglob("*")
        if fichero.is_file()
        and fichero.suffix in sufijos
        and not any(parte in _IGNORADAS for parte in fichero.parts)
    )


# --------------------------------------------------------------------------
# R29 · Los ejemplos de entorno, con placeholders y sin un solo valor
# --------------------------------------------------------------------------


@pytest.mark.parametrize("ejemplo", EJEMPLOS, ids=lambda ruta: ruta.name)
def test_f006_r29_los_ejemplos_de_entorno_no_traen_valores(ejemplo):
    """R29 · las nueve variables están, y ninguna trae un valor real.

    Son los dos ficheros que más tientan: quien configura un despliegue está a
    un copiar y pegar de dejar ahí el identificador de la biblioteca «para no
    tener que buscarlo la próxima vez».
    """
    texto = ejemplo.read_text(encoding="utf-8")

    for variable in VARIABLES_DE_F006:
        assert variable in texto, f"falta {variable} en {ejemplo.name}"

    assert PATRON_GUID.findall(texto) == []


@pytest.mark.parametrize("ejemplo", EJEMPLOS, ids=lambda ruta: ruta.name)
def test_f006_r29_el_secreto_de_los_ejemplos_es_un_placeholder(ejemplo):
    """R29 · `GRAPH_CLIENT_SECRET` no puede traer nada que parezca un secreto.

    Vacío o un placeholder en castellano. Cualquier otra cosa es una
    credencial en el repositorio, y el historial de git no la suelta.
    """
    valor = _valor_declarado(ejemplo.read_text(encoding="utf-8"), "GRAPH_CLIENT_SECRET")

    assert valor in ("", "pon-aqui-el-secreto")


def _valor_declarado(texto: str, variable: str) -> str:
    """El valor que un fichero de ejemplo le da a una variable.

    Sirve para las dos formas: `CLAVE=valor` del `.env` y `"CLAVE": "valor"`
    del `local.settings.json`.
    """
    for patron in (
        rf'"{variable}"\s*:\s*"([^"]*)"',
        rf"^{variable}=(.*)$",
    ):
        encontrado = re.search(patron, texto, re.MULTILINE)
        if encontrado:
            return encontrado.group(1).strip()
    raise AssertionError(f"{variable} no está declarada en el ejemplo")


# --------------------------------------------------------------------------
# R32 · El documento del ecosistema declara lo que consumimos
# --------------------------------------------------------------------------


def test_f006_r32_integracion_declara_el_consumo_de_sharepoint():
    """R32 · qué consumimos, con qué identidad y con qué permisos.

    F-006 hace que este proyecto pase a consumir **SharePoint del tenant**, un
    recurso compartido con IT y con los proyectos que ya viven en ese sitio.
    `CLAUDE.md` obliga a que eso quede escrito en el repositorio que lo
    consume, y `docs/INTEGRACION.md` es la fuente de verdad que creó F-005: se
    le añade una sección, no se crea un documento paralelo.
    """
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert "SharePoint" in texto
    assert "Microsoft Graph" in texto
    for variable in VARIABLES_DE_F006:
        assert variable in texto, f"INTEGRACION.md no nombra {variable}"


def test_f006_r32_integracion_no_trae_ningun_identificador():
    """R32 · nombres de recurso y de variable; **jamás** un valor.

    Este documento existe para ser leído por gente de otros proyectos, así que
    es el fichero con más probabilidad de acabar llevando un GUID «para que se
    entienda mejor».
    """
    assert PATRON_GUID.findall(INTEGRACION.read_text(encoding="utf-8")) == []


def test_f006_r32_integracion_dice_que_se_rompe_si_alguien_toca_el_destino():
    """R32 · lo que de verdad necesita saber quien administre ese sitio.

    Un documento que solo diga «usamos SharePoint» no evita que alguien mueva
    la biblioteca un martes. Tiene que decir **qué se rompe**.
    """
    texto = INTEGRACION.read_text(encoding="utf-8").lower()

    assert "biblioteca" in texto
    assert "permiso" in texto
