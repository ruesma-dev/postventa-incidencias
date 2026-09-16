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
- **R56** · bajo **R12, R17 y R22** de `specs/F-026-aprobacion-humana/`, los
  tres **enmendados**: la decisión humana deja de vivir en una fila que se
  sustituye y pasa al histórico append-only, cuya última fila humana manda.
- **R57** · bajo **R30 y R31** de la misma spec, los dos **precisados, no
  derogados**: la aprobación sigue caducando cuando cambia el veredicto, pero
  eso se resuelve al **derivar** el estado y no con una escritura que marca la
  fila.
- **R58** · bajo **R36** de `specs/F-025-confirmacion-unica/` y en los
  **tres puntos** de `docs/ARCHITECTURE.md` que F-026 ya enmendó: el
  vocabulario pasa a ser el del estado —«solo se archiva lo que está
  `aprobado`»—. Y la **semántica 5**, que pasa a decir que los espacios
  alrededor del separador **no forman parte del código**.

Tres son enmiendas de una feature que se cerró **anteayer** (F-026, el
2026-09-12). Eso no las hace menos enmiendas: al contrario, es cuando más
fácil es dar por sabido lo que solo sabe quien estaba delante.

Lo que **no** se comprueba aquí es lo que vive en otro repositorio
(`azure-apps/`): un test de esta suite que dependiera de que ese repositorio
esté clonado al lado fallaría en cualquier máquina donde no lo esté. Su
verificación es la declarada en `tasks.md`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

REQ_F006 = RAIZ / "specs" / "F-006-sharepoint" / "requirements.md"
REQ_F025 = RAIZ / "specs" / "F-025-confirmacion-unica" / "requirements.md"
REQ_F026 = RAIZ / "specs" / "F-026-aprobacion-humana" / "requirements.md"
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"

#: El día en que el responsable vio fallar el circuito en real y decidió. Va
#: en el recuadro porque sin fecha no se puede juzgar una decisión: no se sabe
#: qué se sabía cuando se tomó.
FECHA = "2026-09-15"

#: El día en que la enmienda se escribe, que **no** es el mismo. Los dos van
#: en el recuadro a propósito: uno dice cuándo se decidió y el otro cuándo se
#: dejó constancia, y la distancia entre ambos también es información.
FECHA_ENMIENDA = "2026-09-16"


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


def _bloque(fichero: Path, abre: str, cierra: str) -> str:
    """El trozo de un documento que va de una marca a la siguiente, aplanado.

    Acotar cada comprobación entre el punto que enmienda y el siguiente
    comprueba, de paso, que el recuadro está **bajo el punto que enmienda** y
    no en cualquier otro sitio del fichero: un recuadro traspapelado no lo lee
    quien lee el punto, que es justo a quien va dirigido.

    Las dos marcas se comprueban antes de cortar. Si alguien renumera un
    requisito, lo que hay que ver es «no encuentro R17», no un bloque vacío
    que pasa media docena de asserts por casualidad.
    """
    texto = fichero.read_text(encoding="utf-8")

    assert abre in texto, f"no se encuentra {abre!r} en {fichero.name}"
    desde = texto.index(abre)
    assert cierra in texto[desde:], f"no se encuentra {cierra!r} tras {abre!r}"
    hasta = texto.index(cierra, desde)
    return _llano(texto[desde:hasta])


def _bloque_r8() -> str:
    """El trozo de F-006 que va de R8 a R9, ya aplanado."""
    return _bloque(REQ_F006, "**R8.**", "**R9.**")


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


# --------------------------------------------------------------------------
# R56 · R12, R17 y R22 de F-026 quedan enmendados
# --------------------------------------------------------------------------

#: Los tres requisitos de F-026 que R56 manda enmendar, cada uno con la marca
#: que abre su bloque, la que lo cierra, el trozo de la **cita** que tiene que
#: aparecer en el recuadro y el trozo del **original** que no puede haberse
#: borrado del documento. Son los tres que nombra el requisito, ni uno más.
REQUISITOS_R56 = [
    pytest.param(
        "**R12.**",
        "**R13.**",
        "La aprobación debe guardarse en una tabla propia del esquema propio",
        "La aprobación debe guardarse en una **tabla propia** del esquema",
        id="R12-la-tabla-propia",
    ),
    pytest.param(
        "**R17.**",
        "**R18.**",
        "El sistema debe dejar una sola fila por parte",
        "El sistema debe dejar **una sola fila por parte**",
        id="R17-una-sola-fila",
    ),
    pytest.param(
        "**R22.**",
        "**R23.**",
        "debe decir si ese parte consta aprobado y si su aprobación sigue",
        "debe decir **si ese parte consta aprobado** y si su aprobación",
        id="R22-lo-que-se-devuelve",
    ),
]


@pytest.mark.parametrize(("abre", "cierra", "cita", "original"), REQUISITOS_R56)
def test_f028_r56_los_tres_requisitos_tienen_recuadro_fechado(
    abre, cierra, cita, original
):
    """R56 · los **tres**, cada uno bajo su punto, con fecha y con feature.

    Que sean tres y no uno no es burocracia: quien lee R17 no lee R12. Un
    documento que dice la enmienda en un punto y la calla en los otros dos es
    peor que uno que no la dijera en ninguno, porque el lector se queda con el
    que leyó y se va convencido de lo contrario.
    """
    bloque = _bloque(REQ_F026, abre, cierra)

    assert "Enmienda" in bloque
    assert FECHA_ENMIENDA in bloque
    assert "F-028" in bloque
    assert "R56" in bloque


@pytest.mark.parametrize(("abre", "cierra", "cita", "original"), REQUISITOS_R56)
def test_f028_r56_cada_recuadro_cita_su_premisa_literal(abre, cierra, cita, original):
    """R56 · **literal**, y la suya.

    Un recuadro que cita el requisito de al lado no sirve: lo que se juzga
    dentro de seis meses es lo que decía **este** punto, no lo que decía la
    sección.
    """
    bloque = _bloque(REQ_F026, abre, cierra)
    recuadro = bloque[bloque.index("Enmienda") :]

    assert cita in recuadro


@pytest.mark.parametrize(("abre", "cierra", "cita", "original"), REQUISITOS_R56)
def test_f028_r56_cada_recuadro_dice_que_lo_invalido(abre, cierra, cita, original):
    """R56 · el porqué, que es el que pide el requisito con nombre y apellidos.

    No es «hemos preferido otro diseño»: es que `hash_parte` como clave
    primaria obliga al `ON CONFLICT DO UPDATE` que **borra la decisión
    anterior**, y con eso el criterio de aceptación «el histórico conserva las
    decisiones en orden» es literalmente imposible de cumplir. Eso es lo que
    convierte un cambio de opinión en una enmienda.
    """
    bloque = _bloque(REQ_F026, abre, cierra)

    assert "ON CONFLICT DO UPDATE" in bloque
    assert "§0.4" in bloque


@pytest.mark.parametrize(("abre", "cierra", "cita", "original"), REQUISITOS_R56)
def test_f028_r56_cada_recuadro_dice_donde_vive_ahora_la_decision(
    abre, cierra, cita, original
):
    """R56 · a dónde se mudó, con el nombre de la tabla y la regla que manda.

    Sin esto, el recuadro dice que el requisito ya no vale y deja al lector sin
    saber qué vale en su lugar, que es la peor forma de enmendar: el punto
    queda tachado y el sistema, sin documentar.
    """
    bloque = _bloque(REQ_F026, abre, cierra)

    assert "append-only" in bloque
    assert "última fila humana" in bloque


@pytest.mark.parametrize(("abre", "cierra", "cita", "original"), REQUISITOS_R56)
def test_f028_r56_cada_recuadro_dice_quien_lo_decidio_y_que_no_cambia(
    abre, cierra, cita, original
):
    """R56 · el quién, el cuándo y el límite de la enmienda.

    Lo decidió una persona, no un agente resolviendo una incomodidad. Y «esto
    ya no vale» sin decir qué sigue valiendo es la lectura que más daño hace:
    la decisión humana se sigue registrando **al lado del veredicto, nunca
    encima**, y eso no lo ha tocado nadie.
    """
    bloque = _bloque(REQ_F026, abre, cierra)

    assert "responsable" in bloque
    assert FECHA in bloque
    assert "Lo que no cambia" in bloque


@pytest.mark.parametrize(("abre", "cierra", "cita", "original"), REQUISITOS_R56)
def test_f028_r56_el_texto_original_de_los_tres_no_se_ha_borrado(
    abre, cierra, cita, original
):
    """R56 · **control negativo**: enmendar es añadir, nunca sustituir.

    Si alguien reescribe R12 con el diseño nuevo y borra el viejo, el recuadro
    se queda citando un texto que ya no está en ninguna parte y el documento
    pierde justo lo que lo hace auditable.
    """
    completo = _llano(REQ_F026.read_text(encoding="utf-8"))

    assert original in completo


# --------------------------------------------------------------------------
# R57 · R30 y R31 de F-026 quedan precisados, no derogados
# --------------------------------------------------------------------------

REQUISITOS_R57 = [
    pytest.param(
        "**R30.**",
        "**R31.**",
        "CUANDO se guarda una validación cuyo veredicto difiere del que se",
        "CUANDO se guarda una validación cuyo veredicto **difiere** del que se",
        id="R30-la-revocacion",
    ),
    pytest.param(
        "**R31.**",
        "**R32.**",
        "MIENTRAS una aprobación esté revocada, el sistema no debe admitir",
        "MIENTRAS una aprobación esté revocada, el sistema **no debe** admitir",
        id="R31-mientras-revocada",
    ),
]


@pytest.mark.parametrize(("abre", "cierra", "cita", "original"), REQUISITOS_R57)
def test_f028_r57_los_dos_recuadros_dicen_que_no_se_derogan(
    abre, cierra, cita, original
):
    """R57 · **precisar no es derogar**, y el recuadro lo dice en su primera línea.

    Es la distinción que el requisito pide marcar, y la que evita el daño: leer
    «R30 está enmendado» como «la aprobación ya no caduca» deja vivas
    decisiones humanas tomadas sobre un veredicto que ya no existe, y con ellas
    se archiva y se cierra en producción.
    """
    bloque = _bloque(REQ_F026, abre, cierra)

    assert "No se deroga: se precisa" in bloque
    assert FECHA_ENMIENDA in bloque
    assert "F-028" in bloque
    assert "R57" in bloque


@pytest.mark.parametrize(("abre", "cierra", "cita", "original"), REQUISITOS_R57)
def test_f028_r57_cada_recuadro_cita_su_premisa_literal(abre, cierra, cita, original):
    """R57 · literal, igual que las enmiendas: lo que se precisa hay que poder
    leerlo tal y como se aprobó."""
    bloque = _bloque(REQ_F026, abre, cierra)

    assert cita in bloque


@pytest.mark.parametrize(("abre", "cierra", "cita", "original"), REQUISITOS_R57)
def test_f028_r57_cada_recuadro_dice_que_ahora_se_resuelve_al_derivar(
    abre, cierra, cita, original
):
    """R57 · el **cómo**, que es todo lo que cambia.

    La regla es la misma —se aprobó *ese* veredicto—; lo que cambia es que se
    comprueba al **derivar** el estado, comparando huellas, en vez de con una
    escritura que marca la fila. Quien no lea esto buscará el código que
    revoca, no lo encontrará y concluirá que la caducidad se perdió por el
    camino.
    """
    bloque = _bloque(REQ_F026, abre, cierra)

    assert "derivar" in bloque
    assert "huella" in bloque
    assert "responsable" in bloque
    assert FECHA in bloque


def test_f028_r57_el_recuadro_de_r30_dice_que_se_cierra_la_ventana():
    """R57 · por qué el cambio **mejora** la garantía, y no solo la mueve.

    Revocar era una segunda escritura después de guardar el veredicto. Entre
    las dos había una ventana: si la segunda fallaba, el parte se quedaba
    aprobado sobre un veredicto que ya no existía. Derivando no hay ventana
    porque no hay nada que escribir.
    """
    bloque = _bloque(REQ_F026, "**R30.**", "**R31.**")

    assert "ventana" in bloque


def test_f028_r57_el_recuadro_de_r31_declara_que_la_aprobacion_puede_revivir():
    """R57 · la consecuencia rara, declarada en vez de descubierta.

    Sin marca de «revocada», si el veredicto vuelve a ser el que se aprobó
    —alguien corrige un campo y deshace la corrección— la aprobación **vuelve
    a contar**. Es lo que ya decía R32 de F-026, pero visto desde aquí parece
    otra cosa, y encontrárselo en producción sin haberlo leído es como se abren
    los partes de incidencia.
    """
    bloque = _bloque(REQ_F026, "**R31.**", "**R32.**")

    assert "vuelve a contar" in bloque


@pytest.mark.parametrize(("abre", "cierra", "cita", "original"), REQUISITOS_R57)
def test_f028_r57_el_texto_original_de_los_dos_no_se_ha_borrado(
    abre, cierra, cita, original
):
    """R57 · control negativo: precisar es añadir debajo, nunca reescribir."""
    completo = _llano(REQ_F026.read_text(encoding="utf-8"))

    assert original in completo


# --------------------------------------------------------------------------
# R58 · R36 de F-025 y los tres puntos de docs/ARCHITECTURE.md
# --------------------------------------------------------------------------


def _bloque_r36() -> str:
    """El trozo de F-025 que va de R36 a R37, ya aplanado."""
    return _bloque(REQ_F025, "**R36.**", "**R37.**")


def test_f028_r58_bajo_r36_de_f025_hay_un_segundo_recuadro():
    """R58 · el vocabulario del estado llega a R36, **sin tocar** lo de F-026.

    R36 lleva ya un recuadro del 2026-09-12. El de F-028 va **debajo**, no
    encima: dos enmiendas son dos hechos, y aplastar la primera con la segunda
    borraría la decisión que abrió el archivo a los partes no aptos.
    """
    bloque = _bloque_r36()

    assert "F-028" in bloque
    assert FECHA_ENMIENDA in bloque
    assert "R58" in bloque


def test_f028_r58_el_recuadro_de_r36_usa_el_vocabulario_del_estado():
    """R58 · «solo se archiva lo que está `aprobado`», con todas las letras.

    Y lo que de verdad cambia: con F-026 la puerta preguntaba «¿es apto, o está
    aprobado?». Ahora pregunta por el **estado**, y eso incluye el caso nuevo
    —un parte **apto** que una persona ha **rechazado** no se archiva—, que con
    el vocabulario viejo no se podía ni enunciar.
    """
    bloque = _bloque_r36()

    assert "solo se archiva, se adjunta y se cierra lo que está `aprobado`" in bloque
    assert "apto y `rechazado`" in bloque


def test_f028_r58_el_recuadro_de_r36_dice_que_la_puerta_no_se_ensancha():
    """R58 · la frase que impide leer la enmienda como una barra libre.

    El estado se lee **del repositorio, nunca del cuerpo de la petición**, y se
    comprueba en los tres pasos del backend, que es donde estaba. Sin esta
    frase, «ahora manda el estado» se lee como «ahora lo decide quien llama».
    """
    bloque = _bloque_r36()

    assert "los tres pasos del backend" in bloque
    assert "del repositorio, nunca del cuerpo" in bloque
    assert "más estrecha" in bloque


def test_f028_r58_la_enmienda_de_f026_en_r36_sigue_entera():
    """R58 · **control negativo**: la enmienda anterior no se ha tocado.

    Es la que documenta por qué un parte no apto puede archivarse, con las
    palabras del responsable del 2026-09-11. Si F-028 la sustituyera por la
    suya, ese porqué se perdería y quedaría un requisito enmendado dos veces
    del que solo se sabe la última.
    """
    bloque = _bloque_r36()

    assert "Enmienda del 2026-09-12" in bloque
    assert "si y solo si consta aprobado y vigente" in bloque


def test_f028_r58_el_texto_original_de_r36_no_se_ha_borrado():
    """R58 · y el requisito original, el de agosto, sigue donde estaba."""
    completo = _llano(REQ_F025.read_text(encoding="utf-8"))

    assert (
        "**R36.** El sistema **no debe** archivar, adjuntar ni cerrar un parte "
        "que no sea `apto` con destino `archivo_y_cierre`" in completo
    )


#: Los tres puntos de `docs/ARCHITECTURE.md` que F-026 precisó el 2026-09-12 y
#: que R58 manda poner al día. Las marcas son las mismas que usa
#: `test_f026_documentacion.py`: si alguien renumera el documento, los dos
#: ficheros se enteran a la vez.
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
        "Un parte sin firma válida no se archiva ni se cierra",
        id="semantica-3",
    ),
    pytest.param(
        "7. **Nada se archiva ni se cierra si no ha pasado todas las validaciones.**",
        "8. **El nombre del fichero",
        "Nada se archiva ni se cierra si no ha pasado todas las validaciones.",
        id="semantica-7",
    ),
]


@pytest.mark.parametrize(("abre", "cierra", "original"), PUNTOS_DE_ARQUITECTURA)
def test_f028_r58_los_tres_puntos_hablan_del_estado(abre, cierra, original):
    """R58 · los tres puntos dicen hoy lo que decide de verdad quién se archiva.

    `ARCHITECTURE.md` es lo primero que lee quien llega al proyecto y el
    reviewer valida contra él. Si sigue diciendo que la puerta la abre «una
    aprobación viva en `postventa.aprobaciones`», manda a leer una tabla que ya
    no se lee y calla el caso nuevo: el parte **apto** que una persona rechazó.
    """
    bloque = _bloque(ARQUITECTURA, abre, cierra)

    assert f"Precisado por F-028 el {FECHA_ENMIENDA}" in bloque
    assert "está `aprobado`" in bloque
    assert "`rechazado`" in bloque
    assert "historico_estado" in bloque


@pytest.mark.parametrize(("abre", "cierra", "original"), PUNTOS_DE_ARQUITECTURA)
def test_f028_r58_los_tres_puntos_conservan_lo_anterior(abre, cierra, original):
    """R58 · **control negativo doble**: ni la regla general ni la precisión de
    F-026 se han borrado.

    Los tres puntos han acumulado ya dos capas, y las dos siguen haciendo
    falta: la regla general rige el 95 % de los partes, y la precisión de F-026
    es la que explica por qué un no apto puede archivarse. Quitar cualquiera de
    las dos para «dejarlo limpio» deja el documento describiendo la excepción
    como si fuera la norma.
    """
    bloque = _bloque(ARQUITECTURA, abre, cierra)

    assert original in bloque
    assert "salvo aprobación humana registrada" in bloque
    assert "Precisado por F-026 el 2026-09-12" in bloque


def _bloque_semantica_5() -> str:
    """El punto 5 de la semántica de dominio, ya aplanado."""
    return _bloque(
        ARQUITECTURA,
        "5. **El número de incidencia lo emite Sigrid**",
        "6. **Cerrar en Sigrid es escritura en producción.**",
    )


def test_f028_r58_la_semantica_5_dice_que_los_espacios_no_son_del_codigo():
    """R58 · la nota del asunto 2, en el punto que define el número.

    Es la regla que costó un cierre que falló en real: `RS26.09 / 0149` es **el
    mismo** número que `RS26.09/0149`, y los espacios que rodean al separador
    no forman parte de él. Va aquí y no solo en F-006 porque quien lee la
    semántica del número es justo quien podría «respetar lo que pone el papel»
    y devolver el defecto.
    """
    bloque = _bloque_semantica_5()

    assert f"Precisado por F-028 el {FECHA_ENMIENDA}" in bloque
    assert "no forman parte del código" in bloque
    assert "RS26.09 / 0149" in bloque
    assert "igualdad exacta" in bloque


def test_f028_r58_la_semantica_5_avisa_de_que_la_obra_no_se_parte():
    """R58 · el aviso que impide «arreglar» de más.

    La regla vale para el **número de incidencia**, no para el código de obra:
    `06-77` es una obra, y partirla por el guion la convertiría en dos tramos,
    con lo que el PDF —que lleva el DNI manuscrito de un cliente— acabaría en
    una carpeta que no es la suya. Es el error que este aviso existe para
    evitar, y por eso va pegado a la regla.
    """
    bloque = _bloque_semantica_5()

    assert "`06-77` es una obra" in bloque


def test_f028_r58_la_semantica_5_conserva_su_texto():
    """R58 · control negativo: el punto original sigue entero."""
    bloque = _bloque_semantica_5()

    assert "se escribe `RS26.08/0123`" in bloque
    assert "nunca se inventa ni se deduce" in bloque
