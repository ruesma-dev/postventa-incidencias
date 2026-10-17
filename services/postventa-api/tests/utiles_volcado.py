# services/postventa-api/tests/utiles_volcado.py
"""Dobles y datos de los tests de la aplicación y el borde del volcado (F-059).

`specs/F-059-volcado-sigrid-backend/design.md` §8, §10 y §11. Como los de la
revisión (`tests/utiles_revision.py`, que es de F-056 y **no se toca**: aquí se
hereda), todos los dobles escriben en una lista común de `llamadas`, y así un
test fija **el orden** de §10 sin mirar dentro: puertas → base → lectura de
Sigrid → escritura anticipada → escritura en Sigrid → base.

- `RevisionConVolcado`: el `RevisionEnMemoria` de F-056 con lo que T6 añadió
  a la base: cada situación lleva la de volcado (`None` sin eventos, como
  `fila_a_situacion`), cada incidencia puede ser de su obra, y `aprobadas`
  deja fuera la `volcada` antes de `candidata_de` (como el repositorio real).
- `VolcadosEnMemoria`: el `RepositorioVolcadoPort` con la semántica de la
  tabla de §9: append-only, los `CHECK` de fila (que el repositorio real
  convierte en `PersistenciaNoDisponible`, 503), `leer_ensayo` que **compara**
  el `oid` y no lo devuelve (B-1 (a)), y `anotar_enviados` que llama a la
  decisión con lo que leería con las filas bloqueadas (R20).
- `PasarelaFalsa`: el `VolcadoSigridPort`. Al recibir un `commit: true`
  comprueba que el `enviado` de cada parte **ya** está guardado (R20): si no,
  falla el test. Sus respuestas llevan las `filas` del preview, un `mensaje`
  y `cod` provisionales, que nunca pueden salir de aquí (R34, R35, D-13).
- `UsuariosEnMemoria`: el `RepositorioUsuariosSigridPort` de F-009.

Datos ficticios: obras `9901` y `9902`, textos «Ejemplo», proveedores `EJnn`,
correos `@ejemplo.invalid`, login y base inventados; los identificadores,
`UUID(int=n)` (ningún GUID literal).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from domain.models.cierre import CorrespondenciaSigrid
from domain.models.errores import PersistenciaNoDisponible
from domain.models.importacion import IncidenciaEnBandeja
from domain.models.persistencia import ResultadoGuardado
from domain.models.revision import (
    AccionRevision,
    CandidataAlVolcado,
    EstadoRevision,
    Quien,
    Revision,
    SituacionDeRevision,
    candidata_de,
    estado_de,
    huella_de_valores,
    valores_importados,
)
from domain.models.situacion_volcado import (
    ESTADOS_CON_PARTE,
    EstadoEvento,
    ModoVolcado,
    ParteEnSigrid,
    SituacionDeVolcado,
    UltimoEvento,
)
from domain.models.volcado import (
    Ensayo,
    EventoDeEnsayo,
    ParteAVolcar,
    PedidaAlVolcado,
    ResultadoParte,
    Seleccion,
    SituacionBloqueada,
    referencia_de,
)
from domain.ports.volcado import DecisionDelVolcado, FamiliaDeRespuesta, RespuestaDeLote

from tests.utiles_revision import (
    AHORA,
    CORREO,
    OBRA,
    OID,
    Guardada,
    RevisionEnMemoria,
    incidencia,
)

__all__ = [
    "AHORA",
    "BASE",
    "CORREO",
    "DNI_INVENTADO",
    "LOGIN",
    "MENSAJE_DE_LA_PASARELA",
    "NOMBRE_INVENTADO",
    "OBRA",
    "OID",
    "OTRA_OBRA",
    "Evento",
    "PasarelaFalsa",
    "RevisionConVolcado",
    "UsuariosEnMemoria",
    "VolcadosEnMemoria",
    "datos_de_lote",
    "incidencia",
]

OTRA_OBRA = "9902"
#: El login de Sigrid de quien ensaya y vuelca: inventado, y **nunca** en un
#: log ni en una respuesta (R34, §15).
LOGIN = "login.ficticio.volcado"
#: La base de Sigrid: inventada.
BASE = "base_ficticia_volcado"
#: Lo que la pasarela compone en el motivo de un parte y en las `filas` del
#: preview: nada de esto puede salir (R34, R35).
MENSAJE_DE_LA_PASARELA = "Ejemplo de mensaje compuesto por la pasarela"
NOMBRE_INVENTADO = "Nombre Inventado Propietario"
DNI_INVENTADO = "00000000T"

#: Los estados que el `CHECK` de §9 admite en un evento de modo `ensayo`.
_DEL_ENSAYO = frozenset(
    {
        EstadoEvento.PREVISTO,
        EstadoEvento.IDEMPOTENTE,
        EstadoEvento.RECHAZADO,
        EstadoEvento.NO_PROCESADO,
    }
)


# --------------------------------------------------------------------------
# La revisión, con la situación de volcado de cada incidencia
# --------------------------------------------------------------------------


class RevisionConVolcado(RevisionEnMemoria):
    """`RevisionEnMemoria` con lo que T6 dio a la base (§12)."""

    def __init__(self, llamadas: list[str], incidencias=(), **kwargs: Any) -> None:
        super().__init__(llamadas, incidencias, **kwargs)
        self.volcados: VolcadosEnMemoria | None = None
        self.obras: dict[UUID, str] = {}

    def obra_de(self, incidencia_id: UUID) -> str:
        return self.obras.get(incidencia_id, self._obra)

    def esta(self, incidencia_id: UUID) -> bool:
        return incidencia_id in self._incidencias

    def ultima(self, incidencia_id: UUID) -> Revision | None:
        return self._ultima(incidencia_id)

    def _situacion(
        self, incidencia_id: UUID, *, con_original: bool = True
    ) -> SituacionDeRevision:
        inc = self._incidencias[incidencia_id]
        original = None
        if con_original and inc.duplicada_de in self._incidencias:
            original = self._situacion(inc.duplicada_de, con_original=False)  # type: ignore[arg-type]
        volcado = None
        if con_original and self.volcados is not None:
            volcado = self.volcados.situacion_de(incidencia_id)
        return SituacionDeRevision(
            incidencia=inc,
            obra_codigo=self.obra_de(incidencia_id),
            origen=self._origen,
            ultima=self._ultima(incidencia_id),
            original=original,
            volcado=volcado,
        )

    def listar(self, *, obra_codigo: str, tope: int) -> tuple[SituacionDeRevision, ...]:
        self.llamadas.append("revision.listar")
        self.topes.append(tope)
        self._fallar()
        if self.listar_devuelve is not None:
            return self.listar_devuelve
        return tuple(
            self._situacion(i) for i in self._incidencias if self.obra_de(i) == obra_codigo
        )[: tope + 1]

    def aprobadas(self, *, obra_codigo: str) -> tuple[CandidataAlVolcado, ...]:
        """Como el repositorio real (T6): la última `aprobar`, fuera la `volcada`."""
        self.llamadas.append("revision.aprobadas")
        self._fallar()
        situaciones = [
            self._situacion(i) for i in self._incidencias if self.obra_de(i) == obra_codigo
        ]
        return tuple(
            candidata_de(s)
            for s in situaciones
            if s.ultima is not None
            and s.ultima.accion is AccionRevision.APROBAR
            and estado_de(s) is not EstadoRevision.VOLCADA
        )

    # -- ayudantes de siembra --------------------------------------------

    def aprobar(self, n: int, **cambios: Any) -> int:
        """La incidencia `n`, aprobada con sus valores importados (y los cambios)."""
        inc = self._incidencias[UUID(int=n)]
        return self.sembrar(
            UUID(int=n), AccionRevision.APROBAR, replace(valores_importados(inc), **cambios)
        )

    def editar(self, n: int, **cambios: Any) -> int:
        inc = self._incidencias[UUID(int=n)]
        return self.sembrar(
            UUID(int=n), AccionRevision.EDITAR, replace(valores_importados(inc), **cambios)
        )

    def falsear_valores(self, revision_id: int, **cambios: Any) -> None:
        """Un valor cambiado **en la base** con la huella vieja (R7, O-B1-1)."""
        for i, guardada in enumerate(self.guardadas):
            if guardada.revision.revision_id == revision_id:
                vieja = guardada.revision
                self.guardadas[i] = Guardada(
                    replace(vieja, valores=replace(vieja.valores, **cambios)), guardada.oid
                )
                return
        raise AssertionError(f"no hay revisión {revision_id}")


# --------------------------------------------------------------------------
# Los eventos del volcado, en memoria
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Evento:
    """Una fila de `postventa.volcados_sigrid` (§9), con el `oid` aparte."""

    evento_id: int
    llamada_id: UUID
    modo: ModoVolcado
    ensayo_id: UUID | None
    incidencia_id: UUID
    revision_id: int
    huella: str
    obra_codigo: str
    referencia_externa: str
    estado: EstadoEvento
    motivo: str | None
    sigrid_ide: int | None
    sigrid_cod: str | None
    actor_oid: str
    actor_correo: str
    at_utc: datetime


def _check(evento: Evento) -> None:
    """Los `CHECK` de fila de §9; el repositorio real los convierte en 503."""
    fallos = []
    if (evento.modo is ModoVolcado.ENSAYO) != (evento.ensayo_id is None):
        fallos.append("modo-ensayo_id")
    if evento.modo is ModoVolcado.ENSAYO and evento.estado not in _DEL_ENSAYO:
        fallos.append("estado-del-ensayo")
    if (evento.estado in ESTADOS_CON_PARTE) != (
        evento.sigrid_ide is not None and evento.sigrid_cod is not None
    ):
        fallos.append("parte")
    if (
        evento.estado in (EstadoEvento.RECHAZADO, EstadoEvento.NO_PROCESADO)
        and evento.motivo is None
    ):
        fallos.append("motivo")
    if not evento.referencia_externa.startswith("PVI-"):
        fallos.append("referencia")
    if fallos:
        raise PersistenciaNoDisponible(
            f"no se ha podido escribir en PostgreSQL: CheckViolation ({', '.join(fallos)})"
        )


class VolcadosEnMemoria:
    """Un `RepositorioVolcadoPort` en memoria con la semántica de §9 y §8.1."""

    def __init__(self, llamadas: list[str], revision: RevisionConVolcado) -> None:
        self.llamadas = llamadas
        self.revision = revision
        revision.volcados = self
        self.eventos: list[Evento] = []
        self.oids_de_lectura: list[str] = []
        self.fallos: dict[str, Exception] = {}
        #: Lo que pasa «en otra conexión» justo antes de bloquear (R20, R29).
        self.antes_de_anotar: Callable[[], None] | None = None
        self.decisiones: list[Seleccion[EventoDeEnsayo]] = []

    # -- lo que se siembra -------------------------------------------------

    def sembrar(
        self,
        n: int,
        estado: EstadoEvento,
        *,
        modo: ModoVolcado = ModoVolcado.VOLCADO,
        motivo: str | None = None,
        ide: int | None = None,
        cod: str | None = None,
        correo: str = CORREO,
        oid: str = OID,
        cuando: datetime = AHORA,
        llamada_id: UUID | None = None,
    ) -> Evento:
        """Un evento ya guardado, como si lo hubiera dejado otro volcado."""
        incidencia_id = UUID(int=n)
        ultima = self.revision.ultima(incidencia_id)
        assert ultima is not None, "un evento de volcado sale de una revisión"
        evento = Evento(
            evento_id=len(self.eventos) + 1,
            llamada_id=llamada_id or UUID(int=900_000 + len(self.eventos)),
            modo=modo,
            ensayo_id=None if modo is ModoVolcado.ENSAYO else UUID(int=800_000),
            incidencia_id=incidencia_id,
            revision_id=ultima.revision_id,
            huella=ultima.huella,
            obra_codigo=self.revision.obra_de(incidencia_id),
            referencia_externa=referencia_de(incidencia_id),
            estado=estado,
            motivo=motivo,
            sigrid_ide=ide,
            sigrid_cod=cod,
            actor_oid=oid,
            actor_correo=correo,
            at_utc=cuando,
        )
        _check(evento)
        self.eventos.append(evento)
        return evento

    # -- lo que lee la base (las dos `LATERAL` de §12) ---------------------

    def situacion_de(self, incidencia_id: UUID) -> SituacionDeVolcado | None:
        suyos = [e for e in self.eventos if e.incidencia_id == incidencia_id]
        if not suyos:
            return None
        con_parte = [e for e in suyos if e.estado in ESTADOS_CON_PARTE]
        de_volcado = [e for e in suyos if e.modo is ModoVolcado.VOLCADO]
        volcada = None
        if con_parte:
            primero = con_parte[0]
            volcada = ParteEnSigrid(
                primero.sigrid_ide,  # type: ignore[arg-type]
                primero.sigrid_cod,  # type: ignore[arg-type]
                primero.at_utc,
                primero.actor_correo,
            )
        ultimo = None
        if de_volcado:
            u = de_volcado[-1]
            ultimo = UltimoEvento(u.estado, u.motivo, u.at_utc, u.actor_correo)
        return SituacionDeVolcado(volcada, ultimo)

    def ultimo_de(self, incidencia_id: UUID) -> Evento | None:
        suyos = [e for e in self.eventos if e.incidencia_id == incidencia_id]
        return suyos[-1] if suyos else None

    def de_la_llamada(self, llamada_id: UUID) -> list[Evento]:
        return [e for e in self.eventos if e.llamada_id == llamada_id]

    def _fallar(self, operacion: str) -> None:
        fallo = self.fallos.get(operacion)
        if fallo is not None:
            raise fallo

    def _insertar(self, eventos: Sequence[Evento]) -> None:
        """Todo o nada, como una transacción con sus `CHECK`."""
        for evento in eventos:
            _check(evento)
        self.eventos.extend(eventos)

    def _nuevo(self, **campos: Any) -> Evento:
        return Evento(evento_id=len(self.eventos) + 1, **campos)

    # -- el puerto ---------------------------------------------------------

    def situaciones(self, *, incidencias: Sequence[UUID]) -> Mapping[UUID, SituacionDeVolcado]:
        self.llamadas.append("volcados.situaciones")
        self._fallar("situaciones")
        return {
            i: self.situacion_de(i) or SituacionDeVolcado(None, None)
            for i in incidencias
            if self.revision.esta(i)
        }

    def guardar_ensayo(
        self,
        *,
        ensayo_id: UUID,
        obra: str,
        resultados: Sequence[ResultadoParte],
        partes: Sequence[ParteAVolcar],
        quien: Quien,
        ahora: datetime,
    ) -> None:
        self.llamadas.append("volcados.guardar_ensayo")
        self._fallar("guardar_ensayo")
        _casan(partes, resultados)
        nuevos = []
        for parte, resultado in zip(partes, resultados, strict=True):
            nuevos.append(
                Evento(
                    evento_id=len(self.eventos) + len(nuevos) + 1,
                    llamada_id=ensayo_id,
                    modo=ModoVolcado.ENSAYO,
                    ensayo_id=None,
                    incidencia_id=parte.incidencia_id,
                    revision_id=parte.revision_id,
                    huella=parte.huella,
                    obra_codigo=obra,
                    referencia_externa=parte.referencia_externa,
                    estado=resultado.estado,
                    motivo=resultado.motivo,
                    sigrid_ide=resultado.sigrid_ide,
                    sigrid_cod=resultado.sigrid_cod,
                    actor_oid=quien.oid,
                    actor_correo=quien.correo,
                    at_utc=ahora,
                )
            )
        self._insertar(nuevos)

    def leer_ensayo(self, *, ensayo_id: UUID, actor_oid: str) -> Ensayo | None:
        self.llamadas.append("volcados.leer_ensayo")
        self.oids_de_lectura.append(actor_oid)
        self._fallar("leer_ensayo")
        suyos = [
            e
            for e in self.eventos
            if e.llamada_id == ensayo_id and e.modo is ModoVolcado.ENSAYO
        ]
        if not suyos:
            return None
        return Ensayo(
            ensayo_id=ensayo_id,
            obra_codigo=suyos[0].obra_codigo,
            de_la_persona=all(e.actor_oid == actor_oid for e in suyos),
            at_utc=suyos[0].at_utc,
            eventos=tuple(
                EventoDeEnsayo(e.incidencia_id, e.revision_id, e.huella, e.estado)
                for e in suyos
            ),
        )

    def anotar_enviados(
        self,
        *,
        llamada_id: UUID,
        ensayo: Ensayo,
        pedidas: Sequence[PedidaAlVolcado],
        quien: Quien,
        ahora: datetime,
        decidir: DecisionDelVolcado,
    ) -> Seleccion[EventoDeEnsayo]:
        self.llamadas.append("volcados.anotar_enviados")
        if not pedidas:
            raise ValueError("la escritura anticipada exige al menos una pedida (R15)")
        if self.antes_de_anotar is not None:
            self.antes_de_anotar()
        self._fallar("anotar_enviados")
        actuales: dict[UUID, SituacionBloqueada] = {}
        for pedida in sorted(pedidas, key=lambda p: p.incidencia_id):
            if not self.revision.esta(pedida.incidencia_id):
                continue
            ultima = self.revision.ultima(pedida.incidencia_id)
            actuales[pedida.incidencia_id] = SituacionBloqueada(
                revision_id=None if ultima is None else ultima.revision_id,
                accion=None if ultima is None else ultima.accion,
                huella=None if ultima is None else ultima.huella,
                volcado=self.situacion_de(pedida.incidencia_id)
                or SituacionDeVolcado(None, None),
            )
        seleccion = decidir(pedidas, ensayo, actuales)
        self.decisiones.append(seleccion)
        self._insertar(
            [
                Evento(
                    evento_id=len(self.eventos) + i + 1,
                    llamada_id=llamada_id,
                    modo=ModoVolcado.VOLCADO,
                    ensayo_id=ensayo.ensayo_id,
                    incidencia_id=e.incidencia_id,
                    revision_id=e.revision_id,
                    huella=e.huella,
                    obra_codigo=ensayo.obra_codigo,
                    referencia_externa=referencia_de(e.incidencia_id),
                    estado=EstadoEvento.ENVIADO,
                    motivo=None,
                    sigrid_ide=None,
                    sigrid_cod=None,
                    actor_oid=quien.oid,
                    actor_correo=quien.correo,
                    at_utc=ahora,
                )
                for i, e in enumerate(seleccion.mandadas)
            ]
        )
        return seleccion

    def guardar_resultados(
        self,
        *,
        llamada_id: UUID,
        ensayo_id: UUID,
        obra: str,
        partes: Sequence[ParteAVolcar],
        resultados: Sequence[ResultadoParte],
        quien: Quien,
        ahora: datetime,
    ) -> None:
        self.llamadas.append("volcados.guardar_resultados")
        self._fallar("guardar_resultados")
        _casan(partes, resultados)
        self._insertar(
            [
                Evento(
                    evento_id=len(self.eventos) + i + 1,
                    llamada_id=llamada_id,
                    modo=ModoVolcado.VOLCADO,
                    ensayo_id=ensayo_id,
                    incidencia_id=parte.incidencia_id,
                    revision_id=parte.revision_id,
                    huella=parte.huella,
                    obra_codigo=obra,
                    referencia_externa=parte.referencia_externa,
                    estado=resultado.estado,
                    motivo=resultado.motivo,
                    sigrid_ide=resultado.sigrid_ide,
                    sigrid_cod=resultado.sigrid_cod,
                    actor_oid=quien.oid,
                    actor_correo=quien.correo,
                    at_utc=ahora,
                )
                for i, (parte, resultado) in enumerate(zip(partes, resultados, strict=True))
            ]
        )


def _casan(partes: Sequence[ParteAVolcar], resultados: Sequence[ResultadoParte]) -> None:
    if not partes or len(partes) != len(resultados):
        raise ValueError("cada parte mandado lleva su resultado, y al menos hay uno")
    for parte, resultado in zip(partes, resultados, strict=True):
        if (parte.incidencia_id, parte.referencia_externa) != (
            resultado.incidencia_id,
            resultado.referencia_externa,
        ):
            raise ValueError("los partes y los resultados no casan uno a uno")


# --------------------------------------------------------------------------
# La pasarela, de mentira
# --------------------------------------------------------------------------


def datos_de_lote(
    cuerpo: Mapping[str, Any],
    estados: Sequence[str] | None = None,
    *,
    motivo: str = "oficio_no_esta_en_la_obra",
    primer_ide: int = 700_001,
) -> dict[str, Any]:
    """Una respuesta 200 de §8.9 para `cuerpo`, parte a parte.

    Por defecto, `previsto` en un ensayo y `creado` en un volcado. Lleva lo que
    la pasarela de verdad pone y que **nunca** puede salir de este servicio:
    las `filas` del preview (con propietario y persona inventados), el
    `mensaje` del motivo, y el `ide` y el `cod` provisionales de un
    `previsto` (R34, R35, D-13).
    """
    commit = cuerpo["commit"]
    partes_mandadas = cuerpo["partes"]
    if estados is None:
        estados = ["creado" if commit else "previsto"] * len(partes_mandadas)
    partes = []
    for i, (mandada, estado) in enumerate(zip(partes_mandadas, estados, strict=True)):
        parte: dict[str, Any] = {
            "indice": i,
            "referencia_externa": mandada["referencia_externa"],
            "estado": estado,
        }
        if estado in ("creado", "idempotente"):
            parte["ide"] = primer_ide + i
            parte["cod"] = f"RS26.10/{i + 1:04d}"
        elif estado == "previsto":
            parte["ide"] = 990_000 + i
            parte["cod"] = f"RS26.10/{9900 + i:04d}"
            parte["filas"] = [
                {"tabla": "rcp", "propietario": NOMBRE_INVENTADO, "nif": DNI_INVENTADO}
            ]
        else:
            parte["motivo"] = {"codigo": motivo, "mensaje": MENSAJE_DE_LA_PASARELA}
        partes.append(parte)
    return {
        "dry_run": not commit,
        "committed": commit and any(p["estado"] == "creado" for p in partes),
        "obra": cuerpo["obra"],
        "partes": partes,
    }


class PasarelaFalsa:
    """Un `VolcadoSigridPort` de mentira que anota cada llamada (§8.1)."""

    def __init__(
        self,
        llamadas: list[str],
        volcados: VolcadosEnMemoria | None = None,
        *,
        login_existe: bool = True,
    ) -> None:
        self.llamadas = llamadas
        self.volcados = volcados
        self.login_existe = login_existe
        self.fallo_login: Exception | None = None
        #: `cuerpo -> RespuestaDeLote`; por defecto, todo `previsto`/`creado`.
        self.al_ensayar: Callable[[Mapping[str, Any]], RespuestaDeLote] = _todo_bien
        self.al_volcar: Callable[[Mapping[str, Any]], RespuestaDeLote] = _todo_bien
        self.logins: list[str] = []
        self.ensayados: list[dict[str, Any]] = []
        self.volcados_mandados: list[dict[str, Any]] = []
        #: Los `enviado` que había al recibir cada `commit: true` (R20).
        self.enviados_al_volcar: list[list[UUID]] = []

    def existe_usuario(self, *, login: str) -> bool:
        self.llamadas.append("sigrid.existe_usuario")
        self.logins.append(login)
        if self.fallo_login is not None:
            raise self.fallo_login
        return self.login_existe

    def ensayar(self, *, cuerpo: Mapping[str, Any]) -> RespuestaDeLote:
        self.llamadas.append("sigrid.ensayar")
        assert cuerpo.get("commit") is False, "un ensayo va con commit: false"
        self.ensayados.append(dict(cuerpo))
        return self.al_ensayar(cuerpo)

    def volcar(self, *, cuerpo: Mapping[str, Any]) -> RespuestaDeLote:
        self.llamadas.append("sigrid.volcar")
        assert cuerpo.get("commit") is True, "un volcado va con commit: true"
        self.volcados_mandados.append(dict(cuerpo))
        if self.volcados is not None:
            enviados = []
            for parte in cuerpo["partes"]:
                incidencia_id = UUID(parte["referencia_externa"].removeprefix("PVI-"))
                ultimo = self.volcados.ultimo_de(incidencia_id)
                assert ultimo is not None and ultimo.estado is EstadoEvento.ENVIADO, (
                    "R20: el enviado tiene que estar guardado antes del commit: true"
                )
                enviados.append(incidencia_id)
            self.enviados_al_volcar.append(enviados)
        return self.al_volcar(cuerpo)


def _todo_bien(cuerpo: Mapping[str, Any]) -> RespuestaDeLote:
    return RespuestaDeLote(tipo=FamiliaDeRespuesta.OK, datos=datos_de_lote(cuerpo))


def responde(
    estados: Sequence[str] | None = None, **kwargs: Any
) -> Callable[[Mapping[str, Any]], RespuestaDeLote]:
    """Una respuesta 200 con esos estados por parte."""

    def _responder(cuerpo: Mapping[str, Any]) -> RespuestaDeLote:
        return RespuestaDeLote(
            tipo=FamiliaDeRespuesta.OK, datos=datos_de_lote(cuerpo, estados, **kwargs)
        )

    return _responder


def responde_datos(
    transformar: Callable[[dict[str, Any]], Any],
) -> Callable[[Mapping[str, Any]], RespuestaDeLote]:
    """Una respuesta 200 con los datos por defecto pasados por `transformar`."""

    def _responder(cuerpo: Mapping[str, Any]) -> RespuestaDeLote:
        return RespuestaDeLote(
            tipo=FamiliaDeRespuesta.OK, datos=transformar(datos_de_lote(cuerpo))
        )

    return _responder


def responde_familia(
    tipo: FamiliaDeRespuesta, codigo: str | None = None
) -> Callable[[Mapping[str, Any]], RespuestaDeLote]:
    """Un 400 de lote (con o sin código) o una llamada sin respuesta."""

    def _responder(_cuerpo: Mapping[str, Any]) -> RespuestaDeLote:
        return RespuestaDeLote(tipo=tipo, codigo=codigo)

    return _responder


# --------------------------------------------------------------------------
# Las correspondencias de F-009
# --------------------------------------------------------------------------


class UsuariosEnMemoria:
    """Un `RepositorioUsuariosSigridPort` en memoria (F-009)."""

    def __init__(
        self,
        llamadas: list[str],
        *,
        login: str | None = LOGIN,
        confirmada: bool = True,
        oid: str = OID,
    ) -> None:
        self.llamadas = llamadas
        self._filas: dict[str, CorrespondenciaSigrid] = {}
        if login is not None:
            self._filas[oid] = CorrespondenciaSigrid(
                usuario_oid=oid,
                login_sigrid=login,
                alta_at_utc=AHORA - timedelta(days=30),
                verificado_at_utc=(AHORA - timedelta(days=30)) if confirmada else None,
            )
        self.guardadas: list[CorrespondenciaSigrid] = []

    def resolver_login(self, *, usuario_oid: str) -> CorrespondenciaSigrid | None:
        self.llamadas.append("usuarios.resolver_login")
        return self._filas.get(usuario_oid)

    def guardar_login(self, *, correspondencia: CorrespondenciaSigrid) -> ResultadoGuardado:
        self.llamadas.append("usuarios.guardar_login")
        self.guardadas.append(correspondencia)
        self._filas[correspondencia.usuario_oid] = correspondencia
        return ResultadoGuardado.CREADO


def incidencia_de(n: int, **cambios: Any) -> IncidenciaEnBandeja:
    """La incidencia `n` de `utiles_revision`, con los cambios."""
    return incidencia(n, **cambios)


def huella_de(revision: Revision) -> str:
    """La huella recalculada sobre los valores de una revisión guardada."""
    return huella_de_valores(revision.valores)
