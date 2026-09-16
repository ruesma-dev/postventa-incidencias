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

## Y el estado del parte viaja en la respuesta (F-028, `design.md` §5)

La respuesta lleva el bloque `estado` —el que F-026 llamaba `aprobacion`—
porque al recargar la pantalla hay que volver a subir la remesa, y eso guarda
sus 22 partes. Si la respuesta no dijera en qué estado queda cada uno, la
pantalla tendría que preguntarlo parte a parte: 22 llamadas de más para pintar
una marca.

Y **no cuesta una consulta más**: `paso_persistencia` ya lee la situación del
parte para la regla de constancia (R23) y la deja en `ContextoParte`, así que
aquí solo se deriva. El sitio donde se paga esa lectura es uno y está medido
(`design.md` §6 y §11.1); duplicarla serían otros 22 viajes por remesa a un
PostgreSQL **compartido** con los demás proyectos.

Lo que se publica del estado lo decide `estado_serializado.py`, que lo
comparten este endpoint y `POST /api/estado`: **ni el `oid`, ni el correo, ni
el nombre, ni el motivo** (R42, R52). Esta respuesta la recibe quien sube la
remesa, que no tiene por qué ser quien decidió sobre ninguno de sus partes.

## No mira `ARCHIVO_HABILITADO` (R34)

Esa ventana protege la biblioteca de SharePoint, que es un sistema ajeno. Esto
escribe en el esquema propio del proyecto, y atarlo dejaría sin poder guardar
el trabajo de revisión justo cuando el archivado está cerrado, que es como se
despliega.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_persistencia import paso_persistencia
from application.pipelines.puerta_de_estado import situacion_leida
from config.settings import obtener_ajustes
from domain.models.errores import PeticionDePersistenciaInvalida
from domain.models.extraccion import ExtraccionParte
from domain.models.firma import LecturaFirma
from domain.models.persistencia import ResultadoGuardado
from domain.models.validacion import ResultadoValidacion, validar_parte
from domain.ports.persistencia import RepositorioPartesPort
from infrastructure.persistencia.fabrica import construir_repositorio

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
from interface_adapters.api.estado_serializado import bloque_de_estado_derivado

__all__ = ["CLAVES_DEL_PARTE", "AnotaLosResultados", "guardar_parte_http"]


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

    remesa_id = a_remesa_id(cuerpo.get("remesa_id"))
    parte = a_parte_troceado(bloque(cuerpo, "parte", CLAVES_DEL_PARTE))
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

    almacen = AnotaLosResultados(
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
        # F-028 · el estado del parte, derivado de la situación que
        # `paso_persistencia` acaba de leer del almacén (R33) y del veredicto
        # que se acaba de guardar. **Sin una consulta más por parte**: son 22
        # viajes por remesa a un PostgreSQL compartido.
        "estado": bloque_de_estado_derivado(
            contexto.validacion, situacion_leida(contexto, almacen)
        ),
        "avisos": list(contexto.avisos),
    }


def _veredicto(
    extraccion: ExtraccionParte, lectura: LecturaFirma
) -> ResultadoValidacion:
    """El veredicto de F-004, recalculado sobre lo que se acaba de recibir (R8).

    Está en su propia función para que se lea de un vistazo qué produce el
    veredicto: la función del dominio, y nada del cuerpo.
    """
    return validar_parte(extraccion, lectura)


class AnotaLosResultados:
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

    Es **público** desde F-026, cuando `POST /api/aprobar` compuso exactamente
    lo mismo —guardar el parte y su veredicto, y contar qué pasó con cada uno—
    y dos envoltorios distintos habrían acabado informando del mismo hecho de
    dos formas distintas. Aquel endpoint lo retiró F-028 T15; quien lo compone
    hoy, por el mismo motivo, es `POST /api/estado`.
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

    def consultar_situacion(self, **datos: Any) -> Any:
        """F-028 · la lee `paso_persistencia` para la regla de constancia.

        Delega y no anota nada: aquí se anotan los dos resultados que el
        contrato de la respuesta promete, y el estado del parte no es uno de
        ellos —lo sirve `estado_serializado.py` a partir de lo que hay en el
        almacén, no de lo que este envoltorio viera pasar—.
        """
        return self._interno.consultar_situacion(**datos)

    def registrar_decision(self, **datos: Any) -> Any:
        """F-028 · la fila de constancia del histórico, si el estado cambió."""
        return self._interno.registrar_decision(**datos)

    def consultar_estado_cierre(self, **datos: Any) -> Any:
        """F-028 · la traza de cierre, que es lo que deja un parte `cerrado`.

        La pregunta `POST /api/estado` **antes de escribir nada**, porque de
        `cerrado` no se sale (R7) y el 409 tiene que llegar sin haber dejado
        filas a su paso.
        """
        return self._interno.consultar_estado_cierre(**datos)

    def cola_validacion_humana(self, **datos: Any) -> tuple:
        return self._interno.cola_validacion_humana(**datos)
