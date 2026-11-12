# services/postventa-api/tests/test_f065_documentacion.py
"""La documentación que F-065 deja al día (T10; R30, O-A4b-6).

Al modo de `test_f060_documentacion.py`. F-065 lee de Sigrid **todas** las
reclamaciones de la obra, con datos personales, y las cruza con la bandeja en
`GET /api/revision/sigrid`; y hace que el ensayo de F-059 vuelva a mirar Sigrid
antes de mandar nada (la guarda). Quien administre `sigrid-api`, quien diseñe
F-064 o F-040 y quien audite los datos personales tienen que poder saberlo sin
abrir el código.

Lo que fija:

- **R30** · `docs/INTEGRACION.md`: la cabecera; §1 (la cuarta lectura y la
  guarda); §4 (ninguna variable); §6 (qué se rompe); §7 (los datos personales:
  que los hay, dónde se enseñan y dónde no van); §8 (la ruta, y el ensayo con
  su guarda); §9 (dónde vive cada pieza).
- **R30** · `docs/ARCHITECTURE.md`: la sección nueva, la de F-059 y la fila de
  `sigrid-api`.
- **R30** · `azure-apps/`: `postventa_incidencias.md` lleva las mismas
  secciones, **idénticas**, y la fila de consumidores de `sigrid_api.md` gana
  la lectura. Otro repositorio: se salta si no está en esta máquina, como en
  `test_f051_documentacion.py`.
- **O-A4b-6**: la guarda, los tres códigos de error, los dos motivos y la regla
  de la emparejada (solo se enlaza en `PTE`, `SAT`, `TER` o `CER`; en `NPR`,
  estado desconocido o vacío, `choca`).
- Que nada de lo nuevo lleva valores, correos ni códigos `RS` reales.

Los controles **leen el código** cuando pueden: la ruta registrada, los motivos,
los veredictos, los códigos de error y los campos de la ficha. Sin red, sin
base, sin IA.

## La cuenta de §8

La tabla de endpoints de §8 sigue en **veinticuatro** a propósito: añadirle una
fila obliga a cambiar la cuenta, que fijan por su literal seis ficheros de
documentación de otras features, y `design.md` §9.2 y §15.6 no los declaran
(`test_f065_alcance_cerrado.py` lo impide). La ruta se declara en un recuadro
tras la cuenta, y ese recuadro dice que son veinticinco; lo fija
`test_f065_r30_la_seccion_ocho_declara_la_ruta_fuera_de_la_cuenta`. La decisión
consta en `progress/impl_F-065.md`, «Bloque A5».
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from domain.models.sigrid_bandeja import Veredicto, cruzar
from domain.models.volcado import MotivoExclusion
from infrastructure.sigrid.consultas_reclamaciones_obra import SQL_RECLAMACIONES_DE_LAS_UNIDADES

from tests.test_f005_integracion_sin_secretos import hallazgos

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent
SERVICIO = RAIZ / "services" / "postventa-api"

INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
FUNCTION_APP = SERVICIO / "function_app.py"
CONSULTAS = SERVICIO / "infrastructure" / "sigrid" / "consultas_reclamaciones_obra.py"
BORDE_DE_LA_RUTA = SERVICIO / "interface_adapters" / "api" / "sigrid_bandeja.py"

#: El repositorio hermano; los dos clones de este proyecto cuelgan del mismo sitio.
AZURE_APPS = RAIZ.parent / "azure-apps"
COPIA = AZURE_APPS / "postventa_incidencias.md"
PASARELA = AZURE_APPS / "sigrid_api.md"

SPEC = "specs/F-065-revision-sigrid-backend/"
RUTA = "GET /api/revision/sigrid"

TITULO_DE_LA_SECCION = "## Las reclamaciones de Sigrid en la revisión (F-065)"
TITULO_DE_LA_LECTURA = "### Con F-065 · la cuarta lectura: las reclamaciones de la obra"
TITULO_DE_LA_GUARDA = "### Con F-065 · la guarda del ensayo"
TITULO_DE_LAS_VARIABLES = "### Las de F-065: ninguna"

#: Los tres códigos nuevos del ensayo (R46), leídos abajo de `function_app.py`.
CODIGOS_NUEVOS_DEL_ENSAYO = ("sigrid_no_disponible", "reclamaciones_sin_verificar", "obra_ambigua")

#: Los dos motivos de exclusión nuevos (R45).
MOTIVOS_NUEVOS = (MotivoExclusion.DUPLICADA_EN_SIGRID, MotivoExclusion.CONFLICTO_SIN_CONFIRMAR)

#: Los módulos de F-065 que §9 de `INTEGRACION.md` tiene que localizar.
MODULOS_DE_F065 = (
    "domain/models/sigrid_bandeja.py",
    "domain/ports/reclamaciones_obra.py",
    "application/pipelines/sigrid_bandeja.py",
    "application/pipelines/guarda_sigrid.py",
    "infrastructure/sigrid/reclamaciones_obra.py",
    "infrastructure/sigrid/consultas_reclamaciones_obra.py",
    "interface_adapters/api/sigrid_bandeja.py",
)

#: Un correo escrito, de cualquier dominio: los documentos no llevan ninguno.
CORREO = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")

#: Un código de reclamación real: en los documentos, solo su forma.
CODIGO_RS = re.compile(r"\bRS\d{2}\.\d{2}/\d{4}\b")


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


def _fila(texto: str, principio: str) -> str:
    """La fila de una tabla de Markdown que empieza por `principio`."""
    filas = [linea for linea in texto.splitlines() if linea.startswith(principio)]
    assert len(filas) == 1, f"se esperaba una fila que empiece por «{principio}»: {len(filas)}"
    return filas[0]


def _integracion(titulo: str) -> str:
    return _seccion(_leer(INTEGRACION), titulo)


def _arquitectura() -> str:
    return _seccion(_leer(ARQUITECTURA), TITULO_DE_LA_SECCION)


def _campos_de_la_ficha() -> tuple[str, ...]:
    """`CAMPOS_DE_LA_FICHA` del borde, leído del código."""
    codigo = _leer(BORDE_DE_LA_RUTA)
    bloque = re.search(r"CAMPOS_DE_LA_FICHA\b[^=]*=\s*\((.*?)\n\)", codigo, re.DOTALL)
    assert bloque, "no se encuentra CAMPOS_DE_LA_FICHA"
    return tuple(re.findall(r'"([a-z_0-9]+)"', bloque.group(1)))


# --------------------------------------------------------------------------
# Los controles leen el código: que no lean nada vacío
# --------------------------------------------------------------------------


def test_f065_t10_los_controles_leen_algo_del_codigo():
    """Un control que no lee nada da verde para siempre: se fija lo que leen."""
    codigo = _leer(FUNCTION_APP)
    assert re.search(r'route="revision/sigrid",\s*methods=\["GET"\]', codigo)
    for texto in CODIGOS_NUEVOS_DEL_ENSAYO:
        assert f'"{texto}"' in codigo, texto
    assert [v.value for v in Veredicto] == ["va", "se_enlaza", "ya_existe", "choca"]
    assert [m.value for m in MOTIVOS_NUEVOS] == ["duplicada_en_sigrid", "conflicto_sin_confirmar"]
    assert len(_campos_de_la_ficha()) >= 10
    for modulo in MODULOS_DE_F065:
        assert (SERVICIO / modulo).is_file(), modulo
    assert "dbo.conest" in _leer(CONSULTAS)


@pytest.mark.parametrize(
    "texto", ("Escríbele a alguien@ejemplo.invalid si falla.", "persona.apellido@ejemplo.invalid")
)
def test_f065_t10_el_control_de_correos_caza(texto):
    assert CORREO.search(texto)


def test_f065_t10_el_control_de_codigos_caza():
    assert CODIGO_RS.search("el parte RS26.10/0074 de la obra")
    assert not CODIGO_RS.search("con la forma RS<aa>.<mm>/<4 cifras>")


# --------------------------------------------------------------------------
# R30 · INTEGRACION.md: la cabecera y §1
# --------------------------------------------------------------------------


def test_f065_r30_la_cabecera_dice_que_f065_lo_toco():
    cabecera = _normal(_leer(INTEGRACION).split("## 1 ·")[0])

    assert "Fecha: 2026-10-31." in cabecera
    assert "Última feature que lo tocó: F-065" in cabecera
    for texto in (RUTA, "guarda del ensayo", "Antes, F-038"):
        assert texto in cabecera, f"la cabecera no dice «{texto}»"


def test_f065_a7_la_cabecera_dice_que_f065_esta_desplegada():
    """Cierre del Bloque A7 (2026-10-31): desplegada desde `dev` `ed590bd` y
    verificada en solo lectura (T-A11 a T-A17); T-A18, el ensayo, pendiente.
    F-038 (front) se publicó el 2026-10-21 y se cerró el 2026-11-11 (merge
    `a7400a1`): la cabecera lo dice en pasado y no vuelve a la frase de antes."""
    cabecera = _normal(_leer(INTEGRACION).split("## 1 ·")[0])

    for texto in ("desplegada el 2026-10-31 desde dev ed590bd", "T-A11 a T-A17", "T-A18 pendiente"):
        assert texto in cabecera, f"la cabecera no dice «{texto}»"
    assert "F-065" in cabecera and "pendiente de publicar" not in cabecera
    assert "publicada el 2026-10-21, verificada en producción el 2026-11-09" in cabecera
    assert "implementada en su rama; se publica con su T6" not in cabecera


def test_f065_r30_la_fila_de_sigrid_api_de_la_seccion_uno_gana_la_lectura():
    uno = _integracion("## 1 · Qué consumimos hoy")
    fila = _normal(_fila(uno, "| `sigrid-api` |"))

    for texto in ("Desde F-065", "cuarta lectura", "reclamaciones de la obra", "guarda del ensayo"):
        assert texto in fila, f"la fila no dice «{texto}»"


def test_f065_r30_la_cuarta_lectura_que_lee_y_cuando():
    seccion = _normal(_integracion(TITULO_DE_LA_LECTURA))

    for texto in (
        RUTA,
        "POST /api/sql/read",
        "ninguna escritura",
        "de cualquier estado y de cualquier fecha",
        "SIGRID_TIP_RECLAMACION",
        "por su código contra dbo.conest",
        "RCPCLI",
        "PVI-",
        "una vez por petición",
        "sin caché",
        "bandeja_demasiado_grande",
        "sin leer Sigrid",
    ):
        assert texto in seccion, f"§1 no dice «{texto}»"


def test_f065_r30_la_cuarta_lectura_el_techo_las_puertas_y_los_errores():
    seccion = _normal(_integracion(TITULO_DE_LA_LECTURA))

    for texto in (
        "max_rows a 500.000",
        "truncated",
        "reclamaciones_sin_verificar",
        "sin calcular ningún conflicto",
        "obra_ambigua",
        "503",
        "ENTORNO en dev o pro",
        "no mira ninguna ventana de escritura",
        "MAX_ALLOWED_ROWS",
    ):
        assert texto in seccion, f"§1 no dice «{texto}»"


def test_f065_r30_la_cuarta_lectura_dice_que_hay_datos_personales():
    seccion = _normal(_integracion(TITULO_DE_LA_LECTURA))

    for texto in (
        "Hay datos personales",
        "propietario",
        "persona que reclama",
        "persona de contacto",
        "teléfonos",
        "correo",
        "Cache-Control: no-store",
        "ni en nuestra base",
        "ni en ningún log",
        "ni en el repositorio",
        "per.dni",
        "per.esiglog",
        "§7",
    ):
        assert texto in seccion, f"§1 no dice «{texto}»"


@pytest.mark.parametrize("titulo", (TITULO_DE_LA_LECTURA, TITULO_DE_LA_GUARDA))
def test_f065_r30_integracion_lleva_a_la_spec(titulo):
    assert SPEC in _integracion(titulo)


# --------------------------------------------------------------------------
# O-A4b-6 · La guarda del ensayo
# --------------------------------------------------------------------------


def _textos_de_la_guarda() -> tuple[tuple[str, str], ...]:
    """Las secciones que tienen que recoger la guarda, con su nombre."""
    return (
        ("integracion", _normal(_integracion(TITULO_DE_LA_GUARDA))),
        ("arquitectura", _normal(_seccion(_leer(ARQUITECTURA), "## Volcado a Sigrid (F-059)"))),
    )


@pytest.mark.parametrize("indice", (0, 1), ids=("integracion", "arquitectura"))
def test_f065_o6_la_guarda_que_lee_y_cuando(indice):
    _, seccion = _textos_de_la_guarda()[indice]

    for texto in (
        "lee Sigrid una vez más",
        "solo sql/read",
        "por unidades",
        "sin la ficha",
        "después de la selección",
        "antes del login",
        "conflictos_confirmados",
    ):
        assert texto in seccion, f"la guarda no dice «{texto}»"


@pytest.mark.parametrize("indice", (0, 1), ids=("integracion", "arquitectura"))
def test_f065_o6_los_dos_motivos_y_los_tres_codigos(indice):
    _, seccion = _textos_de_la_guarda()[indice]

    for motivo in MOTIVOS_NUEVOS:
        assert motivo.value in seccion, f"falta el motivo «{motivo.value}»"
    for codigo in CODIGOS_NUEVOS_DEL_ENSAYO:
        assert codigo in seccion, f"falta el código «{codigo}»"
    assert "Sigrid caída = no se ensaya" in seccion
    assert "sin interruptor" in seccion


@pytest.mark.parametrize("indice", (0, 1), ids=("integracion", "arquitectura"))
def test_f065_o6_la_regla_de_la_emparejada(indice):
    _, seccion = _textos_de_la_guarda()[indice]

    for texto in (
        "solo se enlaza en PTE, SAT, TER o CER",
        "en NPR, con un estado desconocido o vacío da choca",
        "confirmación explícita",
    ):
        assert texto in seccion, f"la regla no dice «{texto}»"


@pytest.mark.parametrize("indice", (0, 1), ids=("integracion", "arquitectura"))
def test_f065_c2_la_excepcion_de_r49(indice):
    """La función es la misma y la lectura no: F-040 no puede darlas por iguales."""
    _, seccion = _textos_de_la_guarda()[indice]

    for texto in (
        "La función es la misma y la lectura no",
        "una referencia PVI- en otra unidad",
        "el bloque volcado de la ruta y la guarda pueden diferir",
        "referencia_en_conflicto",
    ):
        assert texto in seccion, f"la excepción no dice «{texto}»"


def test_f065_c2_el_docstring_de_cruzar_dice_la_excepcion():
    doc = " ".join((cruzar.__doc__ or "").split())

    assert "así que es el mismo" not in doc
    for texto in ("salvo una referencia `PVI-` en otra unidad", "R49", "referencia_en_conflicto"):
        assert texto in doc, f"el docstring no dice «{texto}»"


def test_f065_c3_la_guarda_lee_textos_y_el_codigo_lo_confirma():
    """Lo que el documento dice que lee la guarda es lo que pide su consulta."""
    for columna in ("c.res", "r.resubi"):
        assert columna in SQL_RECLAMACIONES_DE_LAS_UNIDADES
    assert "dbo.per" not in SQL_RECLAMACIONES_DE_LAS_UNIDADES
    assert "r.tex" not in SQL_RECLAMACIONES_DE_LAS_UNIDADES

    siete = _normal(_integracion("## 7 · Datos personales"))
    assert "La guarda del ensayo no lee ninguno" not in siete
    for seccion in (siete, _normal(_integracion(TITULO_DE_LA_GUARDA))):
        for texto in ("con.res", "rcp.resubi", "memoria de la petición"):
            assert texto in seccion, f"no dice «{texto}»"
    assert "sin datos personales" not in _integracion(TITULO_DE_LA_GUARDA)
    assert "sin datos personales" not in _seccion(_leer(ARQUITECTURA), "## Volcado a Sigrid (F-059)")
    assert "sin datos personales" not in _fila(_leer(ARQUITECTURA), "| `sigrid-api` |")


def test_f065_c5_el_codigo_de_cada_motivo():
    """`duplicada_en_sigrid`, su primer código; `conflicto_sin_confirmar`, el primero sin confirmar."""
    seccion = _normal(_integracion(TITULO_DE_LA_GUARDA))

    assert "con su primer código en sigrid_cod" not in seccion
    assert "en duplicada_en_sigrid, el primero de su veredicto" in seccion
    assert "en conflicto_sin_confirmar, el primero sin confirmar" in seccion


def test_f065_o6_cada_veredicto_se_nombra():
    seccion = _integracion(TITULO_DE_LA_GUARDA)
    for veredicto in Veredicto:
        assert f"`{veredicto.value}`" in seccion, veredicto.value


def test_f065_o6_lo_que_no_cambia_con_la_guarda():
    seccion = _normal(_integracion(TITULO_DE_LA_GUARDA))

    for texto in (
        "POST /api/volcado/volcar y GET /api/volcado no cambian",
        "La confirmación no se guarda",
        "F-065 guarda del ensayo",
        "ni un código de reclamación",
        "sigrid-api no cambia",
    ):
        assert texto in seccion, f"la guarda no dice «{texto}»"


# --------------------------------------------------------------------------
# R30 · INTEGRACION.md §4, §6, §7, §8 y §9
# --------------------------------------------------------------------------


def test_f065_r30_la_seccion_cuatro_dice_que_no_hay_variables_nuevas():
    variables = _normal(_integracion(TITULO_DE_LAS_VARIABLES))

    assert "F-065 no añade ninguna variable de entorno" in variables
    assert "SIGRID_TIP_RECLAMACION" in variables


def test_f065_r30_la_seccion_seis_dice_que_se_rompe():
    seis = _normal(_integracion("## 6 · Qué se rompe si alguien toca algo"))

    for texto in ("MAX_ALLOWED_ROWS", "(F-065)", "no se ensaya"):
        assert texto in seis, f"§6 no dice «{texto}»"


def test_f065_c4_bajar_el_tope_de_la_pasarela_da_503_en_todas_las_obras():
    """La pasarela **rechaza** un `max_rows` mayor que su tope: nunca es un 409.

    Que el 400 de la pasarela acaba en 503 lo fija contra el código
    `test_f065_r8_un_max_rows_rechazado_es_503_y_no_llega_al_techo`.
    """
    seis = _integracion("## 6 · Qué se rompe si alguien toca algo")
    fila = _normal(_fila(seis, "| Baja `MAX_ALLOWED_ROWS` de `sql/read`"))

    for texto in ("por debajo de 500.000", "todas las obras", "503", "sigrid_no_disponible", "rechaza"):
        assert texto in fila, f"la fila no dice «{texto}»"
    assert "409" not in fila
    assert "reclamaciones_sin_verificar" not in fila


def test_f065_c4_si_la_pasarela_cae_lo_que_sigue_y_lo_que_no():
    seis = _integracion("## 6 · Qué se rompe si alguien toca algo")
    fila = _normal(_fila(seis, "| La pasarela `sigrid-api` cae o no responde (**F-065**) |"))

    assert "la revisión de la base siguen" not in fila
    for texto in ("Siguen el panel, descartar, recuperar y el historial", "el listado de revisión, editar y aprobar"):
        assert texto in fila, f"la fila no dice «{texto}»"


def test_f065_r30_la_seccion_siete_dice_donde_se_ensenan_y_donde_no_van():
    siete = _normal(_integracion("## 7 · Datos personales"))

    for texto in (
        "Enmienda del 2026-10-30 (F-065)",
        "Dónde se enseñan",
        "Dónde no van",
        "Cache-Control: no-store",
        "per.dni",
        "per.esigpas",
        "per.clamai",
        "No se guardan",
        "La guarda del ensayo no lee la ficha",
    ):
        assert texto in siete, f"§7 no dice «{texto}»"


def test_f065_r30_la_seccion_ocho_declara_la_ruta_fuera_de_la_cuenta():
    """La tabla sigue en veinticuatro; el recuadro dice lo que falta (cabecera)."""
    endpoints = _normal(_integracion("### Los endpoints, y qué hace cada uno"))

    assert "Los veinticuatro quedan en nivel" in endpoints
    for texto in (
        f"{RUTA} (F-065)",
        "son veinticinco",
        "mismo nivel anónimo",
        "la tabla y la cuenta de arriba aún no la recogen",
        "Solo lee",
        "400",
        "409",
        "503",
    ):
        assert texto in endpoints, f"§8 no dice «{texto}»"


def test_f065_r30_la_fila_del_ensayo_dice_la_guarda():
    fila = _normal(_fila(_integracion("### Los endpoints, y qué hace cada uno"), "| `POST /api/volcado/ensayo` |"))

    for texto in ("Desde F-065", "conflictos_confirmados", "sql/read", "sigrid"):
        assert texto in fila, f"la fila del ensayo no dice «{texto}»"


def test_f065_r30_la_seccion_ocho_dice_lo_que_falta_por_publicar():
    """Desde el Bloque A7 (2026-10-31): desplegada y verificada en solo
    lectura; lo que falta es el ensayo T-A18 y las páginas de F-064 y F-040."""
    ausencias = _integracion("### Qué NO está desplegado, y hay que decirlo antes de enseñarlo")
    fila = _normal(_fila(ausencias, "| Las reclamaciones de Sigrid en la revisión |"))

    for texto in ("F-065", "Desplegada el 2026-10-31", "dev ed590bd", "T-A11 a T-A17", "T-A18", "F-064", "F-040"):
        assert texto in fila, f"la fila de F-065 no dice «{texto}»"
    assert "Pendiente de publicar" not in fila
    assert "existen en su rama" not in fila


def test_f065_a7_la_seccion_de_arquitectura_dice_que_esta_desplegada():
    seccion = _normal(_arquitectura())

    assert "Añadida el 2026-10-30 por F-065; desplegada el 2026-10-31 desde dev ed590bd" in seccion
    assert "pendiente de publicar" not in seccion


def test_f065_a7_la_cuarta_lectura_dice_que_esta_desplegada():
    lectura = _normal(_integracion(TITULO_DE_LA_LECTURA))

    assert "desplegada el 2026-10-31 desde dev ed590bd" in lectura
    assert "pendiente de publicar" not in lectura


@pytest.mark.parametrize("modulo", MODULOS_DE_F065)
def test_f065_r30_la_seccion_nueve_localiza_cada_pieza(modulo):
    assert modulo in _integracion("## 9 · Dónde está cada cosa")


def test_f065_r30_la_seccion_nueve_lleva_a_la_spec_y_al_script():
    nueve = _integracion("## 9 · Dónde está cada cosa")
    assert SPEC in nueve
    assert "infra/29_reclamaciones_obra_sigrid.ps1" in nueve


# --------------------------------------------------------------------------
# R30 · ARCHITECTURE.md
# --------------------------------------------------------------------------


def test_f065_r30_la_seccion_va_tras_el_volcado_y_antes_del_acceso_a_datos():
    texto = _leer(ARQUITECTURA)
    assert TITULO_DE_LA_SECCION in texto, "no está la sección de F-065"

    assert (
        texto.index("## Volcado a Sigrid (F-059)")
        < texto.index(TITULO_DE_LA_SECCION)
        < texto.index("## Acceso a datos y sistemas externos")
    )


def test_f065_r30_la_seccion_la_ruta_y_el_cruce():
    seccion = _normal(_arquitectura())

    for texto in (
        RUTA,
        "dominio puro",
        "una sola función",
        "cruzar",
        "PVI-",
        "misma_unidad_oficio_ubicacion",
        "misma_unidad_descripcion_parecida",
        "no bloquea",
        "F-064",
        "F-040",
        SPEC,
        "docs/INTEGRACION.md",
    ):
        assert texto in seccion, f"la sección no dice «{texto}»"


def test_f065_r30_la_seccion_los_datos_personales():
    seccion = _normal(_arquitectura())

    for texto in (
        "Hay datos personales",
        "Cache-Control: no-store",
        "F-065 sigrid de la bandeja",
        "No se guardan",
        "ni en ningún log",
    ):
        assert texto in seccion, f"la sección no dice «{texto}»"


def test_f065_r30_la_fila_de_sigrid_api_de_arquitectura_gana_la_lectura():
    fila = _normal(_fila(_leer(ARQUITECTURA), "| `sigrid-api` |"))

    for texto in ("Desde F-065", "cuarta lectura", "500.000", "guarda del ensayo"):
        assert texto in fila, f"la fila no dice «{texto}»"


# --------------------------------------------------------------------------
# R30 · azure-apps (otro repositorio)
# --------------------------------------------------------------------------

sin_azure_apps = pytest.mark.skipif(
    not COPIA.exists() or not PASARELA.exists(), reason="azure-apps no esta en esta maquina"
)


@sin_azure_apps
@pytest.mark.parametrize(
    "titulo", (TITULO_DE_LA_LECTURA, TITULO_DE_LA_GUARDA, TITULO_DE_LAS_VARIABLES)
)
def test_f065_r30_la_copia_de_azure_apps_lleva_las_secciones_identicas(titulo):
    """`postventa_incidencias.md` es copia de `INTEGRACION.md`: sin divergir."""
    assert _seccion(_leer(COPIA), titulo) == _integracion(titulo)


@sin_azure_apps
@pytest.mark.parametrize(
    "principio",
    (
        "| Baja `MAX_ALLOWED_ROWS` de `sql/read`",
        "| La pasarela `sigrid-api` cae o no responde (**F-065**) |",
        "| El volcado a Sigrid |",
        "| Las reclamaciones de Sigrid en la revisión |",
    ),
)
def test_f065_c4_c6_las_filas_de_la_copia_son_las_de_integracion(principio):
    assert _fila(_leer(COPIA), principio) == _fila(_leer(INTEGRACION), principio)


@sin_azure_apps
def test_f065_c3_la_copia_y_la_fila_de_consumidores_dicen_que_lee_la_guarda():
    copia = _normal(_leer(COPIA).split("## 1 ·")[0])
    assert "sin datos personales" not in copia
    assert "sin la ficha" in copia

    consumidores = _seccion(_leer(PASARELA), "## 10. Consumidores de la API")
    fila = _normal(next(f for f in consumidores.splitlines() if "(F-065;" in f))
    assert "sin datos personales" not in fila
    for texto in ("sin la ficha", "con.res", "rcp.resubi"):
        assert texto in fila, f"la fila no dice «{texto}»"


@sin_azure_apps
def test_f065_la_fila_de_f059_en_consumidores_dice_que_ya_escribio():
    consumidores = _seccion(_leer(PASARELA), "## 10. Consumidores de la API")
    fila = _normal(next(f for f in consumidores.splitlines() if "(F-059 backend;" in f))

    assert "su primera escritura, pendiente" not in fila
    assert "2026-10-19" in fila


@sin_azure_apps
def test_f065_r30_la_copia_de_azure_apps_dice_lo_que_cambia():
    cabecera = _normal(_leer(COPIA).split("## 1 ·")[0])

    for texto in ("LO QUE CAMBIA EN ESTA REVISIÓN (2026-10-31)", "F-065", RUTA, "Fecha del documento: 2026-10-31"):
        assert texto in cabecera, f"la cabecera de la copia no dice «{texto}»"
    assert "desplegada el 2026-10-31 desde dev ed590bd" in cabecera
    assert "F-065 implementada y pendiente de publicar" not in cabecera
    # F-038 se cerró el 2026-11-11 (azure-apps `402b082`): la copia lo dice en pasado.
    assert "F-038 publicada el 2026-10-21, verificada en producción el 2026-11-09" in cabecera
    assert "F-038 mergeada y sin publicar todavía" not in cabecera


@sin_azure_apps
def test_f065_a7_la_fila_de_consumidores_ya_no_dice_pendiente():
    consumidores = _seccion(_leer(PASARELA), "## 10. Consumidores de la API")
    fila = _normal(next(f for f in consumidores.splitlines() if "(F-065;" in f))

    assert "pendiente de publicar" not in fila
    assert "desplegada el 2026-10-31" in fila


@sin_azure_apps
def test_f065_r30_la_copia_de_azure_apps_lleva_los_datos_personales_y_la_ruta():
    copia = _normal(_leer(COPIA))

    for texto in ("Enmienda del 2026-10-30 (F-065)", f"{RUTA} (F-065)", "Las reclamaciones de Sigrid en la revisión"):
        assert texto in copia, f"la copia no dice «{texto}»"


@sin_azure_apps
def test_f065_r30_la_fila_de_consumidores_de_sigrid_api_gana_la_lectura():
    consumidores = _seccion(_leer(PASARELA), "## 10. Consumidores de la API")
    filas = [f for f in consumidores.splitlines() if f.startswith("| **postventa-incidencias**")]
    fila = _normal(next(f for f in filas if "F-065" in f))

    for texto in ("sql/read", "500.000", "reclamaciones", "truncated", "datos personales", "guarda del ensayo"):
        assert texto in fila, f"la fila de consumidores no dice «{texto}»"


# --------------------------------------------------------------------------
# Sin valores, sin correos y sin códigos reales
# --------------------------------------------------------------------------


def _textos_nuevos() -> dict[str, str]:
    integracion = _leer(INTEGRACION)
    return {
        "lectura": _seccion(integracion, TITULO_DE_LA_LECTURA),
        "guarda": _seccion(integracion, TITULO_DE_LA_GUARDA),
        "variables": _seccion(integracion, TITULO_DE_LAS_VARIABLES),
        "arquitectura": _arquitectura(),
    }


@pytest.mark.parametrize("donde", ("lectura", "guarda", "variables", "arquitectura"))
def test_f065_r30_lo_nuevo_no_lleva_valores_ni_correos_ni_codigos(donde):
    texto = _textos_nuevos()[donde]

    assert hallazgos(texto) == {}
    assert CORREO.search(texto) is None, f"{donde} lleva un correo escrito"
    assert CODIGO_RS.search(texto) is None, f"{donde} lleva un código RS real"


def test_f065_r30_los_documentos_nombran_los_campos_que_se_sirven():
    """R33: la lista cerrada, por lo que es, en el documento que la describe."""
    assert _campos_de_la_ficha(), "CAMPOS_DE_LA_FICHA vacía"
    seccion = _normal(_integracion(TITULO_DE_LA_LECTURA))

    for texto in (
        "la descripción larga",
        "el motivo",
        "la urgencia",
        "la forma de comunicación",
        "la fecha prevista de nueva visita",
        "la solución",
        "la clase",
    ):
        assert texto in seccion, f"§1 no nombra «{texto}»"
