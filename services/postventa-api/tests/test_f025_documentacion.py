# services/postventa-api/tests/test_f025_documentacion.py
"""Las enmiendas y la documentación que F-025 deja al día (R38–R43, R47).

Al modo de `test_f009_documentacion.py` y `test_f012_documentacion.py`, pero
con un objeto distinto: aquí lo que se vigila **no es un documento técnico,
es la memoria de una decisión**. F-025 deroga requisitos aprobados de F-009 y
de F-012 —requisitos que gobiernan dos escrituras en un ERP de producción— y
la regla del proyecto es que **un requisito derogado no se borra**: se enmienda
con un recuadro fechado que cita la premisa original **literal**, dice qué la
invalidó y quién lo decidió (patrón de R28 de `specs/F-010-despliegue/`, del
2026-09-03).

El motivo de que esto sea un test y no una revisión: dentro de seis meses,
alguien que lea R63 de F-012 sin el recuadro creerá que el front tiene que
enseñar dos dry-run antes de confirmar, y «arreglará» el front para que
cumpla un requisito que ya no rige. Lo que sobrevive a la siguiente edición no
es una revisión, es un test.

Lo que fija:

- **R38** · bajo R63 de F-012 hay un recuadro con **DEROGADO**, la fecha
  `2026-09-11`, la cita literal de la premisa y quién lo decidió.
- **R39** · bajo R22 de F-012, el recuadro dice que el «antes de confirmar»
  cayó y que el caso idempotente **se sigue diciendo**.
- **R40** · bajo R21 y R49 de F-012, que el **contrato de respuesta no cambia**
  y lo que cambia es cuándo se lee.
- **R41** · bajo R50 de F-012, que **la regla se queda** y lo que se enmienda
  es su justificación.
- **R42, R43** · en F-009, la nota bajo R8/R10: siguen vigentes, y R21 **no se
  vuelve a derogar** porque ya lo estaba desde el 2026-09-06.
- **R47** · `docs/ARCHITECTURE.md` dice que la confirmación es **una sola** y
  que el cálculo previo ocurre **en la misma llamada** que escribe, sin haber
  borrado la exigencia de dry-run.
"""

from __future__ import annotations

from pathlib import Path

import pytest

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
REQ_F009 = RAIZ / "specs" / "F-009-cierre-sigrid" / "requirements.md"
REQ_F012 = RAIZ / "specs" / "F-012-grafico-sigrid" / "requirements.md"

#: La fecha de la decisión del responsable del proyecto. Un recuadro sin fecha
#: no es constancia: es una opinión.
FECHA = "2026-09-11"

#: Las palabras exactas del responsable. Son la prueba de que la decisión la
#: tomó una persona y no un agente «simplificando» el circuito.
CITA_DECISION = (
    "quiero que al darle a archivar los partes aptos me pida confirmación "
    "como ahora, y al confirmar ya haga el proceso de cierre"
)
CITA_NO_ENSENAR = "no hace falta enseñar nada"


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
    """Devuelve, ya aplanado, el trozo del documento entre dos requisitos.

    Sirve para comprobar que el recuadro está **bajo el requisito que
    enmienda** y no en cualquier otro sitio del fichero: un recuadro
    traspapelado no lo lee quien lee el requisito, que es justo a quien va
    dirigido.
    """
    assert requisito in texto, f"no se encuentra {requisito!r}"
    assert siguiente in texto, f"no se encuentra {siguiente!r}"
    desde = texto.index(requisito)
    hasta = texto.index(siguiente, desde)
    assert hasta > desde, f"{siguiente!r} no va después de {requisito!r}"
    return _llano(texto[desde:hasta])


# --------------------------------------------------------------------------
# R38 · R63 de F-012 queda DEROGADO, con su recuadro
# --------------------------------------------------------------------------


def test_f025_r38_bajo_r63_de_f012_hay_un_recuadro_que_dice_derogado():
    """R38 · la palabra tiene que estar, y en mayúsculas.

    «Enmendado» y «matizado» dejan la duda de si el requisito sigue rigiendo.
    R63 **no rige**: no hay ningún gesto «ver qué pasaría» en el front.
    """
    bloque = _bloque(REQ_F012.read_text(encoding="utf-8"), "**R63.**", "**R64.**")

    assert "DEROGADO" in bloque
    assert FECHA in bloque


def test_f025_r38_el_recuadro_de_r63_cita_la_premisa_literal():
    """R38 · **literal**, no resumida.

    Resumir la premisa original es exactamente la forma de que dentro de seis
    meses nadie pueda juzgar si la decisión fue buena: lo que se juzga es lo
    que decía el requisito, no lo que el que lo derogó recordaba que decía.
    """
    bloque = _bloque(REQ_F012.read_text(encoding="utf-8"), "**R63.**", "**R64.**")
    recuadro = bloque[bloque.index("DEROGADO") :]

    assert "ver qué pasaría" in recuadro
    assert "los dos dry-run" in recuadro
    assert "antes de ofrecer la confirmación" in recuadro


def test_f025_r38_el_recuadro_de_r63_dice_quien_lo_decidio_y_con_que_palabras():
    """R38 · quién, cuándo y con qué palabras.

    Se le planteó explícitamente que esa pantalla es lo que protege de cerrar
    la incidencia equivocada si la extracción leyó mal el número del papel.
    Que esa objeción conste, y que conste la respuesta, es lo que convierte el
    riesgo en **aceptado** en vez de en **inadvertido**.
    """
    bloque = _bloque(REQ_F012.read_text(encoding="utf-8"), "**R63.**", "**R64.**")

    assert "responsable" in bloque
    assert CITA_DECISION in bloque
    assert CITA_NO_ENSENAR in bloque


def test_f025_r38_el_recuadro_de_r63_dice_que_la_comprobacion_previa_no_cae():
    """R38 · la mitad más importante del recuadro.

    Lo que R63 protegía de verdad —no escribir sin haber leído antes el estado
    real de la reclamación— **sigue en pie**, dentro de la misma llamada que
    escribe (R20 de F-012). Sin esta frase, el recuadro se puede leer como
    permiso para quitar también el dry-run del backend, que es justo lo que
    `specs/F-025-confirmacion-unica/requirements.md` §6 prohíbe.
    """
    bloque = _bloque(REQ_F012.read_text(encoding="utf-8"), "**R63.**", "**R64.**")

    assert "dentro de la misma llamada que escribe" in bloque
    assert "R20" in bloque


def test_f025_r38_el_recuadro_de_r63_dice_que_f012_sigue_done():
    """R38 · enmendar no es reabrir.

    Sin esta línea, el recuadro parece una feature reabierta y el reviewer
    siguiente no sabe si F-012 vuelve a estar en juego.
    """
    bloque = _bloque(REQ_F012.read_text(encoding="utf-8"), "**R63.**", "**R64.**")

    assert "F-012 sigue `done`" in bloque


def test_f025_r38_el_texto_original_de_r63_no_se_ha_borrado():
    """R38 · **control negativo del control negativo.**

    El recuadro no vale de nada si el requisito que enmienda ha desaparecido:
    lo que se juzga dentro de seis meses es el texto original, con su recuadro
    debajo.
    """
    texto = _llano(REQ_F012.read_text(encoding="utf-8"))

    assert (
        "**R63.** CUANDO el usuario pide «ver qué pasaría», el front debe pedir "
        "para cada parte cerrable **los dos dry-run** —gráfico y cierre, en ese "
        "orden— y enseñarlos juntos antes de ofrecer la confirmación." in texto
    )


# --------------------------------------------------------------------------
# R39 · R22 de F-012: el momento, no el contenido
# --------------------------------------------------------------------------


def test_f025_r39_bajo_r22_de_f012_el_recuadro_retira_el_antes_de_confirmar():
    """R39 · lo que cae es el «antes», no el aviso.

    Una lectura perezosa del recuadro podría concluir que el caso idempotente
    deja de detectarse. No: se detecta igual, se dice igual, y **sigue siendo
    un éxito** (R25 de F-012). Lo único que cambia es que se lee después.
    """
    bloque = _bloque(REQ_F012.read_text(encoding="utf-8"), "**R22.**", "**R23.**")

    assert FECHA in bloque
    assert "idempotente: true" in bloque
    assert "se sigue detectando y se sigue diciendo" in bloque
    assert "R25" in bloque


def test_f025_r39_el_texto_original_de_r22_no_se_ha_borrado():
    """R39 · íd. que R63: el original se queda."""
    texto = _llano(REQ_F012.read_text(encoding="utf-8"))

    assert (
        "**R22.** SI el dry-run responde `idempotente: true`, ENTONCES el sistema "
        "debe decirlo al usuario **antes** de confirmar: ese parte ya está dentro "
        "de Sigrid y el commit no escribirá nada." in texto
    )


# --------------------------------------------------------------------------
# R40 · R21 y R49 de F-012: el contrato de respuesta no cambia
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("requisito", "siguiente"),
    [("**R21.**", "**R22.**"), ("**R49.**", "**R50.**")],
)
def test_f025_r40_los_recuadros_dicen_que_el_contrato_no_cambia(requisito, siguiente):
    """R40 · **ninguna clave de la respuesta cambia.**

    Es la frase que impide que alguien «limpie» del endpoint el bloque del
    cálculo previo porque «ya no se enseña». Se sigue devolviendo entero: lo
    que cambia es que se lee en el resumen de lo que se hizo, no en una
    pantalla anterior a la confirmación.
    """
    bloque = _bloque(REQ_F012.read_text(encoding="utf-8"), requisito, siguiente)

    assert FECHA in bloque
    assert "el momento cambia" in bloque
    assert "no cambia" in bloque and "clave" in bloque
    assert "resumen de lo que se hizo" in bloque


@pytest.mark.parametrize(
    ("requisito", "siguiente", "trozo"),
    [
        ("**R21.**", "**R22.**", "El dry-run debe devolver al usuario"),
        ("**R49.**", "**R50.**", "debe informar del"),
    ],
)
def test_f025_r40_los_recuadros_citan_la_premisa_literal(requisito, siguiente, trozo):
    """R40 · la cita literal también aquí.

    R21 y R49 no se derogan, pero su **justificación** sí se enmienda, y el
    patrón del proyecto no distingue: se cita literal lo que decía.
    """
    bloque = _bloque(REQ_F012.read_text(encoding="utf-8"), requisito, siguiente)
    recuadro = bloque[bloque.index("**Enmienda") :]

    assert trozo in recuadro


# --------------------------------------------------------------------------
# R41 · R50 de F-012: la regla se queda, su motivo era otro
# --------------------------------------------------------------------------


def test_f025_r41_el_recuadro_de_r50_dice_que_la_regla_se_mantiene():
    """R41 · el caso más fácil de estropear de los cinco.

    R50 dice que el dry-run del cierre **no** exige que el gráfico conste
    adjuntado. Su motivo escrito —«así los dos dry-run se pueden enseñar
    juntos»— cayó con F-025. Quien lea solo eso concluirá que la regla cae con
    él, y endurecerá el endpoint hasta que deje de poder consultarse sin
    escribir. El recuadro existe para cortar esa cadena.
    """
    bloque = _bloque(REQ_F012.read_text(encoding="utf-8"), "**R50.**", "**R51.**")

    assert FECHA in bloque
    assert "La regla se queda" in bloque
    assert "se pueden enseñar juntos antes de confirmar" in bloque
    assert "sin escribir" in bloque


# --------------------------------------------------------------------------
# R42, R43 · F-009: la nota bajo R8/R10
# --------------------------------------------------------------------------


def test_f025_r43_la_nota_de_f009_dice_que_r8_y_r10_siguen_vigentes():
    """R43 · lo que cae es la pantalla, no el cálculo previo.

    R10 —«MIENTRAS no exista un dry-run correcto y reciente para esa
    incidencia, el sistema no debe ejecutar ninguna escritura contra Sigrid»—
    es el requisito que sostiene el diseño entero de F-025: se sigue
    cumpliendo porque el cálculo previo se ejecuta **dentro de la misma
    llamada** que escribe.
    """
    bloque = _bloque(REQ_F009.read_text(encoding="utf-8"), "**R10.**", "**R11.**")

    assert FECHA in bloque
    assert "R8 y R10 siguen vigentes" in bloque
    assert "misma llamada" in bloque


def test_f025_r43_la_nota_de_f009_dice_que_la_confirmacion_sigue_haciendo_falta():
    """R43 · **una sola** confirmación, no **ninguna**.

    Es la confusión que más daño haría: «hemos quitado una confirmación» leído
    como «hemos quitado la confirmación» deja el circuito escribiendo en el
    ERP sin que nadie diga que sí. R12–R15 de F-009 siguen enteros.
    """
    bloque = _bloque(REQ_F009.read_text(encoding="utf-8"), "**R10.**", "**R11.**")

    assert "R12–R15 siguen igual" in bloque
    assert "una sola" in bloque
    assert "no ninguna" in bloque


def test_f025_r42_la_nota_de_f009_no_vuelve_a_derogar_r21():
    """R42 · derogar dos veces lo mismo es perder la fecha del primero.

    R21 de F-009 quedó derogado por R48 de F-012 el **2026-09-06**. F-025 lo
    comprueba y lo dice; no lo vuelve a derogar.
    """
    bloque = _bloque(REQ_F009.read_text(encoding="utf-8"), "**R10.**", "**R11.**")

    assert "R21 de F-009 no se enmienda aquí" in bloque
    assert "2026-09-06" in bloque
    assert "R48 de F-012" in bloque


def test_f025_r42_r21_de_f009_conserva_su_texto_y_no_gana_recuadro_nuevo():
    """R42 · control negativo: **ninguna** enmienda nueva bajo R21 de F-009.

    Si alguien le añadiera aquí un recuadro con fecha del 2026-09-11, habría
    dos derogaciones de lo mismo con dos fechas distintas y la buena sería la
    equivocada.
    """
    texto = REQ_F009.read_text(encoding="utf-8")
    bloque = _bloque(texto, "**R21.**", "## 6 · La escritura")

    assert "CUANDO se presenta el dry-run, el sistema debe advertir" in bloque
    assert FECHA not in bloque


# --------------------------------------------------------------------------
# R47 · docs/ARCHITECTURE.md
# --------------------------------------------------------------------------


def test_f025_r47_arquitectura_dice_que_la_confirmacion_es_una_sola():
    """R47 · el paso 7b del pipeline.

    `ARCHITECTURE.md` es lo primero que lee quien llega al proyecto. Si sigue
    diciendo «confirmación del usuario, y solo entonces `commit: true`» sin
    precisar que esa confirmación es **la misma** que la del archivado, lo que
    describe es un circuito que ya no existe.
    """
    texto = _llano(ARQUITECTURA.read_text(encoding="utf-8"))

    assert "una sola confirmación" in texto


def test_f025_r47_arquitectura_dice_que_el_calculo_previo_va_en_la_misma_llamada():
    """R47 · la frase que evita el malentendido peligroso.

    Sin ella, «se quitó el dry-run previo» se lee como «ya no hay dry-run», y
    lo siguiente es que alguien lo quite también del backend.
    """
    texto = _llano(ARQUITECTURA.read_text(encoding="utf-8"))

    assert "en la misma llamada" in texto


def test_f025_r47_arquitectura_no_ha_borrado_la_exigencia_de_dry_run():
    """R47 · **control negativo**, y el que de verdad importa de los tres.

    La verificación de T17 lo pide explícitamente: precisar el documento no
    puede acabar borrando de él la obligación del cálculo previo.
    """
    texto = _llano(ARQUITECTURA.read_text(encoding="utf-8"))

    assert "dry-run" in texto
    assert "Siempre dry-run primero" in texto
    assert "dry-run contra `sigrid-api`" in texto


def test_f025_r47_el_punto_6_de_semantica_sigue_diciendo_que_es_produccion():
    """R47 · el punto 6 se precisa, no se rebaja.

    «Cerrar en Sigrid es escritura en producción» es la frase que justifica
    todas las puertas del proyecto. F-025 le añade cuántas confirmaciones hay
    y dónde ocurre el cálculo previo; no le quita el encabezado.
    """
    texto = _llano(ARQUITECTURA.read_text(encoding="utf-8"))
    punto = _bloque(texto, "6. **Cerrar en Sigrid es escritura en producción.**", "7. ")

    assert "una sola confirmación" in punto
    assert "en la misma llamada" in punto
    assert "F-025" in punto
