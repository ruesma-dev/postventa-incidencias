# services/postventa-api/infrastructure/persistencia/sentencias_bandeja.py
"""El SQL de la bandeja y de las decisiones de equivalencia (F-036), sin abrir nada.

`specs/F-036-importar-excel/design.md` §6.2. Módulo **puro**, con la misma
regla que `sentencias.py`: cada función devuelve `(sql, parametros)` y
**ningún valor se interpola nunca en el texto**. Lo único que se pega al SQL
es el nombre del esquema, validado antes como identificador. Va en un módulo
propio (§2.3): tocar `sentencias.py` arrastraría la mutación de F-005…F-034.

## La no duplicación es de la base (R41)

`insert_primeras` mete la primera fila de cada grupo en **una** sentencia con
`ON CONFLICT (obra_codigo, clave_duplicado) WHERE duplicada_de IS NULL DO
NOTHING`: quien decide es el índice único parcial `ux_bandeja_clave`, no una
consulta previa, y dos importaciones simultáneas del mismo contenido no dejan
dos filas no duplicadas con la misma clave. `insert_duplicadas` no lleva
`ON CONFLICT`: una fila con `duplicada_de` no entra en ese índice.

## Append-only (R81)

`insert_decisiones` no lleva `ON CONFLICT` ni hay ningún `UPDATE` ni `DELETE`
de `decisiones_equivalencia`: manda la última fila de cada par, y la lee
`select_ultimas_decisiones` con `DISTINCT ON`.

Aquí viven también las traducciones de fila a dominio de estas tablas, puras
como el SQL, para que el repositorio solo tenga que ejecutar.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Sequence
from typing import Any
from uuid import UUID

from domain.models.equivalencias import Catalogo, DecisionPar, Motivo
from domain.models.importacion import (
    Elegido,
    EstadoImportacion,
    IncidenciaEnBandeja,
    IncidenciaValida,
)
from domain.models.plantilla_incidencias import Listado, OrigenIncidencia, Urgencia
from domain.ports.bandeja import RegistroImportacion, ResultadoImportacion

from infrastructure.persistencia.ddl import validar_nombre_de_esquema

__all__ = [
    "COLUMNAS_BANDEJA",
    "LIMITE_MAXIMO_BANDEJA",
    "como_uuid",
    "fila_a_decision",
    "fila_a_incidencia",
    "fila_a_resultado_ya_importado",
    "insert_decisiones",
    "insert_duplicadas",
    "insert_importacion",
    "insert_primeras",
    "motivos_de_texto",
    "select_bandeja",
    "select_existentes_por_clave",
    "select_importacion_completa_por_hash",
    "select_ultimas_decisiones",
    "texto_de_motivos",
    "update_recuentos",
    "valores_de_fila",
]

#: Techo de `GET /api/bandeja` (R45). El borde ya lo exige; se aplica **también**
#: aquí, como la cola de F-019: el servidor es de 1 vCPU y compartido.
LIMITE_MAXIMO_BANDEJA = 500

#: Las columnas de `13_bandeja_incidencias.sql`, en su orden.
COLUMNAS_BANDEJA: tuple[str, ...] = (
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

#: Las que se escriben al registrar la importación: los tres recuentos de la
#: bandeja nacen a 0 (su `DEFAULT`) y los fija `update_recuentos`.
_COLUMNAS_IMPORTACION: tuple[str, ...] = (
    "importacion_id",
    "hash_fichero",
    "nombre_fichero",
    "obra_codigo",
    "plantilla_version",
    "estado",
    "importado_por",
    "importado_at_utc",
    "filas_leidas",
    "filas_con_error",
)

#: Las que se leen de una importación, en el orden de `fila_a_resultado_ya_importado`.
_COLUMNAS_LECTURA_IMPORTACION: tuple[str, ...] = (
    "importacion_id",
    "hash_fichero",
    "nombre_fichero",
    "obra_codigo",
    "plantilla_version",
    "importado_por",
    "importado_at_utc",
    "filas_leidas",
    "filas_con_error",
    "estado",
    "filas_nuevas",
    "filas_duplicadas_en_fichero",
    "filas_ya_en_bandeja",
)

#: Las que devuelve `listar`: los campos de `IncidenciaEnBandeja`, en su orden.
_COLUMNAS_LISTADO: tuple[str, ...] = (
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
)

#: Las de `14_decisiones_equivalencia.sql` que se escriben y se leen (sin el
#: `decision_id`, que pone la base).
_COLUMNAS_DECISION: tuple[str, ...] = (
    "catalogo",
    "codigo_a",
    "codigo_b",
    "decision",
    "motivos",
    "obra_codigo",
    "decidido_por",
    "decidido_at_utc",
)

#: Separador de los motivos en su columna de texto (`'errata,plural'`).
_SEPARADOR_MOTIVOS = ","

#: Entre las filas de un `VALUES` de varias.
_ENTRE_FILAS = ",\n"


# --- importaciones -----------------------------------------------------------


def insert_importacion(
    *, esquema: str, importacion: RegistroImportacion
) -> tuple[str, tuple]:
    """Paso 1 de `registrar` (§5.3): la importación, con su estado (R42)."""
    tabla = _tabla(esquema, "importaciones")
    sql = (
        f"INSERT INTO {tabla} ({', '.join(_COLUMNAS_IMPORTACION)})\n"
        f"VALUES {_marcas(len(_COLUMNAS_IMPORTACION))}"
    )
    parametros = (
        importacion.importacion_id,
        importacion.hash_fichero,
        importacion.nombre_fichero,
        importacion.obra_codigo,
        importacion.plantilla_version,
        importacion.estado.value,
        importacion.importado_por,
        importacion.importado_at_utc,
        importacion.filas_leidas,
        importacion.filas_con_error,
    )
    return sql, parametros


def select_importacion_completa_por_hash(
    *, esquema: str, hash_fichero: str
) -> tuple[str, tuple]:
    """El atajo de R39: la **primera** importación completa con esos bytes.

    Dos subidas simultáneas pueden dejar dos completas (§5.3); «el resumen de
    entonces» es el de la primera, la que hizo el trabajo.
    """
    tabla = _tabla(esquema, "importaciones")
    sql = (
        f"SELECT {', '.join(_COLUMNAS_LECTURA_IMPORTACION)}\n"
        f"FROM {tabla}\n"
        "WHERE hash_fichero = %s AND estado = %s\n"
        "ORDER BY importado_at_utc, importacion_id\n"
        "LIMIT 1"
    )
    return sql, (hash_fichero, EstadoImportacion.COMPLETA.value)


def update_recuentos(
    *,
    esquema: str,
    importacion_id: UUID,
    nuevas: int,
    duplicadas_en_fichero: int,
    ya_en_bandeja: int,
) -> tuple[str, tuple]:
    """Paso 5 de `registrar`: los recuentos que solo se saben al final."""
    tabla = _tabla(esquema, "importaciones")
    sql = (
        f"UPDATE {tabla}\n"
        "SET filas_nuevas = %s, filas_duplicadas_en_fichero = %s, filas_ya_en_bandeja = %s\n"
        "WHERE importacion_id = %s"
    )
    return sql, (nuevas, duplicadas_en_fichero, ya_en_bandeja, importacion_id)


def fila_a_resultado_ya_importado(fila: Sequence[Any]) -> ResultadoImportacion:
    """Una fila de `select_importacion_completa_por_hash`, como resumen de R39."""
    importacion = RegistroImportacion(
        importacion_id=como_uuid(fila[0]),
        hash_fichero=fila[1],
        nombre_fichero=fila[2],
        obra_codigo=fila[3],
        plantilla_version=fila[4],
        importado_por=fila[5],
        importado_at_utc=fila[6],
        filas_leidas=fila[7],
        filas_con_error=fila[8],
    )
    return ResultadoImportacion(
        importacion=importacion,
        ya_importado=True,
        estado=EstadoImportacion(fila[9]),
        nuevas=fila[10],
        duplicadas_en_fichero=fila[11],
        ya_en_bandeja=fila[12],
        con_error=fila[8],
        filas=(),
    )


# --- bandeja -----------------------------------------------------------------


def valores_de_fila(
    importacion: RegistroImportacion,
    valida: IncidenciaValida,
    *,
    incidencia_id: UUID,
    clave: str,
    duplicada_de: UUID | None,
) -> tuple:
    """Los valores de una fila de la bandeja, en el orden de `COLUMNAS_BANDEJA`.

    `unidad_nombre` es la etiqueta que vio quien rellenó (§4.1); `creada_at_utc`,
    el instante de la importación, para que el listado ponga las de la más
    reciente primero (R45).
    """
    oficio_codigo, oficio_nombre, oficio_ambiguo = _columnas_de(valida.oficio)
    proveedor_codigo, proveedor_nombre, proveedor_ambiguo = _columnas_de(
        valida.proveedor
    )
    return (
        incidencia_id,
        OrigenIncidencia.EXCEL.value,
        importacion.importacion_id,
        valida.fila,
        importacion.obra_codigo,
        valida.unidad.codigo,
        valida.unidad.etiqueta,
        valida.ubicacion,
        valida.descripcion,
        valida.detalle,
        oficio_codigo,
        oficio_nombre,
        oficio_ambiguo,
        proveedor_codigo,
        proveedor_nombre,
        proveedor_ambiguo,
        None if valida.urgencia is None else valida.urgencia.value,
        None if valida.listado is None else valida.listado.value,
        clave,
        duplicada_de,
        importacion.importado_at_utc,
    )


def insert_primeras(*, esquema: str, filas: Sequence[tuple]) -> tuple[str, tuple]:
    """Paso 2: la primera de cada grupo, en bloque; vuelven las que entraron (R41)."""
    sql = (
        f"{_insert_bandeja(esquema, len(filas))}\n"
        "ON CONFLICT (obra_codigo, clave_duplicado) WHERE duplicada_de IS NULL DO NOTHING\n"
        "RETURNING incidencia_id, clave_duplicado"
    )
    return sql, _aplanar(filas)


def insert_duplicadas(*, esquema: str, filas: Sequence[tuple]) -> tuple[str, tuple]:
    """Paso 4: el resto de filas de los grupos que entraron, con `duplicada_de` (R37)."""
    return _insert_bandeja(esquema, len(filas)), _aplanar(filas)


def select_existentes_por_clave(
    *, esquema: str, obra_codigo: str, claves: Iterable[str]
) -> tuple[str, tuple]:
    """Paso 3: la incidencia que ya estaba de cada clave que no entró (R38)."""
    tabla = _tabla(esquema, "bandeja_incidencias")
    sql = (
        "SELECT clave_duplicado, incidencia_id\n"
        f"FROM {tabla}\n"
        "WHERE obra_codigo = %s AND clave_duplicado = ANY(%s) AND duplicada_de IS NULL"
    )
    return sql, (obra_codigo, list(claves))


def select_bandeja(*, esquema: str, obra_codigo: str, limite: int) -> tuple[str, tuple]:
    """Las filas de una obra, las de la importación más reciente primero (R45)."""
    tabla = _tabla(esquema, "bandeja_incidencias")
    sql = (
        f"SELECT {', '.join(_COLUMNAS_LISTADO)}\n"
        f"FROM {tabla}\n"
        "WHERE obra_codigo = %s\n"
        "ORDER BY creada_at_utc DESC, fila_origen, incidencia_id\n"
        "LIMIT %s"
    )
    return sql, (obra_codigo, max(1, min(limite, LIMITE_MAXIMO_BANDEJA)))


def fila_a_incidencia(fila: Sequence[Any]) -> IncidenciaEnBandeja:
    """Una fila de `select_bandeja`, como `IncidenciaEnBandeja` (R99 lo vigila ella)."""
    return IncidenciaEnBandeja(
        incidencia_id=como_uuid(fila[0]),
        importacion_id=_uuid_o_nada(fila[1]),
        fila_origen=fila[2],
        unidad_codigo=fila[3],
        unidad_nombre=fila[4],
        ubicacion=fila[5],
        descripcion=fila[6],
        detalle=fila[7],
        oficio_codigo=fila[8],
        oficio_nombre=fila[9],
        oficio_ambiguo=fila[10],
        proveedor_codigo=fila[11],
        proveedor_nombre=fila[12],
        proveedor_ambiguo=fila[13],
        urgencia=None if fila[14] is None else Urgencia(fila[14]),
        listado=None if fila[15] is None else Listado(fila[15]),
        duplicada_de=_uuid_o_nada(fila[16]),
        creada_at_utc=fila[17],
    )


# --- decisiones de equivalencia ------------------------------------------------


def insert_decisiones(
    *, esquema: str, decisiones: Sequence[DecisionPar]
) -> tuple[str, tuple]:
    """Varios pares en una sentencia; **sin** `ON CONFLICT` (append-only, R81)."""
    if not decisiones:
        raise ValueError("no hay decisiones que insertar")
    tabla = _tabla(esquema, "decisiones_equivalencia")
    marcas = _marcas(len(_COLUMNAS_DECISION))
    sql = (
        f"INSERT INTO {tabla} ({', '.join(_COLUMNAS_DECISION)})\n"
        f"VALUES {_ENTRE_FILAS.join([marcas] * len(decisiones))}"
    )
    parametros = _aplanar(
        (
            d.catalogo.value,
            d.codigo_a,
            d.codigo_b,
            d.decision,
            texto_de_motivos(d.motivos),
            d.obra_codigo,
            d.decidido_por,
            d.decidido_at_utc,
        )
        for d in decisiones
    )
    return sql, parametros


def select_ultimas_decisiones(
    *, esquema: str, catalogo: Catalogo, codigos: Collection[str]
) -> tuple[str, tuple]:
    """La última decisión de cada par de ese catálogo entre esos códigos (§6.2).

    El orden es el del índice `ix_decisiones_equivalencia_par`; `decision_id`
    desempata dos decisiones del mismo par en el mismo instante.
    """
    tabla = _tabla(esquema, "decisiones_equivalencia")
    sql = (
        f"SELECT DISTINCT ON (codigo_a, codigo_b) {', '.join(_COLUMNAS_DECISION)}\n"
        f"FROM {tabla}\n"
        "WHERE catalogo = %s AND codigo_a = ANY(%s) AND codigo_b = ANY(%s)\n"
        "ORDER BY codigo_a, codigo_b, decidido_at_utc DESC, decision_id DESC"
    )
    ordenados = sorted(set(codigos))
    return sql, (catalogo.value, ordenados, list(ordenados))


def fila_a_decision(fila: Sequence[Any]) -> DecisionPar:
    """Una fila de `select_ultimas_decisiones`, como `DecisionPar`."""
    return DecisionPar(
        catalogo=Catalogo(fila[0]),
        codigo_a=fila[1],
        codigo_b=fila[2],
        decision=fila[3],
        motivos=motivos_de_texto(fila[4]),
        obra_codigo=fila[5],
        decidido_por=fila[6],
        decidido_at_utc=fila[7],
    )


def texto_de_motivos(motivos: Iterable[Motivo]) -> str | None:
    """`{PLURAL, ERRATA}` → `'errata,plural'`; sin motivos, `NULL`."""
    return _SEPARADOR_MOTIVOS.join(sorted(m.value for m in motivos)) or None


def motivos_de_texto(texto: str | None) -> frozenset[Motivo]:
    """Lo contrario. Un motivo que el dominio no conoce es `ValueError`."""
    if not texto:
        return frozenset()
    return frozenset(Motivo(valor) for valor in texto.split(_SEPARADOR_MOTIVOS))


# --- utilidades --------------------------------------------------------------


def _columnas_de(elegido: Elegido | None) -> tuple[str | None, str | None, bool]:
    """Código, nombre y ambigüedad de un oficio o proveedor (R99)."""
    if elegido is None:
        return None, None, False
    return elegido.codigo, elegido.etiqueta, elegido.ambiguo


def _insert_bandeja(esquema: str, filas: int) -> str:
    if filas < 1:
        raise ValueError("no hay filas que insertar en la bandeja")
    tabla = _tabla(esquema, "bandeja_incidencias")
    marcas = _marcas(len(COLUMNAS_BANDEJA))
    return (
        f"INSERT INTO {tabla} ({', '.join(COLUMNAS_BANDEJA)})\n"
        f"VALUES {_ENTRE_FILAS.join([marcas] * filas)}"
    )


def _marcas(columnas: int) -> str:
    return "(" + ", ".join(["%s"] * columnas) + ")"


def _aplanar(filas: Iterable[tuple]) -> tuple:
    return tuple(valor for fila in filas for valor in fila)


def como_uuid(valor: Any) -> UUID:
    """Un identificador de la base: psycopg devuelve `UUID`; se admite también su texto."""
    return UUID(str(valor))


def _uuid_o_nada(valor: Any) -> UUID | None:
    return None if valor is None else como_uuid(valor)


def _tabla(esquema: str, nombre: str) -> str:
    """`<esquema>.<tabla>`, con el esquema validado como identificador."""
    validar_nombre_de_esquema(esquema)
    return f"{esquema}.{nombre}"
