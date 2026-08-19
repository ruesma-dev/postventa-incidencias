# services/postventa-api/tests/test_f005_ddl_orden.py
"""El orden en que se aplica el DDL (F-005, R1).

El orden **es** una dependencia: el esquema antes que las tablas, las tablas
antes que las claves ajenas que apuntan a ellas. Que salga bien no puede
depender de en qué orden devuelva el sistema de ficheros los nombres.

Los ficheros de estos tests son inventados y se crean en un directorio
temporal: no se toca el DDL real.
"""

from __future__ import annotations

import pytest
from domain.models.errores import DdlInseguro

from infrastructure.persistencia.ddl import ficheros_ddl


def _crear(directorio, *nombres):
    """Crea ficheros vacíos con esos nombres y devuelve el directorio."""
    for nombre in nombres:
        (directorio / nombre).write_text("", encoding="utf-8")
    return directorio


def test_f005_r1_los_ficheros_salen_en_orden_lexicografico(tmp_path):
    """Se aplican por nombre ascendente, no por fecha ni por descubrimiento.

    Se crean a propósito en orden inverso: si `ficheros_ddl` devolviera lo que
    da el sistema de ficheros, este test lo cazaría en cuanto el orden de
    creación importara.
    """
    _crear(
        tmp_path,
        "07_preferencias.sql",
        "03_partes.sql",
        "01_esquema.sql",
        "10_extra.sql",
        "02_remesas.sql",
    )

    nombres = [ruta.name for ruta in ficheros_ddl(tmp_path)]

    assert nombres == [
        "01_esquema.sql",
        "02_remesas.sql",
        "03_partes.sql",
        "07_preferencias.sql",
        "10_extra.sql",
    ]


def test_f005_r1_un_sql_fuera_de_convencion_no_se_ignora(tmp_path):
    """Un `.sql` mal nombrado se rechaza; no se aplica a medias ni se calla.

    Un fichero de DDL que nadie aplica es peor que uno que falla: el fallo se
    ve, y la tabla que falta se descubre en producción.
    """
    _crear(tmp_path, "01_esquema.sql", "parches.sql")

    with pytest.raises(DdlInseguro) as fallo:
        ficheros_ddl(tmp_path)

    assert "parches.sql" in fallo.value.motivo


def test_f005_r1_un_directorio_sin_sql_es_un_error(tmp_path):
    """Aplicar «nada» no es aplicar el DDL: es no haberlo encontrado."""
    with pytest.raises(DdlInseguro):
        ficheros_ddl(tmp_path)


def test_f005_r1_un_directorio_que_no_existe_es_un_error(tmp_path):
    """Una ruta mal configurada tiene que decirlo, no arrancar sin esquema."""
    with pytest.raises(DdlInseguro) as fallo:
        ficheros_ddl(tmp_path / "no_existe")

    assert "no_existe" in fallo.value.motivo


def test_f005_r1_solo_entran_los_sql(tmp_path):
    """Un `README.md` en el directorio del DDL no estorba."""
    _crear(tmp_path, "01_esquema.sql")
    (tmp_path / "README.md").write_text("nota inventada", encoding="utf-8")

    assert [ruta.name for ruta in ficheros_ddl(tmp_path)] == ["01_esquema.sql"]
