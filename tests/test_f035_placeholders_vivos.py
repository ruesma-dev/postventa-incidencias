# tests/test_f035_placeholders_vivos.py
"""F-035 · R27-R29 y R37 · La maqueta del portal no se queda viva por olvido.

La maqueta (`services/postventa-front/index.html`, `js/portal.js` y
`js/maqueta_datos.js`) está sembrada de **restos**: placeholders
(`data-placeholder="F-0NN"`) y bloques de datos de ejemplo
(`ficha: "F-0NN"`), cada uno con la ficha que lo sustituirá. La regla de
retirada (`design.md` §7.3) dice que cada ficha quita los suyos **en el mismo
trabajo** en que construye su pieza. Este fichero es lo que hace que olvidarlo
se ponga en rojo:

- **R27**: toda ficha citada existe en `harness/features.json`.
- **R28**: ninguna ficha `done` deja restos.
- **R29**: cada ficha de F-036 a F-048 que no está `done` tiene al menos uno
  (todas las secciones del ciclo existen).
- **R48** (segunda ronda, 2026-09-25): cuando una sección del portal es
  **real** (todas sus fichas `done`), la barra del circuito la enlaza en la
  misma ventana, sin `target`; y la regla consta en `docs/ARCHITECTURE.md` y
  en el `README.md` del front.
- **R62** (enmienda del 2026-10-05): el `estado` que cada sección declara en
  `Portal.SECCIONES` (`real`, `parcial`, `construccion`) es el que dan sus
  fichas en `harness/features.json`.

Vive en la suite de la **raíz** y no en la del front a propósito: la del front
se salta por caché cuando su árbol no cambia (`init.sh`, sección 7 bis), y
pasar una ficha a `done` en `features.json` no toca ese árbol. La de la raíz
se ejecuta siempre.

Los ficheros se leen como texto, sin ejecutar nada.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
FRONT = RAIZ / "services" / "postventa-front"
FEATURES = RAIZ / "harness" / "features.json"
ARCHITECTURE = RAIZ / "docs" / "ARCHITECTURE.md"

#: Los tres ficheros de la maqueta que llevan restos con su ficha.
FICHEROS_CON_RESTOS = (
    FRONT / "index.html",
    FRONT / "js" / "portal.js",
    FRONT / "js" / "maqueta_datos.js",
)

_PLACEHOLDER_HTML = re.compile(r"""data-placeholder\s*=\s*["'](F-\d{3})["']""")
_FICHA_JS = re.compile(r"""\bficha\s*:\s*["'](F-\d{3})["']""")

#: Las fichas del ciclo de posventa que dan contenido a la maqueta (R29).
FICHAS_DEL_CICLO = tuple(f"F-0{n}" for n in range(36, 49))

_GUID = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE
)


def restos_de_la_maqueta() -> dict[str, list[str]]:
    """`{ficha: ["index.html:123", "js/portal.js:45", …]}` de los tres ficheros.

    Si falta un fichero, falla al leerlo: una maqueta sin sus ficheros no
    puede dar «cero restos» por las buenas.
    """
    restos: dict[str, list[str]] = {}
    for fichero in FICHEROS_CON_RESTOS:
        patron = _PLACEHOLDER_HTML if fichero.suffix == ".html" else _FICHA_JS
        texto = fichero.read_text(encoding="utf-8")
        for numero, linea in enumerate(texto.splitlines(), start=1):
            for ficha in patron.findall(linea):
                donde = f"{fichero.relative_to(FRONT).as_posix()}:{numero}"
                restos.setdefault(ficha, []).append(donde)
    return restos


def estados(features: dict) -> dict[str, str]:
    return {f["id"]: f["status"] for f in features["features"]}


def restos_de_fichas_done(features: dict, restos: dict[str, list[str]]) -> list[str]:
    """Los restos de fichas que ya están `done` (R28). Vacío = correcto."""
    hechas = {ficha for ficha, estado in estados(features).items() if estado == "done"}
    return [
        f"{ficha} está done y deja {donde}"
        for ficha in sorted(restos)
        if ficha in hechas
        for donde in restos[ficha]
    ]


def fichas_del_ciclo_sin_restos(features: dict, restos: dict[str, list[str]]) -> list[str]:
    """Las fichas F-036…F-048 sin cerrar que no tienen ni un resto (R29)."""
    por_ficha = estados(features)
    return [
        ficha
        for ficha in FICHAS_DEL_CICLO
        if por_ficha.get(ficha) != "done" and not restos.get(ficha)
    ]


def _features() -> dict:
    return json.loads(FEATURES.read_text(encoding="utf-8"))


def test_f035_r27_toda_ficha_citada_en_la_maqueta_existe():
    existentes = set(estados(_features()))
    restos = restos_de_la_maqueta()

    desconocidas = {f: d for f, d in restos.items() if f not in existentes}
    assert desconocidas == {}, (
        f"la maqueta cita fichas que no están en harness/features.json: {desconocidas}"
    )


def test_f035_r27_la_maqueta_no_cita_a_la_propia_f035():
    """Un resto de F-035 no lo retiraría nadie: R28 lo dejaría vivo para siempre."""
    restos = restos_de_la_maqueta()

    assert "F-035" not in restos, f"restos de F-035: {restos.get('F-035')}"


def test_f035_r28_ninguna_ficha_done_deja_restos_en_la_maqueta():
    problemas = restos_de_fichas_done(_features(), restos_de_la_maqueta())

    assert problemas == [], (
        "hay fichas cerradas con placeholders o datos de ejemplo en la maqueta; "
        "retíralos como dice design.md §7.3 de F-035:\n" + "\n".join(problemas)
    )


def test_f035_r29_cada_ficha_del_ciclo_sin_cerrar_tiene_su_sitio_en_la_maqueta():
    faltan = fichas_del_ciclo_sin_restos(_features(), restos_de_la_maqueta())

    assert faltan == [], (
        f"fichas del ciclo sin ningún placeholder ni bloque de datos en la maqueta: {faltan}"
    )


def test_f035_r28_la_guardia_mira_una_ficha_que_pasa_a_done():
    """Control: con F-044 en `done` en una copia en memoria, la guardia TIENE que dar restos.

    Sin esto, `restos_de_fichas_done` podría devolver siempre lista vacía y
    R28 estaría en verde sin mirar nada. La copia no se escribe en disco.
    """
    features = copy.deepcopy(_features())
    for ficha in features["features"]:
        if ficha["id"] == "F-044":
            ficha["status"] = "done"

    problemas = restos_de_fichas_done(features, restos_de_la_maqueta())

    assert problemas, "con F-044 en done, la guardia no ha visto ningún resto"
    assert all(p.startswith("F-044 ") for p in problemas), problemas


def test_f035_r37_architecture_recoge_el_portal_y_la_regla_de_los_placeholders():
    lineas = ARCHITECTURE.read_text(encoding="utf-8").splitlines()
    inicio = next(
        (i for i, linea in enumerate(lineas)
         if linea.startswith("#") and "El portal de posventa (F-035)" in linea),
        None,
    )
    assert inicio is not None, "falta la sección «El portal de posventa (F-035)»"

    nivel = len(lineas[inicio]) - len(lineas[inicio].lstrip("#"))
    fin = next(
        (i for i in range(inicio + 1, len(lineas))
         if lineas[i].startswith("#")
         and len(lineas[i]) - len(lineas[i].lstrip("#")) <= nivel),
        len(lineas),
    )
    texto = "\n".join(lineas[inicio:fin])

    faltan = [f for f in FICHAS_DEL_CICLO if f not in texto]
    assert faltan == [], f"el mapa del portal no dice qué construyen {faltan}"
    assert "placeholder" in texto.lower(), "falta la regla de los placeholders"


def test_f035_r37_architecture_corrige_el_grupo_de_entra_sin_guid():
    texto = ARCHITECTURE.read_text(encoding="utf-8")

    assert "posventa-usuarios" in texto, (
        "la fila de Entra ID sigue sin decir que el grupo posventa-usuarios existe (D-5)"
    )
    guid = _GUID.search(texto)
    assert guid is None, "hay un GUID en docs/ARCHITECTURE.md"


# --- R48 · Cuando una sección sea real, del circuito se va en la misma ventana ----
#
# Segunda ronda del humano (2026-09-25): «en la misma ventana como en una web
# normal (para la maqueta vale así)». Mientras una sección sea maqueta, la
# barra del circuito la abre aparte (R31); en cuanto todas sus fichas estén
# `done`, la enlaza SIN `target`. Vive aquí, en la raíz, por lo mismo que R28:
# cerrar la última ficha de una sección no toca el árbol del front.

CIRCUITO = FRONT / "partes.html"
PORTAL_JS = FRONT / "js" / "portal.js"
README_FRONT = FRONT / "README.md"

_SECCION_JS = re.compile(r"""\{\s*id:\s*"([a-z]+)",[^}]*?fichas:\s*\[([^\]]*)\]""")
_ENLACE_BARRA = re.compile(r"""<a\s[^>]*href="\./#/([a-z]+)"[^>]*>""")


def secciones_del_portal() -> dict[str, list[str]]:
    """`{id: [fichas]}` de `Portal.SECCIONES` (`js/portal.js`), leído como texto."""
    secciones = {
        seccion: re.findall(r"F-\d{3}", fichas)
        for seccion, fichas in _SECCION_JS.findall(PORTAL_JS.read_text(encoding="utf-8"))
    }
    assert len(secciones) == 8 and "inicio" in secciones and "partes" in secciones, (
        f"no se han leído las ocho secciones de Portal.SECCIONES: {sorted(secciones)}"
    )
    return secciones


def secciones_reales(features: dict, secciones: dict[str, list[str]]) -> list[str]:
    """Las secciones del portal que ya no son maqueta (R48).

    Real: todas las fichas de su entrada están `done`. `inicio` (sin fichas
    propias) lo es cuando lo son todas las demás. `partes` es el circuito y no
    cuenta.
    """
    hechas = {ficha for ficha, estado in estados(features).items() if estado == "done"}
    reales = [
        seccion for seccion, fichas in secciones.items()
        if seccion not in ("inicio", "partes") and fichas and set(fichas) <= hechas
    ]
    demas = [s for s in secciones if s not in ("inicio", "partes")]
    if demas and set(demas) <= set(reales):
        reales.append("inicio")
    return reales


def enlaces_aparte_a_secciones_reales(features: dict, html: str) -> list[str]:
    """Los enlaces de la barra del circuito que abren aparte una sección ya real. Vacío = correcto."""
    reales = secciones_reales(features, secciones_del_portal())
    return [
        f"la barra de partes.html abre «{seccion}» aparte y ya es real: quita su target (R48)"
        for enlace in _ENLACE_BARRA.finditer(html)
        if (seccion := enlace.group(1)) in reales and "target=" in enlace.group(0)
    ]


def test_f035_r48_las_secciones_reales_se_abren_en_la_misma_ventana():
    problemas = enlaces_aparte_a_secciones_reales(_features(), CIRCUITO.read_text(encoding="utf-8"))

    assert problemas == [], (
        "\n".join(problemas)
        + "\nY en el mismo trabajo, resuelve la remesa en curso del circuito (design.md §2 de F-035)."
    )


def test_f035_r48_la_guardia_mira_una_seccion_que_pasa_a_real():
    """Control: con F-048 en `done` en una copia en memoria, `datos` es real y su `target` tiene que saltar."""
    features = copy.deepcopy(_features())
    for ficha in features["features"]:
        if ficha["id"] == "F-048":
            ficha["status"] = "done"

    assert secciones_reales(features, secciones_del_portal()) == ["datos"]
    problemas = enlaces_aparte_a_secciones_reales(features, CIRCUITO.read_text(encoding="utf-8"))
    assert len(problemas) == 1 and "«datos»" in problemas[0], problemas


def test_f035_r48_inicio_es_real_cuando_lo_son_todas_las_demas():
    features = copy.deepcopy(_features())
    fichas = {f for lista in secciones_del_portal().values() for f in lista}
    for ficha in features["features"]:
        if ficha["id"] in fichas:
            ficha["status"] = "done"

    assert sorted(secciones_reales(features, secciones_del_portal())) == sorted(
        ["inicio", "entrada", "bandeja", "incidencias", "impresion", "economico", "datos"]
    )


# --- R62 · El estado de cada sección es el que dan sus fichas ----------------------
#
# Enmienda del 2026-10-05 (opción b): el portal se publica entero y cada
# sección declara en `Portal.SECCIONES` su `estado` —`real`, `parcial` o
# `construccion`—, escrito literal. De él salen la marca de la barra (R66) y
# los recuadros «En construcción» (R63-R65). Vive aquí, en la raíz, por lo
# mismo que R28 y R48: cerrar una ficha en `features.json` no toca el árbol
# del front y su suite se saltaría por caché.

ESTADOS_DE_SECCION = ("real", "parcial", "construccion")

_ESTADO_JS = re.compile(r"""\{\s*id:\s*"([a-z]+)",[^}]*?\bestado:\s*"([a-z]*)"[^}]*\}""")


def estados_declarados(texto: str | None = None) -> dict[str, str]:
    """`{id: estado}` de `Portal.SECCIONES` (`js/portal.js`), leído como texto."""
    if texto is None:
        texto = PORTAL_JS.read_text(encoding="utf-8")
    return dict(_ESTADO_JS.findall(texto))


def estados_segun_las_fichas(features: dict, secciones: dict[str, list[str]]) -> dict[str, str]:
    """El `estado` que corresponde a cada sección según `features.json` (R62).

    - Las secciones que no son `inicio` ni `partes`: `construccion` si
      ninguna de sus fichas está `done`, `parcial` si lo está alguna y `real`
      si lo están todas.
    - `partes` (el circuito, que ya funciona): `parcial` mientras alguna de
      sus fichas (F-045) no esté `done`; `real` cuando lo estén.
    - `inicio`: `real` cuando lo son todas las demás secciones del portal
      (las siete, `partes` incluida); `parcial` mientras no.
    """
    hechas = {ficha for ficha, estado in estados(features).items() if estado == "done"}
    resultado: dict[str, str] = {}
    for seccion, fichas in secciones.items():
        if seccion == "inicio":
            continue
        cerradas = [f for f in fichas if f in hechas]
        if seccion == "partes":
            resultado[seccion] = "real" if len(cerradas) == len(fichas) else "parcial"
        elif not cerradas:
            resultado[seccion] = "construccion"
        elif len(cerradas) == len(fichas):
            resultado[seccion] = "real"
        else:
            resultado[seccion] = "parcial"
    if "inicio" in secciones:
        todas_reales = all(estado == "real" for estado in resultado.values())
        resultado["inicio"] = "real" if todas_reales else "parcial"
    return resultado


def estados_que_no_cuadran(features: dict, declarados: dict[str, str]) -> list[str]:
    """Las secciones cuyo `estado` declarado no es el que dan sus fichas. Vacío = correcto."""
    esperados = estados_segun_las_fichas(features, secciones_del_portal())
    return [
        f"«{seccion}» declara estado «{declarados.get(seccion, '(ninguno)')}» y sus fichas "
        f"dicen «{esperado}»: cámbialo en Portal.SECCIONES (js/portal.js, R62)"
        for seccion, esperado in esperados.items()
        if declarados.get(seccion) != esperado
    ]


def test_f035_r62_cada_seccion_declara_su_estado_literal():
    declarados = estados_declarados()

    assert sorted(declarados) == sorted(secciones_del_portal()), (
        "cada entrada de Portal.SECCIONES lleva su `estado: \"…\"` escrito literal: "
        f"leídos {sorted(declarados)}"
    )
    raros = {s: e for s, e in declarados.items() if e not in ESTADOS_DE_SECCION}
    assert raros == {}, f"estados fuera de {ESTADOS_DE_SECCION}: {raros}"


def test_f035_r62_el_estado_de_cada_seccion_es_el_que_dan_sus_fichas():
    problemas = estados_que_no_cuadran(_features(), estados_declarados())

    assert problemas == [], "\n".join(problemas)


def test_f035_r62_la_guardia_mira_una_ficha_que_pasa_a_done():
    """Control: con F-038 en `done` en una copia en memoria, `bandeja` pasa a `parcial` y la guardia salta."""
    features = copy.deepcopy(_features())
    for ficha in features["features"]:
        if ficha["id"] == "F-038":
            ficha["status"] = "done"

    assert estados_segun_las_fichas(features, secciones_del_portal())["bandeja"] == "parcial"
    problemas = estados_que_no_cuadran(features, estados_declarados())
    assert len(problemas) == 1 and "«bandeja»" in problemas[0], problemas


def test_f035_r62_control_el_lector_de_estados_lee_el_texto():
    """Control: el lector no devuelve un dato fijo; un `estado` cambiado en el texto se ve."""
    texto = PORTAL_JS.read_text(encoding="utf-8")
    cambiado = re.sub(
        r'(\{\s*id:\s*"bandeja",[^}]*?\bestado:\s*")[a-z]*(")', r"\1parcial\2", texto, count=1
    )

    assert cambiado != texto, "el control no encuentra el estado de «bandeja» en js/portal.js"
    assert estados_declarados(cambiado)["bandeja"] == "parcial"
    problemas = estados_que_no_cuadran(_features(), estados_declarados(cambiado))
    assert any("«bandeja»" in p for p in problemas), problemas


def test_f035_r62_partes_e_inicio_siguen_su_propia_regla():
    """`partes` nunca está en construcción (el circuito funciona); `inicio`, real solo con todas reales."""
    features = copy.deepcopy(_features())
    secciones = secciones_del_portal()
    por_id = {f["id"]: f for f in features["features"]}
    for ficha in {f for lista in secciones.values() for f in lista}:
        por_id[ficha]["status"] = "pending"
    assert estados_segun_las_fichas(features, secciones)["partes"] == "parcial"
    assert estados_segun_las_fichas(features, secciones)["inicio"] == "parcial"

    por_id["F-045"]["status"] = "done"
    assert estados_segun_las_fichas(features, secciones)["partes"] == "real"

    for ficha in {f for lista in secciones.values() for f in lista}:
        por_id[ficha]["status"] = "done"
    assert set(estados_segun_las_fichas(features, secciones).values()) == {"real"}


def _seccion_markdown(ruta: Path, titulo: str) -> str:
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    inicio = next(
        (i for i, linea in enumerate(lineas) if linea.startswith("#") and titulo in linea),
        None,
    )
    assert inicio is not None, f"falta la sección «{titulo}» en {ruta.name}"
    nivel = len(lineas[inicio]) - len(lineas[inicio].lstrip("#"))
    fin = next(
        (i for i in range(inicio + 1, len(lineas))
         if lineas[i].startswith("#") and len(lineas[i]) - len(lineas[i].lstrip("#")) <= nivel),
        len(lineas),
    )
    return "\n".join(lineas[inicio:fin])


def test_f035_r48_la_regla_consta_en_architecture_y_en_el_readme_del_front():
    for ruta, titulo in (
        (ARCHITECTURE, "El portal de posventa (F-035)"),
        (README_FRONT, "La maqueta del portal (F-035)"),
    ):
        texto = " ".join(_seccion_markdown(ruta, titulo).split())  # sin los saltos del Markdown
        for imprescindible in ("R48", "misma ventana", "remesa"):
            assert imprescindible in texto, (
                f"{ruta.name} · «{titulo}»: la regla de R48 no dice «{imprescindible}»"
            )
