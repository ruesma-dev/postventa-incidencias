# services/postventa-api/tests/test_f060_documentacion.py
"""La documentación que F-060 deja al día (T20; R43).

Al modo de `test_f056_documentacion.py`. F-060 pone en el texto **exacto** de
Sigrid las ubicaciones de la bandeja que solo difieren en mayúsculas, con una
revisión `editar` **del sistema** (`sistema:normalizar_ubicacion`), a demanda
(`POST /api/revision/normalizar`) y tras cada importación que registra filas
(mejor esfuerzo); y deja una línea de tiempos por cada listado. Quien
administre el PostgreSQL compartido, quien diseñe F-038 o F-048 y quien audite
los datos personales tienen que poder saberlo sin abrir el código.

Lo que fija:

- **R43** · `docs/INTEGRACION.md`:
  - la cabecera: fecha y «Última feature que lo tocó: F-060»;
  - §1: la tercera lectura, ahora también tras importar;
  - §2: las revisiones del sistema en `revisiones_bandeja`, sin DDL, en un lote
    con `FOR UPDATE`, y que el ensayo abre la base pero no escribe ninguna fila
    (O-4 de la review del Bloque 3);
  - §4: ninguna variable de entorno nueva;
  - §7: la identidad del sistema, que no es un dato personal, y que **la marca
    es el correo** (`revisado_correo`), no el `oid` (O-2 de la review del
    Bloque 1);
  - §8: la ruta nueva en la tabla —leída de `function_app.py`—, su cuerpo, la
    normalización tras importar, la línea de tiempos, «Los veintiuno» y lo que
    falta por desplegar;
  - §9: dónde vive cada pieza.
- **R43** · `docs/ARCHITECTURE.md`: la sección «Normalizar las ubicaciones
  (F-060)» —la regla, la constancia, cuándo, el estado `editada` y la
  medición—, la enmienda del «No revisa» de F-036 y las dos filas de la tabla
  de sistemas.
- Que nada de lo nuevo lleva valores (el barrido de
  `test_f005_integracion_sin_secretos.py`) ni un correo escrito.

Los controles **leen el código** cuando pueden —el literal del sistema, la
ruta registrada, los tramos de la traza—. La copia de `azure-apps/` (T29) es
otro repositorio y la pone al día el líder: no se comprueba aquí. Sin red, sin
base, sin IA.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from domain.models.normalizacion import TEXTO_SISTEMA, Coincidencia

from tests.test_f005_integracion_sin_secretos import hallazgos

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent
SERVICIO = RAIZ / "services" / "postventa-api"

INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
FUNCTION_APP = SERVICIO / "function_app.py"
REVISION_HTTP = SERVICIO / "interface_adapters" / "api" / "revision.py"

SPEC = "specs/F-060-normalizar-ubicaciones/"
RUTA = "revision/normalizar"

TITULO_DE_LA_NORMALIZACION = "## Normalizar las ubicaciones (F-060)"
TITULO_DE_LA_LECTURA = "### Con F-060 · la tercera lectura, también tras importar"
TITULO_DE_LAS_REVISIONES = "### Con F-060 · las revisiones del sistema"
TITULO_DE_LAS_VARIABLES = "### Las de F-060: ninguna"

#: Los módulos nuevos de F-060 que §9 de `INTEGRACION.md` tiene que localizar.
MODULOS_DE_F060 = (
    "domain/models/normalizacion.py",
    "interface_adapters/api/normalizacion.py",
    "interface_adapters/api/tiempos.py",
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


def _fila(texto: str, principio: str) -> str:
    """La fila de una tabla de Markdown que empieza por `principio`."""
    filas = [linea for linea in texto.splitlines() if linea.startswith(principio)]
    assert len(filas) == 1, f"se esperaba una fila que empiece por «{principio}»: {len(filas)}"
    return filas[0]


def _integracion(titulo: str) -> str:
    return _seccion(_leer(INTEGRACION), titulo)


def _normalizacion() -> str:
    return _seccion(_leer(ARQUITECTURA), TITULO_DE_LA_NORMALIZACION)


def _tramos_de_la_traza() -> set[str]:
    """Los nombres de tramo que escribe `listar_revision`, leídos del código."""
    codigo = _leer(REVISION_HTTP)
    return set(re.findall(r'cronometro\.tramo\("([a-z_.]+)"\)', codigo)) | {
        f"{p}.listar" if p == "bandeja" else p
        for p in re.findall(r'cronometro\.medir\(\w+, "([a-z_]+)"\)', codigo)
    }


# --------------------------------------------------------------------------
# Los controles leen el código: que no lean nada vacío
# --------------------------------------------------------------------------


def test_f060_t20_los_controles_leen_algo_del_codigo():
    """Un control que no lee nada da verde para siempre: se fija lo que leen."""
    assert TEXTO_SISTEMA == "sistema:normalizar_ubicacion"
    assert [c.value for c in Coincidencia] == ["exacta", "normalizable", "ambigua", "sin_coincidencia"]
    assert re.search(rf'route="{re.escape(RUTA)}",\s*methods=\["POST"\]', _leer(FUNCTION_APP))
    assert {"construir.bandeja", "aplicacion", "serializar", "bandeja.listar"} <= _tramos_de_la_traza()
    for modulo in MODULOS_DE_F060:
        assert (SERVICIO / modulo).is_file(), modulo


@pytest.mark.parametrize(
    "texto", ("Escríbele a alguien@ejemplo.invalid si falla.", "persona.apellido@empresa.es")
)
def test_f060_t20_el_control_de_correos_caza(texto):
    assert CORREO.search(texto)
    assert not CORREO.search(TEXTO_SISTEMA)


# --------------------------------------------------------------------------
# R43 · INTEGRACION.md: la cabecera
# --------------------------------------------------------------------------


def test_f060_r43_la_cabecera_dice_que_f060_lo_toco_y_cuando():
    """Al cierre (2026-10-14, T36), la cabecera pasa a decir que F-060 está
    **desplegada** (T24, 2026-10-13) y verificada en el entorno (T26 y T27,
    2026-10-14), como hizo F-056 en el suyo.
    """
    cabecera = _normal(_leer(INTEGRACION).split("## 1 ·")[0])

    assert "Última feature que lo tocó: F-060" in cabecera
    assert "Fecha: 2026-10-14." in cabecera
    for texto in ("desplegada el 2026-10-13", "verificada en el entorno el 2026-10-14"):
        assert texto in cabecera, f"la cabecera no dice «{texto}»"
    assert "sin desplegar" not in cabecera
    # Lo que ya decía sigue: F-056 desplegada, F-053, F-036 y el origen.
    for texto in ("F-056", "desplegada el 2026-10-09", "F-053", "F-036", "F-005"):
        assert texto in cabecera, f"la cabecera ya no dice «{texto}»"


# --------------------------------------------------------------------------
# R43 · INTEGRACION.md §1, §2 y §4
# --------------------------------------------------------------------------


def test_f060_r43_la_seccion_uno_dice_que_la_importacion_lee_las_ubicaciones():
    uno = _integracion("## 1 · Qué consumimos hoy")
    lectura = _normal(_seccion(uno, TITULO_DE_LA_LECTURA))

    for texto in (
        "POST /api/sql/read",
        "tras cada importación",
        "registra filas",
        "una vez por ejecución",
        "ninguna lectura nueva",
        "POST /api/revision/normalizar",
    ):
        assert texto in lectura, f"§1 no dice «{texto}»"


def test_f060_r43_la_seccion_dos_dice_que_escribe_el_sistema_y_como():
    dos = _integracion("## 2 · La base de datos")
    revisiones = _normal(_seccion(dos, TITULO_DE_LAS_REVISIONES))

    for texto in (
        "postventa.revisiones_bandeja",
        "sin DDL",
        "ningún .sql",
        TEXTO_SISTEMA,
        "accion = editar",
        "Append-only",
        "SELECT … FOR UPDATE",
        "una transacción",
        "se salta",
        "conflictos",
        "postventa.bandeja_incidencias no se toca",
        "nunca un bloqueo consultivo",
        "abre la conexión",
        "no escribe ninguna fila",
        "tras cada importación",
        SPEC,
    ):
        assert texto in revisiones, f"§2 no dice «{texto}»"


def test_f060_r43_la_seccion_cuatro_dice_que_no_hay_variables_nuevas():
    variables = _normal(_integracion(TITULO_DE_LAS_VARIABLES))

    assert "F-060 no añade ninguna variable de entorno" in variables
    assert "ninguna ventana de escritura" in variables


# --------------------------------------------------------------------------
# R43 · INTEGRACION.md §7: la identidad del sistema
# --------------------------------------------------------------------------


def test_f060_r43_la_seccion_siete_dice_que_es_la_identidad_del_sistema():
    siete = _normal(_integracion("## 7 · Datos personales"))

    for texto in (
        "Enmienda del 2026-10-13 (F-060)",
        TEXTO_SISTEMA,
        "no es un dato personal",
        "no es un oid",
        "revisado_por",
        "revisado_correo",
    ):
        assert texto in siete, f"§7 no dice «{texto}»"


def test_f060_r43_la_seccion_siete_dice_que_la_marca_es_el_correo():
    """O-2 de la review del Bloque 1: la marca es el correo, no el `oid`."""
    siete = _normal(_integracion("## 7 · Datos personales"))

    for texto in (
        "La marca es el correo",
        "ninguna persona puede enviar ese correo",
        "el oid no sirve de marca",
        "F-038",
        "F-048",
    ):
        assert texto in siete, f"§7 no dice «{texto}»"


# --------------------------------------------------------------------------
# R43 · INTEGRACION.md §8: la ruta, la importación, la traza y la cuenta
# --------------------------------------------------------------------------


def test_f060_r43_la_tabla_de_la_seccion_ocho_declara_la_ruta():
    tabla = _integracion("### Los endpoints, y qué hace cada uno")
    fila = _normal(_fila(tabla, f"| `POST /api/{RUTA}` |"))

    for texto in (
        "F-060",
        "postventa.revisiones_bandeja",
        "append-only",
        "confirmado: true",
        "ensayo",
        "sin valor por omisión",
        "solo números",
        TEXTO_SISTEMA,
        "no escribe ninguna fila",
        "Nada en Sigrid",
    ):
        assert texto in fila, f"la fila de la ruta no dice «{texto}»"


def test_f060_r43_la_seccion_ocho_dice_la_importacion_la_traza_y_la_cuenta():
    ocho = _normal(_integracion("## 8 · Qué exponemos nosotros"))

    for texto in (
        "Desde F-060",
        '{"obra": "9901", "confirmado": true, "ensayo": true}',
        "Tras cada importación que registra filas",
        "mejor esfuerzo",
        "la respuesta de POST /api/importaciones no cambia",
        "F-060 tiempos del listado",
        "POST /api/revision/normalizar tampoco depende de ninguna ventana",
        "Los veintiuno quedan en nivel",
        "las mismas claves",
    ):
        assert texto in ocho, f"§8 no dice «{texto}»"
    for vieja in ("Los veinte quedan en nivel", "Los diecisiete quedan en nivel"):
        assert vieja not in ocho


def test_f060_r43_la_seccion_ocho_dice_que_f060_no_esta_desplegada():
    """§8 · «Qué NO está desplegado»: F-060, con su consecuencia visible.

    Al cierre (2026-10-14, T36), la fila pasa a decir que la normalización está
    **desplegada** y verificada (T26 y T27), y que lo que falta es la velocidad
    del listado: la medición M2 (T35) y que lo pendiente es **F-061**. El
    párrafo «Desde F-060» de §8 deja también de decir «sin desplegar».
    """
    ausencias = _integracion("### Qué NO está desplegado, y hay que decirlo antes de enseñarlo")
    fila = _normal(_fila(ausencias, "| Normalizar las ubicaciones |"))

    for texto in (
        "F-060",
        "Desplegada el 2026-10-13",
        "verificada en el entorno el 2026-10-14",
        "p50 5,00 s",
        "máximo 13,21 s",
        "F-061",
    ):
        assert texto in fila, f"la fila de F-060 no dice «{texto}»"
    assert "sin desplegar" not in fila

    ocho = _normal(_integracion("## 8 · Qué exponemos nosotros"))
    assert "Desde F-060 (2026-10-13; desplegada el 2026-10-13 y verificada en el entorno el 2026-10-14)" in ocho
    assert "Desde F-060 (2026-10-13; implementada en su rama y sin desplegar)" not in ocho


@pytest.mark.parametrize("modulo", MODULOS_DE_F060)
def test_f060_r43_la_seccion_nueve_localiza_cada_pieza(modulo):
    assert modulo in _integracion("## 9 · Dónde está cada cosa")


@pytest.mark.parametrize(
    "titulo", (TITULO_DE_LA_LECTURA, TITULO_DE_LAS_REVISIONES, "## 9 · Dónde está cada cosa")
)
def test_f060_r43_integracion_lleva_a_la_spec(titulo):
    assert SPEC in _integracion(titulo)


# --------------------------------------------------------------------------
# R43 · ARCHITECTURE.md
# --------------------------------------------------------------------------


def test_f060_r43_la_seccion_va_tras_la_revision_y_antes_del_acceso_a_datos():
    texto = _leer(ARQUITECTURA)
    assert TITULO_DE_LA_NORMALIZACION in texto, "no está la sección de F-060"

    assert (
        texto.index("## Revisión de la bandeja (F-056)")
        < texto.index(TITULO_DE_LA_NORMALIZACION)
        < texto.index("## Acceso a datos y sistemas externos")
    )


def test_f060_r43_la_regla():
    """R1–R5, D-3: la clave, el orden de la clasificación y lo que no coincide."""
    seccion = _normal(_normalizacion())

    for texto in (
        'unicodedata.normalize("NFC", texto).strip().casefold()',
        "el texto exacto de Sigrid",
        "salvo mayúsculas",
        "blancos interiores",
        "tildes",
        "puntuación",
        "el valor de la lista",
        "nunca una transformación",
    ):
        assert texto in seccion, f"la sección no dice «{texto}»"


@pytest.mark.parametrize("coincidencia", [c.value for c in Coincidencia])
def test_f060_r43_nombra_cada_clasificacion(coincidencia):
    assert coincidencia in _normalizacion()


def test_f060_r43_la_constancia_y_el_estado():
    """D-1, D-4, D-6, Q-1: la revisión del sistema, solo editables, `editada`."""
    seccion = _normal(_normalizacion())

    for texto in (
        "una revisión editar del sistema",
        TEXTO_SISTEMA,
        "La marca es el correo",
        "solo la ubicación cambiada",
        "sin DDL",
        "nueva y editada",
        "nunca una aprobada",
        "pasa de nueva a editada",
        "La comparación de F-056 sigue exacta",
    ):
        assert texto in seccion, f"la sección no dice «{texto}»"


def test_f060_r43_cuando_y_la_concurrencia():
    """D-2, D-7, D-8, R34: tras importar (mejor esfuerzo), a demanda con ensayo, el lote."""
    seccion = _normal(_normalizacion())

    for texto in (
        "Tras cada importación que registra filas",
        "mejor esfuerzo",
        "cualquier excepción",
        "por su tipo",
        "POST /api/revision/normalizar",
        "ensayo",
        "sin valor por omisión",
        "una transacción",
        "FOR UPDATE",
        "se salta",
        "idempotente",
    ):
        assert texto in seccion, f"la sección no dice «{texto}»"


def test_f060_r43_la_medicion():
    """R40–R42, D-9: la traza, sus tramos, lo que no lleva, y los nombres de la revisión."""
    seccion = _normal(_normalizacion())

    for texto in (
        "F-060 tiempos del listado",
        "proceso_nuevo",
        "calculo",
        "no cambia nada",
        "ni correo, ni oid, ni textos",
        "test_f056_r31",
        "§11.4",
    ):
        assert texto in seccion, f"la sección no dice «{texto}»"
    for tramo in sorted(_tramos_de_la_traza()):
        assert tramo in seccion, f"la sección no nombra el tramo «{tramo}»"


def test_f060_t36_la_seccion_dice_que_esta_desplegada_y_lo_que_mide():
    """Al cierre (2026-10-14, T36): desplegada y verificada, y la medición M2.

    Lo mismo que la cabecera y §8 de `INTEGRACION.md`: la línea de estado de la
    sección deja de decir «sin desplegar», y la medición dice el resultado tras
    la importación diferida del Bloque 7 (M-3) y que lo que falta es F-061.
    """
    seccion = _normal(_normalizacion())

    for texto in (
        "Añadida el 2026-10-13 por F-060; desplegada el 2026-10-13 y verificada en el entorno el 2026-10-14.",
        "importación diferida",
        "p50 5,00 s",
        "máximo 13,21 s",
        "F-061",
    ):
        assert texto in seccion, f"la sección no dice «{texto}»"
    assert "sin desplegar" not in seccion


def test_f060_r43_dice_lo_que_no_hace_y_lleva_a_la_spec():
    seccion = _normal(_normalizacion())

    for texto in (
        "Nada de F-060 escribe en Sigrid",
        "F-058",
        "F-038",
        SPEC,
        "docs/INTEGRACION.md",
    ):
        assert texto in seccion, f"la sección no dice «{texto}»"


def test_f060_r43_enmienda_el_no_revisa_de_f036():
    no_hacen = _normal(
        _seccion(
            _seccion(_leer(ARQUITECTURA), "## Entrada de incidencias (F-036)"),
            "### Lo que no hacen",
        )
    )

    # Lo de F-056 sigue, y se añade lo de F-060.
    assert "Enmienda del 2026-10-08 (F-056)" in no_hacen
    assert "Enmienda del 2026-10-13 (F-060)" in no_hacen
    assert "la importación escribe revisiones del sistema" in no_hacen


@pytest.mark.parametrize(
    "fila", ("| `sigrid-api` |", "| PostgreSQL `psql-albaranes-rs9k2` |")
)
def test_f060_r43_las_filas_de_sistemas_nombran_f060(fila):
    assert "Desde F-060" in _normal(_fila(_leer(ARQUITECTURA), fila))


# --------------------------------------------------------------------------
# Sin valores y sin correos
# --------------------------------------------------------------------------


def _textos_nuevos() -> dict[str, str]:
    integracion = _leer(INTEGRACION)
    return {
        "integracion-1": _seccion(integracion, TITULO_DE_LA_LECTURA),
        "integracion-2": _seccion(integracion, TITULO_DE_LAS_REVISIONES),
        "integracion-4": _seccion(integracion, TITULO_DE_LAS_VARIABLES),
        "integracion-7": _seccion(integracion, "## 7 · Datos personales"),
        "integracion-8": _seccion(integracion, "## 8 · Qué exponemos nosotros"),
        "arquitectura": _normalizacion(),
    }


@pytest.mark.parametrize(
    "donde",
    ("integracion-1", "integracion-2", "integracion-4", "integracion-7", "integracion-8", "arquitectura"),
)
def test_f060_r43_lo_nuevo_no_lleva_valores_ni_correos(donde):
    texto = _textos_nuevos()[donde]

    assert hallazgos(texto) == {}
    assert CORREO.search(texto) is None, f"{donde} lleva un correo escrito"
