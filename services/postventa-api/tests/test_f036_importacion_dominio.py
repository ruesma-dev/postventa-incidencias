# services/postventa-api/tests/test_f036_importacion_dominio.py
"""F-036 · T5: reconocer la plantilla, validar filas y duplicados (dominio puro).

`design.md` §4.2–§4.5. Aquí se decide **qué entra en la bandeja** y con qué
unidad, oficio y proveedor: el fallo típico —una incidencia que acaba en otra
villa u otro industrial— no se ve hasta que alguien va a la vivienda. Por eso
todo valor tasado se compara **exacto** (decisión 7) y cada caso de la spec es
un test con su requisito en el nombre.

Sin red, sin Sigrid, sin base de datos y sin `openpyxl`: el libro leído se
construye a mano, igual que las opciones de `Oficio` y `Proveedor`
(`OpcionOficio`, `OpcionProveedor`), que en producción calcula T7 con los
grupos vigentes. Los nombres de proveedor son **inventados**.

Los textos de la muestra (`docs/referencia/05_excel_creacion_incidencias.md`)
se usan tal cual donde importan: los cinco «Miras de hierro…» (R36).
"""

from __future__ import annotations

import dataclasses
import hashlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from domain.models import importacion
from domain.models.equivalencias import Catalogo, Grupo
from domain.models.errores import FicheroNoEsPlantilla
from domain.models.importacion import (
    CeldaLeida,
    Elegido,
    ErrorDeFila,
    EstadoFilaImportada,
    EstadoImportacion,
    FilaConError,
    FilaLeida,
    GrupoDeClave,
    IncidenciaEnBandeja,
    IncidenciaValida,
    LibroLeido,
    agrupar_por_clave,
    clave_de_duplicado,
    reconocer_plantilla,
    resolver_oficio_y_proveedor,
    validar_filas,
)
from domain.models.plantilla_incidencias import (
    CABECERA,
    COLUMNA_ERRORES,
    IDENTIFICADOR_PLANTILLA,
    MAX_DESCRIPCION,
    MAX_DETALLE,
    MAX_FILAS,
    CatalogoObra,
    Listado,
    ListasCerradas,
    OficioObra,
    Opcion,
    OpcionOficio,
    OpcionProveedor,
    ProveedorEnObra,
    UnidadPosventa,
    Urgencia,
)

# --------------------------------------------------------------------------
# Datos de prueba
# --------------------------------------------------------------------------

CATALOGO = CatalogoObra(
    obra_codigo="0677",
    obra_nombre="Obra de ejemplo",
    unidades=(
        UnidadPosventa(codigo="0677.03VILLA 1.", nombre="Villa 1"),
        UnidadPosventa(codigo="0677.03VILLA 2.", nombre="Viviendas Bloque Villa 2"),
    ),
    oficios=(
        OficioObra(codigo="0046", nombre="Carpinteria de madera"),
        OficioObra(codigo="0143", nombre="Carpintería de madera"),
        OficioObra(codigo="0028", nombre="Pintura"),
    ),
    proveedores=(
        ProveedorEnObra(
            oficio_codigo="0046",
            proveedor_codigo="P1",
            proveedor_nombre="Carpinterías Ejemplo S.L.",
        ),
        ProveedorEnObra(
            oficio_codigo="0046",
            proveedor_codigo="P2",
            proveedor_nombre="Juan Ejemplo Ejemplo",
        ),
        ProveedorEnObra(
            oficio_codigo="0143",
            proveedor_codigo="P2",
            proveedor_nombre="Juan Ejemplo Ejemplo",
        ),
        ProveedorEnObra(
            oficio_codigo="0028",
            proveedor_codigo="P3",
            proveedor_nombre="Pinturas Ejemplo S.A.",
        ),
    ),
)

LISTAS = ListasCerradas(
    ubicaciones=(
        "Sala / estudio",
        "Dormitorio 1",
        "Dormitorio 3",
        "Dormitorio 4",
        "Baño de planta baja",
        "Cocina",
    ),
    urgencias=(
        Opcion(etiqueta="Urgente", codigo="urgente"),
        Opcion(etiqueta="Peligro para la seguridad", codigo="seguridad"),
    ),
    listados=(
        Opcion(etiqueta="Primer listado", codigo="primero"),
        Opcion(etiqueta="Segundo listado", codigo="segundo"),
    ),
)

# El ejemplo de `design.md` §15.5: el grupo «Carpintería de madera» son 0046 y
# 0143; el proveedor P1 está en la obra con 0046, y el P2 con 0143 y con 0046.
CARPINTERIA = OpcionOficio(
    etiqueta="Carpintería de madera",
    grupo=Grupo(
        catalogo=Catalogo.OFICIO,
        codigos=frozenset({"0046", "0143"}),
        etiqueta="Carpintería de madera",
    ),
    codigos_en_obra=("0046", "0143"),
)
PINTURA = OpcionOficio(
    etiqueta="Pintura",
    grupo=Grupo(
        catalogo=Catalogo.OFICIO, codigos=frozenset({"0028"}), etiqueta="Pintura"
    ),
    codigos_en_obra=("0028",),
)


def _grupo_proveedor(codigo: str, nombre: str) -> Grupo:
    # Sin agrupación de proveedores (F-050) cada código es su propio grupo
    # (costura de design §15.8, cerrada en T7 con `Catalogo.PROVEEDOR`).
    return Grupo(
        catalogo=Catalogo.PROVEEDOR, codigos=frozenset({codigo}), etiqueta=nombre
    )


CARPINTERIA_P1 = OpcionProveedor(
    etiqueta="Carpintería de madera · Carpinterías Ejemplo S.L.",
    oficio=CARPINTERIA,
    grupo=_grupo_proveedor("P1", "Carpinterías Ejemplo S.L."),
    filas_en_obra=(("0046", "P1"),),
)
CARPINTERIA_P2 = OpcionProveedor(
    etiqueta="Carpintería de madera · Juan Ejemplo Ejemplo",
    oficio=CARPINTERIA,
    grupo=_grupo_proveedor("P2", "Juan Ejemplo Ejemplo"),
    filas_en_obra=(("0046", "P2"), ("0143", "P2")),
)
PINTURA_P3 = OpcionProveedor(
    etiqueta="Pintura · Pinturas Ejemplo S.A.",
    oficio=PINTURA,
    grupo=_grupo_proveedor("P3", "Pinturas Ejemplo S.A."),
    filas_en_obra=(("0028", "P3"),),
)
OPCIONES_OFICIO = (CARPINTERIA, PINTURA)
OPCIONES_PROVEEDOR = (CARPINTERIA_P1, CARPINTERIA_P2, PINTURA_P3)


def celda(
    valor: str | float | None,
    *,
    formula: bool = False,
    fecha: bool = False,
) -> CeldaLeida:
    return CeldaLeida(
        valor=valor,
        es_formula=formula,
        es_fecha_o_booleano=fecha,
        texto_original=None if valor is None else str(valor),
    )


def fila(numero: int, **valores: object) -> FilaLeida:
    """Una fila leída; las claves son las columnas con `_` por espacio y sin tildes."""
    nombres = {
        "unidad": "Unidad",
        "ubicacion": "Ubicación",
        "descripcion": "Descripción corta",
        "detalle": "Detalle",
        "oficio": "Oficio",
        "proveedor": "Proveedor",
        "urgencia": "Urgencia",
        "listado": "Listado",
        "errores": COLUMNA_ERRORES,
    }
    celdas = {}
    for clave, valor in valores.items():
        celdas[nombres[clave]] = (
            valor if isinstance(valor, CeldaLeida) else celda(valor)
        )  # type: ignore[arg-type]
    return FilaLeida(numero=numero, celdas=celdas)


def validar(
    *filas: FilaLeida,
) -> tuple[tuple[IncidenciaValida, ...], tuple[FilaConError, ...]]:
    return validar_filas(
        filas,
        catalogo=CATALOGO,
        opciones_oficio=OPCIONES_OFICIO,
        opciones_proveedor=OPCIONES_PROVEEDOR,
        listas=LISTAS,
    )


def una_valida(f: FilaLeida) -> IncidenciaValida:
    validas, con_error = validar(f)
    assert con_error == ()
    assert len(validas) == 1
    return validas[0]


def errores_de(f: FilaLeida) -> list[tuple[str, str]]:
    validas, con_error = validar(f)
    assert validas == ()
    assert len(con_error) == 1
    assert con_error[0].fila is f
    return [(e.columna, e.problema) for e in con_error[0].errores]


def libro(**cambios: object) -> LibroLeido:
    base = LibroLeido(
        identificador=IDENTIFICADOR_PLANTILLA,
        version=1,
        obra_codigo="0677",
        cabecera=CABECERA,
        filas=(fila(2, unidad="Villa 1", descripcion="Sellar sifón"),),
        parece_formato_antiguo=False,
    )
    return replace(base, **cambios)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# R17–R20 · reconocer la plantilla
# --------------------------------------------------------------------------


def test_f036_reconocer_plantilla_buena_devuelve_la_obra_normalizada() -> None:
    assert reconocer_plantilla(libro()) == "0677"
    assert reconocer_plantilla(libro(obra_codigo=" 06 77 ")) == "0677"


@pytest.mark.parametrize(
    "identificador", [None, "", "otra.cosa", IDENTIFICADOR_PLANTILLA + " "]
)
def test_f036_r17_no_es_la_plantilla(identificador: str | None) -> None:
    with pytest.raises(FicheroNoEsPlantilla) as exc:
        reconocer_plantilla(libro(identificador=identificador))
    assert exc.value.codigo == "no_es_la_plantilla"
    assert "Descarga la plantilla de la obra desde el portal" in exc.value.motivo


@pytest.mark.parametrize("identificador", [None, "otra.cosa"])
def test_f036_r17_formato_antiguo(identificador: str | None) -> None:
    with pytest.raises(FicheroNoEsPlantilla) as exc:
        reconocer_plantilla(
            libro(identificador=identificador, parece_formato_antiguo=True)
        )
    assert exc.value.codigo == "formato_antiguo"
    assert "ya no se admite" in exc.value.motivo
    assert "Descarga la plantilla de la obra desde el portal" in exc.value.motivo


def test_f036_r17_el_identificador_manda_sobre_la_forma_antigua() -> None:
    # Con el identificador bueno no hay formato antiguo que valga.
    assert reconocer_plantilla(libro(parece_formato_antiguo=True)) == "0677"


@pytest.mark.parametrize("version", [None, 0, 2, 99])
def test_f036_r18_version_no_soportada(version: int | None) -> None:
    with pytest.raises(FicheroNoEsPlantilla) as exc:
        reconocer_plantilla(libro(version=version))
    assert exc.value.codigo == "version_no_soportada"
    assert "Descarga la plantilla de la obra desde el portal" in exc.value.motivo


def test_f036_r18_la_version_se_mira_antes_que_la_cabecera() -> None:
    with pytest.raises(FicheroNoEsPlantilla) as exc:
        reconocer_plantilla(libro(version=2, cabecera=("Otra",)))
    assert exc.value.codigo == "version_no_soportada"


def test_f036_r19_cabecera_con_espacios_se_admite() -> None:
    cabecera = tuple(f"  {c} " for c in CABECERA) + ("", "  ")
    assert reconocer_plantilla(libro(cabecera=cabecera)) == "0677"


def _motivo_de_cabecera(cabecera: tuple[str, ...]) -> str:
    with pytest.raises(FicheroNoEsPlantilla) as exc:
        reconocer_plantilla(libro(cabecera=cabecera))
    assert exc.value.codigo == "cabecera_distinta"
    assert exc.value.motivo.startswith(
        "La cabecera de la hoja «Incidencias» no es la de la plantilla: "
    )
    return exc.value.motivo


def test_f036_r19_falta_una_columna() -> None:
    sin_proveedor = tuple(c for c in CABECERA if c != "Proveedor")
    assert _motivo_de_cabecera(sin_proveedor).endswith("falta la columna «Proveedor».")


def test_f036_r19_sobra_una_columna() -> None:
    motivo = _motivo_de_cabecera((*CABECERA[:3], "Teléfono", *CABECERA[3:]))
    assert motivo.endswith("sobra la columna «Teléfono».")


def test_f036_r19_sobra_una_columna_sin_nombre_en_medio() -> None:
    motivo = _motivo_de_cabecera((*CABECERA[:2], "", *CABECERA[2:]))
    assert motivo.endswith("sobra una columna sin nombre (la 3.ª).")


def test_f036_r19_columna_repetida() -> None:
    motivo = _motivo_de_cabecera((*CABECERA, "Unidad"))
    assert motivo.endswith("la columna «Unidad» está repetida.")


def test_f036_r19_columna_movida() -> None:
    movida = ("Ubicación", "Unidad", *CABECERA[2:])
    motivo = _motivo_de_cabecera(movida)
    assert motivo.endswith(
        "la columna «Ubicación» está movida: en la posición 1 va «Unidad»."
    )


def test_f036_r19_columna_movida_al_final() -> None:
    movida = (*CABECERA[:7], CABECERA[8], CABECERA[7])
    motivo = _motivo_de_cabecera(movida)
    assert motivo.endswith(
        f"la columna «{CABECERA[8]}» está movida: en la posición 8 va «Listado»."
    )


def test_f036_r19_varios_problemas_a_la_vez() -> None:
    cabecera = ("Unidad", "Ubicación", "Descripción", *CABECERA[3:])
    motivo = _motivo_de_cabecera(cabecera)
    assert motivo.endswith(
        "falta la columna «Descripción corta»; sobra la columna «Descripción»."
    )


def test_f036_r19_cabecera_vacia() -> None:
    motivo = _motivo_de_cabecera(())
    assert "falta la columna «Unidad»" in motivo
    assert "falta la columna «Errores (lo rellena el sistema)»" in motivo


def test_f036_r20_mil_filas_se_admiten_mil_una_no() -> None:
    mil = tuple(fila(n + 2, unidad="Villa 1") for n in range(MAX_FILAS))
    assert reconocer_plantilla(libro(filas=mil)) == "0677"
    with pytest.raises(FicheroNoEsPlantilla) as exc:
        reconocer_plantilla(libro(filas=(*mil, fila(MAX_FILAS + 2, unidad="Villa 1"))))
    assert exc.value.codigo == "demasiadas_filas"
    assert "1001" in exc.value.motivo
    assert "1000" in exc.value.motivo


def test_f036_r115_datos_por_debajo_del_tope_son_demasiadas_filas() -> None:
    # Pocas filas leídas, pero el lector vio datos por debajo de la fila 1001:
    # el mismo error de R20, sin contar las filas (sexta enmienda).
    assert libro().datos_fuera_del_tope is False
    with pytest.raises(FicheroNoEsPlantilla) as exc:
        reconocer_plantilla(libro(datos_fuera_del_tope=True))
    assert exc.value.codigo == "demasiadas_filas"
    assert exc.value.motivo == (
        "El fichero trae datos por debajo de la fila 1001 y el máximo es 1000. "
        "Pártelo en varios ficheros."
    )


def test_f036_r115_mas_de_1000_filas_y_datos_por_debajo_dice_cuantas() -> None:
    mil_una = tuple(fila(n + 2, unidad="Villa 1") for n in range(MAX_FILAS + 1))
    with pytest.raises(FicheroNoEsPlantilla) as exc:
        reconocer_plantilla(libro(filas=mil_una, datos_fuera_del_tope=True))
    assert exc.value.motivo == (
        "El fichero trae 1001 filas con datos y el máximo es 1000. "
        "Pártelo en varios ficheros."
    )


def test_f036_r115_el_tope_se_comprueba_donde_las_filas() -> None:
    # Después de la cabecera y antes de la obra (design §4.2).
    with pytest.raises(FicheroNoEsPlantilla) as exc:
        reconocer_plantilla(libro(cabecera=("x",), datos_fuera_del_tope=True))
    assert exc.value.codigo == "cabecera_distinta"
    with pytest.raises(FicheroNoEsPlantilla) as exc:
        reconocer_plantilla(libro(obra_codigo="06/77", datos_fuera_del_tope=True))
    assert exc.value.codigo == "demasiadas_filas"


@pytest.mark.parametrize("obra", [None, "", "06/77", "X" * 25])
def test_f036_r9_obra_de_los_metadatos_invalida(obra: str | None) -> None:
    with pytest.raises(FicheroNoEsPlantilla) as exc:
        reconocer_plantilla(libro(obra_codigo=obra))
    assert exc.value.codigo == "obra_invalida"
    assert "Descarga la plantilla de la obra desde el portal" in exc.value.motivo


def test_f036_reconocer_orden_de_comprobaciones() -> None:
    # identificador → versión → cabecera → filas → obra (design §4.2).
    todo_mal = {
        "version": 2,
        "cabecera": ("x",),
        "filas": tuple(fila(n, unidad="Villa 1") for n in range(MAX_FILAS + 1)),
        "obra_codigo": "06/77",
    }
    codigos = []
    for quitar in ("identificador", "version", "cabecera", "filas", "obra_codigo"):
        cambios = {"identificador": None, **todo_mal}
        buenos = {
            "identificador": IDENTIFICADOR_PLANTILLA,
            "version": 1,
            "cabecera": CABECERA,
            "filas": (),
            "obra_codigo": "0677",
        }
        for ya in ("identificador", "version", "cabecera", "filas", "obra_codigo"):
            if ya == quitar:
                break
            cambios[ya] = buenos[ya]
        with pytest.raises(FicheroNoEsPlantilla) as exc:
            reconocer_plantilla(libro(**cambios))
        codigos.append(exc.value.codigo)
    assert codigos == [
        "no_es_la_plantilla",
        "version_no_soportada",
        "cabecera_distinta",
        "demasiadas_filas",
        "obra_invalida",
    ]


# --------------------------------------------------------------------------
# R23–R34 · validar fila a fila
# --------------------------------------------------------------------------


def test_f036_fila_minima_valida() -> None:
    v = una_valida(fila(2, unidad="Villa 1", descripcion="Sellar sifón"))
    assert v == IncidenciaValida(
        fila=2,
        unidad=Opcion(etiqueta="Villa 1", codigo="0677.03VILLA 1."),
        ubicacion=None,
        descripcion="Sellar sifón",
        detalle=None,
        oficio=None,
        proveedor=None,
        urgencia=None,
        listado=None,
        avisos=(),
    )


def test_f036_fila_completa_valida() -> None:
    v = una_valida(
        fila(
            7,
            unidad="Viviendas Bloque Villa 2",
            ubicacion="Cocina",
            descripcion="Faltan topes de puerta corredera",
            detalle="  Para cerrar y abrir.\nLas dos hojas.  ",
            oficio="Pintura",
            proveedor="Pintura · Pinturas Ejemplo S.A.",
            urgencia="Peligro para la seguridad",
            listado="Segundo listado",
        )
    )
    assert v.fila == 7
    assert v.unidad == Opcion(
        etiqueta="Viviendas Bloque Villa 2", codigo="0677.03VILLA 2."
    )
    assert v.ubicacion == "Cocina"
    assert v.detalle == "Para cerrar y abrir.\nLas dos hojas."
    assert v.oficio == Elegido(etiqueta="Pintura", codigo="0028", ambiguo=False)
    assert v.proveedor == Elegido(
        etiqueta="Pinturas Ejemplo S.A.", codigo="P3", ambiguo=False
    )
    assert v.urgencia is Urgencia.SEGURIDAD
    assert v.listado is Listado.SEGUNDO
    assert v.avisos == ()


def test_f036_r31_urgente_y_primer_listado() -> None:
    v = una_valida(
        fila(
            2,
            unidad="Villa 1",
            descripcion="x",
            urgencia="Urgente",
            listado="Primer listado",
        )
    )
    assert v.urgencia is Urgencia.URGENTE
    assert v.listado is Listado.PRIMERO


def test_f036_r23_fila_vacia_se_ignora() -> None:
    vacias = (
        fila(2),
        fila(3, unidad=None, descripcion="", detalle="   "),
        fila(4, errores="Fila 4 del fichero subido · Unidad: falta"),  # R66
        fila(5, unidad="\n\t"),
    )
    assert validar(*vacias) == ((), ())


def test_f036_r66_la_columna_errores_se_ignora() -> None:
    v = una_valida(
        fila(2, unidad="Villa 1", descripcion="x", errores="=HIPERVINCULO(1)")
    )
    assert v.descripcion == "x"


def test_f036_r25_falta_la_unidad() -> None:
    assert errores_de(fila(2, descripcion="Sellar sifón")) == [
        (
            "Unidad",
            "falta la unidad; en esta plantilla no se hereda de la fila de arriba",
        )
    ]


def test_f036_r25_fila_sin_unidad_debajo_de_una_con_unidad() -> None:
    primera = fila(2, unidad="Villa 1", descripcion="Sellar sifón")
    segunda = fila(3, descripcion="Enlechar azulejos ducha")
    validas, con_error = validar(primera, segunda)
    assert [v.fila for v in validas] == [2]
    assert [(c.fila.numero, [e.columna for e in c.errores]) for c in con_error] == [
        (3, ["Unidad"])
    ]


@pytest.mark.parametrize(
    "valor",
    [
        "villa 1",
        "Villa 1 ",
        " Villa 1",
        "Villa  1",
        "VILLA 1",
        "Villa 1.",
        "0677.03VILLA 1.",
    ],
)
def test_f036_r26_unidad_exacta(valor: str) -> None:
    assert errores_de(fila(2, unidad=valor, descripcion="x")) == [
        (
            "Unidad",
            (
                "ese valor no está en la lista de unidades de la obra: elígelo del desplegable "
                "(cuidado con mayúsculas, tildes y espacios); si la plantilla es antigua, "
                "descarga una nueva"
            ),
        )
    ]


def test_f036_r27_descripcion_obligatoria() -> None:
    for vacia in (None, "", "  \n "):
        assert errores_de(fila(2, unidad="Villa 1", descripcion=vacia)) == [
            ("Descripción corta", "falta la descripción corta")
        ]


def test_f036_r27_descripcion_saltos_y_espacios() -> None:
    v = una_valida(
        fila(
            2, unidad="Villa 1", descripcion="  Pared  de casoneto\nsin   anclaje \r\n"
        )
    )
    assert v.descripcion == "Pared de casoneto sin anclaje"


def test_f036_r27_ciento_veintiocho_si_ciento_veintinueve_no() -> None:
    assert (
        una_valida(
            fila(2, unidad="Villa 1", descripcion="a" * MAX_DESCRIPCION)
        ).descripcion
        == "a" * 128
    )
    assert errores_de(
        fila(2, unidad="Villa 1", descripcion="a" * (MAX_DESCRIPCION + 1))
    ) == [
        (
            "Descripción corta",
            (
                "la descripción corta tiene 129 caracteres y el máximo es 128: deja lo "
                "esencial y pasa el resto a «Detalle»"
            ),
        )
    ]


def test_f036_r27_el_tope_se_mira_despues_de_colapsar() -> None:
    # 130 caracteres en bruto que colapsados son 128.
    bruto = "a" * 64 + "   " + "b" * 63
    assert len(" ".join(bruto.split())) == 128
    assert (
        una_valida(fila(2, unidad="Villa 1", descripcion=bruto)).descripcion
        == "a" * 64 + " " + "b" * 63
    )


@pytest.mark.parametrize(("valor", "texto"), [(12, "12"), (3.5, "3.5"), (4.0, "4")])
def test_f036_r32_numero_en_texto_libre_es_texto(valor: float, texto: str) -> None:
    v = una_valida(fila(2, unidad="Villa 1", descripcion=valor, detalle=valor))
    assert v.descripcion == texto
    assert v.detalle == texto


def test_f036_r28_detalle_dos_mil_si_dos_mil_uno_no() -> None:
    assert (
        una_valida(
            fila(2, unidad="Villa 1", descripcion="x", detalle="d" * MAX_DETALLE)
        ).detalle
        == "d" * 2000
    )
    assert errores_de(
        fila(2, unidad="Villa 1", descripcion="x", detalle="d" * (MAX_DETALLE + 1))
    ) == [("Detalle", "el detalle tiene 2001 caracteres y el máximo es 2000")]


def test_f036_r28_detalle_conserva_saltos_y_recorta_extremos() -> None:
    v = una_valida(
        fila(2, unidad="Villa 1", descripcion="x", detalle="\n  uno\n\n dos  \n")
    )
    assert v.detalle == "uno\n\n dos"


def test_f036_r28_detalle_se_mide_recortado() -> None:
    v = una_valida(
        fila(
            2,
            unidad="Villa 1",
            descripcion="x",
            detalle="  " + "d" * MAX_DETALLE + "  ",
        )
    )
    assert v.detalle == "d" * 2000


@pytest.mark.parametrize(
    "valor", ["cocina", "Cocina ", "COCINA", "Sala/estudio", "SALA/ ESTUDIO"]
)
def test_f036_r29_ubicacion_exacta(valor: str) -> None:
    assert errores_de(fila(2, unidad="Villa 1", ubicacion=valor, descripcion="x")) == [
        (
            "Ubicación",
            (
                "ese valor no está en la lista de ubicaciones: elígelo del desplegable "
                "(cuidado con mayúsculas, tildes y espacios)"
            ),
        )
    ]


@pytest.mark.parametrize(
    "valor", ["pintura", "Pintura ", "Carpinteria de madera", "0028"]
)
def test_f036_r30_oficio_exacto(valor: str) -> None:
    assert errores_de(fila(2, unidad="Villa 1", descripcion="x", oficio=valor)) == [
        (
            "Oficio",
            (
                "ese valor no está en la lista de oficios de la obra: elígelo del desplegable "
                "(cuidado con mayúsculas, tildes y espacios)"
            ),
        )
    ]


@pytest.mark.parametrize(
    ("columna", "valor", "lista"),
    [
        ("urgencia", "urgente", "urgencias"),
        ("urgencia", "Normal", "urgencias"),
        ("urgencia", "Peligro de seguridad", "urgencias"),
        ("listado", "Primero", "listados"),
        ("listado", "primer listado", "listados"),
    ],
)
def test_f036_r31_urgencia_y_listado_exactos(
    columna: str, valor: str, lista: str
) -> None:
    nombre = {"urgencia": "Urgencia", "listado": "Listado"}[columna]
    assert errores_de(
        fila(2, unidad="Villa 1", descripcion="x", **{columna: valor})
    ) == [
        (
            nombre,
            (
                f"ese valor no está en la lista de {lista}: elígelo del desplegable "
                "(cuidado con mayúsculas, tildes y espacios)"
            ),
        )
    ]


FORMULA = "la celda lleva una fórmula: escribe el texto"
FECHA_TEXTO = "la celda lleva una fecha o un valor verdadero/falso: escribe el texto"
FECHA_TASADA = "la celda lleva una fecha o un valor verdadero/falso: elige un valor del desplegable"
NUMERO_TASADA = "la celda lleva un número: elige un valor del desplegable"


@pytest.mark.parametrize(
    "columna",
    [
        "unidad",
        "ubicacion",
        "descripcion",
        "detalle",
        "oficio",
        "proveedor",
        "urgencia",
        "listado",
    ],
)
def test_f036_r32_formula_en_cualquier_columna(columna: str) -> None:
    valores = {
        "unidad": "Villa 1",
        "descripcion": "x",
        columna: celda("=A1", formula=True),
    }
    errores = errores_de(fila(2, **valores))
    assert [p for _, p in errores] == [FORMULA]


def test_f036_r32_formula_con_valor_de_texto_valido_sigue_siendo_error() -> None:
    # Aunque la fórmula dé justo una etiqueta buena, es una fórmula.
    assert errores_de(
        fila(2, unidad=celda("Villa 1", formula=True), descripcion="x")
    ) == [("Unidad", FORMULA)]


@pytest.mark.parametrize(
    ("columna", "texto"),
    [
        ("descripcion", FECHA_TEXTO),
        ("detalle", FECHA_TEXTO),
        ("urgencia", FECHA_TASADA),
        ("unidad", FECHA_TASADA),
    ],
)
def test_f036_r32_fecha_o_booleano_es_error(columna: str, texto: str) -> None:
    valores = {
        "unidad": "Villa 1",
        "descripcion": "x",
        columna: celda("2026-09-29", fecha=True),
    }
    assert [p for _, p in errores_de(fila(2, **valores))] == [texto]


def test_f036_r32_booleano_sin_marca_tambien_es_error() -> None:
    assert errores_de(fila(2, unidad="Villa 1", descripcion=celda(True))) == [
        ("Descripción corta", FECHA_TEXTO)
    ]  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "columna", ["unidad", "ubicacion", "oficio", "proveedor", "urgencia", "listado"]
)
@pytest.mark.parametrize("numero", [1, 2.5])
def test_f036_r32_numero_en_columna_tasada(columna: str, numero: float) -> None:
    valores = {"unidad": "Villa 1", "descripcion": "x", columna: numero}
    assert [p for _, p in errores_de(fila(2, **valores))] == [NUMERO_TASADA]


def test_f036_r24_r33_errores_de_varias_filas_y_columnas_a_la_vez() -> None:
    f2 = fila(2, ubicacion="cocina", descripcion="a" * 200, oficio="Fontanería")
    f3 = fila(3, unidad="Villa 1", descripcion="Sellar sifón")
    f4 = fila(
        4,
        unidad="Villa 9",
        descripcion="",
        urgencia="URGENTE",
        listado=celda("=1", formula=True),
    )
    validas, con_error = validar(f2, f3, f4)
    assert [v.fila for v in validas] == [3]
    assert [c.fila for c in con_error] == [f2, f4]
    assert [(e.fila, e.columna) for c in con_error for e in c.errores] == [
        (2, "Unidad"),
        (2, "Ubicación"),
        (2, "Descripción corta"),
        (2, "Oficio"),
        (4, "Unidad"),
        (4, "Descripción corta"),
        (4, "Urgencia"),
        (4, "Listado"),
    ]
    assert all(
        isinstance(e, ErrorDeFila) and e.problema for c in con_error for e in c.errores
    )


def test_f036_r33_orden_de_las_filas_se_conserva() -> None:
    filas = [fila(n, unidad="Villa 1", descripcion=f"d{n}") for n in (9, 3, 5)]
    validas, _ = validar(*filas)
    assert [v.fila for v in validas] == [9, 3, 5]


def test_f036_validar_filas_devuelve_tuplas() -> None:
    validas, con_error = validar(fila(2, unidad="Villa 1", descripcion="x"), fila(3))
    assert isinstance(validas, tuple)
    assert isinstance(con_error, tuple)


# --------------------------------------------------------------------------
# R34 · avisos
# --------------------------------------------------------------------------

AVISO_URGENCIA = (
    "menciona peligro, seguridad o urgencia y la columna «Urgencia» está vacía: "
    "márcala si corresponde"
)
AVISO_MAYUSCULAS = (
    "la descripción corta va casi toda en mayúsculas: escríbela normal y marca la "
    "urgencia en su columna"
)


@pytest.mark.parametrize(
    ("descripcion", "detalle"),
    [
        ("Se mueve la mampara, peligro de seguridad.", None),
        ("Se mueve la mampara", "PELIGRO"),
        ("Pandeos en la escalera, error ESTRUCTURAL", None),
        ("Arreglar con urgencia", None),
        ("Es urgente", None),
        ("Falta de Seguridad", None),
        ("Peligró", None),  # sin tildes
    ],
)
def test_f036_r34_aviso_de_urgencia_con_urgencia_vacia(
    descripcion: str, detalle: str | None
) -> None:
    v = una_valida(fila(2, unidad="Villa 1", descripcion=descripcion, detalle=detalle))
    assert v.avisos == (AVISO_URGENCIA,)


def test_f036_r34_sin_aviso_si_la_urgencia_esta_marcada() -> None:
    v = una_valida(
        fila(
            2, unidad="Villa 1", descripcion="Peligro de seguridad", urgencia="Urgente"
        )
    )
    assert v.avisos == ()


def test_f036_r34_sin_aviso_sin_palabras() -> None:
    assert (
        una_valida(
            fila(2, unidad="Villa 1", descripcion="Sellar sifón", detalle="Nada más")
        ).avisos
        == ()
    )


def test_f036_r34_mayusculas_umbral() -> None:
    # 20 letras: 12 en mayúscula (60 %) no avisa; 13 (65 %) sí.
    doce = "ABCDEFGHIJKL" + "mnopqrst"
    trece = "ABCDEFGHIJKLM" + "nopqrst"
    assert una_valida(fila(2, unidad="Villa 1", descripcion=doce)).avisos == ()
    assert una_valida(fila(2, unidad="Villa 1", descripcion=trece)).avisos == (
        AVISO_MAYUSCULAS,
    )


def test_f036_r34_mayusculas_hacen_falta_veinte_letras() -> None:
    # 19 letras en mayúscula (con cifras y signos, que no cuentan): no avisa.
    assert (
        una_valida(
            fila(2, unidad="Villa 1", descripcion="ABCDEFGHIJ KLMNOPQRS 123 !!")
        ).avisos
        == ()
    )
    assert una_valida(
        fila(2, unidad="Villa 1", descripcion="ABCDEFGHIJ KLMNOPQRST 123")
    ).avisos == (AVISO_MAYUSCULAS,)


def test_f036_r34_mayusculas_con_tildes_cuentan_como_letras() -> None:
    assert una_valida(fila(2, unidad="Villa 1", descripcion="ÁÉÍÓÚÑÜ" * 3)).avisos == (
        AVISO_MAYUSCULAS,
    )


def test_f036_r34_los_dos_avisos_de_la_muestra() -> None:
    v = una_valida(
        fila(
            2,
            unidad="Villa 1",
            descripcion="MAMPARA SE MUEVE MUCHO. INESTABLE. PELIGRO DE SEGURIDAD",
        )
    )
    assert v.avisos == (AVISO_URGENCIA, AVISO_MAYUSCULAS)


# --------------------------------------------------------------------------
# R73–R76, R93, R94, R99 · oficio y proveedor
# --------------------------------------------------------------------------


def test_f036_r93_design_15_5_solo_oficio_con_dos_codigos_es_ambiguo() -> None:
    oficio, proveedor = resolver_oficio_y_proveedor(CARPINTERIA, None)
    assert oficio == Elegido(
        etiqueta="Carpintería de madera", codigo=None, ambiguo=True
    )
    assert proveedor is None


def test_f036_r94_design_15_5_el_proveedor_deshace_la_ambiguedad() -> None:
    oficio, proveedor = resolver_oficio_y_proveedor(CARPINTERIA, CARPINTERIA_P1)
    assert oficio == Elegido(
        etiqueta="Carpintería de madera", codigo="0046", ambiguo=False
    )
    assert proveedor == Elegido(
        etiqueta="Carpinterías Ejemplo S.L.", codigo="P1", ambiguo=False
    )


def test_f036_r94_design_15_5_el_proveedor_que_no_la_deshace() -> None:
    oficio, proveedor = resolver_oficio_y_proveedor(CARPINTERIA, CARPINTERIA_P2)
    assert oficio == Elegido(
        etiqueta="Carpintería de madera", codigo=None, ambiguo=True
    )
    assert proveedor == Elegido(
        etiqueta="Juan Ejemplo Ejemplo", codigo="P2", ambiguo=False
    )


def test_f036_r93_oficio_de_un_codigo() -> None:
    assert resolver_oficio_y_proveedor(PINTURA, None) == (
        Elegido(etiqueta="Pintura", codigo="0028", ambiguo=False),
        None,
    )


def test_f036_r76_sin_oficio_ni_proveedor() -> None:
    assert resolver_oficio_y_proveedor(None, None) == (None, None)


def test_f036_r74_d17_solo_proveedor_toma_el_oficio_del_par() -> None:
    assert resolver_oficio_y_proveedor(None, CARPINTERIA_P1) == (
        Elegido(etiqueta="Carpintería de madera", codigo="0046", ambiguo=False),
        Elegido(etiqueta="Carpinterías Ejemplo S.L.", codigo="P1", ambiguo=False),
    )


def test_f036_r75_proveedor_con_varios_codigos_es_ambiguo() -> None:
    # En F-036 no puede darse (sin agrupación de proveedores, F-050), pero la
    # función lo trata: nunca elige sola entre varios códigos.
    par = OpcionProveedor(
        etiqueta="Pintura · Grupo de dos",
        oficio=PINTURA,
        grupo=Grupo(
            catalogo=Catalogo.PROVEEDOR,
            codigos=frozenset({"P3", "P4"}),
            etiqueta="Grupo de dos",
        ),
        filas_en_obra=(("0028", "P3"), ("0028", "P4")),
    )
    assert resolver_oficio_y_proveedor(PINTURA, par) == (
        Elegido(etiqueta="Pintura", codigo="0028", ambiguo=False),
        Elegido(etiqueta="Grupo de dos", codigo=None, ambiguo=True),
    )


def test_f036_resolver_rechaza_un_par_de_otro_oficio() -> None:
    with pytest.raises(ValueError, match="grupo de oficio"):
        resolver_oficio_y_proveedor(PINTURA, CARPINTERIA_P1)


def test_f036_resolver_rechaza_opciones_sin_codigos() -> None:
    sin_codigos = replace(PINTURA, codigos_en_obra=())
    with pytest.raises(ValueError, match="sin códigos"):
        resolver_oficio_y_proveedor(sin_codigos, None)
    par_sin_filas = replace(PINTURA_P3, filas_en_obra=())
    with pytest.raises(ValueError, match="sin códigos"):
        resolver_oficio_y_proveedor(PINTURA, par_sin_filas)


def test_f036_r93_fila_con_oficio_ambiguo_avisa() -> None:
    v = una_valida(
        fila(2, unidad="Villa 1", descripcion="x", oficio="Carpintería de madera")
    )
    assert v.oficio == Elegido(
        etiqueta="Carpintería de madera", codigo=None, ambiguo=True
    )
    assert v.proveedor is None
    assert v.avisos == (
        "el oficio «Carpintería de madera» tiene varios códigos en la obra: se elegirá en la bandeja",
    )


def test_f036_r94_fila_con_proveedor_que_resuelve() -> None:
    v = una_valida(
        fila(
            2,
            unidad="Villa 1",
            descripcion="x",
            oficio="Carpintería de madera",
            proveedor="Carpintería de madera · Carpinterías Ejemplo S.L.",
        )
    )
    assert v.oficio == Elegido(
        etiqueta="Carpintería de madera", codigo="0046", ambiguo=False
    )
    assert v.proveedor == Elegido(
        etiqueta="Carpinterías Ejemplo S.L.", codigo="P1", ambiguo=False
    )
    assert v.avisos == ()


def test_f036_r75_fila_con_proveedor_ambiguo_avisa() -> None:
    par = OpcionProveedor(
        etiqueta="Pintura · Grupo de dos",
        oficio=PINTURA,
        grupo=Grupo(
            catalogo=Catalogo.PROVEEDOR,
            codigos=frozenset({"P3", "P4"}),
            etiqueta="Grupo de dos",
        ),
        filas_en_obra=(("0028", "P3"), ("0028", "P4")),
    )
    validas, con_error = validar_filas(
        [
            fila(
                2, unidad="Villa 1", descripcion="x", proveedor="Pintura · Grupo de dos"
            )
        ],
        catalogo=CATALOGO,
        opciones_oficio=OPCIONES_OFICIO,
        opciones_proveedor=(par,),
        listas=LISTAS,
    )
    assert con_error == ()
    assert validas[0].avisos == (
        "el proveedor «Grupo de dos» tiene varios códigos en la obra: se elegirá en la bandeja",
    )


def test_f036_r74_d17_fila_con_proveedor_y_sin_oficio() -> None:
    v = una_valida(
        fila(
            2,
            unidad="Villa 1",
            descripcion="x",
            proveedor="Pintura · Pinturas Ejemplo S.A.",
        )
    )
    assert v.oficio == Elegido(etiqueta="Pintura", codigo="0028", ambiguo=False)
    assert v.proveedor == Elegido(
        etiqueta="Pinturas Ejemplo S.A.", codigo="P3", ambiguo=False
    )


def test_f036_r74_proveedor_de_otro_oficio_es_error() -> None:
    assert errores_de(
        fila(
            2,
            unidad="Villa 1",
            descripcion="x",
            oficio="Pintura",
            proveedor="Carpintería de madera · Carpinterías Ejemplo S.L.",
        )
    ) == [
        ("Proveedor", "ese proveedor no está dado de alta en la obra para ese oficio")
    ]


@pytest.mark.parametrize(
    "valor",
    [
        "Carpinterías Ejemplo S.L.",  # sin el oficio del par
        "Carpintería de madera · carpinterías ejemplo s.l.",
        "Carpintería de madera ·  Carpinterías Ejemplo S.L.",
        "Pintura · Carpinterías Ejemplo S.L.",  # par que no existe en la obra
    ],
)
def test_f036_r73_proveedor_exacto(valor: str) -> None:
    assert errores_de(fila(2, unidad="Villa 1", descripcion="x", proveedor=valor)) == [
        (
            "Proveedor",
            (
                "ese valor no está en la lista de proveedores de la obra: elígelo del desplegable "
                "(cuidado con mayúsculas, tildes y espacios)"
            ),
        )
    ]


def test_f036_r73_oficio_malo_y_proveedor_bueno_solo_marca_el_oficio() -> None:
    assert [
        c
        for c, _ in errores_de(
            fila(
                2,
                unidad="Villa 1",
                descripcion="x",
                oficio="Nada",
                proveedor="Pintura · Pinturas Ejemplo S.A.",
            )
        )
    ] == ["Oficio"]


def test_f036_r76_sin_proveedor_no_se_propone_ninguno() -> None:
    v = una_valida(fila(2, unidad="Villa 1", descripcion="x", oficio="Pintura"))
    assert v.oficio == Elegido(etiqueta="Pintura", codigo="0028", ambiguo=False)
    assert v.proveedor is None


def test_f036_r12_sin_opciones_de_oficio_la_fila_sin_oficio_entra() -> None:
    validas, con_error = validar_filas(
        [fila(2, unidad="Villa 1", descripcion="x")],
        catalogo=CATALOGO,
        opciones_oficio=(),
        opciones_proveedor=(),
        listas=LISTAS,
    )
    assert con_error == ()
    assert validas[0].oficio is None


@pytest.mark.parametrize(("codigo", "ambiguo"), [("0046", True), (None, False)])
def test_f036_r99_elegido_codigo_none_si_y_solo_si_ambiguo(
    codigo: str | None, ambiguo: bool
) -> None:
    with pytest.raises(ValueError, match="ambiguo"):
        Elegido(etiqueta="x", codigo=codigo, ambiguo=ambiguo)


def test_f036_r99_no_hay_proveedor_sin_oficio() -> None:
    v = una_valida(fila(2, unidad="Villa 1", descripcion="x"))
    with pytest.raises(ValueError, match="proveedor sin oficio"):
        replace(v, proveedor=Elegido(etiqueta="P", codigo="P1", ambiguo=False))


def _en_bandeja(**cambios: object) -> IncidenciaEnBandeja:
    base = IncidenciaEnBandeja(
        incidencia_id=uuid4(),
        importacion_id=uuid4(),
        fila_origen=2,
        unidad_codigo="0677.03VILLA 1.",
        unidad_nombre="Villa 1",
        ubicacion=None,
        descripcion="x",
        detalle=None,
        oficio_codigo="0028",
        oficio_nombre="Pintura",
        oficio_ambiguo=False,
        proveedor_codigo="P3",
        proveedor_nombre="Pinturas Ejemplo S.A.",
        proveedor_ambiguo=False,
        urgencia=None,
        listado=None,
        duplicada_de=None,
        creada_at_utc=datetime(2026, 9, 29, tzinfo=UTC),
    )
    return replace(base, **cambios)  # type: ignore[arg-type]


def test_f036_r99_bandeja_ambiguos_sin_codigo_y_con_nombre() -> None:
    fila_ok = _en_bandeja(
        oficio_codigo=None,
        oficio_ambiguo=True,
        proveedor_codigo=None,
        proveedor_ambiguo=True,
    )
    assert fila_ok.oficio_nombre == "Pintura"
    assert (
        _en_bandeja(
            proveedor_codigo=None,
            proveedor_nombre=None,
            oficio_codigo=None,
            oficio_nombre=None,
        ).oficio_ambiguo
        is False
    )


@pytest.mark.parametrize(
    "cambios",
    [
        {"oficio_ambiguo": True},  # ambiguo con código
        {
            "oficio_codigo": None,
            "oficio_ambiguo": True,
            "oficio_nombre": None,
        },  # ambiguo sin nombre
        {"proveedor_ambiguo": True},
        {"proveedor_codigo": None, "proveedor_ambiguo": True, "proveedor_nombre": None},
        {"oficio_codigo": None, "oficio_nombre": None},  # proveedor sin oficio
        {
            "oficio_codigo": None,
            "oficio_nombre": None,
            "proveedor_codigo": None,
            "proveedor_ambiguo": True,
        },
        {
            "oficio_codigo": None,
            "proveedor_codigo": None,
            "proveedor_nombre": None,
        },  # nombre sin código ni ambigüedad
        {"proveedor_codigo": None},
    ],
)
def test_f036_r99_bandeja_invariantes(cambios: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        _en_bandeja(**cambios)


# --------------------------------------------------------------------------
# R35–R38, R77 · clave de duplicado y grupos
# --------------------------------------------------------------------------


def test_f036_r35_clave_es_sha256_de_los_cuatro_campos_normalizados() -> None:
    esperado = hashlib.sha256(
        b"0677\x1f0677.03VILLA 1.\x1fcocina\x1fsellar sifon"
    ).hexdigest()
    assert (
        clave_de_duplicado(
            obra_codigo="0677",
            unidad_codigo="0677.03VILLA 1.",
            ubicacion="Cocina",
            descripcion="Sellar sifón.",
        )
        == esperado
    )


def test_f036_r35_ubicacion_vacia_cuenta_como_cadena_vacia() -> None:
    esperado = hashlib.sha256(b"0677\x1fU1\x1f\x1fsellar sifon").hexdigest()
    assert (
        clave_de_duplicado(
            obra_codigo="0677",
            unidad_codigo="U1",
            ubicacion=None,
            descripcion="Sellar sifon",
        )
        == esperado
    )
    assert (
        clave_de_duplicado(
            obra_codigo="0677",
            unidad_codigo="U1",
            ubicacion="",
            descripcion="Sellar sifon",
        )
        == esperado
    )


def test_f036_r35_misma_clave_con_mayusculas_tildes_y_punto() -> None:
    a = clave_de_duplicado(
        obra_codigo="0677",
        unidad_codigo="U1",
        ubicacion="Baño 1",
        descripcion="Sellar sifón",
    )
    b = clave_de_duplicado(
        obra_codigo="0677",
        unidad_codigo="U1",
        ubicacion="baño 1",
        descripcion="  SELLAR  sifon. ",
    )
    assert a == b


@pytest.mark.parametrize(
    "cambio",
    [
        {"obra_codigo": "0678"},
        {"unidad_codigo": "U2"},
        {"ubicacion": "Cocina"},
        {"descripcion": "Sellar sifón bien"},
    ],
)
def test_f036_r35_cada_campo_cuenta(cambio: dict[str, str]) -> None:
    base = {
        "obra_codigo": "0677",
        "unidad_codigo": "U1",
        "ubicacion": "Baño 1",
        "descripcion": "Sellar sifón",
    }
    assert clave_de_duplicado(**base) != clave_de_duplicado(**{**base, **cambio})


def test_f036_r35_el_separador_no_deja_mezclar_campos() -> None:
    a = clave_de_duplicado(
        obra_codigo="0677", unidad_codigo="U1", ubicacion="a b", descripcion="c"
    )
    b = clave_de_duplicado(
        obra_codigo="0677", unidad_codigo="U1", ubicacion="a", descripcion="b c"
    )
    assert a != b


# Los cinco «Miras de hierro…» de la muestra, en sus cinco ubicaciones.
MIRAS = "Miras de hierro que son de soporte de encimera estan oxidadas, cerrar contra pared el agujero y tapar esas miras de hierro, PELIGRO DE SEGURIDAD."
MIRAS_OXIDADAS = "Miras de hierro que son de soporte de encimera estan OXIDADAS, cerrar contra pared el agujero y tapar esas miras de hierro, PELIGRO DE SEGURIDAD."
MIRAS_EN_LA_MUESTRA = (
    ("Sala / estudio", MIRAS),
    ("Dormitorio 1", MIRAS_OXIDADAS),
    ("Dormitorio 3", MIRAS),
    ("Dormitorio 4", MIRAS),
    ("Baño de planta baja", MIRAS),
)


def test_f036_r36_miras_de_hierro_en_cinco_ubicaciones_no_son_duplicados() -> None:
    claves = {
        clave_de_duplicado(
            obra_codigo="0677",
            unidad_codigo="0677.03VILLA 1.",
            ubicacion=u,
            descripcion=d,
        )
        for u, d in MIRAS_EN_LA_MUESTRA
    }
    assert len(claves) == 5


def test_f036_r36_misma_ubicacion_y_texto_si_es_duplicado() -> None:
    a = clave_de_duplicado(
        obra_codigo="0677",
        unidad_codigo="U1",
        ubicacion="Dormitorio 1",
        descripcion=MIRAS,
    )
    b = clave_de_duplicado(
        obra_codigo="0677",
        unidad_codigo="U1",
        ubicacion="Dormitorio 1",
        descripcion=MIRAS_OXIDADAS,
    )
    assert a == b


def test_f036_r36_r37_miras_de_hierro_por_la_validacion_y_los_grupos() -> None:
    # El texto de la muestra pasa de 128: va al detalle y la descripción corta
    # es la que propondría la migración.
    filas = [
        fila(
            n,
            unidad="Villa 1",
            ubicacion=u,
            descripcion="Miras de hierro oxidadas en la encimera",
            detalle=d,
        )
        for n, (u, d) in enumerate(MIRAS_EN_LA_MUESTRA, start=2)
    ]
    validas, con_error = validar(*filas)
    assert con_error == ()
    assert all(v.avisos == (AVISO_URGENCIA,) for v in validas)
    grupos = agrupar_por_clave(validas, obra_codigo="0677")
    assert len(grupos) == 5
    assert all(len(g.filas) == 1 for g in grupos)


def test_f036_r37_duplicadas_en_el_fichero_agrupadas_la_primera_manda() -> None:
    f2 = fila(2, unidad="Villa 1", ubicacion="Cocina", descripcion="Sellar sifón")
    f3 = fila(3, unidad="Villa 1", ubicacion="Dormitorio 1", descripcion="Sellar sifón")
    f4 = fila(4, unidad="Villa 1", ubicacion="Cocina", descripcion="sellar sifon.")
    f5 = fila(
        5,
        unidad="Viviendas Bloque Villa 2",
        ubicacion="Cocina",
        descripcion="Sellar sifón",
    )
    f6 = fila(6, unidad="Villa 1", ubicacion="Cocina", descripcion="SELLAR SIFÓN")
    validas, _ = validar(f2, f3, f4, f5, f6)
    grupos = agrupar_por_clave(validas, obra_codigo="0677")
    assert [[v.fila for v in g.filas] for g in grupos] == [[2, 4, 6], [3], [5]]
    assert grupos[0] == GrupoDeClave(
        clave=clave_de_duplicado(
            obra_codigo="0677",
            unidad_codigo="0677.03VILLA 1.",
            ubicacion="Cocina",
            descripcion="Sellar sifón",
        ),
        filas=(validas[0], validas[2], validas[4]),
    )


def test_f036_r77_la_clave_no_incluye_oficio_ni_proveedor() -> None:
    f2 = fila(2, unidad="Villa 1", descripcion="Sellar sifón", oficio="Pintura")
    f3 = fila(
        3,
        unidad="Villa 1",
        descripcion="Sellar sifón",
        proveedor="Carpintería de madera · Carpinterías Ejemplo S.L.",
    )
    f4 = fila(
        4,
        unidad="Villa 1",
        descripcion="Sellar sifón",
        urgencia="Urgente",
        detalle="otro detalle",
    )
    validas, _ = validar(f2, f3, f4)
    assert [
        [v.fila for v in g.filas]
        for g in agrupar_por_clave(validas, obra_codigo="0677")
    ] == [[2, 3, 4]]


def test_f036_r37_la_obra_entra_en_la_clave_de_los_grupos() -> None:
    validas, _ = validar(fila(2, unidad="Villa 1", descripcion="x"))
    a = agrupar_por_clave(validas, obra_codigo="0677")
    b = agrupar_por_clave(validas, obra_codigo="0678")
    assert a[0].clave != b[0].clave


def test_f036_agrupar_sin_filas() -> None:
    assert agrupar_por_clave([], obra_codigo="0677") == ()


# --------------------------------------------------------------------------
# Enumeraciones y estructuras
# --------------------------------------------------------------------------


def test_f036_enumeraciones_de_estado() -> None:
    assert [e.value for e in EstadoFilaImportada] == [
        "nueva",
        "duplicada_en_fichero",
        "ya_en_bandeja",
        "con_error",
    ]
    assert [e.value for e in EstadoImportacion] == ["completa", "parcial"]


def test_f036_estructuras_inmutables() -> None:
    v = una_valida(fila(2, unidad="Villa 1", descripcion="x"))
    with pytest.raises(FrozenInstanceError):
        v.descripcion = "y"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        libro().version = 2  # type: ignore[misc]


def test_f036_r34_mayusculas_umbral_exacto_del_sesenta() -> None:
    # Con 100 letras: 60 en mayúscula (60 %) no avisa; 61 (61 %) sí. Fija el
    # porcentaje al punto, no a la franja 60–64 que deja ver el caso de 20.
    sesenta = "A" * 60 + "b" * 40
    sesenta_y_una = "A" * 61 + "b" * 39
    assert una_valida(fila(2, unidad="Villa 1", descripcion=sesenta)).avisos == ()
    assert una_valida(fila(2, unidad="Villa 1", descripcion=sesenta_y_una)).avisos == (
        AVISO_MAYUSCULAS,
    )


@pytest.mark.parametrize(
    "clase",
    [
        m
        for m in vars(importacion).values()
        if isinstance(m, type)
        and dataclasses.is_dataclass(m)
        and m.__module__ == importacion.__name__
    ],
    ids=lambda c: c.__name__,
)
def test_f036_todas_las_estructuras_de_importacion_son_inmutables(clase: type) -> None:
    assert clase.__dataclass_params__.frozen  # type: ignore[attr-defined]
