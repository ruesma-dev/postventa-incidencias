# services/postventa-api/tests/test_f006_repo_sin_identificadores.py
"""Ningún identificador con forma de GUID puede entrar en el repositorio (R26).

Esta es **la otra mitad** de R26. La primera vive en
`tests/test_f006_arquitectura.py` y barre `services/postventa-api/`. Esta barre
**todo lo demás**, y existe por un motivo concreto y documentado.

## Por qué la primera mitad no bastaba

La review de F-006 (`progress/review_F-006.md`, hallazgo **H1**) encontró el
appId **real** del app registration escrito en `progress/current.md`, bajo el
epígrafe «Lo verificado en Azure». Estaba ahí desde el commit `f2e317b`, que ya
había llegado a `dev`, y **ningún test lo vio**:
`test_f006_r26_ningun_fichero_del_servicio_incrusta_un_identificador` recorre
`_ficheros_del_servicio()`, es decir, solo `services/postventa-api/`.

La lección no es «faltaba un directorio». Es que **el guardián miraba justo
donde los identificadores no se escriben**. Nadie pega el GUID de un sitio de
SharePoint dentro de un adaptador: lo escribe un agente en su informe, al
anotar lo que acaba de verificar en el portal de Azure. Los ficheros de
`progress/` son el sitio con **más** probabilidad de llevar un valor real de
todo el árbol, y eran exactamente los que quedaban fuera.

De ahí el alcance de este fichero: **todo el árbol**, y no una lista de cuatro
directorios. Una lista se queda vieja el día que alguien añade el quinto; una
exclusión explícita de lo que no es del repositorio se rompe de forma ruidosa.

## Tres decisiones de diseño, y su motivo

1. **El fallo dice la ruta y cuántos, nunca el valor.** Un guardián de secretos
   cuya traza de fallo imprime el secreto lo copia al log de CI, al chat y al
   informe de quien lo diagnostique. Aquí se informa `{ruta: nº}`: es lo que
   hace falta para ir a arreglarlo, y nada más.
2. **Se tolera por ruta y por número, jamás por valor.** Escribir aquí los GUID
   que hay que excluir sería meter en el repositorio justo lo que este fichero
   prohíbe. Acotar el número obliga a que ampliar la tolerancia sea un cambio
   visible en la revisión, no un renglón más en una lista.
3. **Lo que no está versionado no se barre.** `.venv/`, `.idea/`, `muestras/`,
   `.env`, `local.settings.json`: son ficheros de la máquina de quien trabaja,
   y ahí un identificador real es **lo normal y lo correcto**. Un barrido que
   los mordiera fallaría en cuanto alguien configurara su entorno, y a la
   tercera vez estaría desactivado. Un guardián desactivado no protege nada.

## Y por qué hay tantos controles positivos

Porque el riesgo de este test no es que no cace: es que cace de más. En
`progress/` hay páginas hablando de GUID, de `Sites.FullControl.All`, de
`SHAREPOINT_SITE_ID` y de trazas con valores enmascarados a propósito. Si algo
de eso disparara la alarma, el test moriría por molesto, no por incorrecto.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# El patrón se **importa**, no se copia: si esta mitad y la del servicio
# usaran dos regex distintas, un día divergirían y solo una de las dos
# cazaría el caso que importa. La otra mitad es la dueña del patrón.
from tests.test_f006_arquitectura import PATRON_GUID

#: Raíz del servicio (este fichero vive en `<servicio>/tests/`) y del repo.
SERVICIO = Path(__file__).resolve().parent.parent
RAIZ = SERVICIO.parent.parent

#: Extensiones de texto que tiene sentido leer. Lo binario no se abre.
EXTENSIONES = (
    ".py",
    ".md",
    ".json",
    ".txt",
    ".yaml",
    ".yml",
    ".example",
    ".sql",
    ".ps1",
    ".sh",
    ".toml",
    ".cfg",
    ".ini",
)

#: Directorios que **no son el repositorio**, aunque estén dentro del árbol.
#:
#: Los cuatro primeros son entorno local o del IDE; `muestras/` y
#: `originales/` son documentos con datos personales que `.gitignore` mantiene
#: fuera de git; `worktrees` son las copias temporales que crean los subagentes
#: del arnés, y barrerlas sería barrer el repositorio dos veces. El resto son
#: cachés.
DIRECTORIOS_NO_VERSIONADOS = (
    ".git",
    ".idea",
    ".venv",
    "venv",
    "node_modules",
    "muestras",
    "originales",
    "worktrees",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".arnes_cache",
)

#: Ficheros que `.gitignore` deja fuera y que **legítimamente** llevan valores.
#:
#: `.env` y `local.settings.json` son la configuración real de quien trabaja:
#: el día que alguien rellene ahí `SHAREPOINT_SITE_ID` estará haciendo
#: exactamente lo que debe, y este test no puede castigarlo por ello.
FICHEROS_NO_VERSIONADOS = (".env", "local.settings.json", "coverage.json")

#: Ficheros que ya citan un GUID, cuántos, y por qué se les tolera.
#:
#: - Los dos de `tests/` son **controles negativos declarados de F-005**:
#:   existen para demostrar que aquellos barridos saltan, y sus valores están
#:   inventados. Los acota también
#:   `test_f006_r26_la_excepcion_de_f005_no_crece_sin_que_se_vea`.
#: - `progress/review_F-006.md` cita el GUID todo a ceros al explicar cuáles
#:   son esos dos controles negativos. Es un valor nulo por construcción, no
#:   identifica nada, y está en un informe entregado: enmascararlo a posteriori
#:   alteraría la evidencia de una review.
#:
#: Ninguna entrada excluye un **valor**, solo un recuento en una ruta: cambiar
#: el GUID de uno de estos ficheros por uno real lo dejaría pasar, y por eso la
#: lista se mantiene corta y se justifica una por una.
GUID_TOLERADO_POR_FICHERO = {
    "services/postventa-api/tests/test_f005_integracion_sin_secretos.py": 1,
    "services/postventa-api/tests/test_f005_repo_sin_datos_personales.py": 1,
    "progress/review_F-006.md": 1,
}


def guid_compuesto(*trozos: str) -> str:
    """Un identificador con forma de GUID, **compuesto en memoria**.

    Los controles de este fichero necesitan valores con forma de GUID, y
    escribirlos como literales haría que este propio test se denunciara a sí
    mismo —con razón—. Componerlos aquí deja el repositorio sin ni una cadena
    con forma de GUID fuera de las tres toleradas y declaradas arriba.
    """
    return "-".join(trozos)


def _es_barrido(fichero: Path, raiz: Path = RAIZ) -> bool:
    """Si un fichero forma parte de lo que este guardián vigila.

    Los directorios excluidos se comparan contra la ruta **relativa a la
    raíz**, nunca contra la absoluta. Con la absoluta el guardián se apagaba
    entero al ejecutarse desde un worktree del arnés: su ruta es
    `<repo>/.claude/worktrees/agent-XXX/`, así que *todos* sus ficheros
    llevaban `worktrees` entre sus `parts` y el barrido salía vacío. Y un
    barrido vacío es justo lo que
    `test_f006_r26_el_barrido_del_repositorio_mira_ficheros_de_verdad`
    existe para impedir: fue ese control el que lo cazó, no una revisión.
    Relativizando, `.claude/worktrees/` se sigue excluyendo desde el árbol
    principal —que es para lo que se puso— y deja de excluirse a sí mismo
    cuando la raíz *es* el worktree.
    """
    return (
        fichero.is_file()
        and fichero.suffix in EXTENSIONES
        and fichero.name not in FICHEROS_NO_VERSIONADOS
        and not any(parte in DIRECTORIOS_NO_VERSIONADOS for parte in fichero.relative_to(raiz).parts)
    )


def _ficheros_barridos(raiz: Path = RAIZ) -> list[Path]:
    """Todos los ficheros de texto versionados del árbol.

    La raíz es un parámetro para que los controles puedan montar un árbol de
    mentira en `tmp_path` y comprobar el barrido **entero** —recorrido,
    filtros y recuento— sin escribir un solo GUID en el repositorio de verdad.
    """
    return sorted(fichero for fichero in raiz.rglob("*") if _es_barrido(fichero, raiz))


def _hallazgos(raiz: Path = RAIZ) -> dict[str, int]:
    """Ruta relativa → cuántos identificadores hay de más. **Nunca el valor.**"""
    encontrados: dict[str, int] = {}
    for fichero in _ficheros_barridos(raiz):
        ruta = fichero.relative_to(raiz).as_posix()
        cuantos = len(PATRON_GUID.findall(fichero.read_text(encoding="utf-8", errors="replace")))
        if cuantos > GUID_TOLERADO_POR_FICHERO.get(ruta, 0):
            encontrados[ruta] = cuantos
    return encontrados


# --------------------------------------------------------------------------
# El barrido mira de verdad, y mira donde hay que mirar
# --------------------------------------------------------------------------


def test_f006_r26_el_barrido_del_repositorio_mira_ficheros_de_verdad():
    """Un barrido que no encuentra nada que leer está verde por no trabajar.

    Sin esto, un error en el filtro dejaría el test en verde para siempre
    mientras no vigila ni un fichero, que es la forma más silenciosa de
    quedarse sin guardián.
    """
    barridos = _ficheros_barridos()

    assert len(barridos) >= 60
    assert any(fichero.suffix == ".md" for fichero in barridos)
    assert any(fichero.suffix == ".py" for fichero in barridos)
    assert any(fichero.suffix == ".ps1" for fichero in barridos)


def test_f006_r26_el_barrido_cubre_el_punto_ciego_que_dejo_pasar_h1():
    """Los informes de `progress/` entran. Es **el** motivo de este fichero.

    Se nombran rutas concretas y no «hay algo de progress»: el hueco de H1 fue
    exactamente que `progress/current.md` —el fichero que un agente escribe
    después de mirar el portal de Azure— no lo miraba nadie. Se comprueban
    también `docs/`, `infra/`, `specs/` y la raíz, que son el resto del árbol
    que quedaba fuera.
    """
    barridos = {fichero.relative_to(RAIZ).as_posix() for fichero in _ficheros_barridos()}

    for ruta in (
        "progress/current.md",
        "progress/impl_F-006.md",
        "docs/INTEGRACION.md",
        "specs/F-006-sharepoint/design.md",
        "CLAUDE.md",
    ):
        assert ruta in barridos, f"el barrido no mira {ruta}"

    assert any(ruta.startswith("infra/") for ruta in barridos)


# --------------------------------------------------------------------------
# El barrido en sí
# --------------------------------------------------------------------------


def test_f006_r26_ningun_fichero_del_repositorio_incrusta_un_identificador():
    """R26 · ni un GUID: ni de tenant, ni de sitio, ni de biblioteca, ni de app.

    Da igual que el repositorio sea privado: el historial de git no suelta lo
    que entra. Y da igual que el GUID sea inventado: quien lo lea no puede
    distinguirlo de uno de verdad.

    Si esto falla, **no se relaja el patrón ni se amplía la tolerancia**: se
    saca el valor del fichero. Y si ya está commiteado, se avisa al humano,
    porque quitarlo del árbol no lo quita del historial.
    """
    assert _hallazgos() == {}


def test_f006_r26_la_tolerancia_del_barrido_no_crece_sin_que_se_vea():
    """Tres ficheros, **un** GUID cada uno, y ni uno más.

    Una lista de excepciones que se puede ampliar en silencio deja de ser una
    defensa al tercer viernes. Que los números vivan aquí obliga a tocarlos
    —y a explicarlo en la revisión— para ampliarla.
    """
    assert len(GUID_TOLERADO_POR_FICHERO) == 3

    for ruta, tolerados in GUID_TOLERADO_POR_FICHERO.items():
        fichero = RAIZ / ruta
        assert fichero.is_file(), f"{ruta} ya no existe: sobra la tolerancia"
        encontrados = PATRON_GUID.findall(fichero.read_text(encoding="utf-8", errors="replace"))
        assert len(encontrados) == tolerados, f"{ruta} ya no lleva {tolerados}"


# --------------------------------------------------------------------------
# Controles negativos: el barrido caza lo que tiene que cazar
# --------------------------------------------------------------------------


def test_f006_r26_el_barrido_caza_un_guid_escrito_en_un_informe(tmp_path):
    """El caso **exacto** de H1: un GUID dentro de un fichero de `progress/`.

    Se monta un árbol de mentira porque el caso real no se puede reproducir en
    el repositorio de verdad sin escribir en él lo que este test prohíbe. Lo
    que se ejercita es el barrido entero —recorrido, filtros y recuento—, no
    solo la expresión regular.
    """
    inventado = guid_compuesto("a1b2c3d4", "e5f6", "4a7b", "8c9d", "e0f1a2b3c4d5")
    informe = tmp_path / "progress" / "impl_F-999.md"
    informe.parent.mkdir(parents=True)
    informe.write_text(
        f"## Lo verificado en Azure\n\n- App registration, appId `{inventado}`.\n",
        encoding="utf-8",
    )

    assert _hallazgos(tmp_path) == {"progress/impl_F-999.md": 1}


@pytest.mark.parametrize(
    "ruta",
    (
        "docs/INTEGRACION.md",
        "infra/desplegar.ps1",
        "specs/F-006-sharepoint/design.md",
        "CHECKPOINTS.md",
        "harness/features.json",
    ),
)
def test_f006_r26_el_barrido_caza_un_guid_en_cualquier_rincon(tmp_path, ruta):
    """Y no solo en `progress/`: el alcance es el árbol entero.

    Cinco sitios que el barrido anterior tampoco miraba, uno por tipo de
    fichero. El GUID va con mayúsculas a propósito: el patrón no distingue
    caja, y un identificador copiado del portal de Azure llega como llega.
    """
    inventado = guid_compuesto("F9E8D7C6", "B5A4", "4321", "9876", "0A1B2C3D4E5F")
    fichero = tmp_path / ruta
    fichero.parent.mkdir(parents=True, exist_ok=True)
    fichero.write_text(f"SHAREPOINT_SITE_ID={inventado}\n", encoding="utf-8")

    assert _hallazgos(tmp_path) == {ruta: 1}


def test_f006_r26_el_barrido_cuenta_todos_los_del_fichero_no_solo_el_primero(tmp_path):
    """Tres GUID en un fichero son tres, no uno.

    Importa porque la tolerancia se expresa en número: si el recuento se
    quedara en el primero, un fichero tolerado podría llevar cuatro
    identificadores reales y seguir en verde.
    """
    fichero = tmp_path / "progress" / "impl_F-999.md"
    fichero.parent.mkdir(parents=True)
    fichero.write_text(
        "\n".join(
            guid_compuesto("00112233", "4455", "4667", "8899", f"aabbccddee{numero:02d}")
            for numero in range(3)
        ),
        encoding="utf-8",
    )

    assert _hallazgos(tmp_path) == {"progress/impl_F-999.md": 3}


# --------------------------------------------------------------------------
# Controles positivos: el barrido NO muerde lo que es legítimo
# --------------------------------------------------------------------------


def test_f006_r26_el_barrido_no_mira_lo_que_no_esta_versionado(tmp_path):
    """La configuración local de quien trabaja **debe** llevar identificadores.

    Este es el control que mantiene vivo al guardián. Un barrido que fallara
    en cuanto alguien rellena su `.env` o abre el proyecto en el IDE se
    desactivaría en tres semanas, y volveríamos justo al punto de partida de
    H1: un repositorio sin nadie mirando.
    """
    inventado = guid_compuesto("11223344", "5566", "4778", "899a", "bbccddeeff00")
    for ruta in (
        ".venv/lib/paquete.py",
        ".idea/workspace.json",
        "muestras/indice.txt",
        "services/postventa-api/local.settings.json",
        "services/postventa-api/__pycache__/basura.py",
        "coverage.json",
    ):
        fichero = tmp_path / ruta
        fichero.parent.mkdir(parents=True, exist_ok=True)
        fichero.write_text(f'{{"SHAREPOINT_SITE_ID": "{inventado}"}}', encoding="utf-8")

    assert _hallazgos(tmp_path) == {}


@pytest.mark.parametrize(
    "texto",
    (
        # Prosa real de `progress/`: se habla de identificadores sin escribirlos.
        (
            "El app registration existe. **Su appId no se escribe aquí**: se "
            "consulta con `az ad app list` cuando haga falta."
        ),
        (
            "El service principal tiene `Sites.Selected`, `Sites.ReadWrite.All` "
            "y `Sites.FullControl.All` consentidos."
        ),
        (
            "Faltan `SHAREPOINT_SITE_ID`, `SHAREPOINT_DRIVE_ID` y "
            "`GRAPH_TENANT_ID` en `.env.example`."
        ),
        "ni un identificador con forma de GUID entra en el repositorio",
        # Trazas y valores enmascarados a propósito, que no son un valor.
        "appId (enmascarado por el líder)",
        "El GUID inventado de la traza de T13 (`b7e41c92-…`) sigue en el historial.",
        "SHAREPOINT_SITE_ID=<pon-aqui-el-id-del-sitio>",
        "GRAPH_CLIENT_SECRET=pon-aqui-el-secreto",
        # Identificadores del proyecto que no son GUID y se parecen de lejos.
        "Entró en el commit `f2e317b`, que ya está en `dev`; `a2c2bae` lo quita.",
        "hash del parte: d41d8cd98f00b204e9800998ecf8427e",
        "PUERTA COBERTURA [OK] 98.2% (336/342, umbral 80%)",
        "drive-de-mentira / item-0001 / https://ejemplo.invalido/sitios/posventa",
        "Arnés v1.5.2 (2026-08-18), rama feature/F-006-sharepoint",
        # El borde por abajo: le falta un carácter a cada grupo.
        "1234567-1234-1234-1234-123456789012",
        "12345678-123-1234-1234-123456789012",
        "12345678-1234-1234-1234-12345678901",
        # Y hexadecimal no es cualquier letra.
        "g1234567-1234-1234-1234-123456789012",
    ),
)
def test_f006_r26_el_barrido_no_muerde_la_prosa_de_los_informes(texto):
    """Ni una de estas frases puede disparar la alarma.

    Todas salen de `progress/`, de `docs/` o de la salida del arnés, y todas
    hablan de identificadores **sin serlo**. Un patrón que salte con esto se
    acaba comentando, y entonces ya no protege de nada.
    """
    assert PATRON_GUID.findall(texto) == []
