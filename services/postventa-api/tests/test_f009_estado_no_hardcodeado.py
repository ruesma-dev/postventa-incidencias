# services/postventa-api/tests/test_f009_estado_no_hardcodeado.py
"""Control negativo de R3: ni un número de estado de Sigrid en el código.

Es la traducción directa del checkpoint **C3** —«nada contra Sigrid hardcodea
un número de estado»— al modo de `test_f005_logs_sin_datos_personales.py`: se
barre el árbol de producción y se falla si aparece uno.

## Por qué esto no es una manía

El `est` de `dbo.con` es **configuración de la instalación**, no una constante
del producto. Hoy el estado de cierre tiene un número concreto en el ERP de
Ruesma; mañana, en otra instalación o tras un cambio de maestros, tiene otro.
Un número escrito en el código no falla: **cierra la incidencia poniéndola en
el estado equivocado**, en producción, y nadie se entera hasta que alguien mira
la ficha. Por eso el estado se resuelve consultando `dbo.conest` por su
**código** (R1) y por eso aquí no puede haber ni un número.

## Las dos reglas, y qué NO prohíben

1. **En el SQL**: la columna `est` no puede aparecer nunca junto a un literal
   numérico. Todo lo que decide un estado viaja como parámetro `?`.
2. **En las constantes**: ninguna constante de producción cuyo nombre hable de
   estado, cierre o `conest` puede valer un entero.

Lo que **no** prohíben, y conviene decirlo porque es lo primero que confunde a
quien lea esto: los tres valores fijos de la **fila de auditoría** de
`dbo.log` —su origen, su tipo de operación y su marca de realizado—. Son
columnas del registro de log, medidas homogéneas sobre las 6.843 filas de
«Cerrar parte», y **no son el estado de ningún concepto**: `sigrid_tablas.md`
llama a esa columna «Estado/Realizado» del propio log. Un test dedicado
comprueba además que ninguno de los tres se pega al texto del SQL: los tres
viajan como parámetros.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
from domain.models.cierre import CODIGO_ESTADO_CIERRE, CODIGOS_ESTADO_CERRABLE

#: Raíz del servicio (este fichero vive en `<servicio>/tests/`).
SERVICIO = Path(__file__).resolve().parent.parent

#: Carpetas que no son código del servicio.
_IGNORADAS = (".venv", "__pycache__", ".pytest_cache", ".ruff_cache")

#: El árbol de **producción**: todo menos la suite.
#:
#: Los tests quedan fuera a propósito: un test **tiene** que poder escribir
#: números de estado, porque para comprobar que el ERP los resuelve hace falta
#: fabricar respuestas del ERP con números dentro.
CAPAS_DE_PRODUCCION = (
    "domain",
    "application",
    "infrastructure",
    "interface_adapters",
    "config",
)

#: La columna `est` pegada a un literal numérico, en cualquier SQL (R3).
#:
#: Cubre las formas con las que aparecería de verdad: `est = 9`, `con.est=9`,
#: `c.est <> 9`, `est IN (9, 7)`. Todas ellas son un estado decidido en el
#: código en vez de resuelto contra `conest`.
PATRON_ESTADO_EN_SQL = re.compile(
    r"\b(?:[a-z]+\.)?est\s*(?:=|==|<>|!=|>=|<=|>|<|\bIN\b)\s*\(?\s*\d",
    re.IGNORECASE,
)

#: Los nombres de constante que **no** pueden valer un entero (R3).
#:
#: Si una constante habla de estado, de cierre o de `conest`, lo que guarda es
#: un **código** —`'CER'`— y jamás su número.
PATRON_NOMBRE_DE_ESTADO = re.compile(
    r"(ESTADO|CIERRE|CERRAD|CONEST|^EST$|^EST_|_EST$)", re.IGNORECASE
)


def _ficheros_de_produccion() -> list[Path]:
    """Los módulos de producción del servicio, sin la suite ni el venv."""
    ficheros = [
        fichero
        for capa in CAPAS_DE_PRODUCCION
        for fichero in (SERVICIO / capa).rglob("*.py")
        if not any(parte in _IGNORADAS for parte in fichero.parts)
    ]
    ficheros.append(SERVICIO / "function_app.py")
    return sorted(ficheros)


def estados_cableados_en_sql(texto: str) -> list[str]:
    """Los sitios donde `est` aparece junto a un número (R3).

    Función pura y pública **a propósito**: un barrido que solo se ejerce
    contra ficheros que ya están limpios no demuestra nada. Aquí abajo hay un
    control negativo que la alimenta con una sentencia culpable y comprueba que
    salta.
    """
    return PATRON_ESTADO_EN_SQL.findall(texto)


def constantes_de_estado_enteras(texto: str) -> list[str]:
    """Las constantes de módulo que hablan de estado y valen un entero (R3).

    Con `ast` y no con una búsqueda de texto: lo que importa es **el valor
    asignado**, no que en algún comentario aparezca un número al lado de la
    palabra «estado».
    """
    culpables: list[str] = []
    for nodo in ast.parse(texto).body:
        if not isinstance(nodo, (ast.Assign, ast.AnnAssign)):
            continue
        destinos = (
            nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]
        )
        nombres = [
            destino.id for destino in destinos if isinstance(destino, ast.Name)
        ]
        for nombre in nombres:
            if PATRON_NOMBRE_DE_ESTADO.search(nombre) and _es_entero(nodo.value):
                culpables.append(nombre)
    return culpables


def _es_entero(valor: ast.expr | None) -> bool:
    """¿El valor asignado es un entero, suelto o dentro de una colección?"""
    if valor is None:
        return False
    if isinstance(valor, ast.Constant):
        return isinstance(valor.value, int) and not isinstance(valor.value, bool)
    if isinstance(valor, (ast.Tuple, ast.List, ast.Set)):
        return any(_es_entero(elemento) for elemento in valor.elts)
    return False


# --------------------------------------------------------------------------
# R3 · el barrido sobre el árbol de producción
# --------------------------------------------------------------------------


def test_f009_r3_hay_arbol_de_produccion_que_barrer():
    """Guardia del propio barrido: si no hay ficheros, no protege nada.

    Sin esto, un cambio de estructura de carpetas dejaría el control pasando en
    verde sobre una lista vacía, que es la peor forma de fallar.
    """
    ficheros = _ficheros_de_produccion()

    assert len(ficheros) > 20
    assert all(fichero.is_file() for fichero in ficheros)


def test_f009_r3_ningun_sql_de_produccion_compara_est_con_un_numero():
    """R3 · el estado siempre viaja como parámetro, nunca pegado al SQL.

    Si esto falla, **no se relaja el patrón**: se saca el número del SQL y se
    manda como parámetro leído de `conest`.
    """
    hallazgos = {
        fichero.relative_to(SERVICIO).as_posix(): estados_cableados_en_sql(
            fichero.read_text(encoding="utf-8")
        )
        for fichero in _ficheros_de_produccion()
        if estados_cableados_en_sql(fichero.read_text(encoding="utf-8"))
    }

    assert hallazgos == {}


def test_f009_r3_ninguna_constante_de_estado_de_produccion_es_un_numero():
    """R3 · ni como valor por defecto, ni como configuración, ni como constante.

    Los tres sitios los nombra el requisito uno a uno, y los tres acaban en lo
    mismo: un número que alguien escribió y que nadie va a revisar cuando el
    ERP cambie sus maestros.
    """
    hallazgos = {
        fichero.relative_to(SERVICIO).as_posix(): constantes_de_estado_enteras(
            fichero.read_text(encoding="utf-8")
        )
        for fichero in _ficheros_de_produccion()
        if constantes_de_estado_enteras(fichero.read_text(encoding="utf-8"))
    }

    assert hallazgos == {}


# --------------------------------------------------------------------------
# R3 · control negativo: los dos barridos saltan de verdad
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sospechoso",
    [
        "UPDATE dbo.con SET est = 9 WHERE ide = ?",
        "SELECT ide FROM dbo.con WHERE c.est=9",
        "SELECT ide FROM dbo.con WHERE est IN (5, 9)",
        "UPDATE dbo.con SET est = ? WHERE ide = ? AND est <> 9",
    ],
)
def test_f009_r3_el_barrido_de_sql_caza_un_numero_inyectado(sospechoso):
    """R3 · control negativo: un patrón que nunca se ha visto saltar no protege.

    Cuatro formas reales de escribir el mismo fallo. Sin este test, un patrón
    mal escrito dejaría pasar todo y el barrido de arriba pasaría en verde para
    siempre.
    """
    assert estados_cableados_en_sql(sospechoso) != []


def test_f009_r3_el_sql_correcto_no_hace_saltar_el_barrido():
    """R3 · y no salta con lo que sí es correcto: el estado como parámetro.

    Un control que salta con todo es un control que alguien acaba desactivando.
    """
    correcto = (
        "UPDATE dbo.con SET est = ? WHERE ide = ? AND tip = ? AND est = ?\n"
        "LEFT JOIN dbo.conest ed ON ed.tip = c.tip AND ed.cod = ?"
    )

    assert estados_cableados_en_sql(correcto) == []


@pytest.mark.parametrize(
    "sospechoso",
    [
        "EST_CERRADA = 9",
        "ESTADO_DE_CIERRE = 9",
        "ESTADOS_CERRABLES = (1, 3, 5)",
        "CONEST_CIERRE: int = 9",
    ],
)
def test_f009_r3_el_barrido_de_constantes_caza_una_inyectada(sospechoso):
    """R3 · control negativo del segundo barrido, con sus cuatro disfraces."""
    assert constantes_de_estado_enteras(sospechoso) != []


def test_f009_r3_las_constantes_correctas_no_hacen_saltar_el_barrido():
    """R3 · un código y una lista de códigos pasan, que es lo que se quiere."""
    correcto = (
        "CODIGO_ESTADO_CIERRE = 'CER'\n"
        "CODIGOS_ESTADO_CERRABLE = ('SAT', 'PTE', 'TER')\n"
    )

    assert constantes_de_estado_enteras(correcto) == []


# --------------------------------------------------------------------------
# R3 · y lo que el dominio sí declara: códigos
# --------------------------------------------------------------------------


def test_f009_r3_lo_que_el_dominio_declara_son_codigos():
    """R3 · la cara positiva del control: `CER` y los tres cerrables, en texto."""
    assert isinstance(CODIGO_ESTADO_CIERRE, str)
    assert not CODIGO_ESTADO_CIERRE.isdigit()
    assert all(
        isinstance(codigo, str) and not codigo.isdigit()
        for codigo in CODIGOS_ESTADO_CERRABLE
    )
