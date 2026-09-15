# services/postventa-api/tests/test_f012_scripts_infra.py
"""Los tres scripts de verificación de F-012 cumplen su contrato (T22–T24).

Al modo de `test_f009_scripts_infra.py`: son PowerShell y no entran ni en la
cobertura ni en la campaña de mutación —`harness/alcance.py` solo mide `.py`—,
así que su contrato se comprueba leyéndolos desde un test de Python, igual que
el DDL en `.sql` se comprueba desde `test_f005_ddl_seguro.py`.

Lo que se fija, y por qué cada cosa:

- **La regla dura de `CLAUDE.md`**: estos tres **no escriben en Sigrid**. Ni
  una sentencia. Sus llamadas al ERP son lecturas, y las sirve un usuario SQL
  de solo lectura.
- **El binario del parte no se saca a una consola** (R45, R53). La columna
  `ima` de la base documental es el PDF con el DNI manuscrito del cliente
  dentro: se pide su `DATALENGTH`, nunca la columna.
- **Los estados van por código, nunca por número** (`CHECKPOINTS.md` C3).
- **Ningún valor**: ni la raíz de la pasarela, ni la clave, ni un código de
  reclamación real, ni un login. Estos ficheros **sí** se versionan y el
  historial de git no suelta lo que entra.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Raíz del repositorio, tres niveles por encima de este fichero.
RAIZ = Path(__file__).resolve().parent.parent.parent.parent
INFRA = RAIZ / "infra"

#: T22 · localiza las reclamaciones candidatas de la obra de prueba.
SCRIPT_OBRA = INFRA / "15_reclamaciones_obra_prueba.ps1"

#: T23 · las tres filas del gráfico en el ERP, y el `MAX(ide)` de `dbo.log`.
SCRIPT_GRAFICO = INFRA / "16_grafico_sigrid.ps1"

#: T24 · la traza propia en `postventa.graficos`.
SCRIPT_TRAZA = INFRA / "17_traza_grafico_local.ps1"

LOS_TRES = (SCRIPT_OBRA, SCRIPT_GRAFICO, SCRIPT_TRAZA)

#: Los dos que hablan con la pasarela.
CONTRA_LA_PASARELA = (SCRIPT_OBRA, SCRIPT_GRAFICO)

#: Verbos que escribirían en el ERP. Ninguno puede aparecer.
VERBOS_DE_ESCRITURA_EN_SIGRID = (
    "INSERT INTO dbo.",
    "UPDATE dbo.",
    "DELETE FROM dbo.",
)

#: Verbos que escribirían en PostgreSQL.
VERBOS_DE_ESCRITURA_EN_PG = ("INSERT INTO", "UPDATE ", "DELETE FROM", "ALTER ", "DROP ")

#: La forma de un GUID: así se escriben el `oid` de Entra y los identificadores
#: de suscripción y de inquilino de Azure. Ninguno entra en el repositorio.
PATRON_GUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

#: Una credencial escrita a mano en el propio fichero.
PATRON_CREDENCIAL_LITERAL = re.compile(
    r"(?:password|contrasena|contraseña|pwd|key)\s*=\s*[\"'][^\"'$)]{4,}[\"']",
    re.IGNORECASE,
)

#: Un nombre de host real: ni el del PostgreSQL compartido ni el de la pasarela.
PATRON_HOST_AZURE = re.compile(
    r"[\w-]+\.(?:postgres\.database|azurewebsites)\.(?:azure\.com|net)",
    re.IGNORECASE,
)

#: Un código de reclamación real, con la forma que usa Sigrid.
PATRON_INCIDENCIA_REAL = re.compile(r"\bRS\d{2}\.\d{2}/\d{4}\b")

#: Un `sha256` de verdad pegado en el fichero.
PATRON_SHA256 = re.compile(r"\b[0-9a-f]{64}\b", re.IGNORECASE)


def _texto(script: Path) -> str:
    return script.read_text(encoding="utf-8")


def _sin_ayuda(texto: str) -> str:
    """El script sin su bloque de ayuda `<# ... #>`.

    Hace falta porque la ayuda de estos scripts explica **por qué** no escriben
    en Sigrid y por qué no se saca el binario, y buscar en el texto crudo daría
    por rotas las reglas que el propio comentario está defendiendo.
    """
    return re.sub(r"<#.*?#>", "", texto, flags=re.DOTALL)


# --------------------------------------------------------------------------
# Existen, y son ASCII y con su ruta
# --------------------------------------------------------------------------


@pytest.mark.parametrize("script", LOS_TRES, ids=lambda ruta: ruta.name)
def test_f012_los_tres_scripts_existen(script):
    """Sin ellos, el bloque 9 se haría a mano contra el ERP de producción.

    Que es exactamente como se cometen los errores que este bloque viene a
    evitar: mirar una fila, creer que dice lo que uno espera, y seguir.
    """
    assert script.is_file()


@pytest.mark.parametrize("script", LOS_TRES, ids=lambda ruta: ruta.name)
def test_f012_cada_script_empieza_por_su_ruta_relativa(script):
    """`docs/CONVENTIONS.md`: primera línea, la ruta del fichero."""
    primera = _texto(script).splitlines()[0]

    assert primera == f"# infra/{script.name}"


@pytest.mark.parametrize("script", LOS_TRES, ids=lambda ruta: ruta.name)
def test_f012_cada_script_es_ascii_puro(script):
    """Como los de F-009 y F-010, y por lo mismo: PowerShell 5.1 en consolas
    con la página de códigos por defecto convierte un acento en dos caracteres
    raros, y un mensaje ilegible en mitad de una verificación contra el ERP es
    lo último que hace falta."""
    assert all(byte < 128 for byte in script.read_bytes())


@pytest.mark.parametrize("script", LOS_TRES, ids=lambda ruta: ruta.name)
def test_f012_cada_script_tiene_ayuda_con_ejemplos(script):
    """Se ejecutan una vez cada varios meses, con el ERP delante.

    Sin `.EXAMPLE` hay que leer el `param()` para saber cómo llamarlos, y ese
    es el momento en que alguien lo llama con el parámetro equivocado.
    """
    texto = _texto(script)

    assert ".SYNOPSIS" in texto
    assert ".DESCRIPTION" in texto
    assert texto.count(".EXAMPLE") >= 1


# --------------------------------------------------------------------------
# La regla dura: ninguno escribe en Sigrid
# --------------------------------------------------------------------------


@pytest.mark.parametrize("script", LOS_TRES, ids=lambda ruta: ruta.name)
def test_f012_ningun_script_escribe_jamas_en_sigrid(script):
    """`CLAUDE.md`, regla dura: en Sigrid solo se escribe desde el desplegado.

    Y estos los ejecuta una persona desde su puesto. Sus llamadas al ERP son
    lecturas, y las sirve el usuario de solo lectura de la pasarela.
    """
    ejecutable = _sin_ayuda(_texto(script)).upper()

    for verbo in VERBOS_DE_ESCRITURA_EN_SIGRID:
        assert verbo.upper() not in ejecutable


@pytest.mark.parametrize("script", CONTRA_LA_PASARELA, ids=lambda ruta: ruta.name)
def test_f012_las_llamadas_al_erp_son_todas_de_lectura(script):
    """Se comprueba por la **ruta** y no solo por el verbo.

    Es la diferencia que se ve de un vistazo al revisar el script, y la que un
    `SELECT` bien escrito dentro de una llamada a `sql/write` no delataría.
    """
    ejecutable = _sin_ayuda(_texto(script))

    assert "/api/sql/write" not in ejecutable
    assert "sigrid/concepto-grafico" not in ejecutable


@pytest.mark.parametrize("script", CONTRA_LA_PASARELA, ids=lambda ruta: ruta.name)
def test_f012_las_consultas_al_erp_van_parametrizadas(script):
    """`sigrid_api.md` §5.2 · marcadores `?`, nunca concatenación.

    Un código concatenado en la cadena sería una inyección contra el ERP de
    producción, lanzada desde un puesto de trabajo.
    """
    ejecutable = _sin_ayuda(_texto(script))

    assert "-Parametros" in ejecutable
    assert "= ?" in ejecutable or "IN (?" in ejecutable


@pytest.mark.parametrize("script", CONTRA_LA_PASARELA, ids=lambda ruta: ruta.name)
def test_f012_cada_script_carga_el_comun_de_lectura(script):
    """Cambiar cómo se llama a la pasarela es cambiar **un** fichero.

    Cuatro copias del manejo de la clave y del formato del veredicto serían
    cuatro cosas que comparar a mano cuando una de ellas deje de coincidir.
    """
    assert '. "$PSScriptRoot\\08_lectura_sigrid_comun.ps1"' in _texto(script)


# --------------------------------------------------------------------------
# T23 · el binario del parte NO sale a la consola de nadie
# --------------------------------------------------------------------------


def test_f012_r45_la_consulta_documental_pide_datalength_y_nunca_el_binario():
    """R45, R53 · **lo más importante de este script.**

    `gra.ima` de la base documental es el PDF del parte, con el DNI manuscrito
    del cliente dentro. Traérselo a una consola para mirar un número sería
    sacar un dato personal de producción sin ningún motivo. Lo que hace falta
    es su tamaño, y eso es lo que se pide.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_GRAFICO))

    assert "DATALENGTH(g.ima)" in ejecutable

    # **Todas** las apariciones de la columna, una a una: solo valen dentro de
    # `DATALENGTH(...)` —su tamaño— o de un `IS NULL` —si hay binario o no—.
    # Cualquier otra la traería a la consola. Se enumeran en vez de buscar un
    # patrón negativo porque así el fallo dice **cuál** es la que sobra.
    apariciones = [
        ejecutable[max(0, encontrada.start() - 12) : encontrada.end() + 9]
        for encontrada in re.finditer(r"\bg\.ima\b", ejecutable)
    ]

    assert apariciones, "el script ya no mira la columna binaria"
    for contexto in apariciones:
        assert (
            "DATALENGTH(g.ima)" in contexto or "g.ima IS NULL" in contexto
        ), f"la columna binaria sale sin acotar: ...{contexto}..."


def test_f012_la_descarga_del_binario_es_opcional_y_no_toca_el_disco():
    """El único camino que trae el PDF es un modificador, no lo normal.

    Y lo que trae **no se escribe en disco**: se calcula el hash en memoria y
    se descarta. Un fichero con el DNI de un cliente en la carpeta de descargas
    de alguien es exactamente lo que no puede quedar suelto.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_GRAFICO))

    assert "[switch]$DescargarYComparar" in ejecutable
    assert "documents/read" in ejecutable
    # Nada de escribir el contenido a un fichero.
    for prohibido in ("Out-File", "Set-Content", "WriteAllBytes", "-OutFile"):
        assert prohibido not in ejecutable


def test_f012_la_descarga_exige_algo_con_que_comparar():
    """Descargar sin comparar no comprueba nada, y sí saca el PDF de
    producción. El script se niega."""
    ejecutable = _sin_ayuda(_texto(SCRIPT_GRAFICO))

    assert "$Sha256Esperado" in ejecutable
    assert "Descargar sin nada con que comparar" in ejecutable


def test_f012_la_casilla_de_bytes_mide_el_contenido_y_no_la_huella():
    """«bytes descargados» tiene que decir cuánto pesa el PDF, no siempre 64.

    `$huella` es la **cadena hexadecimal** del sha256: su `.Length` vale 64
    mida lo que mida el binario, así que anotarla ahí es un número que parece
    un tamaño y no lo es. No era un falso verde —lo que sostiene el bloque es
    la comprobación del sha256 de la línea siguiente— pero sí ruido que
    confunde a quien lee la salida delante del ERP de producción.

    Y el tamaño hay que capturarlo **antes** de soltar `$respuesta`: el script
    lo pone a `$null` en cuanto ha calculado el hash, a propósito, para que
    nada del PDF sobreviva. Leerlo después anotaría un vacío.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_GRAFICO))

    casilla = re.search(
        r'Anotar -Que "bytes descargados" -Valor (\$[\w.]+)', ejecutable
    )
    assert casilla, "no está la casilla «bytes descargados» del bloque de descarga"

    medida = casilla.group(1)
    assert medida != "$huella.Length", (
        "«bytes descargados» está imprimiendo la longitud de la cadena del "
        "sha256, que es siempre 64, en vez del tamaño del binario descargado"
    )

    asignacion = re.search(
        re.escape(medida) + r"\s*=\s*\$respuesta\.Content\.Length", ejecutable
    )
    assert asignacion, (
        f"{medida} no se calcula desde $respuesta.Content.Length, que es lo "
        "único que mide de verdad lo descargado"
    )

    soltar = ejecutable.index("$respuesta = $null")
    assert asignacion.start() < soltar, (
        "el tamaño se lee después de soltar $respuesta, así que la casilla "
        "saldría vacía"
    )


def test_f012_r36_el_script_mira_el_max_ide_de_dbo_log():
    """R36 · el gráfico **no escribe ninguna fila de auditoría**.

    El propio ERP tampoco lo hace al importar un documento (0 filas con
    `tab='gra'` en 8,4 millones). Compararlo antes y después es la única forma
    de comprobarlo, y por eso el script lo lee siempre, no solo cuando se le
    pide.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_GRAFICO))

    assert "MAX(ide) AS max_ide FROM dbo.log" in ejecutable
    assert "$MaxIdeLogEsperado" in ejecutable


def test_f012_el_script_comprueba_las_tres_filas_y_no_solo_una():
    """Un gráfico son **tres filas en dos bases**: si solo se mirara la de
    negocio, un binario que no se escribió pasaría por bueno."""
    ejecutable = _sin_ayuda(_texto(SCRIPT_GRAFICO))

    assert "base de NEGOCIO" in ejecutable
    assert "base DOCUMENTAL" in ejecutable
    assert "ENLACE en rcg" in ejecutable
    assert "emp igual en las dos bases" in ejecutable


def test_f012_r44_el_script_no_imprime_el_login_por_separado():
    """R44 · el login va dentro de `gra.cod`, y ahí se queda.

    Sacarlo a una columna propia del informe sería publicar la identidad de una
    persona en la consola de otra, para nada.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_GRAFICO))

    assert "El login NO se imprime suelto" in ejecutable
    assert 'Columna "usu"' not in ejecutable


# --------------------------------------------------------------------------
# T22 · la obra de prueba, y los estados por código
# --------------------------------------------------------------------------


def test_f012_el_script_de_la_obra_prueba_las_dos_formas_del_codigo():
    """`con.cod` puede llevar ceros a la izquierda, y **no está medido**.

    Suponer una forma y volver con las manos vacías mandaría a alguien a
    buscar en Sigrid una obra que sí existe.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_OBRA))

    assert "PadLeft(4" in ejecutable
    assert "WHERE c.cod IN (?, ?)" in ejecutable


def test_f012_el_script_de_la_obra_para_si_no_hay_exactamente_una():
    """Con dos obras del mismo código no se elige una por nuestra cuenta:
    cuál es la de prueba lo dice Posventa."""
    ejecutable = _sin_ayuda(_texto(SCRIPT_OBRA))

    assert "row_count -eq 0" in ejecutable
    assert "row_count -gt 1" in ejecutable


def test_f012_c3_los_estados_cerrables_van_por_codigo_y_nunca_por_numero():
    """`CHECKPOINTS.md` C3 · `con.est` es un entero **configurable por
    instalación**.

    Filtrar por número aquí produciría un listado de candidatas que parece
    correcto y no lo es — y sobre él se elegiría la reclamación con la que se
    escribe en el ERP.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_OBRA))

    assert 'CodigosCerrables = @("SAT", "PTE", "TER")' in ejecutable
    assert "e.cod IN (?, ?, ?)" in ejecutable
    assert "c.est =" not in ejecutable


def test_f012_las_candidatas_son_las_que_no_tienen_grafico():
    """Sobre una reclamación que ya tiene gráfico no se puede distinguir el que
    escribimos nosotros del que ya estaba."""
    ejecutable = _sin_ayuda(_texto(SCRIPT_OBRA))

    assert "NOT EXISTS (SELECT 1 FROM dbo.rcg r WHERE r.con = c.ide)" in ejecutable


def test_f012_el_script_no_da_de_alta_ninguna_reclamacion():
    """Fuera del dominio de este servicio, y el script lo dice en vez de
    dejar a quien lo lea preguntándose qué hacer."""
    texto = _texto(SCRIPT_OBRA)

    assert "no da de alta reclamaciones" in texto
    assert "POSVENTA" in texto


# --------------------------------------------------------------------------
# T24 · la traza local, solo lectura y solo del esquema propio
# --------------------------------------------------------------------------


def test_f012_la_traza_local_solo_lee_y_solo_del_esquema_propio():
    """`CLAUDE.md`, regla dura: fuera del esquema propio no se toca nada.

    El servidor lo comparten albaranes, partes y el datamart.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_TRAZA)).upper()

    for verbo in VERBOS_DE_ESCRITURA_EN_PG:
        assert verbo.upper() not in ejecutable
    assert "{ESQUEMA}.GRAFICOS" in ejecutable
    assert "PUBLIC." not in ejecutable


def test_f012_el_nombre_del_esquema_se_valida_antes_de_pegarlo_al_sql():
    """Es lo único que se interpola, así que es lo único que hay que validar.

    Un `-Esquema` hostil sería una inyección con permisos de despliegue contra
    un servidor compartido. Misma regla que
    `infrastructure/persistencia/ddl.py`.
    """
    assert "isalnum" in _sin_ayuda(_texto(SCRIPT_TRAZA))


def test_f012_r44_la_traza_local_distingue_el_login_dentro_y_fuera_del_cod():
    """R44 · **la excepción declarada, comprobada de verdad.**

    El login **puede** estar dentro de `gra_cod` —lo genera Sigrid así— y **no
    puede** estar en ninguna otra columna. Un control que solo mirara «aparece
    o no aparece» daría por roto el caso correcto, y uno que ignorara el
    `gra_cod` no comprobaría nada.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_TRAZA))

    assert "login_fuera_del_cod" in ejecutable
    assert "login_dentro_del_cod" in ejecutable
    assert "$LoginQueNoDebeAparecer" in ejecutable


def test_f012_r44_el_oid_no_se_imprime_nunca():
    """R44 · dato personal seudónimo. Se dice **si está**, que es lo único que
    hace falta para el veredicto."""
    ejecutable = _sin_ayuda(_texto(SCRIPT_TRAZA))

    assert "hay_oid" in ejecutable
    assert "El oid NO se imprime" in ejecutable
    assert "confirmado_por IS NOT NULL" in ejecutable


def test_f012_r43_la_traza_local_exige_la_clave_estable_del_erp():
    """R43 · `reclamacion_ide` tiene que estar **ya en el dry-run**.

    Es la clave con la que el datamart cruzará nuestras filas. Si faltara, las
    trazas de dry-run y de error se quedarían sin ella y habría que hacer un
    `ALTER` mañana.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_TRAZA))

    assert "reclamacion_ide relleno (R43)" in ejecutable


def test_f012_r25_la_traza_local_comprueba_si_fue_idempotente():
    """R25 · distingue un gráfico que **escribimos** de uno que **ya estaba**.

    Es la diferencia entre una escritura en producción y ninguna, y es lo que
    T28 del bloque 9 verifica.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_TRAZA))

    assert "$IdempotenteEsperado" in ejecutable
    assert "idempotente (R25)" in ejecutable


def test_f012_las_credenciales_se_piden_por_consola_y_no_se_escriben():
    """Contraseña de PostgreSQL: `SecureString`, y solo en memoria.

    Y las variables de entorno temporales se borran pase lo que pase: la sesión
    tiene que quedar como estaba.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_TRAZA))

    assert "-AsSecureString" in ejecutable
    assert "Remove-Item" in ejecutable


def test_f012_el_estado_esperado_se_valida_contra_los_cinco_del_dominio():
    """Un `-EstadoEsperado` con una errata pasaría como «no coincide» y mandaría
    a mirar el ERP para nada. `ValidateSet` lo caza en el parámetro."""
    from domain.models.persistencia import EstadoGrafico

    ejecutable = _sin_ayuda(_texto(SCRIPT_TRAZA))

    for estado in EstadoGrafico:
        assert f'"{estado.value}"' in ejecutable


# --------------------------------------------------------------------------
# Ningún valor, en ninguno de los tres
# --------------------------------------------------------------------------


@pytest.mark.parametrize("script", LOS_TRES, ids=lambda ruta: ruta.name)
def test_f012_ningun_script_trae_una_credencial(script):
    """Estos ficheros **sí** se versionan, y el historial de git no suelta lo
    que entra."""
    assert PATRON_CREDENCIAL_LITERAL.search(_texto(script)) is None


@pytest.mark.parametrize("script", LOS_TRES, ids=lambda ruta: ruta.name)
def test_f012_ningun_script_trae_un_host_ni_un_identificador(script):
    """Ni el host de la pasarela, ni el del PostgreSQL compartido, ni un `oid`.

    Un ejemplo «para que se entienda mejor» es exactamente como acaba un
    identificador real en un repositorio.
    """
    texto = _texto(script)

    assert PATRON_HOST_AZURE.findall(texto) == []
    assert PATRON_GUID.findall(texto) == []


@pytest.mark.parametrize("script", LOS_TRES, ids=lambda ruta: ruta.name)
def test_f012_ningun_script_trae_un_codigo_de_incidencia_real(script):
    """Los ejemplos van con marcadores. Una incidencia real identifica una
    vivienda y a su propietario."""
    assert PATRON_INCIDENCIA_REAL.findall(_texto(script)) == []


@pytest.mark.parametrize("script", LOS_TRES, ids=lambda ruta: ruta.name)
def test_f012_ningun_script_trae_un_sha256_pegado(script):
    """El `sha256` de un parte identifica un documento con datos personales
    dentro. Entra por parámetro, no escrito en el fichero."""
    assert PATRON_SHA256.findall(_texto(script)) == []


def test_f012_la_obra_de_prueba_es_el_unico_valor_por_defecto_del_script():
    """La obra de prueba **sí** puede estar: no identifica a ningún cliente y
    es la que Ruesma usa para probar. Que sea el valor por defecto es lo que
    impide que alguien apunte a Mirasierra por descuido."""
    ejecutable = _sin_ayuda(_texto(SCRIPT_OBRA))

    assert '[string]$CodigoObra = "404"' in ejecutable


# --------------------------------------------------------------------------
# El utillaje de puesta en marcha del bloque 9: `19_ventana_escritura.ps1` y
# `20_login_sigrid.ps1`
# --------------------------------------------------------------------------
#
# No son de T22–T24: son las dos operaciones que hasta hoy vivían como
# **fragmentos sueltos dentro de un documento** —una línea de `az` copiada a
# mano en el paso 3 de T25 y en T32, y la comprobación del login que no estaba
# escrita en ninguna parte—. Un comando que se copia de un Markdown no tiene
# precondiciones, ni veredicto, ni código de salida, y el del paso 3 de T25 es
# **el más delicado del bloque**: abre la ventana de escritura contra el ERP de
# producción.
#
# Sus comprobaciones viven aquí, con las de los otros tres de F-012, y además
# entran en el censo `scripts_entregados()` de `test_f010_scripts_infra.py`,
# que es donde está el barrido de «ni un nombre de recurso, ni un valor».

#: Abre, cierra y consulta la ventana de escritura contra el ERP.
SCRIPT_VENTANA = INFRA / "19_ventana_escritura.ps1"

#: Comprueba el login del ERP que se derivaría de un correo. Solo lee.
SCRIPT_LOGIN = INFRA / "20_login_sigrid.ps1"

LOS_DOS_DEL_UTILLAJE = (SCRIPT_VENTANA, SCRIPT_LOGIN)


@pytest.mark.parametrize("script", LOS_DOS_DEL_UTILLAJE, ids=lambda ruta: ruta.name)
def test_f012_utillaje_los_dos_scripts_existen(script):
    """Sin ellos, las dos operaciones se hacen copiando de un Markdown."""
    assert script.is_file()


@pytest.mark.parametrize("script", LOS_DOS_DEL_UTILLAJE, ids=lambda ruta: ruta.name)
def test_f012_utillaje_cada_script_empieza_por_su_ruta_relativa(script):
    """`docs/CONVENTIONS.md`: primera línea, la ruta del fichero."""
    assert _texto(script).splitlines()[0] == f"# infra/{script.name}"


@pytest.mark.parametrize("script", LOS_DOS_DEL_UTILLAJE, ids=lambda ruta: ruta.name)
def test_f012_utillaje_cada_script_es_ascii_puro_y_sin_bom(script):
    """Igual que los otros cinco de `infra/`, y por lo mismo.

    Un acento en una consola con la página de códigos por defecto sale como dos
    caracteres raros, y el BOM lo escupiría PowerShell 5.1 en la primera línea.
    """
    crudo = script.read_bytes()

    assert all(byte < 128 for byte in crudo)
    assert not crudo.startswith(b"\xef\xbb\xbf")


@pytest.mark.parametrize("script", LOS_DOS_DEL_UTILLAJE, ids=lambda ruta: ruta.name)
def test_f012_utillaje_cada_script_va_en_crlf(script):
    """`docs/CONVENTIONS.md` · PowerShell del entorno de Ruesma: CRLF."""
    crudo = script.read_bytes()

    assert crudo.count(b"\n") > 0
    assert crudo.count(b"\r\n") == crudo.count(b"\n")


@pytest.mark.parametrize("script", LOS_DOS_DEL_UTILLAJE, ids=lambda ruta: ruta.name)
def test_f012_utillaje_cada_script_tiene_ayuda_con_parametros_y_ejemplos(script):
    """Se ejecutan con el ERP de producción delante y meses de por medio."""
    texto = _texto(script)

    assert ".SYNOPSIS" in texto
    assert ".DESCRIPTION" in texto
    assert ".PARAMETER" in texto
    assert texto.count(".EXAMPLE") >= 2


@pytest.mark.parametrize("script", LOS_DOS_DEL_UTILLAJE, ids=lambda ruta: ruta.name)
def test_f012_utillaje_cada_causa_de_fallo_tiene_su_codigo_y_ninguno_se_repite(script):
    """R5 de F-010 · un script que sale siempre con `1` obliga a leer la traza.

    `20_login_sigrid.ps1` los hereda de `08_lectura_sigrid_comun.ps1`, que es
    donde se declaran para que cuatro scripts no inventen cuatro numeraciones;
    `19_ventana_escritura.ps1` no carga ese común —no habla con la pasarela— y
    declara los suyos.
    """
    texto = _texto(script)
    propios = re.findall(r"^\$SALIDA_[A-Z_]+ = (\d+)$", texto, re.MULTILINE)

    if not propios:
        assert '. "$PSScriptRoot\\08_lectura_sigrid_comun.ps1"' in texto
        return

    assert len(propios) >= 4
    assert len(set(propios)) == len(propios)


@pytest.mark.parametrize("script", LOS_DOS_DEL_UTILLAJE, ids=lambda ruta: ruta.name)
def test_f012_utillaje_ningun_script_trae_un_valor(script):
    """Estos ficheros **sí** se versionan y el historial de git no suelta nada.

    Ni una credencial, ni un host, ni un `oid`, ni un código de reclamación
    real, ni un `sha256`. Y tampoco el login de una persona: el del ERP que no
    cumple la convención se describe, no se escribe.
    """
    texto = _texto(script)

    assert PATRON_CREDENCIAL_LITERAL.search(texto) is None
    assert PATRON_HOST_AZURE.findall(texto) == []
    assert PATRON_GUID.findall(texto) == []
    assert PATRON_INCIDENCIA_REAL.findall(texto) == []
    assert PATRON_SHA256.findall(texto) == []


def test_f012_utillaje_los_dos_entran_en_el_censo_de_los_scripts_de_infra():
    """El barrido de «ni un nombre de recurso (R7), ni un valor (R8)» vive en
    `test_f010_scripts_infra.py` y va por censo.

    Un script nuevo que no entre en el censo queda **fuera del barrido sin que
    se note**, que es exactamente como se cuela un nombre literal.
    """
    from tests.test_f010_scripts_infra import scripts_entregados

    censados = {ruta.name for ruta in scripts_entregados()}

    assert SCRIPT_VENTANA.name in censados
    assert SCRIPT_LOGIN.name in censados


# --------------------------------------------------------------------------
# `19_ventana_escritura.ps1` · la operación más delicada del bloque 9
# --------------------------------------------------------------------------


def test_f012_ventana_el_nombre_de_la_app_setting_va_en_una_constante():
    """Se escribe **una vez**, arriba y con nombre, no repartida por el script.

    Es el interruptor único de D-B: quien lea el script tiene que ver de un
    vistazo cuál es la App Setting que se está tocando.
    """
    texto = _texto(SCRIPT_VENTANA)

    assert '$APP_SETTING_VENTANA = "CIERRE_HABILITADO"' in texto
    assert texto.count('"CIERRE_HABILITADO"') == 1


def test_f012_ventana_los_nombres_de_recurso_salen_del_fichero_de_variables():
    """R7 · el grupo y la Function App **no se escriben aquí**.

    El paso 3 de T25 y el paso 1 de T32 los llevaban tecleados dentro del
    guion. Cambiar el nombre del recurso dejaría dos líneas de un Markdown
    apuntando a algo que ya no existe.
    """
    from tests.test_f010_scripts_infra import NOMBRES_DE_RECURSO

    texto = _texto(SCRIPT_VENTANA)

    assert '. "$PSScriptRoot\\00_vars_postventa.ps1"' in texto
    assert "$PostventaGrupo" in texto
    assert "$PostventaFunction" in texto
    assert [nombre for nombre in NOMBRES_DE_RECURSO if nombre in texto] == []


def test_f012_ventana_por_omision_solo_lee():
    """`-Estado` es el modo por defecto, y sale **antes** de tocar nada.

    Un script que abre la ventana de escritura contra el ERP si se lanza sin
    parámetros es una trampa. Lo que hace sin parámetros es mirar.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_VENTANA))

    assert "[switch]$Estado" in ejecutable
    salida_estado = ejecutable.index('if ($modo -eq "estado")')
    primera_escritura = ejecutable.index("Fijar-Ventana -Valor")

    assert salida_estado < primera_escritura


def test_f012_ventana_el_estado_se_dice_en_palabras():
    """«abierta» / «cerrada», no `true` / `false`.

    Quien lo lanza está decidiendo si el ERP de producción admite escrituras;
    tener que traducir un booleano en ese momento es una forma de equivocarse.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_VENTANA))

    assert "function En-Palabras" in ejecutable
    for palabra in ("abierta", "cerrada", "desconocida"):
        assert f'"{palabra}"' in ejecutable


def test_f012_ventana_abrir_avisa_y_exige_confirmacion_tecleada():
    """**El test central de este script.**

    La ventana es **una sola** para el gráfico y para el cierre (D-B de
    `design.md`, §0.2 del guion del bloque 9): abrirla habilita las **dos**
    escrituras contra el ERP. Eso no puede ser una sorpresa, así que se avisa
    **antes** de pedir la palabra, y la palabra se teclea, como en
    `cargar_secretos_postventa.ps1` y `desplegar_backend.ps1`.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_VENTANA))

    aviso = ejecutable.index("habilita las DOS escrituras contra el ERP")
    confirmacion = ejecutable.index(
        'Read-Host "Escribe ABRIR para continuar (cualquier otra cosa aborta)"'
    )
    escritura = ejecutable.index("Fijar-Ventana -Valor $VALOR_ABIERTA")

    assert aviso < confirmacion < escritura
    assert 'if ($confirmacion -ne "ABRIR")' in ejecutable


def test_f012_ventana_cerrar_no_pide_confirmacion():
    """Cerrar siempre es seguro, y T32 se ejecuta **salga bien o mal**.

    Una palabra que teclear en el camino de cerrar solo puede conseguir que
    alguien deje la ventana abierta por prisa.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_VENTANA))
    tras_abrir = ejecutable.split("Fijar-Ventana -Valor $VALOR_ABIERTA", 1)[1]

    assert ejecutable.count("Read-Host") == 1
    assert "Read-Host" not in tras_abrir
    assert "Fijar-Ventana -Valor $VALOR_CERRADA" in tras_abrir


def test_f012_ventana_despues_de_escribir_se_relee_el_valor():
    """Lo que se imprime es el estado **real**, no el que se pidió.

    La Function tarda unos segundos en reiniciarse, y una escritura que se da
    por buena sin releer es como se sigue el bloque 9 creyendo que la ventana
    está cerrada cuando no lo está.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_VENTANA))
    cuerpo = re.search(
        r"function Fijar-Ventana \{.*?\n\}\n", ejecutable, flags=re.DOTALL
    )
    assert cuerpo, "no está la función que escribe y relee"

    dentro = cuerpo.group()

    assert '"appsettings", "set"' in dentro
    assert dentro.index('"appsettings", "set"') < dentro.index("Leer-Ventana")


def test_f012_ventana_no_toca_ninguna_otra_app_setting():
    """`--settings` nombra **la** variable y ninguna más.

    `az functionapp config appsettings set` con una lista corta no borra las
    demás, pero un `--settings` con dos cosas dentro sería otra decisión
    tomada de paso, y aquí no se toma ninguna.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_VENTANA))
    escrituras = re.findall(r'"--settings",\s*"([^"]+)"', ejecutable)

    assert len(escrituras) == 1
    assert escrituras[0] == "$APP_SETTING_VENTANA=$Valor"


def test_f012_ventana_los_tres_modos_son_excluyentes():
    """`-Abrir -Cerrar` a la vez no es una petición: es una errata."""
    ejecutable = _sin_ayuda(_texto(SCRIPT_VENTANA))

    assert "[switch]$Abrir" in ejecutable
    assert "[switch]$Cerrar" in ejecutable
    assert "$SALIDA_MODO_AMBIGUO" in ejecutable


# --------------------------------------------------------------------------
# `20_login_sigrid.ps1` · solo lectura, y sin inventar SQL
# --------------------------------------------------------------------------


def test_f012_login_la_consulta_es_exactamente_la_del_servicio():
    """**El test central de este script.**

    Si el script preguntara con **otro** SQL que el que usa el servicio, su
    veredicto no diría nada sobre lo que va a pasar en el cierre: diría lo que
    pasa con otra consulta. Se importa la del servicio y se exige literal.
    """
    from infrastructure.sigrid.consultas import SQL_USUARIO

    ejecutable = _sin_ayuda(_texto(SCRIPT_LOGIN))

    assert SQL_USUARIO in ejecutable
    # Y ninguna otra sentencia contra el ERP: una sola consulta, la suya.
    assert len(re.findall(r"(?i)\bSELECT\b", ejecutable)) == 1


def test_f012_login_el_candidato_se_deriva_igual_que_en_el_dominio():
    """La parte anterior a la arroba, en minúsculas: `derivar_login_candidato`.

    Derivarlo «parecido» aquí produciría un veredicto sobre un login que el
    servicio nunca va a proponer, que es peor que no comprobar nada.
    """
    texto = _texto(SCRIPT_LOGIN)
    ejecutable = _sin_ayuda(texto)

    assert "derivar_login_candidato" in texto
    assert "domain/models/cierre.py" in texto
    assert ".ToLower()" in ejecutable
    assert 'IndexOf("@")' in ejecutable


def test_f012_login_acepta_tambien_un_login_directo():
    """Para los que **no** siguen la convención, que los hay.

    Sin `-Login` no habría forma de comprobar el caso que motiva el script.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_LOGIN))

    assert "[string]$Login" in ejecutable
    assert "[string]$Correo" in ejecutable


def test_f012_login_la_cabecera_dice_que_la_convencion_no_siempre_se_cumple():
    """Está **medido**, y el número es la razón de ser del script.

    De 8 usuarios del ERP con correo registrado, 6 cumplen la convención. Sin
    ese dato, alguien da por hecho que la siembra automática va a funcionar
    para todo el mundo.
    """
    # La cabecera va justificada a 79 columnas, así que la frase se parte en
    # varias líneas: se normalizan los espacios antes de buscarla.
    seguido = " ".join(_texto(SCRIPT_LOGIN).split())

    assert "8 usuarios del ERP con correo registrado" in seguido
    assert "6 cumplen" in seguido
    assert "mas corto que el prefijo de su correo" in seguido


def test_f012_login_el_veredicto_distingue_los_tres_casos():
    """Una vez, ninguna, o más de una: tres desenlaces y tres cosas que hacer.

    Y el de «ninguna» **nombra el script del alta manual**: quien recibe ese
    veredicto tiene que saber que lo que toca no es reintentar.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_LOGIN))

    assert "-eq 1" in ejecutable
    assert "-eq 0" in ejecutable
    assert "-gt 1" in ejecutable
    assert "07_alta_usuario_sigrid.ps1" in ejecutable
    assert "Escribir-Veredicto" in ejecutable


def test_f012_login_no_escribe_absolutamente_nada():
    """Ni en el ERP, ni en PostgreSQL, ni en Azure, ni en disco.

    Comprobar un login es una pregunta. La correspondencia la escribe
    `07_alta_usuario_sigrid.ps1`, que es otro script y pide lo suyo.
    """
    ejecutable = _sin_ayuda(_texto(SCRIPT_LOGIN)).upper()

    for verbo in VERBOS_DE_ESCRITURA_EN_SIGRID + VERBOS_DE_ESCRITURA_EN_PG:
        assert verbo.upper() not in ejecutable
    for prohibido in ("PSYCOPG", "APPSETTINGS SET", "OUT-FILE", "SET-CONTENT"):
        assert prohibido not in ejecutable


def test_f012_login_la_consulta_va_parametrizada_y_por_el_comun():
    """`sigrid_api.md` §5.2 · marcador `?`, nunca concatenacion.

    Un correo concatenado en la cadena seria una inyeccion contra el ERP de
    produccion lanzada desde un puesto de trabajo. Y la llamada la hace el
    comun de lectura, no una copia del manejo de la clave.
    """
    texto = _texto(SCRIPT_LOGIN)
    ejecutable = _sin_ayuda(texto)

    assert '. "$PSScriptRoot\\08_lectura_sigrid_comun.ps1"' in texto
    assert "Invoke-SigridLectura" in ejecutable
    assert "-Parametros" in ejecutable
    assert "= ?" in ejecutable
    assert "/api/sql/write" not in ejecutable
