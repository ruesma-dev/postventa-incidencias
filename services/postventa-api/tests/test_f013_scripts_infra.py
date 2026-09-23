# services/postventa-api/tests/test_f013_scripts_infra.py
"""Los dos scripts de medicion de F-013 cumplen su contrato (T1; R27, R28, R30, R32).

Mismo planteamiento que `test_f006_scripts_infra.py` y `test_f012_scripts_infra.py`:
son PowerShell, no entran en la cobertura ni en la campana de mutacion
—`harness/alcance.py` solo mide `.py`— y una revision a ojo no sobrevive a la
siguiente edicion. Lo que sobrevive es esto.

Los dos los lanza **una persona** contra sistemas reales —la biblioteca de
Posventa, sincronizada por OneDrive en sus equipos, y el ERP de produccion—, asi
que lo que se fija aqui es, sobre todo, lo que **no** pueden hacer:

- **`23_destino_posventa.ps1` no escribe en SharePoint. Nunca.** Solo `GET` en
  Graph, mas el `POST` del token, que es el que Entra exige. Ni crear la carpeta
  «ya que estamos» ni subir nada «para probar»: la regla dura de `CLAUDE.md`.
- **`24_ubicacion_sigrid.ps1` no escribe en Sigrid.** Su unica ruta es
  `POST /api/sql/read`, a traves de `08_lectura_sigrid_comun.ps1`.
- **Ningun identificador ni nombre de cliente en la salida por defecto.** Los
  ID del sitio y de la biblioteca, solo con `-MostrarIdentificadores`; los
  ficheros se **cuentan**, nunca se nombran (sus nombres pueden llevar el de un
  cliente); y los nombres de carpeta de unidad y el `con.res` de las unidades
  salen enmascarados salvo con `-MostrarNombres` (`VILLA 05 - GARCIA` es el
  ejemplo del propio `design.md` §4.3).
- **Ningun valor dentro**: ni un GUID, ni el host del inquilino, ni una
  credencial, ni un codigo de reclamacion real. Estos ficheros **si** se
  versionan y el historial de git no suelta lo que entra (R30).
- **CRLF y ASCII puro, sin BOM**, como los otros 25 scripts de `infra/`.
  `docs/CONVENTIONS.md` pide UTF-8 con BOM «salvo excepciones documentadas», y
  `infra/` es una: `test_f010_prompt_keys_infra.py` lee **todos** los `.ps1`
  como `ascii`, y un BOM lo tumba (medido el 2026-09-24 al escribir T1, que
  pedia BOM). Un fichero ASCII ya es UTF-8 valido, y PowerShell 5.1 lo lee
  igual con o sin BOM; el BOM solo haria falta con un acento, y un acento en
  una consola con la pagina de codigos por defecto sale como dos caracteres
  raros. Desviacion anotada en `progress/impl_F-013.md`.

Este fichero no contiene ningun identificador ni ningun host: los controles
negativos se componen en memoria a partir de trozos.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Raiz del repositorio, tres niveles por encima de este fichero.
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

#: El directorio de los scripts re-ejecutables.
INFRA = RAIZ / "infra"

#: R27, R28 · URL -> sitio y biblioteca, permisos del token y, con
#: `-CodigoObra`, el arbol de carpetas de una obra. Solo lectura.
SCRIPT_DESTINO = INFRA / "23_destino_posventa.ps1"

#: R32 · las unidades de posventa de una obra en Sigrid. Solo lectura.
SCRIPT_UBICACION = INFRA / "24_ubicacion_sigrid.ps1"

LOS_DOS = (SCRIPT_DESTINO, SCRIPT_UBICACION)

#: La marca de orden de bytes de UTF-8.
BOM = b"\xef\xbb\xbf"

#: La forma de un GUID: inquilino, sitio, biblioteca y aplicacion.
PATRON_GUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

#: El host del inquilino de SharePoint (R30). Solo casa un nombre de host de
#: verdad: `<inquilino>.sharepoint.com`, con el marcador entre angulos, no.
#: El patron se compone troceado para que este fichero no se contenga a si mismo.
PATRON_HOST_SHAREPOINT = re.compile(
    r"[a-z0-9][a-z0-9-]*" + r"\." + "share" + r"point\.com", re.IGNORECASE
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

#: Un codigo de reclamacion real, con la forma que usa Sigrid.
PATRON_INCIDENCIA_REAL = re.compile(r"\bRS\d{2}\.\d{2}/\d{4}\b")

#: Los verbos HTTP que escriben.
PATRON_VERBOS_QUE_ESCRIBEN = re.compile(r"-Method\s+(Put|Patch|Delete|Merge)\b", re.IGNORECASE)

#: Cualquier `-Method Post`.
PATRON_POST = re.compile(r"-Method\s+Post\b", re.IGNORECASE)

#: Sentencias que escribirian en el ERP.
PATRON_SQL_QUE_ESCRIBE = re.compile(
    r"\b(?:INSERT\s+INTO|UPDATE\s+\w|DELETE\s+FROM|MERGE\s+|EXEC(?:UTE)?\s|TRUNCATE\s|DROP\s|ALTER\s)",
    re.IGNORECASE,
)


def _bytes(script: Path) -> bytes:
    return script.read_bytes()


def _texto(script: Path) -> str:
    """El script como texto (`utf-8-sig`: si alguien le pone un BOM, el test
    que lo prohibe lo dice por su nombre en vez de reventar aqui)."""
    return script.read_text(encoding="utf-8-sig")


def _sin_ayuda(texto: str) -> str:
    """El script sin su bloque de ayuda `<# ... #>`.

    La ayuda explica **por que** no se escribe, y buscar en el texto crudo daria
    por rotas las reglas que el propio comentario esta defendiendo.
    """
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
        rf"^function {re.escape(nombre)} \{{\r?\n.*?^\}}", texto, re.DOTALL | re.MULTILINE
    )
    assert encontrado, f"no encuentro la funcion {nombre}"
    return encontrado.group(0)


# --------------------------------------------------------------------------
# Los dos: existen, y son como el resto de `infra/`
# --------------------------------------------------------------------------


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f013_t1_los_dos_scripts_existen(script):
    """Sin ellos, T2 y T3 se harian a mano contra la biblioteca real y el ERP.

    Y la regla de casado de §4 se escribiria sin haberla contrastado con una
    sola carpeta de verdad, que es exactamente lo que el bloque 0 existe para
    evitar.
    """
    assert script.is_file()


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f013_t1_sin_bom_como_el_resto_de_infra(script):
    """Sin BOM: la excepcion de `infra/` a `docs/CONVENTIONS.md`.

    `test_f010_prompt_keys_infra.py` barre **todos** los `.ps1` leyendolos como
    `ascii`; con un BOM, la suite entera no llega ni a recolectar. Este test lo
    dice aqui, con nombre, en vez de dejar que lo descubra el siguiente.
    """
    assert not _bytes(script).startswith(BOM)


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f013_t1_crlf_en_todas_las_lineas(script):
    """`docs/CONVENTIONS.md`: PowerShell con **CRLF**, sin un solo LF suelto.

    Un fichero mezclado es el peor caso: PowerShell 5.1 lo lee, pero el diff
    de la siguiente edicion sale entero cambiado y esconde lo que de verdad
    cambio.
    """
    crudo = _bytes(script)

    assert b"\r\n" in crudo
    assert crudo.count(b"\n") == crudo.count(b"\r\n")


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f013_t1_contenido_ascii_puro(script):
    """Como el resto de `infra/`: un acento en una consola de PowerShell 5.1
    con la pagina de codigos por defecto sale como dos caracteres raros, y un
    mensaje ilegible en mitad de una medicion es lo ultimo que hace falta."""
    assert all(byte < 128 for byte in _bytes(script))


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f013_t1_cada_script_empieza_por_su_ruta_relativa(script):
    """`docs/CONVENTIONS.md`: primera linea, la ruta del fichero."""
    assert _texto(script).splitlines()[0] == f"# infra/{script.name}"


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f013_t1_se_lanzan_desde_cualquier_sitio(script):
    """Rutas desde `$PSScriptRoot` y `Set-Location` a la raiz del repo.

    Asi se lanzan con una linea corta desde cualquier carpeta, que es como los
    ejecuta el humano (memoria del proyecto: nada de comandos largos).
    """
    ejecutable = _sin_comentarios(_texto(script))

    assert "$PSScriptRoot" in ejecutable
    assert "Set-Location" in ejecutable
    assert '$ErrorActionPreference = "Stop"' in ejecutable


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f013_t1_cargan_el_comun_de_lectura(script):
    """Veredicto, codigos de salida y TLS 1.2 salen de `08_lectura_sigrid_comun.ps1`.

    El TLS no es un detalle: sin el, PowerShell 5.1 muere contra Graph y contra
    la pasarela con un error que no dice nada de TLS.
    """
    ejecutable = _sin_comentarios(_texto(script))

    assert '. "$PSScriptRoot\\08_lectura_sigrid_comun.ps1"' in ejecutable
    assert "Escribir-Veredicto" in ejecutable


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f013_t1_los_dos_admiten_whatif_y_no_llaman_a_nada(script):
    """`-WhatIf` imprime lo que haria y **sale antes de la primera llamada**.

    Es como se comprueban los dos sin tocar ningun sistema.
    """
    ejecutable = _sin_comentarios(_texto(script))

    assert "[switch]$WhatIf" in ejecutable
    assert "no se ha llamado a nada" in ejecutable
    salida_whatif = ejecutable.index("if ($WhatIf)")
    primera_llamada = min(
        ejecutable.index(marca)
        for marca in ("Get-TokenAppOnly -", "Invoke-SigridLectura -")
        if marca in ejecutable
    )

    assert salida_whatif < primera_llamada


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f013_r30_ningun_script_lleva_un_guid(script):
    """R30 · ni de inquilino, ni de sitio, ni de biblioteca, ni de aplicacion."""
    assert PATRON_GUID.findall(_texto(script)) == []


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f013_r30_ningun_script_lleva_el_host_del_inquilino(script):
    """R30 · la URL del sitio entra **por parametro**, nunca escrita aqui."""
    assert PATRON_HOST_SHAREPOINT.findall(_texto(script)) == []
    assert PATRON_HOST_AZURE.findall(_texto(script)) == []


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f013_r30_ningun_script_lleva_una_credencial_ni_un_codigo_real(script):
    """Ni una credencial escrita a mano, ni un codigo de reclamacion de verdad."""
    texto = _texto(script)

    assert PATRON_CREDENCIAL.findall(texto) == []
    assert PATRON_INCIDENCIA_REAL.findall(texto) == []


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f013_t1_ninguno_imprime_un_secreto(script):
    """La salida de estos scripts se pega en un chat o en `progress/`.

    Se revisa **linea a linea**: ninguna que imprima puede nombrar la variable
    del token, del secreto ni de la clave de la pasarela.
    """
    culpables = [
        linea.strip()
        for linea in _texto(script).splitlines()
        if "Write-Host" in linea
        and re.search(r"\$(token|secreto|clientSecret|clave)\b", linea, re.IGNORECASE)
    ]

    assert culpables == []


@pytest.mark.parametrize("script", LOS_DOS, ids=lambda ruta: ruta.name)
def test_f013_t1_los_nombres_salen_enmascarados_salvo_que_se_pidan(script):
    """Los nombres de carpeta y el `con.res` pueden llevar el de un cliente.

    Por defecto pasan por `ConvertTo-FormaSinNombres`; el literal, solo con
    `-MostrarNombres`.
    """
    ejecutable = _sin_comentarios(_texto(script))

    assert "[switch]$MostrarNombres" in ejecutable
    assert "function ConvertTo-FormaSinNombres" in ejecutable
    assert "function Format-Nombre" in ejecutable


def test_f013_t1_la_mascara_es_la_misma_en_los_dos():
    """Dos copias de la mascara que divergen son dos criterios de «nombre».

    Vive en los dos scripts porque `08_lectura_sigrid_comun.ps1` es de F-009 y
    no se toca por esto; a cambio, este test exige que sean identicas.
    """
    assert _funcion(_texto(SCRIPT_DESTINO), "ConvertTo-FormaSinNombres") == _funcion(
        _texto(SCRIPT_UBICACION), "ConvertTo-FormaSinNombres"
    )
    assert _funcion(_texto(SCRIPT_DESTINO), "Format-Nombre") == _funcion(
        _texto(SCRIPT_UBICACION), "Format-Nombre"
    )


# --------------------------------------------------------------------------
# `23_destino_posventa.ps1` · Graph, solo lectura
# --------------------------------------------------------------------------


def test_f013_r27_el_de_graph_solo_hace_get_mas_el_token():
    """R27 · **la regla dura escrita como test.**

    Una sola llamada que no es `GET`, la del token, porque Entra no da un token
    con un `GET`. Cualquier otra seria escribir en la biblioteca de Posventa
    desde un puesto de trabajo, y aparece en sus OneDrive al momento.
    """
    ejecutable = _sin_comentarios(_texto(SCRIPT_DESTINO))

    assert PATRON_VERBOS_QUE_ESCRIBEN.findall(ejecutable) == []
    assert len(PATRON_POST.findall(ejecutable)) == 1
    assert "oauth2/v2.0/token" in ejecutable
    assert "Invoke-WebRequest" not in ejecutable
    # Dos llamadas HTTP en todo el script: la lectura de Graph y el token.
    assert ejecutable.count("Invoke-RestMethod") == 2
    assert "-Method Get" in _funcion(_texto(SCRIPT_DESTINO), "Invoke-GraphLectura")
    assert "-Method Post" in _funcion(_texto(SCRIPT_DESTINO), "Get-TokenAppOnly")


def test_f013_r27_el_de_graph_no_nombra_nada_que_suba_o_cree():
    """R27, R28 · ni subida, ni sesion de subida, ni `conflictBehavior`.

    `conflictBehavior` es la marca de un `POST .../children` que crea una
    carpeta; `:/content` y `createUploadSession`, la de una subida.
    """
    ejecutable = _sin_comentarios(_texto(SCRIPT_DESTINO))

    for prohibido in ("conflictBehavior", "createUploadSession", ":/content", "/content"):
        assert prohibido not in ejecutable


def test_f013_r27_az_solo_para_leer_del_key_vault():
    """`-DesdeKeyVault` lee los `GRAPH_*` del vault del proyecto. Nada mas.

    Ni un `set`, ni un `delete`: el unico `az` es `keyvault secret show`. Y el
    nombre del vault y de los secretos salen de `00_vars_postventa.ps1`, no se
    escriben aqui.
    """
    ejecutable = _sin_comentarios(_texto(SCRIPT_DESTINO))
    usos = re.findall(r"\baz\s+(\w+(?:\s+\w+)?\s+\w+)", ejecutable)

    assert usos == ["keyvault secret show"]
    assert '. "$PSScriptRoot\\00_vars_postventa.ps1"' in ejecutable
    assert "$PostventaKeyVault" in ejecutable
    assert "$PostventaAppSettingsSecretas" in ejecutable
    assert "kv-postventa" not in ejecutable
    assert "graph-client-secret" not in ejecutable


def test_f013_r27_resuelve_sitio_y_biblioteca_desde_la_url():
    """R27 · la URL entra por parametro y el sitio se pide por ruta.

    La biblioteca se casa por su URL (`webUrl`), no por el nombre visible, que
    puede ser «Documentos» o «Documentos compartidos» segun el idioma.
    """
    ejecutable = _sin_comentarios(_texto(SCRIPT_DESTINO))

    assert "[string]$UrlSitio" in ejecutable
    assert '[string]$NombreBiblioteca = "Documentos compartidos"' in ejecutable
    assert "/drives" in ejecutable
    assert "webUrl" in ejecutable


def test_f013_r27_los_identificadores_solo_con_su_interruptor():
    """R27 · los ID del sitio y de la biblioteca, **solo** con `-MostrarIdentificadores`.

    Se imprimen en una unica funcion, y esa funcion se llama una vez, dentro
    del `if` del interruptor.
    """
    texto = _texto(SCRIPT_DESTINO)
    ejecutable = _sin_comentarios(texto)
    funcion = _funcion(texto, "Write-Identificadores")

    assert "[switch]$MostrarIdentificadores" in ejecutable
    assert "Key Vault" in funcion
    assert ejecutable.count("Write-Identificadores") == 2  # definicion y llamada
    llamada = ejecutable.index("Write-Identificadores", ejecutable.index("function Write-Identificadores") + 10)
    anterior = ejecutable.rfind("if (", 0, llamada)
    assert ejecutable[anterior:llamada].startswith("if ($MostrarIdentificadores)")

    fuera = ejecutable.replace(_sin_comentarios(funcion), "")
    assert [linea for linea in fuera.splitlines() if "Write-Host" in linea and ".id" in linea] == []


def test_f013_r28_los_ficheros_se_cuentan_sin_nombrarlos():
    """R28 · de un fichero solo se suma uno al contador.

    Su nombre puede llevar el de un cliente; el de una carpeta, ademas, pasa por
    la mascara al imprimirse. El listado pide solo `name`, `folder` y `file`.
    """
    funcion = _funcion(_texto(SCRIPT_DESTINO), "Get-Hijos")

    assert "$select=name,folder,file" in funcion
    lineas_con_nombre = [linea for linea in funcion.splitlines() if "$elemento.name" in linea]
    assert len(lineas_con_nombre) == 1
    assert "$elemento.folder" in lineas_con_nombre[0]
    assert "$ficheros = $ficheros + 1" in funcion


def test_f013_r28_sigue_la_paginacion_sin_imprimirla():
    """R12, R28 · `@odata.nextLink` hasta el final, y nunca a la consola.

    El `nextLink` lleva dentro el identificador de la biblioteca.
    """
    texto = _texto(SCRIPT_DESTINO)

    assert "@odata.nextLink" in _funcion(texto, "Get-Hijos")
    assert [linea for linea in texto.splitlines() if "Write-Host" in linea and "nextLink" in linea] == []


def test_f013_r28_recorre_la_estructura_de_posventa():
    """R28 · obra -> `PARTES INCIDENCIAS` -> unidades -> `PARTES FIRMADOS`.

    Los dos tramos fijos son parametros con el valor por omision de la spec
    (R1), y la base vacia es la raiz (D-1).
    """
    ejecutable = _sin_comentarios(_texto(SCRIPT_DESTINO))

    assert "[string]$CodigoObra" in ejecutable
    assert '[string]$CarpetaBase = ""' in ejecutable
    assert '[string]$CarpetaIncidencias = "PARTES INCIDENCIAS"' in ejecutable
    assert '[string]$CarpetaFirmados = "PARTES FIRMADOS"' in ejecutable


def test_f013_r27_la_cabecera_dice_que_no_crea_ni_sube_nada():
    """Quien lo abra tiene que saber en la primera pantalla que no escribe."""
    cabecera = _texto(SCRIPT_DESTINO)[:2500]

    assert "NO CREA NADA" in cabecera
    assert "NO SUBE NADA" in cabecera


# --------------------------------------------------------------------------
# `24_ubicacion_sigrid.ps1` · Sigrid, solo lectura
# --------------------------------------------------------------------------


def test_f013_r32_el_de_sigrid_solo_lee_por_sql_read():
    """R32 · la regla dura: en Sigrid, desde un puesto, solo lecturas.

    La unica llamada es `Invoke-SigridLectura` del comun, que solo conoce
    `POST /api/sql/read`. Ni HTTP propio, ni `sql/write`, ni una sentencia que
    escriba.
    """
    ejecutable = _sin_comentarios(_texto(SCRIPT_UBICACION))

    assert "Invoke-SigridLectura" in ejecutable
    assert "Invoke-RestMethod" not in ejecutable
    assert "Invoke-WebRequest" not in ejecutable
    assert "sql/write" not in ejecutable
    assert "concepto-grafico" not in ejecutable
    assert PATRON_SQL_QUE_ESCRIBE.findall(ejecutable) == []


def test_f013_r32_la_consulta_va_parametrizada():
    """Parametros con `?` y nunca interpolados (`azure-apps/sigrid_api.md` §5.2)."""
    ejecutable = _sin_comentarios(_texto(SCRIPT_UBICACION))

    assert "-Parametros" in ejecutable
    assert "o.cod IN (?, ?)" in ejecutable
    assert "c.tip = ?" in ejecutable


def test_f013_r32_la_consulta_recorre_upv_hasta_la_obra():
    """R32 · unidad de posventa (`upv`) -> obra (`upv.obride`), con `con.cod` y `con.res`.

    El mismo camino que usara el adaptador (`design.md` §6.2), para que lo que
    se mida aqui sea lo que el sistema vera.
    """
    ejecutable = _sin_comentarios(_texto(SCRIPT_UBICACION))

    assert "FROM dbo.upv v" in ejecutable
    assert "JOIN dbo.con u ON u.ide = v.ide" in ejecutable
    assert "JOIN dbo.con o ON o.ide = v.obride" in ejecutable
    assert "u.cod" in ejecutable and "u.res" in ejecutable
    assert "COUNT(*)" in ejecutable


def test_f013_r32_la_cabecera_avisa_del_texto_libre():
    """`u.res` puede traer texto libre, y eso se dice antes de ejecutar."""
    cabecera = _texto(SCRIPT_UBICACION)[:3000]

    assert "texto libre" in cabecera
    assert "SOLO LECTURA" in cabecera


# --------------------------------------------------------------------------
# Controles negativos: un patron que nunca se ha visto saltar no protege nada
# --------------------------------------------------------------------------


def test_f013_r30_el_barrido_de_host_caza_uno_inyectado():
    """Control negativo: el host se compone en memoria, a trozos."""
    inventado = "contoso-inventado" + "." + "share" + "point" + "." + "com"

    assert PATRON_HOST_SHAREPOINT.findall(f"https://{inventado}/sites/X") == [inventado]


def test_f013_r30_el_barrido_de_host_no_salta_con_el_marcador():
    """Lo que la ayuda si tiene que poder escribir: el marcador entre angulos."""
    marcador = "https://<inquilino>." + "share" + "point" + ".com/sites/<sitio>"

    assert PATRON_HOST_SHAREPOINT.findall(marcador) == []


def test_f013_r27_el_barrido_de_verbos_caza_uno_inyectado():
    """Control negativo del barrido de verbos que escriben."""
    assert PATRON_VERBOS_QUE_ESCRIBEN.findall("Invoke-RestMethod -Method Put -Uri $u")
    assert PATRON_VERBOS_QUE_ESCRIBEN.findall("Invoke-RestMethod -Method Delete -Uri $u")


def test_f013_r32_el_barrido_de_sql_caza_una_escritura_inyectada():
    """Control negativo del barrido de sentencias que escriben."""
    assert PATRON_SQL_QUE_ESCRIBE.findall("UPDATE dbo.con SET est = 1")
    assert PATRON_SQL_QUE_ESCRIBE.findall("EXEC dbo.algo")
    assert PATRON_SQL_QUE_ESCRIBE.findall("SELECT u.cod FROM dbo.upv v") == []
