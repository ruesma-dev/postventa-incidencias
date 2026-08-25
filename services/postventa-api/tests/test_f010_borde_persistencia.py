# services/postventa-api/tests/test_f010_borde_persistencia.py
"""El borde traduce los fallos de la persistencia (**defecto 14 de F-010**).

El 2026-08-25, ejecutando T18 contra el entorno real, `POST /api/archivar`
devolvió **500 con el cuerpo vacío**. El PDF sintético **sí se había subido** a
SharePoint; lo que falló fue guardar la traza en PostgreSQL, y el servicio lo
sabía: llevaba dentro un `PersistenciaNoDisponible` con su motivo escrito.
Nadie lo tradujo, así que el llamante no recibió nada y hubo que leer
Application Insights media hora para enterarse.

Lo que este fichero fija es **la traducción que faltaba**, y sobre todo la
distinción que hace que el mensaje sea útil:

| Situación | Código | Lo que el llamante necesita saber |
|---|---|---|
| Subida hecha, traza perdida | **500** | el fichero **está** en SharePoint; reintentar no lo arregla |
| La base no responde y **no se subió nada** | **503** | no se ha tocado SharePoint; se puede reintentar |
| Falta configuración de PostgreSQL | **503** | este entorno no archiva; se nombra la variable, nunca su valor |

Los dobles son los de F-006 (`tests/utiles_sharepoint.py`): **SharePoint y
PostgreSQL no aparecen por ninguna parte**. El montaje del `multipart` se
reutiliza del fichero de F-006 en vez de copiarse, para que un cambio del
borde rompa los dos sitios a la vez y no solo uno.

**Ni un dato real.** El «PDF» lleva un DNI inventado —`00000000T` no es
válido— justamente para comprobar que no se cuela en ningún mensaje de error
(R26).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from application.pipelines.paso_archivo import paso_archivo
from domain.models.errores import (
    ArchivoFallido,
    ArchivoSinTraza,
    ConfiguracionPgIncompleta,
    PersistenciaNoDisponible,
)

from tests.test_f006_archivar_http import (
    PDF_CON_DATOS,
    _con_dobles,
    _cuerpo,
    _peticion,
)
from tests.utiles_sharepoint import (
    CARPETA_BASE,
    ArchivoPortFalso,
    BibliotecaFalsa,
    RepositorioFalso,
    contexto_apto,
)

#: Un instante fijo: el paso no consulta el reloj.
AHORA = datetime(2026, 8, 25, 14, 8, tzinfo=UTC)

#: El motivo **real** del 2026-08-25, tal y como lo compone el repositorio de
#: F-005. No lleva DSN, ni contraseña, ni ningún dato del parte.
MOTIVO_REAL = (
    "la operación 'guardar_archivo' no se pudo completar contra PostgreSQL: "
    "ForeignKeyViolation"
)


def _repositorio_caido() -> RepositorioFalso:
    """Un repositorio que no puede guardar la traza, con el motivo de verdad."""
    return RepositorioFalso(fallo=PersistenciaNoDisponible(MOTIVO_REAL))


# --------------------------------------------------------------------------
# El caso que se dio de verdad: subido y sin traza
# --------------------------------------------------------------------------


def test_f010_defecto14_traza_perdida_tras_subir_responde_500_con_cuerpo(monkeypatch):
    """El 500 **habla**: es lo único que separa esto de media hora de logs.

    Y antes de mirar el código, lo que importa: la subida **ocurrió**. Por eso
    este caso no puede llevar el mismo código que los cuatro errores que el
    endpoint ya traducía, que comparten «sin haber subido nada».
    """
    import function_app

    biblioteca = BibliotecaFalsa()
    _con_dobles(monkeypatch, ArchivoPortFalso(biblioteca), _repositorio_caido())

    respuesta = function_app.archivar(_peticion([("parte.pdf", PDF_CON_DATOS)]))

    assert biblioteca.subidas == 1
    assert respuesta.status_code == 500
    assert respuesta.get_body(), "el cuerpo vacío es exactamente el defecto 14"


def test_f010_defecto14_el_mensaje_dice_que_el_fichero_esta_subido(monkeypatch):
    """Sin esa frase, el llamante reintenta a ciegas o lo da por no archivado.

    Las dos mitades del mensaje son necesarias: **dónde está el fichero** y
    **qué es lo que falló**. Con una sola, quien lo lee sigue sin saber si
    tiene que volver a subir.
    """
    import function_app

    _con_dobles(monkeypatch, ArchivoPortFalso(BibliotecaFalsa()), _repositorio_caido())

    cuerpo = _cuerpo(function_app.archivar(_peticion([("parte.pdf", PDF_CON_DATOS)])))

    assert "SharePoint" in cuerpo["error"]
    assert "traza" in cuerpo["error"]
    assert MOTIVO_REAL in cuerpo["error"]


def test_f010_defecto14_el_mensaje_no_lleva_datos_personales_ni_bytes(monkeypatch):
    """R26 · este mensaje viaja al navegador y acaba en un log.

    El motivo de la persistencia se puede reenviar tal cual **porque F-005 lo
    compone sin DSN, sin contraseña y sin nada del parte**; lo que no puede
    aparecer es el contenido del PDF ni el DNI que lleva dentro.
    """
    import function_app

    _con_dobles(monkeypatch, ArchivoPortFalso(BibliotecaFalsa()), _repositorio_caido())

    cuerpo = _cuerpo(function_app.archivar(_peticion([("parte.pdf", PDF_CON_DATOS)])))

    assert "00000000T" not in cuerpo["error"]
    assert "%PDF" not in cuerpo["error"]
    assert "password" not in cuerpo["error"].lower()


# --------------------------------------------------------------------------
# El caso contrario: la base tampoco responde, pero no se subió nada
# --------------------------------------------------------------------------


def test_f010_defecto14_sin_subida_previa_responde_503_y_lo_dice(monkeypatch):
    """Si la subida falló, la traza perdida **no** significa fichero arriba.

    Es el mismo `PersistenciaNoDisponible`, y decir aquí «está en SharePoint»
    mandaría a alguien a buscar un fichero que no existe. Por eso el 503 dice
    lo contrario, y es cierto: no se ha subido nada.
    """
    import function_app

    biblioteca = BibliotecaFalsa()
    _con_dobles(
        monkeypatch,
        ArchivoPortFalso(biblioteca, fallo=ArchivoFallido("el proveedor no respondió")),
        _repositorio_caido(),
    )

    respuesta = function_app.archivar(_peticion([("parte.pdf", PDF_CON_DATOS)]))

    assert biblioteca.subidas == 0
    assert respuesta.status_code == 503
    assert "no se ha subido nada" in _cuerpo(respuesta)["error"]


def test_f010_defecto14_falta_de_configuracion_de_pg_responde_503(monkeypatch):
    """La hermana del error anterior, y hasta hoy otro 500 mudo.

    Se traduce como `ConfiguracionSharePointIncompleta`: **este entorno no
    archiva**. El mensaje nombra la variable que falta y jamás su valor.
    """
    import function_app

    def sin_configuracion(contenido: bytes, **datos):
        raise ConfiguracionPgIncompleta(
            "falta la variable PG_PASSWORD: sin credencial no se puede "
            "construir el repositorio de PostgreSQL"
        )

    monkeypatch.setattr(function_app, "archivar_parte", sin_configuracion)

    respuesta = function_app.archivar(_peticion([("parte.pdf", PDF_CON_DATOS)]))

    assert respuesta.status_code == 503
    assert "PG_PASSWORD" in _cuerpo(respuesta)["error"]


# --------------------------------------------------------------------------
# El paso es quien sabe si se subió: por eso la distinción se hace ahí
# --------------------------------------------------------------------------


def _archivar(ctx, archivador, repositorio):
    """El paso con la carpeta base y la hora de siempre."""
    return paso_archivo(
        ctx, archivador, repositorio, carpeta_base=CARPETA_BASE, ahora=AHORA
    )


def test_f010_defecto14_el_paso_levanta_archivo_sin_traza_cuando_ya_subio():
    """El borde no puede adivinarlo: quien conoce el orden es el paso.

    `ArchivoSinTraza` existe para eso y para nada más: nombrar el único estado
    en el que el parte está archivado y no consta.
    """
    biblioteca = BibliotecaFalsa()

    with pytest.raises(ArchivoSinTraza) as fallo:
        _archivar(contexto_apto(), ArchivoPortFalso(biblioteca), _repositorio_caido())

    assert biblioteca.subidas == 1
    assert MOTIVO_REAL in fallo.value.motivo


def test_f010_defecto14_si_la_subida_fallo_el_paso_no_lo_llama_asi():
    """La traza de error tampoco se pudo guardar, pero no hay fichero arriba.

    Aquí sigue saliendo `PersistenciaNoDisponible` **a propósito**: es lo que
    el borde traduce a 503 «no se ha subido nada».
    """
    biblioteca = BibliotecaFalsa()
    archivador = ArchivoPortFalso(
        biblioteca, fallo=ArchivoFallido("el proveedor no respondió")
    )

    with pytest.raises(PersistenciaNoDisponible):
        _archivar(contexto_apto(), archivador, _repositorio_caido())

    assert biblioteca.subidas == 0
