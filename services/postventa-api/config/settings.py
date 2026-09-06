# services/postventa-api/config/settings.py
"""Configuración del servicio, leída del entorno (`.env` en local).

Una sola fuente de verdad para lo que el servicio necesita saber de fuera.
Nada de valores por defecto para los secretos: si falta una variable
obligatoria, el arranque **falla y lo dice**, en vez de arrancar a medias y
reventar más tarde contra un sistema real.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

#: Nombre con el que el servicio se identifica en logs y en `/health`.
NOMBRE_SERVICIO = "postventa-api"

#: Versión del servicio. Se sube a mano al cerrar una feature que cambie el
#: contrato de la API; no se genera del git porque el paquete desplegado no
#: lleva historial.
VERSION_SERVICIO = "0.1.0"


class Ajustes(BaseSettings):
    """Ajustes del servicio.

    Todos los campos declarados aquí sin valor por defecto son
    **obligatorios**: pydantic-settings falla al instanciar si no están en el
    entorno, con el nombre de la variable que falta.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    entorno: str = Field(
        description=(
            "Entorno de ejecución: local, dev o pro. Obligatoria a propósito: "
            "un valor por defecto haría que un despliegue mal configurado "
            "arrancara diciendo que es 'local'."
        ),
    )
    nivel_log: str = Field(
        default="INFO",
        description="Nivel de logging raíz del servicio.",
    )

    # --- Extracción con IA (F-003) y lectura de la firma (F-004) -------
    # Los nombres de las variables son los que ya usan `partes` y
    # `albaranes` en el ecosistema (`azure-apps`): mismo concepto, mismo
    # nombre, para que quien configure un despliegue no tenga que aprender
    # dos vocabularios.

    ia_proveedor: str = Field(
        default="gemini",
        validation_alias="IA_PROVIDER",
        description="Proveedor de IA. Los soportados los declara la fábrica.",
    )
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias="GEMINI_API_KEY",
        description=(
            "Credencial de Gemini. **Opcional a propósito**: si fuera "
            "obligatoria, `/health` dejaría de arrancar sin clave de IA y la "
            "suite entera necesitaría una credencial falsa en el entorno. "
            "Quien la exige es la fábrica, cuando de verdad hace falta. En "
            "Azure va por Key Vault; en local, en el `.env`, que no se "
            "versiona."
        ),
    )
    gemini_model: str = Field(
        default="gemini-3.7-flash",
        validation_alias="GEMINI_MODEL",
        description=(
            "Modelo multimodal de Gemini. Decisión del humano del 2026-08-18. "
            "Es configuración pura: el adaptador no depende de la versión."
        ),
    )
    ia_timeout_s: int = Field(
        default=120,
        validation_alias="IA_TIMEOUT_S",
        description=(
            "Segundos que se le conceden a una llamada. La Function corta a "
            "los 230 s: una llamada colgada no puede comérselos."
        ),
    )
    ia_reintentos: int = Field(
        default=3,
        validation_alias="IA_REINTENTOS",
        description="Intentos totales ante errores transitorios del proveedor.",
    )
    prompt_key: str = Field(
        default="parte_posventa_es",
        validation_alias="PROMPT_KEY",
        description="Clave del prompt de extracción dentro del YAML.",
    )
    prompt_key_firma: str = Field(
        default="firma_parte_es",
        validation_alias="PROMPT_KEY_FIRMA",
        description=(
            "Clave del prompt que clasifica la firma del cliente (F-004). Es "
            "una clave aparte porque la lectura de la firma se puede cambiar "
            "o reintentar sin rozar el prompt de extracción, cuya calidad se "
            "midió sobre 22 partes reales."
        ),
    )
    prompts_yaml: str = Field(
        default="config/prompts.yaml",
        validation_alias="PROMPTS_YAML_PATH",
        description=(
            "Fichero de prompts, relativo al directorio del servicio (no al "
            "`cwd`: la Function App arranca desde otro sitio)."
        ),
    )

    # --- Persistencia en PostgreSQL (F-005) ----------------------------
    # El servidor `psql-albaranes-rs9k2` es **compartido** con albaranes y
    # compañía. Los nombres de las variables son los que ya usa el
    # ecosistema, por lo mismo que arriba: un solo vocabulario para quien
    # despliega.
    #
    # Los tres campos sin valor por defecto (`pg_host`, `pg_usuario`,
    # `pg_password`) son **opcionales a propósito**, por el mismo motivo que
    # `gemini_api_key`: si fueran obligatorios, `/health` dejaría de arrancar
    # sin base de datos y la suite entera necesitaría credenciales falsas en
    # el entorno. Quien los exige es la fábrica, cuando de verdad hace falta.

    pg_host: str | None = Field(
        default=None,
        validation_alias="PG_HOST",
        description=(
            "Host del PostgreSQL. Opcional a propósito: sin él, `/health` "
            "sigue arrancando y quien lo exige es la fábrica."
        ),
    )
    pg_puerto: int = Field(
        default=5432,
        validation_alias="PG_PORT",
        description="Puerto del PostgreSQL.",
    )
    pg_base: str = Field(
        default="postventa",
        validation_alias="PG_DB",
        description=(
            "Base de datos **propia** del proyecto (decisión D1 del humano "
            "del 2026-08-19). La crea el humano una vez; la aplicación nunca."
        ),
    )
    pg_usuario: str | None = Field(
        default=None,
        validation_alias="PG_USER",
        description="Rol de acceso de la aplicación. Lo crea infraestructura.",
    )
    pg_password: str | None = Field(
        default=None,
        validation_alias="PG_PASSWORD",
        description=(
            "Contraseña del rol. **Secreto**, y opcional a propósito. En "
            "Azure va por referencia a Key Vault; en local, en el `.env`, que "
            "no se versiona. Jamás se escribe en un log ni en un DSN."
        ),
    )
    pg_esquema: str = Field(
        default="postventa",
        validation_alias="PG_SCHEMA",
        description=(
            "Esquema nominado dentro de la base. **No es `public`**: con el "
            "`search_path` fijado solo a este esquema, una sentencia sin "
            "cualificar no puede aterrizar donde no debe."
        ),
    )
    pg_sslmode: str = Field(
        default="require",
        validation_alias="PG_SSLMODE",
        description="Azure Database for PostgreSQL Flexible Server lo exige.",
    )
    pg_max_conexiones: int = Field(
        default=4,
        validation_alias="PG_MAX_CONEXIONES",
        description=(
            "Techo de conexiones del servicio. Bajo a propósito: el servidor "
            "es un `Standard_B1ms` compartido por varios proyectos y una "
            "Function App que escale podría comerse las suyas."
        ),
    )
    pg_statement_timeout_s: int = Field(
        default=30,
        validation_alias="PG_STATEMENT_TIMEOUT_S",
        description="Segundos que se le conceden a una sentencia.",
    )
    pg_lock_timeout_s: int = Field(
        default=5,
        validation_alias="PG_LOCK_TIMEOUT_S",
        description="Segundos esperando un bloqueo antes de rendirse.",
    )
    pg_idle_in_transaction_timeout_s: int = Field(
        default=60,
        validation_alias="PG_IDLE_IN_TRANSACTION_TIMEOUT_S",
        description=(
            "Segundos que puede quedarse una transacción abierta sin hacer "
            "nada antes de que el servidor la corte. Lo exige R9 y `design.md`"
            " §5 no le dio campo: se añade aquí porque una sesión colgada se "
            "queda en el servidor **de otros**. El valor por defecto está "
            "holgadamente por encima de `pg_statement_timeout_s`, para que "
            "nunca corte una transacción que solo está trabajando."
        ),
    )

    # --- Archivo en SharePoint por Microsoft Graph (F-006) -------------
    # Ninguna de estas variables tiene un valor por defecto que apunte a un
    # sitio real, y **ninguna se escribe en el repositorio**: el sitio, la
    # biblioteca, el tenant y la aplicación viajan por entorno. Es lo que hace
    # que F-013 —mudar el archivo a la biblioteca de Posventa— sea cambiar
    # tres variables y su documento, y no reescribir el adaptador.
    #
    # Los `str | None` son **opcionales en el modelo y obligatorios en la
    # fábrica**, exactamente como `GEMINI_API_KEY` (F-003) y `PG_HOST`
    # (F-005): si fueran obligatorios aquí, `/health` dejaría de arrancar sin
    # configuración de SharePoint y la suite entera necesitaría valores falsos
    # en el entorno. Quien los exige es `construir_archivador`, cuando de
    # verdad hacen falta.

    archivo_habilitado: bool = Field(
        default=False,
        validation_alias="ARCHIVO_HABILITADO",
        description=(
            "Interruptor maestro del archivo en SharePoint. **Falso por "
            "defecto a propósito**: el comportamiento por omisión —el de un "
            "`.env` recién copiado o el de un despliegue a medio configurar— "
            "es NO subir nada. Encenderlo es un gesto explícito."
        ),
    )
    sharepoint_site_id: str | None = Field(
        default=None,
        validation_alias="SHAREPOINT_SITE_ID",
        description=(
            "Sitio de SharePoint del destino. No lo usa el adaptador, que va "
            "directo a la biblioteca por su identificador; lo usan el script "
            "de verificación de infra y `docs/INTEGRACION.md`. Por eso no es "
            "obligatoria en la fábrica: exigir configuración que nadie lee es "
            "una vuelta más de despliegue a cambio de nada."
        ),
    )
    sharepoint_drive_id: str | None = Field(
        default=None,
        validation_alias="SHAREPOINT_DRIVE_ID",
        description=(
            "La biblioteca de documentos donde se archivan los partes. "
            "Obligatoria en la fábrica: es el destino."
        ),
    )
    sharepoint_carpeta_base: str = Field(
        default="Postventa",
        validation_alias="SHAREPOINT_CARPETA_BASE",
        description=(
            "Carpeta raíz dentro de la biblioteca. Debajo de ella cuelga una "
            "carpeta por código de obra."
        ),
    )
    graph_tenant_id: str | None = Field(
        default=None,
        validation_alias="GRAPH_TENANT_ID",
        description="Tenant de Entra ID contra el que se pide el token.",
    )
    graph_client_id: str | None = Field(
        default=None,
        validation_alias="GRAPH_CLIENT_ID",
        description="Aplicación (app registration) con la que se archiva.",
    )
    graph_client_secret: str | None = Field(
        default=None,
        validation_alias="GRAPH_CLIENT_SECRET",
        description=(
            "Credencial de la aplicación. **Secreto**: en Azure va por "
            "referencia a Key Vault; en local, solo en el `.env`, que no se "
            "versiona. Jamás se escribe en un log ni en un mensaje de error."
        ),
    )
    graph_timeout_s: int = Field(
        default=60,
        validation_alias="GRAPH_TIMEOUT_S",
        description=(
            "Segundos que se le conceden a una llamada a Graph. La Function "
            "corta a los 230 s: una llamada colgada no puede comérselos."
        ),
    )
    graph_reintentos: int = Field(
        default=3,
        validation_alias="GRAPH_REINTENTOS",
        description="Intentos totales ante errores transitorios de Graph.",
    )

    # --- Cierre de la incidencia en Sigrid (F-009) ---------------------
    # **Esto escribe en el ERP de producción.** Es la única parte de la
    # configuración del servicio que puede modificar un sistema ajeno del que
    # depende toda la empresa, y por eso su valor por omisión —el de un `.env`
    # recién copiado y el de un despliegue a medio configurar— es **no
    # escribir nada**.
    #
    # Los `str | None` son **opcionales en el modelo y obligatorios en la
    # fábrica**, exactamente como `GEMINI_API_KEY` (F-003), `PG_HOST` (F-005) y
    # las de Graph (F-006): si fueran obligatorios aquí, `/health` dejaría de
    # arrancar sin configuración de Sigrid y la suite entera necesitaría
    # valores falsos en el entorno. Quien los exige es `construir_erp`, cuando
    # de verdad hacen falta.

    cierre_habilitado: bool = Field(
        default=False,
        validation_alias="CIERRE_HABILITADO",
        description=(
            "Interruptor maestro del cierre en Sigrid. **Falso por defecto a "
            "propósito**, y con más motivo que el de SharePoint: lo que hay "
            "detrás es el ERP de producción y deshacer un cierre es otro "
            "proceso que alguien tiene que ejecutar a mano. Encenderlo es un "
            "gesto explícito, y se comprueba dos veces: en la fábrica y en el "
            "propio adaptador (R37)."
        ),
    )
    sigrid_api_base_url: str | None = Field(
        default=None,
        validation_alias="SIGRID_API_BASE_URL",
        description=(
            "Raíz de la pasarela `sigrid-api`, que es el **único** acceso al "
            "SQL Server de Sigrid en todo el ecosistema. Obligatoria en la "
            "fábrica: es el destino."
        ),
    )
    sigrid_api_key: str | None = Field(
        default=None,
        validation_alias="SIGRID_API_KEY",
        description=(
            "Clave de función de la pasarela. **Secreto**: en Azure va por "
            "referencia a Key Vault; en local, solo en el `.env`, que no se "
            "versiona. Jamás se escribe en un log, en una URL ni en un mensaje "
            "de error."
        ),
    )
    sigrid_base_datos: str | None = Field(
        default=None,
        validation_alias="SIGRID_BASE_DATOS",
        description=(
            "La base de negocio del ERP, que es la única con escritura "
            "permitida en la pasarela. Va por configuración y **nunca literal "
            "en el código**: el día que cambie, cambia una variable."
        ),
    )
    sigrid_timeout_s: int = Field(
        default=35,
        validation_alias="SIGRID_TIMEOUT_S",
        description=(
            "Segundos que se le conceden a una llamada a la pasarela. Cabe "
            "holgadamente en el presupuesto de 45 s de `ARCHITECTURE.md`, y el "
            "balanceador de la pasarela corta a los 230 s de todas formas."
        ),
    )
    sigrid_reintentos: int = Field(
        default=3,
        validation_alias="SIGRID_REINTENTOS",
        description=(
            "Intentos totales ante errores transitorios **de una lectura**. La "
            "escritura no se reintenta nunca (R27), y eso no es configurable a "
            "propósito: un tiempo agotado no dice que el ERP no haya escrito."
        ),
    )
    sigrid_tip_reclamacion: int = Field(
        default=708,
        validation_alias="SIGRID_TIP_RECLAMACION",
        description=(
            "El tipo de concepto de la reclamación de posventa en `dbo.con`. "
            "Es configuración de la instalación, igual que el número del "
            "estado, y por eso viaja como parámetro del SQL y no pegado al "
            "texto. Tiene valor por defecto porque está medido contra el ERP "
            "—21.554 filas de la extensión, todas de este tipo— y porque sin "
            "él la búsqueda no se podría acotar (R5)."
        ),
    )
    sigrid_zona_horaria: str = Field(
        default="Europe/Madrid",
        validation_alias="SIGRID_ZONA_HORARIA",
        description=(
            "Huso con el que se escriben `fec` y `hor` en la fila de auditoría "
            "del ERP (R24). Sigrid registra la **hora local**: escribir UTC "
            "dejaría nuestras filas de log con dos horas menos que todas las "
            "demás y nadie sabría por qué. La resuelve la fábrica, que falla "
            "si el nombre no existe en vez de suponer un huso."
        ),
    )

    # --- El parte como gráfico de la incidencia (F-012) -------------------
    #
    # **No hay interruptor nuevo**: el gráfico y el cierre son la MISMA ventana
    # de escritura, `CIERRE_HABILITADO`, porque son el mismo sistema, el mismo
    # dueño, la misma ventana y la misma decisión del humano (`design.md` D-B).
    # El gráfico es la primera mitad del cierre; un segundo interruptor solo
    # podría crear estados que no sirven para nada bueno.
    #
    # Estas dos **no son secretos** y por eso llevan valor por defecto: son
    # parámetros medidos, como `SIGRID_TIP_RECLAMACION`.

    sigrid_gratipide_parte: int = Field(
        default=35,
        validation_alias="SIGRID_GRATIPIDE_PARTE",
        description=(
            "La clase de gráfico con la que se adjunta el parte (`auxgra.ide`; "
            "35 = `PV002`, «POSTVENTA:Fotos Reparaciones»). Es configuración de "
            "la instalación, igual que el tipo de concepto y el número del "
            "estado, y por eso viaja como variable y no como literal en el "
            "código (R11). Tiene valor por defecto porque está medido: es la "
            "clase bajo la que Posventa tiene 3.197 gráficos llamados «PARTE "
            "FIRMADO». La pasarela mantiene además su propia lista blanca, así "
            "que cambiarlo aquí a secas no basta: es una decisión de dos "
            "dueños."
        ),
    )
    grafico_max_bytes: int = Field(
        default=10 * 1024 * 1024,
        validation_alias="GRAFICO_MAX_BYTES",
        description=(
            "Tope propio del PDF que se adjunta, comprobado **antes** de llamar "
            "a la pasarela (R18): mandar 13 MB por el proxy para que los "
            "rechacen al otro lado gasta el presupuesto de 45 s en un rechazo "
            "que ya se sabía. **No debe superar el de la pasarela** "
            "(`SIGRID_DOCUMENT_MAX_BYTES`, 10 MB): subirlo aquí solo compra un "
            "rechazo más tardío. Un parte firmado real ocupa 242.534 bytes, así "
            "que el margen es de unas 40 veces."
        ),
    )


@lru_cache(maxsize=1)
def obtener_ajustes() -> Ajustes:
    """Devuelve los ajustes del servicio, cacheados.

    Se cachea porque leer el entorno en cada petición no aporta nada: una
    Function App no cambia de configuración sin reiniciar.
    """
    return Ajustes()
