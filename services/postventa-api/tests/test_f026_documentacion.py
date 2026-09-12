# services/postventa-api/tests/test_f026_documentacion.py
"""Las enmiendas y la documentación que F-026 deja al día (R46, R47).

Mismo objeto que `test_f025_documentacion.py`, y por la misma razón: lo que
aquí se vigila **no es un documento técnico, es la memoria de una decisión**.
F-026 abre una puerta que tres documentos aprobados declaran cerrada —R36 de
F-025 y tres puntos de `docs/ARCHITECTURE.md`— y la regla del proyecto es que
**lo que se deroga no se borra**: se enmienda con un recuadro fechado que cita
la premisa original **literal**, dice qué la invalidó, quién lo decidió y
cuándo. El patrón exacto es el de R28 de `specs/F-010-despliegue/`, del
2026-09-03, y ya lo siguió F-025 el 2026-09-11.

El motivo de que esto sea un test y no una revisión: dentro de seis meses,
alguien que lea «solo se archiva lo que el paso 4 declaró apto» sin el
recuadro creerá que `_exigir_admitido` es un agujero y lo «arreglará» hasta
dejar otra vez bloqueados para siempre los partes que una persona aprobó. Lo
que sobrevive a la siguiente edición no es una revisión, es un test.

Lo que fija:

- **R46** · bajo R36 de F-025 hay un recuadro fechado que cita su texto
  literal, dice que cae **solo su última frase**, y separa lo que dijo el
  responsable de lo que interpretó el líder.
- **R47** · los **tres** puntos de `docs/ARCHITECTURE.md` que hoy afirman lo
  contrario quedan **precisados, no borrados**: siguen diciendo lo que decían
  para todo lo demás, y añaden la puerta nueva diciendo que es **más estrecha**
  que la que abrían.

Lo que **no** se comprueba aquí es R49: el documento del ecosistema vive en
`azure-apps/`, que es **otro repositorio**, y un test de esta suite que
dependiera de que ese repositorio esté clonado al lado fallaría en cualquier
máquina donde no lo esté. Su verificación es la declarada en `tasks.md` (T19):
commit aparte en ese repositorio y `git status` limpio.
"""

from __future__ import annotations

from pathlib import Path

import pytest

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
REQ_F025 = RAIZ / "specs" / "F-025-confirmacion-unica" / "requirements.md"

#: La fecha en que se escriben las enmiendas. Un recuadro sin fecha no es
#: constancia: es una opinión.
FECHA = "2026-09-12"

#: La fecha en que el responsable resolvió las preguntas abiertas de F-026.
#: Va aparte de la anterior a propósito: **decidir** y **dejar constancia** son
#: dos actos, y confundirlos hace imposible saber cuánto tardó el segundo.
FECHA_DECISION = "2026-09-11"

#: Las palabras del responsable sobre qué pasa con los partes no aptos. Son la
#: prueba de que la puerta la abrió una persona y no un agente «desatascando»
#: la cola.
CITA_DECISION = (
    "Los partes no aptos no se archivan hasta que no se aprueban por revisor "
    "humano. En ese momento pasan a aprobados y entrarían en el proceso normal."
)

#: Dónde vive la aprobación, también con sus palabras.
CITA_GUARDARLO = "hay que guardarlo"
CITA_SIGRID = "no hace falta que conste en Sigrid, sí en nuestra base"

#: Y lo que pidió para las correcciones, que es lo contrario y por eso importa.
CITA_SIN_BOTON = (
    "escribir en un campo debe guardar lo que escribes, según escribe guarda, "
    "sin botón"
)


def _llano(texto: str) -> str:
    """Quita los adornos de Markdown que no son contenido y aplana los saltos.

    Estos documentos van envueltos a 79 columnas y los recuadros llevan `> ` al
    principio de cada línea. Comparar contra el texto envuelto haría que un
    simple reajuste de márgenes pusiera el test en rojo **sin que la constancia
    hubiera cambiado**, y un test que se rompe por motivos falsos acaba
    borrado. Lo que aquí se vigila es lo que el recuadro **dice**, no cómo está
    partido.
    """
    sin_cita = "\n".join(
        linea.lstrip().removeprefix(">").lstrip() for linea in texto.splitlines()
    )
    return " ".join(sin_cita.split())


def _bloque(texto: str, requisito: str, siguiente: str) -> str:
    """Devuelve, ya aplanado, el trozo del documento entre dos marcas.

    Sirve para comprobar que el recuadro está **bajo el punto que enmienda** y
    no en cualquier otro sitio del fichero: un recuadro traspapelado no lo lee
    quien lee el punto, que es justo a quien va dirigido.
    """
    assert requisito in texto, f"no se encuentra {requisito!r}"
    assert siguiente in texto, f"no se encuentra {siguiente!r}"
    desde = texto.index(requisito)
    hasta = texto.index(siguiente, desde)
    assert hasta > desde, f"{siguiente!r} no va después de {requisito!r}"
    return _llano(texto[desde:hasta])


def _bloque_r36() -> str:
    """El trozo de F-025 que va de R36 a R37, ya aplanado."""
    return _bloque(REQ_F025.read_text(encoding="utf-8"), "**R36.**", "**R37.**")


#: Los tres puntos de `docs/ARCHITECTURE.md` que R47 manda precisar, con la
#: marca que abre cada uno y la que lo cierra. Son los tres literales que cita
#: el propio requisito, ni uno más.
PUNTOS_DE_ARQUITECTURA = [
    pytest.param(
        "6. **Archivo**",
        "7a. **Gráfico**",
        "Solo se archiva lo que el paso 4 declaró apto",
        id="paso-6-del-pipeline",
    ),
    pytest.param(
        "3. **La firma debe ser humana.**",
        "4. **Lo manuscrito es dato de primera",
        "Un parte sin firma válida no se archiva ni se cierra: va a revisión manual.",
        id="semantica-3",
    ),
    pytest.param(
        "7. **Nada se archiva ni se cierra si no ha pasado todas las validaciones.**",
        "8. **El nombre del fichero",
        "Nada se archiva ni se cierra si no ha pasado todas las validaciones.",
        id="semantica-7",
    ),
]


# --------------------------------------------------------------------------
# R46 · R36 de F-025 queda enmendado, con su recuadro
# --------------------------------------------------------------------------


def test_f026_r46_bajo_r36_de_f025_hay_un_recuadro_de_enmienda_fechado():
    """R46 · el recuadro existe, está fechado y nombra a la feature que lo trae.

    Sin la fecha no se puede juzgar la decisión —no se sabe qué se sabía
    cuando se tomó—, y sin el número de feature no se puede ir a leer el
    porqué completo.
    """
    bloque = _bloque_r36()

    assert "Enmienda" in bloque
    assert FECHA in bloque
    assert "F-026" in bloque


def test_f026_r46_el_recuadro_de_r36_cita_la_premisa_literal():
    """R46 · **literal**, no resumida.

    Resumir la premisa original es exactamente la forma de que dentro de seis
    meses nadie pueda juzgar si la decisión fue buena: lo que se juzga es lo
    que decía el requisito, no lo que recordaba quien lo enmendó.
    """
    bloque = _bloque_r36()
    recuadro = bloque[bloque.index("Enmienda") :]

    assert "ni siquiera dentro de la tanda y ni siquiera si el usuario pulsa" in recuadro
    assert "Los partes en revisión y los de la cola humana siguen fuera" in recuadro


def test_f026_r46_el_recuadro_de_r36_dice_que_solo_cae_la_ultima_frase():
    """R46 · lo que cae es una frase, no el requisito.

    Es la confusión que más daño haría de todas: «R36 está enmendado» leído
    como «R36 ya no rige» deja el circuito archivando y cerrando cualquier
    parte que la validación rechazó. Lo único que cambia es que un no apto
    **aprobado y vigente** entra; todo lo demás sigue prohibido, y sigue
    comprobándose en los tres pasos del backend.
    """
    bloque = _bloque_r36()

    assert "si y solo si consta aprobado y vigente" in bloque
    assert "La prohibición sigue entera" in bloque
    assert "los tres pasos del backend" in bloque


def test_f026_r46_el_recuadro_de_r36_dice_que_la_aprobacion_no_viene_del_cuerpo():
    """R46 · dónde se lee la aprobación, que es la mitad de la garantía.

    Una puerta que se abre con un campo del cuerpo de la petición no es una
    puerta: la abre cualquiera que sepa escribir JSON. La aprobación se lee
    **del repositorio**, y esa frase es la que impide que alguien «simplifique»
    el handler aceptando un `aprobado: true` de fuera.
    """
    bloque = _bloque_r36()

    assert "del repositorio, nunca del cuerpo" in bloque


def test_f026_r46_el_recuadro_de_r36_dice_quien_lo_decidio_y_con_que_palabras():
    """R46 · quién, cuándo y con qué palabras.

    Abrir el archivo de Posventa y el cierre del ERP a partes que la validación
    automática rechazó es una decisión de negocio, no de ingeniería. Que conste
    quién la tomó, cuándo y con qué palabras es lo que convierte el riesgo en
    **aceptado** en vez de en **inadvertido**.
    """
    bloque = _bloque_r36()

    assert "responsable" in bloque
    assert FECHA_DECISION in bloque
    assert CITA_DECISION in bloque
    assert CITA_GUARDARLO in bloque
    assert CITA_SIGRID in bloque


def test_f026_r46_el_recuadro_de_r36_separa_la_interpretacion_del_lider():
    """R46 · lo que dijo el responsable y lo que interpretó el líder, aparte.

    El responsable pidió que **escribir guarde sin botón**. Que **aprobar** sí
    lleve botón no sale de sus palabras: es interpretación del líder, y
    apuntarla como si fuera suya sería atribuirle una decisión que no tomó.
    Quien mañana quiera quitar el botón tiene derecho a saber que discute con
    una interpretación y no con el responsable.
    """
    bloque = _bloque_r36()

    assert "interpretación del líder" in bloque
    assert "no un pronunciamiento del responsable" in bloque
    assert CITA_SIN_BOTON in bloque


def test_f026_r46_el_recuadro_de_r36_dice_que_f025_sigue_done():
    """R46 · enmendar no es reabrir.

    Sin esta línea, el recuadro parece una feature reabierta y el reviewer
    siguiente no sabe si F-025 vuelve a estar en juego. Y con ella queda dicho
    lo que de verdad importa de F-025 aquí: la confirmación **sigue siendo una
    sola**, porque aprobar no arma ninguna confirmación nueva (R29).
    """
    bloque = _bloque_r36()

    assert "F-025 sigue `done`" in bloque
    assert "R29" in bloque


def test_f026_r46_el_texto_original_de_r36_no_se_ha_borrado():
    """R46 · **control negativo del control negativo.**

    El recuadro no vale de nada si el requisito que enmienda ha desaparecido:
    lo que se juzga dentro de seis meses es el texto original, con su recuadro
    debajo.
    """
    texto = _llano(REQ_F025.read_text(encoding="utf-8"))

    assert (
        "**R36.** El sistema **no debe** archivar, adjuntar ni cerrar un parte "
        "que no sea `apto` con destino `archivo_y_cierre`, ni siquiera dentro "
        "de la tanda y ni siquiera si el usuario pulsa dos veces. Los partes en "
        "revisión y los de la cola humana **siguen fuera** (aprobarlos es "
        "**F-026**)." in texto
    )


# --------------------------------------------------------------------------
# R47 · los tres puntos de docs/ARCHITECTURE.md
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("abre", "cierra", "original"), PUNTOS_DE_ARQUITECTURA)
def test_f026_r47_los_tres_puntos_conservan_su_texto(abre, cierra, original):
    """R47 · **precisión, no borrado**, y este es el control negativo.

    La verificación de T18 lo pide con todas las letras: los tres puntos
    «siguen diciendo lo que decían para todo lo demás». Si alguien resolviera
    la contradicción borrando la frase, `ARCHITECTURE.md` dejaría de decir la
    regla general —que es la que rige el 95 % de los partes— para describir
    solo la excepción.
    """
    bloque = _bloque(ARQUITECTURA.read_text(encoding="utf-8"), abre, cierra)

    assert original in bloque


@pytest.mark.parametrize(("abre", "cierra", "original"), PUNTOS_DE_ARQUITECTURA)
def test_f026_r47_los_tres_puntos_nombran_la_aprobacion_humana(abre, cierra, original):
    """R47 · los **tres**, con la misma fórmula y la misma remisión.

    Que sean tres y no uno no es burocracia: quien lee el pipeline no lee la
    semántica, y al revés. Un documento que dice la excepción en un punto y la
    niega en los otros dos es peor que uno que no la dijera en ninguno, porque
    el lector se queda con el que leyó.
    """
    bloque = _bloque(ARQUITECTURA.read_text(encoding="utf-8"), abre, cierra)

    assert "salvo aprobación humana registrada" in bloque
    assert "F-026" in bloque
    assert FECHA in bloque


@pytest.mark.parametrize(("abre", "cierra", "original"), PUNTOS_DE_ARQUITECTURA)
def test_f026_r47_los_tres_puntos_dicen_que_la_puerta_es_mas_estrecha(
    abre, cierra, original
):
    """R47 · la frase que impide leer la enmienda como una barra libre.

    Es literalmente lo que dice el requisito: la aprobación humana es «una
    puerta más estrecha que la que abrían», porque exige una persona, un parte
    concreto, un motivo aprobable y un registro. Sin esta frase, «salvo
    aprobación humana» se lee como «salvo que alguien lo quiera», que es otra
    cosa.
    """
    bloque = _bloque(ARQUITECTURA.read_text(encoding="utf-8"), abre, cierra)

    assert "más estrecha" in bloque
    assert "motivo aprobable" in bloque
    assert "postventa.aprobaciones" in bloque
    assert "Nunca es automática" in bloque


def test_f026_r47_la_semantica_7_dice_que_la_aprobacion_no_va_a_sigrid():
    """R47 · lo que decidió el responsable sobre el ERP, en el punto del ERP.

    La semántica 7 es la que habla de cerrar en Sigrid. Quien lea ahí que un
    parte no apto puede acabar cerrado pensará —con razón— que el ERP debería
    enterarse de que lo cerró una persona a pesar de la máquina. La respuesta
    del responsable fue que no: consta en nuestra base y en ninguna otra. Si no
    está escrito aquí, la pregunta vuelve, y la siguiente vez a lo mejor se
    contesta escribiendo en producción.
    """
    bloque = _bloque(
        ARQUITECTURA.read_text(encoding="utf-8"),
        "7. **Nada se archiva ni se cierra si no ha pasado todas las validaciones.**",
        "8. **El nombre del fichero",
    )

    assert "no se escribe en Sigrid" in bloque


@pytest.mark.parametrize(
    ("abre", "cierra", "conservado"),
    [
        pytest.param(
            "6. **Archivo**",
            "7a. **Gráfico**",
            "con cualquier otro destino no se sube nada",
            id="paso-6-sigue-cerrado-para-lo-demas",
        ),
        pytest.param(
            "3. **La firma debe ser humana.**",
            "4. **Lo manuscrito es dato de primera",
            "Solo firma el cliente",
            id="semantica-3-sigue-exigiendo-firma-humana",
        ),
        pytest.param(
            "7. **Nada se archiva ni se cierra si no ha pasado todas las validaciones.**",
            "8. **El nombre del fichero",
            "Archivar un parte inválido ensucia el archivo de Posventa",
            id="semantica-7-conserva-su-motivo",
        ),
    ],
)
def test_f026_r47_la_precision_no_se_ha_llevado_por_delante_el_resto(
    abre, cierra, conservado
):
    """R47 · segundo control negativo: el **motivo** de cada punto sigue ahí.

    Un punto al que se le añade la excepción y se le quita el razonamiento
    queda convertido en una regla arbitraria, y las reglas arbitrarias se
    borran en la siguiente limpieza. Lo que sostiene los tres puntos —que
    archivar basura ensucia el archivo de Posventa, que una aspa no es una
    firma, que con otro destino no se sube nada— no lo toca F-026.
    """
    bloque = _bloque(ARQUITECTURA.read_text(encoding="utf-8"), abre, cierra)

    assert conservado in bloque
