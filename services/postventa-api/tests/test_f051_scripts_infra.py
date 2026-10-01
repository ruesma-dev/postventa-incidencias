# services/postventa-api/tests/test_f051_scripts_infra.py
"""F-051 T3 · el despliegue no escribe nunca un App Setting vacío.

El incidente del 2026-10-01 empezó aquí: `desplegar_backend.ps1` escribía
`SHAREPOINT_CARPETA_BASE=` (vacía, D-1 de F-013) y Azure **no pasa a la
aplicación un App Setting de valor vacío**. La raíz se escribe ahora como `/`,
que el dominio recorta a la raíz (`unir_ruta`) y la fábrica admite en
`posventa` (F-013 R17).

Lo que se fija:

- `00_vars_postventa.ps1` declara la raíz como `"/"`, no como `""`;
- `desplegar_backend.ps1` pasa la base por `Carpeta-Base-Para-Azure` (vacía o
  solo blancos → `/`) y es eso lo que escribe y lo que enseña;
- y, además, **ninguna** App Setting sale vacía: `App-Settings-Vacias` las
  busca y el despliegue se para antes de `az functionapp config appsettings
  set`, nombrándolas. Es la defensa de la clase de fallo, no solo de este;
- `verificar_destino_sharepoint.ps1` deja de suponer `Postventa` cuando la
  base no está: con `posventa`, es la raíz, como en el servicio;
- los tres, ASCII, CRLF y con su ruta en la primera línea, como todo `infra/`.

Son PowerShell, así que ni cobertura ni mutación los miden. Lo que sí se
puede, y se hace cuando hay un PowerShell en la máquina, es **ejecutar** las
dos funciones nuevas: se copian de `desplegar_backend.ps1` a un `.ps1`
temporal y se lanzan con `-File` (nada de `-Command` con el programa
entrecomillado: es el defecto de PowerShell 5.1 de F-029).
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent.parent.parent
INFRA = RAIZ / "infra"

VARIABLES = INFRA / "00_vars_postventa.ps1"
DESPLIEGUE = INFRA / "desplegar_backend.ps1"
VERIFICAR = INFRA / "verificar_destino_sharepoint.ps1"
LOS_TRES = (VARIABLES, DESPLIEGUE, VERIFICAR)

POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")


def _texto(script: Path) -> str:
    return script.read_text(encoding="utf-8-sig")


def _sin_comentarios(texto: str) -> str:
    """El ejecutable: sin la ayuda `<# ... #>` y sin las líneas de comentario."""
    sin_ayuda = re.sub(r"<#.*?#>", "", texto, flags=re.DOTALL)
    return "\n".join(
        linea for linea in sin_ayuda.splitlines() if not linea.lstrip().startswith("#")
    )


def _funcion(texto: str, nombre: str) -> str:
    """De `function X {` a la `}` de la columna 0."""
    encontrado = re.search(
        rf"^function {re.escape(nombre)} \{{\r?\n.*?^\}}", texto, re.DOTALL | re.MULTILINE
    )
    assert encontrado, f"no encuentro la funcion {nombre}"
    return encontrado.group(0)


def _ajustes(texto: str) -> str:
    (bloque,) = re.findall(r"(?ms)^\$ajustes = @\((.*?)^\)", texto)
    return bloque


# --------------------------------------------------------------------------
# Los tres: como el resto de `infra/`
# --------------------------------------------------------------------------


@pytest.mark.parametrize("script", LOS_TRES, ids=lambda ruta: ruta.name)
def test_f051_t3_ascii_crlf_y_sin_bom(script):
    crudo = script.read_bytes()

    assert not crudo.startswith(b"\xef\xbb\xbf")
    crudo.decode("ascii")
    assert b"\n" not in crudo.replace(b"\r\n", b"")


@pytest.mark.parametrize("script", LOS_TRES, ids=lambda ruta: ruta.name)
def test_f051_t3_cada_script_empieza_por_su_ruta(script):
    assert _texto(script).startswith(f"# infra/{script.name}")


# --------------------------------------------------------------------------
# 00_vars · la raíz es "/"
# --------------------------------------------------------------------------


def test_f051_t3_las_variables_declaran_la_raiz_como_barra():
    """Una sola declaración ejecutable, y vale `/`."""
    assert re.findall(
        r'^\$CarpetaBaseArchivo = "(.*)"\r?$', _texto(VARIABLES), re.MULTILINE
    ) == ["/"]


# --------------------------------------------------------------------------
# desplegar_backend · nunca vacía, y nada vacío
# --------------------------------------------------------------------------


def test_f051_t3_el_despliegue_escribe_la_base_ya_resuelta():
    texto = _texto(DESPLIEGUE)
    ajustes = _ajustes(texto)

    assert '"SHAREPOINT_CARPETA_BASE=$carpetaBaseAppSetting"' in ajustes
    assert "SHAREPOINT_CARPETA_BASE=$CarpetaBaseArchivo" not in texto
    assert re.findall(
        r"^\$carpetaBaseAppSetting = Carpeta-Base-Para-Azure \$CarpetaBaseArchivo\r?$",
        texto,
        re.MULTILINE,
    )


def test_f051_t3_la_base_vacia_se_escribe_como_barra():
    cuerpo = _sin_comentarios(_funcion(_texto(DESPLIEGUE), "Carpeta-Base-Para-Azure"))

    assert "[string]::IsNullOrWhiteSpace($Carpeta)" in cuerpo
    assert 'return "/"' in cuerpo


def test_f051_t3_el_despliegue_ensena_lo_que_escribe():
    """Antes de confirmar y en el resumen: la base que de verdad va a Azure."""
    lineas = [
        linea
        for linea in _texto(DESPLIEGUE).splitlines()
        if "Destino del archivo" in linea
    ]

    assert len(lineas) == 2
    for linea in lineas:
        assert "$carpetaBaseAppSetting" in linea
        assert "$CarpetaBaseArchivo" not in linea


def test_f051_t3_ninguna_app_setting_vacia_llega_a_azure():
    """La guarda va **antes** de fijar las App Settings y sale por `Salir-Con`."""
    texto = _sin_comentarios(_texto(DESPLIEGUE))
    fijar = texto.index("az functionapp config appsettings set")
    guarda = texto.index("$vacias = @(App-Settings-Vacias $ajustes)")

    assert guarda < fijar
    tramo = texto[guarda:fijar]
    assert "if ($vacias.Count -gt 0)" in tramo
    assert "Salir-Con" in tramo
    assert "$SALIDA_FALLO" in tramo


def test_f051_t3_la_guarda_mira_el_valor_y_no_el_nombre():
    cuerpo = _sin_comentarios(_funcion(_texto(DESPLIEGUE), "App-Settings-Vacias"))

    assert "-split '=', 2" in cuerpo
    assert "[string]::IsNullOrWhiteSpace" in cuerpo


@pytest.mark.skipif(POWERSHELL is None, reason="sin PowerShell en esta maquina")
def test_f051_t3_las_dos_funciones_se_ejecutan_en_powershell(tmp_path):
    """Las funciones de verdad, copiadas tal cual y lanzadas con `-File`.

    Cada línea de salida es `caso=resultado`. La entrada con comillas es la
    forma de las referencias a Key Vault (`"X=@Microsoft.KeyVault(...)"`).
    """
    texto = _texto(DESPLIEGUE)
    programa = "\r\n".join(
        (
            _funcion(texto, "Carpeta-Base-Para-Azure"),
            _funcion(texto, "App-Settings-Vacias"),
            '"vacia=" + (Carpeta-Base-Para-Azure "")',
            '"blancos=" + (Carpeta-Base-Para-Azure "   ")',
            '"nula=" + (Carpeta-Base-Para-Azure $null)',
            '"barra=" + (Carpeta-Base-Para-Azure "/")',
            '"nombre=" + (Carpeta-Base-Para-Azure "Postventa")',
            '$lista = @("A=1", "B=", "C=  ", \'"D=@Microsoft.KeyVault(SecretUri=x)"\', \'"E="\', "F=/")',
            '"vacias=" + ((App-Settings-Vacias $lista) -join ",")',
            '"ninguna=" + @(App-Settings-Vacias @("A=1", "F=/")).Count',
        )
    )
    guion = tmp_path / "f051_funciones.ps1"
    guion.write_bytes(programa.encode("ascii"))

    salida = subprocess.run(
        [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(guion)],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    ).stdout
    resultado = dict(
        linea.split("=", 1) for linea in salida.splitlines() if "=" in linea
    )

    assert resultado == {
        "vacia": "/",
        "blancos": "/",
        "nula": "/",
        "barra": "/",
        "nombre": "Postventa",
        "vacias": "B,C,E",
        "ninguna": "0",
    }


# --------------------------------------------------------------------------
# verificar_destino_sharepoint · la ausencia, según la estrategia
# --------------------------------------------------------------------------


def test_f051_t3_la_verificacion_lee_la_estrategia():
    texto = _sin_comentarios(_texto(VERIFICAR))

    assert 'Get-Variable-De-Entorno "SHAREPOINT_ESTRUCTURA"' in texto


def test_f051_t3_la_verificacion_trata_la_raiz_como_raiz():
    """Con `posventa` y sin base, o con `/`, la base es la raíz y existe siempre.

    Antes comparaba el nombre de cada hija de la raíz con `Postventa`, que es
    justo el error del incidente reproducido en el puesto de trabajo.
    """
    texto = _sin_comentarios(_texto(VERIFICAR))

    assert '-eq "posventa"' in texto
    assert ".Trim().Trim('/').Trim()" in texto
    assert "$baseEsRaiz" in texto
    assert "if ($baseEsRaiz) { $existe = $true }" in texto


def _tramo_de_la_base(texto: str) -> str:
    """De la lectura de la estrategia a `$baseEsRaiz`, tal cual está en el script."""
    inicio = texto.index('$estructura = Get-Variable-De-Entorno "SHAREPOINT_ESTRUCTURA"')
    fin = texto.index("$baseEsRaiz = ", inicio)
    return texto[inicio : texto.index("\n", fin)]


@pytest.mark.skipif(POWERSHELL is None, reason="sin PowerShell en esta maquina")
@pytest.mark.parametrize(
    ("estructura", "base", "esperado"),
    (
        pytest.param(None, None, "por_obra|Postventa|False", id="nada"),
        pytest.param("posventa", None, "posventa||True", id="posventa-ausente"),
        pytest.param("posventa", "/", "posventa||True", id="posventa-barra"),
        pytest.param("por_obra", None, "por_obra|Postventa|False", id="por_obra-ausente"),
        pytest.param("por_obra", "/", "por_obra||True", id="por_obra-barra"),
        pytest.param("posventa", " OTRA/ ", "posventa|OTRA|False", id="posventa-nombre"),
    ),
)
def test_f051_t3_la_verificacion_decide_la_base_como_el_servicio(
    tmp_path, monkeypatch, estructura, base, esperado
):
    """El tramo real del script, ejecutado con cada combinación del entorno."""
    for variable, valor in (
        ("SHAREPOINT_ESTRUCTURA", estructura),
        ("SHAREPOINT_CARPETA_BASE", base),
    ):
        if valor is None:
            monkeypatch.delenv(variable, raising=False)
        else:
            monkeypatch.setenv(variable, valor)
    texto = _texto(VERIFICAR)
    programa = "\r\n".join(
        (
            '$EstructuraPorDefecto = "por_obra"',
            '$CarpetaBasePorDefecto = "Postventa"',
            _funcion(texto, "Get-Variable-De-Entorno"),
            _tramo_de_la_base(texto).replace("\r\n", "\n").replace("\n", "\r\n"),
            '"{0}|{1}|{2}" -f $estructura, $carpetaBase, $baseEsRaiz',
        )
    )
    guion = tmp_path / "f051_base.ps1"
    guion.write_bytes(programa.encode("ascii"))

    salida = subprocess.run(
        [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(guion)],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    ).stdout

    assert salida.strip() == esperado
