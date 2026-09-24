# services/postventa-api/domain/ports/biblioteca.py
"""El puerto del explorador: ver y crear carpetas en la biblioteca (F-013).

Hasta F-013 el archivo no necesitaba **mirar** la biblioteca: la carpeta salía
del código de obra (`<base>/<cod obra>`) y `ArchivoPort.asegurar_carpeta` la
creaba a ciegas si faltaba. Con la estructura de Posventa
(`<obra>/PARTES INCIDENCIAS/<unidad>/PARTES FIRMADOS`) las carpetas de obra y
de unidad las crea Posventa a mano, con su grafía, y la carpeta **se
encuentra**, no se compone (`specs/F-013-archivo-posventa/design.md` §1). Para
encontrarla hay que listar; y para crear lo que falta sin partir su archivo en
dos, crear **un nivel cada vez**, dentro de un padre que existe.

## Dos métodos y ninguno más (R48)

Ni listar ficheros, ni mover, ni renombrar, ni borrar. No es minimalismo: es
lo que garantiza que los 142 partes sueltos de VILLA 04 —y cualquier otro
fichero que Posventa tenga en su biblioteca, sincronizada por OneDrive en sus
equipos— **no se tocan**. Un puerto que ofreciera esas operaciones invitaría a
usarlas, y lo que hay dentro de esos ficheros es un PDF con el DNI manuscrito
de un cliente. Deshacer una carpeta creada por error lo hace **una persona**
(R43).

## Por qué un puerto aparte y no dos métodos más de `ArchivoPort`

`ArchivoPort` (F-006) tiene tres operaciones y la fija
`test_f032_alcance_cerrado.py`; su doble, `BibliotecaFalsa`, y los
`isinstance` de F-006 contra un `Protocol` `runtime_checkable` se romperían al
ganar métodos. El adaptador de Graph implementará los dos puertos, y el borde
pasará la misma instancia por los dos lados (`design.md` §3.2).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = ["ExploradorBibliotecaPort"]


@runtime_checkable
class ExploradorBibliotecaPort(Protocol):
    """Quien sabe qué carpetas hay en la biblioteca y cómo crear una más."""

    def listar_carpetas(self, *, carpeta: str) -> tuple[str, ...] | None:
        """Los nombres de las **carpetas** hijas de `carpeta`, tal y como existen.

        Solo carpetas, nunca ficheros, y **todas las páginas** del proveedor
        (R12): una biblioteca con cientos de obras no puede resolver mal porque
        la obra buscada estuviera en la segunda página. `carpeta=""` es la raíz
        de la biblioteca.

        Devuelve `None` si la carpeta no existe, y una tupla vacía si existe
        y no tiene subcarpetas (aunque tenga ficheros: VILLA 04).

        Levanta `ArchivoFallido` si el proveedor no responde de forma
        utilizable. El mensaje no lleva ningún identificador de biblioteca ni
        de sitio (R23).
        """
        ...

    def crear_subcarpeta(self, *, padre: str, nombre: str) -> None:
        """Crea la carpeta `nombre` dentro de `padre`, **un nivel** (R15).

        `padre` **tiene que existir** (`padre=""` es la raíz): este método
        nunca crea intermedias, y un padre ausente es `ArchivoFallido`, no una
        carpeta nueva. Si `nombre` ya existe dentro de `padre` —otra petición
        la creó por medio—, es un **éxito** y queda **una** (R39).

        Levanta `ArchivoFallido` si el proveedor no responde de forma
        utilizable.
        """
        ...
