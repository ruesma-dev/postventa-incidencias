# services/postventa-api/tests/test_f072_persistencia.py
"""La columna `tipo_reclamacion` en las sentencias (F-072 T10, Bloque 4; R15).

`specs/F-072-tipo-reclamacion-sigrid/design.md` §6.2: `sentencias_bandeja.py`
escribe `tipo_reclamacion` en el `INSERT` y pone `listado` a `NULL`;
`sentencias_revision.py` lleva la columna en la foto (escrita y leída) y en
los importados (la fila de la bandeja leída). Módulos puros: aquí no hay base.

| Caso | Requisito |
|---|---|
| la columna, la última del `INSERT` de la bandeja; el tipo de la fila válida | R15, §6.2 |
| `listado` a `NULL` en la bandeja aunque la fila válida traiga uno | R15 |
| `select_bandeja` y `fila_a_incidencia` leen el tipo; nulo, nulo | §6.2, R19 |
| la foto de la revisión: `INSERT` con el tipo y la copia del `listado` | §6.2, R23 |
| la foto y los importados, leídos con su tipo; nulo, nulo | §6.2, R19 |

Que la base acepte y devuelva esas filas es `tests_bbdd/tests/test_f072_bbdd_tipo.py`
(T12/T13, MANUAL). Las columnas van **escritas a mano**: una lista sacada del
propio módulo daría verde ante cualquier cambio.

Datos ficticios: obra `9901`, tipos `9001`…, proveedores `EJ07`; los
identificadores, `UUID(int=n)`.
"""

from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime
from uuid import UUID

import pytest
from domain.models.importacion import Elegido, IncidenciaEnBandeja, IncidenciaValida
from domain.models.plantilla_incidencias import Listado, Opcion, Urgencia
from domain.models.revision import (
    AccionRevision,
    Quien,
    RevisionNueva,
    ValoresIncidencia,
)
from domain.ports.bandeja import RegistroImportacion
from infrastructure.persistencia import sentencias_bandeja, sentencias_revision

ESQUEMA = "postventa"
OBRA = "9901"
U1 = "9901.03VILLA 1."
CREADA = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
AHORA = datetime(2026, 10, 6, 9, 30, tzinfo=UTC)
TIPO = "9001"
OTRO_TIPO = "9002"
HUELLA = "e" * 64
CORREO = "persona@ejemplo.invalid"
QUIEN = Quien(oid="oid-de-prueba-f072", correo=CORREO)

#: Las de la bandeja que escribe el `INSERT`: las de F-036 y, la última, la de F-072.
COLUMNAS_BANDEJA = (
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
    "tipo_reclamacion",
)

#: Las que lee `select_bandeja`: los campos de `IncidenciaEnBandeja`, en su orden.
LISTADO_BANDEJA = (
    "incidencia_id",
    "importacion_id",
    "fila_origen",
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
    "duplicada_de",
    "creada_at_utc",
    "tipo_reclamacion",
)

#: Las de la bandeja que leen las situaciones de la revisión.
LEIDAS_DE_LA_BANDEJA = (
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
    "duplicada_de",
    "creada_at_utc",
    "tipo_reclamacion",
)

#: Las de una revisión que se leen (sin `revisado_por`, R10 de F-056).
LEIDAS_DE_LA_REVISION = (
    "revision_id",
    "incidencia_id",
    "accion",
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
    "huella_valores",
    "motivo",
    "revisado_correo",
    "revisado_at_utc",
    "tipo_reclamacion",
)

#: Las que escribe `insert_revision`.
ESCRITAS_EN_LA_REVISION = (
    "incidencia_id",
    "accion",
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
    "huella_valores",
    "motivo",
    "revisado_por",
    "revisado_correo",
    "revisado_at_utc",
    "tipo_reclamacion",
)

#: Las de `situacion_volcado` que añadió F-059, vacías: sin eventos.
ANCHO_DEL_VOLCADO = 8


def _plana(sql: str) -> str:
    return " ".join(sql.split())


# --------------------------------------------------------------------------
# La bandeja
# --------------------------------------------------------------------------


def _registro() -> RegistroImportacion:
    return RegistroImportacion(
        importacion_id=UUID(int=1),
        hash_fichero="a" * 64,
        nombre_fichero="ejemplo.xlsx",
        obra_codigo=OBRA,
        plantilla_version=2,
        importado_por=QUIEN.oid,
        importado_at_utc=CREADA,
        filas_leidas=1,
        filas_con_error=0,
    )


def _valida(**cambios: object) -> IncidenciaValida:
    base: dict[str, object] = {
        "fila": 2,
        "unidad": Opcion(etiqueta="Villa Ejemplo 1", codigo=U1),
        "ubicacion": "Cocina",
        "descripcion": "Ejemplo de grieta",
        "detalle": None,
        "oficio": Elegido(etiqueta="Carpintería de madera", codigo="0046", ambiguo=False),
        "proveedor": Elegido(etiqueta="Carpintería Ejemplo, S.L.", codigo="EJ07", ambiguo=False),
        "urgencia": Urgencia.URGENTE,
        "listado": None,
        "avisos": (),
        "tipo_reclamacion": TIPO,
    }
    base.update(cambios)
    return IncidenciaValida(**base)  # type: ignore[arg-type]


def _fila_de(valida: IncidenciaValida) -> dict[str, object]:
    valores = sentencias_bandeja.valores_de_fila(
        _registro(), valida, incidencia_id=UUID(int=10), clave="c" * 64, duplicada_de=None
    )
    return dict(zip(COLUMNAS_BANDEJA, valores, strict=True))


def test_f072_r15_las_columnas_de_la_bandeja_terminan_en_el_tipo():
    """La de F-072 va la última, como la deja `ADD COLUMN` en la tabla."""
    assert sentencias_bandeja.COLUMNAS_BANDEJA == COLUMNAS_BANDEJA


def test_f072_r15_la_fila_nueva_lleva_el_tipo_de_la_fila_valida():
    assert _fila_de(_valida())["tipo_reclamacion"] == TIPO
    assert _fila_de(_valida(tipo_reclamacion=OTRO_TIPO))["tipo_reclamacion"] == OTRO_TIPO


@pytest.mark.parametrize("listado", (None, Listado.PRIMERO, Listado.SEGUNDO))
def test_f072_r15_la_fila_nueva_lleva_listado_a_null(listado):
    """El `listado` de F-036 ya no se escribe (R15): aunque una fila válida
    trajera uno, la columna nace a `NULL`; el tipo es el que manda."""
    fila = _fila_de(_valida(listado=listado))

    assert fila["listado"] is None
    assert fila["tipo_reclamacion"] == TIPO


def test_f072_r15_el_insert_de_la_bandeja_escribe_la_columna():
    filas = (tuple(_fila_de(_valida()).values()),)

    for sentencia in (sentencias_bandeja.insert_primeras, sentencias_bandeja.insert_duplicadas):
        sql, parametros = sentencia(esquema=ESQUEMA, filas=filas)
        marcas = "(" + ", ".join(["%s"] * len(COLUMNAS_BANDEJA)) + ")"
        assert sql.startswith(
            f"INSERT INTO postventa.bandeja_incidencias ({', '.join(COLUMNAS_BANDEJA)})\n"
            f"VALUES {marcas}"
        )
        assert parametros == filas[0]
        assert parametros[-1] == TIPO


def test_f072_la_incidencia_en_bandeja_gana_el_tipo_como_ultimo_campo():
    """§3.2: `tipo_reclamacion: str | None = None`, el último campo."""
    campos = [c.name for c in fields(IncidenciaEnBandeja)]
    assert campos == list(LISTADO_BANDEJA)
    assert fields(IncidenciaEnBandeja)[-1].default is None
    assert [c.name for c in fields(IncidenciaValida)][-1] == "tipo_reclamacion"
    assert fields(IncidenciaValida)[-1].default is None


def test_f072_select_bandeja_lee_el_tipo():
    sql, _ = sentencias_bandeja.select_bandeja(esquema=ESQUEMA, obra_codigo=OBRA, limite=10)

    assert sql.startswith(f"SELECT {', '.join(LISTADO_BANDEJA)}\n")


def _fila_listado(tipo: str | None) -> tuple:
    valores = {
        "incidencia_id": UUID(int=10),
        "importacion_id": UUID(int=1),
        "fila_origen": 2,
        "unidad_codigo": U1,
        "unidad_nombre": "Villa Ejemplo 1",
        "ubicacion": "Cocina",
        "descripcion": "Ejemplo de grieta",
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": "EJ07",
        "proveedor_nombre": "Carpintería Ejemplo, S.L.",
        "proveedor_ambiguo": False,
        "urgencia": "urgente",
        "listado": "segundo",
        "duplicada_de": None,
        "creada_at_utc": CREADA,
        "tipo_reclamacion": tipo,
    }
    return tuple(valores[c] for c in LISTADO_BANDEJA)


@pytest.mark.parametrize("tipo", (TIPO, None))
def test_f072_fila_a_incidencia_lee_el_tipo_y_nulo_es_nulo(tipo):
    """Nulo es «anterior a F-072»: se lee nulo, y el `0002` lo pone el dominio
    (`tipo_efectivo`, R19), no la persistencia."""
    incidencia = sentencias_bandeja.fila_a_incidencia(_fila_listado(tipo))

    assert incidencia.tipo_reclamacion == tipo
    assert incidencia.listado is Listado.SEGUNDO


# --------------------------------------------------------------------------
# La revisión
# --------------------------------------------------------------------------


def _valores(**cambios: object) -> ValoresIncidencia:
    base: dict[str, object] = {
        "unidad_codigo": U1,
        "unidad_nombre": "Villa Ejemplo 1",
        "ubicacion": "Cocina",
        "descripcion": "Ejemplo de grieta",
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": "EJ07",
        "proveedor_nombre": "Carpintería Ejemplo, S.L.",
        "proveedor_ambiguo": False,
        "urgencia": Urgencia.URGENTE,
        "listado": Listado.PRIMERO,
        "tipo_reclamacion": TIPO,
    }
    base.update(cambios)
    return ValoresIncidencia(**base)  # type: ignore[arg-type]


def _nueva(valores: ValoresIncidencia) -> RevisionNueva:
    return RevisionNueva(
        incidencia_id=UUID(int=10),
        accion=AccionRevision.EDITAR,
        valores=valores,
        huella=HUELLA,
        motivo=None,
        quien=QUIEN,
        revisado_at_utc=AHORA,
    )


def test_f072_las_columnas_de_la_revision_terminan_en_el_tipo():
    assert sentencias_revision.COLUMNAS_INSERT == ESCRITAS_EN_LA_REVISION
    assert sentencias_revision._LEIDAS_DE_LA_REVISION == LEIDAS_DE_LA_REVISION
    assert sentencias_revision._LEIDAS_DE_LA_BANDEJA == LEIDAS_DE_LA_BANDEJA


@pytest.mark.parametrize("tipo", (TIPO, None))
def test_f072_r23_la_foto_se_escribe_con_el_tipo_y_la_copia_del_listado(tipo):
    """La foto lleva el tipo (nulo si lo es) y el `listado` heredado, copiado
    tal cual (R23): la revisión no lo pone a `NULL`."""
    sql, parametros = sentencias_revision.insert_revision(
        esquema=ESQUEMA, revision=_nueva(_valores(tipo_reclamacion=tipo))
    )
    escrita = dict(zip(ESCRITAS_EN_LA_REVISION, parametros, strict=True))

    assert _plana(sql) == (
        f"INSERT INTO postventa.revisiones_bandeja ({', '.join(ESCRITAS_EN_LA_REVISION)}) "
        f"VALUES ({', '.join(['%s'] * len(ESCRITAS_EN_LA_REVISION))}) RETURNING revision_id"
    )
    assert escrita["tipo_reclamacion"] == tipo
    assert escrita["listado"] == "primero"
    assert escrita["revisado_por"] == QUIEN.oid


def test_f072_el_historial_lee_el_tipo():
    sql, _ = sentencias_revision.select_revisiones(esquema=ESQUEMA, incidencia_id=UUID(int=10))

    assert sql.startswith(f"SELECT {', '.join(LEIDAS_DE_LA_REVISION)}\n")


def test_f072_las_situaciones_leen_el_tipo_de_la_bandeja_y_de_la_foto():
    sql, _ = sentencias_revision.select_situacion(esquema=ESQUEMA, incidencia_id=UUID(int=10))
    plana = _plana(sql)

    for alias in ("b", "o"):
        assert f"{alias}.creada_at_utc, {alias}.tipo_reclamacion" in plana
    for alias in ("u", "uo", "r"):
        assert f"{alias}.revisado_at_utc, {alias}.tipo_reclamacion" in plana


def _fila_revision(tipo: str | None) -> tuple:
    valores = {
        "revision_id": 7,
        "incidencia_id": UUID(int=10),
        "accion": "editar",
        "unidad_codigo": U1,
        "unidad_nombre": "Villa Ejemplo 1",
        "ubicacion": "Cocina",
        "descripcion": "Ejemplo de grieta",
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": "EJ07",
        "proveedor_nombre": "Carpintería Ejemplo, S.L.",
        "proveedor_ambiguo": False,
        "urgencia": "urgente",
        "listado": "primero",
        "huella_valores": HUELLA,
        "motivo": None,
        "revisado_correo": CORREO,
        "revisado_at_utc": AHORA,
        "tipo_reclamacion": tipo,
    }
    return tuple(valores[c] for c in LEIDAS_DE_LA_REVISION)


def _fila_bandeja(n: int, tipo: str | None, *, duplicada_de: UUID | None = None) -> tuple:
    valores = {
        "incidencia_id": UUID(int=n),
        "origen": "excel",
        "importacion_id": UUID(int=1),
        "fila_origen": n,
        "obra_codigo": OBRA,
        "unidad_codigo": U1,
        "unidad_nombre": "Villa Ejemplo 1",
        "ubicacion": "Cocina",
        "descripcion": "Ejemplo de grieta",
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": "EJ07",
        "proveedor_nombre": "Carpintería Ejemplo, S.L.",
        "proveedor_ambiguo": False,
        "urgencia": None,
        "listado": None,
        "duplicada_de": duplicada_de,
        "creada_at_utc": CREADA,
        "tipo_reclamacion": tipo,
    }
    return tuple(valores[c] for c in LEIDAS_DE_LA_BANDEJA)


@pytest.mark.parametrize("tipo", (TIPO, None))
def test_f072_la_foto_se_lee_con_su_tipo_y_nulo_es_nulo(tipo):
    revision = sentencias_revision.fila_a_revision(_fila_revision(tipo))

    assert revision.valores.tipo_reclamacion == tipo
    assert revision.valores.listado is Listado.PRIMERO


def test_f072_la_situacion_lee_el_tipo_de_los_importados_y_de_la_foto():
    """La propia (con su última revisión) y la original de una duplicada (sin
    revisiones): cada una con su tipo, y nulo como nulo."""
    sin_revision = (None,) * len(LEIDAS_DE_LA_REVISION)
    fila = (
        *_fila_bandeja(11, TIPO, duplicada_de=UUID(int=10)),
        *_fila_revision(OTRO_TIPO),
        *_fila_bandeja(10, None),
        *sin_revision,
        *(None,) * ANCHO_DEL_VOLCADO,
    )

    situacion = sentencias_revision.fila_a_situacion(fila)

    assert situacion.incidencia.tipo_reclamacion == TIPO
    assert situacion.ultima is not None
    assert situacion.ultima.valores.tipo_reclamacion == OTRO_TIPO
    assert situacion.original is not None
    assert situacion.original.incidencia.tipo_reclamacion is None
    assert situacion.original.ultima is None
    assert situacion.volcado is None
