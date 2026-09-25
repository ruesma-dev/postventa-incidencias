# services/postventa-api/tests/test_f013_destino_dominio.py
"""F-013 · el casado de las carpetas de Posventa: dominio puro (`design.md` §4).

Aquí se decide **en qué carpeta acaba un PDF con el DNI manuscrito de un
cliente**, y el fallo típico —el parte en la carpeta de otra villa u otra
obra— no se ve desde nuestro lado. Por eso las tablas de `design.md` entran
**enteras y como tablas**: una fila, un caso de `pytest.mark.parametrize`. Si
alguien cambia una regla, la fila que la contradice se pone roja con su nombre.

Sin red, sin Graph, sin Sigrid y sin configuración: nombres de carpeta y filas
del ERP entran como cadenas, y salen tuplas de cadenas.

**Los datos.** El árbol de la obra piloto es el **medido** en T2 y T3
(`progress/explore_F-013.md`, 2026-09-24): la carpeta `677  MIRASIERRA`, su
`PARTES INCIDENCIAS`, `VILLA 01` … `VILLA 07` con sus hojas, y las 15 unidades
de Sigrid. Ninguno lleva nombres de persona (T3 lo comprobó). El resto de
carpetas de la raíz y de la obra, que en la biblioteca real existen, aquí son
**inventadas** y neutras: lo único que importa de ellas es que no llevan el
número de la obra ni la palabra del tramo.
"""

from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest
from domain.models.destino_posventa import (
    PATRON_CODIGO_UNIDAD,
    EstructuraArchivo,
    MotivoDestino,
    UbicacionReclamacion,
    UnidadDeObra,
    carpeta_con_nombre,
    carpetas_de_obra,
    carpetas_de_unidad,
    clave_de_unidad,
    nombre_de_carpeta_admisible,
    nombre_de_obra_nueva,
    nombre_derivado_de_unidad,
    numero_de_obra,
    obras_del_mismo_numero,
    parecidas_de_obra,
    parecidas_de_tramo,
    parecidas_de_unidad,
    unidades_que_casan,
    unir_ruta,
)
from domain.models.errores import DestinoNoResuelto
from domain.models.nombrado import CARACTERES_PROHIBIDOS

MODULO = (
    Path(__file__).resolve().parents[1] / "domain" / "models" / "destino_posventa.py"
)

# --------------------------------------------------------------------------
# Los datos medidos (T2 y T3, 2026-09-24)
# --------------------------------------------------------------------------

#: El `con.res` de la obra 0677 en Sigrid [MEDIDO, `design.md` §1].
RES_OBRA_0677 = "15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)"

#: La carpeta real de la obra: sin el cero y con **dos** blancos [MEDIDO, T2].
CARPETA_OBRA_0677 = "677  MIRASIERRA"

#: La raíz de la biblioteca: la carpeta real de la obra y otras inventadas que
#: no llevan el 677 por ningún lado (T2: «ninguna otra carpeta de la raíz casa
#: ni se parece»).
RAIZ = (
    "0680 OTRA OBRA",
    "0712 PROMOCION NORTE",
    CARPETA_OBRA_0677,
    "ADMINISTRACION",
    "PLANTILLAS",
    "0590 RESIDENCIAL SUR",
)

#: Dentro de la obra: `PARTES INCIDENCIAS` y tres de trabajo interno (T2), con
#: nombres inventados que no llevan la palabra del tramo.
DENTRO_DE_LA_OBRA = ("DOCUMENTACION", "PARTES INCIDENCIAS", "PLANOS", "CORRESPONDENCIA")

#: Las siete unidades que tiene Posventa, siempre con dos cifras [MEDIDO, T2].
UNIDADES_EN_POSVENTA = tuple(f"VILLA {n:02d}" for n in range(1, 8))

#: Las hojas de cada unidad [MEDIDO, T2; el literal de VILLA 02, humano].
HOJAS_EN_POSVENTA = {
    "VILLA 01": ("PARTES FIRMADOS",),
    "VILLA 02": ("PARTES FIRMADO",),
    "VILLA 03": ("PARTES FIRMADOS",),
    "VILLA 04": (),  # sin subcarpetas: 142 ficheros sueltos que no se ven
    "VILLA 05": ("PARTES FIRMADOS",),
    "VILLA 06": ("PARTES FIRMADOS",),
    "VILLA 07": ("PARTES FIRMADOS",),
}

INCIDENCIAS = "PARTES INCIDENCIAS"
FIRMADOS = "PARTES FIRMADOS"
ALTERNATIVA = "PARTES FIRMADO"


def _ubicacion(cod: str | None, res: str | None, *, obra: str = "0677") -> UbicacionReclamacion:
    return UbicacionReclamacion(
        obra_codigo=obra,
        obra_nombre=RES_OBRA_0677,
        unidad_codigo=cod,
        unidad_nombre=res,
    )


#: Las 15 unidades de posventa de la 0677 en Sigrid [MEDIDO, T3].
FILAS_0677 = tuple(
    UnidadDeObra(
        obra_ref="obra-a",
        obra_codigo="0677",
        unidad_codigo=f"0677.03VILLA {n}.",
        unidad_nombre=f"Viviendas Bloque Villa {n}",
    )
    for n in range(1, 16)
)

# --------------------------------------------------------------------------
# La estrategia, los motivos y el error
# --------------------------------------------------------------------------


def test_f013_r1_las_estrategias_son_dos_y_solo_dos():
    """R1 · `por_obra` (F-006) y `posventa` (F-013). Escritas a mano."""
    assert {estructura.value for estructura in EstructuraArchivo} == {
        "por_obra",
        "posventa",
    }


#: Todos los motivos de «destino no resuelto» que nombra R18, enmendado el
#: 2026-09-24 (los de R7, R8, R13, R14, R16, R35, R38, R37, R44, R46 y R50).
MOTIVOS_DE_R18 = {
    # R7
    "reclamacion_no_localizada",
    "reclamacion_ambigua",
    "reclamacion_sin_unidad",
    # R8
    "obra_no_coincide",
    # R13 y R14
    "obra_ambigua",
    "incidencias_ambigua",
    "unidad_ambigua",
    "firmados_ambigua",
    # R35
    "obra_parecida",
    "incidencias_parecida",
    "unidad_parecida",
    "firmados_parecida",
    # R16
    "sin_carpeta_obra",
    "sin_carpeta_incidencias",
    "sin_carpeta_unidad",
    "sin_carpeta_firmados",
    # R38
    "nombre_carpeta_imposible",
    # R37, R44, R46 y R50 (2026-09-24)
    "unidad_sin_nombre_derivable",
    "obra_numero_no_unico",
    "unidades_sin_verificar",
    "nombre_no_casaria",
    "unidad_carpeta_compartida",
}


def test_f013_r18_los_motivos_son_exactamente_los_de_la_spec():
    """R18 · el motivo va a la traza **como código**: la lista es cerrada.

    Un motivo de más sería un 409 que nadie ha especificado; uno de menos, un
    caso que no se puede contar. Los códigos son texto (`StrEnum`) para que la
    traza y la respuesta los lleven tal cual.
    """
    assert {motivo.value for motivo in MotivoDestino} == MOTIVOS_DE_R18
    assert all(isinstance(motivo, str) for motivo in MotivoDestino)


def test_f013_r19_el_error_lleva_motivo_detalle_y_candidatas():
    """R19 · `motivo` (el código), un texto legible y los nombres de carpeta."""
    error = DestinoNoResuelto(
        motivo=MotivoDestino.OBRA_AMBIGUA,
        detalle="dos carpetas empiezan por el número de la obra",
        candidatas=["677  MIRASIERRA", "0677 MIRASIERRA FASE 2"],
    )

    assert isinstance(error, Exception)
    assert error.motivo == "obra_ambigua"
    assert error.detalle == "dos carpetas empiezan por el número de la obra"
    assert error.candidatas == ("677  MIRASIERRA", "0677 MIRASIERRA FASE 2")
    assert "obra_ambigua" in str(error)


def test_f013_r19_sin_candidatas_la_lista_va_vacia():
    """R19 · «lista vacía si no hay»."""
    error = DestinoNoResuelto(
        motivo=MotivoDestino.RECLAMACION_NO_LOCALIZADA, detalle="no está en Sigrid"
    )

    assert error.candidatas == ()


# --------------------------------------------------------------------------
# R9 · La unidad del papel no entra en el casado
# --------------------------------------------------------------------------


def test_f013_r9_la_ubicacion_solo_trae_lo_de_sigrid():
    """R9 · código y nombre de la obra y de la unidad, del ERP. Nada del papel."""
    assert [campo.name for campo in fields(UbicacionReclamacion)] == [
        "obra_codigo",
        "obra_nombre",
        "unidad_codigo",
        "unidad_nombre",
    ]


def test_f013_r9_el_modulo_no_conoce_la_extraccion():
    """R9 · el dominio del destino no puede leer lo que la IA leyó del parte.

    Se miran los **identificadores** del módulo (con `tokenize`, sin su prosa):
    ni `extraccion`, ni `ExtraccionParte`, ni el contexto del paso.
    """
    fuente = MODULO.read_text(encoding="utf-8")
    nombres = {
        token.string
        for token in tokenize.generate_tokens(io.StringIO(fuente).readline)
        if token.type == tokenize.NAME
    }

    assert not nombres & {"extraccion", "ExtraccionParte", "ContextoParte"}


def test_f013_el_modulo_es_dominio_puro():
    """`design.md` §2.1 · sin red, sin E/S y sin infraestructura.

    Solo biblioteca estándar y `nombrado.py` (de donde se **importan** los
    caracteres prohibidos y la normalización del código, `design.md` §4.6).
    """
    arbol = ast.parse(MODULO.read_text(encoding="utf-8"))
    importados = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados |= {alias.name for alias in nodo.names}
        elif isinstance(nodo, ast.ImportFrom):
            importados.add(nodo.module or "")

    assert importados <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "enum",
        "re",
        "unicodedata",
        "domain.models.nombrado",
    }


# --------------------------------------------------------------------------
# §4.1 · La carpeta de obra: casa por el NÚMERO (R10, enmendada el 2026-09-24)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("codigo", "numero"),
    (
        ("0677", 677),
        ("677", 677),
        ("00677", 677),
        ("0", 0),
        ("06 77", 677),  # un blanco no es parte del código (F-032)
        (" 0677 ", 677),
        ("0677-1", None),
        ("RS26", None),
        ("ADM", None),
        ("０６７７", None),  # cifras de ancho completo: no son cifras ASCII
        ("٦٧٧", None),  # cifras arábigo-índicas: tampoco
        ("", None),
        (None, None),
    ),
)
def test_f013_r10_numero_de_obra(codigo, numero):
    """R10 · el número de obra es el entero del código **solo de cifras 0-9**."""
    assert numero_de_obra(codigo) == numero


#: `design.md` §4.1 enmendada, fila a fila, más los blancos que la regla dice
#: de «cualquier clase y cantidad». (carpeta, casa, parecida) para la obra 0677.
TABLA_4_1 = (
    ("677  MIRASIERRA", True, False),  # la real
    ("0677 MIRASIERRA", True, False),
    ("677", True, False),
    ("00677 X", True, False),
    ("0677 15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)", True, False),
    ("06770 X", False, False),
    ("0677-MIRASIERRA", False, True),
    ("677MIRASIERRA", False, True),
    ("OBRA 0677", False, True),
    ("LISTADO 677", False, True),
    ("0680 OTRA", False, False),
    # Los blancos de cualquier clase y cantidad (R10).
    ("677 MIRASIERRA", True, False),
    ("677\tMIRASIERRA", True, False),
    (" 677 MIRASIERRA", True, False),
    # Cifras que no son ASCII: no casan; la amplia las ve.
    ("６７７ MIRASIERRA", False, True),
    ("OBRA0677", False, True),
)


@pytest.mark.parametrize(("carpeta", "casa", "parecida"), TABLA_4_1)
def test_f013_r10_tabla_4_1_casado_de_la_obra_por_numero(carpeta, casa, parecida):
    """R10 y R35 · la tabla de `design.md` §4.1 enmendada, entera."""
    assert carpetas_de_obra([carpeta], codigo_obra="0677") == (
        (carpeta,) if casa else ()
    )
    assert parecidas_de_obra([carpeta], codigo_obra="0677") == (
        (carpeta,) if parecida else ()
    )


@pytest.mark.parametrize("codigo", ("0677", "677", "00677"))
def test_f013_r10_da_igual_como_venga_escrito_el_codigo(codigo):
    """R10 · `0677`, `677` y `00677` son la misma obra (lo que se acepta, T4-4)."""
    assert carpetas_de_obra(RAIZ, codigo_obra=codigo) == (CARPETA_OBRA_0677,)
    assert parecidas_de_obra(RAIZ, codigo_obra=codigo) == ()


def test_f013_r10_se_usa_el_nombre_tal_y_como_existe():
    """R4 · el nombre de la carpeta sale sin recortar ni colapsar sus blancos."""
    (elegida,) = carpetas_de_obra(RAIZ, codigo_obra="0677")

    assert elegida == "677  MIRASIERRA"


@pytest.mark.parametrize(
    ("carpeta", "casa", "parecida"),
    (
        ("ADM", True, False),
        ("ADM GENERAL", True, False),
        (" ADM  GENERAL ", True, False),
        ("ADM GENERAL", True, False),
        ("ADMX", False, False),
        ("ADM.", False, True),
        ("ADM-GENERAL", False, True),
        ("adm general", False, True),  # la literal distingue mayúsculas
        ("OFICINA ADM", False, True),
        ("OTRA", False, False),
    ),
)
def test_f013_r10_codigo_no_numerico_regla_literal(carpeta, casa, parecida):
    """R10 · un código con letras no tiene número: literal, código + blanco.

    La parecida de estos códigos es la igualdad de palabra (§4.5), sin
    mayúsculas ni tildes: `adm general` y `ADM-GENERAL` paran la creación.
    """
    assert carpetas_de_obra([carpeta], codigo_obra="ADM") == (
        (carpeta,) if casa else ()
    )
    assert parecidas_de_obra([carpeta], codigo_obra="ADM") == (
        (carpeta,) if parecida else ()
    )


def test_f013_r10_sin_codigo_no_casa_ni_se_parece_nada():
    """Un código vacío no puede elegir carpeta: ni la de la raíz entera."""
    assert carpetas_de_obra(RAIZ + ("", "   "), codigo_obra="") == ()
    assert parecidas_de_obra(RAIZ, codigo_obra="") == ()
    assert carpetas_de_obra(RAIZ, codigo_obra=None) == ()


def test_f013_r13_dos_carpetas_con_el_mismo_numero_se_devuelven_las_dos():
    """R13 · `677  MIRASIERRA` y `0677 MIRASIERRA FASE 2` → las dos (ambigua).

    El dominio no elige por el resto del nombre ni por los ceros: devuelve las
    dos y el resolutor responde `obra_ambigua` con ellas.
    """
    raiz = RAIZ + ("0677 MIRASIERRA FASE 2",)

    assert carpetas_de_obra(raiz, codigo_obra="0677") == (
        CARPETA_OBRA_0677,
        "0677 MIRASIERRA FASE 2",
    )


# --------------------------------------------------------------------------
# §4.2 · Los tramos fijos y la hoja alternativa (R14, R49)
# --------------------------------------------------------------------------

#: `design.md` §4.2, fila a fila: (hojas en la unidad, alternativa, casan, parecidas).
TABLA_4_2 = (
    (("PARTES FIRMADOS",), ALTERNATIVA, ("PARTES FIRMADOS",), ()),
    (("PARTES FIRMADO",), ALTERNATIVA, ("PARTES FIRMADO",), ()),  # VILLA 02
    (("Partes Firmado",), ALTERNATIVA, ("Partes Firmado",), ()),
    (
        ("PARTES FIRMADOS", "PARTES FIRMADO"),
        ALTERNATIVA,
        ("PARTES FIRMADOS", "PARTES FIRMADO"),  # → firmados_ambigua
        (),
    ),
    (("PARTE FIRMADO",), ALTERNATIVA, (), ("PARTE FIRMADO",)),
    (("FIRMADOS 2024",), ALTERNATIVA, (), ("FIRMADOS 2024",)),
    ((), ALTERNATIVA, (), ()),  # VILLA 04: se crea PARTES FIRMADOS
    (("PARTES FIRMADO",), "", (), ("PARTES FIRMADO",)),  # alternativa vacía
    (("PARTES FIRMADO",), "   ", (), ("PARTES FIRMADO",)),
    # Mayúsculas, tildes y blancos (la clave de `design.md` §4.2).
    (("Partes  Fírmados",), ALTERNATIVA, ("Partes  Fírmados",), ()),
)


@pytest.mark.parametrize(("hojas", "alternativa", "casan", "parecidas"), TABLA_4_2)
def test_f013_r49_tabla_4_2_la_hoja_y_su_alternativa(hojas, alternativa, casan, parecidas):
    """R14 y R49 · la tabla de `design.md` §4.2 enmendada, entera."""
    assert (
        carpeta_con_nombre(hojas, buscado=FIRMADOS, alternativa=alternativa) == casan
    )
    assert (
        parecidas_de_tramo(hojas, buscado=FIRMADOS, alternativa=alternativa)
        == parecidas
    )


def test_f013_r49_la_alternativa_casa_con_su_nombre_tal_y_como_existe():
    """R49 · se archiva **en** `PARTES FIRMADO`, no en un `PARTES FIRMADOS` nuevo."""
    assert carpeta_con_nombre(
        HOJAS_EN_POSVENTA["VILLA 02"], buscado=FIRMADOS, alternativa=ALTERNATIVA
    ) == ("PARTES FIRMADO",)


def test_f013_r14_incidencias_no_tiene_alternativa_y_dos_que_casan_son_ambigua():
    """R14 · `PARTES INCIDENCIAS` y `Partes incidencias` → las dos."""
    assert carpeta_con_nombre(
        ("PARTES INCIDENCIAS", "Partes incidencias", "PLANOS"), buscado=INCIDENCIAS
    ) == ("PARTES INCIDENCIAS", "Partes incidencias")


def test_f013_r14_el_tramo_de_la_obra_medida_casa():
    """T2 · dentro de `677  MIRASIERRA`, `PARTES INCIDENCIAS` casa y nada se parece."""
    assert carpeta_con_nombre(DENTRO_DE_LA_OBRA, buscado=INCIDENCIAS) == (INCIDENCIAS,)
    assert parecidas_de_tramo(DENTRO_DE_LA_OBRA, buscado=INCIDENCIAS) == ()


def test_f013_r14_un_tramo_configurado_vacio_no_casa_con_nada():
    """Una variable de tramo en blanco no puede casar con cualquier carpeta."""
    assert carpeta_con_nombre(("---", "", "PLANOS"), buscado="") == ()
    assert parecidas_de_tramo(("---", "", "PLANOS"), buscado="") == ()


# --------------------------------------------------------------------------
# §4.3 · La carpeta de unidad (R11, D-6)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "clave"),
    (
        ("Viviendas Bloque Villa 5", ("VIVIENDAS", "BLOQUE", "VILLA", "5")),
        ("VILLA 05", ("VILLA", "5")),
        ("0677.03VILLA 5.", ("677", "03VILLA", "5")),  # medido: §4.3
        ("  Villa   05  ", ("VILLA", "5")),
        ("VILLA 05", ("VILLA", "5")),
        ("Villa_5", ("VILLA", "5")),
        ("Vivienda Núñez-3", ("VIVIENDA", "NUNEZ", "3")),
        ("Chalé 007", ("CHALE", "7")),
        ("00", ("0",)),
        (" - ", ()),
        ("", ()),
        (None, ()),
    ),
)
def test_f013_r11_clave_de_unidad(texto, clave):
    """R11 · sin tildes, mayúsculas, lo no alfanumérico separa y `05` = `5`."""
    assert clave_de_unidad(texto) == clave


UBICACION_VILLA_5 = _ubicacion("0677.03VILLA 5.", "Viviendas Bloque Villa 5")

#: `design.md` §4.3, fila a fila, para la unidad «Viviendas Bloque Villa 5».
TABLA_4_3 = (
    ("VILLA 05", True),
    ("Villa 5", True),
    ("VILLA 15", False),
    ("VILLA 05 - GARCÍA", False),  # nunca se «acerca»
    ("05", True),
    ("BLOQUE A", False),
    ("VILLA", False),  # sin número no casa con todas
    ("VILLA 51", False),
    ("VILLA 5.", True),
    ("VILLA5", False),  # un solo token: no es sufijo
)


@pytest.mark.parametrize(("carpeta", "casa"), TABLA_4_3)
def test_f013_r11_tabla_4_3_casado_de_la_unidad(carpeta, casa):
    """R11 · la tabla de `design.md` §4.3, entera."""
    assert carpetas_de_unidad([carpeta], ubicacion=UBICACION_VILLA_5) == (
        (carpeta,) if casa else ()
    )


def test_f013_r11_villa_5_no_casa_con_villa_51():
    """R11 · el sufijo evita el falso positivo de «contiene»."""
    villa_51 = _ubicacion("0677.03VILLA 51.", "Viviendas Bloque Villa 51")

    assert carpetas_de_unidad(["VILLA 5", "VILLA 05"], ubicacion=villa_51) == ()


def test_f013_r11_la_regla_1_casa_por_el_codigo():
    """R11 · regla 1: la clave de la carpeta es la del `con.cod`.

    Con los datos reales no casa nunca (§4.3, medido), y se deja: cubre un ERP
    que algún día guarde la forma corta.
    """
    corta = UbicacionReclamacion(
        obra_codigo="0677", obra_nombre=None, unidad_codigo="VILLA 05", unidad_nombre=None
    )

    assert carpetas_de_unidad(["Villa 5", "VILLA 06"], ubicacion=corta) == ("Villa 5",)


def test_f013_r11_sin_numero_no_casa_aunque_sea_sufijo_del_nombre():
    """R11 · la exigencia del número vale también para las dos reglas.

    `VILLA A` es sufijo de «Viviendas Bloque Villa A» y `LOCAL` es el código
    entero de la unidad, y ninguno casa: una carpeta sin número no identifica
    una unidad (añadido tras la mutación del bloque 1, superviviente 8).
    """
    sin_numeros = UbicacionReclamacion(
        obra_codigo="0677",
        obra_nombre=None,
        unidad_codigo="LOCAL",
        unidad_nombre="Viviendas Bloque Villa A",
    )

    assert carpetas_de_unidad(["VILLA A", "LOCAL", "Villa A"], ubicacion=sin_numeros) == ()


def test_f013_r11_la_carpeta_con_el_nombre_entero_de_la_unidad_casa():
    """R11 y R39 · el sufijo trivial: la clave de la carpeta **es** la del nombre.

    Añadido tras la mutación del bloque 1 (superviviente 9): ningún caso de
    la tabla tenía la misma longitud que la clave del `con.res`.
    """
    assert carpetas_de_unidad(
        ["Viviendas Bloque Villa 5", "VIVIENDAS BLOQUE VILLA 05"],
        ubicacion=UBICACION_VILLA_5,
    ) == ("Viviendas Bloque Villa 5", "VIVIENDAS BLOQUE VILLA 05")


def test_f013_r11_una_carpeta_mas_larga_que_el_nombre_no_casa():
    """R11 · más palabras que el nombre no puede ser su sufijo."""
    assert (
        carpetas_de_unidad(["OTRAS Viviendas Bloque Villa 5"], ubicacion=UBICACION_VILLA_5)
        == ()
    )


def test_f013_r14_dos_carpetas_de_la_misma_unidad_se_devuelven_las_dos():
    """R14 · `VILLA 05` y `05` casan las dos → `unidad_ambigua`."""
    assert carpetas_de_unidad(
        ["VILLA 05", "05", "VILLA 06"], ubicacion=UBICACION_VILLA_5
    ) == ("VILLA 05", "05")


def test_f013_r11_sin_datos_de_la_unidad_no_casa_nada():
    """Una ubicación sin unidad no puede casar con ninguna carpeta."""
    vacia = UbicacionReclamacion(
        obra_codigo="0677", obra_nombre=None, unidad_codigo=None, unidad_nombre=None
    )

    assert carpetas_de_unidad(UNIDADES_EN_POSVENTA, ubicacion=vacia) == ()
    assert parecidas_de_unidad(UNIDADES_EN_POSVENTA, ubicacion=vacia) == ()


# --------------------------------------------------------------------------
# §4.5 · Parecidas: cuándo se crea y cuándo no (R34, R35)
# --------------------------------------------------------------------------


def test_f013_r35_0677_guion_mirasierra_impide_crear_la_obra():
    """R35 obligatorio · `0677-MIRASIERRA` impide crear `0677 ...`."""
    assert carpetas_de_obra(["0677-MIRASIERRA"], codigo_obra="0677") == ()
    assert parecidas_de_obra(["0677-MIRASIERRA"], codigo_obra="0677") == (
        "0677-MIRASIERRA",
    )


def test_f013_r35_villa_05_garcia_impide_crear_la_unidad_5():
    """R35 obligatorio · `VILLA 05 - GARCIA` impide crear la unidad 5."""
    carpetas = ["VILLA 05 - GARCIA"]

    assert carpetas_de_unidad(carpetas, ubicacion=UBICACION_VILLA_5) == ()
    assert parecidas_de_unidad(carpetas, ubicacion=UBICACION_VILLA_5) == (
        "VILLA 05 - GARCIA",
    )


def test_f013_r35_partes_de_incidencias_impide_crear_partes_incidencias():
    """R35 obligatorio · `PARTES DE INCIDENCIAS` impide crear `PARTES INCIDENCIAS`."""
    carpetas = ["PARTES DE INCIDENCIAS"]

    assert carpeta_con_nombre(carpetas, buscado=INCIDENCIAS) == ()
    assert parecidas_de_tramo(carpetas, buscado=INCIDENCIAS) == ("PARTES DE INCIDENCIAS",)


def test_f013_r35_villa_07_no_impide_crear_la_unidad_5():
    """R35 obligatorio · un número distinto es otra unidad: se puede crear."""
    carpetas = ["VILLA 07"]

    assert carpetas_de_unidad(carpetas, ubicacion=UBICACION_VILLA_5) == ()
    assert parecidas_de_unidad(carpetas, ubicacion=UBICACION_VILLA_5) == ()


def test_f013_r35_677_mirasierra_casa_y_no_es_parecida():
    """R35 (añadido el 2026-09-24) · casan y parecidas son una partición."""
    assert carpetas_de_obra([CARPETA_OBRA_0677], codigo_obra="0677") == (
        CARPETA_OBRA_0677,
    )
    assert parecidas_de_obra([CARPETA_OBRA_0677], codigo_obra="0677") == ()


def test_f013_r35_677mirasierra_impide_crear_la_obra():
    """R35 (añadido) · todas las secuencias de cifras cuentan en la amplia."""
    assert carpetas_de_obra(["677MIRASIERRA"], codigo_obra="0677") == ()
    assert parecidas_de_obra(["677MIRASIERRA"], codigo_obra="0677") == ("677MIRASIERRA",)


def test_f013_r35_villa_03_no_impide_crear_villa_13():
    """R35 (añadido) y T4-5 · el `03` del grupo no es número de la unidad."""
    villa_13 = _ubicacion("0677.03VILLA 13.", "Viviendas Bloque Villa 13")

    assert carpetas_de_unidad(["VILLA 03"], ubicacion=villa_13) == ()
    assert parecidas_de_unidad(["VILLA 03"], ubicacion=villa_13) == ()


@pytest.mark.parametrize("n", range(8, 16))
def test_f013_r35_villa_01_a_07_no_impiden_crear_villa_08_a_15(n):
    """R35 (añadido) y T4-5 · las siete que existen no bloquean ninguna nueva."""
    ubicacion = _ubicacion(f"0677.03VILLA {n}.", f"Viviendas Bloque Villa {n}")

    assert carpetas_de_unidad(UNIDADES_EN_POSVENTA, ubicacion=ubicacion) == ()
    assert parecidas_de_unidad(UNIDADES_EN_POSVENTA, ubicacion=ubicacion) == ()


def test_f013_r35_parte_firmado_impide_crear_partes_firmados():
    """R35 (añadido) · la palabra del tramo sin su `S` final y por prefijo."""
    assert carpeta_con_nombre(["PARTE FIRMADO"], buscado=FIRMADOS, alternativa=ALTERNATIVA) == ()
    assert parecidas_de_tramo(
        ["PARTE FIRMADO"], buscado=FIRMADOS, alternativa=ALTERNATIVA
    ) == ("PARTE FIRMADO",)


#: `design.md` §4.5 enmendada, fila a fila (las que no son de obra van arriba
#: con su nivel). (carpetas, ubicación, casan, parecidas) para la unidad.
TABLA_4_5_UNIDAD = (
    # `VILLA5` para la unidad 5: no casa; sí es parecida.
    (("VILLA5",), UBICACION_VILLA_5, (), ("VILLA5",)),
    (("V-5",), UBICACION_VILLA_5, (), ("V-5",)),
    (("CHALET 5",), UBICACION_VILLA_5, (), ("CHALET 5",)),
    (("VILLA 15",), UBICACION_VILLA_5, (), ()),
    # El número de la obra ya no es número de la unidad (consecuencia aceptada).
    (("LISTADO 677",), _ubicacion("0677.03VILLA 13.", "Viviendas Bloque Villa 13"), (), ()),
    # Un `con.cod` fuera del patrón: sus números sí cuentan, como antes.
    (
        ("CASA 3",),
        UbicacionReclamacion(
            obra_codigo="0677", obra_nombre=None, unidad_codigo="CHALET 3", unidad_nombre=None
        ),
        (),
        ("CASA 3",),
    ),
)


@pytest.mark.parametrize(("carpetas", "ubicacion", "casan", "parecidas"), TABLA_4_5_UNIDAD)
def test_f013_r35_tabla_4_5_unidad(carpetas, ubicacion, casan, parecidas):
    """R35 · la amplia de la unidad: todas las secuencias de cifras de la carpeta."""
    assert carpetas_de_unidad(carpetas, ubicacion=ubicacion) == casan
    assert parecidas_de_unidad(carpetas, ubicacion=ubicacion) == parecidas


@pytest.mark.parametrize(
    ("carpetas", "buscado", "parecidas"),
    (
        (("PARTES INCIDENCIA",), INCIDENCIAS, ("PARTES INCIDENCIA",)),
        (("PARTES DE INCIDENCIAS",), INCIDENCIAS, ("PARTES DE INCIDENCIAS",)),
        (("INCIDENCIAS 2025",), INCIDENCIAS, ("INCIDENCIAS 2025",)),
        (("FIRMADOS",), FIRMADOS, ("FIRMADOS",)),
        (("PARTES FIRMADOS (sistema)",), FIRMADOS, ("PARTES FIRMADOS (sistema)",)),
        (("PLANOS", "PARTES", "FIRMA"), FIRMADOS, ()),
        (("PARTES",), INCIDENCIAS, ()),
    ),
)
def test_f013_r35_tabla_4_5_tramos(carpetas, buscado, parecidas):
    """R35 · la amplia del tramo: un token que empieza por la palabra sin su `S`."""
    assert carpeta_con_nombre(carpetas, buscado=buscado) == ()
    assert parecidas_de_tramo(carpetas, buscado=buscado) == parecidas


@pytest.mark.parametrize(
    ("carpetas", "buscado", "parecidas"),
    (
        # Una palabra que no acaba en `S` se usa entera: `ARCHIV` no es parecida
        # de `ARCHIVO`, y `ARCHIVOS 2024` sí.
        (("DOCUMENTOS ARCHIV", "ARCHIVOS 2024"), "PARTES ARCHIVO", ("ARCHIVOS 2024",)),
        # Solo se quita **una** `S`: `CLASES` → `CLASE`, y `CLAS` no es parecida.
        (("CLAS", "CLASE 3"), "CLASES", ("CLASE 3",)),
        # Una palabra que es solo `S` se queda como está: no vale el prefijo vacío.
        (("PLANOS", "S 2"), "PARTES S", ("S 2",)),
        # Y se quita también en una palabra de dos letras: `OS` → `O`.
        (("PLANOS", "O 1"), "HOJA OS", ("O 1",)),
    ),
)
def test_f013_r35_la_palabra_del_tramo_sin_su_s_final(carpetas, buscado, parecidas):
    """R35 · «sin su `S` final», exactamente una, y nunca el prefijo vacío.

    Añadido tras la mutación del bloque 1 (supervivientes 4 a 7): los tramos
    reales (`FIRMADOS`, `INCIDENCIAS`) acaban en `S` y no distinguían estos
    casos.
    """
    assert parecidas_de_tramo(carpetas, buscado=buscado) == parecidas


#: Carpetas mezcladas para comprobar la partición en los cuatro niveles.
MEZCLA = (
    CARPETA_OBRA_0677,
    "0677-MIRASIERRA",
    "0677 MIRASIERRA",
    "677MIRASIERRA",
    "VILLA 05",
    "VILLA5",
    "05",
    "VILLA 05 - GARCIA",
    "PARTES FIRMADOS",
    "PARTES FIRMADO",
    "PARTE FIRMADO",
    "PARTES INCIDENCIAS",
    "PARTES INCIDENCIA",
    "PLANOS",
)


def test_f013_r35_casan_y_parecidas_son_una_particion_en_los_cuatro_niveles():
    """R35 (enmienda del 2026-09-24) · una carpeta que casa nunca es parecida."""
    pares = (
        (
            carpetas_de_obra(MEZCLA, codigo_obra="0677"),
            parecidas_de_obra(MEZCLA, codigo_obra="0677"),
        ),
        (
            carpeta_con_nombre(MEZCLA, buscado=INCIDENCIAS),
            parecidas_de_tramo(MEZCLA, buscado=INCIDENCIAS),
        ),
        (
            carpetas_de_unidad(MEZCLA, ubicacion=UBICACION_VILLA_5),
            parecidas_de_unidad(MEZCLA, ubicacion=UBICACION_VILLA_5),
        ),
        (
            carpeta_con_nombre(MEZCLA, buscado=FIRMADOS, alternativa=ALTERNATIVA),
            parecidas_de_tramo(MEZCLA, buscado=FIRMADOS, alternativa=ALTERNATIVA),
        ),
    )
    for casan, parecidas in pares:
        assert casan, "cada nivel tiene que tener algo que case en la mezcla"
        assert parecidas, "y algo parecido, o el control no controla nada"
        assert not set(casan) & set(parecidas)


# --------------------------------------------------------------------------
# §4.6 · Con qué nombre se crea (R36–R38) y R37: `VILLA NN`
# --------------------------------------------------------------------------


def test_f013_r37_el_patron_es_el_medido():
    """R37 · el único patrón del que se deriva un nombre de unidad (T3)."""
    assert (
        PATRON_CODIGO_UNIDAD.pattern
        == r"(?P<obra>[0-9]+)\.(?P<grupo>[0-9]+)VILLA +(?P<n>[0-9]+)\."
    )


#: `design.md` §4.6, los 15 casos medidos de la 0677, fila a fila:
#: (con.cod, con.res, carpeta en Posventa hoy, nombre derivado, qué hará el sistema).
TABLA_4_6 = (
    ("0677.03VILLA 1.", "Viviendas Bloque Villa 1", "VILLA 01", "VILLA 01", "resuelve"),
    ("0677.03VILLA 2.", "Viviendas Bloque Villa 2", "VILLA 02", "VILLA 02", "resuelve en PARTES FIRMADO"),
    ("0677.03VILLA 3.", "Viviendas Bloque Villa 3", "VILLA 03", "VILLA 03", "resuelve"),
    ("0677.03VILLA 4.", "Viviendas Bloque Villa 4", "VILLA 04", "VILLA 04", "crea PARTES FIRMADOS"),
    ("0677.03VILLA 5.", "Viviendas Bloque Villa 5", "VILLA 05", "VILLA 05", "resuelve"),
    ("0677.03VILLA 6.", "Viviendas Bloque Villa 6", "VILLA 06", "VILLA 06", "resuelve"),
    ("0677.03VILLA 7.", "Viviendas Bloque Villa 7", "VILLA 07", "VILLA 07", "resuelve"),
    ("0677.03VILLA 8.", "Viviendas Bloque Villa 8", None, "VILLA 08", "crea VILLA 08 y su PARTES FIRMADOS"),
    ("0677.03VILLA 9.", "Viviendas Bloque Villa 9", None, "VILLA 09", "crea VILLA 09 y su PARTES FIRMADOS"),
    ("0677.03VILLA 10.", "Viviendas Bloque Villa 10", None, "VILLA 10", "crea VILLA 10 y su PARTES FIRMADOS"),
    ("0677.03VILLA 11.", "Viviendas Bloque Villa 11", None, "VILLA 11", "crea VILLA 11 y su PARTES FIRMADOS"),
    ("0677.03VILLA 12.", "Viviendas Bloque Villa 12", None, "VILLA 12", "crea VILLA 12 y su PARTES FIRMADOS"),
    ("0677.03VILLA 13.", "Viviendas Bloque Villa 13", None, "VILLA 13", "crea VILLA 13 y su PARTES FIRMADOS"),
    ("0677.03VILLA 14.", "Viviendas Bloque Villa 14", None, "VILLA 14", "crea VILLA 14 y su PARTES FIRMADOS"),
    ("0677.03VILLA 15.", "Viviendas Bloque Villa 15", None, "VILLA 15", "crea VILLA 15 y su PARTES FIRMADOS"),
)


def _que_hara_el_sistema(cod: str, res: str) -> str:
    """La última columna de la tabla, calculada **solo** con el dominio.

    Contra el árbol medido: la unidad casa o se crea (sin parecidas), y dentro
    de la unidad la hoja casa o se crea. Lo que el resolutor hace con esto
    (T9) es orquestarlo; la decisión es de aquí.
    """
    ubicacion = _ubicacion(cod, res)
    casan = carpetas_de_unidad(UNIDADES_EN_POSVENTA, ubicacion=ubicacion)
    parecidas = parecidas_de_unidad(UNIDADES_EN_POSVENTA, ubicacion=ubicacion)
    assert len(casan) <= 1 and not parecidas, "la 0677 no tiene ambiguas ni parecidas"
    if not casan:
        nombre = nombre_derivado_de_unidad(cod, codigo_obra="0677")
        return f"crea {nombre} y su {FIRMADOS}"
    (unidad,) = casan
    hojas = HOJAS_EN_POSVENTA[unidad]
    casan_hoja = carpeta_con_nombre(hojas, buscado=FIRMADOS, alternativa=ALTERNATIVA)
    assert not parecidas_de_tramo(hojas, buscado=FIRMADOS, alternativa=ALTERNATIVA)
    if not casan_hoja:
        return f"crea {FIRMADOS}"
    (hoja,) = casan_hoja
    return "resuelve" if hoja == FIRMADOS else f"resuelve en {hoja}"


@pytest.mark.parametrize(("cod", "res", "carpeta", "derivado", "que_hara"), TABLA_4_6)
def test_f013_r37_tabla_4_6_los_15_casos_de_la_0677(cod, res, carpeta, derivado, que_hara):
    """R31, R37, R48, R49 · los 15 casos medidos dan la última columna.

    Y en cada fila, las dos defensas de la unidad: la carpeta (existente o
    creada) casa con **esa** unidad de Sigrid y con ninguna otra (R50).
    """
    assert nombre_derivado_de_unidad(cod, codigo_obra="0677") == derivado
    assert _que_hara_el_sistema(cod, res) == que_hara

    elegida = carpeta if carpeta is not None else derivado
    (unica,) = unidades_que_casan(FILAS_0677, carpeta=elegida)
    assert unica.unidad_codigo == cod


@pytest.mark.parametrize(
    ("cod", "obra", "nombre"),
    (
        ("0677.03VILLA 13", "0677", None),  # sin punto final
        ("0677.03Villa 13.", "0677", None),  # minúsculas: no se relajan
        ("0677.03CHALET 3.", "0677", None),  # otra palabra: otra enmienda
        ("0680.03VILLA 13.", "0677", None),  # otra obra
        ("0677.VILLA 13.", "0677", None),  # sin grupo
        (None, "0677", None),
        ("", "0677", None),
        ("0677.03VILLA  13.", "0677", "VILLA 13"),  # dos blancos
        ("0677.03VILLA 100.", "0677", "VILLA 100"),
        ("00677.03VILLA 5.", "0677", "VILLA 05"),  # mismo número de obra
        ("0677.03VILLA 5.", "677", "VILLA 05"),
        ("  0677.03VILLA 5.  ", "0677", "VILLA 05"),  # extremos recortados
        ("X0677.03VILLA 5.", "0677", None),  # entero: fullmatch
        ("0677.03VILLA 5.X", "0677", None),
        ("0677.03VILLA 5.", "ADM", None),  # obra sin número
        ("0677.03VILLA 5.", "", None),
    ),
)
def test_f013_r37_fuera_del_patron_no_se_inventa(cod, obra, nombre):
    """R37 · lo que no cumple el patrón **entero**, o es de otra obra, es `None`.

    `None` → 409 `unidad_sin_nombre_derivable`, solo si hay que crear (T9).
    """
    assert nombre_derivado_de_unidad(cod, codigo_obra=obra) == nombre


@pytest.mark.parametrize(
    ("codigo", "res", "nombre"),
    (
        ("0677", RES_OBRA_0677, "0677 15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)"),
        ("0677", "  15   VIVIENDAS\tUNIFAMILIARES  ", "0677 15 VIVIENDAS UNIFAMILIARES"),
        ("0677", "Obra en minúsculas", "0677 Obra en minúsculas"),  # literal
        (" 06 77 ", "X", "0677 X"),  # código normalizado, ceros intactos
        ("677", "X", "677 X"),  # sin rellenar ceros
        ("ADM", "Oficina", "ADM Oficina"),
    ),
)
def test_f013_r36_nombre_de_la_obra_que_se_crea(codigo, res, nombre):
    """R36 · `<código> <con.res>`: literal, recortado, blancos colapsados."""
    assert nombre_de_obra_nueva(codigo, res) == nombre


@pytest.mark.parametrize("res", (None, "", "   "))
def test_f013_r36_sin_nombre_de_obra_el_nombre_es_imposible(res):
    """R36 y R38 · sin `con.res` no se inventa: el nombre no pasa R38 → 409."""
    assert not nombre_de_carpeta_admisible(nombre_de_obra_nueva("0677", res))


@pytest.mark.parametrize(
    ("nombre", "admisible"),
    (
        ("VILLA 13", True),
        (FIRMADOS, True),
        (INCIDENCIAS, True),
        ("0677 15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)", True),
        ("", False),
        (" VILLA 13", False),
        ("VILLA 13 ", False),
        ("VILLA 13.", False),
        ("0677 OBRA A/B", False),
    )
    + tuple((f"OBRA {caracter} X", False) for caracter in CARACTERES_PROHIBIDOS),
)
def test_f013_r38_nombres_imposibles(nombre, admisible):
    """R38 · la misma regla que F-006 R7 aplica al fichero; nunca se sanea."""
    assert nombre_de_carpeta_admisible(nombre) is admisible


# --------------------------------------------------------------------------
# R39 y R46 · Lo creado casa consigo mismo, y cuándo no
# --------------------------------------------------------------------------


def test_f013_r39_la_obra_creada_casa_consigo_misma():
    """R39 · `0677 15 VIVIENDAS…` empieza por el número: la siguiente la encuentra."""
    creada = nombre_de_obra_nueva("0677", RES_OBRA_0677)

    assert carpetas_de_obra([creada], codigo_obra="0677") == (creada,)
    assert parecidas_de_obra([creada], codigo_obra="0677") == ()


def test_f013_r39_una_obra_no_numerica_creada_casa_consigo_misma():
    """R39 · también con la regla literal."""
    creada = nombre_de_obra_nueva("ADM", "Oficina central")

    assert carpetas_de_obra([creada], codigo_obra="ADM") == (creada,)


@pytest.mark.parametrize(("cod", "res"), [(fila[0], fila[1]) for fila in TABLA_4_6])
def test_f013_r46_cada_villa_creada_casa_con_su_unidad(cod, res):
    """R46 · `VILLA NN` casa con la unidad porque su `con.res` acaba en `Villa N`."""
    derivado = nombre_derivado_de_unidad(cod, codigo_obra="0677")
    ubicacion = _ubicacion(cod, res)

    assert carpetas_de_unidad([derivado], ubicacion=ubicacion) == (derivado,)
    assert parecidas_de_unidad([derivado], ubicacion=ubicacion) == ()


@pytest.mark.parametrize("buscado", (INCIDENCIAS, FIRMADOS))
def test_f013_r39_los_tramos_creados_casan_consigo_mismos(buscado):
    """R39 · los tramos fijos se crean con el literal buscado."""
    assert carpeta_con_nombre([buscado], buscado=buscado, alternativa=ALTERNATIVA) == (
        buscado,
    )


def test_f013_r46_un_con_res_que_no_acaba_en_su_villa_no_casaria():
    """R46 · `Villa 13 bis` recibiría `VILLA 13`, que ni casa ni deja de ser parecida.

    La siguiente resolución daría 409 para siempre: por eso el resolutor lo
    comprueba antes de anotar la creación (`nombre_no_casaria`).
    """
    ubicacion = _ubicacion("0677.03VILLA 13.", "Viviendas Bloque Villa 13 bis")
    derivado = nombre_derivado_de_unidad("0677.03VILLA 13.", codigo_obra="0677")

    assert derivado == "VILLA 13"
    assert carpetas_de_unidad([derivado], ubicacion=ubicacion) == ()
    assert parecidas_de_unidad([derivado], ubicacion=ubicacion) == (derivado,)


# --------------------------------------------------------------------------
# §4.7 · Números repetidos en Sigrid (R44, R50)
# --------------------------------------------------------------------------


def test_f013_r44_la_0677_medida_es_una_sola_obra():
    """R44 · T3: una obra con ese número y unidades de posventa."""
    assert obras_del_mismo_numero(FILAS_0677, codigo_obra="0677") == frozenset({"obra-a"})


def test_f013_r44_devuelve_un_conjunto_inmutable():
    """R44 · lo que se cuenta son obras distintas, no filas."""
    assert isinstance(obras_del_mismo_numero(FILAS_0677, codigo_obra="0677"), frozenset)


@pytest.mark.parametrize(
    ("codigo_otra", "cuenta"),
    (
        ("0677", 2),  # dos obras 0677: el mismo código literal
        ("677", 2),  # 0677 y 677: el mismo número
        ("00677", 2),
        ("1677", 1),  # lo que el SQL dejara pasar de más, fuera
        ("06770", 1),
        ("X677", 1),
        ("0677-B", 1),
        (None, 1),
    ),
)
def test_f013_r44_obras_del_mismo_numero(codigo_otra, cuenta):
    """R44 · dos obras de Sigrid con el mismo número irían a la misma carpeta."""
    otra = UnidadDeObra(
        obra_ref="obra-b",
        obra_codigo=codigo_otra,
        unidad_codigo="X.01VILLA 1.",
        unidad_nombre="Villa 1",
    )

    assert len(obras_del_mismo_numero(FILAS_0677 + (otra,), codigo_obra="0677")) == cuenta


def test_f013_r44_se_busca_por_numero_con_el_codigo_como_venga():
    """R44 · pedir `677` encuentra la obra guardada como `0677`."""
    assert obras_del_mismo_numero(FILAS_0677, codigo_obra="677") == frozenset({"obra-a"})


@pytest.mark.parametrize(
    ("codigo_fila", "cuenta"),
    (("ADM", 1), (" ADM ", 1), ("adm", 0), ("ADM2", 0), (None, 0)),
)
def test_f013_r44_codigo_no_numerico_mismo_codigo_normalizado(codigo_fila, cuenta):
    """R44 · sin número, el mismo código normalizado (`normalizar_codigo`)."""
    fila = UnidadDeObra(
        obra_ref="obra-adm", obra_codigo=codigo_fila, unidad_codigo=None, unidad_nombre=None
    )

    assert len(obras_del_mismo_numero([fila], codigo_obra="ADM")) == cuenta


def test_f013_r44_sin_filas_o_sin_codigo_no_hay_ninguna_obra():
    """R44 · ninguna obra también es `obra_numero_no_unico` (≠ 1), en el resolutor."""
    assert obras_del_mismo_numero([], codigo_obra="0677") == frozenset()
    assert obras_del_mismo_numero(FILAS_0677, codigo_obra="") == frozenset()


def test_f013_r44_la_referencia_de_obra_no_sale_en_el_repr():
    """R23 y §3.3 · `obra_ref` es un identificador del ERP: no se loguea.

    Un `log.info("%s", unidad)` descuidado no puede sacarlo.
    """
    unidad = UnidadDeObra(
        obra_ref="referencia-opaca-9999",
        obra_codigo="0677",
        unidad_codigo="0677.03VILLA 5.",
        unidad_nombre="Viviendas Bloque Villa 5",
    )

    assert "referencia-opaca-9999" not in repr(unidad)
    assert "0677.03VILLA 5." in repr(unidad)


@pytest.mark.parametrize(
    ("carpeta", "villas"),
    (
        ("VILLA 05", (5,)),
        ("VILLA 01", (1,)),  # no la 11
        ("VILLA 13", (13,)),
        ("Villa 1", (1,)),
        ("VILLA 16", ()),
        ("VILLA 05 - X", ()),
        ("PLANOS", ()),
    ),
)
def test_f013_r50_unidades_que_casan(carpeta, villas):
    """R50 · con qué unidades de la obra casa la carpeta, por la regla estricta."""
    casan = unidades_que_casan(FILAS_0677, carpeta=carpeta)

    assert tuple(fila.unidad_codigo for fila in casan) == tuple(
        f"0677.03VILLA {n}." for n in villas
    )


def test_f013_r50_dos_grupos_que_comparten_villa_casan_los_dos():
    """R50 · `0677.03VILLA 5.` y `0677.04VILLA 5.` → la misma `VILLA 05` → 409.

    La derivación de R37 ignora el grupo, así que las dos darían el mismo
    nombre: el DNI podría acabar en la villa del otro grupo.
    """
    otro_grupo = UnidadDeObra(
        obra_ref="obra-a",
        obra_codigo="0677",
        unidad_codigo="0677.04VILLA 5.",
        unidad_nombre="Viviendas Bloque Villa 5",
    )

    casan = unidades_que_casan(FILAS_0677 + (otro_grupo,), carpeta="VILLA 05")

    assert [fila.unidad_codigo for fila in casan] == ["0677.03VILLA 5.", "0677.04VILLA 5."]
    assert nombre_derivado_de_unidad(
        "0677.04VILLA 5.", codigo_obra="0677"
    ) == nombre_derivado_de_unidad("0677.03VILLA 5.", codigo_obra="0677")


def test_f013_r50_la_unidad_que_casa_solo_por_su_codigo_tambien_cuenta():
    """R50 · la regla estricta entera: también la regla 1, el `con.cod`.

    Una unidad cuyo código corto es `VILLA 05` casa con la carpeta `VILLA 05`
    aunque no tenga `con.res`; junto a la villa 5 medida (que casa por el
    nombre) son **dos** → `unidad_carpeta_compartida`. Contar solo las que
    casan por el nombre dejaría pasar la carpeta compartida, y una carpeta
    elegida por el código se quedaría sin su unidad (añadido en T20: mutante a
    mano U4, que quitaba el código y sobrevivía).
    """
    por_el_codigo = UnidadDeObra(
        obra_ref="obra-a", obra_codigo="0677", unidad_codigo="VILLA 05", unidad_nombre=None
    )

    solo_ella = unidades_que_casan((por_el_codigo,), carpeta="Villa 5")
    las_dos = unidades_que_casan(FILAS_0677 + (por_el_codigo,), carpeta="VILLA 05")

    assert solo_ella == (por_el_codigo,)
    assert [fila.unidad_codigo for fila in las_dos] == ["0677.03VILLA 5.", "VILLA 05"]


# --------------------------------------------------------------------------
# El árbol medido, obra e incidencias (T2)
# --------------------------------------------------------------------------


def test_f013_r31_el_arbol_medido_resuelve_obra_e_incidencias():
    """R31 · obra `677  MIRASIERRA` y `PARTES INCIDENCIAS` «resolverían»."""
    assert carpetas_de_obra(RAIZ, codigo_obra="0677") == (CARPETA_OBRA_0677,)
    assert parecidas_de_obra(RAIZ, codigo_obra="0677") == ()
    assert carpeta_con_nombre(DENTRO_DE_LA_OBRA, buscado=INCIDENCIAS) == (INCIDENCIAS,)


# --------------------------------------------------------------------------
# R17 · La ruta, con base vacía
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tramos", "ruta"),
    (
        (("", CARPETA_OBRA_0677, INCIDENCIAS), "677  MIRASIERRA/PARTES INCIDENCIAS"),
        (("Postventa", "0677"), "Postventa/0677"),
        (("/Postventa/", "0677"), "Postventa/0677"),
        ((" Postventa ", "0677"), "Postventa/0677"),
        (("", "", "0677", ""), "0677"),
        (("/", "0677"), "0677"),
        (("", CARPETA_OBRA_0677, INCIDENCIAS, "VILLA 05", FIRMADOS),
         "677  MIRASIERRA/PARTES INCIDENCIAS/VILLA 05/PARTES FIRMADOS"),
        ((), ""),
        (("",), ""),
    ),
)
def test_f013_r17_unir_ruta_con_base_vacia(tramos, ruta):
    """R17 · base vacía = raíz: sin `/0677` ni `//` ni tramos vacíos."""
    unida = unir_ruta(*tramos)

    assert unida == ruta
    assert not unida.startswith("/")
    assert "//" not in unida


def test_f013_r17_unir_ruta_respeta_los_blancos_de_dentro():
    """R4 · el nombre tal y como existe: los dos blancos de la obra se quedan."""
    assert unir_ruta("", "677  MIRASIERRA") == "677  MIRASIERRA"


# --------------------------------------------------------------------------
# Los tipos del dominio son inmutables
# --------------------------------------------------------------------------


def test_f013_los_datos_de_sigrid_son_inmutables():
    """Entre leerlos y decidir la carpeta no los puede reescribir nadie."""
    with pytest.raises(FrozenInstanceError):
        UBICACION_VILLA_5.unidad_nombre = "otra"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        FILAS_0677[0].obra_ref = "otra"  # type: ignore[misc]
