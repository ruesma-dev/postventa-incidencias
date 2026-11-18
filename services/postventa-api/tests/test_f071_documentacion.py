# services/postventa-api/tests/test_f071_documentacion.py
"""La documentación que F-071 deja al día (T11; R46, `design.md` §12).

Al modo de `test_f060_documentacion.py`. F-071 saca de Sigrid todos los
desplegables de la plantilla salvo urgencia y listado: la ubicación depende de
la unidad de la fila, el oficio y el proveedor van por código, y los grupos de
equivalencia ya no se aplican a la plantilla. Quien rellene, quien revise y
quien administre `sigrid-api` tienen que poder saberlo sin abrir el código.

Lo que fija:

- **R46** · `docs/ARCHITECTURE.md`: «La plantilla», «La importación», «La
  agrupación de oficios casi duplicados», «Dónde vive cada pieza» y «Lo que no
  hace la revisión»; y que ya no dicen lo que F-071 dejó de ser verdad.
- **R46** · `docs/INTEGRACION.md`: §1 (la lectura de ubicaciones también al
  descargar la plantilla y antes de validar lo importado; la plantilla ya no
  lee PostgreSQL), la fila de `GET /api/plantilla` de §8 y los párrafos de la
  lista cerrada de ubicaciones (§1 «Con F-056» y §4).
- Que nada de lo nuevo lleva valores (el barrido de
  `test_f005_integracion_sin_secretos.py`) ni un correo escrito.

Los controles **leen el código** cuando pueden —la versión, el código
`version_anterior`, los nombres de la validación dependiente, las claves del
YAML, los módulos—. La copia de `azure-apps/` la pone al día el líder al
desplegar (R46): es otro repositorio y no se comprueba aquí. Sin red, sin base,
sin IA.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from domain.models.errores import CODIGOS_FICHERO_NO_ES_PLANTILLA
from domain.models.plantilla_incidencias import VERSION_ANTERIOR, VERSION_PLANTILLA

from tests.test_f005_integracion_sin_secretos import hallazgos

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent
SERVICIO = RAIZ / "services" / "postventa-api"

INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
YAML_DE_LA_PLANTILLA = SERVICIO / "config" / "plantilla_incidencias.yaml"
GENERADOR = SERVICIO / "infrastructure" / "documentos" / "excel_openpyxl.py"

SPEC = "specs/F-071-plantilla-desde-sigrid/"

TITULO_DE_LA_ENTRADA = "## Entrada de incidencias (F-036)"
TITULO_DE_LA_REVISION = "## Revisión de la bandeja (F-056)"
TITULO_DE_LA_LECTURA = "### Con F-071 · la tercera lectura, también en la plantilla"
TITULO_DE_F056 = "### Con F-056 · la tercera lectura: las ubicaciones válidas"
TITULO_DE_F060 = "### Con F-060 · la tercera lectura, también tras importar"
TITULO_DE_F065 = "### Con F-065 · la cuarta lectura: las reclamaciones de la obra"

#: El módulo nuevo de F-071 y lo que retiró (R45), por su ruta en el servicio.
MODULO_NUEVO = "domain/models/casado_con_lista.py"
RETIRADOS = (
    "scripts/migrar_excel_f036.py",
    "scripts/migracion_f036.py",
    "scripts/migracion_f036_correcciones.yaml",
)

#: Un correo escrito, de cualquier dominio: los documentos no llevan ninguno.
CORREO = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")


def _leer(documento: Path) -> str:
    return documento.read_text(encoding="utf-8")


def _normal(texto: str) -> str:
    """Sin negritas, sin comillas de código, sin la marca `>` de los recuadros y
    sin saltos: se compara lo que el documento **dice**."""
    sin_recuadro = "\n".join(re.sub(r"^\s*>\s?", "", linea) for linea in texto.splitlines())
    return " ".join(sin_recuadro.replace("*", "").replace("`", "").split())


def _seccion(texto: str, titulo: str) -> str:
    """Desde el título (`## …` o `### …`) hasta el siguiente del mismo nivel o superior."""
    assert titulo in texto, f"no se encuentra la sección «{titulo}»"
    inicio = texto.index(titulo)
    nivel = len(titulo) - len(titulo.lstrip("#"))
    siguiente = re.compile(rf"^#{{1,{nivel}}} ", re.MULTILINE)
    fin = siguiente.search(texto, inicio + len(titulo))
    return texto[inicio : fin.start() if fin else len(texto)]


def _dice(texto: str, frase: str) -> bool:
    """Si el texto dice la frase, sin mirar mayúsculas: una frase puede abrir
    una viñeta en negrita («**La ubicación depende…**») y decir lo mismo."""
    return frase.casefold() in texto.casefold()


def _fila(texto: str, principio: str) -> str:
    """La fila de una tabla de Markdown que empieza por `principio`."""
    filas = [linea for linea in texto.splitlines() if linea.startswith(principio)]
    assert len(filas) == 1, f"se esperaba una fila que empiece por «{principio}»: {len(filas)}"
    return filas[0]


def _entrada(titulo: str) -> str:
    """Una subsección de «Entrada de incidencias (F-036)» de la arquitectura."""
    return _seccion(_seccion(_leer(ARQUITECTURA), TITULO_DE_LA_ENTRADA), titulo)


def _integracion(titulo: str) -> str:
    return _seccion(_leer(INTEGRACION), titulo)


def _textos_nuevos() -> dict[str, str]:
    """Las piezas que escribe F-071, por dónde viven."""
    return {
        "La plantilla": _entrada("### La plantilla"),
        "La importación": _entrada("### La importación, y el Excel de errores"),
        "La agrupación": _entrada("### La agrupación de oficios casi duplicados"),
        "Dónde vive cada pieza": _entrada("### Dónde vive cada pieza"),
        "Lo que no hace la revisión": _seccion(
            _seccion(_leer(ARQUITECTURA), TITULO_DE_LA_REVISION),
            "### Lo que no hace la revisión",
        ),
        "§1 Con F-071": _integracion(TITULO_DE_LA_LECTURA),
    }


# --------------------------------------------------------------------------
# Los controles leen el código: que no lean nada vacío
# --------------------------------------------------------------------------


def test_f071_t11_los_controles_leen_algo_del_codigo():
    """Un control que no lee nada da verde para siempre: se fija lo que leen."""
    assert (VERSION_PLANTILLA, VERSION_ANTERIOR) == (2, 1)
    assert "version_anterior" in CODIGOS_FICHERO_NO_ES_PLANTILLA
    generador = _leer(GENERADOR)
    assert '"tabla_ubicaciones_de_unidad"' in generador
    assert '"ubicaciones_ninguna"' in generador
    assert "INDIRECT(" in generador
    claves = set(yaml.safe_load(_leer(YAML_DE_LA_PLANTILLA)))
    # F-072 R9 (sustituye a `{"urgencias", "listados"} <= claves`).
    assert "urgencias" in claves
    assert "listados" not in claves
    assert "ubicaciones" not in claves
    assert (SERVICIO / MODULO_NUEVO).is_file()
    for retirado in RETIRADOS:
        assert not (SERVICIO / retirado).exists(), retirado


# --------------------------------------------------------------------------
# R46 · ARCHITECTURE.md: «La plantilla»
# --------------------------------------------------------------------------


def test_f071_r46_la_plantilla_dice_que_todo_sale_de_sigrid_salvo_urgencia_y_listado():
    texto = _normal(_entrada("### La plantilla"))

    for esperado in (
        "F-071",
        "todos los desplegables salen de Sigrid salvo urgencia y listado",
        "config/plantilla_incidencias.yaml",
        f"versión {VERSION_PLANTILLA}",
        "no lee PostgreSQL",
        "ninguna lectura nueva",
    ):
        assert esperado in texto, f"«La plantilla» no dice «{esperado}»"


def test_f071_r46_la_plantilla_dice_que_la_ubicacion_depende_de_la_unidad():
    texto = _normal(_entrada("### La plantilla"))

    for esperado in (
        "la ubicación depende de la unidad",
        "tabla_ubicaciones_de_unidad",
        "ubicaciones_ninguna",
        "INDIRECT",
        "prmtpl.ubica",
        "una fila sin unidad no ofrece ninguna",
    ):
        assert _dice(texto, esperado), f"«La plantilla» no dice «{esperado}»"


def test_f071_r46_la_plantilla_dice_oficio_y_proveedor_por_codigo_sin_grupos():
    texto = _normal(_entrada("### La plantilla"))

    for esperado in (
        "el oficio y el proveedor van por código",
        "una entrada por código",
        "los grupos de equivalencia ya no se aplican a la plantilla",
    ):
        assert _dice(texto, esperado), f"«La plantilla» no dice «{esperado}»"


def test_f071_r46_la_plantilla_ya_no_dice_lo_de_antes():
    texto = _normal(_entrada("### La plantilla"))

    for retirado in (
        "Las ubicaciones son una lista cerrada versionada",
        "una entrada por oficio real",
    ):
        assert retirado not in texto, f"«La plantilla» sigue diciendo «{retirado}»"


# --------------------------------------------------------------------------
# R46 · ARCHITECTURE.md: «La importación»
# --------------------------------------------------------------------------


def test_f071_r46_la_importacion_dice_lo_nuevo():
    texto = _normal(_entrada("### La importación, y el Excel de errores"))

    for esperado in (
        "version_anterior",
        f"versión {VERSION_ANTERIOR}",
        "ubicaciones de cada unidad",
        "contra las de la unidad de su fila",
        "la misma regla de F-060",
        "ya no hay oficio_ambiguo de entrada",
        f"versión {VERSION_PLANTILLA}",
    ):
        assert esperado in texto, f"«La importación» no dice «{esperado}»"


def test_f071_r46_la_importacion_ya_no_dice_que_no_hay_casado():
    texto = _normal(_entrada("### La importación, y el Excel de errores"))

    for retirado in (
        "No hay casado aproximado: lo que no es exacto, vuelve.",
        "si su grupo tiene varios códigos en la obra",
    ):
        assert retirado not in texto, f"«La importación» sigue diciendo «{retirado}»"


def test_f071_r46_la_lectura_aislada_ya_no_nombra_el_script_de_migracion():
    texto = _normal(_entrada("### La lectura aislada en un proceso hijo (R118–R120)"))

    assert "sigue leyendo en proceso" not in texto
    assert "se retiró en F-071" in texto


# --------------------------------------------------------------------------
# R46 · ARCHITECTURE.md: la agrupación, dónde vive cada pieza y la revisión
# --------------------------------------------------------------------------


def test_f071_r46_la_agrupacion_ya_no_se_aplica_a_la_plantilla():
    texto = _normal(_entrada("### La agrupación de oficios casi duplicados"))

    for esperado in (
        "Enmienda del 2026-11-09 (F-071)",
        "ya no se aplican a la plantilla",
        "ni a la importación",
        "la revisión de lo ya importado",
        "oficio_ambiguo",
    ):
        assert esperado in texto, f"«La agrupación» no dice «{esperado}»"
    assert "la plantilla enseña una entrada por grupo" not in texto


def test_f071_r46_donde_vive_cada_pieza_nombra_el_casado_y_la_migracion_retirada():
    texto = _normal(_entrada("### Dónde vive cada pieza"))

    for esperado in (
        MODULO_NUEVO.removeprefix("domain/models/"),
        "UbicacionesValidasPort",
        "se retiró en F-071",
        *(Path(r).name for r in RETIRADOS),
    ):
        assert esperado in texto, f"«Dónde vive cada pieza» no dice «{esperado}»"


def test_f071_r46_lo_que_no_hace_la_revision_dice_que_la_lista_del_yaml_ya_no_existe():
    texto = _normal(
        _seccion(
            _seccion(_leer(ARQUITECTURA), TITULO_DE_LA_REVISION),
            "### Lo que no hace la revisión",
        )
    )

    assert "la lista de ubicaciones del YAML ya no existe" in texto
    assert "F-071" in texto
    assert "que sigue ofreciendo la lista de ubicaciones" not in texto


def test_f071_r46_la_fila_de_sigrid_api_de_la_arquitectura_nombra_f071():
    fila = _normal(_fila(_leer(ARQUITECTURA), "| `sigrid-api` |"))

    assert "Desde F-071" in fila
    assert "al descargar la plantilla" in fila


# --------------------------------------------------------------------------
# R46 · INTEGRACION.md §1
# --------------------------------------------------------------------------


def test_f071_r46_la_seccion_uno_tiene_la_lectura_de_f071_en_su_sitio():
    """Dentro de «Qué consumimos hoy», tras la de F-060 y antes de la de F-065."""
    uno = _integracion("## 1 · Qué consumimos hoy")

    assert TITULO_DE_LA_LECTURA in uno
    assert uno.index(TITULO_DE_F060) < uno.index(TITULO_DE_LA_LECTURA) < uno.index(TITULO_DE_F065)


def test_f071_r46_la_seccion_uno_describe_cuando_se_lee():
    texto = _normal(_integracion(TITULO_DE_LA_LECTURA))

    for esperado in (
        "ninguna lectura nueva",
        "POST /api/sql/read",
        "al descargar la plantilla",
        "antes de validar",
        "version_anterior",
        "ya_importado",
        "hasta cuatro",
        "1.000 filas",
        "catalogo_sin_verificar",
        "CatalogoNoDisponible",
        "503",
        "no pide ningún cambio",
        SPEC,
    ):
        assert esperado in texto, f"§1 «Con F-071» no dice «{esperado}»"


def test_f071_r46_la_seccion_uno_dice_lo_que_cambia_en_la_plantilla():
    texto = _normal(_integracion(TITULO_DE_LA_LECTURA))

    for esperado in (
        "todos los desplegables salen de Sigrid salvo urgencia y listado",
        "la ubicación depende de la unidad",
        "el oficio y el proveedor van por código",
        "los grupos de equivalencia ya no se aplican a la plantilla",
        "la plantilla ya no lee PostgreSQL",
        "postventa.decisiones_equivalencia",
        "la lista cerrada de ubicaciones de config/plantilla_incidencias.yaml ya no existe",
        "Ninguna variable de entorno",
    ):
        assert _dice(texto, esperado), f"§1 «Con F-071» no dice «{esperado}»"


def test_f071_r46_la_fila_de_sigrid_api_de_la_seccion_uno_nombra_f071():
    fila = _normal(_fila(_integracion("## 1 · Qué consumimos hoy"), "| `sigrid-api` |"))

    assert "Desde F-071" in fila
    assert "F-071" in fila.rsplit("|", 2)[1]


def test_f071_r46_la_lectura_de_f056_ya_no_dice_que_la_plantilla_ofrece_el_yaml():
    texto = _normal(_integracion(TITULO_DE_F056))

    assert "sigue ofreciendo la lista" not in texto
    assert "desde F-071" in texto


# --------------------------------------------------------------------------
# R46 · INTEGRACION.md §4 y §8
# --------------------------------------------------------------------------


def test_f071_r46_la_seccion_cuatro_ya_no_dice_que_la_lista_de_ubicaciones_es_del_yaml():
    texto = _normal(_integracion("### Las de F-036: ninguna"))

    assert "la lista cerrada de ubicaciones son del dominio" not in texto
    assert "F-071" in texto


def test_f071_r46_la_fila_de_la_plantilla_de_la_seccion_ocho_dice_lo_nuevo():
    fila = _normal(_fila(_integracion("## 8 · Qué exponemos nosotros"), "| `GET /api/plantilla` |"))

    assert "con los grupos de oficios confirmados" not in fila
    for esperado in ("F-071", "las ubicaciones de cada unidad", "por código", "No escribe en ningún sitio"):
        assert esperado in fila, f"la fila de la plantilla no dice «{esperado}»"


def test_f071_r46_la_fila_de_la_importacion_de_la_seccion_ocho_dice_la_v1():
    fila = _normal(
        _fila(_integracion("## 8 · Qué exponemos nosotros"), "| `POST /api/importaciones` |")
    )

    assert "version_anterior" in fila


# --------------------------------------------------------------------------
# Lo nuevo no lleva valores
# --------------------------------------------------------------------------


#: Las claves de `_textos_nuevos`, fijas: leer los documentos al recoger los
#: tests tumbaría la recogida entera si faltara una sección.
DONDE = (
    "La plantilla",
    "La importación",
    "La agrupación",
    "Dónde vive cada pieza",
    "Lo que no hace la revisión",
    "§1 Con F-071",
)


def test_f071_t11_las_claves_del_barrido_son_las_de_los_textos_nuevos():
    assert tuple(_textos_nuevos()) == DONDE


@pytest.mark.parametrize("donde", DONDE)
def test_f071_r46_lo_nuevo_no_lleva_valores_ni_correos(donde):
    texto = _textos_nuevos()[donde]

    assert hallazgos(texto) == {}
    assert CORREO.search(texto) is None, f"{donde} lleva un correo escrito"
