# services/postventa-api/tests/test_f033_alcance_cerrado.py
"""Lo que F-033 promete **no** tocar, comprobado (T10; `design.md` §1.3).

F-033 conecta L1 —la capa **traza** del paso 6— con el almacén, y eso vive en
dos sitios: la persistencia propia (una consulta que ya existía, un `WHERE` más
en un `upsert` que ya existía) y el paso de archivo con su endpoint. Todo lo
demás está fuera, y cada frontera tiene aquí su control:

| Frontera | Por qué no se toca |
|---|---|
| `infrastructure/persistencia/sql/` | **Sin DDL** (regla dura 1): `archivos` ya tenía clave por `hash_parte` y las ocho columnas |
| `services/postventa-front/` | El contrato HTTP de `/api/archivar` no cambia (R23) |
| `paso_grafico.py`, `paso_cierre.py`, `adjuntar.py`, `cerrar.py` | Su «consta archivado» sale del cuerpo y es un defecto, pero arreglarlo cambia las puertas de dos escrituras en el ERP de producción: es **D-6**, ficha aparte (F-034) |
| `domain/models/nombrado.py` | El origen del código de obra y del número de incidencia es **F-031** |

**Sin red, sin base de datos, sin IA y sin reloj.** Los controles del diff
llaman a `git`, que es un proceso local de solo lectura.

## Por qué un fichero propio

`tasks.md` T10 lo deja escrito: «en `test_f033_l1_desde_el_almacen.py` (o
fichero propio si crece)». Crece: son ocho controles con su maquinaria de
`git`, y mezclados con los requisitos de L1 diluirían un fichero que mide lo que
la feature **hace**. Este mide lo que la feature **se prohíbe**, como
`test_f032_alcance_cerrado.py`, del que copia el criterio.

## Las dos mitades, y las tres guardas del diff

Cada frontera tiene **dos** controles:

1. **el del diff** (`git diff --name-only dev...HEAD`): «esta rama no lo tocó».
   Deja de tener algo que mirar en cuanto la rama se mergea, así que lleva las
   tres guardas que F-030 tuvo que inventar el 2026-09-17 para no dejar `dev`
   en rojo —`RAMA_DE_LA_FEATURE`, `_fuera_de_la_rama_de_la_feature` y
   `_la_rama_ya_esta_en_dev`—. Dentro de la rama de la feature se ejecutan
   enteros;
2. **el que no depende de `git`**, que se comprueba siempre, en cualquier rama
   y para siempre: «y hoy sigue siendo lo que tiene que ser».
"""

from __future__ import annotations

import io
import subprocess
import tokenize
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]

#: La raíz del servicio, de donde cuelga el código de producción.
RAIZ_DEL_SERVICIO = RAIZ / "services" / "postventa-api"

#: La rama en la que los controles del diff tienen algo que mirar. Sale de la
#: ficha de F-033 en `harness/features.json`, campo `branch`.
RAMA_DE_LA_FEATURE = "feature/F-033-l1-traza-archivo"


# --------------------------------------------------------------------------
# Preguntarle a `git` qué ha tocado esta rama, sin poder tumbar la suite
# --------------------------------------------------------------------------


def _ficheros_cambiados_en_la_rama() -> list[str] | None:
    """`git diff --name-only dev...HEAD`, o `None` si no se puede preguntar.

    Local y de solo lectura. `None` cuando no hay `git` o `dev` no está en este
    clon (un `checkout` superficial): eso no es un fallo de la feature.

    `dev...HEAD` (tres puntos) y no `dev..HEAD`: interesa lo que ha cambiado
    **esta rama** desde que se separó, no lo que haya entrado en `dev` después.
    """
    try:
        dev = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", "dev"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
        )
        if dev.returncode != 0:
            return None
        diff = subprocess.run(
            ["git", "diff", "--name-only", "dev...HEAD"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):  # pragma: no cover - no hay git en el PATH
        return None
    if diff.returncode != 0:  # pragma: no cover - el repositorio no está sano
        return None
    return [linea.strip() for linea in diff.stdout.splitlines() if linea.strip()]


def _rama_actual() -> str | None:
    """El nombre de la rama de trabajo, o `None` si no se puede saber."""
    try:
        resultado = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):  # pragma: no cover - no hay git en el PATH
        return None
    if resultado.returncode != 0:  # pragma: no cover - repositorio no sano
        return None
    return resultado.stdout.strip() or None


def _la_rama_ya_esta_en_dev() -> bool:
    """`True` cuando `HEAD` ya forma parte de `dev`: la rama cumplió su ciclo.

    Cubre el `checkout` de la rama **después** de mergearla, cuando el diff
    viene vacío sin que sea un fallo. Un diff vacío **sin** estar mergeada sí
    lo es, y lo sigue siendo.
    """
    try:
        resultado = subprocess.run(
            ["git", "merge-base", "--is-ancestor", "HEAD", "dev"],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):  # pragma: no cover - no hay git en el PATH
        return False
    return resultado.returncode == 0


def _fuera_de_la_rama_de_la_feature() -> bool:
    """`True` cuando no estamos en la rama de F-033."""
    rama = _rama_actual()
    return rama is not None and rama != RAMA_DE_LA_FEATURE


def _diff_de_la_rama_o_saltar() -> list[str]:
    """Los ficheros que tocó la rama, normalizados; o se salta el control.

    Es el guardián que evita el defecto de F-030: los controles del diff viven
    **en la rama de la feature mientras no esté mergeada**. Fuera de ahí no hay
    nada que mirar, y un control sin nada que mirar no puede ponerse rojo. Lo
    que no depende de `git` está en el test hermano de cada uno.
    """
    cambiados = _ficheros_cambiados_en_la_rama()
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
    return [ruta.replace("\\", "/") for ruta in cambiados]


def test_f033_el_control_del_diff_no_esta_mirando_una_lista_vacia():
    """El control de los controles: si el diff viniera vacío, mentirían todos.

    Los de abajo afirman que **algo no aparece** en el diff. Un `git diff` que
    no devolviera nada —rama equivocada, `dev` que ya lo contiene todo— los
    pondría verdes sin haber comprobado nada. Aquí se exige que la rama haya
    cambiado algo, y que entre lo cambiado esté el paso del que va la feature.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    assert cambiados, "el diff de la rama no puede estar vacío"
    assert any(
        ruta.endswith("application/pipelines/paso_archivo.py") for ruta in cambiados
    ), "la rama tiene que haber tocado el paso de archivo: es de lo que va la feature"


# --------------------------------------------------------------------------
# Sin DDL: ni un fichero nuevo ni una línea cambiada en `sql/`
# --------------------------------------------------------------------------

#: La carpeta del DDL, tal y como la escribe `git`.
CARPETA_DDL = "services/postventa-api/infrastructure/persistencia/sql/"

#: Los ficheros de DDL que hay, escritos a mano y **no leídos del disco**: una
#: lista recalculada del propio árbol daría verde ante cualquier fichero nuevo,
#: que es justo lo que viene a cazar. Son los once de F-028.
DDL_DE_F028 = (
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
)


def test_f033_la_rama_no_toca_el_ddl():
    """Regla dura 1 · ni un fichero de `sql/` en el diff de la rama entera.

    F-033 sí toca la persistencia —`sentencias.py`, `mapeo.py`,
    `repositorio_pg.py`—, pero sin cambiar el esquema: el tercer `LEFT JOIN`
    lee columnas que ya existían y el `WHERE` de `upsert_archivo` no necesita
    ninguna nueva. Una línea en `sql/` significaría una migración contra el
    PostgreSQL compartido, y eso no está en el alcance.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    culpables = [ruta for ruta in cambiados if ruta.startswith(CARPETA_DDL)]

    assert culpables == [], f"F-033 no lleva DDL. Sobran: {culpables}"


def test_f033_no_hay_ni_un_fichero_de_ddl_nuevo():
    """Regla dura 1 · la mitad que no depende de `git`, y no se puede saltar.

    Los ficheros de DDL son los once de F-028 y ninguno más. No vigila que su
    contenido no cambie —eso lo dice el diff—, sino que no aparezca un
    `12_*.sql` que ninguna rama debería haber necesitado para L1.
    """
    carpeta = RAIZ / CARPETA_DDL
    nombres = tuple(sorted(ruta.name for ruta in carpeta.glob("*.sql")))

    assert nombres == DDL_DE_F028


# --------------------------------------------------------------------------
# R23 · el front no se toca: el contrato de `/api/archivar` es el mismo
# --------------------------------------------------------------------------

CARPETA_DEL_FRONT = "services/postventa-front/"

#: Lo que el front manda en el cuerpo de `/api/archivar`, escrito a mano y en
#: su orden. Las seis claves de **salida** ya las fija
#: `test_f033_archivar_http.py` (R12, R23), con corte y sin él.
CAMPOS_OBLIGATORIOS_DEL_CUERPO = (
    "hash",
    "codigo_obra",
    "numero_incidencia",
    "veredicto",
    "destino",
)


def test_f033_r23_la_rama_no_toca_ni_un_fichero_del_front():
    """R23 · el front no se toca, comprobado en el diff de la rama entera.

    Lo nuevo que ve el front son dos textos posibles dentro de `avisos`, que ya
    pinta como lista. Si hiciera falta una línea de front, sería que el contrato
    ha cambiado, y R23 dice que no.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    culpables = [ruta for ruta in cambiados if ruta.startswith(CARPETA_DEL_FRONT)]

    assert culpables == [], f"F-033 no toca el front. Sobran: {culpables}"


def test_f033_r23_el_cuerpo_de_archivar_pide_lo_mismo_de_siempre():
    """R23 · la mitad que no depende de `git`: la entrada no gana ni pierde nada.

    En particular, **no gana un campo `forzar`** ni nada parecido (R21, D-4): el
    re-archivo del mismo parte no existe desde el circuito. Un campo más aquí
    sería también un cambio que el front tendría que conocer.
    """
    from interface_adapters.api.archivar import CAMPOS_OBLIGATORIOS

    assert CAMPOS_OBLIGATORIOS == CAMPOS_OBLIGATORIOS_DEL_CUERPO


# --------------------------------------------------------------------------
# D-6 y F-031 · los cuatro ficheros del ERP y el nombrado, fuera
# --------------------------------------------------------------------------

#: Los cuatro de D-6 (la precondición «consta archivado» de gráfico y cierre)
#: y el nombrado de F-031, con su ruta tal y como la escribe `git`.
FICHEROS_DE_OTRAS_FICHAS = (
    "services/postventa-api/application/pipelines/paso_grafico.py",
    "services/postventa-api/application/pipelines/paso_cierre.py",
    "services/postventa-api/interface_adapters/api/adjuntar.py",
    "services/postventa-api/interface_adapters/api/cerrar.py",
    "services/postventa-api/domain/models/nombrado.py",
)

#: Los nombres que F-033 introduce en el código de producción y **dónde** se
#: pueden usar, escrito a mano. L1 vive en el paso de archivo y el endpoint
#: solo le pasa la biblioteca vigente; ni el gráfico, ni el cierre, ni el
#: nombrado tienen por qué saber nada de ellos.
NOMBRES_NUEVOS_Y_DONDE_VIVEN = {
    "drive_id_vigente": {
        "application/pipelines/paso_archivo.py",
        "interface_adapters/api/archivar.py",
    },
    "_en_otro_destino": {"application/pipelines/paso_archivo.py"},
    "AVISO_ARCHIVADO_EN_OTRO_DESTINO": {"application/pipelines/paso_archivo.py"},
    "AVISO_INTENTO_ANTERIOR_EN_OTRA_RUTA": {"application/pipelines/paso_archivo.py"},
}

#: Las carpetas del servicio que **no** son código de producción.
CARPETAS_QUE_NO_SON_PRODUCCION = {
    "tests",
    "tests_bbdd",
    ".venv",
    ".python_packages",
    "__pycache__",
}


def _ficheros_de_produccion() -> list[Path]:
    """Los `.py` de producción del servicio, sin tests ni dependencias."""
    return [
        ruta
        for ruta in RAIZ_DEL_SERVICIO.rglob("*.py")
        if not CARPETAS_QUE_NO_SON_PRODUCCION.intersection(
            ruta.relative_to(RAIZ_DEL_SERVICIO).parts
        )
    ]


def _nombres_de_codigo(ruta: Path) -> set[str]:
    """Los identificadores de un fichero, sin su prosa.

    Se leen con `tokenize`, que separa nombres de cadenas y comentarios: este
    proyecto **explica** el código, y una docstring que cite
    `drive_id_vigente` —la de `archivar.py` lo hace en prosa— no es usarlo.
    """
    fuente = ruta.read_text(encoding="utf-8")
    return {
        token.string
        for token in tokenize.generate_tokens(io.StringIO(fuente).readline)
        if token.type == tokenize.NAME
    }


def test_f033_la_rama_no_toca_d6_ni_el_nombrado():
    """D-6, F-031 · ni una línea en los cinco ficheros de otras fichas.

    La tentación está a la vista: `adjuntar` y `cerrar` deciden «consta
    archivado» con lo que dice el cuerpo, y F-033 acaba de dejar la traza en la
    situación que ya leen. Arreglarlo aquí cambiaría las puertas de las dos
    escrituras en el ERP de producción dentro de una ficha que no las revisó.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    culpables = [ruta for ruta in cambiados if ruta in FICHEROS_DE_OTRAS_FICHAS]

    assert culpables == [], (
        f"F-033 no toca D-6 (F-034) ni el nombrado (F-031). Sobran: {culpables}"
    )


def test_f033_lo_nuevo_de_l1_solo_vive_en_el_paso_y_su_endpoint():
    """D-6, F-031 · la mitad que no depende de `git`: L1 está en un solo sitio.

    Recorre todo el código de producción y exige que los nombres que F-033
    introduce aparezcan **exactamente** donde tienen que aparecer: ni en el
    gráfico, ni en el cierre, ni en el nombrado, ni en ningún otro sitio. Y al
    revés también: si el endpoint dejara de pasar la biblioteca vigente, el
    aviso de otro destino de R14 dejaría de poder salir por la biblioteca, y
    este control se pone rojo.
    """
    encontrados: dict[str, set[str]] = {
        nombre: set() for nombre in NOMBRES_NUEVOS_Y_DONDE_VIVEN
    }
    for ruta in _ficheros_de_produccion():
        nombres = _nombres_de_codigo(ruta)
        relativa = ruta.relative_to(RAIZ_DEL_SERVICIO).as_posix()
        for nombre in NOMBRES_NUEVOS_Y_DONDE_VIVEN:
            if nombre in nombres:
                encontrados[nombre].add(relativa)

    assert encontrados == NOMBRES_NUEVOS_Y_DONDE_VIVEN


def test_f033_el_recorrido_de_produccion_ve_los_cinco_ficheros_vigilados():
    """El control del control de arriba: que el recorrido mire donde debe.

    Si la lista de producción saliera vacía o se dejara fuera una carpeta, el
    test de arriba no vería nada en los ficheros de D-6 y del nombrado y daría
    verde sin haberlos leído.
    """
    vistos = {
        f"services/postventa-api/{ruta.relative_to(RAIZ_DEL_SERVICIO).as_posix()}"
        for ruta in _ficheros_de_produccion()
    }

    assert set(FICHEROS_DE_OTRAS_FICHAS) <= vistos
    assert not any("/tests/" in ruta for ruta in vistos)
