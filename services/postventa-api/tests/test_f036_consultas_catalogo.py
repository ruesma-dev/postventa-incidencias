# services/postventa-api/tests/test_f036_consultas_catalogo.py
"""El SQL del catálogo de la obra y el mapeo de sus filas (F-036 T12).

`specs/F-036-importar-excel/design.md` §5.1 y §6.3 (quinta enmienda): **dos**
lecturas, `SQL_UNIDADES_DE_LA_OBRA` y `SQL_OFICIOS_DE_LA_OBRA`, y ninguna más.

- las dos sentencias, **carácter a carácter**, con sus `?` y sin interpolar;
- ni la marca de CIF (F-050) ni las actividades ni su árbol (F-039): ninguna
  referencia a `prv`, `cif`, `conact` ni `auxpronat`;
- el mapeo de cada fila al puerto, en texto; la fila sin proveedor (el `LEFT
  JOIN`, R12 y los oficios `0133`, `0144` y `0166` de la 0677) y la fila mal
  formada, que es `ValueError` sin nombrar lo que traía;
- el puerto tiene dos métodos y la fila de `obrofc` no lleva marca de CIF.

Módulo puro: sin red, sin `httpx`, sin cliente. Ni un dato real: la
referencia de obra, los nombres de unidad y de proveedor son inventados.
"""

from __future__ import annotations

import ast
import inspect
import re
from dataclasses import fields
from pathlib import Path

import pytest

from domain.ports.catalogo_obra import (
    CatalogoObraPort,
    FilaOficioCatalogo,
    FilaUnidadCatalogo,
    LecturaCatalogo,
)
from infrastructure.sigrid import consultas_catalogo
from infrastructure.sigrid.consultas_catalogo import (
    SQL_OFICIOS_DE_LA_OBRA,
    SQL_UNIDADES_DE_LA_OBRA,
    fila_a_oficio_catalogo,
    fila_a_unidad_catalogo,
    select_oficios_de_la_obra,
    select_unidades_de_la_obra,
)

SERVICIO = Path(__file__).resolve().parents[1]
MODULO = SERVICIO / "infrastructure" / "sigrid" / "consultas_catalogo.py"
PUERTO = SERVICIO / "domain" / "ports" / "catalogo_obra.py"

#: Una referencia de obra (`upv.obride`) **inventada**.
OBRIDE = 987_654_321

#: Nombres **inventados**, ninguno de un proveedor real.
PROVEEDOR = "Carpinterías Ejemplo S.L."
UNIDAD = "Viviendas Bloque Villa 5"

SENTENCIAS = (SQL_UNIDADES_DE_LA_OBRA, SQL_OFICIOS_DE_LA_OBRA)


# ==========================================================================
# Las dos sentencias, carácter a carácter (design.md §6.3)
# ==========================================================================


def test_f036_t12_sql_unidades_de_la_obra_caracter_a_caracter():
    """R10 · las unidades de **todas** las obras con ese código, con su
    `obride` para contarlas y el nombre de la obra. El código, literal."""
    assert SQL_UNIDADES_DE_LA_OBRA == (
        "SELECT v.obride, o.cod, o.res, u.cod, u.res\n"
        "FROM dbo.upv v\n"
        "JOIN dbo.con o ON o.ide = v.obride\n"
        "JOIN dbo.con u ON u.ide = v.ide\n"
        "WHERE LTRIM(RTRIM(o.cod)) = ?\n"
        "ORDER BY u.cod"
    )


def test_f036_r13_sql_oficios_de_la_obra_caracter_a_caracter():
    """R13 · sin los oficios de baja; `LEFT JOIN` en el proveedor (R12, §6.3):
    la fila de `obrofc` sin proveedor también viene."""
    assert SQL_OFICIOS_DE_LA_OBRA == (
        "SELECT a.cod, a.res, p.cod, p.res\n"
        "FROM dbo.obrofc f\n"
        "JOIN dbo.auxofc a     ON a.ide = f.ofcide\n"
        "LEFT JOIN dbo.con p   ON p.ide = f.prvide\n"
        "WHERE f.obride = ? AND ISNULL(a.fecbaj, 0) = 0\n"
        "ORDER BY a.cod, p.cod"
    )


@pytest.mark.parametrize("sql", SENTENCIAS, ids=("unidades", "oficios"))
def test_f036_r46_cada_una_es_un_solo_select_sin_nada_que_escriba(sql):
    """R46 · una sola sentencia de lectura: la pasarela solo admite eso en
    `sql/read`, y aquí no hay nada que escribir."""
    assert sql.startswith("SELECT ")
    assert ";" not in sql
    for prohibido in ("INSERT", "UPDATE", "DELETE", "MERGE", "EXEC", "INTO", "DROP"):
        assert not re.search(rf"\b{prohibido}\b", sql, re.IGNORECASE)


@pytest.mark.parametrize("sql", SENTENCIAS, ids=("unidades", "oficios"))
def test_f036_t12_cada_una_lleva_un_solo_marcador(sql):
    assert sql.count("?") == 1


@pytest.mark.parametrize("sql", SENTENCIAS, ids=("unidades", "oficios"))
def test_f036_t12_ni_cif_ni_proveedores_del_maestro_ni_actividades(sql):
    """Quinta enmienda · la marca de CIF sale a F-050 y las actividades y su
    árbol a F-039. `f.prvide` es la columna de `obrofc`, no la tabla `prv`."""
    for prohibido in ("prv", "cif", "conact", "auxpronat", "DENSE_RANK"):
        assert not re.search(rf"\b{prohibido}\b", sql, re.IGNORECASE)


def test_f036_t12_el_modulo_no_nombra_ninguna_tabla_de_fuera_de_f036():
    """Ni en un comentario: lo que no está en el módulo no se cuela en una
    sentencia por descuido."""
    texto = MODULO.read_text(encoding="utf-8")

    for prohibido in (r"dbo\.prv\b", r"\bcif\b", r"\bconact\b", r"\bauxpronat\b"):
        assert not re.search(prohibido, texto, re.IGNORECASE)


def test_f036_t12_solo_dos_sentencias():
    """Quinta enmienda · eran cuatro lecturas; vuelven a ser dos."""
    sentencias = sorted(
        nombre for nombre in dir(consultas_catalogo) if nombre.startswith("SQL_")
    )

    assert sentencias == ["SQL_OFICIOS_DE_LA_OBRA", "SQL_UNIDADES_DE_LA_OBRA"]


# ==========================================================================
# Los parámetros: en orden y nunca en el texto
# ==========================================================================


def test_f036_t12_las_unidades_van_por_el_codigo_de_obra_tal_cual():
    """El código llega ya normalizado (R9) y se compara literal, con sus
    ceros: es el que tiene que casar con el volcado de F-040 (§6.3)."""
    assert select_unidades_de_la_obra(codigo_obra="0677") == (
        SQL_UNIDADES_DE_LA_OBRA,
        ("0677",),
    )


def test_f036_t12_los_oficios_van_por_la_referencia_de_la_obra():
    assert select_oficios_de_la_obra(obra_ref=str(OBRIDE)) == (
        SQL_OFICIOS_DE_LA_OBRA,
        (str(OBRIDE),),
    )


@pytest.mark.parametrize(
    ("componer", "valor"),
    (
        (lambda v: select_unidades_de_la_obra(codigo_obra=v), "X' OR 1=1 --"),
        (lambda v: select_oficios_de_la_obra(obra_ref=v), "1; DROP TABLE x"),
    ),
    ids=("unidades", "oficios"),
)
def test_f036_t12_ningun_valor_se_interpola_en_el_texto(componer, valor):
    """`azure-apps/sigrid_api.md` §5.2: siempre `?` y el valor en `parameters`."""
    sql, parametros = componer(valor)

    assert valor not in sql
    assert parametros == (valor,)


# ==========================================================================
# El mapeo de una unidad
# ==========================================================================


def test_f036_t12_una_unidad_se_mapea_en_texto_y_en_orden():
    fila = [OBRIDE, "0677", "MIRASIERRA EJEMPLO", "0677.03VILLA 5.", UNIDAD]

    assert fila_a_unidad_catalogo(fila) == FilaUnidadCatalogo(
        obra_ref=str(OBRIDE),
        obra_codigo="0677",
        obra_nombre="MIRASIERRA EJEMPLO",
        unidad_codigo="0677.03VILLA 5.",
        unidad_nombre=UNIDAD,
    )


def test_f036_t12_una_unidad_con_nulos_los_deja_en_none():
    """Qué hacer con una unidad sin nombre o sin código lo decide la
    aplicación, no el mapeo."""
    unidad = fila_a_unidad_catalogo((OBRIDE, None, None, None, None))

    assert unidad == FilaUnidadCatalogo(str(OBRIDE), None, None, None, None)


def test_f036_t12_un_codigo_nunca_se_convierte_en_numero():
    """Los códigos son texto: `int()` sobre un código es un bug."""
    unidad = fila_a_unidad_catalogo((OBRIDE, 677, "X", 3, "Y"))
    oficio = fila_a_oficio_catalogo((133, "Z", 42, "W"))

    assert (unidad.obra_codigo, unidad.unidad_codigo) == ("677", "3")
    assert (oficio.oficio_codigo, oficio.proveedor_codigo) == ("133", "42")


def test_f036_t12_los_textos_no_se_recortan_en_el_mapeo():
    """El mapeo no normaliza: las etiquetas las compone el dominio (R8)."""
    unidad = fila_a_unidad_catalogo((OBRIDE, " 0677 ", " OBRA ", " U1 ", " Villa "))

    assert unidad.obra_codigo == " 0677 "
    assert unidad.unidad_codigo == " U1 "
    assert unidad.unidad_nombre == " Villa "


@pytest.mark.parametrize("obride", (None, "", "   "), ids=("nulo", "vacio", "blancos"))
def test_f036_t12_una_unidad_sin_referencia_de_obra_no_se_admite(obride):
    """Sin `obra_ref` no se cuentan las obras (R10): dos filas sin ella
    contarían como una y esconderían la segunda."""
    with pytest.raises(ValueError) as fallo:
        fila_a_unidad_catalogo((obride, "0677", "OBRA", "U1", UNIDAD))

    assert UNIDAD not in str(fallo.value)


def test_f036_t12_obra_ref_no_sale_en_el_repr():
    """Opaca: un log descuidado de la fila no la saca."""
    unidad = fila_a_unidad_catalogo((OBRIDE, "0677", "OBRA", "U1", "Villa 1"))

    assert str(OBRIDE) not in repr(unidad)


# ==========================================================================
# El mapeo de una fila de obrofc
# ==========================================================================


def test_f036_t12_una_fila_de_obrofc_con_proveedor():
    fila = ["0101", "CARPINTERÍA", "P0042", PROVEEDOR]

    assert fila_a_oficio_catalogo(fila) == FilaOficioCatalogo(
        oficio_codigo="0101",
        oficio_nombre="CARPINTERÍA",
        proveedor_codigo="P0042",
        proveedor_nombre=PROVEEDOR,
    )


def test_f036_t12_una_fila_de_obrofc_sin_proveedor():
    """El `LEFT JOIN` (§6.3): en la 0677, `0133`, `0144` y `0166`. Es un oficio
    de la obra que no ofrece ningún par (R12, R71)."""
    assert fila_a_oficio_catalogo(("0133", "PINTURA", None, None)) == (
        FilaOficioCatalogo("0133", "PINTURA", None, None)
    )


def test_f036_t12_un_oficio_sin_nombre_se_admite():
    assert fila_a_oficio_catalogo(("0133", None, None, None)).oficio_nombre is None


@pytest.mark.parametrize("codigo", (None, "", "  "), ids=("nulo", "vacio", "blancos"))
def test_f036_t12_una_fila_de_obrofc_sin_oficio_no_se_admite(codigo):
    """Sin código de oficio no hay nada que ofrecer ni que resolver (R93)."""
    with pytest.raises(ValueError) as fallo:
        fila_a_oficio_catalogo((codigo, "PINTURA", "P0042", PROVEEDOR))

    assert PROVEEDOR not in str(fallo.value)


# ==========================================================================
# La fila mal formada
# ==========================================================================


@pytest.mark.parametrize(
    ("mapeo", "fila"),
    (
        (fila_a_unidad_catalogo, (OBRIDE, "0677", "OBRA", "U1")),
        (fila_a_unidad_catalogo, (OBRIDE, "0677", "OBRA", "U1", UNIDAD, "X")),
        (fila_a_unidad_catalogo, "abcde"),
        (fila_a_unidad_catalogo, None),
        (fila_a_unidad_catalogo, {"obride": OBRIDE}),
        (fila_a_oficio_catalogo, ("0101", "CARPINTERÍA", "P0042")),
        (fila_a_oficio_catalogo, ("0101", "CARPINTERÍA", "P0042", PROVEEDOR, "X")),
        (fila_a_oficio_catalogo, "abcd"),
        (fila_a_oficio_catalogo, 42),
    ),
    ids=(
        "unidad_corta",
        "unidad_larga",
        "unidad_texto",
        "unidad_nula",
        "unidad_objeto",
        "oficio_corta",
        "oficio_larga",
        "oficio_texto",
        "oficio_numero",
    ),
)
def test_f036_t12_una_fila_con_otra_forma_es_valueerror(mapeo, fila):
    """Una cadena de cinco letras se desempaquetaría en cinco «columnas»: se
    exige una lista o una tupla, que es lo que trae `rows[][]`. El mensaje no
    lleva la fila: puede traer el nombre de un proveedor (R47)."""
    with pytest.raises(ValueError) as fallo:
        mapeo(fila)

    assert PROVEEDOR not in str(fallo.value)
    assert UNIDAD not in str(fallo.value)


# ==========================================================================
# El puerto: dos métodos y sin marca de CIF (quinta enmienda)
# ==========================================================================


def test_f036_t12_el_puerto_tiene_dos_metodos_y_ni_uno_mas():
    metodos = sorted(
        nombre
        for nombre, valor in vars(CatalogoObraPort).items()
        if not nombre.startswith("_") and callable(valor)
    )

    assert metodos == ["leer_oficios", "leer_unidades"]


def test_f036_t12_los_metodos_piden_sus_argumentos_por_nombre():
    unidades = inspect.signature(CatalogoObraPort.leer_unidades).parameters
    oficios = inspect.signature(CatalogoObraPort.leer_oficios).parameters

    assert list(unidades) == ["self", "codigo_obra"]
    assert list(oficios) == ["self", "obra_ref"]
    assert unidades["codigo_obra"].kind is inspect.Parameter.KEYWORD_ONLY
    assert oficios["obra_ref"].kind is inspect.Parameter.KEYWORD_ONLY


def test_f036_t12_las_filas_tienen_los_campos_del_diseno():
    assert [c.name for c in fields(FilaUnidadCatalogo)] == [
        "obra_ref",
        "obra_codigo",
        "obra_nombre",
        "unidad_codigo",
        "unidad_nombre",
    ]
    assert [c.name for c in fields(FilaOficioCatalogo)] == [
        "oficio_codigo",
        "oficio_nombre",
        "proveedor_codigo",
        "proveedor_nombre",
    ]
    assert [c.name for c in fields(LecturaCatalogo)] == ["filas", "llego_al_techo"]


@pytest.mark.parametrize(
    ("valor", "campo"),
    (
        (FilaOficioCatalogo("0101", "CARPINTERÍA", None, None), "oficio_codigo"),
        (FilaUnidadCatalogo(str(OBRIDE), "0677", None, "U1", None), "obra_ref"),
        (LecturaCatalogo((), False), "llego_al_techo"),
    ),
    ids=("oficio", "unidad", "lectura"),
)
def test_f036_t12_las_filas_y_la_lectura_son_inmutables(valor, campo):
    """Lo destapó la mutación del Bloque 4: solo se comprobaba la de oficios.
    Una lectura que se pudiera tocar por el camino dejaría cambiar el techo o
    la obra después de decidir con ellos."""
    with pytest.raises(AttributeError):
        setattr(valor, campo, "otra")


# ==========================================================================
# Puros: sin red, sin cliente, sin infraestructura en el puerto
# ==========================================================================


def _importados_de(modulo: Path) -> set[str]:
    arbol = ast.parse(modulo.read_text(encoding="utf-8"))
    importados: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module)
        elif isinstance(nodo, ast.Import):
            importados.update(alias.name for alias in nodo.names)
    return importados


def test_f036_t12_las_consultas_son_puras():
    importados = _importados_de(MODULO)

    for vetado in ("httpx", "tenacity", "infrastructure.sigrid.cliente"):
        assert vetado not in importados


def test_f036_t12_el_puerto_solo_conoce_el_dominio():
    for modulo in _importados_de(PUERTO):
        assert not modulo.startswith(("infrastructure", "application", "httpx"))
