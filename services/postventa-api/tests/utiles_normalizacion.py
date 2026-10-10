# services/postventa-api/tests/utiles_normalizacion.py
"""Dobles de los tests de la normalización de una obra (F-060, Bloque 3).

`specs/F-060-normalizar-ubicaciones/design.md` §7 y §8. Reutiliza los dobles de
F-056 (`tests/utiles_revision.py`) **sin tocarlos**: `RevisionConLote` es una
subclase de `RevisionEnMemoria` que añade `registrar_lote` con la semántica
del repositorio de Postgres (Bloque 2):

- lote vacío: no escribe nada (R16);
- precondiciones (cada revisión con su esperada, ninguna repetida):
  `ValueError` sin escribir;
- la frescura **por fila**: la que ya no tiene la última esperada se salta y
  las demás se escriben, en orden de `incidencia_id` (R12, R13);
- un fallo de la base deshace el lote entero: nada escrito (R14).

Anota `revision.registrar_lote` en la lista común de llamadas, como los demás
dobles, para fijar el orden.

Datos ficticios: obra `9901`, textos «Ejemplo», correos `@ejemplo.invalid`;
los identificadores, `UUID(int=n)`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from uuid import UUID

from domain.models.revision import Revision, RevisionNueva
from domain.ports.revision import ResultadoDelLote

from tests.utiles_revision import Guardada, RevisionEnMemoria

__all__ = ["RevisionConLote"]


class RevisionConLote(RevisionEnMemoria):
    """El `RevisionPort` en memoria de F-056, con el lote de F-060."""

    def __init__(
        self,
        *args: object,
        fallo_del_lote: Exception | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        #: Un fallo **solo** del lote (la base cae al escribir): nada escrito.
        self.fallo_del_lote = fallo_del_lote
        #: Cada lote recibido: sus revisiones y sus esperadas, tal cual.
        self.lotes: list[tuple[tuple[RevisionNueva, ...], dict[UUID, int | None]]] = []
        #: Lo que hace «otra persona» entre el plan y el lote (R13).
        self.antes_del_lote: Callable[[], None] | None = None

    def registrar_lote(
        self,
        *,
        revisiones: Sequence[RevisionNueva],
        esperadas: Mapping[UUID, int | None],
    ) -> ResultadoDelLote:
        self.llamadas.append("revision.registrar_lote")
        self._fallar()
        self.lotes.append((tuple(revisiones), dict(esperadas)))
        if not revisiones:
            return ResultadoDelLote(registradas={}, desactualizadas=frozenset())
        ids = [r.incidencia_id for r in revisiones]
        if len(set(ids)) != len(ids) or any(i not in esperadas for i in ids):
            raise ValueError("lote mal formado: repetida o sin su esperada")
        if self.antes_del_lote is not None:
            self.antes_del_lote()
        if self.fallo_del_lote is not None:
            raise self.fallo_del_lote
        registradas: dict[UUID, int] = {}
        desactualizadas: set[UUID] = set()
        for nueva in sorted(revisiones, key=lambda r: r.incidencia_id):
            ultima = self._ultima(nueva.incidencia_id)
            if (None if ultima is None else ultima.revision_id) != esperadas[
                nueva.incidencia_id
            ]:
                desactualizadas.add(nueva.incidencia_id)
                continue
            revision_id = len(self.guardadas) + 1
            self.guardadas.append(
                Guardada(
                    Revision(
                        revision_id=revision_id,
                        incidencia_id=nueva.incidencia_id,
                        accion=nueva.accion,
                        valores=nueva.valores,
                        huella=nueva.huella,
                        motivo=nueva.motivo,
                        correo=nueva.quien.correo,
                        revisado_at_utc=nueva.revisado_at_utc,
                    ),
                    nueva.quien.oid,
                )
            )
            registradas[nueva.incidencia_id] = revision_id
        return ResultadoDelLote(
            registradas=registradas, desactualizadas=frozenset(desactualizadas)
        )
