# services/postventa-api/infrastructure/persistencia/ddl.py
"""La guarda del DDL: qué se puede aplicar, y **antes** de abrir la conexión.

`psql-albaranes-rs9k2` es un servidor **compartido** con la producción de
albaranes, partes y el datamart. `CLAUDE.md` prohíbe dos cosas sin matices:
ejecutar DDL fuera del esquema propio, y tocar cualquier cosa de ámbito de
servidor. Este módulo es esa prohibición convertida en código.

## Por qué es Python y no un `.sql` más

`docs/CONVENTIONS.md` manda que el DDL viva en ficheros `NN_nombre.sql`, y ahí
vive. Pero las puertas de rigor del arnés (`harness/alcance.py`) solo miden y
mutan ficheros **`.py`**: un `.sql` escaparía entero a la cobertura y a la
campaña de mutación, justo el fichero más peligroso de la feature. Por eso el
DDL está en `.sql` —para poder leerlo antes de aplicarlo— y **todo lo que lo
interpreta está aquí**, donde sí se mide y se muta. Los tests de este módulo
leen los `.sql` reales del repositorio, así que el DDL no puede cambiar sin
que la guarda lo mire.

## Lista blanca, no lista negra

La lista negra de verbos (`VERBOS_PROHIBIDOS`) existe para que el error diga
**qué** se intentó (R6). Pero lo que de verdad sostiene la guarda es que solo
se reconocen **seis formas** de sentencia, todas idempotentes y todas
cualificadas con el esquema configurado. Lo que no se reconoce, no pasa: una
lista negra deja entrar todo lo que a nadie se le ocurrió prohibir.

## La sexta forma, y por qué es la única de datos (F-028)

Las cinco primeras son de **esquema**. La sexta es la **semilla**: un
`INSERT … SELECT … WHERE NOT EXISTS`, y entró con F-028 porque su histórico de
estado tiene que nacer con las aprobaciones que ya había en la tabla de F-026
—si no, el día del despliegue todo parte aprobado a mano perdería su decisión
humana—.

Se admite lo más estrecho que sirve para eso, y cada condición quita una forma
de hacer daño: **`NOT EXISTS` obligatorio** (sin él, cada arranque duplicaría
filas), **todo cualificado** con el esquema propio —también lo que se lee, que
en un servidor compartido es la mitad del problema— y **`ON CONFLICT`
prohibido**, que es R21 de F-028 escrito aquí: el DDL de este proyecto no
vuelve a admitir una escritura que pise filas. Lo que la sexta forma **no**
abre sigue cerrado: no hay `UPDATE`, ni `DELETE`, ni `TRUNCATE`.

Este módulo es **puro**: no importa `psycopg` y no abre nada. Que falle aquí
es que el arranque se cae **sin haber tocado la base de datos de nadie**.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from domain.models.errores import DdlInseguro

__all__ = [
    "ESQUEMA_LITERAL",
    "TIPOS_PROHIBIDOS",
    "VERBOS_PROHIBIDOS",
    "cargar_ddl",
    "ficheros_ddl",
    "sentencias",
    "validar",
    "validar_nombre_de_esquema",
    "valores_check",
]

#: Verbos de ámbito de **servidor** o de **base de datos** (R6). Ninguno de
#: estos puede llegar a intentarse: el servidor lo comparten cuatro proyectos.
#: `CREATE EXTENSION` está aquí, y por eso los UUID se generan en Python en vez
#: de con `gen_random_uuid()`.
VERBOS_PROHIBIDOS: tuple[str, ...] = (
    "CREATE DATABASE",
    "CREATE ROLE",
    "CREATE USER",
    "CREATE EXTENSION",
    "CREATE TABLESPACE",
    "ALTER SYSTEM",
    "ALTER DATABASE",
    "ALTER ROLE",
    "GRANT",
    "REVOKE",
    "DROP DATABASE",
    "DROP SCHEMA",
    "DROP ROLE",
    "CREATE PUBLICATION",
    "CREATE SUBSCRIPTION",
)

#: Tipos binarios (R12, R40). El PDF del parte lleva el DNI manuscrito, vive
#: en SharePoint, y el disco de este servidor es compartido, solo crece y ya
#: se llenó una vez (2026-08-09).
TIPOS_PROHIBIDOS: tuple[str, ...] = ("BYTEA", "BLOB", "LARGE OBJECT", "LO", "OID")

#: El esquema tal y como aparece **literal** en los `.sql`. Si el despliegue
#: configura otro (`PG_SCHEMA`), `cargar_ddl` lo sustituye en el mismo paso en
#: que valida: un solo sitio y una sola pasada.
ESQUEMA_LITERAL = "postventa"

#: Un nombre de esquema aceptable. Sin comillas, sin espacios y sin `;`: el
#: nombre viaja al `search_path` y a cada sentencia, así que un valor hostil
#: en `PG_SCHEMA` sería una inyección con permisos de despliegue.
_PATRON_ESQUEMA = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")

#: Los ficheros de DDL, `NN_nombre.sql` (R1, `docs/CONVENTIONS.md`).
_PATRON_FICHERO = re.compile(r"^\d{2}_[a-z0-9_]+\.sql$")

#: Apertura de un cuerpo entrecomillado con dólares: `$$` o `$etiqueta$`.
_PATRON_DOLAR = re.compile(r"\$\$|\$[A-Za-z_][A-Za-z0-9_]*\$")

_ESPACIOS = re.compile(r"\s+")

#: Cada tabla que una sentencia nombra: la que escribe (`INTO`) y las que lee
#: (`FROM`, `JOIN`). Todas tienen que estar cualificadas con el esquema
#: propio; en un servidor compartido, **leer** la base de otro proyecto cruza
#: la misma frontera que escribir en ella.
_PATRON_OBJETOS_REFERIDOS = re.compile(
    r"\b(?:INTO|FROM|JOIN)\s+([A-Za-z0-9_.\"]+)", flags=re.IGNORECASE
)

#: Cuántos caracteres de la sentencia culpable entran en el mensaje de error.
#: Suficiente para reconocerla; no tanto como para volcar una tabla entera en
#: un log.
_RECORTE = 80


# --- Troceado ---------------------------------------------------------------


def sentencias(texto: str) -> tuple[str, ...]:
    """Trocea un `.sql` en sentencias, cortando por `;`.

    Respeta el contexto, que es todo el trabajo: un `;` dentro de un
    comentario, de un literal `'…'` o de un cuerpo `$$…$$` **no** termina una
    sentencia. Si lo hiciera, se aplicarían fragmentos sueltos contra una base
    compartida.

    Los comentarios se eliminan —lo que se ejecuta es SQL, y así la guarda no
    tiene que distinguir un `CREATE DATABASE` real de uno mencionado en una
    explicación—, pero los saltos de línea y la indentación se conservan: lo
    que imprime el dry-run de la primera aplicación (M2) tiene que poder
    leerlo una persona.

    La última sentencia no necesita `;`, y los huecos —cadenas vacías,
    sentencias de solo comentario— no salen.
    """
    trozos: list[str] = []
    actual: list[str] = []
    posicion = 0
    fin = len(texto)

    while posicion < fin:
        if texto.startswith("--", posicion):
            salto = texto.find("\n", posicion)
            posicion = fin if salto == -1 else salto
            continue
        if texto.startswith("/*", posicion):
            cierre = texto.find("*/", posicion + 2)
            posicion = fin if cierre == -1 else cierre + 2
            actual.append(" ")
            continue

        caracter = texto[posicion]

        if caracter == "'":
            cierre = _fin_de_literal(texto, posicion)
            actual.append(texto[posicion:cierre])
            posicion = cierre
            continue

        etiqueta = _etiqueta_dolar(texto, posicion)
        if etiqueta is not None:
            cierre = texto.find(etiqueta, posicion + len(etiqueta))
            cierre = fin if cierre == -1 else cierre + len(etiqueta)
            actual.append(texto[posicion:cierre])
            posicion = cierre
            continue

        if caracter == ";":
            trozos.append("".join(actual))
            actual = []
            posicion += 1
            continue

        actual.append(caracter)
        posicion += 1

    trozos.append("".join(actual))
    return tuple(trozo.strip() for trozo in trozos if trozo.strip())


def _fin_de_literal(texto: str, inicio: int) -> int:
    """Posición justo detrás de la comilla que cierra el literal.

    Una comilla doblada (`''`) es una comilla dentro del literal, no su fin.
    """
    posicion = inicio + 1
    fin = len(texto)
    while posicion < fin:
        if texto[posicion] == "'":
            if posicion + 1 < fin and texto[posicion + 1] == "'":
                posicion += 2
                continue
            return posicion + 1
        posicion += 1
    return fin


def _etiqueta_dolar(texto: str, posicion: int) -> str | None:
    """La etiqueta `$$` o `$nombre$` que empieza aquí, si empieza alguna."""
    if texto[posicion] != "$":
        return None
    encontrada = _PATRON_DOLAR.match(texto, posicion)
    return encontrada.group(0) if encontrada else None


# --- Validación -------------------------------------------------------------


def validar(sentencia: str, *, esquema: str) -> None:
    """Levanta `DdlInseguro` si esta sentencia no puede aplicarse.

    Cinco controles, en este orden, y el primero que falla manda:

    1. El **nombre del esquema** configurado es un identificador aceptable.
    2. Es **una** sentencia, no varias.
    3. No usa ninguno de los `VERBOS_PROHIBIDOS` (R6).
    4. No nombra `public.` ni declara un tipo binario (R5, R12).
    5. Tiene una de las **seis** formas reconocidas, **idempotente** (R3) y
       **cualificada** con el esquema configurado (R5).

    No abre nada y no conoce ninguna conexión: cuando esto falla, la base de
    datos de los demás no se ha enterado de que existimos.
    """
    validar_nombre_de_esquema(esquema)

    troceadas = sentencias(sentencia)
    if len(troceadas) != 1:
        raise DdlInseguro(
            f"se esperaba una sola sentencia y se han encontrado "
            f"{len(troceadas)}: {_recortar(sentencia)}"
        )

    limpia = _ESPACIOS.sub(" ", troceadas[0]).strip()
    en_mayusculas = limpia.upper()

    _rechazar_verbos_de_servidor(limpia, en_mayusculas)
    _rechazar_esquema_ajeno(limpia, en_mayusculas)
    _rechazar_tipos_binarios(limpia, en_mayusculas)
    _validar_forma(limpia, en_mayusculas, esquema)


def validar_nombre_de_esquema(esquema: str) -> None:
    """El esquema configurado tiene que ser un identificador simple."""
    if not _PATRON_ESQUEMA.match(esquema or ""):
        raise DdlInseguro(
            f"el nombre de esquema configurado no es un identificador válido: "
            f"{esquema!r}. Solo minúsculas, dígitos y '_', empezando por letra "
            f"o '_'"
        )


def _rechazar_verbos_de_servidor(limpia: str, en_mayusculas: str) -> None:
    """R6 · ni una sentencia de ámbito de servidor o de base de datos."""
    for verbo in VERBOS_PROHIBIDOS:
        patron = r"\b" + r"\s+".join(verbo.split()) + r"\b"
        if re.search(patron, en_mayusculas):
            raise DdlInseguro(
                f"la sentencia usa '{verbo}', que es de ámbito de servidor o "
                f"de base de datos y está prohibida en un servidor compartido "
                f"(R6): {_recortar(limpia)}"
            )


def _rechazar_esquema_ajeno(limpia: str, en_mayusculas: str) -> None:
    """R5 · `public` es de los demás; nosotros no escribimos ahí."""
    if "PUBLIC." in en_mayusculas:
        raise DdlInseguro(
            f"la sentencia nombra el esquema 'public', que usan albaranes y "
            f"partes para sus propias tablas (R5): {_recortar(limpia)}"
        )


def _rechazar_tipos_binarios(limpia: str, en_mayusculas: str) -> None:
    """R12, R40 · ni un BLOB en un disco compartido que solo crece."""
    for tipo in TIPOS_PROHIBIDOS:
        patron = r"\b" + r"\s+".join(tipo.split()) + r"\b"
        if re.search(patron, en_mayusculas):
            raise DdlInseguro(
                f"la sentencia declara el tipo binario '{tipo}': los PDF viven "
                f"en SharePoint y de ellos solo se guardan metadatos (R12): "
                f"{_recortar(limpia)}"
            )


def _validar_forma(limpia: str, en_mayusculas: str, esquema: str) -> None:
    """Las seis formas reconocidas. Lo que no está aquí, no se aplica."""
    if en_mayusculas.startswith("INSERT INTO"):
        _validar_insert_semilla(limpia, en_mayusculas, esquema)
    elif en_mayusculas.startswith("CREATE SCHEMA"):
        _validar_create_schema(limpia, esquema)
    elif en_mayusculas.startswith("CREATE TABLE"):
        _validar_create_table(limpia, esquema)
    elif re.match(r"^CREATE (UNIQUE )?INDEX\b", en_mayusculas):
        _validar_create_index(limpia, esquema)
    elif re.match(r"^CREATE (OR REPLACE )?VIEW\b", en_mayusculas):
        _validar_create_view(limpia, esquema)
    elif en_mayusculas.startswith("ALTER TABLE"):
        _validar_alter_table(limpia, esquema)
    else:
        raise DdlInseguro(
            f"la sentencia no tiene ninguna de las formas reconocidas por la "
            f"guarda (CREATE SCHEMA / TABLE / INDEX / VIEW, ALTER TABLE ADD "
            f"COLUMN, INSERT SELECT con WHERE NOT EXISTS): "
            f"{_recortar(limpia)}"
        )


def _validar_insert_semilla(limpia: str, en_mayusculas: str, esquema: str) -> None:
    """`INSERT INTO <esquema>.<tabla> (…) SELECT … WHERE NOT EXISTS (…)`.

    La **semilla**: la única forma de sentencia de datos que el DDL admite, y
    la única que no crea nada (F-028, `design.md` §8.4). Sirve para que una
    tabla nueva nazca con lo que ya había en otra, que es un hecho que no puede
    esperar a la primera petición: el DDL se aplica en el arranque, antes de
    atenderla.

    Tres condiciones, y cada una quita una forma concreta de hacer daño:

    - **`SELECT` y `NOT EXISTS`, los dos.** Sin `NOT EXISTS` la sentencia no es
      idempotente (R3), y una semilla no idempotente añade las mismas filas en
      **cada arranque** de la Function. Un `INSERT … VALUES` cae por aquí, y es
      lo correcto: datos escritos a mano dentro del DDL no son una semilla.
    - **Todo cualificado**, lo que se escribe y lo que se lee. En un servidor
      compartido con la producción de albaranes, partes y el datamart, leer la
      tabla de otro proyecto cruza la misma frontera que escribir en ella.
    - **Ni un `ON CONFLICT`.** Es R21 de F-028 escrito en la guarda: el
      histórico de estado es append-only, y una escritura que pise filas
      escondida en un fichero que se aplica solo al arrancar es justo la que
      nadie revisaría. Las diez tablas anteriores tienen su `ON CONFLICT` en
      `sentencias.py`, donde se lee.

    Lo que esto **no** abre sigue cerrado: `UPDATE`, `DELETE` y `TRUNCATE` no
    son formas reconocidas y caen en `_validar_forma` sin llegar aquí.
    """
    if "ON CONFLICT" in en_mayusculas:
        raise DdlInseguro(
            f"la semilla lleva un ON CONFLICT: el DDL no admite escrituras que "
            f"pisen filas (F-028 R21): {_recortar(limpia)}"
        )
    if not re.search(r"\bSELECT\b", en_mayusculas):
        raise DdlInseguro(
            f"una semilla tiene que derivar sus filas de un SELECT: un INSERT "
            f"con VALUES son datos escritos a mano dentro del DDL: "
            f"{_recortar(limpia)}"
        )
    if not re.search(r"\bNOT EXISTS\s*\(", en_mayusculas):
        raise DdlInseguro(
            f"una semilla tiene que llevar WHERE NOT EXISTS para poder "
            f"aplicarse dos veces sin duplicar filas (R3): {_recortar(limpia)}"
        )

    referidos = _PATRON_OBJETOS_REFERIDOS.findall(limpia)
    if not referidos:
        raise DdlInseguro(
            f"la semilla no nombra ninguna tabla cualificada: {_recortar(limpia)}"
        )
    for objeto in referidos:
        _exigir_cualificado(objeto, esquema, limpia)


def _validar_create_schema(limpia: str, esquema: str) -> None:
    """`CREATE SCHEMA IF NOT EXISTS <esquema>`, y ningún otro esquema."""
    encontrada = re.match(
        r"^CREATE SCHEMA IF NOT EXISTS (\S+)$", limpia, flags=re.IGNORECASE
    )
    if encontrada is None:
        raise DdlInseguro(
            f"un CREATE SCHEMA tiene que ser 'CREATE SCHEMA IF NOT EXISTS "
            f"<esquema>' para poder aplicarse dos veces (R3): {_recortar(limpia)}"
        )
    creado = encontrada.group(1)
    if creado != esquema:
        raise DdlInseguro(
            f"la sentencia crea el esquema '{creado}' y el configurado es "
            f"'{esquema}' (R5): {_recortar(limpia)}"
        )


def _validar_create_table(limpia: str, esquema: str) -> None:
    """`CREATE TABLE IF NOT EXISTS <esquema>.<tabla> (…)`."""
    encontrada = re.match(
        r"^CREATE TABLE IF NOT EXISTS ([^\s(]+)", limpia, flags=re.IGNORECASE
    )
    if encontrada is None:
        raise DdlInseguro(
            f"un CREATE TABLE tiene que llevar IF NOT EXISTS para poder "
            f"aplicarse dos veces (R3): {_recortar(limpia)}"
        )
    _exigir_cualificado(encontrada.group(1), esquema, limpia)


def _validar_create_index(limpia: str, esquema: str) -> None:
    """`CREATE [UNIQUE] INDEX IF NOT EXISTS <nombre> ON <esquema>.<tabla> …`.

    Lo que se exige cualificado es la **tabla**, no el índice: el nombre de un
    índice no lleva esquema, lo hereda de su tabla.
    """
    encontrada = re.match(
        r"^CREATE (?:UNIQUE )?INDEX IF NOT EXISTS \S+ ON ([^\s(]+)",
        limpia,
        flags=re.IGNORECASE,
    )
    if encontrada is None:
        raise DdlInseguro(
            f"un CREATE INDEX tiene que ser 'CREATE [UNIQUE] INDEX IF NOT "
            f"EXISTS <nombre> ON <esquema>.<tabla> …' (R3, R5): "
            f"{_recortar(limpia)}"
        )
    _exigir_cualificado(encontrada.group(1), esquema, limpia)


def _validar_create_view(limpia: str, esquema: str) -> None:
    """`CREATE OR REPLACE VIEW <esquema>.<vista> AS …`."""
    encontrada = re.match(
        r"^CREATE OR REPLACE VIEW ([^\s(]+)", limpia, flags=re.IGNORECASE
    )
    if encontrada is None:
        raise DdlInseguro(
            f"una vista tiene que declararse como CREATE OR REPLACE VIEW para "
            f"poder aplicarse dos veces (R3): {_recortar(limpia)}"
        )
    _exigir_cualificado(encontrada.group(1), esquema, limpia)


def _validar_alter_table(limpia: str, esquema: str) -> None:
    """`ALTER TABLE <esquema>.<tabla> ADD COLUMN IF NOT EXISTS <col> …`.

    Es la **única** forma de `ALTER TABLE` que se admite, y no por gusto: en
    PostgreSQL un `ADD CONSTRAINT` no tiene `IF NOT EXISTS`, así que no es
    idempotente (R3). Las restricciones se declaran dentro del `CREATE TABLE`.
    """
    encontrada = re.match(
        r"^ALTER TABLE ([^\s]+) ADD COLUMN IF NOT EXISTS \S+",
        limpia,
        flags=re.IGNORECASE,
    )
    if encontrada is None:
        raise DdlInseguro(
            f"un ALTER TABLE solo puede ser 'ALTER TABLE <esquema>.<tabla> ADD "
            f"COLUMN IF NOT EXISTS <columna> …': lo demás no es idempotente "
            f"(R3): {_recortar(limpia)}"
        )
    _exigir_cualificado(encontrada.group(1), esquema, limpia)


def _exigir_cualificado(objeto: str, esquema: str, limpia: str) -> None:
    """R5 · el objeto tiene que empezar por `<esquema>.`."""
    if not objeto.lower().startswith(f"{esquema.lower()}."):
        raise DdlInseguro(
            f"el objeto '{objeto}' no está cualificado con el esquema propio "
            f"'{esquema}': una sentencia sin cualificar aterriza donde diga el "
            f"search_path (R5): {_recortar(limpia)}"
        )


def _recortar(sentencia: str) -> str:
    """La sentencia, recortada, para que el error se pueda leer."""
    plana = _ESPACIOS.sub(" ", sentencia).strip()
    if len(plana) <= _RECORTE:
        return plana
    return f"{plana[:_RECORTE]}…"


# --- Carga ------------------------------------------------------------------


def ficheros_ddl(directorio: Path) -> tuple[Path, ...]:
    """Los `NN_nombre.sql` del directorio, en orden lexicográfico (R1).

    Un `.sql` que no siga la convención **no se ignora en silencio**: se
    rechaza. Un fichero de DDL que nadie aplica es peor que uno que falla,
    porque el fallo se ve.
    """
    if not directorio.is_dir():
        raise DdlInseguro(f"no existe el directorio de DDL: {directorio}")

    encontrados = sorted(directorio.glob("*.sql"), key=lambda ruta: ruta.name)
    intrusos = [
        ruta.name for ruta in encontrados if not _PATRON_FICHERO.match(ruta.name)
    ]
    if intrusos:
        raise DdlInseguro(
            f"hay ficheros .sql que no siguen la convención NN_nombre.sql y "
            f"nadie los aplicaría: {', '.join(intrusos)}"
        )
    if not encontrados:
        raise DdlInseguro(f"el directorio de DDL no tiene ningún .sql: {directorio}")
    return tuple(encontrados)


def cargar_ddl(directorio: Path, *, esquema: str) -> tuple[str, ...]:
    """Todas las sentencias del DDL, al esquema pedido y ya validadas.

    Es la única puerta de entrada al DDL: sustituye el esquema literal por el
    configurado **en el mismo paso en que valida**, así que no hay ninguna
    ventana en la que exista una sentencia sustituida y no revisada.

    El error nombra el fichero y la sentencia culpable (R5): sin eso, el que
    lo lea tendría que buscar a mano en siete ficheros.
    """
    validar_nombre_de_esquema(esquema)

    cargadas: list[str] = []
    for fichero in ficheros_ddl(directorio):
        texto = _sustituir_esquema(fichero.read_text(encoding="utf-8"), esquema)
        for sentencia in sentencias(texto):
            try:
                validar(sentencia, esquema=esquema)
            except DdlInseguro as fallo:
                raise DdlInseguro(f"{fichero.name}: {fallo.motivo}") from fallo
            cargadas.append(sentencia)
    return tuple(cargadas)


def _sustituir_esquema(texto: str, esquema: str) -> str:
    """Cambia el esquema literal de los `.sql` por el configurado."""
    return re.sub(rf"\b{ESQUEMA_LITERAL}\b", esquema, texto)


def valores_check(nombres: Iterable[str]) -> str:
    """La lista de valores de un `CHECK`, a partir de un `Enum` del dominio.

    Sirve para que los tests comparen los `CHECK` del `.sql` con las etiquetas
    que de verdad emite el dominio (R20): una etiqueta nueva en F-004 que no
    llegue a la base tiene que romper la suite, no producción.
    """
    valores = list(nombres)
    if not valores:
        raise DdlInseguro("un CHECK sin valores no restringe nada")
    for valor in valores:
        if "'" in valor:
            raise DdlInseguro(
                f"el valor {valor!r} lleva una comilla y rompería el CHECK"
            )
    return ", ".join(f"'{valor}'" for valor in valores)
