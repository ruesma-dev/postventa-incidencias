# services/postventa-api/tests/test_f013_adaptador_graph_listado.py
"""El explorador de la biblioteca sobre Graph, sin red (F-013 T11).

`listar_carpetas` y `crear_subcarpeta` en el adaptador de Graph de F-006, con
el contrato de `ExploradorBibliotecaPort` (`domain/ports/biblioteca.py`,
`specs/F-013-archivo-posventa/design.md` §3.2 y §6.1):

- **R12** · solo carpetas, y **todas** las páginas (`@odata.nextLink`);
- `404` → `None` (la carpeta no existe), que **no** es lo mismo que una
  carpeta sin subcarpetas (VILLA 04 → tupla vacía);
- **R15** · crear es **un nivel por llamada**: padre ausente → `ArchivoFallido`
  sin crear ninguna intermedia;
- **R39** · el `409` de «ya existe» es un éxito, y queda **una**;
- **R23** · nada del `nextLink` —lleva el identificador de la biblioteca y el
  testigo de paginación— ni ningún identificador en los logs ni en los errores.

## Cómo se construye aquí el adaptador real

Con **el ayudante de `test_f006_adaptador_graph.py`**, importado: ese fichero
es uno de los dos autorizados a nombrar el adaptador
(`test_f006_arquitectura.py`, R21), y **siempre** le inyecta el cliente falso
de `tests/utiles_sharepoint.py`. Este fichero no escribe la construcción: así
el guardián de F-006 no necesita una excepción más y la garantía de «nunca con
cliente real» sigue viviendo en un solo sitio.

**Ni un dato real**: la biblioteca, el tenant y los testigos de paginación son
inventados, y ninguno tiene forma de GUID.
"""

from __future__ import annotations

import inspect
import logging

import httpx
import pytest
from domain.models.errores import ArchivoFallido
from domain.ports.archivo import ArchivoPort
from domain.ports.biblioteca import ExploradorBibliotecaPort

from infrastructure.sharepoint import fabrica as fabrica_sharepoint
from infrastructure.sharepoint import graph
from infrastructure.sharepoint.graph import GRAPH
from tests.test_f006_adaptador_graph import DRIVE, SECRETO, TENANT, adaptador
from tests.utiles_sharepoint import conflicto, creado, fallo, no_encontrado, ok

#: Lo que se pide al listar: el nombre y la faceta `folder`, 200 por página.
CONSULTA = "?$select=name,folder&$top=200"

#: La raíz de la biblioteca inventada.
RAIZ = f"{GRAPH}/drives/{DRIVE}/root"

#: Un testigo de paginación **inventado**. En Graph es opaco y va dentro del
#: `nextLink`, junto al identificador de la biblioteca: ninguno de los dos
#: puede acabar en un log.
TESTIGO = "testigo-de-paginacion-inventado-0001"

#: Rutas del árbol medido de la 0677 (T2), con el doble blanco tal cual.
OBRA = "677  MIRASIERRA"
INCIDENCIAS = f"{OBRA}/PARTES INCIDENCIAS"


def _carpeta(nombre: str, hijos: int = 0) -> dict:
    """Un `driveItem` de carpeta, como lo devuelve `$select=name,folder`."""
    return {"name": nombre, "folder": {"childCount": hijos}}


def _fichero(nombre: str) -> dict:
    """Un `driveItem` de fichero: sin faceta `folder`."""
    return {"name": nombre}


def _pagina(*elementos: dict, siguiente: str | None = None) -> dict:
    """Una página de `children`, con su `nextLink` si hay más."""
    cuerpo: dict = {"value": list(elementos)}
    if siguiente is not None:
        cuerpo["@odata.nextLink"] = siguiente
    return cuerpo


def _siguiente(n: int) -> str:
    """El `nextLink` de la página `n`: lleva la biblioteca y el testigo."""
    return f"{RAIZ}/children?$select=name,folder&$top=200&$skiptoken={TESTIGO}-{n}"


@pytest.fixture
def registros():
    """Todo lo que se registre en cualquier logger, en texto, a nivel DEBUG."""
    lineas: list[str] = []
    manejador = logging.Handler(level=logging.DEBUG)
    manejador.emit = lambda registro: lineas.append(  # type: ignore[method-assign]
        f"{registro.name} {registro.getMessage()}"
    )
    raiz = logging.getLogger()
    nivel = raiz.level
    raiz.addHandler(manejador)
    raiz.setLevel(logging.DEBUG)
    try:
        yield lineas
    finally:
        raiz.setLevel(nivel)
        raiz.removeHandler(manejador)


# --------------------------------------------------------------------------
# El adaptador es los dos puertos a la vez (design.md §3.2)
# --------------------------------------------------------------------------


def test_f013_t11_el_adaptador_de_graph_es_archivador_y_explorador_a_la_vez():
    """La **misma** instancia cumple los dos puertos: el paso crea carpetas con
    el mismo `archivador` (decisión 1 del cierre del bloque 2), y si no fuera
    `ExploradorBibliotecaPort` levantaría `TypeError` antes de nada."""
    adap, _ = adaptador()

    assert isinstance(adap, ArchivoPort)
    assert isinstance(adap, ExploradorBibliotecaPort)


def test_f013_t11_la_fabrica_construye_esa_misma_clase():
    """Lo que devuelve `construir_archivador` es de la clase que cumple los dos
    puertos: la fábrica no envuelve ni sustituye el adaptador."""
    clase = fabrica_sharepoint.AdaptadorSharePointGraph

    assert clase is graph.AdaptadorSharePointGraph
    assert issubclass(clase, ExploradorBibliotecaPort)
    assert issubclass(clase, ArchivoPort)


@pytest.mark.parametrize("metodo", ("listar_carpetas", "crear_subcarpeta"))
def test_f013_t11_las_firmas_son_las_del_puerto(metodo):
    """Mismos parámetros, **solo por palabra clave**, que el puerto."""
    del_puerto = inspect.signature(getattr(ExploradorBibliotecaPort, metodo))
    del_adaptador = inspect.signature(getattr(graph.AdaptadorSharePointGraph, metodo))

    assert list(del_adaptador.parameters) == list(del_puerto.parameters)
    for nombre, parametro in del_adaptador.parameters.items():
        if nombre != "self":
            assert parametro.kind is inspect.Parameter.KEYWORD_ONLY


# --------------------------------------------------------------------------
# R12 · listar: solo carpetas, todas las páginas
# --------------------------------------------------------------------------


def test_f013_r12_listar_la_raiz_pide_sus_hijos_con_nombre_y_faceta_de_carpeta():
    adap, cliente = adaptador(ok(_pagina(_carpeta(OBRA))))

    adap.listar_carpetas(carpeta="")

    assert cliente.llamadas == [("GET", f"{RAIZ}/children{CONSULTA}")]


def test_f013_r12_listar_una_carpeta_pide_los_hijos_de_su_ruta_codificada():
    """El doble blanco de `677  MIRASIERRA` viaja codificado y las barras no."""
    adap, cliente = adaptador(ok(_pagina()))

    adap.listar_carpetas(carpeta=INCIDENCIAS)

    assert cliente.llamadas == [
        (
            "GET",
            f"{RAIZ}:/677%20%20MIRASIERRA/PARTES%20INCIDENCIAS:/children{CONSULTA}",
        )
    ]


def test_f013_r12_solo_devuelve_carpetas_y_con_su_nombre_tal_cual():
    """Los ficheros se descartan en cliente: el `$filter` por `folder` no es
    fiable en SharePoint (`design.md` §6.1). El nombre, sin tocar (R4)."""
    adap, _ = adaptador(
        ok(
            _pagina(
                _fichero("0677 - RS26.08 - 0001 PARTE FIRMADO.pdf"),
                _carpeta(OBRA, hijos=3),
                _fichero("LEEME.txt"),
                _carpeta("OTRA OBRA"),
                {"name": "un cuaderno", "package": {"type": "oneNote"}},
            )
        )
    )

    assert adap.listar_carpetas(carpeta="") == (OBRA, "OTRA OBRA")


def test_f013_r12_una_carpeta_con_solo_ficheros_es_una_tupla_vacia_y_no_none():
    """VILLA 04: existe, tiene 142 partes sueltos y **ninguna** subcarpeta."""
    adap, _ = adaptador(ok(_pagina(_fichero("uno.pdf"), _fichero("dos.pdf"))))

    listado = adap.listar_carpetas(carpeta=f"{INCIDENCIAS}/VILLA 04")

    assert listado == ()
    assert listado is not None


def test_f013_r12_sigue_el_next_link_hasta_agotarlo():
    """R12 · una biblioteca con cientos de obras no puede resolver mal porque
    la buscada estuviera en la tercera página."""
    adap, cliente = adaptador(
        ok(_pagina(_carpeta("A"), siguiente=_siguiente(2))),
        ok(_pagina(_fichero("x.pdf"), _carpeta("B"), siguiente=_siguiente(3))),
        ok(_pagina(_carpeta(OBRA))),
    )

    listado = adap.listar_carpetas(carpeta="")

    assert listado == ("A", "B", OBRA)
    assert cliente.llamadas == [
        ("GET", f"{RAIZ}/children{CONSULTA}"),
        ("GET", _siguiente(2)),
        ("GET", _siguiente(3)),
    ]


def test_f013_r12_el_next_link_se_pide_tal_cual_con_el_token_en_la_cabecera():
    """El `nextLink` lleva su propia consulta: no se le añade nada, y el token
    viaja en la cabecera como en todas las llamadas (F-006 R26)."""
    adap, cliente = adaptador(
        ok(_pagina(siguiente=_siguiente(2))), ok(_pagina(_carpeta("B")))
    )

    adap.listar_carpetas(carpeta="")

    assert cliente.urls[1] == _siguiente(2)
    assert cliente.cabeceras[1] == {"Authorization": f"Bearer {cliente.token}"}


def test_f013_r12_un_next_link_fuera_de_graph_no_se_sigue():
    """El token solo viaja a Graph. Un `nextLink` a otro sitio —un proxy que
    reescribe, un cuerpo manipulado— sería mandarle el token a un tercero: se
    para con `ArchivoFallido` sin pedirlo, y sin decir adónde apuntaba."""
    ajeno = f"https://graph.microsoft.com.ejemplo.invalido/v1.0/{TESTIGO}"
    adap, cliente = adaptador(ok(_pagina(_carpeta("A"), siguiente=ajeno)))

    with pytest.raises(ArchivoFallido) as caido:
        adap.listar_carpetas(carpeta="")

    assert len(cliente.llamadas) == 1
    assert ajeno not in caido.value.motivo
    assert TESTIGO not in caido.value.motivo


def test_f013_r12_un_next_link_que_no_es_texto_no_se_sigue():
    adap, cliente = adaptador(ok(_pagina(_carpeta("A"), siguiente=12345)))

    with pytest.raises(ArchivoFallido):
        adap.listar_carpetas(carpeta="")

    assert len(cliente.llamadas) == 1


@pytest.mark.parametrize(
    "cuerpo",
    (
        {},
        {"value": None},
        {"value": {"name": OBRA, "folder": {}}},
        {"value": "677  MIRASIERRA"},
    ),
    ids=("sin_value", "value_nulo", "value_objeto", "value_texto"),
)
def test_f013_r12_una_pagina_sin_lista_de_elementos_es_archivo_fallido(cuerpo):
    """Una respuesta que no trae lo que el contrato promete no es «ninguna
    carpeta»: tomarla por vacía sería crear una obra que ya existe."""
    adap, _ = adaptador(ok(cuerpo))

    with pytest.raises(ArchivoFallido):
        adap.listar_carpetas(carpeta="")


def test_f013_r12_elementos_sin_nombre_de_texto_no_se_inventan():
    """Un elemento raro no tumba el listado ni aparece como carpeta `None`."""
    adap, _ = adaptador(
        ok(
            _pagina(
                "no soy un objeto",
                {"folder": {}},
                {"name": 7, "folder": {}},
                _carpeta(OBRA),
            )
        )
    )

    assert adap.listar_carpetas(carpeta="") == (OBRA,)


# --------------------------------------------------------------------------
# 404 → None; y los errores, como en F-006
# --------------------------------------------------------------------------


def test_f013_r12_una_carpeta_que_no_existe_devuelve_none():
    adap, cliente = adaptador(no_encontrado())

    assert adap.listar_carpetas(carpeta="no existe") is None
    assert len(cliente.llamadas) == 1


def test_f013_r12_un_404_en_una_pagina_siguiente_no_es_none_ni_un_listado_a_medias():
    """La carpeta desapareció mientras se paginaba: ni «no existe» (se crearía
    a ciegas) ni las carpetas de la primera página (faltaría la buscada)."""
    adap, _ = adaptador(
        ok(_pagina(_carpeta("A"), siguiente=_siguiente(2))), no_encontrado()
    )

    with pytest.raises(ArchivoFallido) as caido:
        adap.listar_carpetas(carpeta="")

    assert "404" in caido.value.motivo


@pytest.mark.parametrize("codigo", (408, 429, 500, 502, 503, 504))
def test_f013_r12_un_transitorio_al_listar_se_reintenta(codigo):
    adap, cliente = adaptador(fallo(codigo), ok(_pagina(_carpeta(OBRA))))

    assert adap.listar_carpetas(carpeta="") == (OBRA,)
    assert len(cliente.llamadas) == 2


def test_f013_r12_un_transitorio_en_una_pagina_siguiente_repite_esa_pagina():
    adap, cliente = adaptador(
        ok(_pagina(_carpeta("A"), siguiente=_siguiente(2))),
        httpx.ReadTimeout("se agotó el tiempo"),
        ok(_pagina(_carpeta("B"))),
    )

    assert adap.listar_carpetas(carpeta="") == ("A", "B")
    assert cliente.urls[1:] == [_siguiente(2), _siguiente(2)]


@pytest.mark.parametrize("codigo", (400, 401, 403))
def test_f013_r12_un_definitivo_al_listar_es_archivo_fallido_sin_reintento(codigo):
    adap, cliente = adaptador(fallo(codigo))

    with pytest.raises(ArchivoFallido) as caido:
        adap.listar_carpetas(carpeta="")

    assert str(codigo) in caido.value.motivo
    assert len(cliente.llamadas) == 1


# --------------------------------------------------------------------------
# R15, R39 · crear: un nivel, dentro de un padre que existe
# --------------------------------------------------------------------------


def test_f013_r15_crear_en_la_raiz_es_un_post_a_sus_hijos():
    adap, cliente = adaptador(creado(_carpeta("0678 OTRA OBRA")))

    adap.crear_subcarpeta(padre="", nombre="0678 OTRA OBRA")

    assert cliente.llamadas == [("POST", f"{RAIZ}/children")]
    assert cliente.cuerpos[-1] == {
        "name": "0678 OTRA OBRA",
        "folder": {},
        "@microsoft.graph.conflictBehavior": "fail",
    }


def test_f013_r15_crear_una_unidad_es_un_solo_post_en_su_padre_y_nada_mas():
    """Ni un `GET` previo ni una creación por tramo: **un** nivel por llamada."""
    adap, cliente = adaptador(creado(_carpeta("VILLA 08")))

    adap.crear_subcarpeta(padre=INCIDENCIAS, nombre="VILLA 08")

    assert cliente.llamadas == [
        ("POST", f"{RAIZ}:/677%20%20MIRASIERRA/PARTES%20INCIDENCIAS:/children")
    ]
    assert cliente.cuerpos[-1]["name"] == "VILLA 08"


def test_f013_r15_con_el_padre_ausente_es_archivo_fallido_sin_crear_intermedias():
    """Graph responde `404` al `POST` en un padre que no existe, y eso es un
    fallo —el resolutor listó otra cosa—, no una invitación a crear la ruta."""
    adap, cliente = adaptador(no_encontrado())

    with pytest.raises(ArchivoFallido) as caido:
        adap.crear_subcarpeta(padre=f"{INCIDENCIAS}/VILLA 08", nombre="PARTES FIRMADOS")

    assert "404" in caido.value.motivo
    assert cliente.metodos == ["POST"]
    assert len(cliente.llamadas) == 1


def test_f013_r39_si_ya_existe_es_un_exito_y_no_se_crea_otra():
    """Dos partes de la misma unidad nueva a la vez: el segundo recibe `409` y
    eso es lo que quería. `fail`, nunca `rename`: `VILLA 08 1` no."""
    adap, cliente = adaptador(conflicto())

    adap.crear_subcarpeta(padre=INCIDENCIAS, nombre="VILLA 08")  # no levanta

    assert len(cliente.llamadas) == 1
    assert cliente.cuerpos[-1]["@microsoft.graph.conflictBehavior"] == "fail"


def test_f013_r15_un_transitorio_al_crear_se_reintenta_y_el_409_del_segundo_vale():
    """El primer `POST` pudo llegar y crearla: el reintento recibe `409`, que es
    éxito. Así un corte de red no deja un error donde hay una carpeta."""
    adap, cliente = adaptador(fallo(503), conflicto())

    adap.crear_subcarpeta(padre=INCIDENCIAS, nombre="VILLA 08")

    assert cliente.metodos == ["POST", "POST"]


@pytest.mark.parametrize("codigo", (400, 403))
def test_f013_r15_un_definitivo_al_crear_es_archivo_fallido(codigo):
    adap, cliente = adaptador(fallo(codigo))

    with pytest.raises(ArchivoFallido) as caido:
        adap.crear_subcarpeta(padre=INCIDENCIAS, nombre="VILLA 08")

    assert str(codigo) in caido.value.motivo
    assert len(cliente.llamadas) == 1


# --------------------------------------------------------------------------
# R23 · ni el nextLink ni ningún identificador, en logs ni errores
# --------------------------------------------------------------------------


def test_f013_r23_nada_del_next_link_ni_de_la_biblioteca_en_los_logs(registros):
    adap, cliente = adaptador(
        ok(_pagina(_carpeta("A"), siguiente=_siguiente(2))),
        fallo(503),
        ok(_pagina(_carpeta("B"))),
        creado(_carpeta("VILLA 08")),
    )

    adap.listar_carpetas(carpeta=INCIDENCIAS)
    adap.crear_subcarpeta(padre=INCIDENCIAS, nombre="VILLA 08")

    texto = "\n".join(registros)
    assert registros, "se esperaba al menos una línea que revisar"
    assert TESTIGO not in texto
    assert "skiptoken" not in texto
    assert "nextLink" not in texto
    assert DRIVE not in texto
    assert TENANT not in texto
    assert SECRETO not in texto
    assert cliente.token not in texto
    assert GRAPH not in texto


def test_f013_r23_el_error_de_una_pagina_siguiente_no_lleva_el_next_link():
    adap, _ = adaptador(
        ok(_pagina(_carpeta("A"), siguiente=_siguiente(2))), fallo(403)
    )

    with pytest.raises(ArchivoFallido) as caido:
        adap.listar_carpetas(carpeta="")

    motivo = caido.value.motivo
    assert TESTIGO not in motivo
    assert DRIVE not in motivo
    assert GRAPH not in motivo
    assert "403" in motivo


def test_f013_r23_el_log_del_listado_dice_la_carpeta_y_cuantas_hay(registros):
    """Lo que sí se registra (R23: los nombres de carpeta son de negocio): la
    carpeta, cuántas subcarpetas y cuántas páginas. La raíz se nombra."""
    adap, _ = adaptador(
        ok(_pagina(_carpeta("A"), siguiente=_siguiente(2))),
        ok(_pagina(_carpeta("B"), _fichero("x.pdf"))),
        ok(_pagina(_carpeta("VILLA 01"))),
    )

    adap.listar_carpetas(carpeta="")
    adap.listar_carpetas(carpeta=INCIDENCIAS)

    del_adaptador = [linea for linea in registros if linea.startswith(graph.__name__)]
    assert any(
        "carpeta=(raíz)" in linea and "carpetas=2" in linea and "paginas=2" in linea
        for linea in del_adaptador
    )
    assert any(
        f"carpeta={INCIDENCIAS}" in linea
        and "carpetas=1" in linea
        and "paginas=1" in linea
        for linea in del_adaptador
    )
