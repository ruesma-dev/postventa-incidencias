# tests/test_f035_publicar_maqueta.py
"""F-035 · T20 · `infra/publicar_maqueta.ps1`, leído como texto.

El script publica la maqueta del portal en el entorno de vista previa
`maqueta` de la Static Web App y, con `-Retirar`, lo deshace. Lo ejecuta el
humano contra Azure; aquí no se ejecuta nada. Lo que se fija, y por qué:

- **Nunca el entorno de producción.** `swa deploy` solo con `--env maqueta`;
  toda llamada de `az staticwebapp` que admite entorno lleva
  `--environment-name maqueta` (sin él, el valor por defecto es `default`,
  que ES producción: un `environment delete` sin él borraría la aplicación
  que usa Posventa). Ni `production` ni `backends link` en todo el texto.
- **Las comprobaciones en ejecución** que pidió el líder: el entorno sin
  backend (y antes de darle las App Settings), las App Settings comprobadas
  en el entorno después de fijarlas, y el host leído, no compuesto.
- **La lista de URL de retorno se reescribe entera**, leída antes y
  comprobada después, y nunca vacía (`az ad app update --web-redirect-uris`
  reemplaza: pasar solo una borró la del portal).
- **Las piezas duplicadas de `desplegar_front.ps1`** (enmienda de T20, opción
  B, patrón de F-013): cada función copiada y la lista de lo que no se publica
  son idénticas en los dos scripts. Si alguien cambia una, este test lo dice.
- Lo de todos los scripts de `infra/` (R1, R3–R8 de F-010): ruta en la línea
  1, ASCII con CRLF y sin BOM, `-WhatIf` y confirmación antes de escribir,
  un código por causa, la consola como estaba y ni un valor dentro.

Vive en la suite de la raíz porque `infra/` no es de ningún servicio y la
raíz se ejecuta siempre. Los valores de los controles negativos se componen
en memoria a partir de trozos.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
INFRA = RAIZ / "infra"
SCRIPT = INFRA / "publicar_maqueta.ps1"
FRONT = INFRA / "desplegar_front.ps1"

#: Las funciones copiadas de `desplegar_front.ps1`, idénticas en los dos.
FUNCIONES_DUPLICADAS = (
    "Salir-Con",
    "Existe-Herramienta",
    "Valor-De-Az",
    "Id-De-Aplicacion",
    "Existe-StaticWebApp",
)

#: Los diez nombres de recurso: solo los declara `00_vars_postventa.ps1` (R7).
NOMBRES_DE_RECURSO = (
    "rg-postventa-dev",
    "func-postventa-dev",
    "stpostventadev",
    "kv-postventa-dev",
    "id-postventa-dev",
    "log-postventa-dev",
    "appi-postventa-dev",
    "swa-postventa-ruesma",
    "Postventa Incidencias",
    "posventa-usuarios",
)

PATRON_GUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE)
PATRON_HOST = re.compile(
    r"\b[\w-]+\.(?:postgres\.database\.azure\.com|database\.windows\.net|vault\.azure\.net"
    r"|blob\.core\.windows\.net|azurestaticapps\.net|azurewebsites\.net)\b",
    re.IGNORECASE,
)
PATRON_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
PATRON_CREDENCIAL = re.compile(
    r"(?i)\b(?:password|pwd|passwd|secret|token|api[_-]?key|clave)\s*=\s*[\"'][^\"'$]"
)

#: Una escritura: `az ... create|set|update|delete|...` o la subida con `swa`.
PATRON_ESCRITURA = re.compile(
    r"^\s*(?:az (?:[\w-]+ )*?(?:create|set|update|delete|add|assign|deploy|publish|link)\b"
    r"|swa deploy\b)",
    re.MULTILINE,
)


def _crudo() -> bytes:
    return SCRIPT.read_bytes()


def _texto(script: Path | None = None) -> str:
    return (script or SCRIPT).read_text(encoding="ascii")


def sin_comentarios(texto: str) -> str:
    """El texto con la ayuda `<# #>` y las líneas de comentario en blanco, conservando posiciones."""
    fuera = re.sub(r"(?s)<#.*?#>", lambda h: re.sub(r"[^\n]", " ", h.group()), texto)
    return "\n".join(
        " " * len(linea) if linea.lstrip().startswith("#") else linea for linea in fuera.split("\n")
    )


def _funcion(texto: str, nombre: str) -> str:
    """El cuerpo de una función PowerShell, de `function X {` a la `}` de la columna 0."""
    encontrado = re.search(
        rf"^function {re.escape(nombre)} \{{\r?\n.*?^\}}", texto, re.DOTALL | re.MULTILINE
    )
    assert encontrado, f"no encuentro la función {nombre}"
    return encontrado.group(0)


def _exclusiones(texto: str) -> str:
    """La lista de lo que no se publica: el `@(...)` del `foreach ($sobra in ...)`."""
    encontradas = re.findall(r"foreach \(\$sobra in (@\([^)]*\))\)", texto)
    assert len(encontradas) == 1, f"tiene que haber una lista de exclusiones: {encontradas}"
    return encontradas[0]


def _lineas_de_codigo() -> list[str]:
    return sin_comentarios(_texto()).splitlines()


def _lineas_juntas(lineas: list[str]) -> list[str]:
    """Cada línea con sus continuaciones (el acento grave del final) pegadas."""
    juntas = []
    for i, linea in enumerate(lineas):
        completa = linea
        j = i
        while completa.rstrip().endswith("`") and j + 1 < len(lineas):
            j += 1
            completa = completa.rstrip()[:-1] + " " + lineas[j].strip()
        juntas.append(completa)
    return juntas


def _llamadas(*fragmentos: str) -> list[str]:
    """Las líneas de código (con su continuación) que contienen todos los fragmentos."""
    return [c for c in _lineas_juntas(_lineas_de_codigo()) if all(f in c for f in fragmentos)]


# --- Forma del fichero (R1 de F-010 y CONVENTIONS) ------------------------------


def test_f035_t20_el_script_existe():
    assert SCRIPT.is_file(), "falta infra/publicar_maqueta.ps1 (T20)"


def test_f035_t20_ascii_crlf_sin_bom_y_su_ruta_en_la_linea_1():
    crudo = _crudo()

    assert not crudo.startswith(b"\xef\xbb\xbf"), "sin BOM"
    crudo.decode("ascii")
    assert crudo.count(b"\n") == crudo.count(b"\r\n"), "finales de línea CRLF"
    assert crudo.startswith(b"# infra/publicar_maqueta.ps1\r\n")


def test_f035_t20_tiene_ayuda_con_los_dos_modos_y_carga_las_variables():
    texto = _texto()

    for marca in (".SYNOPSIS", ".DESCRIPTION", ".PARAMETER Retirar", ".PARAMETER WhatIf"):
        assert marca in texto, marca
    assert texto.count(".EXAMPLE") >= 3
    assert '. "$PSScriptRoot\\00_vars_postventa.ps1"' in texto
    assert "[switch]$Retirar" in texto
    assert "[switch]$WhatIf" in texto


# --- Nunca el entorno de producción ---------------------------------------------


def test_f035_t20_sube_solo_al_entorno_maqueta():
    subidas = _llamadas("swa deploy")

    assert subidas == ["    swa deploy $copiaDeTrabajo --env maqueta --no-use-keychain"]


def test_f035_t20_ni_production_ni_backends_link_en_todo_el_texto():
    texto = _texto().lower()

    assert "production" not in texto
    assert "backends link" not in texto
    assert '"backends", "link"' not in texto


def test_f035_t20_toda_llamada_con_entorno_nombra_maqueta():
    """Sin `--environment-name`, `az staticwebapp` usa `default`: producción."""
    codigo = sin_comentarios(_texto())
    llamadas = re.findall(
        r'staticwebapp"?,? "?(?:environment|appsettings|backends)\b[^\n]*(?:`\r?\n[^\n]*)*',
        codigo,
    )

    assert len(llamadas) >= 6, llamadas
    for llamada in llamadas:
        assert re.search(r'--environment-name"?,? "?maqueta\b', llamada), llamada


def test_f035_t20_el_borrado_del_entorno_nombra_maqueta_y_no_pregunta_dos_veces():
    borrados = _llamadas("staticwebapp environment delete")

    assert len(borrados) == 1
    assert "--environment-name maqueta" in borrados[0]
    assert "--yes" in borrados[0]


# --- Las comprobaciones en ejecución --------------------------------------------


def test_f035_t20_sin_backend_o_para_y_antes_de_las_app_settings():
    codigo = sin_comentarios(_texto())
    subida = codigo.find("swa deploy")
    comprobacion = codigo.find("if ((Backends-Del-Entorno) -ne \"0\")", subida)
    app_settings = codigo.find("az staticwebapp appsettings set")

    assert -1 < subida < comprobacion < app_settings
    assert "$SALIDA_CON_BACKEND" in codigo[comprobacion:app_settings]
    # Review 7: se cuenta en PowerShell, sin `--query` (que pasaría por
    # cmd.exe), y lo que no se puede leer ni interpretar vuelve `$null`, que
    # cuenta como «tiene»: `$null -ne "0"`.
    funcion = sin_comentarios(_funcion(_texto(), "Backends-Del-Entorno"))
    assert '"--environment-name", "maqueta", "-o", "json")' in funcion
    assert "--query" not in funcion
    assert "ConvertFrom-Json -InputObject $json -ErrorAction Stop" in funcion
    assert "if (-not $json) { return $null }" in funcion
    assert re.search(r"catch \{\s*return \$null\s*\}", funcion)
    assert "return [string]@($lista).Count" in funcion


def test_f035_t20_si_el_entorno_ya_existe_se_mira_su_backend_antes_de_subir():
    codigo = sin_comentarios(_texto())

    previa = codigo.find("$backendsPrevios -ne \"0\"")
    assert -1 < previa < codigo.find("swa deploy")


def test_f035_t20_las_app_settings_se_comprueban_en_el_entorno_despues_de_fijarlas():
    codigo = sin_comentarios(_texto())
    fijar = codigo.find("az staticwebapp appsettings set")
    comprobar = codigo.find('"appsettings", "list"', fijar)
    parar = codigo.find("$SALIDA_SIN_APPSETTINGS", comprobar)
    retorno = codigo.find("az ad app update --id $appId --web-redirect-uris $todas")

    assert -1 < fijar < comprobar < parar < retorno
    # Quedan si el `set` salió bien Y la lectura del entorno devuelve lo fijado.
    assert (
        "$quedaron = $fijadas -and ($idEnEntorno -eq $clientId) -and ($secretoEnEntorno -eq $secreto)"
        in codigo
    )
    assert "if (-not $quedaron) {" in codigo[comprobar:parar]
    assert "--setting-names \"AZURE_CLIENT_ID=$clientId\" \"AZURE_CLIENT_SECRET=$secreto\"" in codigo


def test_f035_t20_los_valores_salen_del_key_vault_y_el_secreto_se_suelta():
    codigo = sin_comentarios(_texto())

    for secreto in ("swa-client-id", "swa-client-secret"):
        assert f'"keyvault", "secret", "show", "--vault-name", $PostventaKeyVault, "--name", "{secreto}"' in codigo
    # Se suelta en cuanto se ha comprobado lo que quedó en el entorno (la otra
    # asignación a `$null`, en la guarda de cmd, no cuenta: es otra salida).
    assert re.search(r"\$quedaron = [^\n]*\n\s*\$secreto = \$null\s*\n", codigo)


def test_f035_t20_el_host_se_lee_y_se_comprueba_que_no_es_el_de_produccion():
    codigo = sin_comentarios(_texto())

    assert '"--environment-name", "maqueta", "--query", "hostname"' in _funcion(
        _texto(), "Host-Del-Entorno"
    )
    assert '$hostEntorno -notlike "*-maqueta.*"' in codigo
    assert "$hostEntorno -eq $hostProduccion" in codigo


def test_f035_t20_el_registro_de_la_lista_es_el_del_key_vault():
    codigo = sin_comentarios(_texto())

    assert "$appId -ne $clientId" in codigo
    assert "$SALIDA_REGISTRO_INCOHERENTE" in codigo


# --- La lista de URL de retorno, entera ------------------------------------------


def test_f035_t20_cada_reescritura_de_la_lista_va_entera_y_se_comprueba():
    codigo = sin_comentarios(_texto())
    actualizaciones = _llamadas("az ad app update")

    assert sorted(actualizaciones) == sorted(
        [
            "            az ad app update --id $appId --web-redirect-uris $quedan --only-show-errors | Out-Null",
            "        az ad app update --id $appId --web-redirect-uris $todas --only-show-errors | Out-Null",
        ]
    )
    assert "$todas = @($retornos) + $nuevoRetorno" in codigo
    assert "$quedan = @($retornos | Where-Object { $_ -notmatch $patronRetornoMaqueta })" in codigo
    # Después de cada una se vuelve a leer la lista.
    assert codigo.count("$despues = @(Retornos-Registrados $appId)") == 2


def test_f035_t20_nunca_se_reescribe_la_lista_vacia():
    codigo = sin_comentarios(_texto())
    primera = codigo.find("az ad app update")

    confirmacion = codigo.find('Read-Host "Escribe $palabra')
    borrado = codigo.find("az staticwebapp environment delete")

    assert -1 < codigo.find("if ($retornos.Count -eq 0)") < confirmacion < primera
    # Review 7: lo que quedaría al retirar se comprueba ANTES de confirmar y de
    # borrar el entorno, no después.
    guarda = codigo.find(
        "if ($Retirar -and $retornosMaqueta.Count -gt 0 -and $quedan.Count -eq 0) {"
    )
    assert -1 < codigo.find("$quedan = @($retornos") < guarda < confirmacion < borrado
    assert "$SALIDA_LISTA_VACIA" in codigo[guarda:confirmacion]


def test_f035_t20_retirar_solo_quita_las_de_maqueta():
    texto = _texto()
    patron = re.search(r"\$patronRetornoMaqueta = '([^']+)'", texto)

    assert patron
    regex = re.compile(patron.group(1))
    host = "anfitrion-" + "0" * 4
    assert regex.match(f"https://{host}-maqueta.region.1.dominio/.auth/login/aad/callback")
    assert not regex.match(f"https://{host}.1.dominio/.auth/login/aad/callback")
    assert not regex.match(f"https://{host}-otra.region.1.dominio/.auth/login/aad/callback")
    assert not regex.match(f"https://maqueta-{host}.1.dominio/.auth/login/aad/callback")
    assert not regex.match(f"https://{host}-maqueta.region.1.dominio/otra/ruta")


# --- Las piezas duplicadas de desplegar_front.ps1 (opción B) ---------------------


@pytest.mark.parametrize("nombre", FUNCIONES_DUPLICADAS)
def test_f035_t20_cada_funcion_duplicada_es_identica_a_la_de_desplegar_front(nombre):
    assert _funcion(_texto(), nombre) == _funcion(_texto(FRONT), nombre), (
        f"{nombre} ya no es igual en publicar_maqueta.ps1 y desplegar_front.ps1: cambia las dos"
    )


def test_f035_t20_la_lista_de_lo_que_no_se_publica_es_identica():
    assert _exclusiones(_texto()) == _exclusiones(_texto(FRONT))


def test_f035_t20_el_marcador_del_inquilino_es_el_mismo_y_se_comprueba():
    for texto in (_texto(), _texto(FRONT)):
        assert '$marcadorInquilino = "<TENANT_ID>"' in texto
        assert '$texto -notlike "*$marcadorInquilino*"' in texto


def test_f035_t20_control_la_identidad_caza_una_copia_cambiada():
    """Si el test de identidad no ve una diferencia, no protege nada."""
    front = _texto(FRONT)
    cambiada = front.replace('"Que hacer: $QueHacer"', '"Que hay que hacer: $QueHacer"')
    otra_lista = front.replace('"dev_server.py", ', "")

    assert cambiada != front and otra_lista != front
    assert _funcion(cambiada, "Salir-Con") != _funcion(_texto(), "Salir-Con")
    assert _exclusiones(otra_lista) != _exclusiones(_texto())


# --- Lo de todos los scripts de infra/ (R3-R8 de F-010) --------------------------


def test_f035_t20_whatif_y_confirmacion_antes_de_la_primera_escritura():
    codigo = sin_comentarios(_texto())
    primera = PATRON_ESCRITURA.search(codigo)

    assert primera, "no encuentro ninguna escritura"
    whatif = codigo.find("-WhatIf: no se ha")
    confirmacion = codigo.find('Read-Host "Escribe $palabra para continuar')
    assert -1 < whatif < confirmacion < primera.start()
    bloque = codigo[codigo.rfind("if ($WhatIf) {", 0, whatif):confirmacion]
    assert bloque.startswith("if ($WhatIf) {") and "exit 0" in bloque, "-WhatIf tiene que salir"
    assert '"RETIRAR" } else { "PUBLICAR" }' in codigo


def test_f035_t20_cada_causa_tiene_su_codigo_y_dice_que_hacer():
    codigos = re.findall(r"^\$SALIDA_[A-Z_]+ = (\d+)\r?$", _texto(), re.MULTILINE)

    assert len(codigos) >= 5
    assert len(set(codigos)) == len(codigos)
    assert "Que hacer:" in _texto()


def test_f035_t20_la_consola_queda_como_estaba():
    texto = _texto()
    inicio_try = texto.find("\ntry {")
    previo = re.search(r"^\$tokenPrevio = \$env:SWA_CLI_DEPLOYMENT_TOKEN\r?$", texto, re.MULTILINE)
    final = texto.find("\nfinally {")

    assert previo and previo.start() < inicio_try < final
    assert texto.find("$env:SWA_CLI_DEPLOYMENT_TOKEN = $tokenPrevio") > final
    assert texto.find("Remove-Item -Path $copiaDeTrabajo") > final
    assert "--deployment-token" not in texto


def test_f035_t20_no_imprime_identificadores_ni_secretos():
    culpables = [
        linea.strip()
        for linea in _texto().splitlines()
        if "Write-Host" in linea
        and re.search(r"\$(appId|clientId|inquilino|secreto|secretoEnEntorno|token|idEnEntorno)\b", linea)
    ]

    assert culpables == []


def test_f035_t20_ni_un_valor_dentro():
    texto = _texto()

    assert PATRON_GUID.findall(texto) == []
    assert PATRON_HOST.findall(texto) == []
    assert PATRON_IP.findall(texto) == []
    assert PATRON_CREDENCIAL.findall(texto) == []
    assert [n for n in NOMBRES_DE_RECURSO if n in texto] == []


def test_f035_t20_control_los_barridos_cazan_un_valor_inyectado():
    guid = "-".join(("a1b2c3d4", "e5f6", "4a7b", "8c9d", "0e1f2a3b4c5d"))  # noqa: FLY002
    host = "inventado" + "." + "azurestaticapps" + ".net"

    assert PATRON_GUID.findall(f"--id {guid}") == [guid]
    assert PATRON_HOST.findall(f"https://{host}/") == [host]
    assert PATRON_ESCRITURA.search("    az ad app update --id $x")
    assert PATRON_ESCRITURA.search("    swa deploy $x --env maqueta")


# --- Review 7 · Lo que cmd.exe rompe al pasar por az.cmd --------------------------
#
# En Windows `az` es `az.cmd` (y `swa`, `swa.cmd`): los argumentos llegan a un
# bloque `IF ( ... )` de cmd.exe a través de `%*`. Windows PowerShell 5.1 solo
# entrecomilla un argumento si lleva espacios, así que uno como `length(@)`
# llega desnudo y su `)` cierra el `IF`: cmd falla («No se esperaba -o en este
# momento»), `az` no llega a ejecutarse y la lectura vuelve vacía. Le pasó a
# `Backends-Del-Entorno` (review 7): el script paraba SIEMPRE con el código 9.
# Regla: ningún literal que el script pase a `az` o a `swa` puede llevar uno de
# estos caracteres sin llevar también un espacio (que es lo que hace que
# PowerShell lo entrecomille).

#: Los metacaracteres de cmd.exe que rompen un argumento sin comillas.
METACARACTERES_CMD = frozenset("()&|<>^")


def _literales_de(linea: str) -> list[str]:
    """Los literales que una línea de código pasa a `az`/`swa`, o `[]` si no llama."""
    if "Valor-De-Az @(" in linea:
        resto = linea.split("Valor-De-Az @(", 1)[1]
        return [a or b for a, b in re.findall(r"\"([^\"]*)\"|'([^']*)'", resto)]
    if not re.match(r"\s*(?:az|swa)\s", linea):
        return []
    orden = re.split(r"\s\|\s", linea, maxsplit=1)[0]
    orden = re.sub(r"\d?>\s*\$null|\d?>&\d", "", orden)
    try:
        piezas = shlex.split(orden, posix=True)
    except ValueError:
        piezas = orden.split()
    return [re.sub(r"\$\w+", "", p) for p in piezas if not p.startswith("$")]


def argumentos_rotos_por_cmd(texto: str) -> list[str]:
    """Los literales de `az`/`swa` que cmd.exe rompería: metacarácter y sin espacio."""
    problemas = []
    for linea in _lineas_juntas(sin_comentarios(texto).splitlines()):
        for literal in _literales_de(linea):
            if METACARACTERES_CMD & set(literal) and " " not in literal:
                problemas.append(f"{literal!r} en: {linea.strip()[:90]}")
    return problemas


def test_f035_t20_un_secreto_que_cmd_romperia_para_antes_de_escribirse():
    """El único valor libre que va sin comillas a `az` es el secreto: se vigila en ejecución."""
    codigo = sin_comentarios(_texto())
    guarda = codigo.find("if ($secreto -match '[()&|<>^%!\"]') {")
    escritura = codigo.find("az staticwebapp appsettings set")

    assert -1 < codigo.find("$secreto = Valor-De-Az") < guarda < escritura
    assert "$SALIDA_SIN_SECRETOS" in codigo[guarda:escritura]
    patron = re.search(r"\$secreto -match '([^']+)'", codigo).group(1)
    for caracter in METACARACTERES_CMD:
        assert re.search(patron, f"Ab8Q~x{caracter}y"), caracter
    assert not re.search(patron, "Ab8Q~x.y_z-1")


def test_f035_t20_ningun_argumento_de_az_se_rompe_al_pasar_por_cmd():
    assert argumentos_rotos_por_cmd(_texto()) == [], (
        "estos argumentos llegan sin comillas a az.cmd y cmd.exe los rompe"
    )


def test_f035_t20_control_la_regla_caza_el_defecto_de_la_review_7():
    """La línea de antes de la review 7 da rojo; una directa con `&&`, también; con espacios, no."""
    defecto = (
        '    return Valor-De-Az @("staticwebapp", "backends", "show", "--name", '
        '$PostventaStaticWebApp, "--resource-group", $PostventaGrupo, "--environment-name", '
        '"maqueta", "--query", "length(@)", "-o", "tsv")'
    )
    directa = "    az ad app list --query [?a&&b] --only-show-errors | Out-Null"
    con_espacios = (
        "    $x = Valor-De-Az @(\"webapp\", \"--query\", \"[?name=='X'].value | [0]\", \"-o\", \"tsv\")"
    )

    assert argumentos_rotos_por_cmd(_texto() + "\n" + defecto + "\n") != []
    assert argumentos_rotos_por_cmd(_texto() + "\n" + directa + "\n") != []
    assert argumentos_rotos_por_cmd(_texto() + "\n" + con_espacios + "\n") == []

