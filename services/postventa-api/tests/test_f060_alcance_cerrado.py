# services/postventa-api/tests/test_f060_alcance_cerrado.py
"""Lo que F-060 promete **no** tocar, comprobado (T19; R36–R39, `design.md` §12).

F-060 normaliza las ubicaciones de la bandeja al texto exacto de Sigrid con
revisiones del sistema, y mide el listado. Escribe en su esquema propio, lee
Sigrid y roza código de F-036 y de F-056 (la importación, el listado, el
puerto de la revisión). Cada frontera tiene aquí su control:

| Frontera | Requisito | Qué se comprueba |
|---|---|---|
| Las respuestas de F-056 y de la importación | **R36** | las funciones que las construyen, iguales a las de la base; el listado, con las mismas claves |
| El DDL | **R37** | ningún `.sql` cambiado; el último sigue siendo el 15; nada de DDL, `UPDATE`, `DELETE` ni `TRUNCATE` en el código de F-060 |
| Sigrid y las ventanas de escritura | **R38** | ninguna línea añadida y ninguna pieza de F-060 nombra una ruta de escritura de la pasarela ni una ventana (`…_HABILITADO`); ninguna importa las escrituras del ERP; ninguna variable de entorno nueva |
| Los ficheros de «No se toca» | **§12** | sin cambios, ni el front, ni `infra/`, ni la plantilla |
| Los tests de F-036, F-056 y los que cuentan rutas | **R39** | solo los declarados, solo en sus funciones declaradas, y sin perder ninguna aserción salvo las declaradas |
| El resto del código tocado | §12 | en cada fichero, solo cambian o se añaden las piezas declaradas |

## Las excepciones declaradas a «sin tocar» (R39)

- `test_f056_repositorio_revision.py::test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5`
  pasa al conjunto exacto de **siete** operaciones (decisión del humano
  2026-10-10, Bloque 2).
- `test_f010_endpoints_protegidos.py`: la ruta `revision/normalizar` y la
  cuenta a **veintiuno** (T9).
- Por T20 —decisión del líder 2026-10-13, con el criterio que el humano
  aprobó en F-056: un test de documentación que fija una frase que cambia se
  amplía sin relajar y se declara—: `test_f053_documentacion.py`
  (`CUENTA_VIGENTE`, «Los veintiuno», y «Los veinte» en `not in`),
  `test_f012_documentacion.py` (`NUMERALES` hasta 21),
  `test_f019_documentacion.py::test_f019_r32_…` (la cuenta de veinte pasa de
  `in` a `not in` y se exige la de veintiuno) y `test_f056_documentacion.py`:
  `…_r44_la_seccion_ocho_dice_la_cuenta_y_las_ventanas` (la cuenta) y
  `…_r44_la_cabecera_dice_que_f056_lo_toco` (la cabecera pasa a F-060: el
  test deja de exigir que F-056 sea la **última** y exige una cabecera bien
  formada que no retroceda y en la que F-056 y su despliegue sigan constando,
  como hizo F-056 con el de F-036).

## Las dos mitades

Con el patrón de `test_f056_alcance_cerrado.py`: **el del diff**, contra la
**base fija** de la feature (`33d8938`; no `git merge-base`, que se movería si
`dev` avanzara) y hasta el **árbol de trabajo**, con las tres guardas de F-030
para no dejar `dev` en rojo cuando la rama se mergee; y **el que no depende de
`git`**, que se comprueba siempre.

**Sin red, sin base de datos, sin IA y sin reloj.** Los controles del diff
llaman a `git`, que es un proceso local de solo lectura.
"""

from __future__ import annotations

import ast
import re
import subprocess
from collections import Counter
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]
RAIZ_DEL_SERVICIO = RAIZ / "services" / "postventa-api"

#: La rama en la que los controles del diff tienen algo que mirar.
RAMA_DE_LA_FEATURE = "feature/F-060-normalizar-ubicaciones"

#: La base fija de la feature (`tasks.md`, cabecera; `progress/impl_F-060.md`).
BASE_FIJA = "33d8938"

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
    if _fuera_de_la_rama_de_la_feature() or (not cambiados and _la_rama_ya_esta_en_dev()):
        pytest.skip(
            f"este control vive en {RAMA_DE_LA_FEATURE} mientras no esté "
            "mergeada. Lo que no depende de 'git' se sigue comprobando en "
            "cualquier rama, en los tests hermanos de este"
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


# --------------------------------------------------------------------------
# El código, leído con `ast`
# --------------------------------------------------------------------------


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


def _definiciones(fuente: str) -> dict[str, str]:
    """Cada definición de nivel de módulo, sin docstrings, por nombre.

    Las funciones y las asignaciones, por su nombre; una clase, por su nombre
    **sin sus métodos** (sus campos y su cabecera) y cada método aparte, como
    `Clase.metodo`. Los `import` no cuentan: no responden ni escriben nada.
    """
    definiciones: dict[str, str] = {}
    for nodo in _sin_docstrings(ast.parse(fuente)).body:  # type: ignore[attr-defined]
        if isinstance(nodo, ast.FunctionDef | ast.AsyncFunctionDef):
            definiciones[nodo.name] = ast.unparse(nodo)
        elif isinstance(nodo, ast.ClassDef):
            metodos = [m for m in nodo.body if isinstance(m, ast.FunctionDef | ast.AsyncFunctionDef)]
            for metodo in metodos:
                definiciones[f"{nodo.name}.{metodo.name}"] = ast.unparse(metodo)
            nodo.body = [m for m in nodo.body if m not in metodos] or [ast.Pass()]
            definiciones[nodo.name] = ast.unparse(nodo)
        elif isinstance(nodo, ast.Assign | ast.AnnAssign):
            objetivos = nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]
            for objetivo in objetivos:
                if isinstance(objetivo, ast.Name):
                    definiciones[objetivo.id] = ast.unparse(nodo)
    return definiciones


def _actual(relativa: str) -> str:
    return (RAIZ_DEL_SERVICIO / relativa).read_text(encoding="utf-8")


def _codigo_que_se_ejecuta(relativa: str) -> str:
    """Un `.py` entero, sin docstrings ni comentarios."""
    return ast.unparse(_sin_docstrings(ast.parse(_actual(relativa))))


def _novedades(antes: str, ahora: str) -> set[str]:
    """Las definiciones que se añaden o cambian entre dos versiones de un fichero."""
    viejas, nuevas = _definiciones(antes), _definiciones(ahora)
    return {n for n, codigo in nuevas.items() if viejas.get(n) != codigo}


def _quitadas(antes: str, ahora: str) -> set[str]:
    return set(_definiciones(antes)) - set(_definiciones(ahora))


def _claves_de_diccionario(codigo: str) -> Counter[str]:
    """Las claves literales de todos los `{…}` de un código, con su multiplicidad."""
    claves: Counter[str] = Counter()
    for nodo in ast.walk(ast.parse(codigo)):
        if isinstance(nodo, ast.Dict):
            claves.update(
                k.value for k in nodo.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)
            )
    return claves


def _aserciones(fuente: str) -> dict[str, Counter[str]]:
    """Lo que comprueba cada aserción de cada función de test, por función.

    Sin el mensaje: el texto que acompaña a un fallo puede cambiar con la
    cuenta («Los veinte» → «Los veintiuno»); lo que se compara es lo que se
    exige.
    """
    return {
        nodo.name: Counter(
            ast.unparse(a.test) for a in ast.walk(nodo) if isinstance(a, ast.Assert)
        )
        for nodo in ast.parse(fuente).body
        if isinstance(nodo, ast.FunctionDef)
    }




# --------------------------------------------------------------------------
# El código de F-060, escrito a mano
# --------------------------------------------------------------------------

#: Los ficheros **nuevos** de producción de F-060 (`design.md` §12).
NUEVOS_DE_F060 = (
    "domain/models/normalizacion.py",
    "interface_adapters/api/normalizacion.py",
    "interface_adapters/api/tiempos.py",
)

#: Lo que F-060 añade o cambia en ficheros que ya existían, pieza a pieza.
#: `__all__` aparte: solo puede **ganar** nombres.
PIEZAS_DE_F060: dict[str, frozenset[str]] = {
    "application/pipelines/revision.py": frozenset(
        {"ResultadoNormalizacion", "normalizar_ubicaciones"}
    ),
    "domain/ports/revision.py": frozenset({"ResultadoDelLote", "RevisionPort.registrar_lote"}),
    "infrastructure/persistencia/repositorio_revision_pg.py": frozenset(
        {"RepositorioRevisionPostgres.registrar_lote", "RepositorioRevisionPostgres._registrar_lote"}
    ),
    # O-2 de la review del Bloque 4: la importación es código de F-060.
    "interface_adapters/api/importar.py": frozenset(
        {
            "importar_excel",
            "_registro_filas",
            "_normalizar_tras_importar",
            "_normalizar_de_verdad",
            "log",
        }
    ),
    # T18: solo `listar_revision` (la medición, §11.3).
    "interface_adapters/api/revision.py": frozenset({"listar_revision"}),
    "function_app.py": frozenset({"revision_normalizar"}),
}


def _pieza(relativa: str, nombre: str) -> str:
    definiciones = _definiciones(_actual(relativa))
    assert nombre in definiciones, f"{relativa} no define {nombre}"
    return definiciones[nombre]


def _todo_el_codigo_de_f060() -> dict[str, str]:
    """Cada pieza de F-060: los ficheros nuevos enteros y las piezas de §12.

    `importar.py`, **entero** (O-2 de la review del Bloque 4): desde F-060 la
    importación compone la normalización, así que lo que vigila R38 vale para
    todo el fichero.
    """
    piezas = {r: _codigo_que_se_ejecuta(r) for r in NUEVOS_DE_F060}
    piezas["interface_adapters/api/importar.py"] = _codigo_que_se_ejecuta(
        "interface_adapters/api/importar.py"
    )
    for relativa, nombres in PIEZAS_DE_F060.items():
        for nombre in sorted(nombres):
            piezas[f"{relativa}::{nombre}"] = _pieza(relativa, nombre)
    return piezas


def test_f060_el_control_del_diff_no_esta_mirando_una_lista_vacia():
    """Si el diff viniera vacío, los controles de abajo mentirían todos."""
    cambiados = _diff_de_la_rama_o_saltar()

    for relativa in (*NUEVOS_DE_F060, *PIEZAS_DE_F060):
        assert f"{SERVICIO}{relativa}" in cambiados, f"la rama tiene que haber tocado {relativa}"


def test_f060_las_piezas_de_f060_existen_todas():
    """Una lista con algo que no existe daría verde sin mirarlo."""
    assert [r for r in NUEVOS_DE_F060 if not (RAIZ_DEL_SERVICIO / r).is_file()] == []
    piezas = _todo_el_codigo_de_f060()
    assert len(piezas) == len(NUEVOS_DE_F060) + 1 + sum(len(n) for n in PIEZAS_DE_F060.values())
    assert all(codigo.strip() for codigo in piezas.values())


@pytest.mark.parametrize("relativa", sorted(PIEZAS_DE_F060))
def test_f060_s12_en_cada_fichero_tocado_solo_cambia_lo_declarado(relativa):
    """§12 · en cada fichero que ya existía, F-060 solo añade o cambia sus piezas.

    Y no quita ninguna definición: lo de F-036 y F-056 que no es de F-060 queda
    **igual que en la base**, función a función y método a método.
    """
    _diff_de_la_rama_o_saltar()
    antes = _en_la_base(f"{SERVICIO}{relativa}")
    ahora = _actual(relativa)

    assert _novedades(antes, ahora) - {"__all__"} == PIEZAS_DE_F060[relativa]
    assert _quitadas(antes, ahora) == set()


@pytest.mark.parametrize("relativa", sorted(PIEZAS_DE_F060))
def test_f060_s12_all_solo_gana_nombres(relativa):
    _diff_de_la_rama_o_saltar()
    exportados = {}
    for clave, fuente in (("antes", _en_la_base(f"{SERVICIO}{relativa}")), ("ahora", _actual(relativa))):
        definicion = _definiciones(fuente).get("__all__")
        exportados[clave] = set() if definicion is None else set(ast.literal_eval(definicion.split("=", 1)[1].strip()))

    assert exportados["antes"] <= exportados["ahora"]


# --------------------------------------------------------------------------
# R36 · las respuestas de F-056 y de la importación no cambian
# --------------------------------------------------------------------------

#: Las funciones que construyen o traducen las respuestas de
#: `GET /api/revision/historial`, `POST /api/revision/acciones`, la fila del
#: listado y `POST /api/importaciones`: tienen que ser las de la base.
RESPUESTAS_SIN_CAMBIOS = (
    ("interface_adapters/api/revision.py", "historial_revision"),
    ("interface_adapters/api/revision.py", "_con_sus_cambios"),
    ("interface_adapters/api/revision.py", "accion_de_revision"),
    ("interface_adapters/api/revision.py", "_fila_revisada"),
    ("interface_adapters/api/revision.py", "_fila"),
    ("interface_adapters/api/revision.py", "_valores_de"),
    ("interface_adapters/api/revision.py", "_oficios"),
    ("interface_adapters/api/revision.py", "_pares"),
    ("interface_adapters/api/revision.py", "cursor_de"),
    ("interface_adapters/api/revision.py", "_instante"),
    ("interface_adapters/api/revision.py", "_texto"),
    ("interface_adapters/api/importar.py", "serializar_importacion"),
    ("interface_adapters/api/importar.py", "_texto"),
    ("interface_adapters/api/importar.py", "_instante_utc"),
    ("function_app.py", "revision"),
    ("function_app.py", "revision_historial"),
    ("function_app.py", "revision_acciones"),
    ("function_app.py", "importaciones"),
    ("function_app.py", "_error_de_revision"),
    ("function_app.py", "_rechazo_de_obra"),
    ("function_app.py", "_sin_sigrid_o_sin_base"),
    ("function_app.py", "_json"),
)


@pytest.mark.parametrize(
    ("relativa", "nombre"), RESPUESTAS_SIN_CAMBIOS, ids=[f"{r}::{n}" for r, n in RESPUESTAS_SIN_CAMBIOS]
)
def test_f060_r36_las_funciones_que_responden_son_las_de_la_base(relativa, nombre):
    _diff_de_la_rama_o_saltar()
    antes = _definiciones(_en_la_base(f"{SERVICIO}{relativa}"))

    assert nombre in antes, f"la base no define {nombre}: la lista está mal"
    assert _pieza(relativa, nombre) == antes[nombre]


def test_f060_r36_el_listado_responde_con_las_mismas_claves_que_en_la_base():
    """`listar_revision` sí cambia (T18): las claves de su respuesta, no."""
    _diff_de_la_rama_o_saltar()
    relativa = "interface_adapters/api/revision.py"
    antes = _claves_de_diccionario(_definiciones(_en_la_base(f"{SERVICIO}{relativa}"))["listar_revision"])
    ahora = _claves_de_diccionario(_pieza(relativa, "listar_revision"))

    assert {"obra", "catalogo", "resumen", "filtros", "total_filtrado", "incidencias", "siguiente"} <= set(antes)
    assert ahora == antes


# --------------------------------------------------------------------------
# R37 · sin DDL
# --------------------------------------------------------------------------

_ESCRITURA_PROHIBIDA = re.compile(r"\bDELETE\b|\bTRUNCATE\b|(?<!FOR )\bUPDATE\b", re.IGNORECASE)
_DDL = re.compile(r"\b(CREATE|ALTER|DROP)\s+(TABLE|INDEX|SCHEMA|VIEW|FUNCTION)\b", re.IGNORECASE)

#: Los `.sql` del servicio, escritos a mano: F-060 no añade ninguno (D-4).
SQL_DE_LA_BASE = (
    "01_esquema.sql",
    "02_remesas.sql",
    "03_partes.sql",
    "04_validaciones.sql",
    "05_archivos.sql",
    "06_cierres.sql",
    "07_preferencias.sql",
    "08_usuarios_sigrid.sql",
    "09_graficos.sql",
    "10_aprobaciones.sql",
    "11_historico_estado.sql",
    "12_importaciones.sql",
    "13_bandeja_incidencias.sql",
    "14_decisiones_equivalencia.sql",
    "15_revisiones_bandeja.sql",
)


def test_f060_r37_la_rama_no_toca_ningun_sql():
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if r.endswith(".sql")] == []


def test_f060_r37_los_sql_son_los_quince_de_antes():
    """La mitad que no depende de `git`: ni un `16_…sql`."""
    carpeta = RAIZ_DEL_SERVICIO / "infrastructure" / "persistencia" / "sql"

    assert tuple(sorted(f.name for f in carpeta.glob("*.sql"))) == SQL_DE_LA_BASE


def test_f060_r37_el_codigo_de_f060_no_tiene_ddl_ni_actualiza_ni_borra():
    """R15, R37 · ningún DDL, `UPDATE`, `DELETE` ni `TRUNCATE` (el `FOR UPDATE` no lo es)."""
    culpables = {
        pieza: sorted(set(_DDL.findall(codigo)) | set(_ESCRITURA_PROHIBIDA.findall(codigo)))
        for pieza, codigo in _todo_el_codigo_de_f060().items()
        if _DDL.search(codigo) or _ESCRITURA_PROHIBIDA.search(codigo)
    }

    assert culpables == {}


def test_f060_r37_los_detectores_de_ddl_y_escrituras_no_son_ciegos():
    assert _ESCRITURA_PROHIBIDA.search("UPDATE postventa.revisiones_bandeja SET")
    assert _ESCRITURA_PROHIBIDA.search("delete from postventa.bandeja_incidencias")
    assert _ESCRITURA_PROHIBIDA.search("TRUNCATE postventa.revisiones_bandeja")
    assert not _ESCRITURA_PROHIBIDA.search("ORDER BY incidencia_id FOR UPDATE")
    assert _DDL.search("ALTER TABLE postventa.revisiones_bandeja ADD COLUMN x text")
    assert _DDL.search("create index ix on postventa.x (y)")
    assert not _DDL.search("una tabla creada por el DDL")


# --------------------------------------------------------------------------
# R38 · nada en Sigrid y ninguna ventana de escritura
# --------------------------------------------------------------------------

#: Las rutas de escritura de `sigrid-api` (`azure-apps/sigrid_api.md`).
ESCRITURAS_EN_SIGRID = ("sql/write", "sigrid/partes-reclamacion", "sigrid/concepto-grafico")

#: Los módulos del servicio que escriben en el ERP: F-060 no los importa.
MODULOS_QUE_ESCRIBEN_EN_SIGRID = ("infrastructure.sigrid.escrituras", "infrastructure.sigrid.graficos")

#: Carpetas del árbol que **no** son código: las nombran para prohibirlas.
CARPETAS_QUE_NO_SON_CODIGO = {"tests", "tests_js", "tests_bbdd", ".venv", "__pycache__"}

#: Las ventanas de escritura (`CIERRE_HABILITADO`, `ARCHIVO_HABILITADO`, y la
#: de F-059, `VOLCADO_HABILITADO`) y sus campos de `Ajustes`: todas llevan esto.
VENTANA = re.compile(r"habilitado", re.IGNORECASE)

FICHEROS_DE_CONFIGURACION = (
    f"{SERVICIO}config/settings.py",
    f"{SERVICIO}.env.example",
    f"{SERVICIO}local.settings.json.example",
    "infra/00_vars_postventa.ps1",
)


def _es_codigo(ruta: str) -> bool:
    """¿Es código que se ejecuta (servicios o `infra/`), y no una suite?"""
    if not ruta.startswith(("services/", "infra/")):
        return False
    return not CARPETAS_QUE_NO_SON_CODIGO.intersection(ruta.split("/"))


def _nombra_lo_prohibido(texto: str) -> list[str]:
    return [e for e in ESCRITURAS_EN_SIGRID if e in texto] + VENTANA.findall(texto)


def test_f060_r38_ninguna_linea_anadida_al_codigo_nombra_una_escritura_ni_una_ventana():
    """R38 · la mitad del diff: cada línea añadida al código, en cualquier fichero."""
    cambiados = _diff_de_la_rama_o_saltar()
    codigo = [ruta for ruta in cambiados if _es_codigo(ruta)]
    assert codigo, "la rama no ha tocado código: el control no mira nada"

    anadidas = _lineas_anadidas(codigo)

    assert anadidas
    assert [linea for linea in anadidas if _nombra_lo_prohibido(linea)] == []


def test_f060_r38_el_codigo_de_f060_no_nombra_escrituras_ni_ventanas():
    """R38 · la mitad que no depende de `git`."""
    culpables = {
        pieza: _nombra_lo_prohibido(codigo)
        for pieza, codigo in _todo_el_codigo_de_f060().items()
        if _nombra_lo_prohibido(codigo)
    }

    assert culpables == {}


def test_f060_r38_el_detector_de_escrituras_y_ventanas_no_es_ciego():
    assert _nombra_lo_prohibido('cliente.post("sql/write", lote)') == ["sql/write"]
    assert _nombra_lo_prohibido("if ajustes.cierre_habilitado:") == ["habilitado"]
    assert _nombra_lo_prohibido("VOLCADO_HABILITADO") == ["HABILITADO"]
    assert _nombra_lo_prohibido('cliente.post("sql/read", consulta)') == []
    assert _es_codigo(f"{SERVICIO}interface_adapters/api/tiempos.py")
    assert not _es_codigo(f"{SERVICIO}tests/test_f060_alcance_cerrado.py")
    assert not _es_codigo(f"{SERVICIO}tests_bbdd/tests/test_f060_bbdd_lote.py")


def _modulos_importados(relativa: str) -> set[str]:
    importados: set[str] = set()
    for nodo in ast.walk(ast.parse(_actual(relativa))):
        if isinstance(nodo, ast.Import):
            importados.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module)
            importados.update(f"{nodo.module}.{alias.name}" for alias in nodo.names)
    return importados


def test_f060_r38_ningun_modulo_de_f060_importa_las_escrituras_del_erp():
    culpables = {
        r: sorted(m for m in _modulos_importados(r) if m.startswith(MODULOS_QUE_ESCRIBEN_EN_SIGRID))
        for r in (*NUEVOS_DE_F060, *PIEZAS_DE_F060)
    }

    assert {r: m for r, m in culpables.items() if m} == {}


def test_f060_r38_el_detector_de_importaciones_ve_lo_que_hay():
    importados = _modulos_importados("interface_adapters/api/normalizacion.py")

    assert "infrastructure.sigrid.fabrica.construir_catalogo_obra" in importados
    assert "interface_adapters.api.revision.construir_fuente_de_ubicaciones" in importados


def test_f060_r38_la_rama_no_toca_la_configuracion_del_entorno():
    """Ninguna variable de entorno nueva ni ninguna ventana nueva."""
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if r in FICHEROS_DE_CONFIGURACION] == []
    assert not any(r.endswith((".env", "local.settings.json")) for r in cambiados)


def test_f060_r38_el_codigo_de_f060_no_lee_el_entorno_por_su_cuenta():
    culpables = sorted(
        p for p, codigo in _todo_el_codigo_de_f060().items() if re.search(r"\benviron\b|\bgetenv\b", codigo)
    )

    assert culpables == []


# --------------------------------------------------------------------------
# §12 · lo que no se toca
# --------------------------------------------------------------------------

#: Los ficheros de «No se toca» de `design.md` §12, con su ruta de `git`
#: (los `.sql` y `infrastructure/sigrid/*`, en sus propios controles).
INTOCABLES = tuple(
    f"{SERVICIO}{r}"
    for r in (
        "domain/models/revision.py",
        "domain/models/importacion.py",
        "domain/models/plantilla_incidencias.py",
        "domain/models/equivalencias.py",
        "infrastructure/persistencia/sentencias_revision.py",
        "infrastructure/persistencia/sentencias_bandeja.py",
        "infrastructure/persistencia/repositorio_bandeja_pg.py",
        "infrastructure/persistencia/fabrica.py",
        "application/pipelines/paso_importacion.py",
        "application/pipelines/catalogo_obra.py",
        "application/pipelines/plantilla.py",
        "application/pipelines/equivalencias.py",
        "config/plantilla_incidencias.yaml",
        "interface_adapters/api/bandeja.py",
        "interface_adapters/api/plantilla.py",
        "interface_adapters/api/equivalencias.py",
    )
)

#: Carpetas enteras que F-060 no toca: Sigrid (§12), el front (F-038), `infra/`
#: (salvo M-4, Bloque 7) y los documentos, que generan la plantilla (F-058).
CARPETAS_INTOCABLES = (
    f"{SERVICIO}infrastructure/sigrid/",
    f"{SERVICIO}infrastructure/documentos/",
    "services/postventa-front/",
    "infra/",
)


def test_f060_s12_los_intocables_existen():
    assert [r for r in INTOCABLES if not (RAIZ / r).is_file()] == []
    assert [c for c in CARPETAS_INTOCABLES if not (RAIZ / c).is_dir()] == []


def test_f060_s12_la_rama_no_toca_ningun_intocable():
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if r in INTOCABLES] == []


def test_f060_s12_ni_sigrid_ni_la_plantilla_ni_el_front_ni_infra():
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if r.startswith(CARPETAS_INTOCABLES)] == []


# --------------------------------------------------------------------------
# R39 · los tests de F-036 y F-056, y los que cuentan rutas
# --------------------------------------------------------------------------

#: Los tests de otras features que la rama toca, cada uno con las funciones
#: (o constantes) que cambian, y nada más. Ver la cabecera de este fichero.
AMPLIADOS: dict[str, frozenset[str]] = {
    # Decisión del humano 2026-10-10 (Bloque 2): siete operaciones.
    "tests/test_f056_repositorio_revision.py": frozenset(
        {"test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5"}
    ),
    # T9: la ruta nueva y la cuenta a veintiuno.
    "tests/test_f010_endpoints_protegidos.py": frozenset(
        {"ENDPOINTS", "test_f010_r32_el_barrido_de_niveles_ve_lo_que_hay"}
    ),
    # T20: «Los veintiuno» (decisión del líder 2026-10-13).
    "tests/test_f053_documentacion.py": frozenset(
        {"CUENTA_VIGENTE", "test_f053_t6_el_parrafo_va_antes_de_los_diecisiete_y_sin_encabezado"}
    ),
    "tests/test_f012_documentacion.py": frozenset({"NUMERALES"}),
    "tests/test_f019_documentacion.py": frozenset(
        {"test_f019_r32_la_seccion_ocho_ya_habla_de_todos_los_endpoints"}
    ),
    "tests/test_f056_documentacion.py": frozenset(
        {
            "test_f056_r44_la_seccion_ocho_dice_la_cuenta_y_las_ventanas",
            "test_f056_r44_la_cabecera_dice_que_f056_lo_toco",
        }
    ),
}

#: Las aserciones que una ampliación **cambia** (no las que añade): la cuenta
#: de veinte a veintiuno, la lista de seis a siete y la cabecera, que deja de
#: exigir que F-056 sea la última feature. Todas las demás de la base siguen.
ASERCIONES_QUE_CAMBIAN: dict[str, frozenset[str]] = {
    "tests/test_f010_endpoints_protegidos.py": frozenset(
        {"test_f010_r32_el_barrido_de_niveles_ve_lo_que_hay"}
    ),
    "tests/test_f056_repositorio_revision.py": frozenset(
        {"test_f056_r34_el_puerto_tiene_las_seis_operaciones_de_5"}
    ),
    "tests/test_f019_documentacion.py": frozenset(
        {"test_f019_r32_la_seccion_ocho_ya_habla_de_todos_los_endpoints"}
    ),
    "tests/test_f056_documentacion.py": frozenset(
        {"test_f056_r44_la_cabecera_dice_que_f056_lo_toco"}
    ),
}

#: Los tests propios de F-060 y sus dobles.
_DE_F060 = re.compile(r"/tests(_bbdd/tests)?/(test_f060_|utiles_normalizacion\.py)")


def test_f060_r39_la_rama_solo_toca_los_tests_declarados():
    """Fuera de los de F-060, solo los ampliados; ninguno más de ninguna feature."""
    cambiados = _diff_de_la_rama_o_saltar()

    tocados = sorted(
        r.removeprefix(SERVICIO)
        for r in cambiados
        if re.search(r"/tests(_bbdd/tests)?/", r) and not _DE_F060.search(r)
    )

    assert tocados == sorted(AMPLIADOS)


def test_f060_r39_los_de_f036_y_f056_que_toca_son_solo_los_declarados():
    cambiados = _diff_de_la_rama_o_saltar()

    tocados = sorted(
        r.removeprefix(SERVICIO) for r in cambiados if re.search(r"/tests(_bbdd/tests)?/test_f0(36|56)_", r)
    )

    assert tocados == ["tests/test_f056_documentacion.py", "tests/test_f056_repositorio_revision.py"]


@pytest.mark.parametrize("relativa", sorted(AMPLIADOS))
def test_f060_r39_en_cada_ampliado_solo_cambia_lo_declarado(relativa):
    _diff_de_la_rama_o_saltar()
    antes = _en_la_base(f"{SERVICIO}{relativa}")
    ahora = _actual(relativa)

    assert _quitadas(antes, ahora) == set(), "un test ampliado no pierde nada"
    assert _novedades(antes, ahora) == AMPLIADOS[relativa]


@pytest.mark.parametrize("relativa", sorted(AMPLIADOS))
def test_f060_r39_ningun_ampliado_pierde_una_asercion(relativa):
    """Sin relajar: cada aserción de la base sigue, salvo las que cambian por declaración."""
    _diff_de_la_rama_o_saltar()
    antes = _aserciones(_en_la_base(f"{SERVICIO}{relativa}"))
    ahora = _aserciones(_actual(relativa))
    exentas = ASERCIONES_QUE_CAMBIAN.get(relativa, frozenset())

    perdidas = {
        funcion: sorted((aserciones - ahora.get(funcion, Counter())).elements())
        for funcion, aserciones in antes.items()
        if funcion not in exentas and aserciones - ahora.get(funcion, Counter())
    }

    assert perdidas == {}


def test_f060_r39_los_controles_de_los_tests_no_son_ciegos():
    """Control negativo de `_novedades`, `_quitadas` y `_aserciones`."""
    antes = 'X = 1\n\ndef test_a():\n    """Doc."""\n    assert 1 == 1\n    assert 2 == 2\n\ndef test_b():\n    assert 3\n'
    solo_docstring = antes.replace('"""Doc."""', '"""Otra doc."""')
    pierde = antes.replace("    assert 2 == 2\n", "")
    cambia_constante = antes.replace("X = 1", "X = 2")
    sin_b = antes.split("\ndef test_b")[0]

    assert _novedades(antes, solo_docstring) == set()
    assert _novedades(antes, pierde) == {"test_a"}
    assert _novedades(antes, cambia_constante) == {"X"}
    assert _quitadas(antes, sin_b) == {"test_b"}
    assert _aserciones(antes)["test_a"] - _aserciones(pierde)["test_a"] == Counter({"2 == 2": 1})
    assert _aserciones(antes) == {"test_a": Counter({"1 == 1": 1, "2 == 2": 1}), "test_b": Counter({"3": 1})}
    # El mensaje de una aserción puede cambiar; lo que comprueba, no.
    con_mensaje = antes.replace("assert 3\n", 'assert 3, "otro mensaje"\n')
    assert _aserciones(con_mensaje) == _aserciones(antes)


def test_f060_s12_los_controles_del_codigo_no_son_ciegos():
    """`_definiciones` ve los métodos de una clase; `_claves_de_diccionario`, las claves."""
    fuente = 'class P:\n    """Doc."""\n    campo: int\n\n    def m(self):\n        return {"a": 1, "b": {"c": 2}}\n'

    definiciones = _definiciones(fuente)

    assert set(definiciones) == {"P", "P.m"}
    assert "def m" not in definiciones["P"]
    assert _novedades(fuente, fuente.replace('"a"', '"z"')) == {"P.m"}
    assert _claves_de_diccionario(definiciones["P.m"]) == Counter({"a": 1, "b": 1, "c": 1})
