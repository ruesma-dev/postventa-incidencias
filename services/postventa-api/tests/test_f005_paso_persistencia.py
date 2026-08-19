# services/postventa-api/tests/test_f005_paso_persistencia.py
"""El paso del pipeline que guarda (F-005, T18): R30, R31.

Lo que se demuestra es que el paso habla con el **puerto** y no con el
adaptador: todo el test corre contra `RepositorioEnMemoria`, que no sabe SQL.
Si el paso importara `RepositorioPostgres`, este doble no encajaría.

Todo el material es inventado.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from domain.models.errores import ErrorDePersistencia
from domain.models.firma import ClasificacionFirma
from domain.models.persistencia import ResultadoGuardado, nuevo_id
from domain.models.remesa import ModoDeteccion, ParteTroceado
from domain.models.validacion import validar_parte

from application.pipelines.contexto_parte import ContextoParte
from application.pipelines.paso_persistencia import paso_persistencia
from tests.utiles_pg import RepositorioEnMemoria
from tests.utiles_validacion import extraccion_de_ejemplo, lectura_de_firma

AHORA_INVENTADO = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


def _contexto(**cambios) -> ContextoParte:
    """Un contexto de parte con lo que haya pedido el test."""
    parte = ParteTroceado(
        hash="hash-inventado-0001",
        origen="remesa_inventada.pdf",
        paginas_origen=(1,),
        modo_deteccion=ModoDeteccion.UNA_PAGINA_POR_PARTE,
        contenido=b"%PDF-inventado",
    )
    ctx = ContextoParte(parte=parte)
    for nombre, valor in cambios.items():
        setattr(ctx, nombre, valor)
    return ctx


def test_f005_r30_el_paso_guarda_el_parte_por_el_puerto():
    """R30 · el paso no sabe que debajo hay PostgreSQL."""
    repositorio = RepositorioEnMemoria()
    remesa_id = nuevo_id()

    paso_persistencia(
        _contexto(extraccion=extraccion_de_ejemplo()),
        repositorio,
        remesa_id=remesa_id,
        ahora=AHORA_INVENTADO,
    )

    assert len(repositorio.partes) == 1
    assert repositorio.partes[0]["remesa_id"] == remesa_id
    assert repositorio.partes[0]["ahora"] == AHORA_INVENTADO


def test_f005_r20_si_el_parte_trae_veredicto_tambien_se_guarda():
    """La validación se guarda con el parte, no en otro viaje."""
    extraccion = extraccion_de_ejemplo()
    validacion = validar_parte(
        extraccion, lectura_de_firma(ClasificacionFirma.HUMANA)
    )
    repositorio = RepositorioEnMemoria()

    paso_persistencia(
        _contexto(extraccion=extraccion, validacion=validacion),
        repositorio,
        remesa_id=nuevo_id(),
        ahora=AHORA_INVENTADO,
    )

    assert len(repositorio.validaciones) == 1
    assert repositorio.validaciones[0]["resultado"] is validacion


def test_f005_r20_sin_veredicto_no_se_inventa_ninguno():
    """Un parte sin validar se guarda igual, pero sin fila de validación.

    F-003 y F-004 son independientes: puede haber un parte extraído al que
    todavía no se le ha mirado la firma.
    """
    repositorio = RepositorioEnMemoria()

    paso_persistencia(
        _contexto(extraccion=extraccion_de_ejemplo()),
        repositorio,
        remesa_id=nuevo_id(),
        ahora=AHORA_INVENTADO,
    )

    assert len(repositorio.partes) == 1
    assert repositorio.validaciones == []


def test_f005_r16_reprocesar_avisa_de_que_el_parte_ya_estaba():
    """R16 · quien revise el parte tiene que saber que no es la primera vez."""
    repositorio = RepositorioEnMemoria(resultado=ResultadoGuardado.ACTUALIZADO)
    ctx = _contexto(extraccion=extraccion_de_ejemplo())

    paso_persistencia(
        ctx, repositorio, remesa_id=nuevo_id(), ahora=AHORA_INVENTADO
    )

    assert any("ya se había procesado" in aviso for aviso in ctx.avisos)


def test_f005_r16_un_parte_nuevo_no_avisa_de_nada():
    """Un parte que llega por primera vez no arrastra ruido al front."""
    repositorio = RepositorioEnMemoria(resultado=ResultadoGuardado.CREADO)
    ctx = _contexto(extraccion=extraccion_de_ejemplo())

    paso_persistencia(
        ctx, repositorio, remesa_id=nuevo_id(), ahora=AHORA_INVENTADO
    )

    assert ctx.avisos == []


def test_f005_r18_sin_extraccion_no_se_guarda_una_ficha_vacia():
    """Guardar un parte sin leer dejaría una fila que parece ilegible.

    Y no lo es: es que nadie lo miró. Un `AttributeError` sobre un `None` a
    mitad de una remesa de veintidós partes tampoco le sirve a nadie para
    arreglarlo, así que el error dice qué falta.
    """
    repositorio = RepositorioEnMemoria()

    with pytest.raises(ErrorDePersistencia) as fallo:
        paso_persistencia(
            _contexto(), repositorio, remesa_id=nuevo_id(), ahora=AHORA_INVENTADO
        )

    assert "extracción" in fallo.value.motivo
    assert repositorio.partes == []


def test_f005_r30_el_paso_devuelve_el_mismo_contexto():
    """Los pasos añaden al contexto; no lo sustituyen."""
    ctx = _contexto(extraccion=extraccion_de_ejemplo())

    devuelto = paso_persistencia(
        ctx, RepositorioEnMemoria(), remesa_id=nuevo_id(), ahora=AHORA_INVENTADO
    )

    assert devuelto is ctx
