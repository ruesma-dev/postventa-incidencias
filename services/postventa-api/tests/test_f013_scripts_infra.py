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

**T14 (2026-09-24).** El 23 deja de llevar las reglas de casado en PowerShell
y aplica **la del dominio**, con el interprete del servicio y por fichero: el
Python que lleva dentro se extrae aqui y **se ejecuta** contra el arbol medido
de la 0677 (T2) y sus 15 unidades (T3), y tiene que dar exactamente lo de R31.
El 24 escribe esas unidades en un CSV (`-SalidaCsv`) sin `obride`, y el 23 las
lee (`-UnidadesCsv`).
"""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.utiles_destino import (
    ALTERNATIVA,
    CARPETA_OBRA_0677,
    FIRMADOS,
    INCIDENCIAS,
    RES_OBRA_0677,
    UNIDADES_0677,
    arbol_0677,
)

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


# --------------------------------------------------------------------------
# T14 · la regla del dominio en el 23, y el CSV del 24 (R28, R31)
# --------------------------------------------------------------------------

#: Las cuatro copias provisionales de T1 y la clave de §4.3 copiada en
#: PowerShell. T14 las retira: la regla es la del dominio.
REGLAS_PROVISIONALES = (
    "Test-ObraCasa",
    "Test-ObraParecida",
    "Test-TramoCasa",
    "Test-TramoParecido",
    "Get-Tokens",
)

#: El directorio del servicio, que es el que la regla mete en `sys.path`.
SERVICIO = RAIZ / "services" / "postventa-api"

OBRA = CARPETA_OBRA_0677
INC = f"{OBRA}/{INCIDENCIAS}"


def _regla_embebida() -> str:
    """El Python que el 23 ejecuta con `Invoke-PythonDelServicio`."""
    encontrado = re.search(
        r"^\$reglaDelDominio = @'\r?\n(.*?)\r?\n'@",
        _texto(SCRIPT_DESTINO),
        re.DOTALL | re.MULTILINE,
    )
    assert encontrado, "el 23 no lleva la regla del dominio en $reglaDelDominio"
    return encontrado.group(1)


def _columnas_del_24() -> tuple[str, ...]:
    encontrado = re.search(r"^\$ColumnasCsv = @\(([^)]*)\)", _texto(SCRIPT_UBICACION), re.MULTILINE)
    assert encontrado, "el 24 no declara $ColumnasCsv"
    return tuple(re.findall(r'"([^"]+)"', encontrado.group(1)))


def _columnas_de_la_regla() -> tuple[str, ...]:
    encontrado = re.search(r"^COLUMNAS_CSV = \(([^)]*)\)", _regla_embebida(), re.MULTILINE)
    assert encontrado, "la regla no declara COLUMNAS_CSV"
    return tuple(re.findall(r'"([^"]+)"', encontrado.group(1)))


def _csv_del_24(ruta: Path, filas: list[dict[str, str]]) -> Path:
    """El CSV como lo escribe `Export-Csv -NoTypeInformation -Encoding UTF8`
    en PowerShell 5.1: con BOM, todo entrecomillado y CRLF."""
    with ruta.open("w", encoding="utf-8-sig", newline="") as fichero:
        escritor = csv.writer(fichero, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
        escritor.writerow(_columnas_del_24())
        for fila in filas:
            escritor.writerow([fila.get(columna, "") for columna in _columnas_del_24()])
    return ruta


def _unidades_0677(obra: str = "1") -> list[dict[str, str]]:
    """Las 15 unidades de T3, como filas del CSV del 24."""
    return [
        {
            "obra": obra,
            "obra_cod": unidad.obra_codigo,
            "obra_res": RES_OBRA_0677,
            "unidad_cod": unidad.unidad_codigo,
            "unidad_res": unidad.unidad_nombre,
            "reclamaciones": "0",
        }
        for unidad in UNIDADES_0677
    ]


def _listados(arbol: dict[str, tuple[str, ...]]) -> list[dict]:
    """Lo que el 23 anota de cada listado: la ruta y sus carpetas."""
    return [{"ruta": ruta, "carpetas": list(hijas)} for ruta, hijas in arbol.items()]


def _ejecutar_regla(tmp_path: Path, entrada: dict) -> dict:
    """Ejecuta la regla del 23 como la ejecuta el 23: por fichero, con la
    entrada en un JSON temporal cuya ruta va en `F013_ENTRADA_TEMP`.

    Un proceso aparte, sin red (la regla no llama a nadie: lo fija otro test).
    """
    codigo = tmp_path / "regla.py"
    codigo.write_text(_regla_embebida(), encoding="utf-8")
    fichero = tmp_path / "entrada.json"
    fichero.write_text(json.dumps({"servicio": str(SERVICIO), **entrada}), encoding="utf-8-sig")
    resultado = subprocess.run(
        [sys.executable, str(codigo)],
        env={**os.environ, "F013_ENTRADA_TEMP": str(fichero)},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.isascii(), "la salida de la regla tiene que ser ASCII"
    return json.loads(resultado.stdout)


def _veredicto(tmp_path: Path, arbol: dict, filas: list[dict] | None) -> dict:
    entrada = {
        "modo": "veredicto",
        "codigo": "0677",
        "base": "",
        "incidencias": INCIDENCIAS,
        "firmados": FIRMADOS,
        "alternativa": ALTERNATIVA,
        "arbol": _listados(arbol),
        "csv": None,
    }
    if filas is not None:
        entrada["csv"] = str(_csv_del_24(tmp_path / "unidades.csv", filas))
    return _ejecutar_regla(tmp_path, entrada)


def _resumen(unidades: list[dict]) -> list[tuple]:
    return [
        (
            unidad["unidad_cod"],
            unidad["veredicto"],
            tuple(unidad.get("crear") or ()),
            unidad.get("motivo"),
        )
        for unidad in unidades
    ]


#: R31 · lo que el 23 tiene que decir de la 0677 con T2 y T3, fila a fila.
R31_0677 = [
    *(
        (f"0677.03VILLA {n}.", "resolveria", (), None)
        for n in (1, 2, 3)
    ),
    ("0677.03VILLA 4.", "crearia", (FIRMADOS,), None),
    *(
        (f"0677.03VILLA {n}.", "resolveria", (), None)
        for n in (5, 6, 7)
    ),
    *(
        (f"0677.03VILLA {n}.", "crearia", (f"VILLA {n:02d}", FIRMADOS), None)
        for n in range(8, 16)
    ),
]


def test_f013_t14_el_23_ya_no_lleva_las_reglas_provisionales():
    """T14 · ni `Test-ObraCasa` ni las otras tres copias, ni la clave copiada.

    Mientras existieran, lo que dijera el 23 podia no ser lo que hace el
    sistema: la medicion de T2 lo demostro (la 0677 salio «parecida»).
    """
    ejecutable = _sin_comentarios(_texto(SCRIPT_DESTINO))

    for provisional in REGLAS_PROVISIONALES:
        assert provisional not in ejecutable, provisional


def test_f013_t14_el_23_ejecuta_la_regla_del_dominio_por_fichero():
    """T14, `design.md` §7.1 · con el interprete del servicio y **por fichero**.

    `Invoke-PythonDelServicio` del 08: `python -c` no funciona en PowerShell
    5.1 (se come las comillas). La regla importa el dominio y el resolutor de
    verdad, no una copia.
    """
    ejecutable = _sin_comentarios(_texto(SCRIPT_DESTINO))
    regla = _regla_embebida()

    assert "Invoke-PythonDelServicio -Python $python -Codigo $reglaDelDominio" in ejecutable
    assert '".venv\\Scripts\\python.exe"' in ejecutable
    assert not re.search(r"\$python\s+-c\b", ejecutable)
    assert "from domain.models.destino_posventa import" in regla
    assert "from application.pipelines.destino_archivo import resolver_destino_posventa" in regla


def test_f013_t14_la_regla_embebida_no_escribe_ni_llama_a_nadie():
    """R27, R28 · la regla solo lee: el JSON de entrada y el CSV del 24.

    Ni crea carpetas (el explorador que le da al resolutor solo sabe listar lo
    ya listado), ni abre un fichero para escribir, ni habla con la red.
    """
    regla = _regla_embebida()

    assert "crear_subcarpeta" not in regla
    for prohibido in ("httpx", "requests", "urllib", "socket", "subprocess", "infrastructure"):
        assert prohibido not in regla, prohibido
    aperturas = re.findall(r"open\(([^)]*)\)", regla)
    assert aperturas, "la regla lee la entrada y el CSV con open()"
    for apertura in aperturas:
        assert not re.search(r"""["'][wax+]""", apertura), apertura


def test_f013_t14_la_regla_embebida_es_ascii():
    """Va dentro de un `.ps1`: ASCII puro, como el resto del script."""
    assert _regla_embebida().isascii()


def test_f013_t14_el_23_solo_escribe_el_temporal_de_la_regla():
    """El 23 no escribe en disco nada mas que la entrada de la regla, en `%TEMP%`,
    y la borra siempre (`finally`). Ni un CSV, ni un informe."""
    ejecutable = _sin_comentarios(_texto(SCRIPT_DESTINO))
    funcion = _funcion(_texto(SCRIPT_DESTINO), "Invoke-ReglaDelDominio")

    assert "Export-Csv" not in ejecutable
    assert "Out-File" not in ejecutable
    assert ejecutable.count("Set-Content") == 1
    assert "Set-Content" in funcion
    assert "GetTempPath()" in funcion
    assert "finally" in funcion
    assert "Remove-Item -LiteralPath $fichero" in funcion


def test_f013_t14_la_regla_da_lo_de_r31_para_la_0677(tmp_path):
    """R31 · **el caso que para el corte**: la 0677 medida, unidad a unidad.

    VILLA 01, 02, 03, 05, 06 y 07 «resolveria» (la 02, con su `PARTES
    FIRMADO`); VILLA 04 «crearia» `PARTES FIRMADOS`; VILLA 08 … 15 «crearia»
    `VILLA NN` y su hoja; ninguna «bloquearia». La obra y `PARTES INCIDENCIAS`,
    «resolveria».
    """
    resultado = _veredicto(tmp_path, arbol_0677(), _unidades_0677())

    assert resultado["obra"] == {"veredicto": "resolveria", "carpeta": OBRA}
    assert resultado["incidencias"] == {"veredicto": "resolveria", "carpeta": INCIDENCIAS}
    assert _resumen(resultado["unidades"]) == R31_0677
    villa_02 = resultado["unidades"][1]
    assert villa_02["carpeta"] == f"{INC}/VILLA 02/{ALTERNATIVA}"


def test_f013_t14_sin_csv_dice_la_obra_y_ninguna_unidad(tmp_path):
    """Sin `-UnidadesCsv`: la obra y el tramo, y ninguna unidad (no se inventan)."""
    resultado = _veredicto(tmp_path, arbol_0677(), None)

    assert resultado["obra"]["veredicto"] == "resolveria"
    assert resultado["unidades"] == []


def test_f013_t14_una_obra_solo_parecida_bloquearia_todas(tmp_path):
    """R35 · con `0677-MIRASIERRA` (parecida) y ninguna que case: bloquearia."""
    arbol = arbol_0677()
    arbol[""] = ("0677-MIRASIERRA", "0680 OTRA OBRA")

    resultado = _veredicto(tmp_path, arbol, _unidades_0677())

    assert resultado["obra"] == {
        "veredicto": "bloquearia",
        "motivo": "obra_parecida",
        "candidatas": ["0677-MIRASIERRA"],
    }
    assert {unidad["veredicto"] for unidad in resultado["unidades"]} == {"bloquearia"}
    assert {unidad["motivo"] for unidad in resultado["unidades"]} == {"obra_parecida"}


def test_f013_t14_sin_ninguna_obra_crearia_con_el_nombre_de_r36(tmp_path):
    """R36 · ni casa ni se parece ninguna: se crearia `<cod> <con.res>` y todo lo de debajo."""
    arbol = {"": ("0680 OTRA OBRA", "ADMINISTRACION")}

    resultado = _veredicto(tmp_path, arbol, _unidades_0677())

    assert resultado["obra"] == {"veredicto": "crearia", "crear": [f"0677 {RES_OBRA_0677}"]}
    assert resultado["incidencias"] == {"veredicto": "crearia", "crear": [INCIDENCIAS]}
    assert resultado["unidades"][4]["crear"] == [
        f"0677 {RES_OBRA_0677}",
        INCIDENCIAS,
        "VILLA 05",
        FIRMADOS,
    ]


def test_f013_t14_dos_obras_con_el_numero_bloquearian(tmp_path):
    """R44 · dos obras con el mismo número en el CSV (obra 1 y obra 2): bloquearia."""
    filas = [*_unidades_0677("1"), *_unidades_0677("2")]

    resultado = _veredicto(tmp_path, arbol_0677(), filas)

    assert {unidad["motivo"] for unidad in resultado["unidades"]} == {"obra_numero_no_unico"}


def test_f013_t14_lo_que_no_se_ha_listado_sale_sin_medir(tmp_path):
    """Si la regla baja por una carpeta que el 23 no listo, no se adivina."""
    arbol = arbol_0677()
    del arbol[f"{INC}/VILLA 05"]

    resultado = _veredicto(tmp_path, arbol, _unidades_0677())

    assert resultado["unidades"][4]["veredicto"] == "sin medir"
    assert resultado["unidades"][0]["veredicto"] == "resolveria"


def test_f013_t14_la_clasificacion_de_cada_nivel_es_la_del_dominio(tmp_path):
    """Los dos modos con los que el 23 recorre el arbol: obra y tramos."""
    obra = _ejecutar_regla(
        tmp_path,
        {"modo": "obra", "codigo": "0677", "carpetas": [*arbol_0677()[""], "0677-ANEXO"]},
    )
    hojas = _ejecutar_regla(
        tmp_path,
        {
            "modo": "tramos",
            "buscado": FIRMADOS,
            "alternativa": ALTERNATIVA,
            "grupos": [
                {"ruta": f"{INC}/VILLA 02", "nombre": "VILLA 02", "carpetas": [ALTERNATIVA]},
                {"ruta": f"{INC}/VILLA 04", "nombre": "VILLA 04", "carpetas": []},
                {"ruta": f"{INC}/VILLA X", "nombre": "VILLA CINCO", "carpetas": ["FIRMADOS"]},
            ],
        },
    )

    assert obra == {"casan": [OBRA], "parecidas": ["0677-ANEXO"]}
    assert hojas["grupos"] == [
        {"ruta": f"{INC}/VILLA 02", "casan": [ALTERNATIVA], "parecidas": [], "cifras": ["2"]},
        {"ruta": f"{INC}/VILLA 04", "casan": [], "parecidas": [], "cifras": ["4"]},
        {"ruta": f"{INC}/VILLA X", "casan": [], "parecidas": ["FIRMADOS"], "cifras": []},
    ]


def test_f013_t14_el_resumen_cuenta_lo_que_resuelve_la_regla():
    """El defecto del resumen (`progress/explore_F-013.md`), corregido.

    El resumen de T1 contaba solo bajo una obra que **casara** con la regla
    provisional (`Marca -ne "parecida"`) y salio con ceros. Ahora cuenta bajo
    la que resuelve la regla del dominio y, si no hay, lo dice en su linea;
    con `-CarpetaObra`, cuenta la forzada y lo rotula.
    """
    ejecutable = _sin_comentarios(_texto(SCRIPT_DESTINO))

    assert 'Marca -ne "parecida"' not in ejecutable
    assert "resumen sin obra resuelta: se muestran las parecidas" in ejecutable
    assert "resumen de la carpeta forzada con -CarpetaObra" in ejecutable


def test_f013_t14_los_parametros_del_csv():
    """`-SalidaCsv` en el 24 y `-UnidadesCsv` en el 23 (`design.md` §7.1)."""
    assert "[string]$SalidaCsv" in _sin_comentarios(_texto(SCRIPT_UBICACION))
    assert "[string]$UnidadesCsv" in _sin_comentarios(_texto(SCRIPT_DESTINO))


def test_f013_t14_el_csv_del_24_no_lleva_obride_y_es_el_que_lee_el_23():
    """Las columnas del CSV, escritas una vez en cada lado y **iguales**.

    Sin `obride` ni ningun `ide` del ERP: la obra va como el ordinal que el 24
    ya imprime («obra 1»). Y lo que se exporta pasa por `Select-Object` con esa
    lista: ninguna otra propiedad puede colarse en el fichero.
    """
    columnas = _columnas_del_24()
    ejecutable = _sin_comentarios(_texto(SCRIPT_UBICACION))

    assert columnas == _columnas_de_la_regla()
    assert columnas == ("obra", "obra_cod", "obra_res", "unidad_cod", "unidad_res", "reclamaciones")
    assert not [columna for columna in columnas if "ide" in columna]
    assert "Select-Object -Property $ColumnasCsv | Export-Csv" in ejecutable
    assert ejecutable.count("Export-Csv") == 1


def test_f013_t14_el_24_no_deja_el_csv_dentro_del_repositorio():
    """El CSV lleva los literales de `con.res`: fuera del repositorio o nada.

    La comprobacion va **antes** de la lectura de Sigrid: si la ruta no vale,
    no se ha preguntado nada.
    """
    ejecutable = _sin_comentarios(_texto(SCRIPT_UBICACION))

    assert "fuera del repositorio" in ejecutable
    assert ejecutable.index("fuera del repositorio") < ejecutable.index("Invoke-SigridLectura -")
