# services/postventa-api/tests/test_f071_dominio_importacion.py
"""La importación de la plantilla v2, pura (F-071 T1).

`specs/F-071-plantilla-desde-sigrid/design.md` §5.3–§5.6, sobre
`domain/models/importacion.py`:

| Caso | Requisito |
|---|---|
| v1 → `version_anterior` con su texto; 0 y 3 → `version_no_soportada`; v2 sí | R23 |
| ubicación vacía o en blanco: válida, sin aviso | R26 |
| exacta de su unidad: tal cual, sin aviso | R27 |
| casa por el casado de F-060: el texto de Sigrid y el aviso | R28 |
| no casa con su unidad (también ambigua): `UBICACION_FUERA_DE_LA_UNIDAD` | R29 |
| unidad sin ubicaciones: `UNIDAD_SIN_UBICACIONES` | R30 |
| unidad ausente o inválida: contra la unión; `UBICACION_FUERA_DE_LA_OBRA` | R31 |
| oficio: su código y el nombre de Sigrid (no la etiqueta) | R32 |
| proveedor: el par, con el oficio del par | R33 |
| par de otro oficio: `PROVEEDOR_DE_OTRO_OFICIO` | R34 |
| ninguna combinación da ambiguo | R35 |
| casado en las cinco columnas, con aviso; dos por clave → error | R36 |
| lo que ya no está en Sigrid: su texto | R37 |
| fórmula, fecha/booleano y número en tasadas, también en `Ubicación` | R38 |
| orden de los errores = orden de las columnas | R39 |
| clave de duplicado igual con la ubicación en otra mayúscula | R41 |

Sin red, sin Sigrid, sin base de datos y sin `openpyxl`. Datos ficticios: obra
`9901`, «Vivienda N», «Estancia A-NN», «Oficio ficticio N», «Proveedor
ficticio N».
"""

from __future__ import annotations

import itertools
import unicodedata

import pytest
from domain.models import importacion
from domain.models.errores import CODIGOS_FICHERO_NO_ES_PLANTILLA, FicheroNoEsPlantilla
from domain.models.importacion import (
    DESCRIPCION,
    DETALLE,
    ERRORES,
    FECHA_EN_TASADA,
    FORMULA,
    LISTADO,
    NUMERO_EN_TASADA,
    OFICIO,
    PROVEEDOR,
    PROVEEDOR_DE_OTRO_OFICIO,
    UBICACION,
    UBICACION_FUERA_DE_LA_OBRA,
    UBICACION_FUERA_DE_LA_UNIDAD,
    UNIDAD,
    UNIDAD_SIN_UBICACIONES,
    URGENCIA,
    CeldaLeida,
    Elegido,
    FilaConError,
    FilaLeida,
    IncidenciaValida,
    LibroLeido,
    aviso_ubicacion_ajustada,
    aviso_valor_tomado,
    clave_de_duplicado,
    reconocer_plantilla,
    validar_filas,
    ya_no_esta_en_sigrid,
)
from domain.models.plantilla_incidencias import (
    CABECERA,
    IDENTIFICADOR_PLANTILLA,
    CatalogoObra,
    ListasCerradas,
    OficioObra,
    Opcion,
    OpcionOficioSigrid,
    ParSigrid,
    ProveedorEnObra,
    UnidadPosventa,
    Urgencia,
    oficios_del_desplegable,
    pares_del_desplegable,
)

# --------------------------------------------------------------------------
# Datos de prueba
# --------------------------------------------------------------------------

V1 = UnidadPosventa(codigo="9901.V1", nombre="Vivienda 1")
V2 = UnidadPosventa(codigo="9901.V2", nombre="Vivienda 2")
V3 = UnidadPosventa(codigo="9901.V3", nombre="Vivienda 3")  # sin ubicaciones

CATALOGO = CatalogoObra(
    obra_codigo="9901",
    obra_nombre="Obra ficticia",
    unidades=(V1, V2, V3),
    oficios=(
        OficioObra(codigo="0010", nombre="Oficio ficticio 1"),
        OficioObra(codigo="0020", nombre="Oficio ficticio 2"),
        OficioObra(codigo="0030", nombre=None),
    ),
    proveedores=(
        ProveedorEnObra("0010", "P1", "Proveedor ficticio 1"),
        ProveedorEnObra("0020", "P1", "Proveedor ficticio 1"),
        ProveedorEnObra("0020", "P2", None),
        ProveedorEnObra("0030", None, None),
    ),
)
OFICIOS = oficios_del_desplegable(CATALOGO)
PARES = pares_del_desplegable(CATALOGO, OFICIOS)

ET_OFICIO_1 = "Oficio ficticio 1 (0010)"
ET_OFICIO_2 = "Oficio ficticio 2 (0020)"
ET_OFICIO_3 = "0030"
ET_PAR_1_P1 = "Oficio ficticio 1 (0010) · Proveedor ficticio 1 (P1)"
ET_PAR_2_P1 = "Oficio ficticio 2 (0020) · Proveedor ficticio 1 (P1)"
ET_PAR_2_P2 = "Oficio ficticio 2 (0020) · P2"

UBICACIONES = {
    "9901.V1": ("Estancia A-01", "Estancia A-02", "Estancia Ñ-03"),
    "9901.V2": ("Estancia A-04", "Estancia A-05", "estancia a-05"),
    "9901.V3": (),
}

LISTAS = ListasCerradas(
    urgencias=(
        Opcion(etiqueta="Urgente", codigo="urgente"),
        Opcion(etiqueta="Peligro para la seguridad", codigo="seguridad"),
    ),
    listados=(
        Opcion(etiqueta="Primer listado", codigo="primero"),
        Opcion(etiqueta="Segundo listado", codigo="segundo"),
    ),
)


def celda(
    valor: str | float | None, *, formula: bool = False, fecha: bool = False
) -> CeldaLeida:
    return CeldaLeida(
        valor=valor,
        es_formula=formula,
        es_fecha_o_booleano=fecha,
        texto_original=None if valor is None else str(valor),
    )


_COLUMNAS = {
    "unidad": UNIDAD,
    "ubicacion": UBICACION,
    "descripcion": DESCRIPCION,
    "detalle": DETALLE,
    "oficio": OFICIO,
    "proveedor": PROVEEDOR,
    "urgencia": URGENCIA,
    "listado": LISTADO,
    "errores": ERRORES,
}


def fila(numero: int = 2, **valores: object) -> FilaLeida:
    celdas = {
        _COLUMNAS[clave]: valor if isinstance(valor, CeldaLeida) else celda(valor)  # type: ignore[arg-type]
        for clave, valor in valores.items()
    }
    return FilaLeida(numero=numero, celdas=celdas)


def validar(
    *filas: FilaLeida,
    listas: ListasCerradas = LISTAS,
    ubicaciones: dict[str, tuple[str, ...]] | None = None,
    oficios: tuple[OpcionOficioSigrid, ...] = OFICIOS,
    pares: tuple[ParSigrid, ...] = PARES,
) -> tuple[tuple[IncidenciaValida, ...], tuple[FilaConError, ...]]:
    return validar_filas(
        filas,
        catalogo=CATALOGO,
        oficios=oficios,
        pares=pares,
        listas=listas,
        ubicaciones_por_unidad=UBICACIONES if ubicaciones is None else ubicaciones,
    )


def una_valida(f: FilaLeida, **kwargs: object) -> IncidenciaValida:
    validas, con_error = validar(f, **kwargs)  # type: ignore[arg-type]
    assert con_error == ()
    assert len(validas) == 1
    return validas[0]


def errores_de(f: FilaLeida, **kwargs: object) -> list[tuple[str, str]]:
    validas, con_error = validar(f, **kwargs)  # type: ignore[arg-type]
    assert validas == ()
    assert len(con_error) == 1
    return [(e.columna, e.problema) for e in con_error[0].errores]


def basica(**valores: object) -> FilaLeida:
    """Una fila buena de la Vivienda 1 con lo que se pase encima."""
    base: dict[str, object] = {"unidad": "Vivienda 1", "descripcion": "Grieta ficticia"}
    base.update(valores)
    return fila(**base)


# --------------------------------------------------------------------------
# R23 · versión
# --------------------------------------------------------------------------


def _libro(version: int | None) -> LibroLeido:
    return LibroLeido(
        identificador=IDENTIFICADOR_PLANTILLA,
        version=version,
        obra_codigo="9901",
        cabecera=CABECERA,
        filas=(),
        parece_formato_antiguo=False,
    )


TEXTO_VERSION_ANTERIOR = (
    "Esta plantilla es de una versión anterior: sus listas ya no son las de "
    "Sigrid. Descarga una nueva desde el portal y copia en ella tus filas."
)


def test_f071_r23_v1_es_version_anterior_con_su_texto() -> None:
    assert "version_anterior" in CODIGOS_FICHERO_NO_ES_PLANTILLA
    with pytest.raises(FicheroNoEsPlantilla) as error:
        reconocer_plantilla(_libro(1))
    assert error.value.codigo == "version_anterior"
    assert error.value.motivo == TEXTO_VERSION_ANTERIOR


def test_f071_r23_v1_se_rechaza_antes_que_la_cabecera() -> None:
    libro = LibroLeido(
        identificador=IDENTIFICADOR_PLANTILLA,
        version=1,
        obra_codigo="9901",
        cabecera=("Otra",),
        filas=(),
        parece_formato_antiguo=False,
    )
    with pytest.raises(FicheroNoEsPlantilla) as error:
        reconocer_plantilla(libro)
    assert error.value.codigo == "version_anterior"


@pytest.mark.parametrize("version", [0, 3, None])
def test_f071_r23_otras_versiones_siguen_no_soportadas(version: int | None) -> None:
    with pytest.raises(FicheroNoEsPlantilla) as error:
        reconocer_plantilla(_libro(version))
    assert error.value.codigo == "version_no_soportada"


def test_f071_r23_v2_se_reconoce() -> None:
    assert reconocer_plantilla(_libro(2)) == "9901"


# --------------------------------------------------------------------------
# R26–R31 · ubicación
# --------------------------------------------------------------------------


@pytest.mark.parametrize("vacia", [None, "", "   "])
def test_f071_r26_ubicacion_vacia_es_valida_sin_aviso(vacia: str | None) -> None:
    for unidad in ("Vivienda 1", "Vivienda 3"):  # también sin ubicaciones
        valida = una_valida(basica(unidad=unidad, ubicacion=vacia))
        assert valida.ubicacion is None
        assert valida.avisos == ()


def test_f071_r27_exacta_de_su_unidad_tal_cual_sin_aviso() -> None:
    valida = una_valida(basica(ubicacion="Estancia Ñ-03"))
    assert valida.ubicacion == "Estancia Ñ-03"
    assert valida.avisos == ()


def test_f071_r27_exacta_aunque_otra_tenga_la_misma_clave() -> None:
    valida = una_valida(basica(unidad="Vivienda 2", ubicacion="estancia a-05"))
    assert valida.ubicacion == "estancia a-05"
    assert valida.avisos == ()


@pytest.mark.parametrize(
    ("tecleada", "de_sigrid"),
    [
        ("ESTANCIA A-02", "Estancia A-02"),
        ("  Estancia A-01 ", "Estancia A-01"),
        ("estancia ñ-03", "Estancia Ñ-03"),
        (unicodedata.normalize("NFD", "Estancia Ñ-03"), "Estancia Ñ-03"),
    ],
)
def test_f071_r28_casada_guarda_el_texto_de_sigrid_y_avisa(
    tecleada: str, de_sigrid: str
) -> None:
    valida = una_valida(basica(ubicacion=tecleada))
    assert valida.ubicacion == de_sigrid
    assert valida.avisos == (aviso_ubicacion_ajustada(de_sigrid),)


def test_f071_r28_texto_del_aviso() -> None:
    assert aviso_ubicacion_ajustada("Estancia A-01") == (
        "la ubicación se ha ajustado al texto de Sigrid: «Estancia A-01»"
    )


@pytest.mark.parametrize(
    "tecleada",
    [
        "Estancia A-04",  # es de otra unidad
        "Estancia A-1",  # errata
        "Estancia  A-01",  # blanco interior
        "General (toda la unidad)",  # ya no existe (R11)
    ],
)
def test_f071_r29_fuera_de_la_unidad(tecleada: str) -> None:
    assert errores_de(basica(ubicacion=tecleada)) == [
        (UBICACION, UBICACION_FUERA_DE_LA_UNIDAD)
    ]


def test_f071_r29_ambigua_en_su_unidad_es_fuera_de_la_unidad() -> None:
    # «ESTANCIA A-05» casa por clave con dos de la Vivienda 2: no se elige.
    assert errores_de(basica(unidad="Vivienda 2", ubicacion="ESTANCIA A-05")) == [
        (UBICACION, UBICACION_FUERA_DE_LA_UNIDAD)
    ]


def test_f071_r29_texto() -> None:
    assert UBICACION_FUERA_DE_LA_UNIDAD == (
        "esa ubicación no es de la unidad de esta fila: elígela del desplegable, "
        "que enseña solo las de su unidad (si has cambiado la unidad, vuelve a "
        "elegir la ubicación); si el sitio no está, deja la ubicación en blanco y "
        "explícalo en «Detalle»"
    )


def test_f071_r30_unidad_sin_ubicaciones() -> None:
    assert errores_de(basica(unidad="Vivienda 3", ubicacion="Estancia A-01")) == [
        (UBICACION, UNIDAD_SIN_UBICACIONES)
    ]
    assert UNIDAD_SIN_UBICACIONES == (
        "esta unidad no tiene ubicaciones en Sigrid: deja la ubicación en blanco y "
        "explica el sitio en «Detalle»"
    )


def test_f071_r30_unidad_sin_entrada_en_el_mapa_es_sin_ubicaciones() -> None:
    ubicaciones = {k: v for k, v in UBICACIONES.items() if k != "9901.V1"}
    assert errores_de(basica(ubicacion="Estancia A-01"), ubicaciones=ubicaciones) == [
        (UBICACION, UNIDAD_SIN_UBICACIONES)
    ]


@pytest.mark.parametrize(
    "unidad", [None, "Vivienda 9", celda("=A1", formula=True), celda(7.0)]
)
def test_f071_r31_sin_unidad_valida_y_ubicacion_de_la_obra_sin_error_de_ubicacion(
    unidad: object,
) -> None:
    for ubicacion in ("Estancia A-04", "ESTANCIA A-01"):
        valores: dict[str, object] = {"descripcion": "Grieta ficticia", "ubicacion": ubicacion}
        if unidad is not None:
            valores["unidad"] = unidad
        columnas = [c for c, _ in errores_de(fila(**valores))]
        assert columnas == [UNIDAD]


@pytest.mark.parametrize("unidad", [None, "Vivienda 9"])
def test_f071_r31_sin_unidad_valida_y_ubicacion_fuera_de_la_obra(
    unidad: str | None,
) -> None:
    valores: dict[str, object] = {"descripcion": "Grieta ficticia", "ubicacion": "Estancia A-99"}
    if unidad is not None:
        valores["unidad"] = unidad
    errores = errores_de(fila(**valores))
    assert errores[-1] == (UBICACION, UBICACION_FUERA_DE_LA_OBRA)
    assert [c for c, _ in errores] == [UNIDAD, UBICACION]
    assert UBICACION_FUERA_DE_LA_OBRA == (
        "esa ubicación no es de ninguna unidad de la obra: elige primero la unidad "
        "y luego la ubicación del desplegable"
    )


def test_f071_r31_ambigua_en_la_union_es_fuera_de_la_obra() -> None:
    errores = errores_de(fila(descripcion="Grieta ficticia", ubicacion="ESTANCIA A-05"))
    assert errores == [
        (UNIDAD, importacion.FALTA_UNIDAD),
        (UBICACION, UBICACION_FUERA_DE_LA_OBRA),
    ]


def test_f071_r31_la_union_es_solo_de_las_unidades_del_catalogo() -> None:
    ubicaciones = dict(UBICACIONES)
    ubicaciones["9999.AJENA"] = ("Estancia A-99",)
    errores = errores_de(
        fila(descripcion="Grieta ficticia", ubicacion="Estancia A-99"),
        ubicaciones=ubicaciones,
    )
    assert errores[-1] == (UBICACION, UBICACION_FUERA_DE_LA_OBRA)


def test_f071_r22_la_ubicacion_no_sale_de_listas_cerradas() -> None:
    # Ni ListasCerradas ni ningún otro argumento trae ubicaciones: con el mapa
    # vacío, nada casa.
    assert errores_de(basica(ubicacion="Estancia A-01"), ubicaciones={}) == [
        (UBICACION, UNIDAD_SIN_UBICACIONES)
    ]


# --------------------------------------------------------------------------
# R32–R35 · oficio y proveedor
# --------------------------------------------------------------------------


def test_f071_r32_oficio_con_su_codigo_y_el_nombre_de_sigrid() -> None:
    valida = una_valida(basica(oficio=ET_OFICIO_1))
    assert valida.oficio == Elegido(
        etiqueta="Oficio ficticio 1", codigo="0010", ambiguo=False
    )
    assert valida.proveedor is None
    assert valida.avisos == ()


def test_f071_r32_oficio_sin_nombre_el_codigo() -> None:
    valida = una_valida(basica(oficio=ET_OFICIO_3))
    assert valida.oficio == Elegido(etiqueta="0030", codigo="0030", ambiguo=False)


def test_f071_r33_proveedor_con_el_oficio_del_par() -> None:
    valida = una_valida(basica(proveedor=ET_PAR_2_P1))
    assert valida.oficio == Elegido(
        etiqueta="Oficio ficticio 2", codigo="0020", ambiguo=False
    )
    assert valida.proveedor == Elegido(
        etiqueta="Proveedor ficticio 1", codigo="P1", ambiguo=False
    )


def test_f071_r33_proveedor_y_su_oficio_elegidos() -> None:
    valida = una_valida(basica(oficio=ET_OFICIO_1, proveedor=ET_PAR_1_P1))
    assert valida.oficio == Elegido(
        etiqueta="Oficio ficticio 1", codigo="0010", ambiguo=False
    )
    assert valida.proveedor == Elegido(
        etiqueta="Proveedor ficticio 1", codigo="P1", ambiguo=False
    )


def test_f071_r33_proveedor_sin_nombre_el_codigo() -> None:
    valida = una_valida(basica(proveedor=ET_PAR_2_P2))
    assert valida.proveedor == Elegido(etiqueta="P2", codigo="P2", ambiguo=False)
    assert valida.oficio is not None and valida.oficio.codigo == "0020"


def test_f071_r34_par_de_otro_oficio() -> None:
    assert errores_de(basica(oficio=ET_OFICIO_1, proveedor=ET_PAR_2_P1)) == [
        (PROVEEDOR, PROVEEDOR_DE_OTRO_OFICIO)
    ]


def test_f071_r35_ninguna_combinacion_da_ambiguo() -> None:
    # Obra ficticia con oficios de nombre repetido (dos «Oficio ficticio» y dos
    # casi iguales) y un proveedor en dos oficios: el caso que en F-036 daba
    # `oficio_ambiguo`.
    catalogo = CatalogoObra(
        obra_codigo="9902",
        obra_nombre=None,
        unidades=(V1,),
        oficios=(
            OficioObra(codigo="0046", nombre="Oficio ficticio de madera"),
            OficioObra(codigo="0143", nombre="Oficio ficticio de mádera"),
            OficioObra(codigo="0200", nombre="Oficio ficticio"),
            OficioObra(codigo="0201", nombre="Oficio ficticio"),
        ),
        proveedores=(
            ProveedorEnObra("0046", "P1", "Proveedor ficticio 1"),
            ProveedorEnObra("0143", "P1", "Proveedor ficticio 1"),
            ProveedorEnObra("0046", "P2", "Proveedor ficticio 2"),
            ProveedorEnObra("0200", "P3", "Proveedor ficticio 3"),
            ProveedorEnObra("0201", "P3", "Proveedor ficticio 3"),
        ),
    )
    oficios = oficios_del_desplegable(catalogo)
    pares = pares_del_desplegable(catalogo, oficios)
    assert len(oficios) == 4
    assert len(pares) == 5
    vistas = 0
    for oficio, par in itertools.product((None, *oficios), (None, *pares)):
        valores: dict[str, object] = {"unidad": "Vivienda 1", "descripcion": "Grieta ficticia"}
        if oficio is not None:
            valores["oficio"] = oficio.etiqueta
        if par is not None:
            valores["proveedor"] = par.etiqueta
        validas, con_error = validar_filas(
            (fila(**valores),),
            catalogo=catalogo,
            oficios=oficios,
            pares=pares,
            listas=LISTAS,
            ubicaciones_por_unidad={},
        )
        for valida in validas:
            vistas += 1
            for elegido in (valida.oficio, valida.proveedor):
                assert elegido is None or (not elegido.ambiguo and elegido.codigo)
            assert not any("varios códigos" in a for a in valida.avisos)
            if par is not None:
                assert valida.oficio is not None
                assert valida.oficio.codigo == par.oficio.codigo
                assert valida.proveedor is not None
                assert valida.proveedor.codigo == par.proveedor_codigo
            elif oficio is not None:
                assert valida.oficio is not None
                assert valida.oficio.codigo == oficio.codigo
        for mala in con_error:
            assert [(e.columna, e.problema) for e in mala.errores] == [
                (PROVEEDOR, PROVEEDOR_DE_OTRO_OFICIO)
            ]
            assert oficio is not None and par is not None
            assert par.oficio.codigo != oficio.codigo
    # 1 vacía + 4 solo oficio + 5 solo par + 5 par con su oficio.
    assert vistas == 15


# --------------------------------------------------------------------------
# R36 · el casado en las cinco columnas
# --------------------------------------------------------------------------


def test_f071_r36_unidad_con_otra_mayuscula_se_toma_con_aviso() -> None:
    valida = una_valida(basica(unidad="  VIVIENDA 1 "))
    assert valida.unidad == Opcion(etiqueta="Vivienda 1", codigo="9901.V1")
    assert valida.avisos == (aviso_valor_tomado(UNIDAD, "Vivienda 1"),)


def test_f071_r36_texto_del_aviso() -> None:
    assert aviso_valor_tomado("Urgencia", "Urgente") == "Urgencia: se ha tomado «Urgente»"


def test_f071_r36_oficio_y_proveedor_con_otra_mayuscula() -> None:
    valida = una_valida(
        basica(oficio=ET_OFICIO_2.upper(), proveedor=ET_PAR_2_P2.lower())
    )
    assert valida.oficio == Elegido(
        etiqueta="Oficio ficticio 2", codigo="0020", ambiguo=False
    )
    assert valida.proveedor == Elegido(etiqueta="P2", codigo="P2", ambiguo=False)
    assert aviso_valor_tomado(OFICIO, ET_OFICIO_2) in valida.avisos
    assert aviso_valor_tomado(PROVEEDOR, ET_PAR_2_P2) in valida.avisos


def test_f071_r36_urgencia_y_listado_con_otra_mayuscula() -> None:
    valida = una_valida(basica(urgencia="urgente", listado="SEGUNDO LISTADO"))
    assert valida.urgencia is Urgencia.URGENTE
    # F-072 R12, R15 (sustituye a `listado is Listado.SEGUNDO`): se guarda el
    # código de la opción en `tipo_reclamacion` y `listado` nace nulo.
    assert (valida.tipo_reclamacion, valida.listado) == ("segundo", None)
    assert valida.avisos == (
        aviso_valor_tomado(URGENCIA, "Urgente"),
        aviso_valor_tomado(LISTADO, "Segundo listado"),
    )


def test_f071_r36_exactos_sin_aviso() -> None:
    valida = una_valida(
        basica(
            oficio=ET_OFICIO_1,
            proveedor=ET_PAR_1_P1,
            urgencia="Urgente",
            listado="Primer listado",
        )
    )
    assert valida.avisos == ()
    assert valida.urgencia is Urgencia.URGENTE
    # F-072 R12, R15 (sustituye a `listado is Listado.PRIMERO`).
    assert (valida.tipo_reclamacion, valida.listado) == ("primero", None)


def test_f071_r36_dos_por_clave_es_el_error_de_lista() -> None:
    listas = ListasCerradas(
        urgencias=LISTAS.urgencias,
        listados=(
            Opcion(etiqueta="Primer listado", codigo="primero"),
            Opcion(etiqueta="PRIMER LISTADO", codigo="segundo"),
        ),
    )
    errores = errores_de(basica(listado="primer listado"), listas=listas)
    assert [c for c, _ in errores] == [LISTADO]
    # Exacto sí casa aunque otra tenga la misma clave.
    valida = una_valida(basica(listado="PRIMER LISTADO"), listas=listas)
    # F-072 R12, R15 (sustituye a `listado is Listado.SEGUNDO`).
    assert (valida.tipo_reclamacion, valida.listado) == ("segundo", None)
    assert valida.avisos == ()


def test_f071_r36_tildes_no_casan() -> None:
    # La clave de F-060 no quita tildes: «Vivienda 1» no es «Vivíenda 1».
    assert [c for c, _ in errores_de(basica(unidad="Vivíenda 1"))] == [UNIDAD]


# --------------------------------------------------------------------------
# R37 · lo que ya no está en Sigrid
# --------------------------------------------------------------------------

TEXTO_YA_NO_ESTA = (
    "ese valor no está en Sigrid para esta obra (puede que haya cambiado desde "
    "que descargaste la plantilla): elígelo del desplegable de este fichero, que "
    "trae las listas de hoy"
)


@pytest.mark.parametrize("columna", [UNIDAD, OFICIO, PROVEEDOR])
def test_f071_r37_texto(columna: str) -> None:
    assert TEXTO_YA_NO_ESTA in ya_no_esta_en_sigrid(columna)


def test_f071_r37_unidad_que_ya_no_esta() -> None:
    assert errores_de(basica(unidad="Vivienda 9")) == [
        (UNIDAD, ya_no_esta_en_sigrid(UNIDAD))
    ]


def test_f071_r37_oficio_que_ya_no_esta() -> None:
    # Descargada cuando el 0040 estaba en la obra; hoy ya no.
    assert errores_de(basica(oficio="Oficio ficticio 4 (0040)")) == [
        (OFICIO, ya_no_esta_en_sigrid(OFICIO))
    ]


def test_f071_r37_proveedor_que_ya_no_esta() -> None:
    assert errores_de(
        basica(proveedor="Oficio ficticio 1 (0010) · Proveedor ficticio 9 (P9)")
    ) == [(PROVEEDOR, ya_no_esta_en_sigrid(PROVEEDOR))]


def test_f071_r37_etiqueta_de_grupo_v1_ya_no_casa() -> None:
    # La etiqueta de grupo de la v1 («Oficio ficticio 1», sin código) no es
    # una opción de la v2.
    assert errores_de(basica(oficio="Oficio ficticio 1")) == [
        (OFICIO, ya_no_esta_en_sigrid(OFICIO))
    ]


def test_f071_r37_urgencia_fuera_de_lista_sigue_su_texto() -> None:
    errores = errores_de(basica(urgencia="Muy urgente"))
    assert [c for c, _ in errores] == [URGENCIA]
    assert "urgencias" in errores[0][1]


# --------------------------------------------------------------------------
# R38 · fórmula, fecha/booleano y número
# --------------------------------------------------------------------------

_TASADAS = ["unidad", "ubicacion", "oficio", "proveedor", "urgencia", "listado"]


@pytest.mark.parametrize("columna", _TASADAS)
@pytest.mark.parametrize(
    ("mala", "problema"),
    [
        (celda("=B2", formula=True), FORMULA),
        (celda("2026-11-05", fecha=True), FECHA_EN_TASADA),
        (celda(True), FECHA_EN_TASADA),
        (celda(3.0), NUMERO_EN_TASADA),
        (celda(4), NUMERO_EN_TASADA),
    ],
)
def test_f071_r38_tasadas(columna: str, mala: CeldaLeida, problema: str) -> None:
    errores = errores_de(basica(**{columna: mala}))
    assert errores == [(_COLUMNAS[columna], problema)]


# --------------------------------------------------------------------------
# R39 · todas las columnas, en su orden
# --------------------------------------------------------------------------


def test_f071_r39_orden_de_los_errores_es_el_de_las_columnas() -> None:
    f = fila(
        unidad="Vivienda 9",
        ubicacion="Estancia A-99",
        detalle="x" * 2001,
        oficio="Oficio ficticio 9 (0090)",
        proveedor="Oficio ficticio 9 (0090) · P9",
        urgencia="Muy urgente",
        listado="Tercer listado",
    )
    columnas = [c for c, _ in errores_de(f)]
    assert columnas == [
        UNIDAD,
        UBICACION,
        DESCRIPCION,
        DETALLE,
        OFICIO,
        PROVEEDOR,
        URGENCIA,
        LISTADO,
    ]


def test_f071_r39_ubicacion_de_otra_unidad_y_proveedor_de_otro_oficio() -> None:
    errores = errores_de(
        basica(ubicacion="Estancia A-04", oficio=ET_OFICIO_1, proveedor=ET_PAR_2_P1)
    )
    assert errores == [
        (UBICACION, UBICACION_FUERA_DE_LA_UNIDAD),
        (PROVEEDOR, PROVEEDOR_DE_OTRO_OFICIO),
    ]


def test_f071_r39_varias_filas_independientes() -> None:
    buena = basica(ubicacion="Estancia A-01")
    mala = fila(numero=3, unidad="Vivienda 2", descripcion="Otra", ubicacion="Estancia A-01")
    validas, con_error = validar(buena, mala)
    assert [v.fila for v in validas] == [2]
    assert [(m.fila.numero, [e.columna for e in m.errores]) for m in con_error] == [
        (3, [UBICACION])
    ]
    assert con_error[0].fila is mala


def test_f071_r39_fila_vacia_se_ignora() -> None:
    assert validar(fila(errores="lo rellena el sistema")) == ((), ())


# --------------------------------------------------------------------------
# R41 · clave de duplicado
# --------------------------------------------------------------------------


def test_f071_r41_clave_igual_con_otra_mayuscula_en_la_ubicacion() -> None:
    a = clave_de_duplicado(
        obra_codigo="9901",
        unidad_codigo="9901.V1",
        ubicacion="Estancia A-01",
        descripcion="Grieta ficticia",
    )
    b = clave_de_duplicado(
        obra_codigo="9901",
        unidad_codigo="9901.V1",
        ubicacion="ESTANCIA A-01",
        descripcion="Grieta ficticia",
    )
    assert a == b


def test_f071_r41_la_ubicacion_casada_da_la_misma_clave_que_la_exacta() -> None:
    exacta = una_valida(basica(ubicacion="Estancia A-01"))
    casada = una_valida(basica(ubicacion="ESTANCIA A-01"))
    assert exacta.ubicacion == casada.ubicacion == "Estancia A-01"
