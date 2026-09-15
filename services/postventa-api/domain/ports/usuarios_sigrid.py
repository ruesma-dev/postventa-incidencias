# services/postventa-api/domain/ports/usuarios_sigrid.py
"""El puerto de las correspondencias `oid` de Entra → login de Sigrid (F-009).

Va aparte de `RepositorioPartesPort` y de `RepositorioPreferenciasPort` por lo
mismo que aquellos dos fueron uno aparte del otro: **son tres vidas
distintas**. Lo que se guarda de un parte lo escribe el pipeline; la
preferencia de auto-cierre la decide el usuario y su fila nace sola al
decidirla; y esto lo da de alta un administrador, y **su ausencia impide
cerrar**. Fundirlas haría que guardar una preferencia creara media identidad.

## Por qué existe una tabla y no una derivación

Porque la derivación no da la talla, y está medido (`design.md` §1, D2): de los
228 usuarios del ERP, **ninguno** tiene correo registrado; de los 8 que lo
tienen en la tabla de usuario×empresa, **6** cumplen la convención «el login es
la parte local del correo». Un 75 % no vale cuando el error consiste en firmar
en el log de un ERP de producción el cierre de una persona que no lo hizo.

Así que la derivación es la **siembra**, no el mecanismo: se propone un
candidato, lo verifica el ERP, y solo lo verificado se guarda aquí (R33) para
que el segundo cierre de esa persona no derive nada (R29).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.models.cierre import CorrespondenciaSigrid
from domain.models.persistencia import ResultadoGuardado

__all__ = ["RepositorioUsuariosSigridPort"]


@runtime_checkable
class RepositorioUsuariosSigridPort(Protocol):
    """El almacén del par `oid` → login, sea quien sea quien lo implemente."""

    def resolver_login(self, *, usuario_oid: str) -> CorrespondenciaSigrid | None:
        """La correspondencia de ese usuario, o `None` si no hay ninguna.

        `None` **no** es un error: es la primera vez de esa persona, y lo que
        toca entonces es derivar un candidato y verificarlo (R30).

        Una correspondencia devuelta se usa **sin derivar nada** (R29, R34),
        esté ya confirmada o venga de un alta manual: la derivación nunca gana
        a lo que alguien dio de alta a mano.
        """
        ...

    def guardar_login(
        self, *, correspondencia: CorrespondenciaSigrid
    ) -> ResultadoGuardado:
        """Deja **una sola** fila por usuario, con su marca de verificación.

        Es lo que hace que la siembra ocurra una vez y no en cada cierre (R33).
        Guardar la misma correspondencia dos veces actualiza la fila; no crea
        una segunda identidad para la misma persona.
        """
        ...
