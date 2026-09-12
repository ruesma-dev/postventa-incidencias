# services/postventa-api/domain/models/persistencia.py
"""Entidades de lo que se guarda (F-005).

**Dominio puro**: ni `psycopg`, ni SQL, ni nombres de columna. Lo que hay aquí
es el vocabulario de lo que el proceso deja escrito —una remesa recibida, la
traza del archivo de un parte, la traza de su cierre, la preferencia de un
usuario y la cola de validación humana— con independencia de que debajo haya
PostgreSQL, un fichero o nada.

## Por qué los UUID se generan aquí y no en la base

`CLAUDE.md` prohíbe tocar el servidor compartido, y `gen_random_uuid()` exige
`CREATE EXTENSION pgcrypto`, que es exactamente una sentencia de ámbito de
base de datos. Así que el identificador de una remesa lo produce la
aplicación: `nuevo_id()`.

## Datos personales

Tres campos de este módulo llevan dato personal y van marcados uno a uno:
`EntradaCola.observaciones` es texto manuscrito del cliente (**personal
directo**), y `RegistroRemesa.usuario_oid` y `TrazaCierre.confirmado_por` son
el identificador opaco de Entra ID de un empleado (**seudónimo**). De un
empleado se guarda el `oid` y **nunca** su correo ni su nombre.

La misma regla rige `Aprobacion.aprobado_por` (F-026), que vive en
`domain/models/aprobacion.py` y no aquí: la aprobación humana es un hecho con
ciclo de vida propio, como el cierre o el gráfico, y por eso tiene su módulo.
Lo que se guarda de quien aprueba es el `oid` opaco y nada más — nunca su
correo, nunca su nombre y nunca su login del ERP (R13 de F-026).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

__all__ = [
    "EPOCA_SIN_DECIDIR",
    "EntradaCola",
    "EstadoArchivo",
    "EstadoCierre",
    "EstadoGrafico",
    "PreferenciasUsuario",
    "RegistroRemesa",
    "ResultadoGuardado",
    "TrazaArchivo",
    "TrazaCierre",
    "TrazaGrafico",
    "nuevo_id",
]


#: El instante convencional de «este usuario no ha decidido nada todavía».
#:
#: `obtener_preferencias` devuelve siempre una `PreferenciasUsuario`, nunca
#: `None`: quien no ha decidido nada **no tiene** auto-cierre, y eso es un
#: valor, no una ausencia. Hace falta un instante para acompañarlo, y se usa
#: este —la época Unix— en vez de la hora actual para que la respuesta sea
#: reproducible y para que se distinga de un vistazo de una preferencia
#: guardada de verdad.
EPOCA_SIN_DECIDIR = datetime(1970, 1, 1, tzinfo=UTC)


def nuevo_id() -> str:
    """Un identificador nuevo, en texto.

    Se genera en Python **a propósito** (`design.md` §2): usar
    `gen_random_uuid()` obligaría a `CREATE EXTENSION pgcrypto`, que es una
    sentencia de ámbito de base de datos y está prohibida en un servidor
    compartido con producción ajena.
    """
    return str(uuid.uuid4())


class EstadoArchivo(str, Enum):
    """En qué punto está el archivo del parte en SharePoint (F-006)."""

    PENDIENTE = "pendiente"
    ARCHIVADO = "archivado"
    ERROR = "error"


class EstadoCierre(str, Enum):
    """En qué punto está el cierre de la incidencia en Sigrid (F-009).

    `CERRADO` es **terminal**: una vez escrito, no se pisa (R25). `YA_CERRADA`
    es distinto y no es un error: la incidencia estaba cerrada antes de que
    llegáramos nosotros.
    """

    PENDIENTE = "pendiente"
    DRY_RUN_OK = "dry_run_ok"
    CERRADO = "cerrado"
    ERROR = "error"
    YA_CERRADA = "ya_cerrada"


class EstadoGrafico(str, Enum):
    """En qué punto está el parte como gráfico de la reclamación (F-012).

    `ADJUNTADO` es **terminal**: una vez escrito, no se pisa (R30). Es la
    **primera capa de idempotencia** de la feature: un reintento del mismo
    parte se responde desde aquí, sin llamar a la pasarela ni mandar los bytes
    otra vez (R24).

    `YA_CERRADA` no es un error y no es del gráfico: es la reclamación que ya
    estaba cerrada antes de llegar nosotros, a la que **no se le adjunta nada**
    (R16). El gráfico es la primera mitad del cierre y no se deja en el ERP sin
    la segunda que lo justifica.
    """

    PENDIENTE = "pendiente"
    DRY_RUN_OK = "dry_run_ok"
    ADJUNTADO = "adjuntado"
    ERROR = "error"
    YA_CERRADA = "ya_cerrada"


class ResultadoGuardado(str, Enum):
    """Qué pasó al guardar: es la respuesta a «¿reprocesar duplicó algo?».

    `SIN_CAMBIOS` no es un fallo: es lo que devuelve intentar pisar un cierre
    ya terminal (R25). Que sea un valor propio y no un `False` es lo que
    permite distinguir «no había nada que hacer» de «no se pudo».
    """

    CREADO = "creado"
    ACTUALIZADO = "actualizado"
    SIN_CAMBIOS = "sin_cambios"


@dataclass(frozen=True)
class RegistroRemesa:
    """Una subida: qué llegó, cuándo y cuántos partes salieron de ella."""

    id: str
    nombre_origen: str
    recibida_at_utc: datetime
    num_partes: int
    avisos: tuple[str, ...] = ()
    #: **DATO PERSONAL seudónimo**: el `oid` opaco de Entra ID de quien sube
    #: la remesa. Queda `None` hasta F-007/F-010 (decisión D6 del humano del
    #: 2026-08-19). Nunca su correo ni su nombre.
    usuario_oid: str | None = None


@dataclass(frozen=True)
class TrazaArchivo:
    """Qué pasó al archivar el parte en SharePoint (F-006).

    Una sola por parte (R23): la clave es el `hash_parte`, así que subir dos
    veces el mismo parte no genera dos trazas.
    """

    hash_parte: str
    estado: EstadoArchivo
    nombre_fichero: str | None = None
    carpeta: str | None = None
    drive_id: str | None = None
    item_id: str | None = None
    web_url: str | None = None
    motivo: str | None = None
    archivado_at_utc: datetime | None = None


@dataclass(frozen=True)
class TrazaCierre:
    """Qué pasó al cerrar la incidencia en Sigrid (F-009).

    `estado_origen_sigrid` y `estado_destino_sigrid` guardan **el código que
    se resolvió en ejecución**, como traza de lo que se hizo. No es
    configuración y nadie los lee para decidir: `CHECKPOINTS.md` C3 prohíbe
    hardcodear un estado de Sigrid, y registrarlo a posteriori no lo hace.
    """

    hash_parte: str
    numero_incidencia: str
    estado: EstadoCierre
    estado_origen_sigrid: str | None = None
    estado_destino_sigrid: str | None = None
    #: **DATO PERSONAL seudónimo**: el `oid` de Entra de quien confirmó el
    #: cierre. Nunca su correo ni su nombre.
    confirmado_por: str | None = None
    motivo: str | None = None
    dry_run_at_utc: datetime | None = None
    cerrado_at_utc: datetime | None = None


@dataclass(frozen=True)
class TrazaGrafico:
    """Qué pasó al adjuntar el parte a la reclamación como gráfico (F-012).

    Una sola por parte: la clave es el `hash_parte`, así que subir dos veces el
    mismo parte no genera dos trazas.

    Guarda **identificadores y el `sha256`**, y ni un byte del PDF ni un campo
    manuscrito (R45): el documento vive en SharePoint y en Sigrid, y el disco
    del servidor es compartido.

    `sha256` y `hash_parte` son **dos cosas distintas** y aquí conviven a
    propósito (D-L): el segundo identifica el parte y es la clave de todas las
    trazas; el primero identifica **los bytes exactos** que se enviaron y es lo
    que la pasarela cotejó. Guardarlo es lo que permite explicar, meses
    después, qué fichero hay dentro del ERP.

    `reclamacion_ide` es el `con.ide` de la reclamación, guardado **desde el
    primer dry-run**: es la clave estable del ERP con la que se cruzan nuestras
    filas, mientras que `numero_incidencia` (`con.cod`) es legible pero no es
    clave.
    """

    hash_parte: str
    numero_incidencia: str
    estado: EstadoGrafico
    #: El `con.ide` de la reclamación en el ERP. Se rellena ya en el dry-run.
    reclamacion_ide: int | None = None
    #: El hash de **los bytes enviados**, no la huella de páginas del parte.
    sha256: str | None = None
    bytes: int | None = None
    nombre_fichero: str | None = None
    gratipide: int | None = None
    #: El `cod` que genera la pasarela. **Lleva el login del ERP dentro**
    #: (sello + 4 dígitos + `.login`) porque es el identificador del gráfico
    #: tal y como Sigrid lo produce, y es lo que hace falta para localizarlo.
    gra_cod: str | None = None
    gra_ide_negocio: int | None = None
    #: Puede quedar `None` en el caso idempotente: la respuesta no lo trae
    #: [MEDIDO]. No se inventa.
    gra_ide_documental: int | None = None
    rcg_ide: int | None = None
    idempotente: bool = False
    #: **DATO PERSONAL seudónimo**: el `oid` de Entra de quien confirmó. Nunca
    #: su correo, su nombre ni su login de Sigrid (R44).
    confirmado_por: str | None = None
    motivo: str | None = None
    dry_run_at_utc: datetime | None = None
    adjuntado_at_utc: datetime | None = None


@dataclass(frozen=True)
class PreferenciasUsuario:
    """Lo que un usuario ha decidido sobre el auto-cierre (F-010).

    Revocar es dejar `auto_cierre` en `False` con su marca de tiempo (R28): un
    booleano y una fecha bastan, y así no hay dos maneras de estar revocado.
    """

    #: **DATO PERSONAL seudónimo**: el `oid` opaco de Entra ID. Es la clave, y
    #: es lo único que se guarda del empleado.
    usuario_oid: str
    auto_cierre: bool
    actualizado_at_utc: datetime


@dataclass(frozen=True)
class EntradaCola:
    """Un parte esperando decisión humana, con las pruebas delante (R22).

    Trae la transcripción de las observaciones porque quien decide necesita
    leer lo que escribió el cliente. **No es una copia**: se recupera de la
    fila del parte con un `JOIN` (R21, R39), que es el único sitio donde ese
    texto vive.
    """

    hash_parte: str
    codigo_obra: str | None
    numero_incidencia: str | None
    #: **DATO PERSONAL directo**: texto manuscrito del cliente. Nunca al log
    #: (R29), nunca al repositorio (R38).
    observaciones: str | None
    confianza_observaciones: int
    clasificacion_firma: str
    motivos: tuple[tuple[str, str], ...]
    validado_at_utc: datetime
