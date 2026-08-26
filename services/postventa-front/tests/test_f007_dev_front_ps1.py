# services/postventa-front/tests/test_f007_dev_front_ps1.py
"""El script con el que el humano arranca el front, comprobado de verdad.

`dev_front.ps1` es la única pieza de F-007 que ejecuta una persona a mano, y la
que se usa en la verificación manual T14. Si está roto, lo descubre el humano
en mitad de la demo.

Se comprueban dos cosas que se rompen solas:

1. **La codificación.** `docs/CONVENTIONS.md` (convenios de Ruesma): PowerShell
   en **UTF-8 con BOM y CRLF**. Sin BOM, Windows PowerShell 5.1 lee las tildes
   como bytes sueltos; con LF, algunos editores corporativos lo enseñan en una
   sola línea.
2. **Que `-Ayuda` imprime y NO arranca nada.** Es lo que se le dice al humano
   que pruebe primero.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

RAIZ_FRONT = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ_FRONT / "dev_front.ps1"

BOM = b"\xef\xbb\xbf"


def _ruta_de_powershell() -> str | None:
    return shutil.which("powershell")


def test_f007_r36_el_script_existe_y_va_en_utf8_con_bom_y_crlf():
    crudo = SCRIPT.read_bytes()

    assert crudo.startswith(BOM), "dev_front.ps1 tiene que ir en UTF-8 con BOM"
    assert crudo.count(b"\n") == crudo.count(b"\r\n"), (
        "dev_front.ps1 tiene que ir con finales de línea CRLF"
    )


def test_f007_r36_el_script_declara_los_dos_parametros_con_sus_valores():
    contenido = SCRIPT.read_text(encoding="utf-8-sig")

    assert "[int]$Puerto = 5173" in contenido
    assert '[string]$Api = "http://localhost:7073"' in contenido
    assert "[switch]$Ayuda" in contenido


def test_f007_r36_el_script_no_lleva_ningun_secreto_ni_ruta_de_maquina():
    """Ni credenciales, ni tenant, ni la carpeta de nadie."""
    contenido = SCRIPT.read_text(encoding="utf-8-sig")

    for prohibido in ("password", "secret", "TENANT", "C:\\Users\\"):
        assert prohibido.lower() not in contenido.lower(), (
            f"dev_front.ps1 contiene '{prohibido}'"
        )


def test_f007_r36_la_ayuda_se_imprime_y_no_arranca_nada():
    """`-Ayuda` sale con 0, imprime el uso y no levanta ningún servidor.

    Si `powershell` no está, esto **falla diciéndolo**: no se salta en
    silencio, igual que con `node` (R32). Este es un proyecto de un entorno
    Windows y `infra/` entero son scripts de PowerShell.
    """
    powershell = _ruta_de_powershell()
    assert powershell is not None, (
        "no se encuentra 'powershell' en el PATH y dev_front.ps1 es el punto de "
        "entrada del humano"
    )

    proceso = subprocess.run(
        [powershell, "-NoProfile", "-File", str(SCRIPT), "-Ayuda"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )

    assert proceso.returncode == 0, proceso.stderr
    assert "dev_front.ps1" in proceso.stdout
    assert "-Puerto" in proceso.stdout and "-Api" in proceso.stdout
    assert "func start --port 7073" in proceso.stdout
    assert "http://localhost:5173" not in proceso.stdout, (
        "la ayuda no debe anunciar que el front está sirviendo: no ha arrancado"
    )
