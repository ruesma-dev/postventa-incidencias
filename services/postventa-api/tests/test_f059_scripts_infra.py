# services/postventa-api/tests/test_f059_scripts_infra.py
"""Los scripts de F-059 cumplen su contrato (T18; R38, R39, `design.md` §13, §14).

Son PowerShell: no entran en la cobertura ni en la campaña de mutación
—`harness/alcance.py` solo mide `.py`—, así que su contrato se comprueba
leyéndolos, como hacen `test_f012_scripts_infra.py` con la ventana del ERP y
`test_f036_scripts_infra.py` con su lectura de Sigrid.

- **`infra/27_ventana_volcado.ps1`** (R38): la ventana `VOLCADO_HABILITADO`,
  calco de `19_ventana_escritura.ps1`. Sin parámetros **solo lee**; `-Abrir`
  avisa de lo que abre y pide una palabra tecleada; `-Cerrar` cierra **sin
  preguntar**; y después de escribir **vuelve a leer** el valor.
- **`infra/28_volcado_lectura_sigrid.ps1`** (R39): las fotos de antes y de
  después de la verificación en producción (T25, T26). **Solo
  `POST /api/sql/read`**, a través de `08_lectura_sigrid_comun.ps1`; solo
  `SELECT`, con marcadores `?`; y **ninguna** columna de descripciones,
  nombres, propietario ni persona: del parte, el código, los códigos de
  estado, tipo y oficio, la **longitud** de la ubicación, cuántos
  intervinientes y cuántos marcados como causante, y si su UPV es de la obra;
  y el `MAX(cod)` de la serie del mes.
- **`infra/desplegar_backend.ps1`** (R38, D-3): `VOLCADO_HABILITADO=false` en
  su propia línea de `$ajustes`, **en todos los despliegues**, con y sin
  `-VentanasCerradas`; y `VOLCADO_PARTES_POR_LLAMADA`, con el valor por
  defecto del código.

**Codificación: ASCII puro, sin BOM y CRLF.** `tasks.md` T18 dice «UTF-8 con
BOM y CRLF», que es la regla general de `docs/CONVENTIONS.md`; pero
`infra/` es una de sus «excepciones documentadas»: `test_f010_prompt_keys_infra.py`
lee **todos** los `.ps1` como `ascii` y un BOM tumba la suite entera al
recolectar, y `test_f010_scripts_infra.py` lee así `desplegar_backend.ps1`.
Un fichero ASCII ya es UTF-8 válido. Es la misma desviación, por la misma
causa, que dejaron escrita `test_f013_scripts_infra.py` y
`test_f036_scripts_infra.py`; consta en `progress/impl_F-059.md` (Bloque 5).

Este fichero no lleva ningún identificador ni ningún host: los controles
negativos se componen en memoria a partir de trozos. Sin red, sin base, sin
IA: solo se leen los ficheros.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Raíz del repositorio, tres niveles por encima de este fichero.
RAIZ = Path(__file__).resolve().parent.parent.parent.parent
INFRA = RAIZ / "infra"

#: R38 · la ventana del volcado.
SCRIPT_VENTANA = INFRA / "27_ventana_volcado.ps1"

#: R39 · las fotos de Sigrid, solo lectura.
SCRIPT_LECTURA = INFRA / "28_volcado_lectura_sigrid.ps1"

#: R38 · el despliegue del backend, que la publica cerrada.
SCRIPT_DESPLIEGUE = INFRA / "desplegar_backend.ps1"

#: La lectura compartida por todos los scripts que preguntan a `sigrid-api`.
COMUN = INFRA / "08_lectura_sigrid_comun.ps1"

LOS_DOS = (SCRIPT_VENTANA, SCRIPT_LECTURA)
LOS_TRES = (*LOS_DOS, SCRIPT_DESPLIEGUE)

#: La App Setting de la ventana y la del troceo (`config/settings.py`).
VENTANA = "VOLCADO_HABILITADO"
TROCEO = "VOLCADO_PARTES_POR_LLAMADA"

#: Las otras dos ventanas del servicio: el script del volcado no las toca.
OTRAS_VENTANAS = ("CIERRE_HABILITADO", "ARCHIVO_HABILITADO")

#: La marca de orden de bytes de UTF-8.
BOM = b"\xef\xbb\xbf"

#: La forma de un GUID: el `oid` de Entra, la suscripción, el inquilino.
PATRON_GUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

#: Hosts de Azure: el PostgreSQL compartido y la pasarela.
PATRON_HOST_AZURE = re.compile(
    r"[\w-]+\.(?:postgres\.database|azurewebsites)\.(?:azure\.com|net)",
    re.IGNORECASE,
)

#: Una credencial escrita a mano en el propio fichero.
PATRON_CREDENCIAL = re.compile(
    r"(?i)\b(?:password|pwd|passwd|secret|token|api[_-]?key|clave)\s*=\s*[\"'][^\"'$]",
)

#: Un código de parte real, con la forma de la serie de Sigrid.
PATRON_PARTE_REAL = re.compile(r"\bRS\d{2}\.\d{2}/\d{4}\b")

#: Un correo escrito, de cualquier dominio.
PATRON_CORREO = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")

#: Una dirección IPv4.
PATRON_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

#: Sentencias que escribirían en el ERP.
PATRON_SQL_QUE_ESCRIBE = re.compile(
    r"\b(?:INSERT\s+INTO|UPDATE\s+\w|DELETE\s+FROM|MERGE\s+|EXEC(?:UTE)?\s|TRUNCATE\s|DROP\s|ALTER\s|CREATE\s)",
    re.IGNORECASE,
)

#: Columnas de Sigrid que llevan texto de personas o de la propiedad (R39, R34):
#: la descripción (`con.res`, `rcp.tex`), el propietario y quien reclama
#: (`cliide`, `recide`, `cntide`), sus teléfonos y correos (`tel`, `ele`), el
#: motivo, la solución y la urgencia, y el nombre de un fichero (`nom`).
COLUMNAS_PROHIBIDAS = re.compile(
    r"\.(?:res|tex|cliide|recide|cntide|peride|tel|ele|motrcp|solrcp|texurg|nom)\b",
    re.IGNORECASE,
)

#: Tablas de personas que la foto no puede ni rozar.
TABLAS_PROHIBIDAS = re.compile(r"\bdbo\.(?:per|prv|cli|concnt|condir)\b", re.IGNORECASE)


def _bytes(script: Path) -> bytes:
    return script.read_bytes()


def _texto(script: Path) -> str:
    """El script como texto (`utf-8-sig`: si alguien le pone un BOM, el test que
    lo prohíbe lo dice por su nombre en vez de reventar aquí)."""
    return script.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def _sin_ayuda(texto: str) -> str:
    """Sin el bloque `<# ... #>`: la ayuda explica lo que no se hace, y buscar
    en ella daría por rotas las reglas que defiende."""
    return re.sub(r"<#.*?#>", "", texto, flags=re.DOTALL)


def _ejecutable(script: Path) -> str:
    """Sin la ayuda ni las líneas de comentario: lo que de verdad se ejecuta."""
    return "\n".join(
        linea
        for linea in _sin_ayuda(_texto(script)).splitlines()
        if not linea.lstrip().startswith("#")
    )


def _ayuda(script: Path) -> str:
    texto = _texto(script)
    assert "<#" in texto and "#>" in texto, f"{script.name} no tiene ayuda"
    return texto[texto.index("<#") : texto.index("#>")]


def _plano(texto: str) -> str:
    return " ".join(texto.split())


# --------------------------------------------------------------------------
# Los tres: existen, con su ruta, ASCII, sin BOM, CRLF y sin valores
# --------------------------------------------------------------------------


@pytest.mark.parametrize("script", LOS_TRES, ids=lambda ruta: ruta.name)
def test_f059_r38_r39_los_scripts_existen(script):
    assert script.is_file(), f"falta {script.name}"


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f059_r38_r39_cada_script_empieza_por_su_ruta(script):
    """`docs/CONVENTIONS.md`: primera línea, la ruta relativa."""
    assert _texto(script).splitlines()[0] == f"# infra/{script.name}"


@pytest.mark.parametrize("script", LOS_TRES, ids=lambda ruta: ruta.name)
def test_f059_r38_r39_ascii_puro_sin_bom_y_crlf(script):
    """La excepción de `infra/` (cabecera de este fichero): ASCII, sin BOM, CRLF."""
    crudo = _bytes(script)

    assert not crudo.startswith(BOM), "un BOM tumba test_f010_prompt_keys_infra.py"
    assert all(byte < 128 for byte in crudo), (
        "un acento sale como dos caracteres raros en la consola"
    )
    assert crudo.count(b"\n") > 0
    assert crudo.count(b"\r\n") == crudo.count(b"\n"), "todas las líneas en CRLF"


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f059_r38_r39_cada_script_tiene_ayuda_con_parametros_y_ejemplos(script):
    """Se lanzan con el ERP de producción delante, y meses de por medio."""
    ayuda = _ayuda(script)

    for marca in (".SYNOPSIS", ".DESCRIPTION", ".PARAMETER"):
        assert marca in ayuda, f"{script.name} sin {marca}"
    assert ayuda.count(".EXAMPLE") >= 2


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f059_r38_r39_ningun_script_trae_un_valor(script):
    """Se versionan, y el historial de git no suelta lo que entra (CLAUDE.md)."""
    from tests.test_f010_scripts_infra import NOMBRES_DE_RECURSO

    texto = _texto(script)

    assert PATRON_GUID.findall(texto) == []
    assert PATRON_HOST_AZURE.findall(texto) == []
    assert PATRON_CREDENCIAL.search(texto) is None
    assert PATRON_PARTE_REAL.findall(texto) == []
    assert PATRON_CORREO.search(texto) is None
    assert PATRON_IP.findall(texto) == []
    assert [nombre for nombre in NOMBRES_DE_RECURSO if nombre in texto] == []


def test_f059_r38_r39_los_detectores_de_valores_no_son_ciegos():
    """Control negativo: cada patrón caza lo suyo, compuesto a trozos."""
    assert PATRON_GUID.search("1a2b3c4d-" + "0000-1111-2222-" + "333344445555")
    assert PATRON_HOST_AZURE.search("algo" + ".azurewebsites" + ".net")
    assert PATRON_CREDENCIAL.search("$clave = " + '"abc"')
    assert PATRON_PARTE_REAL.search("RS" + "99.10/" + "0001")
    assert PATRON_CORREO.search("alguien" + "@ejemplo.invalid")
    assert PATRON_IP.search("10." + "0.0.1")
    assert PATRON_SQL_QUE_ESCRIBE.search("DELETE " + "FROM dbo.con")
    assert COLUMNAS_PROHIBIDAS.search("SELECT c" + ".res FROM dbo.con c")
    assert COLUMNAS_PROHIBIDAS.search("r" + ".cliide")
    assert TABLAS_PROHIBIDAS.search("JOIN dbo" + ".per p")


# --------------------------------------------------------------------------
# R38 · `27_ventana_volcado.ps1`, la ventana del volcado
# --------------------------------------------------------------------------


def test_f059_r38_la_ventana_es_volcado_habilitado_y_solo_esa():
    """Una constante arriba, con nombre; ni el cierre ni el archivo (R37)."""
    texto = _texto(SCRIPT_VENTANA)
    ejecutable = _ejecutable(SCRIPT_VENTANA)

    assert f'$APP_SETTING_VENTANA = "{VENTANA}"' in ejecutable
    assert ejecutable.count(f'"{VENTANA}"') == 1
    for otra in OTRAS_VENTANAS:
        assert otra not in ejecutable, f"el script del volcado no toca {otra}"
    assert '. "$PSScriptRoot\\00_vars_postventa.ps1"' in texto
    assert "$PostventaGrupo" in ejecutable
    assert "$PostventaFunction" in ejecutable


def test_f059_r38_la_ventana_sin_parametros_solo_lee():
    """`-Estado` por omisión, y sale **antes** de la primera escritura."""
    ejecutable = _ejecutable(SCRIPT_VENTANA)

    assert "[switch]$Estado" in ejecutable
    assert '$modo = "estado"' in ejecutable
    salida_estado = ejecutable.index('if ($modo -eq "estado")')
    primera_escritura = ejecutable.index("Fijar-Ventana -Valor")

    assert salida_estado < primera_escritura
    tramo_estado = ejecutable[salida_estado:primera_escritura]
    assert "exit 0" in tramo_estado


def test_f059_r38_la_ventana_ausente_es_cerrada_y_la_ilegible_desconocida():
    """Sin la App Setting manda el defecto del código, `False`: cerrada. Una
    lectura que no se pudo hacer no sale en verde: desconocida, y no se toca."""
    ejecutable = _ejecutable(SCRIPT_VENTANA)

    assert (
        "if ([string]::IsNullOrWhiteSpace($valor)) { return $VALOR_CERRADA }"
        in ejecutable
    )
    assert "if ($actual -eq $VALOR_DESCONOCIDO)" in ejecutable
    assert "$SALIDA_SIN_LECTURA" in ejecutable


def test_f059_r38_la_ventana_se_dice_en_palabras():
    ejecutable = _ejecutable(SCRIPT_VENTANA)

    assert "function En-Palabras" in ejecutable
    for palabra in ("abierta", "cerrada", "desconocida"):
        assert f'"{palabra}"' in ejecutable


def test_f059_r38_abrir_avisa_de_lo_que_abre_y_pide_una_palabra():
    """**El test central del script.** El aviso de `design.md` §13 va **antes**
    de la palabra, y la palabra antes de escribir."""
    ejecutable = _ejecutable(SCRIPT_VENTANA)

    avisos = [
        ejecutable.index(frase)
        for frase in (
            "Abre la CREACION DE PARTES en el ERP de produccion",
            "para cualquier usuario del grupo con login de Sigrid",
            "El siguiente despliegue la vuelve a cerrar",
        )
    ]
    palabra = ejecutable.index(
        'Read-Host "Escribe ABRIR para continuar (cualquier otra cosa aborta)"'
    )
    escritura = ejecutable.index("Fijar-Ventana -Valor $VALOR_ABIERTA")

    assert max(avisos) < palabra < escritura
    assert 'if ($confirmacion -ne "ABRIR")' in ejecutable
    assert "$SALIDA_SIN_CONFIRMAR" in ejecutable


def test_f059_r38_cerrar_no_pide_ninguna_palabra():
    """Cerrar es lo seguro, y T26 lo ejecuta **sin preguntar**, salga bien o mal."""
    ejecutable = _ejecutable(SCRIPT_VENTANA)
    tras_abrir = ejecutable.split("Fijar-Ventana -Valor $VALOR_ABIERTA", 1)[1]

    assert ejecutable.count("Read-Host") == 1
    assert "Read-Host" not in tras_abrir
    assert "Fijar-Ventana -Valor $VALOR_CERRADA" in tras_abrir


def test_f059_r38_tras_escribir_se_vuelve_a_leer():
    """Lo que se imprime es lo que dice el entorno, no lo que se pidió."""
    ejecutable = _ejecutable(SCRIPT_VENTANA)
    cuerpo = re.search(
        r"function Fijar-Ventana \{.*?\n\}\n", ejecutable, flags=re.DOTALL
    )
    assert cuerpo, "no está la función que escribe y relee"
    dentro = cuerpo.group()

    assert '"appsettings", "set"' in dentro
    assert dentro.index('"appsettings", "set"') < dentro.index("return Leer-Ventana")
    assert "if ($tras -ne $pedido)" in ejecutable
    assert "$SALIDA_NO_COINCIDE" in ejecutable


def test_f059_r38_la_unica_escritura_es_esa_app_setting():
    """Un `--settings`, con la variable de la ventana y nada más."""
    ejecutable = _ejecutable(SCRIPT_VENTANA)

    assert re.findall(r'"--settings",\s*"([^"]+)"', ejecutable) == [
        "$APP_SETTING_VENTANA=$Valor"
    ]
    assert ejecutable.count('"appsettings", "set"') == 1


def test_f059_r38_los_modos_son_excluyentes_y_cada_fallo_tiene_su_codigo():
    """R5 de F-010: un código de salida por causa, sin repetir ninguno."""
    ejecutable = _ejecutable(SCRIPT_VENTANA)
    codigos = re.findall(r"^\$SALIDA_[A-Z_]+ = (\d+)$", ejecutable, re.MULTILINE)

    assert "[switch]$Abrir" in ejecutable
    assert "[switch]$Cerrar" in ejecutable
    assert "$SALIDA_MODO_AMBIGUO" in ejecutable
    assert len(codigos) >= 6
    assert len(set(codigos)) == len(codigos)


def test_f059_r38_la_ventana_no_habla_con_la_pasarela():
    """El script toca el plano de gestión de Azure, nunca `sigrid-api`: ni una
    ruta de la pasarela ni una llamada HTTP propia. (Sus mensajes sí nombran
    `POST /api/volcado/volcar`, que es nuestro borde, no la pasarela.)"""
    ejecutable = _ejecutable(SCRIPT_VENTANA)

    assert "/api/sql/" not in ejecutable
    assert "/api/sigrid/" not in ejecutable
    assert re.search(r"Invoke-(?:RestMethod|WebRequest)", ejecutable) is None
    assert "08_lectura_sigrid_comun.ps1" not in ejecutable


def test_f059_r38_la_ayuda_dice_que_se_publica_cerrada_y_que_el_ensayo_no_la_mira():
    """D-3 y D-4, con su porqué: el que lo lance tiene que saber qué abre."""
    ayuda = _plano(_ayuda(SCRIPT_VENTANA))

    for texto in (
        VENTANA,
        "D-3",
        "D-4",
        "CADA DESPLIEGUE LA VUELVE A CERRAR",
        "/api/volcado/volcar",
        "/api/volcado/ensayo",
        "19_ventana_escritura.ps1",
        "config/settings.py",
    ):
        assert texto in ayuda, f"la ayuda no dice «{texto}»"


# --------------------------------------------------------------------------
# R39 · `28_volcado_lectura_sigrid.ps1`, las fotos de Sigrid
# --------------------------------------------------------------------------


def _consultas() -> list[str]:
    """Las sentencias del script: los here-strings literales `@' ... '@`."""
    return re.findall(
        r"@'\n(.*?)\n'@", _sin_ayuda(_texto(SCRIPT_LECTURA)), flags=re.DOTALL
    )


def test_f059_r39_las_consultas_se_leen():
    """Un control que no lee nada da verde siempre: al menos las cuatro fotos
    (la obra, la serie del mes, los partes con la referencia y su ficha)."""
    assert len(_consultas()) >= 4


def test_f059_r39_solo_lee_y_por_el_comun():
    """Solo `POST /api/sql/read`, y a través de `08_lectura_sigrid_comun.ps1`
    (R111 de F-036): ni HTTP propio, ni otra ruta de la pasarela."""
    texto = _texto(SCRIPT_LECTURA)
    ejecutable = _ejecutable(SCRIPT_LECTURA)

    assert '. "$PSScriptRoot\\08_lectura_sigrid_comun.ps1"' in texto
    assert "Invoke-SigridLectura" in ejecutable
    assert "/api/" not in ejecutable
    assert re.search(r"Invoke-(?:RestMethod|WebRequest)", ejecutable) is None
    for ruta in ("sql/write", "partes-reclamacion", "concepto-grafico"):
        assert ruta not in ejecutable


def test_f059_r39_cada_consulta_es_un_select_con_marcadores():
    """Solo `SELECT` (la guarda de la pasarela no admite `WITH`), ninguna que
    escriba, los valores por `?` y nada interpolado dentro del SQL."""
    for sql in _consultas():
        assert sql.lstrip().upper().startswith("SELECT"), sql
        assert PATRON_SQL_QUE_ESCRIBE.search(sql) is None, sql
        assert "?" in sql, sql
        assert "$" not in sql, sql
        assert "SELECT *" not in sql.upper(), sql


def test_f059_r39_ninguna_consulta_lee_nombres_propietario_ni_persona():
    """R39 · «sin descripciones, nombres, propietario ni persona». La ubicación,
    solo por su **longitud**."""
    for sql in _consultas():
        assert COLUMNAS_PROHIBIDAS.search(sql) is None, sql
        assert TABLAS_PROHIBIDAS.search(sql) is None, sql
        sin_longitud = sql.replace("LEN(r.resubi)", "")
        assert "resubi" not in sin_longitud, sql


def test_f059_r39_la_foto_del_parte_trae_lo_que_pide_r39():
    """Por la referencia en `conext` `RCPCLI`: cuántos `tip 708`, y del parte el
    `cod`, los códigos de estado, tipo y oficio, la longitud de la ubicación,
    los intervinientes, los causantes y si su UPV es de la obra."""
    junto = _plano("\n".join(_consultas()))

    for texto in (
        "x.cod = ?",
        "x.valt = ?",
        "c.tip = ?",
        "COUNT(*) AS partes",
        "e.cod AS estado_cod",
        "t.cod AS tipo_cod",
        "o.cod AS oficio_cod",
        "LEN(r.resubi) AS ubicacion_longitud",
        "dbo.rcpint",
        "cauave",
        "AS intervinientes",
        "AS causantes",
        "AS upv_de_la_obra",
        "dbo.conest",
        "dbo.auxtrcp",
        "dbo.auxofc",
    ):
        assert texto in junto, f"las consultas no traen «{texto}»"


def test_f059_r39_la_serie_del_mes_y_el_listado_de_nuestros_partes():
    """El `MAX(cod)` de la serie del mes (`RS<aa>.<mm>/` y cuatro cifras, como
    `sigrid-api`) y, sin referencia, los partes de la obra con `PVI-`: es lo que
    localiza lo creado para anularlo (`design.md` §14)."""
    junto = _plano("\n".join(_consultas()))
    ejecutable = _ejecutable(SCRIPT_LECTURA)

    assert "MAX(c.cod) AS max_cod" in junto
    assert "c.cod LIKE ?" in junto
    assert "x.valt LIKE ?" in junto
    assert '"RS{0:yy}.{0:MM}/"' in ejecutable
    assert '"[0-9][0-9][0-9][0-9]"' in ejecutable
    assert '"PVI-%"' in ejecutable
    assert '"RCPCLI"' in ejecutable


def test_f059_r39_la_referencia_tiene_que_ser_nuestra():
    """Una referencia sin el prefijo exacto `PVI-` no es de este servicio, y la
    foto de otra cosa no prueba nada (sensible a mayúsculas, como la pasarela)."""
    ejecutable = _ejecutable(SCRIPT_LECTURA)

    assert "[string]$Referencia" in ejecutable
    assert "[string]$CodigoObra" in ejecutable
    assert "-cnotmatch '^PVI-'" in ejecutable
    assert "$SALIDA_PARAMETRO" in ejecutable


def test_f059_r39_el_veredicto_es_el_del_comun():
    """Con la referencia, **un** parte y de la obra; si no, `NO PASA` (sale 6)."""
    ejecutable = _ejecutable(SCRIPT_LECTURA)

    assert "Reiniciar-Veredicto" in ejecutable
    assert 'Comprobar -Que "partes tip 708 con la referencia" -Esperado 1' in ejecutable
    assert 'Comprobar -Que "su UPV es de la obra" -Esperado "si"' in ejecutable
    assert "Escribir-Veredicto" in ejecutable


def test_f059_r39_la_ayuda_dice_lo_que_no_hace():
    """Solo lectura, y lo que no imprime: quien lo lea antes de lanzarlo tiene
    que saber que no anula ni pasa a PTE."""
    ayuda = _plano(_ayuda(SCRIPT_LECTURA))

    for texto in (
        "SOLO LECTURA",
        "POST /api/sql/read",
        "RCPCLI",
        "PVI-",
        "MAX(cod)",
        "NO PROCEDE",
        "PTE",
        "T25",
        "T26",
    ):
        assert texto in ayuda, f"la ayuda no dice «{texto}»"


# --------------------------------------------------------------------------
# R38 · `desplegar_backend.ps1`: la ventana del volcado, publicada cerrada
# --------------------------------------------------------------------------


def _ajustes(ejecutable: str) -> str:
    bloque = re.findall(r"(?ms)^\$ajustes = @\((.*?)^\)", ejecutable)
    assert len(bloque) == 1, "no se encuentra el bloque $ajustes"
    return bloque[0]


def problemas_de_la_ventana_del_volcado(ejecutable: str) -> list[str]:
    """Lo que falta para que `VOLCADO_HABILITADO` se publique **cerrada siempre**.

    `ejecutable` es el script sin ayuda ni comentarios. La lista vacía es D-3:
    la variable sale **una vez**, en **su línea** de `$ajustes` y con el literal
    `false`; ni con una variable que pudiera cambiar, ni dentro del bloque de
    `-VentanasCerradas`, ni con `true` en ninguna parte.
    """
    problemas: list[str] = []
    linea = re.compile(rf'^[ \t]*"{VENTANA}=false",?[ \t]*$', re.MULTILINE)
    if not linea.search(_ajustes(ejecutable)):
        problemas.append(f"{VENTANA}=false no está en su línea de $ajustes")
    if ejecutable.count(VENTANA) != 1:
        problemas.append(f"{VENTANA} aparece {ejecutable.count(VENTANA)} veces, no 1")
    if re.search(rf"{VENTANA}\s*=\s*\$", ejecutable):
        problemas.append(f"{VENTANA} toma su valor de una variable")
    if re.search(rf"{VENTANA}\s*=\s*true", ejecutable, re.IGNORECASE):
        problemas.append(f"{VENTANA}=true escrito")
    bloque = re.search(
        r"(?s)^if \(\$VentanasCerradas\) \{\n(.*?)^\}", ejecutable, re.MULTILINE
    )
    if bloque and "volcado" in bloque.group(1).lower():
        problemas.append("la ventana del volcado depende de -VentanasCerradas")
    return problemas


def test_f059_r38_d3_el_despliegue_publica_la_ventana_cerrada_con_y_sin_el_switch():
    """**El test central del despliegue.** Con o sin `-VentanasCerradas`, el
    mismo literal, en su línea: la ventana se abre con `27_` para cada volcado."""
    assert problemas_de_la_ventana_del_volcado(_ejecutable(SCRIPT_DESPLIEGUE)) == []


def test_f059_r38_d3_el_detector_de_la_ventana_no_es_ciego():
    """Control negativo, compuesto en memoria: abierta, con variable, dentro del
    switch, o fuera de `$ajustes`."""
    base = (
        "param(\n    [switch]$VentanasCerradas\n)\n"
        '$ventanaCierre = "true"\n'
        "if ($VentanasCerradas) {\n"
        '    $ventanaCierre = "false"\n'
        "}\n"
        "$ajustes = @(\n"
        '    "CIERRE_HABILITADO=$ventanaCierre",\n'
        f'    "{VENTANA}=false",\n'
        ")\n"
    )
    abierta = base.replace(f'"{VENTANA}=false"', f'"{VENTANA}=true"')
    con_variable = base.replace(f'"{VENTANA}=false"', f'"{VENTANA}=$ventanaVolcado"')
    en_el_switch = base.replace(
        '    $ventanaCierre = "false"\n',
        '    $ventanaCierre = "false"\n    $ventanaVolcado = "false"\n',
    )
    fuera = (
        base.replace(f'    "{VENTANA}=false",\n', "") + f'$extra = "{VENTANA}=false"\n'
    )

    assert problemas_de_la_ventana_del_volcado(base) == []
    for variante in (abierta, con_variable, en_el_switch, fuera):
        assert variante != base
        assert problemas_de_la_ventana_del_volcado(variante) != []


def test_f059_r30_r38_el_despliegue_fija_el_troceo_con_el_defecto_del_codigo():
    """`VOLCADO_PARTES_POR_LLAMADA`, en `$ajustes`, con el mismo 5 que el código
    (R30: entero de 1 a 50; se ajusta sin desplegar, Q-8)."""
    from config.settings import Ajustes

    defecto = Ajustes.model_fields["volcado_partes_por_llamada"].default
    lineas = re.findall(
        rf'^[ \t]*"{TROCEO}=(\d+)",?[ \t]*$',
        _ajustes(_ejecutable(SCRIPT_DESPLIEGUE)),
        re.MULTILINE,
    )

    assert lineas == [str(defecto)]
    assert 1 <= int(lineas[0]) <= 50
    assert Ajustes.model_fields["volcado_habilitado"].default is False


def test_f059_r38_el_despliegue_ensena_la_ventana_del_volcado_antes_de_confirmar():
    """Quien teclea DESPLEGAR tiene que ver que el volcado queda cerrado."""
    ejecutable = _ejecutable(SCRIPT_DESPLIEGUE)
    linea = [
        renglon
        for renglon in ejecutable.splitlines()
        if "Write-Host" in renglon and "Ventana del volcado" in renglon
    ]

    assert len(linea) >= 1
    assert "CERRADA" in linea[0]
    assert ejecutable.index("Ventana del volcado") < ejecutable.index(
        'Read-Host "Escribe DESPLEGAR'
    )


def test_f059_r38_la_cabecera_del_despliegue_lo_explica():
    """Un `false` sin explicación es un `false` que el siguiente cambia."""
    ayuda = _plano(_ayuda(SCRIPT_DESPLIEGUE))

    for texto in (
        VENTANA,
        TROCEO,
        "D-3",
        "27_ventana_volcado.ps1",
        "CERRADA EN TODOS LOS DESPLIEGUES",
    ):
        assert texto in ayuda, f"la cabecera no dice «{texto}»"
    parametro = ayuda.split(".PARAMETER VentanasCerradas", 1)[1].split(".EXAMPLE", 1)[0]
    assert VENTANA in parametro, (
        "el parámetro tiene que decir que el volcado queda cerrado igual"
    )
