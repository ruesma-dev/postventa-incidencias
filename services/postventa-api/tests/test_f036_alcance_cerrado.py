# services/postventa-api/tests/test_f036_alcance_cerrado.py
"""Lo que F-036 promete **no** tocar, comprobado (T20; R46, R48, R49, R59, §2.3).

F-036 mete en el servicio la entrada de incidencias por Excel: lee Sigrid,
escribe en su propio esquema y devuelve ficheros. Todo eso roza cosas que no
son suyas, y cada frontera tiene aquí su control:

| Frontera | Requisito | Por qué no se toca |
|---|---|---|
| Las escrituras en Sigrid (`sql/write`, `sigrid/partes-reclamacion`, `sigrid/concepto-grafico`) | **R46** | F-036 solo lee (`POST /api/sql/read`); el catálogo de Sigrid no se corrige desde aquí |
| Las ventanas `ARCHIVO_HABILITADO` y `CIERRE_HABILITADO` | **R48** | leer Sigrid y escribir en el esquema propio no abren nada ajeno; la lectura exige `ENTORNO` en `dev`/`pro` |
| Las variables de entorno | **R49** | los endpoints nuevos no añaden ninguna |
| Los `.xlsx` | **R59** | ni la plantilla, ni el original, ni el `v2`, ni el Excel de errores, ni fixtures: los tests construyen sus libros en memoria |
| Los ficheros de `design.md` §2.3 | §2.3 | las escrituras del ERP, el SQL de F-013, la persistencia de F-005…F-034, sus puertos, sus pasos y sus handlers, `infra/00_vars_postventa.ps1` y la rama de F-035 |

## Las dos mitades, y las tres guardas del diff

Con el patrón de `test_f034_alcance_cerrado.py`:

1. **el del diff** (`git diff <base>`, del punto donde la rama se separó de
   `dev` al **árbol de trabajo**, así que ve también lo que aún no se ha
   commiteado): «esta rama no lo tocó». Lleva las tres guardas de F-030
   —`RAMA_DE_LA_FEATURE`, `_fuera_de_la_rama_de_la_feature` y
   `_la_rama_ya_esta_en_dev`— para no dejar `dev` en rojo cuando la rama se
   mergee;
2. **el que no depende de `git`**, que se comprueba siempre: «y hoy sigue
   siendo lo que tiene que ser».

## Una desviación, escrita (B6-19 en `progress/impl_F-036.md`)

`design.md` §2.3 dice que `infra/08_lectura_sigrid_comun.ps1` «se usa tal
cual», pero T1 bis (`1b3edfb`, encargo del líder del 2026-09-28) tuvo que
arreglar en él la doble codificación de las tildes que exige **R111**. Aquí no
se exige que sea idéntico a `dev`, sino lo más estricto que sigue siendo
verdad: **fuera de `Invoke-SigridLectura` no ha cambiado ni un carácter**, y
esa función sigue tocando solo `POST /api/sql/read`.

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

#: La raíz del servicio, de donde cuelga el código de producción.
RAIZ_DEL_SERVICIO = RAIZ / "services" / "postventa-api"

#: La rama en la que los controles del diff tienen algo que mirar. Sale de la
#: ficha de F-036 en `harness/features.json`, campo `branch`.
RAMA_DE_LA_FEATURE = "feature/F-036-importar-excel"

#: La rama de F-035, que F-036 ni mergea ni toca (§2.3).
RAMA_DE_F035 = "feature/F-035-portal-posventa"

#: Prefijo de las rutas del servicio tal y como las escribe `git`.
SERVICIO = "services/postventa-api/"


# --------------------------------------------------------------------------
# Preguntarle a `git` qué ha tocado esta rama, sin poder tumbar la suite
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


def _base_de_la_rama() -> str | None:
    """`git merge-base dev HEAD`, o `None` si `dev` no está en este clon."""
    base = _git("merge-base", "dev", "HEAD")
    if base is None or base.returncode != 0:
        return None
    return base.stdout.strip() or None


def _ficheros_cambiados_en_la_rama() -> list[str] | None:
    """`git diff --name-only <base>`: los commits de la rama **y** el árbol.

    Contra la **base** y no contra `dev`: lo que interesa es lo que ha
    cambiado esta rama desde que se separó, no lo que haya entrado en `dev`
    después. Y contra el árbol de trabajo, no contra `HEAD`: un fichero
    intocable modificado sin commitear también se ve.
    """
    base = _base_de_la_rama()
    if base is None:
        return None
    diff = _git("diff", "--name-only", base)
    if diff is None or diff.returncode != 0:  # pragma: no cover - repo no sano
        return None
    return [
        linea.strip().replace("\\", "/")
        for linea in diff.stdout.splitlines()
        if linea.strip()
    ]


def _rama_actual() -> str | None:
    """El nombre de la rama de trabajo, o `None` si no se puede saber."""
    resultado = _git("rev-parse", "--abbrev-ref", "HEAD")
    if resultado is None or resultado.returncode != 0:  # pragma: no cover
        return None
    return resultado.stdout.strip() or None


def _la_rama_ya_esta_en_dev() -> bool:
    """`True` cuando `HEAD` ya forma parte de `dev`: la rama cumplió su ciclo."""
    resultado = _git("merge-base", "--is-ancestor", "HEAD", "dev")
    return resultado is not None and resultado.returncode == 0


def _fuera_de_la_rama_de_la_feature() -> bool:
    """`True` cuando no estamos en la rama de F-036."""
    rama = _rama_actual()
    return rama is not None and rama != RAMA_DE_LA_FEATURE


def _saltar_si_no_hay_rama_que_mirar(cambiados: list[str] | None) -> list[str]:
    """Los ficheros que tocó la rama; o se salta el control (defecto de F-030).

    Los controles del diff viven **en la rama de la feature mientras no esté
    mergeada**. Fuera de ahí no hay nada que mirar, y un control sin nada que
    mirar no puede ponerse rojo. Lo que no depende de `git` está en el test
    hermano de cada uno.
    """
    if cambiados is None:  # pragma: no cover - depende del clon, no del código
        pytest.skip("no hay 'git' o la rama 'dev' no está en este clon")
    if _fuera_de_la_rama_de_la_feature() or (
        not cambiados and _la_rama_ya_esta_en_dev()
    ):
        pytest.skip(
            f"este control vive en {RAMA_DE_LA_FEATURE} mientras no esté "
            "mergeada. Lo que no depende de 'git' se sigue comprobando en "
            "cualquier rama, en el test hermano de este"
        )
    return cambiados


def _diff_de_la_rama_o_saltar() -> list[str]:
    return _saltar_si_no_hay_rama_que_mirar(_ficheros_cambiados_en_la_rama())


def _fuente_en_la_base_de_la_rama(ruta: str) -> str:
    """El fichero tal y como estaba cuando la rama se separó de `dev`."""
    base = _base_de_la_rama()
    assert base is not None, "sin base de la rama"
    fuente = _git("show", f"{base}:{ruta}")
    assert fuente is not None and fuente.returncode == 0, f"sin {ruta} en la base"
    return fuente.stdout


def test_f036_el_control_del_diff_no_esta_mirando_una_lista_vacia():
    """El control de los controles: si el diff viniera vacío, mentirían todos.

    Los de abajo afirman que **algo no aparece** en el diff. Un `git diff` que
    no devolviera nada los pondría verdes sin haber comprobado nada. Aquí se
    exige que la rama haya tocado aquello de lo que va la feature.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    assert cambiados, "el diff de la rama no puede estar vacío"
    for imprescindible in (
        f"{SERVICIO}function_app.py",
        f"{SERVICIO}interface_adapters/api/importar.py",
        f"{SERVICIO}application/pipelines/equivalencias.py",
        f"{SERVICIO}infrastructure/sigrid/catalogo_obra.py",
    ):
        assert imprescindible in cambiados, (
            f"la rama tiene que haber tocado {imprescindible}: es de lo que va "
            "la feature"
        )


# --------------------------------------------------------------------------
# El código de F-036, escrito a mano
# --------------------------------------------------------------------------

#: Los ficheros **nuevos** de producción de F-036 en el servicio
#: (`design.md` §2.1), escritos a mano y **no leídos del disco**: una lista
#: recalculada del propio árbol daría verde ante cualquier fichero nuevo. Los
#: del Bloque 8 (la migración) están al final; los del Bloque 7 (el front)
#: viven fuera del servicio y van en `FRONT_DE_F036`.
NUEVOS_DE_F036 = (
    "domain/models/plantilla_incidencias.py",
    "domain/models/importacion.py",
    "domain/models/equivalencias.py",
    "domain/ports/catalogo_obra.py",
    "domain/ports/hoja_calculo.py",
    "domain/ports/bandeja.py",
    "domain/ports/equivalencias.py",
    "application/pipelines/catalogo_obra.py",
    "application/pipelines/plantilla.py",
    "application/pipelines/contexto_importacion.py",
    "application/pipelines/paso_importacion.py",
    "application/pipelines/equivalencias.py",
    "config/plantilla_incidencias.yaml",
    "infrastructure/documentos/plantilla_yaml.py",
    "infrastructure/documentos/excel_openpyxl.py",
    "infrastructure/documentos/lector_aislado.py",  # T40 (octava enmienda)
    "infrastructure/documentos/ejecutor_aislado.py",  # T40 (octava enmienda)
    "infrastructure/sigrid/consultas_catalogo.py",
    "infrastructure/sigrid/catalogo_obra.py",
    "infrastructure/persistencia/sql/12_importaciones.sql",
    "infrastructure/persistencia/sql/13_bandeja_incidencias.sql",
    "infrastructure/persistencia/sql/14_decisiones_equivalencia.sql",
    "infrastructure/persistencia/sentencias_bandeja.py",
    "infrastructure/persistencia/repositorio_bandeja_pg.py",
    "interface_adapters/api/plantilla.py",
    "interface_adapters/api/importar.py",
    "interface_adapters/api/bandeja.py",
    "interface_adapters/api/equivalencias.py",
    "scripts/medir_catalogos_f036.py",
    "scripts/migracion_f036.py",
    "scripts/migrar_excel_f036.py",
    "scripts/contar_elementos_xml_f036.py",  # T37 (séptima enmienda)
)

#: Los ficheros **nuevos** del front de F-036 (Bloque 7), desde la raíz del
#: repositorio. Les aplican los controles de texto —R46 (ninguna escritura de
#: Sigrid nombrada), R48 (ninguna ventana) y R49 (no leen el entorno)—, sobre
#: el fichero **entero**, comentarios incluidos, que es más estricto. **No**
#: les aplica el de imports de R46, que mira módulos de Python: el front solo
#: habla con el `/api` de este servicio (`js/api.js`), nunca con `sigrid-api`.
FRONT_DE_F036 = (
    "services/postventa-front/importar.html",
    "services/postventa-front/oficios.html",
    "services/postventa-front/js/importacion.js",
    "services/postventa-front/js/oficios.js",
)

#: El script de medición de T1, en la raíz del repositorio.
SCRIPT_DE_MEDICION = "infra/26_catalogos_plantilla_sigrid.ps1"

#: Lo que F-036 añade dentro de ficheros que ya existían: la función exacta.
FUNCIONES_DE_F036 = (
    ("function_app.py", "plantilla"),
    ("function_app.py", "importaciones"),
    ("function_app.py", "bandeja"),
    ("function_app.py", "catalogos_propuestas"),
    ("function_app.py", "catalogos_decisiones"),
    ("infrastructure/sigrid/fabrica.py", "construir_catalogo_obra"),
    ("infrastructure/persistencia/fabrica.py", "construir_bandeja"),
    ("infrastructure/persistencia/fabrica.py", "construir_equivalencias"),
)


def _sin_docstrings(arbol: ast.AST) -> ast.AST:
    """El árbol sin los docstrings: lo que se **ejecuta**, no lo que se explica.

    Varios módulos de F-036 dicen en su docstring que **no** dependen de
    `CIERRE_HABILITADO` o que **no** usan `sql/write`; eso no puede contar
    como usarlos. Los comentarios ya los quita `ast`.
    """
    for nodo in ast.walk(arbol):
        if isinstance(
            nodo, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ):
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
    """El código de un fichero del servicio sin docstrings ni comentarios.

    Un `.py` se reescribe desde su árbol; el SQL y el YAML se leen tal cual.
    """
    ruta = RAIZ_DEL_SERVICIO / relativa
    fuente = ruta.read_text(encoding="utf-8")
    if ruta.suffix != ".py":
        return fuente
    return ast.unparse(_sin_docstrings(ast.parse(fuente)))


def _funcion(relativa: str, nombre: str) -> str:
    """El código de una función de nivel de módulo, sin su docstring."""
    arbol = ast.parse((RAIZ_DEL_SERVICIO / relativa).read_text(encoding="utf-8"))
    for nodo in arbol.body:
        if isinstance(nodo, ast.FunctionDef) and nodo.name == nombre:
            return ast.unparse(_sin_docstrings(nodo))
    raise AssertionError(f"{relativa} no define {nombre}")


def _todo_el_codigo_de_f036() -> dict[str, str]:
    """Cada pieza de F-036 con el código que ejecuta, por nombre legible."""
    piezas = {relativa: _codigo_que_se_ejecuta(relativa) for relativa in NUEVOS_DE_F036}
    piezas.update(
        {
            f"{relativa}::{nombre}": _funcion(relativa, nombre)
            for relativa, nombre in FUNCIONES_DE_F036
        }
    )
    piezas[SCRIPT_DE_MEDICION] = _ps1_sin_comentarios(
        (RAIZ / SCRIPT_DE_MEDICION).read_text(encoding="utf-8")
    )
    piezas.update(
        {front: (RAIZ / front).read_text(encoding="utf-8") for front in FRONT_DE_F036}
    )
    return piezas


def _ps1_sin_comentarios(fuente: str) -> str:
    """Un `.ps1` sin sus bloques `<# … #>` ni sus comentarios de línea."""
    sin_bloques = re.sub(r"<#.*?#>", "", fuente, flags=re.DOTALL)
    return "\n".join(
        linea
        for linea in sin_bloques.splitlines()
        if not linea.lstrip().startswith("#")
    )


def test_f036_la_lista_de_ficheros_de_f036_existe_entera():
    """Una lista con un fichero que no existe daría verde sin mirarlo."""
    faltan = [r for r in NUEVOS_DE_F036 if not (RAIZ_DEL_SERVICIO / r).is_file()]
    faltan += [r for r in FRONT_DE_F036 if not (RAIZ / r).is_file()]

    assert faltan == []
    assert (RAIZ / SCRIPT_DE_MEDICION).is_file()
    assert (
        len(_todo_el_codigo_de_f036())
        == len(NUEVOS_DE_F036) + len(FUNCIONES_DE_F036) + 1 + len(FRONT_DE_F036)
    )


def test_f036_r46_los_bloques_7_y_8_tambien_estan_en_el_control():
    """Cambio 5 de la review 1: la migración y el front, mirados sin docstrings."""
    piezas = _todo_el_codigo_de_f036()

    for script in ("scripts/migracion_f036.py", "scripts/migrar_excel_f036.py"):
        assert script in NUEVOS_DE_F036
        assert script in piezas
    for front in (
        "services/postventa-front/importar.html",
        "services/postventa-front/oficios.html",
        "services/postventa-front/js/importacion.js",
        "services/postventa-front/js/oficios.js",
    ):
        assert front in piezas


def test_f036_quitar_docstrings_no_esconde_el_codigo():
    """Control negativo del comparador: el docstring se va, lo demás se queda."""
    fuente = (
        '"""Doc: sin CIERRE_HABILITADO."""\n'
        "def f():\n"
        '    """Tampoco sql/write."""\n'
        '    return ajustes.cierre_habilitado or "sql/write"\n'
    )

    codigo = ast.unparse(_sin_docstrings(ast.parse(fuente)))

    assert "CIERRE_HABILITADO" not in codigo
    assert "cierre_habilitado" in codigo
    assert "sql/write" in codigo
    assert _ps1_sin_comentarios("<# sql/write #>\n# sql/write\n$a = 'sql/read'") == (
        "\n$a = 'sql/read'"
    )


# --------------------------------------------------------------------------
# R46 · nada de F-036 escribe en Sigrid
# --------------------------------------------------------------------------

#: Las rutas de escritura de `sigrid-api` (`azure-apps/sigrid_api.md`).
ESCRITURAS_EN_SIGRID = (
    "sql/write",
    "sigrid/partes-reclamacion",
    "sigrid/concepto-grafico",
)

#: Los módulos del servicio que escriben en el ERP (§2.3): F-036 no los importa.
MODULOS_QUE_ESCRIBEN_EN_SIGRID = (
    "infrastructure.sigrid.escrituras",
    "infrastructure.sigrid.graficos",
)

#: Carpetas del árbol que **no** son código: las nombran para prohibirlas.
CARPETAS_QUE_NO_SON_CODIGO = {
    "tests",
    "tests_js",
    "tests_bbdd",
    ".venv",
    "__pycache__",
}


def _es_codigo(ruta: str) -> bool:
    """¿Es código que se ejecuta (servicios, scripts o `infra/`)?"""
    if not ruta.startswith(("services/", "infra/")):
        return False
    return not CARPETAS_QUE_NO_SON_CODIGO.intersection(ruta.split("/"))


def test_f036_r46_ninguna_linea_anadida_por_la_rama_nombra_una_escritura():
    """R46 · la mitad del diff: **cada línea añadida** al código, en cualquier fichero.

    Mirar líneas añadidas y no ficheros enteros: `function_app.py` ya
    documentaba `/api/cerrar` antes de F-036, y eso no es de esta rama. Los
    tests, las specs, `progress/` y la documentación se quedan fuera: nombran
    las escrituras para prohibirlas.
    """
    cambiados = _diff_de_la_rama_o_saltar()
    codigo = [ruta for ruta in cambiados if _es_codigo(ruta)]
    assert codigo, "la rama no ha tocado código: el control no mira nada"

    diff = _git("diff", "-U0", _base_de_la_rama() or "", "--", *codigo)
    assert diff is not None and diff.returncode == 0
    anadidas = [
        linea
        for linea in diff.stdout.splitlines()
        if linea.startswith("+") and not linea.startswith("+++")
    ]

    culpables = [
        linea for linea in anadidas if any(e in linea for e in ESCRITURAS_EN_SIGRID)
    ]
    assert anadidas
    assert culpables == []


def test_f036_r46_el_codigo_de_f036_no_nombra_ninguna_escritura():
    """R46 · la mitad que no depende de `git`: el código que se ejecuta."""
    culpables = {
        pieza: [e for e in ESCRITURAS_EN_SIGRID if e in codigo]
        for pieza, codigo in _todo_el_codigo_de_f036().items()
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


def test_f036_r46_ningun_modulo_de_f036_importa_las_escrituras_del_erp():
    culpables = {
        relativa: sorted(
            m
            for m in _modulos_importados(relativa)
            if m.startswith(MODULOS_QUE_ESCRIBEN_EN_SIGRID)
        )
        for relativa in NUEVOS_DE_F036
        if relativa.endswith(".py")
    }

    assert {r: m for r, m in culpables.items() if m} == {}


def test_f036_r46_el_adaptador_del_catalogo_solo_conoce_sql_read():
    """R46 · «el adaptador del catálogo solo usa `POST /api/sql/read`».

    Todas las rutas de la pasarela que aparecen en el código del adaptador
    (sin docstrings) son esa, y la petición se hace con `post`.
    """
    codigo = _codigo_que_se_ejecuta("infrastructure/sigrid/catalogo_obra.py")

    rutas = set(re.findall(r"['\"](/api/[\w/\-]+)['\"]", codigo))
    assert rutas == {"/api/sql/read"}
    assert ".post(" in codigo
    for verbo in (".put(", ".patch(", ".delete("):
        assert verbo not in codigo


# --------------------------------------------------------------------------
# R48 · ninguna ventana de escritura; la lectura, con la puerta del entorno
# --------------------------------------------------------------------------


def test_f036_r48_el_codigo_de_f036_no_mira_ninguna_ventana_de_escritura():
    """R48 · ni `ARCHIVO_HABILITADO` ni `CIERRE_HABILITADO`, en ninguna pieza.

    Se busca «habilitado» en minúsculas sobre el código sin docstrings: cubre
    las dos variables, sus campos en `Ajustes` (`archivo_habilitado`,
    `cierre_habilitado`) y cualquier interruptor nuevo con el mismo nombre.
    """
    culpables = sorted(
        pieza
        for pieza, codigo in _todo_el_codigo_de_f036().items()
        if "habilitado" in codigo.lower()
    )

    assert culpables == []


def test_f036_r48_la_fabrica_del_catalogo_pasa_por_la_puerta_del_entorno():
    """R48 · la lectura del catálogo exige `ENTORNO` en `dev` o `pro`.

    El comportamiento lo prueban los tests de T13; aquí se fija que la fábrica
    **llama** a la puerta y que la lista es la del cierre, importada.
    """
    fabrica = _funcion("infrastructure/sigrid/fabrica.py", "construir_catalogo_obra")
    adaptador = _codigo_que_se_ejecuta("infrastructure/sigrid/catalogo_obra.py")

    assert "exigir_entorno_con_catalogo(ajustes.entorno)" in fabrica
    assert "ENTORNOS_CON_CIERRE" in adaptador
    assert "infrastructure.sigrid.cliente.ENTORNOS_CON_CIERRE" in _modulos_importados(
        "infrastructure/sigrid/catalogo_obra.py"
    )


# --------------------------------------------------------------------------
# R49 · ninguna variable de entorno nueva
# --------------------------------------------------------------------------

#: Donde vive la configuración del entorno: si F-036 añadiera una variable,
#: tendría que pasar por alguno de estos.
FICHEROS_DE_CONFIGURACION = (
    f"{SERVICIO}config/settings.py",
    f"{SERVICIO}.env.example",
    f"{SERVICIO}local.settings.json.example",
    "infra/00_vars_postventa.ps1",
)


def test_f036_r49_la_rama_no_toca_la_configuracion_del_entorno():
    """R49 · ni un campo en `Ajustes`, ni una línea en los ejemplos ni en `00_vars`."""
    cambiados = _diff_de_la_rama_o_saltar()

    culpables = [ruta for ruta in cambiados if ruta in FICHEROS_DE_CONFIGURACION]

    assert culpables == []
    assert not any(ruta.endswith((".env", "local.settings.json")) for ruta in cambiados)


def _lee_el_entorno(codigo: str) -> bool:
    return bool(re.search(r"\benviron\b|\bgetenv\b|\bputenv\b", codigo))


def test_f036_r49_el_codigo_de_f036_no_lee_el_entorno_por_su_cuenta():
    """R49 · la mitad que no depende de `git`: la configuración entra por `Ajustes`.

    Un `os.environ[...]` o un `os.getenv(...)` en código de F-036 sería una
    variable nueva que no pasa por `config/settings.py` ni por ningún ejemplo.
    """
    culpables = sorted(
        pieza
        for pieza, codigo in _todo_el_codigo_de_f036().items()
        if not pieza.endswith(".ps1") and _lee_el_entorno(codigo)
    )

    assert culpables == []
    assert _lee_el_entorno("valor = os.environ['X']")
    assert _lee_el_entorno("valor = os.getenv('X')")
    assert not _lee_el_entorno("entorno = ajustes.entorno")


# --------------------------------------------------------------------------
# R59 · ningún `.xlsx` entra en git
# --------------------------------------------------------------------------

EXTENSIONES_DE_LIBRO = (".xlsx", ".xlsm", ".xls", ".xltx", ".xltm")


def _es_un_libro(ruta: str) -> bool:
    return ruta.lower().endswith(EXTENSIONES_DE_LIBRO)


def test_f036_r59_ningun_commit_de_la_rama_trae_un_libro():
    """R59 · la mitad del diff: ni en un commit de la rama, ni preparado para uno.

    El historial entero de la rama, no solo el árbol: un fichero que entra y se
    borra en el commit siguiente sigue en el historial para siempre.
    """
    _diff_de_la_rama_o_saltar()
    historial = _git("log", "--name-only", "--format=", "dev..HEAD")
    preparados = _git("diff", "--cached", "--name-only")
    assert historial is not None and historial.returncode == 0
    assert preparados is not None and preparados.returncode == 0

    rutas = historial.stdout.splitlines() + preparados.stdout.splitlines()

    assert [r for r in rutas if _es_un_libro(r.strip())] == []
    assert any(r.strip() for r in historial.stdout.splitlines())


def test_f036_r59_ningun_libro_versionado_ni_en_los_tests():
    """R59 · la mitad que no depende de la rama: el índice y las carpetas de tests."""
    versionados = _git("ls-files")
    if versionados is None:  # pragma: no cover - no hay git
        pytest.skip("no hay 'git'")

    assert [r for r in versionados.stdout.splitlines() if _es_un_libro(r)] == []
    for carpeta in ("tests", "tests_bbdd"):
        en_disco = [
            p.name
            for p in (RAIZ_DEL_SERVICIO / carpeta).rglob("*")
            if _es_un_libro(p.name)
        ]
        assert en_disco == [], f"hay libros en {carpeta}: {en_disco}"


def test_f036_r59_el_gitignore_deja_fuera_los_xlsx():
    patrones = (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "*.xlsx" in patrones
    assert "*.xls" in patrones


#: Los tests de F-036 que tocan libros.
TESTS_CON_LIBROS = (
    "tests/utiles_plantilla.py",
    "tests/utiles_importacion.py",
    "tests/test_f036_excel_generador.py",
    "tests/test_f036_excel_lector.py",
    "tests/test_f036_pipeline_importacion.py",
    "tests/test_f036_importar_http.py",
    "tests/test_f036_plantilla_http.py",
)


def _abre_un_fichero_de_disco(fuente: str) -> list[int]:
    """Las líneas donde `load_workbook` u `open` reciben una ruta escrita a mano."""
    arbol = ast.parse(fuente)
    lineas: list[int] = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call) or not nodo.args:
            continue
        nombre = getattr(nodo.func, "id", None) or getattr(nodo.func, "attr", None)
        primero = nodo.args[0]
        if nombre in {"load_workbook", "open"} and (
            (isinstance(primero, ast.Constant) and isinstance(primero.value, str))
            or (
                isinstance(primero, ast.Call)
                and getattr(primero.func, "id", "") == "Path"
            )
        ):
            lineas.append(nodo.lineno)
    return lineas


def test_f036_r59_los_tests_construyen_sus_libros_en_memoria():
    """R59 · «ni fixtures de tests»: ningún `load_workbook("…")` ni `open(Path(…))`."""
    culpables = {
        r: _abre_un_fichero_de_disco(
            (RAIZ_DEL_SERVICIO / r).read_text(encoding="utf-8")
        )
        for r in TESTS_CON_LIBROS
    }

    assert {r: l for r, l in culpables.items() if l} == {}


def test_f036_r59_el_detector_de_ficheros_de_disco_no_es_ciego():
    fuente = (
        "from openpyxl import load_workbook\n"
        "libro = load_workbook('plantilla.xlsx')\n"
        "otro = open(Path('x.xlsx'), 'rb')\n"
        "bien = load_workbook(io.BytesIO(b''))\n"
    )

    assert _abre_un_fichero_de_disco(fuente) == [2, 3]


# --------------------------------------------------------------------------
# §2.3 · lo que no se toca (y tienta): idéntico a `dev`
# --------------------------------------------------------------------------

#: Los ficheros de `design.md` §2.3, con su ruta de `git`, escritos a mano.
INTOCABLES = (
    # Las escrituras en el ERP y el SQL de F-013.
    f"{SERVICIO}infrastructure/sigrid/cliente.py",
    f"{SERVICIO}infrastructure/sigrid/escrituras.py",
    f"{SERVICIO}infrastructure/sigrid/graficos.py",
    f"{SERVICIO}infrastructure/sigrid/consultas_ubicacion.py",
    # La persistencia del circuito de partes (F-005…F-034).
    f"{SERVICIO}infrastructure/persistencia/sentencias.py",
    f"{SERVICIO}infrastructure/persistencia/repositorio_pg.py",
    # `RepositorioPartesPort`, `ErpPort`, `UbicacionPort`.
    f"{SERVICIO}domain/ports/persistencia.py",
    f"{SERVICIO}domain/ports/erp.py",
    f"{SERVICIO}domain/ports/ubicacion.py",
    # Los pasos del circuito de partes (F-002…F-034).
    f"{SERVICIO}application/pipelines/paso_archivo.py",
    f"{SERVICIO}application/pipelines/paso_cierre.py",
    f"{SERVICIO}application/pipelines/paso_extraccion.py",
    f"{SERVICIO}application/pipelines/paso_firma.py",
    f"{SERVICIO}application/pipelines/paso_grafico.py",
    f"{SERVICIO}application/pipelines/paso_ingesta.py",
    f"{SERVICIO}application/pipelines/paso_persistencia.py",
    f"{SERVICIO}application/pipelines/paso_troceado.py",
    f"{SERVICIO}application/pipelines/paso_validacion.py",
    # Y sus handlers.
    f"{SERVICIO}interface_adapters/api/adjuntar.py",
    f"{SERVICIO}interface_adapters/api/archivar.py",
    f"{SERVICIO}interface_adapters/api/cerrar.py",
    f"{SERVICIO}interface_adapters/api/cola.py",
    f"{SERVICIO}interface_adapters/api/cuerpos.py",
    f"{SERVICIO}interface_adapters/api/estado.py",
    f"{SERVICIO}interface_adapters/api/estado_serializado.py",
    f"{SERVICIO}interface_adapters/api/extraer.py",
    f"{SERVICIO}interface_adapters/api/firma.py",
    f"{SERVICIO}interface_adapters/api/health.py",
    f"{SERVICIO}interface_adapters/api/parte.py",
    f"{SERVICIO}interface_adapters/api/remesa.py",
    f"{SERVICIO}interface_adapters/api/split.py",
    f"{SERVICIO}interface_adapters/api/validar.py",
    # Las variables del despliegue (R49 también).
    "infra/00_vars_postventa.ps1",
)

#: El script común de lectura: tocado por T1 bis, solo dentro de una función.
LECTURA_COMUN = "infra/08_lectura_sigrid_comun.ps1"
FUNCION_TOCADA_EN_T1_BIS = "Invoke-SigridLectura"


def test_f036_s2_3_la_rama_no_toca_ningun_intocable():
    """§2.3 · ni una línea en los ficheros que tientan."""
    cambiados = _diff_de_la_rama_o_saltar()

    culpables = [ruta for ruta in cambiados if ruta in INTOCABLES]

    assert culpables == [], f"F-036 no toca esto (§2.3). Sobran: {culpables}"


def test_f036_s2_3_los_intocables_existen():
    """Una lista con una ruta mal escrita daría verde sin mirar nada."""
    faltan = [r for r in INTOCABLES if not (RAIZ / r).is_file()]

    assert faltan == []


def _sin_funcion_ps1(fuente: str, nombre: str) -> str:
    """El script sin la función `nombre` (de `function X {` a la `}` de columna 0)."""
    lineas = fuente.splitlines()
    inicio = lineas.index(f"function {nombre} {{")
    fin = lineas.index("}", inicio)
    return "\n".join(lineas[:inicio] + lineas[fin + 1 :])


def _funcion_ps1(fuente: str, nombre: str) -> str:
    lineas = fuente.splitlines()
    inicio = lineas.index(f"function {nombre} {{")
    return "\n".join(lineas[inicio : lineas.index("}", inicio) + 1])


def test_f036_s2_3_la_lectura_comun_solo_cambia_dentro_de_invoke_sigrid_lectura():
    """§2.3 con la desviación de T1 bis (B6-19): fuera de esa función, idéntico.

    `design.md` §2.3 dice «se usa tal cual»; R111 obligó a arreglar en él la
    decodificación de la respuesta de la pasarela. Lo demás —la clave, el
    destino, los parámetros, `Invoke-PythonDelServicio`, los veredictos— no se
    ha movido.
    """
    _diff_de_la_rama_o_saltar()
    antes = _fuente_en_la_base_de_la_rama(LECTURA_COMUN)
    ahora = (RAIZ / LECTURA_COMUN).read_text(encoding="utf-8")

    assert _sin_funcion_ps1(ahora, FUNCION_TOCADA_EN_T1_BIS) == _sin_funcion_ps1(
        antes, FUNCION_TOCADA_EN_T1_BIS
    )


def test_f036_s2_3_el_recorte_de_la_funcion_no_es_ciego():
    fuente = "a\nfunction F {\n  cuerpo\n}\nb\nfunction G {\n  otro\n}\n"

    assert _sin_funcion_ps1(fuente, "F") == "a\nb\nfunction G {\n  otro\n}"
    assert _sin_funcion_ps1(fuente, "F") != _sin_funcion_ps1(fuente, "G")


def test_f036_r46_la_lectura_comun_sigue_leyendo_solo_sql_read():
    """R46 · la mitad que no depende de `git` de la desviación: la función tocada.

    Tras T1 bis sigue llamando a `POST /api/sql/read` y a nada más.
    """
    fuente = (RAIZ / LECTURA_COMUN).read_text(encoding="utf-8")
    funcion = _ps1_sin_comentarios(_funcion_ps1(fuente, FUNCION_TOCADA_EN_T1_BIS))

    assert set(re.findall(r"\"(/api/[\w/\-]+)\"", funcion)) == {"/api/sql/read"}
    assert "-Method Post" in funcion
    for escritura in ESCRITURAS_EN_SIGRID:
        assert escritura not in _ps1_sin_comentarios(fuente)


#: Los métodos de los tres puertos que §2.3 cierra, escritos a mano.
METODOS_DE_LOS_PUERTOS = {
    ("domain/ports/persistencia.py", "RepositorioPartesPort"): (
        "guardar_remesa",
        "guardar_parte",
        "guardar_validacion",
        "guardar_archivo",
        "guardar_cierre",
        "guardar_grafico",
        "consultar_grafico",
        "consultar_situacion",
        "registrar_decision",
        "consultar_estado_cierre",
        "cola_validacion_humana",
    ),
    ("domain/ports/erp.py", "ErpPort"): (
        "leer_reclamacion",
        "existe_usuario",
        "cerrar",
    ),
    ("domain/ports/ubicacion.py", "UbicacionPort"): (
        "leer_ubicacion",
        "leer_unidades_del_numero",
    ),
}


@pytest.mark.parametrize(("fichero", "clase"), sorted(METODOS_DE_LOS_PUERTOS))
def test_f036_s2_3_los_puertos_del_circuito_no_ganan_ni_un_metodo(fichero, clase):
    """§2.3 · la mitad que no depende de `git`: «ni un método más»."""
    arbol = ast.parse((RAIZ_DEL_SERVICIO / fichero).read_text(encoding="utf-8"))
    (definicion,) = [
        n for n in arbol.body if isinstance(n, ast.ClassDef) and n.name == clase
    ]

    metodos = tuple(n.name for n in definicion.body if isinstance(n, ast.FunctionDef))

    assert metodos == METODOS_DE_LOS_PUERTOS[(fichero, clase)]


def test_f036_s2_3_ningun_commit_de_f035_ha_entrado_en_la_rama():
    """§2.3 · «la rama `feature/F-035-portal-posventa`: ni se mergea ni se toca».

    Los commits de F-035 que no están en `dev` no pueden estar en `HEAD`. Lo
    que F-035 ya tuviera en `dev` (su punto de pausa) no cuenta: eso lo trajo
    `dev`, no esta rama.
    """
    _diff_de_la_rama_o_saltar()
    existe = _git("rev-parse", "--verify", "--quiet", RAMA_DE_F035)
    if existe is None or existe.returncode != 0:  # pragma: no cover - otro clon
        pytest.skip(f"la rama {RAMA_DE_F035} no está en este clon")
    de_f035 = _git("rev-list", RAMA_DE_F035, "^dev")
    de_f036 = _git("rev-list", "HEAD", "^dev")
    assert de_f035 is not None and de_f036 is not None

    comunes = set(de_f035.stdout.split()) & set(de_f036.stdout.split())

    assert de_f036.stdout.split(), "la rama no tiene commits propios: no mira nada"
    assert comunes == set()
