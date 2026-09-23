# services/postventa-api/tests/test_f010_tarjeta_portal.py
"""El bloque de la tarjeta del portal esta escrito y completo (R23, R24, R25).

La tarjeta vive en OTRO repositorio (`front-portal`) y ningun agente de este la
toca. Lo que F-010 entrega -y lo que su criterio de aceptacion pide- es que
**quede escrito que hay que cambiar**: el bloque literal y el procedimiento.

Por que esto es un test y no una revision a ojo: un bloque de catalogo al que
le falta un campo obligatorio no da error, da una tarjeta que no se pinta o que
se pinta mal, y el fallo aparece en el portal de otro proyecto, donde nadie va
a sospechar de este repositorio. Los nueve campos del esquema de
`azure-apps/portal.md` seccion 4.1 se comprueban aqui, uno a uno.

Y el `requiredGroupId` se comprueba DOS veces por dos motivos distintos: que
sea un marcador (R24, para que el barrido de identificadores del repositorio
siga en verde) y que el documento avise de que un marcador sin rellenar deja la
tarjeta velada en Azure, que es lo que de verdad pasa cuando alguien pega el
bloque y se olvida del paso 2.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Raiz del repositorio, tres niveles por encima de este fichero.
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

#: El runbook, que es el entregable de T10.
DESPLIEGUE = RAIZ / "docs" / "DESPLIEGUE.md"

#: Los nueve campos obligatorios del esquema del catalogo.
CAMPOS_DEL_CATALOGO = (
    "id",
    "title",
    "description",
    "category",
    "icon",
    "url",
    "requiredGroupName",
    "requiredGroupId",
    "comingSoon",
)

#: Los cuatro pasos del alta, segun `azure-apps/portal.md` seccion 8.2.
PASOS_DEL_ALTA = ("catalog.js", "requiredGroupId", "deploy.ps1", "/.auth/logout")

#: La forma de un GUID. En este documento no puede haber ninguno.
PATRON_GUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)


@pytest.fixture
def runbook() -> str:
    return DESPLIEGUE.read_text(encoding="utf-8")


@pytest.fixture
def bloque(runbook: str) -> str:
    """El bloque `js` **de la tarjeta**, aislado de la prosa que lo rodea.

    Se busca por su contenido y no por ser el primero: desde que el runbook
    trae tambien el fragmento de consola de T18 (defecto 13, seccion 5 bis),
    «el primer bloque js» ya no es la tarjeta, y estos tests estarian
    afirmando sobre otra cosa sin enterarse.
    """
    candidatos = [
        hallado
        for hallado in re.findall(r"```js\n(.*?)```", runbook, re.DOTALL)
        if "requiredGroupId" in hallado
    ]
    assert candidatos, "el runbook no trae el bloque de la tarjeta"
    return candidatos[0]


def test_f010_t10_el_runbook_existe():
    """Sin el, el criterio de aceptacion de la feature no se cumple."""
    assert DESPLIEGUE.is_file()


@pytest.mark.parametrize("campo", CAMPOS_DEL_CATALOGO)
def test_f010_r23_el_bloque_trae_los_nueve_campos(bloque, campo):
    """R23 · el esquema entero, no «los que hacian falta».

    Un campo que falta no da error: da una tarjeta mal pintada en el portal de
    otro proyecto.
    """
    assert re.search(rf"^\s*{campo}:", bloque, re.MULTILINE) is not None


def test_f010_r23_el_bloque_nombra_el_grupo_y_la_categoria_del_ecosistema(bloque):
    """El nombre del grupo tiene que ser el mismo de los otros dos sitios.

    Y la categoria, una que el portal ya conoce: si no existe en
    `categoryOrder`, la seccion se va al final por orden alfabetico.
    """
    assert 'requiredGroupName: "posventa-usuarios"' in bloque
    assert 'category: "Obra"' in bloque
    assert "comingSoon: false" in bloque


def test_f010_r24_el_identificador_del_grupo_es_un_marcador(bloque):
    """R24 · un GUID real aqui hace fallar el barrido del repositorio.

    Y ademas seria un identificador de Entra en el historial de git, que no
    suelta lo que entra. El valor se rellena en `front-portal`.
    """
    assert "REEMPLAZAR_ID_GRUPO_POSVENTA" in bloque
    assert PATRON_GUID.findall(bloque) == []


def test_f010_r24_el_runbook_entero_no_lleva_ningun_identificador(runbook):
    """R24 · ni en el bloque, ni en los ejemplos, ni en la prosa."""
    assert PATRON_GUID.findall(runbook) == []


@pytest.mark.parametrize("paso", PASOS_DEL_ALTA)
def test_f010_r25_el_procedimiento_nombra_los_cuatro_pasos(runbook, paso):
    """R25 · pegar, rellenar el GUID, desplegar y volver a entrar.

    El cuarto es el que siempre se olvida: el token trae los grupos que el
    usuario tenia en el momento de pedirlo, asi que meter a alguien en el
    grupo no basta.
    """
    assert paso in runbook


def test_f010_r25_el_procedimiento_no_fija_quien_lo_ejecuta(runbook):
    """R25 · dos vias abiertas, y ninguna dada por hecha.

    `front-portal` es un repositorio con historial propio y commits del
    humano, a diferencia de `azure-apps`; pero el alta exige ademas desplegar,
    que es un acto sobre Azure. Ni suponer que lo hara el humano ni suponer lo
    contrario: el procedimiento sirve para las dos.
    """
    assert "no supone" in runbook
    assert "quien lleve `front-portal`" in runbook


def test_f010_t10_el_runbook_repite_los_dos_avisos_del_portal(runbook):
    """Los dos ya rompieron una tarjeta, y los dos se olvidan igual.

    Uno se manifiesta como «funciona en local y no en Azure»; el otro, como
    «a mi no me sale y a ti si». Ninguno de los dos se diagnostica solo.
    """
    assert "velada" in runbook
    assert "Ctrl+F5" in runbook
    assert "empareja por nombre" in runbook


def test_f010_r34_el_runbook_trae_las_dos_lineas_de_la_ventana_de_escritura(runbook):
    """R34 · abrir y cerrar sin redesplegar y sin tocar codigo.

    Las dos lineas sueltas, una por linea, porque se pegan en una consola. Y
    la de cerrar tiene que estar: una ventana que solo se sabe abrir se queda
    abierta.
    """
    assert "ARCHIVO_HABILITADO=true" in runbook
    assert "ARCHIVO_HABILITADO=false" in runbook
    # Hasta el 2026-09-22 aqui se exigia «Se cierra **siempre** al terminar»:
    # la ventana nacia cerrada en cada despliegue. Desde el 2026-09-23 nace
    # ABIERTA (decision del humano, enmienda bajo R33 de F-010), y lo que el
    # runbook tiene que decir es como se despliega cerrada y que el siguiente
    # despliegue la vuelve a abrir: quien la cierre a mano y no lo sepa, la
    # vera abierta tras la siguiente publicacion.
    assert "-VentanasCerradas" in runbook
    assert "El siguiente despliegue la vuelve a abrir" in runbook


def test_despliegue_ventanas_el_runbook_dice_la_decision_y_el_riesgo(runbook):
    """2026-09-23 · abiertas por defecto, el codigo sin cambiar, y el riesgo.

    Una puerta que el despliegue deja abierta sin que el runbook diga por que,
    quien lo decidio, que el defecto del codigo sigue apagado y que riesgo se
    acepto es una puerta que el siguiente cierra «porque parece un descuido»,
    o que nadie sabe que esta abierta.
    """
    texto = " ".join(runbook.split())

    assert "2026-09-23" in texto
    assert "`config/settings.py`" in texto
    assert "Riesgo aceptado" in texto
    assert "sin una puerta manual" in texto
    assert "Mientras F-034 no esté desplegada" in texto


def test_f010_t10_el_runbook_explica_por_que_los_endpoints_son_anonimos(runbook):
    """Quien lea el runbook antes de desplegar tiene que encontrarselo alli.

    Es el sitio donde mira quien va a tocar Azure, y es justo quien podria
    «arreglar» el `auth_level`.
    """
    assert "la plataforma lo exige" in runbook
    assert "auth_level=FUNCTION" in runbook


def test_f010_defecto13_el_runbook_trae_la_via_de_t18_por_la_consola(runbook):
    """Defecto 13 · el host desnudo de la Function ya no acepta la llamada.

    El comando de T18 —`verificar_archivo_dev.ps1 -BaseUrl <host>`— recibe el
    400 de Easy Auth desde que el backend esta enlazado a la Static Web App.
    La via que si funciona se ejecuto el 2026-08-25 desde la consola del
    navegador, y el fragmento tiene que vivir aqui: en un fichero suelto del
    escritorio de alguien no sobrevive a la siguiente sesion.
    """
    assert "5 bis" in runbook
    assert "azureStaticWebApps" in runbook
    assert "F12" in runbook
    assert 'fetch("/api/archivar"' in runbook


def test_f010_defecto13_el_fragmento_de_consola_llama_al_mismo_origen(runbook):
    """R8 · y por eso el fragmento no lleva ni una URL: es del mismo origen.

    Escribir ahi el host del front seria meter en el repositorio justo lo que
    todos los scripts se cuidan de no traer, y ademas romperia la unica gracia
    del metodo: que la peticion pase por el proxy que autentica.
    """
    fragmentos = [
        bloque
        for bloque in re.findall(r"```js\n(.*?)```", runbook, re.DOTALL)
        if "fetch(" in bloque
    ]

    assert fragmentos, "el runbook no trae el fragmento de consola de T18"
    for fragmento in fragmentos:
        assert "http://" not in fragmento
        assert "https://" not in fragmento


def test_f010_t10_el_runbook_dice_que_no_esta_desplegado(runbook):
    """El entorno tiene que ser util y HONESTO sin el cierre en Sigrid.

    Que se sepa antes de la demostracion, no durante.
    """
    assert "F-008" in runbook
    assert "F-019" in runbook
    assert "recarga la página" in runbook
