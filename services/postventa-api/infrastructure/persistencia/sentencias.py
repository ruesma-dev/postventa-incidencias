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
from domain.models.estado import DecisionEstado, EstadoParte
from domain.models.extraccion import ExtraccionParte
from domain.models.persistencia import (
    PreferenciasUsuario,
    RegistroRemesa,
    TrazaArchivo,
    TrazaCierre,
    TrazaGrafico,
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
    "ORIGEN_DECISION_HUMANA",
    "ORIGEN_ULTIMO_CAMBIO",
    "insert_decision_estado",
    "select_cola",
    "select_estado_cierre",
    "select_grafico",
    "select_login_sigrid",
    "select_preferencias",
    "select_situacion_estado",
    "select_veredicto_y_cierre",
    "upsert_archivo",
    "upsert_cierre",
    "upsert_grafico",
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


#: Las columnas de `archivos`, en el orden en que se escriben y se leen (F-033).
#:
#: Una sola lista para el `INSERT` de `upsert_archivo` y para el tramo de la
#: traza en `select_veredicto_y_cierre`, **a propósito** y por lo mismo que
#: `_COLUMNAS_GRAFICO`: dos listas del mismo orden divergen, y el día que
#: divergieran `mapeo.fila_a_traza_archivo` leería la carpeta donde está el
#: nombre del fichero sin que nadie lo notara. Es exactamente la tupla que
#: `upsert_archivo` declaraba en su cuerpo hasta F-033, en el mismo orden.
_COLUMNAS_ARCHIVO: tuple[str, ...] = (
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


def upsert_archivo(*, esquema: str, traza: TrazaArchivo) -> tuple[str, tuple]:
    """Deja **una** fila de archivo por parte (R23), **sin pisar una archivada**.

    `intentos` se incrementa en cada reintento: es lo que permite ver que un
    parte lleva cinco subidas fallidas sin tener que leer un log.

    > **Enmienda del 2026-09-18 · F-033 T3 (R17).** Hasta hoy el `DO UPDATE` no
    > llevaba `WHERE`: cualquier escritura pisaba la fila, también una en
    > `archivado`, y con ella la carpeta, el nombre, el `drive_id`, el
    > `item_id` y el `web_url` del fichero que ya estaba subido — que dejaba de
    > ser localizable desde nuestra base.
    >
    > Ahora lleva el mismo `WHERE` que `upsert_cierre` y `upsert_grafico`: si la
    > fila ya está en `archivado`, no se actualiza y la sentencia **no devuelve
    > ninguna fila**; el repositorio lee esa ausencia como `SIN_CAMBIOS`.
    > `pendiente` y `error` se siguen pisando: son reintentos.
    >
    > El estado terminal viaja como **parámetro**, no pegado al SQL, por la
    > misma regla que todo lo demás de este módulo.
    """
    tabla = _tabla(esquema, "archivos")
    sql = (
        f"INSERT INTO {tabla} ({', '.join(_COLUMNAS_ARCHIVO)}, intentos)\n"
        f"VALUES ({', '.join(['%s'] * len(_COLUMNAS_ARCHIVO))}, 0)\n"
        f"ON CONFLICT (hash_parte) DO UPDATE SET\n"
        f"{_asignaciones(_COLUMNAS_ARCHIVO, excluidas={'hash_parte'})},\n"
        f"    intentos = {tabla}.intentos + 1\n"
        f"WHERE {tabla}.estado <> %s\n"
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
        _ESTADO_ARCHIVO_TERMINAL,
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


#: Las columnas de `graficos`, en el orden en que se escriben y se leen.
#:
#: Una sola lista para el `INSERT` y para el `SELECT` **a propósito**: dos
#: listas del mismo orden divergen, y el día que divergieran `fila_a_traza_grafico`
#: leería el `sha256` donde está el nombre del fichero sin que nadie lo notara.
_COLUMNAS_GRAFICO: tuple[str, ...] = (
    "hash_parte",
    "numero_incidencia",
    "reclamacion_ide",
    "estado",
    "sha256",
    "bytes",
    "nombre_fichero",
    "gratipide",
    "gra_cod",
    "gra_ide_negocio",
    "gra_ide_documental",
    "rcg_ide",
    "idempotente",
    "confirmado_por",
    "motivo",
    "dry_run_at_utc",
    "adjuntado_at_utc",
)


def upsert_grafico(*, esquema: str, traza: TrazaGrafico) -> tuple[str, tuple]:
    """Registra el gráfico, **sin pisar uno ya adjuntado** (F-012, R30).

    Mismo patrón que `upsert_cierre`, y la pieza clave es la misma: el `WHERE`
    del `DO UPDATE`. Si la fila ya está en `adjuntado`, no se actualiza y la
    sentencia **no devuelve ninguna fila**; el repositorio lee esa ausencia
    como `SIN_CAMBIOS`.

    Sin ese `WHERE`, un reintento reescribiría la traza de una escritura real
    en el ERP — y con ella el `gra_cod`, que es la **única** forma de localizar
    después el gráfico dentro de Sigrid.

    El estado terminal viaja como **parámetro** y no pegado al SQL, por la
    misma regla que todo lo demás de este módulo.
    """
    tabla = _tabla(esquema, "graficos")
    sql = (
        f"INSERT INTO {tabla} ({', '.join(_COLUMNAS_GRAFICO)}, intentos)\n"
        f"VALUES ({', '.join(['%s'] * len(_COLUMNAS_GRAFICO))}, 0)\n"
        f"ON CONFLICT (hash_parte) DO UPDATE SET\n"
        f"{_asignaciones(_COLUMNAS_GRAFICO, excluidas={'hash_parte'})},\n"
        f"    intentos = {tabla}.intentos + 1\n"
        f"WHERE {tabla}.estado <> %s\n"
        f"RETURNING (xmax = 0) AS creado"
    )
    parametros = (
        traza.hash_parte,
        traza.numero_incidencia,
        traza.reclamacion_ide,
        traza.estado.value,
        traza.sha256,
        traza.bytes,
        traza.nombre_fichero,
        traza.gratipide,
        traza.gra_cod,
        traza.gra_ide_negocio,
        traza.gra_ide_documental,
        traza.rcg_ide,
        traza.idempotente,
        traza.confirmado_por,
        traza.motivo,
        traza.dry_run_at_utc,
        traza.adjuntado_at_utc,
        _ESTADO_GRAFICO_TERMINAL,
    )
    return sql, parametros


def select_grafico(*, esquema: str, hash_parte: str) -> tuple[str, tuple]:
    """La traza del gráfico de un parte, por su `hash` (F-012, R2, R24, R49).

    La leen dos sitios por dos motivos distintos: `paso_grafico`, como primera
    capa de idempotencia —si dice `adjuntado`, no se llama a la pasarela ni se
    mandan los bytes—, y `paso_cierre`, como precondición del `commit`.

    Devuelve **las mismas columnas y en el mismo orden** que escribe
    `upsert_grafico`: las dos se apoyan en `_COLUMNAS_GRAFICO`.
    """
    tabla = _tabla(esquema, "graficos")
    sql = (
        f"SELECT {', '.join(_COLUMNAS_GRAFICO)}\n"
        f"FROM {tabla}\n"
        "WHERE hash_parte = %s"
    )
    return sql, (hash_parte,)


#: Las columnas de `historico_estado` que viajan en cada fila, en el orden en
#: que se escriben y en el que se leen.
#:
#: Una sola lista para el `INSERT` y para el `SELECT` **a propósito**, como
#: `_COLUMNAS_GRAFICO`: `fila_a_decision_estado` desempaqueta por posición, y
#: dos listas del mismo orden divergen — el día que divergieran, una decisión
#: volvería con la huella en el sitio del `oid` y nadie lo notaría.
#:
#: `cambio_id` no está: lo pone la base (`bigserial`) y nadie lo lee. Es lo que
#: desempata dos cambios del mismo parte en el mismo instante, y para eso basta
#: con que esté en el `ORDER BY`.
_COLUMNAS_HISTORICO: tuple[str, ...] = (
    "hash_parte",
    "estado",
    "decidido_at_utc",
    "estado_anterior",
    "decidido_por",
    "motivo",
    "huella_veredicto",
)

#: El orden del histórico: lo más reciente primero, y el contador desempata.
#:
#: Las dos cosas hacen falta. Sin `cambio_id DESC`, dos cambios del mismo parte
#: en el mismo instante —una decisión humana y la constancia que la sigue caen
#: seguidas— volverían en el orden que decidiera PostgreSQL, y la «última
#: decisión humana» sería la que tocara ese día. Es el mismo orden que declara
#: el índice `ix_historico_estado_parte`, y por eso se escribe una vez.
_ORDEN_HISTORICO = "ORDER BY decidido_at_utc DESC, cambio_id DESC"

#: Marcador de la rama que trae la última decisión **de una persona**.
#:
#: No es un valor que venga de fuera: es parte de la forma de la consulta, como
#: el nombre de la tabla, y por eso se pega al texto en vez de viajar como
#: parámetro. Las dos ramas del `UNION ALL` pueden devolver **la misma fila**
#: —cuando el último cambio lo decidió una persona—, y sin el marcador quien
#: lea no podría distinguir eso de «hay una decisión humana antigua y una
#: constancia reciente», que son situaciones opuestas.
ORIGEN_DECISION_HUMANA = "decision_humana"

#: Marcador de la rama que trae el último cambio, lo decidiera quien lo
#: decidiera. De esa fila **solo** se mira el estado, y solo para la regla de
#: constancia (R26): el histórico es constancia, nunca criterio.
ORIGEN_ULTIMO_CAMBIO = "ultimo_cambio"


def insert_decision_estado(
    *, esquema: str, decision: DecisionEstado
) -> tuple[str, tuple]:
    """Añade una fila al histórico de estado. **Append-only** (F-028, R21).

    **No lleva `ON CONFLICT`, y es el punto entero de la feature.** Las otras
    diez tablas del esquema se escriben con `ON CONFLICT (hash_parte) DO
    UPDATE` porque de cada una solo interesa el último estado; aquí interesan
    todos, en orden. `postventa.aprobaciones` es lo que pasa cuando no: un
    ciclo aprobar → rechazar → aprobar deja **una** fila y borra el rechazo por
    el camino, así que nadie puede responder después a «quién lo rechazó y por
    qué» (R25, `design.md` §0.4).

    De quien decide viaja el `oid` **opaco** de Entra ID y nada más (R15), y de
    la máquina no viaja ningún autor: `decidido_por` a `NULL` **es** «lo decidió
    la máquina» (R24). Inventarse ahí un `"sistema"` convertiría una anotación
    en una acusación, y borraría lo único que distingue las dos clases de fila.

    Ni una letra del papel entra aquí: sobre qué veredicto se decidió va como
    **huella**, y el `motivo` es texto de **quien revisa**. Los dos viajan como
    parámetros del driver, nunca interpolados en el texto.

    El `RETURNING (xmax = 0)` devuelve siempre `creado` —un `INSERT` sin
    conflicto no actualiza nada— y está para que el adaptador pueda usar el
    mismo camino de escritura que las demás operaciones.
    """
    tabla = _tabla(esquema, "historico_estado")
    sql = (
        f"INSERT INTO {tabla} ({', '.join(_COLUMNAS_HISTORICO)})\n"
        f"VALUES ({', '.join(['%s'] * len(_COLUMNAS_HISTORICO))})\n"
        f"RETURNING (xmax = 0) AS creado"
    )
    parametros = (
        decision.hash_parte,
        decision.estado.value,
        decision.decidido_at_utc,
        _valor_de_estado(decision.estado_anterior),
        decision.decidido_por,
        decision.motivo,
        decision.huella_veredicto,
    )
    return sql, parametros


def select_situacion_estado(*, esquema: str, hash_parte: str) -> tuple[str, tuple]:
    """Las **dos** últimas filas que hacen falta de un parte (`design.md` §8.5).

    Un `UNION ALL` de dos `SELECT … LIMIT 1` sobre el mismo índice:

    - la última fila **humana** (`decidido_por IS NOT NULL`), que es la decisión
      vigente y la única que manda sobre la máquina (R9);
    - la última fila **de cualquiera**, de la que solo se mira el estado y solo
      para la regla de constancia —si el estado derivado no es este, se añade
      una fila— (R26).

    Que la rama humana filtre por `decidido_por IS NOT NULL` y no por otra cosa
    no es un detalle: **quién decidió es el tipo de fila**. No hay columna
    «tipo», porque inventarse un autor para la máquina era justo lo que R24
    prohíbe. Si el filtro fuera otro, una fila de constancia podría colarse como
    decisión de una persona, y con eso se abre la puerta del circuito que
    escribe en el ERP de producción.

    Las dos ramas pueden devolver **la misma fila**; por eso cada una se marca
    con su origen.

    **Alternativa descartada** (`design.md` §8.5): un `LEFT JOIN LATERAL` que lo
    resolviera todo en una sentencia. Ahorra un viaje a la misma conexión ya
    abierta y cuesta un SQL que nadie de este repositorio sabe leer de un
    vistazo.
    """
    tabla = _tabla(esquema, "historico_estado")
    columnas = ", ".join(_COLUMNAS_HISTORICO)
    sql = (
        f"(SELECT '{ORIGEN_DECISION_HUMANA}' AS origen, {columnas}\n"
        f" FROM {tabla}\n"
        f" WHERE hash_parte = %s AND decidido_por IS NOT NULL\n"
        f" {_ORDEN_HISTORICO}\n"
        f" LIMIT 1)\n"
        f"UNION ALL\n"
        f"(SELECT '{ORIGEN_ULTIMO_CAMBIO}' AS origen, {columnas}\n"
        f" FROM {tabla}\n"
        f" WHERE hash_parte = %s\n"
        f" {_ORDEN_HISTORICO}\n"
        f" LIMIT 1)"
    )
    return sql, (hash_parte, hash_parte)


def select_estado_cierre(*, esquema: str, hash_parte: str) -> tuple[str, tuple]:
    """El estado de la traza de cierre de un parte, o ninguna fila (F-028, R18).

    Es el tercer hecho de la situación, y **es de otro sistema**: `cerrado` no
    es una opinión nuestra, es lo que dice el ERP y lo que F-009 dejó apuntado
    al escribirlo. Por eso se lee cada vez en vez de guardar una copia nuestra:
    una copia acabaría diciendo que un parte está cerrado cuando no lo está, o
    al revés (`design.md` §3).

    Se trae **solo** la columna `estado`. El resto de la traza —el número de
    incidencia, quién confirmó, el motivo— no hace falta para derivar el estado,
    y `confirmado_por` es dato personal seudónimo: lo que no se lee no se puede
    filtrar.
    """
    tabla = _tabla(esquema, "cierres")
    sql = f"SELECT estado\nFROM {tabla}\nWHERE hash_parte = %s"
    return sql, (hash_parte,)


def select_veredicto_y_cierre(*, esquema: str, hash_parte: str) -> tuple[str, tuple]:
    """El veredicto guardado **y** el estado de cierre, en un solo viaje (F-030).

    Sustituye a `select_estado_cierre` **dentro de `consultar_situacion`** y
    solo ahí: la lectura del veredicto viaja dentro de la consulta que las tres
    puertas ya ejecutaban, así que siguen siendo dos sentencias por llamada y
    **ni un viaje más** (R18). No es una optimización prematura: este
    PostgreSQL lo comparten albaranes y compañía, y una tanda son 22 partes por
    tres pasos.

    Trae **tres columnas de `partes`** que no están en `validaciones`: las
    observaciones, el código de obra y el número de incidencia. Su propio DDL
    lo manda —ahí no se copia el texto manuscrito de un cliente (R21, R39)— y
    sin ellas no se pueden recomponer los seis campos de la cadena canónica de
    la huella, que es lo que hace que una aprobación humana siga contando.

    **Se ancla en `partes` y los dos `JOIN` son `LEFT`**, y ninguna de las dos
    cosas es de estilo:

    - `validaciones` y `cierres` tienen `hash_parte` como clave primaria **y**
      como `REFERENCES postventa.partes`, así que ninguna puede tener fila
      donde no la haya en `partes`: anclar ahí no pierde nada.
    - Si se anclara en `validaciones`, un parte **sin veredicto** se llevaría
      por delante el estado de cierre, y entonces un parte **cerrado** sin fila
      de validación dejaría de dar `cerrado` — que es el hecho del ERP que gana
      a todo (F-028 R16, R18).
    - Si los `JOIN` no fueran `LEFT`, pasaría lo mismo con cada uno por su
      lado: el caso normal del primer día es un parte validado y sin cerrar.

    **Sin fila de `partes` no vuelve ninguna fila**, y eso se traduce a
    veredicto `None` y cierre `None`: es exactamente lo que devuelve hoy
    `select_estado_cierre` en ese caso, y de ahí sale el error propio de «no
    consta que este parte haya pasado la validación» (R8, R9).

    El `hash` va como **parámetro del driver**, nunca pegado al texto. Lo único
    que se interpola es el esquema, y lo valida `_tabla`.

    El orden de las diez columnas es el que lee
    `mapeo.fila_a_validacion_y_cierre`, y las dos cosas viven pegadas por eso.

    > **Enmienda del 2026-09-18 · F-033 T3 (R2, R3).** Trae también **la traza
    > de archivo**: un tercer `LEFT JOIN` a `archivos`, anclado en `partes` como
    > los otros dos, con sus ocho columnas **al final** —las diez de antes no
    > se mueven, y `fila_a_validacion_y_cierre` no se toca—. Las ocho salen de
    > `_COLUMNAS_ARCHIVO` sin el `hash`, la misma lista que escribe
    > `upsert_archivo`, y las parte `mapeo.fila_a_situacion_guardada`.
    >
    > Es lo que lee la primera capa contra el duplicado en SharePoint (L1 del
    > paso 6), y viaja aquí para que **no cueste ninguna sentencia más**: siguen
    > siendo dos por `consultar_situacion` (criterio 4 de la ficha). `LEFT` por
    > lo mismo que los otros: un parte validado y sin archivar es el caso
    > normal, y un `JOIN` a secas se llevaría por delante el veredicto.
    > `archivos` tiene el `hash_parte` como clave primaria, así que el tercer
    > `JOIN` no multiplica filas.
    >
    > El nombre de la función **se conserva**: renombrarla tocaría cinco
    > ficheros de test sin añadir nada (`design.md` §3.2).
    """
    partes = _tabla(esquema, "partes")
    validaciones = _tabla(esquema, "validaciones")
    cierres = _tabla(esquema, "cierres")
    archivos = _tabla(esquema, "archivos")
    de_archivo = ", ".join(f"a.{columna}" for columna in _COLUMNAS_ARCHIVO[1:])
    sql = (
        "SELECT v.veredicto, v.destino, v.clasificacion_firma, v.motivos,\n"
        "       v.avisos,\n"
        "       p.observaciones, p.observaciones_confianza_pct,\n"
        "       p.codigo_obra, p.numero_incidencia,\n"
        "       c.estado,\n"
        f"       {de_archivo}\n"
        f"FROM {partes} AS p\n"
        f"LEFT JOIN {validaciones} AS v ON v.hash_parte = p.hash_parte\n"
        f"LEFT JOIN {cierres} AS c ON c.hash_parte = p.hash_parte\n"
        f"LEFT JOIN {archivos} AS a ON a.hash_parte = p.hash_parte\n"
        "WHERE p.hash_parte = %s"
    )
    return sql, (hash_parte,)


def _valor_de_estado(estado: EstadoParte | None) -> str | None:
    """El literal que va a la columna, o `None` si no hay estado.

    `estado_anterior` a `None` significa «no había estado registrado antes»: es
    la primera fila de ese parte. Escribir ahí `'pendiente'` sería afirmar un
    tramo de la película que nadie presenció.
    """
    return None if estado is None else estado.value


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

#: El estado del gráfico que no se pisa (R30). También como **parámetro**.
#:
#: Es otra constante y no la misma que la del cierre porque son dos escrituras
#: externas distintas: «adjuntado pero no cerrado» es un estado real, y
#: compartir la constante haría que cambiar una cambiara la otra.
_ESTADO_GRAFICO_TERMINAL = "adjuntado"

#: El estado de archivo que no se pisa (F-033, R17). También como **parámetro**.
#:
#: Otra constante y no la del cierre ni la del gráfico por la misma razón que
#: esas dos son distintas entre sí: son hechos distintos, y compartirla haría
#: que cambiar una cambiara las otras.
_ESTADO_ARCHIVO_TERMINAL = "archivado"


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
