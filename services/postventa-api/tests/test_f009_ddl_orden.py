# services/postventa-api/tests/test_f009_ddl_orden.py
"""El DDL que añade F-009, contra el DDL **real** del repositorio.

`test_f005_ddl_orden.py` prueba el mecanismo con ficheros inventados en un
directorio temporal. Este prueba lo contrario: que el fichero de verdad que
esta feature añade **pasa la guarda de verdad**, con el orden de verdad.

Es una distinción que importa en un servidor compartido con la producción de
albaranes, partes y el datamart: la guarda puede ser impecable y el fichero
nuevo colarse fuera del esquema propio, o no aplicarse nunca porque nadie lo
recoge.
"""

from __future__ import annotations

import pytest
from infrastructure.persistencia.arranque import DIRECTORIO_SQL
from infrastructure.persistencia.ddl import (
    ESQUEMA_LITERAL,
    cargar_ddl,
    ficheros_ddl,
    sentencias,
    validar,
)

#: El fichero que añade F-009.
FICHERO = "08_usuarios_sigrid.sql"

#: La tabla que construye.
TABLA = "usuarios_sigrid"


def _texto() -> str:
    return (DIRECTORIO_SQL / FICHERO).read_text(encoding="utf-8")


def test_f009_el_ddl_de_f009_se_recoge_con_los_demas():
    """Si no se recogiera, la tabla no existiría y nadie lo notaría al arrancar.

    Un fichero de DDL que nadie aplica es peor que uno que falla: el fallo se
    ve, y la tabla que falta se descubre en producción, cerrando.
    """
    nombres = [ruta.name for ruta in ficheros_ddl(DIRECTORIO_SQL)]

    assert FICHERO in nombres


def test_f009_el_ddl_de_f009_va_despues_del_esquema():
    """El orden **es** una dependencia: el esquema antes que la tabla.

    Hasta F-012 este fichero era además **el último**, y el test lo fijaba.
    Ya no lo es —`09_graficos.sql` va detrás— y esa aserción se retira: era
    una propiedad del catálogo en aquel momento, no del DDL de F-009. Lo que
    sigue vigente, y es lo que de verdad protegía, es la dependencia.
    """
    nombres = [ruta.name for ruta in ficheros_ddl(DIRECTORIO_SQL)]

    assert nombres.index("01_esquema.sql") < nombres.index(FICHERO)


def test_f009_la_guarda_acepta_el_ddl_de_f009_tal_y_como_esta():
    """Se valida el fichero **real**, no una copia inventada.

    Si mañana alguien le añade una sentencia que la guarda no reconoce, este
    test se cae antes de que llegue a aplicarse contra el servidor compartido.
    """
    for sentencia in sentencias(_texto()):
        validar(sentencia, esquema=ESQUEMA_LITERAL)


def test_f009_el_ddl_completo_del_proyecto_sigue_siendo_valido():
    """Y el conjunto, cargado y validado de una pasada, también.

    `cargar_ddl` es la única puerta de entrada al DDL: sustituye el esquema
    literal por el configurado **en el mismo paso en que valida**, así que no
    hay ninguna ventana en la que exista una sentencia sustituida y no
    revisada.
    """
    cargadas = cargar_ddl(DIRECTORIO_SQL, esquema=ESQUEMA_LITERAL)

    assert any(TABLA in sentencia for sentencia in cargadas)


def test_f009_la_tabla_se_crea_dentro_del_esquema_propio_y_nunca_en_public():
    """`CLAUDE.md`, regla dura: fuera del esquema propio no se toca nada.

    `public` lo usan albaranes y partes para sus propias tablas, y el servidor
    es el mismo.
    """
    texto = _texto()

    assert f"{ESQUEMA_LITERAL}.{TABLA}" in texto
    assert "public." not in texto.lower()


def test_f009_la_tabla_es_idempotente():
    """Aplicar el DDL dos veces no puede fallar: se aplica en cada arranque."""
    assert "CREATE TABLE IF NOT EXISTS" in _texto()


def test_f009_el_ddl_no_declara_ningun_tipo_binario():
    """Ni un BLOB: el disco de ese servidor es compartido y ya se llenó una vez.

    Aquí no viene a cuento —esta tabla guarda dos textos y dos fechas— y por eso
    mismo es el sitio barato para dejar la comprobación puesta.
    """
    en_mayusculas = _texto().upper()

    for tipo in ("BYTEA", "BLOB", "LARGE OBJECT"):
        assert tipo not in en_mayusculas


@pytest.mark.parametrize(
    "columna",
    ["usuario_oid", "login_sigrid", "alta_at_utc", "verificado_at_utc"],
)
def test_f009_la_tabla_declara_las_cuatro_columnas_del_diseno(columna):
    """Las cuatro de `design.md` §7.4, ni una más."""
    assert columna in _texto()


def test_f009_r33_la_marca_de_verificacion_es_anulable():
    """R33, R34 · no todo lo que hay aquí está verificado, y hay que poder verlo.

    Un alta manual entra sin marca; la siembra la pone al confirmarse contra el
    ERP. Si la columna fuera `NOT NULL`, el alta manual tendría que inventarse
    una fecha de verificación que nadie hizo — y eso es exactamente lo que R32
    prohíbe: dar por confirmado lo que no se ha comprobado.
    """
    linea = next(
        fila for fila in _texto().splitlines() if "verificado_at_utc" in fila and "timestamptz" in fila
    )

    assert "NOT NULL" not in linea.upper()


def test_f009_el_oid_es_la_clave_primaria_y_no_hay_dos_filas_por_persona():
    """Una sola correspondencia por usuario, garantizada por la base.

    Dos filas para la misma persona con logins distintos serían dos identidades
    para firmar el mismo cierre, y quién firma lo decidiría el azar del
    `ORDER BY`.
    """
    linea = next(
        fila for fila in _texto().splitlines() if fila.strip().startswith("usuario_oid")
    )

    assert "PRIMARY KEY" in linea.upper()
