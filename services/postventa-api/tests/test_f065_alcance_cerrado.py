# services/postventa-api/tests/test_f065_alcance_cerrado.py
"""Lo que F-065 promete **no** tocar, comprobado (T9; R26–R28, `design.md` §9).

F-065 lee de Sigrid **todas** las reclamaciones de la obra y las cruza con la
bandeja, en una ruta aparte, `GET /api/revision/sigrid`. Toca tres ficheros que
ya existían (`fabrica.py`, `errores.py`, `function_app.py`) y roza código de
F-036, F-056, F-059 y F-060 (el adaptador del catálogo, el listado, el volcado,
el cronómetro). Cada frontera tiene aquí su control:

| Frontera | Requisito | Qué se comprueba |
|---|---|---|
| Los ficheros de la rama | §9.1–9.2 | solo cambian los declarados (y la spec, `progress/` y el backlog) |
| Lo que NO se toca | §9.3, §15.6 | sin cambios: el listado y la revisión, el catálogo, el adaptador y la persistencia del volcado, la normalización, la plantilla, el cronómetro, la configuración, el DDL, `requirements.txt` y el front |
| La guarda del ensayo | §15.6 (A4 bis) | en los ficheros del volcado de F-059, **solo** las piezas declaradas: `MotivoExclusion`, `PeticionDeEnsayo`, `ResultadoDeEnsayo`, `ensayar`, el borde del ensayo y las tres entradas de `function_app.py` (con `filas`); `volcar`, `panel_de_volcado` y las selecciones, intactos |
| Los ficheros que ya existían | §9.2 | en cada uno, **solo** las piezas declaradas; ninguna definición quitada; el resto del módulo solo gana sus `import` |
| Las rutas que ya había | **R26** | las funciones que las sirven y traducen sus errores, las de la base |
| Sigrid | **R27** | ninguna pieza de F-065 nombra otra ruta de la pasarela que `sql/read` ni importa las escrituras del ERP; ninguna mira una ventana de escritura |
| Variables, DDL, dependencias y caché | **R28** | ninguna variable de entorno nueva ni lectura del entorno, ningún `.sql` ni sentencia de escritura, ninguna dependencia, ninguna caché |
| Los tests de otras features | §9.2, §15.6 | solo `test_f010_endpoints_protegidos.py` (la cuenta de rutas, T8) y los tres del ensayo de F-059 (el doble vacío del lector y las dos ampliaciones aditivas), solo en lo declarado y sin perder ninguna aserción |

## La excepción declarada: la cuenta de rutas

`test_f010_endpoints_protegidos.py` cuenta las rutas que publica
`function_app.py` y exige que cuadren con su lista: **toda** ruta nueva pasa por
ahí (F-019, F-036, F-056, F-059 y F-060 lo hicieron igual). `design.md` §9.2 no
lo nombra; T8 lo exige («el servicio entero en verde»). Cambian **solo**
`ENDPOINTS` (gana `revision/sigrid`, y su comentario) y la cuenta del control
negativo (24 → 25); ninguna aserción se pierde.

Con el patrón de `test_f060_alcance_cerrado.py`: **el del diff**, contra la
**base fija** del tramo (`b863b46`, anotada en `progress/impl_F-065.md`; no
`git merge-base`, que se movería si `dev` avanzara) y hasta el **árbol de
trabajo**, con las tres guardas de F-030 para no dejar `dev` en rojo cuando la
rama se mergee; y **el que no depende de `git`**, que se comprueba siempre.
El Bloque A4 bis (T17) amplía esta guarda a lo que toca del volcado (§15.6):
`PIEZAS_DE_LA_GUARDA` e `IMPORTS_DE_LA_GUARDA`, aparte de las de §9.2 para que
se vea qué es de cada bloque.

## Las dos ampliaciones aditivas de F-059 (enmienda del líder, 2026-10-29)

`CLAVES_DEL_ENSAYO` (`test_f059_volcado_http.py`) gana `"sigrid"` (R47) y la
lista de `test_f059_r11_r18_los_motivos_de_exclusion` gana, **al final**,
`"duplicada_en_sigrid"` y `"conflicto_sin_confirmar"` (R45). Aquí se fija que
solo **ganan** esos valores: ninguno se quita ni se cambia.

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
RAMA_DE_LA_FEATURE = "feature/F-065-revision-sigrid-backend"

#: La base fija del tramo (`progress/impl_F-065.md`, «Anotación de base»).
BASE_FIJA = "b863b46"

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
    nuevos = _git("ls-files", "--others", "--exclude-standard")
    sin_seguir = [] if nuevos is None or nuevos.returncode != 0 else nuevos.stdout.splitlines()
    return sorted(
        {
            linea.strip().replace("\\", "/")
            for linea in [*diff.stdout.splitlines(), *sin_seguir]
            if linea.strip()
        }
    )


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
    `Clase.metodo`. Los `import` no cuentan: van en `_resto_del_modulo`.
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


def _es_definicion(nodo: ast.stmt) -> bool:
    if isinstance(nodo, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return True
    if isinstance(nodo, ast.Assign):
        return all(isinstance(objetivo, ast.Name) for objetivo in nodo.targets)
    if isinstance(nodo, ast.AnnAssign):
        return isinstance(nodo.target, ast.Name)
    return False


def _resto_del_modulo(fuente: str) -> list[str]:
    """Las sentencias de módulo que no son una definición (los `import`, sobre todo).

    Cada `from m import a, b` se parte en `from m import a` y `from m import b`:
    así, ganar un nombre en un `import` que ya estaba se ve como **una** sentencia
    nueva y no como «quitar una y poner otra».
    """
    resto: list[str] = []
    for nodo in _sin_docstrings(ast.parse(fuente)).body:  # type: ignore[attr-defined]
        if _es_definicion(nodo):
            continue
        if isinstance(nodo, ast.ImportFrom):
            resto.extend(
                ast.unparse(ast.ImportFrom(module=nodo.module, names=[alias], level=nodo.level))
                for alias in nodo.names
            )
        elif isinstance(nodo, ast.Import):
            resto.extend(ast.unparse(ast.Import(names=[alias])) for alias in nodo.names)
        else:
            resto.append(ast.unparse(nodo))
    return resto


def _actual(relativa: str) -> str:
    return (RAIZ_DEL_SERVICIO / relativa).read_text(encoding="utf-8")


def _codigo_que_se_ejecuta(fuente: str) -> str:
    """Un `.py` entero, sin docstrings ni comentarios."""
    return ast.unparse(_sin_docstrings(ast.parse(fuente)))


def _novedades(antes: str, ahora: str) -> set[str]:
    """Las definiciones que se añaden o cambian entre dos versiones de un fichero."""
    viejas, nuevas = _definiciones(antes), _definiciones(ahora)
    return {n for n, codigo in nuevas.items() if viejas.get(n) != codigo}


def _quitadas(antes: str, ahora: str) -> set[str]:
    return set(_definiciones(antes)) - set(_definiciones(ahora))


def _aserciones(fuente: str) -> dict[str, Counter[str]]:
    """Lo que comprueba cada aserción de cada función de test, sin su mensaje."""
    return {
        nodo.name: Counter(ast.unparse(a.test) for a in ast.walk(nodo) if isinstance(a, ast.Assert))
        for nodo in ast.parse(fuente).body
        if isinstance(nodo, ast.FunctionDef)
    }


def _modulos_importados(fuente: str) -> set[str]:
    importados: set[str] = set()
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Import):
            importados.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module)
            importados.update(f"{nodo.module}.{alias.name}" for alias in nodo.names)
    return importados


# --------------------------------------------------------------------------
# §9.1–9.2 · lo que F-065 declara
# --------------------------------------------------------------------------

#: Los ficheros **nuevos** de producción de F-065 (`design.md` §9.1).
NUEVOS_DE_F065 = (
    "domain/models/sigrid_bandeja.py",
    "domain/ports/reclamaciones_obra.py",
    "infrastructure/sigrid/consultas_reclamaciones_obra.py",
    "infrastructure/sigrid/reclamaciones_obra.py",
    "application/pipelines/sigrid_bandeja.py",
    "interface_adapters/api/sigrid_bandeja.py",
    # Bloque A4 bis (§15.6): la guarda del ensayo.
    "application/pipelines/guarda_sigrid.py",
)

#: Lo que F-065 añade en ficheros de producción que ya existían (§9.2), pieza
#: a pieza. `__all__` aparte: solo puede **ganar** nombres.
PIEZAS_DE_F065: dict[str, frozenset[str]] = {
    "infrastructure/sigrid/fabrica.py": frozenset({"construir_reclamaciones_obra"}),
    "domain/models/errores.py": frozenset(
        {"ReclamacionesSinVerificar", "ReclamacionesSinVerificar.__init__"}
    ),
    # La ruta, su traducción de errores y `_json_sin_cache` (con `_sin_cache`,
    # que pone la cabecera a las respuestas de error de siempre, y la constante).
    "function_app.py": frozenset(
        {"CACHE_CONTROL_SIN_CACHE", "_sin_cache", "_json_sin_cache", "revision_sigrid"}
    ),
}

#: Lo que el resto de cada módulo (los `import`) gana, y nada más.
IMPORTS_DE_F065: dict[str, frozenset[str]] = {
    "infrastructure/sigrid/fabrica.py": frozenset(
        {
            "from domain.ports.reclamaciones_obra import ReclamacionesObraPort",
            "from infrastructure.sigrid.reclamaciones_obra import AdaptadorReclamacionesObraSigridApi",
        }
    ),
    "domain/models/errores.py": frozenset(),
    "function_app.py": frozenset(
        {
            "from domain.models.errores import ReclamacionesSinVerificar",
            "from interface_adapters.api.sigrid_bandeja import sigrid_de_la_bandeja",
        }
    ),
}

#: Lo que la guarda del ensayo (Bloque A4 bis, `design.md` §15.6) cambia en
#: ficheros del volcado de F-059 y en `function_app.py`, pieza a pieza.
PIEZAS_DE_LA_GUARDA: dict[str, frozenset[str]] = {
    # Solo dos valores más (R45).
    "domain/models/volcado.py": frozenset({"MotivoExclusion"}),
    # La petición, el resultado y la llamada a la guarda; nada más.
    "application/pipelines/volcado.py": frozenset(
        {"PeticionDeEnsayo", "ResultadoDeEnsayo", "ensayar"}
    ),
    # La clave opcional (R43), el lector y el bloque `sigrid` (R47).
    "interface_adapters/api/volcado.py": frozenset(
        {
            "_CONFIRMADOS",
            "_CLAVES_DE_CONFIRMACION",
            "_MAX_CODIGOS_CONFIRMADOS",
            "ensayar_volcado",
            "_sigrid_de",
            "_confirmados",
            "_codigos_confirmados",
        }
    ),
    # Las tres entradas de R46 y `filas` en `reclamaciones_sin_verificar`.
    "function_app.py": frozenset({"CODIGOS_DEL_VOLCADO", "HTTP_DEL_VOLCADO", "_error_del_volcado"}),
}

#: Lo que el resto de cada uno de esos módulos gana por la guarda.
IMPORTS_DE_LA_GUARDA: dict[str, frozenset[str]] = {
    "domain/models/volcado.py": frozenset(),
    "application/pipelines/volcado.py": frozenset(
        {
            "from dataclasses import field",
            "from types import MappingProxyType",
            "from domain.ports.reclamaciones_obra import ReclamacionesObraPort",
            "from application.pipelines.guarda_sigrid import GuardaDelEnsayo",
            "from application.pipelines.guarda_sigrid import aplicar_guarda_de_sigrid",
            "from application.pipelines.guarda_sigrid import registrar_la_guarda",
        }
    ),
    "interface_adapters/api/volcado.py": frozenset(
        {
            "from domain.models.volcado import PATRON_COD_PARTE",
            "from infrastructure.sigrid.fabrica import construir_reclamaciones_obra",
            "from application.pipelines.guarda_sigrid import GuardaDelEnsayo",
        }
    ),
    "function_app.py": frozenset(),
}

#: Cada fichero de producción que ya existía, con todo lo que F-065 declara en él.
TOCADOS = sorted(set(PIEZAS_DE_F065) | set(PIEZAS_DE_LA_GUARDA))


def _piezas_declaradas(relativa: str) -> frozenset[str]:
    return PIEZAS_DE_F065.get(relativa, frozenset()) | PIEZAS_DE_LA_GUARDA.get(relativa, frozenset())


def _imports_declarados(relativa: str) -> frozenset[str]:
    return IMPORTS_DE_F065.get(relativa, frozenset()) | IMPORTS_DE_LA_GUARDA.get(relativa, frozenset())


#: Los tests de F-065 (`design.md` §9.1).
TESTS_DE_F065 = re.compile(r"^services/postventa-api/tests/test_f065_[a-z_]+\.py$")

#: Los tests de otras features que la rama toca, con lo que cambia en cada uno.
AMPLIADOS: dict[str, frozenset[str]] = {
    # T8: la ruta nueva y la cuenta a veinticinco (ver la cabecera).
    "tests/test_f010_endpoints_protegidos.py": frozenset(
        {"ENDPOINTS", "test_f010_r32_el_barrido_de_niveles_ve_lo_que_hay"}
    ),
    # Bloque A4 bis (§15.6): el doble vacío del lector donde se construye el
    # ensayo, y las dos ampliaciones aditivas.
    "tests/test_f059_pipeline_volcado.py": frozenset(
        {"SinReclamacionesEnSigrid", "SinReclamacionesEnSigrid.leer", "Mundo.ensayar"}
    ),
    "tests/test_f059_volcado_http.py": frozenset(
        {"SinReclamacionesEnSigrid", "SinReclamacionesEnSigrid.leer", "_componer", "CLAVES_DEL_ENSAYO"}
    ),
    "tests/test_f059_volcado_dominio.py": frozenset({"test_f059_r11_r18_los_motivos_de_exclusion"}),
}

#: Las aserciones que una ampliación **cambia**: la cuenta de 24 a 25.
ASERCIONES_QUE_CAMBIAN: dict[str, frozenset[str]] = {
    "tests/test_f010_endpoints_protegidos.py": frozenset(
        {"test_f010_r32_el_barrido_de_niveles_ve_lo_que_hay"}
    ),
    # La lista de motivos gana dos valores al final (se fija abajo).
    "tests/test_f059_volcado_dominio.py": frozenset({"test_f059_r11_r18_los_motivos_de_exclusion"}),
}

#: Lo demás que la rama puede tocar: los documentos de §9.2 (Bloque A5), el
#: script de la medición (R29) y la memoria del arnés.
OTROS_DECLARADOS = frozenset(
    {
        "infra/29_reclamaciones_obra_sigrid.ps1",
        "docs/ARCHITECTURE.md",
        "docs/INTEGRACION.md",
        "harness/features.json",
        "BACKLOG.md",
    }
)
CARPETAS_DECLARADAS = (
    "specs/F-065-revision-sigrid-backend/",
    "specs/F-064-bandeja-con-sigrid/",
    "progress/",
)


def _declarado(ruta: str) -> bool:
    if ruta.startswith(CARPETAS_DECLARADAS) or ruta in OTROS_DECLARADOS:
        return True
    if TESTS_DE_F065.match(ruta):
        return True
    relativa = ruta.removeprefix(SERVICIO)
    return ruta.startswith(SERVICIO) and (
        relativa in NUEVOS_DE_F065
        or relativa in PIEZAS_DE_F065
        or relativa in PIEZAS_DE_LA_GUARDA
        or relativa in AMPLIADOS
    )


def _pieza(relativa: str, nombre: str) -> str:
    definiciones = _definiciones(_actual(relativa))
    assert nombre in definiciones, f"{relativa} no define {nombre}"
    return definiciones[nombre]


def _todo_el_codigo_de_f065() -> dict[str, str]:
    """Cada pieza de F-065: los ficheros nuevos enteros y las piezas de §9.2."""
    piezas = {r: _codigo_que_se_ejecuta(_actual(r)) for r in NUEVOS_DE_F065}
    for relativa, nombres in PIEZAS_DE_F065.items():
        for nombre in sorted(nombres):
            piezas[f"{relativa}::{nombre}"] = _pieza(relativa, nombre)
    return piezas


def test_f065_el_control_del_diff_no_esta_mirando_una_lista_vacia():
    """Si el diff viniera vacío, los controles de abajo mentirían todos."""
    cambiados = _diff_de_la_rama_o_saltar()

    for relativa in (*NUEVOS_DE_F065, *TOCADOS, *AMPLIADOS):
        assert f"{SERVICIO}{relativa}" in cambiados, f"la rama tiene que haber tocado {relativa}"


def test_f065_las_piezas_de_f065_existen_todas():
    """Una lista con algo que no existe daría verde sin mirarlo."""
    assert [r for r in NUEVOS_DE_F065 if not (RAIZ_DEL_SERVICIO / r).is_file()] == []
    piezas = _todo_el_codigo_de_f065()
    assert len(piezas) == len(NUEVOS_DE_F065) + sum(len(n) for n in PIEZAS_DE_F065.values())
    assert all(codigo.strip() for codigo in piezas.values())


def test_f065_a4bis_las_piezas_de_la_guarda_existen_todas():
    """Lo mismo para §15.6: cada pieza declarada está definida y no está vacía."""
    for relativa, nombres in PIEZAS_DE_LA_GUARDA.items():
        for nombre in nombres:
            assert _pieza(relativa, nombre).strip(), f"{relativa}::{nombre}"
    assert set(IMPORTS_DE_LA_GUARDA) == set(PIEZAS_DE_LA_GUARDA)


def test_f065_s9_la_rama_solo_toca_los_ficheros_declarados():
    """§9.1–9.2 · fuera de lo declarado, nada; ni de otra feature ni de la nuestra."""
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if not _declarado(r)] == []


@pytest.mark.parametrize("relativa", TOCADOS)
def test_f065_s9_en_cada_fichero_tocado_solo_cambia_lo_declarado(relativa):
    """§9.2 y §15.6 · en cada fichero que ya existía, F-065 solo añade o cambia
    sus piezas, y no quita nada."""
    _diff_de_la_rama_o_saltar()
    antes = _en_la_base(f"{SERVICIO}{relativa}")
    ahora = _actual(relativa)

    assert _novedades(antes, ahora) - {"__all__"} == _piezas_declaradas(relativa)
    assert _quitadas(antes, ahora) == set()


@pytest.mark.parametrize("relativa", TOCADOS)
def test_f065_s9_all_solo_gana_nombres(relativa):
    _diff_de_la_rama_o_saltar()
    exportados = {}
    for clave, fuente in (("antes", _en_la_base(f"{SERVICIO}{relativa}")), ("ahora", _actual(relativa))):
        definicion = _definiciones(fuente).get("__all__")
        exportados[clave] = (
            set() if definicion is None else set(ast.literal_eval(definicion.split("=", 1)[1].strip()))
        )

    assert exportados["antes"] <= exportados["ahora"]


@pytest.mark.parametrize("relativa", sorted(set(IMPORTS_DE_F065) | set(IMPORTS_DE_LA_GUARDA)))
def test_f065_s9_el_resto_del_modulo_solo_gana_sus_import(relativa):
    """Lo que no es una definición (los `import`, un `try` o una llamada de módulo)."""
    _diff_de_la_rama_o_saltar()
    antes = Counter(_resto_del_modulo(_en_la_base(f"{SERVICIO}{relativa}")))
    ahora = Counter(_resto_del_modulo(_actual(relativa)))

    assert antes - ahora == Counter(), "el resto del módulo no pierde nada"
    assert set((ahora - antes).elements()) == _imports_declarados(relativa)
    assert max((ahora - antes).values(), default=1) == 1


def test_f065_s9_los_controles_del_codigo_no_son_ciegos():
    """`_definiciones` ve los métodos; `_resto_del_modulo` parte los `import`."""
    fuente = (
        '"""Doc."""\nfrom a import b, c\nimport d\n\nclass P:\n    """Doc."""\n'
        "    campo: int\n\n    def m(self):\n        return 1\n\nX = 1\n"
    )

    definiciones = _definiciones(fuente)
    assert set(definiciones) == {"P", "P.m", "X"}
    assert "def m" not in definiciones["P"]
    assert _novedades(fuente, fuente.replace("return 1", "return 2")) == {"P.m"}
    assert _novedades(fuente, fuente.replace('"""Doc."""', '"""Otra."""')) == set()
    assert _quitadas(fuente, fuente.replace("X = 1\n", "")) == {"X"}
    assert _resto_del_modulo(fuente) == ["from a import b", "from a import c", "import d"]
    gana = fuente.replace("from a import b, c", "from a import b, c, e")
    assert Counter(_resto_del_modulo(gana)) - Counter(_resto_del_modulo(fuente)) == Counter(
        {"from a import e": 1}
    )
    assert _resto_del_modulo(fuente + "f()\n")[-1] == "f()"


# --------------------------------------------------------------------------
# §9.3 · lo que no se toca
# --------------------------------------------------------------------------

#: Los ficheros de «Lo que NO se toca» de `design.md` §9.3, con su ruta de `git`.
INTOCABLES = tuple(
    f"{SERVICIO}{r}"
    for r in (
        "domain/models/revision.py",
        "application/pipelines/revision.py",
        "interface_adapters/api/revision.py",
        "infrastructure/sigrid/catalogo_obra.py",
        "infrastructure/sigrid/consultas_catalogo.py",
        "infrastructure/sigrid/ubicaciones_validas.py",
        # El volcado, salvo lo que la guarda declara en `PIEZAS_DE_LA_GUARDA`
        # (§15.6): el adaptador de `partes-reclamacion`, su persistencia y su
        # dominio de estados quedan enteros.
        "domain/models/situacion_volcado.py",
        "domain/ports/volcado.py",
        "infrastructure/sigrid/volcado.py",
        "infrastructure/persistencia/repositorio_volcado_pg.py",
        "infrastructure/persistencia/sentencias_volcado.py",
        # Se usan sus funciones; no se tocan.
        "domain/models/normalizacion.py",
        "domain/models/plantilla_incidencias.py",
        "interface_adapters/api/tiempos.py",
        "config/settings.py",
        "requirements.txt",
        # El puerto de la revisión (F-056) y el del catálogo, sin cambiar (§10.2).
        "domain/ports/revision.py",
        "domain/ports/catalogo_obra.py",
    )
)

#: Carpetas enteras que F-065 no toca: el DDL y el front (F-064).
CARPETAS_INTOCABLES = (
    f"{SERVICIO}infrastructure/persistencia/sql/",
    "services/postventa-front/",
)


def test_f065_s9_3_los_intocables_existen():
    assert [r for r in INTOCABLES if not (RAIZ / r).is_file()] == []
    assert [c for c in CARPETAS_INTOCABLES if not (RAIZ / c).is_dir()] == []


def test_f065_s9_3_la_rama_no_toca_ningun_intocable():
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if r in INTOCABLES] == []
    assert [r for r in cambiados if r.startswith(CARPETAS_INTOCABLES)] == []


# --------------------------------------------------------------------------
# R26 · las rutas que ya había responden y registran igual
# --------------------------------------------------------------------------

#: Las funciones que sirven las rutas de F-056, F-059 y F-060 y traducen sus
#: errores: tienen que ser las de la base (los handlers, en sus ficheros, están
#: en `INTOCABLES`).
RESPUESTAS_SIN_CAMBIOS = (
    "revision",
    "revision_historial",
    "revision_acciones",
    "revision_normalizar",
    "volcado",
    "volcado_ensayo",
    "volcado_volcar",
    "_json",
    "_error_de_revision",
    "_rechazo_de_obra",
    "_sin_sigrid_o_sin_base",
    "_configuracion_rota",
    # `_error_del_volcado` gana `filas` (§15.6): se fija abajo, aparte.
    "_cuerpo_del_volcado_no_es_json",
    "CODIGOS_DE_REVISION",
    "CODIGOS_DE_RECHAZO_DE_OBRA",
)


@pytest.mark.parametrize("nombre", RESPUESTAS_SIN_CAMBIOS)
def test_f065_r26_las_funciones_que_responden_son_las_de_la_base(nombre):
    _diff_de_la_rama_o_saltar()
    antes = _definiciones(_en_la_base(f"{SERVICIO}function_app.py"))

    assert nombre in antes, f"la base no define {nombre}: la lista está mal"
    assert _pieza("function_app.py", nombre) == antes[nombre]


#: Lo que el volcado de F-059 sigue teniendo **igual** en cada fichero que la
#: guarda toca (§15.6, «Lo que NO se toca»).
DEL_VOLCADO_SIN_CAMBIOS: dict[str, tuple[str, ...]] = {
    "domain/models/volcado.py": (
        "seleccionar_para_ensayo",
        "seleccionar_para_volcado",
        "validar_ensayo",
        "interpretar_respuesta",
        "Excluida",
        "Seleccion",
        "PATRON_COD_PARTE",
        "MAX_PARTES_POR_LLAMADA",
        "CADUCIDAD_DEL_ENSAYO",
        "resumen_de",
    ),
    "application/pipelines/volcado.py": ("volcar", "panel_de_volcado", "PeticionDeVolcado", "_login"),
    "interface_adapters/api/volcado.py": (
        "volcar_a_sigrid",
        "leer_panel_de_volcado",
        "_objeto",
        "_incidencias",
        "_pedidas",
        "_CLAVES_DEL_ENSAYO",
        "_parte_del_ensayo",
        "_excluida",
    ),
    "function_app.py": ("ERRORES_DEL_VOLCADO", "MENSAJES_DEL_LOGIN", "volcado", "volcado_ensayo", "volcado_volcar"),
}


@pytest.mark.parametrize(
    ("relativa", "nombre"),
    [(r, n) for r, nombres in DEL_VOLCADO_SIN_CAMBIOS.items() for n in nombres],
)
def test_f065_a4bis_volcar_el_panel_y_las_selecciones_no_cambian(relativa, nombre):
    _diff_de_la_rama_o_saltar()
    antes = _definiciones(_en_la_base(f"{SERVICIO}{relativa}"))

    assert nombre in antes, f"la base no define {nombre}: la lista está mal"
    assert _pieza(relativa, nombre) == antes[nombre]


#: La única rama que gana la traducción de errores del volcado (§15.6).
RAMA_DE_FILAS = (
    "\n    elif isinstance(error, ReclamacionesSinVerificar):\n        cuerpo['filas'] = error.filas"
)


def test_f065_a4bis_la_traduccion_de_errores_del_volcado_solo_gana_filas():
    _diff_de_la_rama_o_saltar()
    antes = _definiciones(_en_la_base(f"{SERVICIO}function_app.py"))["_error_del_volcado"]
    ahora = _pieza("function_app.py", "_error_del_volcado")

    assert ahora.count(RAMA_DE_FILAS) == 1
    assert ahora.replace(RAMA_DE_FILAS, "") == antes


def _tabla(relativa: str, nombre: str, fuente: str | None = None) -> dict[str, str]:
    """Un diccionario de módulo, como `{clave: valor}` en texto."""
    arbol = ast.parse(_actual(relativa) if fuente is None else fuente)
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and any(
            isinstance(o, ast.Name) and o.id == nombre for o in nodo.targets
        ):
            assert isinstance(nodo.value, ast.Dict)
            return {
                ast.unparse(k): ast.unparse(v)
                for k, v in zip(nodo.value.keys, nodo.value.values, strict=True)
                if k is not None
            }
    raise AssertionError(f"{relativa} no define {nombre}")


@pytest.mark.parametrize(
    ("nombre", "nuevas"),
    [
        (
            "CODIGOS_DEL_VOLCADO",
            {
                "CatalogoNoDisponible": "'sigrid_no_disponible'",
                "ReclamacionesSinVerificar": "'reclamaciones_sin_verificar'",
                "ObraAmbigua": "'obra_ambigua'",
            },
        ),
        (
            "HTTP_DEL_VOLCADO",
            {"CatalogoNoDisponible": "503", "ReclamacionesSinVerificar": "409", "ObraAmbigua": "409"},
        ),
    ],
)
def test_f065_a4bis_las_tablas_del_volcado_solo_ganan_las_tres_de_la_guarda(nombre, nuevas):
    """R46: tres entradas más; las de F-059, las mismas y con el mismo valor."""
    _diff_de_la_rama_o_saltar()
    antes = _tabla("function_app.py", nombre, _en_la_base(f"{SERVICIO}function_app.py"))
    ahora = _tabla("function_app.py", nombre)

    assert {k: v for k, v in ahora.items() if k not in nuevas} == antes
    assert {k: ahora[k] for k in nuevas if k in ahora} == nuevas


def test_f065_a4bis_el_codigo_de_la_guarda_en_el_volcado_solo_lee_y_no_mira_ventanas():
    """R27, R28 y R46 sobre las piezas de §15.6, salvo las dos tablas de
    `function_app.py`, que ya nombraban `VolcadoDeshabilitado` (F-059) y cuyo
    cambio fija el test de arriba entrada a entrada."""
    tablas = {"function_app.py::CODIGOS_DEL_VOLCADO", "function_app.py::HTTP_DEL_VOLCADO"}
    piezas = {
        f"{r}::{n}": _pieza(r, n)
        for r, nombres in PIEZAS_DE_LA_GUARDA.items()
        for n in nombres
        if f"{r}::{n}" not in tablas
    }
    assert len(piezas) == sum(len(n) for n in PIEZAS_DE_LA_GUARDA.values()) - 2

    culpables = {
        pieza: _nombra_una_escritura(codigo)
        + _rutas_que_no_son_sql_read(codigo)
        + VENTANA.findall(codigo)
        + re.findall(r"\benviron\b|\bgetenv\b", codigo)
        + _DDL.findall(codigo)
        + _ESCRITURA.findall(codigo)
        + _CACHE.findall(codigo)
        for pieza, codigo in piezas.items()
    }

    assert {p: c for p, c in culpables.items() if c} == {}


def test_f065_r26_la_ruta_nueva_es_la_unica_ruta_nueva():
    _diff_de_la_rama_o_saltar()
    patron = re.compile(r'@app\.route\(\s*route="([\w/]+)"')
    antes = set(patron.findall(_en_la_base(f"{SERVICIO}function_app.py")))
    ahora = set(patron.findall(_actual("function_app.py")))

    assert ahora - antes == {"revision/sigrid"}
    assert antes - ahora == set()


# --------------------------------------------------------------------------
# R27 · solo `sql/read`, y ninguna escritura del ERP
# --------------------------------------------------------------------------

#: Las rutas de escritura de `sigrid-api` (`azure-apps/sigrid_api.md`).
ESCRITURAS_EN_SIGRID = ("sql/write", "partes-reclamacion", "concepto-grafico")

#: Los módulos que escriben en el ERP o lo componen: ninguna pieza nueva los importa.
MODULOS_QUE_ESCRIBEN_EN_SIGRID = (
    "infrastructure.sigrid.escrituras",
    "infrastructure.sigrid.graficos",
    "infrastructure.sigrid.volcado",
    "interface_adapters.api.volcado",
    "application.pipelines.volcado",
)

#: Las ventanas de escritura y sus campos de `Ajustes`: todas llevan esto (R2).
VENTANA = re.compile(r"habilitado", re.IGNORECASE)

#: Cualquier ruta de la pasarela escrita en el código.
RUTA_DE_LA_PASARELA = re.compile(r"/api/[\w/.-]+")

CARPETAS_QUE_NO_SON_CODIGO = {"tests", "tests_js", "tests_bbdd", ".venv", "__pycache__"}


def _es_codigo(ruta: str) -> bool:
    if not ruta.startswith(("services/", "infra/")):
        return False
    return not CARPETAS_QUE_NO_SON_CODIGO.intersection(ruta.split("/"))


def _nombra_una_escritura(texto: str) -> list[str]:
    return [e for e in ESCRITURAS_EN_SIGRID if e in texto]


def _rutas_que_no_son_sql_read(texto: str) -> list[str]:
    return [r for r in RUTA_DE_LA_PASARELA.findall(texto) if r != "/api/sql/read"]


def test_f065_r27_ninguna_linea_anadida_al_codigo_nombra_una_escritura():
    """La mitad del diff: cada línea añadida al código, también en los comentarios."""
    cambiados = _diff_de_la_rama_o_saltar()
    codigo = [ruta for ruta in cambiados if _es_codigo(ruta) and (RAIZ / ruta).is_file()]
    assert codigo, "la rama no ha tocado código: el control no mira nada"

    anadidas = _lineas_anadidas(codigo)

    assert anadidas
    assert [linea for linea in anadidas if _nombra_una_escritura(linea)] == []


def test_f065_r27_r2_el_codigo_de_f065_solo_nombra_sql_read_y_ninguna_ventana():
    """La mitad que no depende de `git`, sobre lo que se ejecuta."""
    culpables = {
        pieza: _nombra_una_escritura(codigo) + _rutas_que_no_son_sql_read(codigo) + VENTANA.findall(codigo)
        for pieza, codigo in _todo_el_codigo_de_f065().items()
    }

    assert {p: c for p, c in culpables.items() if c} == {}


def test_f065_r27_ninguna_pieza_de_f065_importa_las_escrituras_del_erp():
    piezas = {r: _modulos_importados(_actual(r)) for r in NUEVOS_DE_F065}
    piezas.update({f"{r}::import": {i.split(" import ")[0].removeprefix("from ") for i in IMPORTS_DE_F065[r]} for r in IMPORTS_DE_F065})
    piezas.update(
        {
            f"{r}::import-de-la-guarda": {i.split(" import ")[0].removeprefix("from ") for i in nuevos}
            for r, nuevos in IMPORTS_DE_LA_GUARDA.items()
        }
    )

    culpables = {
        r: sorted(m for m in importados if m.startswith(MODULOS_QUE_ESCRIBEN_EN_SIGRID))
        for r, importados in piezas.items()
    }

    assert {r: m for r, m in culpables.items() if m} == {}


def test_f065_r27_los_detectores_no_son_ciegos():
    assert _nombra_una_escritura('cliente.post("sql/write", lote)') == ["sql/write"]
    assert _nombra_una_escritura("POST /api/sigrid/partes-reclamacion") == ["partes-reclamacion"]
    assert _rutas_que_no_son_sql_read('RUTA = "/api/sigrid/concepto-grafico"') == ["/api/sigrid/concepto-grafico"]
    assert _rutas_que_no_son_sql_read('RUTA_LECTURA = "/api/sql/read"') == []
    assert VENTANA.findall("if ajustes.volcado_habilitado:") == ["habilitado"]
    importados = _modulos_importados(_actual("interface_adapters/api/sigrid_bandeja.py"))
    assert "infrastructure.sigrid.fabrica.construir_reclamaciones_obra" in importados
    assert _modulos_importados("from infrastructure.sigrid.volcado import X\n") >= {"infrastructure.sigrid.volcado"}
    assert _es_codigo(f"{SERVICIO}interface_adapters/api/sigrid_bandeja.py")
    assert not _es_codigo(f"{SERVICIO}tests/test_f065_http.py")


# --------------------------------------------------------------------------
# R28 · sin variables, sin DDL, sin dependencias y sin caché
# --------------------------------------------------------------------------

FICHEROS_DE_CONFIGURACION = (
    f"{SERVICIO}config/settings.py",
    f"{SERVICIO}.env.example",
    f"{SERVICIO}local.settings.json.example",
    "infra/00_vars_postventa.ps1",
)
DEPENDENCIAS = (
    f"{SERVICIO}requirements.txt",
    f"{SERVICIO}requirements-dev.txt",
    "requirements-dev.txt",
)

#: Los `.sql` del servicio: F-065 no añade ninguno (R28).
SQL_DE_LA_BASE = tuple(f"{n:02d}_{s}.sql" for n, s in enumerate(
    (
        "esquema", "remesas", "partes", "validaciones", "archivos", "cierres", "preferencias",
        "usuarios_sigrid", "graficos", "aprobaciones", "historico_estado", "importaciones",
        "bandeja_incidencias", "decisiones_equivalencia", "revisiones_bandeja", "volcados_sigrid",
    ),
    start=1,
))  # fmt: skip

_ESCRITURA = re.compile(r"\bINSERT\s+INTO\b|\bDELETE\b|\bTRUNCATE\b|\bMERGE\b|(?<!FOR )\bUPDATE\b", re.IGNORECASE)
_DDL = re.compile(r"\b(CREATE|ALTER|DROP)\s+(TABLE|INDEX|SCHEMA|VIEW|FUNCTION)\b", re.IGNORECASE)
_CACHE = re.compile(r"lru_cache|\bcache\b|functools")


def test_f065_r28_la_rama_no_toca_la_configuracion_ni_las_dependencias():
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if r in FICHEROS_DE_CONFIGURACION or r in DEPENDENCIAS] == []
    assert not any(r.endswith((".env", "local.settings.json")) for r in cambiados)


def test_f065_r28_la_rama_no_toca_ningun_sql():
    cambiados = _diff_de_la_rama_o_saltar()

    assert [r for r in cambiados if r.endswith(".sql")] == []


def test_f065_r28_los_sql_son_los_dieciseis_de_antes():
    """La mitad que no depende de `git`: ni un `17_…sql`."""
    carpeta = RAIZ_DEL_SERVICIO / "infrastructure" / "persistencia" / "sql"

    assert tuple(sorted(f.name for f in carpeta.glob("*.sql"))) == SQL_DE_LA_BASE


def test_f065_r28_el_codigo_de_f065_no_lee_el_entorno_ni_escribe_ni_guarda():
    culpables = {
        pieza: sorted(
            set(re.findall(r"\benviron\b|\bgetenv\b", codigo))
            | set(_DDL.findall(codigo))
            | set(_ESCRITURA.findall(codigo))
            | set(_CACHE.findall(codigo))
        )
        for pieza, codigo in _todo_el_codigo_de_f065().items()
    }

    assert {p: c for p, c in culpables.items() if c} == {}


def test_f065_r28_los_detectores_de_entorno_ddl_escrituras_y_cache_no_son_ciegos():
    assert _ESCRITURA.search("UPDATE dbo.con SET est = 3")
    assert _ESCRITURA.search("insert into postventa.x values (1)")
    assert _ESCRITURA.search("DELETE FROM dbo.rcp")
    assert not _ESCRITURA.search("SELECT v.obride, c.cod FROM dbo.rcp r ORDER BY c.cod")
    assert _DDL.search("ALTER TABLE postventa.revisiones_bandeja ADD COLUMN x text")
    assert not _DDL.search("una tabla creada por el DDL")
    assert _CACHE.search("@functools.lru_cache(maxsize=1)")
    assert re.findall(r"\benviron\b|\bgetenv\b", "os.getenv('X')") == ["getenv"]


# --------------------------------------------------------------------------
# Los tests de otras features: solo la cuenta de rutas
# --------------------------------------------------------------------------


def test_f065_la_rama_solo_toca_los_tests_ajenos_declarados():
    cambiados = _diff_de_la_rama_o_saltar()

    tocados = sorted(
        r.removeprefix(SERVICIO)
        for r in cambiados
        if re.search(r"/tests(_bbdd/tests)?/", r) and not TESTS_DE_F065.match(r)
    )

    assert tocados == sorted(AMPLIADOS)


@pytest.mark.parametrize("relativa", sorted(AMPLIADOS))
def test_f065_en_cada_test_ajeno_solo_cambia_lo_declarado(relativa):
    _diff_de_la_rama_o_saltar()
    antes = _en_la_base(f"{SERVICIO}{relativa}")
    ahora = _actual(relativa)

    assert _quitadas(antes, ahora) == set(), "un test ampliado no pierde nada"
    assert _novedades(antes, ahora) == AMPLIADOS[relativa]


@pytest.mark.parametrize("relativa", sorted(AMPLIADOS))
def test_f065_ningun_test_ajeno_pierde_una_asercion(relativa):
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
    for funcion in exentas:
        assert sum(ahora[funcion].values()) == sum(antes[funcion].values()), funcion


def _lista_de_la_asercion(fuente: str, funcion: str) -> list[str]:
    """La lista literal de la única aserción `[...] == [...]` de un test."""
    for nodo in ast.parse(fuente).body:
        if isinstance(nodo, ast.FunctionDef) and nodo.name == funcion:
            (asercion,) = [a for a in ast.walk(nodo) if isinstance(a, ast.Assert)]
            return ast.literal_eval(asercion.test.comparators[0])  # type: ignore[attr-defined]
    raise AssertionError(f"no hay {funcion}")


def test_f065_a4bis_la_lista_de_motivos_de_f059_solo_gana_los_dos_al_final():
    _diff_de_la_rama_o_saltar()
    relativa = "tests/test_f059_volcado_dominio.py"
    funcion = "test_f059_r11_r18_los_motivos_de_exclusion"
    antes = _lista_de_la_asercion(_en_la_base(f"{SERVICIO}{relativa}"), funcion)
    ahora = _lista_de_la_asercion(_actual(relativa), funcion)

    assert ahora == [*antes, "duplicada_en_sigrid", "conflicto_sin_confirmar"]


def test_f065_a4bis_las_claves_del_ensayo_de_f059_solo_ganan_sigrid():
    _diff_de_la_rama_o_saltar()
    relativa = "tests/test_f059_volcado_http.py"

    def claves(fuente: str) -> set[str]:
        return ast.literal_eval(_definiciones(fuente)["CLAVES_DEL_ENSAYO"].split("=", 1)[1].strip())

    assert claves(_actual(relativa)) == claves(_en_la_base(f"{SERVICIO}{relativa}")) | {"sigrid"}


def _sentencias(fuente: str, nombre: str) -> list[str]:
    """Las sentencias de una función o de un método (`Clase.metodo`), sin docstring."""
    clase, _, metodo = nombre.rpartition(".")
    arbol = _sin_docstrings(ast.parse(fuente))
    nodos = arbol.body  # type: ignore[attr-defined]
    if clase:
        (nodo_clase,) = [n for n in nodos if isinstance(n, ast.ClassDef) and n.name == clase]
        nodos = nodo_clase.body
    (funcion,) = [n for n in nodos if isinstance(n, ast.FunctionDef) and n.name == metodo]
    return [ast.unparse(s) for s in funcion.body]


def test_f065_a4bis_el_doble_del_lector_es_lo_unico_que_gana_el_ensayo_de_f059():
    """`Mundo.ensayar` solo gana los dos argumentos de la guarda; `_componer`,
    solo la sustitución de `construir_reclamaciones_obra`. Ninguna otra línea."""
    _diff_de_la_rama_o_saltar()
    pipeline = "tests/test_f059_pipeline_volcado.py"
    antes = _sentencias(_en_la_base(f"{SERVICIO}{pipeline}"), "Mundo.ensayar")
    ahora = _sentencias(_actual(pipeline), "Mundo.ensayar")
    argumentos = ", reclamaciones=SinReclamacionesEnSigrid(), tip=708"
    assert [s.replace(argumentos, "", 1) for s in ahora] == antes
    assert sum(s.count(argumentos) for s in ahora) == 1

    http = "tests/test_f059_volcado_http.py"
    antes = _sentencias(_en_la_base(f"{SERVICIO}{http}"), "_componer")
    ahora = _sentencias(_actual(http), "_componer")
    sustitucion = (
        "monkeypatch.setattr(modulo, 'construir_reclamaciones_obra', "
        "lambda _ajustes: SinReclamacionesEnSigrid())"
    )
    assert [s for s in ahora if s != sustitucion] == antes
    assert ahora.count(sustitucion) == 1


def test_f065_la_cuenta_de_rutas_incluye_la_nueva():
    """La mitad que no depende de `git`: la cuenta que vigila F-010, con la ruta."""
    fuente = (RAIZ_DEL_SERVICIO / "tests" / "test_f010_endpoints_protegidos.py").read_text(encoding="utf-8")
    endpoints = ast.literal_eval(_definiciones(fuente)["ENDPOINTS"].split("=", 1)[1].strip())

    assert "revision/sigrid" in endpoints
    assert len(endpoints) == 25


def test_f065_los_controles_de_los_tests_no_son_ciegos():
    antes = 'X = 1\n\ndef test_a():\n    """Doc."""\n    assert 1 == 1\n    assert 2 == 2\n'
    pierde = antes.replace("    assert 2 == 2\n", "")

    assert _novedades(antes, pierde) == {"test_a"}
    assert _aserciones(antes)["test_a"] - _aserciones(pierde)["test_a"] == Counter({"2 == 2": 1})
    assert _aserciones(antes.replace("assert 1 == 1", 'assert 1 == 1, "otro"')) == _aserciones(antes)
    assert TESTS_DE_F065.match("services/postventa-api/tests/test_f065_http.py")
    assert not TESTS_DE_F065.match("services/postventa-api/tests/test_f056_revision_http.py")
    assert _declarado("progress/impl_F-065.md")
    assert _declarado(f"{SERVICIO}function_app.py")
    assert not _declarado(f"{SERVICIO}interface_adapters/api/revision.py")
    assert not _declarado(f"{SERVICIO}tests/test_f056_revision_http.py")
    assert not _declarado("specs/F-040-volcado-front/tasks.md")
