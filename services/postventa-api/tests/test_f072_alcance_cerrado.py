# services/postventa-api/tests/test_f072_alcance_cerrado.py
"""Lo que F-072 promete **no** tocar, comprobado (T21; R31, R32, `design.md` §3.3).

F-072 lleva el tipo de reclamación de `dbo.auxtrcp` de la plantilla al volcado.
Roza la plantilla y la importación de F-036/F-071, la revisión de F-056, el
volcado de F-059 y el DDL. Cada frontera tiene aquí su control:

| Frontera | Requisito | Qué se comprueba |
|---|---|---|
| Sigrid | **R31** | las piezas de F-072 no nombran una escritura de la pasarela ni una ventana, ni importan un adaptador de escritura; la lectura nueva hereda la de `sql/read` del catálogo; de la fábrica, la función nueva tampoco |
| Los tests | **R31** | ningún test de F-072 importa un driver de base, la IA o un cliente de red real; la guardia `sin_red` de `conftest.py` sigue puesta para toda la sesión |
| Las consultas que ya existían | **R32** | iguales carácter a carácter: huella fija de cada constante `SQL_*` y, en la rama, el fichero entero contra la base; en `infrastructure/sigrid/` solo se añaden los dos módulos de F-072 y la fábrica solo gana |
| El DDL | **R32** | `13_`, `15_` y `16_*.sql` con su huella de la base; en la rama, el único `.sql` es `17_tipo_reclamacion.sql`, nuevo; `ddl.py` sin cambios |
| Los ficheros de «No se toca» | **R32**, §3.3 | sin cambios: el front, el volcado de la aplicación y la guarda, `excel_openpyxl.py` y la lectura aislada, las equivalencias, F-065 y `function_app.py` salvo docstrings |

## Las dos mitades

Con el patrón de `test_f071_alcance_cerrado.py`: **el del diff**, contra la
**base fija** de la feature (`6994cb0`, `design.md` cabecera; no
`git merge-base`, que se movería si `dev` avanzara) y hasta el **árbol de
trabajo**, con las tres guardas de F-030 para no dejar `dev` en rojo cuando la
rama se mergee; y **el que no depende de `git`**, que se comprueba siempre.

`tests_bbdd/tests/test_f072_bbdd_tipo.py` (R17) no entra en el control de los
tests: es la suite MANUAL contra la base efímera y local, fuera de la suite
normal.

**Sin red, sin base de datos, sin IA y sin reloj.** Los controles del diff
llaman a `git`, que es un proceso local de solo lectura.
"""

from __future__ import annotations

import ast
import hashlib
import importlib
import re
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]
RAIZ_DEL_SERVICIO = RAIZ / "services" / "postventa-api"
TESTS = RAIZ_DEL_SERVICIO / "tests"

#: La rama en la que los controles del diff tienen algo que mirar.
RAMA_DE_LA_FEATURE = "feature/F-072-tipo-reclamacion-sigrid"

#: La base fija de la feature (`design.md`, cabecera; `requirements.md`).
BASE_FIJA = "6994cb0"

SERVICIO = "services/postventa-api/"

#: Las piezas de código que F-072 crea o cambia (`design.md` §3.1 y §3.2), sin
#: `domain/models/volcado.py` —es el volcado de F-059, que nombra su propia
#: escritura; F-072 solo cambia el `tipo` del parte— ni `fabrica.py`, que
#: construye también las escrituras: de ella se mira solo la función nueva.
PIEZAS_DE_F072 = (
    "application/pipelines/contexto_importacion.py",
    "application/pipelines/paso_importacion.py",
    "application/pipelines/plantilla.py",
    "application/pipelines/revision.py",
    "application/pipelines/tipos_reclamacion.py",
    "domain/models/importacion.py",
    "domain/models/plantilla_incidencias.py",
    "domain/models/revision.py",
    "domain/ports/tipos_reclamacion.py",
    "infrastructure/documentos/plantilla_yaml.py",
    "infrastructure/persistencia/sentencias_bandeja.py",
    "infrastructure/persistencia/sentencias_revision.py",
    "infrastructure/sigrid/consultas_tipos_reclamacion.py",
    "infrastructure/sigrid/tipos_reclamacion.py",
    "interface_adapters/api/bandeja.py",
    "interface_adapters/api/importar.py",
    "interface_adapters/api/plantilla.py",
    "interface_adapters/api/revision.py",
)

#: Lo que nombraría una escritura en Sigrid o una ventana de escritura.
MARCAS_DE_ESCRITURA = (
    "sql/write",
    "partes-reclamacion",
    "concepto-grafico",
    "_habilitado",
)

#: Los adaptadores de Sigrid que escriben: ninguna pieza de F-072 los importa.
ADAPTADORES_DE_ESCRITURA = (
    "infrastructure.sigrid.escrituras",
    "infrastructure.sigrid.graficos",
    "infrastructure.sigrid.volcado",
)

#: Lo que un test de F-072 no puede importar (R31): la base, la IA.
IMPORTS_PROHIBIDOS_EN_LOS_TESTS = (
    "psycopg",
    "psycopg2",
    "psycopg_pool",
    "google.genai",
    "google.generativeai",
    "infrastructure.llm",
)

#: Las consultas de Sigrid que ya existían (R32), por módulo y constante, con la
#: huella `sha256` de su texto en la base fija `6994cb0`.
CONSULTAS_DE_SIGRID = {
    ("infrastructure.sigrid.consultas_catalogo", "SQL_UNIDADES_DE_LA_OBRA"): (
        "43582a85dfd4c0df2360412f0062348c1a88e1b92761ba6e89e2e5f04ae36c9e"
    ),
    ("infrastructure.sigrid.consultas_catalogo", "SQL_OFICIOS_DE_LA_OBRA"): (
        "10eb8186bf9475e0347112aa4079cfc089011c85bf4c0442461ea1fecb1ad058"
    ),
    ("infrastructure.sigrid.consultas_ubicaciones_validas", "SQL_UBICACIONES_DE_LAS_UNIDADES"): (
        "fa92707bd5f786f6ad20340b6649a928a97d09cbc657bc6ed6d6080d9f0df8a7"
    ),
    ("infrastructure.sigrid.consultas_reclamaciones_obra", "SQL_RECLAMACIONES_DE_LA_OBRA"): (
        "ed0ab14756420ec14f2df6ead1243d7ff97b87b0b127aa472b1799a6ee9eda02"
    ),
    ("infrastructure.sigrid.consultas_reclamaciones_obra", "SQL_RECLAMACIONES_DE_LAS_UNIDADES"): (
        "67fdf23629d0b09289fde2f349cf521939731ecd83bfc8023ca3ad052bc3c170"
    ),
    ("infrastructure.sigrid.consultas_ubicacion", "SQL_UBICACION"): (
        "dd7ba0f8c84383d9f317bae549d935f75fcba332ee63eaca15012606823c666e"
    ),
    ("infrastructure.sigrid.consultas_ubicacion", "SQL_UNIDADES_DEL_NUMERO"): (
        "acb08bf73fa792253433ca809bd928dd22dfeb95fd4ea4a7ec29e44aad552018"
    ),
    ("infrastructure.sigrid.consultas_ubicacion", "SQL_UNIDADES_DEL_CODIGO"): (
        "b7bea3dea658fe497d3597cb97f733531715d943fef93651fd2efe96e43cbd50"
    ),
}

#: Los `.sql` que R32 nombra, con la huella de su texto en la base fija (sin
#: mirar el fin de línea, que depende de `core.autocrlf` del clon).
SQL_INTOCABLES = {
    "13_bandeja_incidencias.sql": "8ffba339dba6636164193e0e6c9b1dd17c87d12fe92affa3ef5e6947b82f3378",
    "15_revisiones_bandeja.sql": "b8df99e2c4ea0af8fcdf7926d5d2d20211f88523fa0fcb108c4483215293c79a",
    "16_volcados_sigrid.sql": "12279ec69bf1131c7772b93adcc3ce95e5ad92524eba3fe26786e431c043f45c",
}
DIRECTORIO_SQL = "infrastructure/persistencia/sql/"

#: El único `.sql` que trae F-072 (`design.md` §7), y nuevo.
SQL_DE_F072 = SERVICIO + DIRECTORIO_SQL + "17_tipo_reclamacion.sql"

#: En `infrastructure/sigrid/`, lo único que la rama puede tocar (§3.1, §3.2).
EN_SIGRID = SERVICIO + "infrastructure/sigrid/"
NUEVOS_EN_SIGRID = frozenset(
    {
        EN_SIGRID + "consultas_tipos_reclamacion.py",
        EN_SIGRID + "tipos_reclamacion.py",
    }
)
FABRICA = EN_SIGRID + "fabrica.py"
#: Lo que la fábrica gana (§3.2) y lo único de ella que cambia (`__all__`).
NUEVAS_EN_LA_FABRICA = frozenset({"construir_tipos_reclamacion"})
CAMBIAN_EN_LA_FABRICA = frozenset({"__all__"})

#: R32 y `design.md` §3.3: directorios enteros que la rama no toca.
DIRECTORIOS_INTOCABLES = ("services/postventa-front/",)

#: R32 y `design.md` §3.3: ficheros sueltos que la rama no toca.
FICHEROS_INTOCABLES = tuple(
    SERVICIO + ruta
    for ruta in (
        # Las lecturas y escrituras de Sigrid que ya existían.
        "infrastructure/sigrid/consultas_catalogo.py",
        "infrastructure/sigrid/consultas_ubicaciones_validas.py",
        "infrastructure/sigrid/consultas_reclamaciones_obra.py",
        "infrastructure/sigrid/catalogo_obra.py",
        "infrastructure/sigrid/volcado.py",
        "infrastructure/sigrid/cliente.py",
        # El volcado de la aplicación y la guarda del ensayo (F-059, F-065).
        "application/pipelines/volcado.py",
        "application/pipelines/guarda_sigrid.py",
        # El DDL.
        "infrastructure/persistencia/ddl.py",
        # El generador y la lectura aislada (D-21 de F-071).
        "infrastructure/documentos/excel_openpyxl.py",
        "infrastructure/documentos/lector_aislado.py",
        "infrastructure/documentos/ejecutor_aislado.py",
        # Las equivalencias.
        "domain/models/equivalencias.py",
        "application/pipelines/equivalencias.py",
        "interface_adapters/api/equivalencias.py",
        "domain/ports/equivalencias.py",
        # F-065.
        "domain/models/sigrid_bandeja.py",
        "application/pipelines/sigrid_bandeja.py",
        "interface_adapters/api/sigrid_bandeja.py",
    )
)

FUNCTION_APP = SERVICIO + "function_app.py"


# --------------------------------------------------------------------------
# `git`, sin poder tumbar la suite
# --------------------------------------------------------------------------


def _git(*argumentos: str) -> subprocess.CompletedProcess[str] | None:
    """Un `git` local y de solo lectura, o `None` si no hay `git`."""
    try:
        return subprocess.run(
            ["git", *argumentos],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except (OSError, ValueError):  # pragma: no cover - no hay git en el PATH
        return None


def _base() -> str | None:
    """La base fija, si está en este clon."""
    resultado = _git("rev-parse", "--verify", "--quiet", f"{BASE_FIJA}^{{commit}}")
    if resultado is None or resultado.returncode != 0:
        return None
    return resultado.stdout.strip() or None


def _cambios_en_la_rama() -> list[tuple[str, str]] | None:
    """`git diff --name-status <base fija>`: los commits de la rama **y** el árbol.

    Cada cambio como `(estado, ruta)`, con `estado` en una letra (`A`, `M`,
    `D`…); un renombrado cuenta como su ruta nueva y su ruta vieja.
    """
    base = _base()
    if base is None:
        return None
    diff = _git("diff", "--name-status", base)
    if diff is None or diff.returncode != 0:  # pragma: no cover - repo no sano
        return None
    cambios: list[tuple[str, str]] = []
    for linea in diff.stdout.splitlines():
        partes = linea.strip().split("\t")
        if len(partes) < 2:
            continue
        estado = partes[0][:1]
        for ruta in partes[1:]:
            cambios.append((estado, ruta.strip().replace("\\", "/")))
    return cambios


def _rama_actual() -> str | None:
    resultado = _git("rev-parse", "--abbrev-ref", "HEAD")
    if resultado is None or resultado.returncode != 0:  # pragma: no cover
        return None
    return resultado.stdout.strip() or None


def _la_rama_ya_esta_en_dev() -> bool:
    """`True` cuando `HEAD` ya forma parte de `dev`: la rama cumplió su ciclo."""
    resultado = _git("merge-base", "--is-ancestor", "HEAD", "dev")
    return resultado is not None and resultado.returncode == 0


def _fuera_de_la_rama_de_la_feature() -> bool:
    rama = _rama_actual()
    return rama is not None and rama != RAMA_DE_LA_FEATURE


def _diff_de_la_rama_o_saltar() -> list[tuple[str, str]]:
    """Los cambios de la rama; o se salta el control (defecto de F-030)."""
    cambios = _cambios_en_la_rama()
    if cambios is None:  # pragma: no cover - depende del clon
        pytest.skip(f"no hay 'git' o la base fija {BASE_FIJA} no está en este clon")
    if _fuera_de_la_rama_de_la_feature() or (not cambios and _la_rama_ya_esta_en_dev()):
        pytest.skip(
            f"este control vive en {RAMA_DE_LA_FEATURE} mientras no esté "
            "mergeada. Lo que no depende de 'git' se sigue comprobando en "
            "cualquier rama, en los tests hermanos de este"
        )
    return cambios


def _en_la_base(ruta: str) -> str:
    fuente = _git("show", f"{_base()}:{ruta}")
    assert fuente is not None and fuente.returncode == 0, f"sin {ruta} en la base"
    return fuente.stdout


# --------------------------------------------------------------------------
# Las reglas, puras: lo que se le pasa es lo que se juzga
# --------------------------------------------------------------------------


def tocados_intocables(rutas: list[str]) -> list[str]:
    """Las rutas de `rutas` que R32 y §3.3 prohíben tocar.

    En `infrastructure/sigrid/` solo valen los dos módulos nuevos y la fábrica
    (que se juzga aparte); en el DDL, solo `17_tipo_reclamacion.sql`.
    """
    prohibidas = []
    for ruta in rutas:
        if ruta.startswith(DIRECTORIOS_INTOCABLES) or ruta in FICHEROS_INTOCABLES:
            prohibidas.append(ruta)
        elif ruta.startswith(EN_SIGRID) and ruta not in NUEVOS_EN_SIGRID | {FABRICA}:
            prohibidas.append(ruta)
    return sorted(prohibidas)


def sql_tocados(cambios: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Los cambios en `.sql` que no son añadir `17_tipo_reclamacion.sql`."""
    return sorted(
        (estado, ruta)
        for estado, ruta in cambios
        if ruta.lower().endswith(".sql") and (estado, ruta) != ("A", SQL_DE_F072)
    )


def marcas_de_escritura(fuente: str) -> list[str]:
    """Las marcas de `MARCAS_DE_ESCRITURA` que aparecen en `fuente`, sin mayúsculas."""
    plegada = fuente.casefold()
    return [marca for marca in MARCAS_DE_ESCRITURA if marca in plegada]


def modulos_importados(fuente: str) -> set[str]:
    """Cada módulo que importa `fuente`, y cada `módulo.nombre` de un `from`."""
    importados: set[str] = set()
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module)
            importados.update(f"{nodo.module}.{alias.name}" for alias in nodo.names)
        elif isinstance(nodo, ast.Import):
            importados.update(alias.name for alias in nodo.names)
    return importados


def _de(importados: set[str], prefijos: tuple[str, ...]) -> list[str]:
    return sorted(
        modulo
        for modulo in importados
        if any(modulo == p or modulo.startswith(p + ".") for p in prefijos)
    )


def importa_escrituras(fuente: str) -> list[str]:
    """Los adaptadores de escritura de Sigrid que importa `fuente`."""
    return _de(modulos_importados(fuente), ADAPTADORES_DE_ESCRITURA)


def importa_base_o_ia(fuente: str) -> list[str]:
    """Los drivers de base o de IA que importa `fuente` (R31, los tests)."""
    return _de(modulos_importados(fuente), IMPORTS_PROHIBIDOS_EN_LOS_TESTS)


def construye_un_cliente_de_red(fuente: str) -> bool:
    """Si `fuente` construye un cliente de `httpx` de verdad (`httpx.Client(...)`)."""
    for nodo in ast.walk(ast.parse(fuente)):
        if (
            isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Attribute)
            and nodo.func.attr in {"Client", "AsyncClient"}
            and isinstance(nodo.func.value, ast.Name)
            and nodo.func.value.id == "httpx"
        ):
            return True
    return False


def definiciones(fuente: str) -> dict[str, str]:
    """Cada definición de nivel de módulo, por nombre, como en F-060 y F-071."""
    salida: dict[str, str] = {}
    for nodo in ast.parse(fuente).body:
        if isinstance(nodo, ast.FunctionDef | ast.AsyncFunctionDef):
            salida[nodo.name] = ast.unparse(nodo)
        elif isinstance(nodo, ast.ClassDef):
            for metodo in nodo.body:
                if isinstance(metodo, ast.FunctionDef | ast.AsyncFunctionDef):
                    salida[f"{nodo.name}.{metodo.name}"] = ast.unparse(metodo)
            salida[nodo.name] = ast.unparse(nodo)
        elif isinstance(nodo, ast.Assign | ast.AnnAssign):
            objetivos = nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]
            for objetivo in objetivos:
                if isinstance(objetivo, ast.Name):
                    salida[objetivo.id] = ast.unparse(nodo)
    return salida


def sin_docstrings(fuente: str) -> str:
    """El código de `fuente` sin ningún docstring (módulo, clases, funciones)."""
    arbol = ast.parse(fuente)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            cuerpo = nodo.body
            if (
                cuerpo
                and isinstance(cuerpo[0], ast.Expr)
                and isinstance(cuerpo[0].value, ast.Constant)
                and isinstance(cuerpo[0].value.value, str)
            ):
                nodo.body = cuerpo[1:] or [ast.Pass()]
    return ast.unparse(arbol)


def huella_de_texto(texto: str) -> str:
    """La `sha256` de un texto con el fin de línea normalizado a `\\n`."""
    return hashlib.sha256(texto.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _leer(ruta_en_el_servicio: str) -> str:
    return (RAIZ_DEL_SERVICIO / ruta_en_el_servicio).read_text(encoding="utf-8")


def _tests_de_f072() -> list[Path]:
    return sorted(TESTS.glob("test_f072_*.py"))


# --------------------------------------------------------------------------
# Los controles cazan: cada regla, contra un caso que tiene que cazar
# --------------------------------------------------------------------------


def test_f072_t21_los_controles_leen_algo():
    """Un control que no lee nada da verde para siempre: lo que leen existe."""
    for ruta in FICHEROS_INTOCABLES:
        assert (RAIZ / ruta).is_file(), ruta
    for directorio in DIRECTORIOS_INTOCABLES:
        assert (RAIZ / directorio).is_dir(), directorio
    for pieza in PIEZAS_DE_F072:
        assert (RAIZ_DEL_SERVICIO / pieza).is_file(), pieza
    for nombre in SQL_INTOCABLES:
        assert (RAIZ_DEL_SERVICIO / DIRECTORIO_SQL / nombre).is_file(), nombre
    assert (RAIZ / SQL_DE_F072).is_file()
    assert NUEVAS_EN_LA_FABRICA <= set(definiciones(_leer(FABRICA.removeprefix(SERVICIO))))
    # Los tests de F-072 que se barren: los nueve de §3.1 y estos dos.
    assert len(_tests_de_f072()) >= 11


def test_f072_t21_el_control_de_lo_intocable_caza():
    rutas = [
        "services/postventa-front/js/revision.js",
        SERVICIO + "infrastructure/sigrid/consultas_catalogo.py",
        SERVICIO + "infrastructure/sigrid/escrituras.py",
        SERVICIO + "infrastructure/persistencia/ddl.py",
        SERVICIO + "infrastructure/documentos/excel_openpyxl.py",
        SERVICIO + "application/pipelines/guarda_sigrid.py",
        SERVICIO + "infrastructure/sigrid/tipos_reclamacion.py",
        FABRICA,
        SERVICIO + "domain/models/revision.py",
    ]

    assert tocados_intocables(rutas) == sorted(rutas[:6])


def test_f072_t21_el_control_del_sql_caza():
    cambios = [
        ("A", SQL_DE_F072),
        ("M", SQL_DE_F072),
        ("M", SERVICIO + DIRECTORIO_SQL + "13_bandeja_incidencias.sql"),
        ("A", SERVICIO + DIRECTORIO_SQL + "18_otra.SQL"),
        ("M", SERVICIO + "domain/models/revision.py"),
    ]

    assert sql_tocados(cambios) == sorted(cambios[1:4])


def test_f072_t21_los_controles_del_codigo_cazan():
    escribe = (
        "from infrastructure.sigrid.volcado import AdaptadorVolcado\n"
        "import psycopg\n"
        "from google import genai\n"
        "import httpx\n"
        "RUTA = '/api/sigrid/partes-reclamacion'\n"
        "cliente = httpx.Client()\n"
    )

    assert marcas_de_escritura(escribe) == ["partes-reclamacion"]
    assert importa_escrituras(escribe) == [
        "infrastructure.sigrid.volcado",
        "infrastructure.sigrid.volcado.AdaptadorVolcado",
    ]
    assert importa_base_o_ia(escribe) == ["google.genai", "psycopg"]
    assert construye_un_cliente_de_red(escribe)
    assert not construye_un_cliente_de_red("import httpx\nerror = httpx.ReadTimeout('x')\n")
    assert sin_docstrings('"""a"""\ndef f():\n    """b"""\n    return 1\n') == sin_docstrings(
        "def f():\n    return 1\n"
    )
    assert huella_de_texto("a\r\nb") == huella_de_texto("a\nb")


# --------------------------------------------------------------------------
# R31 · sin `git`: solo `sql/read`, ninguna escritura ni ventana
# --------------------------------------------------------------------------


@pytest.mark.parametrize("pieza", PIEZAS_DE_F072)
def test_f072_r31_ninguna_pieza_nombra_una_escritura_ni_una_ventana(pieza):
    assert marcas_de_escritura(_leer(pieza)) == [], pieza


@pytest.mark.parametrize("pieza", PIEZAS_DE_F072)
def test_f072_r31_ninguna_pieza_importa_un_adaptador_de_escritura(pieza):
    assert importa_escrituras(_leer(pieza)) == [], pieza


def test_f072_r31_la_funcion_nueva_de_la_fabrica_solo_construye_la_lectura():
    funcion = definiciones(_leer(FABRICA.removeprefix(SERVICIO)))["construir_tipos_reclamacion"]

    assert marcas_de_escritura(funcion) == []
    assert "AdaptadorTiposReclamacionSigridApi(" in funcion
    assert "exigir_entorno_con_catalogo(" in funcion


def test_f072_r31_la_lectura_nueva_va_por_sql_read_heredado():
    """El adaptador hereda el del catálogo, que solo conoce `RUTA_LECTURA`."""
    from infrastructure.sigrid.catalogo_obra import RUTA_LECTURA, AdaptadorCatalogoSigridApi
    from infrastructure.sigrid.tipos_reclamacion import AdaptadorTiposReclamacionSigridApi

    assert RUTA_LECTURA == "/api/sql/read"
    assert issubclass(AdaptadorTiposReclamacionSigridApi, AdaptadorCatalogoSigridApi)
    assert set(vars(AdaptadorTiposReclamacionSigridApi)) - {"__doc__", "__module__"} <= {
        "leer",
        "__qualname__",
        "__firstlineno__",
        "__static_attributes__",
    }
    fuente = _leer("infrastructure/sigrid/tipos_reclamacion.py")
    assert "httpx" not in modulos_importados(fuente)


# --------------------------------------------------------------------------
# R31 · sin `git`: los tests no tocan red, base ni IA
# --------------------------------------------------------------------------


def test_f072_r31_la_guardia_sin_red_sigue_puesta_para_toda_la_sesion():
    conftest = ast.parse((TESTS / "conftest.py").read_text(encoding="utf-8"))
    sin_red = [
        nodo
        for nodo in conftest.body
        if isinstance(nodo, ast.FunctionDef) and nodo.name == "sin_red"
    ]

    assert len(sin_red) == 1
    decorador = ast.unparse(sin_red[0].decorator_list[0])
    assert "autouse=True" in decorador and "scope='session'" in decorador
    assert "socket.socket.connect = _conexion_prohibida" in ast.unparse(sin_red[0])


@pytest.mark.parametrize("test", [p.name for p in sorted(TESTS.glob("test_f072_*.py"))])
def test_f072_r31_ningun_test_importa_la_base_ni_la_ia_ni_abre_la_red(test):
    fuente = (TESTS / test).read_text(encoding="utf-8")

    assert importa_base_o_ia(fuente) == [], test
    assert not construye_un_cliente_de_red(fuente), test


# --------------------------------------------------------------------------
# R32 · sin `git`: las consultas y el DDL que ya existían
# --------------------------------------------------------------------------


@pytest.mark.parametrize("modulo,constante", list(CONSULTAS_DE_SIGRID))
def test_f072_r32_las_consultas_de_sigrid_iguales_caracter_a_caracter(modulo, constante):
    """La huella de la base: cambiar una letra de la consulta cambia la huella."""
    texto = getattr(importlib.import_module(modulo), constante)

    assert hashlib.sha256(texto.encode("utf-8")).hexdigest() == CONSULTAS_DE_SIGRID[
        (modulo, constante)
    ]


@pytest.mark.parametrize("nombre", list(SQL_INTOCABLES))
def test_f072_r32_los_sql_anteriores_son_los_de_la_base(nombre):
    assert huella_de_texto(_leer(DIRECTORIO_SQL + nombre)) == SQL_INTOCABLES[nombre]


# --------------------------------------------------------------------------
# R32 · contra la base fija, en la rama
# --------------------------------------------------------------------------


def test_f072_r32_la_rama_no_toca_lo_intocable():
    rutas = [ruta for _, ruta in _diff_de_la_rama_o_saltar()]

    assert tocados_intocables(rutas) == []


def test_f072_r32_el_unico_sql_de_la_rama_es_el_17_y_es_nuevo():
    assert sql_tocados(_diff_de_la_rama_o_saltar()) == []


def test_f072_r32_en_sigrid_solo_se_anaden_los_dos_modulos_nuevos():
    cambios = _diff_de_la_rama_o_saltar()
    en_sigrid = {(estado, ruta) for estado, ruta in cambios if ruta.startswith(EN_SIGRID)}

    assert en_sigrid <= {("A", ruta) for ruta in NUEVOS_EN_SIGRID} | {("M", FABRICA)}


@pytest.mark.parametrize(
    "modulo",
    (
        "infrastructure/sigrid/consultas_catalogo.py",
        "infrastructure/sigrid/consultas_ubicaciones_validas.py",
        "infrastructure/sigrid/consultas_reclamaciones_obra.py",
        "infrastructure/sigrid/consultas_ubicacion.py",
        "infrastructure/sigrid/consultas.py",
    ),
)
def test_f072_r32_las_consultas_de_sigrid_son_las_de_la_base(modulo):
    """El fichero entero, carácter a carácter, contra la base fija."""
    _diff_de_la_rama_o_saltar()

    assert _leer(modulo).replace("\r\n", "\n") == _en_la_base(SERVICIO + modulo)


def test_f072_r32_las_huellas_son_las_de_la_base():
    """Las huellas fijas de arriba son las del texto de la base, no las de hoy."""
    _diff_de_la_rama_o_saltar()
    for (modulo, constante), huella in CONSULTAS_DE_SIGRID.items():
        texto = getattr(importlib.import_module(modulo), constante)
        fuente = _en_la_base(SERVICIO + modulo.replace(".", "/") + ".py")
        assert constante in fuente, constante
        assert hashlib.sha256(texto.encode("utf-8")).hexdigest() == huella, constante
    for nombre, huella in SQL_INTOCABLES.items():
        assert huella_de_texto(_en_la_base(SERVICIO + DIRECTORIO_SQL + nombre)) == huella, nombre


def test_f072_r32_la_fabrica_solo_gana_la_lectura_de_los_tipos():
    _diff_de_la_rama_o_saltar()
    hoy = definiciones(_leer(FABRICA.removeprefix(SERVICIO)))
    antes = definiciones(_en_la_base(FABRICA))

    cambiadas = {n for n in hoy if n in antes and hoy[n] != antes[n]}
    assert set(hoy) - set(antes) == NUEVAS_EN_LA_FABRICA
    assert set(antes) - set(hoy) == set()
    assert cambiadas <= CAMBIAN_EN_LA_FABRICA, sorted(cambiadas - CAMBIAN_EN_LA_FABRICA)


def test_f072_r32_function_app_no_cambia_salvo_docstrings():
    _diff_de_la_rama_o_saltar()

    assert sin_docstrings(_leer(FUNCTION_APP.removeprefix(SERVICIO))) == sin_docstrings(
        _en_la_base(FUNCTION_APP)
    )


def test_f072_r32_rutas_http_iguales():
    _diff_de_la_rama_o_saltar()

    def rutas(fuente: str) -> set[str]:
        return set(re.findall(r'route="([^"]+)"', fuente))

    assert rutas(_leer(FUNCTION_APP.removeprefix(SERVICIO))) == rutas(_en_la_base(FUNCTION_APP))
