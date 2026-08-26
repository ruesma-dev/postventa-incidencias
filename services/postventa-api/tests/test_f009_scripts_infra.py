# services/postventa-api/tests/test_f009_scripts_infra.py
"""El script de alta manual cumple su contrato (F-009, R34, T12).

Al modo de `test_f005_scripts_infra.py`: el script es PowerShell y no entra ni
en la cobertura ni en la campaña de mutación —`harness/alcance.py` solo mide
`.py`—, así que su contrato se comprueba leyéndolo desde un test de Python,
igual que el DDL en `.sql` se comprueba desde `test_f005_ddl_seguro.py`.

Lo que se fija, y por qué cada cosa:

- **La regla dura de `CLAUDE.md`**: este script **no escribe en Sigrid**. Ni
  una sentencia. Su única llamada al ERP es una lectura, y la sirve un usuario
  SQL de solo lectura.
- **R32** · no marca como verificada una correspondencia que el ERP no ha
  confirmado. Por defecto entra **sin marca**.
- **R34** · existe justamente para los casos que no siguen la convención, así
  que tiene que poder dar de alta un login que la derivación nunca produciría.
- **Idempotente** · volver a lanzarlo con los mismos datos actualiza la fila,
  no crea una segunda identidad para la misma persona.
- **Ningún secreto y ningún login concreto**: este fichero sí se versiona.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Raíz del repositorio, tres niveles por encima de este fichero.
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

#: El script de alta manual de una correspondencia (R34).
SCRIPT = RAIZ / "infra" / "07_alta_usuario_sigrid.ps1"

#: Verbos que escribirían en el ERP. Ninguno puede aparecer.
VERBOS_DE_ESCRITURA_EN_SIGRID = ("INSERT INTO dbo.", "UPDATE dbo.", "DELETE FROM dbo.")

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


def _texto() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def _sin_ayuda(texto: str) -> str:
    """El script sin su bloque de ayuda `<# ... #>`.

    Hace falta porque la ayuda de este script explica **por qué** no escribe en
    Sigrid, y buscar en el texto crudo daría por rota la regla que el propio
    comentario está defendiendo.
    """
    return re.sub(r"<#.*?#>", "", texto, flags=re.DOTALL)


def test_f009_t12_el_script_de_alta_manual_existe():
    """R34 · sin él, los 2 de 8 casos medidos no tienen salida.

    Son usuarios reales del ERP cuyo login no se deriva de su correo. Sin este
    script, esas personas no podrían cerrar ninguna incidencia.
    """
    assert SCRIPT.is_file()


def test_f009_t12_el_script_no_escribe_jamas_en_sigrid():
    """`CLAUDE.md`, regla dura: en Sigrid solo se escribe desde el desplegado.

    Y este script lo ejecuta una persona desde su puesto. Su única llamada al
    ERP es un recuento, y la sirve el usuario de solo lectura de la pasarela.
    """
    ejecutable = _sin_ayuda(_texto()).upper()

    for verbo in VERBOS_DE_ESCRITURA_EN_SIGRID:
        assert verbo.upper() not in ejecutable


def test_f009_t12_la_unica_llamada_al_erp_es_de_lectura():
    """Y va al endpoint de lectura, no al de escritura.

    Se comprueba por la ruta y no solo por el verbo: es la diferencia que se ve
    de un vistazo al revisar el script.
    """
    ejecutable = _sin_ayuda(_texto())

    assert "/api/sql/read" in ejecutable
    assert "/api/sql/write" not in ejecutable


def test_f009_t12_la_consulta_al_erp_va_parametrizada():
    """`sigrid_api.md` §5.2 · marcadores `?`, nunca concatenación.

    Un login concatenado en la cadena sería una inyección contra el ERP,
    lanzada desde un puesto de trabajo.
    """
    ejecutable = _sin_ayuda(_texto())

    assert 'WHERE cod = ?' in ejecutable
    assert '"parameters"' in ejecutable


def test_f009_t12_el_script_es_idempotente():
    """Volver a lanzarlo actualiza la fila; no crea una segunda.

    Dos filas para la misma persona serían dos identidades para firmar el mismo
    cierre, y quién firma lo decidiría el azar de un `ORDER BY`.
    """
    ejecutable = _sin_ayuda(_texto())

    assert "ON CONFLICT (usuario_oid) DO UPDATE SET" in ejecutable


def test_f009_t12_el_alta_conserva_la_fecha_original():
    """Refrescar el alta al reconfirmar borraría desde cuándo existe el mapeo."""
    ejecutable = _sin_ayuda(_texto())

    assert "alta_at_utc = EXCLUDED.alta_at_utc" not in ejecutable
    assert "login_sigrid = EXCLUDED.login_sigrid" in ejecutable


def test_f009_r32_por_defecto_el_alta_queda_sin_marcar_como_verificada():
    """R32 · el script no da por comprobado lo que no ha comprobado.

    La marca la pone la aplicación la primera vez que esa persona cierre algo,
    contra el ERP. Un alta que se marcara sola convertiría «alguien lo escribió
    a mano» en «el ERP lo confirmó», que es exactamente lo que R32 prohíbe.
    """
    ejecutable = _sin_ayuda(_texto())

    assert "$verificado = $false" in ejecutable
    assert "-VerificarAhora" in ejecutable


def test_f009_t12_la_escritura_va_al_esquema_propio_y_nunca_a_public():
    """`CLAUDE.md`, regla dura: fuera del esquema propio no se toca nada.

    El servidor lo comparten albaranes, partes y el datamart.
    """
    ejecutable = _sin_ayuda(_texto())

    assert "usuarios_sigrid" in ejecutable
    assert "public." not in ejecutable.lower()


def test_f009_t12_el_nombre_del_esquema_se_valida_antes_de_pegarlo_al_sql():
    """Es lo único que se interpola, así que es lo único que hay que validar.

    Un `-Esquema` hostil sería una inyección con permisos de despliegue contra
    un servidor compartido. Es la misma regla que aplica
    `infrastructure/persistencia/ddl.py`.
    """
    ejecutable = _sin_ayuda(_texto())

    assert "isalnum" in ejecutable


def test_f009_r35_el_script_rechaza_un_login_que_no_cabe_en_el_erp():
    """R35 · 48 caracteres, y no se trunca: un login truncado es otro login."""
    ejecutable = _sin_ayuda(_texto())

    assert "48" in ejecutable
    assert "No se trunca" in ejecutable


def test_f009_t12_el_script_no_trae_ningun_secreto():
    """Este fichero **sí** se versiona, y el historial de git no suelta nada."""
    assert PATRON_CREDENCIAL_LITERAL.search(_texto()) is None


def test_f009_t12_las_credenciales_se_piden_por_consola_y_no_se_escriben():
    """Contraseña y clave de función: `SecureString`, y solo en memoria."""
    ejecutable = _sin_ayuda(_texto())

    assert ejecutable.count("-AsSecureString") >= 2
    assert "Remove-Item" in ejecutable


def test_f009_t12_el_script_no_trae_ningun_identificador_ni_host_real():
    """Ni un `oid` de nadie, ni la URL de la pasarela, ni el host de la base.

    Un ejemplo «para que se entienda mejor» es exactamente como acaba un
    identificador real en un repositorio.
    """
    texto = _texto()

    assert PATRON_GUID.findall(texto) == []
    assert PATRON_HOST_AZURE.findall(texto) == []


@pytest.mark.parametrize("parametro", ["UsuarioOid", "LoginSigrid"])
def test_f009_t12_los_dos_datos_de_la_correspondencia_son_obligatorios(parametro):
    """No hay valor por defecto para ninguno de los dos, y no puede haberlo.

    Un `oid` por omisión daría de alta la correspondencia de otra persona.
    """
    ejecutable = _sin_ayuda(_texto())
    linea = next(fila for fila in ejecutable.splitlines() if f"${parametro}" in fila)

    assert "Mandatory = $true" in linea


def test_f009_t12_el_script_no_trae_ningun_login_concreto():
    """Ni el de nadie del ERP: los ejemplos van con marcadores.

    Los logins que han cerrado partes de posventa son **tres**, y son personas.
    """
    ejemplos = [
        linea
        for linea in _texto().splitlines()
        if "07_alta_usuario_sigrid.ps1" in linea and "-UsuarioOid" in linea
    ]

    for linea in ejemplos:
        assert "<el" in linea, f"el ejemplo trae un valor concreto: {linea}"
