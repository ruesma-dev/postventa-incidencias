# services/postventa-api/tests/test_f013_fabricas.py
"""F-013 · la configuración del destino y lo que la fábrica exige (R1, R3, R17, R49).

La estrategia `posventa` cambia **dónde** se archiva el parte, y la única forma
de cambiarla es la configuración (R1). Lo que se prueba aquí:

- que los **cinco** campos nuevos existen, con su variable y su valor por
  omisión (`design.md` §2.2, enmendado el 2026-09-24);
- que el campo de la unidad que se retiró en T4 (`SHAREPOINT_NOMBRE_UNIDAD`)
  **no ha vuelto** (R3);
- que la fábrica del archivador se niega, **antes** de construir el adaptador
  —y por tanto antes de pedir ningún token—, ante una estrategia desconocida
  (R3) y ante una base vacía en `por_obra` (R17);
- y que la forma alternativa de la hoja trae el literal medido de VILLA 02 y
  admite quedarse vacía (R49).

Ni un valor real: el `drive`, el tenant, el cliente y el secreto son
**inventados**, como en `test_f006_fabrica.py`. El adaptador real **no se
construye** en ningún test de este fichero: se sustituye en la fábrica por un
espía que solo cuenta cuántas veces lo habrían construido.
"""

from __future__ import annotations

from typing import ClassVar

import infrastructure.sharepoint.fabrica as fabrica_sharepoint
import pytest
from config.settings import Ajustes
from domain.models.errores import ConfiguracionSharePointIncompleta

#: Un secreto **inventado**, para comprobar que no sale en ningún mensaje.
SECRETO_INVENTADO = "secreto-inventado-que-no-existe-f013"

#: Los cinco campos que añade F-013, con su variable y su valor por omisión
#: (`design.md` §2.2, enmendado el 2026-09-24). Escritos a mano: cambiar un
#: nombre o un defecto tiene que costar un cambio visible aquí.
CAMPOS_NUEVOS = (
    ("sharepoint_estructura", "SHAREPOINT_ESTRUCTURA", "por_obra"),
    (
        "sharepoint_carpeta_incidencias",
        "SHAREPOINT_CARPETA_INCIDENCIAS",
        "PARTES INCIDENCIAS",
    ),
    ("sharepoint_carpeta_firmados", "SHAREPOINT_CARPETA_FIRMADOS", "PARTES FIRMADOS"),
    (
        "sharepoint_carpeta_firmados_alternativa",
        "SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA",
        "PARTES FIRMADO",
    ),
    ("sharepoint_crear_carpetas", "SHAREPOINT_CREAR_CARPETAS", True),
)


class _EspiaDelAdaptador:
    """Ocupa el sitio del adaptador de Graph dentro de la fábrica.

    Registra cada construcción y no hace nada más: ni cliente HTTP, ni token.
    Si un test de «se niega antes del token» lo ve construido, la puerta ha
    llegado tarde.
    """

    construcciones: ClassVar[list[dict]] = []

    def __init__(self, **argumentos) -> None:
        type(self).construcciones.append(argumentos)


@pytest.fixture
def espia(monkeypatch):
    """La fábrica, con el adaptador cambiado por el espía."""
    _EspiaDelAdaptador.construcciones = []
    monkeypatch.setattr(
        fabrica_sharepoint, "AdaptadorSharePointGraph", _EspiaDelAdaptador
    )
    return _EspiaDelAdaptador


def _ajustes(**cambios) -> Ajustes:
    """Ajustes completos e inventados, con lo que el test quiera pisar.

    `_env_file=None` para que el `.env` de quien ejecuta la suite no cambie el
    resultado (mismo motivo que en `test_f006_fabrica.py`).
    """
    base = {
        "entorno": "dev",
        "archivo_habilitado": True,
        "sharepoint_drive_id": "drive-inventado",
        "sharepoint_carpeta_base": "Postventa",
        "graph_tenant_id": "tenant-inventado",
        "graph_client_id": "cliente-inventado",
        "graph_client_secret": SECRETO_INVENTADO,
    }
    base.update(cambios)
    return Ajustes(_env_file=None, **base)


# --------------------------------------------------------------------------
# R1 · El destino es configuración: cinco campos, con su variable y su defecto
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("campo", "variable", "defecto"), CAMPOS_NUEVOS)
def test_f013_r1_cada_campo_nuevo_existe_con_su_variable_y_su_defecto(
    campo, variable, defecto
):
    """R1 · el campo, el nombre de la variable de entorno y el valor por omisión."""
    declarado = Ajustes.model_fields[campo]

    assert declarado.validation_alias == variable
    assert declarado.default == defecto
    assert type(declarado.default) is type(defecto)


@pytest.mark.parametrize(
    ("campo", "variable", "valor", "esperado"),
    (
        ("sharepoint_estructura", "SHAREPOINT_ESTRUCTURA", "posventa", "posventa"),
        (
            "sharepoint_carpeta_incidencias",
            "SHAREPOINT_CARPETA_INCIDENCIAS",
            "Partes de otra forma",
            "Partes de otra forma",
        ),
        (
            "sharepoint_carpeta_firmados",
            "SHAREPOINT_CARPETA_FIRMADOS",
            "Hoja de otra forma",
            "Hoja de otra forma",
        ),
        (
            "sharepoint_carpeta_firmados_alternativa",
            "SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA",
            "Otra alternativa",
            "Otra alternativa",
        ),
        ("sharepoint_crear_carpetas", "SHAREPOINT_CREAR_CARPETAS", "false", False),
    ),
)
def test_f013_r1_cada_campo_se_lee_del_entorno(
    monkeypatch, campo, variable, valor, esperado
):
    """R1 · cambiar de estrategia o de nombres es cambiar una variable.

    Se lee del entorno, que es como llega en Azure (App Settings), y no por
    el nombre del campo.
    """
    monkeypatch.setenv(variable, valor)

    assert getattr(Ajustes(_env_file=None), campo) == esperado


def test_f013_r1_crear_carpetas_esta_encendido_por_omision():
    """R1, D-4 y T4-3 · «crear desde el principio».

    A diferencia de `ARCHIVO_HABILITADO`, este interruptor **no** es la puerta
    de la escritura —esa sigue siendo la ventana de archivo—: dice si, cuando
    ya se archiva, se pueden crear las carpetas que falten. El humano decidió
    que sí, desde el primer despliegue.
    """
    assert Ajustes(_env_file=None).sharepoint_crear_carpetas is True


def test_f013_r1_la_estrategia_por_omision_es_la_de_hoy():
    """R1 y R2 · sin tocar nada, el servicio archiva como F-006.

    Es lo que hace que desplegar esta rama no mude nada hasta el corte.
    """
    ajustes = Ajustes(_env_file=None)

    assert ajustes.sharepoint_estructura == "por_obra"
    assert ajustes.sharepoint_carpeta_base == "Postventa"


# --------------------------------------------------------------------------
# R3 · Estrategia desconocida → error de configuración, antes del token
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "estructura", ("otra", "", "POSVENTA", " posventa", "por obra", "posventa2")
)
def test_f013_r3_estrategia_desconocida_falla_antes_de_construir_el_adaptador(
    espia, estructura
):
    """R3 · un valor que no es ninguno de los dos no se interpreta: se rechaza.

    Ni mayúsculas ni blancos se «arreglan»: una variable mal escrita en un
    despliegue tiene que pararlo, no archivar con una estrategia adivinada.
    """
    with pytest.raises(ConfiguracionSharePointIncompleta) as fallo:
        fabrica_sharepoint.construir_archivador(
            _ajustes(sharepoint_estructura=estructura)
        )

    assert espia.construcciones == []
    assert "SHAREPOINT_ESTRUCTURA" in fallo.value.motivo
    assert "por_obra" in fallo.value.motivo
    assert "posventa" in fallo.value.motivo


def test_f013_r3_el_mensaje_no_lleva_el_secreto():
    """R3 · el motivo acaba en un log; la credencial no puede acabar ahí."""
    with pytest.raises(ConfiguracionSharePointIncompleta) as fallo:
        fabrica_sharepoint.construir_archivador(
            _ajustes(sharepoint_estructura="otra")
        )

    motivo = fallo.value.motivo
    for inicio in range(len(SECRETO_INVENTADO) - 5):
        assert SECRETO_INVENTADO[inicio : inicio + 6] not in motivo


@pytest.mark.parametrize("estructura", ("por_obra", "posventa"))
def test_f013_r3_las_dos_estrategias_admitidas_construyen(espia, estructura):
    """R3 · el control de arriba no puede ser «rechazarlo todo».

    Con una estrategia válida y la configuración completa, la fábrica llega a
    construir el adaptador (aquí, el espía) una vez.
    """
    fabrica_sharepoint.construir_archivador(
        _ajustes(sharepoint_estructura=estructura)
    )

    assert len(espia.construcciones) == 1


def test_f013_r3_la_puerta_del_entorno_sigue_yendo_antes(espia):
    """R3 · el orden de F-006 no cambia: primero, si aquí se archiva.

    Un puesto de trabajo con una estrategia mal escrita recibe «este entorno no
    archiva», no «te falta arreglar una variable».
    """
    from domain.models.errores import ArchivoDeshabilitado

    with pytest.raises(ArchivoDeshabilitado):
        fabrica_sharepoint.construir_archivador(
            _ajustes(entorno="local", sharepoint_estructura="otra")
        )

    assert espia.construcciones == []


def test_f013_r3_no_existe_el_campo_de_la_unidad():
    """R3 (enmienda del 2026-09-24) · `SHAREPOINT_NOMBRE_UNIDAD` se retiró en T4.

    La unidad se crea como `VILLA NN` derivado del `con.cod` con una regla
    fija (R37): no hay nada que elegir por configuración, y la variable tenía
    un valor (`nombre`) que habría creado `Viviendas Bloque Villa 13` al lado
    de `VILLA 01` … `VILLA 07`. Este test existe para que no vuelva por
    inercia: ni el campo, ni ningún alias con ese nombre.
    """
    assert "sharepoint_nombre_unidad" not in Ajustes.model_fields
    alias = {
        str(campo.validation_alias).upper()
        for campo in Ajustes.model_fields.values()
        if campo.validation_alias is not None
    }
    assert "SHAREPOINT_NOMBRE_UNIDAD" not in alias


def test_f013_r3_la_variable_retirada_no_hace_nada(monkeypatch):
    """R3 · y si alguien la deja puesta en un despliegue, se ignora.

    `extra="ignore"` en los ajustes: no revienta el arranque, y no llega a
    ningún campo.
    """
    monkeypatch.setenv("SHAREPOINT_NOMBRE_UNIDAD", "nombre")

    ajustes = Ajustes(_env_file=None)

    assert not hasattr(ajustes, "sharepoint_nombre_unidad")


# --------------------------------------------------------------------------
# R17 · Base vacía: raíz en `posventa`, error de configuración en `por_obra`
# --------------------------------------------------------------------------


@pytest.mark.parametrize("base", ("", "   ", "/", " / ", "//"))
def test_f013_r17_base_vacia_en_por_obra_es_error_de_configuracion(espia, base):
    """R17 · en `por_obra`, una base vacía dejaría `/0677` en la raíz.

    Las carpetas por código de F-006 acabarían sueltas en la raíz de la
    biblioteca de Posventa, mezcladas con las suyas. Se para en la fábrica,
    antes de construir nada, nombrando la variable. Una base de solo blancos o
    solo barras es la misma base vacía: `carpeta_de_archivo` la recortaría a
    nada.
    """
    with pytest.raises(ConfiguracionSharePointIncompleta) as fallo:
        fabrica_sharepoint.construir_archivador(
            _ajustes(sharepoint_estructura="por_obra", sharepoint_carpeta_base=base)
        )

    assert espia.construcciones == []
    assert "SHAREPOINT_CARPETA_BASE" in fallo.value.motivo


@pytest.mark.parametrize("base", ("", "   ", "/"))
def test_f013_r17_base_vacia_en_posventa_es_la_raiz(espia, base):
    """R17 y D-1 · en `posventa`, base vacía = raíz de la biblioteca.

    Es la configuración del corte (`$CarpetaBaseArchivo = ""`): la fábrica no
    puede rechazarla.
    """
    fabrica_sharepoint.construir_archivador(
        _ajustes(sharepoint_estructura="posventa", sharepoint_carpeta_base=base)
    )

    assert len(espia.construcciones) == 1


def test_f013_r17_una_base_con_nombre_vale_en_las_dos(espia):
    """R17 · el control de la base no rechaza lo que ya funciona hoy."""
    for estructura in ("por_obra", "posventa"):
        fabrica_sharepoint.construir_archivador(
            _ajustes(
                sharepoint_estructura=estructura,
                sharepoint_carpeta_base="Postventa",
            )
        )

    assert len(espia.construcciones) == 2


def test_f013_r17_estrategia_mala_y_base_vacia_se_dicen_juntas(espia):
    """R17 y R3 · quien despliega no descubre los fallos de uno en uno.

    Mismo criterio que F-006 R28 con las variables que faltan.
    """
    with pytest.raises(ConfiguracionSharePointIncompleta) as fallo:
        fabrica_sharepoint.construir_archivador(
            _ajustes(
                sharepoint_estructura="otra",
                sharepoint_carpeta_base="",
                sharepoint_drive_id=None,
            )
        )

    motivo = fallo.value.motivo
    assert "SHAREPOINT_ESTRUCTURA" in motivo
    assert "SHAREPOINT_DRIVE_ID" in motivo
    assert espia.construcciones == []


# --------------------------------------------------------------------------
# R49 · La forma alternativa de la hoja
# --------------------------------------------------------------------------


def test_f013_r49_la_alternativa_por_omision_es_la_de_villa_02():
    """R49 y T4-6 · `PARTES FIRMADO`, el literal que dio el humano el 2026-09-24.

    No hace falta escribirla en el despliegue: vale su defecto del código
    (`design.md` §2.2).
    """
    assert (
        Ajustes(_env_file=None).sharepoint_carpeta_firmados_alternativa
        == "PARTES FIRMADO"
    )


def test_f013_r49_la_alternativa_puede_quedar_vacia(monkeypatch):
    """R49 · vacía = ninguna forma alternativa.

    Una variable creada y dejada en blanco **no** vuelve al defecto: es la
    forma de apagar la alternativa sin tocar el código.
    """
    monkeypatch.setenv("SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA", "")

    assert Ajustes(_env_file=None).sharepoint_carpeta_firmados_alternativa == ""


def test_f013_r49_la_alternativa_vacia_no_impide_construir(espia):
    """R49 · la fábrica no la exige: vacía es un valor admitido."""
    fabrica_sharepoint.construir_archivador(
        _ajustes(
            sharepoint_estructura="posventa",
            sharepoint_carpeta_firmados_alternativa="",
        )
    )

    assert len(espia.construcciones) == 1
