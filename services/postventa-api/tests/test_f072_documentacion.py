# services/postventa-api/tests/test_f072_documentacion.py
"""La documentación que F-072 deja al día (T21; R33, `design.md` §3.2 y §11).

Al modo de `test_f071_documentacion.py`. F-072 saca de Sigrid el tipo de
reclamación de punta a punta: la plantilla ofrece los tipos de `dbo.auxtrcp`,
la bandeja guarda el código en una columna nueva, la revisión lo enseña con la
misma clave `listado` y el volcado manda el **tipo efectivo** en vez de
`0002` siempre. Quien revise, quien lea las tablas y quien administre
`sigrid-api` tienen que poder saberlo sin abrir el código.

Lo que fija:

- **R33** · `docs/ARCHITECTURE.md`: la sección «El tipo de reclamación
  (F-072)» —la lectura, la columna, el tipo efectivo, la plantilla y la
  importación, el contrato de `listado` y el volcado—; las enmiendas de «La
  plantilla» de F-071 y de «El parte que se manda» de F-059, que ya no pueden
  decir sin más que el tipo es `0002` siempre.
- **R33** · `docs/INTEGRACION.md`: la lectura de `auxtrcp` (§1), la columna
  `tipo_reclamacion` (§2), el tipo del parte (§3 bis), «Las de F-072» (§4),
  qué se rompe (§6) y las filas de §8 con el contrato de `listado`.
- Que nada de lo nuevo lleva valores (el barrido de
  `test_f005_integracion_sin_secretos.py`) ni un correo escrito.

Los controles **leen el código** cuando pueden —la consulta, el tipo por
defecto, el motivo, el nombre de la columna, la línea de log—. La copia de
`azure-apps/` la pone al día el líder al desplegar (R33, `tasks.md` T25): es
otro repositorio y no se comprueba aquí. La cabecera de `INTEGRACION.md` no se
toca: `test_f065_documentacion.py` la fija a F-065. Sin red, sin base, sin IA.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from domain.models.plantilla_incidencias import TIPO_RECLAMACION_POR_DEFECTO
from domain.models.revision import MotivoNoAprobable
from infrastructure.sigrid.consultas_tipos_reclamacion import SQL_TIPOS_RECLAMACION

from tests.test_f005_integracion_sin_secretos import hallazgos

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent
SERVICIO = RAIZ / "services" / "postventa-api"

INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
YAML_DE_LA_PLANTILLA = SERVICIO / "config" / "plantilla_incidencias.yaml"
SQL_DE_LA_COLUMNA = SERVICIO / "infrastructure" / "persistencia" / "sql" / "17_tipo_reclamacion.sql"
APLICACION_DE_LOS_TIPOS = SERVICIO / "application" / "pipelines" / "tipos_reclamacion.py"

SPEC = "specs/F-072-tipo-reclamacion-sigrid/"

TITULO_DE_F072 = "## El tipo de reclamación (F-072)"
TITULO_DE_LA_ENTRADA = "## Entrada de incidencias (F-036)"
TITULO_DEL_VOLCADO = "## Volcado a Sigrid (F-059)"
TITULO_DE_LA_LECTURA = "### Con F-072 · la quinta lectura: los tipos de reclamación"
TITULO_DE_LA_COLUMNA = "### Con F-072 · la columna `tipo_reclamacion`"
TITULO_DEL_PARTE = "### Qué escribimos como PARTE NUEVO (F-059)"
TITULO_DE_F071 = "### Con F-071 · la tercera lectura, también en la plantilla"

#: Las subsecciones de la sección nueva de la arquitectura, en su orden.
SUBSECCIONES_DE_F072 = (
    "### La lectura: `dbo.auxtrcp`",
    "### La columna `tipo_reclamacion` y el tipo efectivo",
    "### Plantilla e importación",
    "### La revisión: el contrato de `listado`",
    "### El volcado",
    "### Dónde vive cada pieza",
    "### Lo que no hace",
)

#: El nombre de la columna nueva y el de la línea de log de R30.
COLUMNA = "tipo_reclamacion"
LINEA_DE_LOG = "F-072 tipos de reclamación leídos en Sigrid"

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
    """Si el texto dice la frase, sin mirar mayúsculas."""
    return frase.casefold() in texto.casefold()


def _fila(texto: str, principio: str) -> str:
    """La fila de una tabla de Markdown que empieza por `principio`."""
    filas = [linea for linea in texto.splitlines() if linea.startswith(principio)]
    assert len(filas) == 1, f"se esperaba una fila que empiece por «{principio}»: {len(filas)}"
    return filas[0]


def _f072() -> str:
    return _seccion(_leer(ARQUITECTURA), TITULO_DE_F072)


def _de_f072(titulo: str) -> str:
    return _seccion(_f072(), titulo)


def _integracion(titulo: str) -> str:
    return _seccion(_leer(INTEGRACION), titulo)


def _ocho(principio: str) -> str:
    return _normal(_fila(_integracion("## 8 · Qué exponemos nosotros"), principio))


def _textos_nuevos() -> dict[str, str]:
    """Las piezas que escribe F-072, por dónde viven."""
    return {
        "ARCHITECTURE «El tipo de reclamación»": _f072(),
        "INTEGRACION §1 Con F-072": _integracion(TITULO_DE_LA_LECTURA),
        "INTEGRACION §2 Con F-072": _integracion(TITULO_DE_LA_COLUMNA),
        "INTEGRACION §4 Las de F-072": _integracion("### Las de F-072: ninguna"),
    }


# --------------------------------------------------------------------------
# Los controles leen el código: que no lean nada vacío
# --------------------------------------------------------------------------


def test_f072_t21_los_controles_leen_algo_del_codigo():
    """Un control que no lee nada da verde para siempre: se fija lo que leen."""
    assert TIPO_RECLAMACION_POR_DEFECTO == "0002"
    assert MotivoNoAprobable.TIPO_FUERA_DE_SIGRID.value == "tipo_fuera_de_sigrid"
    assert SQL_TIPOS_RECLAMACION.startswith("SELECT cod, res, pos FROM dbo.auxtrcp")
    assert f"ADD COLUMN IF NOT EXISTS {COLUMNA} text" in _leer(SQL_DE_LA_COLUMNA)
    assert LINEA_DE_LOG in _leer(APLICACION_DE_LOS_TIPOS)
    claves = set(yaml.safe_load(_leer(YAML_DE_LA_PLANTILLA)))
    assert "urgencias" in claves and "listados" not in claves


# --------------------------------------------------------------------------
# R33 · ARCHITECTURE.md: «El tipo de reclamación (F-072)»
# --------------------------------------------------------------------------


def test_f072_r33_la_seccion_existe_con_sus_subsecciones_en_orden():
    seccion = _f072()
    posiciones = [seccion.index(titulo) for titulo in SUBSECCIONES_DE_F072]

    assert posiciones == sorted(posiciones)
    assert SPEC in seccion


def test_f072_r33_la_seccion_dice_de_donde_sale_y_que_el_front_no_cambia():
    texto = _normal(_f072())

    for esperado in (
        "de punta a punta",
        "dbo.auxtrcp",
        "el front no cambia",
        f"En blanco, {TIPO_RECLAMACION_POR_DEFECTO}",
        "docs/INTEGRACION.md",
    ):
        assert _dice(texto, esperado), f"la sección no dice «{esperado}»"


def test_f072_r33_la_lectura_dice_la_consulta_cuando_y_los_errores():
    texto = _normal(_de_f072("### La lectura: `dbo.auxtrcp`"))

    for esperado in (
        SQL_TIPOS_RECLAMACION,
        "POST /api/sql/read",
        "una vez por petición",
        "sin caché entre peticiones",
        "después del catálogo y de las ubicaciones",
        "no la hacen",
        "CatalogoSinVerificar",
        "CatalogoNoDisponible",
        LINEA_DE_LOG,
        "nunca un res",
    ):
        assert esperado in texto, f"«La lectura» no dice «{esperado}»"


def test_f072_r33_la_columna_y_el_tipo_efectivo():
    texto = _normal(_de_f072("### La columna `tipo_reclamacion` y el tipo efectivo"))

    for esperado in (
        "17_tipo_reclamacion.sql",
        COLUMNA,
        "ADD COLUMN IF NOT EXISTS",
        "postventa.bandeja_incidencias",
        "postventa.revisiones_bandeja",
        "columna nueva",
        "lo heredado no se migra en la base",
        "tipo efectivo",
        f"si es nulo (las filas anteriores a F-072), {TIPO_RECLAMACION_POR_DEFECTO}",
        "tipo_efectivo",
        "listado heredado",
    ):
        assert esperado in texto, f"«La columna» no dice «{esperado}»"


def test_f072_r33_plantilla_e_importacion():
    texto = _normal(_de_f072("### Plantilla e importación"))

    for esperado in (
        "<res> (<cod>)",
        "solo admite el blanco",
        "versión 2",
        "casar_con_lista",
        "código",
        f"en blanco, guarda {TIPO_RECLAMACION_POR_DEFECTO}",
        "Primer listado",
        "Excel de errores",
    ):
        assert _dice(texto, esperado), f"«Plantilla e importación» no dice «{esperado}»"


def test_f072_r33_el_contrato_de_listado_no_cambia_de_forma():
    texto = _normal(_de_f072("### La revisión: el contrato de `listado`"))

    for esperado in (
        "La forma del contrato no cambia",
        "la clave sigue siendo listado",
        "catalogo.listados",
        "{codigo, etiqueta}",
        "valores.listado",
        "importados.listado",
        "nunca null",
        "GET /api/bandeja",
        "POST /api/revision/acciones",
        f"con null, se guarda {TIPO_RECLAMACION_POR_DEFECTO}",
        MotivoNoAprobable.TIPO_FUERA_DE_SIGRID.value,
        "sin_cambios",
        "conserva su huella",
    ):
        assert esperado in texto, f"«La revisión» no dice «{esperado}»"


def test_f072_r33_el_volcado_manda_el_tipo_efectivo_y_no_relee():
    texto = _normal(_de_f072("### El volcado"))

    for esperado in ("tipo efectivo", "parte_de", "TIPO_RECLAMACION", "no lee auxtrcp", "tipo_no_valido"):
        assert esperado in texto, f"«El volcado» no dice «{esperado}»"


def test_f072_r33_donde_vive_nombra_piezas_que_existen():
    texto = _de_f072("### Dónde vive cada pieza")

    for ruta in (
        "domain/models/plantilla_incidencias.py",
        "domain/ports/tipos_reclamacion.py",
        "infrastructure/sigrid/tipos_reclamacion.py",
        "infrastructure/sigrid/fabrica.py",
        "application/pipelines/tipos_reclamacion.py",
    ):
        assert ruta in texto, ruta
        assert (SERVICIO / ruta).is_file(), ruta
    assert "Ninguna variable de entorno nueva" in _normal(texto)


def test_f072_r33_lo_que_no_hace():
    texto = _normal(_de_f072("### Lo que no hace"))

    for esperado in ("No escribe en Sigrid", "No toca el front", "F-040", "No traduce el listado heredado"):
        assert esperado in texto, f"«Lo que no hace» no dice «{esperado}»"


# --------------------------------------------------------------------------
# R33 · ARCHITECTURE.md: lo que F-072 deja de hacer verdad en F-071 y F-059
# --------------------------------------------------------------------------


def test_f072_r33_la_plantilla_de_f071_lleva_la_enmienda():
    entrada = _seccion(_leer(ARQUITECTURA), TITULO_DE_LA_ENTRADA)
    texto = _normal(_seccion(entrada, "### La plantilla"))

    assert "Enmienda del 2026-11-17 (F-072)" in texto
    for esperado in ("el listado también sale de Sigrid", "solo la urgencia sigue en el YAML"):
        assert esperado in texto, f"«La plantilla» no dice «{esperado}»"


def test_f072_r33_el_parte_de_f059_ya_no_dice_solo_tipo_0002_siempre():
    """«tipo 0002 siempre» de F-059 se queda como historia, con lo de F-072 al lado."""
    texto = _normal(_seccion(_seccion(_leer(ARQUITECTURA), TITULO_DEL_VOLCADO), "### El parte que se manda"))

    assert "con F-059, tipo 0002 siempre" in texto
    assert "desde F-072, el tipo efectivo" in texto
    assert "el listado de la bandeja no lo decide)" not in texto


def test_f072_r33_lo_que_hereda_f040_nombra_el_tipo_efectivo():
    texto = _normal(_seccion(_leer(ARQUITECTURA), "### Lo que hereda F-040"))

    assert "el tipo 0002 (desde F-072, el tipo efectivo de cada incidencia)" in texto


def test_f072_r33_la_importacion_y_la_revision_nombran_la_lectura():
    entrada = _seccion(_leer(ARQUITECTURA), TITULO_DE_LA_ENTRADA)
    importacion = _normal(_seccion(entrada, "### La importación, y el Excel de errores"))
    no_hace = _normal(_seccion(_leer(ARQUITECTURA), "### Lo que no hace la revisión"))

    assert "desde F-072, los tipos de reclamación" in importacion
    assert "desde F-072, una cuarta por petición" in no_hace


# --------------------------------------------------------------------------
# R33 · INTEGRACION.md
# --------------------------------------------------------------------------


def test_f072_r33_la_fila_de_sigrid_api_de_la_seccion_uno_nombra_f072():
    uno = _integracion("## 1 · Qué consumimos hoy")
    sigrid = _normal(_fila(uno, "| `sigrid-api` |"))
    base = _normal(_fila(uno, "| PostgreSQL `psql-albaranes-rs9k2` |"))

    for esperado in ("Desde F-072", "quinta lectura", "dbo.auxtrcp", "tipo efectivo"):
        assert esperado in sigrid, f"la fila de sigrid-api no dice «{esperado}»"
    assert "F-072" in sigrid.rsplit("|", 2)[1]
    assert COLUMNA in base and "F-072" in base.rsplit("|", 2)[1]


def test_f072_r33_la_seccion_uno_dice_la_lectura():
    seccion = _integracion(TITULO_DE_LA_LECTURA)
    texto = _normal(seccion)

    assert SQL_TIPOS_RECLAMACION in seccion  # el bloque de código, tal cual
    for esperado in (
        "POST /api/sql/read",
        "ninguna escritura",
        "Una vez por petición",
        "GET /api/plantilla",
        "POST /api/importaciones",
        "GET /api/revision",
        "POST /api/revision/acciones",
        "no la hacen",
        "catalogo_sin_verificar",
        "CatalogoNoDisponible",
        LINEA_DE_LOG,
        "nunca un res",
        "consultas_tipos_reclamacion.py",
        "no pide ningún cambio",
        SPEC,
    ):
        assert esperado in texto, f"§1 «Con F-072» no dice «{esperado}»"


def test_f072_r33_la_seccion_uno_de_f071_lleva_la_enmienda():
    texto = _normal(_integracion(TITULO_DE_F071))

    assert "Enmienda del 2026-11-17 (F-072)" in texto
    assert "el listado también sale de Sigrid" in texto


def test_f072_r33_la_seccion_dos_dice_la_columna():
    texto = _normal(_integracion(TITULO_DE_LA_COLUMNA))

    for esperado in (
        "17_tipo_reclamacion.sql",
        "ADD COLUMN IF NOT EXISTS",
        "postventa.bandeja_incidencias",
        "postventa.revisiones_bandeja",
        "primer ALTER TABLE",
        "dueño",
        "Nada a nivel de servidor",
        "código",
        "nunca su nombre",
        f"tipo efectivo es {TIPO_RECLAMACION_POR_DEFECTO}",
        "lo heredado no se migra en la base",
        "listado se queda",
        "F-048",
    ):
        assert esperado in texto, f"§2 «Con F-072» no dice «{esperado}»"


def test_f072_r33_tres_bis_dice_el_tipo_del_parte():
    texto = _normal(_integracion(TITULO_DEL_PARTE))

    for esperado in ("Con F-059, tipo 0002 siempre", "Desde F-072, el tipo efectivo", "tipo_no_valido"):
        assert esperado in texto, f"§3 bis no dice «{esperado}»"


def test_f072_r33_la_seccion_cuatro_dice_que_no_hay_variables():
    texto = _normal(_integracion("### Las de F-072: ninguna"))

    assert "F-072 no añade ninguna variable de entorno" in texto
    assert "TIPO_RECLAMACION_POR_DEFECTO" in texto
    assert "F-072" in _normal(_integracion("### Las de F-036: ninguna"))


def test_f072_r33_la_seccion_seis_dice_que_se_rompe():
    seis = _integracion("## 6 · Qué se rompe si alguien toca algo")
    caida = _normal(_fila(seis, "| La pasarela `sigrid-api` cae o no responde, o la lectura de `dbo.auxtrcp`"))
    baja = _normal(_fila(seis, "| Alguien da de baja en Sigrid un tipo de reclamación"))

    assert "503" in caida and "catalogo_sin_verificar" in caida
    assert "tipo_fuera_de_sigrid" in baja and "tipo_no_valido" in baja


@pytest.mark.parametrize(
    "principio,esperados",
    [
        ("| `GET /api/plantilla` |", ("Desde F-072", "tipos de reclamación", "<res> (<cod>)")),
        ("| `POST /api/importaciones` |", ("Desde F-072", COLUMNA, "0002 en blanco")),
        ("| `GET /api/bandeja` |", ("Desde F-072", "tipo efectivo", "nunca null")),
        (
            "| `GET /api/revision` |",
            ("Desde F-072", "sin cambiar la forma", "catalogo.listados", "{codigo, etiqueta}",
             "valores.listado", "importados.listado", "nunca null", "tipo_fuera_de_sigrid"),
        ),
        (
            "| `POST /api/revision/acciones` |",
            ("Desde F-072", "código de auxtrcp", "null, que guarda 0002", "valores_no_validos",
             "incidencia_no_aprobable con tipo_fuera_de_sigrid"),
        ),
        ("| `POST /api/volcado/ensayo` |", ("Desde F-072", "tipo efectivo")),
    ],
)
def test_f072_r33_las_filas_de_la_seccion_ocho_dicen_el_contrato(principio, esperados):
    fila = _ocho(principio)

    for esperado in esperados:
        assert esperado in fila, f"la fila «{principio}» no dice «{esperado}»"


def test_f072_r33_la_seccion_ocho_dice_que_no_esta_desplegada_y_la_nueve_donde_esta():
    no_desplegado = _normal(
        _fila(_integracion("### Qué NO está desplegado, y hay que decirlo antes de enseñarlo"),
              "| El tipo de reclamación de Sigrid | F-072 |")
    )
    nueve = _integracion("## 9 · Dónde está cada cosa")

    assert "sin desplegar" in no_desplegado
    assert SPEC in nueve
    for ruta in (
        "infrastructure/sigrid/tipos_reclamacion.py",
        "infrastructure/sigrid/consultas_tipos_reclamacion.py",
        "application/pipelines/tipos_reclamacion.py",
        "infrastructure/persistencia/sql/17_tipo_reclamacion.sql",
    ):
        assert f"services/postventa-api/{ruta}" in nueve, ruta
        assert (SERVICIO / ruta).is_file(), ruta


# --------------------------------------------------------------------------
# Lo nuevo no lleva valores
# --------------------------------------------------------------------------


#: Las claves de `_textos_nuevos`, fijas: leer los documentos al recoger los
#: tests tumbaría la recogida entera si faltara una sección.
DONDE = (
    "ARCHITECTURE «El tipo de reclamación»",
    "INTEGRACION §1 Con F-072",
    "INTEGRACION §2 Con F-072",
    "INTEGRACION §4 Las de F-072",
)


def test_f072_t21_las_claves_del_barrido_son_las_de_los_textos_nuevos():
    assert tuple(_textos_nuevos()) == DONDE


@pytest.mark.parametrize("donde", DONDE)
def test_f072_r33_lo_nuevo_no_lleva_valores_ni_correos(donde):
    texto = _textos_nuevos()[donde]

    assert hallazgos(texto) == {}
    assert CORREO.search(texto) is None, f"{donde} lleva un correo escrito"
