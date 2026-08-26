# services/postventa-api/interface_adapters/api/remesa.py
"""Handler de `POST /api/remesa`: dejar constancia de una subida (F-019).

Aquí se **compone el adaptador** —el repositorio de PostgreSQL— y se serializa
el resultado, como manda `docs/CONVENTIONS.md`: la composición vive en el
punto de entrada y nunca dentro de un paso. El puerto inyectable es la costura
de test del endpoint: con él, la suite prueba el borde entero sin que aparezca
una base de datos por ninguna parte.

## Por qué existe, y por qué es el primero de los tres

Porque `postventa.partes.remesa_id` tiene clave ajena contra
`postventa.remesas.id`. Sin una remesa registrada no se puede guardar un
parte, y sin un parte guardado no se puede archivar: ese es el orden que
F-019 viene a hacer verdad, y este endpoint es su primer eslabón.

## Lo que NO hace

- **No mira `ARCHIVO_HABILITADO`** (R34). Esa ventana protege la biblioteca de
  SharePoint, que es un sistema ajeno y compartido; esto escribe en el esquema
  propio del proyecto. Atarlos dejaría sin poder guardar el trabajo de
  revisión justo cuando el archivado está cerrado, que es como se despliega.
- **No guarda `usuario_oid`** (R6, decisión D3 del humano del 2026-08-26). La
  identidad llega en `x-ms-client-principal`, que va en base64 **sin firma**:
  guardarla invitaría a confundir una traza con una identidad verificada.

## El punto flojo, dicho en voz alta

`postventa.remesas` **no tiene clave natural** —ni hash del fichero, ni nombre
único— y F-019 no puede dársela sin tocar el DDL (decisión D2). Consecuencia:
quien resuba el mismo PDF sin conservar su `remesa_id` crea una segunda fila
de remesa. No duplica ningún parte, que es lo que prohíbe
`docs/ARCHITECTURE.md` §9, pero ensucia el histórico. Por eso el `remesa_id`
se devuelve siempre y el front lo conserva mientras dura la remesa en
pantalla.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from config.settings import obtener_ajustes
from domain.models.errores import PeticionDePersistenciaInvalida
from domain.models.persistencia import RegistroRemesa, nuevo_id
from domain.ports.persistencia import RepositorioPartesPort
from infrastructure.persistencia.fabrica import construir_repositorio

__all__ = ["registrar_remesa"]


def registrar_remesa(
    cuerpo: Any,
    *,
    repositorio: RepositorioPartesPort | None = None,
    ahora: datetime | None = None,
) -> dict[str, Any]:
    """Registra la remesa y devuelve su identificador (R1, R2, R3).

    Levanta `PeticionDePersistenciaInvalida` (→ 400) diciendo **qué** está mal,
    y deja subir sin traducir `ConfiguracionPgIncompleta` y
    `PersistenciaNoDisponible` (→ 503): convertir eso en códigos HTTP es
    trabajo del borde.
    """
    if not isinstance(cuerpo, Mapping):
        raise PeticionDePersistenciaInvalida(
            "el cuerpo tiene que ser un objeto JSON con 'nombre_origen' y "
            "'num_partes'"
        )

    remesa = RegistroRemesa(
        id=_identificador(cuerpo.get("remesa_id")),
        nombre_origen=_nombre_origen(cuerpo.get("nombre_origen")),
        recibida_at_utc=ahora if ahora is not None else datetime.now(UTC),
        num_partes=_num_partes(cuerpo.get("num_partes")),
        avisos=_avisos(cuerpo.get("avisos")),
        # R6 / D3: la cabecera de identidad no está firmada. Se queda en NULL.
        usuario_oid=None,
    )

    almacen = (
        repositorio
        if repositorio is not None
        else construir_repositorio(obtener_ajustes())
    )
    resultado = almacen.guardar_remesa(remesa=remesa)
    return {"remesa_id": remesa.id, "resultado": resultado.value}


def _identificador(crudo: Any) -> str:
    """El `remesa_id` del llamante, o uno nuevo (R2, R3, R5).

    Se comprueba **aquí** y no en la base: la columna es `uuid`, así que dejar
    pasar cualquier cadena convertiría un error del llamante en un error de
    infraestructura, y el 503 que saldría manda a mirar el servidor a quien
    tenía que corregir su petición.
    """
    if crudo is None:
        return nuevo_id()
    try:
        return str(UUID(str(crudo)))
    except (ValueError, AttributeError, TypeError) as mal_formado:
        raise PeticionDePersistenciaInvalida(
            "'remesa_id' no es un UUID: o se manda el que devolvió una llamada "
            "anterior, o no se manda ninguno y el servicio lo genera"
        ) from mal_formado


def _nombre_origen(crudo: Any) -> str:
    """De qué fichero salió la remesa. Obligatorio y no vacío (R4)."""
    nombre = str(crudo).strip() if isinstance(crudo, str) else ""
    if not nombre:
        raise PeticionDePersistenciaInvalida(
            "el cuerpo no trae 'nombre_origen', que es el fichero del que "
            "salió la remesa"
        )
    return nombre


def _num_partes(crudo: Any) -> int:
    """Cuántos partes salieron del troceado: un entero ≥ 0 (R4).

    `bool` se rechaza a mano porque en Python **es** un `int`: un
    `isinstance(crudo, int)` a secas dejaría pasar un `True` que acabaría en la
    columna como un 1 que nadie escribió.
    """
    if isinstance(crudo, bool) or not isinstance(crudo, int) or crudo < 0:
        raise PeticionDePersistenciaInvalida(
            "'num_partes' tiene que ser un entero mayor o igual que cero"
        )
    return crudo


def _avisos(crudo: Any) -> tuple[str, ...]:
    """Los avisos del troceado, si los hay. Opcionales, y sin dato del papel.

    Lo que llega aquí son los avisos que emitió `POST /api/split` sobre los
    **ficheros** —cuál se descartó y por qué—, nunca sobre su contenido.
    """
    if crudo is None:
        return ()
    if not isinstance(crudo, (list, tuple)):
        raise PeticionDePersistenciaInvalida(
            "'avisos' tiene que ser una lista de textos"
        )
    return tuple(str(aviso) for aviso in crudo)
