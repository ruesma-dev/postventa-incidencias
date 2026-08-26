# services/postventa-api/tests/test_f010_endpoints_protegidos.py
"""La anonimidad de los endpoints es DELIBERADA y esta explicada (R18, R32, R31).

Este fichero no comprueba que algo funcione: comprueba que algo **siga como
esta y se sepa por que**. Es raro, y tiene motivo.

## Correccion de F-019 (2026-08-26): esta cabecera decia algo que ya no es cierto

Hasta hoy abria diciendo que «al desplegar, los seis endpoints de
`function_app.py` quedan **en internet** con `auth_level=ANONYMOUS`». Era
verdad cuando se escribio y **dejo de serlo el 2026-08-25**, al descubrir el
defecto 13 de F-010 ejecutando contra Azure.

Lo que hay de verdad, y esta en `docs/DESPLIEGUE.md` §5 bis:

1. **El backend enlazado.** Desde que la Function App es backend enlazado de
   la Static Web App, la plataforma le activa Easy Auth con el proveedor
   `azureStaticWebApps` y el backend **solo acepta lo que entra por el proxy
   del front**. Preguntarle por su nombre de host -cualquier ruta,
   `GET /api/health` incluido- devuelve un `400` que **no es nuestro**: lo
   escribe la plataforma antes de que el codigo se entere. No hay nada que
   configurar.
2. **La regla `/*` de la Static Web App**, que exige `authenticated` en `/*` y
   en `/api/*`, mas la asignacion obligatoria al grupo de Posventa. Lo fija
   `services/postventa-front/tests/test_f010_config_swa.py`.

Asi que el `auth_level` de `function_app.py` es **irrelevante desde
internet**: nadie alcanza el codigo sin pasar por el proxy, y el proxy exige
sesion.

Que una cabecera exagere un riesgo gasta el mismo credito que una que lo
esconda: la proxima vez, quien la lea no sabra cual de las dos tiene delante.

## Entonces, ¿por que sigue en `ANONYMOUS`?

Porque `auth_level=FUNCTION` **rompe el front el mismo dia que se aplica**: el
proxy autentica al usuario, reenvia la cabecera `x-ms-client-principal` y **no
anade** ninguna clave de funcion, asi que la Function empezaria a devolver
`401` a traves del front. Y el fallo no lo caza ningun test del repositorio,
porque ninguno atraviesa ese proxy. Es la clase de error que reaparece a los
seis meses, cuando ya nadie recuerda por que estaba asi.

De ahi R32: la cabecera del modulo lo explica y este fichero lo fija, atado a
la explicacion:

    si alguien cambia una cosa sin la otra, falla.

Cambiar el `auth_level` sin borrar la nota falla porque los endpoints dejan de
ser anonimos. Borrar la nota dejando el `auth_level` falla porque desaparece
la explicacion. Las dos a la vez tambien fallan. Lo unico que pasa es un
cambio consciente que ademas reescriba el porque, que es exactamente lo que se
persigue.

**Nada de esto relaja el test.** F-019 lo amplia de seis endpoints a nueve y
le anade dos comprobaciones sobre la cabecera -donde esta la proteccion de
verdad, y que anade `GET /api/cola` al cuadro-. No quita ninguna.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: El punto de entrada HTTP, leido como TEXTO.
#:
#: Se lee en vez de importarse a proposito: lo que se fija es lo que dice el
#: decorador en el fichero, no lo que un objeto tenga en memoria despues de
#: que el runtime de Functions lo haya construido.
FUNCTION_APP = Path(__file__).resolve().parent.parent / "function_app.py"

#: Los nueve endpoints del servicio. Si manana hay un decimo, este test se
#: entera: la cuenta tiene que cuadrar con las rutas declaradas.
#:
#: Eran seis hasta F-019, que anadio `remesa`, `parte` y `cola`.
ENDPOINTS = (
    "health",
    "split",
    "extraer",
    "firma",
    "validar",
    "remesa",
    "parte",
    "cola",
    "archivar",
)

#: Un decorador de ruta con su nivel de autenticacion.
PATRON_RUTA = re.compile(
    r"@app\.route\(\s*route=\"(?P<ruta>\w+)\".*?auth_level=func\.AuthLevel\.(?P<nivel>\w+)\s*\)",
    re.DOTALL,
)


@pytest.fixture
def codigo() -> str:
    return FUNCTION_APP.read_text(encoding="utf-8")


def niveles(codigo: str) -> dict[str, str]:
    """Que nivel de autenticacion declara cada ruta."""
    return {
        hallado.group("ruta"): hallado.group("nivel")
        for hallado in PATRON_RUTA.finditer(codigo)
    }


def test_f019_r30_la_cabecera_dice_donde_esta_la_proteccion_de_verdad(codigo):
    """R30 · el backend enlazado, la regla `/*` y el grupo.

    No basta con decir «esta anonimo y no pasa nada»: quien lea esto tiene que
    salir sabiendo **quien impide el paso**, y que no hay nada que configurar
    porque lo pone la plataforma. Sin eso, alguien se pone a apretar tuercas
    en Azure que ya estan apretadas -que es lo que casi pasa en la primera
    ronda de la spec de F-019- o, peor, deja escrito que el servicio esta mas
    desprotegido de lo que esta.
    """
    cabecera = codigo[: codigo.index("from __future__")]

    assert "azureStaticWebApps" in cabecera
    assert "Easy Auth" in cabecera
    assert "staticwebapp.config.json" in cabecera
    assert "irrelevante desde" in cabecera


def test_f019_r30_la_cabecera_dice_que_anade_la_cola_al_cuadro(codigo):
    """R30 · `GET /api/cola` cambia el modelo de amenaza, y hay que decirlo.

    Es el primer endpoint que devuelve dato personal acumulado sin que el
    llamante aporte el PDF. La exposicion que crea no es hacia internet: es
    hacia un usuario ya autenticado del grupo, y el riesgo real es el volumen.
    Quien lo lea al reves protegera de lo que no toca.
    """
    cabecera = codigo[: codigo.index("from __future__")]

    assert "/api/cola" in cabecera
    assert "dato personal acumulado" in cabecera
    assert "volumen" in cabecera
    assert "tope duro" in cabecera


def test_f010_r32_la_anonimidad_es_deliberada_y_esta_explicada(codigo):
    """R32 · los nueve siguen anonimos **y** la cabecera dice por que.

    Las dos mitades en un solo test, y no en dos, porque lo que hay que
    impedir es que se separen: un `auth_level` cambiado con la nota intacta
    deja una mentira en la cabecera, y una nota borrada con el `auth_level`
    intacto deja un endpoint anonimo sin explicacion, que es como estaba antes
    de F-010.
    """
    declarados = niveles(codigo)

    assert sorted(declarados) == sorted(ENDPOINTS)
    assert set(declarados.values()) == {"ANONYMOUS"}

    cabecera = codigo[: codigo.index("from __future__")]
    assert "no es un descuido" in cabecera
    assert "backend enlazado" in cabecera
    assert "x-ms-client-principal" in cabecera
    assert "auth_level=FUNCTION` no vale" in cabecera


def test_f010_r32_la_cabecera_dice_donde_esta_el_control_de_acceso(codigo):
    """R32 · «esta anonimo» sin decir «y entonces quien decide» no vale.

    Quien lea esto tiene que salir sabiendo las cuatro capas, y sobre todo la
    segunda: la ventana de escritura es el candado que si controlamos.
    """
    cabecera = codigo[: codigo.index("from __future__")]

    assert "control de acceso" in cabecera
    assert "grupo de Posventa" in cabecera
    assert "ARCHIVO_HABILITADO" in cabecera
    assert "apagado" in cabecera
    assert "tope de gasto" in cabecera.lower()


def test_f010_r32_la_cabecera_avisa_de_que_la_cabecera_de_identidad_no_protege(codigo):
    """R32 · `x-ms-client-principal` es base64 SIN firma.

    Es la trampa fina de este montaje: la cabecera esta ahi, se lee, parece
    una prueba de identidad y cualquiera que llame a la Function directamente
    puede fabricarla. Quien no lo sepa la usara como control de acceso.
    """
    cabecera = codigo[: codigo.index("from __future__")]

    assert "sin firma" in cabecera
    assert "fabricarla" in cabecera


def test_f010_r18_health_sigue_anonimo(codigo):
    """R18 · y seguiria anonimo aunque lo demas no lo fuera.

    Lo usan el propio despliegue y el front para saber si el backend responde,
    y no expone ningun dato. Protegerlo seria quedarse sin la unica senal que
    se puede mirar desde fuera cuando algo va mal.
    """
    assert niveles(codigo)["health"] == "ANONYMOUS"

    cabecera = codigo[: codigo.index("from __future__")]
    assert "seguiría siendo anónimo" in cabecera


def test_f010_r33_la_cabecera_apunta_a_la_ventana_de_escritura_en_archivar(codigo):
    """R33 · quien lea el endpoint que escribe tiene que dar con la nota.

    La explicacion larga vive al final del modulo; la entrada de `archivar` en
    la lista de arriba manda alli. Sin ese puente, la nota se lee solo si
    alguien baja hasta el final por casualidad.
    """
    assert "ventana de escritura cerrada" in codigo
    assert "nota del final de este" in codigo


def test_f010_r32_el_barrido_de_niveles_ve_lo_que_hay(codigo):
    """Control negativo: un patron que no encuentra nada no fija nada.

    Si manana el decorador se escribe de otra forma y el patron deja de
    casar, `niveles()` devolveria un diccionario vacio y los tests de arriba
    pasarian sin comprobar nada. Este los sostiene.
    """
    assert len(niveles(codigo)) == len(ENDPOINTS) == 9
    assert PATRON_RUTA.findall("@app.route(route=\"x\", auth_level=func.AuthLevel.FUNCTION)") == [
        ("x", "FUNCTION")
    ]
