# services/postventa-api/tests/test_f065_aplicacion.py
"""La aplicación de las reclamaciones de Sigrid en la revisión (F-065, T7; R3, R4, R8, R9).

`specs/F-065-revision-sigrid-backend/design.md` §10.3: `mirar_sigrid` orquesta,
en este orden, **una** lectura de la base (`RevisionPort.listar` con el tope de
F-056) → el tope (`BandejaDemasiadoGrande` con `contar`, sin Sigrid) → **una**
lectura de Sigrid (`ReclamacionesObraPort.leer`) → el techo o `truncated`
(`ReclamacionesSinVerificar`, sin cruzar) → las obras (`ObraAmbigua`) →
`cruzar` del dominio.

| Caso | Requisito |
|---|---|
| una lectura de la base y como mucho una de Sigrid, en ese orden, y ninguna otra operación | R3 |
| la bandeja pasa de 10.000 → 409 con el recuento, sin leer Sigrid; justo 10.000 sí lee | R4 |
| al techo o `truncated` → 409 con las filas, **sin cruzar**; el fallo de Sigrid sube tal cual | R8 |
| dos `obra_ref` → `obra_ambigua`, sin cruzar; cero filas → vista vacía; el techo va antes | R9 |
| el paso de la fila del puerto a la reclamación del dominio, y el cruce, el del dominio | R10–R19 (la costura) |
| ningún mensaje de error lleva nada de una fila | R22, R40 |

Los dobles y los datos de este fichero los usan también `test_f065_http.py` y
`test_f065_datos_personales.py` (sin un fichero de utilidades más: §9.1).
Datos inventados (R39): obra `9901`, unidades `VILLA 05`…, códigos `RS…` de
los ejemplos ficticios de §5.4, textos «Ejemplo …», teléfonos `000 000 00n`,
correos `@ejemplo.invalid`; los identificadores, `UUID(int=n)`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import fields
from datetime import date
from typing import Any
from uuid import UUID

import pytest
from domain.models.errores import (
    BandejaDemasiadoGrande,
    CatalogoNoDisponible,
    ObraAmbigua,
    PersistenciaNoDisponible,
)
from domain.models.revision import TOPE_LECTURA_OBRA, SituacionDeRevision
from domain.models.sigrid_bandeja import ReclamacionSigrid, cruzar
from domain.ports.catalogo_obra import LecturaCatalogo
from domain.ports.reclamaciones_obra import FichaReclamacion, FilaReclamacionObra

from tests.test_f065_dominio import OFICIO, U, pvi, sit
from tests.utiles_revision import RevisionEnMemoria, prohibido

OBRA = "9901"
TIP = 708
#: `upv.obride` inventados: nunca salen de la aplicación (R6, R22).
OBRA_REF = "7000123"
OTRA_OBRA_REF = "7000456"


# --------------------------------------------------------------------------
# Los datos: filas del puerto con la ficha de R33 entera, inventada
# --------------------------------------------------------------------------


def ficha(n: int = 1) -> FichaReclamacion:
    """Una ficha con **todos** los campos de R33 rellenos y reconocibles."""
    return FichaReclamacion(
        descripcion_larga=f"Ejemplo descripcion larga secreta {n}",
        motivo=f"Ejemplo motivo secreto {n}",
        urgencia=f"Ejemplo urgencia secreta {n}",
        forma_comunicacion=2,
        fecha_prevista=date(2026, 11, 3),
        solucion=f"Ejemplo solucion secreta {n}",
        clase_codigo="CL1",
        clase_nombre=f"Ejemplo clase secreta {n}",
        telefonos_avisos=f"000 000 1{n:02d}",
        correo_avisos=f"avisos{n}@ejemplo.invalid",
        propietario=f"Ejemplo Propietario Secreto {n}",
        reclama_nombre=f"Ejemplo Reclamante Secreto {n}",
        reclama_telefono=f"000 000 2{n:02d}",
        reclama_telefono2=f"000 000 3{n:02d}",
        reclama_correo=f"reclama{n}@ejemplo.invalid",
        contacto_nombre=f"Ejemplo Contacto Secreto {n}",
        contacto_telefono=f"000 000 4{n:02d}",
        contacto_telefono2=f"000 000 5{n:02d}",
        contacto_correo=f"contacto{n}@ejemplo.invalid",
    )


def valores_de_la_ficha(f: FichaReclamacion) -> list[str]:
    """Los valores de texto de una ficha: ninguno puede ir a un log (R38)."""
    return [str(getattr(f, c.name)) for c in fields(f) if isinstance(getattr(f, c.name), str)]


def fila(
    cod: str,
    estado: str | None = "SAT",
    *,
    fecha: date | None = date(2026, 9, 15),
    unidad: str | None = U,
    ubicacion: str | None = "Cocina",
    oficio: str | None = OFICIO,
    descripcion: str | None = "Fuga bajo el fregadero",
    referencia: str | None = None,
    obra_ref: str = OBRA_REF,
    n: int = 1,
) -> FilaReclamacionObra:
    """Una fila del puerto (las 31 columnas de §3 ya mapeadas), inventada."""
    return FilaReclamacionObra(
        obra_ref=obra_ref,
        cod=cod,
        estado_codigo=estado,
        fecha=fecha,
        unidad_codigo=unidad,
        oficio_codigo=oficio,
        oficio_nombre=None if oficio is None else "Fontaneria Ejemplo",
        tipo_codigo="GAR",
        tipo_nombre="Ejemplo de tipo",
        ubicacion=ubicacion,
        descripcion=descripcion,
        referencia=referencia,
        ficha=ficha(n),
    )


def obra_de_ejemplo() -> tuple[tuple[SituacionDeRevision, ...], tuple[FilaReclamacionObra, ...]]:
    """Una bandeja y una obra de Sigrid que dan **los siete** tipos de hallazgo.

    Sobre los ejemplos ficticios de §5.4:

    - 1 `nueva` · Cocina · 0039 · «Gotea el grifo» frente a `RS26.09/0123`
      (`PTE`, E1) → `coincide` de conflicto; frente a `RS23.06/0300` (`CER`, E4)
      → `coincide` de aviso;
    - 2 `volcada` como `RS26.10/0090` y nada con `PVI-<2>` (E13) →
      `volcada_no_encontrada`;
    - 3 `volcada` como `RS26.10/0074`, con `PVI-<3>` en `RS26.10/0080` →
      `codigo_distinto`; y esa en `NPR` → `anulada_en_sigrid`;
    - 4 `en_duda`, con `PVI-<4>` en `RS26.10/0081` (`SAT`, E7) →
      `ya_en_sigrid`;
    - 5 `aprobada`, con `PVI-<5>` en `RS26.10/0082` y `RS26.10/0083` →
      `varias_en_sigrid`;
    - `RS26.09/0439` con `PVI-PRUEBA-0001` (E8) → `referencia_desconocida`;
    - y `RS26.08/0001` sin fecha, `RS26.08/0002` con un estado desconocido y
      `RS26.09/0200` en `NPR` (E5), que no dan pares.
    """
    situaciones = (
        sit(1, "nueva"),
        sit(2, "volcada", volcada_como="RS26.10/0090", ubicacion="Terraza", descripcion="Ejemplo de otra cosa"),
        sit(3, "volcada", volcada_como="RS26.10/0074", ubicacion="Terraza", descripcion="Ejemplo de otra cosa"),
        sit(4, "en_duda", ubicacion="Terraza", descripcion="Ejemplo de otra cosa"),
        sit(5, "aprobada", ubicacion="Terraza", descripcion="Ejemplo de otra cosa"),
    )
    filas = (
        fila("RS26.09/0123", "PTE", n=1),
        fila("RS23.06/0300", "CER", fecha=date(2023, 6, 1), n=2),
        fila("RS26.10/0080", "NPR", ubicacion="Patio", descripcion="Ejemplo ajeno", referencia=pvi(3), n=3),
        fila("RS26.10/0081", "SAT", ubicacion="Patio", descripcion="Ejemplo ajeno", referencia=pvi(4), n=4),
        fila("RS26.10/0082", "SAT", ubicacion="Patio", descripcion="Ejemplo ajeno", referencia=pvi(5), n=5),
        fila("RS26.10/0083", "SAT", ubicacion="Patio", descripcion="Ejemplo ajeno", referencia=pvi(5), n=6),
        fila("RS26.09/0439", "SAT", ubicacion="Patio", descripcion="Ejemplo ajeno", referencia="PVI-PRUEBA-0001", n=7),
        fila("RS26.08/0001", "TER", fecha=None, ubicacion="Patio", descripcion="Ejemplo ajeno", n=8),
        fila("RS26.08/0002", "XYZ", ubicacion="Patio", descripcion="Ejemplo ajeno", n=9),
        fila("RS26.09/0200", "NPR", n=10),
    )
    return situaciones, filas


# --------------------------------------------------------------------------
# Los dobles
# --------------------------------------------------------------------------


class LectorDeReclamaciones:
    """Un `ReclamacionesObraPort` de mentira: devuelve lo que se le dé y anota cada lectura."""

    def __init__(
        self,
        llamadas: list[str],
        filas: tuple[FilaReclamacionObra, ...] = (),
        *,
        al_techo: bool = False,
        fallo: Exception | None = None,
    ) -> None:
        self.llamadas = llamadas
        self.filas = filas
        self.al_techo = al_techo
        self.fallo = fallo
        self.pedidas: list[dict[str, Any]] = []

    def leer(self, *, codigo_obra: str, tip: int) -> LecturaCatalogo[FilaReclamacionObra]:
        self.llamadas.append("sigrid.leer")
        self.pedidas.append({"codigo_obra": codigo_obra, "tip": tip})
        if self.fallo is not None:
            raise self.fallo
        return LecturaCatalogo(self.filas, self.al_techo)


class BandejaSoloLectura:
    """El `RevisionPort` de la ruta: `listar` y `contar`, y **nada más** (R3, R37).

    Cualquier otra operación —`registrar`, `registrar_lote`, `situacion`,
    `historial`, `aprobadas`— falla si se llama: la ruta no escribe nada en
    la base ni hace ninguna otra lectura.
    """

    def __init__(
        self,
        llamadas: list[str],
        situaciones: tuple[SituacionDeRevision, ...] = (),
        *,
        total: int | None = None,
        fallo: Exception | None = None,
    ) -> None:
        self._memoria = RevisionEnMemoria(llamadas, fallo=fallo)
        self._memoria.listar_devuelve = situaciones
        self._memoria.total_para_contar = total

    @property
    def topes(self) -> list[int]:
        return self._memoria.topes

    def listar(self, *, obra_codigo: str, tope: int) -> tuple[SituacionDeRevision, ...]:
        return self._memoria.listar(obra_codigo=obra_codigo, tope=tope)

    def contar(self, *, obra_codigo: str) -> int:
        return self._memoria.contar(obra_codigo=obra_codigo)

    def __getattr__(self, nombre: str) -> Callable[..., object]:
        return prohibido(f"revision.{nombre}")


def _mirar(
    revision: BandejaSoloLectura, lector: LectorDeReclamaciones, *, obra: str = OBRA, tip: int = TIP
):
    from application.pipelines.sigrid_bandeja import mirar_sigrid

    return mirar_sigrid(obra, revision=revision, reclamaciones=lector, tip=tip)


def _mundo(
    situaciones: tuple[SituacionDeRevision, ...] = (),
    filas: tuple[FilaReclamacionObra, ...] = (),
    **lector: Any,
) -> tuple[list[str], BandejaSoloLectura, LectorDeReclamaciones]:
    llamadas: list[str] = []
    return (
        llamadas,
        BandejaSoloLectura(llamadas, situaciones),
        LectorDeReclamaciones(llamadas, filas, **lector),
    )


# ==========================================================================
# R3 · una lectura de la base y como mucho una de Sigrid, en ese orden
# ==========================================================================


def test_f065_r3_una_lectura_de_la_base_y_una_de_sigrid_en_ese_orden() -> None:
    situaciones, filas = obra_de_ejemplo()
    llamadas, revision, lector = _mundo(situaciones, filas)

    _mirar(revision, lector)

    assert llamadas == ["revision.listar", "sigrid.leer"]
    assert revision.topes == [TOPE_LECTURA_OBRA]
    assert lector.pedidas == [{"codigo_obra": OBRA, "tip": TIP}]


def test_f065_r3_el_tipo_de_concepto_es_el_que_se_le_pasa() -> None:
    _, revision, lector = _mundo()

    _mirar(revision, lector, tip=999)

    assert lector.pedidas == [{"codigo_obra": OBRA, "tip": 999}]


def test_f065_r3_la_bandeja_vacia_tambien_lee_sigrid_una_vez() -> None:
    """Sin incidencias, las reclamaciones se listan igual (Q-2: todas)."""
    _, filas = obra_de_ejemplo()
    llamadas, revision, lector = _mundo((), filas)

    vista = _mirar(revision, lector)

    assert llamadas == ["revision.listar", "sigrid.leer"]
    assert len(vista.cruce.reclamaciones) == len(filas)


def test_f065_r3_si_la_base_falla_no_se_lee_sigrid() -> None:
    llamadas: list[str] = []
    revision = BandejaSoloLectura(llamadas, fallo=PersistenciaNoDisponible("la base no responde"))
    lector = LectorDeReclamaciones(llamadas)

    with pytest.raises(PersistenciaNoDisponible):
        _mirar(revision, lector)

    assert llamadas == ["revision.listar"]


def test_f065_r3_el_doble_de_la_bandeja_no_deja_hacer_nada_mas() -> None:
    """Control no ciego del doble: cualquier otra operación del puerto falla."""
    revision = BandejaSoloLectura([])

    for operacion in ("registrar", "registrar_lote", "situacion", "historial", "aprobadas"):
        with pytest.raises(AssertionError, match="no se tenía que llamar"):
            getattr(revision, operacion)()


# ==========================================================================
# R4 · la bandeja demasiado grande: 409 con el recuento, sin leer Sigrid
# ==========================================================================


def test_f065_r4_mas_de_diez_mil_es_409_con_el_recuento_y_sin_sigrid() -> None:
    llamadas: list[str] = []
    una = sit(1)
    revision = BandejaSoloLectura(llamadas, (una,) * (TOPE_LECTURA_OBRA + 1), total=12_345)
    lector = LectorDeReclamaciones(llamadas, obra_de_ejemplo()[1])

    with pytest.raises(BandejaDemasiadoGrande) as error:
        _mirar(revision, lector)

    assert error.value.total == 12_345
    assert "12345" in error.value.motivo
    assert llamadas == ["revision.listar", "revision.contar"]
    assert lector.pedidas == []


def test_f065_r4_justo_diez_mil_no_es_demasiado() -> None:
    llamadas: list[str] = []
    revision = BandejaSoloLectura(llamadas, (sit(1),) * TOPE_LECTURA_OBRA)
    lector = LectorDeReclamaciones(llamadas)

    _mirar(revision, lector)

    assert llamadas == ["revision.listar", "sigrid.leer"]


# ==========================================================================
# R8 · al techo o `truncated`: 409, sin cruzar nada
# ==========================================================================


def test_f065_r8_al_techo_es_409_con_las_filas_y_sin_cruzar(monkeypatch) -> None:
    from application.pipelines import sigrid_bandeja as modulo
    from domain.models.errores import ReclamacionesSinVerificar

    situaciones, filas = obra_de_ejemplo()
    _, revision, lector = _mundo(situaciones, filas, al_techo=True)
    monkeypatch.setattr(modulo, "cruzar", prohibido("cruzar"))

    with pytest.raises(ReclamacionesSinVerificar) as error:
        _mirar(revision, lector)

    assert error.value.filas == len(filas)
    assert str(len(filas)) in error.value.motivo


def test_f065_r8_con_cero_filas_y_la_marca_tambien_es_409(monkeypatch) -> None:
    """`llego_al_techo` es «filas ≥ tope **o** `truncated`» (adaptador): la marca manda."""
    from application.pipelines import sigrid_bandeja as modulo
    from domain.models.errores import ReclamacionesSinVerificar

    _, revision, lector = _mundo((sit(1),), (), al_techo=True)
    monkeypatch.setattr(modulo, "cruzar", prohibido("cruzar"))

    with pytest.raises(ReclamacionesSinVerificar) as error:
        _mirar(revision, lector)

    assert error.value.filas == 0


def test_f065_r8_el_techo_va_antes_que_la_obra_ambigua(monkeypatch) -> None:
    from domain.models.errores import ReclamacionesSinVerificar

    filas = (fila("RS26.09/0123"), fila("RS26.09/0124", obra_ref=OTRA_OBRA_REF))
    _, revision, lector = _mundo((sit(1),), filas, al_techo=True)

    with pytest.raises(ReclamacionesSinVerificar):
        _mirar(revision, lector)


def test_f065_r8_el_fallo_de_sigrid_sube_tal_cual_y_sin_nada_a_medias() -> None:
    fallo = CatalogoNoDisponible("no se ha podido leer las reclamaciones de la obra en Sigrid: Timeout")
    llamadas, revision, lector = _mundo((sit(1),), fallo=fallo)

    with pytest.raises(CatalogoNoDisponible) as error:
        _mirar(revision, lector)

    assert error.value is fallo
    assert llamadas == ["revision.listar", "sigrid.leer"]


def test_f065_r8_reclamaciones_sin_verificar_es_un_error_de_dominio_con_las_filas() -> None:
    from domain.models import errores
    from domain.models.errores import ReclamacionesSinVerificar

    error = ReclamacionesSinVerificar("Ejemplo de motivo", filas=7)

    assert isinstance(error, Exception)
    assert error.motivo == "Ejemplo de motivo"
    assert error.filas == 7
    assert str(error) == "Ejemplo de motivo"
    assert ReclamacionesSinVerificar.__module__ == errores.__name__


# ==========================================================================
# R9 · más de una obra: `obra_ambigua`; ninguna fila: vista vacía
# ==========================================================================


def test_f065_r9_dos_obras_es_obra_ambigua_sin_cruzar(monkeypatch) -> None:
    from application.pipelines import sigrid_bandeja as modulo

    filas = (fila("RS26.09/0123"), fila("RS26.09/0124", obra_ref=OTRA_OBRA_REF))
    _, revision, lector = _mundo((sit(1),), filas)
    monkeypatch.setattr(modulo, "cruzar", prohibido("cruzar"))

    with pytest.raises(ObraAmbigua) as error:
        _mirar(revision, lector)

    assert OBRA in error.value.motivo
    assert "2" in error.value.motivo


def test_f065_r9_muchas_filas_de_una_sola_obra_no_es_ambigua() -> None:
    _, filas = obra_de_ejemplo()
    assert len({f.obra_ref for f in filas}) == 1
    _, revision, lector = _mundo((sit(1),), filas)

    vista = _mirar(revision, lector)

    assert len(vista.cruce.reclamaciones) == len(filas)


def test_f065_r9_cero_filas_es_una_vista_vacia_y_no_un_error() -> None:
    situaciones = (sit(1), sit(2, "volcada", volcada_como="RS26.10/0090"))
    _, revision, lector = _mundo(situaciones, ())

    vista = _mirar(revision, lector)

    assert vista.obra_codigo == OBRA
    assert vista.cruce.reclamaciones == ()
    # Sin reclamaciones, la `volcada` no se encuentra: el cruce se hace igual.
    assert [h.tipo.value for h in vista.cruce.hallazgos] == ["volcada_no_encontrada"]


# ==========================================================================
# La costura con el dominio: la fila del puerto → la reclamación; el cruce
# ==========================================================================


def test_f065_r19_la_vista_no_se_puede_cambiar_despues_de_cruzar() -> None:
    """Lo que el borde serializa es lo que se cruzó: nadie lo reescribe por el camino."""
    import dataclasses

    _, revision, lector = _mundo(*obra_de_ejemplo())
    vista = _mirar(revision, lector)

    with pytest.raises(dataclasses.FrozenInstanceError):
        vista.situaciones = ()  # type: ignore[misc]


def test_f065_r19_la_vista_lleva_la_bandeja_entera_y_el_cruce_del_dominio() -> None:
    situaciones, filas = obra_de_ejemplo()
    _, revision, lector = _mundo(situaciones, filas)

    vista = _mirar(revision, lector)

    assert vista.situaciones == situaciones
    esperado = cruzar(
        situaciones,
        [
            ReclamacionSigrid(
                cod=f.cod,
                estado=f.estado_codigo,
                fecha=f.fecha,
                unidad_codigo=f.unidad_codigo,
                ubicacion=f.ubicacion,
                oficio_codigo=f.oficio_codigo,
                oficio_nombre=f.oficio_nombre,
                tipo_codigo=f.tipo_codigo,
                tipo_nombre=f.tipo_nombre,
                descripcion=f.descripcion,
                referencia=f.referencia,
                ficha=f.ficha,
            )
            for f in filas
        ],
    )
    assert vista.cruce == esperado
    assert {h.tipo.value for h in vista.cruce.hallazgos} == {
        "coincide",
        "ya_en_sigrid",
        "varias_en_sigrid",
        "volcada_no_encontrada",
        "codigo_distinto",
        "anulada_en_sigrid",
        "referencia_desconocida",
    }


def test_f065_r6_cada_campo_de_la_fila_pasa_a_la_reclamacion_y_la_ficha_es_la_misma() -> None:
    """Ningún campo se pierde ni se cruza con otro; `obra_ref` no pasa (R6, R22)."""
    original = fila(
        "RS26.09/0123",
        "PTE",
        fecha=date(2026, 9, 1),
        unidad="VILLA 07",
        ubicacion="Ejemplo ubicacion",
        oficio="0040",
        descripcion="Ejemplo descripcion",
        referencia=pvi(77),
    )
    _, revision, lector = _mundo((), (original,))

    (reclamacion, emparejada), = _mirar(revision, lector).cruce.reclamaciones

    assert emparejada is None
    assert reclamacion == ReclamacionSigrid(
        cod="RS26.09/0123",
        estado="PTE",
        fecha=date(2026, 9, 1),
        unidad_codigo="VILLA 07",
        ubicacion="Ejemplo ubicacion",
        oficio_codigo="0040",
        oficio_nombre="Fontaneria Ejemplo",
        tipo_codigo="GAR",
        tipo_nombre="Ejemplo de tipo",
        descripcion="Ejemplo descripcion",
        referencia=pvi(77),
        ficha=original.ficha,
    )
    assert reclamacion.ficha is original.ficha
    assert not hasattr(reclamacion, "obra_ref")


def test_f065_r10_la_referencia_empareja_con_la_bandeja_de_la_obra() -> None:
    situaciones, filas = obra_de_ejemplo()
    _, revision, lector = _mundo(situaciones, filas)

    cruce = _mirar(revision, lector).cruce

    emparejadas = {r.cod: uid for r, uid in cruce.reclamaciones if uid is not None}
    assert emparejadas == {
        "RS26.10/0080": UUID(int=3),
        "RS26.10/0081": UUID(int=4),
        "RS26.10/0083": UUID(int=5),
    }


# ==========================================================================
# R22, R40 · ningún mensaje de error lleva nada de una fila
# ==========================================================================


def test_f065_r22_r40_los_errores_no_repiten_ninguna_fila() -> None:
    from domain.models.errores import ReclamacionesSinVerificar

    situaciones, filas = obra_de_ejemplo()
    prohibidos = {OBRA_REF, OTRA_OBRA_REF}
    for f in filas:
        prohibidos.update({f.cod, f.descripcion or "", f.ubicacion or "", f.referencia or ""})
        prohibidos.update(valores_de_la_ficha(f.ficha))
    prohibidos.discard("")

    mensajes = []
    _, revision, lector = _mundo(situaciones, filas, al_techo=True)
    with pytest.raises(ReclamacionesSinVerificar) as techo:
        _mirar(revision, lector)
    mensajes.append(techo.value.motivo)

    dos_obras = (*filas, fila("RS26.09/0999", obra_ref=OTRA_OBRA_REF))
    _, revision, lector = _mundo(situaciones, dos_obras)
    with pytest.raises(ObraAmbigua) as ambigua:
        _mirar(revision, lector)
    mensajes.append(ambigua.value.motivo)

    for mensaje in mensajes:
        assert [p for p in prohibidos if p in mensaje] == [], mensaje
