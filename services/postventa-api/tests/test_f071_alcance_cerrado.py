# services/postventa-api/tests/test_f071_alcance_cerrado.py
"""Lo que F-071 promete **no** tocar, comprobado (T11; R42, R43, R45, `design.md` §3.3, §3.4 y §10).

F-071 saca de Sigrid los desplegables de la plantilla y valida la importación
contra ellos. Roza la importación y la plantilla de F-036, la regla de casado
de F-060 y la lectura de ubicaciones de F-056. Cada frontera tiene aquí su
control:

| Frontera | Requisito | Qué se comprueba |
|---|---|---|
| Sigrid | **R42** | las tres consultas que ya existían, iguales carácter a carácter (huella fija y, en la rama, contra la base); `infrastructure/sigrid/**` sin cambios; ninguna pieza de F-071 nombra una escritura de la pasarela ni una ventana, ni importa un adaptador de escritura |
| Endpoints, variables, dependencias, DDL | **R42** | las rutas de `function_app.py`, las de la base; `config/settings.py` y los manifiestos sin cambios; ningún `.sql` nuevo ni cambiado; ninguna pieza de F-071 lee el entorno |
| Los ficheros de «No se toca» | **R43**, §3.4 | sin cambios: la revisión, el volcado, las equivalencias, la persistencia, la lectura aislada y `services/postventa-front/` |
| La parte lectora del generador | **R43**, §3.4 | en `excel_openpyxl.py`, el lector igual que en la base; solo cambian o se añaden las piezas declaradas del generador (§7.1) |
| La migración de F-036 | **R45**, §3.3 | los tres ficheros del script y sus dos tests, borrados en la rama y ausentes en el árbol; los dos scripts que se quedan, presentes; nadie los nombra |

## Las dos mitades

Con el patrón de `test_f060_alcance_cerrado.py`: **el del diff**, contra la
**base fija** de la feature (`ed935ad`, cabecera de `tasks.md`; no
`git merge-base`, que se movería si `dev` avanzara) y hasta el **árbol de
trabajo**, con las tres guardas de F-030 para no dejar `dev` en rojo cuando la
rama se mergee; y **el que no depende de `git`**, que se comprueba siempre.

**Sin red, sin base de datos, sin IA y sin reloj.** Los controles del diff
llaman a `git`, que es un proceso local de solo lectura.
"""

from __future__ import annotations

import ast
import hashlib
import re
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]
RAIZ_DEL_SERVICIO = RAIZ / "services" / "postventa-api"

#: La rama en la que los controles del diff tienen algo que mirar.
RAMA_DE_LA_FEATURE = "feature/F-071-plantilla-desde-sigrid"

#: La base fija de la feature (`tasks.md`, cabecera; `progress/impl_F-071.md`).
BASE_FIJA = "ed935ad"

SERVICIO = "services/postventa-api/"

#: Las piezas de código que F-071 crea o cambia (`design.md` §3.1 y §3.2), sin
#: `errores.py` ni `function_app.py`, que son de todo el servicio y en los que
#: F-071 solo añade un código (`version_anterior`) y dos docstrings.
PIEZAS_DE_F071 = (
    "application/pipelines/contexto_importacion.py",
    "application/pipelines/paso_importacion.py",
    "application/pipelines/plantilla.py",
    "domain/models/casado_con_lista.py",
    "domain/models/importacion.py",
    "domain/models/normalizacion.py",
    "domain/models/plantilla_incidencias.py",
    "domain/ports/hoja_calculo.py",
    "infrastructure/documentos/excel_openpyxl.py",
    "infrastructure/documentos/plantilla_yaml.py",
    "interface_adapters/api/importar.py",
    "interface_adapters/api/plantilla.py",
)

#: Las tres consultas de Sigrid que F-071 usa (R42), por módulo y constante, con
#: la huella `sha256` de su texto en la base fija `ed935ad`.
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
}

#: Lo que nombraría una escritura en Sigrid o una ventana de escritura.
MARCAS_DE_ESCRITURA = (
    "sql/write",
    "partes-reclamacion",
    "concepto-grafico",
    "_habilitado",
)

#: Los adaptadores de Sigrid que escriben: ninguna pieza de F-071 los importa.
ADAPTADORES_DE_ESCRITURA = (
    "infrastructure.sigrid.escrituras",
    "infrastructure.sigrid.graficos",
    "infrastructure.sigrid.volcado",
)

#: R43 y `design.md` §3.4: directorios enteros que la rama no toca.
DIRECTORIOS_INTOCABLES = (
    SERVICIO + "infrastructure/sigrid/",
    SERVICIO + "infrastructure/persistencia/",
    "services/postventa-front/",
)

#: R43 y `design.md` §3.4: ficheros sueltos que la rama no toca.
FICHEROS_INTOCABLES = tuple(
    SERVICIO + ruta
    for ruta in (
        # La revisión.
        "domain/models/revision.py",
        "application/pipelines/revision.py",
        "interface_adapters/api/revision.py",
        "domain/ports/revision.py",
        # El volcado (F-059/F-040).
        "domain/models/volcado.py",
        "domain/models/situacion_volcado.py",
        "application/pipelines/volcado.py",
        # Las equivalencias.
        "domain/models/equivalencias.py",
        "application/pipelines/equivalencias.py",
        "interface_adapters/api/equivalencias.py",
        "domain/ports/equivalencias.py",
        # La lectura aislada.
        "infrastructure/documentos/lector_aislado.py",
        "infrastructure/documentos/ejecutor_aislado.py",
        # Las variables de entorno.
        "config/settings.py",
        "local.settings.json.example",
    )
)

#: Los volcados de la aplicación, por patrón (`application/pipelines/volcado*.py`).
PATRON_DE_LOS_VOLCADOS = re.compile(
    rf"^{re.escape(SERVICIO)}application/pipelines/volcado[^/]*\.py$"
)

#: Los manifiestos de dependencias (R42: ninguna dependencia nueva).
MANIFIESTOS = (
    SERVICIO + "requirements.txt",
    SERVICIO + "requirements-dev.txt",
    "requirements-dev.txt",
)

#: El script de migración de F-036 y sus tests (R45, `design.md` §3.3).
RETIRADOS = tuple(
    SERVICIO + ruta
    for ruta in (
        "scripts/migrar_excel_f036.py",
        "scripts/migracion_f036.py",
        "scripts/migracion_f036_correcciones.yaml",
        "tests/test_f036_migracion.py",
        "tests/test_f036_migracion_contenido.py",
    )
)

#: Los dos scripts de F-036 que se quedan (`design.md` §3.3).
SE_QUEDAN = (
    SERVICIO + "scripts/medir_catalogos_f036.py",
    SERVICIO + "scripts/contar_elementos_xml_f036.py",
)

#: Los ficheros que pueden nombrar la migración retirada: los que vigilan que
#: se fue (el de F-036 lo cita en su control, este la lista y el de la
#: documentación comprueba que los documentos dicen que se retiró).
PUEDEN_NOMBRAR_LA_MIGRACION = frozenset(
    {
        SERVICIO + "tests/test_f036_alcance_cerrado.py",
        SERVICIO + "tests/test_f071_alcance_cerrado.py",
        SERVICIO + "tests/test_f071_documentacion.py",
    }
)

#: `excel_openpyxl.py`: lo que F-071 declara cambiar o añadir en el generador
#: (`design.md` §7.1). Todo lo demás —el lector entero incluido— queda igual.
GENERADOR = SERVICIO + "infrastructure/documentos/excel_openpyxl.py"
CAMBIAN_EN_EL_GENERADOR = frozenset(
    {"GeneradorPlantillaOpenpyxl", "GeneradorPlantillaOpenpyxl.generar", "LISTAS", "_validacion"}
)
NUEVAS_EN_EL_GENERADOR = frozenset(
    {
        "FORMULA_UBICACION",
        "GeneradorPlantillaOpenpyxl._ubicaciones",
        "PREFIJO_UBICACIONES",
        "TABLA_UBICACIONES",
        "UBICACIONES_NINGUNA",
        "_exigir_distintas",
    }
)
#: La parte lectora de `excel_openpyxl.py` (R43): idéntica a la de la base.
PARTE_LECTORA = frozenset(
    {"LectorPlantillaOpenpyxl", "LectorPlantillaOpenpyxl.leer", "_leer_libro", "leer_en_hijo"}
)


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
    """Las rutas de `rutas` que R43 y §3.4 prohíben tocar."""
    return sorted(
        ruta
        for ruta in rutas
        if ruta.startswith(DIRECTORIOS_INTOCABLES)
        or ruta in FICHEROS_INTOCABLES
        or PATRON_DE_LOS_VOLCADOS.match(ruta)
    )


def sql_tocados(rutas: list[str]) -> list[str]:
    """Las rutas `.sql` de `rutas`: R42 no admite ni uno nuevo ni uno cambiado."""
    return sorted(ruta for ruta in rutas if ruta.lower().endswith(".sql"))


def marcas_de_escritura(fuente: str) -> list[str]:
    """Las marcas de `MARCAS_DE_ESCRITURA` que aparecen en `fuente`, sin mayúsculas."""
    plegada = fuente.casefold()
    return [marca for marca in MARCAS_DE_ESCRITURA if marca in plegada]


def importa_escrituras(fuente: str) -> list[str]:
    """Los adaptadores de escritura de Sigrid que importa `fuente`."""
    importados: set[str] = set()
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module)
            importados.update(f"{nodo.module}.{alias.name}" for alias in nodo.names)
        elif isinstance(nodo, ast.Import):
            importados.update(alias.name for alias in nodo.names)
    return sorted(
        modulo
        for modulo in importados
        if any(modulo == a or modulo.startswith(a + ".") for a in ADAPTADORES_DE_ESCRITURA)
    )


def lee_el_entorno(fuente: str) -> bool:
    """Si `fuente` lee variables de entorno (`os.environ`, `os.getenv`, `putenv`)."""
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Attribute) and nodo.attr in {"environ", "getenv", "putenv"}:
            return True
        if isinstance(nodo, ast.ImportFrom) and nodo.module == "os":
            if any(a.name in {"environ", "getenv", "putenv"} for a in nodo.names):
                return True
    return False


def rutas_de(fuente: str) -> set[str]:
    """Las rutas HTTP que registra `function_app.py`: cada `route="…"`."""
    return set(re.findall(r'route="([^"]+)"', fuente))


def definiciones(fuente: str) -> dict[str, str]:
    """Cada definición de nivel de módulo, por nombre, como en F-060.

    Las funciones y las asignaciones, por su nombre; una clase, por su nombre
    (con su cuerpo entero) y cada método aparte, como `Clase.metodo`.
    """
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


def _leer(ruta_en_el_servicio: str) -> str:
    return (RAIZ_DEL_SERVICIO / ruta_en_el_servicio).read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Los controles cazan: cada regla, contra un caso que tiene que cazar
# --------------------------------------------------------------------------


def test_f071_t11_los_controles_leen_algo():
    """Un control que no lee nada da verde para siempre: lo que leen existe."""
    for ruta in (*FICHEROS_INTOCABLES, *SE_QUEDAN, *MANIFIESTOS[:2]):
        assert (RAIZ / ruta).is_file(), ruta
    for directorio in DIRECTORIOS_INTOCABLES:
        assert (RAIZ / directorio).is_dir(), directorio
    for pieza in PIEZAS_DE_F071:
        assert (RAIZ_DEL_SERVICIO / pieza).is_file(), pieza
    assert len(rutas_de(_leer("function_app.py"))) > 20
    assert PARTE_LECTORA <= set(definiciones(_leer(GENERADOR.removeprefix(SERVICIO))))


def test_f071_t11_el_control_de_lo_intocable_caza():
    rutas = [
        SERVICIO + "infrastructure/sigrid/consultas_catalogo.py",
        SERVICIO + "infrastructure/persistencia/sql/16_nueva.sql",
        "services/postventa-front/importar.html",
        SERVICIO + "domain/models/revision.py",
        SERVICIO + "application/pipelines/volcado_ensayo.py",
        SERVICIO + "config/settings.py",
        SERVICIO + "domain/models/importacion.py",
    ]

    assert tocados_intocables(rutas) == sorted(rutas[:-1])


def test_f071_t11_el_control_del_sql_caza():
    assert sql_tocados(["a/b/16_nueva.SQL", "a/b/c.py"]) == ["a/b/16_nueva.SQL"]


def test_f071_t11_los_controles_del_codigo_cazan():
    escribe = (
        "from infrastructure.sigrid.escrituras import EscrituraSigrid\n"
        "import os\n"
        "RUTA = '/api/sql/write'\n"
        "VENTANA = os.environ.get('VOLCADO_HABILITADO')\n"
    )

    assert marcas_de_escritura(escribe) == ["sql/write", "_habilitado"]
    assert importa_escrituras(escribe) == [
        "infrastructure.sigrid.escrituras",
        "infrastructure.sigrid.escrituras.EscrituraSigrid",
    ]
    assert lee_el_entorno(escribe)
    assert not lee_el_entorno("from os import path\n")
    assert rutas_de('@app.route(route="plantilla", methods=["GET"])') == {"plantilla"}


# --------------------------------------------------------------------------
# R42 · sin `git`: las consultas, las escrituras y el entorno
# --------------------------------------------------------------------------


@pytest.mark.parametrize("modulo,constante", list(CONSULTAS_DE_SIGRID))
def test_f071_r42_las_consultas_de_sigrid_iguales_caracter_a_caracter(modulo, constante):
    """La huella de la base: cambiar una letra de la consulta cambia la huella."""
    import importlib

    texto = getattr(importlib.import_module(modulo), constante)

    assert hashlib.sha256(texto.encode("utf-8")).hexdigest() == CONSULTAS_DE_SIGRID[
        (modulo, constante)
    ]


@pytest.mark.parametrize("pieza", PIEZAS_DE_F071)
def test_f071_r42_ninguna_pieza_nombra_una_escritura_ni_una_ventana(pieza):
    assert marcas_de_escritura(_leer(pieza)) == [], pieza


@pytest.mark.parametrize("pieza", PIEZAS_DE_F071)
def test_f071_r42_ninguna_pieza_importa_un_adaptador_de_escritura(pieza):
    assert importa_escrituras(_leer(pieza)) == [], pieza


@pytest.mark.parametrize("pieza", PIEZAS_DE_F071)
def test_f071_r42_ninguna_pieza_lee_el_entorno(pieza):
    assert not lee_el_entorno(_leer(pieza)), pieza


# --------------------------------------------------------------------------
# R45 · sin `git`: la migración, retirada
# --------------------------------------------------------------------------


def test_f071_r45_la_migracion_no_esta_y_los_dos_scripts_se_quedan():
    for ruta in RETIRADOS:
        assert not (RAIZ / ruta).exists(), f"{ruta} sigue en el árbol"
    for ruta in SE_QUEDAN:
        assert (RAIZ / ruta).is_file(), f"{ruta} ya no está"


def test_f071_r45_ningun_fichero_del_servicio_nombra_la_migracion():
    nombres = ("migrar_excel_f036", "migracion_f036")
    nombran = sorted(
        ruta.relative_to(RAIZ).as_posix()
        for ruta in (RAIZ / "services").rglob("*")
        if ruta.is_file()
        and ruta.suffix in {".py", ".yaml", ".yml", ".json", ".ps1", ".js", ".html", ".toml"}
        and "__pycache__" not in ruta.parts
        and ".venv" not in ruta.parts
        and ruta.relative_to(RAIZ).as_posix() not in PUEDEN_NOMBRAR_LA_MIGRACION
        and any(n in ruta.read_text(encoding="utf-8", errors="replace") for n in nombres)
    )

    assert nombran == []


# --------------------------------------------------------------------------
# R42, R43, R45 · contra la base fija, en la rama
# --------------------------------------------------------------------------


def test_f071_r43_la_rama_no_toca_lo_intocable():
    rutas = [ruta for _, ruta in _diff_de_la_rama_o_saltar()]

    assert tocados_intocables(rutas) == []


def test_f071_r42_la_rama_no_trae_ni_cambia_ningun_sql():
    rutas = [ruta for _, ruta in _diff_de_la_rama_o_saltar()]

    assert sql_tocados(rutas) == []


def test_f071_r42_la_rama_no_cambia_ningun_manifiesto_de_dependencias():
    rutas = {ruta for _, ruta in _diff_de_la_rama_o_saltar()}

    assert rutas.isdisjoint(MANIFIESTOS)


def test_f071_r42_la_rama_no_registra_ningun_endpoint_nuevo():
    _diff_de_la_rama_o_saltar()
    ruta = SERVICIO + "function_app.py"

    assert rutas_de(_leer("function_app.py")) == rutas_de(_en_la_base(ruta))


@pytest.mark.parametrize(
    "modulo",
    (
        "infrastructure/sigrid/consultas_catalogo.py",
        "infrastructure/sigrid/consultas_ubicaciones_validas.py",
    ),
)
def test_f071_r42_las_consultas_de_sigrid_son_las_de_la_base(modulo):
    """El fichero entero, carácter a carácter, contra la base fija."""
    _diff_de_la_rama_o_saltar()

    assert _leer(modulo) == _en_la_base(SERVICIO + modulo)


def test_f071_r42_las_huellas_son_las_de_la_base():
    """La huella fija de arriba es la del texto de la base, no la de hoy."""
    _diff_de_la_rama_o_saltar()
    for (modulo, constante), huella in CONSULTAS_DE_SIGRID.items():
        fuente = _en_la_base(SERVICIO + modulo.replace(".", "/") + ".py")
        valores = [
            ast.literal_eval(nodo.value)
            for nodo in ast.parse(fuente).body
            if isinstance(nodo, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == constante for t in nodo.targets)
        ]
        assert len(valores) == 1 and isinstance(valores[0], str), constante
        assert hashlib.sha256(valores[0].encode("utf-8")).hexdigest() == huella, constante


def test_f071_r43_la_parte_lectora_del_generador_es_la_de_la_base():
    _diff_de_la_rama_o_saltar()
    hoy = definiciones(_leer(GENERADOR.removeprefix(SERVICIO)))
    antes = definiciones(_en_la_base(GENERADOR))

    for nombre in PARTE_LECTORA:
        assert hoy[nombre] == antes[nombre], f"{nombre} cambió"


def test_f071_r43_en_el_generador_solo_cambia_lo_declarado():
    _diff_de_la_rama_o_saltar()
    hoy = definiciones(_leer(GENERADOR.removeprefix(SERVICIO)))
    antes = definiciones(_en_la_base(GENERADOR))

    cambiadas = {n for n in hoy if n in antes and hoy[n] != antes[n]}
    nuevas = set(hoy) - set(antes)
    quitadas = set(antes) - set(hoy)

    assert cambiadas <= CAMBIAN_EN_EL_GENERADOR, sorted(cambiadas - CAMBIAN_EN_EL_GENERADOR)
    assert nuevas <= NUEVAS_EN_EL_GENERADOR, sorted(nuevas - NUEVAS_EN_EL_GENERADOR)
    assert quitadas == set()


def test_f071_r45_la_rama_borra_la_migracion_y_sus_tests():
    cambios = _diff_de_la_rama_o_saltar()
    borrados = {ruta for estado, ruta in cambios if estado == "D"}

    assert set(RETIRADOS) <= borrados
    assert borrados.isdisjoint(SE_QUEDAN)
