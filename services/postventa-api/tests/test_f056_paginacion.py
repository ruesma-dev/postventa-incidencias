# services/postventa-api/tests/test_f056_paginacion.py
"""El orden, el cursor, la paginación y el resumen de la revisión (F-056 T1).

`domain/models/revision.py` (`design.md` §4, §7; R23, R25–R27). Puro.

| Caso | Requisito |
|---|---|
| `clave_de_orden`: fecha descendente, fila ascendente (sin fila al final), id | R25 |
| `texto_de_clave` / `clave_de_texto`: ida y vuelta; JSON compacto y canónico (el base64url del cursor lo pone el borde: decisión del humano 2026-10-07) | R25 |
| clave manipulada → `PeticionDeRevisionInvalida`, sin repetirla | R23, R25 |
| `paginar`: recorrer todas las páginas da cada fila una vez y en orden, con empates de fecha y filas sin `fila_origen` | R25 |
| filtros `estado` y `con_motivos` en el servidor; `total_filtrado` | R26 |
| `tamano` de 1 a 200 | R23 |
| `resumen` sobre todas, con `por_estado` y `por_motivo` | R27 |
| `fila_de_revision`: estado, motivos y cambios con las mismas funciones | R26, R29 |

Datos ficticios: obra `9901`; identificadores `UUID(int=n)`.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest
from domain.models.errores import PeticionDeRevisionInvalida
from domain.models.importacion import IncidenciaEnBandeja
from domain.models.plantilla_incidencias import (
    CatalogoObra,
    OficioObra,
    OrigenIncidencia,
    ProveedorEnObra,
    UnidadPosventa,
)
from domain.models.revision import (
    MAX_TEXTO_CLAVE,
    TAMANO_MAXIMO,
    TAMANO_POR_DEFECTO,
    TOPE_LECTURA_OBRA,
    AccionRevision,
    ClaveDeOrden,
    EstadoRevision,
    FilaDeRevision,
    FiltroEstado,
    MotivoNoAprobable,
    Revision,
    SituacionDeRevision,
    clave_de_texto,
    clave_de_orden,
    fila_de_revision,
    huella_de_valores,
    paginar,
    resumen,
    texto_de_clave,
    valores_importados,
)

E = EstadoRevision
M = MotivoNoAprobable
OBRA = "9901"
U1 = "9901.03VILLA 1."
T0 = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
AHORA = datetime(2026, 10, 6, 9, 30, tzinfo=UTC)


def incidencia(
    n: int, *, creada: datetime = T0, fila: int | None = None, **cambios: object
) -> IncidenciaEnBandeja:
    base: dict[str, object] = {
        "incidencia_id": UUID(int=n),
        "importacion_id": UUID(int=1000),
        "fila_origen": fila,
        "unidad_codigo": U1,
        "unidad_nombre": "Villa Ejemplo 1",
        "ubicacion": "Baño",
        "descripcion": f"Ejemplo {n}",
        "detalle": None,
        "oficio_codigo": "0046",
        "oficio_nombre": "Carpintería de madera",
        "oficio_ambiguo": False,
        "proveedor_codigo": None,
        "proveedor_nombre": None,
        "proveedor_ambiguo": False,
        "urgencia": None,
        "listado": None,
        "duplicada_de": None,
        "creada_at_utc": creada,
    }
    base.update(cambios)
    return IncidenciaEnBandeja(**base)  # type: ignore[arg-type]


def situacion(
    inc: IncidenciaEnBandeja, ultima: Revision | None = None
) -> SituacionDeRevision:
    return SituacionDeRevision(
        incidencia=inc,
        obra_codigo=OBRA,
        origen=OrigenIncidencia.EXCEL,
        ultima=ultima,
        original=None,
    )


def fila(
    n: int,
    *,
    creada: datetime = T0,
    fila_origen: int | None = None,
    estado: EstadoRevision = E.NUEVA,
    motivos: tuple[MotivoNoAprobable, ...] = (),
) -> FilaDeRevision:
    return FilaDeRevision(
        situacion=situacion(incidencia(n, creada=creada, fila=fila_origen)),
        estado=estado,
        motivos=motivos,
        cambios=(),
    )


def ids(filas: tuple[FilaDeRevision, ...] | list[FilaDeRevision]) -> list[int]:
    return [f.situacion.incidencia.incidencia_id.int for f in filas]


def _mezcla() -> list[FilaDeRevision]:
    """23 filas con empates de fecha, filas sin `fila_origen` y ids desordenados."""
    t1, t2, t3 = T0, T0 + timedelta(hours=1), T0 + timedelta(microseconds=1)
    filas = []
    n = 0
    for creada in (t1, t2, t3):
        for fila_origen in (None, 7, 2, None, 2, 30, 9, 2):
            n += 1
            if creada is t3 and n % 8 == 0:
                continue
            filas.append(fila(100 - n, creada=creada, fila_origen=fila_origen))
    return filas


def _clave_esperada(f: FilaDeRevision) -> tuple[object, ...]:
    inc = f.situacion.incidencia
    epoca = datetime(1970, 1, 1, tzinfo=UTC)
    return (
        -((inc.creada_at_utc - epoca) // timedelta(microseconds=1)),
        inc.fila_origen is None,
        inc.fila_origen or 0,
        inc.incidencia_id.int,
    )


# --------------------------------------------------------------------------
# Constantes y enumeraciones
# --------------------------------------------------------------------------


def test_f056_r23_r24_constantes() -> None:
    assert (TAMANO_POR_DEFECTO, TAMANO_MAXIMO, TOPE_LECTURA_OBRA) == (100, 200, 10_000)


def test_f056_r23_filtros_de_estado() -> None:
    assert [f.value for f in FiltroEstado] == [
        "activas",
        "todas",
        "nueva",
        "editada",
        "aprobada",
        "descartada",
    ]


# --------------------------------------------------------------------------
# R25 · el orden y el cursor
# --------------------------------------------------------------------------


def test_f056_r25_clave_de_orden() -> None:
    sit = situacion(incidencia(5, creada=T0, fila=12))
    assert clave_de_orden(sit) == ClaveDeOrden(
        creada_at_utc=T0, fila_origen=12, incidencia_id=UUID(int=5)
    )


def test_f056_r25_el_orden_es_total_y_estable() -> None:
    filas = _mezcla()
    pagina = paginar(filas, filtro=FiltroEstado.TODAS, tamano=TAMANO_MAXIMO)
    assert ids(pagina.filas) == ids(sorted(filas, key=_clave_esperada))
    assert pagina.siguiente is None
    assert pagina.total_filtrado == len(filas) == 23


def test_f056_r25_fecha_descendente_fila_ascendente_sin_fila_al_final_e_id() -> None:
    filas = [
        fila(1, creada=T0, fila_origen=None),
        fila(2, creada=T0, fila_origen=3),
        fila(3, creada=T0 + timedelta(seconds=1), fila_origen=50),
        fila(4, creada=T0, fila_origen=3),
        fila(5, creada=T0, fila_origen=1),
        fila(6, creada=T0 - timedelta(days=1), fila_origen=1),
        fila(0, creada=T0, fila_origen=None),
    ]
    pagina = paginar(list(reversed(filas)), filtro=FiltroEstado.TODAS)
    assert ids(pagina.filas) == [3, 5, 2, 4, 0, 1, 6]


def test_f056_r25_el_orden_distingue_microsegundos_y_zonas() -> None:
    otra_zona = datetime(2026, 10, 1, 10, 0, tzinfo=UTC).astimezone(
        timezone(timedelta(hours=2))
    )
    filas = [
        fila(1, creada=T0),
        fila(2, creada=T0 + timedelta(microseconds=1)),
        fila(3, creada=otra_zona),  # 12:00+02:00, o sea 10:00 UTC
    ]
    assert ids(paginar(filas, filtro=FiltroEstado.TODAS).filas) == [3, 2, 1]


@pytest.mark.parametrize("fila_origen", [None, 1, 7, 1000])
def test_f056_r25_texto_de_clave_ida_y_vuelta(fila_origen: int | None) -> None:
    clave = ClaveDeOrden(
        creada_at_utc=T0 + timedelta(microseconds=123),
        fila_origen=fila_origen,
        incidencia_id=UUID(int=77),
    )
    texto = texto_de_clave(clave)
    assert isinstance(texto, str)
    assert clave_de_texto(texto) == clave


def test_f056_r25_el_texto_de_la_clave_es_json_compacto_y_canonico() -> None:
    # Decisión del humano del 2026-10-07: el dominio no codifica; el cursor
    # opaco (base64url) lo pone y lo quita el borde HTTP (Bloque 3).
    clave = ClaveDeOrden(creada_at_utc=T0, fila_origen=None, incidencia_id=UUID(int=77))
    assert texto_de_clave(clave) == (
        '{"c":"2026-10-01T08:00:00+00:00","f":null,"i":"' + str(UUID(int=77)) + '"}'
    )


def _json(obj: object) -> str:
    return json.dumps(obj, separators=(",", ":"))


_BUENO = {"c": T0.isoformat(), "f": 3, "i": str(UUID(int=77))}


@pytest.mark.parametrize(
    "texto",
    [
        None,
        5,
        b"{}",
        "",
        "!!!",
        "no es json",
        _json([1, 2, 3]),
        _json("texto"),
        _json(None),
        _json({"c": T0.isoformat(), "f": 3}),
        _json({**_BUENO, "x": 1}),
        _json({**_BUENO, "f": "3"}),
        _json({**_BUENO, "f": True}),
        _json({**_BUENO, "f": 0}),
        _json({**_BUENO, "f": -1}),
        _json({**_BUENO, "f": 2.0}),
        _json({**_BUENO, "c": "2026-10-01T08:00:00"}),
        _json({**_BUENO, "c": "ayer"}),
        _json({**_BUENO, "c": 5}),
        _json({**_BUENO, "i": "no-es-uuid"}),
        _json({**_BUENO, "i": 77}),
        _json({"f": 3, "c": T0.isoformat(), "i": str(UUID(int=77))}),
        json.dumps(_BUENO),
        json.dumps(_BUENO, indent=1),
        " " + _json(_BUENO),
        _json({**_BUENO, "i": str(UUID(int=77)).upper()}),
    ],
)
def test_f056_r23_clave_manipulada_es_peticion_invalida(texto: object) -> None:
    with pytest.raises(PeticionDeRevisionInvalida):
        clave_de_texto(texto)


def test_f056_r23_la_clave_buena_construida_a_mano_vale() -> None:
    assert clave_de_texto(_json(_BUENO)) == ClaveDeOrden(
        creada_at_utc=T0, fila_origen=3, incidencia_id=UUID(int=77)
    )


def _texto_de_largo(largo: int) -> tuple[ClaveDeOrden, str]:
    """Un texto emitido de verdad con exactamente `largo` caracteres."""
    for digitos in range(1, 400):
        clave = ClaveDeOrden(
            creada_at_utc=T0, fila_origen=int("1" * digitos), incidencia_id=UUID(int=77)
        )
        texto = texto_de_clave(clave)
        if len(texto) == largo:
            return clave, texto
    raise AssertionError(f"no hay texto de {largo} caracteres")


def test_f056_r23_el_texto_de_la_clave_tiene_como_mucho_384_caracteres() -> None:
    assert MAX_TEXTO_CLAVE == 384
    clave, texto = _texto_de_largo(384)
    assert clave_de_texto(texto) == clave
    _, demasiado = _texto_de_largo(385)
    with pytest.raises(PeticionDeRevisionInvalida):
        clave_de_texto(demasiado)


def test_f056_r23_el_error_de_la_clave_no_la_repite() -> None:
    texto = _json({**_BUENO, "i": "Ejemplo-que-no-debe-salir"})
    with pytest.raises(PeticionDeRevisionInvalida) as exc:
        clave_de_texto(texto)
    assert texto not in str(exc.value)
    assert "Ejemplo-que-no-debe-salir" not in str(exc.value)


# --------------------------------------------------------------------------
# R25 · paginar
# --------------------------------------------------------------------------


def _recorrer(
    filas: list[FilaDeRevision], tamano: int, **filtros: object
) -> tuple[list[int], list[int]]:
    vistos: list[int] = []
    tamanos: list[int] = []
    despues_de = None
    for _ in range(1000):
        pagina = paginar(filas, despues_de=despues_de, tamano=tamano, **filtros)  # type: ignore[arg-type]
        vistos += ids(pagina.filas)
        tamanos.append(len(pagina.filas))
        if pagina.siguiente is None:
            return vistos, tamanos
        assert pagina.siguiente == clave_de_orden(pagina.filas[-1].situacion)
        despues_de = clave_de_texto(texto_de_clave(pagina.siguiente))
    raise AssertionError("la paginación no termina")


@pytest.mark.parametrize("tamano", [1, 2, 5, 7, 20, 21, 22, 200])
def test_f056_r25_recorrer_todas_las_paginas_da_cada_fila_una_vez_y_en_orden(
    tamano: int,
) -> None:
    filas = _mezcla()
    vistos, tamanos = _recorrer(filas, tamano, filtro=FiltroEstado.TODAS)
    assert vistos == ids(sorted(filas, key=_clave_esperada))
    assert len(set(vistos)) == len(filas)
    assert all(t == tamano for t in tamanos[:-1])
    assert 0 < tamanos[-1] <= tamano


def test_f056_r25_la_ultima_pagina_exacta_no_deja_una_pagina_vacia() -> None:
    filas = [fila(n, fila_origen=n) for n in range(1, 21)]
    vistos, tamanos = _recorrer(filas, 5, filtro=FiltroEstado.TODAS)
    assert tamanos == [5, 5, 5, 5]
    assert vistos == list(range(1, 21))


def test_f056_r25_una_pagina_y_la_siguiente() -> None:
    filas = [fila(n, fila_origen=n) for n in range(1, 8)]
    primera = paginar(filas, filtro=FiltroEstado.TODAS, tamano=3)
    assert (ids(primera.filas), primera.total_filtrado) == ([1, 2, 3], 7)
    assert primera.siguiente == clave_de_orden(filas[2].situacion)
    segunda = paginar(
        filas, filtro=FiltroEstado.TODAS, tamano=3, despues_de=primera.siguiente
    )
    assert (ids(segunda.filas), segunda.total_filtrado) == ([4, 5, 6], 7)
    tercera = paginar(
        filas, filtro=FiltroEstado.TODAS, tamano=3, despues_de=segunda.siguiente
    )
    assert (ids(tercera.filas), tercera.siguiente, tercera.total_filtrado) == (
        [7],
        None,
        7,
    )


def test_f056_r25_sin_filas_no_hay_siguiente() -> None:
    pagina = paginar([], filtro=FiltroEstado.TODAS)
    assert (pagina.filas, pagina.total_filtrado, pagina.siguiente) == ((), 0, None)


def test_f056_r25_despues_de_una_fila_que_ya_no_esta_sigue_por_su_sitio() -> None:
    filas = [fila(n, fila_origen=n) for n in range(1, 8)]
    desaparecida = ClaveDeOrden(
        creada_at_utc=T0, fila_origen=4, incidencia_id=UUID(int=0)
    )
    pagina = paginar(
        filas, filtro=FiltroEstado.TODAS, tamano=2, despues_de=desaparecida
    )
    assert ids(pagina.filas) == [4, 5]
    despues_de_la_4 = clave_de_orden(filas[3].situacion)
    pagina = paginar(
        filas, filtro=FiltroEstado.TODAS, tamano=2, despues_de=despues_de_la_4
    )
    assert ids(pagina.filas) == [5, 6]


def test_f056_r25_despues_de_la_ultima_no_queda_nada() -> None:
    filas = [fila(n, fila_origen=n) for n in range(1, 4)]
    pagina = paginar(
        filas, filtro=FiltroEstado.TODAS, despues_de=clave_de_orden(filas[2].situacion)
    )
    assert (pagina.filas, pagina.siguiente, pagina.total_filtrado) == ((), None, 3)


@pytest.mark.parametrize("tamano", [0, -1, TAMANO_MAXIMO + 1])
def test_f056_r23_tamano_fuera_de_rango(tamano: int) -> None:
    with pytest.raises(PeticionDeRevisionInvalida):
        paginar([fila(1)], filtro=FiltroEstado.TODAS, tamano=tamano)


def test_f056_r23_tamano_en_los_bordes_y_por_defecto() -> None:
    filas = [fila(n, fila_origen=n) for n in range(1, 251)]
    assert len(paginar(filas, filtro=FiltroEstado.TODAS, tamano=1).filas) == 1
    assert (
        len(paginar(filas, filtro=FiltroEstado.TODAS, tamano=TAMANO_MAXIMO).filas)
        == 200
    )
    por_defecto = paginar(filas)
    assert len(por_defecto.filas) == TAMANO_POR_DEFECTO == 100


# --------------------------------------------------------------------------
# R26 · los filtros, en el servidor
# --------------------------------------------------------------------------

_CON = (M.SIN_UBICACION,)


def _por_estados() -> list[FilaDeRevision]:
    return [
        fila(1, fila_origen=1, estado=E.NUEVA),
        fila(2, fila_origen=2, estado=E.NUEVA, motivos=_CON),
        fila(3, fila_origen=3, estado=E.EDITADA),
        fila(4, fila_origen=4, estado=E.EDITADA, motivos=_CON),
        fila(5, fila_origen=5, estado=E.APROBADA),
        fila(6, fila_origen=6, estado=E.DESCARTADA),
        fila(7, fila_origen=7, estado=E.DESCARTADA, motivos=_CON),
    ]


@pytest.mark.parametrize(
    ("filtro", "esperados"),
    [
        (FiltroEstado.ACTIVAS, [1, 2, 3, 4, 5]),
        (FiltroEstado.TODAS, [1, 2, 3, 4, 5, 6, 7]),
        (FiltroEstado.NUEVA, [1, 2]),
        (FiltroEstado.EDITADA, [3, 4]),
        (FiltroEstado.APROBADA, [5]),
        (FiltroEstado.DESCARTADA, [6, 7]),
    ],
)
def test_f056_r26_filtro_de_estado(filtro: FiltroEstado, esperados: list[int]) -> None:
    pagina = paginar(_por_estados(), filtro=filtro)
    assert ids(pagina.filas) == esperados
    assert pagina.total_filtrado == len(esperados)


def test_f056_r26_el_filtro_por_defecto_es_activas() -> None:
    assert ids(paginar(_por_estados()).filas) == [1, 2, 3, 4, 5]


@pytest.mark.parametrize(
    ("con_motivos", "esperados"),
    [(None, [1, 2, 3, 4, 5]), (True, [2, 4]), (False, [1, 3, 5])],
)
def test_f056_r26_filtro_con_motivos(
    con_motivos: bool | None, esperados: list[int]
) -> None:
    pagina = paginar(
        _por_estados(), filtro=FiltroEstado.ACTIVAS, con_motivos=con_motivos
    )
    assert ids(pagina.filas) == esperados
    assert pagina.total_filtrado == len(esperados)


def test_f056_r26_los_dos_filtros_juntos() -> None:
    pagina = paginar(_por_estados(), filtro=FiltroEstado.DESCARTADA, con_motivos=True)
    assert ids(pagina.filas) == [7]


def test_f056_r26_paginar_con_filtro_recorre_solo_las_filtradas() -> None:
    filas = _por_estados()
    vistos, tamanos = _recorrer(
        filas, 2, filtro=FiltroEstado.ACTIVAS, con_motivos=False
    )
    assert (vistos, tamanos) == ([1, 3, 5], [2, 1])


# --------------------------------------------------------------------------
# R27 · el resumen
# --------------------------------------------------------------------------


def test_f056_r27_resumen_sobre_todas_las_filas() -> None:
    filas = _por_estados() + [
        fila(
            8, estado=E.NUEVA, motivos=(M.SIN_UBICACION, M.OFICIO_AMBIGUO, M.DUPLICADA)
        ),
    ]
    r = resumen(filas)
    assert r.total == 8
    assert r.por_estado == {E.NUEVA: 3, E.EDITADA: 2, E.APROBADA: 1, E.DESCARTADA: 2}
    assert r.con_motivos == 4
    assert list(r.por_motivo) == list(M)
    assert r.por_motivo == {
        M.UNIDAD_FUERA_DE_LA_OBRA: 0,
        M.SIN_UBICACION: 4,
        M.UBICACION_FUERA_DE_LISTA: 0,
        M.SIN_OFICIO: 0,
        M.OFICIO_AMBIGUO: 1,
        M.OFICIO_FUERA_DE_LA_OBRA: 0,
        M.PAR_FUERA_DE_LA_OBRA: 0,
        M.PROVEEDOR_AMBIGUO: 0,
        M.DUPLICADA: 1,
    }


def test_f056_r27_resumen_vacio_lleva_todas_las_claves_a_cero() -> None:
    r = resumen([])
    assert (r.total, r.con_motivos) == (0, 0)
    assert r.por_estado == dict.fromkeys(E, 0)
    assert list(r.por_estado) == list(E)
    assert r.por_motivo == dict.fromkeys(M, 0)


# --------------------------------------------------------------------------
# R26, R29 · una fila, con las mismas funciones que las acciones
# --------------------------------------------------------------------------

CATALOGO = CatalogoObra(
    obra_codigo=OBRA,
    obra_nombre=None,
    unidades=(UnidadPosventa(codigo=U1, nombre="Villa Ejemplo 1"),),
    oficios=(OficioObra(codigo="0046", nombre="Carpintería de madera"),),
    proveedores=(ProveedorEnObra("0046", None, None),),
)


def test_f056_r29_fila_de_revision_sin_revisiones() -> None:
    sit = situacion(incidencia(1, ubicacion=None))
    f = fila_de_revision(sit, catalogo=CATALOGO, ubicaciones={U1: ("Baño",)})
    assert f == FilaDeRevision(
        situacion=sit, estado=E.NUEVA, motivos=(M.SIN_UBICACION,), cambios=()
    )


def test_f056_r29_fila_de_revision_editada() -> None:
    inc = incidencia(1, ubicacion=None)
    vigentes = replace(valores_importados(inc), ubicacion="Terraza", detalle="Ejemplo")
    ultima = Revision(
        revision_id=3,
        incidencia_id=UUID(int=1),
        accion=AccionRevision.EDITAR,
        valores=vigentes,
        huella=huella_de_valores(vigentes),
        motivo=None,
        correo="persona@ejemplo.invalid",
        revisado_at_utc=AHORA,
    )
    f = fila_de_revision(
        situacion(inc, ultima), catalogo=CATALOGO, ubicaciones={U1: ("Baño",)}
    )
    assert f.estado is E.EDITADA
    assert f.motivos == (M.UBICACION_FUERA_DE_LISTA,)
    assert f.cambios == ("ubicacion", "detalle")
