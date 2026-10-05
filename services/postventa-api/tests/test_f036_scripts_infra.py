# services/postventa-api/tests/test_f036_scripts_infra.py
"""El script de medicion de F-036 cumple su contrato (T1; R90, R107, R109, R110).

`infra/26_catalogos_plantilla_sigrid.ps1` lo lanza **una persona** contra el ERP
de produccion (T2), asi que lo que se fija aqui es, sobre todo, lo que **no**
puede hacer. Mismo planteamiento que `test_f013_scripts_infra.py`: es
PowerShell, no entra en la cobertura ni en la campana de mutacion
—`harness/alcance.py` solo mide `.py`— y una revision a ojo no sobrevive a la
siguiente edicion.

- **Solo `POST /api/sql/read`**, a traves de `08_lectura_sigrid_comun.ps1`. Ni
  HTTP propio, ni `sql/write`, ni una sentencia que escriba, y solo `SELECT`
  (el guardia de la pasarela no admite `WITH`).
- **Ningun `ide` ni `cif` en ninguna salida**: el `ide` de la obra solo viaja
  como parametro de las lecturas; el CIF solo entra en la expresion que lo
  normaliza (`design.md` §6.3) y lo que sale es un recuento o la marca opaca
  del `DENSE_RANK` (R90).
- **Nombres solo con `-MostrarNombres`**: los de la obra y las unidades pasan
  por la misma mascara que `24_ubicacion_sigrid.ps1`; los de proveedor no se
  imprimen nunca (solo van al JSON).
- **`-SalidaJson` fuera del repositorio**: el JSON lleva nombres de proveedor.
- **Ningun valor dentro** (ni GUID, ni host, ni credencial), **CRLF y ASCII
  puro, sin BOM**, y la ruta en la primera linea, como el resto de `infra/`.

Este fichero no contiene ningun identificador ni ningun host: los controles
negativos se componen en memoria a partir de trozos.
"""

from __future__ import annotations

import re
from pathlib import Path

#: Raiz del repositorio, tres niveles por encima de este fichero.
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

#: El directorio de los scripts re-ejecutables.
INFRA = RAIZ / "infra"

#: T1 · el catalogo de la plantilla de una obra, medido en Sigrid. Solo lectura.
SCRIPT = INFRA / "26_catalogos_plantilla_sigrid.ps1"

#: El de F-013, de donde se copia la mascara de nombres.
SCRIPT_UBICACION = INFRA / "24_ubicacion_sigrid.ps1"

#: La lectura compartida por todos los scripts que preguntan a `sigrid-api`.
COMUN = INFRA / "08_lectura_sigrid_comun.ps1"

#: La marca de orden de bytes de UTF-8.
BOM = b"\xef\xbb\xbf"

#: La forma de un GUID.
PATRON_GUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

#: Hosts de Azure: el PostgreSQL compartido y la pasarela.
PATRON_HOST_AZURE = re.compile(
    r"[\w-]+\.(?:postgres\.database|azurewebsites)\.(?:azure\.com|net)",
    re.IGNORECASE,
)

#: El host del inquilino de SharePoint, compuesto a trozos.
PATRON_HOST_SHAREPOINT = re.compile(
    r"[a-z0-9][a-z0-9-]*" + r"\." + "share" + r"point\.com", re.IGNORECASE
)

#: Una credencial escrita a mano en el propio fichero.
PATRON_CREDENCIAL = re.compile(
    r"(?i)\b(?:password|pwd|passwd|secret|token|api[_-]?key|clave)\s*=\s*[\"'][^\"'$]",
)

#: Un codigo de reclamacion real, con la forma que usa Sigrid.
PATRON_INCIDENCIA_REAL = re.compile(r"\bRS\d{2}\.\d{2}/\d{4}\b")

#: Sentencias que escribirian en el ERP.
PATRON_SQL_QUE_ESCRIBE = re.compile(
    r"\b(?:INSERT\s+INTO|UPDATE\s+\w|DELETE\s+FROM|MERGE\s+|EXEC(?:UTE)?\s|TRUNCATE\s|DROP\s|ALTER\s)",
    re.IGNORECASE,
)

#: La normalizacion del CIF de `design.md` §6.3, caracter a caracter (en una linea).
NORMALIZACION_CIF = (
    "UPPER(REPLACE(REPLACE(REPLACE(LTRIM(RTRIM(pv.cif)), '-', ''), ' ', ''), '.', ''))"
)

#: La unica otra forma en que el CIF puede aparecer: para saber si esta vacio.
CIF_VACIO = "NULLIF(LTRIM(RTRIM(pv.cif)), '')"

#: Las claves del JSON de `-SalidaJson`: `design.md` §10.3 y §16.2.
CLAVES_JSON = {
    "obra",
    "codigo",
    "nombre",
    "unidades",
    "oficios_obra",
    "oficio_codigo",
    "oficio_nombre",
    "proveedor_codigo",
    "proveedor_nombre",
    "marca_cif",
    "oficios_catalogo",
    "familias_proveedor",
    "familia_codigo",
    "familia_nombre",
    "homolo",
    "familias_catalogo",
    # T1 bis (2026-09-28): las actividades, `conact` -> `auxpronat`.
    "actividades_proveedor",
    "actividad_codigo",
    "actividades_catalogo",
    "pos",
    "fecbaj",
}

#: Las marcas de ambito que admiten las plantillas de SQL.
MARCAS_AMBITO = {"PROVEEDORES", "OFICIOS", "FILAS"}


def _bytes() -> bytes:
    return SCRIPT.read_bytes()


def _texto(script: Path = SCRIPT) -> str:
    """El script como texto (`utf-8-sig`: si alguien le pone un BOM, el test
    que lo prohibe lo dice por su nombre en vez de reventar aqui)."""
    return script.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def _sin_ayuda(texto: str) -> str:
    """El script sin su bloque de ayuda `<# ... #>`."""
    return re.sub(r"<#.*?#>", "", texto, flags=re.DOTALL)


def _sin_comentarios(texto: str) -> str:
    """El ejecutable: sin la ayuda y sin las lineas de comentario."""
    return "\n".join(
        linea
        for linea in _sin_ayuda(texto).splitlines()
        if not linea.lstrip().startswith("#")
    )


def _funcion(texto: str, nombre: str) -> str:
    """El cuerpo de una funcion PowerShell, de `function X {` a la `}` de la columna 0."""
    encontrado = re.search(
        rf"^function {re.escape(nombre)} \{{\n.*?^\}}", texto, re.DOTALL | re.MULTILINE
    )
    assert encontrado, f"no encuentro la funcion {nombre}"
    return encontrado.group(0)


def _sqls() -> dict[str, str]:
    """Cada consulta del script: `$sqlX = @' ... '@` (literal, sin interpolar)."""
    return dict(
        re.findall(r"^\$(sql\w+) = @'\n(.*?)\n'@", _texto(), re.DOTALL | re.MULTILINE)
    )


def _plantillas() -> dict[str, str]:
    """Las consultas que llevan una marca de ambito (`{PROVEEDORES}`...)."""
    return {nombre: sql for nombre, sql in _sqls().items() if re.search(r"\{[A-Z_]+\}", sql)}


def _fragmentos() -> dict[str, str]:
    """Los trozos de SQL que sustituyen a las marcas, por `MARCA|ambito`."""
    bloque = re.search(r"^\$Fragmentos = @\{\n(.*?)\n\}", _texto(), re.DOTALL | re.MULTILINE)
    assert bloque, "el script no declara $Fragmentos"
    return dict(re.findall(r'^\s*"([A-Z_]+\|\w+)"\s*=\s*"([^"]*)"', bloque.group(1), re.MULTILINE))


def _plano(texto: str) -> str:
    """El SQL en una linea: espacios colapsados y sin el blanco junto a un parentesis."""
    return re.sub(r"\s+", " ", texto).replace("( ", "(").replace(" )", ")")


def _lineas_que_imprimen() -> list[str]:
    return [linea for linea in _sin_comentarios(_texto()).splitlines() if "Write-Host" in linea]


# --------------------------------------------------------------------------
# Existe, y es como el resto de `infra/`
# --------------------------------------------------------------------------


def test_f036_t1_el_script_existe():
    """Sin el, T2 se haria a mano contra el ERP de produccion."""
    assert SCRIPT.is_file()


def test_f036_t1_sin_bom_como_el_resto_de_infra():
    """`test_f010_prompt_keys_infra.py` lee todos los `.ps1` como `ascii`."""
    assert not _bytes().startswith(BOM)


def test_f036_t1_crlf_en_todas_las_lineas():
    """`docs/CONVENTIONS.md`: PowerShell con CRLF, sin un solo LF suelto."""
    crudo = _bytes()

    assert b"\r\n" in crudo
    assert crudo.count(b"\n") == crudo.count(b"\r\n")


def test_f036_t1_contenido_ascii_puro():
    """Un acento en una consola de PowerShell 5.1 sale como dos caracteres raros."""
    assert all(byte < 128 for byte in _bytes())


def test_f036_t1_empieza_por_su_ruta_relativa():
    """`docs/CONVENTIONS.md`: primera linea, la ruta del fichero."""
    assert _texto().splitlines()[0] == f"# infra/{SCRIPT.name}"


def test_f036_t1_se_lanza_desde_cualquier_sitio():
    """Rutas desde `$PSScriptRoot` y `Set-Location` a la raiz del repositorio."""
    ejecutable = _sin_comentarios(_texto())

    assert "$PSScriptRoot" in ejecutable
    assert "Set-Location" in ejecutable
    assert '$ErrorActionPreference = "Stop"' in ejecutable


def test_f036_t1_carga_el_comun_de_lectura():
    """Veredicto, codigos de salida, TLS 1.2 y la unica ruta HTTP salen del 08."""
    ejecutable = _sin_comentarios(_texto())

    assert '. "$PSScriptRoot\\08_lectura_sigrid_comun.ps1"' in ejecutable
    assert "Escribir-Veredicto" in ejecutable


def test_f036_t1_los_parametros_del_encargo():
    """`tasks.md` T1: `-CodigoObra`, `-SalidaJson`, `-MostrarNombres`, `-SinGlobal`."""
    ejecutable = _sin_comentarios(_texto())

    for parametro in (
        "[string]$CodigoObra",
        "[string]$SalidaJson",
        "[switch]$MostrarNombres",
        "[switch]$SinGlobal",
        "[switch]$WhatIf",
    ):
        assert parametro in ejecutable, parametro


def test_f036_t1_sin_codigo_de_obra_no_pregunta_nada():
    """`-CodigoObra` es obligatorio: sin el, para antes de la primera lectura."""
    ejecutable = _sin_comentarios(_texto())

    assert "Falta -CodigoObra" in ejecutable
    assert ejecutable.index("Falta -CodigoObra") < ejecutable.index("Invoke-SigridLectura -")


def test_f036_t1_whatif_no_llama_a_nada():
    """`-WhatIf` imprime lo que haria y sale antes de la primera llamada."""
    ejecutable = _sin_comentarios(_texto())

    assert "no se ha llamado a nada" in ejecutable
    assert ejecutable.index("if ($WhatIf)") < ejecutable.index("Invoke-SigridLectura -")
    assert ejecutable.index("if ($WhatIf)") < ejecutable.index("Get-SigridClave")


# --------------------------------------------------------------------------
# Ningun valor dentro
# --------------------------------------------------------------------------


def test_f036_t1_sin_guid():
    assert PATRON_GUID.findall(_texto()) == []


def test_f036_t1_sin_host():
    """La raiz de la pasarela entra por parametro o por la sesion, nunca escrita aqui."""
    assert PATRON_HOST_AZURE.findall(_texto()) == []
    assert PATRON_HOST_SHAREPOINT.findall(_texto()) == []


def test_f036_t1_sin_credencial_ni_codigo_real():
    texto = _texto()

    assert PATRON_CREDENCIAL.findall(texto) == []
    assert PATRON_INCIDENCIA_REAL.findall(texto) == []


def test_f036_t1_no_imprime_un_secreto():
    """Ninguna linea que imprime nombra la clave de la pasarela."""
    culpables = [
        linea.strip()
        for linea in _lineas_que_imprimen()
        if re.search(r"\$(clave|token|secreto)\b", linea, re.IGNORECASE)
    ]

    assert culpables == []


# --------------------------------------------------------------------------
# Solo lectura
# --------------------------------------------------------------------------


def test_f036_t1_solo_lee_por_sql_read():
    """La regla dura: en Sigrid, desde un puesto, solo lecturas.

    La unica llamada es `Invoke-SigridLectura` del comun, que solo conoce
    `POST /api/sql/read`.
    """
    ejecutable = _sin_comentarios(_texto())

    assert "Invoke-SigridLectura" in ejecutable
    for prohibido in (
        "Invoke-RestMethod",
        "Invoke-WebRequest",
        "sql/write",
        "concepto-grafico",
        "partes-reclamacion",
        "System.Net.WebClient",
        "HttpClient",
    ):
        assert prohibido not in ejecutable, prohibido
    assert PATRON_SQL_QUE_ESCRIBE.findall(ejecutable) == []


def test_f036_t1_no_ejecuta_python_ni_nada_de_fuera():
    """Todo se calcula en SQL: ni Python (`-c` rompe en PowerShell 5.1, F-029), ni `az`."""
    ejecutable = _sin_comentarios(_texto())

    assert "Invoke-PythonDelServicio" not in ejecutable
    assert not re.search(r"\$python\b", ejecutable, re.IGNORECASE)
    assert not re.search(r"^\s*az\s", ejecutable, re.MULTILINE)
    assert "Start-Process" not in ejecutable


def test_f036_t1_hay_consultas_y_todas_son_select():
    """El guardia de la pasarela solo admite `SELECT` (`sigrid_api.md` §5.1): nada de `WITH`."""
    consultas = _sqls()

    assert len(consultas) >= 15
    for nombre, sql in consultas.items():
        assert sql.lstrip().upper().startswith("SELECT"), nombre
        assert ";" not in sql, nombre
        assert "$" not in sql, nombre


def test_f036_t1_las_consultas_son_literales():
    """Todas con here-string de comilla simple: PowerShell no interpola nada dentro."""
    texto = _texto()

    assert not re.search(r'^\$sql\w+ = @"', texto, re.MULTILINE)
    assert not re.search(r'^\$sql\w+ = "', texto, re.MULTILINE)


def test_f036_t1_el_codigo_de_obra_solo_viaja_como_parametro():
    """El codigo se pregunta con `?` y nunca se pega en el SQL (`sigrid_api.md` §5.2)."""
    ejecutable = _sin_comentarios(_texto())

    assert "LTRIM(RTRIM(o.cod)) = ?" in _sqls()["sqlUnidades"]
    assert "-Parametros @($codigo)" in ejecutable
    for linea in ejecutable.splitlines():
        if "$codigo" in linea:
            assert not re.search(r"(?i)\$sql|\.Replace\(|\$Fragmentos", linea), linea


def test_f036_t1_nunca_pide_mas_de_mil_filas():
    """`sigrid-api` sirve como maximo 1.000 filas por peticion."""
    ejecutable = _sin_comentarios(_texto())

    assert "$MaxFilas = 1000" in ejecutable
    for valor in re.findall(r"-MaxFilas\s+(\d+)", ejecutable):
        assert int(valor) <= 1000


# --------------------------------------------------------------------------
# Las plantillas de ambito: obra, todos los `obrofc` y el maestro
# --------------------------------------------------------------------------


def test_f036_t1_las_plantillas_no_llevan_parametros_propios():
    """Cada `?` de una consulta con ambito sale de un fragmento de obra.

    Asi el script puede rellenarlos todos con el `ide` de la obra sin
    equivocarse de orden: una plantilla con un `?` propio lo romperia.
    """
    plantillas = _plantillas()

    assert plantillas
    for nombre, sql in plantillas.items():
        assert "?" not in sql, nombre
        assert set(re.findall(r"\{([A-Z_]+)\}", sql)) <= MARCAS_AMBITO, nombre


def test_f036_t1_los_fragmentos_de_ambito():
    """Solo los fragmentos de obra llevan `?` (el `ide` de la obra, uno cada uno)."""
    fragmentos = _fragmentos()

    assert set(fragmentos) == {
        "PROVEEDORES|obra",
        "PROVEEDORES|obrofc",
        "PROVEEDORES|maestro",
        "OFICIOS|obra",
        "OFICIOS|obrofc",
        "OFICIOS|maestro",
        "FILAS|obra",
        "FILAS|obrofc",
    }
    for clave, sql in fragmentos.items():
        assert sql.upper().startswith("SELECT "), clave
        if clave.endswith("|obra"):
            assert sql.count("?") == 1, clave
            assert "ob.obride = ?" in sql, clave
        else:
            assert "?" not in sql, clave


def test_f036_t1_el_ide_de_la_obra_solo_va_a_los_parametros():
    """El `ide` de la obra se lee para preguntar por ella y para nada mas.

    Cada linea que lo nombra es la que lo asigna o la que lo pasa como
    parametro; ninguna lo imprime ni lo guarda en el JSON.
    """
    ejecutable = _sin_comentarios(_texto())
    lineas = [linea.strip() for linea in ejecutable.splitlines() if "$obraIde" in linea]

    assert lineas
    for linea in lineas:
        assert re.fullmatch(
            r"\$obraIde = \[long\]\S.*|\$parametros \+= \$obraIde|.*-Parametros @\(\$obraIde\).*",
            linea,
        ), linea


# --------------------------------------------------------------------------
# Ningun `ide` ni `cif` en ninguna salida (R90)
# --------------------------------------------------------------------------


def test_f036_r90_el_cif_solo_entra_normalizado():
    """R90 · el CIF no sale: solo la expresion de §6.3 y la prueba de vacio lo tocan."""
    texto = _plano(_sin_comentarios(_texto()))
    sin_expresiones = texto.replace(NORMALIZACION_CIF, "").replace(CIF_VACIO, "")

    assert NORMALIZACION_CIF in texto
    assert re.findall(r"(?i)\.cif\b", sin_expresiones) == []


def test_f036_r90_la_marca_de_cif_es_la_de_design():
    """R90, `design.md` §6.3 · la marca opaca es el `DENSE_RANK` del CIF normalizado."""
    sql = _plano(_sqls()["sqlOficiosObraJson"])

    assert (
        "CASE WHEN " + CIF_VACIO + " IS NULL THEN NULL "
        "ELSE DENSE_RANK() OVER (ORDER BY " + NORMALIZACION_CIF + ") END AS marca_cif"
    ) in sql
    assert "WHERE f.obride = ? AND ISNULL(a.fecbaj, 0) = 0" in sql


def test_f036_r90_los_grupos_por_cif_se_cuentan_en_sql():
    """R90 · los grupos que comparten CIF se cuentan con `GROUP BY` y salen sin el CIF."""
    sql = _plano(_sqls()["sqlGruposCif"])

    assert NORMALIZACION_CIF in sql
    assert "GROUP BY" in sql
    assert sql.startswith("SELECT g.n AS tamano, COUNT(*) AS grupos ")


def test_f036_t1_ninguna_columna_devuelta_es_un_ide_salvo_la_obra():
    """De Sigrid solo vuelve un `ide`: el de la obra, que no sale del script."""
    alias = [
        a
        for sql in _sqls().values()
        for a in re.findall(r"(?i)\bAS\s+(\w+)", sql)
    ]

    assert [a for a in alias if re.search(r"(?i)ide$", a) and a != "ide"] == ["obra_ide"]
    assert {a for a in alias if "cif" in a.lower()} <= {"marca_cif", "proveedores_sin_cif"}


def test_f036_t1_ninguna_linea_que_imprime_nombra_un_ide_o_un_cif():
    """Ni una variable `...Ide` ni una `...Cif` en lo que se imprime."""
    culpables = [
        linea.strip()
        for linea in _lineas_que_imprimen()
        if re.search(r"(?i)\$\w*(?:ide|cif)\b", linea) or "obra_ide" in linea or "marca_cif" in linea
    ]

    assert culpables == []


def test_f036_t1_las_claves_del_json_son_las_de_design():
    """`design.md` §10.3 y §16.2: la forma del JSON, y ninguna clave con `ide` ni `cif` a secas."""
    funcion = _funcion(_texto(), "New-CatalogoJson")
    claves = set(re.findall(r"^\s*(\w+) = ", funcion, re.MULTILINE)) - {"catalogo"}
    claves = {clave for clave in claves if not clave.startswith("$")}

    assert claves == CLAVES_JSON
    assert not [clave for clave in claves if clave.endswith("ide") or clave == "cif"]


# --------------------------------------------------------------------------
# Nombres solo con `-MostrarNombres`
# --------------------------------------------------------------------------


def test_f036_t1_la_mascara_es_la_del_24():
    """Dos copias de la mascara que divergen son dos criterios de «nombre»."""
    for funcion in ("ConvertTo-FormaSinNombres", "Format-Nombre"):
        assert _funcion(_texto(), funcion) == _funcion(_texto(SCRIPT_UBICACION), funcion), funcion


def test_f036_t1_los_nombres_de_obra_y_unidad_salen_por_la_mascara():
    """Cada `.Codigo` / `.Nombre` que se imprime pasa por `Format-Nombre`."""
    culpables = []
    for linea in _lineas_que_imprimen():
        for encontrado in re.finditer(r"\$\w+\.(?:Nombre|Codigo|Res|Cod)\b", linea):
            antes = linea[: encontrado.start()]
            if not antes.rstrip("( ").endswith(("Format-Nombre", "ConvertTo-FormaSinNombres")):
                culpables.append(linea.strip())

    assert culpables == []


def test_f036_t1_los_nombres_de_proveedor_no_se_imprimen():
    """Los nombres de proveedor solo van al JSON, nunca a la consola."""
    for linea in _lineas_que_imprimen():
        assert "proveedor_nombre" not in linea
        assert not re.search(r"\bp\.res\b", linea), linea


# --------------------------------------------------------------------------
# Lo que se mide (`tasks.md` T1, `design.md` §15.7 y §16.2, R109)
# --------------------------------------------------------------------------


def test_f036_t1_unidades_de_la_obra_como_en_design():
    """§6.3 · unidades (`upv`) de las obras con ese codigo, comparado literal."""
    sql = _sqls()["sqlUnidades"]

    assert "FROM dbo.upv v" in sql
    assert "JOIN dbo.con o ON o.ide = v.obride" in sql
    assert "JOIN dbo.con u ON u.ide = v.ide" in sql


def test_f036_t1_mide_obrofc_de_la_obra():
    """Filas, oficios, oficios de baja, proveedores y oficios con varios proveedores."""
    resumen = _sqls()["sqlObrofcResumen"]
    varios = _sqls()["sqlOficiosVariosProveedores"]
    lista = _sqls()["sqlOficiosDeLaObra"]

    for columna in ("filas", "oficios", "oficios_de_baja", "proveedores"):
        assert f"AS {columna}" in resumen, columna
    assert "fecbaj" in resumen
    assert "HAVING COUNT(DISTINCT f.prvide) > 1" in varios
    assert "a.cod AS oficio_cod" in lista and "a.res AS oficio_res" in lista


def test_f036_t1_nombres_parecidos_sin_mayusculas_ni_tildes():
    """§15.7 · grupos de nombre igual con `COLLATE Latin1_General_CI_AI`, en los dos catalogos."""
    proveedores = _sqls()["sqlGruposNombreProveedor"]
    oficios = _sqls()["sqlGruposNombreOficio"]

    assert "COLLATE Latin1_General_CI_AI" in proveedores
    assert "COLLATE Latin1_General_CI_AI" in oficios
    assert "{PROVEEDORES}" in proveedores
    assert "{OFICIOS}" in oficios


def test_f036_t1_ubicaciones_y_espacios():
    """Las 60 `rcp.resubi` mas frecuentes de la obra y los valores de `upv.espacios`."""
    ubicaciones = _sqls()["sqlUbicaciones"]
    espacios = _sqls()["sqlEspacios"]

    assert "SELECT TOP (60)" in ubicaciones
    assert "r.resubi" in ubicaciones
    assert "JOIN dbo.upv v ON v.ide = r.upvide" in ubicaciones
    assert "v.espacios" in espacios


def test_f036_r109_mide_las_familias():
    """R109 · `confam`, el cruce por codigo con `auxofc`, `entfam` y `prv.ofcide`."""
    sqls = _sqls()

    assert "dbo.confam" in sqls["sqlFamiliasResumen"]
    assert "homolo" in sqls["sqlFamiliasResumen"]
    assert "fecbaj" in sqls["sqlFamiliasResumen"]
    assert "familias" in sqls["sqlFamiliasDistribucion"]
    assert "fa.cod = a.cod" in _plano(sqls["sqlCruceCatalogos"])
    assert "{PROVEEDORES}" in sqls["sqlCruceObra"] and "{OFICIOS}" in sqls["sqlCruceObra"]
    assert "{FILAS}" in sqls["sqlFamiliasCubren"]
    assert "fa.cod = a.cod" in _plano(sqls["sqlFamiliasCubren"])
    assert "fampro" in sqls["sqlEntfam"] and "fament" in sqls["sqlEntfam"]
    assert "pv.ofcide" in sqls["sqlOficioFicha"]


def test_f036_t1_lo_global_solo_sin_singlobal():
    """Lo global va entero dentro de `if (-not $SinGlobal)`, y antes del JSON."""
    ejecutable = _sin_comentarios(_texto())

    inicio = ejecutable.index("if (-not $SinGlobal) {")
    fin = ejecutable.index("\n}", inicio)
    bloque = ejecutable[inicio:fin]
    fuera = ejecutable[:inicio] + ejecutable[fin:]

    for ambito in ('-Ambito "obrofc"', '-Ambito "maestro"'):
        assert ambito in bloque, ambito
        assert ambito not in fuera, ambito


# --------------------------------------------------------------------------
# `-SalidaJson`: fuera del repositorio, y con la forma de §10.3
# --------------------------------------------------------------------------


def test_f036_t1_el_json_no_cae_dentro_del_repositorio():
    """El JSON lleva nombres de proveedor: fuera del repositorio o nada.

    La comprobacion va **antes** de la primera lectura: si la ruta no vale, no
    se ha preguntado nada.
    """
    ejecutable = _sin_comentarios(_texto())

    assert "fuera del repositorio" in ejecutable
    assert ejecutable.index("fuera del repositorio") < ejecutable.index("Invoke-SigridLectura -")
    assert (
        "    if ($rutaJson.StartsWith($raizCompleta + \"\\\", "
        "[StringComparison]::OrdinalIgnoreCase) -or\n"
        "        $rutaJson -ieq $raizCompleta) {"
    ) in ejecutable


def test_f036_t1_solo_escribe_el_json():
    """Una sola escritura en disco, la del JSON, y solo con `-SalidaJson`."""
    ejecutable = _sin_comentarios(_texto())

    for prohibido in ("Export-Csv", "Out-File", "Set-Content", "Add-Content", "New-Item"):
        assert prohibido not in ejecutable, prohibido
    assert ejecutable.count("WriteAllText") == 1
    escritura = ejecutable.index("WriteAllText")
    assert ejecutable.rfind("if ($rutaJson", 0, escritura) != -1


def test_f036_t1_todo_auxofc_en_el_json_paginado():
    """§10.3 · `oficios_catalogo` es **todo** `auxofc`: se pagina por `ide` (`sigrid_api.md` §6.4)."""
    sql = _sqls()["sqlOficiosCatalogoJson"]

    assert "FROM dbo.auxofc a" in sql
    assert "ORDER BY a.ide" in sql
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql


def test_f036_r107_las_familias_de_los_proveedores_de_la_obra():
    """R107 · codigos y nombres de familia y `homolo`; del proveedor, solo su codigo."""
    sql = _plano(_sqls()["sqlFamiliasProveedorJson"])

    assert "SELECT p.cod AS proveedor_codigo, fa.cod AS familia_codigo, fa.res AS familia_nombre, cf.homolo AS homolo" in sql
    assert "WHERE cf.conide IN (SELECT f.prvide FROM dbo.obrofc f WHERE f.obride = ?)" in sql
    assert "ISNULL(fa.fecbaj, 0) = 0" in sql
    assert not re.search(r"\bp\.res\b", sql)


# --------------------------------------------------------------------------
# Controles negativos: un patron que nunca se ha visto saltar no protege nada
# --------------------------------------------------------------------------


def test_f036_t1_el_barrido_de_sql_caza_una_escritura_inyectada():
    assert PATRON_SQL_QUE_ESCRIBE.findall("UPDATE dbo.con SET est = 1")
    assert PATRON_SQL_QUE_ESCRIBE.findall("EXEC dbo.algo")
    assert PATRON_SQL_QUE_ESCRIBE.findall("SELECT a.cod FROM dbo.auxofc a") == []


def test_f036_t1_el_barrido_de_host_caza_uno_inyectado():
    inventado = "algo-inventado" + "." + "azure" + "websites" + ".net"

    assert PATRON_HOST_AZURE.findall(f"https://{inventado}/api") == [inventado]


def test_f036_r90_el_barrido_de_cif_caza_uno_suelto():
    """Control negativo: un `pv.cif` fuera de la expresion normalizada salta."""
    suelto = _plano("SELECT pv.cif FROM dbo.prv pv").replace(NORMALIZACION_CIF, "")

    assert re.findall(r"(?i)\.cif\b", suelto) == [".cif"]


def test_f036_t1_el_barrido_de_ide_caza_uno_impreso():
    """Control negativo: imprimir el `ide` de la obra salta."""
    linea = 'Write-Host ("obra {0}" -f $obraIde)'

    assert re.search(r"(?i)\$\w*(?:ide|cif)\b", linea)


# --------------------------------------------------------------------------
# T1 bis · R111: el texto de Sigrid llega en UTF-8, sin doble codificacion
# --------------------------------------------------------------------------
#
# T2 (2026-09-28) encontro `Fontaneria` con la `i` acentuada escrita como
# `C3 83 C2 AD`: la pasarela responde `Content-Type: application/json` SIN
# `charset` (el worker de Python de Azure Functions solo lo anade a los tipos
# `text/*`), e `Invoke-RestMethod` de PowerShell 5.1 decodifica entonces el
# cuerpo como ISO-8859-1. La lectura tiene que decodificar los BYTES como UTF-8
# ella misma, y como la lectura es el 08, se arregla ahi para todos.


def _lectura_comun() -> str:
    """El cuerpo ejecutable de `Invoke-SigridLectura`, sin ayuda ni comentarios."""
    return _sin_comentarios(_funcion(_texto(COMUN), "Invoke-SigridLectura"))


def test_f036_r111_el_comun_no_deja_decodificar_a_invoke_restmethod():
    """R111 · `Invoke-RestMethod` decide el juego de caracteres por la cabecera, y la pasarela no lo manda."""
    lectura = _lectura_comun()

    assert "Invoke-RestMethod" not in lectura
    assert "Invoke-WebRequest" in lectura
    assert "-UseBasicParsing" in lectura


def test_f036_r111_el_comun_decodifica_los_bytes_como_utf8():
    """R111 · los bytes crudos de la respuesta, decodificados como UTF-8 y luego `ConvertFrom-Json`.

    `.Content` es el texto ya decodificado por PowerShell (mal): no se usa.
    """
    lectura = _lectura_comun()

    assert "[Text.Encoding]::UTF8.GetString($web.RawContentStream.ToArray())" in lectura
    assert "ConvertFrom-Json" in lectura
    assert not re.search(r"\$web\.Content\b", lectura)


def test_f036_r111_el_comun_envia_el_cuerpo_en_utf8():
    """R111 · la peticion va en bytes UTF-8 y lo dice: un parametro con tilde no llega en Latin-1."""
    lectura = _lectura_comun()

    assert "$bytesCuerpo = [Text.Encoding]::UTF8.GetBytes($cuerpo)" in lectura
    assert "-Body $bytesCuerpo" in lectura
    assert '-ContentType "application/json; charset=utf-8"' in lectura


def test_f036_r111_el_comun_sigue_leyendo_solo_por_sql_read():
    """La correccion no abre otra ruta: un `POST` a `/api/sql/read`, y nada mas."""
    lectura = _lectura_comun()

    assert '-Uri ($BaseUrl + "/api/sql/read")' in lectura
    assert lectura.count("Invoke-WebRequest") == 1
    assert "-Method Post" in lectura
    assert "sql/write" not in _sin_comentarios(_texto(COMUN))


def test_f036_r111_el_comun_sigue_siendo_ascii_crlf_sin_bom():
    """El 08 lo leen todos los tests de `infra/` como `ascii`, y es PowerShell con CRLF."""
    crudo = COMUN.read_bytes()

    assert not crudo.startswith(BOM)
    assert all(byte < 128 for byte in crudo)
    assert crudo.count(b"\n") == crudo.count(b"\r\n")


def test_f036_r111_ningun_script_llama_a_la_pasarela_por_su_cuenta():
    """R111 · la lectura de la pasarela vive en el 08: ningun otro `.ps1` la llama con
    `Invoke-RestMethod`/`Invoke-WebRequest` (el 07 lo hace desde Python, con `urllib`)."""
    culpables = [
        script.name
        for script in sorted(INFRA.glob("*.ps1"))
        if script != COMUN
        and "/api/sql/read" in _sin_comentarios(_texto(script))
        and re.search(r"Invoke-(?:RestMethod|WebRequest)", _sin_comentarios(_texto(script)))
    ]

    assert culpables == []


def test_f036_r111_el_json_se_escribe_en_utf8_sin_bom():
    """R111 · `WriteAllText` con `UTF8Encoding($false)`: ni el BOM ni el ANSI de `Set-Content`."""
    ejecutable = _sin_comentarios(_texto())

    assert (
        "[IO.File]::WriteAllText($rutaJson, $texto, (New-Object System.Text.UTF8Encoding($false)))"
        in ejecutable
    )


# --------------------------------------------------------------------------
# T1 bis · R109: las actividades, `conact` -> `auxpronat`
# --------------------------------------------------------------------------


def test_f036_r109_mide_las_actividades_de_los_proveedores():
    """R109 (1) y (2) · proveedores con `conact`, cuantas cada uno, `homolo` y de baja."""
    sqls = _sqls()
    resumen = _plano(sqls["sqlActividadesResumen"])
    distribucion = _plano(sqls["sqlActividadesDistribucion"])

    assert "FROM ({PROVEEDORES}) p" in resumen
    assert "LEFT JOIN dbo.conact ca ON ca.conide = p.ide" in resumen
    assert "LEFT JOIN dbo.auxpronat n ON n.ide = ca.actide" in resumen
    for columna in ("con_actividades", "filas", "homologadas", "de_baja", "sin_actividad"):
        assert f"AS {columna}" in resumen, columna
    assert "ISNULL(ca.homolo, 0) <> 0" in resumen
    assert "ISNULL(n.fecbaj, 0) <> 0" in resumen
    assert "{PROVEEDORES}" in distribucion
    assert "COUNT(ca.ide) AS actividades" in distribucion


def test_f036_r109_las_actividades_tambien_en_global():
    """R109 · lo de `conact` se mide en la obra y, salvo `-SinGlobal`, en todos los `obrofc`."""
    ejecutable = _sin_comentarios(_texto())
    inicio = ejecutable.index("if (-not $SinGlobal) {")
    fin = ejecutable.index("\n}", inicio)

    assert 'Write-Actividades -Ambito "obra"' in ejecutable[:inicio]
    assert 'Write-Actividades -Ambito "obrofc"' in ejecutable[inicio:fin]


def test_f036_r109_el_tamano_de_auxpronat():
    """R109 (3) · filas, de baja, codigos y `pos` del catalogo, contados en SQL."""
    sql = _plano(_sqls()["sqlArbolResumen"])

    assert "FROM dbo.auxpronat n" in sql
    for columna in ("filas", "de_baja", "codigos", "sin_codigo", "posiciones", "sin_posicion"):
        assert f"AS {columna}" in sql, columna


def test_f036_r109_el_arbol_se_lee_entero_y_paginado():
    """R109 (3) · para deducir niveles y padres hace falta todo `auxpronat`: por paginas y por `ide`."""
    sql = _plano(_sqls()["sqlActividadesCatalogo"])

    assert sql.startswith(
        "SELECT n.cod AS codigo, n.res AS nombre, n.pos AS pos, n.fecbaj AS fecbaj FROM dbo.auxpronat n"
    )
    assert "ORDER BY n.ide" in sql
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql


def test_f036_r109_el_padre_se_deduce_por_prefijo_del_codigo():
    """R109 (3) · padre = el codigo mas largo del catalogo que es prefijo propio del codigo.

    Si no sale ninguno y todos los codigos miden lo mismo, se prueba con los
    ceros de relleno quitados (`0100` padre de `0101`). Y si tampoco, se dice.
    """
    funcion = _funcion(_texto(), "Get-ArbolActividades")

    assert ".Substring(0, $k)" in funcion
    assert 'TrimEnd("0")' in funcion
    for hipotesis in ('"prefijo"', '"ceros"', '"ninguna"'):
        assert hipotesis in funcion, hipotesis


def test_f036_r109_la_forma_del_codigo_enmascara_letras_y_cifras():
    """Los ejemplos de `cod` salen como forma: cada letra `A`, cada cifra `9`, separadores tal cual."""
    funcion = _funcion(_texto(), "ConvertTo-FormaCodigo")

    assert '-replace "\\p{L}", "A"' in funcion
    assert '-replace "\\p{N}", "9"' in funcion


def test_f036_r109_las_actividades_solo_con_mostrarnombres():
    """Codigo y nombre de actividad, literales solo con `-MostrarNombres`; si no, la forma."""
    funcion = _sin_comentarios(_funcion(_texto(), "Format-Actividad"))

    assert "if ($MostrarNombres)" in funcion
    assert "ConvertTo-FormaCodigo" in funcion
    for nombre in ("Write-ArbolActividades", "Write-Actividades"):
        cuerpo = _sin_comentarios(_funcion(_texto(), nombre))
        for linea in cuerpo.splitlines():
            if "Write-Host" in linea:
                assert not PATRON_NOMBRE_IMPRESO.search(linea), linea


#: Ni una variable `$nombre...` ni una propiedad `.nombre` / `.res` en lo que se imprime.
PATRON_NOMBRE_IMPRESO = re.compile(r"(?i)\$nombre|\.(?:nombre|res)\b")


def test_f036_r109_el_barrido_de_nombres_caza_uno_impreso():
    """Control negativo: imprimir el nombre de una actividad salta; un recuento, no."""
    assert PATRON_NOMBRE_IMPRESO.search('Write-Host ("{0}" -f $fila.nombre)')
    assert PATRON_NOMBRE_IMPRESO.search('Write-Host ("{0}" -f $porCodigo[$raiz].res)')
    assert PATRON_NOMBRE_IMPRESO.search('Write-Host ("{0}" -f $nombreRaiz)')
    assert not PATRON_NOMBRE_IMPRESO.search('Write-Host ("{0}" -f $textoSeparadores)')


def test_f036_r109_actividades_por_rama_de_primer_nivel():
    """R109 (4) · las actividades de los proveedores de la obra, contadas por su raiz."""
    funcion = _funcion(_texto(), "Write-ArbolActividades")

    assert ".Raiz[" in funcion
    assert "por rama de primer nivel" in funcion


def test_f036_r109_cruce_de_actividades_y_oficios():
    """R109 (5) · `auxpronat` frente a `auxofc` por codigo y por nombre sin mayusculas ni tildes."""
    sql = _plano(_sqls()["sqlCruceActividadesOficios"])

    assert "n.cod = a.cod" in sql
    assert (
        "LTRIM(RTRIM(n.res)) COLLATE Latin1_General_CI_AI = LTRIM(RTRIM(a.res)) COLLATE Latin1_General_CI_AI"
        in sql
    )
    for columna in (
        "codigos_en_los_dos",
        "codigos_solo_actividades",
        "codigos_solo_oficios",
        "actividades_mismo_nombre",
        "oficios_mismo_nombre",
    ):
        assert f"AS {columna}" in sql, columna


def test_f036_r107_las_actividades_de_los_proveedores_de_la_obra():
    """R107 · del proveedor, solo su codigo; de la actividad, su codigo y `homolo`. Paginado."""
    sql = _plano(_sqls()["sqlActividadesProveedor"])

    assert sql.startswith(
        "SELECT p.cod AS proveedor_codigo, n.cod AS actividad_codigo, ca.homolo AS homolo FROM dbo.conact ca"
    )
    assert "WHERE ca.conide IN (SELECT f.prvide FROM dbo.obrofc f WHERE f.obride = ?)" in sql
    assert "ORDER BY ca.ide" in sql
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql
    assert not re.search(r"\bp\.res\b", sql)


def test_f036_t1_las_lecturas_paginadas_anaden_desde_y_tamano():
    """Una sola forma de paginar: `Read-Paginas` anade `desde` y `tamano` a los parametros dados."""
    funcion = _sin_comentarios(_funcion(_texto(), "Read-Paginas"))

    assert "($Parametros + @($desde, $TamanoPagina))" in funcion
    assert "if ($pagina.row_count -lt $TamanoPagina) { break }" in funcion
    assert "return ,$paginas" in funcion


def test_f036_t1_se_mantiene_lo_de_confam():
    """Lo de `confam` se queda: que este vacio es un dato de T2 (`progress/explore_F-036.md`)."""
    ejecutable = _sin_comentarios(_texto())

    assert 'Write-Familias -Ambito "obra"' in ejecutable
    assert 'Write-Familias -Ambito "obrofc"' in ejecutable
    assert "familias_proveedor = $familias" in _funcion(_texto(), "New-CatalogoJson")
