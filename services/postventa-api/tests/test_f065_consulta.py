# services/postventa-api/tests/test_f065_consulta.py
"""La consulta de las reclamaciones de la obra y su mapeo (F-065 T5; R5, R6, R33).

`specs/F-065-revision-sigrid-backend/design.md` §3 (el SQL) y §10.2 (el puerto
y el recorte de los códigos). Módulo puro: aquí no hay red, ni base, ni IA.

| Caso | Requisito |
|---|---|
| `SQL_RECLAMACIONES_DE_LA_OBRA` carácter a carácter, la de §3 **y** la del script 29 | R5, R6, R29 |
| los cuatro parámetros en el orden de los marcadores; ningún valor en el texto | R5 |
| las 31 columnas: las 12 de R6 y la lista cerrada de R33; ninguna prohibida | R6, R33 |
| el mapeo: columnas exactas, `obra_ref` y `cod` obligatorios, `YYYYMMDD` a fecha, `0` a nulo, una fecha imposible es error **sin la fila** | R6, R33, R40 |
| el recorte de `estado_codigo`, `cod`, `tipo_codigo` y `clase_codigo`; `unidad_codigo` y `oficio_codigo` **tal cual** | §10.2 (enmienda del 2026-10-28) |
| la consulta de la guarda (`SQL_RECLAMACIONES_DE_LAS_UNIDADES`), carácter a carácter con §15.5 y con el script 29, de 1 a `N` marcadores, sin R33 | R44, R70 (T15) |
| su mapeo: 12 columnas, `ficha` a `None`, los mismos recortes | R44, §15.2 (T15) |

Datos inventados (R39): obra `9901`, unidades `9901.03VILLA n.`, códigos
`RS26.09/…` de §5.4, «Ejemplo …», teléfonos `000 000 00n`, correos
`@ejemplo.invalid`. Ningún identificador real; la referencia se compone con
`UUID(int=n)`.
"""

from __future__ import annotations

import re
from dataclasses import FrozenInstanceError, fields, replace
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from domain.models.volcado import PREFIJO_REFERENCIA
from domain.ports.reclamaciones_obra import FichaReclamacion, FilaReclamacionObra
from infrastructure.sigrid.consultas_catalogo import SQL_UNIDADES_DE_LA_OBRA
from infrastructure.sigrid.consultas_reclamaciones_obra import (
    CAMPO_REFERENCIA,
    COLUMNAS_DE_LAS_UNIDADES,
    COLUMNAS_RECLAMACION,
    MARCADORES,
    MAX_UNIDADES,
    PATRON_REFERENCIA,
    SQL_RECLAMACIONES_DE_LA_OBRA,
    SQL_RECLAMACIONES_DE_LAS_UNIDADES,
    fila_a_reclamacion_de_las_unidades,
    fila_a_reclamacion_obra,
    select_reclamaciones_de_la_obra,
    select_reclamaciones_de_las_unidades,
)

RAIZ = Path(__file__).resolve().parents[3]
DESIGN = RAIZ / "specs" / "F-065-revision-sigrid-backend" / "design.md"
SCRIPT = RAIZ / "infra" / "29_reclamaciones_obra_sigrid.ps1"

OBRA = "9901"
TIP = 708
REFERENCIA = f"{PREFIJO_REFERENCIA}{UUID(int=1)}"

#: `design.md` §3, tal cual (treinta y una columnas).
SQL_DE_DESIGN = (
    "SELECT v.obride, c.cod, e.cod, c.fec, u.cod, a.cod, a.res, t.cod, t.res, r.resubi, c.res, p.valt,\n"
    "       CAST(r.tex AS nvarchar(max)), r.motrcp, r.texurg, r.rcptip, r.fecpre,\n"
    "       CAST(r.solrcp AS nvarchar(max)), k.cod, k.res,\n"
    "       CAST(r.tel AS nvarchar(max)), CAST(r.ele AS nvarchar(max)),\n"
    "       cl.res, pr.nom, pr.tel, pr.tel2, pr.ele, pc.nom, pc.tel, pc.tel2, pc.ele\n"
    "FROM dbo.rcp r\n"
    "JOIN dbo.con c ON c.ide = r.ide\n"
    "JOIN dbo.upv v ON v.ide = r.upvide\n"
    "JOIN dbo.con u ON u.ide = v.ide\n"
    "JOIN dbo.con o ON o.ide = v.obride\n"
    "LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est\n"
    "LEFT JOIN dbo.auxofc a ON a.ide = r.ofcide\n"
    "LEFT JOIN dbo.auxtrcp t ON t.ide = r.trcpide\n"
    "LEFT JOIN dbo.auxrcp k ON k.ide = r.rcpide\n"
    "LEFT JOIN dbo.con cl ON cl.ide = r.cliide\n"
    "LEFT JOIN dbo.per pr ON pr.ide = r.recide\n"
    "LEFT JOIN dbo.per pc ON pc.ide = r.cntide\n"
    "OUTER APPLY (SELECT TOP 1 x.valt FROM dbo.conext x\n"
    "             WHERE x.conide = c.ide AND x.cod = ? AND x.valt LIKE ?\n"
    "             ORDER BY x.ide) p\n"
    "WHERE c.tip = ? AND LTRIM(RTRIM(o.cod)) = ?\n"
    "ORDER BY c.cod"
)

#: R6: lo de trabajo, en el orden de §3.
COLUMNAS_R6 = (
    "v.obride", "c.cod", "e.cod", "c.fec", "u.cod", "a.cod", "a.res", "t.cod",
    "t.res", "r.resubi", "c.res", "p.valt",
)  # fmt: skip

#: R33: la lista cerrada, en el orden de §3.
COLUMNAS_R33 = (
    "CAST(r.tex AS nvarchar(max))", "r.motrcp", "r.texurg", "r.rcptip", "r.fecpre",
    "CAST(r.solrcp AS nvarchar(max))", "k.cod", "k.res",
    "CAST(r.tel AS nvarchar(max))", "CAST(r.ele AS nvarchar(max))",
    "cl.res", "pr.nom", "pr.tel", "pr.tel2", "pr.ele",
    "pc.nom", "pc.tel", "pc.tel2", "pc.ele",
)  # fmt: skip

#: Una fila completa, inventada, con un valor **distinto** en cada columna:
#: así un cambio de columna se ve.
FILA: list[Any] = [
    7001,                                # v.obride, entero como lo da la pasarela
    "RS26.09/0123",                      # c.cod
    "PTE",                               # e.cod
    20260915,                            # c.fec
    "9901.03VILLA 1.",                   # u.cod
    "0133",                              # a.cod
    "Ejemplo Fontaneria",                # a.res
    "GAR",                               # t.cod
    "Ejemplo Garantia",                  # t.res
    "Cocina",                            # r.resubi
    "Ejemplo gotera en la cocina",       # c.res
    REFERENCIA,                          # p.valt
    "Ejemplo descripcion larga",         # r.tex
    "Ejemplo motivo",                    # r.motrcp
    "Ejemplo urgente",                   # r.texurg
    2,                                   # r.rcptip
    20261001,                            # r.fecpre
    "Ejemplo solucion",                  # r.solrcp
    "CL1",                               # k.cod
    "Ejemplo clase",                     # k.res
    "000 000 000",                       # r.tel
    "avisos@ejemplo.invalid",            # r.ele
    "Ejemplo Propietario",               # cl.res
    "Ejemplo Reclamante",                # pr.nom
    "000 000 001",                       # pr.tel
    "000 000 002",                       # pr.tel2
    "reclama@ejemplo.invalid",           # pr.ele
    "Ejemplo Contacto",                  # pc.nom
    "000 000 003",                       # pc.tel
    "000 000 004",                       # pc.tel2
    "contacto@ejemplo.invalid",          # pc.ele
]  # fmt: skip

FICHA_ESPERADA = FichaReclamacion(
    descripcion_larga="Ejemplo descripcion larga",
    motivo="Ejemplo motivo",
    urgencia="Ejemplo urgente",
    forma_comunicacion=2,
    fecha_prevista=date(2026, 10, 1),
    solucion="Ejemplo solucion",
    clase_codigo="CL1",
    clase_nombre="Ejemplo clase",
    telefonos_avisos="000 000 000",
    correo_avisos="avisos@ejemplo.invalid",
    propietario="Ejemplo Propietario",
    reclama_nombre="Ejemplo Reclamante",
    reclama_telefono="000 000 001",
    reclama_telefono2="000 000 002",
    reclama_correo="reclama@ejemplo.invalid",
    contacto_nombre="Ejemplo Contacto",
    contacto_telefono="000 000 003",
    contacto_telefono2="000 000 004",
    contacto_correo="contacto@ejemplo.invalid",
)

FILA_ESPERADA = FilaReclamacionObra(
    obra_ref="7001",
    cod="RS26.09/0123",
    estado_codigo="PTE",
    fecha=date(2026, 9, 15),
    unidad_codigo="9901.03VILLA 1.",
    oficio_codigo="0133",
    oficio_nombre="Ejemplo Fontaneria",
    tipo_codigo="GAR",
    tipo_nombre="Ejemplo Garantia",
    ubicacion="Cocina",
    descripcion="Ejemplo gotera en la cocina",
    referencia=REFERENCIA,
    ficha=FICHA_ESPERADA,
)

#: Las posiciones de §3 que importan aquí.
I_OBRIDE, I_COD, I_ESTADO, I_FEC, I_UNIDAD, I_OFICIO, I_OFICIO_NOMBRE = 0, 1, 2, 3, 4, 5, 6
I_TIPO, I_TIPO_NOMBRE, I_UBICACION, I_DESCRIPCION, I_REFERENCIA = 7, 8, 9, 10, 11
I_TEX, I_RCPTIP, I_FECPRE, I_CLASE = 12, 15, 16, 18

#: Los valores de la fila que son texto: ninguno puede salir en un mensaje.
TEXTOS_DE_LA_FILA = [v for v in FILA if isinstance(v, str)]


def _con(**cambios: Any) -> list[Any]:
    """La fila completa con algunas columnas cambiadas, por posición `iN`."""
    fila = list(FILA)
    for nombre, valor in cambios.items():
        fila[int(nombre[1:])] = valor
    return fila


# ==========================================================================
# R5, R6, R29 · la consulta, carácter a carácter
# ==========================================================================


def test_f065_r6_la_consulta_caracter_a_caracter() -> None:
    assert SQL_RECLAMACIONES_DE_LA_OBRA == SQL_DE_DESIGN


def _consulta_de_design() -> str:
    """El bloque `sql` de §3 de `design.md`, tal cual."""
    lineas = DESIGN.read_text(encoding="utf-8").splitlines()
    inicio = lineas.index("## 3 · La consulta (`SQL_RECLAMACIONES_DE_LA_OBRA`)")
    apertura = lineas.index("```sql", inicio)
    cierre = lineas.index("```", apertura + 1)
    return "\n".join(lineas[apertura + 1 : cierre])


def test_f065_r6_la_consulta_es_la_de_design_3() -> None:
    """El código y la spec dicen lo mismo: si uno cambia, este test lo cuenta."""
    assert _consulta_de_design().startswith("SELECT v.obride")
    assert SQL_RECLAMACIONES_DE_LA_OBRA == _consulta_de_design()


def _consulta_del_script() -> str:
    """El here-string `$SQL_RECLAMACIONES_DE_LA_OBRA` del script 29, en LF.

    El fichero es CRLF; el script lo pasa a LF antes de mandarlo
    (`ConvertTo-SqlConLf`, fijado en `test_f065_scripts_infra.py`), así que lo
    que llega a la pasarela es este texto con saltos `\\n`.
    """
    texto = SCRIPT.read_bytes().decode("ascii").replace("\r\n", "\n")
    encontradas = re.findall(
        r"^\$SQL_RECLAMACIONES_DE_LA_OBRA = @'\n(.*?)\n'@", texto, flags=re.DOTALL | re.MULTILINE
    )
    assert len(encontradas) == 1, "el script 29 no tiene un único $SQL_RECLAMACIONES_DE_LA_OBRA"
    return encontradas[0]


def test_f065_r29_la_consulta_es_identica_a_la_del_script_29() -> None:
    """R29: el script mide **la misma** consulta que lee el adaptador."""
    assert SQL_RECLAMACIONES_DE_LA_OBRA == _consulta_del_script()


def test_f065_r5_el_filtro_de_obra_es_el_de_las_unidades_de_f036() -> None:
    """El código de obra, literal y recortado, como `SQL_UNIDADES_DE_LA_OBRA`."""
    assert "WHERE LTRIM(RTRIM(o.cod)) = ?" in SQL_UNIDADES_DE_LA_OBRA.splitlines()
    assert SQL_RECLAMACIONES_DE_LA_OBRA.splitlines()[-2] == "WHERE c.tip = ? AND LTRIM(RTRIM(o.cod)) = ?"
    assert "JOIN dbo.con o ON o.ide = v.obride" in SQL_RECLAMACIONES_DE_LA_OBRA.splitlines()


def test_f065_r5_todos_los_estados_y_todas_las_fechas_y_el_estado_por_codigo() -> None:
    """Q-2: sin filtro de estado ni de fecha; el estado se lee por `conest.cod` (C3)."""
    donde = SQL_RECLAMACIONES_DE_LA_OBRA.split("WHERE c.tip")[1]
    assert "est" not in donde
    assert "fec" not in donde
    assert "LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est" in SQL_RECLAMACIONES_DE_LA_OBRA


@pytest.mark.parametrize("codigo", ["9901", "0677", "9901' OR 1=1 --"])
def test_f065_r5_los_parametros_en_el_orden_de_los_marcadores(codigo: str) -> None:
    """`RCPCLI`, `PVI-%`, el tipo y la obra (§3); ningún valor en el texto."""
    sql, parametros = select_reclamaciones_de_la_obra(codigo_obra=codigo, tip=TIP)

    assert sql == SQL_RECLAMACIONES_DE_LA_OBRA
    assert parametros == ("RCPCLI", "PVI-%", TIP, codigo)
    assert sql.count("?") == len(parametros) == 4
    assert codigo not in sql


def test_f065_r5_el_tipo_viaja_como_lo_pide_quien_llama() -> None:
    _, parametros = select_reclamaciones_de_la_obra(codigo_obra=OBRA, tip=709)

    assert parametros[2] == 709


def test_f065_r5_la_referencia_es_la_de_f059() -> None:
    """El campo de `conext` y el prefijo `PVI-` del volcado (R10, F-059)."""
    assert CAMPO_REFERENCIA == "RCPCLI"
    assert PATRON_REFERENCIA == f"{PREFIJO_REFERENCIA}%" == "PVI-%"


def test_f065_r5_ningun_literal_en_el_texto() -> None:
    """Todo valor por `?`: ni comillas, ni el tipo, ni el campo, ni el patrón."""
    for prohibido in ("'", '"', "708", "RCPCLI", "PVI", "%"):
        assert prohibido not in SQL_RECLAMACIONES_DE_LA_OBRA


def _columnas_del_select() -> list[str]:
    """Las expresiones entre `SELECT` y `FROM`, separadas por comas."""
    lista = SQL_RECLAMACIONES_DE_LA_OBRA.split("SELECT ", 1)[1].split("\nFROM dbo.rcp r", 1)[0]
    return [columna.strip() for columna in lista.split(",")]


def test_f065_r6_r33_las_treinta_y_una_columnas_son_las_de_r6_y_la_lista_cerrada_de_r33() -> None:
    assert COLUMNAS_RECLAMACION == 31
    assert tuple(_columnas_del_select()) == COLUMNAS_R6 + COLUMNAS_R33


def test_f065_r6_los_textos_ilimitados_van_enteros() -> None:
    """`tex`, `solrcp`, `tel` y `ele` son `text` en Sigrid: con `CAST` (§6.6 de la pasarela)."""
    for campo in ("tex", "solrcp", "tel", "ele"):
        assert f"CAST(r.{campo} AS nvarchar(max))" in _columnas_del_select()


@pytest.mark.parametrize(
    "vetado",
    [r"\bdni\b", r"\besiglog\b", r"\besigpas\b", r"\bclamai\b", r"\bdir\b", r"\bdir1\b", r"\bdir2\b",
     r"\bp[rc]\.tex\b", r"\bdir\w*"],
)  # fmt: skip
def test_f065_r33_la_consulta_no_nombra_nada_vetado(vetado: str) -> None:
    """Ni el DNI, ni las credenciales de i-Sigrid, ni direcciones, ni `per.tex`."""
    assert re.search(vetado, SQL_RECLAMACIONES_DE_LA_OBRA) is None


def test_f065_r33_ningun_ide_sale_salvo_la_obra_de_la_unidad() -> None:
    """R33: «ni ningún `ide`». `upv.obride` se lee para contar obras (R9) y no sale."""
    con_ide = [c for c in _columnas_del_select() if c.endswith("ide") or ".ide" in c]
    assert con_ide == ["v.obride"]


def test_f065_r33_el_detector_de_vetados_no_es_ciego() -> None:
    """Control: el mismo detector sí ve un campo vetado metido en la consulta."""
    sucia = SQL_RECLAMACIONES_DE_LA_OBRA.replace("pr.ele,", "pr.ele, pr.dni, pr.tex, pr.dir1,")
    for vetado in (r"\bdni\b", r"\bp[rc]\.tex\b", r"\bdir1\b"):
        assert re.search(vetado, sucia) is not None


# ==========================================================================
# R6, R33 · el mapeo de cada fila
# ==========================================================================


def test_f065_r6_r33_una_fila_completa_al_puerto() -> None:
    assert fila_a_reclamacion_obra(FILA) == FILA_ESPERADA


def test_f065_r6_una_tupla_vale_como_una_lista() -> None:
    assert fila_a_reclamacion_obra(tuple(FILA)) == FILA_ESPERADA


def test_f065_r6_r33_los_campos_del_puerto_son_los_de_design() -> None:
    """`design.md` §10.2: los nombres y el orden, también de la ficha."""
    assert [f.name for f in fields(FilaReclamacionObra)] == [
        "obra_ref", "cod", "estado_codigo", "fecha", "unidad_codigo", "oficio_codigo",
        "oficio_nombre", "tipo_codigo", "tipo_nombre", "ubicacion", "descripcion",
        "referencia", "ficha",
    ]  # fmt: skip
    assert [f.name for f in fields(FichaReclamacion)] == [
        "descripcion_larga", "motivo", "urgencia", "forma_comunicacion", "fecha_prevista",
        "solucion", "clase_codigo", "clase_nombre", "telefonos_avisos", "correo_avisos",
        "propietario", "reclama_nombre", "reclama_telefono", "reclama_telefono2",
        "reclama_correo", "contacto_nombre", "contacto_telefono", "contacto_telefono2",
        "contacto_correo",
    ]  # fmt: skip


def test_f065_r6_r33_todo_lo_opcional_puede_venir_nulo() -> None:
    """Con los `LEFT JOIN` y el `OUTER APPLY`, todo salvo `obride` y `cod` puede ser `NULL`."""
    fila = [7001, "RS26.09/0123", *([None] * 29)]

    mapeada = fila_a_reclamacion_obra(fila)

    assert mapeada == FilaReclamacionObra(
        "7001", "RS26.09/0123", None, None, None, None, None, None, None, None, None, None,
        FichaReclamacion(*([None] * 19)),
    )  # fmt: skip


def test_f065_r6_los_textos_y_los_codigos_que_no_son_texto_pasan_a_texto() -> None:
    """Como el catálogo de F-036: lo que no es `None` se pasa a `str`."""
    fila = _con(i4=990103, i5=133, i7=7, i18=1)

    mapeada = fila_a_reclamacion_obra(fila)

    assert (mapeada.unidad_codigo, mapeada.oficio_codigo, mapeada.tipo_codigo) == ("990103", "133", "7")
    assert mapeada.ficha.clase_codigo == "1"


@pytest.mark.parametrize("obride", [None, "", "   "], ids=["nula", "vacia", "blancos"])
def test_f065_r9_obra_ref_es_obligatoria(obride: Any) -> None:
    """Dos filas sin obra contarían como una sola obra y esconderían la segunda (R9)."""
    with pytest.raises(ValueError) as fallo:
        fila_a_reclamacion_obra(_con(i0=obride))

    assert str(fallo.value) == "una reclamación sin referencia de obra"


@pytest.mark.parametrize("cod", [None, "", "   "], ids=["nulo", "vacio", "blancos"])
def test_f065_r6_el_codigo_es_obligatorio_y_sin_la_fila(cod: Any) -> None:
    """El `cod` de solo blancos es error, no una reclamación sin código (§10.2)."""
    with pytest.raises(ValueError) as fallo:
        fila_a_reclamacion_obra(_con(i1=cod))

    assert str(fallo.value) == "una reclamación sin código"


# --- las fechas: YYYYMMDD, 0 es nulo -------------------------------------


@pytest.mark.parametrize(
    ("valor", "esperada"),
    [
        (20260915, date(2026, 9, 15)),
        (20240229, date(2024, 2, 29)),
        (19991231, date(1999, 12, 31)),
        (10101, date(1, 1, 1)),
        (99991231, date(9999, 12, 31)),
        (0, None),
        (None, None),
    ],
    ids=["normal", "bisiesto", "fin-de-siglo", "la-primera", "la-ultima", "cero", "nula"],
)
def test_f065_r6_r33_las_fechas_yyyymmdd_y_el_cero_es_nulo(valor: Any, esperada: date | None) -> None:
    """`con.fec` y `rcp.fecpre`: enteros `YYYYMMDD`; `0` significa `NULL` (§6.6 de la pasarela)."""
    mapeada = fila_a_reclamacion_obra(_con(i3=valor, i16=valor))

    assert mapeada.fecha == esperada
    assert mapeada.ficha.fecha_prevista == esperada


IMPOSIBLES = [20261301, 20260230, 20230229, 20260900, 20260015, 1231, 100000101, -20260915]
NO_ENTEROS = ["20260915", 20260915.0, True, False, [20260915]]


@pytest.mark.parametrize("columna", [I_FEC, I_FECPRE], ids=["con.fec", "rcp.fecpre"])
@pytest.mark.parametrize("valor", IMPOSIBLES + NO_ENTEROS)
def test_f065_r40_una_fecha_imposible_es_error_sin_la_fila(columna: int, valor: Any) -> None:
    """Ni el valor ni ningún texto de la fila en el mensaje, ni en el de su causa."""
    with pytest.raises(ValueError) as fallo:
        fila_a_reclamacion_obra(_con(**{f"i{columna}": valor}))

    assert str(fallo.value) == "una fecha de Sigrid que no es un entero YYYYMMDD válido"
    assert fallo.value.__cause__ is None
    # Ni la causa ni el contexto: el error de `date` no viaja con él.
    assert fallo.value.__context__ is None or fallo.value.__suppress_context__
    for texto in [str(valor), *TEXTOS_DE_LA_FILA]:
        assert texto not in str(fallo.value)


# --- la forma de comunicación: un entero, tal cual -------------------------


@pytest.mark.parametrize("valor", [0, 1, 2, 7, None])
def test_f065_r33_la_forma_de_comunicacion_es_un_entero_tal_cual(valor: int | None) -> None:
    """`rcp.rcptip` es un entero de Sigrid (un código), no una fecha: el `0` se queda."""
    assert fila_a_reclamacion_obra(_con(i15=valor)).ficha.forma_comunicacion == valor


@pytest.mark.parametrize("valor", ["2", 2.0, True, [2]])
def test_f065_r40_una_forma_de_comunicacion_que_no_es_entero_es_error_sin_la_fila(valor: Any) -> None:
    with pytest.raises(ValueError) as fallo:
        fila_a_reclamacion_obra(_con(i15=valor))

    assert str(fallo.value) == "una forma de comunicación de Sigrid que no es un entero"


# --- la forma de la fila ----------------------------------------------------


@pytest.mark.parametrize(
    "fila",
    [None, "x" * 31, FILA[:30], [*FILA, None], {"cod": "RS26.09/0123"}, [], 31],
    ids=["nula", "texto-de-31", "treinta", "treinta-y-dos", "objeto", "vacia", "entero"],
)
def test_f065_r40_una_fila_mal_formada_es_un_error_que_no_la_repite(fila: Any) -> None:
    with pytest.raises(ValueError) as fallo:
        fila_a_reclamacion_obra(fila)

    assert str(fallo.value) == "una fila de Sigrid sin las 31 columnas esperadas"


# ==========================================================================
# §10.2 · el recorte de los códigos (enmienda del 2026-10-28)
# ==========================================================================


@pytest.mark.parametrize(
    ("estado", "esperado"),
    [("SAT     ", "SAT"), (" PTE", "PTE"), ("  NPR  ", "NPR"), ("CER", "CER"),
     ("        ", None), ("", None), (None, None)],
    ids=["relleno", "blanco-delante", "los-dos-lados", "limpio", "solo-blancos", "vacio", "nulo"],
)  # fmt: skip
def test_f065_r17_el_estado_se_recorta_y_el_vacio_es_nulo(estado: str | None, esperado: str | None) -> None:
    """El dominio compara el estado tal cual con los cinco códigos (R17): rellenado
    con blancos, todas serían «desconocidas» y el cruce daría cero pares sin error."""
    assert fila_a_reclamacion_obra(_con(i2=estado)).estado_codigo == esperado


@pytest.mark.parametrize(
    ("cod", "esperado"),
    [("RS26.09/0123  ", "RS26.09/0123"), ("  RS26.09/0123", "RS26.09/0123"),
     (" RS26.09/0123 ", "RS26.09/0123"), ("RS26.09/0123", "RS26.09/0123")],
    ids=["relleno", "blanco-delante", "los-dos-lados", "limpio"],
)  # fmt: skip
def test_f065_r12_el_codigo_se_recorta(cod: str, esperado: str) -> None:
    """El `cod` se compara con el `sigrid_cod` guardado por F-059, sin blancos (R12)."""
    assert fila_a_reclamacion_obra(_con(i1=cod)).cod == esperado


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [("GAR     ", "GAR"), (" GAR", "GAR"), ("    ", None), ("", None), (None, None)],
    ids=["relleno", "blanco-delante", "solo-blancos", "vacio", "nulo"],
)
def test_f065_r6_el_tipo_y_la_clase_se_recortan_y_el_vacio_es_nulo(valor: str | None, esperado: str | None) -> None:
    mapeada = fila_a_reclamacion_obra(_con(i7=valor, i18=valor))

    assert mapeada.tipo_codigo == esperado
    assert mapeada.ficha.clase_codigo == esperado


@pytest.mark.parametrize(
    "valor",
    ["9901.03VILLA 1.  ", "  9901.03VILLA 1.", "0133    ", " 0133", "    ", ""],
    ids=["relleno", "blanco-delante", "oficio-relleno", "oficio-blanco-delante", "solo-blancos", "vacio"],
)
def test_f065_r14_la_unidad_y_el_oficio_van_tal_cual_como_el_catalogo_de_f036(valor: str) -> None:
    """Decisión del líder del 2026-10-28, opción (a): R14 los compara por código
    exacto con los de la bandeja, que vienen del catálogo de F-036 leídos **tal
    cual** de las mismas columnas. Recortarlos solo aquí rompería el cruce."""
    mapeada = fila_a_reclamacion_obra(_con(i4=valor, i5=valor))

    assert mapeada.unidad_codigo == valor
    assert mapeada.oficio_codigo == valor


def test_f065_r14_los_nombres_y_los_textos_van_tal_cual() -> None:
    """Solo se recortan los cuatro códigos de §10.2: lo demás, como llega."""
    fila = _con(
        i6="  Ejemplo Fontaneria ", i8=" Ejemplo Garantia  ", i9=" Cocina ",
        i10="  Ejemplo gotera  ", i11=f"{REFERENCIA}  ", i12=" Ejemplo larga ",
        i19=" Ejemplo clase ", i22=" Ejemplo Propietario ", i23="   ",
    )  # fmt: skip

    mapeada = fila_a_reclamacion_obra(fila)

    assert (mapeada.oficio_nombre, mapeada.tipo_nombre, mapeada.ubicacion) == (
        "  Ejemplo Fontaneria ", " Ejemplo Garantia  ", " Cocina ",
    )  # fmt: skip
    assert (mapeada.descripcion, mapeada.referencia) == ("  Ejemplo gotera  ", f"{REFERENCIA}  ")
    assert mapeada.ficha.descripcion_larga == " Ejemplo larga "
    assert mapeada.ficha.clase_nombre == " Ejemplo clase "
    assert mapeada.ficha.propietario == " Ejemplo Propietario "
    assert mapeada.ficha.reclama_nombre == "   "


def test_f065_r9_obra_ref_va_tal_cual() -> None:
    """Como `FilaUnidadCatalogo`: opaca, sin recortar; solo se cuentan distintas."""
    assert fila_a_reclamacion_obra(_con(i0=" 7001 ")).obra_ref == " 7001 "


# ==========================================================================
# R40 · las filas del puerto no enseñan sus valores
# ==========================================================================


def test_f065_r40_la_fila_y_la_ficha_no_imprimen_ningun_valor_en_su_repr() -> None:
    fila = fila_a_reclamacion_obra(FILA)

    for texto in (repr(fila), repr(fila.ficha), str(fila), str(fila.ficha)):
        for valor in [*TEXTOS_DE_LA_FILA, "7001", "2026", "000 000"]:
            assert valor not in texto, (valor, texto)
    assert repr(fila) == "FilaReclamacionObra()"
    assert repr(fila.ficha) == "FichaReclamacion()"


def test_f065_r40_las_filas_son_inmutables() -> None:
    fila = fila_a_reclamacion_obra(FILA)

    with pytest.raises(FrozenInstanceError):
        fila.cod = "RS26.09/0124"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        fila.ficha.propietario = None  # type: ignore[misc]


# ==========================================================================
# R44, R70 · la consulta de la guarda del ensayo (Bloque A4 bis, T15)
# ==========================================================================

#: `design.md` §15.5 con **una** unidad: las 12 columnas de R6, sin R33.
SQL_DE_UNA_UNIDAD = (
    "SELECT v.obride, c.cod, e.cod, c.fec, u.cod, a.cod, a.res, t.cod, t.res, r.resubi, c.res, p.valt\n"
    "FROM dbo.rcp r\n"
    "JOIN dbo.con c ON c.ide = r.ide\n"
    "JOIN dbo.upv v ON v.ide = r.upvide\n"
    "JOIN dbo.con u ON u.ide = v.ide\n"
    "JOIN dbo.con o ON o.ide = v.obride\n"
    "LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est\n"
    "LEFT JOIN dbo.auxofc a ON a.ide = r.ofcide\n"
    "LEFT JOIN dbo.auxtrcp t ON t.ide = r.trcpide\n"
    "OUTER APPLY (SELECT TOP 1 x.valt FROM dbo.conext x\n"
    "             WHERE x.conide = c.ide AND x.cod = ? AND x.valt LIKE ?\n"
    "             ORDER BY x.ide) p\n"
    "WHERE c.tip = ? AND LTRIM(RTRIM(o.cod)) = ? AND u.cod IN (?)\n"
    "ORDER BY c.cod"
)

#: Las unidades de los ejemplos, con los blancos que trae el catálogo (tal cual).
UNIDADES = ("9901.03VILLA 1.", "9901.03VILLA 2.  ", "9901.03VILLA 3.", "9901.03VILLA 4.", "9901.03VILLA 5.")


def _con_marcadores(n: int) -> str:
    """El texto de §15.5 con `n` marcadores en el `IN`, separados por coma y espacio."""
    return SQL_DE_UNA_UNIDAD.replace("IN (?)", "IN (" + ", ".join(["?"] * n) + ")")


def test_f065_r44_la_consulta_de_una_unidad_caracter_a_caracter() -> None:
    sql, _ = select_reclamaciones_de_las_unidades(codigo_obra=OBRA, tip=TIP, unidades=UNIDADES[:1])

    assert sql == SQL_DE_UNA_UNIDAD


def test_f065_r44_la_de_cinco_unidades_caracter_a_caracter() -> None:
    sql, _ = select_reclamaciones_de_las_unidades(codigo_obra=OBRA, tip=TIP, unidades=UNIDADES)

    assert sql.splitlines()[-2] == "WHERE c.tip = ? AND LTRIM(RTRIM(o.cod)) = ? AND u.cod IN (?, ?, ?, ?, ?)"
    assert sql == _con_marcadores(5)


@pytest.mark.parametrize("n", [1, 2, 5, 49, 50])
def test_f065_r44_de_uno_a_n_marcadores_uno_por_unidad(n: int) -> None:
    unidades = tuple(f"9901.03VILLA {i}." for i in range(n))

    sql, parametros = select_reclamaciones_de_las_unidades(codigo_obra=OBRA, tip=TIP, unidades=unidades)

    assert sql == _con_marcadores(n)
    assert parametros == ("RCPCLI", "PVI-%", TIP, OBRA, *unidades)
    assert sql.count("?") == len(parametros) == 4 + n


def test_f065_r44_la_plantilla_es_la_consulta_con_el_hueco_de_los_marcadores() -> None:
    """La plantilla que comparte con el script 29: el `IN` con `__MARCADORES__`."""
    assert MARCADORES == "__MARCADORES__"
    assert SQL_RECLAMACIONES_DE_LAS_UNIDADES == SQL_DE_UNA_UNIDAD.replace("IN (?)", f"IN ({MARCADORES})")


def _consulta_de_la_guarda_en_design() -> str:
    """El bloque `sql` de §15.5, sin su comentario y con `?, …, ?` como hueco."""
    lineas = DESIGN.read_text(encoding="utf-8").splitlines()
    inicio = lineas.index("### 15.5 · Qué lee el ensayo, y su coste (S-5)")
    apertura = lineas.index("```sql", inicio)
    cierre = lineas.index("```", apertura + 1)
    sin_comentario = [linea for linea in lineas[apertura + 1 : cierre] if not linea.startswith("--")]
    return "\n".join(sin_comentario).replace("(?, …, ?)", f"({MARCADORES})")


def test_f065_r44_la_consulta_es_la_de_design_15_5() -> None:
    """El código y la spec dicen lo mismo: si uno cambia, este test lo cuenta."""
    assert _consulta_de_la_guarda_en_design().startswith("SELECT v.obride")
    assert SQL_RECLAMACIONES_DE_LAS_UNIDADES == _consulta_de_la_guarda_en_design()


def _plantilla_del_script() -> str:
    """El here-string `$SQL_RECLAMACIONES_DE_LAS_UNIDADES` del script 29, en LF."""
    texto = SCRIPT.read_bytes().decode("ascii").replace("\r\n", "\n")
    encontradas = re.findall(
        r"^\$SQL_RECLAMACIONES_DE_LAS_UNIDADES = @'\n(.*?)\n'@", texto, flags=re.DOTALL | re.MULTILINE
    )
    assert len(encontradas) == 1, "el script 29 no tiene un único $SQL_RECLAMACIONES_DE_LAS_UNIDADES"
    return encontradas[0]


def test_f065_r70_la_plantilla_es_identica_a_la_del_script_29() -> None:
    """R70: el script mide **la misma** consulta que lee la guarda."""
    assert SQL_RECLAMACIONES_DE_LAS_UNIDADES == _plantilla_del_script()


def test_f065_r44_las_doce_columnas_son_las_de_r6_sin_r33() -> None:
    lista = SQL_RECLAMACIONES_DE_LAS_UNIDADES.split("SELECT ", 1)[1].split("\nFROM dbo.rcp r", 1)[0]

    assert COLUMNAS_DE_LAS_UNIDADES == 12
    assert tuple(c.strip() for c in lista.split(",")) == COLUMNAS_R6


def test_f065_r44_mismas_uniones_que_la_obra_salvo_las_de_r33() -> None:
    """Las líneas de la guarda son las de la obra sin las de R33, y el `IN` al final."""
    obra = SQL_RECLAMACIONES_DE_LA_OBRA.splitlines()
    guarda = SQL_RECLAMACIONES_DE_LAS_UNIDADES.splitlines()
    de_r33 = ("dbo.auxrcp", "dbo.con cl", "dbo.per")
    desde = obra.index("FROM dbo.rcp r")

    assert guarda[1:-2] == [linea for linea in obra[desde:-2] if not any(r in linea for r in de_r33)]
    assert guarda[-2] == obra[-2] + f" AND u.cod IN ({MARCADORES})"
    assert guarda[-1] == obra[-1] == "ORDER BY c.cod"


@pytest.mark.parametrize(
    "vetado",
    [r"\bdni\b", r"\besiglog\b", r"\besigpas\b", r"\bclamai\b", r"\bdir\w*", r"\bper\b", r"\bauxrcp\b",
     r"\bcliide\b", r"\br\.tex\b", r"\br\.tel\b", r"\br\.ele\b", r"\bmotrcp\b", r"\bsolrcp\b",
     r"\btexurg\b", r"\brcptip\b", r"\bfecpre\b", r"\.nom\b"],
)  # fmt: skip
def test_f065_r44_la_guarda_no_lee_ni_un_dato_personal(vetado: str) -> None:
    """R44: sin los campos de R33 (ni ningún vetado de §8)."""
    assert re.search(vetado, SQL_RECLAMACIONES_DE_LAS_UNIDADES) is None


def test_f065_r44_el_detector_de_la_guarda_no_es_ciego() -> None:
    for vetado in (r"\bper\b", r"\bmotrcp\b", r"\.nom\b", r"\br\.tel\b"):
        assert re.search(vetado, SQL_RECLAMACIONES_DE_LA_OBRA) is not None


@pytest.mark.parametrize("codigo", ["9901' OR 1=1 --", "0677"])
def test_f065_r44_ningun_valor_en_el_texto(codigo: str) -> None:
    """Todo por `?`: ni la obra, ni las unidades, ni el campo, ni el patrón."""
    unidades = ("VILLA 15'; DROP TABLE dbo.rcp --", "Ejemplo Unidad")

    sql, parametros = select_reclamaciones_de_las_unidades(codigo_obra=codigo, tip=TIP, unidades=unidades)

    for prohibido in ("'", '"', "708", "RCPCLI", "PVI", "%", codigo, *unidades):
        assert prohibido not in sql
    assert parametros[3:] == (codigo, *unidades)


def test_f065_r44_las_unidades_van_tal_cual_y_en_el_orden_recibido() -> None:
    """Sin recortar (R14: `u.cod` se compara tal cual) ni reordenar: el orden lo pone la guarda."""
    _, parametros = select_reclamaciones_de_las_unidades(
        codigo_obra=OBRA, tip=TIP, unidades=("9901.03VILLA 2.  ", "  9901.03VILLA 1.")
    )

    assert parametros[4:] == ("9901.03VILLA 2.  ", "  9901.03VILLA 1.")


@pytest.mark.parametrize(
    "unidades", [(), tuple(f"U{i:02d}" for i in range(51))], ids=["ninguna", "cincuenta-y-una"]
)
def test_f065_r44_de_una_a_cincuenta_unidades_y_si_no_es_error_sin_valores(unidades: tuple[str, ...]) -> None:
    """Sin unidades no hay consulta que tenga sentido; con más de 50 no cabe en
    una llamada del ensayo (`N` ≤ 50). Error de programación, sin repetir nada."""
    assert MAX_UNIDADES == 50
    with pytest.raises(ValueError) as fallo:
        select_reclamaciones_de_las_unidades(codigo_obra=OBRA, tip=TIP, unidades=unidades)

    assert str(fallo.value) == "la lectura de la guarda lleva de 1 a 50 unidades"


def test_f065_r44_justo_cincuenta_unidades_si() -> None:
    sql, _ = select_reclamaciones_de_las_unidades(
        codigo_obra=OBRA, tip=TIP, unidades=tuple(f"U{i:02d}" for i in range(50))
    )

    assert sql.count("?") == 54


def test_f065_r44_unidades_repetidas_son_error_sin_repetirlas() -> None:
    with pytest.raises(ValueError) as fallo:
        select_reclamaciones_de_las_unidades(
            codigo_obra=OBRA, tip=TIP, unidades=("Ejemplo U1", "Ejemplo U2", "Ejemplo U1")
        )

    assert str(fallo.value) == "la lectura de la guarda lleva cada unidad una sola vez"


# --- el mapeo de la guarda: 12 columnas y sin ficha ------------------------


def test_f065_r44_una_fila_de_la_guarda_al_puerto_sin_ficha() -> None:
    """§15.2: `ficha` a `None` en la lectura de la guarda, que no lee R33."""
    assert fila_a_reclamacion_de_las_unidades(FILA[:12]) == replace(FILA_ESPERADA, ficha=None)
    assert fila_a_reclamacion_de_las_unidades(tuple(FILA[:12])) == replace(FILA_ESPERADA, ficha=None)


def test_f065_r44_la_guarda_hace_los_mismos_recortes_que_la_obra() -> None:
    fila = _con(i1=" RS26.09/0123 ", i2="PTE   ", i4="9901.03VILLA 1.  ", i5=" 0133", i7=" GAR ")[:12]

    mapeada = fila_a_reclamacion_de_las_unidades(fila)

    assert (mapeada.cod, mapeada.estado_codigo, mapeada.tipo_codigo) == ("RS26.09/0123", "PTE", "GAR")
    assert (mapeada.unidad_codigo, mapeada.oficio_codigo) == ("9901.03VILLA 1.  ", " 0133")
    assert mapeada.ficha is None


@pytest.mark.parametrize(
    ("cambio", "mensaje"),
    [
        ({"i0": None}, "una reclamación sin referencia de obra"),
        ({"i0": "  "}, "una reclamación sin referencia de obra"),
        ({"i1": "  "}, "una reclamación sin código"),
        ({"i3": 20261345}, "una fecha de Sigrid que no es un entero YYYYMMDD válido"),
    ],
    ids=["sin-obra", "obra-en-blanco", "sin-codigo", "fecha-imposible"],
)
def test_f065_r44_la_guarda_exige_obra_codigo_y_una_fecha_valida(cambio: dict[str, Any], mensaje: str) -> None:
    with pytest.raises(ValueError) as fallo:
        fila_a_reclamacion_de_las_unidades(_con(**cambio)[:12])

    assert str(fallo.value) == mensaje


@pytest.mark.parametrize(
    "fila",
    [None, "x" * 12, FILA[:11], FILA[:13], FILA, {"cod": "RS26.09/0123"}, [], 12],
    ids=["nula", "texto-de-12", "once", "trece", "treinta-y-una", "objeto", "vacia", "entero"],
)
def test_f065_r40_una_fila_de_la_guarda_mal_formada_no_se_repite(fila: Any) -> None:
    """Con 31 columnas también es error: la guarda nunca recibe la ficha."""
    with pytest.raises(ValueError) as fallo:
        fila_a_reclamacion_de_las_unidades(fila)

    assert str(fallo.value) == "una fila de Sigrid sin las 12 columnas esperadas"
    for texto in TEXTOS_DE_LA_FILA:
        assert texto not in str(fallo.value)


@pytest.mark.parametrize(
    ("cambio", "mensaje"),
    [
        ({"i0": None, "i16": 20261345}, "una reclamación sin referencia de obra"),
        ({"i0": "  ", "i15": "2"}, "una reclamación sin referencia de obra"),
        ({"i1": "  ", "i16": 20261345}, "una reclamación sin código"),
        ({"i1": None, "i15": "2"}, "una reclamación sin código"),
    ],
    ids=["sin-obra-y-fecpre", "obra-en-blanco-y-rcptip", "sin-codigo-y-fecpre", "codigo-nulo-y-rcptip"],
)
def test_f065_r40_la_obra_y_el_codigo_se_miran_antes_que_la_ficha(cambio: dict[str, Any], mensaje: str) -> None:
    """Con la ficha también mal, el error es el de la fila: la ficha va después."""
    with pytest.raises(ValueError) as fallo:
        fila_a_reclamacion_obra(_con(**cambio))

    assert str(fallo.value) == mensaje


def test_f065_r44_la_obra_sigue_dando_la_ficha_entera() -> None:
    """O-A4b-3 / L-7: la ficha admite `None` solo en la lectura de la guarda; la
    de la obra (la de la ruta) la sigue dando entera."""
    assert fila_a_reclamacion_obra(FILA).ficha == FICHA_ESPERADA
    assert FilaReclamacionObra("7001", "RS26.09/0123", *([None] * 11)).ficha is None
