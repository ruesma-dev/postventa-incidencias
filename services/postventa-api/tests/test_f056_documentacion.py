# services/postventa-api/tests/test_f056_documentacion.py
"""La documentación que F-056 deja al día (T15; R44).

Al modo de `test_f036_documentacion.py`. F-056 añade al servicio la
**revisión de la bandeja**: una tabla append-only en el esquema propio, tres
endpoints, una **tercera lectura** de Sigrid (las ubicaciones válidas de la
tipología de cada unidad) y, por primera vez en el esquema, el **correo** de
una persona —el de quien revisa—. Quien administre el PostgreSQL compartido o
`sigrid-api`, quien diseñe F-038 (la página) o F-040 (el volcado) y quien
audite los datos personales tienen que poder saberlo sin abrir el código.

Lo que fija:

- **R44** · `docs/INTEGRACION.md`:
  - §1: las **tres** lecturas de Sigrid por `POST /api/sql/read` (las dos de
    F-036 y la de ubicaciones), con las tablas del SQL de verdad, su techo,
    su 409 y su 503, y que no se pide nada al dueño de la pasarela;
  - §2: la tabla `postventa.revisiones_bandeja`, append-only, en el árbol y
    con su `.sql`, y que la bandeja de F-036 no se toca;
  - §4: que no hay variables de entorno nuevas (R40);
  - §7: el **correo** como dato de un **empleado interno**, dónde se guarda,
    las **tres** respuestas que lo llevan (el listado, el historial y la 200
    de la acción, con el de quien actúa; nunca un error), que no va a ningún
    log, que el `oid` no sale en ninguna respuesta y que no se publica en el
    datamart (F-048);
  - §8: los tres endpoints en la tabla —leídos de `function_app.py`—, la
    paginación, que no dependen de ninguna ventana, la cuenta de «veinte» y
    lo que hereda F-040;
  - §9: dónde vive cada pieza.
- **R44** · `docs/ARCHITECTURE.md`: la sección «Revisión de la bandeja
  (F-056)» —la tabla append-only, los estados derivados, las acciones, los
  motivos de no aprobable (leídos del `Enum` del dominio), los tres
  endpoints, la paginación, el correo, que no escribe en Sigrid y lo que
  hereda F-040—, la enmienda en «Lo que no hacen» de F-036 y las dos filas de
  la tabla de sistemas.
- Que nada de lo nuevo lleva valores (el barrido de
  `test_f005_integracion_sin_secretos.py`) ni un correo escrito.

Los controles **leen el código** siempre que pueden —la tabla del DDL, las
tablas de Sigrid del SQL de las ubicaciones, las rutas registradas y los
`Enum` del dominio— y exigen que el documento los nombre: lo que se documenta
es lo implementado. La copia de `azure-apps/` (T16) es **otro repositorio** y
no se comprueba aquí, con el criterio de `test_f036_documentacion.py`. Sin red,
sin base, sin IA: solo se leen el Markdown y el código.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from domain.models.revision import AccionRevision, EstadoRevision, MotivoNoAprobable
from infrastructure.sigrid.consultas_ubicaciones_validas import (
    SQL_UBICACIONES_DE_LAS_UNIDADES,
)
from tests.test_f005_integracion_sin_secretos import hallazgos

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent
SERVICIO = RAIZ / "services" / "postventa-api"

INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
FUNCTION_APP = SERVICIO / "function_app.py"
DDL_DE_F056 = (
    SERVICIO / "infrastructure" / "persistencia" / "sql" / "15_revisiones_bandeja.sql"
)

#: Las tres rutas de F-056 (`design.md` §8), como las escribe la tabla de §8.
ENDPOINTS_DE_F056 = (
    ("GET", "revision"),
    ("GET", "revision/historial"),
    ("POST", "revision/acciones"),
)

#: La spec, a la que apuntan los dos documentos.
SPEC = "specs/F-056-revision-bandeja-backend/"

#: Los módulos de F-056 que §9 de `INTEGRACION.md` tiene que localizar.
MODULOS_DE_F056 = (
    "application/pipelines/revision.py",
    "domain/models/revision.py",
    "infrastructure/persistencia/repositorio_revision_pg.py",
    "infrastructure/sigrid/ubicaciones_validas.py",
    "infrastructure/sigrid/consultas_ubicaciones_validas.py",
    "interface_adapters/api/revision.py",
)

TITULO_DE_LA_REVISION = "## Revisión de la bandeja (F-056)"

#: Los dos subapartados de F-056 en `INTEGRACION.md`: la lectura, en §1; la
#: tabla, en §2.
TITULO_DE_LA_LECTURA = "### Con F-056 · la tercera lectura: las ubicaciones válidas"
TITULO_DE_LA_TABLA = "### Con F-056 · la revisión de la bandeja"

#: Un correo escrito, de cualquier dominio: los documentos no llevan ninguno.
CORREO = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")


def _leer(documento: Path) -> str:
    return documento.read_text(encoding="utf-8")


def _normal(texto: str) -> str:
    """Sin negritas, sin comillas de código, sin la marca `>` de los recuadros y
    sin saltos: se compara lo que el documento **dice**, no cómo está envuelto
    a 79 columnas."""
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


def _tabla_del_ddl() -> list[str]:
    """La tabla que crea el DDL de F-056, leída de su `.sql`."""
    return re.findall(
        r"CREATE TABLE IF NOT EXISTS postventa\.(\w+) \(", _leer(DDL_DE_F056)
    )


def _tablas_de_sigrid() -> set[str]:
    """Las tablas de Sigrid que lee la consulta de las ubicaciones, del código."""
    return set(re.findall(r"\bdbo\.(\w+)", SQL_UBICACIONES_DE_LAS_UNIDADES))


def _integracion(titulo: str) -> str:
    return _seccion(_leer(INTEGRACION), titulo)


def _revision() -> str:
    """La sección de F-056 en la arquitectura. Se lee en el cuerpo de cada test,
    no en un fixture: si falta, el test **falla** por aserción en vez de dar
    un error de preparación."""
    return _seccion(_leer(ARQUITECTURA), TITULO_DE_LA_REVISION)


# --------------------------------------------------------------------------
# Los controles leen el código: que no lean nada vacío
# --------------------------------------------------------------------------


def test_f056_t15_los_controles_leen_algo_del_codigo():
    """Un control que no lee nada da verde para siempre: se fija lo que leen."""
    assert _tabla_del_ddl() == ["revisiones_bandeja"]
    assert _tablas_de_sigrid() == {"upv", "con", "prmtpl"}
    assert [a.value for a in AccionRevision] == [
        "editar",
        "descartar",
        "aprobar",
        "recuperar",
    ]
    assert len(MotivoNoAprobable) == 9
    registradas = _leer(FUNCTION_APP)
    for metodo, ruta in ENDPOINTS_DE_F056:
        assert re.search(
            rf'route="{re.escape(ruta)}",\s*methods=\["{metodo}"\]', registradas
        ), f"{metodo} {ruta} no está registrada en function_app.py"
    for modulo in MODULOS_DE_F056:
        assert (SERVICIO / modulo).is_file(), modulo


@pytest.mark.parametrize(
    "texto",
    (
        "Escríbele a alguien@ejemplo.invalid si falla.",
        "persona.apellido@empresa.es",
    ),
    ids=("ficticio", "con-punto"),
)
def test_f056_t15_el_control_de_correos_caza(texto):
    """Control negativo: el barrido de correos salta con un correo escrito."""
    assert CORREO.search(texto)


# --------------------------------------------------------------------------
# R44 · INTEGRACION.md §1: las tres lecturas de Sigrid
# --------------------------------------------------------------------------


def test_f056_r44_la_fila_de_sigrid_api_de_la_seccion_uno_nombra_f056():
    """§1 · la fila de `sigrid-api` gana la tercera lectura."""
    fila = _normal(_fila(_integracion("## 1 · Qué consumimos hoy"), "| `sigrid-api`"))

    for texto in ("F-056", "tercera lectura", "ubicaciones válidas"):
        assert texto in fila, f"la fila de sigrid-api no dice «{texto}»"


@pytest.mark.parametrize("tabla", sorted(_tablas_de_sigrid()))
def test_f056_r44_la_seccion_uno_nombra_cada_tabla_de_la_tercera_lectura(tabla):
    """§1 · las tablas de la lectura de ubicaciones, sacadas del SQL de verdad."""
    assert f"dbo.{tabla}" in _integracion(TITULO_DE_LA_LECTURA)


def test_f056_r44_la_seccion_uno_describe_la_tercera_lectura():
    """§1 · R46–R48: solo `sql/read`, por unidad, su techo, sus errores y cuándo."""
    seccion = _normal(_integracion(TITULO_DE_LA_LECTURA))

    for texto in (
        "tres lecturas",
        "POST /api/sql/read",
        "ninguna escritura",
        "prmtpl.ubica",
        "tipología",
        "por unidad",
        "exacta",
        "1.000 filas",
        "catalogo_sin_verificar",
        "503",
        "Una vez por petición",
        "GET /api/revision",
        "editar",
        "aprobar",
        "descartar",
        "recuperar",
        "historial",
        "no pide ningún cambio",
        "CIERRE_HABILITADO",
        "ARCHIVO_HABILITADO",
        "config/plantilla_incidencias.yaml",
    ):
        assert texto in seccion, f"§1 «Con F-056» no dice «{texto}»"


def test_f056_r44_la_tercera_lectura_va_dentro_de_la_seccion_uno():
    """Va con las otras dos, en «Qué consumimos hoy», detrás de la de F-036."""
    uno = _integracion("## 1 · Qué consumimos hoy")

    assert TITULO_DE_LA_LECTURA in uno
    assert uno.index("### Con F-036") < uno.index(TITULO_DE_LA_LECTURA)


# --------------------------------------------------------------------------
# R44 · INTEGRACION.md §2: la tabla
# --------------------------------------------------------------------------


@pytest.mark.parametrize("tabla", _tabla_del_ddl())
def test_f056_r44_la_seccion_dos_nombra_la_tabla_nueva(tabla):
    """§2 · el árbol del esquema y su párrafo, con la tabla del DDL real."""
    seccion = _integracion("## 2 · La base de datos")
    arbol = seccion[
        seccion.index("```") : seccion.index("```", seccion.index("```") + 3)
    ]

    assert tabla in arbol, f"el árbol del esquema no tiene «{tabla}»"
    assert f"postventa.{tabla}" in seccion
    assert DDL_DE_F056.name in seccion


def test_f056_r44_la_seccion_dos_describe_la_tabla():
    """§2 · R4, R36–R38: append-only, la foto, el `oid` y el correo, sin binarios."""
    seccion = _normal(_integracion(TITULO_DE_LA_TABLA))

    for texto in (
        "Append-only",
        "revision_id",
        "foto completa",
        "revisado_por",
        "revisado_correo",
        "El estado no se guarda",
        "postventa.bandeja_incidencias",
        "no se toca",
        "FOR UPDATE",
        "ninguna columna binaria ni JSON",
        SPEC,
    ):
        assert texto in seccion, f"§2 «Con F-056» no dice «{texto}»"
    assert "ya no son trece, son catorce" in _normal(
        _integracion("## 2 · La base de datos")
    )


def test_f056_r44_la_seccion_dos_corrige_lo_que_decia_de_f038():
    """§2 · la bandeja de F-036 decía que su revisión era de F-038: ahora es de F-056."""
    seccion = _normal(_integracion("## 2 · La base de datos"))

    assert "la revisión de la bandeja es F-056" in seccion


# --------------------------------------------------------------------------
# R44 · INTEGRACION.md §4: ninguna variable nueva (R40)
# --------------------------------------------------------------------------


def test_f056_r40_la_seccion_cuatro_dice_que_no_hay_variables_nuevas():
    seccion = _normal(_integracion("## 4 · Variables de entorno"))

    assert "F-056 no añade ninguna variable de entorno" in seccion


# --------------------------------------------------------------------------
# R44 · INTEGRACION.md §7: el correo, explícito
# --------------------------------------------------------------------------


def _enmienda_del_correo() -> str:
    """El recuadro de F-056 en §7: desde su línea de «Enmienda» hasta la última
    línea seguida que empieza por `>`. Lo del correo se busca **ahí**, no en
    toda la sección: «una sola columna de una sola tabla», por ejemplo, ya lo
    decía §7 del DNI."""
    lineas = _integracion("## 7 · Datos personales").splitlines()
    inicio = [
        i
        for i, linea in enumerate(lineas)
        if "Enmienda del 2026-10-08 (F-056)" in linea
    ]
    assert len(inicio) == 1, f"se esperaba un recuadro de F-056 en §7: {len(inicio)}"
    recuadro = []
    for linea in lineas[inicio[0] :]:
        if not linea.startswith(">"):
            break
        recuadro.append(linea.removeprefix(">"))
    return _normal(" ".join(recuadro))


def test_f056_r44_la_seccion_siete_dice_que_es_el_correo_y_donde_se_guarda():
    """§7 · D-8, design §9: de quién es, dónde vive y por qué."""
    seccion = _enmienda_del_correo()

    for texto in (
        "F-056",
        "correo corporativo",
        "empleado interno",
        "posventa-usuarios",
        "postventa.revisiones_bandeja",
        "revisado_correo",
        "una sola columna de una sola tabla",
        "traza de quién dice ser",
        "/.auth/me",
        "decisión del humano del 2026-10-06",
    ):
        assert texto in seccion, f"§7 no dice «{texto}»"


def test_f056_r44_la_seccion_siete_cuenta_las_tres_respuestas_con_correo():
    """§7 · R10, R11 y la decisión del líder del 2026-10-08: tres, y cuáles."""
    seccion = _enmienda_del_correo()

    for texto in (
        "tres respuestas",
        "GET /api/revision",
        "GET /api/revision/historial",
        "POST /api/revision/acciones",
        "quien acaba de actuar",
        "Ningún error",
    ):
        assert texto in seccion, f"§7 no dice «{texto}»"


def test_f056_r44_la_seccion_siete_dice_lo_que_no_se_hace_con_el_correo():
    """§7 · R11, R41, R12: ni logs, ni el `oid` en respuestas, ni otras tablas, ni F-048."""
    seccion = _enmienda_del_correo()

    for texto in (
        "no va a ningún log",
        "el oid no sale en ninguna respuesta",
        "Ninguna otra tabla",
        "F-048",
        "motivo",
        "solo sale en el historial",
    ):
        assert texto in seccion, f"§7 no dice «{texto}»"


def test_f056_r44_la_seccion_siete_enmienda_lo_de_nunca_su_correo():
    """§7 decía «nunca su correo ni su nombre»: se conserva y se enmienda, no se borra."""
    seccion = _normal(_integracion("## 7 · Datos personales"))

    assert "nunca su correo ni su nombre" in seccion
    assert "Enmienda del 2026-10-08 (F-056)" in seccion


# --------------------------------------------------------------------------
# R44 · INTEGRACION.md §8: los tres endpoints y «veinte»
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("metodo", "ruta"), ENDPOINTS_DE_F056, ids=lambda x: str(x))
def test_f056_r44_la_tabla_de_la_seccion_ocho_declara_cada_endpoint(metodo, ruta):
    """§8 · cada ruta de F-056 es una fila de la tabla, y la fila es de F-056."""
    tabla = _integracion("### Los endpoints, y qué hace cada uno")

    assert "F-056" in _fila(tabla, f"| `{metodo} /api/{ruta}` |")


def test_f056_r44_las_filas_dicen_que_hace_cada_endpoint():
    """§8 · qué lee, qué escribe y dónde; ninguno escribe en Sigrid."""
    tabla = _integracion("### Los endpoints, y qué hace cada uno")
    listado = _normal(_fila(tabla, "| `GET /api/revision` |"))
    historial = _normal(_fila(tabla, "| `GET /api/revision/historial` |"))
    acciones = _normal(_fila(tabla, "| `POST /api/revision/acciones` |"))

    for texto in (
        "paginada",
        "cursor",
        "200",
        "10.000",
        "bandeja_demasiado_grande",
        "correo",
    ):
        assert texto in listado, f"la fila del listado no dice «{texto}»"
    for texto in ("no lee Sigrid", "correo"):
        assert texto in historial, f"la fila del historial no dice «{texto}»"
    for texto in (
        "postventa.revisiones_bandeja",
        "append-only",
        "confirmado: true",
        "revision_desactualizada",
        "incidencia_no_aprobable",
        "Nada en Sigrid",
        "F-040",
    ):
        assert texto in acciones, f"la fila de las acciones no dice «{texto}»"


def test_f056_r44_la_seccion_ocho_dice_la_cuenta_y_las_ventanas():
    """§8 · R40 y la cuenta de anónimos: veinte (O-1 de la review del Bloque 3)."""
    seccion = _normal(_integracion("## 8 · Qué exponemos nosotros"))

    for texto in (
        "Los veinte quedan en nivel",
        "Los tres endpoints de F-056 no dependen de ARCHIVO_HABILITADO ni de CIERRE_HABILITADO",
        "tercer endpoint que devuelve dato de fuera acumulado",
    ):
        assert texto in seccion, f"§8 no dice «{texto}»"
    assert "Los diecisiete quedan en nivel" not in seccion


def test_f056_r44_la_seccion_ocho_dice_lo_que_hereda_f040_y_lo_que_falta():
    """§8 · R34: las candidatas al volcado son de F-040; la página es F-038."""
    seccion = _normal(_integracion("## 8 · Qué exponemos nosotros"))

    for texto in ("candidatas al volcado", "F-040", "F-038", "paginación"):
        assert texto in seccion, f"§8 no dice «{texto}»"


def test_f056_r44_la_seccion_ocho_dice_que_f056_no_esta_desplegada():
    """§8 · «Qué NO está desplegado»: F-056, con su consecuencia visible."""
    tabla = _normal(_integracion("### Qué NO está desplegado"))
    fila = _normal(
        _fila(_integracion("### Qué NO está desplegado"), "| La revisión de la bandeja")
    )

    assert "F-056" in tabla
    for texto in ("F-056", "sin desplegar", "F-038"):
        assert texto in fila, f"la fila de F-056 no dice «{texto}»"


# --------------------------------------------------------------------------
# R44 · INTEGRACION.md §9 y la cabecera
# --------------------------------------------------------------------------


@pytest.mark.parametrize("modulo", MODULOS_DE_F056)
def test_f056_r44_la_seccion_nueve_localiza_cada_pieza(modulo):
    assert modulo in _integracion("## 9 · Dónde está cada cosa")


@pytest.mark.parametrize(
    ("seccion", "titulo"),
    (
        ("§1", TITULO_DE_LA_LECTURA),
        ("§2", "## 2 · La base de datos"),
        ("§9", "## 9 · Dónde está cada cosa"),
    ),
)
def test_f056_r44_integracion_lleva_a_la_spec(seccion, titulo):
    assert SPEC in _integracion(titulo), seccion


def test_f056_r44_la_cabecera_dice_que_f056_lo_toco():
    """La cabecera, al día (O-1 de la review de F-053)."""
    cabecera = _normal(_leer(INTEGRACION).split("## 1 ·")[0])

    assert "Última feature que lo tocó: F-056" in cabecera
    assert "Fecha: 2026-10-08." in cabecera


# --------------------------------------------------------------------------
# R44 · ARCHITECTURE.md
# --------------------------------------------------------------------------


def test_f056_r44_la_arquitectura_tiene_la_seccion_de_la_revision():
    revision = _revision()
    assert len(_normal(revision)) > 2000


def test_f056_r44_la_seccion_va_tras_la_entrada_y_antes_del_acceso_a_datos():
    """Va con la entrada de F-036, que revisa, antes de la tabla de sistemas."""
    texto = _leer(ARQUITECTURA)
    assert TITULO_DE_LA_REVISION in texto, "no está la sección de F-056"

    assert (
        texto.index("## Entrada de incidencias (F-036)")
        < texto.index(TITULO_DE_LA_REVISION)
        < texto.index("## Acceso a datos y sistemas externos")
    )


def test_f056_r44_describe_la_tabla_y_los_estados():
    """R1, R4, R36–R38: append-only, la foto, estados derivados, `revision_id`."""
    revision = _revision()
    texto = _normal(revision)

    for texto_esperado in (
        "postventa.revisiones_bandeja",
        "append-only",
        "foto completa",
        "revision_id",
        "se deriva",
        "postventa.bandeja_incidencias",
    ):
        assert texto_esperado in texto, f"la sección no dice «{texto_esperado}»"


@pytest.mark.parametrize("estado", [e.value for e in EstadoRevision])
def test_f056_r44_nombra_cada_estado(estado):
    revision = _revision()
    assert estado in revision


@pytest.mark.parametrize("accion", [a.value for a in AccionRevision])
def test_f056_r44_nombra_cada_accion(accion):
    revision = _revision()
    assert accion in revision


@pytest.mark.parametrize("motivo", [m.value for m in MotivoNoAprobable])
def test_f056_r44_nombra_cada_motivo_de_no_aprobable(motivo):
    """R21 · los códigos, leídos del `Enum`: lo que ve la página es lo que hay."""
    revision = _revision()
    assert motivo in revision


def test_f056_r44_describe_la_concurrencia_y_la_validacion():
    """R7, R13, R20, R46–R48: frescura optimista y validación contra Sigrid de hoy."""
    revision = _revision()
    texto = _normal(revision)

    for texto_esperado in (
        "revision_previa",
        "revision_desactualizada",
        "FOR UPDATE",
        "catálogo de hoy",
        "comparación exacta",
        "ubicaciones válidas",
        "tipología",
        "prmtpl.ubica",
        "por unidad",
    ):
        assert texto_esperado in texto, f"la sección no dice «{texto_esperado}»"


def test_f056_r44_describe_los_tres_endpoints_y_la_paginacion():
    """R23–R33: las tres rutas, el cursor opaco y el resumen de la obra entera."""
    revision = _revision()
    texto = _normal(revision)

    for metodo, ruta in ENDPOINTS_DE_F056:
        assert f"{metodo} /api/{ruta}" in texto, f"la sección no nombra {metodo} {ruta}"
    for texto_esperado in (
        "cursor",
        "base64url",
        "tamano",
        "200",
        "10.000",
        "bandeja_demasiado_grande",
        "resumen",
        "por_motivo",
    ):
        assert texto_esperado in texto, f"la sección no dice «{texto_esperado}»"


def test_f056_r44_describe_el_correo():
    """D-8: dónde se guarda, las tres respuestas que lo llevan y que no va a logs."""
    revision = _revision()
    texto = _normal(revision)

    for texto_esperado in (
        "revisado_correo",
        "tres respuestas",
        "nunca va a un log",
        "el oid no sale en ninguna respuesta",
    ):
        assert texto_esperado in texto, f"la sección no dice «{texto_esperado}»"


def test_f056_r44_dice_que_no_escribe_en_sigrid_y_lo_que_hereda_f040():
    """R39, R34–R35 y design §10: solo lee; lo aprobado es lo que F-040 vuelca."""
    revision = _revision()
    texto = _normal(revision)

    for texto_esperado in (
        "Nada de F-056 escribe en Sigrid",
        "tres lecturas",
        "POST /api/sql/read",
        "candidatas_al_volcado",
        "CandidataAlVolcado",
        "huella",
        "F-040",
        "F-038",
        "CIERRE_HABILITADO",
        "Ninguna variable de entorno nueva",
    ):
        assert texto_esperado in texto, f"la sección no dice «{texto_esperado}»"


def test_f056_r44_lleva_a_la_spec_y_a_integracion():
    revision = _revision()
    assert SPEC in revision
    assert "docs/INTEGRACION.md" in revision


def test_f056_r44_enmienda_lo_que_no_hacen_de_f036():
    """«Lo que no hacen» de F-036 decía que revisar es F-038: se enmienda, no se borra."""
    no_hacen = _normal(
        _seccion(
            _seccion(_leer(ARQUITECTURA), "## Entrada de incidencias (F-036)"),
            "### Lo que no hacen",
        )
    )

    assert "No revisa" in no_hacen
    assert "Enmienda del 2026-10-08 (F-056)" in no_hacen
    assert "el backend de la revisión es F-056" in no_hacen


def test_f056_r44_la_fila_de_sigrid_api_nombra_la_tercera_lectura():
    fila = _normal(_fila(_leer(ARQUITECTURA), "| `sigrid-api` |"))

    assert "F-056" in fila
    assert "tercera lectura" in fila


def test_f056_r44_la_fila_de_postgresql_nombra_la_tabla_nueva():
    fila = _normal(_fila(_leer(ARQUITECTURA), "| PostgreSQL `psql-albaranes-rs9k2` |"))

    assert "F-056" in fila
    for tabla in _tabla_del_ddl():
        assert tabla in fila, f"la fila de PostgreSQL no nombra «{tabla}»"


# --------------------------------------------------------------------------
# Sin valores y sin correos
# --------------------------------------------------------------------------


def _textos_nuevos() -> dict[str, str]:
    """Lo que F-056 añade a los dos documentos, por sección."""
    integracion = _leer(INTEGRACION)
    return {
        "integracion-1": _seccion(integracion, TITULO_DE_LA_LECTURA),
        "integracion-2": _seccion(integracion, TITULO_DE_LA_TABLA),
        "integracion-7": _seccion(integracion, "## 7 · Datos personales"),
        "integracion-8": _seccion(integracion, "## 8 · Qué exponemos nosotros"),
        "arquitectura": _seccion(_leer(ARQUITECTURA), TITULO_DE_LA_REVISION),
    }


@pytest.mark.parametrize(
    "donde",
    (
        "integracion-1",
        "integracion-2",
        "integracion-7",
        "integracion-8",
        "arquitectura",
    ),
)
def test_f056_r44_lo_nuevo_no_lleva_valores_ni_correos(donde):
    """Ni hosts, ni GUID, ni IP (el barrido de F-005), ni un correo escrito."""
    texto = _textos_nuevos()[donde]

    assert hallazgos(texto) == {}
    assert CORREO.search(texto) is None, f"{donde} lleva un correo escrito"
