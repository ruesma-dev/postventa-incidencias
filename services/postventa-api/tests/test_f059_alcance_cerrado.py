# services/postventa-api/tests/test_f059_alcance_cerrado.py
"""Lo que F-059 promete **no** tocar, comprobado (T16; R36, R37, R41, `design.md` §17, §21).

F-059 **escribe en el ERP de producción** (crea partes de reclamación con
`POST /api/sigrid/partes-reclamacion`), escribe en su esquema propio y roza
código de F-009, de F-056 y de F-060. Cada frontera tiene aquí su control:

| Frontera | Requisito | Qué se comprueba |
|---|---|---|
| Las rutas de `sigrid-api` | **R36** | el código de F-059 solo nombra `sql/read` y `partes-reclamacion`; ninguna línea añadida nombra `sql/write`; la ruta de `partes-reclamacion` vive **solo** en `infrastructure/sigrid/volcado.py`; ningún módulo de F-059 importa las escrituras ni el gráfico |
| La ventana | **R37**, **R42** | `VOLCADO_HABILITADO` solo en los ajustes y en `construir_volcador`; ni el cierre, ni el gráfico, ni el archivo la miran; el volcado no mira `CIERRE_HABILITADO` ni `ARCHIVO_HABILITADO` |
| La escritura | **O-B3-3** | solo `infrastructure/sigrid/fabrica.py` construye `AdaptadorVolcadoSigridApi`, y solo `construir_volcador` lo pide con `escritura_habilitada=True` |
| El SQL | **R32**, **R33** | un `.sql` nuevo, el `16_`; ni DDL fuera de él ni `UPDATE`/`DELETE`/`TRUNCATE` en el código de F-059 |
| Los tests de otras features | **R41** (F-1 (a)) | los de F-009 sin diff; los de la lista de excepciones de `design.md` §21.3, **solo** en las funciones declaradas aquí a mano, y **sin perder ninguna aserción** salvo las declaradas |
| El código tocado de F-009, F-056 y F-060 | §12, §17 | en cada fichero que ya existía, solo cambian o se añaden las piezas declaradas; `paso_cierre.py`, solo la anotación de `erp`; los ejemplos de entorno, solo las dos variables |
| Lo de «No se toca» | §17, §21.5 | sin cambios: `services/postventa-front/` entero, las piezas de F-060 y lo demás de la lista |

## Las dos mitades

Con el patrón de `test_f060_alcance_cerrado.py`: **el del diff**, contra la
**base fija** de la feature (`2d2efd7`; no `git merge-base`, que se movería si
`dev` avanzara) y hasta el **árbol de trabajo**, con las tres guardas de F-030
para no dejar `dev` en rojo cuando la rama se mergee (sin `git` o sin la base
en el clon, fuera de la rama de la feature, o ya mergeada y sin diff → se
salta); y **el que no depende de `git`**, que se comprueba siempre.

## Las excepciones de R41 (F-1 (a), decisión del humano del 2026-10-15)

Escritas a mano, función a función, en `AMPLIADOS` (la lista de `design.md`
§21.3, más el `test_f056_r12_la_unica_columna_…` de B-2). Las del grupo B que
cambian los documentos (T20, Bloque 5) estuvieron declaradas hasta T20 en
`AMPLIADOS_EN_EL_BLOQUE_5`, donde solo se exigía que **no cambiara nada
más** que lo declarado; T20 las pasó a igualdad, declaró las aserciones que
cambian en `ASERCIONES_QUE_CAMBIAN`, una a una (desde C-B4-1, la aserción y no
la función), y ese conjunto queda **vacío**, y así se exige (O-B4-3).

**Sin red, sin base de datos, sin IA y sin reloj.** Los controles del diff
llaman a `git`, que es un proceso local de solo lectura.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]
RAIZ_DEL_SERVICIO = RAIZ / "services" / "postventa-api"

#: La rama en la que los controles del diff tienen algo que mirar.
RAMA_DE_LA_FEATURE = "feature/F-059-volcado-sigrid-backend"

#: La base fija de la feature (`tasks.md`, cabecera; `progress/impl_F-059.md`).
BASE_FIJA = "2d2efd7"

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
    **sin sus métodos** y cada método aparte, como `Clase.metodo`. Los
    `import` no cuentan: no responden ni escriben nada.
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
    """Un `.py` sin docstrings ni comentarios; el SQL, sin sus comentarios `--`."""
    fuente = _actual(relativa)
    if relativa.endswith(".sql"):
        return "\n".join(linea.split("--")[0] for linea in fuente.splitlines())
    return ast.unparse(_sin_docstrings(ast.parse(fuente)))


def _novedades(antes: str, ahora: str) -> set[str]:
    """Las definiciones que se añaden o cambian entre dos versiones de un fichero."""
    viejas, nuevas = _definiciones(antes), _definiciones(ahora)
    return {n for n, codigo in nuevas.items() if viejas.get(n) != codigo}


def _quitadas(antes: str, ahora: str) -> set[str]:
    return set(_definiciones(antes)) - set(_definiciones(ahora))


def _aserciones(fuente: str) -> dict[str, Counter[str]]:
    """Lo que comprueba cada aserción de cada función de test, por función."""
    return {
        nodo.name: Counter(ast.unparse(a.test) for a in ast.walk(nodo) if isinstance(a, ast.Assert))
        for nodo in ast.parse(fuente).body
        if isinstance(nodo, ast.FunctionDef)
    }


def _modulos_importados(relativa: str, fuente: str | None = None) -> set[str]:
    importados: set[str] = set()
    for nodo in ast.walk(ast.parse(_actual(relativa) if fuente is None else fuente)):
        if isinstance(nodo, ast.Import):
            importados.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module)
            importados.update(f"{nodo.module}.{alias.name}" for alias in nodo.names)
    return importados


#: Lo que se despliega del servicio: `function_app.py` y sus cinco capas (ni
#: las suites, ni `scripts/`, que son herramientas de puesto, ni `.venv`).
CARPETAS_DE_CODIGO = ("application", "config", "domain", "infrastructure", "interface_adapters")


def _codigo_del_servicio() -> dict[str, str]:
    """Todo el `.py` de producción del servicio, sin docstrings ni comentarios."""
    rutas = [RAIZ_DEL_SERVICIO / "function_app.py"]
    for carpeta in CARPETAS_DE_CODIGO:
        rutas.extend((RAIZ_DEL_SERVICIO / carpeta).rglob("*.py"))
    return {
        relativa: _codigo_que_se_ejecuta(relativa)
        for relativa in sorted(r.relative_to(RAIZ_DEL_SERVICIO).as_posix() for r in rutas)
        if "__pycache__" not in relativa
    }


# --------------------------------------------------------------------------
# El código de F-059, escrito a mano
# --------------------------------------------------------------------------

#: Los ficheros **nuevos** de producción de F-059 (`design.md` §17).
NUEVOS_DE_F059 = (
    "domain/models/situacion_volcado.py",
    "domain/models/volcado.py",
    "domain/ports/volcado.py",
    "application/pipelines/volcado.py",
    "infrastructure/persistencia/sql/16_volcados_sigrid.sql",
    "infrastructure/persistencia/sentencias_volcado.py",
    "infrastructure/persistencia/repositorio_volcado_pg.py",
    "infrastructure/sigrid/volcado.py",
    "interface_adapters/api/volcado.py",
)

#: Lo que F-059 añade o cambia en ficheros que ya existían, pieza a pieza
#: (`design.md` §12 y §17). `__all__` aparte: solo puede **ganar** nombres.
PIEZAS_DE_F059: dict[str, frozenset[str]] = {
    # §8.4: solo la anotación de `erp` (lo comprueba su propio test).
    "application/pipelines/paso_cierre.py": frozenset({"resolver_login_de_sigrid"}),
    # §13: los dos campos (lo comprueba su propio test).
    "config/settings.py": frozenset({"Ajustes"}),
    # §7: los ocho errores.
    "domain/models/errores.py": frozenset(
        {
            f"{error}{metodo}"
            for error in (
                "CuerpoDeVolcadoInvalido",
                "VolcadoDeshabilitado",
                "ConfiguracionDeVolcadoInvalida",
                "EnsayoNoValido",
                "VolcadoRechazadoPorLaPasarela",
                "EnsayoSinRespuesta",
                "VolcadoSinRespuesta",
                "VolcadoSinTraza",
            )
            for metodo in ("", ".__init__")
        }
    ),
    # §12: los seis estados, las acciones, `volcado` en la situación.
    "domain/models/revision.py": frozenset(
        {
            "EstadoRevision",
            "FiltroEstado",
            "SituacionDeRevision",
            "_CANDIDATOS",
            "_FUERA_DE_ACTIVAS",
            "_PERMITIDAS",
            "_pasa",
            "es_candidata",
            "estado_de",
        }
    ),
    # §8.4: el protocolo del login.
    "domain/ports/usuarios_sigrid.py": frozenset(
        {"VerificadorDeLoginPort", "VerificadorDeLoginPort.existe_usuario"}
    ),
    # §11: las tres rutas y su traducción propia; `_error_de_revision` no cambia.
    "function_app.py": frozenset(
        {
            "CODIGOS_DEL_VOLCADO",
            "HTTP_DEL_VOLCADO",
            "MENSAJES_DEL_LOGIN",
            "ERRORES_DEL_VOLCADO",
            "_error_del_volcado",
            "_cuerpo_del_volcado_no_es_json",
            "volcado",
            "volcado_ensayo",
            "volcado_volcar",
        }
    ),
    # §8.3: `construir_volcados`.
    "infrastructure/persistencia/fabrica.py": frozenset({"construir_volcados"}),
    # §12: R2 en `_registrar` y `aprobadas` sin la `volcada` (O-B2-1).
    "infrastructure/persistencia/repositorio_revision_pg.py": frozenset(
        {
            "_BLOQUEAN_LA_REVISION",
            "RepositorioRevisionPostgres._registrar",
            "RepositorioRevisionPostgres._exigir_que_no_este_volcada",
            "RepositorioRevisionPostgres.aprobadas",
        }
    ),
    # §12: las dos `LATERAL` y `fila_a_situacion`.
    "infrastructure/persistencia/sentencias_revision.py": frozenset(
        {"_SIN_EVENTOS", "_select_situaciones", "fila_a_situacion"}
    ),
    # §8.3: las dos fábricas, **añadidas**.
    "infrastructure/sigrid/fabrica.py": frozenset(
        {"construir_ensayador", "construir_volcador", "_adaptador_de_volcado"}
    ),
    # §12: `_fila` (el objeto `volcado`, F-2 (a)) y `_filtro`.
    "interface_adapters/api/revision.py": frozenset({"_fila", "_filtro"}),
}


def _pieza(relativa: str, nombre: str) -> str:
    definiciones = _definiciones(_actual(relativa))
    assert nombre in definiciones, f"{relativa} no define {nombre}"
    return definiciones[nombre]


#: Los dos campos de `Ajustes` que son de F-059 (§13): la clase entera tiene
#: los de las demás ventanas, que no son suyos.
CAMPOS_DE_F059 = ("volcado_habilitado", "volcado_partes_por_llamada")


def _todo_el_codigo_de_f059() -> dict[str, str]:
    """Cada pieza de F-059: los ficheros nuevos enteros y las piezas declaradas.

    De `Ajustes`, solo sus dos campos.
    """
    piezas = {r: _codigo_que_se_ejecuta(r) for r in NUEVOS_DE_F059}
    for relativa, nombres in PIEZAS_DE_F059.items():
        for nombre in sorted(nombres):
            piezas[f"{relativa}::{nombre}"] = _pieza(relativa, nombre)
    campos = _clase_ajustes(_actual("config/settings.py"))
    piezas["config/settings.py::Ajustes"] = "\n".join(campos[c] for c in CAMPOS_DE_F059)
    return piezas


def test_f059_el_control_del_diff_no_esta_mirando_una_lista_vacia():
    """Si el diff viniera vacío, los controles de abajo mentirían todos."""
    cambiados = _diff_de_la_rama_o_saltar()

    for relativa in (*NUEVOS_DE_F059, *PIEZAS_DE_F059):
        assert f"{SERVICIO}{relativa}" in cambiados, f"la rama tiene que haber tocado {relativa}"


def test_f059_las_piezas_de_f059_existen_todas():
    """Una lista con algo que no existe daría verde sin mirarlo."""
    assert [r for r in NUEVOS_DE_F059 if not (RAIZ_DEL_SERVICIO / r).is_file()] == []
    piezas = _todo_el_codigo_de_f059()
    assert len(piezas) == len(NUEVOS_DE_F059) + sum(len(n) for n in PIEZAS_DE_F059.values())
    assert all(codigo.strip() for codigo in piezas.values())


@pytest.mark.parametrize("relativa", sorted(PIEZAS_DE_F059))
def test_f059_s12_en_cada_fichero_tocado_solo_cambia_lo_declarado(relativa):
    """§12, §17 · en cada fichero que ya existía, F-059 solo añade o cambia sus piezas.

    Y no quita ninguna definición: lo de F-009, F-036, F-056 y F-060 que no es
    de F-059 queda **igual que en la base**, función a función y método a
    método.
    """
    _diff_de_la_rama_o_saltar()
    antes = _en_la_base(f"{SERVICIO}{relativa}")
    ahora = _actual(relativa)

    assert _novedades(antes, ahora) - {"__all__"} == PIEZAS_DE_F059[relativa]
    assert _quitadas(antes, ahora) == set()


@pytest.mark.parametrize("relativa", sorted(PIEZAS_DE_F059))
def test_f059_s12_all_solo_gana_nombres(relativa):
    _diff_de_la_rama_o_saltar()
    exportados = {}
    for clave, fuente in (("antes", _en_la_base(f"{SERVICIO}{relativa}")), ("ahora", _actual(relativa))):
        definicion = _definiciones(fuente).get("__all__")
        exportados[clave] = (
            set() if definicion is None else set(ast.literal_eval(definicion.split("=", 1)[1].strip()))
        )

    assert exportados["antes"] <= exportados["ahora"]


def test_f059_s84_paso_cierre_solo_cambia_la_anotacion_de_erp():
    """§8.4, R41 · ni una línea de lógica de `paso_cierre.py` cambia."""
    _diff_de_la_rama_o_saltar()
    relativa = "application/pipelines/paso_cierre.py"
    antes = _definiciones(_en_la_base(f"{SERVICIO}{relativa}"))["resolver_login_de_sigrid"]
    ahora = _pieza(relativa, "resolver_login_de_sigrid")

    assert "erp: ErpPort" in antes
    assert ahora == antes.replace("erp: ErpPort", "erp: VerificadorDeLoginPort")


def _clase_ajustes(fuente: str) -> dict[str, str]:
    """Los campos de `Ajustes`, por nombre."""
    for nodo in _sin_docstrings(ast.parse(fuente)).body:  # type: ignore[attr-defined]
        if isinstance(nodo, ast.ClassDef) and nodo.name == "Ajustes":
            return {
                s.target.id: ast.unparse(s)
                for s in nodo.body
                if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)
            }
    raise AssertionError("no hay Ajustes")


def test_f059_s13_los_ajustes_solo_ganan_los_dos_campos_del_volcado():
    """§13 · `volcado_habilitado` y `volcado_partes_por_llamada`, y nada más cambia."""
    _diff_de_la_rama_o_saltar()
    relativa = "config/settings.py"
    antes = _clase_ajustes(_en_la_base(f"{SERVICIO}{relativa}"))
    ahora = _clase_ajustes(_actual(relativa))

    assert set(ahora) - set(antes) == {"volcado_habilitado", "volcado_partes_por_llamada"}
    assert {k: ahora[k] for k in antes} == antes


def _variables_del_env(texto: str) -> dict[str, str]:
    return dict(
        linea.split("=", 1)
        for linea in texto.splitlines()
        if linea.strip() and not linea.lstrip().startswith("#") and "=" in linea
    )


def test_f059_s17_los_ejemplos_de_entorno_solo_ganan_las_dos_variables():
    """§17 · los dos nombres, con su placeholder, y nada más cambia."""
    _diff_de_la_rama_o_saltar()
    env_antes = _variables_del_env(_en_la_base(f"{SERVICIO}.env.example"))
    env_ahora = _variables_del_env(_actual(".env.example"))
    json_antes = json.loads(_en_la_base(f"{SERVICIO}local.settings.json.example"))
    json_ahora = json.loads(_actual("local.settings.json.example"))
    nuevas = {"VOLCADO_HABILITADO": "false", "VOLCADO_PARTES_POR_LLAMADA": "5"}

    assert env_ahora == {**env_antes, **nuevas}
    assert set(env_antes).isdisjoint(nuevas)
    assert json_ahora == {**json_antes, "Values": {**json_antes["Values"], **nuevas}}


# --------------------------------------------------------------------------
# R36 · las rutas de `sigrid-api`
# --------------------------------------------------------------------------

#: Las únicas rutas de `sigrid-api` que nombra F-059 (R36).
RUTAS_PERMITIDAS = {"/api/sql/read", "/api/sigrid/partes-reclamacion"}

#: Las rutas de escritura de `sigrid-api` que **no** son la de F-059.
OTRAS_ESCRITURAS = ("sql/write", "sigrid/concepto-grafico")

#: Los módulos del servicio que escriben en el ERP por otro camino.
MODULOS_QUE_ESCRIBEN_EN_SIGRID = ("infrastructure.sigrid.escrituras", "infrastructure.sigrid.graficos")

#: Las carpetas que no son código, para el control del diff.
_NO_CODIGO = {"tests", "tests_js", "tests_bbdd", ".venv", "__pycache__"}

_RUTA_DE_LA_PASARELA = re.compile(r"/api/[a-z_/-]+")


def _es_codigo(ruta: str) -> bool:
    """¿Es código que se ejecuta (servicios o `infra/`), y no una suite?"""
    if not ruta.startswith(("services/", "infra/")):
        return False
    return not _NO_CODIGO.intersection(ruta.split("/"))


def test_f059_r36_el_codigo_de_f059_solo_nombra_sql_read_y_partes_reclamacion():
    nombradas = {
        pieza: set(_RUTA_DE_LA_PASARELA.findall(codigo))
        for pieza, codigo in _todo_el_codigo_de_f059().items()
    }

    todas = set().union(*nombradas.values())
    assert todas == RUTAS_PERMITIDAS
    assert {p: r for p, r in nombradas.items() if r} == {
        "infrastructure/sigrid/volcado.py": RUTAS_PERMITIDAS
    }


def test_f059_r36_ninguna_pieza_de_f059_nombra_otra_escritura():
    culpables = {
        pieza: [e for e in OTRAS_ESCRITURAS if e in codigo]
        for pieza, codigo in _todo_el_codigo_de_f059().items()
        if any(e in codigo for e in OTRAS_ESCRITURAS)
    }

    assert culpables == {}


def _veces_sql_write(ruta: str, fuente: str) -> int:
    """Cuántas veces nombra `sql/write` lo que se **ejecuta** de un fichero.

    Un `.py`, sin docstrings ni comentarios (un docstring puede decir «ni
    `sql/write`»); cualquier otro fichero de código, entero.
    """
    if ruta.endswith(".py"):
        fuente = ast.unparse(_sin_docstrings(ast.parse(fuente)))
    return fuente.count("sql/write")


def test_f059_r36_ningun_fichero_de_codigo_gana_un_sql_write():
    """R36 · la mitad del diff: ningún fichero de código tocado por la rama, en
    `services/` o en `infra/`, nombra `sql/write` más veces que en la base."""
    cambiados = _diff_de_la_rama_o_saltar()
    codigo = [ruta for ruta in cambiados if _es_codigo(ruta) and (RAIZ / ruta).is_file()]
    assert codigo, "la rama no ha tocado código: el control no mira nada"

    def en_la_base(ruta: str) -> str:
        fuente = _git("show", f"{_base()}:{ruta}")
        return fuente.stdout if fuente is not None and fuente.returncode == 0 else ""

    ganan = {
        ruta: (
            _veces_sql_write(ruta, en_la_base(ruta)),
            _veces_sql_write(ruta, (RAIZ / ruta).read_text(encoding="utf-8")),
        )
        for ruta in codigo
    }

    assert {r: v for r, v in ganan.items() if v[1] > v[0]} == {}
    # Control negativo: el docstring no cuenta; el código, sí.
    assert _veces_sql_write("x.py", 'def f():\n    """Ni sql/write."""\n    return "sql/write"\n') == 1
    assert _veces_sql_write("x.ps1", "# sql/write\n") == 1


def test_f059_r36_la_ruta_de_partes_reclamacion_vive_solo_en_el_adaptador():
    """En **todo** el código del servicio, no solo en el de F-059: la ruta y su constante."""
    codigo = _codigo_del_servicio()
    con_la_ruta = sorted(r for r, c in codigo.items() if "sigrid/partes-reclamacion" in c)
    con_la_constante = sorted(r for r, c in codigo.items() if "RUTA_PARTES_RECLAMACION" in c)

    assert con_la_ruta == ["infrastructure/sigrid/volcado.py"]
    assert con_la_constante == ["infrastructure/sigrid/volcado.py"]


def _escrituras_importadas(relativa: str, fuente: str | None = None) -> list[str]:
    return sorted(
        m for m in _modulos_importados(relativa, fuente) if m.startswith(MODULOS_QUE_ESCRIBEN_EN_SIGRID)
    )


def test_f059_r36_ningun_modulo_nuevo_de_f059_importa_las_escrituras_del_erp():
    """Los módulos nuevos y `function_app.py` (§11): ni `escrituras` ni `graficos`."""
    culpables = {
        r: _escrituras_importadas(r) for r in (*NUEVOS_DE_F059, "function_app.py") if r.endswith(".py")
    }

    assert {r: m for r, m in culpables.items() if m} == {}


def test_f059_r36_los_ficheros_tocados_no_ganan_importaciones_de_las_escrituras():
    """La fábrica de Sigrid ya importaba el gráfico (`construir_graficos`): ni ella
    ni ningún otro fichero tocado gana una importación de las escrituras."""
    _diff_de_la_rama_o_saltar()

    for relativa in PIEZAS_DE_F059:
        antes = _escrituras_importadas(relativa, _en_la_base(f"{SERVICIO}{relativa}"))
        assert _escrituras_importadas(relativa) == antes, relativa


def test_f059_r36_los_detectores_no_son_ciegos():
    assert _RUTA_DE_LA_PASARELA.findall('RUTA = "/api/sql/write"') == ["/api/sql/write"]
    assert _RUTA_DE_LA_PASARELA.findall('f"{base}/api/sigrid/partes-reclamacion"') == [
        "/api/sigrid/partes-reclamacion"
    ]
    assert _es_codigo(f"{SERVICIO}interface_adapters/api/volcado.py")
    assert not _es_codigo(f"{SERVICIO}tests/test_f059_alcance_cerrado.py")
    assert "infrastructure/sigrid/volcado.py" in _codigo_del_servicio()
    assert not any(r.startswith("tests/") for r in _codigo_del_servicio())


# --------------------------------------------------------------------------
# R37, R42 · la ventana del volcado es suya, y solo suya
# --------------------------------------------------------------------------

_VENTANA_DEL_VOLCADO = re.compile(r"volcado_habilitado", re.IGNORECASE)
_OTRAS_VENTANAS = re.compile(r"cierre_habilitado|archivo_habilitado", re.IGNORECASE)

#: Los módulos del cierre, el gráfico y el archivo (R37): no miran la del volcado.
DEL_CIERRE_EL_GRAFICO_Y_EL_ARCHIVO = (
    "infrastructure/sigrid/cliente.py",
    "infrastructure/sigrid/escrituras.py",
    "infrastructure/sigrid/graficos.py",
    "application/pipelines/paso_cierre.py",
    "application/pipelines/paso_grafico.py",
    "application/pipelines/paso_archivo.py",
    "interface_adapters/api/cerrar.py",
    "interface_adapters/api/adjuntar.py",
    "interface_adapters/api/archivar.py",
)


def test_f059_r37_la_ventana_del_volcado_solo_la_miran_los_ajustes_la_fabrica_y_el_adaptador():
    """R16, R37 · se lee en los ajustes, se comprueba en `construir_volcador` y el
    adaptador la nombra al negarse a volcar sin ella; en ningún otro sitio."""
    con_la_ventana = sorted(
        relativa
        for relativa, codigo in _codigo_del_servicio().items()
        if _VENTANA_DEL_VOLCADO.search(codigo)
    )

    assert con_la_ventana == [
        "config/settings.py",
        "infrastructure/sigrid/fabrica.py",
        "infrastructure/sigrid/volcado.py",
    ]
    for relativa, donde in (
        ("infrastructure/sigrid/fabrica.py", ["construir_volcador"]),
        ("infrastructure/sigrid/volcado.py", ["AdaptadorVolcadoSigridApi.volcar"]),
    ):
        definiciones = _definiciones(_actual(relativa))
        assert sorted(n for n, c in definiciones.items() if _VENTANA_DEL_VOLCADO.search(c)) == donde


def test_f059_r37_ni_el_cierre_ni_el_grafico_ni_el_archivo_la_miran():
    culpables = [
        r for r in DEL_CIERRE_EL_GRAFICO_Y_EL_ARCHIVO if _VENTANA_DEL_VOLCADO.search(_codigo_que_se_ejecuta(r))
    ]

    assert culpables == []


def test_f059_r37_r42_el_volcado_no_mira_las_otras_ventanas():
    culpables = sorted(
        pieza for pieza, codigo in _todo_el_codigo_de_f059().items() if _OTRAS_VENTANAS.search(codigo)
    )

    assert culpables == []


def test_f059_r37_los_detectores_de_ventanas_no_son_ciegos():
    assert _VENTANA_DEL_VOLCADO.search("ajustes.volcado_habilitado")
    assert _VENTANA_DEL_VOLCADO.search('"VOLCADO_HABILITADO"')
    assert _OTRAS_VENTANAS.search("exigir_interruptor_de_cierre(ajustes.cierre_habilitado)")
    assert not _OTRAS_VENTANAS.search("exigir_entorno_con_cierre(entorno)")
    assert _VENTANA_DEL_VOLCADO.search(_codigo_que_se_ejecuta("config/settings.py"))


# --------------------------------------------------------------------------
# O-B3-3 · solo la fábrica construye el adaptador que escribe
# --------------------------------------------------------------------------


def _llamadas(nombre_llamado: str) -> list[tuple[str, str, ast.Call]]:
    """Cada llamada a `nombre_llamado` en el código del servicio: fichero, función y nodo."""
    halladas = []
    for relativa in _codigo_del_servicio():
        arbol = ast.parse(_actual(relativa))
        for funcion in ast.walk(arbol):
            if not isinstance(funcion, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            for nodo in ast.walk(funcion):
                if isinstance(nodo, ast.Call):
                    llamado = nodo.func
                    nombre = getattr(llamado, "id", None) or getattr(llamado, "attr", None)
                    if nombre == nombre_llamado:
                        halladas.append((relativa, funcion.name, nodo))
    return halladas


def _con_escritura(llamada: ast.Call) -> bool:
    """¿La llamada pide `escritura_habilitada` con algo que no es un `False` literal?"""
    for clave in llamada.keywords:
        if clave.arg == "escritura_habilitada":
            return not (isinstance(clave.value, ast.Constant) and clave.value.value is False)
    return False


def test_f059_o_b3_3_solo_la_fabrica_construye_el_adaptador_del_volcado():
    donde = sorted({(r, f) for r, f, _ in _llamadas("AdaptadorVolcadoSigridApi")})

    assert donde == [("infrastructure/sigrid/fabrica.py", "_adaptador_de_volcado")]


def test_f059_o_b3_3_solo_construir_volcador_pide_la_escritura():
    quien_pide = sorted(
        {(r, f) for r, f, llamada in _llamadas("_adaptador_de_volcado") if _con_escritura(llamada)}
    )
    quien_llama = sorted({(r, f) for r, f, _ in _llamadas("_adaptador_de_volcado")})

    assert quien_pide == [("infrastructure/sigrid/fabrica.py", "construir_volcador")]
    assert quien_llama == [
        ("infrastructure/sigrid/fabrica.py", "construir_ensayador"),
        ("infrastructure/sigrid/fabrica.py", "construir_volcador"),
    ]
    # Y el adaptador recibe lo que le pasan, sin fijarlo él.
    (llamada,) = [c for _, _, c in _llamadas("AdaptadorVolcadoSigridApi")]
    (clave,) = [k for k in llamada.keywords if k.arg == "escritura_habilitada"]
    assert isinstance(clave.value, ast.Name) and clave.value.id == "escritura_habilitada"


def test_f059_o_b3_3_el_detector_de_llamadas_no_es_ciego():
    fuente = "def f():\n    A(escritura_habilitada=True)\n    A(escritura_habilitada=False)\n    m.A(x=1)\n"
    llamadas = [n for n in ast.walk(ast.parse(fuente)) if isinstance(n, ast.Call)]

    assert [_con_escritura(c) for c in llamadas] == [True, False, False]
    assert _llamadas("construir_volcador")  # la ruta del volcado la llama


# --------------------------------------------------------------------------
# R32, R33 · el SQL
# --------------------------------------------------------------------------

_ESCRITURA_PROHIBIDA = re.compile(r"\bDELETE\b|\bTRUNCATE\b|(?<!FOR )\bUPDATE\b", re.IGNORECASE)
_DDL = re.compile(r"\b(CREATE|ALTER|DROP)\s+(TABLE|INDEX|SCHEMA|VIEW|FUNCTION)\b", re.IGNORECASE)


def test_f059_r32_el_unico_sql_nuevo_es_el_16():
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if r.endswith(".sql")] == [
        f"{SERVICIO}infrastructure/persistencia/sql/16_volcados_sigrid.sql"
    ]


def test_f059_r33_el_codigo_de_f059_no_actualiza_ni_borra_y_el_ddl_es_el_16():
    con_escritura = sorted(p for p, c in _todo_el_codigo_de_f059().items() if _ESCRITURA_PROHIBIDA.search(c))
    con_ddl = sorted(p for p, c in _todo_el_codigo_de_f059().items() if _DDL.search(c))
    sql = _codigo_que_se_ejecuta("infrastructure/persistencia/sql/16_volcados_sigrid.sql")

    assert con_escritura == []
    assert con_ddl == ["infrastructure/persistencia/sql/16_volcados_sigrid.sql"]
    assert re.findall(r"\b(?:TABLE|INDEX)\s+IF\s+NOT\s+EXISTS\s+([\w.]+)", sql) == [
        "postventa.volcados_sigrid",
        "ix_volcados_sigrid_incidencia",
        "ix_volcados_sigrid_llamada",
    ]
    assert "public." not in sql


def test_f059_r33_los_detectores_de_sql_no_son_ciegos():
    assert _ESCRITURA_PROHIBIDA.search("UPDATE postventa.volcados_sigrid SET")
    assert _ESCRITURA_PROHIBIDA.search("delete from postventa.volcados_sigrid")
    assert not _ESCRITURA_PROHIBIDA.search("ORDER BY incidencia_id FOR UPDATE")
    assert _DDL.search("CREATE TABLE IF NOT EXISTS postventa.x (y int)")
    assert "FOR UPDATE" in _codigo_que_se_ejecuta("infrastructure/persistencia/sentencias_revision.py")


# --------------------------------------------------------------------------
# §17, §21.5 · lo que no se toca
# --------------------------------------------------------------------------

#: Los ficheros de «No se toca» de `design.md` §17, enteros, con su ruta de `git`.
INTOCABLES = tuple(
    f"{SERVICIO}{r}"
    for r in (
        "infrastructure/sigrid/cliente.py",
        "infrastructure/sigrid/escrituras.py",
        "infrastructure/sigrid/graficos.py",
        "infrastructure/sigrid/consultas.py",
        "infrastructure/sigrid/catalogo_obra.py",
        "infrastructure/sigrid/ubicacion.py",
        "application/pipelines/paso_grafico.py",
        "application/pipelines/paso_archivo.py",
        "application/pipelines/catalogo_obra.py",
        "application/pipelines/plantilla.py",
        # F-056 y F-060: `candidatas_al_volcado`, `normalizar_ubicaciones` y
        # `ResultadoNormalizacion` viven aquí, y el fichero entero no cambia.
        "application/pipelines/revision.py",
        "interface_adapters/api/cerrar.py",
        "interface_adapters/api/adjuntar.py",
        "interface_adapters/api/archivar.py",
        "interface_adapters/api/bandeja.py",
        "interface_adapters/api/importar.py",
        "interface_adapters/api/plantilla.py",
        "interface_adapters/api/normalizacion.py",
        "interface_adapters/api/tiempos.py",
        "domain/models/normalizacion.py",
        # `RevisionPort` (siete operaciones) y `ResultadoDelLote` (F-060).
        "domain/ports/revision.py",
        "infrastructure/persistencia/sql/13_bandeja_incidencias.sql",
        "infrastructure/persistencia/sql/14_decisiones_equivalencia.sql",
        "infrastructure/persistencia/sql/15_revisiones_bandeja.sql",
        "config/plantilla_incidencias.yaml",
        "tests/utiles_revision.py",
    )
) + ("infra/19_ventana_escritura.ps1", "infra/22_ventana_archivo.ps1")

#: Carpetas enteras que F-059 no toca: el front es F-040.
CARPETAS_INTOCABLES = ("services/postventa-front/",)

#: Las piezas de F-060 (y de F-056 que comparte) dentro de ficheros que F-059
#: sí toca (§17, §21.5): tienen que ser **las de la base**.
PIEZAS_INTOCABLES = (
    ("infrastructure/persistencia/repositorio_revision_pg.py", "RepositorioRevisionPostgres.registrar_lote"),
    ("infrastructure/persistencia/repositorio_revision_pg.py", "RepositorioRevisionPostgres._registrar_lote"),
    ("infrastructure/persistencia/sentencias_revision.py", "select_bloquear"),
    ("infrastructure/persistencia/sentencias_revision.py", "select_ultimas_revisiones"),
    ("infrastructure/persistencia/sentencias_revision.py", "insert_revision"),
    ("interface_adapters/api/revision.py", "listar_revision"),
    ("function_app.py", "revision_normalizar"),
    ("function_app.py", "_error_de_revision"),
    ("function_app.py", "revision"),
    ("function_app.py", "revision_historial"),
    ("function_app.py", "revision_acciones"),
    ("function_app.py", "cerrar"),
    ("function_app.py", "adjuntar"),
    ("function_app.py", "archivar"),
)


def test_f059_s17_los_intocables_existen():
    assert [r for r in INTOCABLES if not (RAIZ / r).is_file()] == []
    assert [c for c in CARPETAS_INTOCABLES if not (RAIZ / c).is_dir()] == []


def test_f059_s17_la_rama_no_toca_ningun_intocable_ni_el_front():
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if r in INTOCABLES] == []
    assert [r for r in cambiados if r.startswith(CARPETAS_INTOCABLES)] == []


@pytest.mark.parametrize(
    ("relativa", "nombre"), PIEZAS_INTOCABLES, ids=[f"{r}::{n}" for r, n in PIEZAS_INTOCABLES]
)
def test_f059_s21_5_las_piezas_de_f060_y_las_compartidas_son_las_de_la_base(relativa, nombre):
    _diff_de_la_rama_o_saltar()
    antes = _definiciones(_en_la_base(f"{SERVICIO}{relativa}"))

    assert nombre in antes, f"la base no define {nombre}: la lista está mal"
    assert _pieza(relativa, nombre) == antes[nombre]


# --------------------------------------------------------------------------
# R41 · los tests de otras features (F-1 (a): la lista de excepciones)
# --------------------------------------------------------------------------

#: Los tests de otras features que la rama toca, cada uno con las funciones
#: (o constantes) que cambian, y nada más (`design.md` §21.3).
AMPLIADOS: dict[str, frozenset[str]] = {
    # Grupo A · el `16_volcados_sigrid.sql` (T4/T5).
    "tests/test_f005_ddl_idempotente_texto.py": frozenset(
        {"test_f005_r1_se_aplican_todos_los_ficheros_en_orden"}
    ),
    "tests/test_f028_ddl_historico.py": frozenset(
        {"test_f028_el_fichero_sigue_la_convencion_y_se_aplica_el_ultimo"}
    ),
    "tests/test_f030_veredicto_persistido.py": frozenset(
        {"test_f030_r20_no_hay_ni_un_fichero_de_ddl_nuevo"}
    ),
    "tests/test_f031_alcance_cerrado.py": frozenset({"test_f031_r17_no_hay_ni_un_fichero_de_ddl_nuevo"}),
    "tests/test_f032_alcance_cerrado.py": frozenset({"test_f032_r22_no_hay_ni_un_fichero_de_ddl_nuevo"}),
    "tests/test_f033_alcance_cerrado.py": frozenset({"test_f033_no_hay_ni_un_fichero_de_ddl_nuevo"}),
    "tests/test_f034_alcance_cerrado.py": frozenset({"test_f034_r23_no_hay_ni_un_fichero_de_ddl_nuevo"}),
    "tests/test_f036_ddl.py": frozenset(
        {"test_f036_t14_los_tres_ficheros_se_aplican_detras_del_historico_y_en_orden"}
    ),
    "tests/test_f056_ddl.py": frozenset(
        {
            "test_f056_r36_el_fichero_va_detras_de_los_de_f036",
            # B-2 (humano, 2026-10-16).
            "test_f056_r12_la_unica_columna_de_correo_del_esquema_es_revisado_correo",
        }
    ),
    "tests/test_f056_alcance_cerrado.py": frozenset({"test_f056_r12_solo_15_declara_una_columna_de_correo"}),
    "tests/test_f060_alcance_cerrado.py": frozenset({"test_f060_r37_los_sql_son_los_quince_de_antes"}),
    # Grupo B · la cuenta de anónimos (T13): 21 → 24.
    "tests/test_f010_endpoints_protegidos.py": frozenset(
        {"ENDPOINTS", "test_f010_r32_el_barrido_de_niveles_ve_lo_que_hay"}
    ),
    # Grupo B · la cuenta y la cabecera de `INTEGRACION.md` (T20, Bloque 5).
    "tests/test_f012_documentacion.py": frozenset(
        {"NUMERALES", "test_f012_r68_integracion_declara_el_endpoint_nuevo_que_exponemos"}
    ),
    "tests/test_f053_documentacion.py": frozenset(
        {"CUENTA_VIGENTE", "test_f053_t6_el_parrafo_va_antes_de_los_diecisiete_y_sin_encabezado"}
    ),
    "tests/test_f019_documentacion.py": frozenset(
        {"test_f019_r32_la_seccion_ocho_ya_habla_de_todos_los_endpoints"}
    ),
    "tests/test_f056_documentacion.py": frozenset(
        {"test_f056_r44_la_seccion_ocho_dice_la_cuenta_y_las_ventanas"}
    ),
    "tests/test_f060_documentacion.py": frozenset(
        {
            "test_f060_r43_la_seccion_ocho_dice_la_importacion_la_traza_y_la_cuenta",
            "test_f060_r43_la_cabecera_dice_que_f060_lo_toco_y_cuando",
        }
    ),
    # Grupo C · los estados y la fila de F-056 (T2, T4, T13).
    "tests/test_f056_paginacion.py": frozenset(
        {"test_f056_r23_filtros_de_estado", "test_f056_r27_resumen_sobre_todas_las_filas"}
    ),
    "tests/test_f056_pipeline_revision.py": frozenset(
        {"test_f056_r27_resumen_de_toda_la_obra_y_pagina_filtrada"}
    ),
    "tests/test_f056_revision_dominio.py": frozenset(
        {"PERMITIDAS", "SITUACIONES", "sit_en_duda", "sit_volcada"}
    ),
    "tests/test_f056_revision_http.py": frozenset(
        {"CLAVES_DE_FILA", "test_f056_r27_la_respuesta_lleva_lo_de_r27"}
    ),
    # El ancho de las filas falsas de `_select_situaciones`, `aprobadas` y
    # `registrar` (T4), con los casos de R2, R3, R4 y R33 sobre ese repositorio.
    "tests/test_f056_repositorio_revision.py": frozenset(
        {
            "COD",
            "CORREO_DEL_VOLCADO",
            "EN_DUDA",
            "LEIDAS_DEL_VOLCADO",
            "SIN_VOLCADO",
            "VOLCADA",
            "_conexion_con_volcado",
            "_fila",
            "_fila_de_volcado",
            "_parte_en_sigrid",
            "_ultimo",
            "_volcado",
            "test_f056_r10_las_situaciones_leen_estas_columnas_en_este_orden",
            "test_f056_r22_r38_cada_situacion_trae_su_ultima_y_la_de_su_original",
            "test_f056_r4_r7_registrar_bloquea_comprueba_inserta_y_confirma",
            "test_f059_r1_r4_las_lateral_del_volcado_son_de_la_propia",
            "test_f059_r1_r4_una_fila_volcada_trae_su_parte_y_su_ultimo",
            "test_f059_r1_una_fila_en_duda",
            "test_f059_r2_la_comprobacion_va_antes_que_la_frescura",
            "test_f059_r2_r27_un_ultimo_rechazado_si_admite_la_accion",
            "test_f059_r2_r29_registrar_con_un_volcado_aparecido_es_409_sin_insertar",
            "test_f059_r2_se_lee_tras_el_bloqueo_y_solo_la_de_la_propia",
            "test_f059_r2_si_la_base_falla_al_leer_el_volcado_es_503_y_nada_a_medias",
            "test_f059_r33_las_situaciones_no_seleccionan_actor_oid",
            "test_f059_r36_una_fila_sin_el_ancho_del_volcado_no_se_lee_a_medias",
            "test_f059_r3_aprobadas_con_una_volcada_no_falla_y_no_la_devuelve",
            "test_f059_r4_la_original_de_una_duplicada_queda_sin_volcado",
            "test_f059_r4_listar_y_situacion_traen_la_situacion_de_volcado",
            "test_f059_r4_un_ultimo_rechazado_deja_la_aprobada_con_su_motivo",
            "test_f059_r4_una_fila_sin_eventos_no_tiene_volcado",
        }
    ),
}

#: Los del grupo B que cambiaban con los documentos (T20): hasta entonces solo
#: se exigía que no cambiara nada que no estuviera declarado. **T20 los sacó
#: de aquí** (O-B4-3 de la review del Bloque 4): los cinco —`test_f012_`,
#: `test_f053_`, `test_f019_`, `test_f056_` y `test_f060_documentacion.py`—
#: pasan a igualdad con lo declarado en `AMPLIADOS`, y sus aserciones que
#: cambian están, una a una, en `ASERCIONES_QUE_CAMBIAN`. Se deja vacío y no se
#: borra: así se ve que no queda ninguno a medias.
AMPLIADOS_EN_EL_BLOQUE_5: frozenset[str] = frozenset()

#: Las aserciones de la base que **cambian** (no las que se añaden), una a una y
#: por función, con su texto normalizado (`ast.unparse`): la cifra o el fichero
#: vigente sustituye a la anterior, como dice R41. **Solo** esas se pueden
#: perder; todas las demás de la base, también las de estas mismas funciones,
#: siguen (C-B4-1 de la review del Bloque 4: antes se eximía la función entera).
#: T20 añade, con el mismo formato, las del grupo B de los documentos: de los
#: cinco ficheros, solo dos pierden aserciones (la cifra vieja en `in` de
#: F-019 y las dos literales de la cabecera de F-060); en los otros tres la
#: cifra está en una constante o en una tupla, y lo que cambia es el dato, no
#: la aserción.
ASERCIONES_QUE_CAMBIAN: dict[str, dict[str, frozenset[str]]] = {
    "tests/test_f005_ddl_idempotente_texto.py": {
        "test_f005_r1_se_aplican_todos_los_ficheros_en_orden": frozenset(
            {
                "nombres == ['01_esquema.sql', '02_remesas.sql', '03_partes.sql', '04_validaciones.sql', '05_archivos.sql', '06_cierres.sql', '07_preferencias.sql', '08_usuarios_sigrid.sql', '09_graficos.sql', '10_aprobaciones.sql', '11_historico_estado.sql', '12_importaciones.sql', '13_bandeja_incidencias.sql', '14_decisiones_equivalencia.sql', '15_revisiones_bandeja.sql']",
            }
        ),
    },
    "tests/test_f028_ddl_historico.py": {
        "test_f028_el_fichero_sigue_la_convencion_y_se_aplica_el_ultimo": frozenset(
            {
                "nombres[nombres.index(FICHERO) + 1:] == ['12_importaciones.sql', '13_bandeja_incidencias.sql', '14_decisiones_equivalencia.sql', '15_revisiones_bandeja.sql']",
            }
        ),
    },
    "tests/test_f030_veredicto_persistido.py": {
        "test_f030_r20_no_hay_ni_un_fichero_de_ddl_nuevo": frozenset(
            {
                'nombres == DDL_DE_F028 + DDL_DE_F036 + DDL_DE_F056',
            }
        ),
    },
    "tests/test_f031_alcance_cerrado.py": {
        "test_f031_r17_no_hay_ni_un_fichero_de_ddl_nuevo": frozenset(
            {
                'nombres == DDL_DE_F028 + DDL_DE_F036 + DDL_DE_F056',
            }
        ),
    },
    "tests/test_f032_alcance_cerrado.py": {
        "test_f032_r22_no_hay_ni_un_fichero_de_ddl_nuevo": frozenset(
            {
                'nombres == DDL_DE_F028 + DDL_DE_F036 + DDL_DE_F056',
            }
        ),
    },
    "tests/test_f033_alcance_cerrado.py": {
        "test_f033_no_hay_ni_un_fichero_de_ddl_nuevo": frozenset(
            {
                'nombres == DDL_DE_F028 + DDL_DE_F036 + DDL_DE_F056',
            }
        ),
    },
    "tests/test_f034_alcance_cerrado.py": {
        "test_f034_r23_no_hay_ni_un_fichero_de_ddl_nuevo": frozenset(
            {
                'nombres == DDL_DE_F028 + DDL_DE_F036 + DDL_DE_F056',
            }
        ),
    },
    "tests/test_f036_ddl.py": {
        "test_f036_t14_los_tres_ficheros_se_aplican_detras_del_historico_y_en_orden": frozenset(
            {
                "nombres[nombres.index('11_historico_estado.sql') + 1:] == [*FICHEROS, '15_revisiones_bandeja.sql']",
            }
        ),
    },
    "tests/test_f056_ddl.py": {
        "test_f056_r36_el_fichero_va_detras_de_los_de_f036": frozenset(
            {
                'nombres[-1] == FICHERO',
            }
        ),
        "test_f056_r12_la_unica_columna_de_correo_del_esquema_es_revisado_correo": frozenset(
            {
                "con_correo == [f'{ESQUEMA}.{TABLA}.revisado_correo']",
            }
        ),
    },
    "tests/test_f056_alcance_cerrado.py": {
        "test_f056_r12_solo_15_declara_una_columna_de_correo": frozenset(
            {
                "con_correo == ['15_revisiones_bandeja.sql']",
            }
        ),
    },
    "tests/test_f060_alcance_cerrado.py": {
        "test_f060_r37_los_sql_son_los_quince_de_antes": frozenset(
            {
                "tuple(sorted((f.name for f in carpeta.glob('*.sql')))) == SQL_DE_LA_BASE",
            }
        ),
    },
    "tests/test_f010_endpoints_protegidos.py": {
        "test_f010_r32_el_barrido_de_niveles_ve_lo_que_hay": frozenset(
            {
                'len(niveles(codigo)) == len(ENDPOINTS) == 21',
            }
        ),
    },
    # Grupo B · los documentos (T20). «Los veintiuno», de `in` a `not in`, y
    # «Los veinticuatro» en `in` (F-019); y la cabecera de F-060, que deja de
    # exigir que F-060 sea la última y su fecha la del documento, y exige una
    # cabecera bien formada que no retroceda, con F-060 y su despliegue.
    "tests/test_f019_documentacion.py": {
        "test_f019_r32_la_seccion_ocho_ya_habla_de_todos_los_endpoints": frozenset(
            {
                "'Los veintiuno quedan en nivel' in seccion_ocho",
            }
        ),
    },
    "tests/test_f060_documentacion.py": {
        "test_f060_r43_la_cabecera_dice_que_f060_lo_toco_y_cuando": frozenset(
            {
                "'Última feature que lo tocó: F-060' in cabecera",
                "'Fecha: 2026-10-14.' in cabecera",
            }
        ),
    },
    "tests/test_f056_paginacion.py": {
        "test_f056_r23_filtros_de_estado": frozenset(
            {
                "[f.value for f in FiltroEstado] == ['activas', 'todas', 'nueva', 'editada', 'aprobada', 'descartada']",
            }
        ),
        "test_f056_r27_resumen_sobre_todas_las_filas": frozenset(
            {
                'r.por_estado == {E.NUEVA: 3, E.EDITADA: 2, E.APROBADA: 1, E.DESCARTADA: 2}',
            }
        ),
    },
    "tests/test_f056_pipeline_revision.py": {
        "test_f056_r27_resumen_de_toda_la_obra_y_pagina_filtrada": frozenset(
            {
                'resultado.resumen.por_estado == {E.NUEVA: 3, E.EDITADA: 0, E.APROBADA: 1, E.DESCARTADA: 1}',
            }
        ),
    },
    "tests/test_f056_revision_http.py": {
        "test_f056_r27_la_respuesta_lleva_lo_de_r27": frozenset(
            {
                "datos['resumen'] == {'total': 3, 'por_estado': {'nueva': 2, 'editada': 0, 'aprobada': 0, 'descartada': 1}, 'con_motivos': 1, 'por_motivo': {m.value: int(m is MotivoNoAprobable.SIN_UBICACION) for m in MotivoNoAprobable}}",
            }
        ),
    },
    "tests/test_f056_repositorio_revision.py": {
        "test_f056_r22_r38_cada_situacion_trae_su_ultima_y_la_de_su_original": frozenset(
            {
                "sql.count('LEFT JOIN LATERAL') == 2",
            }
        ),
        "test_f056_r4_r7_registrar_bloquea_comprueba_inserta_y_confirma": frozenset(
            {
                'conexion.ejecutadas[2].parametros[0] == UUID(int=1)',
                'len(sql) == 3',
                "sql[2].startswith(f'INSERT INTO {ESQUEMA}.revisiones_bandeja ')",
            }
        ),
    },
}

#: Los tests propios de F-059 y sus dobles.
_DE_F059 = re.compile(r"/tests(_bbdd/tests)?/(test_f059_|utiles_volcado\.py)")


def _tocados(cambiados: list[str]) -> list[str]:
    return sorted(
        r.removeprefix(SERVICIO)
        for r in cambiados
        if re.search(r"/tests(_bbdd/tests)?/", r) and not _DE_F059.search(r)
    )


def test_f059_r41_la_rama_solo_toca_los_tests_declarados():
    """Fuera de los de F-059, solo los ampliados; ninguno más de ninguna feature."""
    tocados = set(_tocados(_diff_de_la_rama_o_saltar()))

    assert tocados <= set(AMPLIADOS)
    assert set(AMPLIADOS) - AMPLIADOS_EN_EL_BLOQUE_5 <= tocados


def test_f059_r41_o_b4_3_ningun_ampliado_queda_a_medias():
    """Tras T20 ningún ampliado se compara con `<=`: todos, con igualdad. Un
    fichero que volviera a `AMPLIADOS_EN_EL_BLOQUE_5` relajaría su control."""
    assert AMPLIADOS_EN_EL_BLOQUE_5 == frozenset()
    for relativa in (
        "tests/test_f012_documentacion.py",
        "tests/test_f053_documentacion.py",
        "tests/test_f019_documentacion.py",
        "tests/test_f056_documentacion.py",
        "tests/test_f060_documentacion.py",
    ):
        assert relativa in AMPLIADOS, relativa


def test_f059_r41_los_tests_de_f009_no_tienen_diff():
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if re.search(r"/tests(_bbdd/tests)?/test_f009_", r)] == []


def test_f059_r41_de_f012_f036_y_f053_solo_los_de_la_lista():
    cambiados = _diff_de_la_rama_o_saltar()

    tocados = {
        r.removeprefix(SERVICIO)
        for r in cambiados
        if re.search(r"/tests(_bbdd/tests)?/test_f0(12|36|53)_", r)
    }

    assert tocados <= {
        "tests/test_f036_ddl.py",
        "tests/test_f012_documentacion.py",
        "tests/test_f053_documentacion.py",
    }
    assert "tests/test_f036_ddl.py" in tocados


@pytest.mark.parametrize("relativa", sorted(AMPLIADOS))
def test_f059_r41_en_cada_ampliado_solo_cambia_lo_declarado(relativa):
    _diff_de_la_rama_o_saltar()
    antes = _en_la_base(f"{SERVICIO}{relativa}")
    ahora = _actual(relativa)

    assert _quitadas(antes, ahora) == set(), "un test ampliado no pierde nada"
    if relativa in AMPLIADOS_EN_EL_BLOQUE_5:
        assert _novedades(antes, ahora) <= AMPLIADOS[relativa]
    else:
        assert _novedades(antes, ahora) == AMPLIADOS[relativa]


def _perdidas_no_declaradas(
    antes: str, ahora: str, declaradas: Mapping[str, frozenset[str]]
) -> dict[str, list[str]]:
    """Las aserciones de la base que ya no están y **no** se declararon, por función.

    `declaradas` es lo de un fichero en `ASERCIONES_QUE_CAMBIAN`. Se compara con
    multiplicidad (`Counter`): declarar una aserción permite perderla **una** vez.
    """
    viejas, nuevas = _aserciones(antes), _aserciones(ahora)
    sobran = {}
    for funcion, aserciones in viejas.items():
        perdidas = aserciones - nuevas.get(funcion, Counter())
        no_declaradas = perdidas - Counter(declaradas.get(funcion, frozenset()))
        if no_declaradas:
            sobran[funcion] = sorted(no_declaradas.elements())
    return sobran


@pytest.mark.parametrize("relativa", sorted(AMPLIADOS))
def test_f059_r41_ningun_ampliado_pierde_una_asercion(relativa):
    """Sin relajar: cada aserción de la base sigue, salvo **las** declaradas una a una (C-B4-1)."""
    _diff_de_la_rama_o_saltar()
    antes = _en_la_base(f"{SERVICIO}{relativa}")

    assert _perdidas_no_declaradas(antes, _actual(relativa), ASERCIONES_QUE_CAMBIAN.get(relativa, {})) == {}


@pytest.mark.parametrize("relativa", sorted(ASERCIONES_QUE_CAMBIAN))
def test_f059_r41_c_b4_1_lo_declarado_es_lo_que_se_pierde(relativa):
    """Cada aserción declarada estaba en la base, en su función, y ya no está: una
    declaración de más sería una puerta abierta para relajar después."""
    _diff_de_la_rama_o_saltar()
    antes = _aserciones(_en_la_base(f"{SERVICIO}{relativa}"))
    ahora = _aserciones(_actual(relativa))

    for funcion, declaradas in ASERCIONES_QUE_CAMBIAN[relativa].items():
        perdidas = antes.get(funcion, Counter()) - ahora.get(funcion, Counter())
        assert declaradas == set(perdidas), (relativa, funcion)


def test_f059_r41_lo_que_cambia_esta_declarado_como_ampliado():
    """Una aserción que cambia en una función que no se declara ampliada no se puede."""
    for relativa, funciones in ASERCIONES_QUE_CAMBIAN.items():
        assert set(funciones) <= AMPLIADOS[relativa], relativa
        assert all(funciones.values()), relativa


def test_f059_r41_c_b4_1_quitar_una_asercion_no_declarada_da_rojo():
    """Control negativo con un fichero de verdad (C-B4-1, «G1» de la review del Bloque 4).

    En `test_f056_r4_r7_registrar_bloquea_comprueba_inserta_y_confirma`, que sí
    tiene aserciones declaradas, se quita una que **no** lo está —la de los
    `commits` y `rollbacks`—: la guarda la ve. Y la que sí está declarada se
    puede perder sin que salte.
    """
    _diff_de_la_rama_o_saltar()
    relativa = "tests/test_f056_repositorio_revision.py"
    funcion = "test_f056_r4_r7_registrar_bloquea_comprueba_inserta_y_confirma"
    g1 = "(conexion.commits, conexion.rollbacks) == (1, 0)"
    antes = _en_la_base(f"{SERVICIO}{relativa}")
    declaradas = ASERCIONES_QUE_CAMBIAN[relativa]

    def sin(fuente: str, texto: str) -> str:
        arbol = ast.parse(fuente)
        for nodo in arbol.body:
            if isinstance(nodo, ast.FunctionDef) and nodo.name == funcion:
                nodo.body = [
                    s for s in nodo.body if not (isinstance(s, ast.Assert) and ast.unparse(s.test) == texto)
                ]
        return ast.unparse(arbol)

    actual = _actual(relativa)
    assert g1 in _aserciones(actual)[funcion]
    assert _perdidas_no_declaradas(antes, sin(actual, g1), declaradas) == {funcion: [g1]}
    assert _perdidas_no_declaradas(antes, actual, declaradas) == {}


def test_f059_r41_c_b4_1_la_guarda_de_aserciones_no_es_ciega():
    """Control negativo sin `git`: una función declarada no exime a sus demás aserciones."""
    antes = "def test_a():\n    assert 1 == 1\n    assert 2 == 2\n\ndef test_b():\n    assert 3\n"
    declaradas = {"test_a": frozenset({"1 == 1"})}

    assert _perdidas_no_declaradas(antes, antes.replace("    assert 1 == 1\n", ""), declaradas) == {}
    assert _perdidas_no_declaradas(antes, antes.replace("    assert 2 == 2\n", ""), declaradas) == {
        "test_a": ["2 == 2"]
    }
    assert _perdidas_no_declaradas(antes, antes.replace("    assert 3\n", "    pass\n"), declaradas) == {
        "test_b": ["3"]
    }
    # Declarar una aserción la deja perder una vez, no dos.
    doble = antes.replace("    assert 1 == 1\n", "    assert 1 == 1\n    assert 1 == 1\n")
    assert _perdidas_no_declaradas(doble, antes.replace("    assert 1 == 1\n", ""), declaradas) == {
        "test_a": ["1 == 1"]
    }


def test_f059_r41_los_controles_de_los_tests_no_son_ciegos():
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
    con_mensaje = antes.replace("assert 3\n", 'assert 3, "otro mensaje"\n')
    assert _aserciones(con_mensaje) == _aserciones(antes)
    assert _tocados(
        [f"{SERVICIO}tests/test_f059_x.py", f"{SERVICIO}tests/test_f056_y.py", f"{SERVICIO}tests/utiles_volcado.py"]
    ) == ["tests/test_f056_y.py"]
