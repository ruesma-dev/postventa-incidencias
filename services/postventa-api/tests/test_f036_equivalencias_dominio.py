# services/postventa-api/tests/test_f036_equivalencias_dominio.py
"""F-036 · T7: oficios casi duplicados, dominio puro (`design.md` §15).

Lo que se fija aquí: la clave de un nombre (tildes, mayúsculas, siglas,
puntuación, palabras vacías), el singular burdo, la distancia de edición, los
cuatro motivos (R78) con sus umbrales de D-22, la propuesta de grupos (cliques
frente a cadenas, R79; pares decididos fuera, R85), los grupos vigentes (última
decisión, contradicciones, R82; etiqueta, R86; todas las obras, R84) y el
discriminador `catalogo` (R95), además de la costura de proveedores de §15.8
(«cada código, su propio grupo»).

Los tres pares de oficios **medidos** en la 0677 (`progress/explore_F-036.md`)
son casos de test con sus nombres de Sigrid: los oficios no son datos
personales. Los proveedores, **inventados**.

Sin red, sin Sigrid, sin base de datos y sin configuración.
"""

from __future__ import annotations

import dataclasses
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest
from domain.models import equivalencias
from domain.models.equivalencias import (
    PALABRAS_VACIAS,
    PERFILES,
    Candidato,
    Catalogo,
    DecisionPar,
    Grupo,
    GruposVigentes,
    Motivo,
    ParPropuesto,
    Perfil,
    Propuesta,
    clave_de_nombre,
    clave_singular,
    distancia_edicion,
    grupos_de_proveedor,
    grupos_vigentes,
    motivos_del_par,
    proponer_grupos,
)

OFICIO = PERFILES[Catalogo.OFICIO]
T0 = datetime(2026, 9, 29, 10, 0, tzinfo=UTC)

# Los tres pares medidos en la 0677 (T2): código y nombre de `auxofc`.
C0046 = Candidato("0046", "Carpinteria de madera")
C0143 = Candidato("0143", "Carpintería de madera")
C0085 = Candidato("0085", "Mobiliario de cocinas")
C0166 = Candidato("0166", "Mobiliario cocina")
C0033 = Candidato("0033", "Solados y Alicatados M.O.")
C0133 = Candidato("0133", "Solados y Alicatados")
C0028 = Candidato("0028", "Pintura")
C0134 = Candidato("0134", "Fontanería")
OFICIOS_0677 = (C0046, C0143, C0085, C0166, C0033, C0133, C0028, C0134)


def _decision(
    a: str,
    b: str,
    decision: str = "mismo",
    *,
    catalogo: Catalogo = Catalogo.OFICIO,
    cuando: datetime = T0,
    obra: str = "0677",
) -> DecisionPar:
    return DecisionPar(
        catalogo=catalogo,
        codigo_a=a,
        codigo_b=b,
        decision=decision,  # type: ignore[arg-type]
        motivos=frozenset(),
        obra_codigo=obra,
        decidido_por="oid-de-prueba",
        decidido_at_utc=cuando,
    )


def _grupos(
    candidatos: tuple[Candidato, ...],
    decisiones: tuple[DecisionPar, ...] = (),
    uso: dict[str, int] | None = None,
) -> GruposVigentes:
    return grupos_vigentes(candidatos, decisiones, OFICIO, uso or {})


def _codigos(grupos: GruposVigentes) -> list[list[str]]:
    return [sorted(g.codigos) for g in grupos.grupos]


# --------------------------------------------------------------------------
# Perfil, catálogos y motivos (§15.2, R95, R96)
# --------------------------------------------------------------------------


def test_f036_perfiles_solo_oficio() -> None:
    # Quinta enmienda: el perfil de proveedores (formas jurídicas) es de F-050.
    assert list(PERFILES) == [Catalogo.OFICIO]
    assert PERFILES[Catalogo.OFICIO] == Perfil(Catalogo.OFICIO, frozenset())
    with pytest.raises(TypeError):
        PERFILES[Catalogo.PROVEEDOR] = OFICIO  # type: ignore[index]


def test_f036_r95_catalogos_con_su_valor_de_la_tabla() -> None:
    # Los valores son los del CHECK de `decisiones_equivalencia` (§6.1).
    # PROVEEDOR existe como discriminador (costura §15.8), sin perfil.
    assert [c.value for c in Catalogo] == ["oficio", "proveedor"]


def test_f036_r78_motivos_y_sus_codigos() -> None:
    assert [m.value for m in Motivo] == ["mismo_nombre", "plural", "errata", "incluido"]


def test_f036_palabras_vacias() -> None:
    assert PALABRAS_VACIAS == frozenset(
        {"de", "del", "la", "las", "el", "los", "y", "e"}
    )


# --------------------------------------------------------------------------
# a) clave_de_nombre
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("nombre", "clave"),
    [
        ("Carpintería de madera", "carpinteria madera"),
        ("Carpinteria de madera", "carpinteria madera"),
        ("CARPINTERÍA DE MADERA", "carpinteria madera"),
        ("Solados y Alicatados M.O.", "solados alicatados mo"),
        ("Solados y Alicatados M.O", "solados alicatados mo"),
        ("Solados y Alicatados", "solados alicatados"),
        ("Mobiliario de cocinas", "mobiliario cocinas"),
        ("Fontanería & Calefacción", "fontaneria calefaccion"),
        ("Albañilería", "albanileria"),
        ("  Pintura   exterior  ", "pintura exterior"),
        ("Pintura-exterior", "pintura exterior"),
        ("Pintura/exterior", "pintura exterior"),
        ("Pintura_exterior", "pintura exterior"),
        ("Pintura, (exterior).", "pintura exterior"),
        ("Distribuidor p. baja", "distribuidor p baja"),  # «p.» no es sigla
        ("Vidrio S.A.T. especial", "vidrio sat especial"),
        ("Cerrajería 2.5", "cerrajeria 2 5"),  # las cifras no son siglas
        ("El de la las los del e y", ""),
        ("", ""),
        ("...", ""),
    ],
)
def test_f036_r78_clave_de_nombre(nombre: str, clave: str) -> None:
    assert clave_de_nombre(nombre, OFICIO) == clave


def test_f036_r96_clave_quita_las_palabras_del_perfil() -> None:
    # La costura: F-050 meterá aquí las formas jurídicas sin tocar la función.
    perfil = Perfil(Catalogo.OFICIO, frozenset({"sl", "sa"}))
    assert clave_de_nombre("Pinturas Ejemplo S.L.", perfil) == "pinturas ejemplo"
    assert clave_de_nombre("Pinturas Ejemplo SA", perfil) == "pinturas ejemplo"
    assert clave_de_nombre("Pinturas Ejemplo S.L.", OFICIO) == "pinturas ejemplo sl"


# --------------------------------------------------------------------------
# b) clave_singular
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("clave", "singular"),
    [
        ("mobiliario cocinas", "mobiliario cocina"),
        ("solados alicatados", "solado alicatado"),
        ("casas", "casa"),  # cinco letras: pierde la s
        ("gris", "gris"),  # cuatro: no
        ("tres mesas", "tres mesa"),
        ("instalaciones", "instalacion"),  # consonante + es
        ("canales", "canal"),
        ("muebles", "muebl"),  # burdo a propósito (§15.2 b)
        ("bambues", "bambue"),  # vocal + es: solo la s
        ("pintura", "pintura"),
        ("mo", "mo"),
        ("", ""),
    ],
)
def test_f036_r78_clave_singular(clave: str, singular: str) -> None:
    assert clave_singular(clave) == singular


# --------------------------------------------------------------------------
# distancia_edicion
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "distancia"),
    [
        ("", "", 0),
        ("abc", "abc", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("kitten", "sitting", 3),
        ("carpinteria", "carpintaria", 1),
        ("abcd", "abdc", 2),
        ("pintura", "pinturas", 1),
        ("madera", "mader", 1),
        ("flaw", "lawn", 2),
    ],
)
def test_f036_distancia_edicion(a: str, b: str, distancia: int) -> None:
    assert distancia_edicion(a, b) == distancia
    assert distancia_edicion(b, a) == distancia


# --------------------------------------------------------------------------
# c) motivos_del_par (R78, D-22)
# --------------------------------------------------------------------------


def test_f036_r78_los_tres_pares_medidos_en_la_0677() -> None:
    assert motivos_del_par(C0046, C0143, OFICIO) == {Motivo.MISMO_NOMBRE}
    assert motivos_del_par(C0085, C0166, OFICIO) == {Motivo.PLURAL}
    assert motivos_del_par(C0033, C0133, OFICIO) == {Motivo.INCLUIDO}
    # Y el orden del par no cambia nada.
    assert motivos_del_par(C0133, C0033, OFICIO) == {Motivo.INCLUIDO}


def test_f036_r78_sin_parecido_sin_motivos() -> None:
    assert motivos_del_par(C0028, C0134, OFICIO) == frozenset()
    assert motivos_del_par(C0046, C0085, OFICIO) == frozenset()


def test_f036_r78_sin_nombre_o_sin_clave_no_hay_motivos() -> None:
    assert motivos_del_par(Candidato("1", None), Candidato("2", None), OFICIO) == set()
    assert motivos_del_par(Candidato("1", None), C0028, OFICIO) == set()
    assert motivos_del_par(C0028, Candidato("1", None), OFICIO) == set()
    # Nombres que se quedan sin clave (solo palabras vacías) no se parecen.
    assert (
        motivos_del_par(Candidato("1", "de la"), Candidato("2", "y"), OFICIO) == set()
    )


def test_f036_r78_mismo_nombre_excluye_los_demas() -> None:
    motivos = motivos_del_par(
        Candidato("1", "Instalaciones eléctricas"),
        Candidato("2", "INSTALACIONES ELECTRICAS."),
        OFICIO,
    )
    assert motivos == {Motivo.MISMO_NOMBRE}


def test_f036_r78_plural_no_es_ademas_errata() -> None:
    # «mobiliario cocinas» / «mobiliario cocina»: distancia 1 en 18, que sería
    # errata; lo explica el plural y es lo único que se dice.
    motivos = motivos_del_par(
        Candidato("1", "Mobiliario cocinas"),
        Candidato("2", "Mobiliario cocina"),
        OFICIO,
    )
    assert motivos == {Motivo.PLURAL}


@pytest.mark.parametrize(
    ("a", "b", "errata"),
    [
        ("pavimentos", "pavimentas", True),  # 1 en 10: 10 %
        ("carpinter", "carpintar", False),  # 1 en 9: 11 %
        ("abcdefghijklmnopqrst", "abcdefghijklmnopqrxx", True),  # 2 en 20: 10 %
        ("abcdefghijklmnopqrs", "abcdefghijklmnopqxx", False),  # 2 en 19
        (
            "abcdefghijklmnopqrstuvwxyzabcd",
            "abcdefghijklmnopqrstuvwxyzaxxx",
            False,
        ),  # 3
        ("pavimentos exteriores", "pavimentos exterioras", True),
    ],
)
def test_f036_r78_d22_errata_y_sus_bordes(a: str, b: str, errata: bool) -> None:
    motivos = motivos_del_par(Candidato("1", a), Candidato("2", b), OFICIO)
    assert (Motivo.ERRATA in motivos) is errata


def test_f036_d22_errata_minimo_de_ocho_caracteres(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Con el 10 % de D-22 el mínimo de 8 nunca decide (con distancia 1 la
    # larga tiene ≥ 10); se prueba sin ese tope para que no quede sin vigilar
    # si T9 cambia el porcentaje.
    monkeypatch.setattr(equivalencias, "ERRATA_MAX_PORCENTAJE", 100)
    ocho = motivos_del_par(
        Candidato("1", "abcdefgh"), Candidato("2", "abcdefgx"), OFICIO
    )
    siete = motivos_del_par(
        Candidato("1", "abcdefg"), Candidato("2", "abcdefx"), OFICIO
    )
    assert Motivo.ERRATA in ocho
    assert Motivo.ERRATA not in siete


@pytest.mark.parametrize(
    ("a", "b", "incluido"),
    [
        ("Solados y Alicatados", "Solados y Alicatados M.O.", True),
        ("Pintura exterior", "Pintura exterior e interior", True),
        ("Pintura", "Pintura exterior", False),  # la corta, de una palabra
        ("Pintura exterior", "Pintura exteriores lisas", False),  # no es por palabras
        ("Mobiliario cocina", "Mobiliario cocinas", False),  # misma longitud
        ("exterior Pintura", "Pintura exterior e interior", False),  # el principio
    ],
)
def test_f036_r78_d22_incluido(a: str, b: str, incluido: bool) -> None:
    assert (
        Motivo.INCLUIDO in motivos_del_par(Candidato("1", a), Candidato("2", b), OFICIO)
    ) is incluido
    assert (
        Motivo.INCLUIDO in motivos_del_par(Candidato("2", b), Candidato("1", a), OFICIO)
    ) is incluido


def test_f036_r78_incluido_y_errata_a_la_vez() -> None:
    # Los motivos son un conjunto: un par puede tener más de uno.
    motivos = motivos_del_par(
        Candidato("1", "Revestimientos continuos"),
        Candidato("2", "Revestimientos continuos pétreos"),
        OFICIO,
    )
    assert motivos == {Motivo.INCLUIDO}
    motivos = motivos_del_par(
        Candidato("1", "Revestimientos continuos"),
        Candidato("2", "Revestimientos continuos a"),
        OFICIO,
    )
    assert motivos == {Motivo.INCLUIDO, Motivo.ERRATA}


# --------------------------------------------------------------------------
# d) proponer_grupos (R78, R79, R80, R85)
# --------------------------------------------------------------------------


def test_f036_r78_propuestas_de_la_0677() -> None:
    propuestas = proponer_grupos(OFICIOS_0677, (), OFICIO)
    assert propuestas == (
        Propuesta(
            catalogo=Catalogo.OFICIO,
            codigos=("0033", "0133"),
            pares=(ParPropuesto("0033", "0133", frozenset({Motivo.INCLUIDO})),),
            por_pares=False,
        ),
        Propuesta(
            catalogo=Catalogo.OFICIO,
            codigos=("0046", "0143"),
            pares=(ParPropuesto("0046", "0143", frozenset({Motivo.MISMO_NOMBRE})),),
            por_pares=False,
        ),
        Propuesta(
            catalogo=Catalogo.OFICIO,
            codigos=("0085", "0166"),
            pares=(ParPropuesto("0085", "0166", frozenset({Motivo.PLURAL})),),
            por_pares=False,
        ),
    )
    assert propuestas[0].motivos == {Motivo.INCLUIDO}


def test_f036_r78_propuestas_deterministas() -> None:
    uno = proponer_grupos(OFICIOS_0677, (), OFICIO)
    otro = proponer_grupos(tuple(reversed(OFICIOS_0677)), (), OFICIO)
    assert uno == otro


def test_f036_r79_clique_de_tres_es_un_grupo() -> None:
    candidatos = (
        Candidato("0003", "Pintura exterior"),
        Candidato("0001", "Pintura Exterior"),
        Candidato("0002", "Pinturas exteriores"),
        Candidato("0009", "Fontanería"),
    )
    (propuesta,) = proponer_grupos(candidatos, (), OFICIO)
    assert propuesta.codigos == ("0001", "0002", "0003")
    assert propuesta.por_pares is False
    assert [(p.codigo_a, p.codigo_b) for p in propuesta.pares] == [
        ("0001", "0002"),
        ("0001", "0003"),
        ("0002", "0003"),
    ]
    assert propuesta.pares[1].motivos == {Motivo.MISMO_NOMBRE}
    assert propuesta.motivos == {Motivo.MISMO_NOMBRE, Motivo.PLURAL}


def test_f036_r79_cadena_se_propone_por_pares() -> None:
    # A ~ B (incluido) y A ~ C (plural), pero B y C no se parecen: ante la
    # duda, separadas.
    candidatos = (
        Candidato("A", "Tabiqueria seca"),
        Candidato("B", "Tabiqueria seca placa"),
        Candidato("C", "Tabiquería secas"),
    )
    propuestas = proponer_grupos(candidatos, (), OFICIO)
    # A–B incluido, A–C plural, B–C nada: no es clique.
    assert motivos_del_par(candidatos[1], candidatos[2], OFICIO) == set()
    assert [p.codigos for p in propuestas] == [("A", "B"), ("A", "C")]
    assert all(p.por_pares for p in propuestas)
    assert all(len(p.pares) == 1 for p in propuestas)


def test_f036_r85_par_decidido_no_se_vuelve_a_proponer() -> None:
    for decision in ("mismo", "distinto"):
        propuestas = proponer_grupos(
            OFICIOS_0677, (_decision("0046", "0143", decision),), OFICIO
        )
        assert [p.codigos for p in propuestas] == [("0033", "0133"), ("0085", "0166")]


def test_f036_r85_par_decidido_rompe_el_clique() -> None:
    # Con 0001–0003 decidido, lo que queda (0001–0002, 0002–0003) ya no es un
    # clique: se propone por pares.
    candidatos = (
        Candidato("0001", "Pintura Exterior"),
        Candidato("0002", "Pinturas exteriores"),
        Candidato("0003", "Pintura exterior"),
    )
    propuestas = proponer_grupos(candidatos, (_decision("0001", "0003"),), OFICIO)
    assert [p.codigos for p in propuestas] == [("0001", "0002"), ("0002", "0003")]
    assert all(p.por_pares for p in propuestas)


def test_f036_r95_decision_de_otro_catalogo_no_cuenta() -> None:
    # Un proveedor con los mismos códigos que un par de oficios no lo decide.
    otra = _decision("0046", "0143", catalogo=Catalogo.PROVEEDOR)
    propuestas = proponer_grupos(OFICIOS_0677, (otra,), OFICIO)
    assert ("0046", "0143") in [p.codigos for p in propuestas]


def test_f036_r78_sin_nombre_no_se_propone() -> None:
    candidatos = (Candidato("1", None), Candidato("2", None), Candidato("3", "Pintura"))
    assert proponer_grupos(candidatos, (), OFICIO) == ()


def test_f036_r78_codigo_repetido_cuenta_una_vez() -> None:
    candidatos = (C0046, C0046, C0143)
    (propuesta,) = proponer_grupos(candidatos, (), OFICIO)
    assert propuesta.codigos == ("0046", "0143")


def test_f036_r78_sin_candidatos() -> None:
    assert proponer_grupos((), (), OFICIO) == ()


def test_f036_r80_proponer_no_agrupa() -> None:
    # La propuesta sola no cambia los grupos vigentes.
    assert proponer_grupos(OFICIOS_0677, (), OFICIO)
    grupos = _grupos(OFICIOS_0677)
    assert all(len(g.codigos) == 1 for g in grupos.grupos)


# --------------------------------------------------------------------------
# DecisionPar
# --------------------------------------------------------------------------


def test_f036_r95_decision_par_en_orden_y_con_decision_valida() -> None:
    assert _decision("0046", "0143").codigo_a == "0046"
    with pytest.raises(ValueError):
        _decision("0143", "0046")
    with pytest.raises(ValueError):
        _decision("0046", "0046")
    with pytest.raises(ValueError):
        _decision("0046", "0143", "quizá")
    assert _decision("0046", "0143", "distinto").decision == "distinto"


# --------------------------------------------------------------------------
# grupos_vigentes (R81, R82, R84, R86, R95)
# --------------------------------------------------------------------------


def test_f036_r82_sin_decisiones_cada_codigo_es_su_grupo() -> None:
    grupos = _grupos((C0143, C0046, C0028))
    assert grupos.catalogo is Catalogo.OFICIO
    assert grupos.grupos == (
        Grupo(Catalogo.OFICIO, frozenset({"0028"}), "Pintura"),
        Grupo(Catalogo.OFICIO, frozenset({"0046"}), "Carpinteria de madera"),
        Grupo(Catalogo.OFICIO, frozenset({"0143"}), "Carpintería de madera"),
    )
    assert grupos.no_aplicados == ()


def test_f036_r82_mismo_une_y_la_cadena_tambien() -> None:
    candidatos = (C0046, C0143, Candidato("0200", "Carpintería madera"), C0028)
    decisiones = (_decision("0046", "0143"), _decision("0143", "0200"))
    grupos = _grupos(candidatos, decisiones)
    assert _codigos(grupos) == [["0028"], ["0046", "0143", "0200"]]


def test_f036_r82_componente_con_distinto_no_se_aplica_y_avisa() -> None:
    candidatos = (C0046, C0143, Candidato("0200", "Carpintería madera"), C0028)
    decisiones = (
        _decision("0046", "0143"),
        _decision("0143", "0200"),
        _decision("0046", "0200", "distinto"),
    )
    grupos = _grupos(candidatos, decisiones)
    assert _codigos(grupos) == [["0028"], ["0046"], ["0143"], ["0200"]]
    assert grupos.no_aplicados == (frozenset({"0046", "0143", "0200"}),)


def test_f036_r82_distinto_entre_grupos_distintos_no_estorba() -> None:
    decisiones = (_decision("0033", "0133"), _decision("0046", "0133", "distinto"))
    grupos = _grupos((C0033, C0133, C0046), decisiones)
    assert _codigos(grupos) == [["0033", "0133"], ["0046"]]
    assert grupos.no_aplicados == ()


def test_f036_r81_manda_la_ultima_decision() -> None:
    separar = (
        _decision("0046", "0143"),
        _decision("0046", "0143", "distinto", cuando=T0 + timedelta(minutes=1)),
    )
    assert _codigos(_grupos((C0046, C0143), separar)) == [["0046"], ["0143"]]
    # Separar un par no es una contradicción: su última decisión es «distinto».
    assert _grupos((C0046, C0143), separar).no_aplicados == ()
    volver = (
        _decision("0046", "0143", "distinto"),
        _decision("0046", "0143", cuando=T0 + timedelta(minutes=1)),
    )
    assert _codigos(_grupos((C0046, C0143), volver)) == [["0046", "0143"]]
    # El orden en que llegan no importa: manda la fecha.
    assert _codigos(_grupos((C0046, C0143), tuple(reversed(separar)))) == [
        ["0046"],
        ["0143"],
    ]


def test_f036_r81_a_igual_fecha_manda_la_ultima_que_llega() -> None:
    empate = (_decision("0046", "0143"), _decision("0046", "0143", "distinto"))
    assert _codigos(_grupos((C0046, C0143), empate)) == [["0046"], ["0143"]]
    empate = (_decision("0046", "0143", "distinto"), _decision("0046", "0143"))
    assert _codigos(_grupos((C0046, C0143), empate)) == [["0046", "0143"]]


def test_f036_r95_decisiones_de_otro_catalogo_no_agrupan() -> None:
    decisiones = (_decision("0046", "0143", catalogo=Catalogo.PROVEEDOR),)
    assert _codigos(_grupos((C0046, C0143), decisiones)) == [["0046"], ["0143"]]


def test_f036_r84_decision_de_otra_obra_vale_aqui() -> None:
    decisiones = (_decision("0046", "0143", obra="0999"),)
    assert _codigos(_grupos((C0046, C0143), decisiones)) == [["0046", "0143"]]


def test_f036_r84_grupo_con_un_codigo_de_fuera_de_la_obra() -> None:
    # 0143 está en la obra; 0999 no, pero se decidió desde otra obra que son el
    # mismo: el grupo lo lleva y la obra solo tiene uno de sus códigos.
    grupos = _grupos((C0143, C0028), (_decision("0143", "0999"),))
    assert _codigos(grupos) == [["0028"], ["0143", "0999"]]
    assert grupos.grupos[1].etiqueta == "Carpintería de madera"


def test_f036_r84_grupos_sin_ningun_codigo_de_la_obra_no_salen() -> None:
    decisiones = (
        _decision("0997", "0998"),
        _decision("0998", "0999"),
        _decision("0997", "0999", "distinto"),
        _decision("0990", "0991"),
    )
    grupos = _grupos((C0028,), decisiones)
    assert _codigos(grupos) == [["0028"]]
    assert grupos.no_aplicados == ()


def test_f036_r86_etiqueta_del_miembro_con_mas_filas() -> None:
    decisiones = (_decision("0046", "0143"),)
    grupo = _grupos((C0046, C0143), decisiones, {"0046": 1, "0143": 3}).grupos[0]
    assert grupo.etiqueta == "Carpintería de madera"
    grupo = _grupos((C0046, C0143), decisiones, {"0046": 2, "0143": 1}).grupos[0]
    assert grupo.etiqueta == "Carpinteria de madera"


def test_f036_r86_sin_filas_en_la_obra_cuenta_cero() -> None:
    # 0046 no tiene filas; 0143, una: manda 0143 aunque su código sea mayor.
    grupo = _grupos((C0046, C0143), (_decision("0046", "0143"),), {"0143": 1}).grupos[0]
    assert grupo.etiqueta == "Carpintería de madera"


def test_f036_r86_a_igualdad_el_de_codigo_menor() -> None:
    decisiones = (_decision("0046", "0143"),)
    grupo = _grupos((C0143, C0046), decisiones, {"0046": 2, "0143": 2}).grupos[0]
    assert grupo.etiqueta == "Carpinteria de madera"
    grupo = _grupos((C0143, C0046), decisiones).grupos[0]
    assert grupo.etiqueta == "Carpinteria de madera"


def test_f036_r86_etiqueta_recortada_o_el_codigo() -> None:
    grupos = _grupos(
        (
            Candidato("0001", "  Pintura  "),
            Candidato("0002", None),
            Candidato("0003", " "),
        )
    )
    assert [g.etiqueta for g in grupos.grupos] == ["Pintura", "0002", "0003"]


def test_f036_r86_el_de_mas_filas_sin_nombre_da_su_codigo() -> None:
    decisiones = (_decision("0001", "0002"),)
    grupo = _grupos(
        (Candidato("0001", "Pintura"), Candidato("0002", None)), decisiones, {"0002": 5}
    ).grupos[0]
    assert grupo.etiqueta == "0002"


def test_f036_grupos_vigentes_deterministas() -> None:
    decisiones = (_decision("0046", "0143"), _decision("0033", "0133"))
    uno = _grupos(OFICIOS_0677, decisiones)
    otro = _grupos(tuple(reversed(OFICIOS_0677)), tuple(reversed(decisiones)))
    assert uno == otro


def test_f036_grupo_de() -> None:
    grupos = _grupos((C0046, C0143, C0028), (_decision("0046", "0143"),))
    assert grupos.grupo_de("0143").codigos == {"0046", "0143"}
    assert grupos.grupo_de("0028").etiqueta == "Pintura"
    with pytest.raises(ValueError):
        grupos.grupo_de("9999")


def test_f036_grupos_vigentes_rechaza_grupos_incoherentes() -> None:
    oficio = Grupo(Catalogo.OFICIO, frozenset({"1"}), "Uno")
    with pytest.raises(ValueError):
        GruposVigentes(
            catalogo=Catalogo.OFICIO,
            grupos=(oficio, Grupo(Catalogo.PROVEEDOR, frozenset({"2"}), "Dos")),
            no_aplicados=(),
        )
    with pytest.raises(ValueError):
        GruposVigentes(
            catalogo=Catalogo.OFICIO,
            grupos=(oficio, Grupo(Catalogo.OFICIO, frozenset({"1", "3"}), "Otro")),
            no_aplicados=(),
        )
    with pytest.raises(ValueError):
        GruposVigentes(
            catalogo=Catalogo.OFICIO,
            grupos=(Grupo(Catalogo.OFICIO, frozenset(), "Vacío"),),
            no_aplicados=(),
        )
    GruposVigentes(catalogo=Catalogo.OFICIO, grupos=(oficio,), no_aplicados=())


# --------------------------------------------------------------------------
# §15.8 · la costura de proveedores: cada código, su propio grupo
# --------------------------------------------------------------------------


def test_f036_costura_grupos_de_proveedor_cada_codigo_su_grupo() -> None:
    grupos = grupos_de_proveedor(
        (
            Candidato("P2", "Juan Ejemplo Ejemplo"),
            Candidato("P1", " Carpinterías Ejemplo S.L. "),
            Candidato("P2", "Juan Ejemplo Ejemplo"),  # el mismo, con otro oficio
            Candidato("P3", None),
            Candidato("P4", "Pinturas Ejemplo S.A."),
            Candidato("P5", "Pinturas Ejemplo SA"),  # parecido: NO se agrupa
        )
    )
    assert grupos.catalogo is Catalogo.PROVEEDOR
    assert grupos.grupos == (
        Grupo(Catalogo.PROVEEDOR, frozenset({"P1"}), "Carpinterías Ejemplo S.L."),
        Grupo(Catalogo.PROVEEDOR, frozenset({"P2"}), "Juan Ejemplo Ejemplo"),
        Grupo(Catalogo.PROVEEDOR, frozenset({"P3"}), "P3"),
        Grupo(Catalogo.PROVEEDOR, frozenset({"P4"}), "Pinturas Ejemplo S.A."),
        Grupo(Catalogo.PROVEEDOR, frozenset({"P5"}), "Pinturas Ejemplo SA"),
    )
    assert grupos.no_aplicados == ()


def test_f036_r95_un_codigo_de_oficio_y_otro_de_proveedor_iguales_no_se_confunden() -> (
    None
):
    oficios = _grupos((Candidato("0001", "Pintura"),))
    proveedores = grupos_de_proveedor((Candidato("0001", "Pintura"),))
    assert oficios.grupo_de("0001") != proveedores.grupo_de("0001")
    assert oficios.grupo_de("0001").etiqueta == proveedores.grupo_de("0001").etiqueta


# --------------------------------------------------------------------------
# Inmutabilidad y pureza
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "clase",
    [
        m
        for m in vars(equivalencias).values()
        if isinstance(m, type)
        and dataclasses.is_dataclass(m)
        and m.__module__ == equivalencias.__name__
    ],
    ids=lambda c: c.__name__,
)
def test_f036_estructuras_de_equivalencias_inmutables(clase: type) -> None:
    assert clase.__dataclass_params__.frozen  # type: ignore[attr-defined]


def test_f036_propuesta_inmutable() -> None:
    (propuesta, *_) = proponer_grupos(OFICIOS_0677, (), OFICIO)
    with pytest.raises(FrozenInstanceError):
        propuesta.codigos = ()  # type: ignore[misc]
