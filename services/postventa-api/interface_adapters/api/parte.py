# services/postventa-api/interface_adapters/api/parte.py
"""Handler de `POST /api/parte`: guardar el parte y su veredicto (F-019).

Aquí se **compone el paso** —`application/pipelines/paso_persistencia.py`, que
está escrito exactamente para esto desde F-005 y hasta hoy no tenía punto de
entrada— y se serializa el resultado, como manda `docs/CONVENTIONS.md`: la
composición vive en el punto de entrada y nunca dentro de un paso.

## El cuerpo es el de `/api/validar` más dos claves, y es deliberado

El front ya compone ese cuerpo (`js/pipeline.js::cuerpoDeValidacion`), así que
reutilizarlo evita que haya **dos formas de describir el mismo parte**, que es
como divergen los contratos. Los parsers son literalmente los mismos: viven en
`interface_adapters/api/cuerpos.py` desde T1 de esta feature.

Lo propio de aquí son `remesa_id` y el bloque `parte` —de qué fichero salió,
qué páginas suyas y cómo se decidió el corte—, que `/api/validar` no necesita
porque no guarda nada.

## El veredicto se recalcula. Siempre (R8)

**Nunca** se acepta un veredicto ya hecho en el cuerpo. Lo que se decide con
él es si una incidencia del ERP se archiva y se cierra, así que se vuelve a
emitir aquí con `domain/models/validacion.py::validar_parte`, que es dominio
puro y no gasta IA. Lo guardado es lo que dicen las reglas sobre los datos
recibidos, y no lo que el llamante quiera contar.

## Los bytes no entran (R12)

`ParteTroceado.contenido` se reconstruye como `b""`. El PDF lleva el DNI
manuscrito, vive en SharePoint y el disco de este servidor es compartido y
solo crece. `upsert_parte` los ignora de todas formas: lo que se evita aquí es
**ofrecer la vía**.

## No mira `ARCHIVO_HABILITADO` (R34)

Esa ventana protege la biblioteca de SharePoint, que es un sistema ajeno. Esto
escribe en el esquema propio del proyecto, y atarlo dejaría sin poder guardar
el trabajo de revisión justo cuando el archivado está cerrado, que es como se
despliega.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_persistencia import paso_persistencia
from config.settings import obtener_ajustes
from domain.models.errores import PeticionDePersistenciaInvalida
from domain.models.extraccion import ExtraccionParte
from domain.models.persistencia import ResultadoGuardado
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import ResultadoValidacion, validar_parte
from domain.ports.persistencia import RepositorioPartesPort
from infrastructure.persistencia.fabrica import construir_repositorio

from interface_adapters.api.cuerpos import (
    CLAVES_DE_LA_EXTRACCION,
    CLAVES_DE_LA_FIRMA,
    a_extraccion,
    a_lectura_de_firma,
    bloque,
)

__all__ = ["CLAVES_DEL_PARTE", "guardar_parte_http"]

#: Lo que tiene que traer el bloque `parte` del cuerpo.
#:
#: Los cuatro, y no solo el `hash`: `origen` y `paginas_origen` son lo que
#: permite volver sobre la remesa sin reabrirla, y `modo_deteccion` es la
#: diferencia entre «este documento no tenía ningún parte de dos hojas» y «en
#: este documento no se ha podido mirar». Guardar un parte sin ellos deja una
#: fila que no se puede rastrear.
CLAVES_DEL_PARTE = ("hash", "origen", "paginas_origen", "modo_deteccion")


def guardar_parte_http(
    cuerpo: Any,
    *,
    repositorio: RepositorioPartesPort | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]:
    """Guarda el parte y su veredicto, y cuenta qué pasó con cada uno (R7).

    Levanta `PeticionDePersistenciaInvalida` y `CuerpoDeValidacionInvalido`
    (→ 400) diciendo **qué** falta, y deja subir sin traducir
    `ReferenciaNoConsta` (→ 409), `ConfiguracionPgIncompleta` y
    `PersistenciaNoDisponible` (→ 503): convertir eso en códigos HTTP es
    trabajo del borde.
    """
    if not isinstance(cuerpo, Mapping):
        raise PeticionDePersistenciaInvalida(
            "el cuerpo tiene que ser un objeto JSON con 'remesa_id', 'parte', "
            "'extraccion' y 'firma'"
        )

    remesa_id = _remesa_id(cuerpo.get("remesa_id"))
    parte = _a_parte_troceado(bloque(cuerpo, "parte", CLAVES_DEL_PARTE))
    extraccion = a_extraccion(
        bloque(cuerpo, "extraccion", CLAVES_DE_LA_EXTRACCION)
    )
    lectura = a_lectura_de_firma(bloque(cuerpo, "firma", CLAVES_DE_LA_FIRMA))

    contexto = ContextoParte(
        parte=parte,
        extraccion=extraccion,
        lectura_firma=lectura,
        # R8: el veredicto se emite AQUÍ, con las reglas de F-004. Nunca llega
        # hecho desde fuera.
        validacion=_veredicto(extraccion, lectura),
    )

    almacen = _AnotaLosResultados(
        repositorio
        if repositorio is not None
        else construir_repositorio(obtener_ajustes())
    )
    paso_persistencia(
        contexto,
        almacen,
        remesa_id=remesa_id,
        ahora=ahora if ahora is not None else datetime.now(UTC),
    )
    return {
        "hash_parte": parte.hash,
        "resultado_parte": almacen.resultado_parte,
        "resultado_validacion": almacen.resultado_validacion,
        "avisos": list(contexto.avisos),
    }


def _veredicto(
    extraccion: ExtraccionParte, lectura: Any
) -> ResultadoValidacion:
    """El veredicto de F-004, recalculado sobre lo que se acaba de recibir (R8).

    Está en su propia función para que se lea de un vistazo qué produce el
    veredicto: la función del dominio, y nada del cuerpo.
    """
    return validar_parte(extraccion, lectura)


class _AnotaLosResultados:
    """Envuelve el puerto y recuerda qué devolvió cada guardado.

    `paso_persistencia` **no se reescribe** (`design.md` §2): recibe el
    contexto, el repositorio, el `remesa_id` y el `ahora`, y devuelve el
    contexto. Pero el contrato de `POST /api/parte` promete `resultado_parte`
    y `resultado_validacion`, y esos dos valores el paso los consume y los
    descarta.

    La alternativa era deducirlos del texto de un aviso —«este parte ya se
    había procesado antes»—, que ataría la respuesta HTTP a la redacción de un
    mensaje y **no daría ninguna respuesta** para la validación, porque el paso
    no emite aviso por ella. Así que se anotan al pasar, que es composición en
    el punto de entrada y lo único que hay aquí.

    Implementa `RepositorioPartesPort` entero delegando: si mañana el paso
    llamara a otra operación, este envoltorio no se interpone.
    """

    def __init__(self, interno: RepositorioPartesPort) -> None:
        self._interno = interno
        #: Por omisión, lo que devuelve un `upsert` que crea la fila. Solo se
        #: leen después de que el paso haya llamado a las dos operaciones; si
        #: alguna levantara, la excepción sube y nadie lee esto.
        self.resultado_parte = ResultadoGuardado.CREADO.value
        self.resultado_validacion = ResultadoGuardado.CREADO.value

    def guardar_parte(self, **datos: Any) -> ResultadoGuardado:
        resultado = self._interno.guardar_parte(**datos)
        self.resultado_parte = resultado.value
        return resultado

    def guardar_validacion(self, **datos: Any) -> ResultadoGuardado:
        resultado = self._interno.guardar_validacion(**datos)
        self.resultado_validacion = resultado.value
        return resultado

    def guardar_remesa(self, **datos: Any) -> ResultadoGuardado:
        return self._interno.guardar_remesa(**datos)

    def guardar_archivo(self, **datos: Any) -> ResultadoGuardado:
        return self._interno.guardar_archivo(**datos)

    def guardar_cierre(self, **datos: Any) -> ResultadoGuardado:
        return self._interno.guardar_cierre(**datos)

    def cola_validacion_humana(self, **datos: Any) -> tuple:
        return self._interno.cola_validacion_humana(**datos)


def _remesa_id(crudo: Any) -> str:
    """El `remesa_id` que devolvió `POST /api/remesa`. Obligatorio (R10, R11).

    Se comprueba que sea un UUID **aquí**: la columna es `uuid`, así que
    dejarlo pasar convertiría un error del llamante en un 503 que manda a
    mirar el servidor a quien tenía que corregir su petición.
    """
    if crudo is None:
        raise PeticionDePersistenciaInvalida(
            "el cuerpo no trae 'remesa_id': es el identificador que devolvió "
            "POST /api/remesa, y hay que registrar la remesa antes de guardar "
            "sus partes"
        )
    try:
        return str(UUID(str(crudo)))
    except (ValueError, AttributeError, TypeError) as mal_formado:
        raise PeticionDePersistenciaInvalida(
            "'remesa_id' no es un UUID: tiene que ser el que devolvió "
            "POST /api/remesa"
        ) from mal_formado


def _a_parte_troceado(bloque_parte: Mapping[str, Any]) -> ParteTroceado:
    """Reconstruye lo que produjo `POST /api/split`, **sin los bytes** (R12)."""
    return ParteTroceado(
        hash=_texto(bloque_parte["hash"], "parte.hash"),
        origen=_texto(bloque_parte["origen"], "parte.origen"),
        paginas_origen=_paginas(bloque_parte["paginas_origen"]),
        modo_deteccion=_modo(bloque_parte["modo_deteccion"]),
        # R12: el PDF vive en SharePoint. Aquí no entra ni un byte.
        contenido=b"",
    )


def _texto(crudo: Any, nombre: str) -> str:
    """Un texto obligatorio y no vacío del bloque `parte`."""
    valor = str(crudo).strip() if isinstance(crudo, str) else ""
    if not valor:
        raise PeticionDePersistenciaInvalida(
            f"'{nombre}' tiene que ser un texto no vacío"
        )
    return valor


def _paginas(crudo: Any) -> tuple[int, ...]:
    """Las páginas del original de las que salió el parte, numeradas desde 1.

    Se exige que sean números: `paginas_origen` es lo que permite volver sobre
    la remesa sin reabrirla, y una lista de textos deja una fila que no
    localiza nada.
    """
    if isinstance(crudo, str) or not isinstance(crudo, Sequence):
        raise PeticionDePersistenciaInvalida(
            "'parte.paginas_origen' tiene que ser una lista de números de página"
        )
    paginas = []
    for pagina in crudo:
        if isinstance(pagina, bool) or not isinstance(pagina, int):
            raise PeticionDePersistenciaInvalida(
                "'parte.paginas_origen' tiene que traer solo números de página"
            )
        paginas.append(pagina)
    return tuple(paginas)


def _modo(crudo: Any) -> ModoDeteccion:
    """Cómo se decidió dónde empezaba el parte, con los valores del dominio.

    Un valor desconocido **no** se sustituye por el más común: guardaría una
    mentira sobre cómo se troceó la remesa, y esa columna es lo que distingue
    «no había partes de dos hojas» de «no se pudo mirar».
    """
    try:
        return ModoDeteccion(crudo)
    except ValueError as desconocido:
        admitidos = ", ".join(modo.value for modo in ModoDeteccion)
        raise PeticionDePersistenciaInvalida(
            f"'parte.modo_deteccion' no es uno de los valores admitidos "
            f"({admitidos})"
        ) from desconocido
