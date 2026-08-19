# services/postventa-api/tests/test_f006_fabrica.py
"""Las puertas que impiden subir a SharePoint desde local (R19, R20, R28).

`CLAUDE.md` lo dice sin matices: **PROHIBIDO subir nada al SharePoint de
Posventa desde local**. Y el `acceptance` 4 de F-006 lo repite. Esa regla no
se cumple por disciplina —la disciplina se rompe un viernes a las siete— sino
porque **el código lo impide**, con dos puertas independientes que se prueban
aquí y una tercera (la guardia de red de F-003) que se prueba en
`test_f006_arquitectura.py`.

**Este es el único fichero de toda la suite que nombra
`AdaptadorSharePointGraph`**, y lo hace precisamente para comprobar que **no
se deja construir**. Que sea el único está vigilado por
`test_f006_r21_ningun_test_construye_el_adaptador_real`.

Ni un valor real: el `drive`, el tenant, el cliente y el secreto de estos
tests son **inventados** y no apuntan a nada. Ninguno tiene forma de GUID a
propósito: quien lea el repositorio no puede distinguir un GUID inventado de
uno de verdad, así que aquí no entra ninguno de los dos.
"""

from __future__ import annotations

import pytest
from config.settings import Ajustes
from domain.models.errores import (
    ArchivoDeshabilitado,
    ConfiguracionSharePointIncompleta,
)

from infrastructure.sharepoint.fabrica import (
    ENTORNOS_CON_ARCHIVO,
    construir_archivador,
)
from infrastructure.sharepoint.graph import AdaptadorSharePointGraph

#: Un secreto **inventado**. Existe para comprobar que no sale en ningún
#: mensaje de error, ni entero ni troceado.
SECRETO_INVENTADO = "secreto-inventado-que-no-existe-0000"


def _ajustes(**cambios) -> Ajustes:
    """Ajustes completos e inventados, con lo que el test quiera pisar.

    Todos los campos van **explícitos** para que el `.env` de quien ejecute la
    suite no pueda cambiar el resultado de un test.
    """
    base = {
        "entorno": "dev",
        "archivo_habilitado": True,
        "sharepoint_site_id": "sitio-inventado",
        "sharepoint_drive_id": "drive-inventado",
        "sharepoint_carpeta_base": "Postventa",
        "graph_tenant_id": "tenant-inventado",
        "graph_client_id": "cliente-inventado",
        "graph_client_secret": SECRETO_INVENTADO,
    }
    base.update(cambios)
    return Ajustes(**base)


# --------------------------------------------------------------------------
# R19 · La puerta del entorno, en la fábrica y en el constructor
# --------------------------------------------------------------------------


@pytest.mark.parametrize("entorno", ("local", "test", "preproduccion", ""))
def test_f006_r19_en_entorno_local_la_fabrica_no_construye_el_adaptador(entorno):
    """R19 · fuera de `dev` y `pro`, no hay adaptador que valga.

    Y se prueba también con `test`, que es el entorno que `conftest.py` fija
    para **toda** la suite: dentro de los tests, el adaptador real no se puede
    construir ni queriendo.
    """
    with pytest.raises(ArchivoDeshabilitado) as fallo:
        construir_archivador(_ajustes(entorno=entorno))

    assert "ENTORNO" in fallo.value.motivo


def test_f006_r19_el_constructor_del_adaptador_tambien_muerde():
    """R19 · componer las piezas a mano **no** es la vía para saltarse la puerta.

    La comprobación está en el propio constructor y no solo en la fábrica a
    propósito (`design.md` §5, puerta 1): un script suelto, un `python -c` o un
    test «solo para probar» se topan igual con ella.

    Este es el único sitio de la suite donde se construye la clase real, y se
    construye para comprobar que **se niega**.
    """
    with pytest.raises(ArchivoDeshabilitado) as fallo:
        AdaptadorSharePointGraph(
            entorno="test",
            drive_id="drive-inventado",
            tenant_id="tenant-inventado",
            client_id="cliente-inventado",
            client_secret=SECRETO_INVENTADO,
        )

    assert "ENTORNO" in fallo.value.motivo
    assert SECRETO_INVENTADO not in fallo.value.motivo


def test_f006_r19_los_entornos_con_archivo_son_dos_y_solo_dos():
    """R19 · `dev` y `pro`. Ni `local`, ni `test`, ni `staging`.

    Escritos a mano y comparados por igualdad: añadir un entorno a esta lista
    es abrir la puerta a subir desde otro sitio, y tiene que costar un cambio
    visible en un test.
    """
    assert tuple(ENTORNOS_CON_ARCHIVO) == ("dev", "pro")


# --------------------------------------------------------------------------
# R20 · El interruptor maestro, apagado por defecto
# --------------------------------------------------------------------------


def test_f006_r20_por_defecto_el_archivo_esta_deshabilitado():
    """R20 · el comportamiento por omisión es **no subir**.

    Se comprueba sobre el valor por defecto declarado del campo, que es lo que
    rige en un `.env` recién copiado o en un despliegue a medio configurar. Un
    interruptor de este tipo encendido por defecto convierte cualquier
    despliegue incompleto en una subida a un sitio equivocado.
    """
    assert Ajustes.model_fields["archivo_habilitado"].default is False


def test_f006_r20_sin_el_interruptor_la_fabrica_se_niega():
    """R20 · y con todo lo demás bien puesto, tampoco se construye.

    El entorno es `dev` y la configuración está completa: lo único que falta
    es el gesto explícito de encenderlo. El motivo nombra la variable para que
    quien despliega sepa qué le falta.
    """
    with pytest.raises(ArchivoDeshabilitado) as fallo:
        construir_archivador(_ajustes(archivo_habilitado=False))

    assert "ARCHIVO_HABILITADO" in fallo.value.motivo


def test_f006_r20_las_dos_puertas_dan_motivos_distintos():
    """R20 · «este entorno no archiva» y «no lo has encendido» son dos cosas.

    Un motivo único obligaría a quien despliega a comprobar las dos.
    """
    with pytest.raises(ArchivoDeshabilitado) as por_entorno:
        construir_archivador(_ajustes(entorno="local"))
    with pytest.raises(ArchivoDeshabilitado) as por_interruptor:
        construir_archivador(_ajustes(archivo_habilitado=False))

    assert por_entorno.value.motivo != por_interruptor.value.motivo


# --------------------------------------------------------------------------
# R28 · Configuración incompleta: se dice la variable, jamás el valor
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("campo", "variable"),
    (
        ("sharepoint_drive_id", "SHAREPOINT_DRIVE_ID"),
        ("graph_tenant_id", "GRAPH_TENANT_ID"),
        ("graph_client_id", "GRAPH_CLIENT_ID"),
        ("graph_client_secret", "GRAPH_CLIENT_SECRET"),
    ),
)
@pytest.mark.parametrize("ausente", (None, "", "   "))
def test_f006_r28_configuracion_incompleta_falla_nombrando_la_variable(
    campo, variable, ausente
):
    """R28 · se dice **qué variable** falta, nunca su valor.

    Y una variable creada y dejada en blanco cuenta como ausente: es un caso
    real de despliegue, y sin este control el servicio arrancaría para fallar
    después contra Graph con un error indescifrable.
    """
    with pytest.raises(ConfiguracionSharePointIncompleta) as fallo:
        construir_archivador(_ajustes(**{campo: ausente}))

    assert variable in fallo.value.motivo


def test_f006_r28_el_secreto_no_aparece_en_el_mensaje_ni_en_fragmentos():
    """R28 · el mensaje acaba en un log. La credencial no puede acabar ahí.

    No basta con que no salga entera: se comprueba que **ningún fragmento** de
    seis caracteres del secreto aparece en el motivo. Un mensaje que dijera
    «GRAPH_CLIENT_SECRET=secret…» filtraría lo suficiente para que valga la
    pena intentarlo.
    """
    with pytest.raises(ConfiguracionSharePointIncompleta) as fallo:
        construir_archivador(_ajustes(sharepoint_drive_id=None))

    motivo = fallo.value.motivo
    assert SECRETO_INVENTADO not in motivo
    for inicio in range(len(SECRETO_INVENTADO) - 5):
        assert SECRETO_INVENTADO[inicio : inicio + 6] not in motivo


def test_f006_r28_faltando_varias_se_nombran_todas():
    """R28 · quien despliega no puede descubrirlas de una en una.

    Un error que nombra solo la primera obliga a tres vueltas de despliegue
    para arreglar tres variables.
    """
    with pytest.raises(ConfiguracionSharePointIncompleta) as fallo:
        construir_archivador(
            _ajustes(sharepoint_drive_id=None, graph_client_id=None)
        )

    assert "SHAREPOINT_DRIVE_ID" in fallo.value.motivo
    assert "GRAPH_CLIENT_ID" in fallo.value.motivo


def test_f006_r28_la_puerta_del_entorno_va_antes_que_la_de_configuracion():
    """R28 · en `local`, ni siquiera se mira si la configuración está completa.

    Es el orden que protege: lo primero que se comprueba es si este sitio
    puede archivar. Si se comprobara antes la configuración, un puesto de
    trabajo con el `.env` completo recibiría el error «equivocado» y alguien
    podría creer que solo le falta rellenar una variable.
    """
    with pytest.raises(ArchivoDeshabilitado):
        construir_archivador(
            _ajustes(entorno="local", sharepoint_drive_id=None)
        )
