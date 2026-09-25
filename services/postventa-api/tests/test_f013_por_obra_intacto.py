# services/postventa-api/tests/test_f013_por_obra_intacto.py
"""F-013 T10 · R2: sin resolutor, el paso de archivo es **exactamente** el de hoy.

`SHAREPOINT_ESTRUCTURA=por_obra` es el valor por omisión y lo que está
desplegado hasta el corte (`design.md` §7.3). R2 exige que en esa estrategia el
paso componga la carpeta y el nombre como F-006, **sin llamar a Sigrid ni
listar ninguna carpeta**, y que los tests de F-006 sigan en verde sin tocarlos.

## Dos mitades, como `test_f032_alcance_cerrado.py`

- **La que no depende de `git`** se comprueba siempre, en cualquier rama y
  para siempre: sin resolutor, las llamadas y su orden son las de F-006 y
  F-019; un archivador que además sabe listar y crear carpetas no recibe
  ninguna de esas llamadas; y L1 sigue comparando la carpeta.
- **La del diff** mira lo que esta rama cambió desde `dev`: ningún test de
  F-006, F-019, F-031, F-032 ni F-034 se ha tocado; de los de F-033 solo
  `test_f033_r21_la_firma_no_ofrece_ninguna_forma_de_forzar` (T10 bis), y solo
  para añadir `resolver_destino`; y las piezas de F-019 y F-033 de
  `paso_archivo.py` son las mismas, sentencia a sentencia. Fuera de la rama
  de F-013, o ya mergeada, se **salta** (el defecto de F-030: un control del
  diff sin diff que mirar no puede ponerse rojo).

Sin red, sin base de datos y sin IA: `git` es un proceso local de solo
lectura.
"""

from __future__ import annotations

import ast
import inspect
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import application.pipelines.paso_archivo as paso
import pytest
from domain.models.estado import SituacionParte
from domain.models.persistencia import EstadoArchivo, TrazaArchivo

from tests.utiles_destino import ExploradorFalso
from tests.utiles_sharepoint import (
    CARPETA_BASE,
    ArchivoPortFalso,
    RepositorioFalso,
    contexto_apto,
)
from tests.utiles_validacion import HASH_DE_PRUEBA

RAIZ = Path(__file__).resolve().parents[3]
SERVICIO = "services/postventa-api/"

#: La rama en la que los controles del diff tienen algo que mirar (ficha de
#: F-013 en `harness/features.json`, campo `branch`).
RAMA_DE_LA_FEATURE = "feature/F-013-archivo-posventa"

AHORA = datetime(2026, 9, 24, 10, 0, tzinfo=UTC)

CARPETA_DE_HOY = f"{CARPETA_BASE}/0677"
NOMBRE_DE_HOY = "0677 - RS26.08 - 0123 PARTE FIRMADO.pdf"

#: Las llamadas del paso de hoy, en su orden (F-006 + la garantía de F-019).
LLAMADAS_DE_HOY = [
    "repositorio.guardar_archivo(pendiente)",
    "archivador.asegurar_carpeta",
    "archivador.buscar",
    "archivador.subir",
    "repositorio.guardar_archivo(archivado)",
]


class _ArchivadorQueTambienExplora(ArchivoPortFalso):
    """Un archivador con los dos puertos, como el de Graph en `posventa`."""

    def __init__(self, registro: list[str]) -> None:
        super().__init__(registro=registro)
        self.explorador = ExploradorFalso({"": ("0677",)}, registro=registro)

    def listar_carpetas(self, *, carpeta: str):
        return self.explorador.listar_carpetas(carpeta=carpeta)

    def crear_subcarpeta(self, *, padre: str, nombre: str) -> None:
        self.explorador.crear_subcarpeta(padre=padre, nombre=nombre)


def _archivar(archivador, *, archivo: TrazaArchivo | None = None, **extra):
    ctx = contexto_apto()
    repositorio = RepositorioFalso(
        registro=archivador.registro,
        situacion=SituacionParte(validacion=ctx.validacion, archivo=archivo),
    )
    return paso.paso_archivo(
        ctx, archivador, repositorio, carpeta_base=CARPETA_BASE, ahora=AHORA, **extra
    )


# ==========================================================================
# La mitad que no depende de `git`
# ==========================================================================


def test_f013_r2_sin_resolutor_el_paso_hace_las_mismas_llamadas_que_hoy():
    """R2 · mismo orden, misma carpeta `<base>/<obra>`, mismo nombre."""
    registro: list[str] = []
    archivador = ArchivoPortFalso(registro=registro)

    ctx = _archivar(archivador)

    assert registro == LLAMADAS_DE_HOY
    assert archivador.llamadas[0] == ("asegurar_carpeta", {"carpeta": CARPETA_DE_HOY})
    assert ctx.archivo.carpeta == CARPETA_DE_HOY
    assert ctx.archivo.nombre_fichero == NOMBRE_DE_HOY
    assert ctx.avisos == []


def test_f013_r2_sin_resolutor_no_se_lista_ni_se_crea_aunque_se_pueda():
    """R2 · con un archivador que sabe explorar, sin resolutor no explora."""
    registro: list[str] = []
    archivador = _ArchivadorQueTambienExplora(registro)

    ctx = _archivar(archivador)

    assert registro == LLAMADAS_DE_HOY
    assert archivador.explorador.llamadas == []
    assert ctx.archivo.carpeta == CARPETA_DE_HOY


def test_f013_r2_resolver_destino_a_none_es_lo_mismo_que_no_pasarlo():
    """R2 · el valor por omisión explícito no cambia nada."""
    registro: list[str] = []

    ctx = _archivar(ArchivoPortFalso(registro=registro), resolver_destino=None)

    assert registro == LLAMADAS_DE_HOY
    assert ctx.archivo.carpeta == CARPETA_DE_HOY


def test_f013_r2_en_por_obra_l1_sigue_comparando_la_carpeta():
    """R2, F-033 R14 · lo que R45 relaja es **solo** de `posventa`."""
    registro: list[str] = []
    archivada = TrazaArchivo(
        hash_parte=HASH_DE_PRUEBA,
        estado=EstadoArchivo.ARCHIVADO,
        nombre_fichero=NOMBRE_DE_HOY,
        carpeta=f"{CARPETA_BASE}/0677-antigua",
    )

    ctx = _archivar(ArchivoPortFalso(registro=registro), archivo=archivada)

    assert ctx.avisos == [paso.AVISO_YA_ARCHIVADO, paso.AVISO_ARCHIVADO_EN_OTRO_DESTINO]
    assert registro == []


def test_f013_r2_la_firma_de_en_otro_destino_no_cambia():
    """`tasks.md` T10 · «sin tocar la firma de `_en_otro_destino`»."""
    assert list(inspect.signature(paso._en_otro_destino).parameters) == [
        "traza",
        "destino",
        "drive_id_vigente",
    ]


# ==========================================================================
# La mitad del diff (solo en la rama de F-013 mientras no esté mergeada)
# ==========================================================================


def _git(*argumentos: str) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            ["git", *argumentos], cwd=RAIZ, capture_output=True, text=True,
            encoding="utf-8", check=False,
        )
    except (OSError, ValueError):  # pragma: no cover - no hay git en el PATH
        return None


def _base_de_la_rama_o_saltar() -> str:
    """El commit donde la rama se separó de `dev`; o se salta el control."""
    rama = _git("rev-parse", "--abbrev-ref", "HEAD")
    base = _git("merge-base", "dev", "HEAD")
    if rama is None or base is None or base.returncode != 0:  # pragma: no cover
        pytest.skip("no hay 'git' o la rama 'dev' no está en este clon")
    ya_en_dev = _git("merge-base", "--is-ancestor", "HEAD", "dev")
    if rama.stdout.strip() != RAMA_DE_LA_FEATURE or (
        ya_en_dev is not None and ya_en_dev.returncode == 0
    ):
        pytest.skip(
            f"este control vive en {RAMA_DE_LA_FEATURE} mientras no esté "
            "mergeada; la mitad que no depende de 'git' se comprueba siempre"
        )
    return base.stdout.strip()


def _cambiados(base: str) -> list[str]:
    diff = _git("diff", "--name-only", base)
    assert diff is not None and diff.returncode == 0
    return [linea.strip() for linea in diff.stdout.splitlines() if linea.strip()]


def _en_la_base(base: str, ruta: str) -> str:
    fuente = _git("show", f"{base}:{ruta}")
    assert fuente is not None and fuente.returncode == 0, ruta
    return fuente.stdout


def _funciones(fuente: str) -> dict[str, str]:
    """`nombre -> ast.dump` de cada función de primer nivel del módulo."""
    return {
        nodo.name: ast.dump(nodo)
        for nodo in ast.parse(fuente).body
        if isinstance(nodo, ast.FunctionDef)
    }


def test_f013_r2_el_control_del_diff_mira_una_lista_con_el_paso():
    """El control de los controles: el diff no puede venir vacío."""
    cambiados = _cambiados(_base_de_la_rama_o_saltar())

    assert f"{SERVICIO}application/pipelines/paso_archivo.py" in cambiados


#: Los prefijos de los tests de otras fichas que esta rama no toca (§11).
TESTS_AJENOS = ("test_f006_", "test_f019_", "test_f031_", "test_f032_", "test_f034_")

#: El único test de F-033 que se toca, y el único motivo (T10 bis).
FICHERO_DE_T10_BIS = f"{SERVICIO}tests/test_f033_l1_desde_el_almacen.py"
TEST_DE_T10_BIS = "test_f033_r21_la_firma_no_ofrece_ninguna_forma_de_forzar"


#: La única excepción entre los tests de F-006, con nombre (T16, R30).
#:
#: `design.md` §2.2 y `tasks.md` T16 mandan añadir el barrido del host del
#: inquilino a **este** fichero de F-006, y el control de abajo lo prohibía:
#: la spec se contradecía (§2.2 frente a la fila de §11). Se resuelve como
#: T10 bis con el test de F-033: el fichero se nombra, y el control siguiente
#: exige que su diff **solo añada** —ni un test de F-006 cambia ni desaparece—.
#: Recuadro del 2026-09-24 en `progress/impl_F-013.md`, «Bloque 6».
FICHERO_DE_T16 = f"{SERVICIO}tests/test_f006_repo_sin_identificadores.py"


def test_f013_r2_los_tests_de_otras_fichas_no_se_han_tocado():
    """R2, `design.md` §11 · F-006, F-019, F-031, F-032, F-034: ni una línea.

    Salvo `FICHERO_DE_T16`, que solo puede crecer (control siguiente).
    """
    cambiados = _cambiados(_base_de_la_rama_o_saltar())

    ajenos = [
        ruta for ruta in cambiados
        if ruta.startswith(f"{SERVICIO}tests/")
        and Path(ruta).name.startswith(TESTS_AJENOS)
        and ruta != FICHERO_DE_T16
    ]
    de_f033 = [
        ruta for ruta in cambiados
        if ruta.startswith(f"{SERVICIO}tests/") and Path(ruta).name.startswith("test_f033_")
    ]
    assert ajenos == []
    assert de_f033 in ([], [FICHERO_DE_T10_BIS])


def _nombre_de_sentencia(nodo: ast.stmt) -> str:
    """Cómo se llama lo que declara una sentencia de primer nivel."""
    if isinstance(nodo, ast.FunctionDef | ast.ClassDef):
        return nodo.name
    if isinstance(nodo, ast.Assign):
        return ",".join(objetivo.id for objetivo in nodo.targets if isinstance(objetivo, ast.Name))
    if isinstance(nodo, ast.Import | ast.ImportFrom):
        return ",".join(alias.name for alias in nodo.names)
    return type(nodo).__name__


def test_f013_t16_del_barrido_de_f006_solo_se_anade_lo_del_host():
    """T16 · `test_f006_repo_sin_identificadores.py` solo crece, y solo con R30.

    Cada sentencia de primer nivel que tenía en la base de la rama sigue ahí,
    **idéntica** (`ast.dump`) y en el mismo orden; el docstring del módulo solo
    gana texto al final; y lo nuevo es de R30: el `import re`, los tests
    `test_f013_r30_*` y las piezas con «host» en el nombre. Así ningún test de
    F-006 puede cambiar ni desaparecer por la puerta que abre la excepción.
    """
    base = _base_de_la_rama_o_saltar()
    antes = ast.parse(_en_la_base(base, FICHERO_DE_T16))
    hoy = ast.parse((RAIZ / FICHERO_DE_T16).read_text(encoding="utf-8"))

    assert ast.get_docstring(hoy, clean=False).startswith(ast.get_docstring(antes, clean=False))

    sentencias_de_antes = [ast.dump(nodo) for nodo in antes.body[1:]]
    sentencias_de_hoy = iter(ast.dump(nodo) for nodo in hoy.body[1:])
    # Subsecuencia: cada una de antes aparece, en orden, entre las de hoy.
    assert all(
        any(sentencia == de_hoy for de_hoy in sentencias_de_hoy) for sentencia in sentencias_de_antes
    )

    nuevas = [
        _nombre_de_sentencia(nodo) for nodo in hoy.body[1:] if ast.dump(nodo) not in sentencias_de_antes
    ]
    assert nuevas, "el barrido del host de R30 no está en el fichero"
    assert [
        nombre
        for nombre in nuevas
        if not (nombre == "re" or nombre.startswith("test_f013_r30_") or "host" in nombre.lower())
    ] == []


def test_f013_t10_bis_de_los_tests_de_f033_solo_cambia_el_de_la_firma():
    """T10 bis · el diff de ese fichero se limita al conjunto y al recuadro."""
    base = _base_de_la_rama_o_saltar()
    antes = _funciones(_en_la_base(base, FICHERO_DE_T10_BIS))
    hoy = _funciones((RAIZ / FICHERO_DE_T10_BIS).read_text(encoding="utf-8"))

    assert set(hoy) == set(antes)
    distintas = sorted(nombre for nombre in hoy if hoy[nombre] != antes[nombre])
    assert distintas in ([], [TEST_DE_T10_BIS])

    def _conjunto(fuente: str) -> set[str]:
        (funcion,) = [
            nodo for nodo in ast.parse(fuente).body
            if isinstance(nodo, ast.FunctionDef) and nodo.name == TEST_DE_T10_BIS
        ]
        (conjunto,) = [nodo for nodo in ast.walk(funcion) if isinstance(nodo, ast.Set)]
        return {elemento.value for elemento in conjunto.elts}

    ganados = _conjunto((RAIZ / FICHERO_DE_T10_BIS).read_text(encoding="utf-8")) - _conjunto(
        _en_la_base(base, FICHERO_DE_T10_BIS)
    )
    assert ganados == {"resolver_destino"}


#: Las piezas de F-006, F-019 y F-033 de `paso_archivo.py` que T10 no toca.
#: `_subir` no está: pierde `asegurar_carpeta`, que pasa al cuerpo del paso
#: porque en `posventa` se sustituye por las creaciones (R15).
PIEZAS_INTACTAS = (
    "_devolver_la_guardada",
    "_en_otro_destino",
    "_avisar_del_intento_anterior",
    "_tomar_la_de_la_otra_peticion",
    "_registrar_si_no_se_aplico",
    "_dejar_constancia_previa",
    "_dejar_constancia",
    "_exigir_admitido",
    "_ya_archivado",
    "_traza_de_exito",
    "_traza_de_error",
)


@pytest.mark.parametrize("pieza", PIEZAS_INTACTAS)
def test_f013_r2_las_piezas_de_f019_y_f033_del_paso_no_cambian(pieza):
    """R2, R21 · sentencia a sentencia, como estaban en la base de la rama."""
    ruta = f"{SERVICIO}application/pipelines/paso_archivo.py"
    base = _base_de_la_rama_o_saltar()

    antes = _funciones(_en_la_base(base, ruta))
    hoy = _funciones((RAIZ / ruta).read_text(encoding="utf-8"))

    assert hoy[pieza] == antes[pieza]
