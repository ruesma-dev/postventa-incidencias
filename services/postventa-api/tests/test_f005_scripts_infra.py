# services/postventa-api/tests/test_f005_scripts_infra.py
"""Los dos scripts de `infra/` cumplen su contrato (F-005, R7, R35, R36, T21).

`tasks.md` deja la verificación de T21 en «revisión del script». Una revisión
no sobrevive a la siguiente edición: lo que sí sobrevive es esto. Los scripts
son PowerShell y no entran ni en la cobertura ni en la campaña de mutación
—`harness/alcance.py` solo mide `.py`—, así que su contrato se comprueba
leyéndolos desde un test de Python, igual que el DDL en `.sql` se comprueba
desde `test_f005_ddl_seguro.py`.

Lo que se fija aquí, y por qué cada cosa:

- **R7 · crear la base es cosa de una persona.** `CREATE DATABASE` y
  `CREATE ROLE` son de ámbito de servidor y `ddl.py` los rechaza. Su único
  sitio legítimo es `crear_base_postventa.ps1`, y detrás de una confirmación
  escrita.
- **R35 · Docker parado no es Docker ausente.** Decisión D3 del humano
  (2026-08-19), verificada en su puesto: hay Docker 29.5.3 instalado y el
  demonio suele estar parado. Los dos casos se arreglan de forma distinta, así
  que se distinguen y se dicen distinto.
- **R36 · sin `psql`.** No está en el `PATH` de ese puesto. Un script que lo
  invoque funciona en la máquina de quien lo escribió y en ninguna otra.
- **La trampa de PowerShell 5.1.** Redirigir el stderr de un ejecutable nativo
  con `$ErrorActionPreference = "Stop"` lanza un `NativeCommandError` y aborta
  el script. `docker rm -f` de un contenedor que no existe escribe en stderr y
  es el caso **normal** en la primera ejecución: el script moriría siempre en
  el arranque. Por eso todas las llamadas a `docker` pasan por un único punto
  que neutraliza la trampa.
- **Ningún secreto.** Estos ficheros sí se versionan; las credenciales se
  piden por consola y viven en memoria.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Raíz del repositorio, tres niveles por encima de este fichero.
RAIZ = Path(__file__).resolve().parent.parent.parent.parent

#: El directorio de los scripts re-ejecutables de despliegue.
INFRA = RAIZ / "infra"

#: El script que levanta la base desechable y ejecuta la suite (M1).
SCRIPT_EFIMERA = INFRA / "pruebas_bbdd_efimera.ps1"

#: El script que crea la base y el rol, una sola vez y a mano (R7).
SCRIPT_CREACION = INFRA / "crear_base_postventa.ps1"

#: El único punto por el que se llama a `docker`.
FUNCION_DOCKER = "Invocar-Docker"

#: Una redirección del stderr de un ejecutable nativo.
PATRON_REDIRECCION = re.compile(r"2>\s*(?:\$null|&1)")

#: La forma de un GUID, que es como se escriben los IDs de suscripción y de
#: inquilino de Azure. Ninguno puede estar en el repositorio.
PATRON_GUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

#: Un nombre de servidor de PostgreSQL de Azure, con su dominio completo.
PATRON_SERVIDOR_AZURE = re.compile(r"[\w-]+\.postgres\.database\.azure\.com")

#: Una credencial escrita a mano en el propio fichero.
PATRON_CREDENCIAL_LITERAL = re.compile(
    r"(?:password|contrasena|contraseña|pwd)\s*=\s*[\"'][^\"'$)]{4,}[\"']",
    re.IGNORECASE,
)


def _sin_comentarios(texto: str) -> list[str]:
    """Las líneas **ejecutables** del script.

    Se quitan el bloque de ayuda `<# ... #>` y las líneas de comentario. Hace
    falta porque los propios comentarios de estos scripts hablan de `psql` y
    del servidor compartido para explicar justo por qué no se usan: buscar en
    el texto crudo daría por rota la regla que el comentario está defendiendo.
    """
    sin_ayuda = re.sub(r"<#.*?#>", "", texto, flags=re.DOTALL)
    return [
        linea
        for linea in sin_ayuda.splitlines()
        if linea.strip() and not linea.lstrip().startswith("#")
    ]


def _cuerpo_de_funcion(texto: str, nombre: str) -> str:
    """El cuerpo de una función de PowerShell, contando llaves.

    Devuelve cadena vacía si la función no está declarada, que es lo que
    permite al test denunciarlo con un mensaje entendible en vez de reventar
    con un `IndexError`.
    """
    inicio = re.search(rf"function\s+{re.escape(nombre)}\b", texto)
    if inicio is None:
        return ""

    resto = texto[inicio.start() :]
    primera_llave = resto.find("{")
    if primera_llave == -1:
        return ""

    profundidad = 0
    for posicion, caracter in enumerate(resto[primera_llave:], start=primera_llave):
        if caracter == "{":
            profundidad += 1
        elif caracter == "}":
            profundidad -= 1
            if profundidad == 0:
                return resto[primera_llave : posicion + 1]
    return ""


def _invocaciones_de_docker(lineas: list[str]) -> list[str]:
    """Las líneas que **ejecutan** `docker`.

    `Get-Command docker` no lo ejecuta: comprueba si está instalado, que es la
    otra mitad de R35 y tiene que poder seguir ahí.
    """
    return [
        linea
        for linea in lineas
        if re.search(r"(?<![$\w-])docker\b", linea) and "Get-Command" not in linea
    ]


def _verbos_de_docker(texto: str) -> list[str]:
    """Los verbos de docker que el script usa, en el orden en que los usa.

    Las llamadas pasan por `Invocar-Docker` y el verbo es el primer elemento
    del array de argumentos: `@("run", "--rm", ...)` es `run`.
    """
    return re.findall(
        rf"{re.escape(FUNCION_DOCKER)}\s+-Argumentos\s+@\(\s*\"([a-z]+)\"", texto
    )


@pytest.fixture(scope="module")
def efimera() -> str:
    return SCRIPT_EFIMERA.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def creacion() -> str:
    return SCRIPT_CREACION.read_text(encoding="utf-8")


def test_f005_t21_los_dos_scripts_de_infra_existen():
    """Sin esto, todo lo demás pasaría en verde leyendo ficheros vacíos."""
    assert SCRIPT_EFIMERA.is_file()
    assert SCRIPT_CREACION.is_file()
    assert SCRIPT_EFIMERA.read_text(encoding="utf-8").strip()
    assert SCRIPT_CREACION.read_text(encoding="utf-8").strip()


def test_f005_cada_script_empieza_por_su_ruta_relativa(efimera, creacion):
    """Convención del proyecto (`docs/CONVENTIONS.md`), también en PowerShell."""
    assert efimera.splitlines()[0] == "# infra/pruebas_bbdd_efimera.ps1"
    assert creacion.splitlines()[0] == "# infra/crear_base_postventa.ps1"


def test_f005_r36_ningun_script_de_infra_invoca_psql(efimera, creacion):
    """R36 · `psql` no está en el `PATH` de ese puesto.

    La espera a que la base responda y cualquier comprobación se hacen con
    `psycopg`, desde el intérprete del `.venv` del servicio.
    """
    for nombre, texto in (("efímera", efimera), ("creación", creacion)):
        ejecutables = _sin_comentarios(texto)
        con_psql = [linea for linea in ejecutables if re.search(r"\bpsql\b", linea)]
        assert con_psql == [], f"el script de {nombre} invoca psql"


def test_f005_r35_el_script_efimero_distingue_docker_ausente_de_docker_parado(efimera):
    """R35 · dos problemas distintos, dos mensajes distintos.

    Un único «no puedo con Docker» manda a quien lo lea a instalar algo que ya
    tiene. El caso real de este puesto es el segundo: instalado y parado.
    """
    ejecutables = "\n".join(_sin_comentarios(efimera))
    verbos = _verbos_de_docker(ejecutables)

    assert "Get-Command docker" in ejecutables, "no se comprueba si está instalado"
    assert "info" in verbos, "no se comprueba si el demonio responde"
    assert "docker desktop" in ejecutables.lower(), (
        "el mensaje del demonio parado no dice qué arrancar"
    )

    posicion_ausente = ejecutables.find("Get-Command docker")
    posicion_parado = ejecutables.find('@("info")')
    assert posicion_ausente < posicion_parado, (
        "se comprueba antes que Docker responda que si está instalado: quien "
        "no lo tenga recibirá el mensaje equivocado"
    )


def test_f005_r35_el_script_efimero_comprueba_docker_antes_de_tocar_nada(efimera):
    """La comprobación va **primero**, no tres pasos después.

    Si se hiciera después de `docker run`, el fallo llegaría como un error
    opaco de conexión a una base que nunca llegó a existir.
    """
    verbos = _verbos_de_docker("\n".join(_sin_comentarios(efimera)))

    assert "run" in verbos, "el script no levanta ningún contenedor"
    assert verbos.index("info") < verbos.index("run")


def test_f005_el_contenedor_efimero_se_destruye_pase_lo_que_pase(efimera):
    """El contenedor se tira en un `finally`, no al final del camino feliz.

    Un test en rojo dejaría si no una PostgreSQL viva escuchando en el puerto,
    y la siguiente ejecución fallaría al levantar la suya.
    """
    ejecutables = "\n".join(_sin_comentarios(efimera))

    posicion_finally = ejecutables.rfind("finally")
    assert posicion_finally != -1, "el script no tiene bloque finally"

    assert "rm" in _verbos_de_docker(ejecutables[posicion_finally:]), (
        "el contenedor no se destruye dentro del finally"
    )


def test_f005_toda_llamada_a_docker_pasa_por_el_punto_que_neutraliza_powershell(
    efimera,
):
    """La trampa de PowerShell 5.1, cerrada en un solo sitio.

    Con `$ErrorActionPreference = "Stop"`, redirigir el stderr de un ejecutable
    nativo lanza un `NativeCommandError` **terminante**. `docker rm -f` de un
    contenedor que no existe escribe en stderr, y eso pasa en toda primera
    ejecución: sin este cierre el script aborta antes de empezar.

    Se arregla en una función porque `$ErrorActionPreference` tiene ámbito de
    función: dentro vale `Continue`, y fuera sigue valiendo `Stop`.
    """
    cuerpo = _cuerpo_de_funcion(efimera, FUNCION_DOCKER)
    assert cuerpo, f"el script no declara la función {FUNCION_DOCKER}"
    assert '$ErrorActionPreference = "Continue"' in cuerpo, (
        f"{FUNCION_DOCKER} no neutraliza la trampa: sin bajar "
        f"$ErrorActionPreference, la redirección del stderr aborta el script"
    )

    fuera = _invocaciones_de_docker(
        [linea for linea in _sin_comentarios(efimera) if linea not in cuerpo]
    )
    assert fuera == [], (
        f"hay llamadas a docker fuera de {FUNCION_DOCKER}: {fuera}"
    )


def test_f005_ninguna_redireccion_de_stderr_fuera_de_ese_punto(efimera, creacion):
    """La misma trampa, mirada desde el otro lado.

    Vigila los dos scripts: el de creación también llama a un ejecutable
    nativo —el `python` del `.venv`— y una redirección suelta ahí tendría el
    mismo efecto.
    """
    cuerpo_docker = _cuerpo_de_funcion(efimera, FUNCION_DOCKER)

    for nombre, texto in (("efímera", efimera), ("creación", creacion)):
        sueltas = [
            linea
            for linea in _sin_comentarios(texto)
            if PATRON_REDIRECCION.search(linea) and linea not in cuerpo_docker
        ]
        assert sueltas == [], (
            f"el script de {nombre} redirige el stderr de un nativo fuera de "
            f"{FUNCION_DOCKER}: {sueltas}"
        )


def test_f005_r7_crear_base_y_rol_solo_desde_el_script_manual(creacion, efimera):
    """R7 · lo que la aplicación no puede hacer nunca.

    `CREATE DATABASE` y `CREATE ROLE` son de ámbito de servidor y
    `psql-albaranes-rs9k2` sostiene la producción de otros tres proyectos.
    `ddl.py` los rechaza antes de abrir conexión; su único sitio es este
    script, que ejecuta una persona mirando lo que va a pasar.
    """
    assert "CREATE DATABASE" in creacion
    assert "CREATE ROLE" in creacion

    assert "CREATE DATABASE" not in efimera
    assert "CREATE ROLE" not in efimera


def test_f005_r7_la_creacion_exige_una_confirmacion_escrita(creacion):
    """Escribir en un servidor compartido no puede ser un `Enter` de más."""
    ejecutables = "\n".join(_sin_comentarios(creacion))

    assert "Read-Host" in ejecutables
    assert "CREAR" in ejecutables

    posicion_confirmacion = ejecutables.find("CREAR")
    posicion_creacion = ejecutables.find("CREATE ROLE")
    assert posicion_confirmacion < posicion_creacion, (
        "se crea el rol antes de pedir la confirmación"
    )


def test_f005_la_creacion_no_toca_nada_de_ambito_de_servidor(creacion):
    """Ni parámetros, ni autenticación, ni almacenamiento, ni extensiones.

    Lo comparten albaranes, partes y el datamart: `CLAUDE.md` lo prohíbe.
    """
    ejecutables = "\n".join(_sin_comentarios(creacion)).upper()

    for prohibida in ("ALTER SYSTEM", "CREATE EXTENSION", "PG_RELOAD_CONF", "DROP "):
        assert prohibida not in ejecutables, (
            f"el script ejecuta '{prohibida}', que es de ámbito de servidor"
        )


def test_f005_el_script_manual_deja_el_entorno_como_estaba(creacion):
    """Lo que el script mete en el entorno, el script lo deja como estaba.

    `PG_PASSWORD` es lo grave —queda una credencial viva en la consola de
    quien lo lanzó—, pero las demás tampoco pueden quedarse: la siguiente cosa
    que ese humano ejecute en la misma ventana heredaría una configuración que
    no puso él, apuntando al servidor compartido.

    Se comprueba que **cada** variable que el script escribe está en la lista
    que guarda y restaura. Es la parte que se olvida al añadir la séptima
    variable, y la que este test caza.
    """
    puestas = set(re.findall(r"\$env:([A-Z][A-Z0-9_]*)\s*=", creacion))
    censadas = set(re.findall(r"\"([A-Z][A-Z0-9_]*)\"", creacion))

    assert puestas, "el script no define ninguna variable de entorno"
    assert puestas <= censadas, (
        f"variables que el script escribe y no guarda ni restaura: "
        f"{sorted(puestas - censadas)}"
    )

    assert "GetEnvironmentVariable" in creacion, (
        "no se guarda el valor anterior: restaurar sin guardar es borrar"
    )
    assert 'Remove-Item -Path "Env:\\$nombre"' in creacion
    assert 'Set-Item -Path "Env:\\$nombre"' in creacion


def test_f005_ningun_secreto_literal_en_los_scripts_de_infra(efimera, creacion):
    """Estos ficheros sí se versionan, y git no suelta lo que entra.

    Ni contraseñas, ni nombres de servidor completos, ni IDs de suscripción o
    de inquilino. Todo se pide por consola o llega por parámetro.
    """
    for nombre, texto in (("efímera", efimera), ("creación", creacion)):
        assert PATRON_GUID.search(texto) is None, f"GUID literal en {nombre}"
        assert PATRON_SERVIDOR_AZURE.search(texto) is None, (
            f"nombre de servidor de Azure en {nombre}"
        )
        assert PATRON_CREDENCIAL_LITERAL.search(texto) is None, (
            f"credencial escrita a mano en {nombre}"
        )


def test_f005_las_credenciales_se_piden_como_securestring(creacion):
    """Una contraseña tecleada en claro queda en el historial de la consola."""
    ejecutables = "\n".join(_sin_comentarios(creacion))

    assert ejecutables.count("-AsSecureString") >= 2


def _python_incrustado(texto: str) -> list[str]:
    """Los `here-string` de PowerShell que llevan dentro un programa Python.

    Se reconocen por el `import`. Las interpolaciones de PowerShell (`$Var`)
    se sustituyen por un `0` para poder compilar: lo que se comprueba es la
    sintaxis del programa, no el valor que le llega.
    """
    bloques = re.findall(r"@[\"'](.*?)[\"']@", texto, flags=re.DOTALL)
    return [
        re.sub(r"\$[A-Za-z_]\w*", "0", bloque)
        for bloque in bloques
        if re.search(r"^import |^from ", bloque, flags=re.MULTILINE)
    ]


def test_f005_el_python_incrustado_en_los_scripts_compila(efimera, creacion):
    """Los dos scripts llevan Python dentro, y ese Python tiene que compilar.

    No hay `psql` en el puesto (R36), así que todo lo que habla con PostgreSQL
    desde estos scripts es `psycopg` incrustado en un `here-string`. Un error
    de sintaxis ahí no lo ve nadie hasta que alguien lanza el script contra el
    servidor compartido, con la confirmación ya escrita y el rol ya creado.
    """
    total = 0
    for nombre, texto in (("efímera", efimera), ("creación", creacion)):
        bloques = _python_incrustado(texto)
        assert bloques, f"no se ha encontrado el Python incrustado en {nombre}"
        for bloque in bloques:
            compile(bloque, f"<{nombre}>", "exec")
            total += 1

    assert total >= 2


def test_f005_el_python_incrustado_no_recibe_credenciales_por_argumento(
    efimera, creacion
):
    """Las contraseñas no viajan en la línea de comandos.

    La línea de comandos de un proceso la lee cualquiera con un `Get-Process`.
    Van por `stdin` o por variable de entorno.
    """
    for nombre, texto in (("efímera", efimera), ("creación", creacion)):
        for bloque in _python_incrustado(texto):
            culpables = [
                linea
                for linea in bloque.splitlines()
                if "sys.argv" in linea and "password" in linea.lower()
            ]
            assert culpables == [], (
                f"el Python de {nombre} recibe una credencial por argumento: "
                f"{culpables}"
            )


def test_f005_el_script_efimero_no_apunta_nunca_al_servidor_compartido(efimera):
    """La base desechable vive en esta máquina y en ningún otro sitio.

    El `conftest.py` de `tests_bbdd` aborta si el DSN sale de aquí; esto es el
    fusible de antes, en el sitio donde se compone ese DSN.
    """
    ejecutables = "\n".join(_sin_comentarios(efimera))

    assert "127.0.0.1" in ejecutables
    assert "psql-albaranes" not in ejecutables
