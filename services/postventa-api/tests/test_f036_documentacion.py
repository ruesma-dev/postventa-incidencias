# services/postventa-api/tests/test_f036_documentacion.py
"""La documentación que F-036 deja al día (T26; R60, R61).

Al modo de `test_f013_documentacion.py`. F-036 abre una **segunda vía de
entrada** en el servicio —la plantilla, la importación del Excel de la
propiedad y la bandeja— y con ella el proyecto pasa a **leer el catálogo de
una obra** en Sigrid, a guardar **texto libre de la propiedad** y nombres de
proveedor en el servidor compartido, y a exponer cinco rutas más. Quien
administre `sigrid-api` o el PostgreSQL compartido tiene que poder saberlo sin
abrir el código, y quien diseñe F-037, F-038, F-039, F-040 o F-050 tiene que
encontrar escrito qué dejó hecho F-036 y qué no.

Lo que fija:

- **R60** · `docs/INTEGRACION.md` describe las **dos** lecturas nuevas de
  `sigrid-api` (§1), las **tres** tablas nuevas y la costura del
  discriminador `catalogo` (§2), que no hay variables nuevas (§4), el texto
  libre de la propiedad y los nombres de proveedor como datos que no salen en
  los logs (§7) y los **cinco** endpoints nuevos (§8).
- **R61** · `docs/ARCHITECTURE.md` describe la vía de entrada (plantilla →
  importación → bandeja, con el Excel de errores), la agrupación de oficios, y
  **lo que no hacen**: ni escriben en Sigrid, ni agrupan proveedores (F-050),
  ni leen actividades (F-039).

Los controles no copian el texto del documento: **leen el código** siempre
que pueden —las tablas del DDL, los valores del `CHECK` de `catalogo`, las
tablas de Sigrid del SQL del catálogo, las rutas registradas en
`function_app.py` y las dependencias de `requirements.txt`— y exigen que el
documento las nombre. Así, lo que se documenta es **lo implementado**, no el
borrador de la spec; y unos controles negativos impiden que vuelva lo que la
quinta enmienda sacó de F-036.

Lo que **no** se comprueba aquí es la copia de `azure-apps/`, que es **otro
repositorio**: un test que dependiera de que esté clonado al lado fallaría en
cualquier máquina donde no lo esté (el mismo criterio que
`test_f028_documentacion.py`). Su verificación es la declarada en `tasks.md`.
Los valores (hosts, GUID, IP) los barren `test_f005_integracion_sin_secretos.py`
y `test_f006_repo_sin_identificadores.py`; aquí se reutiliza el primero sobre
la sección nueva de la arquitectura, que aquel no mira.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from infrastructure.documentos import lector_aislado
from infrastructure.sigrid.consultas_catalogo import (
    SQL_OFICIOS_DE_LA_OBRA,
    SQL_UNIDADES_DE_LA_OBRA,
)
from tests.test_f005_integracion_sin_secretos import hallazgos

#: Raíz del repositorio (este fichero vive en `<servicio>/tests/`).
RAIZ = Path(__file__).resolve().parent.parent.parent.parent
SERVICIO = RAIZ / "services" / "postventa-api"

INTEGRACION = RAIZ / "docs" / "INTEGRACION.md"
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
FUNCTION_APP = SERVICIO / "function_app.py"
REQUISITOS_PY = SERVICIO / "requirements.txt"
DDL = SERVICIO / "infrastructure" / "persistencia" / "sql"
DDL_DE_F036 = (
    DDL / "12_importaciones.sql",
    DDL / "13_bandeja_incidencias.sql",
    DDL / "14_decisiones_equivalencia.sql",
)

#: El día de la última revisión de la documentación: T26 la escribió el
#: 2026-09-30, T44 (la lectura aislada, octava enmienda) la revisó el 2026-10-01
#: y el cierre de F-036 la dio por desplegada el 2026-10-05.
FECHA = "2026-10-05"

#: Las cinco rutas de F-036 (`design.md` §8), como las escribe la tabla de §8.
ENDPOINTS_DE_F036 = (
    ("GET", "plantilla"),
    ("POST", "importaciones"),
    ("GET", "bandeja"),
    ("GET", "catalogos/propuestas"),
    ("POST", "catalogos/decisiones"),
)

#: Las dos páginas nuevas del front (`design.md` §9 y §15.6).
PAGINAS_DE_F036 = ("importar.html", "oficios.html")

#: Las dos dependencias nuevas del servicio (`design.md` §2.2, T10).
DEPENDENCIAS_DE_F036 = ("openpyxl", "defusedxml")

#: Lo que la quinta enmienda (2026-09-29) sacó de F-036 y **no** puede
#: aparecer como si estuviera hecho: la marca de CIF y las lecturas de
#: actividades (a F-050 y F-039), la columna de proveedor fuera de `obrofc`,
#: las rutas y la página con los nombres de antes.
RETIRADO_DE_F036 = (
    "proveedor_fuera_de_obrofc",
    "SQL_ACTIVIDADES",
    "SQL_ARBOL_ACTIVIDADES",
    "/api/proveedores/",
    "catalogos.html",
    "proveedores.html",
    "decisiones_proveedor",
    "DENSE_RANK",
)


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


def _tablas_de_sigrid() -> set[str]:
    """Las tablas de Sigrid que leen las dos consultas del catálogo, del código."""
    return set(
        re.findall(r"\bdbo\.(\w+)", SQL_UNIDADES_DE_LA_OBRA + SQL_OFICIOS_DE_LA_OBRA)
    )


def _tablas_del_ddl() -> list[str]:
    """Las tablas que crea el DDL de F-036, leídas de sus `.sql`."""
    tablas: list[str] = []
    for fichero in DDL_DE_F036:
        tablas += re.findall(
            r"CREATE TABLE IF NOT EXISTS postventa\.(\w+) \(", _leer(fichero)
        )
    return tablas


def _catalogos_del_check() -> list[str]:
    """Los valores que admite el `CHECK` de `catalogo`, leídos del DDL."""
    hallado = re.search(
        r"catalogo\s+text\s+NOT NULL CHECK \(catalogo IN \(([^)]*)\)\)",
        _leer(DDL_DE_F036[2]),
    )
    assert hallado is not None, "no se encuentra el CHECK de catalogo en el DDL"
    return re.findall(r"'(\w+)'", hallado.group(1))


# --------------------------------------------------------------------------
# Los controles leen el código: que no lean nada vacío
# --------------------------------------------------------------------------


def test_f036_t26_los_controles_leen_algo_del_codigo():
    """Un control que no lee nada da verde para siempre: se fija lo que leen."""
    assert _tablas_de_sigrid() == {"upv", "con", "obrofc", "auxofc"}
    assert _tablas_del_ddl() == [
        "importaciones",
        "bandeja_incidencias",
        "decisiones_equivalencia",
    ]
    assert _catalogos_del_check() == ["oficio", "proveedor", "actividad_oficio"]
    registradas = _leer(FUNCTION_APP)
    for metodo, ruta in ENDPOINTS_DE_F036:
        assert re.search(
            rf'route="{re.escape(ruta)}",\s*methods=\["{metodo}"\]', registradas
        ), f"{metodo} {ruta} no está registrada en function_app.py"
    requisitos = _leer(REQUISITOS_PY)
    for dependencia in DEPENDENCIAS_DE_F036:
        assert re.search(rf"^{dependencia}\b", requisitos, re.MULTILINE)


# --------------------------------------------------------------------------
# R60 · INTEGRACION.md
# --------------------------------------------------------------------------


def test_f036_r60_la_cabecera_dice_que_f036_lo_toco_y_cuando():
    """La cabecera dice la última feature que tocó el documento, con fecha."""
    cabecera = _normal(_leer(INTEGRACION).split("## 1 ·")[0])

    assert f"Fecha: {FECHA}" in cabecera
    assert "Última feature que lo tocó: F-036" in cabecera


def test_f036_r60_la_fila_de_sigrid_api_de_la_seccion_uno_nombra_f036():
    """§1 · la fila de `sigrid-api` gana las lecturas del catálogo."""
    fila = _normal(
        _fila(
            _seccion(_leer(INTEGRACION), "## 1 · Qué consumimos hoy"), "| `sigrid-api`"
        )
    )

    assert "F-036" in fila
    assert "catálogo de una obra" in fila


@pytest.mark.parametrize("tabla", sorted(_tablas_de_sigrid()))
def test_f036_r60_la_seccion_uno_nombra_cada_tabla_de_sigrid_que_se_lee(tabla):
    """§1 · las tablas de las dos lecturas, sacadas del SQL de verdad."""
    seccion = _seccion(_leer(INTEGRACION), "## 1 · Qué consumimos hoy")

    assert f"dbo.{tabla}" in seccion


def test_f036_r60_la_seccion_uno_describe_las_dos_lecturas_nuevas():
    """§1 · dos lecturas, solo `sql/read`, su techo y sus puertas (R11, R46, R48)."""
    seccion = _normal(_seccion(_leer(INTEGRACION), "## 1 · Qué consumimos hoy"))

    for texto in (
        "Lo nuevo de F-036",
        "dos lecturas",
        "POST /api/sql/read",
        "ninguna escritura",
        "1.000 filas",
        "catalogo_sin_verificar",
        "obra_ambigua",
        "obra_sin_unidades",
        "ENTORNO",
        "CIERRE_HABILITADO",
        "ARCHIVO_HABILITADO",
        "CatalogoNoDisponible",
        "503",
    ):
        assert texto in seccion, f"§1 no dice «{texto}»"


def test_f036_r60_la_seccion_uno_dice_que_no_pide_nada_al_dueno_de_sigrid_api():
    """§11 del diseño: F-036 no pide nada a `sigrid-api`; lo que sí, F-039 y F-040."""
    seccion = _normal(_seccion(_leer(INTEGRACION), "## 1 · Qué consumimos hoy"))

    assert "no pide ningún cambio" in seccion
    assert "F-039" in seccion
    assert "F-040" in seccion


@pytest.mark.parametrize("tabla", _tablas_del_ddl())
def test_f036_r60_la_seccion_dos_nombra_cada_tabla_nueva(tabla):
    """§2 · el árbol del esquema y su párrafo, con las tablas del DDL real."""
    seccion = _seccion(_leer(INTEGRACION), "## 2 · La base de datos")
    arbol = seccion[
        seccion.index("```") : seccion.index("```", seccion.index("```") + 3)
    ]

    assert tabla in arbol, f"el árbol del esquema no tiene «{tabla}»"
    assert f"postventa.{tabla}" in seccion


@pytest.mark.parametrize("fichero", DDL_DE_F036, ids=lambda ruta: ruta.name)
def test_f036_r60_la_seccion_dos_nombra_cada_fichero_de_ddl(fichero):
    """§2 · el orden del DDL sigue en `12`, `13` y `14`."""
    assert fichero.name in _seccion(_leer(INTEGRACION), "## 2 · La base de datos")


@pytest.mark.parametrize("valor", _catalogos_del_check())
def test_f036_r60_la_seccion_dos_explica_la_costura_del_discriminador(valor):
    """§2 · el `CHECK` de `catalogo` admite ya tres valores; F-036 solo escribe uno."""
    seccion = _normal(_seccion(_leer(INTEGRACION), "## 2 · La base de datos"))

    assert valor in seccion
    for texto in ("catalogo", "F-050", "F-039", "append-only", "solo escribe oficio"):
        assert texto in seccion, f"§2 no dice «{texto}»"


def test_f036_r60_la_seccion_dos_dice_que_no_se_guarda_ningun_binario():
    """§2 · ni el `.xlsx` ni el Excel de errores entran en la base."""
    seccion = _normal(_seccion(_leer(INTEGRACION), "## 2 · La base de datos"))

    assert "ni el .xlsx ni el Excel de errores" in seccion


def test_f036_r49_la_seccion_cuatro_dice_que_no_hay_variables_nuevas():
    """§4 · R49: las rutas nuevas no añaden ninguna variable de entorno."""
    seccion = _normal(_seccion(_leer(INTEGRACION), "## 4 · Variables de entorno"))

    assert "F-036 no añade ninguna variable de entorno" in seccion


def test_f036_r60_la_seccion_seis_dice_que_se_rompe_con_f036():
    """§6 · qué se rompe aquí si la pasarela cambia o Sigrid cambia un oficio."""
    seccion = _normal(_seccion(_leer(INTEGRACION), "## 6 · Qué se rompe"))

    for texto in ("F-036", "catalogo_sin_verificar", "vuelven con error"):
        assert texto in seccion, f"§6 no dice «{texto}»"


def test_f036_r60_la_seccion_siete_dice_los_datos_personales_nuevos():
    """§7 · R47: texto libre de la propiedad y nombres de proveedor, fuera de los logs."""
    seccion = _normal(_seccion(_leer(INTEGRACION), "## 7 · Datos personales"))

    for texto in (
        "F-036",
        "texto libre de la propiedad",
        "descripcion",
        "detalle",
        "proveedor_nombre",
        "autónomo",
        "nombre_fichero",
        "importado_por",
        "decidido_por",
        "no sale en ningún log",
        "GET /api/bandeja",
    ):
        assert texto in seccion, f"§7 no dice «{texto}»"


@pytest.mark.parametrize(("metodo", "ruta"), ENDPOINTS_DE_F036, ids=lambda x: str(x))
def test_f036_r60_la_tabla_de_la_seccion_ocho_declara_cada_endpoint(metodo, ruta):
    """§8 · cada ruta de F-036 es una fila de la tabla de endpoints."""
    tabla = _seccion(_leer(INTEGRACION), "### Los endpoints, y qué hace cada uno")

    assert _fila(tabla, f"| `{metodo} /api/{ruta}`")


def test_f036_r60_la_seccion_ocho_dice_que_hace_cada_endpoint():
    """§8 · lo que escribe cada una, dónde, y que ninguna toca Sigrid."""
    seccion = _normal(_seccion(_leer(INTEGRACION), "## 8 · Qué exponemos nosotros"))

    for texto in (
        "Excel de errores",
        "postventa.importaciones",
        "postventa.bandeja_incidencias",
        "postventa.decisiones_equivalencia",
        "confirmado: true",
        "tope duro de 500",
        "solo el catálogo oficio",
        "Los cinco endpoints de F-036 no dependen de ARCHIVO_HABILITADO ni de CIERRE_HABILITADO",
    ):
        assert texto in seccion, f"§8 no dice «{texto}»"


@pytest.mark.parametrize("pagina", PAGINAS_DE_F036)
def test_f036_r60_la_seccion_ocho_nombra_las_paginas_nuevas(pagina):
    """§8 · lo que se expone a las personas: dos páginas más del front."""
    assert pagina in _seccion(_leer(INTEGRACION), "## 8 · Qué exponemos nosotros")


def test_f036_r60_la_seccion_ocho_dice_que_f036_no_esta_desplegada():
    """§8 · «Qué NO está desplegado»: F-036, con su consecuencia visible."""
    tabla = _normal(_seccion(_leer(INTEGRACION), "### Qué NO está desplegado"))

    assert "F-036" in tabla
    assert "no crea ninguna incidencia en Sigrid" in tabla


@pytest.mark.parametrize("dependencia", DEPENDENCIAS_DE_F036)
def test_f036_r60_integracion_nombra_las_dependencias_nuevas(dependencia):
    """El despliegue las instala en la compilación remota: quien despliega lo lee aquí."""
    assert dependencia in _leer(INTEGRACION)


def test_f036_r60_integracion_dice_lo_que_queda_fuera():
    """Actividades (F-039) y agrupación de proveedores (F-050), con nombre."""
    texto = _normal(_leer(INTEGRACION))

    assert "las actividades del proveedor" in texto
    assert "agrupar los proveedores casi duplicados" in texto


@pytest.mark.parametrize(
    ("seccion", "titulo"),
    (
        ("§1", "## 1 · Qué consumimos hoy"),
        ("§2", "## 2 · La base de datos"),
        ("§9", "## 9 · Dónde está cada cosa"),
    ),
)
def test_f036_r60_integracion_lleva_a_la_spec(seccion, titulo):
    """El detalle vive en la spec; el documento del ecosistema apunta allí."""
    assert "specs/F-036-importar-excel/" in _seccion(_leer(INTEGRACION), titulo), (
        seccion
    )


# --------------------------------------------------------------------------
# R61 · ARCHITECTURE.md
# --------------------------------------------------------------------------

TITULO_DE_LA_ENTRADA = "## Entrada de incidencias (F-036)"


@pytest.fixture
def entrada() -> str:
    return _seccion(_leer(ARQUITECTURA), TITULO_DE_LA_ENTRADA)


def test_f036_r61_la_arquitectura_tiene_la_seccion_de_la_entrada(entrada):
    assert len(_normal(entrada)) > 2000


def test_f036_r61_describe_la_via_de_entrada(entrada):
    """Plantilla → importación → bandeja, con el Excel de errores."""
    texto = _normal(entrada)

    for texto_esperado in (
        "plantilla → importación → bandeja",
        "Excel de errores",
        "comparación exacta",
        "completa",
        "parcial",
        "ya_importado",
        "duplicada",
        "oficio_ambiguo",
        "sha256",
        "no se guarda",
    ):
        assert texto_esperado in texto, f"la sección no dice «{texto_esperado}»"


def test_f036_r61_describe_la_agrupacion_de_oficios(entrada):
    """Propuesta automática, confirmación humana, append-only, sin tocar Sigrid."""
    texto = _normal(entrada)

    for texto_esperado in (
        "oficios casi duplicados",
        "propone",
        "una persona",
        "postventa.decisiones_equivalencia",
        "append-only",
        "manda la última",
        "oficios.html",
    ):
        assert texto_esperado in texto, f"la sección no dice «{texto_esperado}»"


def test_f036_r61_dice_lo_que_no_hacen(entrada):
    """Lo que no hace ninguna de las dos piezas, y quién lo hará."""
    texto = _normal(entrada)

    for texto_esperado in (
        "Nada de F-036 escribe en Sigrid",
        "F-038",
        "F-040",
        "F-037",
        "F-039",
        "F-050",
        "las actividades del proveedor",
        "agrupar los proveedores casi duplicados",
    ):
        assert texto_esperado in texto, f"la sección no dice «{texto_esperado}»"


@pytest.mark.parametrize("dependencia", DEPENDENCIAS_DE_F036)
def test_f036_r61_nombra_las_dependencias_nuevas(entrada, dependencia):
    assert dependencia in entrada


@pytest.mark.parametrize("pagina", PAGINAS_DE_F036)
def test_f036_r61_nombra_las_paginas_nuevas(entrada, pagina):
    assert pagina in entrada


def test_f036_r61_lleva_a_la_spec_y_a_integracion(entrada):
    assert "specs/F-036-importar-excel/" in entrada
    assert "docs/INTEGRACION.md" in entrada


def test_f036_r61_la_seccion_esta_antes_del_acceso_a_datos():
    """Va con el dominio, antes de la tabla de sistemas externos que la cita."""
    texto = _leer(ARQUITECTURA)

    assert texto.index(TITULO_DE_LA_ENTRADA) < texto.index(
        "## Acceso a datos y sistemas externos"
    )


def test_f036_r61_la_fila_de_sigrid_api_nombra_las_lecturas_del_catalogo():
    """La tabla de sistemas: `sigrid-api` gana las dos lecturas, sin ventana."""
    fila = _normal(_fila(_leer(ARQUITECTURA), "| `sigrid-api` |"))

    assert "F-036" in fila
    assert "dos lecturas" in fila
    assert "sin CIERRE_HABILITADO" in fila


def test_f036_r61_la_fila_de_postgresql_nombra_las_tablas_nuevas():
    """La tabla de sistemas: el PostgreSQL gana la bandeja y las decisiones."""
    fila = _normal(_fila(_leer(ARQUITECTURA), "| PostgreSQL `psql-albaranes-rs9k2` |"))

    assert "F-036" in fila
    for tabla in _tablas_del_ddl():
        assert tabla in fila, f"la fila de PostgreSQL no nombra «{tabla}»"


def test_f036_r61_la_seccion_nueva_no_lleva_valores(entrada):
    """El barrido de `test_f005` no mira la arquitectura: se le pasa esta sección."""
    assert hallazgos(entrada) == {}


# --------------------------------------------------------------------------
# Lo retirado por la quinta enmienda no vuelve como si estuviera hecho
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "documento", (INTEGRACION, ARQUITECTURA), ids=lambda ruta: ruta.name
)
@pytest.mark.parametrize("retirado", RETIRADO_DE_F036)
def test_f036_t26_ningun_documento_describe_lo_retirado(documento, retirado):
    """La documentación describe lo implementado, no el borrador de la spec."""
    assert retirado not in _leer(documento)


@pytest.mark.parametrize(
    "documento",
    (
        "Tabla nueva postventa.decisiones_proveedor, con DENSE_RANK sobre el CIF.",
        "La página catalogos.html y /api/proveedores/decisiones.",
    ),
    ids=("tabla-y-cif", "pagina-y-ruta"),
)
def test_f036_t26_el_control_de_lo_retirado_caza(documento):
    """Control negativo: el barrido de arriba salta con lo que tiene que saltar."""
    assert any(retirado in documento for retirado in RETIRADO_DE_F036)


# --------------------------------------------------------------------------
# T44 · La lectura aislada (R118–R120, octava enmienda): lo que cambia hacia
# fuera. Los números se leen del código, no se copian.
# --------------------------------------------------------------------------

MIB = 1024 * 1024


def _topes_de_la_lectura_aislada() -> tuple[str, ...]:
    """Los topes de la lectura aislada como los escribe la documentación."""
    assert lector_aislado.BYTES_MEMORIA_HIJO == 1024 * MIB
    return (
        f"{lector_aislado.SEGUNDOS_HIJO} s",
        "1 GiB",
        f"{lector_aislado.MAX_BYTES_DESCOMPRIMIDOS // MIB} MiB",
        f"{lector_aislado.MAX_BYTES_RESULTADO // MIB} MiB",
        f"{lector_aislado.PRESUPUESTO_ELEMENTOS_XML:,}".replace(",", "."),
        f"{lector_aislado.SEGUNDOS_ESPERA_LECTURA} s",
    )


def test_f036_t44_los_topes_se_leen_del_codigo():
    """Un control que no lee nada da verde para siempre: se fija lo que lee."""
    assert _topes_de_la_lectura_aislada() == (
        "30 s",
        "1 GiB",
        "17 MiB",
        "11 MiB",
        "300.000",
        "5 s",
    )


@pytest.fixture
def lectura_aislada() -> str:
    return _seccion(_leer(ARQUITECTURA), "### La lectura aislada en un proceso hijo")


def test_f036_t44_la_lectura_aislada_va_dentro_de_la_entrada(entrada, lectura_aislada):
    assert lectura_aislada in entrada


def test_f036_t44_la_arquitectura_dice_los_topes_de_la_lectura_aislada(lectura_aislada):
    texto = _normal(lectura_aislada)

    for tope in _topes_de_la_lectura_aislada():
        assert tope in texto, f"la sección no dice el tope «{tope}»"


def test_f036_t44_la_arquitectura_describe_la_lectura_aislada(lectura_aislada):
    """Qué corre dónde, qué responde y qué exige: R118, R119 y R120."""
    texto = _normal(lectura_aislada)

    for texto_esperado in (
        "proceso hijo",
        "El padre no abre nunca el libro",
        "lector_aislado.py",
        "fichero_sospechoso",
        "JSON",
        "forkserver",
        "spawn",
        "setrlimit(RLIMIT_AS)",
        "503",
        "LectorSinAislamiento",
        "LecturaOcupada",
        "Una lectura aislada a la vez por proceso",
        "2.048 MB",
        "102 MiB",
        "docs/INTEGRACION.md §6",
    ):
        assert texto_esperado in texto, f"la sección no dice «{texto_esperado}»"


def test_f036_t45_la_arquitectura_dice_el_tope_de_cpu_del_hijo(lectura_aislada):
    """R119 con la novena enmienda: el tope de CPU, para el padre muerto."""
    texto = _normal(lectura_aislada)

    for texto_esperado in (
        "tope de CPU",
        "setrlimit(RLIMIT_CPU)",
        "sus segundos más 5",
        "35 s",
        "cuenta CPU, no reloj",
        "padre muerto",
    ):
        assert texto_esperado in texto, f"la sección no dice «{texto_esperado}»"


def test_f036_t44_la_arquitectura_nombra_los_modulos_nuevos(entrada):
    texto = _normal(_seccion(entrada, "### Dónde vive cada pieza"))

    assert "lector_aislado.py" in texto
    assert "ejecutor_aislado.py" in texto


def test_f036_t44_integracion_dice_que_rompe_la_importacion():
    """§6: la instancia de 2.048 MB, una lectura a la vez y los 503 nuevos."""
    seccion = _seccion(_leer(INTEGRACION), "## 6 · Qué se rompe")
    texto = _normal(seccion)

    for texto_esperado in (
        "Baja la memoria de la instancia",
        "2.048 MB",
        "--instance-memory",
        "1 GiB",
        "FUNCTIONS_WORKER_PROCESS_COUNT",
        "una lectura aislada a la vez",
        "otra importación en curso; reintenta",
        "setrlimit",
        "503",
        "D-31",
    ):
        assert texto_esperado in texto, f"§6 no dice «{texto_esperado}»"
    assert hallazgos(seccion) == {}


def test_f036_t44_la_fila_de_importaciones_dice_la_lectura_aislada():
    tabla = _seccion(_leer(INTEGRACION), "### Los endpoints, y qué hace cada uno")
    fila = _normal(_fila(tabla, "| `POST /api/importaciones` |"))

    assert "proceso hijo" in fila
    assert "fichero_sospechoso" in fila
    assert "503" in fila
