# services/postventa-api/infrastructure/persistencia/sentencias.py
"""El SQL de cada operación: texto y parámetros, sin abrir nada.

Módulo **puro**. Cada función devuelve `(sql, parametros)`, y **ningún valor
se interpola nunca en el texto**: los valores viajan como parámetros del
driver. Lo único que se pega al SQL es el nombre del esquema, que se valida
antes como identificador (`validar_nombre_de_esquema`).

## `xmax = 0`, o cómo se sabe si se creó o se actualizó

Todas las escrituras son `INSERT … ON CONFLICT … DO UPDATE`, que es la forma
de que **reprocesar actualice y no duplique** (R14–R17). Para distinguir las
dos cosas sin una segunda consulta se devuelve `(xmax = 0) AS creado`: en la
fila que acaba de insertarse, `xmax` vale 0; en la que se actualizó, no. Y en
el caso del cierre terminal, que no se actualiza, **no vuelve ninguna fila**,
que es justo lo que R25 pide poder distinguir.

## Lo que se conserva y lo que se refresca

En `partes`, el `DO UPDATE` **no toca `primera_vez_at_utc`** y sí incrementa
`reprocesos` (R15). Es la diferencia entre saber que un parte se ha subido
tres veces desde marzo y creer que llegó hoy.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from domain.models.cierre import CorrespondenciaSigrid
from domain.models.extraccion import ExtraccionParte
from domain.models.persistencia import (
    PreferenciasUsuario,
    RegistroRemesa,
    TrazaArchivo,
    TrazaCierre,
)
from domain.models.remesa import ParteTroceado
from domain.models.validacion import Destino, ResultadoValidacion

from infrastructure.persistencia.ddl import validar_nombre_de_esquema
from infrastructure.persistencia.mapeo import (
    columnas_de_campos,
    json_de_avisos,
    valores_de_campos,
    valores_de_traza_ia,
    valores_de_validacion,
)

__all__ = [
    "LIMITE_MAXIMO_COLA",
    "select_cola",
    "select_login_sigrid",
    "select_preferencias",
    "upsert_archivo",
    "upsert_cierre",
    "upsert_login_sigrid",
    "upsert_parte",
    "upsert_preferencias",
    "upsert_remesa",
    "upsert_validacion",
]

#: Techo de la consulta de la cola. El servidor es un `Standard_B1ms` de 1 vCPU
#: compartido: una petición que pidiera cien mil filas no se la come ella sola,
#: se la comen los demás.
LIMITE_MAXIMO_COLA = 500

#: Las columnas de `partes` que no dependen de los campos leídos.
_COLUMNAS_FIJAS_PARTE: tuple[str, ...] = (
    "hash_parte",
    "remesa_id",
    "origen",
    "paginas_origen",
    "modo_deteccion",
    "primera_vez_at_utc",
    "actualizado_at_utc",
)

#: Las cinco columnas de la traza de IA (R19).
_COLUMNAS_TRAZA_IA: tuple[str, ...] = (
    "ia_proveedor",
    "ia_modelo",
    "prompt_key",
    "prompt_version",
    "prompt_huella",
)

#: Lo único de `partes` que **no** se refresca al reprocesar (R15).
_NO_SE_PISA_AL_REPROCESAR = frozenset({"hash_parte", "primera_vez_at_utc"})


def upsert_remesa(*, esquema: str, remesa: RegistroRemesa) -> tuple[str, tuple]:
    """Guarda una remesa; volver a guardarla con el mismo `id` la actualiza."""
    tabla = _tabla(esquema, "remesas")
    columnas = (
        "id",
        "nombre_origen",
        "recibida_at_utc",
        "num_partes",
        "avisos",
        "usuario_oid",
    )
    sql = (
        f"INSERT INTO {tabla} ({', '.join(columnas)})\n"
        f"VALUES (%s, %s, %s, %s, %s::jsonb, %s)\n"
        f"ON CONFLICT (id) DO UPDATE SET\n"
        f"{_asignaciones(columnas, excluidas={'id'})}\n"
        f"RETURNING (xmax = 0) AS creado"
    )
    parametros = (
        remesa.id,
        remesa.nombre_origen,
        remesa.recibida_at_utc,
        remesa.num_partes,
        json_de_avisos(remesa.avisos),
        remesa.usuario_oid,
    )
    return sql, parametros


def upsert_parte(
    *,
    esquema: str,
    parte: ParteTroceado,
    extraccion: ExtraccionParte,
    remesa_id: str,
    ahora: datetime,
) -> tuple[str, tuple]:
    """Guarda el parte y lo leído de él; reprocesarlo actualiza (R14, R15).

    De `parte` se toman su huella, su origen, sus páginas y el modo de
    detección. **Sus bytes no entran** (R12, R40): el PDF lleva el DNI
    manuscrito, vive en SharePoint, y el disco de este servidor es compartido.
    """
    tabla = _tabla(esquema, "partes")
    columnas = (
        *_COLUMNAS_FIJAS_PARTE,
        *columnas_de_campos(),
        *_COLUMNAS_TRAZA_IA,
        "avisos_extraccion",
    )
    marcadores = ", ".join(
        "%s::jsonb" if columna == "avisos_extraccion" else "%s" for columna in columnas
    )
    asignaciones = _asignaciones(columnas, excluidas=_NO_SE_PISA_AL_REPROCESAR)

    sql = (
        f"INSERT INTO {tabla} ({', '.join(columnas)})\n"
        f"VALUES ({marcadores})\n"
        f"ON CONFLICT (hash_parte) DO UPDATE SET\n"
        f"{asignaciones},\n"
        f"    reprocesos = {tabla}.reprocesos + 1\n"
        f"RETURNING (xmax = 0) AS creado"
    )
    parametros = (
        parte.hash,
        remesa_id,
        parte.origen,
        list(parte.paginas_origen),
        parte.modo_deteccion.value,
        ahora,
        ahora,
        *valores_de_campos(extraccion),
        *valores_de_traza_ia(extraccion),
        json_de_avisos(extraccion.avisos),
    )
    return sql, parametros


def upsert_validacion(
    *, esquema: str, resultado: ResultadoValidacion, ahora: datetime
) -> tuple[str, tuple]:
    """Guarda el veredicto **sustituyendo** el anterior (R17).

    La clave primaria es el `hash_parte`, así que revalidar un parte —lo que
    hará F-011 cuando alguien corrija un campo— no puede acumular una segunda
    fila con un veredicto distinto para el mismo parte.
    """
    tabla = _tabla(esquema, "validaciones")
    columnas = (
        "hash_parte",
        "veredicto",
        "destino",
        "clasificacion_firma",
        "motivos",
        "avisos",
        "validado_at_utc",
    )
    sql = (
        f"INSERT INTO {tabla} ({', '.join(columnas)})\n"
        f"VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)\n"
        f"ON CONFLICT (hash_parte) DO UPDATE SET\n"
        f"{_asignaciones(columnas, excluidas={'hash_parte'})}\n"
        f"RETURNING (xmax = 0) AS creado"
    )
    return sql, valores_de_validacion(resultado, ahora)


def upsert_archivo(*, esquema: str, traza: TrazaArchivo) -> tuple[str, tuple]:
    """Deja **una** fila de archivo por parte (R23).

    `intentos` se incrementa en cada reintento: es lo que permite ver que un
    parte lleva cinco subidas fallidas sin tener que leer un log.
    """
    tabla = _tabla(esquema, "archivos")
    columnas = (
        "hash_parte",
        "estado",
        "nombre_fichero",
        "carpeta",
        "drive_id",
        "item_id",
        "web_url",
        "motivo",
        "archivado_at_utc",
    )
    sql = (
        f"INSERT INTO {tabla} ({', '.join(columnas)}, intentos)\n"
        f"VALUES ({', '.join(['%s'] * len(columnas))}, 0)\n"
        f"ON CONFLICT (hash_parte) DO UPDATE SET\n"
        f"{_asignaciones(columnas, excluidas={'hash_parte'})},\n"
        f"    intentos = {tabla}.intentos + 1\n"
        f"RETURNING (xmax = 0) AS creado"
    )
    parametros = (
        traza.hash_parte,
        traza.estado.value,
        traza.nombre_fichero,
        traza.carpeta,
        traza.drive_id,
        traza.item_id,
        traza.web_url,
        traza.motivo,
        traza.archivado_at_utc,
    )
    return sql, parametros


def upsert_cierre(*, esquema: str, traza: TrazaCierre) -> tuple[str, tuple]:
    """Registra el cierre, **sin pisar uno ya cerrado** (R25, R26).

    El `WHERE` del `DO UPDATE` es la pieza clave: si la fila ya está en
    `cerrado`, no se actualiza y la sentencia **no devuelve ninguna fila**. El
    repositorio lee esa ausencia como `SIN_CAMBIOS`. Sin ese `WHERE`, volver a
    ejecutar el cierre reescribiría la traza de una escritura real en el ERP de
    producción.
    """
    tabla = _tabla(esquema, "cierres")
    columnas = (
        "hash_parte",
        "numero_incidencia",
        "estado",
        "estado_origen_sigrid",
        "estado_destino_sigrid",
        "dry_run_at_utc",
        "cerrado_at_utc",
        "confirmado_por",
        "motivo",
    )
    sql = (
        f"INSERT INTO {tabla} ({', '.join(columnas)}, intentos)\n"
        f"VALUES ({', '.join(['%s'] * len(columnas))}, 0)\n"
        f"ON CONFLICT (hash_parte) DO UPDATE SET\n"
        f"{_asignaciones(columnas, excluidas={'hash_parte'})},\n"
        f"    intentos = {tabla}.intentos + 1\n"
        f"WHERE {tabla}.estado <> %s\n"
        f"RETURNING (xmax = 0) AS creado"
    )
    parametros = (
        traza.hash_parte,
        traza.numero_incidencia,
        traza.estado.value,
        traza.estado_origen_sigrid,
        traza.estado_destino_sigrid,
        traza.dry_run_at_utc,
        traza.cerrado_at_utc,
        traza.confirmado_por,
        traza.motivo,
        _ESTADO_TERMINAL,
    )
    return sql, parametros


def select_cola(*, esquema: str, limite: int) -> tuple[str, tuple]:
    """Los partes que esperan que una persona decida (R22).

    Las observaciones se traen **de `partes` con un `JOIN`**: no hay copia en
    `validaciones` (R21, R39). Y el destino va como parámetro, no pegado al
    texto: es un valor, y los valores no se interpolan.
    """
    validaciones = _tabla(esquema, "validaciones")
    partes = _tabla(esquema, "partes")
    sql = (
        "SELECT v.hash_parte, p.codigo_obra, p.numero_incidencia,\n"
        "       p.observaciones, p.observaciones_confianza_pct,\n"
        "       v.clasificacion_firma, v.motivos, v.validado_at_utc\n"
        f"FROM {validaciones} AS v\n"
        f"JOIN {partes} AS p ON p.hash_parte = v.hash_parte\n"
        "WHERE v.destino = %s\n"
        "ORDER BY v.validado_at_utc ASC\n"
        "LIMIT %s"
    )
    return sql, (Destino.COLA_VALIDACION_HUMANA.value, _limite_seguro(limite))


def upsert_preferencias(
    *, esquema: str, preferencias: PreferenciasUsuario
) -> tuple[str, tuple]:
    """Deja **una sola** fila por usuario (R27, R28)."""
    tabla = _tabla(esquema, "preferencias_usuario")
    columnas = ("usuario_oid", "auto_cierre", "actualizado_at_utc")
    sql = (
        f"INSERT INTO {tabla} ({', '.join(columnas)})\n"
        f"VALUES (%s, %s, %s)\n"
        f"ON CONFLICT (usuario_oid) DO UPDATE SET\n"
        f"{_asignaciones(columnas, excluidas={'usuario_oid'})}\n"
        f"RETURNING (xmax = 0) AS creado"
    )
    parametros = (
        preferencias.usuario_oid,
        preferencias.auto_cierre,
        preferencias.actualizado_at_utc,
    )
    return sql, parametros


def select_preferencias(*, esquema: str, usuario_oid: str) -> tuple[str, tuple]:
    """La preferencia de un usuario, por su `oid` opaco de Entra ID."""
    tabla = _tabla(esquema, "preferencias_usuario")
    sql = (
        "SELECT usuario_oid, auto_cierre, actualizado_at_utc\n"
        f"FROM {tabla}\n"
        "WHERE usuario_oid = %s"
    )
    return sql, (usuario_oid,)


def select_login_sigrid(*, esquema: str, usuario_oid: str) -> tuple[str, tuple]:
    """La correspondencia de un usuario, por su `oid` opaco de Entra (F-009).

    La clave es el `oid` y no el correo: el correo **no se guarda en ninguna
    parte** de este proyecto. Lo que hay aquí es el par que hace falta para
    firmar el cierre en el ERP, y ni un dato más de la persona.
    """
    tabla = _tabla(esquema, "usuarios_sigrid")
    sql = (
        "SELECT usuario_oid, login_sigrid, alta_at_utc, verificado_at_utc\n"
        f"FROM {tabla}\n"
        "WHERE usuario_oid = %s"
    )
    return sql, (usuario_oid,)


def upsert_login_sigrid(
    *, esquema: str, correspondencia: CorrespondenciaSigrid
) -> tuple[str, tuple]:
    """Deja **una sola** fila por usuario, con su marca de verificación (R33).

    `alta_at_utc` **no se refresca** al reconfirmar, por la misma regla que
    `primera_vez_at_utc` en la tabla de partes: se conserva lo que cuenta la
    historia —desde cuándo existe este mapeo— y se refresca lo que cuenta el
    ahora —cuándo se comprobó por última vez contra el ERP—.

    Dos filas para la misma persona serían dos identidades para firmar el mismo
    cierre, y quién firma lo decidiría el azar de un `ORDER BY`. Lo impide la
    clave primaria, no una comprobación previa en Python.
    """
    tabla = _tabla(esquema, "usuarios_sigrid")
    columnas = ("usuario_oid", "login_sigrid", "alta_at_utc", "verificado_at_utc")
    sql = (
        f"INSERT INTO {tabla} ({', '.join(columnas)})\n"
        f"VALUES (%s, %s, %s, %s)\n"
        f"ON CONFLICT (usuario_oid) DO UPDATE SET\n"
        f"{_asignaciones(columnas, excluidas={'usuario_oid', 'alta_at_utc'})}\n"
        f"RETURNING (xmax = 0) AS creado"
    )
    parametros = (
        correspondencia.usuario_oid,
        correspondencia.login_sigrid,
        correspondencia.alta_at_utc,
        correspondencia.verificado_at_utc,
    )
    return sql, parametros


#: El estado de cierre que no se pisa (R25). Va como **parámetro**, no pegado
#: al SQL, por la misma regla que todo lo demás.
_ESTADO_TERMINAL = "cerrado"


def _tabla(esquema: str, nombre: str) -> str:
    """`<esquema>.<tabla>`, con el esquema validado como identificador.

    Es lo único que se pega al texto del SQL, y por eso se valida aquí: un
    `PG_SCHEMA` hostil sería una inyección con permisos de despliegue.
    """
    validar_nombre_de_esquema(esquema)
    return f"{esquema}.{nombre}"


def _asignaciones(columnas: Sequence[str], *, excluidas: Any) -> str:
    """El `SET col = EXCLUDED.col` de un `DO UPDATE`, salvo las excluidas."""
    return ",\n".join(
        f"    {columna} = EXCLUDED.{columna}"
        for columna in columnas
        if columna not in excluidas
    )


def _limite_seguro(limite: int) -> int:
    """El límite pedido, acotado entre 1 y `LIMITE_MAXIMO_COLA`.

    Se acota en vez de fallar porque quien pide la cola es el front, y un
    límite absurdo no debe tumbar la pantalla; lo que no puede es llegar a la
    base y ponerse a leer sin techo en un servidor de 1 vCPU compartido.
    """
    return max(1, min(limite, LIMITE_MAXIMO_COLA))
