# services/postventa-api/tests/test_f059_documentacion.py
"""La documentación que F-059 deja al día (T18, T20; R40).

Al modo de `test_f056_documentacion.py` y `test_f060_documentacion.py`. F-059
**crea partes de reclamación en el ERP de producción**: una tabla append-only
de eventos, tres endpoints, una ventana propia que se publica **cerrada** y,
por segunda vez en el esquema, el **correo** de una persona —el de quien
ensaya o vuelca—. Quien administre `sigrid-api`, el PostgreSQL compartido o
el ERP, quien diseñe F-040 (la página) y quien audite los datos personales
tienen que poder saberlo sin abrir el código; y Posventa, que el parte **nace
en SAT y lo pasa a PTE a mano**.

Lo que fija (R40):

- `docs/ARCHITECTURE.md`: la sección «Volcado a Sigrid (F-059)» —el flujo,
  los seis estados (leídos del `Enum`), la tabla, la ventana, el troceo, por
  qué el reintento es seguro y que el parte queda en SAT—, la enmienda de la
  de F-056 sobre estados y acciones (y sobre lo que heredaba F-040), y las
  filas de `sigrid-api` y de PostgreSQL de la tabla de sistemas.
- `docs/INTEGRACION.md`: la cabecera; §2, la tabla en el árbol y su
  subapartado; §3 bis, «Qué escribimos como PARTE NUEVO (F-059)»; §4, las dos
  variables (leídas de `.env.example`); §7, la cuarta superficie y el correo
  de quien vuelca; §8, los tres endpoints —leídos de `function_app.py`—, que
  no miran las otras ventanas, «Los veinticuatro quedan en nivel» sin «Los
  veintiuno», y lo que falta por desplegar; §9, dónde vive cada pieza.
- `docs/DESPLIEGUE.md`: la sección de la ventana del volcado, publicada
  cerrada, con `27_ventana_volcado.ps1` y `28_volcado_lectura_sigrid.ps1`.
- Que nada de lo nuevo lleva valores (el barrido de
  `test_f005_integracion_sin_secretos.py`) ni un correo escrito.

La copia de `azure-apps/` (T21) es **otro repositorio** y no se comprueba
aquí, con el criterio de `test_f036_documentacion.py`. Sin red, sin base, sin
IA: solo se leen el Markdown y el código.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from domain.models.revision import EstadoRevision
from domain.models.situacion_volcado import EstadoEvento, ModoVolcado

from tests.test_f005_integracion_sin_secretos import hallazgos

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent
SERVICIO = RAIZ / "services" / "postventa-api"

INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
DESPLIEGUE = RAIZ / "docs" / "DESPLIEGUE.md"
FUNCTION_APP = SERVICIO / "function_app.py"
EJEMPLO_ENV = SERVICIO / ".env.example"
DDL_DE_F059 = (
    SERVICIO / "infrastructure" / "persistencia" / "sql" / "16_volcados_sigrid.sql"
)

#: Las tres rutas de F-059 (`design.md` §11), como las escribe la tabla de §8.
ENDPOINTS_DE_F059 = (
    ("GET", "volcado"),
    ("POST", "volcado/ensayo"),
    ("POST", "volcado/volcar"),
)

#: Las dos App Settings de F-059 (`config/settings.py`, §13).
VARIABLES_DE_F059 = ("VOLCADO_HABILITADO", "VOLCADO_PARTES_POR_LLAMADA")

#: La spec, a la que apuntan los documentos.
SPEC = "specs/F-059-volcado-sigrid-backend/"

#: Los módulos de F-059 que §9 de `INTEGRACION.md` tiene que localizar.
MODULOS_DE_F059 = (
    "domain/models/volcado.py",
    "domain/models/situacion_volcado.py",
    "domain/ports/volcado.py",
    "application/pipelines/volcado.py",
    "interface_adapters/api/volcado.py",
    "infrastructure/sigrid/volcado.py",
    "infrastructure/persistencia/repositorio_volcado_pg.py",
    "infrastructure/persistencia/sentencias_volcado.py",
)

#: Los dos scripts de F-059.
SCRIPTS_DE_F059 = (
    "infra/27_ventana_volcado.ps1",
    "infra/28_volcado_lectura_sigrid.ps1",
)

TITULO_DEL_VOLCADO = "## Volcado a Sigrid (F-059)"
TITULO_DE_LA_REVISION = "## Revisión de la bandeja (F-056)"
TITULO_DE_LA_NORMALIZACION = "## Normalizar las ubicaciones (F-060)"
TITULO_DE_SISTEMAS = "## Acceso a datos y sistemas externos"

TITULO_DE_LA_TABLA = "### Con F-059 · el volcado a Sigrid"
TITULO_DEL_PARTE = "### Qué escribimos como PARTE NUEVO (F-059)"
TITULO_DE_LAS_VARIABLES = "### Las de F-059 (el volcado)"
TITULO_DE_LA_VENTANA = "## 4 ter · La ventana del volcado: `/api/volcado/volcar`"

#: Un correo escrito, de cualquier dominio: los documentos no llevan ninguno.
CORREO = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")


def _leer(documento: Path) -> str:
    return documento.read_text(encoding="utf-8")


def _normal(texto: str) -> str:
    """Sin negritas, sin comillas de código, sin la marca `>` de los recuadros y
    sin saltos: se compara lo que el documento **dice**, no cómo está envuelto."""
    sin_recuadro = "\n".join(
        re.sub(r"^\s*>\s?", "", linea) for linea in texto.splitlines()
    )
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
    assert len(filas) == 1, (
        f"se esperaba una fila que empiece por «{principio}»: {len(filas)}"
    )
    return filas[0]


def _integracion(titulo: str) -> str:
    return _seccion(_leer(INTEGRACION), titulo)


def _volcado() -> str:
    """La sección de F-059 en la arquitectura. Se lee en el cuerpo de cada test:
    si falta, el test **falla** por aserción en vez de dar un error de preparación."""
    return _seccion(_leer(ARQUITECTURA), TITULO_DEL_VOLCADO)


def _variables_del_ejemplo() -> set[str]:
    return {
        linea.split("=", 1)[0].strip()
        for linea in _leer(EJEMPLO_ENV).splitlines()
        if "=" in linea and not linea.lstrip().startswith("#")
    }


# --------------------------------------------------------------------------
# Los controles leen el código: que no lean nada vacío
# --------------------------------------------------------------------------


def test_f059_r40_los_controles_leen_algo_del_codigo():
    """Un control que no lee nada da verde para siempre: se fija lo que leen."""
    assert len(EstadoRevision) == 6
    assert {"volcada", "en_duda"} <= {e.value for e in EstadoRevision}
    assert [m.value for m in ModoVolcado] == ["ensayo", "volcado"]
    assert len(EstadoEvento) == 7
    assert re.findall(
        r"CREATE TABLE IF NOT EXISTS postventa\.(\w+) \(", _leer(DDL_DE_F059)
    ) == ["volcados_sigrid"]
    registradas = _leer(FUNCTION_APP)
    for metodo, ruta in ENDPOINTS_DE_F059:
        assert re.search(
            rf'route="{re.escape(ruta)}",\s*methods=\["{metodo}"\]', registradas
        ), f"{metodo} {ruta} no está registrada en function_app.py"
    assert set(VARIABLES_DE_F059) <= _variables_del_ejemplo()
    for modulo in MODULOS_DE_F059:
        assert (SERVICIO / modulo).is_file(), modulo


@pytest.mark.parametrize(
    "texto",
    ("Escríbele a alguien@ejemplo.invalid si falla.", "persona.apellido@empresa.invalid"),
    ids=("ficticio", "con-punto"),
)
def test_f059_r40_el_control_de_correos_caza(texto):
    """Control negativo: el barrido de correos salta con un correo escrito."""
    assert CORREO.search(texto)


# --------------------------------------------------------------------------
# R40 · ARCHITECTURE.md
# --------------------------------------------------------------------------


def test_f059_r40_la_arquitectura_tiene_la_seccion_del_volcado():
    assert len(_normal(_volcado())) > 3000


def test_f059_r40_la_seccion_va_tras_la_normalizacion_y_antes_de_los_sistemas():
    texto = _leer(ARQUITECTURA)
    assert TITULO_DEL_VOLCADO in texto, "no está la sección de F-059"

    assert texto.index(TITULO_DE_LA_NORMALIZACION) < texto.index(TITULO_DEL_VOLCADO)
    assert texto.index(TITULO_DEL_VOLCADO) < texto.index(TITULO_DE_SISTEMAS)


@pytest.mark.parametrize("estado", [e.value for e in EstadoRevision])
def test_f059_r40_la_seccion_nombra_cada_estado(estado):
    """Los seis, leídos del `Enum`: el que se añada tiene que pasar por aquí."""
    assert estado in _normal(_volcado())


def test_f059_r40_la_seccion_cuenta_el_flujo_y_la_tabla():
    seccion = _normal(_volcado())

    for texto in (
        "GET /api/volcado",
        "POST /api/volcado/ensayo",
        "POST /api/volcado/volcar",
        "POST /api/sigrid/partes-reclamacion",
        "commit: false",
        "commit: true",
        "ensayo vigente",
        "30 minutos",
        "escritura anticipada",
        "enviado",
        "sin_respuesta",
        "postventa.volcados_sigrid",
        "16_volcados_sigrid.sql",
        "append-only",
        "sin índice único",
        "FOR UPDATE",
        SPEC,
    ):
        assert texto in seccion, f"la sección no dice «{texto}»"


def test_f059_r40_la_seccion_cuenta_la_ventana_y_el_troceo():
    seccion = _normal(_volcado())

    for texto in (
        "VOLCADO_HABILITADO",
        "se publica cerrada",
        "27_ventana_volcado.ps1",
        "el ensayo no la mira",
        "VOLCADO_PARTES_POR_LLAMADA",
        "troceo",
        "F-040",
        "proxy",
        "45 s",
    ):
        assert texto in seccion, f"la sección no dice «{texto}»"


def test_f059_r40_la_seccion_dice_por_que_el_reintento_es_seguro():
    seccion = _normal(_volcado())

    for texto in (
        "reintentar es seguro",
        "PVI-",
        "RCPCLI",
        "idempotente",
        "sp_getapplock",
        "no se reintenta",
    ):
        assert texto in seccion, f"la sección no dice «{texto}»"


def test_f059_r40_la_seccion_dice_que_el_parte_queda_en_sat():
    """Q-3: nace en SAT y **Posventa lo pasa a PTE a mano**; anularlo es la UI."""
    seccion = _normal(_volcado())

    for texto in (
        "SAT",
        "Posventa lo pasa a PTE a mano",
        "NO PROCEDE",
        "nunca con DELETE",
        "tipo 0002",
        "causante",
    ):
        assert texto in seccion, f"la sección no dice «{texto}»"


def test_f059_r40_la_seccion_de_f056_lleva_la_enmienda_de_estados_acciones_y_f040():
    """La enmienda de T2 (seis estados, sin acciones) y la de lo que heredaba
    F-040: el backend del volcado lo hizo F-059."""
    revision = _normal(_seccion(_leer(ARQUITECTURA), TITULO_DE_LA_REVISION))

    assert "Enmienda de F-059 (2026-10-15): seis estados" in revision
    assert "acciones: []" in revision
    hereda = _normal(_seccion(_leer(ARQUITECTURA), "### Lo que hereda F-040"))
    assert "Enmienda de F-059 (2026-10-17)" in hereda
    assert "Volcado a Sigrid (F-059)" in hereda


def test_f059_r40_la_tabla_de_sistemas_lo_dice_en_sigrid_api_y_en_postgresql():
    sistemas = _seccion(_leer(ARQUITECTURA), TITULO_DE_SISTEMAS)
    sigrid = _normal(_fila(sistemas, "| `sigrid-api` |"))
    postgres = _normal(_fila(sistemas, "| PostgreSQL `psql-albaranes-rs9k2` |"))

    for texto in (
        "Desde F-059",
        "POST /api/sigrid/partes-reclamacion",
        "VOLCADO_HABILITADO",
    ):
        assert texto in sigrid, f"la fila de sigrid-api no dice «{texto}»"
    for texto in ("Desde F-059", "volcados_sigrid"):
        assert texto in postgres, f"la fila de PostgreSQL no dice «{texto}»"


# --------------------------------------------------------------------------
# R40 · INTEGRACION.md: la cabecera y §2
# --------------------------------------------------------------------------


def test_f059_r40_la_cabecera_dice_que_f059_lo_toco():
    """Bien formada, que no retroceda y con F-059; sin la frase «sin desplegar»,
    que `test_f060_r43_la_cabecera_…` no deja estar en la cabecera."""
    from datetime import date

    cabecera = _normal(_leer(INTEGRACION).split("## 1 ·")[0])
    fechas = re.findall(r"Fecha: (\d{4}-\d{2}-\d{2})\. ", cabecera)
    features = re.findall(r"Última feature que lo tocó: F-(\d{3})\b", cabecera)

    assert features == ["059"]
    assert len(fechas) == 1
    assert date.fromisoformat(fechas[0]) >= date(2026, 10, 17)
    for texto in ("partes de reclamación", "§3 bis", "no está desplegada", "F-060"):
        assert texto in cabecera, f"la cabecera no dice «{texto}»"
    assert "sin desplegar" not in cabecera


def test_f059_r40_la_seccion_dos_tiene_la_tabla_en_el_arbol_y_su_subapartado():
    dos = _integracion("## 2 · La base de datos")
    arbol = re.search(r"```\n(.*?)```", dos, flags=re.DOTALL)
    assert arbol, "no está el árbol del esquema"
    tabla = _normal(_seccion(dos, TITULO_DE_LA_TABLA))

    assert "volcados_sigrid" in arbol.group(1)
    assert "ya no son catorce, son quince" in _normal(dos)
    for texto in (
        "postventa.volcados_sigrid",
        "16_volcados_sigrid.sql",
        "append-only",
        "Una fila por parte",
        "enviado",
        "actor_oid",
        "actor_correo",
        "no se lee nunca",
        "sin índice único",
        "FOR UPDATE",
        "ninguna columna binaria ni JSON",
        "no se tocan",
        SPEC,
    ):
        assert texto in tabla, f"§2 no dice «{texto}»"


# --------------------------------------------------------------------------
# R40 · INTEGRACION.md §3 bis: el parte nuevo
# --------------------------------------------------------------------------


def test_f059_r40_tres_bis_cuenta_lo_que_escribe_la_pasarela():
    parte = _normal(_integracion(TITULO_DEL_PARTE))

    for texto in (
        "POST /api/sigrid/partes-reclamacion",
        "cinco filas",
        "con, rcp, rcpint, conext y log",
        "una transacción por parte",
        "tipo 0002",
        "causante: false",
        "forma_comunicacion",
        "PVI-",
        "RCPCLI",
        "usu",
        "el login de Sigrid de la persona que vuelca",
        "commit: false",
        "commit: true",
        "No mandamos",
        "propietario",
    ):
        assert texto in parte, f"§3 bis no dice «{texto}»"


def test_f059_r40_tres_bis_dice_sat_pte_y_como_se_reconocen_y_anulan():
    """Q-3 y §14: nace en SAT, **Posventa lo pasa a PTE a mano**, se reconoce por
    `PVI-` en `RCPCLI` y se anula en la UI (NO PROCEDE), nunca con `DELETE`."""
    parte = _normal(_integracion(TITULO_DEL_PARTE))

    for texto in (
        "SAT",
        "Posventa lo pasa a PTE a mano",
        "avisa al industrial",
        "Cómo se reconocen nuestros partes",
        "NO PROCEDE",
        "nunca con DELETE",
        "28_volcado_lectura_sigrid.ps1",
        "reintentar es seguro",
        "VOLCADO_HABILITADO",
        "Volumen esperado",
    ):
        assert texto in parte, f"§3 bis no dice «{texto}»"


def test_f059_r40_tres_bis_dice_lo_que_no_hace():
    parte = _normal(_integracion(TITULO_DEL_PARTE))

    for texto in ("no pide ningún cambio", "sql/write", "no pasa a PTE", "urgencia"):
        assert texto in parte, f"§3 bis no dice «{texto}»"


# --------------------------------------------------------------------------
# R40 · INTEGRACION.md §4 y §7
# --------------------------------------------------------------------------


def test_f059_r40_la_seccion_cuatro_declara_las_dos_variables():
    variables = _normal(_integracion(TITULO_DE_LAS_VARIABLES))

    for variable in VARIABLES_DE_F059:
        assert variable in variables, f"§4 no declara {variable}"
    for texto in (
        "apagado por defecto en el código",
        "se publica cerrada",
        "27_ventana_volcado.ps1",
        "de 1 a 50",
        "503",
    ):
        assert texto in variables, f"§4 no dice «{texto}»"


def test_f059_r40_la_seccion_siete_cuenta_la_cuarta_superficie_y_el_correo():
    siete = _normal(_integracion("## 7 · Datos personales"))

    for texto in (
        "Enmienda del 2026-10-17 (F-059)",
        "volcados_sigrid.actor_correo",
        "cuarta superficie",
        "lo que este servicio escribe en el ERP",
        "GET /api/revision",
        "POST /api/revision/acciones",
        "volcado_por",
        "el oid no sale en ninguna respuesta",
        "ningún log",
        "filas",
        "motivo.mensaje",
    ):
        assert texto in siete, f"§7 no dice «{texto}»"


# --------------------------------------------------------------------------
# R40 · INTEGRACION.md §8 y §9
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("metodo", "ruta"), ENDPOINTS_DE_F059, ids=[r for _, r in ENDPOINTS_DE_F059]
)
def test_f059_r40_la_seccion_ocho_declara_cada_endpoint(metodo, ruta):
    tabla = _integracion("### Los endpoints, y qué hace cada uno")

    fila = _normal(_fila(tabla, f"| `{metodo} /api/{ruta}` |"))
    assert "F-059" in fila


def test_f059_r40_la_seccion_ocho_dice_la_cuenta_las_ventanas_y_lo_que_falta():
    ocho = _normal(_integracion("## 8 · Qué exponemos nosotros"))

    for texto in (
        "Los veinticuatro quedan en nivel",
        "Los tres endpoints de F-059 no dependen de ARCHIVO_HABILITADO ni de CIERRE_HABILITADO",
        "VOLCADO_HABILITADO",
        "Desde F-059",
        "el objeto volcado",
        "F-040",
    ):
        assert texto in ocho, f"§8 no dice «{texto}»"
    assert "Los veintiuno quedan en nivel" not in ocho
    fila = _normal(
        _fila(_integracion("### Qué NO está desplegado"), "| El volcado a Sigrid |")
    )
    for texto in ("F-059", "no está desplegada", "cerrada", "F-040"):
        assert texto in fila, f"la fila de F-059 no dice «{texto}»"


@pytest.mark.parametrize(
    "pieza", (*MODULOS_DE_F059, *SCRIPTS_DE_F059, SPEC, "16_volcados_sigrid.sql")
)
def test_f059_r40_la_seccion_nueve_localiza_cada_pieza(pieza):
    assert pieza in _integracion("## 9 · Dónde está cada cosa")


# --------------------------------------------------------------------------
# R40 · DESPLIEGUE.md
# --------------------------------------------------------------------------


def test_f059_r40_el_despliegue_tiene_la_seccion_de_la_ventana():
    texto = _leer(DESPLIEGUE)
    assert TITULO_DE_LA_VENTANA in texto, "no está la sección de la ventana del volcado"
    assert (
        texto.index("## 4 bis ·")
        < texto.index(TITULO_DE_LA_VENTANA)
        < texto.index("## 5 ·")
    )


def test_f059_r40_la_ventana_se_publica_cerrada_y_se_abre_con_su_script():
    ventana = _normal(_seccion(_leer(DESPLIEGUE), TITULO_DE_LA_VENTANA))

    for texto in (
        "VOLCADO_HABILITADO",
        "se publica cerrada",
        "con o sin -VentanasCerradas",
        "D-3",
        "27_ventana_volcado.ps1",
        "-Abrir",
        "-Cerrar",
        "sin preguntar",
        "el ensayo no la mira",
        "503 volcado_deshabilitado",
        "28_volcado_lectura_sigrid.ps1",
        "VOLCADO_PARTES_POR_LLAMADA",
        "Posventa lo pasa a PTE a mano",
        "NO PROCEDE",
    ):
        assert texto in ventana, f"la sección de la ventana no dice «{texto}»"


def test_f059_r40_la_tabla_de_scripts_dice_que_el_volcado_queda_cerrado():
    fila = _normal(
        _fila(_seccion(_leer(DESPLIEGUE), "## 2 ·"), "| 2 | `desplegar_backend.ps1` |")
    )

    assert "la del volcado" in fila
    assert "§4 ter" in fila


# --------------------------------------------------------------------------
# Ningún valor ni correo en lo nuevo
# --------------------------------------------------------------------------


def _lo_nuevo() -> dict[str, str]:
    return {
        "arquitectura": _volcado(),
        "integracion §2": _integracion(TITULO_DE_LA_TABLA),
        "integracion §3 bis": _integracion(TITULO_DEL_PARTE),
        "integracion §4": _integracion(TITULO_DE_LAS_VARIABLES),
        "despliegue": _seccion(_leer(DESPLIEGUE), TITULO_DE_LA_VENTANA),
    }


def test_f059_r40_lo_nuevo_no_lleva_valores_ni_correos():
    for nombre, texto in _lo_nuevo().items():
        assert hallazgos(texto) == {}, nombre
        assert CORREO.search(texto) is None, nombre
