# services/postventa-api/interface_adapters/api/adjuntar.py
"""Handler de `POST /api/adjuntar`, sin nada de Azure dentro.

Aquí se **componen los cinco puertos** —el ERP, el del gráfico, el repositorio
de partes, el de correspondencias y el de preferencias— y se serializa el
resultado, como manda `docs/CONVENTIONS.md`: la composición vive en el punto de
entrada y nunca dentro de un paso.

Los cinco puertos inyectables son **la costura de test del endpoint**: con
ellos, la suite prueba el borde entero sin que Sigrid aparezca por ninguna
parte. Sin ellos, el handler construye lo de verdad, y es ahí —y solo ahí—
donde se topa con la puerta de entorno. Por eso, llamado desde un puesto de
trabajo, este endpoint responde **503 y no toca el ERP**.

## Por qué es `multipart` y no JSON

Porque lo que se adjunta **son los bytes del parte** (D-H), y el front ya los
tiene: los conserva desde `/api/split` y ya compone el `File` para archivar. Es
exactamente el mismo objeto que mandó a `/api/archivar`, y eso es lo que hace
que en Sigrid acabe el mismo documento que hay en SharePoint.

**Descartado: que el backend descargue el PDF de SharePoint.** Garantizaría
byte a byte esa igualdad, pero exige un método de descarga nuevo en
`ArchivoPort`, encadena dos proveedores externos en la misma petición y gasta
el presupuesto de 45 s dos veces. El nivel de confianza es el de F-006, ni más
ni menos, y se dice.

## El dry-run es lo que se hace por omisión

`commit` vale `false` si no viene, y eso no es comodidad: quien llame a este
endpoint sin haber leído el contrato **no escribe nada en el ERP de
producción**. Escribir exige además `confirmado` o el auto-cierre guardado
(R23), y una **sola** confirmación cubre el gráfico y el cierre.

Y como el cuerpo es un formulario y no JSON, `commit` y `confirmado` llegan
como texto: solo cuenta **exactamente** la cadena `true`. Cualquier otra cosa
—`"false"`, `"1"`, `"si"`— es no. En Python `"false"` es verdadero, y ahí
está el fallo que esto impide.

## El veredicto ya no llega en el cuerpo: se lee de donde está guardado

**Enmienda del 2026-09-16 (F-030).** Hasta hoy este endpoint reconstruía un
`ResultadoValidacion` con el `veredicto` y el `destino` del formulario y
valores fijos para todo lo demás, y la puerta del paso derivaba el estado de
**ese** objeto. Como la huella recomputada sobre él no dependía del parte, la
decisión de una persona sobre ese parte no contaba nunca; y al revés, un
cuerpo que dijera
`veredicto=apto` pasaba la puerta sin que nadie hubiera mirado el parte.

Desde F-030 el contexto sale de aquí **sin veredicto** y la puerta lo lee de
`postventa.validaciones`, dentro de la consulta de situación que ya hacía
(`F-030 design.md` §5.4). El porqué largo está en `archivar.py`, que es donde
F-006 dejó anotada la decisión D4 que esta feature paga.

`veredicto` y `destino` **siguen siendo obligatorios en el cuerpo y siguen
validándose** contra las enumeraciones de F-004: el contrato HTTP no cambia y
un valor desconocido sigue siendo un 400 (R19, D6 de F-030). Lo que ya no
hacen es decidir nada.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_grafico import paso_grafico
from config.settings import obtener_ajustes
from domain.models.errores import CuerpoDeGraficoInvalido
from domain.models.grafico import ResultadoGrafico
from domain.models.persistencia import EstadoArchivo, TrazaArchivo
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import Destino, Veredicto
from domain.ports.erp import ErpPort
from domain.ports.grafico import GraficoPort
from domain.ports.persistencia import (
    RepositorioPartesPort,
    RepositorioPreferenciasPort,
)
from domain.ports.usuarios_sigrid import RepositorioUsuariosSigridPort
from infrastructure.persistencia.fabrica import construir_repositorio
from infrastructure.sigrid.fabrica import construir_erp, construir_graficos

__all__ = ["CAMPOS_OBLIGATORIOS", "adjuntar_grafico"]

#: Lo que el formulario tiene que traer, además del fichero.
#:
#: `commit` y `confirmado` **no** están: son opcionales y su valor por omisión
#: —no escribir— es el seguro. `correo` tampoco: solo hace falta cuando hay que
#: derivar un candidato de login, y quien ya tiene correspondencia confirmada
#: no lo necesita.
CAMPOS_OBLIGATORIOS = (
    "hash",
    "codigo_obra",
    "numero_incidencia",
    "veredicto",
    "destino",
    "estado_archivo",
    "usuario_oid",
)


def adjuntar_grafico(
    contenido: bytes,
    *,
    hash: str = "",
    codigo_obra: str = "",
    numero_incidencia: str = "",
    veredicto: str = "",
    destino: str = "",
    estado_archivo: str = "",
    usuario_oid: str = "",
    correo: str = "",
    commit: str | bool = False,
    confirmado: str | bool = False,
    erp: ErpPort | None = None,
    graficos: GraficoPort | None = None,
    repositorio: RepositorioPartesPort | None = None,
    usuarios: RepositorioUsuariosSigridPort | None = None,
    preferencias: RepositorioPreferenciasPort | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]:
    """Adjunta **un** parte a su reclamación, o dice qué se adjuntaría.

    Levanta `CuerpoDeGraficoInvalido` y `CuerpoDeCierreInvalido` (→ 400),
    `ParteNoApto`, `ParteNoArchivado`, `NombradoImposible`,
    `GraficoDemasiadoGrande`, `GraficoNoEsPdf`, `ReclamacionNoLocalizada`,
    `EstadoNoCerrable`, `UsuarioSigridNoMapeado`, `UsuarioSigridInexistente`,
    `GraficoRechazadoPorLaPasarela` y `ReferenciaNoConsta` (→ 409),
    `CierreDeshabilitado`, `ConfiguracionSigridIncompleta`,
    `EscrituraDocumentalDeshabilitada`, `ConfiguracionPgIncompleta` y
    `PersistenciaNoDisponible` (→ 503), `GraficoFallido` (→ 502) y
    `GraficoSinTraza` (→ 500) **sin traducirlas**: convertir eso en códigos
    HTTP es trabajo del borde.

    **En casi todos esos casos, sin haber escrito nada en el ERP.** Los dos que
    no lo garantizan lo dicen en su mensaje:

    - `GraficoFallido`, si la escritura llegó a salir y no volvió la respuesta.
      Y a diferencia de F-009, **el reintento es seguro**: el endpoint es
      idempotente por tamaño y `sha256`.
    - `GraficoSinTraza`, que es el único en el que el gráfico **sí está** en el
      ERP y lo que falta es la traza local.
    """
    _exigir_cuerpo(
        contenido,
        hash=hash,
        codigo_obra=codigo_obra,
        numero_incidencia=numero_incidencia,
        veredicto=veredicto,
        destino=destino,
        estado_archivo=estado_archivo,
        usuario_oid=usuario_oid,
    )
    ajustes = obtener_ajustes()

    contexto = paso_grafico(
        _como_contexto(
            contenido,
            hash_parte=hash,
            estado_archivo=estado_archivo,
        ),
        erp if erp is not None else construir_erp(ajustes),
        graficos if graficos is not None else construir_graficos(ajustes),
        repositorio if repositorio is not None else construir_repositorio(ajustes),
        usuarios if usuarios is not None else construir_repositorio(ajustes),
        preferencias if preferencias is not None else construir_repositorio(ajustes),
        commit=_bandera(commit),
        confirmado=_bandera(confirmado),
        usuario_oid=usuario_oid.strip(),
        correo=correo.strip(),
        numero_incidencia=numero_incidencia,
        codigo_obra=codigo_obra,
        gratipide=ajustes.sigrid_gratipide_parte,
        tope_bytes=ajustes.grafico_max_bytes,
        ahora=ahora if ahora is not None else datetime.now(UTC),
    )
    return _serializar(contexto)


def _exigir_cuerpo(contenido: bytes, **campos: str) -> None:
    """El formulario, comprobado; o el 400 diciendo **qué** le falta (R58).

    El **fichero entra en la comprobación** y no se trata aparte: es el campo
    que más veces se olvida al llamar a mano, y un mensaje que enumera seis
    campos y calla el séptimo manda a buscar donde no es.

    Los tres valores de enumeración se comprueban contra el dominio, y eso
    **no es cosmético**: un veredicto que no existe, tratado «como si fuera no
    apto», daría un 409 engañoso; tratado al revés —«como si fuera apto»—
    subiría al ERP de producción el parte de una incidencia que nadie ha
    validado.

    El motivo dice qué falta y **nunca** lo que sí venía: por esta petición
    pasa el PDF con el DNI manuscrito dentro, y este texto acaba en un log
    (R53).
    """
    faltan = [nombre for nombre, valor in campos.items() if not (valor or "").strip()]
    if not contenido:
        faltan.append("fichero")
    if faltan:
        raise CuerpoDeGraficoInvalido(
            f"la petición no trae: {', '.join(sorted(faltan))}"
        )

    _exigir_valor_conocido(Veredicto, campos["veredicto"], "veredicto")
    _exigir_valor_conocido(Destino, campos["destino"], "destino")
    _exigir_valor_conocido(EstadoArchivo, campos["estado_archivo"], "estado_archivo")


def _exigir_valor_conocido(enumeracion, valor: str, nombre: str) -> None:
    """El valor tiene que ser uno de los que declara el dominio."""
    admitidos = [miembro.value for miembro in enumeracion]
    if valor not in admitidos:
        raise CuerpoDeGraficoInvalido(
            f"'{nombre}' no es uno de los valores admitidos "
            f"({', '.join(admitidos)})"
        )


def _bandera(valor: Any) -> bool:
    """Una bandera del formulario, y **solo** la cadena `true` cuenta.

    En un `multipart` todo llega como texto, y en Python `"false"` es
    verdadero: sin esta comparación, mandar `commit=false` escribiría en el ERP
    de producción. Se admite también el `True` de Python para poder llamar al
    handler desde un test sin fabricar cadenas.
    """
    if valor is True:
        return True
    return isinstance(valor, str) and valor.strip() == "true"


def _como_contexto(
    contenido: bytes,
    *,
    hash_parte: str,
    estado_archivo: str,
) -> ContextoParte:
    """Reconstruye el contexto mínimo que necesita el paso del gráfico.

    El estado del archivo llega en el formulario y **se vuelve a comprobar**
    dentro del paso, exactamente igual que si viniera de dentro. El
    **veredicto ya no**: se va sin rellenar y lo lee la puerta del paso, de la
    base, porque este endpoint no recibe la extracción y no puede emitirlo
    (F-030; la enmienda está arriba y el porqué largo en `archivar.py`).

    De la extracción **no se reconstruye nada**: el paso no la necesita —la
    obra y la incidencia llegan aparte— y pedirla obligaría al front a
    reenviar el DNI y las observaciones manuscritas del cliente en cada
    llamada, que es justo el dato que no debe viajar de más.
    """
    return ContextoParte(
        parte=ParteTroceado(
            hash=hash_parte.strip(),
            origen="",
            paginas_origen=(),
            modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
            contenido=contenido,
        ),
        validacion=None,
        archivo=TrazaArchivo(
            hash_parte=hash_parte.strip(),
            estado=EstadoArchivo(estado_archivo),
        ),
    )


def _serializar(contexto: ContextoParte) -> dict[str, Any]:
    """Pasa el resultado a JSON. **Ni una clave más que las de R56.**

    Ni los bytes del PDF, ni su texto codificado, ni ningún campo manuscrito,
    ni la configuración del destino —la raíz de la pasarela, la base, la
    clave—, ni el `oid` de quien confirma. Esta respuesta la recibe un
    navegador, y de ahí a una captura de pantalla en un correo hay un paso.

    Lo que **sí** lleva es el dry-run entero (R21): sin él, quien tiene que
    confirmar estaría confirmando a ciegas.
    """
    resultado = contexto.grafico
    return {
        "hash_parte": contexto.parte.hash,
        "numero_incidencia": _incidencia(resultado),
        "estado": resultado.estado.value,
        "idempotente": _idempotente(resultado),
        "filas_afectadas": (
            resultado.respuesta.filas_afectadas
            if resultado.respuesta is not None
            else 0
        ),
        "motivo": resultado.motivo,
        "dry_run": _dry_run(resultado),
        "avisos": list(contexto.avisos),
    }


def _incidencia(resultado: ResultadoGrafico) -> str | None:
    """El código de la reclamación, venga del plan o de la traza.

    Los dos caminos existen: el normal deja plan, y el de R24 —ya adjuntado
    según la traza local— no llega a leer ninguna reclamación y solo tiene la
    traza. Quien recibe la respuesta necesita el código en los dos.
    """
    if resultado.plan is not None:
        return resultado.plan.reclamacion.codigo
    if resultado.traza is not None:
        return resultado.traza.numero_incidencia
    return None


def _idempotente(resultado: ResultadoGrafico) -> bool:
    """¿La pasarela dijo que el documento ya estaba? (R22, R25).

    Se lee de la respuesta cuando la hubo, y de la traza cuando se resolvió sin
    llamar a nadie (R24). En ese segundo caso **la traza manda**: dice si el
    gráfico que hay en el ERP lo escribimos nosotros o ya estaba.
    """
    if resultado.respuesta is not None:
        return resultado.respuesta.idempotente
    if resultado.traza is not None:
        return resultado.traza.idempotente
    return False


def _dry_run(resultado: ResultadoGrafico) -> dict[str, Any]:
    """Todo lo que R21 exige enseñar antes de confirmar.

    El estado va **legible** —código y descripción— y no como número: el número
    no le dice nada a quien confirma, y además es configuración del ERP que
    este servicio no escribe en ninguna parte (C3).

    Cuando el gráfico se resolvió desde la traza local (R24) **no hay dry-run
    que enseñar**, porque no se ha leído nada: se devuelve lo que la traza sabe
    del documento que ya está dentro. Inventar un dry-run ahí sería enseñar una
    lectura que no se ha hecho.

    Lo que **nunca** sale: el `cod` ya escrito —lleva el login del ERP dentro
    (R44)— ni los `ide` de las tres filas. El `cod_previsto` sí, porque es lo
    que el dry-run dice que **se generaría** y es lo que permite localizar
    después el gráfico; y por eso el front no lo imprime junto al login.
    """
    if resultado.plan is None:
        traza = resultado.traza
        return {
            "ya_estaba": True,
            "nombre_fichero": traza.nombre_fichero if traza is not None else None,
            "sha256": traza.sha256 if traza is not None else None,
            "bytes": traza.bytes if traza is not None else None,
            "gratipide": traza.gratipide if traza is not None else None,
            "avisos_pasarela": [],
        }

    plan = resultado.plan
    reclamacion = plan.reclamacion
    return {
        "ya_estaba": False,
        "incidencia": reclamacion.codigo,
        "descripcion": reclamacion.descripcion,
        "estado_actual": {
            "codigo": reclamacion.estado_origen.cod,
            "descripcion": reclamacion.estado_origen.res,
        },
        "login_sigrid": plan.login_sigrid,
        "nombre_fichero": plan.peticion.nom,
        "descripcion_grafico": plan.peticion.res,
        "gratipide": plan.peticion.gratipide,
        "bytes": plan.peticion.bytes,
        "sha256": plan.peticion.sha256,
        "cod_previsto": plan.cod_previsto,
        "idempotente_previsto": plan.idempotente_previsto,
        "cerrable": plan.cerrable,
        "ya_cerrada": plan.ya_cerrada,
        "avisos_pasarela": list(plan.avisos_pasarela),
    }
