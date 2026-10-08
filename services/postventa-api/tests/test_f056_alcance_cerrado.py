# services/postventa-api/tests/test_f056_alcance_cerrado.py
"""Lo que F-056 promete **no** tocar, comprobado (T13; R12, R37, R39, R40, R45, §12).

F-056 mete en el servicio la revisión de la bandeja: una tabla nueva en su
esquema, una aplicación y tres endpoints. Lee Sigrid y escribe en su propio
esquema, y roza cosas que no son suyas. Cada frontera tiene aquí su control:

| Frontera | Requisito | Por qué no se toca |
|---|---|---|
| Las escrituras en Sigrid (`sql/write`, `sigrid/partes-reclamacion`, `sigrid/concepto-grafico`) | **R39** | F-056 solo lee, por `POST /api/sql/read` (las dos lecturas de F-036 y, desde el Bloque 3 bis, la de las ubicaciones válidas, §16.3); crear partes es F-040 |
| Las ventanas `ARCHIVO_HABILITADO` y `CIERRE_HABILITADO`, y las variables de entorno | **R40** | leer Sigrid y escribir en el esquema propio no abren nada ajeno; ninguna variable nueva |
| `UPDATE`, `DELETE`, `TRUNCATE` y DDL fuera del esquema | **R37** | la tabla es append-only y la bandeja no se toca |
| Lo de F-036 y F-053: sus tests, `GET /api/bandeja`, la importación, la plantilla, los catálogos | **R45** | y los ficheros de «No se toca» de `design.md` §12 |
| Una columna de correo fuera de `revisiones_bandeja` | **R12** | la excepción del correo es solo de esa tabla |

## Las dos mitades, y las tres guardas del diff

Con el patrón de `test_f036_alcance_cerrado.py`:

1. **el del diff**, contra la **base fija** de la feature (`f86d639`, fijada
   por el líder el 2026-10-06; no `git merge-base`, que se movería si `dev`
   avanzara) y hasta el **árbol de trabajo**, así que ve también lo que aún no
   se ha commiteado. Lleva las tres guardas de F-030 —`RAMA_DE_LA_FEATURE`,
   `_fuera_de_la_rama_de_la_feature` y `_la_rama_ya_esta_en_dev`— para no
   dejar `dev` en rojo cuando la rama se mergee;
2. **el que no depende de `git`**, que se comprueba siempre.

## Lo que **no** barre la guardia de R37: `tests_bbdd/` (O-5 de la review del Bloque 2)

R37 habla del **código del servicio**. La limpieza de
`tests_bbdd/tests/test_f056_bbdd_revision.py` lleva el **único** `DELETE` de
F-056, y va contra la base **efímera** de T8 (el `conftest` de `tests_bbdd`
aborta si el DSN no es local): sin vaciar `revisiones_bandeja`, la limpieza
de los tests de F-036 chocaría con la clave ajena. Por eso aquí, como en
F-036 con su propia limpieza, las suites (`tests/`, `tests_bbdd/`) no cuentan
como código: nombran lo prohibido para probarlo. Un test lo fija.

**Sin red, sin base de datos, sin IA y sin reloj.** Los controles del diff
llaman a `git`, que es un proceso local de solo lectura.
"""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]
RAIZ_DEL_SERVICIO = RAIZ / "services" / "postventa-api"

#: La rama en la que los controles del diff tienen algo que mirar (campo
#: `branch` de F-056 en `harness/features.json`).
RAMA_DE_LA_FEATURE = "feature/F-056-revision-bandeja-backend"

#: La base fija de la feature: el `dev` del que nace la rama.
BASE_FIJA = "f86d639"

SERVICIO = "services/postventa-api/"


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


def _ficheros_cambiados_en_la_rama() -> list[str] | None:
    """`git diff --name-only <base fija>`: los commits de la rama **y** el árbol."""
    base = _base()
    if base is None:
        return None
    diff = _git("diff", "--name-only", base)
    if diff is None or diff.returncode != 0:  # pragma: no cover - repo no sano
        return None
    return [
        linea.strip().replace("\\", "/") for linea in diff.stdout.splitlines() if linea.strip()
    ]


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


def _diff_de_la_rama_o_saltar() -> list[str]:
    """Los ficheros que tocó la rama; o se salta el control (defecto de F-030)."""
    cambiados = _ficheros_cambiados_en_la_rama()
    if cambiados is None:  # pragma: no cover - depende del clon
        pytest.skip(f"no hay 'git' o la base fija {BASE_FIJA} no está en este clon")
    if _fuera_de_la_rama_de_la_feature() or (
        not cambiados and _la_rama_ya_esta_en_dev()
    ):
        pytest.skip(
            f"este control vive en {RAMA_DE_LA_FEATURE} mientras no esté "
            "mergeada. Lo que no depende de 'git' se sigue comprobando en "
            "cualquier rama, en el test hermano de este"
        )
    return cambiados


def _en_la_base(ruta: str) -> str:
    fuente = _git("show", f"{_base()}:{ruta}")
    assert fuente is not None and fuente.returncode == 0, f"sin {ruta} en la base"
    return fuente.stdout


def _lineas_anadidas(rutas: list[str]) -> list[str]:
    diff = _git("diff", "-U0", _base() or "", "--", *rutas)
    assert diff is not None and diff.returncode == 0
    return [
        linea
        for linea in diff.stdout.splitlines()
        if linea.startswith("+") and not linea.startswith("+++")
    ]


def test_f056_el_control_del_diff_no_esta_mirando_una_lista_vacia():
    """Si el diff viniera vacío, los controles de abajo mentirían todos."""
    cambiados = _diff_de_la_rama_o_saltar()

    for imprescindible in (
        f"{SERVICIO}function_app.py",
        f"{SERVICIO}domain/models/revision.py",
        f"{SERVICIO}application/pipelines/revision.py",
        f"{SERVICIO}interface_adapters/api/revision.py",
        f"{SERVICIO}infrastructure/persistencia/sql/15_revisiones_bandeja.sql",
    ):
        assert imprescindible in cambiados, f"la rama tiene que haber tocado {imprescindible}"


# --------------------------------------------------------------------------
# El código de F-056, escrito a mano
# --------------------------------------------------------------------------

#: Los ficheros **nuevos** de producción de F-056 (`design.md` §12), escritos a
#: mano y no leídos del disco. Los tres últimos, del Bloque 3 bis (§16.3; O-2
#: de la review del Bloque 3).
NUEVOS_DE_F056 = (
    "domain/models/revision.py",
    "domain/ports/revision.py",
    "application/pipelines/revision.py",
    "infrastructure/persistencia/sql/15_revisiones_bandeja.sql",
    "infrastructure/persistencia/sentencias_revision.py",
    "infrastructure/persistencia/repositorio_revision_pg.py",
    "interface_adapters/api/revision.py",
    "domain/ports/ubicaciones_validas.py",
    "infrastructure/sigrid/consultas_ubicaciones_validas.py",
    "infrastructure/sigrid/ubicaciones_validas.py",
)

#: Lo que F-056 añade dentro de ficheros que ya existían: la función exacta.
FUNCIONES_DE_F056 = (
    ("function_app.py", "_error_de_revision"),
    ("function_app.py", "revision"),
    ("function_app.py", "revision_historial"),
    ("function_app.py", "revision_acciones"),
    ("infrastructure/persistencia/fabrica.py", "construir_revision"),
    ("infrastructure/sigrid/fabrica.py", "construir_ubicaciones_validas"),
)


def _sin_docstrings(arbol: ast.AST) -> ast.AST:
    """El árbol sin docstrings: lo que se **ejecuta**, no lo que se explica."""
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
    return arbol


def _codigo_que_se_ejecuta(relativa: str) -> str:
    """Un `.py` sin docstrings ni comentarios; el SQL, sin sus comentarios `--`."""
    ruta = RAIZ_DEL_SERVICIO / relativa
    fuente = ruta.read_text(encoding="utf-8")
    if ruta.suffix == ".sql":
        return "\n".join(linea.split("--")[0] for linea in fuente.splitlines())
    return ast.unparse(_sin_docstrings(ast.parse(fuente)))


def _funcion(relativa: str, nombre: str, fuente: str | None = None) -> str:
    """El código de una función de nivel de módulo, sin su docstring."""
    texto = fuente if fuente is not None else (RAIZ_DEL_SERVICIO / relativa).read_text(
        encoding="utf-8"
    )
    for nodo in ast.parse(texto).body:
        if isinstance(nodo, ast.FunctionDef) and nodo.name == nombre:
            return ast.unparse(_sin_docstrings(nodo))
    raise AssertionError(f"{relativa} no define {nombre}")


def _todo_el_codigo_de_f056() -> dict[str, str]:
    piezas = {r: _codigo_que_se_ejecuta(r) for r in NUEVOS_DE_F056}
    piezas.update({f"{r}::{n}": _funcion(r, n) for r, n in FUNCIONES_DE_F056})
    return piezas


def test_f056_la_lista_de_ficheros_de_f056_existe_entera():
    """Una lista con un fichero que no existe daría verde sin mirarlo."""
    faltan = [r for r in NUEVOS_DE_F056 if not (RAIZ_DEL_SERVICIO / r).is_file()]

    assert faltan == []
    assert len(_todo_el_codigo_de_f056()) == len(NUEVOS_DE_F056) + len(FUNCIONES_DE_F056)


def test_f056_quitar_docstrings_no_esconde_el_codigo():
    """Control negativo del comparador: el docstring se va, lo demás se queda."""
    fuente = '"""Sin CIERRE_HABILITADO."""\ndef f():\n    """Ni sql/write."""\n    return "sql/write"\n'

    codigo = ast.unparse(_sin_docstrings(ast.parse(fuente)))

    assert "CIERRE_HABILITADO" not in codigo
    assert "sql/write" in codigo


# --------------------------------------------------------------------------
# R39 · nada de F-056 escribe en Sigrid
# --------------------------------------------------------------------------

#: Las rutas de escritura de `sigrid-api` (`azure-apps/sigrid_api.md`).
ESCRITURAS_EN_SIGRID = ("sql/write", "sigrid/partes-reclamacion", "sigrid/concepto-grafico")

#: Los módulos del servicio que escriben en el ERP: F-056 no los importa.
MODULOS_QUE_ESCRIBEN_EN_SIGRID = ("infrastructure.sigrid.escrituras", "infrastructure.sigrid.graficos")

#: Carpetas del árbol que **no** son código: las nombran para prohibirlas.
#: `tests_bbdd` incluida: su limpieza es el único `DELETE` de F-056 (O-5).
CARPETAS_QUE_NO_SON_CODIGO = {"tests", "tests_js", "tests_bbdd", ".venv", "__pycache__"}


def _es_codigo(ruta: str) -> bool:
    """¿Es código que se ejecuta (servicios o `infra/`), y no una suite?"""
    if not ruta.startswith(("services/", "infra/")):
        return False
    return not CARPETAS_QUE_NO_SON_CODIGO.intersection(ruta.split("/"))


def test_f056_r39_ninguna_linea_anadida_por_la_rama_nombra_una_escritura():
    """R39 · la mitad del diff: cada línea añadida al código, en cualquier fichero."""
    cambiados = _diff_de_la_rama_o_saltar()
    codigo = [ruta for ruta in cambiados if _es_codigo(ruta)]
    assert codigo, "la rama no ha tocado código: el control no mira nada"

    anadidas = _lineas_anadidas(codigo)

    assert anadidas
    assert [linea for linea in anadidas if any(e in linea for e in ESCRITURAS_EN_SIGRID)] == []


def test_f056_r39_el_codigo_de_f056_no_nombra_ninguna_escritura():
    """R39 · la mitad que no depende de `git`."""
    culpables = {
        pieza: [e for e in ESCRITURAS_EN_SIGRID if e in codigo]
        for pieza, codigo in _todo_el_codigo_de_f056().items()
        if any(e in codigo for e in ESCRITURAS_EN_SIGRID)
    }

    assert culpables == {}


def _modulos_importados(relativa: str) -> set[str]:
    arbol = ast.parse((RAIZ_DEL_SERVICIO / relativa).read_text(encoding="utf-8"))
    importados: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module)
            importados.update(f"{nodo.module}.{alias.name}" for alias in nodo.names)
    return importados


def test_f056_r39_ningun_modulo_de_f056_importa_las_escrituras_del_erp():
    culpables = {
        r: sorted(m for m in _modulos_importados(r) if m.startswith(MODULOS_QUE_ESCRIBEN_EN_SIGRID))
        for r in NUEVOS_DE_F056 + ("function_app.py",)
        if r.endswith(".py")
    }

    assert {r: m for r, m in culpables.items() if m} == {}


def test_f056_r39_de_sigrid_solo_se_usa_el_catalogo_de_f036():
    """R39 · de `infrastructure/sigrid`, F-056 usa las lecturas y nada más.

    Fuera de `infrastructure/sigrid`, solo el borde, y solo los dos
    constructores de lectura: el catálogo de F-036 y, desde el Bloque 3 bis
    (O-2 de la review del Bloque 3), `construir_ubicaciones_validas`. Dentro,
    el adaptador nuevo reutiliza el del catálogo (su puerta de entorno, su
    `sql/read`, sus reintentos y su techo) y sus propias consultas; ni el
    cliente del cierre ni las escrituras.
    """
    de_sigrid = {
        r: sorted(m for m in _modulos_importados(r) if m.startswith("infrastructure.sigrid"))
        for r in NUEVOS_DE_F056
        if r.endswith(".py")
    }

    assert {r: m for r, m in de_sigrid.items() if m} == {
        "interface_adapters/api/revision.py": [
            "infrastructure.sigrid.fabrica",
            "infrastructure.sigrid.fabrica.construir_catalogo_obra",
            "infrastructure.sigrid.fabrica.construir_ubicaciones_validas",
        ],
        "infrastructure/sigrid/ubicaciones_validas.py": [
            "infrastructure.sigrid.catalogo_obra",
            "infrastructure.sigrid.catalogo_obra.AdaptadorCatalogoSigridApi",
            "infrastructure.sigrid.consultas_ubicaciones_validas",
            "infrastructure.sigrid.consultas_ubicaciones_validas.fila_a_ubicaciones_unidad",
            "infrastructure.sigrid.consultas_ubicaciones_validas.select_ubicaciones_de_las_unidades",
        ],
    }


# --------------------------------------------------------------------------
# R40 · ninguna ventana de escritura y ninguna variable nueva
# --------------------------------------------------------------------------

FICHEROS_DE_CONFIGURACION = (
    f"{SERVICIO}config/settings.py",
    f"{SERVICIO}.env.example",
    f"{SERVICIO}local.settings.json.example",
    "infra/00_vars_postventa.ps1",
)


def test_f056_r40_el_codigo_de_f056_no_mira_ninguna_ventana_de_escritura():
    """R40 · ni `ARCHIVO_HABILITADO` ni `CIERRE_HABILITADO`, ni sus campos de `Ajustes`."""
    culpables = sorted(
        pieza for pieza, codigo in _todo_el_codigo_de_f056().items() if "habilitado" in codigo.lower()
    )

    assert culpables == []


def test_f056_r40_la_rama_no_toca_la_configuracion_del_entorno():
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if r in FICHEROS_DE_CONFIGURACION] == []
    assert not any(r.endswith((".env", "local.settings.json")) for r in cambiados)


def _lee_el_entorno(codigo: str) -> bool:
    return bool(re.search(r"\benviron\b|\bgetenv\b|\bputenv\b", codigo))


def test_f056_r40_el_codigo_de_f056_no_lee_el_entorno_por_su_cuenta():
    culpables = sorted(p for p, codigo in _todo_el_codigo_de_f056().items() if _lee_el_entorno(codigo))

    assert culpables == []
    assert _lee_el_entorno("os.environ['X']")
    assert not _lee_el_entorno("ajustes.entorno")


# --------------------------------------------------------------------------
# R37 · append-only, y DDL solo en el esquema propio
# --------------------------------------------------------------------------

_ESCRITURA_PROHIBIDA = re.compile(r"\bDELETE\b|\bTRUNCATE\b|(?<!FOR )\bUPDATE\b", re.IGNORECASE)
_DDL = re.compile(r"\b(CREATE|ALTER|DROP)\s+(TABLE|INDEX|SCHEMA|VIEW|FUNCTION)\b", re.IGNORECASE)


def test_f056_r37_el_codigo_de_f056_no_actualiza_ni_borra():
    """R37 · ningún `UPDATE`, `DELETE` ni `TRUNCATE` (el `FOR UPDATE` del bloqueo no lo es)."""
    culpables = {
        pieza: _ESCRITURA_PROHIBIDA.findall(codigo)
        for pieza, codigo in _todo_el_codigo_de_f056().items()
        if _ESCRITURA_PROHIBIDA.search(codigo)
    }

    assert culpables == {}
    assert "FOR UPDATE" in _codigo_que_se_ejecuta("infrastructure/persistencia/sentencias_revision.py")


def test_f056_r37_el_detector_de_escrituras_no_es_ciego():
    assert _ESCRITURA_PROHIBIDA.search("UPDATE postventa.revisiones_bandeja SET")
    assert _ESCRITURA_PROHIBIDA.search("delete from postventa.bandeja_incidencias")
    assert _ESCRITURA_PROHIBIDA.search("TRUNCATE postventa.revisiones_bandeja")
    assert not _ESCRITURA_PROHIBIDA.search("ORDER BY incidencia_id FOR UPDATE")


def test_f056_r37_el_ddl_solo_esta_en_su_sql_y_en_su_esquema():
    """R37 · DDL solo en `15_revisiones_bandeja.sql`, y todo cualificado en `postventa`."""
    con_ddl = sorted(p for p, codigo in _todo_el_codigo_de_f056().items() if _DDL.search(codigo))
    sql = _codigo_que_se_ejecuta("infrastructure/persistencia/sql/15_revisiones_bandeja.sql")

    assert con_ddl == ["infrastructure/persistencia/sql/15_revisiones_bandeja.sql"]
    assert re.findall(r"\b(?:TABLE|INDEX)\s+IF\s+NOT\s+EXISTS\s+([\w.]+)", sql) == [
        "postventa.revisiones_bandeja",
        "ix_revisiones_bandeja_incidencia",
    ]
    assert re.findall(r"\bON\s+([\w.]+)", sql) == ["postventa.revisiones_bandeja"]
    assert "public." not in sql


def test_f056_r37_o5_la_guardia_no_barre_las_suites_y_por_que():
    """O-5 de la review del Bloque 2: `tests_bbdd/` no es código del servicio.

    Su limpieza lleva el único `DELETE` de F-056, contra la base efímera de T8.
    Se fija que existe (si un día desapareciera, esta excepción sobraría) y
    que `_es_codigo` no la cuenta, igual que F-036 con la suya.
    """
    limpieza = (RAIZ_DEL_SERVICIO / "tests_bbdd/tests/test_f056_bbdd_revision.py").read_text(
        encoding="utf-8"
    )

    assert re.search(r"\bDELETE\b", limpieza)
    assert not _es_codigo(f"{SERVICIO}tests_bbdd/tests/test_f056_bbdd_revision.py")
    assert not _es_codigo(f"{SERVICIO}tests/test_f056_alcance_cerrado.py")
    assert _es_codigo(f"{SERVICIO}application/pipelines/revision.py")


# --------------------------------------------------------------------------
# R45, §12 · lo de F-036 y F-053 no cambia
# --------------------------------------------------------------------------

#: Los ficheros de «No se toca» de `design.md` §12, con su ruta de `git`.
INTOCABLES = tuple(
    f"{SERVICIO}{r}"
    for r in (
        "infrastructure/persistencia/sql/12_importaciones.sql",
        "infrastructure/persistencia/sql/13_bandeja_incidencias.sql",
        "infrastructure/persistencia/sql/14_decisiones_equivalencia.sql",
        "domain/models/importacion.py",
        "domain/models/plantilla_incidencias.py",
        "domain/models/equivalencias.py",
        "application/pipelines/equivalencias.py",
        "application/pipelines/catalogo_obra.py",
        "application/pipelines/plantilla.py",
        "application/pipelines/paso_importacion.py",
        "interface_adapters/api/bandeja.py",
        "interface_adapters/api/importar.py",
        "interface_adapters/api/equivalencias.py",
        "interface_adapters/api/plantilla.py",
        "infrastructure/persistencia/sentencias_bandeja.py",
        "infrastructure/persistencia/repositorio_bandeja_pg.py",
        "config/plantilla_incidencias.yaml",
        "infrastructure/sigrid/__init__.py",
        "infrastructure/sigrid/catalogo_obra.py",
        "infrastructure/sigrid/cliente.py",
        "infrastructure/sigrid/consultas.py",
        "infrastructure/sigrid/consultas_catalogo.py",
        "infrastructure/sigrid/consultas_ubicacion.py",
        "infrastructure/sigrid/escrituras.py",
        "infrastructure/sigrid/graficos.py",
        "infrastructure/sigrid/ubicacion.py",
    )
)

#: Las funciones de `function_app.py` de F-036 y F-053: la plantilla, la
#: importación, la bandeja y los catálogos no cambian (R45).
FUNCIONES_DE_F036 = (
    "plantilla",
    "importaciones",
    "bandeja",
    "catalogos_propuestas",
    "catalogos_decisiones",
    "_rechazo_de_obra",
    "_sin_sigrid_o_sin_base",
)

#: El único test de F-036 que la rama toca: `test_f036_ddl.py`, ampliado por
#: T4 (lo que va tras el 11 es 12, 13, 14 y 15), sin relajar nada.
TESTS_DE_F036_AMPLIADOS = (f"{SERVICIO}tests/test_f036_ddl.py",)


def test_f056_s12_los_intocables_existen():
    assert [r for r in INTOCABLES if not (RAIZ / r).is_file()] == []


def test_f056_s12_la_rama_no_toca_ningun_intocable():
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if r in INTOCABLES] == []


def test_f056_r45_la_rama_no_toca_los_tests_de_f036_ni_de_f053():
    """R45 · siguen en verde **sin tocarse** (salvo el `.sql` que T4 manda ampliar)."""
    cambiados = _diff_de_la_rama_o_saltar()

    tocados = [
        r
        for r in cambiados
        if re.search(r"/tests(_bbdd/tests)?/test_f0(36|53)_", r) and r not in TESTS_DE_F036_AMPLIADOS
    ]

    assert tocados == []


def test_f056_r45_ni_el_front_ni_infra():
    """`services/postventa-front/` es F-038; `infra/*`, del despliegue (§12)."""
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if r.startswith(("services/postventa-front/", "infra/"))] == []


def test_f056_r45_los_endpoints_de_f036_y_f053_no_cambian_en_function_app():
    """La plantilla, la importación, la bandeja y los catálogos: la misma función."""
    _diff_de_la_rama_o_saltar()
    antes = _en_la_base(f"{SERVICIO}function_app.py")

    distintas = [
        n for n in FUNCIONES_DE_F036 if _funcion("function_app.py", n) != _funcion("function_app.py", n, antes)
    ]

    assert distintas == []


def test_f056_s12_la_fabrica_de_sigrid_solo_puede_ganar_funciones():
    """§12: en `infrastructure/sigrid/fabrica.py` solo se **añade** (Bloque 3 bis)."""
    _diff_de_la_rama_o_saltar()
    relativa = "infrastructure/sigrid/fabrica.py"
    antes = _en_la_base(f"{SERVICIO}{relativa}")
    nombres = [n.name for n in ast.parse(antes).body if isinstance(n, ast.FunctionDef)]

    assert nombres, "la fábrica de la base no tiene funciones: el control no mira nada"
    assert [n for n in nombres if _funcion(relativa, n) != _funcion(relativa, n, antes)] == []


# --------------------------------------------------------------------------
# R12 · ninguna columna de correo fuera de `revisiones_bandeja`
# --------------------------------------------------------------------------

CARPETA_SQL = RAIZ_DEL_SERVICIO / "infrastructure" / "persistencia" / "sql"


def test_f056_r12_solo_15_declara_una_columna_de_correo():
    """La mitad que no depende de `git`: el `.sql` sin comentarios de cada fichero."""
    con_correo = sorted(
        f.name
        for f in CARPETA_SQL.glob("*.sql")
        if re.search(r"correo", _codigo_que_se_ejecuta(f"infrastructure/persistencia/sql/{f.name}"), re.IGNORECASE)
    )

    assert con_correo == ["15_revisiones_bandeja.sql"]


def test_f056_r12_la_rama_no_toca_otro_sql():
    """La mitad del diff: el único `.sql` que toca la rama es el suyo."""
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if r.endswith(".sql")] == [
        f"{SERVICIO}infrastructure/persistencia/sql/15_revisiones_bandeja.sql"
    ]
