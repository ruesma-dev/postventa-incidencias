# services/postventa-api/tests/utiles_revision.py
"""Dobles y datos de los tests de la aplicación y el borde de la revisión (F-056).

`specs/F-056-revision-bandeja-backend/design.md` §5, §7 y §8. Todos los dobles
escriben en una lista común de `llamadas`, y así un test fija **el orden** de
`aplicar_accion` (§7) sin mirar dentro: `situacion` → (transición y frescura,
sin colaborador) → Sigrid (catálogo y ubicaciones) → `registrar`.

- `RevisionEnMemoria`: el `RevisionPort` con la semántica de la base que le
  importa a la aplicación: append-only, la última por `revision_id` (R38), la
  frescura de **todas** las esperadas antes de escribir (R7, R22) y
  `aprobadas` con `candidata_de` del dominio (R34), como el repositorio real.
  Guarda el `oid` aparte, como la columna `revisado_por`: nunca sale en una
  lectura (R10).
- `CatalogoDeLaObra`: el `CatalogoObraPort` con la obra `9901` inventada.
- `UbicacionesQueCuentan`: la fuente de las ubicaciones válidas por unidad
  (en el Bloque 3 llega como parámetro; su lectura de Sigrid es el Bloque 3
  bis).

Datos ficticios: obra `9901`, textos «Ejemplo», correos `@ejemplo.invalid`;
los identificadores, `UUID(int=n)` (ningún GUID literal).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID

from domain.models.errores import RevisionDesactualizada
from domain.models.importacion import IncidenciaEnBandeja
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    Listado,
    ListasCerradas,
    Opcion,
    OrigenIncidencia,
    Urgencia,
)
from domain.models.revision import (
    CandidataAlVolcado,
    Revision,
    RevisionNueva,
    SituacionDeRevision,
    candidata_de,
    es_candidata,
)
from domain.ports.catalogo_obra import (
    FilaOficioCatalogo,
    FilaUnidadCatalogo,
    LecturaCatalogo,
)

OBRA = "9901"
OBRA_REF = "123456789"  # `upv.obride` inventado
U1 = "9901.03VILLA 1."
U2 = "9901.03VILLA 2."
U3 = "9901.03VILLA 3."  # sin tipología: lista vacía
CREADA = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
AHORA = datetime(2026, 10, 8, 9, 30, tzinfo=UTC)

#: Quien revisa: un `oid` **opaco** inventado, sin forma de GUID, y un correo
#: ficticio. Ninguno de los dos puede salir en un log; el `oid`, en ninguna
#: respuesta (R10, R11, R41).
OID = "oid-de-prueba-de-la-revision"
CORREO = "persona.revisora@ejemplo.invalid"
OID_2 = "oid-de-prueba-de-otra-persona"
CORREO_2 = "otra.persona@ejemplo.invalid"

#: Textos que no pueden ir a un log (R41): descripción, detalle, motivo,
#: nombres de unidad y de proveedor.
DESCRIPCION = "Ejemplo de grieta junto a la ventana del salón"
DETALLE = "Ejemplo de detalle con el teléfono de una persona"
MOTIVO = "Ejemplo de motivo de descarte con un nombre propio"
NOMBRE_U1 = "Villa Ejemplo Uno"
NOMBRE_PROVEEDOR = "Carpintería Ejemplo, S.L."

#: Las ubicaciones válidas por unidad (la tipología de cada una, R48).
UBICACIONES: dict[str, tuple[str, ...]] = {
    U1: ("Baño", "Cocina", "cocina"),
    U2: ("Terraza", "Baño"),
    U3: (),
}

LISTAS = ListasCerradas(
    ubicaciones=("Esto no se usa: D-4",),
    urgencias=(Opcion("Urgente", "urgente"), Opcion("Seguridad", "seguridad")),
    listados=(Opcion("Primer listado", "primero"), Opcion("Segundo listado", "segundo")),
)


# --------------------------------------------------------------------------
# Las incidencias de la bandeja
# --------------------------------------------------------------------------


def incidencia(n: int = 1, **cambios: object) -> IncidenciaEnBandeja:
    base: dict[str, object] = {
        "incidencia_id": UUID(int=n),
        "importacion_id": UUID(int=1000),
        "fila_origen": n + 1,
        "unidad_codigo": U1,
        "unidad_nombre": NOMBRE_U1,
        "ubicacion": "Baño",
        "descripcion": DESCRIPCION,
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": "EJ07",
        "proveedor_nombre": NOMBRE_PROVEEDOR,
        "proveedor_ambiguo": False,
        "urgencia": None,
        "listado": None,
        "duplicada_de": None,
        "creada_at_utc": CREADA,
    }
    base.update(cambios)
    return IncidenciaEnBandeja(**base)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# El catálogo de Sigrid de la obra 9901
# --------------------------------------------------------------------------


def filas_de_unidades(obra_ref: str = OBRA_REF) -> tuple[FilaUnidadCatalogo, ...]:
    return tuple(
        FilaUnidadCatalogo(
            obra_ref=obra_ref,
            obra_codigo=OBRA,
            obra_nombre="Promoción Ejemplo",
            unidad_codigo=codigo,
            unidad_nombre=nombre,
        )
        for codigo, nombre in (
            (U1, NOMBRE_U1),
            (U2, None),
            (U3, "Villa Ejemplo Tres"),
        )
    )


def filas_de_oficios() -> tuple[FilaOficioCatalogo, ...]:
    return (
        FilaOficioCatalogo("0046", "Carpintería de madera", "EJ07", NOMBRE_PROVEEDOR),
        FilaOficioCatalogo("0046", "Carpintería de madera", "EJ07", "Otro nombre, S.L."),
        FilaOficioCatalogo("0143", "Carpinteria de madera", "EJ08", "Maderas Ejemplo, S.A."),
        FilaOficioCatalogo("0200", None, None, None),
    )


class CatalogoDeLaObra:
    """Un `CatalogoObraPort` de mentira: la obra 9901, y anota cada lectura."""

    def __init__(
        self,
        llamadas: list[str],
        *,
        unidades: tuple[FilaUnidadCatalogo, ...] | None = None,
        oficios: tuple[FilaOficioCatalogo, ...] | None = None,
        al_techo: bool = False,
        fallo: Exception | None = None,
    ) -> None:
        self.llamadas = llamadas
        self._unidades = filas_de_unidades() if unidades is None else unidades
        self._oficios = filas_de_oficios() if oficios is None else oficios
        self._al_techo = al_techo
        self._fallo = fallo
        self.obras_pedidas: list[str] = []

    def leer_unidades(self, *, codigo_obra: str) -> LecturaCatalogo[FilaUnidadCatalogo]:
        self.llamadas.append("catalogo.leer_unidades")
        self.obras_pedidas.append(codigo_obra)
        if self._fallo is not None:
            raise self._fallo
        return LecturaCatalogo(self._unidades, self._al_techo)

    def leer_oficios(self, *, obra_ref: str) -> LecturaCatalogo[FilaOficioCatalogo]:
        self.llamadas.append("catalogo.leer_oficios")
        return LecturaCatalogo(self._oficios, False)


class UbicacionesQueCuentan:
    """La fuente de las ubicaciones válidas: un mapa por unidad, y anota cada lectura."""

    def __init__(
        self,
        llamadas: list[str],
        mapa: Mapping[str, tuple[str, ...]] | None = None,
        *,
        fallo: Exception | None = None,
    ) -> None:
        self.llamadas = llamadas
        self.mapa = dict(UBICACIONES if mapa is None else mapa)
        self._fallo = fallo
        self.catalogos: list[CatalogoObra] = []

    def __call__(self, catalogo: CatalogoObra) -> Mapping[str, tuple[str, ...]]:
        self.llamadas.append("ubicaciones")
        self.catalogos.append(catalogo)
        if self._fallo is not None:
            raise self._fallo
        return self.mapa


def prohibido(que: str) -> Callable[..., object]:
    """Un constructor o una lectura que falla si se llega a llamar."""

    def _falla(*_args: object, **_kwargs: object) -> object:
        raise AssertionError(f"no se tenía que llamar a {que}")

    return _falla


class Prohibido:
    """Un puerto cuyo cualquier método falla si se llama."""

    def __init__(self, que: str) -> None:
        self._que = que

    def __getattr__(self, nombre: str) -> Callable[..., object]:
        return prohibido(f"{self._que}.{nombre}")


# --------------------------------------------------------------------------
# La revisión, en memoria
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Guardada:
    """Una fila de `revisiones_bandeja`: la revisión leída y el `oid` aparte."""

    revision: Revision
    oid: str


class RevisionEnMemoria:
    """Un `RevisionPort` en memoria con la semántica de la base (§5)."""

    def __init__(
        self,
        llamadas: list[str],
        incidencias: tuple[IncidenciaEnBandeja, ...] = (),
        *,
        obra: str = OBRA,
        origen: OrigenIncidencia = OrigenIncidencia.EXCEL,
        fallo: Exception | None = None,
    ) -> None:
        self.llamadas = llamadas
        self._incidencias: dict[UUID, IncidenciaEnBandeja] = {
            i.incidencia_id: i for i in incidencias
        }
        self._obra = obra
        self._origen = origen
        self._fallo = fallo
        self.guardadas: list[Guardada] = []
        self.registros: list[tuple[RevisionNueva, dict[UUID, int | None]]] = []
        self.topes: list[int] = []
        self.total_para_contar: int | None = None
        self.listar_devuelve: tuple[SituacionDeRevision, ...] | None = None
        #: Lo que hace «otra persona» justo antes de que esta registre (R7).
        self.antes_de_registrar: Callable[[], None] | None = None

    # -- lo que se siembra -------------------------------------------------

    def anadir(self, incidencia: IncidenciaEnBandeja) -> None:
        self._incidencias[incidencia.incidencia_id] = incidencia

    def sembrar(
        self,
        incidencia_id: UUID,
        accion,
        valores,
        *,
        motivo: str | None = None,
        correo: str = CORREO,
        oid: str = OID,
        cuando: datetime = AHORA,
    ) -> int:
        """Una revisión ya guardada, como si la hubiera hecho alguien antes."""
        from domain.models.revision import huella_de_valores

        revision_id = len(self.guardadas) + 1
        self.guardadas.append(
            Guardada(
                Revision(
                    revision_id=revision_id,
                    incidencia_id=incidencia_id,
                    accion=accion,
                    valores=valores,
                    huella=huella_de_valores(valores),
                    motivo=motivo,
                    correo=correo,
                    revisado_at_utc=cuando,
                ),
                oid,
            )
        )
        return revision_id

    # -- lo que lee la base ------------------------------------------------

    def _ultima(self, incidencia_id: UUID) -> Revision | None:
        suyas = [g.revision for g in self.guardadas if g.revision.incidencia_id == incidencia_id]
        return max(suyas, key=lambda r: r.revision_id) if suyas else None

    def _situacion(self, incidencia_id: UUID, *, con_original: bool = True) -> SituacionDeRevision:
        incidencia = self._incidencias[incidencia_id]
        original = None
        if con_original and incidencia.duplicada_de in self._incidencias:
            original = self._situacion(incidencia.duplicada_de, con_original=False)  # type: ignore[arg-type]
        return SituacionDeRevision(
            incidencia=incidencia,
            obra_codigo=self._obra,
            origen=self._origen,
            ultima=self._ultima(incidencia_id),
            original=original,
        )

    def _fallar(self) -> None:
        if self._fallo is not None:
            raise self._fallo

    # -- el puerto ---------------------------------------------------------

    def listar(self, *, obra_codigo: str, tope: int) -> tuple[SituacionDeRevision, ...]:
        self.llamadas.append("revision.listar")
        self.topes.append(tope)
        self._fallar()
        if self.listar_devuelve is not None:
            return self.listar_devuelve
        if obra_codigo != self._obra:
            return ()
        return tuple(self._situacion(i) for i in self._incidencias)[: tope + 1]

    def contar(self, *, obra_codigo: str) -> int:
        self.llamadas.append("revision.contar")
        self._fallar()
        if self.total_para_contar is not None:
            return self.total_para_contar
        return len(self._incidencias) if obra_codigo == self._obra else 0

    def situacion(self, *, incidencia_id: UUID) -> SituacionDeRevision | None:
        self.llamadas.append("revision.situacion")
        self._fallar()
        if incidencia_id not in self._incidencias:
            return None
        return self._situacion(incidencia_id)

    def registrar(
        self, *, revision: RevisionNueva, esperadas: Mapping[UUID, int | None]
    ) -> int:
        self.llamadas.append("revision.registrar")
        self._fallar()
        if self.antes_de_registrar is not None:
            self.antes_de_registrar()
        self.registros.append((revision, dict(esperadas)))
        for incidencia_id, esperada in esperadas.items():
            ultima = self._ultima(incidencia_id)
            if (None if ultima is None else ultima.revision_id) != esperada:
                raise RevisionDesactualizada("otra persona ha revisado antes")
        revision_id = len(self.guardadas) + 1
        self.guardadas.append(
            Guardada(
                Revision(
                    revision_id=revision_id,
                    incidencia_id=revision.incidencia_id,
                    accion=revision.accion,
                    valores=revision.valores,
                    huella=revision.huella,
                    motivo=revision.motivo,
                    correo=revision.quien.correo,
                    revisado_at_utc=revision.revisado_at_utc,
                ),
                revision.quien.oid,
            )
        )
        return revision_id

    def historial(
        self, *, incidencia_id: UUID
    ) -> tuple[SituacionDeRevision, tuple[Revision, ...]] | None:
        self.llamadas.append("revision.historial")
        self._fallar()
        if incidencia_id not in self._incidencias:
            return None
        suyas = tuple(
            sorted(
                (g.revision for g in self.guardadas if g.revision.incidencia_id == incidencia_id),
                key=lambda r: r.revision_id,
            )
        )
        return self._situacion(incidencia_id), suyas

    def aprobadas(self, *, obra_codigo: str) -> tuple[CandidataAlVolcado, ...]:
        self.llamadas.append("revision.aprobadas")
        self._fallar()
        if obra_codigo != self._obra:
            return ()
        situaciones = (self._situacion(i) for i in self._incidencias)
        return tuple(candidata_de(s) for s in situaciones if es_candidata(s))


def con_urgencia(inc: IncidenciaEnBandeja) -> IncidenciaEnBandeja:
    """La misma incidencia con urgencia y listado, para los campos tasados."""
    return replace(inc, urgencia=Urgencia.URGENTE, listado=Listado.PRIMERO)
