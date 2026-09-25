# services/postventa-api/tests/test_f049_villa_tres_cifras.py
"""F-049 · las villas que crea el archivo, siempre con tres cifras.

El paso 2 del corte de F-013 (2026-09-25) midió con el script 23 que Posventa
ha reorganizado la biblioteca de la obra piloto: sus unidades se llaman ahora
`VILLA 001` … `VILLA 007`, `VILLA 012` y `VILLA 013`. El humano decidió
«siempre con tres cifras»: lo que cree el sistema es `VILLA 008`, `VILLA 013`;
con 1.000 o más, tal cual.

Lo que **no** cambia, y aquí se fija para que no cambie: cómo se **casa**. La
clave de la unidad compara números enteros, así que `VILLA 001`, `VILLA 01` y
`VILLA 1` son la misma villa 1.

Sin red, sin Graph, sin Sigrid. Los datos medidos de T2 (2026-09-24, dos
cifras) son los de `tests/utiles_destino.py` y no se tocan: la biblioteca
reorganizada es un árbol **nuevo**, montado aquí. Las hojas de sus carpetas no
se midieron el 2026-09-25 [NO MEDIDO]: aquí todas llevan `PARTES FIRMADOS`,
que es lo neutro para lo que se prueba (el nivel de la unidad).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from application.pipelines.destino_archivo import (
    DestinoResuelto,
    resolver_destino_posventa,
)
from domain.models.destino_posventa import (
    MotivoDestino,
    carpetas_de_unidad,
    nombre_de_carpeta_admisible,
    nombre_derivado_de_unidad,
    parecidas_de_unidad,
    unidades_que_casan,
)
from domain.models.errores import DestinoNoResuelto

from tests.utiles_destino import (
    ALTERNATIVA,
    CARPETA_OBRA_0677,
    DENTRO_DE_LA_OBRA_0677,
    FIRMADOS,
    INCIDENCIAS,
    RAIZ_0677,
    UNIDADES_0677,
    ExploradorFalso,
    reclamacion_0677,
    ubicacion_0677,
    ubicaciones_0677,
)

RAIZ = Path(__file__).resolve().parents[3]

INC = f"{CARPETA_OBRA_0677}/{INCIDENCIAS}"

#: Las carpetas de unidad de la 0677 tras la reorganización de Posventa, como
#: las listó el script 23 en el paso 2 del corte [MEDIDO, 2026-09-25].
VILLAS_REORGANIZADAS = tuple(f"VILLA {n:03d}" for n in (*range(1, 8), 12, 13))

#: Las unidades de Sigrid con carpeta y sin ella, en la biblioteca reorganizada.
CON_CARPETA = (*range(1, 8), 12, 13)
SIN_CARPETA = (8, 9, 10, 11, 14, 15)


def _arbol(villas: tuple[str, ...] = VILLAS_REORGANIZADAS) -> dict[str, tuple[str, ...]]:
    """La 0677 con las carpetas de unidad dadas, cada una con su hoja."""
    arbol: dict[str, tuple[str, ...]] = {
        "": RAIZ_0677,
        CARPETA_OBRA_0677: DENTRO_DE_LA_OBRA_0677,
        INC: villas,
    }
    for villa in villas:
        arbol[f"{INC}/{villa}"] = (FIRMADOS,)
    return arbol


def _resolver(explorador: ExploradorFalso, n: int) -> DestinoResuelto:
    """Resuelve la reclamación de la villa `n`; el resolutor nunca crea."""
    try:
        return resolver_destino_posventa(
            codigo_obra="0677",
            numero_incidencia=reclamacion_0677(n),
            nombre_fichero="0677 - RS26.08 - 0005 PARTE FIRMADO.pdf",
            explorador=explorador,
            ubicaciones=ubicaciones_0677(),
            base="",
            incidencias=INCIDENCIAS,
            firmados=FIRMADOS,
            firmados_alternativa=ALTERNATIVA,
            crear_carpetas=True,
        )
    finally:
        assert explorador.creaciones == []


# --------------------------------------------------------------------------
# R1 · el nombre que se crea, con al menos tres cifras
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cod", "nombre"),
    (
        ("0677.03VILLA 1.", "VILLA 001"),
        ("0677.03VILLA 8.", "VILLA 008"),
        ("0677.03VILLA 13.", "VILLA 013"),
        ("0677.03VILLA 99.", "VILLA 099"),
        ("0677.03VILLA 100.", "VILLA 100"),
        ("0677.03VILLA 999.", "VILLA 999"),
        ("0677.03VILLA 1000.", "VILLA 1000"),
        ("0677.03VILLA 12345.", "VILLA 12345"),
        ("0677.03VILLA 008.", "VILLA 008"),  # los ceros del con.cod no cuentan
        ("0677.03VILLA 0013.", "VILLA 013"),
        ("0677.03VILLA 0.", "VILLA 000"),
        ("0677.03VILLA  8.", "VILLA 008"),  # dos blancos, como en F-013
        ("  0677.03VILLA 8.  ", "VILLA 008"),
    ),
)
def test_f049_r1_la_villa_se_crea_con_tres_cifras(cod, nombre):
    """R1 · `VILLA 008`, `VILLA 013`; de tres cifras en adelante, tal cual."""
    assert nombre_derivado_de_unidad(cod, codigo_obra="0677") == nombre


@pytest.mark.parametrize(
    "cod",
    ("0677.03VILLA 8", "0677.03Villa 8.", "0680.03VILLA 8.", "0677.VILLA 8.", None, ""),
)
def test_f049_r1_lo_que_no_cumple_el_patron_sigue_sin_nombre(cod):
    """R1 · el ancho no cambia lo que se deriva y lo que no (F-013 R37)."""
    assert nombre_derivado_de_unidad(cod, codigo_obra="0677") is None


@pytest.mark.parametrize("n", range(1, 16))
def test_f049_r1_las_15_villas_de_la_0677(n):
    """R1 · las 15 unidades medidas de la 0677: `VILLA 001` … `VILLA 015`."""
    assert nombre_derivado_de_unidad(f"0677.03VILLA {n}.", codigo_obra="0677") == (
        f"VILLA {n:03d}"
    )


# --------------------------------------------------------------------------
# R2 · cómo se casa no cambia
# --------------------------------------------------------------------------


@pytest.mark.parametrize("carpeta", ("VILLA 001", "VILLA 01", "VILLA 1", "Villa 001"))
def test_f049_r2_tres_dos_o_una_cifra_son_la_misma_villa_1(carpeta):
    """R2 · la villa 1, y ninguna otra (ni la 10, ni la 11)."""
    casan = unidades_que_casan(UNIDADES_0677, carpeta=carpeta)

    assert [fila.unidad_codigo for fila in casan] == ["0677.03VILLA 1."]
    assert carpetas_de_unidad([carpeta], ubicacion=ubicacion_0677(1)) == (carpeta,)
    assert parecidas_de_unidad([carpeta], ubicacion=ubicacion_0677(1)) == ()


@pytest.mark.parametrize("n", (10, 100))
def test_f049_r2_villa_001_no_es_la_10_ni_la_100(n):
    """R2 · `VILLA 001` ni casa con la 10 o la 100 ni se les parece."""
    ubicacion = ubicacion_0677(n)  # `0677.03VILLA {n}.`, «Viviendas Bloque Villa {n}»

    assert carpetas_de_unidad(["VILLA 001"], ubicacion=ubicacion) == ()
    assert parecidas_de_unidad(["VILLA 001"], ubicacion=ubicacion) == ()


@pytest.mark.parametrize("n", CON_CARPETA)
def test_f049_r2_la_biblioteca_reorganizada_casa_sin_crear(n):
    """R2 · 1–7, 12 y 13 resuelven en su `VILLA 0NN` existente: nada que crear."""
    resuelto = _resolver(ExploradorFalso(_arbol()), n)

    assert resuelto.carpetas_por_crear == ()
    assert resuelto.destino.carpeta == f"{INC}/VILLA {n:03d}/{FIRMADOS}"


@pytest.mark.parametrize("n", SIN_CARPETA)
def test_f049_r2_las_que_faltan_se_crean_con_tres_cifras(n):
    """R2 · 8–11, 14 y 15 se crean como `VILLA 0NN` con su hoja; nada las para."""
    resuelto = _resolver(ExploradorFalso(_arbol()), n)

    villa = f"VILLA {n:03d}"
    assert resuelto.carpetas_por_crear == ((INC, villa), (f"{INC}/{villa}", FIRMADOS))
    assert resuelto.destino.carpeta == f"{INC}/{villa}/{FIRMADOS}"


def test_f049_r2_villa_01_y_villa_001_juntas_son_ambiguas():
    """R2 · si conviven las dos grafías, son dos candidatas de la villa 1: 409."""
    villas = ("VILLA 01", *VILLAS_REORGANIZADAS)

    with pytest.raises(DestinoNoResuelto) as error:
        _resolver(ExploradorFalso(_arbol(villas)), 1)

    assert error.value.motivo is MotivoDestino.UNIDAD_AMBIGUA
    assert set(error.value.candidatas) == {"VILLA 01", "VILLA 001"}


# --------------------------------------------------------------------------
# R3 · lo creado casa consigo mismo, y solo con su unidad
# --------------------------------------------------------------------------


@pytest.mark.parametrize("n", range(1, 16))
def test_f049_r3_cada_villa_creada_casa_con_su_unidad_y_con_ninguna_otra(n):
    """R3 (F-013 R38, R46, R50) · para las 15 unidades de la 0677."""
    creada = nombre_derivado_de_unidad(f"0677.03VILLA {n}.", codigo_obra="0677")

    assert nombre_de_carpeta_admisible(creada)
    assert carpetas_de_unidad([creada], ubicacion=ubicacion_0677(n)) == (creada,)
    assert parecidas_de_unidad([creada], ubicacion=ubicacion_0677(n)) == ()
    (unica,) = unidades_que_casan(UNIDADES_0677, carpeta=creada)
    assert unica.unidad_codigo == f"0677.03VILLA {n}."


@pytest.mark.parametrize("n", SIN_CARPETA)
def test_f049_r3_la_segunda_resolucion_la_encuentra(n):
    """R3 (F-013 R39) · creada en el doble, la siguiente la encuentra sin crear."""
    explorador = ExploradorFalso(_arbol())
    for padre, nombre in _resolver(explorador, n).carpetas_por_crear:
        explorador.crear_subcarpeta(padre=padre, nombre=nombre)
    explorador.creaciones.clear()

    segunda = _resolver(explorador, n)

    assert segunda.carpetas_por_crear == ()
    assert segunda.destino.carpeta == f"{INC}/VILLA {n:03d}/{FIRMADOS}"


# --------------------------------------------------------------------------
# R4 · la documentación, con recuadro fechado que cita la premisa
# --------------------------------------------------------------------------

REQUISITOS_F013 = RAIZ / "specs" / "F-013-archivo-posventa" / "requirements.md"
DISENO_F013 = RAIZ / "specs" / "F-013-archivo-posventa" / "design.md"
TAREAS_F013 = RAIZ / "specs" / "F-013-archivo-posventa" / "tasks.md"
INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"
DESPLIEGUE = RAIZ / "docs" / "DESPLIEGUE.md"

#: Cómo empieza un recuadro de esta feature: fechado en su cabecera.
CABECERA = re.compile(r"^(?:Enmienda|Precisión) del 2026-09-25 \(F-049\)")

#: Las premisas que se enmiendan, tal y como están escritas (sin marcado).
PREMISAS = {
    REQUISITOS_F013: (
        # T4-1
        "(0677.03VILLA 13. → VILLA 13, dos cifras)",
        # T4-5
        "como VILLA NN con su PARTES FIRMADOS",
        # Vocabulario
        "VILLA NN, compuesto del con.cod de la unidad de Sigrid con la regla de R37",
        # R37
        (
            "el nombre es VILLA seguido de <n> como entero con al menos dos cifras: "
            "1 → VILLA 01, 13 → VILLA 13, 100 → VILLA 100."
        ),
        # R31
        "VILLA 08 … VILLA 15 crearían VILLA NN y su PARTES FIRMADOS (T4-5)",
        # R42
        "en la 0677: VILLA 08 … VILLA 15 según lleguen sus partes",
    ),
    DISENO_F013: (
        # §1
        "7: VILLA 01 … VILLA 07, siempre dos cifras",
        # §4.5
        "se crean VILLA 08 … VILLA 15",
        # §4.6
        'NN = f"{int(n):02d}".',
        # §7.3
        "VILLA 08–15 «crearía VILLA NN» y su hoja",
    ),
    TAREAS_F013: ("VILLA 08–15 «crearía VILLA NN» y su hoja",),
    INTEGRACION: (
        "(0677.03VILLA 13. → VILLA 13)",
        "VILLA 08 … VILLA 15 según lleguen sus partes.",
    ),
    DESPLIEGUE: (
        "VILLA 08 … 15, «crearía VILLA NN + PARTES FIRMADOS»",
        "en la 0677, VILLA 08 … VILLA 15 según lleguen sus partes",
    ),
}

#: Lo que cada documento tiene que decir **dentro** de sus recuadros de F-049.
LO_NUEVO = {
    REQUISITOS_F013: ("VILLA 008", "VILLA 013", "VILLA 1000", "al menos tres cifras"),
    DISENO_F013: ('NN = f"{int(n):03d}"', "VILLA 001", "VILLA 012", "VILLA 008"),
    TAREAS_F013: ("crearía VILLA 008",),
    INTEGRACION: ("VILLA 013", "VILLA 008"),
    DESPLIEGUE: ("crearía VILLA 008", "VILLA 001"),
}


def _normal(texto: str) -> str:
    """Sin negritas, sin comillas de código y sin saltos."""
    return " ".join(texto.replace("*", "").replace("`", "").split())


def _bloques(texto: str) -> list[tuple[bool, str]]:
    """El documento en bloques `(es_recuadro, texto normalizado)`, en orden."""
    bloques: list[tuple[bool, list[str]]] = []
    for linea in texto.splitlines():
        cita = linea.lstrip().startswith(">")
        contenido = linea.lstrip()[1:] if cita else linea
        if not bloques or bloques[-1][0] != cita:
            bloques.append((cita, []))
        bloques[-1][1].append(contenido)
    return [(cita, _normal(" ".join(lineas))) for cita, lineas in bloques]


def _partes(documento: Path) -> tuple[list[str], str]:
    """Los recuadros de F-049 y el resto del documento, normalizados."""
    bloques = _bloques(documento.read_text(encoding="utf-8"))
    de_f049 = [texto for cita, texto in bloques if cita and CABECERA.match(texto)]
    resto = " ".join(
        texto for cita, texto in bloques if not (cita and CABECERA.match(texto))
    )
    return de_f049, resto


def _comprobar(documento: Path, premisas: tuple[str, ...], nuevo: tuple[str, ...]) -> None:
    recuadros, resto = _partes(documento)
    assert recuadros, f"{documento.name}: ningún recuadro fechado de F-049"
    for premisa in premisas:
        citada = _normal(premisa)
        assert any(citada in recuadro for recuadro in recuadros), (
            f"{documento.name}: ningún recuadro de F-049 cita «{premisa}»"
        )
        assert citada in resto, f"{documento.name}: «{premisa}» se ha borrado de su sitio"
    for texto in nuevo:
        assert any(_normal(texto) in recuadro for recuadro in recuadros), (
            f"{documento.name}: los recuadros de F-049 no dicen «{texto}»"
        )
    assert any("humano" in recuadro for recuadro in recuadros)


@pytest.mark.parametrize("documento", tuple(PREMISAS), ids=lambda ruta: ruta.parent.name + "/" + ruta.name)
def test_f049_r4_la_documentacion_lleva_su_recuadro_fechado(documento):
    """R4 · cada premisa de «dos cifras», citada en un recuadro y viva en su sitio."""
    _comprobar(documento, PREMISAS[documento], LO_NUEVO[documento])


def test_f049_r4_el_runbook_de_r31_dice_crearia_villa_008():
    """R4 · la salida esperada de R31 en el runbook del corte (§9)."""
    texto = DESPLIEGUE.read_text(encoding="utf-8")
    inicio = texto.index("## 9 ")
    fin = texto.find("\n## ", inicio + 1)
    seccion = texto[inicio : fin if fin != -1 else len(texto)]
    recuadros = [t for cita, t in _bloques(seccion) if cita and CABECERA.match(t)]

    assert any("crearía VILLA 008" in recuadro for recuadro in recuadros)


PREMISA_DE_PRUEBA = "La villa se crea con **dos cifras**."


@pytest.mark.parametrize(
    "contenido",
    (
        # Parafrasea en vez de citar.
        f"{PREMISA_DE_PRUEBA}\n\n> **Enmienda del 2026-09-25 (F-049).** El humano: tres. VILLA 008.\n",
        # Cita, pero la premisa se ha borrado de su sitio.
        f"> **Enmienda del 2026-09-25 (F-049).** Decía «{PREMISA_DE_PRUEBA}». Humano: VILLA 008.\n",
        # Cita y conserva, pero sin fecha en la cabecera.
        f"{PREMISA_DE_PRUEBA}\n\n> **Enmienda (F-049).** Decía «{PREMISA_DE_PRUEBA}». Humano: VILLA 008.\n",
        # Cita y conserva, pero no dice lo nuevo.
        f"{PREMISA_DE_PRUEBA}\n\n> **Enmienda del 2026-09-25 (F-049).** Decía «{PREMISA_DE_PRUEBA}». Humano.\n",
        # Cita, conserva y dice lo nuevo, pero no quién lo decidió.
        f"{PREMISA_DE_PRUEBA}\n\n> **Enmienda del 2026-09-25 (F-049).** Decía «{PREMISA_DE_PRUEBA}». VILLA 008.\n",
    ),
    ids=("parafrasea", "borra-la-premisa", "sin-fecha", "sin-lo-nuevo", "sin-quien"),
)
def test_f049_r4_el_control_caza_lo_que_no_es_enmendar(tmp_path, contenido):
    """Controles negativos: el control de R4 no se conforma con cualquier cosa."""
    fichero = tmp_path / "DOC.md"
    fichero.write_text(contenido, encoding="utf-8")

    with pytest.raises(AssertionError):
        _comprobar(fichero, (PREMISA_DE_PRUEBA,), ("VILLA 008",))


def test_f049_r4_el_control_acepta_una_enmienda_bien_hecha(tmp_path):
    """Y el positivo, con la cita partida en dos líneas y otro marcado."""
    fichero = tmp_path / "DOC.md"
    fichero.write_text(
        f"{PREMISA_DE_PRUEBA}\n\n> **Enmienda del 2026-09-25 (F-049).** Decía «La villa se\n"
        "> crea con dos cifras.» Lo decidió el humano: `VILLA 008`.\n",
        encoding="utf-8",
    )

    _comprobar(fichero, (PREMISA_DE_PRUEBA,), ("VILLA 008",))
