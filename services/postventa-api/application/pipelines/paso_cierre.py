# services/postventa-api/application/pipelines/paso_cierre.py
"""Paso 7 del pipeline: cerrar la incidencia en Sigrid (F-009).

Habla con **puertos**, jamás con adaptadores: este módulo no sabe que debajo
hay una pasarela HTTP ni que hay PostgreSQL, y por eso se prueba entero con
dobles en memoria, **sin red y sin escribir en el ERP de producción**. Es lo
mismo que hace `paso_archivo` con `ArchivoPort`.

`ahora` entra por parámetro y no se lee del reloj aquí, por lo mismo que en
F-005 y F-006: un paso que consulta la hora no se puede probar dos veces con el
mismo resultado, y lo que produce acaba escrito en un ERP de producción.

`paso_cierre` **no construye adaptadores**: la composición vive en el punto de
entrada (`docs/CONVENTIONS.md`). Aquí no se puede ni intentar escribir desde
local, porque aquí no hay nada que sepa cómo hacerlo.

## Quién firma el cierre, que es lo que resuelve este módulo hoy

El mecanismo lo decidió el humano el 2026-08-26 —«el correo manda y el login se
confirma una vez»— sobre un supuesto que **la base no confirma**: `usu.ele`
está vacío en los 228 usuarios del ERP. Así que el supuesto se trata como
supuesto:

1. **Correspondencia confirmada** → se usa, **sin derivar nada** y sin volver a
   preguntarle al ERP (R29). La derivación es la **siembra**, no el mecanismo
   de cada cierre.
2. **Correspondencia sin confirmar** —un alta manual— → **tiene precedencia
   sobre la derivación** (R34), pero se verifica igual antes de escribir (R32).
   Precedencia no es exención.
3. **Sin correspondencia** → se deriva un candidato del correo (R30) y se
   verifica contra el ERP por lectura.
4. **El ERP dice que no** → no se cierra (R31), y el error nombra el correo y
   el login intentado para que se pueda dar de alta a mano.
5. **El ERP dice que sí** → se guarda como confirmada (R33).

Lo que hace seguro apoyarse en un supuesto no confirmado es el paso 3: el
supuesto **propone**, el ERP **dispone**, y solo lo que el ERP confirma se
guarda y se escribe.
"""

from __future__ import annotations

from datetime import datetime

from domain.models.cierre import CorrespondenciaSigrid, derivar_login_candidato
from domain.models.errores import (
    UsuarioSigridInexistente,
    UsuarioSigridNoMapeado,
)
from domain.ports.erp import ErpPort
from domain.ports.usuarios_sigrid import RepositorioUsuariosSigridPort

__all__ = ["resolver_login_de_sigrid"]


def resolver_login_de_sigrid(
    usuarios: RepositorioUsuariosSigridPort,
    erp: ErpPort,
    *,
    usuario_oid: str,
    correo: str,
    ahora: datetime,
) -> str:
    """El login con el que se firmará el cierre (R29–R34).

    Levanta `UsuarioSigridNoMapeado` (→ 409) si no hay de dónde sacarlo y
    `UsuarioSigridInexistente` (→ 409) si el ERP no lo confirma. En los dos
    casos **no se escribe nada en Sigrid**: esto ocurre antes de tocar nada.

    Nada de lo que devuelve o levanta lleva el `oid` (R43, R45): el `oid` es
    dato personal seudónimo, no le dice nada a quien lea el mensaje y sí
    identifica a la persona en un log. El **correo** sí va en el mensaje, y no
    choca con R45: se lo estamos diciendo a su dueño, que lo tiene delante.
    """
    correspondencia = usuarios.resolver_login(usuario_oid=usuario_oid)

    if correspondencia is not None and correspondencia.confirmada:
        return correspondencia.login_sigrid

    login = _candidato(correspondencia, correo=correo)
    _exigir_que_el_erp_lo_confirme(erp, login=login, correo=correo)

    usuarios.guardar_login(
        correspondencia=CorrespondenciaSigrid(
            usuario_oid=usuario_oid,
            login_sigrid=login,
            alta_at_utc=(
                correspondencia.alta_at_utc if correspondencia is not None else ahora
            ),
            verificado_at_utc=ahora,
        )
    )
    return login


def _candidato(
    correspondencia: CorrespondenciaSigrid | None, *, correo: str
) -> str:
    """El login que se le va a proponer al ERP (R30, R34).

    **El alta manual gana a la derivación**, y ese orden es el requisito: la
    tabla existe justamente para los casos en los que la convención falla —2 de
    los 8 usuarios medidos—, así que derivar por encima de lo que un
    administrador dio de alta la dejaría sin servir para nada.
    """
    if correspondencia is not None:
        return correspondencia.login_sigrid

    login = derivar_login_candidato(correo)
    if not login:
        raise UsuarioSigridNoMapeado(
            "no hay correspondencia guardada con el ERP para este usuario y "
            "tampoco un correo del que derivar un candidato, así que no hay con "
            "qué firmar el cierre: hay que dar el mapeo de alta a mano con "
            "infra/07_alta_usuario_sigrid.ps1"
        )
    return login


def _exigir_que_el_erp_lo_confirme(erp: ErpPort, *, login: str, correo: str) -> None:
    """El ERP tiene la última palabra, y sin ella no se cierra (R31, R32).

    Se comprueba **siempre** que la correspondencia no esté confirmada: venga de
    un alta manual o de una derivación. Dar por bueno un login sin comprobarlo
    sería firmar en el log de un ERP de producción a nombre de alguien que
    quizá no existe.

    El mensaje nombra el correo **y** el login intentado. Sin esas dos cosas,
    quien lo recibe no puede dar de alta la correspondencia: no sabría ni de
    quién es el problema ni qué se probó.
    """
    if erp.existe_usuario(login=login):
        return

    raise UsuarioSigridInexistente(
        f"el login «{login}», derivado del correo {correo}, no existe "
        f"exactamente una vez en el maestro de usuarios del ERP, así que no se "
        f"cierra nada y no se ha escrito nada en Sigrid: hay que dar de alta la "
        f"correspondencia a mano con infra/07_alta_usuario_sigrid.ps1"
    )
