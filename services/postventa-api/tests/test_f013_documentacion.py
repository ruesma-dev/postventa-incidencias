# services/postventa-api/tests/test_f013_documentacion.py
"""La documentación y la infra de despliegue que F-013 deja al día (T17; R26, R29).

Al modo de `test_f012_documentacion.py`. Un documento desactualizado que
parece vigente hace más daño que no tenerlo, y aquí vale doble: lo que F-013
cambia es **dónde aterriza un PDF con el DNI de un cliente**, en una
biblioteca sincronizada por OneDrive en los equipos de Posventa.

Lo que fija:

- **R29** · cada documento que decía otra cosa lleva un **recuadro fechado**
  que **cita literal** la premisa que se enmienda —sitio de IT, carpeta por
  código de obra, «sin listados de carpeta», «F-013 sale casi gratis»— y dice
  qué la invalidó y quién lo decidió. **Nada se borra**: la premisa citada
  sigue también en su sitio, fuera del recuadro.
- **R26** · la documentación dice, con fecha, que los **133** partes de IT se
  quedan allí, que no se migran, no se borran y no se les retira la traza, y
  que por eso Posventa no los contiene ni los contendrá; y **no** documenta
  cómo localizarlos (enmienda del 2026-09-22).
- **R43** · el procedimiento para deshacer una carpeta creada por error, con
  una consulta **de solo lectura**.
- **El runbook del corte** (`design.md` §7.3 enmendado el 2026-09-24): crear
  desde el principio, aviso a Posventa antes, comprobaciones del mismo día y
  los tres frenos; y los dos scripts con sus parámetros reales.
- **La infra**: `$EstructuraArchivo`, `$CarpetaBaseArchivo` y
  `$CrearCarpetasArchivo`, en `por_obra` / `Postventa` / `true` **hasta el
  corte**, escritas por el despliegue; las ventanas de escritura, intactas.
- **`.env.example`** con las cinco variables nuevas de T5 y los mismos
  valores por defecto que el código.

Ni un valor real: los documentos se barren además en
`test_f005_integracion_sin_secretos.py` y `test_f006_repo_sin_identificadores.py`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from config.settings import Ajustes
from domain.models.destino_posventa import MotivoDestino

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent
SERVICIO = RAIZ / "services" / "postventa-api"

INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"
DESPLIEGUE = RAIZ / "docs" / "DESPLIEGUE.md"
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
REQUISITOS_F006 = RAIZ / "specs" / "F-006-sharepoint" / "requirements.md"
DISENO_F006 = RAIZ / "specs" / "F-006-sharepoint" / "design.md"
VARIABLES_INFRA = RAIZ / "infra" / "00_vars_postventa.ps1"
DESPLIEGUE_BACKEND = RAIZ / "infra" / "desplegar_backend.ps1"
EJEMPLO_ENV = SERVICIO / ".env.example"

DOCUMENTOS = (INTEGRACION, DESPLIEGUE, ARQUITECTURA)

#: La fecha de los recuadros de este trabajo, y la feature que los firma.
FECHA = "2026-09-24"

#: Las cinco variables de T5 (`config/settings.py`) y el campo que alimentan.
VARIABLES_DE_F013 = {
    "SHAREPOINT_ESTRUCTURA": "sharepoint_estructura",
    "SHAREPOINT_CARPETA_INCIDENCIAS": "sharepoint_carpeta_incidencias",
    "SHAREPOINT_CARPETA_FIRMADOS": "sharepoint_carpeta_firmados",
    "SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA": "sharepoint_carpeta_firmados_alternativa",
    "SHAREPOINT_CREAR_CARPETAS": "sharepoint_crear_carpetas",
}

#: La variable retirada en T4 (R1, R3). Que no vuelva por inercia a ningún
#: documento ni script: se nombra aquí troceada para que este fichero no la
#: contenga entera y el barrido de abajo pueda mirarlo también.
VARIABLE_RETIRADA = "SHAREPOINT_" + "NOMBRE_UNIDAD"

#: R29 · las premisas de `docs/INTEGRACION.md` §3 que F-013 enmienda, tal y
#: como están escritas (sin el marcado de negrita).
PREMISAS_DE_INTEGRACION = (
    "El de IT, el mismo donde vive la biblioteca de albaranes",
    "Propia de este proyecto, no la de nadie más",
    "debajo una carpeta por código de obra",
    (
        "Una subida por parte, sin listados de carpeta: se pide el fichero por su "
        "nombre exacto, nunca el contenido entero de la carpeta de una obra."
    ),
    "es la feature F-013, y sale casi gratis porque la ruta es configuración y no código",
)

#: R29 · las de `docs/DESPLIEGUE.md`.
PREMISAS_DE_DESPLIEGUE = (
    "El archivo definitivo de Posventa. Se archiva en la biblioteca de dev; mudarlo es F-013.",
    "archivar el parte apto en la biblioteca de dev del sitio de IT",
)

#: R29 · las de `docs/ARCHITECTURE.md`: el paso 6 y la fila de SharePoint.
PREMISAS_DE_ARQUITECTURA = (
    "subida a SharePoint, en `<carpeta base>/<código de obra>/`",
    "Mientras estemos en dev, biblioteca propia en el sitio de IT",
    "es la feature F-013, y sale casi gratis porque la ruta es configuración",
)

#: R29 · las de la spec de F-006: vocabulario «Destino de dev», R10, R11, R27.
PREMISAS_DE_REQUISITOS_F006 = (
    "biblioteca propia dentro del sitio de IT, el mismo donde vive la de albaranes",
    "`<carpeta base>/<código de obra>`, con la carpeta base leída de configuración",
    (
        "CUANDO la carpeta del código de obra no existe en la biblioteca, el sistema "
        "debe crearla antes de subir el fichero."
    ),
    "eso es lo que hace posible F-013 sin rehacer nada",
)

#: R29 · la de `design.md` §7 de F-006.
PREMISAS_DE_DISENO_F006 = (
    (
        "F-013 —mudar el archivo a la biblioteca de Posventa— es, gracias a esto, "
        "cambiar tres variables y su documento"
    ),
)

#: R26 · la premisa H4 del 2026-09-18 y las dos frases del humano que la
#: enmiendan, literales.
PREMISA_H4 = "Lo ya archivado en IT se queda en IT, sin migración, y se documenta que sigue allí"
FRASES_DEL_HUMANO_SOBRE_IT = (
    "lo que esta en IT eran pruebas, se puede olvidar",
    "los partes en IT se pueden olvidar, pero no borrar",
)

#: Lo que una consulta de solo lectura no puede llevar.
PATRON_SQL_QUE_ESCRIBE = re.compile(
    r"\b(?:INSERT|UPDATE|DELETE|MERGE|TRUNCATE|DROP|ALTER|CREATE|GRANT)\b", re.IGNORECASE
)


def _normal(texto: str) -> str:
    """Sin negritas, sin comillas de código y sin saltos: la cita se compara
    por su texto, no por su marcado."""
    return " ".join(texto.replace("*", "").replace("`", "").split())


def _recuadros(texto: str) -> list[str]:
    """Cada bloque de citas (`> ...`) del documento, ya normalizado."""
    bloques: list[list[str]] = []
    dentro = False
    for linea in texto.splitlines():
        if linea.lstrip().startswith(">"):
            if not dentro:
                bloques.append([])
            bloques[-1].append(linea.lstrip()[1:])
            dentro = True
        else:
            dentro = False
    return [_normal(" ".join(bloque)) for bloque in bloques]


#: Cómo empieza un recuadro de este trabajo: fechado en su cabecera, no de pasada.
CABECERA_DE_RECUADRO = re.compile(rf"^(?:Enmienda|Precisión) del {FECHA} \(F-013\)")


def _recuadros_de_f013(texto: str) -> list[str]:
    """Los recuadros cuya **cabecera** lleva la fecha y la feature (R29)."""
    return [recuadro for recuadro in _recuadros(texto) if CABECERA_DE_RECUADRO.match(recuadro)]


def _leer(documento: Path) -> str:
    return documento.read_text(encoding="utf-8")


def _seccion(texto: str, titulo: str) -> str:
    """Desde el título (`## …` o `### …`) hasta el siguiente del mismo nivel o superior."""
    inicio = texto.index(titulo)
    nivel = len(titulo) - len(titulo.lstrip("#"))
    siguiente = re.compile(rf"^#{{1,{nivel}}} ", re.MULTILINE)
    fin = siguiente.search(texto, inicio + len(titulo))
    return texto[inicio : fin.start() if fin else len(texto)]


def _comprobar_citas(documento: Path, premisas: tuple[str, ...]) -> None:
    """Cada premisa, citada en un recuadro de F-013 **y** viva en su sitio."""
    texto = _leer(documento)
    recuadros = _recuadros_de_f013(texto)
    fuera_de_los_recuadros = _normal(
        " ".join(linea for linea in texto.splitlines() if not linea.lstrip().startswith(">"))
    )

    assert recuadros, f"{documento.name} no tiene ningún recuadro fechado de F-013"
    for premisa in premisas:
        citada = _normal(premisa)
        assert any(citada in recuadro for recuadro in recuadros), (
            f"{documento.name}: ningún recuadro de F-013 cita «{premisa}»"
        )
        assert citada in fuera_de_los_recuadros, (
            f"{documento.name}: «{premisa}» ya no está en su sitio; nada se borra (R29)"
        )


# --------------------------------------------------------------------------
# R29 · los recuadros fechados citan literal la premisa
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("documento", "premisas"),
    (
        (INTEGRACION, PREMISAS_DE_INTEGRACION),
        (DESPLIEGUE, PREMISAS_DE_DESPLIEGUE),
        (ARQUITECTURA, PREMISAS_DE_ARQUITECTURA),
        (REQUISITOS_F006, PREMISAS_DE_REQUISITOS_F006),
        (DISENO_F006, PREMISAS_DE_DISENO_F006),
    ),
    ids=("INTEGRACION", "DESPLIEGUE", "ARCHITECTURE", "F-006-requirements", "F-006-design"),
)
def test_f013_r29_los_recuadros_citan_literal_la_premisa(documento, premisas):
    """R29 · la premisa entre comillas, y la de verdad sigue en su sitio."""
    _comprobar_citas(documento, premisas)


@pytest.mark.parametrize(
    "documento",
    (INTEGRACION, DESPLIEGUE, ARQUITECTURA, REQUISITOS_F006, DISENO_F006),
    ids=lambda ruta: ruta.name if ruta.parent.name == "docs" else f"F-006-{ruta.name}",
)
def test_f013_r29_los_recuadros_dicen_que_la_invalido_y_quien(documento):
    """R29 · «qué la invalidó y quién lo decidió»: el humano, y cuándo."""
    recuadros = " ".join(_recuadros_de_f013(_leer(documento)))

    assert "humano" in recuadros
    assert "2026-09-18" in recuadros


PREMISA_DE_PRUEBA = "La carpeta es **una por código de obra**, y sale casi gratis."
RECUADRO_DE_PRUEBA = "> **Enmienda del 2026-09-24 (F-013).** Lo decidió el humano el 2026-09-18."


@pytest.mark.parametrize(
    "documento",
    (
        # Parafrasea en vez de citar.
        f"{PREMISA_DE_PRUEBA}\n\n{RECUADRO_DE_PRUEBA} Ya no es una carpeta por obra.\n",
        # Cita, pero la premisa se ha borrado de su sitio.
        f"{RECUADRO_DE_PRUEBA} Decía «{PREMISA_DE_PRUEBA}».\n",
        # Cita y conserva, pero el recuadro no lleva fecha.
        f"{PREMISA_DE_PRUEBA}\n\n> **Enmienda (F-013).** Decía «{PREMISA_DE_PRUEBA}».\n",
    ),
    ids=("parafrasea", "borra-la-premisa", "sin-fecha"),
)
def test_f013_r29_el_control_de_citas_caza_lo_que_no_es_citar(tmp_path, documento):
    """Controles negativos: el control de R29 no se conforma con cualquier cosa."""
    fichero = tmp_path / "DOC.md"
    fichero.write_text(documento, encoding="utf-8")

    with pytest.raises(AssertionError):
        _comprobar_citas(fichero, (PREMISA_DE_PRUEBA,))


def test_f013_r29_el_control_de_citas_acepta_una_cita_bien_hecha(tmp_path):
    """Y el positivo: premisa en su sitio y citada, con marcado distinto, pasa."""
    fichero = tmp_path / "DOC.md"
    fichero.write_text(
        f"{PREMISA_DE_PRUEBA}\n\n{RECUADRO_DE_PRUEBA} Decía «La carpeta es una por\n> código de obra, y sale casi gratis.»\n",
        encoding="utf-8",
    )

    _comprobar_citas(fichero, (PREMISA_DE_PRUEBA,))


def test_f013_r29_el_recuadro_de_arquitectura_esta_en_el_paso_6():
    """El paso 6 es el que dice dónde se archiva: el recuadro va dentro de él."""
    texto = _leer(ARQUITECTURA)
    paso_6 = texto[texto.index("6. **Archivo**") : texto.index("7a. **Gráfico**")]

    assert _recuadros_de_f013(paso_6)


# --------------------------------------------------------------------------
# INTEGRACION.md §3 · sitio, estructura, listados, Sigrid, qué se rompe
# --------------------------------------------------------------------------


def test_f013_r29_integracion_describe_el_destino_de_posventa():
    """El sitio, la biblioteca, la base y la ruta que manda desde el corte."""
    seccion = _normal(_seccion(_leer(INTEGRACION), "## 3 · SharePoint"))

    for texto in (
        "Documentos compartidos",
        "raíz de la biblioteca",
        "PARTES INCIDENCIAS",
        "PARTES FIRMADOS",
        "PARTES FIRMADO",
        "677 MIRASIERRA",
        "VILLA NN",
        "casa por su número",
        "SHAREPOINT_ESTRUCTURA=posventa",
    ):
        assert texto in seccion, f"§3 no dice «{texto}»"


def test_f013_r12_integracion_dice_que_ahora_si_hay_listados():
    """«Sin listados de carpeta» deja de ser verdad, y hay que decir cuántos."""
    seccion = _normal(_seccion(_leer(INTEGRACION), "## 3 · SharePoint"))

    assert "hasta cuatro listados" in seccion
    assert "solo carpetas" in seccion
    assert "nunca los ficheros" in seccion
    assert "solo se sigue si apunta a Graph" in seccion


def test_f013_r41_integracion_declara_la_dependencia_de_sigrid_api_al_archivar():
    """**Dos** lecturas por parte, las dos por `sql/read`, y qué pasa si falla."""
    seccion = _normal(_seccion(_leer(INTEGRACION), "## 3 · SharePoint"))

    assert "dos lecturas" in seccion
    assert "/api/sql/read" in seccion
    assert "sin CIERRE_HABILITADO" in seccion
    assert "UbicacionNoDisponible" in seccion
    assert "ArchivoDeshabilitado" in seccion
    assert "unidades_sin_verificar" in seccion


@pytest.mark.parametrize(
    "caso",
    (
        "renombra la carpeta de obra",
        "423",
        "sigrid-api sin configurar",
        "incluso un parte ya archivado responde 503",
        "SHAREPOINT_ESTRUCTURA mal escrita",
        "el vacío no llega",
    ),
)
def test_f013_integracion_dice_que_se_rompe_con_f013(caso):
    """La tabla «qué se rompe» de F-013, con la decisión del bloque 5.

    El líder decidió el 2026-09-24 dejar que falle cerrado: con `posventa` y
    `sigrid-api` sin configurar, el lector se construye en el borde antes del
    paso y **incluso un parte ya archivado responde 503**. Se documenta aquí,
    que es donde lo busca quien vea el 503.
    """
    seccion = _normal(_seccion(_leer(INTEGRACION), "## 3 · SharePoint"))

    assert caso in seccion, f"la tabla de F-013 no dice «{caso}»"


@pytest.mark.parametrize("motivo", [motivo.value for motivo in MotivoDestino])
def test_f013_r19_integracion_nombra_cada_motivo_del_409(motivo):
    """Los 22 códigos de R18, uno a uno: quien vea un 409 tiene que encontrarlo."""
    assert motivo in _leer(INTEGRACION)


@pytest.mark.parametrize("variable", VARIABLES_DE_F013)
def test_f013_r1_integracion_nombra_las_variables_nuevas_en_su_seccion_4(variable):
    """R1 · en §4, con las demás variables, y sin ningún valor que no sea de ejemplo."""
    seccion = _seccion(_leer(INTEGRACION), "## 4 · Variables de entorno")

    assert variable in seccion


@pytest.mark.parametrize("documento", DOCUMENTOS, ids=lambda ruta: ruta.name)
def test_f013_r1_ningun_documento_resucita_la_variable_retirada(documento):
    """R1, R3 · retirada en T4: no puede volver por inercia."""
    assert VARIABLE_RETIRADA not in _leer(documento)


# --------------------------------------------------------------------------
# R26 · lo que se queda en IT
# --------------------------------------------------------------------------


def test_f013_r26_integracion_dice_que_los_133_se_quedan_en_it():
    """R26 enmendado el 2026-09-22: olvidar no es borrar, y se escribe con fecha."""
    recuadros = [
        recuadro for recuadro in _recuadros_de_f013(_leer(INTEGRACION)) if "133" in recuadro
    ]

    assert recuadros, "ningún recuadro de F-013 habla de los 133 partes de IT"
    recuadro = " ".join(recuadros)
    for texto in (
        "no se migran",
        "no se borran",
        "no se les retira la traza",
        "no los contiene ni los contendrá",
        "no se documenta cómo localizarlos",
        _normal(PREMISA_H4),
        *FRASES_DEL_HUMANO_SOBRE_IT,
    ):
        assert texto in recuadro, f"el recuadro de IT no dice «{texto}»"


def test_f013_r26_integracion_dice_lo_de_h3_de_f034():
    """Un parte archivado en IT **sí** puede adjuntarse y cerrarse (H-3 de F-034)."""
    seccion = _normal(_seccion(_leer(INTEGRACION), "## 3 · SharePoint"))

    assert "exigir_parte_archivado" in seccion
    assert "no su biblioteca" in seccion


# --------------------------------------------------------------------------
# R43 · deshacer una carpeta creada por error
# --------------------------------------------------------------------------


def test_f013_r43_integracion_lleva_el_procedimiento_para_deshacer_una_carpeta():
    """Lo hace una persona; el sistema no borra, no mueve y no renombra nunca."""
    seccion = _normal(_seccion(_leer(INTEGRACION), "### Deshacer una carpeta creada por error"))

    for texto in (
        "lo hace una persona",
        "no borra, no mueve ni renombra",
        "papelera del sitio",
        "item_id",
        "se propaga a los OneDrive",
        "22_ventana_archivo.ps1 -Cerrar",
    ):
        assert texto in seccion, f"el procedimiento de R43 no dice «{texto}»"


def test_f013_r43_la_consulta_es_de_solo_lectura_y_mira_la_carpeta():
    """La consulta que dice qué partes hay en una carpeta antes de deshacerla."""
    seccion = _seccion(_leer(INTEGRACION), "### Deshacer una carpeta creada por error")
    (consulta,) = re.findall(r"```sql\n(.*?)```", seccion, re.DOTALL)

    assert consulta.lstrip().upper().startswith("SELECT")
    assert "postventa.archivos" in consulta
    assert "carpeta" in consulta
    assert PATRON_SQL_QUE_ESCRIBE.findall(consulta) == []


def test_f013_r43_el_barrido_de_sql_caza_una_escritura():
    """Control negativo del barrido de arriba."""
    assert PATRON_SQL_QUE_ESCRIBE.findall("UPDATE postventa.archivos SET carpeta = 'x'")


# --------------------------------------------------------------------------
# DESPLIEGUE.md · el runbook del corte (design.md §7.3 enmendado)
# --------------------------------------------------------------------------

TITULO_DEL_CORTE = "## 9 · El corte de F-013"


def test_f013_t17_el_runbook_del_corte_existe():
    assert TITULO_DEL_CORTE in _leer(DESPLIEGUE)


@pytest.mark.parametrize(
    "texto",
    (
        "Crear desde el principio",
        "sin -VentanasCerradas",
        '$EstructuraArchivo = "posventa"',
        '$CarpetaBaseArchivo = ""',
        '$CrearCarpetasArchivo = "true"',
        "cargar_secretos_postventa.ps1 -Solo",
        "az functionapp config appsettings list",
        "25_mediciones_despliegue.ps1",
        "F-013 carpeta creada:",
        "R31",
        "R33",
        "R42",
        "R43",
        "riesgo 16",
    ),
)
def test_f013_t17_el_runbook_tiene_cada_paso(texto):
    seccion = _normal(_seccion(_leer(DESPLIEGUE), TITULO_DEL_CORTE))

    assert _normal(texto) in seccion, f"el runbook no dice «{texto}»"


def test_f013_t17_el_aviso_a_posventa_va_antes_del_despliegue():
    """T4-3 · con las ventanas abiertas, el aviso es **antes**, no después."""
    seccion = _seccion(_leer(DESPLIEGUE), TITULO_DEL_CORTE)

    assert seccion.index("Avisar a Posventa") < seccion.index("desplegar_backend.ps1")


@pytest.mark.parametrize(
    "freno",
    (
        "22_ventana_archivo.ps1 -Cerrar",
        '$CrearCarpetasArchivo = "false"',
        '$EstructuraArchivo = "por_obra"',
    ),
)
def test_f013_t17_el_runbook_tiene_los_tres_frenos(freno):
    frenos = _normal(_seccion(_leer(DESPLIEGUE), "### Los tres frenos"))

    assert _normal(freno) in frenos


@pytest.mark.parametrize(
    "texto",
    (
        "-UnidadesCsv",
        "-SalidaCsv",
        "-CarpetaFirmadosAlternativa",
        "-DesdeKeyVault",
        "-MostrarNombres",
        "-CarpetaObra",
        "sin BOM",
        "fuera del repositorio",
        "resolver_destino_posventa",
        "nunca obride",
        "LIKE",
    ),
)
def test_f013_t17_el_runbook_documenta_los_dos_scripts_como_son(texto):
    """Los parámetros reales (bloque 4) y el límite conocido del ensayo en seco."""
    scripts = _normal(_seccion(_leer(DESPLIEGUE), "### Los dos scripts de solo lectura"))

    assert _normal(texto) in scripts, f"los scripts no dicen «{texto}»"


# --------------------------------------------------------------------------
# La infra: por_obra hasta el corte, y las ventanas intactas
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("variable", "valor"),
    (("EstructuraArchivo", "por_obra"), ("CarpetaBaseArchivo", "Postventa"), ("CrearCarpetasArchivo", "true")),
)
def test_f013_t17_las_variables_del_destino_valen_lo_de_hasta_el_corte(variable, valor):
    """`design.md` §2.2 · `por_obra` / `Postventa` hasta el corte; crear, `true` (T4-3)."""
    texto = VARIABLES_INFRA.read_text(encoding="ascii")

    assert re.findall(rf'^\${variable} = "(.*)"\r?$', texto, re.MULTILINE) == [valor]


@pytest.mark.parametrize(
    "ajuste",
    (
        '"SHAREPOINT_ESTRUCTURA=$EstructuraArchivo"',
        '"SHAREPOINT_CARPETA_BASE=$CarpetaBaseArchivo"',
        '"SHAREPOINT_CREAR_CARPETAS=$CrearCarpetasArchivo"',
    ),
)
def test_f013_t17_el_despliegue_escribe_el_destino_desde_las_variables(ajuste):
    """En `$ajustes`, en cada despliegue, y con el valor de `00_vars_postventa.ps1`."""
    texto = DESPLIEGUE_BACKEND.read_text(encoding="ascii")
    (ajustes,) = re.findall(r"(?ms)^\$ajustes = @\((.*?)^\)", texto)

    assert ajuste in ajustes


def test_f013_t17_el_despliegue_no_escribe_la_base_a_mano_ni_la_alternativa():
    """La línea que había (`SHAREPOINT_CARPETA_BASE=Postventa`) sale; la alternativa
    vale su defecto del código y no se escribe; nada re-declara las variables."""
    texto = DESPLIEGUE_BACKEND.read_text(encoding="ascii")

    assert "SHAREPOINT_CARPETA_BASE=Postventa" not in texto
    assert "SHAREPOINT_CARPETA_FIRMADOS_ALTERNATIVA=" not in texto
    for variable in ("EstructuraArchivo", "CarpetaBaseArchivo", "CrearCarpetasArchivo"):
        assert not re.search(rf"^\s*\${variable}\s*=", texto, re.MULTILINE)


def test_f013_t17_el_despliegue_dice_a_donde_va_a_archivar():
    """Antes de confirmar y en el resumen: quien despliega ve la estrategia."""
    lineas = [
        linea
        for linea in DESPLIEGUE_BACKEND.read_text(encoding="ascii").splitlines()
        if "Destino del archivo" in linea
    ]

    assert len(lineas) == 2
    for linea in lineas:
        assert "$EstructuraArchivo" in linea
        assert "$CarpetaBaseArchivo" in linea
        assert "$CrearCarpetasArchivo" in linea


def test_f013_t17_las_ventanas_siguen_abiertas_por_defecto():
    """Cambio del 2026-09-23, que F-013 **no** toca (lo fijan los tests de F-010)."""
    texto = DESPLIEGUE_BACKEND.read_text(encoding="ascii")

    assert '$ventanaArchivo = "true"' in texto
    assert '"ARCHIVO_HABILITADO=$ventanaArchivo"' in texto
    assert '"CIERRE_HABILITADO=$ventanaCierre"' in texto


def test_f013_r1_ningun_script_de_infra_escribe_la_variable_retirada():
    for script in sorted((RAIZ / "infra").glob("*.ps1")):
        assert VARIABLE_RETIRADA not in script.read_text(encoding="utf-8-sig"), script.name


# --------------------------------------------------------------------------
# `.env.example` · las cinco variables de T5, con los valores del código
# --------------------------------------------------------------------------


def _declaradas_en_el_ejemplo() -> dict[str, str]:
    declaradas: dict[str, str] = {}
    for linea in EJEMPLO_ENV.read_text(encoding="utf-8").splitlines():
        if "=" in linea and not linea.lstrip().startswith("#"):
            clave, valor = linea.split("=", 1)
            declaradas[clave.strip()] = valor.strip()
    return declaradas


@pytest.mark.parametrize(("variable", "campo"), VARIABLES_DE_F013.items())
def test_f013_t5_el_ejemplo_declara_la_variable_con_el_defecto_del_codigo(variable, campo):
    """Pendiente del bloque 1: el ejemplo dice lo mismo que `config/settings.py`."""
    declaradas = _declaradas_en_el_ejemplo()
    defecto = Ajustes.model_fields[campo].default

    assert variable in declaradas, f"{variable} no está en .env.example"
    esperado = str(defecto).lower() if isinstance(defecto, bool) else str(defecto)
    assert declaradas[variable] == esperado


def test_f013_t5_el_ejemplo_no_resucita_la_variable_retirada():
    assert VARIABLE_RETIRADA not in EJEMPLO_ENV.read_text(encoding="utf-8")


def test_f013_t5_el_ejemplo_sigue_en_por_obra():
    """El ejemplo es para un puesto de trabajo: la estrategia de siempre."""
    assert _declaradas_en_el_ejemplo()["SHAREPOINT_ESTRUCTURA"] == "por_obra"
