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

import re
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
    for variable in llamadas:
        assert re.search(rf"\{variable} = ConvertTo-SqlConLf\b", ejecutable), (
            f"{variable} no pasa por ConvertTo-SqlConLf"
        )


def test_f065_r29_los_parametros_van_en_el_orden_de_los_marcadores():
    """`RCPCLI`, `PVI-%`, el tipo y la obra (§3); y el techo de la pasarela."""
    ejecutable = _ejecutable()

    assert '$CAMPO_REFERENCIA = "RCPCLI"' in ejecutable
    assert '$PATRON_NUESTROS = "PVI-%"' in ejecutable
    assert "[int]$Tip = 708" in ejecutable
    assert "$parametros = @($CAMPO_REFERENCIA, $PATRON_NUESTROS, $Tip, $obraCod)" in ejecutable
    assert "-Parametros $parametros" in ejecutable
    assert "[int]$MaxFilas = 500000" in ejecutable
    assert "$TECHO_PASARELA = 500000" in ejecutable
    assert "-MaxFilas $MaxFilas" in ejecutable
    assert "if ($MaxFilas -lt 1 -or $MaxFilas -gt $TECHO_PASARELA)" in ejecutable


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
    assert "$COLUMNAS_DE_LA_OBRA = 31" in ejecutable
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
    assert "$PRIMERA_COLUMNA_R33 = 12" in ejecutable


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
        assert constante in ejecutable, f"falta «{constante}»"
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
