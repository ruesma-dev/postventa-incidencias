# services/postventa-api/tests/test_f028_documentacion.py
"""Las enmiendas que F-028 deja escritas (R55, y las que vengan después).

Mismo objeto y mismo patrón que `test_f026_documentacion.py`: lo que se vigila
aquí **no es un documento técnico, es la memoria de una decisión**. La regla
del proyecto es que **lo que se deroga no se borra**: se enmienda con un
recuadro fechado que cita la premisa original **literal**, dice qué la
invalidó y quién lo decidió y cuándo. El patrón nació en R28 de
`specs/F-010-despliegue/` el 2026-09-03 y lo siguieron F-025 y F-026.

Por qué esto es un test y no una revisión: R8 de F-006 es un requisito
**aprobado** que dice, desde agosto, que los espacios redundantes de un código
se **colapsan**. F-028 hace que los que tocan un separador **desaparezcan**.
Quien dentro de seis meses lea R8 sin el recuadro tendrá delante un requisito
aprobado y un código que no lo cumple, y lo «arreglará» devolviendo el espacio
—y con él, el cierre que hoy falla en real—. Lo que sobrevive a la siguiente
edición no es una revisión: es un test.

Lo que fija hoy:

- **R55** · bajo R8 de `specs/F-006-sharepoint/requirements.md` hay un
  recuadro fechado que cita su texto **literal**, dice qué cambia, qué lo
  invalidó, quién lo decidió y qué **no** cambia. Y el texto original no se
  ha borrado de ningún sitio.

Lo que **no** se comprueba aquí es lo que vive en otro repositorio
(`azure-apps/`): un test de esta suite que dependiera de que ese repositorio
esté clonado al lado fallaría en cualquier máquina donde no lo esté. Su
verificación es la declarada en `tasks.md`.
"""

from __future__ import annotations

from pathlib import Path

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

REQ_F006 = RAIZ / "specs" / "F-006-sharepoint" / "requirements.md"

#: El día en que el responsable vio fallar el circuito en real y decidió. Va
#: en el recuadro porque sin fecha no se puede juzgar una decisión: no se sabe
#: qué se sabía cuando se tomó.
FECHA = "2026-09-15"


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


def _bloque_r8() -> str:
    """El trozo de F-006 que va de R8 a R9, ya aplanado.

    Acotarlo entre los dos requisitos comprueba, de paso, que el recuadro está
    **bajo el punto que enmienda** y no en cualquier otro sitio del fichero: un
    recuadro traspapelado no lo lee quien lee el punto, que es justo a quien va
    dirigido.
    """
    texto = REQ_F006.read_text(encoding="utf-8")
    desde = texto.index("**R8.**")
    hasta = texto.index("**R9.**", desde)
    return _llano(texto[desde:hasta])


# --------------------------------------------------------------------------
# R55 · R8 de F-006 queda enmendado, con su recuadro
# --------------------------------------------------------------------------


def test_f028_r55_bajo_r8_de_f006_hay_un_recuadro_de_enmienda_fechado():
    """R55 · el recuadro existe, está fechado y nombra a la feature que lo trae.

    Sin la fecha no se puede juzgar la decisión; sin el número de feature no se
    puede ir a leer el porqué completo.
    """
    bloque = _bloque_r8()

    assert "Enmienda" in bloque
    assert FECHA in bloque
    assert "F-028" in bloque


def test_f028_r55_el_recuadro_de_r8_cita_la_premisa_literal():
    """R55 · **literal**, no resumida.

    Resumir la premisa original es exactamente la forma de que dentro de seis
    meses nadie pueda juzgar si la decisión fue buena: lo que se juzga es lo que
    decía el requisito, no lo que recordaba quien lo enmendó.
    """
    bloque = _bloque_r8()
    recuadro = bloque[bloque.index("Enmienda") :]

    assert (
        "El sistema debe colapsar los espacios redundantes de los códigos"
        in recuadro
    )
    assert (
        "dos lecturas del mismo parte que solo difieran en espacios produzcan"
        in recuadro
    )

    # El ejemplo de R8 se comprueba contra el texto **sin aplanar**, y es el
    # único caso del fichero que lo necesita: lo que hay que ver es que los
    # espacios dobles de `0677  -  RS26.08` siguen ahí. Aplanarlos los
    # colapsaría a uno y el test daría por buena una cita que ya no dice lo
    # que decía el requisito — justo el error que este fichero vigila.
    assert "`0677  -  RS26.08` → `0677 - RS26.08`" in REQ_F006.read_text(
        encoding="utf-8"
    )


def test_f028_r55_el_recuadro_de_r8_dice_exactamente_que_cambia():
    """R55 · qué cambia, con el valor nuevo escrito.

    «R8 está enmendado» sin el valor concreto obliga a leer el código para
    saber qué normaliza hoy la función, que es justo lo que el recuadro existe
    para evitar.
    """
    bloque = _bloque_r8()

    assert "se eliminan" in bloque
    assert "RS26.08-0123" in bloque


def test_f028_r55_el_recuadro_de_r8_dice_que_la_invalido_y_quien_lo_decidio():
    """R55 · el porqué y el quién, que es lo que distingue una enmienda de un
    cambio de opinión.

    El porqué no es estético: el ERP busca la reclamación por igualdad exacta,
    así que el parte se archivaba bien y el cierre fallaba. Y lo decidió una
    persona, no un agente «arreglando» un test incómodo.
    """
    bloque = _bloque_r8()

    assert "igualdad exacta" in bloque
    assert "responsable del proyecto el 2026-09-15" in bloque


def test_f028_r55_el_recuadro_de_r8_dice_que_la_garantia_no_se_recorta():
    """R55 · la garantía de R8 no se recorta: **se cumple por primera vez**.

    Es la lectura que más daño haría: entender que R8 pedía menos que antes.
    Pedía lo mismo, y no se cumplía.
    """
    bloque = _bloque_r8()

    assert "se cumple por primera vez" in bloque
    assert "Lo que no cambia" in bloque


def test_f028_r55_el_texto_original_de_r8_no_se_ha_borrado():
    """R55 · el requisito enmendado conserva su texto en alguna parte.

    Control negativo de la regla del proyecto: enmendar es añadir un recuadro,
    nunca sustituir el texto por el nuevo y dejar el histórico solo en git. Si
    alguien reescribe R8 y borra la cita, este test lo ve.
    """
    completo = _llano(REQ_F006.read_text(encoding="utf-8"))

    assert (
        "El sistema debe colapsar los espacios redundantes de los códigos"
        in completo
    )
