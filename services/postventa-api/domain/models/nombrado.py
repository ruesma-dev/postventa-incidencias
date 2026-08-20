# services/postventa-api/domain/models/nombrado.py
"""Cómo se llama el fichero de un parte y en qué carpeta va (F-006, paso 5).

**Dominio puro**: sin reloj, sin azar, sin red y sin configuración. Dos
cadenas entran —el código de obra y el nº de incidencia— y sale el nombre del
fichero. Mismas entradas, mismo nombre, hoy y dentro de un año. Eso es lo que
permite volver a nombrar un parte cuando una persona corrija un campo (F-007)
y obtener **exactamente** el mismo fichero en vez de un segundo casi igual.

La carpeta base sí es configuración, pero entra como **argumento**: el dominio
no la lee de ningún sitio. Es lo que hace que F-013 —mudar el archivo a la
biblioteca de Posventa— sea cambiar variables de entorno y no reescribir esto.

## Tres cosas distintas que es fácil confundir

`docs/ARCHITECTURE.md` (semánticas 2 y 5) las separa, y confundirlas estropea
a la vez el nombre y la carpeta. Los ejemplos son **inventados**:

| Dato | Ejemplo | De dónde sale | Para qué sirve aquí |
|---|---|---|---|
| Código de obra | `0677` | campo propio del papel | **la carpeta** y el primer tramo del nombre |
| Código de incidencia | `RS26.08/0123` | lo emite Sigrid **entero** | el segundo tramo del nombre |
| Nombre del fichero | `0677 - RS26.08 - 0123 PARTE FIRMADO.pdf` | se compone aquí | lo que ve Posventa |

El código de incidencia **no es** «obra + número»: es otra cosa. Y se escribe
con **barra** en Sigrid y en el papel, pero con **guion** en el nombre del
fichero: la barra es un separador de ruta y partiría el fichero en dos
carpetas.

## Las tres reglas que este módulo no negocia

1. **Los ceros a la izquierda se conservan.** `int("0677")` es un bug, no una
   normalización: `677` es otra obra y el parte acabaría archivado en la
   promoción de otro. Aquí se trabaja con `str` de punta a punta.
2. **El sufijo va literal.** ` PARTE FIRMADO` en mayúsculas es lo que ya usa
   Posventa y lo que distingue el parte conformado de cualquier otro
   documento de la misma incidencia.
3. **Un nombre imposible es un error, nunca un saneo silencioso.** Sustituir
   el carácter raro por `_` archivaría en Posventa un fichero con un nombre
   que nadie pidió, en un archivo que se consulta a mano, y nadie se
   enteraría. Un error ruidoso es mejor que un archivo sucio.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.models.errores import NombradoImposible

__all__ = [
    "CARACTERES_PROHIBIDOS",
    "EXTENSION",
    "GUIONES_EQUIVALENTES",
    "SEPARADOR",
    "SUFIJO",
    "DestinoArchivo",
    "carpeta_de_archivo",
    "componer_destino",
    "nombre_admisible",
    "nombre_de_archivo",
    "normalizar_codigo",
]

#: Espacio, guion **normal** (`U+002D`) y espacio. El guion es el normal a
#: propósito: un guion largo aquí es invisible al ojo y muy visible en la
#: carpeta de Posventa el día que alguien busque el fichero.
SEPARADOR = " - "

#: Lo que Posventa ya escribe en sus partes conformados. Literal.
SUFIJO = " PARTE FIRMADO"

#: La extensión, en minúsculas.
EXTENSION = ".pdf"

#: Todo lo que en el mundo real hace de guion y **no** es `U+002D`.
#:
#: Salen de los escaneos, de los correos y de Word, que sustituye guiones por
#: rayas sin avisar. Dos lecturas del mismo parte que solo difieran en esto
#: tienen que producir el mismo nombre, o el archivo acaba con dos ficheros
#: que a ojo son idénticos.
#:
#: `U+002D` **no** está en la lista: es el destino, no el origen.
GUIONES_EQUIVALENTES = "‐‑‒–—―−"

#: Lo que SharePoint (y Windows) no admiten en un nombre de fichero.
CARACTERES_PROHIBIDOS = '"*:<>?/\\|'

#: La traducción de todos los guiones raros al normal, de una pasada.
_A_GUION_NORMAL = str.maketrans({guion: "-" for guion in GUIONES_EQUIVALENTES})


def normalizar_codigo(bruto: str | None) -> str:
    """Guiones al normal, espacios colapsados y extremos recortados.

    **No toca los ceros a la izquierda** y **no convierte a número**: lo que
    entra como `str` sale como `str`, y `0677` sigue siendo `0677`.

    Un código ausente, vacío o de solo espacios sale como cadena vacía. No se
    levanta nada aquí: quien decide que eso es un error es quien va a nombrar
    el fichero, y este mismo saneo lo usa también la carpeta.
    """
    if bruto is None:
        return ""
    return " ".join(bruto.translate(_A_GUION_NORMAL).split())


def nombre_admisible(nombre: str) -> bool:
    """¿Se puede archivar un fichero con ese nombre?

    Tres motivos para decir que no, y los tres dejan el mismo rastro en
    SharePoint —un fichero que no está donde se le busca—:

    - lleva alguno de los caracteres que el servicio no admite;
    - empieza o acaba en espacio, que SharePoint recorta por su cuenta;
    - acaba en punto, que SharePoint también recorta por su cuenta.

    Es una función pública y no una comprobación escondida dentro de
    `nombre_de_archivo` **a propósito**: desde allí las dos últimas ramas son
    inalcanzables —los códigos ya vienen recortados y el nombre siempre acaba
    en `.pdf`—, y una guardia que nadie puede ejercitar es una guardia que
    nadie sabe si funciona. Aquí se prueba directamente, caso a caso.
    """
    if not nombre:
        return False
    if any(caracter in CARACTERES_PROHIBIDOS for caracter in nombre):
        return False
    if nombre != nombre.strip():
        return False
    return not nombre.endswith(".")


def nombre_de_archivo(
    *, codigo_obra: str | None, numero_incidencia: str | None
) -> str:
    """`<obra> - <incidencia> PARTE FIRMADO.pdf`, con la incidencia sin barras.

    Los cinco pasos, **en este orden**, y el orden importa:

    1. Se normalizan los dos códigos. Vacío → `NombradoImposible` diciendo
       **cuál** falta: «faltan datos» obliga a mirar el papel entero.
    2. En la incidencia, la barra pasa a ` - `. Se hace **después** de
       normalizar los guiones para que `RS26.08 – 0123` (guion largo) y
       `RS26.08/0123` acaben en el mismo sitio: son el mismo parte leído dos
       veces.
    3. Se vuelven a colapsar los espacios de la incidencia: una barra rodeada
       de espacios (`RS26.08 / 0123`) dejaría espacios dobles.
    4. Se compone.
    5. Se **comprueba**, no se sanea (R7).

    Los parámetros son de solo palabra clave para que nadie pueda invertir
    obra e incidencia en la llamada y archivar el parte con el nombre del
    revés, que es un fallo que ningún test de tipos ve.
    """
    obra = normalizar_codigo(codigo_obra)
    if not obra:
        raise NombradoImposible(
            "falta el código de obra del parte: sin él no se puede componer "
            "el nombre del fichero ni saber en qué carpeta va"
        )

    incidencia = normalizar_codigo(numero_incidencia)
    if not incidencia:
        raise NombradoImposible(
            "falta el nº de incidencia del parte: sin él no se puede componer "
            "el nombre del fichero"
        )

    incidencia = " ".join(incidencia.replace("/", SEPARADOR).split())
    nombre = f"{obra}{SEPARADOR}{incidencia}{SUFIJO}{EXTENSION}"

    if not nombre_admisible(nombre):
        raise NombradoImposible(
            f"el nombre compuesto no vale para SharePoint: «{nombre}». No se "
            f"corrige por nuestra cuenta: el parte va a revisión manual"
        )
    return nombre


def carpeta_de_archivo(*, carpeta_base: str, codigo_obra: str | None) -> str:
    """`<base>/<obra>`, con los ceros de la obra intactos.

    La base llega de configuración y se recorta por los extremos: `Postventa/`
    y `Postventa` son la misma carpeta, pero la primera produciría
    `Postventa//0677`, que para Graph es otra ruta distinta.

    Sin código de obra no hay carpeta: `<base>/` a secas sería la biblioteca
    entera, y ahí el parte no lo encuentra nadie.
    """
    obra = normalizar_codigo(codigo_obra)
    if not obra:
        raise NombradoImposible(
            "falta el código de obra del parte: sin él no se sabe en qué "
            "carpeta se archiva"
        )
    return f"{carpeta_base.strip().strip('/')}/{obra}"


@dataclass(frozen=True)
class DestinoArchivo:
    """Dónde va el parte y cómo se llama, en una sola pieza.

    Inmutable a propósito: entre componerlo y subir el fichero hay varias
    llamadas al proveedor, y si alguien pudiera reescribir el nombre por el
    camino la comprobación de R7 no estaría protegiendo nada.
    """

    carpeta: str
    nombre_fichero: str

    @property
    def ruta_relativa(self) -> str:
        """La ruta dentro de la biblioteca, para logs y para la traza."""
        return f"{self.carpeta}/{self.nombre_fichero}"


def componer_destino(
    *, carpeta_base: str, codigo_obra: str | None, numero_incidencia: str | None
) -> DestinoArchivo:
    """La carpeta y el nombre de un parte, de una vez.

    Es lo que consume el paso de archivo: componer las dos cosas por separado
    invita a que un día se compruebe una y no la otra.
    """
    return DestinoArchivo(
        carpeta=carpeta_de_archivo(
            carpeta_base=carpeta_base, codigo_obra=codigo_obra
        ),
        nombre_fichero=nombre_de_archivo(
            codigo_obra=codigo_obra, numero_incidencia=numero_incidencia
        ),
    )
