# services/postventa-api/tests/test_f013_puertos_y_dobles.py
"""F-013 T8 · los dos puertos nuevos y sus dobles, con el árbol medido de la 0677.

Tres cosas, y las tres sostienen los tests del resolutor (T9) y del paso (T10):

1. **Los puertos tienen exactamente lo que dice la spec** (`design.md` §3.2,
   §3.3). El del explorador, **dos métodos y ninguno más** (R48): ni listar
   ficheros, ni mover, ni renombrar, ni borrar. Es lo que garantiza que los
   142 partes sueltos de VILLA 04 no se tocan.
2. **Los dobles se comportan como lo de verdad** y **anotan cada llamada**. Un
   doble que no registra no deja comprobar el orden, y en esta feature el
   orden es el requisito: la obra se valida antes de listar, bajo un nivel
   nuevo no se lista, el resolutor no escribe (`reviewer.md`, punto 7).
3. **El árbol medido es uno**: el de `tests/utiles_destino.py` tiene que ser
   el mismo que el de las tablas de `test_f013_destino_dominio.py` (T6). Dos
   copias del mismo dato divergen siempre, y aquí divergir es probar el
   resolutor contra una biblioteca que no es la de Posventa.

Sin red, sin Graph, sin Sigrid.
"""

from __future__ import annotations

import ast
import inspect

import pytest
from domain.models.destino_posventa import UbicacionReclamacion, UnidadDeObra
from domain.models.errores import ArchivoFallido, ConfiguracionSigridIncompleta
from domain.ports.biblioteca import ExploradorBibliotecaPort
from domain.ports.ubicacion import UbicacionPort

from tests import test_f013_destino_dominio as t6
from tests.utiles_destino import (
    CARPETA_OBRA_0677,
    DENTRO_DE_LA_OBRA_0677,
    FICHEROS_SUELTOS_VILLA_04,
    HOJAS_0677,
    INCIDENCIAS,
    RAIZ_0677,
    RES_OBRA_0677,
    UNIDADES_0677,
    UNIDADES_EN_POSVENTA_0677,
    ExploradorFalso,
    UbicacionesFalsas,
    explorador_0677,
    ubicacion_0677,
    ubicaciones_0677,
)

#: Lo que el explorador puede hacer, en el orden en que lo declara (R48).
OPERACIONES_DEL_EXPLORADOR = ("listar_carpetas", "crear_subcarpeta")

#: Lo que el explorador **no** puede hacer nunca (R43, R48).
VERBOS_PROHIBIDOS = (
    "borrar", "eliminar", "mover", "renombrar", "fichero", "subir", "copiar",
    "delete", "move", "rename",
)

#: Las dos lecturas de la ubicación, en el orden en que las declara el puerto.
LECTURAS_DE_LA_UBICACION = ("leer_ubicacion", "leer_unidades_del_numero")


def _metodos(clase) -> tuple[str, ...]:
    arbol = ast.parse(inspect.getsource(clase))
    return tuple(
        nodo.name
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.FunctionDef | ast.AsyncFunctionDef)
    )


# ==========================================================================
# Los puertos
# ==========================================================================


def test_f013_r48_el_explorador_tiene_exactamente_dos_metodos():
    """R48 · `listar_carpetas` y `crear_subcarpeta`, y ninguno más."""
    metodos = _metodos(ExploradorBibliotecaPort)

    assert metodos == OPERACIONES_DEL_EXPLORADOR
    for verbo in VERBOS_PROHIBIDOS:
        assert not any(verbo in metodo for metodo in metodos)


def test_f013_r48_las_firmas_del_explorador_son_las_de_la_spec():
    """`design.md` §3.2 · todo por palabra clave: nadie invierte padre y nombre."""
    listar = inspect.signature(ExploradorBibliotecaPort.listar_carpetas)
    crear = inspect.signature(ExploradorBibliotecaPort.crear_subcarpeta)

    assert list(listar.parameters) == ["self", "carpeta"]
    assert list(crear.parameters) == ["self", "padre", "nombre"]
    for firma in (listar, crear):
        for nombre, parametro in firma.parameters.items():
            if nombre != "self":
                assert parametro.kind is inspect.Parameter.KEYWORD_ONLY


def test_f013_el_puerto_de_ubicacion_tiene_las_dos_lecturas():
    """`design.md` §3.3 · las dos lecturas, y ninguna escritura."""
    assert _metodos(UbicacionPort) == LECTURAS_DE_LA_UBICACION
    leer = inspect.signature(UbicacionPort.leer_ubicacion)
    unidades = inspect.signature(UbicacionPort.leer_unidades_del_numero)

    assert list(leer.parameters) == ["self", "codigo_reclamacion"]
    assert list(unidades.parameters) == ["self", "codigo_obra"]
    for firma in (leer, unidades):
        for nombre, parametro in firma.parameters.items():
            if nombre != "self":
                assert parametro.kind is inspect.Parameter.KEYWORD_ONLY


def test_f013_los_puertos_no_viven_en_el_puerto_de_archivo():
    """`design.md` §2.3 · `ArchivoPort` no gana métodos; los nuevos, aparte."""
    from domain.ports.archivo import ArchivoPort

    assert _metodos(ArchivoPort) == ("asegurar_carpeta", "buscar", "subir")


def test_f013_los_dobles_cumplen_los_puertos():
    """Los dobles son `isinstance` de sus puertos: si el puerto cambia, se ve."""
    assert isinstance(ExploradorFalso(), ExploradorBibliotecaPort)
    assert isinstance(UbicacionesFalsas(), UbicacionPort)


# ==========================================================================
# ExploradorFalso
# ==========================================================================


def test_f013_explorador_lista_solo_carpetas_y_en_su_orden():
    """R12, R48 · lista las carpetas hijas; los ficheros sueltos no aparecen."""
    explorador = ExploradorFalso(
        {"": ("B", "A"), "B": (), "A": ()}, ficheros={"A": 3}
    )

    assert explorador.listar_carpetas(carpeta="") == ("B", "A")
    assert explorador.listar_carpetas(carpeta="A") == ()


def test_f013_explorador_una_carpeta_que_no_existe_es_none():
    """`design.md` §3.2 · `None` si la carpeta no existe (el `404` de Graph)."""
    explorador = ExploradorFalso({"": ("A",), "A": ()})

    assert explorador.listar_carpetas(carpeta="NO EXISTE") is None


def test_f013_explorador_anota_cada_llamada_en_orden():
    """Cada llamada, con sus argumentos, en su lista y en el registro compartido."""
    registro: list[str] = []
    explorador = ExploradorFalso({"": ("A",), "A": ()}, registro=registro)

    explorador.listar_carpetas(carpeta="")
    explorador.crear_subcarpeta(padre="A", nombre="B")
    explorador.listar_carpetas(carpeta="A/B")

    assert explorador.llamadas == [
        ("listar_carpetas", {"carpeta": ""}),
        ("crear_subcarpeta", {"padre": "A", "nombre": "B"}),
        ("listar_carpetas", {"carpeta": "A/B"}),
    ]
    assert registro == [
        "explorador.listar_carpetas:",
        "explorador.crear_subcarpeta:A|B",
        "explorador.listar_carpetas:A/B",
    ]
    assert explorador.listados == ["", "A/B"]
    assert explorador.creaciones == [("A", "B")]


def test_f013_explorador_crea_un_nivel_dentro_de_un_padre_que_existe():
    """R15 · un nivel por llamada: la carpeta nueva aparece y se puede listar."""
    explorador = ExploradorFalso({"": ("A",), "A": ()})

    explorador.crear_subcarpeta(padre="A", nombre="B")

    assert explorador.listar_carpetas(carpeta="A") == ("B",)
    assert explorador.listar_carpetas(carpeta="A/B") == ()


def test_f013_explorador_crea_en_la_raiz():
    """`padre=""` es la raíz de la biblioteca (D-1)."""
    explorador = ExploradorFalso({"": ("A",)})

    explorador.crear_subcarpeta(padre="", nombre="B")

    assert explorador.listar_carpetas(carpeta="") == ("A", "B")


def test_f013_explorador_padre_ausente_es_archivo_fallido_sin_crear_intermedias():
    """`design.md` §3.2 · nunca crea intermedias: padre ausente = `ArchivoFallido`."""
    explorador = ExploradorFalso({"": ("A",), "A": ()})

    with pytest.raises(ArchivoFallido):
        explorador.crear_subcarpeta(padre="A/NO EXISTE", nombre="B")

    assert explorador.listar_carpetas(carpeta="A") == ()
    assert explorador.listar_carpetas(carpeta="A/NO EXISTE") is None
    assert explorador.carpetas_nuevas == []


def test_f013_explorador_crear_la_que_ya_existe_es_exito_y_no_duplica():
    """R39 · «ya existe» cuenta como éxito (`409` de Graph) y deja **una**."""
    explorador = ExploradorFalso({"": ("A",), "A": ()})

    explorador.crear_subcarpeta(padre="", nombre="A")
    explorador.crear_subcarpeta(padre="", nombre="A")

    assert explorador.listar_carpetas(carpeta="") == ("A",)
    assert explorador.carpetas_nuevas == []
    assert len(explorador.creaciones) == 2


def test_f013_explorador_carpetas_nuevas_son_las_que_de_verdad_crea():
    """Distingue lo que se **pidió** crear de lo que **apareció**."""
    explorador = ExploradorFalso({"": ()})

    explorador.crear_subcarpeta(padre="", nombre="A")
    explorador.crear_subcarpeta(padre="A", nombre="B")

    assert explorador.carpetas_nuevas == ["A", "A/B"]


def test_f013_explorador_puede_fallar_al_listar_y_al_crear():
    """El fallo del proveedor se inyecta sin red, y la llamada queda anotada."""
    caido = ArchivoFallido("Graph respondió 503")
    explorador = ExploradorFalso({"": ()}, fallo_al_listar=caido, fallo_al_crear=caido)

    with pytest.raises(ArchivoFallido) as al_listar:
        explorador.listar_carpetas(carpeta="")
    with pytest.raises(ArchivoFallido) as al_crear:
        explorador.crear_subcarpeta(padre="", nombre="A")

    assert al_listar.value is caido
    assert al_crear.value is caido
    assert [nombre for nombre, _ in explorador.llamadas] == [
        "listar_carpetas",
        "crear_subcarpeta",
    ]
    assert explorador.carpetas_nuevas == []


def test_f013_explorador_no_expone_los_ficheros_pero_los_conserva():
    """R48 · VILLA 04: 142 ficheros sueltos que el explorador ni ve ni toca."""
    explorador = explorador_0677()
    villa_04 = f"{CARPETA_OBRA_0677}/{INCIDENCIAS}/VILLA 04"

    assert explorador.listar_carpetas(carpeta=villa_04) == ()
    explorador.crear_subcarpeta(padre=villa_04, nombre="PARTES FIRMADOS")

    assert explorador.listar_carpetas(carpeta=villa_04) == ("PARTES FIRMADOS",)
    assert explorador.ficheros_en(villa_04) == FICHEROS_SUELTOS_VILLA_04 == 142


def test_f013_explorador_no_comparte_el_arbol_con_quien_lo_construyo():
    """Crear en un doble no cambia el diccionario de otro test."""
    arbol = {"": ("A",), "A": ()}
    explorador = ExploradorFalso(arbol)

    explorador.crear_subcarpeta(padre="A", nombre="B")

    assert arbol == {"": ("A",), "A": ()}


# ==========================================================================
# UbicacionesFalsas
# ==========================================================================


def _una_ubicacion() -> UbicacionReclamacion:
    return UbicacionReclamacion("0677", RES_OBRA_0677, "0677.03VILLA 5.", "Viviendas Bloque Villa 5")


def test_f013_ubicaciones_devuelve_las_filas_de_cada_reclamacion():
    """Todas las filas: el dominio decide qué es 0, 1 o varias (R7)."""
    una = _una_ubicacion()
    ubicaciones = UbicacionesFalsas({"RS26.08/0123": (una, una)})

    assert ubicaciones.leer_ubicacion(codigo_reclamacion="RS26.08/0123") == (una, una)
    assert ubicaciones.leer_ubicacion(codigo_reclamacion="RS26.08/9999") == ()


def test_f013_ubicaciones_devuelve_las_unidades_tal_cual_se_le_dieron():
    """La segunda lectura: preselecciona el SQL y decide el dominio (§4.7)."""
    ubicaciones = UbicacionesFalsas(unidades=UNIDADES_0677)

    assert ubicaciones.leer_unidades_del_numero(codigo_obra="0677") == UNIDADES_0677


def test_f013_ubicaciones_anota_cada_llamada_en_orden():
    """Las dos lecturas, con su argumento, en su lista y en el registro compartido."""
    registro: list[str] = []
    ubicaciones = UbicacionesFalsas(registro=registro)

    ubicaciones.leer_ubicacion(codigo_reclamacion="RS26.08/0123")
    ubicaciones.leer_unidades_del_numero(codigo_obra="0677")

    assert ubicaciones.llamadas == [
        ("leer_ubicacion", {"codigo_reclamacion": "RS26.08/0123"}),
        ("leer_unidades_del_numero", {"codigo_obra": "0677"}),
    ]
    assert registro == [
        "ubicaciones.leer_ubicacion:RS26.08/0123",
        "ubicaciones.leer_unidades_del_numero:0677",
    ]


@pytest.mark.parametrize(
    "fallo", (ConfiguracionSigridIncompleta("faltan variables"), TimeoutError("sin respuesta"))
)
def test_f013_ubicaciones_puede_fallar_por_red_en_cada_lectura(fallo):
    """R41 · cada lectura puede fallar por su cuenta, y la llamada queda anotada."""
    primera = UbicacionesFalsas(fallo_al_ubicar=fallo)
    segunda = UbicacionesFalsas(fallo_al_leer_unidades=fallo)

    with pytest.raises(type(fallo)) as en_la_primera:
        primera.leer_ubicacion(codigo_reclamacion="RS26.08/0123")
    assert segunda.leer_ubicacion(codigo_reclamacion="RS26.08/0123") == ()
    with pytest.raises(type(fallo)) as en_la_segunda:
        segunda.leer_unidades_del_numero(codigo_obra="0677")

    assert en_la_primera.value is fallo
    assert en_la_segunda.value is fallo
    assert [nombre for nombre, _ in primera.llamadas] == ["leer_ubicacion"]
    assert [nombre for nombre, _ in segunda.llamadas] == [
        "leer_ubicacion",
        "leer_unidades_del_numero",
    ]


# ==========================================================================
# El árbol medido de la 0677 (T2 y T3), uno y el mismo
# ==========================================================================


def test_f013_el_arbol_medido_es_el_de_las_tablas_del_dominio():
    """Un dato, un sitio: los datos de T8 son los de T6, carácter a carácter."""
    assert CARPETA_OBRA_0677 == t6.CARPETA_OBRA_0677 == "677  MIRASIERRA"
    assert RES_OBRA_0677 == t6.RES_OBRA_0677
    assert RAIZ_0677 == t6.RAIZ
    assert DENTRO_DE_LA_OBRA_0677 == t6.DENTRO_DE_LA_OBRA
    assert UNIDADES_EN_POSVENTA_0677 == t6.UNIDADES_EN_POSVENTA
    assert HOJAS_0677 == t6.HOJAS_EN_POSVENTA
    assert UNIDADES_0677 == t6.FILAS_0677


def test_f013_el_arbol_medido_de_la_0677_tal_y_como_lo_ve_el_explorador():
    """T2 · la raíz, la obra, `PARTES INCIDENCIAS`, siete unidades y sus hojas."""
    explorador = explorador_0677()
    obra = CARPETA_OBRA_0677
    incidencias = f"{obra}/{INCIDENCIAS}"

    assert explorador.listar_carpetas(carpeta="") == RAIZ_0677
    assert explorador.listar_carpetas(carpeta=obra) == DENTRO_DE_LA_OBRA_0677
    assert explorador.listar_carpetas(carpeta=incidencias) == tuple(
        f"VILLA {n:02d}" for n in range(1, 8)
    )
    assert explorador.listar_carpetas(carpeta=f"{incidencias}/VILLA 02") == (
        "PARTES FIRMADO",
    )
    assert explorador.listar_carpetas(carpeta=f"{incidencias}/VILLA 04") == ()
    for villa in ("VILLA 01", "VILLA 03", "VILLA 05", "VILLA 06", "VILLA 07"):
        assert explorador.listar_carpetas(carpeta=f"{incidencias}/{villa}") == (
            "PARTES FIRMADOS",
        )
    for n in range(8, 16):
        assert explorador.listar_carpetas(carpeta=f"{incidencias}/VILLA {n:02d}") is None


def test_f013_la_raiz_medida_no_lleva_el_677_fuera_de_su_carpeta():
    """T2 · «ninguna otra carpeta de la raíz casa ni se parece»."""
    otras = [nombre for nombre in RAIZ_0677 if nombre != CARPETA_OBRA_0677]

    assert len(otras) == len(RAIZ_0677) - 1
    assert not any("677" in nombre for nombre in otras)


def test_f013_las_15_unidades_medidas_de_la_0677():
    """T3 · quince unidades, una obra, `con.cod` y `con.res` sin nombres de persona."""
    assert len(UNIDADES_0677) == 15
    assert {fila.obra_ref for fila in UNIDADES_0677} == {"obra-a"}
    assert [fila.unidad_codigo for fila in UNIDADES_0677] == [
        f"0677.03VILLA {n}." for n in range(1, 16)
    ]
    assert [fila.unidad_nombre for fila in UNIDADES_0677] == [
        f"Viviendas Bloque Villa {n}" for n in range(1, 16)
    ]
    assert all(isinstance(fila, UnidadDeObra) for fila in UNIDADES_0677)


@pytest.mark.parametrize("n", range(1, 16))
def test_f013_la_ubicacion_de_cada_unidad_de_la_0677(n):
    """La fila que devolvería la primera lectura para una reclamación de la villa N."""
    assert ubicacion_0677(n) == UbicacionReclamacion(
        obra_codigo="0677",
        obra_nombre=RES_OBRA_0677,
        unidad_codigo=f"0677.03VILLA {n}.",
        unidad_nombre=f"Viviendas Bloque Villa {n}",
    )


def test_f013_las_ubicaciones_de_la_0677_con_una_reclamacion_por_villa():
    """El doble de la 0677: una reclamación por villa y las 15 unidades."""
    ubicaciones = ubicaciones_0677()

    for n in range(1, 16):
        assert ubicaciones.leer_ubicacion(
            codigo_reclamacion=f"RS26.08/{n:04d}"
        ) == (ubicacion_0677(n),)
    assert ubicaciones.leer_unidades_del_numero(codigo_obra="0677") == UNIDADES_0677


def test_f013_cada_explorador_de_la_0677_es_uno_nuevo():
    """Crear en uno no deja la carpeta en el siguiente: cada test, su biblioteca."""
    primero = explorador_0677()
    primero.crear_subcarpeta(padre=f"{CARPETA_OBRA_0677}/{INCIDENCIAS}", nombre="VILLA 08")

    assert explorador_0677().listar_carpetas(
        carpeta=f"{CARPETA_OBRA_0677}/{INCIDENCIAS}/VILLA 08"
    ) is None
