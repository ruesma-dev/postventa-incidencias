# services/postventa-api/domain/models/errores.py
"""Errores de dominio: de la ingesta de remesas (F-002), de la extracción
(F-003), de la validación (F-004), de la persistencia (F-005), del archivo
(F-006) y del cierre en Sigrid (F-009).

Los de la ingesta son los casos en los que algo de la entrada **no se puede
trocear**. Los dos que dejan la remesa entera sin resultado tienen su código
HTTP en el borde (`interface_adapters/api/split.py`); el tercero,
`PdfIlegible`, no llega tan lejos: lo captura el pipeline y se queda en un
aviso.

Los de la extracción se dividen en dos familias que conviene no confundir:
lo que falla **procesando un parte** (`ParteDemasiadoGrande`,
`ExtraccionFallida`) y lo que falla **al arrancar**, por configuración
(`PromptNoEncontrado`, `ProveedorNoSoportado`, `ConfiguracionIaIncompleta`).
Los segundos revientan al construir las piezas, no en mitad de una remesa de
veintidós partes.

Los de la validación siguen el mismo reparto: `SchemaDesconocido` es
configuración —un prompt que declara un schema que no existe— y revienta antes
de gastar una llamada; `ValidacionSinDatos` y `CuerpoDeValidacionInvalido` son
peticiones mal formadas y acaban en un 400.

Los de la persistencia cuelgan todos de `ErrorDePersistencia` para poder
capturarlos juntos, y dos de ellos son **guardarraíles de un servidor
compartido**: `DdlInseguro` y `DdlNoPermitidoAqui` se levantan antes de abrir
ninguna conexión, así que lo que prohíbe `CLAUDE.md` no llega ni a intentarse.

Los del cierre son los más caros de confundir, porque detrás hay el **ERP de
producción**, y se reparten en tres familias que el borde traduce a códigos
distintos a propósito: lo que está **mal pedido** (`CuerpoDeCierreInvalido` →
400), lo que **no se puede cerrar tal y como está** (`ParteNoApto`,
`ParteNoArchivado`, `ReclamacionNoLocalizada`, `EstadoDeCierreNoResoluble`,
`EstadoNoCerrable`, `UsuarioSigridNoMapeado`, `UsuarioSigridInexistente`,
`EstadoCambiadoDesdeElDryRun` → 409) y lo que dice que **aquí no se cierra**
(`CierreDeshabilitado`, `ConfiguracionSigridIncompleta` → 503). `CierreFallido`
es el único que habla del ERP (→ 502). **En todos ellos, sin haber escrito
nada.**

Y hay un duodécimo que se sale de las tres familias porque es el único en el
que **sí se escribió**: `CierreSinTraza` (→ 500), la incidencia cerrada en el
ERP cuya traza local no se pudo guardar. Es el hermano de `ArchivoSinTraza`, y
está aquí por la misma lección: si no tuviera nombre propio saldría como el 503
de «la base no responde», que promete que no se ha tocado nada.

Los del **gráfico** (F-012) repiten ese reparto sobre una escritura distinta
—el PDF del parte adjunto a la reclamación, tres filas en dos bases— y añaden
lo único que allí es nuevo: `CuerpoDeGraficoInvalido` (→ 400),
`GraficoDemasiadoGrande`, `GraficoNoEsPdf`, `ParteNoAdjuntado` y
`GraficoRechazadoPorLaPasarela` (→ 409), `EscrituraDocumentalDeshabilitada`
(→ 503, y es **configuración de otro proyecto**), `GraficoFallido` (→ 502, con
`reintento_seguro` dentro porque el endpoint es idempotente por contenido) y
`GraficoSinTraza` (→ 500, el único en el que el ERP **sí** está escrito). Las
puertas —`CierreDeshabilitado`, `ConfiguracionSigridIncompleta`— y los 409 de
F-009 se **reutilizan**: son la misma ventana y el mismo interruptor.

El de la **aprobación humana** (F-026) es uno solo, `ParteNoAprobable` (→ 409),
y cae del lado de «no se puede tal y como está»: la petición está bien formada
y lo que no admite la decisión es el estado del parte.

Los del **estado del parte** (F-028) son dos y repiten ese mismo reparto sobre
`POST /api/estado`: `ParteCerrado` (→ 409) es «la petición está bien y el parte
ya está cerrado en el ERP, que es un estado terminal», y
`CambioDeEstadoInvalido` (→ 400) es «el cuerpo no trae lo que dice el
contrato» —falta quién decide, falta la confirmación, el estado pedido no es
uno de los dos manuales o el rechazo viene sin motivo—. **En los dos, sin
haber escrito nada.**

El dominio no sabe de HTTP: quien traduce a 400 / 409 / 413 / 500 / 502 / 503
es el borde.
"""

from __future__ import annotations


class ErrorDeIngesta(Exception):
    """Raíz de los errores de la ingesta, para poder capturarlos juntos."""


class RemesaSinPdfUtilizable(ErrorDeIngesta):
    """La entrada no produjo ni un solo PDF que se pudiera abrir (R5).

    Lleva los avisos acumulados: quien recibe el error necesita saber **qué**
    se descartó y por qué, o el mensaje no sirve para corregir el envío.
    """

    def __init__(self, motivo: str, avisos: tuple[str, ...] = ()) -> None:
        super().__init__(motivo)
        self.motivo = motivo
        self.avisos = avisos


class PdfIlegible(ErrorDeIngesta):
    """Un PDF que no se puede abrir o no se puede leer: cifrado o corrupto.

    Vive en el dominio, y no junto al adaptador que lo levanta, porque quien
    lo captura es el pipeline (R4: un fichero roto no tumba una remesa de 22
    partes) y el pipeline no puede importar infraestructura.

    El nombre del fichero no entra aquí: quien abre el PDF solo tiene sus
    bytes, y es el pipeline —que sí sabe de qué fichero venían— el que compone
    el aviso.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class LimiteDeEntradaSuperado(ErrorDeIngesta):
    """La entrada se pasa de los límites declarados de la ingesta (R6).

    Se levanta **antes de descomprimir nada**, sobre los tamaños que declara
    el índice del comprimido: una bomba de descompresión no puede llegar a
    expandirse.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ParteDemasiadoGrande(Exception):
    """El parte no cabe en una petición en línea al modelo (F-003, R16).

    Se levanta **sin llamar al modelo**, y por eso el borde lo traduce a
    **413** y nunca a 502: no hay proveedor roto que reportar; hay una
    petición demasiado grande, y eso lo arregla quien la manda.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ExtraccionFallida(Exception):
    """El modelo no ha producido una respuesta utilizable (F-003, R15).

    Reintentos agotados, respuesta que no es JSON, o JSON que no es un
    mapping. El `motivo` dice **qué** pasó y **nunca** lleva el contenido del
    parte ni los valores leídos: el parte lleva DNI de clientes y este texto
    acaba en un log.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class SchemaDesconocido(Exception):
    """Un prompt declara un `schema` que el dominio no registra (F-004, R5).

    Es un fallo de **configuración**, no de un parte: alguien ha escrito en el
    YAML un nombre de schema que no existe en `CAMPOS_POR_SCHEMA`. Revienta
    **antes** de llamar al modelo, porque llamarlo con el schema equivocado
    devolvería campos que nadie sabe leer, y caro.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ValidacionSinDatos(Exception):
    """Se pide validar un parte sin extracción o sin lectura de firma (R21).

    Un veredicto inventado sobre datos que no están es peor que un error: se
    archivaría o se cerraría una incidencia sin haber mirado el parte. El
    borde lo traduce a **400**.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class CuerpoDeValidacionInvalido(Exception):
    """El cuerpo de `/api/validar` no trae lo que dice el contrato (R24).

    El motivo dice **qué falta** —y nunca lo que sí venía—: el cuerpo lleva
    los valores leídos del parte, con DNI incluido, y este texto acaba en un
    log.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class PeticionDePersistenciaInvalida(Exception):
    """La petición de un endpoint de F-019 no cumple su contrato (R4, R5, R10, R17).

    Es el hermano de `CuerpoDeValidacionInvalido` y `CuerpoDeArchivoInvalido`,
    y existe por lo mismo que ellos: el borde la traduce a **400** y nunca a
    503. La distinción importa más aquí que en ningún otro sitio, porque las
    tres cosas que se rechazan —un `num_partes` que no es un entero, un
    `remesa_id` que no es un UUID, un `limite` que no es un número— acabarían,
    si se dejaran pasar, en un error de PostgreSQL. Y un 503 «la base no
    responde» manda a mirar el servidor a quien tenía que corregir su
    petición.

    Cubre las tres formas que toma una petición en esta feature: el cuerpo de
    `POST /api/remesa`, las dos claves propias de `POST /api/parte` —el resto
    de ese cuerpo lo comprueban los parsers de `interface_adapters/api/cuerpos.py`,
    que levantan `CuerpoDeValidacionInvalido` porque es literalmente el cuerpo
    de `/api/validar`— y la cadena de consulta de `GET /api/cola`.

    **No cuelga de `ErrorDePersistencia`** a propósito: no es un fallo del
    almacén, es una petición mal escrita, y colgarla de ahí haría que el
    `except ErrorDePersistencia` de `paso_persistencia` se la tragara.

    El motivo dice **qué** está mal y nunca lo que sí venía: el cuerpo lleva
    los valores leídos del parte, con el DNI y las observaciones manuscritas
    dentro, y este texto acaba en un log que sobrevive al parte (R18).
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class PromptNoEncontrado(Exception):
    """El fichero de prompts no sirve, o no declara la clave pedida (R9).

    Falla al **construir** el repositorio o al pedir la clave, antes de gastar
    una sola llamada: llamar a un modelo con un prompt vacío produce basura
    cara y silenciosa.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ProveedorNoSoportado(Exception):
    """`IA_PROVIDER` nombra un proveedor que no existe (R12).

    El motivo lista los válidos: un error de configuración que no dice cuáles
    son las opciones obliga a leer el código para arreglarlo.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ConfiguracionIaIncompleta(Exception):
    """Falta configuración para construir el extractor (R12).

    El motivo nombra **la variable** que falta —`GEMINI_API_KEY`— y **jamás su
    valor**, ni entero ni en fragmentos: es una credencial.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ErrorDePersistencia(Exception):
    """Raíz de los errores de la persistencia (F-005).

    Existe para poder capturarlos juntos en el borde: quien compone el
    pipeline no necesita distinguir «el DDL es inseguro» de «falta el host»
    para decidir que la remesa no se puede guardar.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class DdlInseguro(ErrorDePersistencia):
    """Una sentencia del DDL se sale del esquema propio, o toca el servidor.

    Es el error más importante de F-005 y se levanta **antes de abrir
    ninguna conexión** (R5, R6). El servidor es compartido con la producción
    de otros proyectos: un `CREATE DATABASE`, un `GRANT` o una tabla sin
    cualificar no pueden llegar a intentarse.
    """


class DdlNoPermitidoAqui(ErrorDePersistencia):
    """Se ha intentado aplicar el DDL desde `local` contra un host remoto.

    No es lo mismo que `DdlInseguro`: el DDL puede ser impecable y aun así no
    ser este el sitio desde donde se aplica (R11). Escribir contra la base
    compartida desde el portátil de alguien es exactamente lo que `CLAUDE.md`
    reserva al entorno desplegado.
    """


class PersistenciaNoDisponible(ErrorDePersistencia):
    """No se ha podido hablar con la base de datos.

    El motivo dice **qué** falló y **jamás** el DSN ni la contraseña: estos
    mensajes acaban en un log.
    """


class ReferenciaNoConsta(ErrorDePersistencia):
    """Se ha intentado escribir una fila que apunta a otra que no existe (F-019).

    Es el error de una **clave ajena**, y tiene nombre propio porque el borde
    lo traduce a **409** y no a 503. La diferencia no es cosmética: un 503 dice
    «la base no responde, reintenta» y reintentar esto no lo arregla nunca; un
    409 dice **qué hacer** —guardar el parte, o registrar la remesa— y quien lo
    recibe puede hacerlo.

    Los dos casos que se dan hoy, y los dos son el mismo defecto 15 de F-010
    visto desde sitios distintos:

    - `archivos.hash_parte → partes.hash_parte`: se archiva un parte que nadie
      guardó. Esta es **la restricción en la que se apoya toda la garantía de
      orden de F-019**: la traza previa en `pendiente` sólo se puede escribir
      si el parte ya consta, así que la misma clave ajena que antes hacía
      fallar el proceso *después* de subir el fichero pasa a hacerlo fallar
      *antes*, sin haber tocado SharePoint.
    - `partes.remesa_id → remesas.id`: se guarda un parte de una remesa que no
      se registró.

    **No hereda de `PersistenciaNoDisponible`** a propósito: el borde ya
    captura esa otra y se lo tragaría, y volvería el 503 engañoso sin que
    ningún test lo notase.

    El motivo nombra **la operación** y jamás los parámetros: llevan el DNI y
    la transcripción de las observaciones manuscritas, y estos mensajes acaban
    en un log que sobrevive al parte (R18).
    """


class ConfiguracionPgIncompleta(ErrorDePersistencia):
    """Falta configuración para construir el repositorio (R30).

    El motivo nombra **las variables** que faltan —`PG_HOST`, `PG_USER`…— y
    nunca sus valores. Se exige en la fábrica y no al leer los ajustes, por lo
    mismo que `GEMINI_API_KEY`: `/health` tiene que arrancar sin base de datos.
    """


class NombradoImposible(Exception):
    """No se puede componer el nombre del fichero de un parte (F-006, R6, R7).

    Dos casos, y los dos acaban igual —el parte va a revisión manual— pero
    por motivos distintos: falta uno de los dos códigos, o el nombre que sale
    lleva algo que SharePoint no admite.

    Lo que **no** hace este error es dejar que el proceso siga. La alternativa
    —inventarse el dato que falta, o sustituir el carácter raro por `_`—
    archivaría en el archivo de Posventa un fichero con un nombre que nadie
    pidió, en una carpeta que se consulta a mano, y nadie se enteraría.

    En la práctica no debería llegar aquí ningún parte sin códigos: F-004 no
    los declara aptos. Por eso esto es una **red de seguridad**, no el camino
    normal.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ParteNoApto(Exception):
    """Se ha pedido archivar un parte que no está listo (F-006, R17, R18).

    Dos casos, y el motivo los distingue porque se arreglan de forma distinta:
    **no consta veredicto** —hay que revalidar el parte— o **el veredicto dice
    que no** —hay que volver al papel, o que alguien decida a mano—.

    Archivar «por si acaso» un parte que F-004 mandó a la cola de validación
    humana es exactamente lo que prohíbe `CHECKPOINTS.md` C3: alguien tenía que
    decidir sobre él y ya no va a poder.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ArchivoFallido(Exception):
    """El proveedor del archivo no ha respondido de forma utilizable (F-006).

    Reintentos agotados, error no transitorio, o respuesta que no trae lo que
    el contrato promete. El borde lo traduce a **502**: el fallo es de un
    sistema externo, no de quien mandó la petición.

    El `motivo` dice **qué** pasó y **nunca** los bytes del parte, ni el DNI,
    ni las observaciones manuscritas, ni el token, ni el secreto de cliente
    (R26): el parte lleva datos personales y este texto acaba en la base y en
    un log que sobrevive al parte.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ArchivoSinTraza(Exception):
    """El parte **está subido** y no ha quedado constancia (defecto 14, F-010).

    Es el único estado del archivo en el que la operación salió a medias: el
    PDF ya está en la biblioteca de Posventa —y ahí se queda: nadie lo borra
    para «dejarlo limpio»— pero la traza de F-005 no se ha podido escribir.

    Existe porque **el borde no puede deducirlo**. Cuando lo que sale del paso
    es un `PersistenciaNoDisponible` a secas, quien recibe la respuesta no
    tiene forma de saber si el fichero llegó a subirse, y las dos lecturas
    llevan a acciones opuestas: reintentar, o ir a mirar la carpeta. El único
    que conoce el orden es el paso, y por eso es él quien lo nombra.

    Lo levantó a la luz T18 el 2026-08-25: la clave ajena `archivos_hash_parte`
    rechazó la traza porque el parte no estaba en `partes` —eso es F-019—, y el
    llamante recibió un **500 con el cuerpo vacío**.

    El `motivo` reenvía el de la persistencia, que F-005 compone **sin DSN, sin
    contraseña y sin nada del parte** (R26, R29).
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ArchivoDeshabilitado(Exception):
    """Este sitio no puede archivar en SharePoint (F-006, R19, R20).

    Dos motivos, y los dos son **puertas a propósito**, no fallos:

    - el entorno no es `dev` ni `pro` —típicamente, es un puesto de trabajo—, y
      `CLAUDE.md` prohíbe sin matices subir al SharePoint de Posventa desde
      local;
    - `ARCHIVO_HABILITADO` no está encendido, que es el estado por defecto de
      un `.env` recién copiado y de un despliegue a medio configurar.

    El borde lo traduce a **503**: no es culpa de quien manda la petición ni
    del proveedor; es que aquí no se archiva.

    Se levanta en la fábrica **y en el constructor del adaptador**. No es
    redundancia decorativa: componer las piezas de otra manera —un script
    suelto, un `python -c`, un test «solo para probar»— tiene que toparse
    igual con la puerta, porque lo que se sube a SharePoint lo ve Posventa y
    no se puede deshacer.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ConfiguracionSharePointIncompleta(Exception):
    """Falta configuración para construir el archivador (F-006, R28).

    El motivo nombra **las variables** que faltan —`SHAREPOINT_DRIVE_ID`,
    `GRAPH_TENANT_ID`…— y **jamás sus valores**, ni enteros ni en fragmentos:
    `GRAPH_CLIENT_SECRET` es una credencial y estos mensajes acaban en un log.

    Se exige en la fábrica y no al leer los ajustes, por lo mismo que
    `GEMINI_API_KEY` y `PG_PASSWORD`: `/health` tiene que arrancar sin
    configuración de SharePoint y la suite entera tiene que correr sin
    credenciales en el entorno.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ParteNoArchivado(Exception):
    """Se ha pedido cerrar un parte que no consta archivado (F-009, R17).

    Es el hermano de `ParteNoApto` y existe porque son **dos precondiciones
    distintas del cierre**, y se arreglan de forma distinta: aquella se arregla
    revalidando o decidiendo a mano; esta, archivando el parte.

    R17 es el orden del procedimiento de Posventa, datado en F-008 §4.2:
    primero el documento, después el cierre. Si el PDF no está guardado en
    ninguna parte, cerrar la incidencia la da por resuelta sin dejar la prueba
    en ningún sitio — y eso es exactamente lo que sostiene el riesgo aceptado
    de `design.md` §2, que solo es asumible **porque el parte firmado existe**.

    El borde lo traduce a **409**: no es un fallo del ERP ni de la petición, es
    que este parte todavía no se puede cerrar.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ReclamacionNoLocalizada(Exception):
    """La búsqueda por código no devolvió **exactamente una** reclamación (R7).

    Cero o varias, y las dos acaban igual: **no se escribe nada**. El motivo
    dice cuántas se encontraron, porque cero («ese código no existe en el ERP»)
    y dos («el código no es único en ese tipo, algo va mal») se arreglan de
    formas opuestas.

    Que el código sea único está medido —23.063 de 23.063 dentro del tipo 708—,
    así que esto es una **red de seguridad**, no el camino normal. La búsqueda
    se acota siempre por el `tip` de la reclamación (R5): la unicidad se midió
    dentro del tipo, no en toda la tabla.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class EstadoDeCierreNoResoluble(Exception):
    """`conest` no resuelve el estado de cierre a una sola fila (F-009, R2).

    Es el error que protege `CHECKPOINTS.md` C3 por el otro lado: el número del
    estado no está en el código **a propósito**, así que si el ERP no lo dice —o
    lo dice dos veces— la respuesta no puede ser suponerlo. Se aborta sin
    escribir nada y se registra el motivo.

    El borde lo traduce a **409**: no se puede cerrar tal y como está el ERP.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class EstadoNoCerrable(Exception):
    """La reclamación está en un estado que no admite cierre automático (R19).

    El motivo **nombra el estado**, y no por cortesía: sin él, quien recibe el
    error no puede saber si lo que toca es esperar, revisar la reclamación o
    cerrarla a mano en el ERP.

    El caso que más importa es `NPR` (NO PROCEDE): alguien decidió que esa
    reclamación no procede, y cerrarla la daría por resuelta.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class UsuarioSigridNoMapeado(Exception):
    """No hay de dónde sacar el login de quien confirma el cierre (F-009, R30).

    No hay correspondencia guardada **y** tampoco hay un correo del que derivar
    un candidato. Sin login no se firma: `dbo.log.usu` lleva el login de la
    persona que ejecuta el proceso, nunca un usuario técnico ni un valor
    constante (R28, decisión D2 del humano).

    El borde lo traduce a **409**, y lo que hay que hacer es dar de alta la
    correspondencia con `infra/07_alta_usuario_sigrid.ps1` (R34).
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class UsuarioSigridInexistente(Exception):
    """El login candidato no existe **exactamente una vez** en el ERP (R31).

    Es la puerta que hace seguro apoyarse en un supuesto que la base no
    confirma: el correo **propone**, el ERP **dispone**. Aquí el ERP ha dicho
    que no, así que no se cierra y **no se escribe nada en Sigrid** (R32).

    El motivo nombra el correo del usuario y el login que se intentó, y eso
    **no choca con R45**: son dos destinos distintos. El mensaje va al usuario
    autenticado y le nombra **su propio** correo, que ya es suyo y lo tiene
    delante; el log lo lee cualquiera que abra Application Insights, y por eso
    este texto **no se registra tal cual** (R45).

    El borde lo traduce a **409**: hay que dar de alta la correspondencia a
    mano. Es el caso de los 2 de 8 usuarios medidos que no siguen la convención.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class EstadoCambiadoDesdeElDryRun(Exception):
    """La reclamación se movió entre el dry-run y la escritura (F-009, R11).

    **No se ha aplicado nada.** El cambio de estado lleva en su condición el
    estado de origen que se leyó en el dry-run, así que si alguien movió la
    reclamación entretanto no encuentra la fila; la de auditoría tampoco, que
    depende de que el cambio se hubiera aplicado, y el batch entero se va sin
    tocar el ERP.

    Existe porque **no se puede asumir que lo leído siga ahí**: F-008 §2.4
    encontró 81 filas `DESHACER proceso`, así que los cierres se deshacen y las
    reclamaciones se mueven.

    El borde lo traduce a **409**: hay que volver a mirar el dry-run.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class CierreFallido(Exception):
    """El ERP no ha respondido de forma utilizable al cerrar (F-009, R27, R50).

    Reintentos agotados, error no transitorio, o una respuesta que no trae lo
    que el contrato promete —el caso que más importa: un
    `total_affected_rows` que no es 2—.

    **El cierre no se reintenta solo** (R27). Reintentar una escritura contra un
    ERP de producción sin que nadie mire es cómo se cierran dos veces las cosas;
    el reintento lo pide una persona.

    El `motivo` dice **qué** pasó y **nunca** el cuerpo crudo de la respuesta,
    ni la clave de función, ni ningún dato del parte (R46, R50): estos mensajes
    acaban en la base y en un log que sobrevive al parte.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class CierreSinTraza(Exception):
    """La incidencia **está cerrada en el ERP** y no ha quedado constancia.

    Es el único estado del cierre en el que la operación salió a medias: el
    cambio de estado y la fila de auditoría **ya están escritos en
    producción** —y ahí se quedan: nadie los deshace «para dejarlo limpio»,
    deshacer un cierre en Sigrid es otro proceso que ejecuta una persona— pero
    la traza de F-005 no se ha podido guardar.

    Es el hermano exacto de `ArchivoSinTraza`, y existe por lo mismo: **el
    borde no puede deducirlo**. Cuando lo que sale del paso es un
    `PersistenciaNoDisponible` a secas, el borde responde 503 diciendo «no se
    ha cerrado nada en el ERP, se puede reintentar» — y eso sería **mentira**,
    con la incidencia ya cerrada. Reintentar entonces no arregla nada: como
    mucho da `ya_cerrada`, y como poco confunde a quien mire.

    La lección no es nueva en este repositorio: es el **defecto 14 de F-010**,
    que en el archivo costó media hora de Application Insights leer algo que el
    servicio ya sabía. `design.md` no lo previó para el cierre; se aplica aquí
    el mismo patrón, con el mismo motivo y con más razón, porque lo que queda a
    medias es una escritura en el ERP y no un fichero.

    El `motivo` reenvía el de la persistencia, que F-005 compone **sin DSN, sin
    contraseña y sin nada del parte**.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class CierreDeshabilitado(Exception):
    """Aquí no se escribe en Sigrid (F-009, R36, R37).

    Dos motivos, y los dos son **puertas a propósito**, no fallos:

    - el entorno no es `dev` ni `pro` —típicamente, es un puesto de trabajo—, y
      `CLAUDE.md` prohíbe sin matices escribir en Sigrid desde local;
    - `CIERRE_HABILITADO` no está encendido, que es el estado por defecto de un
      `.env` recién copiado y de un despliegue a medio configurar.

    Se levanta en la fábrica **y en el constructor del adaptador** (R37). No es
    redundancia decorativa: componer las piezas de otra manera —un script
    suelto, un `python -c`, un test «solo para probar»— tiene que toparse igual
    con la puerta, porque un cierre en el ERP lo ve Posventa y deshacerlo es
    otro proceso que alguien tiene que ejecutar a mano.

    El borde lo traduce a **503**: no es culpa de quien manda la petición ni
    del ERP; es que aquí no se cierra.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ConfiguracionSigridIncompleta(Exception):
    """Falta configuración para hablar con `sigrid-api` (F-009, R38).

    El motivo nombra **todas** las variables que faltan de una vez
    —descubrirlas de una en una son tres vueltas de despliegue— y **jamás sus
    valores**, ni enteros ni en fragmentos: `SIGRID_API_KEY` es una credencial y
    estos mensajes acaban en un log.

    Se exige en la fábrica y no al leer los ajustes, por lo mismo que
    `GEMINI_API_KEY`, `PG_PASSWORD` y `GRAPH_CLIENT_SECRET`: `/health` tiene que
    arrancar sin configuración de Sigrid y la suite entera tiene que correr sin
    credenciales en el entorno.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class CuerpoDeCierreInvalido(Exception):
    """El cuerpo de `/api/cerrar` no trae lo que dice el contrato (F-009, R47).

    Falta un campo, o el veredicto o el destino traen un valor que el dominio
    no reconoce. El borde lo traduce a **400**, y no a 409: la petición está
    mal formada, no es que la incidencia no se pueda cerrar.

    Esa distinción no es cosmética, y aquí menos que en ningún otro sitio: un
    veredicto desconocido tratado «como si fuera no apto» daría un 409
    engañoso; tratado al revés —«como si fuera apto»— **cerraría en el ERP de
    producción una incidencia que nadie ha validado**. Se rechaza y punto.

    El motivo dice **qué falta** y nunca lo que sí venía: el cuerpo lleva los
    códigos del parte y el correo de quien confirma, y este texto acaba en un
    log (R45).
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class CuerpoDeArchivoInvalido(Exception):
    """El cuerpo de `/api/archivar` no trae lo que dice el contrato (F-006, R31).

    Falta un campo, o el veredicto o el destino traen un valor que el dominio
    no reconoce. El borde lo traduce a **400**, y no a 409: la petición está
    mal formada, no es que el parte no se pueda archivar.

    Esa distinción no es cosmética. Un veredicto desconocido tratado «como si
    fuera no apto» daría un 409 engañoso; tratado al revés —«como si fuera
    apto»— archivaría un parte que nadie ha validado. Se rechaza y punto.

    El motivo dice **qué falta** y nunca lo que sí venía: el cuerpo lleva los
    códigos del parte y este texto acaba en un log.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class CuerpoDeGraficoInvalido(Exception):
    """La petición de `/api/adjuntar` no trae lo que dice el contrato (F-012, R58).

    Falta un campo, el veredicto o el destino traen un valor que el dominio no
    reconoce, o lo que se compondría **no cabe en el ERP**: el nombre pasa de
    255, la descripción de 48 o el login de 24. El borde lo traduce a **400**,
    y no a 409: la petición está mal formada, no es que el gráfico no se pueda
    adjuntar.

    Lo que no cabe **no se trunca**, y por eso es un error y no un saneo: un
    nombre truncado deja de cruzar con el fichero de SharePoint, y un login
    truncado es otro login — firmaría el gráfico a nombre de nadie.

    El motivo dice **qué** está mal y nunca lo que sí venía: por esta petición
    pasa el PDF del parte con el DNI manuscrito dentro, y este texto acaba en
    un log (R53).
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class GraficoDemasiadoGrande(Exception):
    """El PDF pasa de `GRAFICO_MAX_BYTES` (F-012, R18).

    Se levanta **antes de llamar a la pasarela**: mandar 13 MB codificados por
    el proxy para que los rechacen al otro lado gasta el presupuesto de 45 s en
    un 409 que ya se sabía. El borde lo traduce a **409**.

    El motivo dice **cuánto ocupa y cuál es el tope**, que son los dos números
    sin los cuales quien lo recibe no sabe qué corregir. El tope propio no debe
    superar el de la pasarela: subirlo aquí solo compra un rechazo más tardío.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class GraficoNoEsPdf(Exception):
    """Los bytes no empiezan por `%PDF-` (F-012, R19).

    Igual que el anterior, **antes** de llamar a la pasarela, que solo admite
    lo que esté en su `SIGRID_DOCUMENT_ALLOWED_MAGIC`. El borde lo traduce a
    **409**.

    El motivo **no lleva ni un byte del fichero**: si no es un PDF puede ser
    cualquier cosa, y volcar su principio en un log es volcar contenido
    desconocido de un cliente (R53).
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ParteNoAdjuntado(Exception):
    """Se pide cerrar una incidencia cuyo parte no consta adjuntado (F-012, R2).

    Es la **precondición nueva del cierre**, simétrica a la de archivo
    (`ParteNoArchivado`): con F-012 el gráfico va **antes** del cambio de
    estado, así que ninguna reclamación puede quedar cerrada sin su parte
    dentro de Sigrid.

    Se comprueba contra **nuestra** traza (`postventa.graficos`) y nunca
    consultando `rcg` ni `gra` del ERP: R20 de F-009 sigue vigente y el cierre
    sigue sin saber qué es un gráfico. El borde lo traduce a **409**, y **sin
    haber tocado el ERP** (R62).
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class GraficoRechazadoPorLaPasarela(Exception):
    """La pasarela rechaza la petición del gráfico, sin escribir nada (F-012, R33).

    Lleva el `codigo` de `details.codigo`, que es una **lista cerrada** de doce
    valores (`azure-apps/sigrid_api.md` §8.8): el concepto no existe, el tipo
    no coincide, la clase no está permitida, el login no vale, el fichero está
    vacío, no es del tipo permitido o pasa del tope de la pasarela.

    Del cuerpo de la respuesta **solo se toma ese código** y se descarta el
    resto (R35): detrás hay un SQL Server de producción con datos de clientes,
    y lo que la pasarela cuente de un error no puede acabar en un log.

    El borde lo traduce a **409**. En todos estos casos el ERP quedó intacto:
    la pasarela los levanta antes del `COMMIT` o dentro de la transacción, que
    revierte.
    """

    def __init__(self, motivo: str, *, codigo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo
        self.codigo = codigo


class EscrituraDocumentalDeshabilitada(Exception):
    """Falta una precondición del dueño de `sigrid-api` (F-012, R32).

    Dos códigos: `escritura_documental_deshabilitada` (la pasarela tiene
    cerrada su base documental, o no la tiene configurada) y
    `base_de_datos_no_permitida` (nuestra `SIGRID_BASE_DATOS` no está en su
    lista blanca).

    **No es un fallo de esta feature ni de quien llama**: es configuración de
    **otro proyecto**, declarada como precondición (H4 de `design.md`) y
    documentada en `docs/INTEGRACION.md` §6 como «qué se rompe si el dueño la
    cambia». Por eso el borde lo traduce a **503** y no a 409: no hay nada que
    corregir en la petición, y aquí y ahora no se adjunta.

    Lleva el `codigo` para poder nombrarlo en el mensaje: sin él, quien lo
    reciba no sabe **cuál** de las dos precondiciones pedirle a su dueño.
    """

    def __init__(self, motivo: str, *, codigo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo
        self.codigo = codigo


class GraficoFallido(Exception):
    """No se ha podido adjuntar el gráfico (F-012, R28, R29, R31, R34).

    Es el hermano de `CierreFallido`, con **una diferencia que importa y que
    va en el propio objeto**: `reintento_seguro`. El endpoint de la pasarela es
    **idempotente por tamaño y `sha256`**, así que volver a pedirlo no duplica
    el gráfico — ni siquiera cuando el fallo fue un tiempo agotado y no se sabe
    si el ERP llegó a escribir.

    Eso lo distingue de F-009, donde el reintento lo decide una persona después
    de mirar el ERP. Aquí el motivo **dice** que el reintento es seguro, porque
    quien lo lee tiene que poder actuar sin abrir Sigrid.

    El borde lo traduce a **502**. El motivo va **acotado**: nunca el cuerpo
    crudo de la respuesta, ni la URL de la pasarela, ni la clave de función
    (R35, R55).
    """

    def __init__(self, motivo: str, *, reintento_seguro: bool = True) -> None:
        super().__init__(motivo)
        self.motivo = motivo
        self.reintento_seguro = reintento_seguro


class GraficoSinTraza(Exception):
    """El gráfico **está en el ERP** y no ha quedado constancia (F-012, R47).

    Es el hermano exacto de `CierreSinTraza` y de `ArchivoSinTraza`, y existe
    por lo mismo: **el borde no puede deducirlo**. Un `PersistenciaNoDisponible`
    a secas saldría como 503 diciendo «no se ha escrito nada, reintenta», y eso
    sería mentira con las tres filas ya dentro de Sigrid.

    La diferencia con sus hermanos es cómo se arregla: aquí el reintento **sí**
    es inofensivo —la pasarela responderá `idempotente: true` y no escribirá
    nada—, lo que falta es la traza local. El borde lo traduce a **500**.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ParteNoAprobable(Exception):
    """Se ha pedido aprobar un parte que no se puede aprobar (F-026, R9, R10).

    Dos casos, y el motivo los distingue porque se arreglan de forma distinta:

    - **le falta un dato decisivo** —el código de obra o el nº de incidencia—:
      ahí no hay nada que decidir, hay algo que teclear, y teclearlo devuelve
      el parte a verde por las reglas de F-004 sin aprobar nada (R7);
    - **ya es apto**: no hay nada que aprobar (R10).

    El borde lo traduce a **409 y nunca a 400**, y la distinción no es
    cosmética: la petición está perfectamente formada —trae su `usuario_oid`,
    su confirmación y su parte—, lo que pasa es que **el estado del parte no
    admite esa decisión**. Un 400 mandaría a revisar el cuerpo a quien tiene
    que ir a corregir un campo del papel. Es el mismo reparto que ya hacen
    `ParteNoApto` y `ParteNoArchivado`.

    El motivo dice **cuál** lo impide y qué hay que corregir (R9), y **nunca**
    lleva el texto de las observaciones ni ningún otro dato del papel: esto
    acaba en un log (R43).
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ParteCerrado(Exception):
    """Se ha pedido cambiar el estado de un parte ya cerrado (F-028, R7).

    `cerrado` es **terminal** y de ahí no sale ninguna flecha (D5). Lo escrito
    en Sigrid y en SharePoint no se deshace desde aquí, y cambiar el estado
    solo conseguiría que nuestra base dijera algo distinto del ERP: la
    incidencia seguiría cerrada y el parte figuraría como rechazado.

    El borde lo traduce a **409 y nunca a 400**, con el mismo reparto que
    `ParteNoApto` y `ParteNoAprobable`: la petición está perfectamente formada
    —trae su `usuario_oid`, su confirmación y su motivo—, y lo que no admite
    la decisión es **el estado del parte**. Un 400 mandaría a revisar el
    cuerpo a quien no tiene nada que revisar.

    En la pantalla no llega a levantarse casi nunca, porque la web ya no
    ofrece ningún gesto sobre un parte cerrado y lo **explica** en vez de
    fallar (R41). Esto es la puerta de atrás: quien llame al endpoint
    directamente se lleva el 409.

    Si alguna vez apareciera la necesidad de **deshacer** un cierre, no se
    implementa aquí: es escritura de reversión en el ERP de producción, la
    decide el dueño del proceso y se marcaría `blocked` según `CLAUDE.md`.

    El motivo dice **por qué** no se puede y **nunca** lleva el `oid` de quien
    decidió, el motivo que escribió ni ningún dato del papel: esto acaba en un
    log (R52, R53).
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class CambioDeEstadoInvalido(Exception):
    """El cuerpo de `POST /api/estado` no trae lo que dice el contrato (F-028).

    Los casos, y todos se arreglan en el cuerpo de la petición (R31): falta
    **quién decide** (R14), falta la confirmación explícita o no es el booleano
    de JSON (R29), el `estado` pedido **no es uno de los dos manuales** —a
    `pendiente` no se vuelve a mano y a `cerrado` solo se llega cerrando la
    incidencia (R10)—, el rechazo viene **sin motivo** (R11) o el motivo pasa
    de `LIMITE_MOTIVO` (R13).

    El borde lo traduce a **400**, y no a 409: la petición está mal formada,
    no es que el parte no admita la decisión. La distinción no es cosmética,
    y es la misma que ya escribió `CuerpoDeArchivoInvalido`: un estado
    desconocido tratado «como si fuera rechazado» dejaría un parte fuera de la
    tanda sin que nadie lo hubiera decidido; tratado al revés, lo metería. Se
    rechaza y punto.

    **Sin haber escrito nada**, que es la otra mitad del requisito: un cuerpo
    mal formado no puede dejar media fila en el histórico.

    El motivo dice **qué** falta y nunca lo que sí venía: por aquí pasan el
    `oid` de quien decide y el texto que escribió, y esto acaba en un log
    (R52, R53).
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo
