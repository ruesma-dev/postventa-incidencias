# services/postventa-api/interface_adapters/api/aprobar.py
"""Handler de `POST /api/aprobar`: la decisión humana sobre un parte (F-026).

Es la **única** puerta por la que un parte que F-004 rechazó puede acabar
entrando en el circuito que archiva en SharePoint y cierra una incidencia en
el ERP de producción. Todo lo que hay aquí existe para que esa puerta sea
estrecha, explícita y quede registrada.

## Endpoint propio, y no una clave más en `/api/parte` (R18)

Guardar ocurre en **cada revalidación**; aprobar es una decisión de una
persona. Colgar la aprobación de `/api/parte` la convertiría en un efecto de
guardar, y el día que el autoguardado escriba solo se estaría aprobando solo.
Una petición, una decisión, una fila de auditoría.

## Y sin embargo guarda el parte (design.md §6)

Aprobar hace **las dos cosas en una sola llamada**: guarda el parte con su
veredicto —reutilizando `paso_persistencia`, que es idempotente— y escribe la
aprobación con la huella de *ese mismo* veredicto.

Hacerlo en dos llamadas dejaría una ventana entre «lo que se guardó» y «lo que
se aprobó», y lo que quedaría en la base sería la aprobación de un veredicto
que no está escrito. Así, la huella aprobada es por construcción la del
veredicto que acaba de escribirse.

El orden importa y es el del código: parte → validación → aprobación. La
validación se guarda antes porque **guardar una validación revoca** la
aprobación cuyo veredicto ya no coincide (R30); escribir la aprobación antes
la dejaría revocada en el mismo acto de nacer.

## El veredicto se recalcula. Siempre (R5)

**Nunca** se acepta un veredicto ya hecho en el cuerpo, igual que en
`/api/parte` (R8 de F-019). Es lo que sostiene R9 entera: si llegara hecho,
quien llama se declararía aprobable y aprobaría un parte al que le falta el
código de obra, que es lo único que esta feature **no** puede permitir.

## Qué se guarda de la persona: el `oid`, y nada más (R13)

El `oid` opaco de Entra ID. Nunca el correo, nunca el nombre, nunca el login
de Sigrid. Es el mismo tratamiento que ya reciben `cierres.confirmado_por` y
`graficos.confirmado_por`. Y **no sale en la respuesta** (R38, R43): la
pantalla no lo necesita y quien audite lo lee en la base.

## No mira `ARCHIVO_HABILITADO` ni `CIERRE_HABILITADO` (R21)

Esas ventanas protegen SharePoint y el ERP, que son sistemas ajenos. Aprobar
escribe en el esquema propio del proyecto, y atarlo dejaría sin poder registrar
el trabajo de revisión justo cuando las ventanas de escritura están cerradas,
que es como se despliega el entorno.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_persistencia import paso_persistencia
from config.settings import obtener_ajustes
from domain.models.aprobacion import (
    MOTIVOS_APROBABLES,
    Aprobacion,
    es_aprobable,
    huella_de_veredicto,
)
from domain.models.errores import (
    ParteNoAprobable,
    PeticionDePersistenciaInvalida,
)
from domain.models.validacion import ResultadoValidacion, Veredicto, validar_parte
from domain.ports.persistencia import RepositorioPartesPort
from infrastructure.persistencia.fabrica import construir_repositorio

from interface_adapters.api.aprobacion_serializada import bloque_de_aprobacion
from interface_adapters.api.cuerpos import (
    CLAVES_DE_LA_EXTRACCION,
    CLAVES_DE_LA_FIRMA,
    CLAVES_DEL_PARTE,
    a_extraccion,
    a_lectura_de_firma,
    a_parte_troceado,
    a_remesa_id,
    bloque,
)
from interface_adapters.api.parte import AnotaLosResultados

__all__ = ["aprobar_parte_http"]


def aprobar_parte_http(
    cuerpo: Any,
    *,
    repositorio: RepositorioPartesPort | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]:
    """Registra que una persona aprueba este parte, y devuelve qué pasó (R2).

    Levanta `PeticionDePersistenciaInvalida` y `CuerpoDeValidacionInvalido`
    (→ 400) diciendo **qué** falta, `ParteNoAprobable` (→ 409) diciendo **qué**
    lo impide, y deja subir sin traducir `ReferenciaNoConsta` (→ 409),
    `ConfiguracionPgIncompleta` y `PersistenciaNoDisponible` (→ 503):
    convertir eso en códigos HTTP es trabajo del borde.

    En los tres casos de rechazo **no se ha escrito nada** (R20): las dos
    puertas de este handler —quién decide y qué se puede decidir— van antes de
    la primera llamada al puerto.
    """
    if not isinstance(cuerpo, Mapping):
        raise PeticionDePersistenciaInvalida(
            "el cuerpo tiene que ser un objeto JSON con 'remesa_id', 'parte', "
            "'extraccion', 'firma', 'usuario_oid' y 'confirmado'"
        )

    usuario_oid = _usuario_oid(cuerpo.get("usuario_oid"))
    _exigir_confirmacion(cuerpo.get("confirmado"))

    remesa_id = a_remesa_id(cuerpo.get("remesa_id"))
    parte = a_parte_troceado(bloque(cuerpo, "parte", CLAVES_DEL_PARTE))
    extraccion = a_extraccion(bloque(cuerpo, "extraccion", CLAVES_DE_LA_EXTRACCION))
    lectura = a_lectura_de_firma(bloque(cuerpo, "firma", CLAVES_DE_LA_FIRMA))

    # R5: el veredicto se emite AQUÍ, con las reglas de F-004, y sobre él se
    # decide si el parte es aprobable. Lo que venga en el cuerpo no se mira.
    validacion = validar_parte(extraccion, lectura)
    _exigir_aprobable(validacion)

    contexto = ContextoParte(
        parte=parte,
        extraccion=extraccion,
        lectura_firma=lectura,
        validacion=validacion,
    )
    almacen = AnotaLosResultados(
        repositorio
        if repositorio is not None
        else construir_repositorio(obtener_ajustes())
    )
    momento = ahora if ahora is not None else datetime.now(UTC)

    paso_persistencia(contexto, almacen, remesa_id=remesa_id, ahora=momento)

    aprobacion = Aprobacion(
        hash_parte=parte.hash,
        aprobado_por=usuario_oid,
        aprobado_at_utc=momento,
        destino_aprobado=validacion.destino,
        motivos_aprobados=tuple(motivo.codigo for motivo in validacion.motivos),
        huella_aprobada=huella_de_veredicto(validacion),
        validado_at_utc=momento,
    )
    almacen.guardar_aprobacion(aprobacion=aprobacion)

    return {
        "hash_parte": parte.hash,
        "resultado_parte": almacen.resultado_parte,
        "resultado_validacion": almacen.resultado_validacion,
        "aprobacion": bloque_de_aprobacion(aprobacion),
        "avisos": list(contexto.avisos),
    }


def _usuario_oid(crudo: Any) -> str:
    """Quién decide. Obligatorio, y el `oid` opaco (R4, R13).

    Sin él **no se registra nada**: lo que esta feature guarda es justamente
    que una persona concreta se hizo responsable de meter en el ERP un parte
    que la máquina había rechazado. Una aprobación anónima no es una
    aprobación, es un permiso.
    """
    valor = crudo.strip() if isinstance(crudo, str) else ""
    if not valor:
        raise PeticionDePersistenciaInvalida(
            "el cuerpo no trae 'usuario_oid': sin saber quién decide no se "
            "puede registrar la decisión, y aprobar un parte es hacerse "
            "responsable de que entre en el circuito que cierra la incidencia"
        )
    return valor


def _exigir_confirmacion(crudo: Any) -> None:
    """Aprobar es un **acto explícito** (R1): el booleano de JSON, no otra cosa.

    Se exige `true` de verdad y no un valor «que parezca verdadero»: la cadena
    `"true"` o un `1` son un cliente que serializa mal, y tratarlos como
    confirmación convierte un fallo de programación en una aprobación
    registrada a nombre de una persona.
    """
    if crudo is not True:
        raise PeticionDePersistenciaInvalida(
            "el cuerpo no trae 'confirmado': true — aprobar un parte que la "
            "validación rechazó es un acto explícito, y se confirma con el "
            "booleano de JSON"
        )


def _exigir_aprobable(validacion: ResultadoValidacion) -> None:
    """La segunda puerta: **qué** se puede decidir (R9, R10).

    El motivo dice cuál lo impide y cómo se arregla, porque los dos casos se
    arreglan de forma opuesta: al parte ya apto no hay que hacerle nada, y al
    que ha perdido un dato decisivo hay que **teclearlo**, no aprobarlo. Y no
    lleva ni una letra del papel (R43): esto acaba en un log.
    """
    if es_aprobable(validacion):
        return

    if validacion.veredicto == Veredicto.APTO:
        raise ParteNoAprobable(
            f"este parte ya es apto: la validación lo manda a "
            f"«{validacion.destino.value}» y no hay nada que aprobar"
        )

    impiden = sorted(
        motivo.codigo.value
        for motivo in validacion.motivos
        if motivo.codigo not in MOTIVOS_APROBABLES
    )
    if not impiden:
        raise ParteNoAprobable(
            f"este parte no es apto y la validación no dice por qué, así que "
            f"no hay nada que decidir: va a «{validacion.destino.value}» y hay "
            f"que revalidarlo"
        )
    raise ParteNoAprobable(
        f"este parte no se puede aprobar: {', '.join(impiden)}. Ahí no hay nada "
        f"que decidir — hay que corregir ese campo del parte y revalidarlo, y "
        f"con eso vuelve al circuito sin que nadie tenga que aprobar nada"
    )
