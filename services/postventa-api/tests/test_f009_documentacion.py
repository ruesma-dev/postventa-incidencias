# services/postventa-api/tests/test_f009_documentacion.py
"""La documentación que F-009 deja al día (R52, y T19/T20 de `tasks.md`).

Al modo de `test_f019_documentacion.py`. Un documento desactualizado que parece
vigente hace más daño que no tenerlo, y eso vale doble aquí: lo que estos
documentos describen es **la única escritura de este proyecto en un ERP de
producción**, y quien los lee es quien administra la pasarela o el ERP.

Lo que fija:

- **R52** · `docs/INTEGRACION.md` nombra las variables nuevas y **ningún
  valor**.
- **`docs/ARCHITECTURE.md`** dice el orden decidido —validar → cerrar → subir
  el PDF— y **el riesgo aceptado, sin suavizarlo**. `tasks.md` T19 lo pide con
  esas palabras porque lo que había antes decía que el alcance «está en el
  aire», y dejarlo así sería documentar una feature que ya existe como si no
  se hubiera decidido nada.
- **`docs/DESPLIEGUE.md`** explica la App Setting del interruptor y cómo se
  abre y se cierra.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from infrastructure.sigrid.fabrica import VARIABLES_OBLIGATORIAS

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"
DESPLIEGUE = RAIZ / "docs" / "DESPLIEGUE.md"

#: Las ocho variables que F-009 añade. Se nombran; sus valores, jamás.
VARIABLES_DE_F009 = (
    "CIERRE_HABILITADO",
    "SIGRID_API_BASE_URL",
    "SIGRID_API_KEY",
    "SIGRID_BASE_DATOS",
    "SIGRID_TIMEOUT_S",
    "SIGRID_REINTENTOS",
    "SIGRID_TIP_RECLAMACION",
    "SIGRID_ZONA_HORARIA",
)

#: Un nombre de host real de la pasarela o del servidor de base de datos.
PATRON_HOST_AZURE = re.compile(
    r"[\w-]+\.(?:azurewebsites\.net|postgres\.database\.azure\.com)",
    re.IGNORECASE,
)

#: Una clave de función: la que sirve la pasarela es una cadena larga en
#: base64url. Cualquier valor con esa pinta pegado a una variable es un
#: secreto en el repositorio.
PATRON_VALOR_DE_SECRETO = re.compile(
    r"SIGRID_API_KEY\s*[=:]\s*[\"']?[A-Za-z0-9+/=_-]{20,}",
)


# --------------------------------------------------------------------------
# R52 · INTEGRACION.md nombra las variables y ningún valor
# --------------------------------------------------------------------------


@pytest.mark.parametrize("variable", VARIABLES_DE_F009)
def test_f009_r52_integracion_nombra_las_variables_nuevas(variable):
    """R52 · quien despliegue tiene que poder saber qué hay que configurar.

    Sin esto, la lista de variables solo vive en el código, y quien administra
    la pasarela no puede saber qué le estamos pidiendo.
    """
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert variable in texto, f"INTEGRACION.md no nombra {variable}"


def test_f009_r52_integracion_no_trae_el_valor_de_ningun_secreto():
    """R52 · nombres, **jamás** valores. Y el historial de git no suelta nada.

    Este documento existe para ser leído por gente de otros proyectos, así que
    es el fichero con más probabilidad de acabar llevando «la URL de verdad
    para que se entienda mejor».
    """
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert PATRON_VALOR_DE_SECRETO.search(texto) is None
    assert PATRON_HOST_AZURE.findall(texto) == []


def test_f009_r52_la_lista_documentada_cubre_las_obligatorias_de_la_fabrica():
    """R52 · si mañana la fábrica exige una variable más, este test lo dice.

    Se comprueba contra `VARIABLES_OBLIGATORIAS` y no contra una lista escrita
    a mano: dos listas del mismo concepto divergen, y la que se quedaría corta
    sería la de la documentación.
    """
    documentadas = set(VARIABLES_DE_F009)

    for _campo, variable in VARIABLES_OBLIGATORIAS:
        assert variable in documentadas
        assert variable in INTEGRACION.read_text(encoding="utf-8")


def test_f009_r52_integracion_dice_que_ahora_ESCRIBIMOS_en_el_erp():
    """R52 · el cambio que de verdad hay que contar.

    Hasta F-009 este proyecto solo leía de Sigrid. Un documento que siga
    diciendo «lectura de la incidencia» describe otro proyecto.
    """
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert "ESCRITURA en el ERP de producción" in texto
    assert "dbo.log" in texto


def test_f009_r52_integracion_dice_que_se_rompe_si_tocan_la_pasarela():
    """R52 · lo que de verdad necesita saber el dueño de `sigrid-api`.

    Un documento que solo diga «usamos la pasarela» no evita que alguien le
    quite el `UPDATE` de la lista blanca un martes.
    """
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert "ALLOWED_WRITE_PREFIXES" in texto
    assert "ALLOWED_WRITE_DATABASES" in texto


def test_f009_integracion_declara_el_endpoint_que_escribe_en_el_erp():
    """El inventario de endpoints tiene que decir cuál toca producción."""
    texto = INTEGRACION.read_text(encoding="utf-8")

    assert "`POST /api/cerrar`" in texto


# --------------------------------------------------------------------------
# T19 · ARCHITECTURE.md: el orden decidido y el riesgo, sin suavizar
# --------------------------------------------------------------------------


def test_f009_t19_arquitectura_declara_el_orden_decidido():
    """T19 · validar → cerrar → subir el PDF, con esas palabras.

    Lo que había antes decía que el alcance «está en el aire». Dejarlo así
    sería documentar como indecisa una feature que ya está implementada.
    """
    texto = ARQUITECTURA.read_text(encoding="utf-8")

    assert "validar → cerrar → subir el PDF" in texto
    # El documento sí dice «Ya no está en el aire», que es la frase que cierra
    # la duda. Lo que no puede quedar es la afirmación en presente.
    assert "el alcance del cierre en v1 está en el aire" not in texto


def test_f009_t19_arquitectura_escribe_el_riesgo_aceptado_sin_suavizarlo():
    """T19 · **sin suavizarlo**, que es como lo pide `tasks.md`.

    Tiene que decir las dos cosas incómodas: que vamos a producir
    reclamaciones cerradas sin gráfico, y que eso no ha pasado ni una vez en
    los cierres recientes del ERP.
    """
    texto = ARQUITECTURA.read_text(encoding="utf-8")

    assert "RIESGO ACEPTADO" in texto
    assert "sin ninguna fila en `rcg`" in texto
    assert "2.365" in texto


def test_f009_t19_arquitectura_dice_que_el_riesgo_tiene_fecha_de_caducidad():
    """T19 · y qué lo cierra, para que no se lea como algo permanente."""
    texto = ARQUITECTURA.read_text(encoding="utf-8")

    assert "fecha de caducidad" in texto
    assert "F-012" in texto


def test_f009_t19_arquitectura_ya_no_dice_que_f009_dependa_de_sigrid_api():
    """T19 · lo dijo la spec vieja y **es falso**: D3 lo midió.

    Las dos sentencias caben en la pasarela tal y como está desplegada. Dejar
    escrito lo contrario mandaría a quien coja esta feature a pedir un cambio
    en otro repositorio que no hace falta.
    """
    texto = ARQUITECTURA.read_text(encoding="utf-8")

    assert "F-009 depende de un\nendpoint nuevo en `sigrid-api`" not in texto
    assert "**F-009, en cambio, NO exige tocar el repositorio `sigrid-api`**" in texto


def test_f009_t19_arquitectura_declara_las_puertas_del_cierre():
    """T19 · la tabla de sistemas externos dice con qué se protege el ERP."""
    texto = ARQUITECTURA.read_text(encoding="utf-8")

    assert "CIERRE_HABILITADO" in texto
    assert "la escritura no se reintenta jamás" in texto


# --------------------------------------------------------------------------
# T19 · DESPLIEGUE.md: la App Setting y cómo se abre
# --------------------------------------------------------------------------


def test_f009_t19_despliegue_explica_la_ventana_de_escritura_del_cierre():
    """T19 · la App Setting, y **cómo se abre y se cierra**.

    Sin el procedimiento escrito, quien la abra el día del piloto la dejará
    abierta.
    """
    texto = DESPLIEGUE.read_text(encoding="utf-8")

    assert "CIERRE_HABILITADO=true" in texto
    assert "CIERRE_HABILITADO=false" in texto


def test_f009_t19_despliegue_dice_que_la_ventana_no_basta_para_cerrar():
    """T19 · abrirla **no** cierra nada, y hay que decirlo.

    Es la diferencia con la ventana de archivo, y confundirlas haría que
    alguien creyera que ha dejado el ERP abierto de par en par.
    """
    texto = DESPLIEGUE.read_text(encoding="utf-8")

    assert "Lo que la ventana NO sustituye" in texto
    assert "dry-run por omisión" in texto


def test_f009_t19_despliegue_dice_que_el_interruptor_es_una_variable_aparte():
    """T19 · poder archivar no puede implicar poder cerrar.

    Si fueran la misma variable, abrir la ventana para subir unos partes
    abriría a la vez la escritura en el ERP.
    """
    texto = DESPLIEGUE.read_text(encoding="utf-8")

    assert "variable aparte" in texto


def test_f009_t19_despliegue_no_trae_ninguna_url_ni_clave_real():
    """T19 · el procedimiento se explica con nombres, no con valores."""
    texto = DESPLIEGUE.read_text(encoding="utf-8")

    assert PATRON_VALOR_DE_SECRETO.search(texto) is None
