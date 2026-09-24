# services/postventa-api/tests/test_f013_arquitectura.py
"""Invariantes de F-013 que ningún test de comportamiento vigila (T16).

`design.md` §11 y su enmienda del 2026-09-24. Son cosas que se degradan solas
en cuanto alguien tiene prisa, y que si se degradan **no se nota** hasta que
un parte con DNI aterriza en la carpeta de otra vivienda:

- **El dominio del destino es puro.** `destino_posventa.py` y los dos puertos
  nuevos no conocen ningún cliente HTTP ni la infraestructura, y el resolutor
  (`destino_archivo.py`) tampoco: ni HTTP, ni logs. Que el resolutor no
  registre nada es lo que garantiza que el `con.res` de la unidad no sale por
  ahí (R23; decisión 9 del bloque 2 en `progress/impl_F-013.md`).
- **`nombrado.py` y `ArchivoPort` no cambian** (`design.md` §2.3): el nombre
  del fichero es el de F-006 (R5) y el puerto de archivo conserva sus tres
  operaciones. La mitad del diff se salta fuera de la rama, como en
  `test_f013_por_obra_intacto.py`.
- **Los nombres vigilados de F-031, F-033 y F-034** no entran en
  `destino_archivo.py` ni en `destino_posventa.py` (§2.3): el resolutor
  recibe dos cadenas, nunca el contexto, y compara con `normalizar_codigo`.
- **El explorador tiene exactamente dos métodos** (R48): ni listar ficheros,
  ni mover, ni renombrar, ni borrar. Es lo que garantiza que los 142 partes
  sueltos de VILLA 04 no se tocan.
- **`obra_ref` no sale en ningún log ni en ningún error** del servicio
  (`design.md` §3.3, R23, R44): es una referencia del ERP y se trata como los
  identificadores de SharePoint.

Todo se mira con `ast`, no buscando texto: una línea de un docstring que
explique por qué **no** se usa `ctx.extraccion` no es usarlo, y un
`log.info(fila.obra_ref)` partido en tres líneas sigue siendo una fuga.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from domain.ports.archivo import ArchivoPort
from domain.ports.biblioteca import ExploradorBibliotecaPort

from tests.test_f006_arquitectura import (
    PROHIBIDOS_ARRIBA_DEL_PUERTO,
    _modulos_importados,
)
from tests.test_f013_por_obra_intacto import (
    SERVICIO as PREFIJO_DEL_SERVICIO,
)
from tests.test_f013_por_obra_intacto import (
    _base_de_la_rama_o_saltar,
    _cambiados,
)

#: Raíz del servicio (este fichero vive en `<servicio>/tests/`).
SERVICIO = Path(__file__).resolve().parent.parent

DESTINO_POSVENTA = SERVICIO / "domain" / "models" / "destino_posventa.py"
PUERTO_BIBLIOTECA = SERVICIO / "domain" / "ports" / "biblioteca.py"
PUERTO_UBICACION = SERVICIO / "domain" / "ports" / "ubicacion.py"
RESOLUTOR = SERVICIO / "application" / "pipelines" / "destino_archivo.py"
NOMBRADO = SERVICIO / "domain" / "models" / "nombrado.py"
PUERTO_ARCHIVO = SERVICIO / "domain" / "ports" / "archivo.py"

#: Lo nuevo de F-013 que vive por encima de la infraestructura.
LO_NUEVO_ARRIBA_DEL_PUERTO = (DESTINO_POSVENTA, PUERTO_BIBLIOTECA, PUERTO_UBICACION, RESOLUTOR)

#: Además de lo que ya prohíbe F-006 (`httpx`, `msal`, `requests` e
#: `infrastructure`), lo que haría de estos módulos algo con E/S o con
#: conocimiento del borde.
PROHIBIDOS_EN_LO_NUEVO = (
    *PROHIBIDOS_ARRIBA_DEL_PUERTO,
    "interface_adapters",
    "function_app",
    "config",
    "socket",
    "http",
    "urllib",
    "subprocess",
    "os",
    "pathlib",
    "psycopg",
    "logging",
    "structlog",
)

#: Lo único que puede importar cada módulo, dicho en positivo. Una lista de
#: permitidos no se queda vieja el día que alguien añade un cliente nuevo: lo
#: nuevo, sea lo que sea, no está en ella.
PERMITIDOS = {
    DESTINO_POSVENTA: {"__future__", "re", "unicodedata", "collections", "dataclasses", "enum", "typing", "domain"},
    PUERTO_BIBLIOTECA: {"__future__", "typing"},
    PUERTO_UBICACION: {"__future__", "typing", "domain"},
    RESOLUTOR: {"__future__", "collections", "dataclasses", "typing", "domain"},
}

#: Llamadas que son E/S o ejecución arbitraria, aunque no necesiten import.
LLAMADAS_CON_EFECTO = ("open", "print", "input", "eval", "exec", "compile", "__import__")

#: `design.md` §2.3 y §11 enmendado: lo que ni el resolutor ni el dominio del
#: destino pueden nombrar. Los siete primeros viven en las tablas
#: `NOMBRES_NUEVOS_Y_DONDE_VIVEN` de F-031, F-033 y F-034; los tres últimos son
#: la puerta de atrás al contexto del paso (`ctx`, `ctx.extraccion`,
#: `ctx.situacion`) que la firma sin contexto cerró.
NOMBRES_VIGILADOS = (
    "codigos_guardados",
    "CodigosDelParte",
    "codigos_declarados",
    "exigir_codigos_declarados",
    "es_el_mismo_codigo",
    "drive_id_vigente",
    "_en_otro_destino",
    "ContextoParte",
    "extraccion",
    "ctx",
)

#: Los dos métodos del explorador, y ninguno más (R48).
METODOS_DEL_EXPLORADOR = {"listar_carpetas", "crear_subcarpeta"}

#: Las tres operaciones de `ArchivoPort` desde F-006.
METODOS_DE_ARCHIVO_PORT = {"asegurar_carpeta", "buscar", "subir"}

#: Lo que no puede salir: la referencia opaca de la obra y su columna del ERP.
REFERENCIAS_DE_OBRA = ("obra_ref", "obride")

#: Los métodos de un logger de la biblioteca estándar.
METODOS_DE_LOG = ("debug", "info", "warning", "warn", "error", "exception", "critical", "log")

#: Los nombres con los que el servicio llama a su logger (`log = logging.getLogger(...)`).
NOMBRES_DE_LOGGER = ("log", "logger", "logging", "_log")

#: Constructores de error que acaban en un mensaje, una respuesta o una traza.
ERRORES_CON_MENSAJE = ("DestinoNoResuelto", "UbicacionNoDisponible", "ArchivoFallido")

_IGNORADAS = (".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "tests", "tests_bbdd")


# --------------------------------------------------------------------------
# Utilidades: identificadores, llamadas de log y fugas, con `ast`
# --------------------------------------------------------------------------


def _arbol(fichero: Path) -> ast.Module:
    return ast.parse(fichero.read_text(encoding="utf-8"))


def _identificadores(nodo: ast.AST) -> set[str]:
    """Todos los nombres que un fragmento de código **usa o declara**.

    Nombres, atributos, parámetros, argumentos por palabra clave, funciones,
    clases e imports (con sus alias y cada tramo del módulo). No los textos:
    un docstring que explica por qué no se usa algo no es usarlo.
    """
    nombres: set[str] = set()
    for hijo in ast.walk(nodo):
        if isinstance(hijo, ast.Name):
            nombres.add(hijo.id)
        elif isinstance(hijo, ast.Attribute):
            nombres.add(hijo.attr)
        elif isinstance(hijo, ast.arg) or isinstance(hijo, ast.keyword) and hijo.arg:
            nombres.add(hijo.arg)
        elif isinstance(hijo, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            nombres.add(hijo.name)
        elif isinstance(hijo, ast.alias):
            nombres.update(hijo.name.split("."))
            if hijo.asname:
                nombres.add(hijo.asname)
        elif isinstance(hijo, ast.ImportFrom) and hijo.module:
            nombres.update(hijo.module.split("."))
    return nombres


def _es_llamada_de_log(llamada: ast.Call) -> bool:
    funcion = llamada.func
    if not isinstance(funcion, ast.Attribute) or funcion.attr not in METODOS_DE_LOG:
        return False
    objeto = funcion.value
    if isinstance(objeto, ast.Name):
        return objeto.id in NOMBRES_DE_LOGGER
    # `logging.getLogger(__name__).info(...)`
    return (
        isinstance(objeto, ast.Call)
        and isinstance(objeto.func, ast.Attribute)
        and objeto.func.attr == "getLogger"
    )


def _es_error_con_mensaje(llamada: ast.Call) -> bool:
    funcion = llamada.func
    nombre = funcion.id if isinstance(funcion, ast.Name) else getattr(funcion, "attr", None)
    return nombre in ERRORES_CON_MENSAJE


def _fugas_de_obra_ref(fuente: str) -> list[int]:
    """Líneas donde la referencia de obra acaba en un log, un error o un `raise`."""
    fugas: list[int] = []
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Call) and (_es_llamada_de_log(nodo) or _es_error_con_mensaje(nodo)):
            vigilado = nodo
        elif isinstance(nodo, ast.Raise) and nodo.exc is not None:
            vigilado = nodo.exc
        else:
            continue
        if _identificadores(vigilado) & set(REFERENCIAS_DE_OBRA):
            fugas.append(nodo.lineno)
    return fugas


def _modulos_de_produccion() -> list[Path]:
    return sorted(
        fichero
        for fichero in SERVICIO.rglob("*.py")
        if not any(parte in _IGNORADAS for parte in fichero.relative_to(SERVICIO).parts)
    )


def _metodos_de_la_clase(fichero: Path, clase: str) -> set[str]:
    (definicion,) = [
        nodo for nodo in _arbol(fichero).body if isinstance(nodo, ast.ClassDef) and nodo.name == clase
    ]
    return {nodo.name for nodo in definicion.body if isinstance(nodo, ast.FunctionDef)}


# --------------------------------------------------------------------------
# El dominio del destino es puro, y el resolutor no registra nada
# --------------------------------------------------------------------------


def test_f013_t16_los_ficheros_vigilados_existen():
    """Un control sobre ficheros que no existen está verde por no mirar."""
    for fichero in (*LO_NUEVO_ARRIBA_DEL_PUERTO, NOMBRADO, PUERTO_ARCHIVO):
        assert fichero.is_file(), fichero


@pytest.mark.parametrize("fichero", LO_NUEVO_ARRIBA_DEL_PUERTO, ids=lambda ruta: ruta.name)
def test_f013_t16_lo_nuevo_no_conoce_ni_http_ni_la_infraestructura(fichero):
    """`design.md` §11 · el dominio sin `httpx`, y el resolutor tampoco.

    F-006 ya lo vigila para `domain/` y `application/` en general
    (`test_f006_arquitectura.py`, R22); aquí se amplía a lo que haría de estos
    módulos algo con E/S —sockets, ficheros, procesos, la base— o con
    conocimiento del borde y de la configuración.
    """
    assert _modulos_importados(fichero) & set(PROHIBIDOS_EN_LO_NUEVO) == set()


@pytest.mark.parametrize("fichero", LO_NUEVO_ARRIBA_DEL_PUERTO, ids=lambda ruta: ruta.name)
def test_f013_t16_lo_nuevo_solo_importa_lo_permitido(fichero):
    """Dicho en positivo: biblioteca estándar sin E/S y `domain`, nada más."""
    assert _modulos_importados(fichero) <= PERMITIDOS[fichero]


@pytest.mark.parametrize("fichero", LO_NUEVO_ARRIBA_DEL_PUERTO, ids=lambda ruta: ruta.name)
def test_f013_t16_lo_nuevo_no_hace_e_s_sin_importar_nada(fichero):
    """`open`, `print` o `eval` no necesitan import y son E/S igual."""
    llamadas = {
        nodo.func.id
        for nodo in ast.walk(_arbol(fichero))
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
    }

    assert llamadas & set(LLAMADAS_CON_EFECTO) == set()


def test_f013_r23_el_resolutor_no_registra_nada():
    """Ni un log en el resolutor: lo que haya que contar lo cuenta el paso.

    Es la garantía de que el `con.res` de la unidad —texto libre de la ficha
    del ERP— no puede salir de aquí hacia un log (R23).
    """
    llamadas_de_log = [
        nodo.lineno
        for nodo in ast.walk(_arbol(RESOLUTOR))
        if isinstance(nodo, ast.Call) and _es_llamada_de_log(nodo)
    ]

    assert llamadas_de_log == []
    assert "logging" not in _modulos_importados(RESOLUTOR)


# --------------------------------------------------------------------------
# `nombrado.py` y `ArchivoPort` no cambian
# --------------------------------------------------------------------------


def test_f013_r5_archivo_port_conserva_sus_tres_operaciones():
    """`design.md` §2.3 · el puerto de archivo no gana métodos.

    Lo vigila también `test_f032_alcance_cerrado.py` contra el borrado y el
    renombrado; aquí se fija el conjunto **exacto**, porque el riesgo de F-013
    es otro: meter `listar_carpetas` aquí «ya que el adaptador lo tiene».
    """
    assert _metodos_de_la_clase(PUERTO_ARCHIVO, "ArchivoPort") == METODOS_DE_ARCHIVO_PORT
    assert not (METODOS_DEL_EXPLORADOR & {nombre for nombre in dir(ArchivoPort) if not nombre.startswith("_")})


def test_f013_r5_nombrado_no_sabe_de_estrategias():
    """El dominio del nombre no conoce la estrategia de destino (§2.3).

    La base vacía se rechaza en la fábrica, no en `nombrado.py`: si este
    módulo importara `destino_posventa` o nombrara la estrategia, el nombre
    del fichero empezaría a depender de a dónde va.
    """
    identificadores = _identificadores(_arbol(NOMBRADO))

    assert "destino_posventa" not in identificadores
    assert "EstructuraArchivo" not in identificadores
    assert "sharepoint_estructura" not in identificadores


@pytest.mark.parametrize("fichero", (NOMBRADO, PUERTO_ARCHIVO), ids=lambda ruta: ruta.name)
def test_f013_t16_nombrado_y_archivo_port_no_se_tocan_en_la_rama(fichero):
    """La mitad del diff: ni una línea de estos dos ficheros en la rama.

    Fuera de `feature/F-013-archivo-posventa`, o ya mergeada, se salta: un
    control del diff sin diff que mirar no puede ponerse rojo.
    """
    cambiados = _cambiados(_base_de_la_rama_o_saltar())
    ruta = PREFIJO_DEL_SERVICIO + fichero.relative_to(SERVICIO).as_posix()

    assert ruta not in cambiados


# --------------------------------------------------------------------------
# Los nombres vigilados de F-031, F-033 y F-034
# --------------------------------------------------------------------------


@pytest.mark.parametrize("fichero", (RESOLUTOR, DESTINO_POSVENTA), ids=lambda ruta: ruta.name)
@pytest.mark.parametrize("nombre", NOMBRES_VIGILADOS)
def test_f013_t16_el_destino_no_nombra_lo_vigilado(fichero, nombre):
    """`design.md` §2.3 · los códigos llegan como dos cadenas, ya guardados.

    Si el resolutor nombrara `codigos_guardados` o `drive_id_vigente`, las
    tablas de F-031, F-033 y F-034 se pondrían rojas; si recibiera `ctx`,
    tendría `ctx.extraccion` a mano, que es justo lo que F-031 cerró.
    """
    assert nombre not in _identificadores(_arbol(fichero))


# --------------------------------------------------------------------------
# R48 · el explorador, dos métodos y ninguno más
# --------------------------------------------------------------------------


def test_f013_r48_el_explorador_tiene_exactamente_dos_metodos():
    """Ni listar ficheros, ni mover, ni renombrar, ni borrar (§3.2)."""
    assert _metodos_de_la_clase(PUERTO_BIBLIOTECA, "ExploradorBibliotecaPort") == METODOS_DEL_EXPLORADOR
    assert {
        nombre for nombre in vars(ExploradorBibliotecaPort) if not nombre.startswith("_")
    } == METODOS_DEL_EXPLORADOR


# --------------------------------------------------------------------------
# R23 · `obra_ref` fuera de logs y errores
# --------------------------------------------------------------------------


def test_f013_r23_el_barrido_de_obra_ref_mira_modulos_de_verdad():
    """El control de los controles: el barrido no puede salir vacío."""
    rutas = {fichero.relative_to(SERVICIO).as_posix() for fichero in _modulos_de_produccion()}

    assert "infrastructure/sigrid/ubicacion.py" in rutas
    assert "infrastructure/sigrid/consultas_ubicacion.py" in rutas
    assert "application/pipelines/destino_archivo.py" in rutas
    assert "function_app.py" in rutas
    assert not any(ruta.startswith("tests/") for ruta in rutas)


@pytest.mark.parametrize(
    "fichero",
    _modulos_de_produccion(),
    ids=lambda ruta: ruta.relative_to(SERVICIO).as_posix(),
)
def test_f013_r23_obra_ref_no_sale_en_ningun_log_ni_error(fichero):
    """§3.3, R23, R44 · la referencia de obra sirve para contar y para nada más.

    Ni en una llamada de log, ni en `DestinoNoResuelto` (que acaba en el 409 y
    en la traza), ni en `UbicacionNoDisponible` (el 503), ni en ningún `raise`.
    """
    assert _fugas_de_obra_ref(fichero.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(
    "fuente",
    (
        'log.info("unidades de %s", fila.obra_ref)',
        'log.warning(\n    "obra %s",\n    obride,\n)',
        'logging.getLogger(__name__).debug(f"{obra_ref}")',
        'raise DestinoNoResuelto("obra_numero_no_unico", f"obras: {obra_ref}")',
        'raise ValueError(f"sin obra: {fila.obra_ref}")',
        'error = UbicacionNoDisponible(motivo=str(obride))',
    ),
)
def test_f013_r23_el_barrido_de_obra_ref_caza_una_fuga_inyectada(fuente):
    """Controles negativos: un barrido que nunca se ha visto saltar no protege."""
    assert _fugas_de_obra_ref(fuente) != []


@pytest.mark.parametrize(
    "fuente",
    (
        "obras = frozenset(fila.obra_ref for fila in filas)",
        'if obra_ref is None:\n    raise ValueError("una unidad sin referencia de obra")',
        'log.info("unidades leídas: filas=%s", len(filas))',
        "UnidadDeObra(obra_ref=obra_ref, obra_codigo=None, unidad_codigo=None, unidad_nombre=None)",
    ),
)
def test_f013_r23_el_barrido_de_obra_ref_no_muerde_lo_legitimo(fuente):
    """Usar la referencia para contar obras es su razón de ser: eso no es fuga."""
    assert _fugas_de_obra_ref(fuente) == []


def test_f013_t16_el_barrido_de_nombres_caza_uno_inyectado():
    """El detector de nombres ve un parámetro, un atributo y un import."""
    fuente = (
        "from application.pipelines.codigos_del_parte import codigos_guardados\n"
        "def resolver(ctx):\n"
        "    return ctx.extraccion\n"
    )

    assert {"codigos_guardados", "ctx", "extraccion"} <= _identificadores(ast.parse(fuente))
    assert "extraccion" not in _identificadores(ast.parse('"""ctx.extraccion no se usa"""'))
