# services/postventa-api/interface_adapters/api/cerrar.py
"""Handler de `POST /api/cerrar`, sin nada de Azure dentro.

Aquí se **componen los cuatro puertos** —el ERP, el repositorio de partes, el de
correspondencias y el de preferencias— y se serializa el resultado, como manda
`docs/CONVENTIONS.md`: la composición vive en el punto de entrada y nunca dentro
de un paso.

Los cuatro puertos inyectables son **la costura de test del endpoint**: con
ellos, la suite prueba el borde entero sin que Sigrid aparezca por ninguna
parte. Sin ellos, el handler construye lo de verdad, y es ahí —y solo ahí—
donde se topa con la puerta de entorno. Por eso, llamado desde un puesto de
trabajo, este endpoint responde **503 y no toca el ERP**.

## Por qué existe este endpoint y no solo el paso del pipeline

Porque sin él **no hay ninguna forma legítima de ejercitar el cierre real**. La
única vía permitida es el entorno desplegado, y algo tiene que haber ahí que se
pueda invocar. Este endpoint es lo que hace posible la verificación manual del
bloque 8 de `tasks.md`.

## El dry-run es lo que se hace por omisión

`commit` vale `false` si no viene, y eso no es comodidad: quien llame a este
endpoint sin haber leído el contrato **no cierra nada en el ERP de
producción**. Cerrar exige además `confirmado: true` o tener el auto-cierre
guardado (R12), y quien lo pida sin ninguna de las dos cosas recibe un 400 que
dice qué le falta.

## La identidad llega en el cuerpo, y hay que decir lo que eso significa

`usuario_oid` y `correo` los manda el front, que los saca de la sesión de la
Static Web App. Esa cabecera **no está firmada** (ver `function_app.py`), así
que esto es una **traza de quién dice ser**, no una identidad verificada — y es
la misma decisión, dicha igual, que tomó F-019 (D3) al dejar `usuario_oid` en
`NULL` en las remesas.

Aquí sí se guarda, y no es una contradicción: para firmar el log del ERP hace
falta un login, y el login **no sale del cuerpo**. Sale de la correspondencia
guardada, o de un candidato **que el ERP tiene que confirmar** antes de que se
escriba nada (R30–R32). Es decir: quien mintiera sobre su `oid` no conseguiría
firmar como otro; conseguiría, como mucho, que el cierre se firmara con el
login que esa persona tenga dado de alta, y eso queda registrado.

## El veredicto ya no llega en el cuerpo: se lee de donde está guardado

**Enmienda del 2026-09-16 (F-030).** Hasta hoy este endpoint reconstruía un
`ResultadoValidacion` con el `veredicto` y el `destino` del cuerpo y valores
fijos para todo lo demás, y la puerta del paso derivaba el estado de **ese**
objeto. Como la huella recomputada sobre él no dependía del parte, la
aprobación de una persona no contaba nunca; y al revés, un cuerpo que dijera
`veredicto=apto` pasaba la puerta sin que nadie hubiera mirado el parte, con
una incidencia del ERP de producción al otro lado.

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

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_cierre import paso_cierre
from config.settings import obtener_ajustes
from domain.models.cierre import PlanDeCierre
from domain.models.errores import CuerpoDeCierreInvalido
from domain.models.persistencia import EstadoArchivo, TrazaArchivo, TrazaGrafico
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import Destino, Veredicto
from domain.ports.erp import ErpPort
from domain.ports.persistencia import (
    RepositorioPartesPort,
    RepositorioPreferenciasPort,
)
from domain.ports.usuarios_sigrid import RepositorioUsuariosSigridPort
from infrastructure.persistencia.fabrica import construir_repositorio
from infrastructure.sigrid.fabrica import construir_erp

__all__ = ["CAMPOS_OBLIGATORIOS", "cerrar_incidencia"]

#: Lo que el cuerpo tiene que traer, y sin lo cual no se puede ni empezar.
#:
#: `commit` y `confirmado` **no** están: son opcionales y su valor por omisión
#: —no cerrar— es el seguro. `correo` tampoco: solo hace falta cuando hay que
#: derivar un candidato, y quien ya tiene correspondencia confirmada no lo
#: necesita.
CAMPOS_OBLIGATORIOS = (
    "hash",
    "numero_incidencia",
    "veredicto",
    "destino",
    "estado_archivo",
    "usuario_oid",
)


def cerrar_incidencia(
    cuerpo: Any,
    *,
    erp: ErpPort | None = None,
    repositorio: RepositorioPartesPort | None = None,
    usuarios: RepositorioUsuariosSigridPort | None = None,
    preferencias: RepositorioPreferenciasPort | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]:
    """Ejecuta el dry-run —y, si procede, el cierre— y devuelve la respuesta.

    Levanta `CuerpoDeCierreInvalido` (→ 400), `ParteNoApto`,
    `ParteNoArchivado`, `ReclamacionNoLocalizada`, `EstadoDeCierreNoResoluble`,
    `EstadoNoCerrable`, `UsuarioSigridNoMapeado`, `UsuarioSigridInexistente` y
    `EstadoCambiadoDesdeElDryRun` (→ 409), `CierreDeshabilitado`,
    `ConfiguracionSigridIncompleta`, `ConfiguracionPgIncompleta` y
    `PersistenciaNoDisponible` (→ 503), `CierreFallido` (→ 502) y
    `CierreSinTraza` (→ 500) **sin traducirlas**: convertir eso en códigos HTTP
    es trabajo del borde.

    **En casi todos esos casos, sin haber escrito nada en el ERP**, y los dos
    que no lo garantizan lo dicen en su mensaje:

    - `CierreFallido`, si la escritura llegó a salir y no volvió la respuesta.
      El reintento lo decide una persona (R27).
    - `CierreSinTraza`, que es el único en el que la incidencia **sí está
      cerrada** y lo que falta es la traza local.
    """
    datos = _exigir_cuerpo(cuerpo)
    ajustes = obtener_ajustes()

    contexto = paso_cierre(
        _como_contexto(datos),
        erp if erp is not None else construir_erp(ajustes),
        repositorio if repositorio is not None else construir_repositorio(ajustes),
        usuarios if usuarios is not None else construir_repositorio(ajustes),
        preferencias if preferencias is not None else construir_repositorio(ajustes),
        commit=_bandera(datos.get("commit")),
        confirmado=_bandera(datos.get("confirmado")),
        usuario_oid=str(datos["usuario_oid"]).strip(),
        correo=str(datos.get("correo") or "").strip(),
        numero_incidencia=str(datos["numero_incidencia"]),
        ahora=ahora if ahora is not None else datetime.now(UTC),
    )
    return _serializar(contexto)


def _exigir_cuerpo(cuerpo: Any) -> Mapping[str, Any]:
    """El cuerpo, comprobado; o el 400 diciendo **qué** le falta (R47).

    Los tres valores de enumeración se comprueban contra el dominio, y eso
    **no es cosmético**: un veredicto que no existe, tratado «como si fuera no
    apto», daría un 409 engañoso; tratado al revés —«como si fuera apto»—
    cerraría en el ERP de producción una incidencia que nadie ha validado. Se
    rechaza y punto.

    El motivo dice qué falta y **nunca** lo que sí venía: el cuerpo lleva el
    correo de quien confirma y su `oid`, y este texto acaba en un log (R45).
    """
    if not isinstance(cuerpo, Mapping):
        raise CuerpoDeCierreInvalido(
            f"el cuerpo tiene que ser un objeto JSON con "
            f"{', '.join(CAMPOS_OBLIGATORIOS)}"
        )

    faltan = [
        campo
        for campo in CAMPOS_OBLIGATORIOS
        if not str(cuerpo.get(campo) or "").strip()
    ]
    if faltan:
        raise CuerpoDeCierreInvalido(
            f"la petición no trae: {', '.join(sorted(faltan))}"
        )

    _exigir_valor_conocido(Veredicto, cuerpo["veredicto"], "veredicto")
    _exigir_valor_conocido(Destino, cuerpo["destino"], "destino")
    _exigir_valor_conocido(EstadoArchivo, cuerpo["estado_archivo"], "estado_archivo")
    return cuerpo


def _exigir_valor_conocido(enumeracion, valor: Any, nombre: str) -> None:
    """El valor tiene que ser uno de los que declara el dominio."""
    admitidos = [miembro.value for miembro in enumeracion]
    if valor not in admitidos:
        raise CuerpoDeCierreInvalido(
            f"'{nombre}' no es uno de los valores admitidos "
            f"({', '.join(admitidos)})"
        )


def _bandera(valor: Any) -> bool:
    """Una bandera del cuerpo, y **solo** el `true` de JSON cuenta.

    Se compara con `is True` a propósito: una cadena `"false"` es verdadera en
    Python, y aquí eso significaría escribir en el ERP de producción porque
    alguien mandó texto donde iba un booleano.
    """
    return valor is True


def _como_contexto(datos: Mapping[str, Any]) -> ContextoParte:
    """Reconstruye el contexto mínimo que necesita el paso de cierre.

    El estado del archivo llega en el cuerpo y **se vuelve a comprobar** dentro
    del paso, exactamente igual que si viniera de dentro. El **veredicto ya
    no**: se va sin rellenar y lo lee la puerta del paso, de la base, porque
    este endpoint no recibe la extracción y no puede emitirlo (F-030; la
    enmienda está arriba y el porqué largo en `archivar.py`).

    De la extracción **no se reconstruye nada**: el paso de cierre no la
    necesita —el número de incidencia llega aparte— y pedirla obligaría al
    front a reenviar el DNI y las observaciones manuscritas del cliente en cada
    cierre, que es justo el dato que no debe viajar de más (R51).

    Y los bytes del PDF tampoco: este endpoint no sube nada.
    """
    hash_parte = str(datos["hash"]).strip()
    return ContextoParte(
        parte=ParteTroceado(
            hash=hash_parte,
            origen="",
            paginas_origen=(),
            modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
            contenido=b"",
        ),
        validacion=None,
        archivo=TrazaArchivo(
            hash_parte=hash_parte,
            estado=EstadoArchivo(datos["estado_archivo"]),
        ),
    )


def _serializar(contexto: ContextoParte) -> dict[str, Any]:
    """Pasa el resultado a JSON. **Ni una clave más que las de R51.**

    Ni un campo manuscrito del parte, ni el contenido del PDF, ni la
    configuración del destino —la URL de la pasarela, la base, la clave—, ni el
    `oid` de quien confirma (R43). Esta respuesta la recibe un navegador, y de
    ahí a una captura de pantalla en un correo hay un paso.

    Lo que **sí** lleva es el dry-run entero (R9, R21): sin él, quien tiene que
    confirmar estaría confirmando a ciegas.
    """
    resultado = contexto.cierre
    return {
        "hash_parte": contexto.parte.hash,
        "numero_incidencia": resultado.plan.reclamacion.codigo,
        "estado": resultado.estado.value,
        "filas_afectadas": resultado.filas_afectadas,
        "dry_run": _dry_run(resultado.plan, contexto.traza_grafico),
        "avisos": list(contexto.avisos),
    }


def _dry_run(
    plan: PlanDeCierre, traza_grafico: TrazaGrafico | None
) -> dict[str, Any]:
    """Lo que R9 exige enseñar antes de confirmar, más el estado del gráfico.

    Los estados van **legibles** —código y descripción— y no como números: el
    número no le dice nada a quien confirma, y además es configuración del ERP
    que este servicio no escribe en ninguna parte (C3).

    El bloque `grafico` es lo que F-012 añade (R49) y lo que **sustituye** al
    `aviso_sin_grafico` que R48 derogó. La diferencia es la que importa: aquel
    era una advertencia fija que decía siempre lo mismo; esto es **el estado
    real** de este parte, leído de la traza propia.
    """
    reclamacion = plan.reclamacion
    return {
        "grafico": _grafico(traza_grafico),
        "incidencia": reclamacion.codigo,
        "descripcion": reclamacion.descripcion,
        "estado_origen": {
            "codigo": reclamacion.estado_origen.cod,
            "descripcion": reclamacion.estado_origen.res,
        },
        "estado_destino": {
            "codigo": reclamacion.estado_destino.cod,
            "descripcion": reclamacion.estado_destino.res,
        },
        "login_sigrid": plan.login_sigrid,
        "cerrable": plan.cerrable,
        "ya_cerrada": plan.ya_cerrada,
    }


def _grafico(traza: TrazaGrafico | None) -> dict[str, Any]:
    """El estado del gráfico de este parte, para el dry-run del cierre (R49).

    Tres estados que quien confirma tiene que poder distinguir: **adjuntado**
    —con el nombre del fichero y el `sha256`, para poder cotejarlo con lo que
    hay en SharePoint—, **dry_run_ok** —se miró, no se subió— y **no consta**.

    `no_consta` es un valor y no una ausencia a propósito: una clave que unas
    veces está y otras no obliga al front a distinguir `undefined` de un
    estado, y ahí es donde se pierde un aviso.

    Lo que **no** sale: el `gra_cod` —lleva el login del ERP dentro (R44)— ni
    los `ide` de las tres filas. Esta respuesta la recibe un navegador, y de
    ahí a una captura de pantalla hay un paso.
    """
    if traza is None:
        return {
            "estado": "no_consta",
            "nombre_fichero": None,
            "sha256": None,
            "adjuntado_at_utc": None,
        }
    return {
        "estado": traza.estado.value,
        "nombre_fichero": traza.nombre_fichero,
        "sha256": traza.sha256,
        "adjuntado_at_utc": (
            traza.adjuntado_at_utc.isoformat()
            if traza.adjuntado_at_utc is not None
            else None
        ),
    }
