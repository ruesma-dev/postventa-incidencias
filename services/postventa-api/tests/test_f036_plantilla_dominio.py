# services/postventa-api/tests/test_f036_plantilla_dominio.py
"""F-036 · T4: el contrato de la plantilla, dominio puro (`design.md` §4.1).

Lo que se fija aquí es lo que **no puede moverse sin que se rompa la
importación**: el identificador y la versión que reconoce el importador, la
cabecera exacta, los topes, los códigos de las enumeraciones (que la base y el
YAML repiten), el código de obra admisible (R9) y las etiquetas de las unidades
(R8), que son lo que el importador compara carácter a carácter con lo que trae
cada fila.

Sin red, sin Sigrid y sin configuración. Las unidades de la obra piloto son las
**medidas** en T2 (`progress/explore_F-036.md`): «Viviendas Bloque Villa N»,
sin nombres de persona. Las demás son inventadas.

T7 añade `opciones_de_oficio` y `opciones_de_proveedor` (R71, R72, R86, R92):
los desplegables de `Oficio` y `Proveedor` calculados desde el catálogo de la
obra y los grupos vigentes, con los tres pares de oficios medidos en la 0677.
Los proveedores son **inventados**.
"""

from __future__ import annotations

import ast
import dataclasses
from collections import Counter
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path

import pytest
from domain.models import equivalencias, plantilla_incidencias
from domain.models.equivalencias import (
    PERFILES,
    Candidato,
    Catalogo,
    DecisionPar,
    Grupo,
    GruposVigentes,
    grupos_de_proveedor,
    grupos_vigentes,
)
from domain.models.errores import (
    CODIGOS_FICHERO_NO_ES_PLANTILLA,
    CatalogoNoDisponible,
    CatalogoSinVerificar,
    CodigoDeObraInvalido,
    CodigoNoEsDeLaObra,
    FicheroDemasiadoGrande,
    FicheroNoEsPlantilla,
    ObraAmbigua,
    ObraSinUnidades,
    PeticionDeDecisionInvalida,
    PeticionDeImportacionInvalida,
)
from domain.models.importacion import Elegido, resolver_oficio_y_proveedor
from domain.models.plantilla_incidencias import (
    CABECERA,
    COLUMNA_ERRORES,
    IDENTIFICADOR_PLANTILLA,
    MAX_CODIGO_OBRA,
    MAX_DESCRIPCION,
    MAX_DETALLE,
    MAX_FILAS,
    MAX_UBICACION,
    SEPARADOR_PAR,
    VERSION_PLANTILLA,
    VERSIONES_SOPORTADAS,
    CatalogoObra,
    Listado,
    ListasCerradas,
    OficioObra,
    Opcion,
    OpcionOficio,
    OpcionProveedor,
    OrigenIncidencia,
    ProveedorEnObra,
    UnidadPosventa,
    Urgencia,
    etiquetas_de_unidades,
    normalizar_codigo_obra,
    normalizar_para_clave,
    opciones_de_oficio,
    opciones_de_proveedor,
)

RAIZ = Path(__file__).resolve().parents[1]
MODULOS_PUROS = (
    RAIZ / "domain" / "models" / "plantilla_incidencias.py",
    RAIZ / "domain" / "models" / "equivalencias.py",
)

# Las 15 unidades de la 0677, tal y como las midió T2 (código y `con.res`).
UNIDADES_0677 = tuple(
    UnidadPosventa(codigo=f"0677.03VILLA {n}.", nombre=f"Viviendas Bloque Villa {n}")
    for n in range(1, 16)
)


# --------------------------------------------------------------------------
# Constantes del contrato
# --------------------------------------------------------------------------


def test_f036_r2_cabecera_exacta_y_en_orden() -> None:
    assert CABECERA == (
        "Unidad",
        "Ubicación",
        "Descripción corta",
        "Detalle",
        "Oficio",
        "Proveedor",
        "Urgencia",
        "Listado",
        "Errores (lo rellena el sistema)",
    )
    assert CABECERA[-1] == COLUMNA_ERRORES


def test_f036_r6_r18_identificador_y_version() -> None:
    assert (
        IDENTIFICADOR_PLANTILLA == "ruesma.postventa-incidencias.plantilla-incidencias"
    )
    assert VERSION_PLANTILLA == 1
    assert VERSIONES_SOPORTADAS == frozenset({1})
    assert VERSION_PLANTILLA in VERSIONES_SOPORTADAS


def test_f036_topes_de_design_4_1() -> None:
    # 128: con.res y `descripcion` de §8.9; 48: rcp.resubi; 2000: D-11;
    # 1000 filas: D-11; 24: `obra` de §8.9.
    assert (
        MAX_DESCRIPCION,
        MAX_UBICACION,
        MAX_DETALLE,
        MAX_FILAS,
        MAX_CODIGO_OBRA,
    ) == (
        128,
        48,
        2000,
        1000,
        24,
    )
    assert SEPARADOR_PAR == " · "


def test_f036_enumeraciones_con_sus_codigos() -> None:
    # Los códigos los repiten el YAML (T6) y los CHECK de la base (T14).
    assert [u.value for u in Urgencia] == ["urgente", "seguridad"]
    assert [x.value for x in Listado] == ["primero", "segundo"]
    assert [o.value for o in OrigenIncidencia] == ["excel", "web"]


def test_f036_estructuras_inmutables() -> None:
    unidad = UnidadPosventa(codigo="U1", nombre="Uno")
    with pytest.raises(FrozenInstanceError):
        unidad.codigo = "U2"  # type: ignore[misc]
    catalogo = CatalogoObra(
        obra_codigo="0677",
        obra_nombre=None,
        unidades=(unidad,),
        oficios=(OficioObra(codigo="0028", nombre="Pintura"),),
        proveedores=(
            ProveedorEnObra(
                oficio_codigo="0028", proveedor_codigo=None, proveedor_nombre=None
            ),
        ),
    )
    with pytest.raises(FrozenInstanceError):
        catalogo.obra_codigo = "0678"  # type: ignore[misc]
    listas = ListasCerradas(ubicaciones=("Cocina",), urgencias=(), listados=())
    with pytest.raises(FrozenInstanceError):
        listas.ubicaciones = ()  # type: ignore[misc]


def test_f036_opciones_de_oficio_y_proveedor_se_construyen_a_mano() -> None:
    # T5 las usa construidas a mano; T7 escribe las funciones que las calculan.
    grupo = Grupo(
        catalogo=Catalogo.OFICIO,
        codigos=frozenset({"0046", "0143"}),
        etiqueta="Carpintería de madera",
    )
    oficio = OpcionOficio(
        etiqueta="Carpintería de madera", grupo=grupo, codigos_en_obra=("0046", "0143")
    )
    par = OpcionProveedor(
        etiqueta="Carpintería de madera · Carpinterías Ejemplo S.L.",
        oficio=oficio,
        grupo=Grupo(
            catalogo=Catalogo.PROVEEDOR,
            codigos=frozenset({"P1"}),
            etiqueta="Carpinterías Ejemplo S.L.",
        ),
        filas_en_obra=(("0046", "P1"),),
    )
    assert par.oficio is oficio
    assert Catalogo.OFICIO.value == "oficio"
    # T7: PROVEEDOR como discriminador, sin perfil (costura de §15.8).
    assert [c.value for c in Catalogo] == ["oficio", "proveedor"]
    with pytest.raises(FrozenInstanceError):
        grupo.etiqueta = "otra"  # type: ignore[misc]


# --------------------------------------------------------------------------
# R9 · el código de obra
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("bruto", "esperado"),
    [
        ("0677", "0677"),
        (" 0677 ", "0677"),
        ("06 77", "0677"),  # F-032: un espacio no es parte del código
        ("06\t77\n", "0677"),
        ("06\u00a077", "0677"),
        ("RS26.09-0178", "RS26.09-0178"),
        ("06\u201377", "06-77"),  # guion raro → normal (nombrado.normalizar_codigo)
        ("a_B.c-9", "a_B.c-9"),
        ("X" * 24, "X" * 24),
    ],
)
def test_f036_r9_codigo_de_obra_admisible(bruto: str, esperado: str) -> None:
    assert normalizar_codigo_obra(bruto) == esperado


@pytest.mark.parametrize(
    "bruto",
    [
        None,
        "",
        "   ",
        "X" * 25,  # pasa de 24
        " " + "X" * 25,
        "06/77",  # `/` fuera de [0-9A-Za-z._-]
        "0677;",
        "0677ñ",
        "0677\u200b",  # ancho cero: no es blanco para Python (D3 de F-032)
        677,  # no es texto
        6.77,
        ["0677"],
    ],
)
def test_f036_r9_codigo_de_obra_invalido(bruto: object) -> None:
    with pytest.raises(CodigoDeObraInvalido) as exc:
        normalizar_codigo_obra(bruto)
    # El mensaje no repite lo que llegó: puede ser cualquier cosa.
    assert "0677" not in str(exc.value)
    assert exc.value.motivo == str(exc.value)


def test_f036_r9_codigo_de_obra_veinticuatro_tras_quitar_espacios() -> None:
    # 25 caracteres con un espacio dentro son 24 de código: se admite.
    assert normalizar_codigo_obra("X" * 12 + " " + "X" * 12) == "X" * 24


# --------------------------------------------------------------------------
# R35 · normalización solo para la clave de duplicado
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Sellar sifón", "sellar sifon"),
        ("Sellar sifon.", "sellar sifon"),
        ("  SELLAR   SIFÓN  ", "sellar sifon"),
        ("Sellar\nsifón", "sellar sifon"),
        ("Sellar sifón.,;:", "sellar sifon"),
        ("Sellar sifón . ,", "sellar sifon"),
        ("Sellar sifón!", "sellar sifon!"),  # solo . , ; : al final
        ("Sellar, sifón", "sellar, sifon"),  # la de dentro se queda
        ("Baño\x1fplanta", "bano planta"),  # el separador de la clave no sobrevive
        ("Pingüino ÑANDÚ", "pinguino nandu"),
        ("", ""),
        ("...", ""),
    ],
)
def test_f036_r35_normalizar_para_clave(texto: str, esperado: str) -> None:
    assert normalizar_para_clave(texto) == esperado
    assert "\x1f" not in normalizar_para_clave(texto)


# --------------------------------------------------------------------------
# R8 · etiquetas de las unidades
# --------------------------------------------------------------------------


def test_f036_r8_unidades_de_la_0677() -> None:
    opciones = etiquetas_de_unidades(UNIDADES_0677)
    # Ordenadas por código (texto): «VILLA 1.», «VILLA 10.», … «VILLA 15.», «VILLA 2.»…
    assert [o.codigo for o in opciones] == sorted(u.codigo for u in UNIDADES_0677)
    assert opciones[0] == Opcion(
        etiqueta="Viviendas Bloque Villa 1", codigo="0677.03VILLA 1."
    )
    assert {o.etiqueta for o in opciones} == {
        f"Viviendas Bloque Villa {n}" for n in range(1, 16)
    }
    assert len(opciones) == 15


def test_f036_r8_nombre_recortado() -> None:
    opciones = etiquetas_de_unidades(
        [UnidadPosventa(codigo="U1", nombre="  Villa 1  ")]
    )
    assert opciones == (Opcion(etiqueta="Villa 1", codigo="U1"),)


def test_f036_r8_orden_por_codigo_no_por_nombre() -> None:
    unidades = [
        UnidadPosventa(codigo="B", nombre="Alfa"),
        UnidadPosventa(codigo="A", nombre="Beta"),
        UnidadPosventa(codigo="C", nombre="Gamma"),
    ]
    assert [o.codigo for o in etiquetas_de_unidades(unidades)] == ["A", "B", "C"]


def test_f036_r8_colision_de_nombre_normalizado() -> None:
    unidades = [
        UnidadPosventa(codigo="U2", nombre="Villa Ñ"),
        UnidadPosventa(codigo="U1", nombre="villa  n"),
        UnidadPosventa(codigo="U3", nombre="Otra"),
    ]
    assert etiquetas_de_unidades(unidades) == (
        Opcion(etiqueta="villa  n (U1)", codigo="U1"),
        Opcion(etiqueta="Villa Ñ (U2)", codigo="U2"),
        Opcion(etiqueta="Otra", codigo="U3"),
    )


def test_f036_r8_colision_de_tres() -> None:
    unidades = [UnidadPosventa(codigo=c, nombre="Local") for c in ("L3", "L1", "L2")]
    assert [o.etiqueta for o in etiquetas_de_unidades(unidades)] == [
        "Local (L1)",
        "Local (L2)",
        "Local (L3)",
    ]


@pytest.mark.parametrize("vacio", [None, "", "   "])
def test_f036_r8_nombre_vacio_da_el_codigo(vacio: str | None) -> None:
    unidades = [
        UnidadPosventa(codigo="U1", nombre=vacio),
        UnidadPosventa(codigo="U2", nombre="Villa 2"),
    ]
    assert etiquetas_de_unidades(unidades) == (
        Opcion(etiqueta="U1", codigo="U1"),
        Opcion(etiqueta="Villa 2", codigo="U2"),
    )


def test_f036_r8_nombre_vacio_frente_a_un_nombre_igual_a_su_codigo() -> None:
    # La unidad sin nombre se enseña con su código; si otra se llama así, las
    # dos chocarían: la que tiene nombre gana su código entre paréntesis.
    unidades = [
        UnidadPosventa(codigo="U1", nombre=None),
        UnidadPosventa(codigo="U2", nombre="u1"),
    ]
    etiquetas = etiquetas_de_unidades(unidades)
    assert etiquetas == (
        Opcion(etiqueta="U1", codigo="U1"),
        Opcion(etiqueta="u1 (U2)", codigo="U2"),
    )


def test_f036_r8_etiquetas_siempre_distintas() -> None:
    unidades = [
        UnidadPosventa(codigo="A", nombre="Casa"),
        UnidadPosventa(codigo="B", nombre="CASA"),
        UnidadPosventa(codigo="C", nombre=None),
        UnidadPosventa(codigo="D", nombre="c"),
        UnidadPosventa(codigo="E", nombre="Casá"),
    ]
    etiquetas = [o.etiqueta for o in etiquetas_de_unidades(unidades)]
    assert len(set(etiquetas)) == len(etiquetas)
    assert etiquetas == ["Casa (A)", "CASA (B)", "C", "c (D)", "Casá (E)"]


def test_f036_r8_determinista() -> None:
    unidades = list(UNIDADES_0677) + [UnidadPosventa(codigo="0677.99", nombre=None)]
    primera = etiquetas_de_unidades(unidades)
    assert etiquetas_de_unidades(reversed(unidades)) == primera
    assert etiquetas_de_unidades(tuple(unidades)) == primera
    assert isinstance(primera, tuple)


def test_f036_r8_sin_unidades() -> None:
    assert etiquetas_de_unidades([]) == ()


# --------------------------------------------------------------------------
# §4.6 · errores nuevos
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "clase",
    [
        CodigoDeObraInvalido,
        PeticionDeImportacionInvalida,
        FicheroDemasiadoGrande,
        ObraSinUnidades,
        ObraAmbigua,
        CatalogoSinVerificar,
        CatalogoNoDisponible,
        PeticionDeDecisionInvalida,
        CodigoNoEsDeLaObra,
    ],
)
def test_f036_errores_llevan_su_motivo(clase: type[Exception]) -> None:
    error = clase("algo concreto")
    assert error.motivo == "algo concreto"  # type: ignore[attr-defined]
    assert str(error) == "algo concreto"


def test_f036_fichero_no_es_plantilla_lleva_codigo_y_motivo() -> None:
    assert CODIGOS_FICHERO_NO_ES_PLANTILLA == frozenset(
        {
            "no_es_xlsx",
            "contiene_macros",
            "fichero_sospechoso",
            "no_es_la_plantilla",
            "formato_antiguo",
            "version_no_soportada",
            "cabecera_distinta",
            "demasiadas_filas",
            "obra_invalida",
        }
    )
    error = FicheroNoEsPlantilla("formato_antiguo", "Ese formato ya no se admite.")
    assert error.codigo == "formato_antiguo"
    assert error.motivo == "Ese formato ya no se admite."
    assert str(error) == "formato_antiguo: Ese formato ya no se admite."


def test_f036_fichero_no_es_plantilla_rechaza_un_codigo_fuera_de_la_lista() -> None:
    with pytest.raises(ValueError, match="no_es_un_codigo"):
        FicheroNoEsPlantilla("no_es_un_codigo", "x")


# --------------------------------------------------------------------------
# Dominio puro
# --------------------------------------------------------------------------


@pytest.mark.parametrize("modulo", MODULOS_PUROS, ids=lambda p: p.name)
def test_f036_modulos_de_dominio_puros(modulo: Path) -> None:
    texto = modulo.read_text(encoding="utf-8")
    assert (
        texto.splitlines()[0] == f"# services/postventa-api/domain/models/{modulo.name}"
    )
    importados: set[str] = set()
    for nodo in ast.walk(ast.parse(texto)):
        if isinstance(nodo, ast.Import):
            importados.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module.split(".")[0])
    prohibidos = {"openpyxl", "httpx", "psycopg", "requests", "yaml"}
    assert not importados & prohibidos
    assert importados <= {
        "__future__",
        "collections",
        "dataclasses",
        "enum",
        "re",
        "unicodedata",
        "domain",
        "hashlib",
        "uuid",
        "datetime",
        "types",
        "typing",
    }


@pytest.mark.parametrize(
    "clase",
    [
        m
        for modulo in (plantilla_incidencias, equivalencias)
        for m in vars(modulo).values()
        if isinstance(m, type)
        and dataclasses.is_dataclass(m)
        and m.__module__ == modulo.__name__
    ],
    ids=lambda c: c.__name__,
)
def test_f036_todas_las_estructuras_del_contrato_son_inmutables(clase: type) -> None:
    assert clase.__dataclass_params__.frozen  # type: ignore[attr-defined]


# --------------------------------------------------------------------------
# T7 · R92, R86 · las opciones de `Oficio`
# --------------------------------------------------------------------------

# Oficios de la 0677 medidos en T2 (dos de los tres pares) y filas de `obrofc`
# con proveedores inventados. 0166 está en la obra sin proveedor, como allí.
OFICIOS = (
    OficioObra("0143", "Carpintería de madera"),
    OficioObra("0046", "Carpinteria de madera"),
    OficioObra("0028", "Pintura"),
    OficioObra("0166", "Mobiliario cocina"),
    OficioObra("0085", "Mobiliario de cocinas"),
)
FILAS = (
    ProveedorEnObra("0046", "P1", "Carpinterías Ejemplo S.L."),
    ProveedorEnObra("0143", "P2", "Juan Ejemplo Ejemplo"),
    ProveedorEnObra("0046", "P2", "Juan Ejemplo Ejemplo"),
    ProveedorEnObra("0028", "P3", "Pinturas Ejemplo S.A."),
    ProveedorEnObra("0085", "P4", "Cocinas Ejemplo S.L."),
    ProveedorEnObra("0166", None, None),
)
T0 = datetime(2026, 9, 29, 10, 0, tzinfo=UTC)


def _catalogo(
    oficios: tuple[OficioObra, ...] = OFICIOS,
    filas: tuple[ProveedorEnObra, ...] = FILAS,
) -> CatalogoObra:
    return CatalogoObra(
        obra_codigo="0677",
        obra_nombre=None,
        unidades=UNIDADES_0677,
        oficios=oficios,
        proveedores=filas,
    )


def _mismo(a: str, b: str) -> DecisionPar:
    return DecisionPar(
        catalogo=Catalogo.OFICIO,
        codigo_a=a,
        codigo_b=b,
        decision="mismo",
        motivos=frozenset(),
        obra_codigo="0677",
        decidido_por="oid-de-prueba",
        decidido_at_utc=T0,
    )


def _grupos_oficio(
    catalogo: CatalogoObra, decisiones: tuple[DecisionPar, ...] = ()
) -> GruposVigentes:
    # Como lo hará la aplicación: los oficios de la obra y sus filas de obrofc.
    uso = Counter(f.oficio_codigo for f in catalogo.proveedores)
    return grupos_vigentes(
        (Candidato(o.codigo, o.nombre) for o in catalogo.oficios),
        decisiones,
        PERFILES[Catalogo.OFICIO],
        uso,
    )


def _grupos_proveedor(catalogo: CatalogoObra) -> GruposVigentes:
    return grupos_de_proveedor(
        Candidato(f.proveedor_codigo, f.proveedor_nombre)
        for f in catalogo.proveedores
        if f.proveedor_codigo is not None
    )


def _pares(
    catalogo: CatalogoObra, decisiones: tuple[DecisionPar, ...] = ()
) -> tuple[OpcionProveedor, ...]:
    oficios = opciones_de_oficio(catalogo, _grupos_oficio(catalogo, decisiones))
    return opciones_de_proveedor(catalogo, _grupos_proveedor(catalogo), oficios)


def test_f036_r92_sin_grupos_un_oficio_por_codigo_y_por_orden_de_codigo() -> None:
    catalogo = _catalogo()
    opciones = opciones_de_oficio(catalogo, _grupos_oficio(catalogo))
    # Sin grupos confirmados el desplegable queda como antes: uno por código,
    # por orden de código. 0046 y 0143 dan la misma etiqueta sin tildes: cada
    # una lleva su código, como las unidades (R8).
    assert [(o.etiqueta, o.codigos_en_obra) for o in opciones] == [
        ("Pintura", ("0028",)),
        ("Carpinteria de madera (0046)", ("0046",)),
        ("Mobiliario de cocinas", ("0085",)),
        ("Carpintería de madera (0143)", ("0143",)),
        ("Mobiliario cocina", ("0166",)),
    ]
    assert opciones[0].grupo == Grupo(Catalogo.OFICIO, frozenset({"0028"}), "Pintura")


def test_f036_r92_r86_grupo_confirmado_es_una_opcion() -> None:
    catalogo = _catalogo()
    grupos = _grupos_oficio(catalogo, (_mismo("0046", "0143"),))
    opciones = opciones_de_oficio(catalogo, grupos)
    # R86: 0046 tiene dos filas en obrofc y 0143 una: manda el nombre de 0046.
    assert [(o.etiqueta, o.codigos_en_obra) for o in opciones] == [
        ("Pintura", ("0028",)),
        ("Carpinteria de madera", ("0046", "0143")),
        ("Mobiliario de cocinas", ("0085",)),
        ("Mobiliario cocina", ("0166",)),
    ]
    assert opciones[1].grupo is grupos.grupo_de("0143")


def test_f036_r92_grupo_con_codigos_de_fuera_de_la_obra() -> None:
    catalogo = _catalogo()
    opciones = opciones_de_oficio(
        catalogo, _grupos_oficio(catalogo, (_mismo("0143", "0999"),))
    )
    (carpinteria,) = (o for o in opciones if "0143" in o.codigos_en_obra)
    assert carpinteria.codigos_en_obra == ("0143",)
    assert carpinteria.grupo.codigos == {"0143", "0999"}


def test_f036_r92_dos_grupos_con_la_misma_etiqueta_llevan_sus_codigos() -> None:
    catalogo = _catalogo(
        oficios=(
            OficioObra("0046", "Carpintería de madera"),
            OficioObra("0143", "Carpintería de madera"),
            OficioObra("0200", "Carpintería en madera"),
        ),
        filas=(ProveedorEnObra("0046", "P1", "Carpinterías Ejemplo S.L."),),
    )
    opciones = opciones_de_oficio(
        catalogo, _grupos_oficio(catalogo, (_mismo("0046", "0200"),))
    )
    assert [o.etiqueta for o in opciones] == [
        "Carpintería de madera (0046, 0200)",
        "Carpintería de madera (0143)",
    ]


def test_f036_r92_etiquetas_que_chocan_aun_con_codigo_fallan() -> None:
    catalogo = _catalogo(
        oficios=(
            OficioObra("0028", "Pintura"),
            OficioObra("0030", "Pintura"),
            OficioObra("0099", "Pintura (0028)"),
        ),
        filas=(),
    )
    with pytest.raises(ValueError):
        opciones_de_oficio(catalogo, _grupos_oficio(catalogo))


def test_f036_r12_obra_sin_oficios_sin_opciones() -> None:
    catalogo = _catalogo(oficios=(), filas=())
    assert opciones_de_oficio(catalogo, _grupos_oficio(catalogo)) == ()
    assert opciones_de_proveedor(catalogo, _grupos_proveedor(catalogo), ()) == ()


def test_f036_r92_oficio_sin_grupo_o_grupos_de_otro_catalogo_fallan() -> None:
    catalogo = _catalogo()
    incompletos = _grupos_oficio(_catalogo(oficios=OFICIOS[:2]))
    with pytest.raises(ValueError):
        opciones_de_oficio(catalogo, incompletos)
    with pytest.raises(ValueError):
        opciones_de_oficio(catalogo, _grupos_proveedor(catalogo))


# --------------------------------------------------------------------------
# T7 · R71, R72 · los pares de `Proveedor`
# --------------------------------------------------------------------------


def test_f036_r71_pares_sin_grupos() -> None:
    pares = _pares(_catalogo())
    assert [(p.etiqueta, p.filas_en_obra) for p in pares] == [
        ("Pintura · Pinturas Ejemplo S.A.", (("0028", "P3"),)),
        ("Carpinteria de madera (0046) · Carpinterías Ejemplo S.L.", (("0046", "P1"),)),
        ("Carpinteria de madera (0046) · Juan Ejemplo Ejemplo", (("0046", "P2"),)),
        ("Mobiliario de cocinas · Cocinas Ejemplo S.L.", (("0085", "P4"),)),
        ("Carpintería de madera (0143) · Juan Ejemplo Ejemplo", (("0143", "P2"),)),
    ]
    # 0166 está en obrofc sin proveedor: no da ningún par (R71).
    assert not [p for p in pares if "0166" in p.oficio.codigos_en_obra]


def test_f036_r71_la_parte_de_oficio_es_la_opcion_de_oficio() -> None:
    catalogo = _catalogo()
    oficios = opciones_de_oficio(catalogo, _grupos_oficio(catalogo))
    pares = opciones_de_proveedor(catalogo, _grupos_proveedor(catalogo), oficios)
    for par in pares:
        assert par.oficio in oficios
        assert par.etiqueta.startswith(par.oficio.etiqueta + SEPARADOR_PAR)
        assert par.grupo.catalogo is Catalogo.PROVEEDOR
        assert len(par.grupo.codigos) == 1
    assert pares[0].grupo.etiqueta == "Pinturas Ejemplo S.A."


def test_f036_r71_con_grupo_de_oficio_y_la_tabla_de_15_5() -> None:
    # design §15.5: el grupo «Carpintería de madera» son 0046 y 0143; P1 está
    # con 0046 y P2 con 0143 y con 0046.
    catalogo = _catalogo()
    grupos = _grupos_oficio(catalogo, (_mismo("0046", "0143"),))
    oficios = opciones_de_oficio(catalogo, grupos)
    pares = opciones_de_proveedor(catalogo, _grupos_proveedor(catalogo), oficios)
    por_etiqueta = {p.etiqueta: p for p in pares}
    assert list(por_etiqueta) == [
        "Pintura · Pinturas Ejemplo S.A.",
        "Carpinteria de madera · Carpinterías Ejemplo S.L.",
        "Carpinteria de madera · Juan Ejemplo Ejemplo",
        "Mobiliario de cocinas · Cocinas Ejemplo S.L.",
    ]
    p1 = por_etiqueta["Carpinteria de madera · Carpinterías Ejemplo S.L."]
    p2 = por_etiqueta["Carpinteria de madera · Juan Ejemplo Ejemplo"]
    assert p1.filas_en_obra == (("0046", "P1"),)
    assert p2.filas_en_obra == (("0046", "P2"), ("0143", "P2"))
    carpinteria = oficios[1]
    assert resolver_oficio_y_proveedor(carpinteria, None) == (
        Elegido("Carpinteria de madera", None, True),
        None,
    )
    assert resolver_oficio_y_proveedor(carpinteria, p1) == (
        Elegido("Carpinteria de madera", "0046", False),
        Elegido("Carpinterías Ejemplo S.L.", "P1", False),
    )
    assert resolver_oficio_y_proveedor(carpinteria, p2) == (
        Elegido("Carpinteria de madera", None, True),
        Elegido("Juan Ejemplo Ejemplo", "P2", False),
    )


def test_f036_r72_mismo_nombre_en_el_mismo_oficio_lleva_el_codigo() -> None:
    filas = (
        *FILAS,
        ProveedorEnObra("0028", "P5", "Pinturas Ejemplo S.A."),
        ProveedorEnObra("0028", "P6", "PINTURAS EJEMPLO S.A."),
    )
    pares = _pares(_catalogo(filas=filas))
    pintura = [p.etiqueta for p in pares if p.oficio.codigos_en_obra == ("0028",)]
    assert pintura == [
        "Pintura · Pinturas Ejemplo S.A. (P3)",
        "Pintura · Pinturas Ejemplo S.A. (P5)",
        "Pintura · PINTURAS EJEMPLO S.A. (P6)",
    ]


def test_f036_r72_mismo_nombre_en_oficios_distintos_no_lleva_codigo() -> None:
    etiquetas = [p.etiqueta for p in _pares(_catalogo())]
    assert "Carpinteria de madera (0046) · Juan Ejemplo Ejemplo" in etiquetas
    assert "Carpintería de madera (0143) · Juan Ejemplo Ejemplo" in etiquetas


def test_f036_r72_proveedor_sin_nombre_da_su_codigo_y_orden_por_nombre() -> None:
    filas = (
        ProveedorEnObra("0028", "P9", None),
        ProveedorEnObra("0028", "P3", "pinturas Ejemplo S.A."),
        ProveedorEnObra("0028", "P7", "Acabados Ejemplo"),
    )
    pares = _pares(_catalogo(filas=filas))
    assert [p.etiqueta for p in pares] == [
        "Pintura · Acabados Ejemplo",
        "Pintura · P9",
        "Pintura · pinturas Ejemplo S.A.",
    ]


def test_f036_r71_filas_repetidas_y_oficios_fuera_del_desplegable() -> None:
    filas = (
        ProveedorEnObra("0028", "P3", "Pinturas Ejemplo S.A."),
        ProveedorEnObra("0028", "P3", "Pinturas Ejemplo S.A."),
        # Un oficio que no está en el desplegable (de baja, R13): sin par.
        ProveedorEnObra("0777", "P8", "Otro Ejemplo"),
    )
    pares = _pares(_catalogo(filas=filas))
    assert [(p.etiqueta, p.filas_en_obra) for p in pares] == [
        ("Pintura · Pinturas Ejemplo S.A.", (("0028", "P3"),)),
    ]


def test_f036_r71_deterministas() -> None:
    uno = _pares(_catalogo())
    otro = _pares(_catalogo(filas=tuple(reversed(FILAS))))
    assert uno == otro


def test_f036_r71_grupos_de_otro_catalogo_o_proveedor_sin_grupo_fallan() -> None:
    catalogo = _catalogo()
    oficios = opciones_de_oficio(catalogo, _grupos_oficio(catalogo))
    with pytest.raises(ValueError):
        opciones_de_proveedor(catalogo, _grupos_oficio(catalogo), oficios)
    incompletos = _grupos_proveedor(_catalogo(filas=FILAS[:1]))
    with pytest.raises(ValueError):
        opciones_de_proveedor(catalogo, incompletos, oficios)
