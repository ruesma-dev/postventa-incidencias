# services/postventa-api/tests/test_f034_alcance_cerrado.py
"""Lo que F-034 promete **no** tocar, comprobado (T13; R23, R26, R39).

F-034 cambia de dónde salen tres datos con los que `POST /api/adjuntar` y
`POST /api/cerrar` escriben en el ERP de producción —el estado del archivo y
los dos códigos— y los toma de la situación que la puerta de aptitud ya leía.
Eso vive en diez ficheros del backend y uno del front, y **nada más**. Cada
frontera que tienta tiene aquí su control:

| Frontera | Por qué no se toca |
|---|---|
| `infrastructure/persistencia/` (`sentencias.py`, `mapeo.py`, `repositorio_pg.py`) y `sql/` | **R23**: el dato ya viaja en la consulta de situación (F-030 los códigos, F-033 la traza). Ni una columna, ni una sentencia, ni DDL |
| `domain/ports/persistencia.py`, `domain/models/estado.py` | **R23**: ni un método del puerto, ni un campo de `SituacionParte` |
| `domain/models/nombrado.py`, `grafico.py`, `cierre.py` | **R24** y `design.md` §2.3: dominio puro; `componer_peticion` sigue recibiendo dos cadenas, lo que cambia es **quién** se las da |
| `paso_archivo.py`, `archivar.py` | **R26**: solo el `import` de las piezas que se mudan a `codigos_del_parte.py`. Ni una regla de `/api/archivar` cambia |
| `js/pipeline.js`, `js/autoguardado.js` | **R31**: el cuerpo de las dos peticiones no cambia; `vaciarPendientes()` es de F-031 y aquí solo se llama |

Y hereda, ampliado, el control «dónde vive lo nuevo» de F-031
(`test_f031_alcance_cerrado.py`, tabla `NOMBRES_NUEVOS_Y_DONDE_VIVEN`), por la
decisión del humano del 2026-09-23 («si» a `progress/impl_F-034.md` §2.4 (a)):
`codigos_del_parte.py` es **la única definición** de `CodigosDelParte`,
`codigos_guardados`, `exigir_codigos_declarados` y `exigir_codigos_completos`,
y solo los usan los ficheros previstos.

**Sin red, sin base de datos, sin IA y sin reloj.** Los controles del diff
llaman a `git`, que es un proceso local de solo lectura.

## Las dos mitades, y las tres guardas del diff

Con el patrón de `test_f033_alcance_cerrado.py` y `test_f031_alcance_cerrado.py`:

1. **el del diff** (`git diff --name-only dev...HEAD`, y `git show` de la base
   de la rama para comparar dos ficheros): «esta rama no lo tocó». Deja de
   tener algo que mirar en cuanto la rama se mergea, así que lleva las tres
   guardas que F-030 tuvo que inventar el 2026-09-17 para no dejar `dev` en
   rojo —`RAMA_DE_LA_FEATURE`, `_fuera_de_la_rama_de_la_feature` y
   `_la_rama_ya_esta_en_dev`—. Dentro de la rama se ejecutan enteros;
2. **el que no depende de `git`**, que se comprueba siempre, en cualquier rama
   y para siempre: «y hoy sigue siendo lo que tiene que ser».
"""

from __future__ import annotations

import ast
import io
import subprocess
import tokenize
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]

#: La raíz del servicio, de donde cuelga el código de producción.
RAIZ_DEL_SERVICIO = RAIZ / "services" / "postventa-api"

#: La rama en la que los controles del diff tienen algo que mirar. Sale de la
#: ficha de F-034 en `harness/features.json`, campo `branch`.
RAMA_DE_LA_FEATURE = "feature/F-034-archivo-persistido-en-erp"

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


def _ficheros_cambiados_en_la_rama() -> list[str] | None:
    """`git diff --name-only dev...HEAD`, o `None` si no se puede preguntar.

    `None` cuando no hay `git` o `dev` no está en este clon (un `checkout`
    superficial): eso no es un fallo de la feature.

    `dev...HEAD` (tres puntos) y no `dev..HEAD`: interesa lo que ha cambiado
    **esta rama** desde que se separó, no lo que haya entrado en `dev` después.
    """
    dev = _git("rev-parse", "--verify", "--quiet", "dev")
    if dev is None or dev.returncode != 0:
        return None
    diff = _git("diff", "--name-only", "dev...HEAD")
    if diff is None or diff.returncode != 0:  # pragma: no cover - repo no sano
        return None
    return [linea.strip() for linea in diff.stdout.splitlines() if linea.strip()]


def _rama_actual() -> str | None:
    """El nombre de la rama de trabajo, o `None` si no se puede saber."""
    resultado = _git("rev-parse", "--abbrev-ref", "HEAD")
    if resultado is None or resultado.returncode != 0:  # pragma: no cover
        return None
    return resultado.stdout.strip() or None


def _la_rama_ya_esta_en_dev() -> bool:
    """`True` cuando `HEAD` ya forma parte de `dev`: la rama cumplió su ciclo.

    Cubre el `checkout` de la rama **después** de mergearla, cuando el diff
    viene vacío sin que sea un fallo. Un diff vacío **sin** estar mergeada sí
    lo es, y lo sigue siendo.
    """
    resultado = _git("merge-base", "--is-ancestor", "HEAD", "dev")
    return resultado is not None and resultado.returncode == 0


def _fuera_de_la_rama_de_la_feature() -> bool:
    """`True` cuando no estamos en la rama de F-034."""
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


def _fuente_en_la_base_de_la_rama(ruta: str) -> str:
    """El fichero tal y como estaba cuando la rama se separó de `dev`.

    La **base** (`git merge-base dev HEAD`) y no `dev` a secas: si `dev`
    avanzara con otra feature que tocara el mismo fichero, la comparación
    estaría midiendo el trabajo de otra rama.
    """
    base = _git("merge-base", "dev", "HEAD")
    assert base is not None and base.returncode == 0, "sin base de la rama"
    fuente = _git("show", f"{base.stdout.strip()}:{ruta}")
    assert fuente is not None and fuente.returncode == 0, f"sin {ruta} en la base"
    return fuente.stdout


def test_f034_el_control_del_diff_no_esta_mirando_una_lista_vacia():
    """El control de los controles: si el diff viniera vacío, mentirían todos.

    Los de abajo afirman que **algo no aparece** en el diff. Un `git diff` que
    no devolviera nada los pondría verdes sin haber comprobado nada. Aquí se
    exige que la rama haya tocado los dos pasos de los que va la feature y el
    punto del front.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    assert cambiados, "el diff de la rama no puede estar vacío"
    for imprescindible in (
        f"{SERVICIO}application/pipelines/paso_grafico.py",
        f"{SERVICIO}application/pipelines/paso_cierre.py",
        "services/postventa-front/js/app.js",
    ):
        assert imprescindible in cambiados, (
            f"la rama tiene que haber tocado {imprescindible}: es de lo que va "
            "la feature"
        )


# --------------------------------------------------------------------------
# El código de producción que toca la rama: el de `design.md` §2, y ninguno más
# --------------------------------------------------------------------------

#: Los once ficheros de producción de `design.md` §2.1 y §2.2, escritos a mano.
#: Los tests, las specs, `progress/` y la documentación no cuentan aquí: la
#: frontera que importa es qué código se ejecuta distinto.
PRODUCCION_QUE_TOCA_F034 = {
    f"{SERVICIO}application/pipelines/codigos_del_parte.py",
    f"{SERVICIO}application/pipelines/puerta_de_estado.py",
    f"{SERVICIO}application/pipelines/paso_grafico.py",
    f"{SERVICIO}application/pipelines/paso_cierre.py",
    f"{SERVICIO}application/pipelines/paso_archivo.py",
    f"{SERVICIO}domain/models/errores.py",
    f"{SERVICIO}interface_adapters/api/adjuntar.py",
    f"{SERVICIO}interface_adapters/api/cerrar.py",
    f"{SERVICIO}interface_adapters/api/archivar.py",
    f"{SERVICIO}function_app.py",
    "services/postventa-front/js/app.js",
}

#: Las carpetas de un servicio que **no** son código de producción.
CARPETAS_QUE_NO_SON_PRODUCCION = {
    "tests",
    "tests_js",
    "tests_bbdd",
    ".venv",
    ".python_packages",
    "__pycache__",
}


def _es_produccion(ruta: str) -> bool:
    """¿Es un fichero de código de producción de algún servicio?"""
    if not ruta.startswith("services/"):
        return False
    return not CARPETAS_QUE_NO_SON_PRODUCCION.intersection(ruta.split("/"))


def test_f034_r39_la_rama_solo_toca_el_codigo_de_produccion_del_diseno():
    """R39 · lo que se ejecuta distinto es exactamente la lista de `design.md` §2.

    Ni uno más —un fichero de persistencia, del dominio o del front que no
    estaba en el diseño es alcance que nadie revisó— y ni uno menos: si uno de
    los once no apareciera, la feature estaría a medias o se habría hecho por
    otro sitio.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    produccion = {ruta for ruta in cambiados if _es_produccion(ruta)}

    assert produccion == PRODUCCION_QUE_TOCA_F034


# --------------------------------------------------------------------------
# R23, R39 · la persistencia, el puerto, `estado.py` y el dominio, intactos
# --------------------------------------------------------------------------

#: Los ocho ficheros que R39 y `tasks.md` T13 enumeran, con su ruta de `git`.
FICHEROS_INTOCABLES = (
    f"{SERVICIO}infrastructure/persistencia/sentencias.py",
    f"{SERVICIO}infrastructure/persistencia/mapeo.py",
    f"{SERVICIO}infrastructure/persistencia/repositorio_pg.py",
    f"{SERVICIO}domain/ports/persistencia.py",
    f"{SERVICIO}domain/models/estado.py",
    f"{SERVICIO}domain/models/nombrado.py",
    f"{SERVICIO}domain/models/grafico.py",
    f"{SERVICIO}domain/models/cierre.py",
)

#: La carpeta del DDL, tal y como la escribe `git`.
CARPETA_DDL = f"{SERVICIO}infrastructure/persistencia/sql/"


def test_f034_r39_la_rama_no_toca_la_persistencia_ni_el_dominio():
    """R23, R39 · ni una línea en los ocho ficheros de T13.

    Es lo que abarata la feature (`design.md` §1.1): el dato correcto **ya
    estaba en la situación**. Una línea aquí significaría que alguien decidió
    traerlo por un segundo camino o cambiar lo que se hace con él.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    culpables = [ruta for ruta in cambiados if ruta in FICHEROS_INTOCABLES]

    assert culpables == [], f"F-034 no toca esto (R23, R39). Sobran: {culpables}"


def test_f034_r23_la_rama_no_toca_el_ddl():
    """R23 · ni un fichero de `sql/` en el diff de la rama entera.

    Una línea en `sql/` sería una migración contra el PostgreSQL **compartido
    con albaranes**, y eso no está en el alcance ni se hace desde local.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    culpables = [ruta for ruta in cambiados if ruta.startswith(CARPETA_DDL)]

    assert culpables == [], f"F-034 no lleva DDL (R23). Sobran: {culpables}"


#: Los ficheros de DDL que hay, escritos a mano y **no leídos del disco**: una
#: lista recalculada del propio árbol daría verde ante cualquier fichero nuevo.
#: Son los once de F-028, los mismos que vigilan F-031 y F-033.
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

#: Los once métodos de `RepositorioPartesPort`, escritos a mano y en su orden.
METODOS_DEL_PUERTO_DE_PARTES = (
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
)

#: Los cinco campos de `SituacionParte`, escritos a mano. `archivo` (F-033) y
#: `validacion` (F-030) son justo los dos de los que F-034 lee; no hace falta
#: un sexto.
CAMPOS_DE_SITUACION_PARTE = (
    "decision_humana",
    "ultimo_estado_registrado",
    "estado_cierre",
    "validacion",
    "archivo",
)

#: Lo que exporta `sentencias.py`, escrito a mano: una sentencia nueva
#: aparecería aquí antes que en ningún otro sitio (R23).
SENTENCIAS_PUBLICAS = (
    "LIMITE_MAXIMO_COLA",
    "ORIGEN_DECISION_HUMANA",
    "ORIGEN_ULTIMO_CAMBIO",
    "insert_decision_estado",
    "select_cola",
    "select_estado_cierre",
    "select_grafico",
    "select_login_sigrid",
    "select_preferencias",
    "select_situacion_estado",
    "select_veredicto_y_cierre",
    "upsert_archivo",
    "upsert_cierre",
    "upsert_grafico",
    "upsert_login_sigrid",
    "upsert_parte",
    "upsert_preferencias",
    "upsert_remesa",
    "upsert_validacion",
)

#: Lo que exporta `nombrado.py`, escrito a mano (R24: las cuatro reglas y
#: `nombre_admisible`, letra por letra; `es_el_mismo_codigo` la trajo F-031).
NOMBRADO_PUBLICO = (
    "CARACTERES_PROHIBIDOS",
    "EXTENSION",
    "GUIONES_EQUIVALENTES",
    "SEPARADOR",
    "SEPARADORES_DE_CODIGO",
    "SUFIJO",
    "DestinoArchivo",
    "carpeta_de_archivo",
    "componer_destino",
    "es_el_mismo_codigo",
    "nombre_admisible",
    "nombre_de_archivo",
    "normalizar_codigo",
    "tramos_de_codigo",
)

#: Los parámetros de `componer_peticion`, en su orden. Sigue recibiendo **dos
#: cadenas** (`design.md` §2.3): F-034 cambia quién se las da, no qué recibe.
PARAMETROS_DE_COMPONER_PETICION = (
    "reclamacion",
    "login",
    "codigo_obra",
    "numero_incidencia",
    "gratipide",
    "contenido",
    "bytes",
    "sha256",
)


def _arbol(relativa: str) -> ast.Module:
    """El árbol sintáctico de un fichero del servicio, leído del disco."""
    return ast.parse((RAIZ_DEL_SERVICIO / relativa).read_text(encoding="utf-8"))


def _clase(arbol: ast.Module, nombre: str) -> ast.ClassDef:
    for nodo in arbol.body:
        if isinstance(nodo, ast.ClassDef) and nodo.name == nombre:
            return nodo
    raise AssertionError(f"no se encuentra la clase {nombre}")


def _funcion(arbol: ast.Module, nombre: str) -> ast.FunctionDef:
    for nodo in arbol.body:
        if isinstance(nodo, ast.FunctionDef) and nodo.name == nombre:
            return nodo
    raise AssertionError(f"no se encuentra la función {nombre}")


def _all_de(arbol: ast.Module) -> tuple[str, ...]:
    """El `__all__` de un módulo, leído sin importarlo."""
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and any(
            isinstance(destino, ast.Name) and destino.id == "__all__"
            for destino in nodo.targets
        ):
            return tuple(ast.literal_eval(nodo.value))
    raise AssertionError("el módulo no tiene __all__")


def _metodos(clase: ast.ClassDef) -> tuple[str, ...]:
    return tuple(
        miembro.name
        for miembro in clase.body
        if isinstance(miembro, ast.FunctionDef | ast.AsyncFunctionDef)
    )


def test_f034_r23_no_hay_ni_un_fichero_de_ddl_nuevo():
    """R23 · la mitad que no depende de `git`: los once de F-028 y ninguno más."""
    carpeta = RAIZ / CARPETA_DDL
    nombres = tuple(sorted(ruta.name for ruta in carpeta.glob("*.sql")))

    assert nombres == DDL_DE_F028


def test_f034_r23_el_puerto_no_gana_ni_un_metodo_y_el_adaptador_tampoco():
    """R23 · ni un método en el puerto, ni uno público de más en el adaptador.

    El adaptador de PostgreSQL implementa tres puertos (partes, preferencias y
    usuarios del ERP): sus métodos públicos son los once de partes y los
    cuatro de los otros dos. Un `consultar_codigos(hash)` o un
    `consultar_archivo(hash)` sería la señal de que alguien volvió a abrir un
    segundo camino hacia lo que la situación ya trae.
    """
    puerto = _metodos(
        _clase(_arbol("domain/ports/persistencia.py"), "RepositorioPartesPort")
    )
    adaptador = _metodos(
        _clase(
            _arbol("infrastructure/persistencia/repositorio_pg.py"),
            "RepositorioPostgres",
        )
    )
    publicos_del_adaptador = tuple(
        nombre for nombre in adaptador if not nombre.startswith("_")
    )

    assert puerto == METODOS_DEL_PUERTO_DE_PARTES
    assert publicos_del_adaptador == (
        *METODOS_DEL_PUERTO_DE_PARTES,
        "obtener_preferencias",
        "guardar_preferencias",
        "resolver_login",
        "guardar_login",
    )


def test_f034_r23_situacion_parte_no_gana_campos():
    """R23 · `SituacionParte` trae ya las cinco cosas; no gana una sexta."""
    clase = _clase(_arbol("domain/models/estado.py"), "SituacionParte")
    campos = tuple(
        miembro.target.id
        for miembro in clase.body
        if isinstance(miembro, ast.AnnAssign) and isinstance(miembro.target, ast.Name)
    )

    assert campos == CAMPOS_DE_SITUACION_PARTE


def test_f034_r23_sentencias_no_gana_ninguna_sentencia():
    """R23 · lo que exporta `sentencias.py` es lo de antes de la feature."""
    assert _all_de(_arbol("infrastructure/persistencia/sentencias.py")) == (
        SENTENCIAS_PUBLICAS
    )


def test_f034_r24_el_dominio_del_nombrado_y_del_grafico_no_cambia_de_forma():
    """R24, `design.md` §2.3 · el nombrado exporta lo mismo y la petición recibe
    las mismas dos cadenas.

    Si `componer_peticion` empezara a recibir la situación o el contexto, el
    dominio puro sabría de dónde salen los códigos, que es exactamente lo que
    la aplicación decide y el dominio no.
    """
    componer = _funcion(_arbol("domain/models/grafico.py"), "componer_peticion")
    parametros = tuple(
        argumento.arg for argumento in componer.args.args + componer.args.kwonlyargs
    )

    assert _all_de(_arbol("domain/models/nombrado.py")) == NOMBRADO_PUBLICO
    assert parametros == PARAMETROS_DE_COMPONER_PETICION


# --------------------------------------------------------------------------
# R26 · de `paso_archivo.py` y `archivar.py`, solo el `import`
# --------------------------------------------------------------------------

#: Lo que se mudó de `paso_archivo.py` a `codigos_del_parte.py` en T3, con el
#: nombre que tenía allí y el que tiene ahora.
MUDADOS_DE_PASO_ARCHIVO = {
    "_codigos_guardados": "codigos_guardados",
    "_exigir_codigos_declarados": "exigir_codigos_declarados",
}

#: La única línea nueva de código de `paso_archivo.py`: la cola del mensaje,
#: que antes vivía dentro del `raise` de la copia privada.
CONSTANTE_NUEVA_DE_PASO_ARCHIVO = "_Y_POR_ESO_NO_SE_ARCHIVA"


class _SinProsaNiImports(ast.NodeTransformer):
    """Quita docstrings e `import` de un árbol: lo que queda es el código.

    Las enmiendas fechadas de F-034 van en la prosa y los `import` cambian por
    definición; ninguna de las dos cosas es una regla.
    """

    def _sin_docstring(self, cuerpo: list[ast.stmt]) -> list[ast.stmt]:
        if (
            cuerpo
            and isinstance(cuerpo[0], ast.Expr)
            and isinstance(cuerpo[0].value, ast.Constant)
            and isinstance(cuerpo[0].value.value, str)
        ):
            return cuerpo[1:]
        return cuerpo

    def visit_Module(self, nodo: ast.Module) -> ast.Module:
        nodo.body = [
            sentencia
            for sentencia in self._sin_docstring(nodo.body)
            if not isinstance(sentencia, ast.Import | ast.ImportFrom)
        ]
        self.generic_visit(nodo)
        return nodo

    def visit_FunctionDef(self, nodo: ast.FunctionDef) -> ast.FunctionDef:
        nodo.body = self._sin_docstring(nodo.body) or [ast.Pass()]
        self.generic_visit(nodo)
        return nodo

    def visit_ClassDef(self, nodo: ast.ClassDef) -> ast.ClassDef:
        nodo.body = self._sin_docstring(nodo.body) or [ast.Pass()]
        self.generic_visit(nodo)
        return nodo


class _ComoAntesDeLaMudanza(ast.NodeTransformer):
    """Deshace, en el árbol de hoy, lo único que T3 cambió en `paso_archivo`.

    Vuelve a llamar a las piezas por su nombre privado de antes y retira el
    `y_por_eso=` de la llamada al cotejo. Si después de eso el árbol no es
    **idéntico** al de la base de la rama, algo más que el `import` cambió.
    """

    def visit_Name(self, nodo: ast.Name) -> ast.Name:
        antes = {nuevo: viejo for viejo, nuevo in MUDADOS_DE_PASO_ARCHIVO.items()}
        if nodo.id in antes:
            nodo.id = antes[nodo.id]
        return nodo

    def visit_Call(self, nodo: ast.Call) -> ast.Call:
        self.generic_visit(nodo)
        if (
            isinstance(nodo.func, ast.Name)
            and nodo.func.id == "_exigir_codigos_declarados"
        ):
            nodo.keywords = [
                palabra for palabra in nodo.keywords if palabra.arg != "y_por_eso"
            ]
        return nodo


def _sin_definiciones(arbol: ast.Module, nombres: set[str]) -> ast.Module:
    """Quita del nivel de módulo las clases, funciones y constantes nombradas."""

    def se_queda(sentencia: ast.stmt) -> bool:
        if isinstance(sentencia, ast.ClassDef | ast.FunctionDef):
            return sentencia.name not in nombres
        if isinstance(sentencia, ast.Assign):
            return not any(
                isinstance(destino, ast.Name) and destino.id in nombres
                for destino in sentencia.targets
            )
        return True

    arbol.body = [sentencia for sentencia in arbol.body if se_queda(sentencia)]
    return arbol


def _codigo(fuente: str) -> ast.Module:
    return _SinProsaNiImports().visit(ast.parse(fuente))


def _paso_archivo_de_antes_sin_lo_mudado(fuente: str) -> str:
    arbol = _sin_definiciones(
        _codigo(fuente), {"CodigosDelParte", *MUDADOS_DE_PASO_ARCHIVO}
    )
    return ast.dump(arbol)


def _paso_archivo_de_hoy_como_antes(fuente: str) -> str:
    arbol = _sin_definiciones(_codigo(fuente), {CONSTANTE_NUEVA_DE_PASO_ARCHIVO})
    return ast.dump(_ComoAntesDeLaMudanza().visit(arbol))


def test_f034_r26_el_comparador_no_es_ciego():
    """El control del control de abajo: un cambio de regla **sí** se ve.

    Con dos fuentes sintéticas que solo difieren en el orden de dos
    comprobaciones —el tipo de cambio que R26 prohíbe—, el comparador tiene que
    decir que no son iguales. Y con dos que solo difieren en la prosa y en los
    `import`, que sí.
    """
    antes = (
        '"""Cabecera."""\nimport os\n\n'
        "def paso(ctx):\n    '''Doc.'''\n    primero(ctx)\n    segundo(ctx)\n"
    )
    solo_prosa = (
        '"""Cabecera enmendada."""\nimport sys\n\n'
        "def paso(ctx):\n    '''Otra doc.'''\n    primero(ctx)\n    segundo(ctx)\n"
    )
    otra_regla = (
        '"""Cabecera."""\nimport os\n\n'
        "def paso(ctx):\n    '''Doc.'''\n    segundo(ctx)\n    primero(ctx)\n"
    )

    assert ast.dump(_codigo(antes)) == ast.dump(_codigo(solo_prosa))
    assert ast.dump(_codigo(antes)) != ast.dump(_codigo(otra_regla))


def test_f034_r26_de_paso_archivo_solo_cambia_la_mudanza():
    """R26 · `paso_archivo.py`, comparado con la base de la rama, no cambia de regla.

    Sin prosa ni `import`, sin lo que se mudó (`CodigosDelParte` y los dos
    privados de F-031) y sin la constante con la cola del mensaje, el árbol de
    hoy —con las piezas llamadas por su nombre de antes y sin el `y_por_eso=`—
    es **idéntico** al de la base. Mismo orden, mismas llamadas, mismos
    argumentos: el mensaje byte a byte lo vigila aparte
    `test_f034_r26_codigos_el_mensaje_de_archivar_es_byte_a_byte_el_de_f031`.
    """
    _diff_de_la_rama_o_saltar()
    ruta = f"{SERVICIO}application/pipelines/paso_archivo.py"

    antes = _paso_archivo_de_antes_sin_lo_mudado(_fuente_en_la_base_de_la_rama(ruta))
    hoy = _paso_archivo_de_hoy_como_antes((RAIZ / ruta).read_text(encoding="utf-8"))

    assert hoy == antes, "paso_archivo.py cambió algo más que la mudanza (R26)"


def test_f034_r26_de_archivar_solo_cambia_el_import():
    """R26 · `archivar.py` sin prosa ni `import` es idéntico al de la base."""
    _diff_de_la_rama_o_saltar()
    ruta = f"{SERVICIO}interface_adapters/api/archivar.py"

    antes = ast.dump(_codigo(_fuente_en_la_base_de_la_rama(ruta)))
    hoy = ast.dump(_codigo((RAIZ / ruta).read_text(encoding="utf-8")))

    assert hoy == antes, "archivar.py cambió algo más que el import (R26)"


def _importa_de(arbol: ast.Module, modulo: str) -> set[str]:
    """Los nombres que un módulo importa de otro, con `from … import …`."""
    return {
        alias.name
        for nodo in arbol.body
        if isinstance(nodo, ast.ImportFrom) and nodo.module == modulo
        for alias in nodo.names
    }


def test_f034_r26_archivo_y_su_endpoint_importan_la_pieza_compartida():
    """R26 · la mitad que no depende de `git`: las piezas llegan por `import`.

    `paso_archivo.py` importa las tres que usa y `archivar.py` la clase, del
    módulo compartido; y ninguno de los dos vuelve a importar la clase del
    otro sitio (`archivar.py` la tomaba de `paso_archivo` hasta F-034).
    """
    compartido = "application.pipelines.codigos_del_parte"
    paso = _arbol("application/pipelines/paso_archivo.py")
    endpoint = _arbol("interface_adapters/api/archivar.py")

    assert _importa_de(paso, compartido) == {
        "CodigosDelParte",
        "codigos_guardados",
        "exigir_codigos_declarados",
    }
    assert _importa_de(endpoint, compartido) == {"CodigosDelParte"}
    assert "CodigosDelParte" not in _importa_de(
        endpoint, "application.pipelines.paso_archivo"
    )


# --------------------------------------------------------------------------
# R31 · el front: solo `reintentarCierre` y su test
# --------------------------------------------------------------------------

CARPETA_DEL_FRONT = "services/postventa-front/"

#: Lo único que F-034 toca del front (`design.md` §2.1, §2.2 y §7).
FRONT_QUE_TOCA_F034 = {
    "services/postventa-front/js/app.js",
    "services/postventa-front/tests_js/reintento_vaciado.test.js",
}


def test_f034_r31_la_rama_solo_toca_app_js_y_su_test_en_el_front():
    """R31, `design.md` §2.3 · ni `pipeline.js` ni `autoguardado.js`.

    El cuerpo de `/api/adjuntar` y `/api/cerrar` lo componen `cuerpoDeGrafico`
    y `cuerpoDeCierre` en `js/pipeline.js`; si ese fichero apareciera aquí, el
    contrato habría cambiado y R18 dice que no. `vaciarPendientes()` es de
    F-031 y aquí solo se llama.
    """
    cambiados = _diff_de_la_rama_o_saltar()

    del_front = {ruta for ruta in cambiados if ruta.startswith(CARPETA_DEL_FRONT)}

    assert del_front == FRONT_QUE_TOCA_F034


#: Los campos obligatorios de los dos cuerpos, escritos a mano y en su orden,
#: copiados de la base de la rama (`e2e5d7a`): R18, el contrato HTTP no
#: cambia; D-3, `estado_archivo` sigue obligatorio y validado, aunque ya no
#: decida nada. `correo` no es obligatorio en ninguno de los dos (F-009).
CAMPOS_OBLIGATORIOS_DE_ADJUNTAR = (
    "hash",
    "codigo_obra",
    "numero_incidencia",
    "veredicto",
    "destino",
    "estado_archivo",
    "usuario_oid",
)
CAMPOS_OBLIGATORIOS_DE_CERRAR = (
    "hash",
    "numero_incidencia",
    "veredicto",
    "destino",
    "estado_archivo",
    "usuario_oid",
)


def test_f034_r18_los_dos_cuerpos_piden_lo_mismo_de_siempre():
    """R18, D-3 · la mitad que no depende de `git`: la entrada no gana ni pierde.

    Lo que el front manda no cambia (R31) porque lo que el backend pide no
    cambia. Si alguien retirara `estado_archivo` del contrato —la opción (c) de
    D-3, descartada—, el front de producción empezaría a recibir 400.
    """
    from interface_adapters.api import adjuntar, cerrar

    assert adjuntar.CAMPOS_OBLIGATORIOS == CAMPOS_OBLIGATORIOS_DE_ADJUNTAR
    assert cerrar.CAMPOS_OBLIGATORIOS == CAMPOS_OBLIGATORIOS_DE_CERRAR


# --------------------------------------------------------------------------
# Heredado de F-031 y ampliado · lo nuevo vive exactamente donde tiene que vivir
# --------------------------------------------------------------------------

#: Las piezas de `codigos_del_parte.py`, que **solo** se definen allí.
PIEZAS_COMPARTIDAS = (
    "CodigosDelParte",
    "codigos_guardados",
    "exigir_codigos_declarados",
    "exigir_codigos_completos",
)

#: Los nombres que F-034 introduce o mueve en el código de producción, y
#: **dónde** se pueden usar, escrito a mano. Hereda las filas que la enmienda
#: del 2026-09-23 dejó en `test_f031_alcance_cerrado.py` y añade las de F-034:
#: `exigir_codigos_completos` (solo el gráfico y el cierre: archivar no la
#: llama, H-4), `CodigoNoConsta` (la levanta el módulo compartido y la traduce
#: a 409 el borde) y `exigir_parte_archivado` (la puerta de archivo en un solo
#: sitio, D-6).
NOMBRES_NUEVOS_Y_DONDE_VIVEN = {
    "CodigosDelParte": {
        "application/pipelines/codigos_del_parte.py",
        "application/pipelines/paso_archivo.py",
        "application/pipelines/paso_grafico.py",
        "application/pipelines/paso_cierre.py",
        "interface_adapters/api/archivar.py",
        "interface_adapters/api/adjuntar.py",
        "interface_adapters/api/cerrar.py",
    },
    "codigos_guardados": {
        "application/pipelines/codigos_del_parte.py",
        "application/pipelines/paso_archivo.py",
        "application/pipelines/paso_grafico.py",
        "application/pipelines/paso_cierre.py",
    },
    "exigir_codigos_declarados": {
        "application/pipelines/codigos_del_parte.py",
        "application/pipelines/paso_archivo.py",
        "application/pipelines/paso_grafico.py",
        "application/pipelines/paso_cierre.py",
    },
    "exigir_codigos_completos": {
        "application/pipelines/codigos_del_parte.py",
        "application/pipelines/paso_grafico.py",
        "application/pipelines/paso_cierre.py",
    },
    "codigos_declarados": {
        "application/pipelines/paso_archivo.py",
        "application/pipelines/paso_grafico.py",
        "application/pipelines/paso_cierre.py",
        "interface_adapters/api/archivar.py",
        "interface_adapters/api/adjuntar.py",
        "interface_adapters/api/cerrar.py",
    },
    "CodigoNoConsta": {
        "domain/models/errores.py",
        "application/pipelines/codigos_del_parte.py",
        "function_app.py",
    },
    "CodigosNoCoinciden": {
        "domain/models/errores.py",
        "application/pipelines/codigos_del_parte.py",
        "function_app.py",
    },
    "es_el_mismo_codigo": {
        "domain/models/nombrado.py",
        "application/pipelines/codigos_del_parte.py",
    },
    "exigir_parte_archivado": {
        "application/pipelines/puerta_de_estado.py",
        "application/pipelines/paso_grafico.py",
        "application/pipelines/paso_cierre.py",
    },
}

#: Los nombres que F-034 **retira** y que no pueden volver a aparecer en
#: producción: las dos copias privadas de la puerta de archivo (D-6) y los dos
#: privados de F-031 que se mudaron (T3).
NOMBRES_RETIRADOS = (
    "_exigir_archivado",
    "_codigos_guardados",
    "_exigir_codigos_declarados",
)


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
    proyecto **explica** el código, y una docstring que cite `CodigosDelParte`
    —las enmiendas fechadas de F-034 lo hacen en prosa— no es usarlo.
    """
    fuente = ruta.read_text(encoding="utf-8")
    return {
        token.string
        for token in tokenize.generate_tokens(io.StringIO(fuente).readline)
        if token.type == tokenize.NAME
    }


def _definiciones(ruta: Path) -> set[str]:
    """Lo que un fichero **define**: clases, funciones y nombres asignados.

    A cualquier nivel, no solo en el de módulo: una copia escondida dentro de
    una función sigue siendo una copia.
    """
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    definidos: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            definidos.add(nodo.name)
        elif isinstance(nodo, ast.Assign | ast.AnnAssign):
            destinos = nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]
            definidos.update(
                destino.id for destino in destinos if isinstance(destino, ast.Name)
            )
    return definidos


def test_f034_las_piezas_compartidas_solo_se_definen_en_su_modulo():
    """D-2 · una regla, un sitio: `codigos_del_parte.py` es la única definición.

    Es lo que la decisión D-2 aprobó y lo que la cabecera del módulo razona: la
    copia que se aflojara sería la que dejara escribir en la reclamación
    equivocada. Un `CodigosDelParte` redefinido en un paso —aunque fuera
    idéntico— convertiría el `isinstance` de otro en mentira.
    """
    donde: dict[str, set[str]] = {nombre: set() for nombre in PIEZAS_COMPARTIDAS}
    for ruta in _ficheros_de_produccion():
        definidos = _definiciones(ruta)
        relativa = ruta.relative_to(RAIZ_DEL_SERVICIO).as_posix()
        for nombre in PIEZAS_COMPARTIDAS:
            if nombre in definidos:
                donde[nombre].add(relativa)

    assert donde == {
        nombre: {"application/pipelines/codigos_del_parte.py"}
        for nombre in PIEZAS_COMPARTIDAS
    }


def test_f034_lo_nuevo_solo_vive_en_los_ficheros_previstos():
    """R39 · la mitad que no depende de `git`: nada se ha desparramado.

    Recorre **todo** el código de producción y exige que cada nombre aparezca
    exactamente donde tiene que aparecer: ni en la persistencia, ni en el
    dominio del nombrado, ni en ningún otro endpoint. Y al revés también: si
    `cerrar.py` dejara de pasar `codigos_declarados`, el cotejo de R9 se
    quedaría sin alimentar desde el borde y este control se pondría rojo.
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


def test_f034_lo_retirado_no_vuelve():
    """D-6, T3 · las copias retiradas no reaparecen en ningún fichero."""
    vuelven = {
        nombre: ruta.relative_to(RAIZ_DEL_SERVICIO).as_posix()
        for ruta in _ficheros_de_produccion()
        for nombre in NOMBRES_RETIRADOS
        if nombre in _nombres_de_codigo(ruta)
    }

    assert vuelven == {}


def _lecturas_de_ctx_archivo(relativa: str) -> list[int]:
    """Las líneas donde un fichero lee o escribe `ctx.archivo`."""
    arbol = _arbol(relativa)
    return [
        nodo.lineno
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Attribute)
        and nodo.attr == "archivo"
        and isinstance(nodo.value, ast.Name)
        and nodo.value.id == "ctx"
    ]


@pytest.mark.parametrize(
    "relativa",
    [
        "application/pipelines/paso_grafico.py",
        "application/pipelines/paso_cierre.py",
        "application/pipelines/puerta_de_estado.py",
        "application/pipelines/codigos_del_parte.py",
    ],
)
def test_f034_r1_la_segunda_fuente_del_archivo_esta_cerrada(relativa):
    """R1, R5 · ni los dos pasos ni sus piezas tocan `ctx.archivo`.

    Era el campo que el borde fabricaba con el `estado_archivo` del cuerpo. Sin
    este control, alguien podría volver a leerlo mañana sin tocar ninguno de
    los ficheros que vigila el diff y los tests de comportamiento seguirían
    verdes mientras el borde no lo rellenara.
    """
    assert _lecturas_de_ctx_archivo(relativa) == []


@pytest.mark.parametrize(
    "relativa",
    ["interface_adapters/api/adjuntar.py", "interface_adapters/api/cerrar.py"],
)
def test_f034_r4_el_borde_no_fabrica_la_traza_de_archivo(relativa):
    """R4 · `adjuntar.py` y `cerrar.py` ya no conocen `TrazaArchivo`."""
    assert "TrazaArchivo" not in _nombres_de_codigo(RAIZ_DEL_SERVICIO / relativa)


def test_f034_el_recorrido_de_produccion_ve_los_ficheros_vigilados():
    """El control de los controles sin `git`: que el recorrido mire donde debe.

    Si la lista de producción saliera vacía o se dejara fuera una carpeta, los
    tests de arriba no verían nada y darían verde sin haber leído nada.
    """
    vistos = {
        f"{SERVICIO}{ruta.relative_to(RAIZ_DEL_SERVICIO).as_posix()}"
        for ruta in _ficheros_de_produccion()
    }

    assert set(FICHEROS_INTOCABLES) <= vistos
    assert {
        ruta for ruta in PRODUCCION_QUE_TOCA_F034 if ruta.startswith(SERVICIO)
    } <= vistos
    assert not any("/tests/" in ruta for ruta in vistos)
