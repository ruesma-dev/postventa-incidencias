# services/postventa-api/tests/test_f065_scripts_infra.py
"""El script de medición de F-065 cumple su contrato (T1, T2; R29).

`infra/29_reclamaciones_obra_sigrid.ps1` lo lanza **una persona** contra el ERP
de producción (T-A0), con la consulta que leerá el adaptador: todas las
reclamaciones de la obra **con los datos personales de R33**. Así que lo que se
fija aquí es, sobre todo, lo que **no** puede hacer: ni escribir, ni imprimir
un texto, un nombre, un teléfono, un correo, un código de reclamación o una
referencia. Solo recuentos, bytes y segundos.

Es PowerShell: no entra en la cobertura ni en la campaña de mutación
—`harness/alcance.py` solo mide `.py`—, así que su contrato se comprueba
leyéndolo, como hacen `test_f036_scripts_infra.py` y `test_f059_scripts_infra.py`.

- **Solo `POST /api/sql/read`**, a través de `08_lectura_sigrid_comun.ps1`:
  ni HTTP propio, ni `sql/write`, ni `partes-reclamacion`, ni
  `concepto-grafico`; solo `SELECT`, con todos los valores por `?`.
- **La consulta es la de `design.md` §3, carácter a carácter** (R29: «la misma
  consulta que el adaptador»). El adaptador aún no existe (Bloque A3): este
  fichero la compara con el texto de §3 escrito aquí, y T5 fija que el
  adaptador lleva el mismo.
- **Nada de una fila sale por la consola.** Todo lo que se imprime pasa por
  `Write-Host` con variables de una lista cerrada, por `Comprobar`/`Anotar`
  con literales, o por `Anotar-Cifra`, que **solo admite cifras** y, si recibe
  otra cosa, para sin repetirla. Las etiquetas variables salen de listas
  constantes del script (estados conocidos, tramos, campos de R33, umbrales),
  nunca de los datos.
- **Ningún valor dentro** (ni pasarela, ni base, ni clave, ni obra), **ASCII
  puro, sin BOM y CRLF**, y la ruta en la primera línea, como el resto de
  `infra/`. R29 lo dice así («ASCII sin BOM y con CRLF»): es la excepción de
  `infra/` de `docs/CONVENTIONS.md`.

Este fichero no lleva ningún identificador ni ningún host: los controles
negativos se componen en memoria a partir de trozos. Sin red, sin base, sin
IA: solo se leen los ficheros.
"""

from __future__ import annotations

import calendar
import json
import os
import re
import shutil
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pytest

#: Raíz del repositorio, tres niveles por encima de este fichero.
RAIZ = Path(__file__).resolve().parent.parent.parent.parent
INFRA = RAIZ / "infra"

#: R29 · la medición de las reclamaciones de la obra, solo lectura.
SCRIPT = INFRA / "29_reclamaciones_obra_sigrid.ps1"

#: La lectura compartida por todos los scripts que preguntan a `sigrid-api`.
COMUN = INFRA / "08_lectura_sigrid_comun.ps1"

#: La marca de orden de bytes de UTF-8.
BOM = b"\xef\xbb\xbf"

#: `design.md` §3, `SQL_RECLAMACIONES_DE_LA_OBRA`, tal cual: treinta y una
#: columnas; parámetros `RCPCLI`, `PVI-%`, el tipo y la obra.
SQL_DE_LA_OBRA = """\
SELECT v.obride, c.cod, e.cod, c.fec, u.cod, a.cod, a.res, t.cod, t.res, r.resubi, c.res, p.valt,
       CAST(r.tex AS nvarchar(max)), r.motrcp, r.texurg, r.rcptip, r.fecpre,
       CAST(r.solrcp AS nvarchar(max)), k.cod, k.res,
       CAST(r.tel AS nvarchar(max)), CAST(r.ele AS nvarchar(max)),
       cl.res, pr.nom, pr.tel, pr.tel2, pr.ele, pc.nom, pc.tel, pc.tel2, pc.ele
FROM dbo.rcp r
JOIN dbo.con c ON c.ide = r.ide
JOIN dbo.upv v ON v.ide = r.upvide
JOIN dbo.con u ON u.ide = v.ide
JOIN dbo.con o ON o.ide = v.obride
LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est
LEFT JOIN dbo.auxofc a ON a.ide = r.ofcide
LEFT JOIN dbo.auxtrcp t ON t.ide = r.trcpide
LEFT JOIN dbo.auxrcp k ON k.ide = r.rcpide
LEFT JOIN dbo.con cl ON cl.ide = r.cliide
LEFT JOIN dbo.per pr ON pr.ide = r.recide
LEFT JOIN dbo.per pc ON pc.ide = r.cntide
OUTER APPLY (SELECT TOP 1 x.valt FROM dbo.conext x
             WHERE x.conide = c.ide AND x.cod = ? AND x.valt LIKE ?
             ORDER BY x.ide) p
WHERE c.tip = ? AND LTRIM(RTRIM(o.cod)) = ?
ORDER BY c.cod"""

#: Q0 · qué forma del código guarda Sigrid (con y sin ceros) y cuántas obras
#: con unidades de posventa la tienen.
SQL_FORMAS = """\
SELECT LTRIM(RTRIM(o.cod)) AS obra_cod, COUNT(DISTINCT v.obride) AS obras
FROM dbo.upv v
JOIN dbo.con o ON o.ide = v.obride
WHERE LTRIM(RTRIM(o.cod)) IN (?, ?)
GROUP BY LTRIM(RTRIM(o.cod))"""

#: Q2 · `con.fec` frente a `rcp.fec` (T-A0), solo recuentos, con el filtro de
#: obra de §3.
SQL_FECHAS = """\
SELECT COUNT(*) AS reclamaciones,
       SUM(CASE WHEN r.fec = c.fec THEN 1 ELSE 0 END) AS iguales,
       SUM(CASE WHEN r.fec > c.fec THEN 1 ELSE 0 END) AS rcp_posterior,
       SUM(CASE WHEN r.fec < c.fec THEN 1 ELSE 0 END) AS rcp_anterior,
       SUM(CASE WHEN r.fec IS NULL OR r.fec = 0 THEN 1 ELSE 0 END) AS rcp_vacia,
       SUM(CASE WHEN c.fec IS NULL OR c.fec = 0 THEN 1 ELSE 0 END) AS con_vacia
FROM dbo.rcp r
JOIN dbo.con c ON c.ide = r.ide
JOIN dbo.upv v ON v.ide = r.upvide
JOIN dbo.con o ON o.ide = v.obride
WHERE c.tip = ? AND LTRIM(RTRIM(o.cod)) = ?"""

#: `design.md` §5.3, paso 3: la lista cerrada de palabras vacías del dominio.
PALABRAS_VACIAS = (
    "del", "las", "los", "con", "por", "para", "que", "sus", "una", "unos",
    "unas", "muy", "mas", "sin", "sobre", "entre", "hay", "esta", "este",
    "esto", "son", "como", "han", "tiene",
)

#: R33 · los diecinueve campos de la ficha, en el orden de la consulta, con
#: la etiqueta que imprime el script (solo cuántas reclamaciones lo traen).
CAMPOS_R33 = (
    ("descripcion larga", 12),
    ("motivo", 13),
    ("urgencia", 14),
    ("forma de comunicacion", 15),
    ("fecha prevista", 16),
    ("solucion", 17),
    ("clase (codigo)", 18),
    ("clase (nombre)", 19),
    ("telefonos de avisos", 20),
    ("correo de avisos", 21),
    ("propietario", 22),
    ("persona que reclama: nombre", 23),
    ("persona que reclama: telefono", 24),
    ("persona que reclama: telefono 2", 25),
    ("persona que reclama: correo", 26),
    ("persona de contacto: nombre", 27),
    ("persona de contacto: telefono", 28),
    ("persona de contacto: telefono 2", 29),
    ("persona de contacto: correo", 30),
)

#: Las variables que una línea de `Write-Host` o un mensaje de `Salir-Con`
#: pueden llevar: la obra que teclea la persona y sus dos formas, el tipo, el
#: techo y los límites del propio script. Ninguna sale de una fila.
VARIABLES_QUE_SE_PUEDEN_IMPRIMIR = frozenset(
    {
        "$codigo",
        "$conCeros",
        "$sinCeros",
        "$obraCod",
        "$Tip",
        "$MaxFilas",
        "$TECHO_PASARELA",
        "$MAX_UNIDADES",
        "$modo",
    }
)

#: En `Comprobar`/`Anotar`/`Anotar-Cifra -Que`: además de las de arriba, las
#: cifras de control y las etiquetas que salen de las listas constantes.
VARIABLES_DE_LAS_ETIQUETAS = VARIABLES_QUE_SE_PUEDEN_IMPRIMIR | frozenset(
    {
        "$columnasEsperadas",
        "$columnasLeidas",
        "$bajoElTecho",
        "$nombreEstado",
        "$tramo",
        "$campo",
        "$umbral",
        "$Que",
        "$numero",
    }
)

#: Lo que delata una fila en una línea que imprime.
PATRON_FILA = re.compile(r"\$fila\b|\$filas\b|\.rows\b|\[\$COL_|Get-SigridValor|\$respuesta\b")

#: Una variable de PowerShell (sin el `$(` de una subexpresión).
PATRON_VARIABLE = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*")

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

#: Un código de reclamación real, con la forma de la serie de Sigrid.
PATRON_PARTE_REAL = re.compile(r"\bRS\d{2}\.\d{2}/\d{4}\b")

#: Un correo escrito, de cualquier dominio.
PATRON_CORREO = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")

#: Una dirección IPv4.
PATRON_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

#: Un código de obra con la forma de los de Ruesma (cuatro cifras con cero
#: delante): la obra entra por parámetro, nunca escrita.
PATRON_OBRA = re.compile(r"\b0\d{3}\b")

#: El nombre de la base de negocio del ERP, compuesto a trozos.
NOMBRE_DE_LA_BASE = "rue" + "sma"

#: Sentencias que escribirían en el ERP.
PATRON_SQL_QUE_ESCRIBE = re.compile(
    r"\b(?:INSERT\s+INTO|UPDATE\s+\w|DELETE\s+FROM|MERGE\s+|EXEC(?:UTE)?\s|TRUNCATE\s|DROP\s|ALTER\s|CREATE\s)",
    re.IGNORECASE,
)

#: R33 · lo que la consulta no nombra nunca: el DNI, las credenciales de
#: i-Sigrid, las direcciones y las observaciones de la persona (`per.tex`).
PATRON_VETADO = re.compile(
    r"\b(?:dni|esiglog|esigpas|clamai|dir|dir1|dir2|dircpo|dirpob|dirpro)\b"
    r"|\bp[rc]\.tex\b|\bper\.tex\b",
    re.IGNORECASE,
)

#: Lo que escribiría en disco o lanzaría otro programa.
PATRON_ESCRITURA_LOCAL = re.compile(
    r"\b(?:Set-Content|Add-Content|Out-File|Export-Csv|New-Item|Remove-Item|"
    r"Copy-Item|Move-Item|Start-Process|Invoke-Expression|Invoke-PythonDelServicio|"
    r"Write-Output|Out-Host|Format-Table|Format-List|Out-GridView|Write-Warning|"
    r"Write-Verbose|Write-Information|Write-Error)\b",
    re.IGNORECASE,
)


def _bytes(script: Path) -> bytes:
    return script.read_bytes()


def _texto(script: Path = SCRIPT) -> str:
    """El script como texto (`utf-8-sig`: si alguien le pone un BOM, el test que
    lo prohíbe lo dice por su nombre en vez de reventar aquí)."""
    return script.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def _sin_ayuda(texto: str) -> str:
    """Sin el bloque `<# ... #>`: la ayuda explica lo que no se hace, y buscar
    en ella daría por rotas las reglas que defiende."""
    return re.sub(r"<#.*?#>", "", texto, flags=re.DOTALL)


def _sin_comentarios(texto: str) -> str:
    return "\n".join(
        linea for linea in texto.splitlines() if not linea.lstrip().startswith("#")
    )


def _ejecutable(texto: str | None = None) -> str:
    """Sin la ayuda ni las líneas de comentario: lo que de verdad se ejecuta."""
    return _sin_comentarios(_sin_ayuda(_texto() if texto is None else texto))


def _lineas(texto: str | None = None) -> set[str]:
    """Las líneas ejecutables, recortadas: para exigir una línea **entera**."""
    return {linea.strip() for linea in _ejecutable(texto).splitlines()}


def _ayuda() -> str:
    texto = _texto()
    assert "<#" in texto and "#>" in texto, f"{SCRIPT.name} no tiene ayuda"
    return texto[texto.index("<#") : texto.index("#>")]


def _plano(texto: str) -> str:
    return " ".join(texto.split())


def _consultas(texto: str | None = None) -> list[str]:
    """Las sentencias del script: los here-strings literales `@' ... '@`."""
    fuente = _texto() if texto is None else texto
    return re.findall(r"@'\n(.*?)\n'@", _sin_ayuda(fuente), flags=re.DOTALL)


def _consulta(variable: str, texto: str | None = None) -> str:
    """El here-string asignado a `variable`, tal cual."""
    fuente = _texto() if texto is None else texto
    encontradas = re.findall(
        rf"^\${variable} = @'\n(.*?)\n'@", _sin_ayuda(fuente), flags=re.DOTALL | re.MULTILINE
    )
    assert len(encontradas) == 1, f"no hay un here-string ${variable}"
    return encontradas[0]


def problemas_de_impresion(ejecutable: str) -> list[str]:
    """Lo que imprimiría algo de una fila (R29: solo recuentos, bytes y segundos).

    `ejecutable` es el script sin ayuda ni comentarios. La lista vacía quiere
    decir: ninguna línea que imprime nombra una fila; `Write-Host` y los
    mensajes de `Salir-Con` solo llevan variables de la lista cerrada;
    `Comprobar`/`Anotar` y la etiqueta de `Anotar-Cifra`, también (su valor
    puede ser cualquier expresión: `Anotar-Cifra` solo deja pasar cifras); y
    nada escribe en disco ni por otra salida.
    """
    problemas: list[str] = []
    for linea in ejecutable.splitlines():
        if "Write-Host" in linea:
            if PATRON_FILA.search(linea):
                problemas.append(f"Write-Host con una fila: {linea.strip()}")
            sobran = set(PATRON_VARIABLE.findall(linea)) - VARIABLES_QUE_SE_PUEDEN_IMPRIMIR
            if sobran:
                problemas.append(f"Write-Host con {sorted(sobran)}: {linea.strip()}")
        for orden in ("Comprobar ", "Anotar ", "Anotar-Cifra "):
            if re.search(rf"(?:^|[\s;{{(]){re.escape(orden)}", linea) is None:
                continue
            if PATRON_FILA.search(linea):
                problemas.append(f"{orden.strip()} con una fila: {linea.strip()}")
            etiqueta = linea.split("-Valor", 1)[0] if orden == "Anotar-Cifra " else linea
            sobran = set(PATRON_VARIABLE.findall(etiqueta)) - VARIABLES_DE_LAS_ETIQUETAS
            if sobran:
                problemas.append(f"{orden.strip()} con {sorted(sobran)}: {linea.strip()}")
    for mensaje in re.findall(r"Salir-Con\b(.*?)\$SALIDA_\w+", ejecutable, flags=re.DOTALL):
        if PATRON_FILA.search(mensaje):
            problemas.append(f"Salir-Con con una fila: {_plano(mensaje)}")
        sobran = set(PATRON_VARIABLE.findall(mensaje)) - VARIABLES_QUE_SE_PUEDEN_IMPRIMIR
        if sobran:
            problemas.append(f"Salir-Con con {sorted(sobran)}: {_plano(mensaje)}")
    for culpable in PATRON_ESCRITURA_LOCAL.findall(ejecutable):
        problemas.append(f"escribe o saca por otra via: {culpable}")
    return problemas


# --------------------------------------------------------------------------
# El fichero: existe, con su ruta, ASCII, sin BOM, CRLF, con ayuda
# --------------------------------------------------------------------------


def test_f065_r29_el_script_existe():
    assert SCRIPT.is_file(), f"falta {SCRIPT.name}"


def test_f065_r29_empieza_por_su_ruta():
    """`docs/CONVENTIONS.md`: primera línea, la ruta relativa."""
    assert _texto().splitlines()[0] == f"# infra/{SCRIPT.name}"


def test_f065_r29_ascii_puro_sin_bom_y_crlf():
    """R29 y la excepción de `infra/`: ASCII, sin BOM, CRLF en todas las líneas."""
    crudo = _bytes(SCRIPT)

    assert not crudo.startswith(BOM), "un BOM tumba test_f010_prompt_keys_infra.py"
    assert all(byte < 128 for byte in crudo), "un acento sale como dos caracteres raros"
    assert crudo.count(b"\n") > 0
    assert crudo.count(b"\r\n") == crudo.count(b"\n"), "todas las líneas en CRLF"


def test_f065_r29_tiene_ayuda_con_parametros_y_ejemplos():
    """Se lanza con el ERP de producción delante y meses de por medio."""
    ayuda = _ayuda()

    for marca in (
        ".SYNOPSIS",
        ".DESCRIPTION",
        ".PARAMETER CodigoObra",
        ".PARAMETER MaxFilas",
        ".PARAMETER SigridBaseUrl",
        ".PARAMETER SigridBaseDatos",
    ):
        assert marca in ayuda, f"la ayuda no trae {marca}"
    assert ayuda.count(".EXAMPLE") >= 2


def test_f065_r29_la_ayuda_dice_lo_que_hace_y_lo_que_no():
    """Quien lo lea antes de lanzarlo tiene que saber qué mide, que es de solo
    lectura, que no imprime ningún dato y que el parecido es aproximado."""
    ayuda = _plano(_ayuda())

    for texto in (
        "SOLO LECTURA",
        "POST /api/sql/read",
        "08_lectura_sigrid_comun.ps1",
        "R29",
        "T-A0",
        "R33",
        "truncated",
        "bytes",
        "segundos",
        "APROXIMA",
        "design.md",
        "con y sin ceros",
    ):
        assert texto in ayuda, f"la ayuda no dice «{texto}»"


# --------------------------------------------------------------------------
# Solo lectura, por el común
# --------------------------------------------------------------------------


def test_f065_r29_carga_el_comun_y_solo_lee_por_el():
    """Solo `POST /api/sql/read`, a través de `08_lectura_sigrid_comun.ps1`
    (R111 de F-036): ni HTTP propio, ni otra ruta de la pasarela."""
    texto = _texto()
    ejecutable = _ejecutable()

    assert '. "$PSScriptRoot\\08_lectura_sigrid_comun.ps1"' in texto
    assert "Invoke-SigridLectura" in ejecutable
    assert "/api/" not in ejecutable
    assert re.search(r"Invoke-(?:RestMethod|WebRequest)", ejecutable) is None
    for ruta in ("sql/write", "partes-reclamacion", "concepto-grafico"):
        assert ruta not in ejecutable, f"el script nombra {ruta}"


def test_f065_r29_no_escribe_en_disco_ni_lanza_nada():
    """Una medición no deja ficheros: lo que mide sale por la consola y nada más."""
    assert PATRON_ESCRITURA_LOCAL.findall(_ejecutable()) == []


def test_f065_r29_hay_consultas_y_todas_son_select_con_marcadores():
    """Solo `SELECT` (la guarda de la pasarela no admite `WITH`), ninguna que
    escriba, los valores por `?` y nada interpolado dentro del SQL."""
    consultas = _consultas()

    assert len(consultas) >= 3, "la de la obra, la de las dos formas del código y la de las fechas"
    for sql in consultas:
        assert sql.lstrip().upper().startswith("SELECT"), sql
        assert PATRON_SQL_QUE_ESCRIBE.search(sql) is None, sql
        assert "?" in sql, sql
        assert "$" not in sql, sql
        assert "SELECT *" not in sql.upper(), sql


def test_f065_r29_ninguna_consulta_nombra_lo_vetado_de_r33():
    """R33 · ni `dni`, ni `esiglog`/`esigpas`/`clamai`, ni direcciones, ni
    `per.tex`; tampoco en las consultas auxiliares."""
    for sql in _consultas():
        assert PATRON_VETADO.search(sql) is None, sql


def test_f065_r29_la_consulta_de_la_obra_es_la_de_design_caracter_a_caracter():
    """**El test central de T2.** R29: «la misma consulta que el adaptador
    (texto idéntico)». Se compara con el texto de `design.md` §3 escrito aquí;
    T5 fija que el adaptador lleva el mismo."""
    assert _consulta("SQL_RECLAMACIONES_DE_LA_OBRA") == SQL_DE_LA_OBRA


def test_f065_r29_el_sql_viaja_con_saltos_lf_como_el_del_adaptador():
    """El fichero es CRLF; el texto del adaptador, LF. Para que lo que llega a la
    pasarela sea **el mismo** carácter a carácter, el script lo pasa a LF antes
    de mandarlo, y toda consulta pasa por ahí."""
    ejecutable = _ejecutable()

    assert "function ConvertTo-SqlConLf" in ejecutable
    assert '-replace "`r`n", "`n"' in ejecutable
    llamadas = re.findall(r"-Sql (\$\w+)", ejecutable)
    assert len(llamadas) == ejecutable.count("Invoke-SigridLectura"), (
        "cada llamada a Invoke-SigridLectura con su -Sql $variable"
    )
    assert llamadas, "no se encuentra ninguna llamada a Invoke-SigridLectura"
    for variable in set(llamadas):
        asignaciones = re.findall(rf"^\s*\{variable} = (.*)$", ejecutable, flags=re.MULTILINE)
        assert asignaciones, f"{variable} no se asigna"
        for asignacion in asignaciones:
            assert asignacion.startswith("ConvertTo-SqlConLf "), (
                f"{variable} no pasa por ConvertTo-SqlConLf: {asignacion}"
            )


def test_f065_r29_los_parametros_van_en_el_orden_de_los_marcadores():
    """`RCPCLI`, `PVI-%`, el tipo y la obra (§3); y el techo de la pasarela.
    Por **líneas enteras**: `= 500` contiene `= 50`, y la línea de la guarda
    empieza como la de la obra."""
    lineas = _lineas()

    for linea in (
        '$CAMPO_REFERENCIA = "RCPCLI"',
        '$PATRON_NUESTROS = "PVI-%"',
        "[int]$Tip = 708,",
        "[int]$MaxFilas = 500000",
        "$TECHO_PASARELA = 500000",
        "$parametros = @($CAMPO_REFERENCIA, $PATRON_NUESTROS, $Tip, $obraCod)",
        "-Parametros $parametros -MaxFilas $MaxFilas -Tolerante",
        "if ($MaxFilas -lt 1 -or $MaxFilas -gt $TECHO_PASARELA) {",
    ):
        assert linea in lineas, f"falta la línea «{linea}»"


def test_f065_r29_las_consultas_auxiliares_son_las_que_dice_la_ayuda():
    """La forma del código (Q0) y `con.fec` frente a `rcp.fec` (Q2), escritas
    aquí enteras: solo recuentos y el código recortado, nunca un `ide`."""
    assert _consulta("SQL_FORMAS_DE_LA_OBRA") == SQL_FORMAS
    assert _consulta("SQL_FECHAS_DE_LA_OBRA") == SQL_FECHAS


def test_f065_r29_la_obra_con_y_sin_ceros_como_el_28():
    """Las dos formas del código, preguntadas con dos marcadores; y a la consulta
    de la obra va la forma que guarda Sigrid, recortada (el filtro de F-036)."""
    ejecutable = _ejecutable()
    obra = _consulta("SQL_FORMAS_DE_LA_OBRA")

    assert "[string]$CodigoObra" in ejecutable
    assert '$conCeros = $codigo.PadLeft(4, "0")' in ejecutable
    assert '$sinCeros = $codigo.TrimStart("0")' in ejecutable
    assert "-Parametros @($conCeros, $sinCeros)" in ejecutable
    assert "LTRIM(RTRIM(o.cod)) IN (?, ?)" in obra
    assert "COUNT(DISTINCT v.obride) AS obras" in obra
    assert '$codigo -notmatch "^[A-Za-z0-9._-]{1,20}$"' in ejecutable


def test_f065_r29_la_pasarela_tiene_que_aceptarla_y_sin_truncar():
    """Si la pasarela rechaza la consulta (el `OUTER APPLY`, por ejemplo) o la
    respuesta viene `truncated`, se dice y **no pasa**; y a la medición le
    interesa también si se llegó al techo."""
    ejecutable = _ejecutable()

    assert "-Tolerante" in ejecutable
    assert "if ($null -eq $respuesta)" in ejecutable
    assert (
        'Comprobar -Que "la pasarela acepto la consulta, sin truncated" -Esperado "si" -Obtenido "no"'
        in ejecutable
    )
    assert (
        'Comprobar -Que "la pasarela acepto la consulta, sin truncated" -Esperado "si" -Obtenido "si"'
        in ejecutable
    )
    assert 'Anotar -Que "truncated" -Valor "no"' in ejecutable
    assert (
        'Comprobar -Que "filas por debajo del techo" -Esperado "si" -Obtenido $bajoElTecho'
        in ejecutable
    )
    assert (
        'Comprobar -Que "columnas de la respuesta" -Esperado $columnasEsperadas -Obtenido $columnasLeidas'
        in ejecutable
    )
    assert "$COLUMNAS_DE_LA_OBRA = 31" in _lineas()
    assert "[Diagnostics.Stopwatch]::StartNew()" in ejecutable


# --------------------------------------------------------------------------
# R29 · solo recuentos, bytes y segundos
# --------------------------------------------------------------------------


def test_f065_r29_nada_de_una_fila_sale_por_la_consola():
    """**El test central de T1.** R29: «ningún texto, nombre, teléfono, correo,
    código de reclamación ni referencia»."""
    assert problemas_de_impresion(_ejecutable()) == []


def test_f065_r29_anotar_cifra_solo_deja_pasar_cifras_y_no_repite_lo_que_recibe():
    """Si a `Anotar-Cifra` le llegara un texto por un error, para **sin** decir
    cuál (un `[double]` en la firma lo repetiría en el mensaje de error)."""
    cuerpo = re.search(
        r"function Anotar-Cifra \{.*?\n\}\n", _ejecutable(), flags=re.DOTALL
    )
    assert cuerpo, "no está Anotar-Cifra"
    dentro = cuerpo.group()

    assert "[double]::TryParse(" in dentro
    assert "[Globalization.CultureInfo]::InvariantCulture" in dentro
    assert "$SALIDA_SIN_DATO" in dentro
    assert "Anotar -Que $Que -Valor $numero" in dentro
    assert "[double]$Valor" not in dentro


def test_f065_r29_las_etiquetas_variables_salen_de_listas_constantes():
    """Los estados, los tramos, los campos de R33 y los umbrales se recorren
    desde listas escritas en el script; la variable del bucle no se asigna en
    ningún otro sitio. Así ninguna etiqueta sale de los datos."""
    ejecutable = _ejecutable()

    for bucle in (
        "foreach ($nombreEstado in $ESTADOS_CONOCIDOS)",
        "foreach ($tramo in $TRAMOS)",
        "foreach ($campo in $CAMPOS_R33)",
        "foreach ($umbral in $UMBRALES)",
    ):
        assert ejecutable.count(bucle) >= 1, f"falta «{bucle}»"
    for variable in ("$nombreEstado", "$tramo", "$campo", "$umbral"):
        assert re.search(rf"\{variable}\s*=[^=]", ejecutable) is None, (
            f"{variable} se asigna fuera de su bucle"
        )
    assert '$ESTADOS_CONOCIDOS = @("PTE", "SAT", "TER", "CER", "NPR")' in ejecutable
    assert "$UMBRALES = @(40, 50, 60)" in ejecutable


def test_f065_r29_imprime_los_recuentos_de_r29():
    """R29, uno por uno: filas, obras, `truncated`, bytes (todos y los de R33),
    segundos; por estado y por antigüedad; por unidad; sin oficio, sin
    ubicación, con `PVI-`; los grupos de R14 dentro de Sigrid; y los pares
    parecidos con 40, 50 y 60. Y `con.fec` frente a `rcp.fec` (T-A0)."""
    ejecutable = _ejecutable()

    for etiqueta in (
        "filas",
        "obras distintas en las filas",
        "segundos",
        "bytes de la respuesta, todos los campos",
        "bytes de los campos de R33",
        "sin estado",
        "otro estado",
        "unidades con reclamaciones",
        "reclamaciones por unidad: minimo",
        "reclamaciones por unidad: mediana",
        "reclamaciones por unidad: maximo",
        "sin oficio",
        "sin ubicacion",
        "con referencia PVI-",
        "grupos unidad+oficio+ubicacion con mas de una",
        "reclamaciones en esos grupos",
        "pares de la misma unidad comparados",
        "con.fec igual a rcp.fec",
        "rcp.fec posterior a con.fec",
        "rcp.fec anterior a con.fec",
        "rcp.fec vacia",
        "con.fec vacia",
    ):
        assert f'-Que "{etiqueta}"' in ejecutable, f"no imprime «{etiqueta}»"
    assert '-Que ("estado " + $nombreEstado)' in ejecutable
    assert '-Que ("antiguedad: " + $tramo)' in ejecutable
    assert '-Que ("R33 rellenos: " + $campo.Nombre)' in ejecutable
    assert '-Que ("pares con parecido >= " + $umbral)' in ejecutable
    assert (
        '$TRAMOS = @("menos de 6 meses", "de 6 a 12 meses", "de 12 a 24 meses", '
        '"mas de 24 meses", "sin fecha legible")'
    ) in ejecutable


def test_f065_r29_los_campos_de_r33_son_los_diecinueve_y_en_su_columna():
    """La lista cerrada de R33, en el orden de §3: cuántas reclamaciones traen
    cada uno, nunca cuál."""
    ejecutable = _ejecutable()
    declarados = re.findall(
        r'@\{ Nombre = "([^"]+)"; Columna = (\d+) \}', ejecutable
    )

    assert [(nombre, int(columna)) for nombre, columna in declarados] == list(CAMPOS_R33)
    assert "$PRIMERA_COLUMNA_R33 = 12" in _lineas()


def test_f065_r29_las_columnas_de_trabajo_estan_en_su_sitio():
    """Por posición, porque la consulta no lleva alias (es la del adaptador): la
    respuesta repite `cod`. Por eso el script comprueba antes que llegan 31."""
    ejecutable = _ejecutable()

    for constante in (
        "$COL_OBRA = 0",
        "$COL_ESTADO = 2",
        "$COL_FECHA = 3",
        "$COL_UNIDAD = 4",
        "$COL_OFICIO = 5",
        "$COL_UBICACION = 9",
        "$COL_DESCRIPCION = 10",
        "$COL_REFERENCIA = 11",
    ):
        assert constante in _lineas(), f"falta «{constante}»"
    assert ejecutable.index("-Obtenido $columnasLeidas") < ejecutable.index("[$COL_ESTADO]")


def test_f065_r29_el_parecido_es_el_de_r36_aproximado():
    """§5.3: `plegar`, partir por lo que no es letra o cifra, fuera las de menos
    de 3 letras y las vacías, sin la `s` final a las de 5 o más; Jaccard por
    abajo; 100 si la clave normalizada es la misma; y casa con ≥ 2 en común."""
    ejecutable = _ejecutable()
    lista = re.search(r"\$PALABRAS_VACIAS = @\(([^)]*)\)", ejecutable)

    assert lista, "no está $PALABRAS_VACIAS"
    assert tuple(re.findall(r'"([^"]+)"', lista.group(1))) == PALABRAS_VACIAS
    for pieza in (
        "[Text.NormalizationForm]::FormKD",
        "\\p{Mn}",
        "[^\\p{L}\\p{N}]+",
        "$palabra.Length -lt 3",
        "$palabra.Length -ge 5",
        "[math]::Floor(100 * $comunes / $union)",
        "$comunes -ge 2",
        '.TrimEnd(".,;: ".ToCharArray())',
    ):
        assert pieza in ejecutable, f"el parecido no trae «{pieza}»"


def test_f065_r29_los_grupos_y_las_unidades_distinguen_mayusculas():
    """La unidad y el oficio, por código exacto (R14): un `@{}` de PowerShell no
    distingue mayúsculas y juntaría lo que la aplicación separa."""
    ejecutable = _ejecutable()

    assert "Dictionary[string,object]" in ejecutable
    assert re.search(r"\$porUnidad = @\{\}", ejecutable) is None
    assert re.search(r"\$grupos = @\{\}", ejecutable) is None


# --------------------------------------------------------------------------
# Ningún valor dentro
# --------------------------------------------------------------------------


def test_f065_r29_ningun_valor_en_el_fichero():
    """Ni pasarela, ni base, ni clave, ni obra, ni un código de reclamación: se
    versiona, y el historial de git no suelta lo que entra (CLAUDE.md)."""
    from tests.test_f010_scripts_infra import NOMBRES_DE_RECURSO

    texto = _texto()

    assert PATRON_GUID.findall(texto) == []
    assert PATRON_HOST_AZURE.findall(texto) == []
    assert PATRON_CREDENCIAL.search(texto) is None
    assert PATRON_PARTE_REAL.findall(texto) == []
    assert PATRON_CORREO.search(texto) is None
    assert PATRON_IP.findall(texto) == []
    assert PATRON_OBRA.findall(texto) == []
    assert NOMBRE_DE_LA_BASE not in texto.lower()
    assert [nombre for nombre in NOMBRES_DE_RECURSO if nombre in texto] == []


def test_f065_r29_los_detectores_no_son_ciegos():
    """Control negativo: cada patrón caza lo suyo, compuesto a trozos."""
    assert PATRON_GUID.search("1a2b3c4d-" + "0000-1111-2222-" + "333344445555")
    assert PATRON_HOST_AZURE.search("algo" + ".azurewebsites" + ".net")
    assert PATRON_CREDENCIAL.search("$clave = " + '"abc"')
    assert PATRON_PARTE_REAL.search("RS" + "99.10/" + "0001")
    assert PATRON_CORREO.search("alguien" + "@ejemplo.invalid")
    assert PATRON_IP.search("10." + "0.0.1")
    assert PATRON_OBRA.search("-CodigoObra " + "0" + "999")
    assert PATRON_SQL_QUE_ESCRIBE.search("DELETE " + "FROM dbo.con")
    assert PATRON_VETADO.search("SELECT p" + "r.dni FROM dbo.per pr")
    assert PATRON_VETADO.search("SELECT p" + "c.tex FROM dbo.per pc")
    assert PATRON_VETADO.search("SELECT x." + "esigpas")
    assert PATRON_VETADO.search("SELECT c." + "dir1")
    assert PATRON_VETADO.search("SELECT CAST(r.tex AS nvarchar(max))") is None
    assert PATRON_ESCRITURA_LOCAL.search("$x | Export" + "-Csv a.csv")


def test_f065_r29_el_detector_de_impresion_no_es_ciego():
    """Control negativo, compuesto en memoria: cada forma de sacar una fila por
    la consola da un problema; la forma buena, ninguno."""
    buena = (
        'Write-Host "Obra: $obraCod"\n'
        'Anotar-Cifra -Que "filas" -Valor $numeroDeFilas\n'
        'Anotar-Cifra -Que ("estado " + $nombreEstado) -Valor $porEstado[$nombreEstado]\n'
        'Comprobar -Que "columnas de la respuesta" -Esperado $columnasEsperadas -Obtenido $columnasLeidas\n'
        'Salir-Con ("Falta -CodigoObra: " + $codigo) $SALIDA_PARAMETRO\n'
    )
    malas = (
        'Write-Host $fila[$COL_DESCRIPCION]\n',
        'Write-Host ("Unidad: " + $unidad)\n',
        'Anotar -Que "unidad" -Valor $unidad\n',
        'Anotar-Cifra -Que ("unidad " + $unidad) -Valor 1\n',
        'Comprobar -Que "x" -Esperado 1 -Obtenido $fila[0]\n',
        'Salir-Con ("Fila rara: " +\n    $descripcion) $SALIDA_SIN_DATO\n',
        '$filas | Format' + '-Table\n',
        'Write' + '-Output $descripcion\n',
    )

    assert problemas_de_impresion(buena) == []
    for mala in malas:
        assert problemas_de_impresion(buena + mala) != [], mala


def test_f065_r29_el_comun_sigue_siendo_de_solo_lectura():
    """El 08 no cambia con esta ficha: sigue leyendo solo por `sql/read`."""
    comun = _ejecutable(_texto(COMUN))

    assert '-Uri ($BaseUrl + "/api/sql/read")' in comun
    assert "sql/write" not in comun


# --------------------------------------------------------------------------
# R70 · `-Unidades`: la consulta de la guarda del ensayo (T2 bis, S-5)
# --------------------------------------------------------------------------

#: `design.md` §15.5, `SQL_RECLAMACIONES_DE_LAS_UNIDADES` con **una** unidad:
#: las 12 columnas de R6, sin R33, y un marcador en el `IN`.
SQL_DE_UNA_UNIDAD = """\
SELECT v.obride, c.cod, e.cod, c.fec, u.cod, a.cod, a.res, t.cod, t.res, r.resubi, c.res, p.valt
FROM dbo.rcp r
JOIN dbo.con c ON c.ide = r.ide
JOIN dbo.upv v ON v.ide = r.upvide
JOIN dbo.con u ON u.ide = v.ide
JOIN dbo.con o ON o.ide = v.obride
LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est
LEFT JOIN dbo.auxofc a ON a.ide = r.ofcide
LEFT JOIN dbo.auxtrcp t ON t.ide = r.trcpide
OUTER APPLY (SELECT TOP 1 x.valt FROM dbo.conext x
             WHERE x.conide = c.ide AND x.cod = ? AND x.valt LIKE ?
             ORDER BY x.ide) p
WHERE c.tip = ? AND LTRIM(RTRIM(o.cod)) = ? AND u.cod IN (?)
ORDER BY c.cod"""

#: La misma con **cinco** unidades: cinco marcadores, separados por coma y
#: espacio. Escrita entera, no compuesta: T15 cambia esta comparación por la
#: de `select_reclamaciones_de_las_unidades`.
SQL_DE_CINCO_UNIDADES = """\
SELECT v.obride, c.cod, e.cod, c.fec, u.cod, a.cod, a.res, t.cod, t.res, r.resubi, c.res, p.valt
FROM dbo.rcp r
JOIN dbo.con c ON c.ide = r.ide
JOIN dbo.upv v ON v.ide = r.upvide
JOIN dbo.con u ON u.ide = v.ide
JOIN dbo.con o ON o.ide = v.obride
LEFT JOIN dbo.conest e ON e.tip = c.tip AND e.est = c.est
LEFT JOIN dbo.auxofc a ON a.ide = r.ofcide
LEFT JOIN dbo.auxtrcp t ON t.ide = r.trcpide
OUTER APPLY (SELECT TOP 1 x.valt FROM dbo.conext x
             WHERE x.conide = c.ide AND x.cod = ? AND x.valt LIKE ?
             ORDER BY x.ide) p
WHERE c.tip = ? AND LTRIM(RTRIM(o.cod)) = ? AND u.cod IN (?, ?, ?, ?, ?)
ORDER BY c.cod"""

#: Cómo compone el script el `IN`: su línea, tal cual. Si cambia (otro
#: separador, otro marcador), el test que la exige falla antes que el resto.
LINEA_QUE_COMPONE = (
    "$sql = ConvertTo-SqlConLf ($SQL_RECLAMACIONES_DE_LAS_UNIDADES.Replace("
    '$MARCADORES, ((@("?") * $codigosDeUnidad.Count) -join ", ")))'
)


def _lo_que_manda_el_script_con(unidades: int) -> str:
    """El texto que el script manda con `unidades` unidades: su here-string con
    el marcador sustituido como dice `LINEA_QUE_COMPONE` (y en LF)."""
    plantilla = _consulta("SQL_RECLAMACIONES_DE_LAS_UNIDADES")
    return plantilla.replace("__MARCADORES__", ", ".join(["?"] * unidades))


def test_f065_r70_admite_unidades_y_lo_explica():
    """`-Unidades`, una lista de códigos, con su ayuda y su ejemplo."""
    ejecutable = _ejecutable()
    ayuda = _plano(_ayuda())

    assert "[string[]]$Unidades" in ejecutable
    assert ".PARAMETER Unidades" in _ayuda()
    for texto in ("R70", "T-A0 bis", "15.5", "sin R33", "cuantas unidades", "-Unidades"):
        assert texto in ayuda, f"la ayuda no dice «{texto}»"
    ejemplos = _ayuda().split(".EXAMPLE")[1:]
    assert any("-Unidades" in ejemplo for ejemplo in ejemplos), "ningun ejemplo con -Unidades"


def test_f065_r70_la_consulta_de_la_guarda_es_la_de_design_con_una_y_con_cinco():
    """**El test central de T2 bis.** R70: «texto idéntico para 1 y para 5
    unidades»."""
    ejecutable = _ejecutable()

    assert '$MARCADORES = "__MARCADORES__"' in ejecutable
    assert LINEA_QUE_COMPONE in ejecutable
    assert _lo_que_manda_el_script_con(1) == SQL_DE_UNA_UNIDAD
    assert _lo_que_manda_el_script_con(5) == SQL_DE_CINCO_UNIDADES


@pytest.mark.parametrize("unidades", [1, 2, 3, 4, 5, 50])
def test_f065_r70_el_script_manda_lo_mismo_que_la_funcion_de_la_guarda(unidades):
    """T15 (lo que dejó dicho T2 bis): la comparación con
    `select_reclamaciones_de_las_unidades`, la función que compone la lectura
    de la guarda del ensayo. El script y el servicio mandan **el mismo texto**,
    con el mismo número de marcadores."""
    from infrastructure.sigrid.consultas_reclamaciones_obra import (
        select_reclamaciones_de_las_unidades,
    )

    sql, _ = select_reclamaciones_de_las_unidades(
        codigo_obra="9901", tip=708, unidades=tuple(f"U{n:02d}" for n in range(unidades))
    )

    assert _lo_que_manda_el_script_con(unidades) == sql


def test_f065_r70_la_guarda_es_la_de_la_obra_sin_r33_y_con_el_filtro_de_unidades():
    """Mismas uniones que §3 salvo las de R33 (`auxrcp`, el propietario y las
    dos personas), las doce primeras columnas, y el `IN` al final del `WHERE`."""
    guarda = _consulta("SQL_RECLAMACIONES_DE_LAS_UNIDADES")
    obra = _consulta("SQL_RECLAMACIONES_DE_LA_OBRA")

    assert guarda.splitlines()[0] == obra.splitlines()[0].rstrip(",")
    for de_r33 in ("dbo.auxrcp", "dbo.per", "r.cliide", "r.tex", "r.tel", "r.ele", "motrcp", "solrcp", "texurg", "rcptip", "fecpre", ".nom"):
        assert de_r33 not in guarda, f"la guarda lee {de_r33}: no lee ni un dato personal"
    assert "AND u.cod IN (__MARCADORES__)\nORDER BY c.cod" in guarda
    assert "$COLUMNAS_DE_LAS_UNIDADES = 12" in _lineas()


def test_f065_r70_un_marcador_por_unidad_y_los_parametros_en_orden():
    """Los cuatro de §3 y después una unidad por marcador, sin interpolar nada."""
    assert (
        "$parametros = @($CAMPO_REFERENCIA, $PATRON_NUESTROS, $Tip, $obraCod) + $codigosDeUnidad"
        in _lineas()
    )
    assert "$columnasEsperadas = $COLUMNAS_DE_LAS_UNIDADES" in _lineas()


def test_f065_r70_la_lista_se_parte_por_comas_y_tiene_tope():
    """Con `powershell -File` la lista llega como **un** texto con comas (el
    comando de T-A0 bis): el script la parte, recorta y quita los vacíos; sin
    ninguna unidad, o con más de las que caben en una llamada del ensayo, para."""
    ejecutable = _ejecutable()

    assert '-split ","' in ejecutable
    # Las variables de PowerShell no distinguen mayúsculas: una lista local
    # llamada `$unidades` pisaría el parámetro `$Unidades` antes de leerlo.
    assert re.search(r"\$unidades\s*=", ejecutable, flags=re.IGNORECASE) is None
    assert "$codigosDeUnidad = @($Unidades | ForEach-Object" in ejecutable
    assert "$MAX_UNIDADES = 50" in _lineas()
    assert "if ($codigosDeUnidad.Count -gt $MAX_UNIDADES)" in ejecutable
    assert 'if ($PSBoundParameters.ContainsKey("Unidades"))' in ejecutable
    assert "if ($codigosDeUnidad.Count -eq 0)" in ejecutable


def test_f065_r70_imprime_cuantas_unidades_y_no_cuales():
    """R70: filas, `truncated`, bytes y segundos, y **cuántas** unidades. Ni una
    línea que imprime nombra la lista, salvo por su `Count`."""
    ejecutable = _ejecutable()

    assert 'Anotar-Cifra -Que "unidades pedidas" -Valor $codigosDeUnidad.Count' in ejecutable
    for linea in ejecutable.splitlines():
        if re.search(r"Write-Host|Anotar|Comprobar|Salir-Con", linea):
            sin_count = re.sub(r"\$codigosDeUnidad\.Count\b", "", linea)
            assert (
                re.search(r"\$(?:unidades|codigosDeUnidad)\b", sin_count, flags=re.IGNORECASE)
                is None
            ), linea


def test_f065_r70_con_unidades_no_hace_las_cuentas_de_la_obra():
    """La guarda mide lo que cuesta, no la población: con `-Unidades` el
    veredicto sale **antes** de las cuentas de R29 y de la consulta de fechas."""
    ejecutable = _ejecutable()
    veredicto = ejecutable.index('Escribir-Veredicto -Titulo "MEDICION DE LA GUARDA"')
    # La rama que cierra la guarda: el último `if ($conUnidades)` antes de su veredicto.
    rama = ejecutable.rindex("if ($conUnidades) {", 0, veredicto)

    assert rama < veredicto < ejecutable.index("[$COL_ESTADO]")
    assert veredicto < ejecutable.index("$SQL_FECHAS_DE_LA_OBRA", rama)
    assert ejecutable.index("bytes de la respuesta, todos los campos") < rama


# --------------------------------------------------------------------------
# El script, ejecutado contra un lector doble (sin red, datos inventados)
# --------------------------------------------------------------------------
#
# Leer el script fija su forma; ejecutarlo fija lo que **hace**: las cuentas de
# R29, el texto exacto que manda a la pasarela y, sobre todo, que con datos
# personales delante no saca **ninguno** por la consola. El doble es el `08`
# de verdad con `Invoke-SigridLectura` redefinida al final: no hay red (y la
# raíz es `.invalid`, que no resuelve nunca). Datos de prueba de R39: «Ejemplo
# …», `@ejemplo.invalid`, `000 000 000`. Si el puesto no tiene PowerShell, se
# salta: lo de arriba se sigue comprobando.

#: El ejecutable de PowerShell del puesto, si lo hay.
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")

#: `Invoke-SigridLectura` de mentira: apunta cada llamada (SQL, parámetros,
#: `max_rows`, `-Tolerante`) y devuelve filas inventadas según la consulta.
LECTOR_DOBLE = r"""

# --- Doble de test_f065_scripts_infra.py: sin red ---------------------------
$script:LlamadaDoble = 0
function Invoke-SigridLectura {
    param([string]$BaseUrl, [string]$Clave, [string]$BaseDatos, [string]$Sql,
        [object[]]$Parametros = @(), [int]$MaxFilas = 50, [int]$TimeoutS = 35, [switch]$Tolerante)
    $script:LlamadaDoble = $script:LlamadaDoble + 1
    $base = Join-Path $env:F065_SALIDA ("llamada_" + $script:LlamadaDoble)
    [IO.File]::WriteAllText($base + ".sql", $Sql)
    $apunte = ("" + $MaxFilas + [char]31 + [bool]$Tolerante + [char]31 + (($Parametros | ForEach-Object { "$_" }) -join [char]31))
    [IO.File]::WriteAllText($base + ".par", $apunte)
    if ($Sql.Contains("AS obra_cod")) {
        $obras = 2
        if ($env:F065_OBRAS_TEXTO -eq "1") { $obras = "Ejemplo Nombre Secreto" }
        return [pscustomobject]@{ ok = $true; truncated = $false; columns = @("obra_cod", "obras"); rows = @(,@("0999", $obras)); row_count = 1 }
    }
    if ($Sql.Contains("AS rcp_posterior")) {
        return [pscustomobject]@{ ok = $true; truncated = $false; columns = @("reclamaciones", "iguales", "rcp_posterior", "rcp_anterior", "rcp_vacia", "con_vacia"); rows = @(,@(14, 3, 1, $null, 0, 0)); row_count = 1 }
    }
    if ($env:F065_RECHAZO -eq "1") {
        if ($Tolerante) { Write-Host "  AVISO: la pasarela no ha dado por buena la consulta."; return $null }
        exit 4
    }
    $filas = [IO.File]::ReadAllText($env:F065_FILAS) | ConvertFrom-Json
    $columnas = 31
    if ($Sql.Contains("u.cod IN")) {
        $columnas = 12
        $filas = @($filas | ForEach-Object { ,($_[0..11]) })
    }
    return [pscustomobject]@{ ok = $true; truncated = $false; columns = @(1..$columnas); rows = $filas; row_count = @($filas).Count }
}
"""


def _hace(meses: int, dias: int = 0) -> int:
    """Hoy menos `meses` (el día recortado al último del mes, como
    `AddMonths` de .NET) más `dias`, en el `YYYYMMDD` del ERP."""
    # La fecha LOCAL, a propósito: el script cuenta los meses con `Get-Date`.
    hoy = date.today()  # noqa: DTZ011
    total = hoy.year * 12 + hoy.month - 1 - meses
    anio, mes = divmod(total, 12)
    dia = min(hoy.day, calendar.monthrange(anio, mes + 1)[1])
    return int((date(anio, mes + 1, dia) + timedelta(days=dias)).strftime("%Y%m%d"))


#: R33 entero (dos reclamaciones) y casi vacío (las demás): un blanco no
#: cuenta, `rcptip` 0 sí (es un valor), la fecha prevista 0 no.
R33_ENTERO = [
    "Ejemplo descripcion larga", "Ejemplo motivo", "Ejemplo urgencia", 1, 20260101,
    "Ejemplo solucion", "C1", "Ejemplo clase", "000 000 000", "avisos@ejemplo.invalid",
    "Ejemplo Propietario", "Ejemplo Reclama", "000 000 000", "000 000 000",
    "reclama@ejemplo.invalid", "Ejemplo Contacto", "000 000 000", "000 000 000",
    "contacto@ejemplo.invalid",
]
R33_CASI_VACIO = ["Ejemplo descripcion larga", "  ", None, 0, 0] + [None] * 14


def _fila(obra, cod, estado, fecha, unidad, oficio, ubicacion, descripcion, referencia, r33):
    nombre_oficio = None if oficio is None else "Ejemplo oficio"
    return [obra, cod, estado, fecha, unidad, oficio, nombre_oficio, "0002", "Ejemplo tipo",
            ubicacion, descripcion, referencia, *r33]


def _filas() -> list[list]:
    """Catorce reclamaciones inventadas; cada una está ahí por una regla."""
    c = R33_CASI_VACIO
    return [
        _fila(11, "RSX/1", "PTE", _hace(2), "VILLA 05", "0039", "Cocina", "Gotea el grifo", "PVI-ejemplo-1", R33_ENTERO),
        _fila(11, "RSX/2", "SAT", _hace(8), "VILLA 05", "0039", " cocina ", "Gotea el grifo.", None, R33_ENTERO),
        _fila(11, "RSX/3", "XYZ", 0, "VILLA 05", None, None, "Silicona negra en banera", None, c),
        _fila(12, "RSX/4", None, 20251301, "Villa 05", "0039", "Cocina", "Cambiar silicona banera", None, c),
        _fila(11, "RSX/5", "CER", _hace(18), "VILLA 06", "0039", "Bano", "Grifos sueltos", None, c),
        _fila(11, "RSX/6", "TER", _hace(24), "VILLA 06", "0039", "BANO", "Grifo suelto en cocina", None, c),
        _fila(11, "RSX/7", "NPR", _hace(6, 1), "VILLA 07", "0039", "  ", "Silicona negra banera", None, c),
        _fila(11, "RSX/8", "pte", _hace(6), "VILLA 07", "0039", "Salon", "Cambiar silicona banera", None, c),
        _fila(11, "RSX/9", "SAT", _hace(12), "VILLA 07", "0039", "salon ", "Silicona negra para pared salon", None, c),
        _fila(11, "RSX/10", "SAT", _hace(2), "VILLA 06", "0039", "Bano", "", None, c),
        _fila(11, "RSX/11", "SAT", _hace(2), "VILLA 06", "0039", "Bano", "  ", None, c),
        _fila(11, "RSX/12", "TER", _hace(40), "VILLA 08", "0012", None, "Grifo!", None, c),
        _fila(11, "RSX/13", "CER", _hace(40), "VILLA 08", "0012", None, "grifo?", None, c),
        _fila(11, "RSX/14", "PTE", _hace(40), "VILLA 08", "0012", None, "Grifo cocina", None, c),
    ]


def _bytes_json(valor) -> int:
    """El JSON compacto en UTF-8: lo que el script aproxima (su ayuda)."""
    return len(json.dumps(valor, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


#: Lo que no puede aparecer en la consola: cada valor inventado de una fila.
VALORES_DE_LAS_FILAS = (
    "Ejemplo", "ejemplo.invalid", "000 000 000", "RSX/", "PVI-ejemplo", "VILLA", "Villa",
    "Gotea", "Cocina", "cocina", "Silicona", "Grifo", "grifo", "Salon", "salon", "Bano",
    "BANO", "XYZ", "pte ", "Secreto",
)


def _lanzar(
    tmp_path: Path, *argumentos: str, obra: str | None = "999", **entorno: str
) -> tuple[int, str, list[tuple[str, str]]]:
    """Copia el 29 y el 08 con el doble a `tmp_path`, lo lanza y devuelve el
    código de salida, la consola y las llamadas (SQL, apunte) en orden.
    Con `obra=None` no se pasa `-CodigoObra`."""
    carpeta = tmp_path / "infra"
    salida = tmp_path / "llamadas"
    carpeta.mkdir()
    salida.mkdir()
    shutil.copyfile(SCRIPT, carpeta / SCRIPT.name)
    (carpeta / COMUN.name).write_bytes(
        COMUN.read_bytes() + LECTOR_DOBLE.replace("\n", "\r\n").encode("ascii")
    )
    filas = tmp_path / "filas.json"
    filas.write_text(json.dumps(_filas()), encoding="utf-8")
    variables = {
        **os.environ,
        "SIGRID_API_KEY": "falsa",
        "F065_FILAS": str(filas),
        "F065_SALIDA": str(salida),
        **entorno,
    }
    resultado = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-File", str(carpeta / SCRIPT.name),
         *(() if obra is None else ("-CodigoObra", obra)),
         "-SigridBaseUrl", "http://pasarela.ejemplo.invalid", "-SigridBaseDatos", "ejemplo",
         *argumentos],
        capture_output=True, timeout=120, env=variables, check=False,
    )
    consola = (resultado.stdout + resultado.stderr).decode("utf-8", errors="replace")
    llamadas = []
    for n in range(1, 10):
        sql = salida / f"llamada_{n}.sql"
        if not sql.exists():
            break
        llamadas.append(
            (sql.read_text(encoding="utf-8"), (salida / f"llamada_{n}.par").read_text(encoding="utf-8"))
        )
    return resultado.returncode, consola, llamadas


def _veredicto(consola: str) -> dict[str, str]:
    """La tabla de `Escribir-Veredicto` (`{0,-46} {1,-22} {2}`): qué → obtenido."""
    tabla = {}
    for linea in consola.splitlines():
        if len(linea) > 70 and linea[46] == " " and linea[69] == " " and not linea.startswith("QUE "):
            tabla[linea[:46].rstrip()] = linea[70:].strip()
    return tabla


def _apunte(max_rows: int, tolerante: bool, *parametros: object) -> str:
    return chr(31).join([str(max_rows), str(tolerante), chr(31).join(str(p) for p in parametros)])


necesita_powershell = pytest.mark.skipif(POWERSHELL is None, reason="sin PowerShell en el puesto")


@pytest.fixture(scope="module")
def obra_entera(tmp_path_factory):
    return _lanzar(tmp_path_factory.mktemp("obra"))


@pytest.fixture(scope="module")
def guarda(tmp_path_factory):
    return _lanzar(tmp_path_factory.mktemp("guarda"), "-Unidades", "VILLA 05, ,VILLA 07")


@necesita_powershell
def test_f065_r29_ejecutado_no_saca_ningun_valor_de_las_filas(obra_entera, guarda):
    """**El test central de R29, ejecutado.** Con R33 entero delante, ni un
    texto, nombre, teléfono, correo, código ni referencia en la consola."""
    for codigo, consola, _ in (obra_entera, guarda):
        assert codigo == 0, consola
        assert [valor for valor in VALORES_DE_LAS_FILAS if valor in consola] == []


@necesita_powershell
def test_f065_r29_ejecutado_manda_a_la_pasarela_el_texto_de_design(obra_entera):
    """Las tres lecturas, en orden: las dos formas del código; la de §3 tal
    cual (en LF), con sus cuatro parámetros, el techo y `-Tolerante`; y la de
    las fechas, con la forma que guarda Sigrid."""
    _, _, llamadas = obra_entera

    assert [sql for sql, _ in llamadas] == [SQL_FORMAS, SQL_DE_LA_OBRA, SQL_FECHAS]
    assert [apunte for _, apunte in llamadas] == [
        _apunte(10, False, "0999", "999"),
        _apunte(500000, True, "RCPCLI", "PVI-%", 708, "0999"),
        _apunte(1, True, 708, "0999"),
    ]


@necesita_powershell
def test_f065_r29_ejecutado_cuenta_lo_que_pide_r29(obra_entera):
    """Las cuentas de R29 sobre las catorce filas inventadas, una por una."""
    _, consola, _ = obra_entera
    filas = _filas()
    esperado = {
        "obras con ese codigo y unidades de posventa": "2",
        "la pasarela acepto la consulta, sin truncated": "si",
        "truncated": "no",
        "filas": "14",
        "filas por debajo del techo": "si",
        "columnas de la respuesta": "31",
        "bytes de la respuesta, todos los campos": str(_bytes_json(filas)),
        "bytes de los campos de R33": str(sum(_bytes_json(f[12:]) - 1 for f in filas)),
        "obras distintas en las filas": "2",
        "estado PTE": "2",
        "estado SAT": "4",
        "estado TER": "2",
        "estado CER": "2",
        "estado NPR": "1",
        "otro estado": "2",
        "sin estado": "1",
        "antiguedad: menos de 6 meses": "4",
        "antiguedad: de 6 a 12 meses": "2",
        "antiguedad: de 12 a 24 meses": "2",
        "antiguedad: mas de 24 meses": "4",
        "antiguedad: sin fecha legible": "2",
        "unidades con reclamaciones": "5",
        "reclamaciones por unidad: minimo": "1",
        "reclamaciones por unidad: mediana": "3",
        "reclamaciones por unidad: maximo": "4",
        "sin oficio": "1",
        "sin ubicacion": "5",
        "con referencia PVI-": "1",
        "grupos unidad+oficio+ubicacion con mas de una": "3",
        "reclamaciones en esos grupos": "8",
        "pares de la misma unidad comparados": "15",
        "pares con parecido >= 40": "5",
        "pares con parecido >= 50": "4",
        "pares con parecido >= 60": "3",
        "con.fec igual a rcp.fec": "3",
        "rcp.fec posterior a con.fec": "1",
        "rcp.fec anterior a con.fec": "0",
        "rcp.fec vacia": "0",
        "con.fec vacia": "0",
    }
    for nombre, _ in CAMPOS_R33:
        esperado[f"R33 rellenos: {nombre}"] = "2"
    esperado["R33 rellenos: descripcion larga"] = "14"
    esperado["R33 rellenos: forma de comunicacion"] = "14"

    tabla = _veredicto(consola)
    assert {clave: tabla.get(clave) for clave in esperado} == esperado
    assert "MEDICION DE LA OBRA : PASA" in consola


@necesita_powershell
def test_f065_r70_ejecutado_la_guarda_manda_su_texto_y_solo_cuenta(guarda):
    """Con `-Unidades` (una lista con comas y un hueco, como la entrega
    `powershell -File`): la consulta de §15.5 con dos marcadores, las unidades
    detrás de los cuatro de siempre, y solo filas, bytes y cuántas unidades."""
    _, consola, llamadas = guarda
    filas = _filas()
    tabla = _veredicto(consola)

    assert [sql for sql, _ in llamadas] == [
        SQL_FORMAS,
        SQL_DE_UNA_UNIDAD.replace("u.cod IN (?)", "u.cod IN (?, ?)"),
    ]
    assert llamadas[1][1] == _apunte(500000, True, "RCPCLI", "PVI-%", 708, "0999", "VILLA 05", "VILLA 07")
    assert tabla["filas"] == "14"
    assert tabla["columnas de la respuesta"] == "12"
    assert tabla["unidades pedidas"] == "2"
    assert tabla["bytes de la respuesta, todos los campos"] == str(_bytes_json([f[:12] for f in filas]))
    assert not [clave for clave in tabla if clave.startswith(("R33", "estado", "pares", "bytes de los campos"))]
    assert "MEDICION DE LA GUARDA : PASA" in consola


@necesita_powershell
def test_f065_r29_ejecutado_si_la_pasarela_la_rechaza_no_pasa(tmp_path):
    """Un `OUTER APPLY` rechazado (o un `truncated`): se dice, no se cuenta
    nada, y el veredicto sale 6, no un `exit` a medias del común."""
    codigo, consola, _ = _lanzar(tmp_path, F065_RECHAZO="1")
    tabla = _veredicto(consola)

    assert codigo == 6, consola
    assert tabla["la pasarela acepto la consulta, sin truncated"] == "no"
    assert "filas" not in tabla
    assert "NO PASA" in consola


@necesita_powershell
def test_f065_r29_ejecutado_un_texto_en_una_cifra_para_sin_repetirlo(tmp_path):
    """Si a `Anotar-Cifra` le llega un texto (aquí, el recuento de obras), el
    script para con 5 y el texto no sale por la consola."""
    codigo, consola, _ = _lanzar(tmp_path, F065_OBRAS_TEXTO="1")

    assert codigo == 5, consola
    assert "Secreto" not in consola
    assert "no ha salido como cifra" in consola


@necesita_powershell
def test_f065_r8_r29_ejecutado_llegar_al_techo_no_es_quedar_por_debajo(tmp_path):
    """R8: «con ese número de filas **o más**», 409. Con `-MaxFilas` igual a las
    filas que llegan, la medición lo dice y no pasa."""
    codigo, consola, _ = _lanzar(tmp_path, "-MaxFilas", "14")
    tabla = _veredicto(consola)

    assert codigo == 6, consola
    assert tabla["filas"] == "14"
    assert tabla["filas por debajo del techo"] == "no"


#: Cada rechazo de las precondiciones: (id, argumentos, `-CodigoObra`, el
#: trozo del mensaje que dice cuál ha saltado). 51 = `$MAX_UNIDADES` + 1.
PARAMETROS_MALOS = [
    ("maxfilas_0", ("-MaxFilas", "0"), "999", "-MaxFilas va de 1 a 500000"),
    ("maxfilas_500001", ("-MaxFilas", "500001"), "999", "-MaxFilas va de 1 a 500000"),
    ("unidades_vacia", ("-Unidades", " , "), "999", "-Unidades sin ninguna unidad"),
    ("unidades_51", ("-Unidades", ",".join(f"U{n:02d}" for n in range(51))), "999",
     "-Unidades admite como mucho 50 unidades"),
    ("obra_no_valida", (), "0 9", "El codigo de obra solo admite"),
    ("sin_obra", (), None, "Falta -CodigoObra"),
]


@necesita_powershell
@pytest.mark.parametrize(
    ("argumentos", "obra", "mensaje"),
    [pytest.param(a, o, m, id=i) for i, a, o, m in PARAMETROS_MALOS],
)
def test_f065_r29_r70_ejecutado_un_parametro_malo_para_antes_de_leer(tmp_path, argumentos, obra, mensaje):
    """**La puerta va antes del ERP** (regla 7 del protocolo, C-A1-1 de la
    review). Con un parámetro malo el script para con 3 y **no llega ni a
    Q0**: el lector doble no apunta ninguna llamada. Que la línea exista no
    basta; si una comprobación baja por debajo de la lectura, la pasarela de
    producción ya habría recibido un `max_rows` fuera de rango o una guarda
    con 51 marcadores."""
    codigo, consola, llamadas = _lanzar(tmp_path, *argumentos, obra=obra)

    assert codigo == 3, consola
    assert llamadas == []
    assert mensaje in consola, consola
