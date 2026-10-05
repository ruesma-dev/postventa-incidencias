# services/postventa-api/tests/test_f036_repositorio_bandeja.py
"""La bandeja y las decisiones de equivalencia sobre PostgreSQL, con un doble (F-036 T15).

`specs/F-036-importar-excel/design.md` §5.3, §6.2 y §15.4:

- `BandejaPort.registrar` en **una** transacción (R40): la importación, las
  primeras de cada grupo con `ON CONFLICT … DO NOTHING` (R41), las existentes
  de las claves que no entraron (R38), las duplicadas del fichero (R37) y los
  recuentos. Importación **completa**, **parcial** y con **cero** válidas
  (R69, R70).
- `importacion_completa_por_hash` (R39) y `listar` con su tope duro de 500
  también en la sentencia (R45).
- `EquivalenciasPort`: append-only, por pares y **por catálogo** (R81, R83,
  R95), la última decisión de cada par con `DISTINCT ON`.
- `construir_bandeja` y `construir_equivalencias`: la misma receta de
  conexión que `construir_repositorio`.

Sin base de datos: el doble de `tests/utiles_pg.py`. Lo que solo PostgreSQL
puede demostrar —que el índice parcial muerde, que el DDL entra dos veces— es
`tests_bbdd/tests/test_f036_bbdd_bandeja.py` (T16, MANUAL). Ni un dato real ni
un GUID escrito a mano: los identificadores salen de `UUID(int=n)`.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime
from uuid import UUID

import psycopg
import pytest
from config.settings import Ajustes
from domain.models.equivalencias import Catalogo, DecisionPar, Motivo
from domain.models.errores import (
    ConfiguracionPgIncompleta,
    DdlInseguro,
    DdlNoPermitidoAqui,
    PersistenciaNoDisponible,
)
from domain.models.importacion import (
    Elegido,
    EstadoFilaImportada,
    EstadoImportacion,
    GrupoDeClave,
    IncidenciaEnBandeja,
    IncidenciaValida,
)
from domain.models.plantilla_incidencias import Listado, Opcion, Urgencia
from domain.ports.bandeja import (
    BandejaPort,
    FilaImportada,
    RegistroImportacion,
    ResultadoImportacion,
)
from domain.ports.equivalencias import EquivalenciasPort
from infrastructure.persistencia import fabrica, sentencias_bandeja
from infrastructure.persistencia.repositorio_bandeja_pg import (
    RepositorioBandejaPostgres,
    RepositorioEquivalenciasPostgres,
)
from infrastructure.persistencia.sentencias_bandeja import (
    COLUMNAS_BANDEJA,
    LIMITE_MAXIMO_BANDEJA,
    insert_decisiones,
    insert_duplicadas,
    insert_importacion,
    insert_primeras,
    select_bandeja,
    select_existentes_por_clave,
    select_importacion_completa_por_hash,
    select_ultimas_decisiones,
    update_recuentos,
)

from tests.utiles_pg import ConexionDoble

ESQUEMA = "postventa"
AHORA = datetime(2026, 9, 30, 8, 15, tzinfo=UTC)
DESPUES = datetime(2026, 9, 30, 9, 0, tzinfo=UTC)

#: Datos **inventados**: ni una obra, unidad, proveedor ni persona reales.
OBRA = "9999"
OID = "oid-inventado-de-quien-sube"
NOMBRE_FICHERO = "incidencias de Fulanito Inventado.xlsx"
HASH = hashlib.sha256(b"bytes inventados del fichero").hexdigest()
DESCRIPCION = "Grieta inventada junto a la ventana"
DETALLE = "Detalle inventado con un telefono 600000000"
UNIDAD = Opcion(etiqueta="VILLA INVENTADA 7", codigo="U-07")
PROVEEDOR_NOMBRE = "Autonomo Inventado Perez"
PROVEEDOR_CODIGO = "P-4242"


def _id(n: int) -> UUID:
    return UUID(int=n)


def _clave(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()


class _Ids:
    """Genera `UUID(int=1000)`, `UUID(int=1001)`… en orden: deterministas y sin
    literales."""

    def __init__(self, primero: int = 1000) -> None:
        self.siguiente = primero

    def __call__(self) -> UUID:
        valor = UUID(int=self.siguiente)
        self.siguiente += 1
        return valor


def _registro(
    *, filas_leidas: int = 3, filas_con_error: int = 0
) -> RegistroImportacion:
    return RegistroImportacion(
        importacion_id=_id(1),
        hash_fichero=HASH,
        nombre_fichero=NOMBRE_FICHERO,
        obra_codigo=OBRA,
        plantilla_version=1,
        importado_por=OID,
        importado_at_utc=AHORA,
        filas_leidas=filas_leidas,
        filas_con_error=filas_con_error,
    )


def _valida(
    fila: int,
    *,
    descripcion: str = DESCRIPCION,
    oficio: Elegido | None = None,
    proveedor: Elegido | None = None,
    urgencia: Urgencia | None = None,
    listado: Listado | None = None,
    ubicacion: str | None = "Salon",
    detalle: str | None = None,
) -> IncidenciaValida:
    return IncidenciaValida(
        fila=fila,
        unidad=UNIDAD,
        ubicacion=ubicacion,
        descripcion=descripcion,
        detalle=detalle,
        oficio=oficio,
        proveedor=proveedor,
        urgencia=urgencia,
        listado=listado,
        avisos=(),
    )


def _grupo(clave: str, *filas: int) -> GrupoDeClave:
    return GrupoDeClave(clave=clave, filas=tuple(_valida(f) for f in filas))


def _repositorio(
    conexion: ConexionDoble, ids: _Ids | None = None
) -> RepositorioBandejaPostgres:
    return RepositorioBandejaPostgres(conexion, esquema=ESQUEMA, nuevo_id=ids or _Ids())


def _decision(
    a: str = "0046",
    b: str = "0143",
    *,
    catalogo: Catalogo = Catalogo.OFICIO,
    decision: str = "mismo",
    motivos: frozenset[Motivo] = frozenset({Motivo.MISMO_NOMBRE}),
    cuando: datetime = AHORA,
) -> DecisionPar:
    return DecisionPar(
        catalogo=catalogo,
        codigo_a=a,
        codigo_b=b,
        decision=decision,
        motivos=motivos,
        obra_codigo=OBRA,
        decidido_por=OID,
        decidido_at_utc=cuando,
    )


# ==========================================================================
# Los puertos (design.md §5.3, §15.4)
# ==========================================================================


def test_f036_t15_el_puerto_de_la_bandeja_tiene_tres_metodos():
    publicos = sorted(n for n in vars(BandejaPort) if not n.startswith("_"))

    assert publicos == ["importacion_completa_por_hash", "listar", "registrar"]


def test_f036_t15_el_puerto_de_equivalencias_tiene_dos_metodos():
    publicos = sorted(n for n in vars(EquivalenciasPort) if not n.startswith("_"))

    assert publicos == ["registrar", "ultimas_decisiones"]


def test_f036_t15_los_repositorios_cumplen_sus_puertos():
    assert isinstance(_repositorio(ConexionDoble()), BandejaPort)
    assert isinstance(
        RepositorioEquivalenciasPostgres(ConexionDoble(), esquema=ESQUEMA),
        EquivalenciasPort,
    )


def test_f036_t15_los_campos_de_los_tipos_del_puerto_son_los_del_diseno():
    assert [f.name for f in fields(RegistroImportacion)] == [
        "importacion_id",
        "hash_fichero",
        "nombre_fichero",
        "obra_codigo",
        "plantilla_version",
        "importado_por",
        "importado_at_utc",
        "filas_leidas",
        "filas_con_error",
    ]
    assert [f.name for f in fields(FilaImportada)] == [
        "fila",
        "estado",
        "incidencia_id",
        "duplicada_de_fila",
        "existente_id",
    ]
    assert [f.name for f in fields(ResultadoImportacion)] == [
        "importacion",
        "ya_importado",
        "estado",
        "nuevas",
        "duplicadas_en_fichero",
        "ya_en_bandeja",
        "con_error",
        "filas",
    ]


@pytest.mark.parametrize(
    "objeto",
    (
        _registro(),
        FilaImportada(
            fila=2,
            estado=EstadoFilaImportada.NUEVA,
            incidencia_id=_id(5),
            duplicada_de_fila=None,
            existente_id=None,
        ),
        ResultadoImportacion(
            importacion=_registro(),
            ya_importado=False,
            estado=EstadoImportacion.COMPLETA,
            nuevas=0,
            duplicadas_en_fichero=0,
            ya_en_bandeja=0,
            con_error=0,
            filas=(),
        ),
    ),
)
def test_f036_t15_los_tipos_del_puerto_son_inmutables(objeto):
    with pytest.raises(FrozenInstanceError):
        objeto.fila = 3  # type: ignore[misc]


@pytest.mark.parametrize(
    ("con_error", "estado"),
    (
        (0, EstadoImportacion.COMPLETA),
        (1, EstadoImportacion.PARCIAL),
        (7, EstadoImportacion.PARCIAL),
    ),
)
def test_f036_r69_r70_el_estado_de_la_importacion_sale_de_las_filas_con_error(
    con_error, estado
):
    assert _registro(filas_leidas=7, filas_con_error=con_error).estado is estado


def test_f036_r47_el_registro_no_ensena_el_oid_ni_el_fichero_en_su_repr():
    texto = repr(_registro())

    assert OID not in texto
    assert NOMBRE_FICHERO not in texto


# ==========================================================================
# Sentencias (§6.2): texto, parámetros, nada interpolado
# ==========================================================================


def test_f036_t15_insert_importacion_con_su_estado_y_los_recuentos_a_cero():
    sql, parametros = insert_importacion(
        esquema=ESQUEMA, importacion=_registro(filas_con_error=2)
    )

    assert sql == (
        "INSERT INTO postventa.importaciones (importacion_id, hash_fichero, "
        "nombre_fichero, obra_codigo, plantilla_version, estado, importado_por, "
        "importado_at_utc, filas_leidas, filas_con_error)\n"
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    assert parametros == (
        _id(1),
        HASH,
        NOMBRE_FICHERO,
        OBRA,
        1,
        "parcial",
        OID,
        AHORA,
        3,
        2,
    )


def test_f036_r39_select_de_la_importacion_completa_por_hash():
    sql, parametros = select_importacion_completa_por_hash(
        esquema=ESQUEMA, hash_fichero=HASH
    )

    assert sql == (
        "SELECT importacion_id, hash_fichero, nombre_fichero, obra_codigo, "
        "plantilla_version, importado_por, importado_at_utc, filas_leidas, "
        "filas_con_error, estado, filas_nuevas, filas_duplicadas_en_fichero, "
        "filas_ya_en_bandeja\n"
        "FROM postventa.importaciones\n"
        "WHERE hash_fichero = %s AND estado = %s\n"
        "ORDER BY importado_at_utc, importacion_id\n"
        "LIMIT 1"
    )
    assert parametros == (HASH, "completa")


def test_f036_t15_las_columnas_de_la_bandeja_son_las_del_ddl():
    assert COLUMNAS_BANDEJA == (
        "incidencia_id",
        "origen",
        "importacion_id",
        "fila_origen",
        "obra_codigo",
        "unidad_codigo",
        "unidad_nombre",
        "ubicacion",
        "descripcion",
        "detalle",
        "oficio_codigo",
        "oficio_nombre",
        "oficio_ambiguo",
        "proveedor_codigo",
        "proveedor_nombre",
        "proveedor_ambiguo",
        "urgencia",
        "listado",
        "clave_duplicado",
        "duplicada_de",
        "creada_at_utc",
    )


def test_f036_r41_insert_primeras_en_bloque_con_on_conflict_del_indice_parcial():
    """R41 · una sentencia para todas, y quien decide es el índice único parcial."""
    filas = (
        sentencias_bandeja.valores_de_fila(
            _registro(),
            _valida(2),
            incidencia_id=_id(10),
            clave=_clave("a"),
            duplicada_de=None,
        ),
        sentencias_bandeja.valores_de_fila(
            _registro(),
            _valida(3),
            incidencia_id=_id(11),
            clave=_clave("b"),
            duplicada_de=None,
        ),
    )

    sql, parametros = insert_primeras(esquema=ESQUEMA, filas=filas)

    marcas = "(" + ", ".join(["%s"] * 21) + ")"
    assert sql == (
        f"INSERT INTO postventa.bandeja_incidencias ({', '.join(COLUMNAS_BANDEJA)})\n"
        f"VALUES {marcas},\n{marcas}\n"
        "ON CONFLICT (obra_codigo, clave_duplicado) WHERE duplicada_de IS NULL DO NOTHING\n"
        "RETURNING incidencia_id, clave_duplicado"
    )
    assert parametros == filas[0] + filas[1]


def test_f036_r37_insert_duplicadas_sin_on_conflict_ni_returning():
    filas = (
        sentencias_bandeja.valores_de_fila(
            _registro(),
            _valida(4),
            incidencia_id=_id(12),
            clave=_clave("a"),
            duplicada_de=_id(10),
        ),
    )

    sql, parametros = insert_duplicadas(esquema=ESQUEMA, filas=filas)

    marcas = "(" + ", ".join(["%s"] * 21) + ")"
    assert sql == (
        f"INSERT INTO postventa.bandeja_incidencias ({', '.join(COLUMNAS_BANDEJA)})\n"
        f"VALUES {marcas}"
    )
    assert parametros == filas[0]


@pytest.mark.parametrize("sentencia", (insert_primeras, insert_duplicadas))
def test_f036_t15_insertar_cero_filas_es_un_error_de_quien_llama(sentencia):
    with pytest.raises(ValueError):
        sentencia(esquema=ESQUEMA, filas=())


def test_f036_t15_valores_de_una_fila_completa():
    """Cada columna, en su sitio; `creada_at_utc` es el instante de la importación
    (R45: las de la más reciente primero)."""
    oficio = Elegido(etiqueta="Carpinteria inventada", codigo="0046", ambiguo=False)
    proveedor = Elegido(
        etiqueta=PROVEEDOR_NOMBRE, codigo=PROVEEDOR_CODIGO, ambiguo=False
    )
    valida = _valida(
        5,
        oficio=oficio,
        proveedor=proveedor,
        urgencia=Urgencia.SEGURIDAD,
        listado=Listado.SEGUNDO,
        detalle=DETALLE,
    )

    valores = sentencias_bandeja.valores_de_fila(
        _registro(),
        valida,
        incidencia_id=_id(20),
        clave=_clave("c"),
        duplicada_de=_id(19),
    )

    assert valores == (
        _id(20),
        "excel",
        _id(1),
        5,
        OBRA,
        "U-07",
        "VILLA INVENTADA 7",
        "Salon",
        DESCRIPCION,
        DETALLE,
        "0046",
        "Carpinteria inventada",
        False,
        PROVEEDOR_CODIGO,
        PROVEEDOR_NOMBRE,
        False,
        "seguridad",
        "segundo",
        _clave("c"),
        _id(19),
        AHORA,
    )


def test_f036_r99_valores_de_una_fila_con_oficio_ambiguo_y_sin_proveedor():
    oficio = Elegido(etiqueta="Carpinteria inventada", codigo=None, ambiguo=True)
    valida = _valida(6, oficio=oficio, ubicacion=None)

    valores = sentencias_bandeja.valores_de_fila(
        _registro(), valida, incidencia_id=_id(21), clave=_clave("d"), duplicada_de=None
    )
    por_columna = dict(zip(COLUMNAS_BANDEJA, valores, strict=True))

    assert por_columna["oficio_codigo"] is None
    assert por_columna["oficio_nombre"] == "Carpinteria inventada"
    assert por_columna["oficio_ambiguo"] is True
    assert por_columna["proveedor_codigo"] is None
    assert por_columna["proveedor_nombre"] is None
    assert por_columna["proveedor_ambiguo"] is False
    assert por_columna["ubicacion"] is None
    assert por_columna["urgencia"] is None
    assert por_columna["listado"] is None
    assert por_columna["duplicada_de"] is None


def test_f036_t15_valores_de_una_fila_con_proveedor_ambiguo():
    """F-050 · la costura: un proveedor ambiguo va sin código y con su nombre."""
    oficio = Elegido(etiqueta="Carpinteria inventada", codigo="0046", ambiguo=False)
    proveedor = Elegido(etiqueta=PROVEEDOR_NOMBRE, codigo=None, ambiguo=True)

    valores = sentencias_bandeja.valores_de_fila(
        _registro(),
        _valida(7, oficio=oficio, proveedor=proveedor),
        incidencia_id=_id(22),
        clave=_clave("e"),
        duplicada_de=None,
    )
    por_columna = dict(zip(COLUMNAS_BANDEJA, valores, strict=True))

    assert por_columna["proveedor_codigo"] is None
    assert por_columna["proveedor_nombre"] == PROVEEDOR_NOMBRE
    assert por_columna["proveedor_ambiguo"] is True


def test_f036_r38_select_de_las_existentes_por_clave():
    sql, parametros = select_existentes_por_clave(
        esquema=ESQUEMA, obra_codigo=OBRA, claves=(_clave("b"), _clave("a"))
    )

    assert sql == (
        "SELECT clave_duplicado, incidencia_id\n"
        "FROM postventa.bandeja_incidencias\n"
        "WHERE obra_codigo = %s AND clave_duplicado = ANY(%s) AND duplicada_de IS NULL"
    )
    assert parametros == (OBRA, [_clave("b"), _clave("a")])


def test_f036_t15_update_de_los_recuentos():
    sql, parametros = update_recuentos(
        esquema=ESQUEMA,
        importacion_id=_id(1),
        nuevas=4,
        duplicadas_en_fichero=2,
        ya_en_bandeja=3,
    )

    assert sql == (
        "UPDATE postventa.importaciones\n"
        "SET filas_nuevas = %s, filas_duplicadas_en_fichero = %s, filas_ya_en_bandeja = %s\n"
        "WHERE importacion_id = %s"
    )
    assert parametros == (4, 2, 3, _id(1))


def test_f036_r45_select_de_la_bandeja_por_obra_y_en_orden():
    sql, parametros = select_bandeja(esquema=ESQUEMA, obra_codigo=OBRA, limite=200)

    assert sql == (
        "SELECT incidencia_id, importacion_id, fila_origen, unidad_codigo, "
        "unidad_nombre, ubicacion, descripcion, detalle, oficio_codigo, "
        "oficio_nombre, oficio_ambiguo, proveedor_codigo, proveedor_nombre, "
        "proveedor_ambiguo, urgencia, listado, duplicada_de, creada_at_utc\n"
        "FROM postventa.bandeja_incidencias\n"
        "WHERE obra_codigo = %s\n"
        "ORDER BY creada_at_utc DESC, fila_origen, incidencia_id\n"
        "LIMIT %s"
    )
    assert parametros == (OBRA, 200)


@pytest.mark.parametrize(
    ("pedido", "aplicado"),
    ((1, 1), (0, 1), (-5, 1), (499, 499), (500, 500), (501, 500), (100_000, 500)),
)
def test_f036_r45_el_tope_de_500_tambien_en_la_sentencia(pedido, aplicado):
    """Dos cinturones, como la cola de F-019: el borde da 400 y aquí se acota."""
    _, parametros = select_bandeja(esquema=ESQUEMA, obra_codigo=OBRA, limite=pedido)

    assert parametros[-1] == aplicado
    assert LIMITE_MAXIMO_BANDEJA == 500


def test_f036_r81_insert_decisiones_varios_pares_en_una_sentencia_y_sin_on_conflict():
    """R81 · append-only: nada se pisa. Los motivos, ordenados y en texto."""
    decisiones = (
        _decision(motivos=frozenset({Motivo.PLURAL, Motivo.ERRATA})),
        _decision(
            "0033", "0133", decision="distinto", motivos=frozenset(), cuando=DESPUES
        ),
    )

    sql, parametros = insert_decisiones(esquema=ESQUEMA, decisiones=decisiones)

    marcas = "(" + ", ".join(["%s"] * 8) + ")"
    assert sql == (
        "INSERT INTO postventa.decisiones_equivalencia (catalogo, codigo_a, codigo_b, "
        "decision, motivos, obra_codigo, decidido_por, decidido_at_utc)\n"
        f"VALUES {marcas},\n{marcas}"
    )
    assert parametros == (
        "oficio",
        "0046",
        "0143",
        "mismo",
        "errata,plural",
        OBRA,
        OID,
        AHORA,
        "oficio",
        "0033",
        "0133",
        "distinto",
        None,
        OBRA,
        OID,
        DESPUES,
    )
    assert "ON CONFLICT" not in sql and "UPDATE" not in sql


def test_f036_t15_insertar_cero_decisiones_es_un_error_de_quien_llama():
    with pytest.raises(ValueError):
        insert_decisiones(esquema=ESQUEMA, decisiones=())


def test_f036_r95_select_de_las_ultimas_decisiones_de_un_catalogo():
    """R95 · el par se identifica con su catálogo; manda la última (§6.2)."""
    sql, parametros = select_ultimas_decisiones(
        esquema=ESQUEMA, catalogo=Catalogo.OFICIO, codigos={"0143", "0046", "0085"}
    )

    assert sql == (
        "SELECT DISTINCT ON (codigo_a, codigo_b) catalogo, codigo_a, codigo_b, "
        "decision, motivos, obra_codigo, decidido_por, decidido_at_utc\n"
        "FROM postventa.decisiones_equivalencia\n"
        "WHERE catalogo = %s AND codigo_a = ANY(%s) AND codigo_b = ANY(%s)\n"
        "ORDER BY codigo_a, codigo_b, decidido_at_utc DESC, decision_id DESC"
    )
    assert parametros == ("oficio", ["0046", "0085", "0143"], ["0046", "0085", "0143"])


@pytest.mark.parametrize(
    "construir",
    (
        lambda e: insert_importacion(esquema=e, importacion=_registro()),
        lambda e: select_importacion_completa_por_hash(esquema=e, hash_fichero=HASH),
        lambda e: select_existentes_por_clave(
            esquema=e, obra_codigo=OBRA, claves=("x",)
        ),
        lambda e: update_recuentos(
            esquema=e,
            importacion_id=_id(1),
            nuevas=0,
            duplicadas_en_fichero=0,
            ya_en_bandeja=0,
        ),
        lambda e: select_bandeja(esquema=e, obra_codigo=OBRA, limite=1),
        lambda e: insert_decisiones(esquema=e, decisiones=(_decision(),)),
        lambda e: select_ultimas_decisiones(
            esquema=e, catalogo=Catalogo.OFICIO, codigos={"a"}
        ),
    ),
)
def test_f036_t15_un_esquema_hostil_no_llega_al_sql(construir):
    with pytest.raises(DdlInseguro):
        construir("postventa; DROP TABLE x")


def test_f036_t15_el_esquema_configurado_se_respeta():
    sql, _ = select_bandeja(esquema="otro_inventado", obra_codigo=OBRA, limite=1)

    assert "FROM otro_inventado.bandeja_incidencias" in sql


@pytest.mark.parametrize(
    ("texto", "motivos"),
    (
        (None, frozenset()),
        ("", frozenset()),
        ("errata", frozenset({Motivo.ERRATA})),
        ("errata,plural", frozenset({Motivo.ERRATA, Motivo.PLURAL})),
    ),
)
def test_f036_t15_los_motivos_van_y_vuelven_en_texto(texto, motivos):
    assert sentencias_bandeja.motivos_de_texto(texto) == motivos
    if texto:
        assert sentencias_bandeja.texto_de_motivos(motivos) == texto
    else:
        assert sentencias_bandeja.texto_de_motivos(motivos) is None


def test_f036_t15_un_motivo_desconocido_en_la_base_es_un_error():
    with pytest.raises(ValueError):
        sentencias_bandeja.motivos_de_texto("errata,inventado")


# ==========================================================================
# registrar (§5.3): una transacción, cinco pasos como mucho
# ==========================================================================


def _preparar_primeras(conexion: ConexionDoble, *claves: str) -> None:
    """El `RETURNING` de las primeras que **sí** entraron."""
    conexion.responder(
        "ON CONFLICT", [(_id(9_000 + i), c) for i, c in enumerate(claves)]
    )


def test_f036_r40_completa_todo_nuevo_en_una_transaccion():
    conexion = ConexionDoble()
    _preparar_primeras(conexion, _clave("a"), _clave("b"))

    resultado = _repositorio(conexion).registrar(
        importacion=_registro(filas_leidas=2),
        grupos=(_grupo(_clave("a"), 2), _grupo(_clave("b"), 3)),
    )

    assert [s.split()[0:3] for s in conexion.sql_ejecutado] == [
        ["INSERT", "INTO", "postventa.importaciones"],
        ["INSERT", "INTO", "postventa.bandeja_incidencias"],
        ["UPDATE", "postventa.importaciones", "SET"],
    ]
    assert conexion.commits == 1
    assert conexion.rollbacks == 0
    assert resultado == ResultadoImportacion(
        importacion=_registro(filas_leidas=2),
        ya_importado=False,
        estado=EstadoImportacion.COMPLETA,
        nuevas=2,
        duplicadas_en_fichero=0,
        ya_en_bandeja=0,
        con_error=0,
        filas=(
            FilaImportada(2, EstadoFilaImportada.NUEVA, _id(1000), None, None),
            FilaImportada(3, EstadoFilaImportada.NUEVA, _id(1001), None, None),
        ),
    )
    assert conexion.primera_con("UPDATE").parametros == (2, 0, 0, _id(1))


def test_f036_r40_las_primeras_van_en_una_sola_sentencia_con_sus_ids():
    conexion = ConexionDoble()
    _preparar_primeras(conexion, _clave("a"), _clave("b"))

    _repositorio(conexion).registrar(
        importacion=_registro(), grupos=(_grupo(_clave("a"), 2), _grupo(_clave("b"), 3))
    )

    primeras = conexion.primera_con("ON CONFLICT").parametros
    assert len(primeras) == 2 * len(COLUMNAS_BANDEJA)
    assert primeras[0] == _id(1000)
    assert primeras[len(COLUMNAS_BANDEJA)] == _id(1001)
    assert primeras[18] == _clave("a")
    assert primeras[19] is None


def test_f036_r37_las_duplicadas_del_fichero_apuntan_a_la_primera():
    conexion = ConexionDoble()
    _preparar_primeras(conexion, _clave("a"))

    resultado = _repositorio(conexion).registrar(
        importacion=_registro(filas_leidas=3), grupos=(_grupo(_clave("a"), 2, 5, 9),)
    )

    duplicadas = [
        e
        for e in conexion.ejecutadas
        if e.sql.startswith("INSERT")
        and "ON CONFLICT" not in e.sql
        and "bandeja_incidencias" in e.sql
    ]
    assert len(duplicadas) == 1
    ancho = len(COLUMNAS_BANDEJA)
    parametros = duplicadas[0].parametros
    assert len(parametros) == 2 * ancho
    assert parametros[0] == _id(1001)
    assert parametros[3] == 5
    assert parametros[19] == _id(1000)
    assert parametros[ancho] == _id(1002)
    assert parametros[ancho + 3] == 9
    assert parametros[ancho + 19] == _id(1000)
    assert resultado.nuevas == 1
    assert resultado.duplicadas_en_fichero == 2
    assert resultado.filas == (
        FilaImportada(2, EstadoFilaImportada.NUEVA, _id(1000), None, None),
        FilaImportada(5, EstadoFilaImportada.DUPLICADA_EN_FICHERO, _id(1001), 2, None),
        FilaImportada(9, EstadoFilaImportada.DUPLICADA_EN_FICHERO, _id(1002), 2, None),
    )
    assert conexion.primera_con("UPDATE").parametros == (1, 2, 0, _id(1))
    assert conexion.commits == 1


def test_f036_r38_una_clave_que_ya_estaba_deja_fuera_su_grupo_entero():
    """R38 · ni la primera ni sus duplicadas: todo el grupo `ya_en_bandeja`, con
    el identificador de la existente. Y del grupo que sí entró, sus duplicadas."""
    conexion = ConexionDoble()
    _preparar_primeras(conexion, _clave("b"))
    conexion.responder("= ANY(", [(_clave("a"), _id(77))])

    resultado = _repositorio(conexion).registrar(
        importacion=_registro(filas_leidas=4),
        grupos=(_grupo(_clave("a"), 2, 4), _grupo(_clave("b"), 3, 5)),
    )

    existentes = conexion.primera_con("= ANY(")
    assert existentes.parametros == (OBRA, [_clave("a")])
    duplicadas = [
        e
        for e in conexion.ejecutadas
        if e.sql.startswith("INSERT")
        and "ON CONFLICT" not in e.sql
        and "bandeja_incidencias" in e.sql
    ]
    assert len(duplicadas) == 1
    assert len(duplicadas[0].parametros) == len(COLUMNAS_BANDEJA)
    assert duplicadas[0].parametros[3] == 5
    assert duplicadas[0].parametros[19] == _id(1001)
    assert resultado.filas == (
        FilaImportada(2, EstadoFilaImportada.YA_EN_BANDEJA, None, None, _id(77)),
        FilaImportada(3, EstadoFilaImportada.NUEVA, _id(1001), None, None),
        FilaImportada(4, EstadoFilaImportada.YA_EN_BANDEJA, None, None, _id(77)),
        FilaImportada(5, EstadoFilaImportada.DUPLICADA_EN_FICHERO, _id(1002), 3, None),
    )
    assert (
        resultado.nuevas,
        resultado.duplicadas_en_fichero,
        resultado.ya_en_bandeja,
    ) == (1, 1, 2)
    assert conexion.primera_con("UPDATE").parametros == (1, 1, 2, _id(1))
    assert conexion.commits == 1


def test_f036_r67_reimportar_lo_mismo_no_escribe_ni_una_fila_de_bandeja_de_mas():
    """R38, R67 · todo `ya_en_bandeja`: ni una duplicada insertada."""
    conexion = ConexionDoble()
    conexion.responder("= ANY(", [(_clave("a"), _id(70)), (_clave("b"), _id(71))])

    resultado = _repositorio(conexion).registrar(
        importacion=_registro(filas_leidas=3),
        grupos=(_grupo(_clave("a"), 2, 3), _grupo(_clave("b"), 4)),
    )

    assert conexion.veces_con("INSERT INTO postventa.bandeja_incidencias") == 1
    assert (
        resultado.nuevas,
        resultado.duplicadas_en_fichero,
        resultado.ya_en_bandeja,
    ) == (0, 0, 3)
    assert [f.estado for f in resultado.filas] == [
        EstadoFilaImportada.YA_EN_BANDEJA
    ] * 3
    assert [f.existente_id for f in resultado.filas] == [_id(70), _id(70), _id(71)]


def test_f036_r42_parcial_con_filas_con_error():
    conexion = ConexionDoble()
    _preparar_primeras(conexion, _clave("a"))

    resultado = _repositorio(conexion).registrar(
        importacion=_registro(filas_leidas=5, filas_con_error=4),
        grupos=(_grupo(_clave("a"), 2),),
    )

    assert (
        conexion.primera_con("INSERT INTO postventa.importaciones").parametros[5]
        == "parcial"
    )
    assert resultado.estado is EstadoImportacion.PARCIAL
    assert resultado.con_error == 4
    assert resultado.nuevas == 1
    assert resultado.ya_importado is False


def test_f036_r70_cero_validas_solo_la_importacion_y_sus_recuentos():
    """R70 · consta, parcial, con 0 nuevas: pasos 1 y 5, nada más."""
    conexion = ConexionDoble()

    resultado = _repositorio(conexion).registrar(
        importacion=_registro(filas_leidas=3, filas_con_error=3), grupos=()
    )

    assert len(conexion.ejecutadas) == 2
    assert conexion.ejecutadas[0].sql.startswith("INSERT INTO postventa.importaciones")
    assert conexion.ejecutadas[1].sql.startswith("UPDATE postventa.importaciones")
    assert conexion.ejecutadas[1].parametros == (0, 0, 0, _id(1))
    assert conexion.commits == 1
    assert resultado.estado is EstadoImportacion.PARCIAL
    assert (resultado.nuevas, resultado.con_error, resultado.filas) == (0, 3, ())


@pytest.mark.parametrize(
    "patron",
    (
        "INSERT INTO postventa.importaciones",
        "ON CONFLICT",
        "= ANY(",
        "UPDATE postventa.importaciones",
    ),
)
def test_f036_r40_si_falla_cualquier_paso_no_queda_nada_a_medias(patron):
    """R40 · la base falla → `PersistenciaNoDisponible` (503), `rollback` y ni un
    `commit`. El mensaje no lleva ni un dato de la fila ni del fichero (R47)."""
    conexion = ConexionDoble()
    conexion.responder("= ANY(", [(_clave("a"), _id(70))])
    conexion.fallar(patron, psycopg.OperationalError("caida inventada " + DESCRIPCION))

    with pytest.raises(PersistenciaNoDisponible) as fallo:
        _repositorio(conexion).registrar(
            importacion=_registro(filas_leidas=2), grupos=(_grupo(_clave("a"), 2, 3),)
        )

    assert conexion.commits == 0
    assert conexion.rollbacks == 1
    motivo = fallo.value.motivo
    assert "registrar_importacion" in motivo
    for dato in (DESCRIPCION, HASH, NOMBRE_FICHERO, OID, _clave("a")):
        assert dato not in motivo


def test_f036_r40_falla_la_insercion_de_duplicadas_y_tampoco_queda_nada():
    class ConexionQueFallaEnLasDuplicadas(ConexionDoble):
        def fallo_para(self, sql: str) -> Exception | None:
            if (
                sql.startswith("INSERT INTO postventa.bandeja_incidencias")
                and "ON CONFLICT" not in sql
            ):
                return psycopg.OperationalError("caida inventada")
            return None

    conexion = ConexionQueFallaEnLasDuplicadas()
    _preparar_primeras(conexion, _clave("a"))

    with pytest.raises(PersistenciaNoDisponible):
        _repositorio(conexion).registrar(
            importacion=_registro(), grupos=(_grupo(_clave("a"), 2, 3),)
        )

    assert conexion.veces_con("ON CONFLICT") == 1
    assert conexion.veces_con("UPDATE") == 0
    assert (conexion.commits, conexion.rollbacks) == (0, 1)


def test_f036_r40_una_clave_ni_insertada_ni_encontrada_no_se_da_por_buena():
    """Si el `ON CONFLICT` la saltó y el `SELECT` no la ve, algo no cuadra: se
    deshace todo en vez de inventarse un estado para esas filas."""
    conexion = ConexionDoble()

    with pytest.raises(PersistenciaNoDisponible) as fallo:
        _repositorio(conexion).registrar(
            importacion=_registro(), grupos=(_grupo(_clave("a"), 2),)
        )

    assert (conexion.commits, conexion.rollbacks) == (0, 1)
    assert conexion.veces_con("UPDATE") == 0
    assert _clave("a") not in fallo.value.motivo


def test_f036_r40_un_error_que_no_es_de_la_base_tambien_deshace_y_sube_tal_cual():
    conexion = ConexionDoble()
    conexion.fallar("UPDATE", RuntimeError("inventado"))

    with pytest.raises(RuntimeError):
        _repositorio(conexion).registrar(importacion=_registro(), grupos=())

    assert (conexion.commits, conexion.rollbacks) == (0, 1)


def test_f036_r40_si_el_rollback_tambien_falla_manda_el_error_original():
    class ConexionSinRollback(ConexionDoble):
        def rollback(self) -> None:
            self.rollbacks += 1
            raise psycopg.OperationalError("conexion rota inventada")

    conexion = ConexionSinRollback()
    conexion.fallar("UPDATE", psycopg.OperationalError("caida"))

    with pytest.raises(PersistenciaNoDisponible):
        _repositorio(conexion).registrar(importacion=_registro(), grupos=())

    assert conexion.rollbacks == 1


def test_f036_t15_los_ids_son_uuid4_por_defecto():
    conexion = ConexionDoble()
    conexion.responder("ON CONFLICT", [(None, _clave("a"))])

    resultado = RepositorioBandejaPostgres(conexion, esquema=ESQUEMA).registrar(
        importacion=_registro(), grupos=(_grupo(_clave("a"), 2),)
    )

    assert resultado.filas[0].incidencia_id.version == 4


def test_f036_r47_el_log_de_registrar_solo_lleva_obra_recuentos_e_id(caplog):
    conexion = ConexionDoble()
    _preparar_primeras(conexion, _clave("a"))
    oficio = Elegido(etiqueta="Carpinteria inventada", codigo="0046", ambiguo=False)
    proveedor = Elegido(
        etiqueta=PROVEEDOR_NOMBRE, codigo=PROVEEDOR_CODIGO, ambiguo=False
    )
    grupo = GrupoDeClave(
        clave=_clave("a"),
        filas=(_valida(2, oficio=oficio, proveedor=proveedor, detalle=DETALLE),),
    )

    with caplog.at_level(logging.DEBUG):
        _repositorio(conexion).registrar(
            importacion=_registro(filas_con_error=1), grupos=(grupo,)
        )

    texto = caplog.text
    assert str(_id(1)) in texto
    assert f"obra={OBRA}" in texto
    assert "estado=parcial" in texto
    assert "nuevas=1" in texto and "con_error=1" in texto
    for prohibido in (
        DESCRIPCION,
        DETALLE,
        NOMBRE_FICHERO,
        OID,
        "VILLA INVENTADA",
        PROVEEDOR_NOMBRE,
        PROVEEDOR_CODIGO,
        HASH,
        _clave("a"),
    ):
        assert prohibido not in texto, prohibido


# ==========================================================================
# importacion_completa_por_hash (R39) y listar (R45)
# ==========================================================================


def _fila_importacion() -> tuple:
    return (
        _id(1),
        HASH,
        NOMBRE_FICHERO,
        OBRA,
        1,
        OID,
        AHORA,
        3,
        0,
        "completa",
        2,
        1,
        0,
    )


def test_f036_r39_sin_importacion_completa_devuelve_none():
    conexion = ConexionDoble()

    assert (
        _repositorio(conexion).importacion_completa_por_hash(hash_fichero=HASH) is None
    )
    assert conexion.primera_con("FROM postventa.importaciones").parametros == (
        HASH,
        "completa",
    )
    assert conexion.commits == 1


def test_f036_r39_con_importacion_completa_devuelve_el_resumen_de_entonces():
    conexion = ConexionDoble()
    conexion.responder("FROM postventa.importaciones", [_fila_importacion()])

    resultado = _repositorio(conexion).importacion_completa_por_hash(hash_fichero=HASH)

    assert resultado == ResultadoImportacion(
        importacion=_registro(filas_leidas=3),
        ya_importado=True,
        estado=EstadoImportacion.COMPLETA,
        nuevas=2,
        duplicadas_en_fichero=1,
        ya_en_bandeja=0,
        con_error=0,
        filas=(),
    )
    assert len(conexion.ejecutadas) == 1


def test_f036_r39_el_id_de_la_base_vuelve_como_uuid_aunque_llegue_en_texto():
    conexion = ConexionDoble()
    fila = list(_fila_importacion())
    fila[0] = str(_id(1))
    conexion.responder("FROM postventa.importaciones", [tuple(fila)])

    resultado = _repositorio(conexion).importacion_completa_por_hash(hash_fichero=HASH)

    assert resultado is not None
    assert resultado.importacion.importacion_id == _id(1)


def test_f036_r39_si_la_base_falla_al_buscar_el_hash_es_503():
    conexion = ConexionDoble()
    conexion.fallar("FROM postventa.importaciones", psycopg.OperationalError("caida"))

    with pytest.raises(PersistenciaNoDisponible) as fallo:
        _repositorio(conexion).importacion_completa_por_hash(hash_fichero=HASH)

    assert "importacion_completa_por_hash" in fallo.value.motivo
    assert HASH not in fallo.value.motivo
    assert conexion.rollbacks == 1


def _fila_bandeja(n: int, **cambios) -> tuple:
    base = {
        "incidencia_id": _id(n),
        "importacion_id": _id(1),
        "fila_origen": n,
        "unidad_codigo": "U-07",
        "unidad_nombre": "VILLA INVENTADA 7",
        "ubicacion": "Salon",
        "descripcion": DESCRIPCION,
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpinteria inventada",
        "oficio_ambiguo": False,
        "proveedor_codigo": PROVEEDOR_CODIGO,
        "proveedor_nombre": PROVEEDOR_NOMBRE,
        "proveedor_ambiguo": False,
        "urgencia": "urgente",
        "listado": "primero",
        "duplicada_de": None,
        "creada_at_utc": AHORA,
    }
    base.update(cambios)
    return tuple(base.values())


def test_f036_r45_listar_mapea_cada_fila_a_una_incidencia_de_la_bandeja():
    conexion = ConexionDoble()
    conexion.responder(
        "FROM postventa.bandeja_incidencias",
        [
            _fila_bandeja(2),
            _fila_bandeja(
                3,
                oficio_codigo=None,
                oficio_ambiguo=True,
                proveedor_codigo=None,
                proveedor_nombre=None,
                urgencia=None,
                listado=None,
                duplicada_de=str(_id(2)),
                importacion_id=str(_id(1)),
                incidencia_id=str(_id(3)),
            ),
        ],
    )

    filas = _repositorio(conexion).listar(obra_codigo=OBRA, limite=200)

    assert filas == (
        IncidenciaEnBandeja(
            incidencia_id=_id(2),
            importacion_id=_id(1),
            fila_origen=2,
            unidad_codigo="U-07",
            unidad_nombre="VILLA INVENTADA 7",
            ubicacion="Salon",
            descripcion=DESCRIPCION,
            detalle=None,
            oficio_codigo="0046",
            oficio_nombre="Carpinteria inventada",
            oficio_ambiguo=False,
            proveedor_codigo=PROVEEDOR_CODIGO,
            proveedor_nombre=PROVEEDOR_NOMBRE,
            proveedor_ambiguo=False,
            urgencia=Urgencia.URGENTE,
            listado=Listado.PRIMERO,
            duplicada_de=None,
            creada_at_utc=AHORA,
        ),
        IncidenciaEnBandeja(
            incidencia_id=_id(3),
            importacion_id=_id(1),
            fila_origen=3,
            unidad_codigo="U-07",
            unidad_nombre="VILLA INVENTADA 7",
            ubicacion="Salon",
            descripcion=DESCRIPCION,
            detalle=None,
            oficio_codigo=None,
            oficio_nombre="Carpinteria inventada",
            oficio_ambiguo=True,
            proveedor_codigo=None,
            proveedor_nombre=None,
            proveedor_ambiguo=False,
            urgencia=None,
            listado=None,
            duplicada_de=_id(2),
            creada_at_utc=AHORA,
        ),
    )
    assert conexion.primera_con("FROM postventa.bandeja_incidencias").parametros == (
        OBRA,
        200,
    )
    assert conexion.commits == 1


@pytest.mark.parametrize(
    ("urgencia", "listado"),
    (("seguridad", None), (None, "segundo")),
)
def test_f036_r45_urgencia_y_listado_se_leen_cada_una_de_su_columna(urgencia, listado):
    """Una sin la otra: la urgencia no depende de que haya listado, ni al revés
    (lo destapó la mutación del Bloque 5)."""
    conexion = ConexionDoble()
    conexion.responder(
        "FROM postventa.bandeja_incidencias",
        [_fila_bandeja(5, urgencia=urgencia, listado=listado)],
    )

    (fila,) = _repositorio(conexion).listar(obra_codigo=OBRA, limite=5)

    assert fila.urgencia == (None if urgencia is None else Urgencia(urgencia))
    assert fila.listado == (None if listado is None else Listado(listado))


def test_f036_r45_una_incidencia_web_sin_importacion_ni_fila():
    conexion = ConexionDoble()
    conexion.responder(
        "FROM postventa.bandeja_incidencias",
        [_fila_bandeja(4, importacion_id=None, fila_origen=None)],
    )

    (fila,) = _repositorio(conexion).listar(obra_codigo=OBRA, limite=5)

    assert fila.importacion_id is None
    assert fila.fila_origen is None


def test_f036_r45_listar_acota_el_limite_antes_de_llegar_a_la_base():
    conexion = ConexionDoble()

    assert _repositorio(conexion).listar(obra_codigo=OBRA, limite=9_999) == ()
    assert conexion.primera_con("LIMIT").parametros == (OBRA, 500)


def test_f036_r45_si_la_base_falla_al_listar_es_503():
    conexion = ConexionDoble()
    conexion.fallar(
        "FROM postventa.bandeja_incidencias", psycopg.OperationalError("caida")
    )

    with pytest.raises(PersistenciaNoDisponible) as fallo:
        _repositorio(conexion).listar(obra_codigo=OBRA, limite=5)

    assert "listar_bandeja" in fallo.value.motivo


# ==========================================================================
# EquivalenciasPort (§15.4): por pares, por catálogo y append-only
# ==========================================================================


def _equivalencias(conexion: ConexionDoble) -> RepositorioEquivalenciasPostgres:
    return RepositorioEquivalenciasPostgres(conexion, esquema=ESQUEMA)


def test_f036_r81_registrar_decisiones_en_una_transaccion():
    conexion = ConexionDoble()
    decisiones = (_decision(), _decision("0033", "0133", decision="distinto"))

    _equivalencias(conexion).registrar(decisiones=decisiones)

    assert len(conexion.ejecutadas) == 1
    assert conexion.ejecutadas[0].sql.startswith(
        "INSERT INTO postventa.decisiones_equivalencia"
    )
    assert len(conexion.ejecutadas[0].parametros) == 16
    assert conexion.commits == 1


def test_f036_t15_registrar_cero_decisiones_no_toca_la_base():
    conexion = ConexionDoble()

    _equivalencias(conexion).registrar(decisiones=())

    assert conexion.ejecutadas == []
    assert conexion.commits == 0


def test_f036_r81_si_la_base_falla_no_se_guarda_ninguna_decision():
    conexion = ConexionDoble()
    conexion.fallar("decisiones_equivalencia", psycopg.OperationalError("caida"))

    with pytest.raises(PersistenciaNoDisponible) as fallo:
        _equivalencias(conexion).registrar(decisiones=(_decision(),))

    assert (conexion.commits, conexion.rollbacks) == (0, 1)
    assert "registrar_decisiones" in fallo.value.motivo
    assert OID not in fallo.value.motivo


def test_f036_r95_las_ultimas_decisiones_vuelven_como_decisiones_del_dominio():
    conexion = ConexionDoble()
    conexion.responder(
        "DISTINCT ON",
        [
            ("oficio", "0046", "0143", "mismo", "mismo_nombre", OBRA, OID, AHORA),
            ("oficio", "0033", "0133", "distinto", None, "8888", OID, DESPUES),
        ],
    )

    decisiones = _equivalencias(conexion).ultimas_decisiones(
        catalogo=Catalogo.OFICIO, codigos=("0046", "0143", "0033", "0133")
    )

    assert decisiones == (
        _decision(),
        DecisionPar(
            catalogo=Catalogo.OFICIO,
            codigo_a="0033",
            codigo_b="0133",
            decision="distinto",
            motivos=frozenset(),
            obra_codigo="8888",
            decidido_por=OID,
            decidido_at_utc=DESPUES,
        ),
    )
    assert conexion.primera_con("DISTINCT ON").parametros[0] == "oficio"
    assert conexion.commits == 1


def test_f036_r95_el_catalogo_viaja_como_parametro_y_separa_los_mismos_codigos():
    """R95 · un código de oficio y otro de proveedor escritos igual no se mezclan."""
    conexion = ConexionDoble()

    _equivalencias(conexion).ultimas_decisiones(
        catalogo=Catalogo.PROVEEDOR, codigos=("0046", "0143")
    )
    _equivalencias(conexion).registrar(
        decisiones=(_decision(catalogo=Catalogo.PROVEEDOR),)
    )

    assert conexion.primera_con("DISTINCT ON").parametros[0] == "proveedor"
    assert conexion.primera_con("INSERT").parametros[0] == "proveedor"


@pytest.mark.parametrize("codigos", ((), ("0046",), ("0046", "0046")))
def test_f036_t15_con_menos_de_dos_codigos_no_hay_pares_ni_consulta(codigos):
    conexion = ConexionDoble()

    assert (
        _equivalencias(conexion).ultimas_decisiones(
            catalogo=Catalogo.OFICIO, codigos=codigos
        )
        == ()
    )
    assert conexion.ejecutadas == []


def test_f036_t15_con_dos_codigos_si_hay_consulta():
    conexion = ConexionDoble()

    _equivalencias(conexion).ultimas_decisiones(
        catalogo=Catalogo.OFICIO, codigos=("0046", "0143")
    )

    assert conexion.veces_con("DISTINCT ON") == 1


def test_f036_t15_si_la_base_falla_al_leer_decisiones_es_503():
    conexion = ConexionDoble()
    conexion.fallar("DISTINCT ON", psycopg.OperationalError("caida"))

    with pytest.raises(PersistenciaNoDisponible) as fallo:
        _equivalencias(conexion).ultimas_decisiones(
            catalogo=Catalogo.OFICIO, codigos=("a", "b")
        )

    assert "ultimas_decisiones" in fallo.value.motivo


def test_f036_r47_el_log_de_las_decisiones_solo_lleva_catalogo_y_recuento(caplog):
    conexion = ConexionDoble()

    with caplog.at_level(logging.DEBUG):
        _equivalencias(conexion).registrar(
            decisiones=(_decision(), _decision("0033", "0133"))
        )

    assert "catalogos=oficio" in caplog.text
    assert "pares=2" in caplog.text
    for prohibido in ("0046", "0143", "0033", "0133", OID, OBRA):
        assert prohibido not in caplog.text, prohibido


# ==========================================================================
# La fábrica: la misma receta que construir_repositorio
# ==========================================================================


def _ajustes(**cambios) -> Ajustes:
    base = {
        "entorno": "dev",
        "pg_host": "host.inventado.ejemplo",
        "pg_base": "base_inventada",
        "pg_usuario": "usuario_inventado",
        "pg_password": "contrasena-inventada",
        "pg_esquema": "otro_inventado",
    }
    base.update(cambios)
    return Ajustes(_env_file=None, **base)


@pytest.fixture
def conexion_de_la_fabrica(monkeypatch):
    """`psycopg.connect` y el DDL, sustituidos: sin red y sin tocar ningún esquema."""
    conexion = ConexionDoble()
    llamadas: dict[str, object] = {}

    def conectar(dsn, *, password):
        llamadas["dsn"] = dsn
        llamadas["password"] = password
        return conexion

    def asegurar(conn, *, ajustes):
        llamadas["asegurado"] = (conn, ajustes.pg_esquema)
        return 0

    monkeypatch.setattr(fabrica.psycopg, "connect", conectar)
    monkeypatch.setattr(fabrica, "asegurar_esquema", asegurar)
    return conexion, llamadas


@pytest.mark.parametrize(
    ("construir", "clase"),
    (
        (fabrica.construir_bandeja, RepositorioBandejaPostgres),
        (fabrica.construir_equivalencias, RepositorioEquivalenciasPostgres),
        (fabrica.construir_repositorio, fabrica.RepositorioPostgres),
    ),
)
def test_f036_t15_la_fabrica_abre_fija_la_sesion_y_asegura_el_esquema(
    conexion_de_la_fabrica, construir, clase
):
    conexion, llamadas = conexion_de_la_fabrica

    repositorio = construir(_ajustes())

    assert isinstance(repositorio, clase)
    assert repositorio._conexion is conexion
    assert repositorio._esquema == "otro_inventado"
    assert "contrasena-inventada" not in llamadas["dsn"]
    assert llamadas["password"] == "contrasena-inventada"
    assert llamadas["asegurado"] == (conexion, "otro_inventado")
    assert conexion.sql_ejecutado[0] == "SET search_path TO otro_inventado"
    assert len(conexion.sql_ejecutado) == 5
    assert conexion.commits == 1


@pytest.mark.parametrize(
    "construir", (fabrica.construir_bandeja, fabrica.construir_equivalencias)
)
def test_f036_t15_sin_contrasena_la_fabrica_no_abre_nada(
    conexion_de_la_fabrica, construir
):
    conexion, llamadas = conexion_de_la_fabrica

    with pytest.raises(ConfiguracionPgIncompleta):
        construir(_ajustes(pg_password="  "))

    assert llamadas == {}
    assert conexion.ejecutadas == []


@pytest.mark.parametrize(
    "construir", (fabrica.construir_bandeja, fabrica.construir_equivalencias)
)
def test_f036_t15_desde_local_contra_un_host_remoto_no_se_conecta(
    conexion_de_la_fabrica, construir
):
    _, llamadas = conexion_de_la_fabrica

    with pytest.raises(DdlNoPermitidoAqui):
        construir(_ajustes(entorno="local"))

    assert llamadas == {}


@pytest.mark.parametrize(
    "construir", (fabrica.construir_bandeja, fabrica.construir_equivalencias)
)
def test_f036_t15_si_no_se_puede_conectar_es_503(monkeypatch, construir):
    def conectar(dsn, *, password):
        raise psycopg.OperationalError("inventado")

    monkeypatch.setattr(fabrica.psycopg, "connect", conectar)

    with pytest.raises(PersistenciaNoDisponible):
        construir(_ajustes())


def test_f036_t15_la_fabrica_exporta_las_tres_construcciones():
    assert fabrica.__all__ == [
        "construir_bandeja",
        "construir_equivalencias",
        "construir_repositorio",
    ]
