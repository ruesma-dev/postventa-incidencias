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
