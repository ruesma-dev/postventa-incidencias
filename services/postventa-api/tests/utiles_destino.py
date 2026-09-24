# services/postventa-api/tests/utiles_destino.py
"""Dobles y datos de prueba del destino en la biblioteca de Posventa (F-013).

Como `tests/utiles_sharepoint.py` para F-006: aquí vive lo que los tests de
F-013 necesitan construir, y por eso ninguno abre red, ninguno lista la
biblioteca real y **ninguno lee Sigrid**.

## Los dobles anotan cada llamada

En esta feature **el orden es el requisito**: la reclamación y su obra se
validan antes de listar nada (R8, R44), bajo un nivel que se va a crear no se
lista (el padre es nuevo), el resolutor no escribe, y el paso crea **después**
de la traza previa. Nada de eso se puede afirmar mirando el resultado: hay que
mirar **qué se pidió y en qué orden**. Por eso los dos dobles apuntan cada
llamada en su propia lista (`llamadas`) y, si se les da, en un `registro`
**compartido** con los demás dobles del test —el mismo patrón que
`ArchivoPortFalso` y `RepositorioFalso` usan en F-019—.

## `ExploradorFalso` no es un mock: es una biblioteca de carpetas de mentira

Se comporta como Graph en lo que importa: lista **solo carpetas** (los ficheros
sueltos existen, pero no se ven: VILLA 04), devuelve `None` para una carpeta
que no existe, crea **un nivel** dentro de un padre que existe, trata «ya
existe» como éxito y **nunca** crea intermedias —un padre ausente es
`ArchivoFallido`—. Así, «lo creado casa consigo mismo» (R39) se comprueba
creando de verdad en el doble y volviendo a resolver.

## El árbol medido de la 0677

Es el de T2 y T3 (`progress/explore_F-013.md`, 2026-09-24): la carpeta de obra
`677  MIRASIERRA` —sin el cero y con **dos** blancos—, su `PARTES INCIDENCIAS`,
`VILLA 01` … `VILLA 07` con sus hojas (VILLA 02 con `PARTES FIRMADO`, VILLA 04
sin subcarpetas y con 142 ficheros sueltos) y las 15 unidades de Sigrid. **Sin
nombres de persona**: T3 midió que no los hay. Las demás carpetas de la raíz y
de la obra existen en la biblioteca real, pero sus nombres aquí son
**inventados** y neutros: lo único que importa de ellas es que no llevan el
número de la obra ni la palabra de ningún tramo. Tienen que coincidir con las
de `test_f013_destino_dominio.py` (T6), y un test lo vigila.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from domain.models.destino_posventa import UbicacionReclamacion, UnidadDeObra
from domain.models.errores import ArchivoFallido

__all__ = [
    "ALTERNATIVA",
    "CARPETA_OBRA_0677",
    "DENTRO_DE_LA_OBRA_0677",
    "FICHEROS_SUELTOS_VILLA_04",
    "FIRMADOS",
    "HOJAS_0677",
    "INCIDENCIAS",
    "RAIZ_0677",
    "RES_OBRA_0677",
    "UNIDADES_0677",
    "UNIDADES_EN_POSVENTA_0677",
    "ExploradorFalso",
    "UbicacionesFalsas",
    "explorador_0677",
    "reclamacion_0677",
    "ubicacion_0677",
    "ubicaciones_0677",
]

# --------------------------------------------------------------------------
# Los tramos fijos, con sus valores por omisión (R1, R49)
# --------------------------------------------------------------------------

INCIDENCIAS = "PARTES INCIDENCIAS"
FIRMADOS = "PARTES FIRMADOS"
ALTERNATIVA = "PARTES FIRMADO"

# --------------------------------------------------------------------------
# El árbol medido de la 0677 (T2)
# --------------------------------------------------------------------------

#: El `con.res` de la obra 0677 en Sigrid [MEDIDO, `design.md` §1].
RES_OBRA_0677 = "15 VIVIENDAS UNIFAMILIARES EN MIRASIERRA(MADRID)"

#: La carpeta real de la obra: sin el cero y con **dos** blancos [MEDIDO, T2].
CARPETA_OBRA_0677 = "677  MIRASIERRA"

#: La raíz de la biblioteca: la carpeta real de la obra y otras inventadas que
#: no llevan el 677 (T2: «ninguna otra carpeta de la raíz casa ni se parece»).
RAIZ_0677 = (
    "0680 OTRA OBRA",
    "0712 PROMOCION NORTE",
    CARPETA_OBRA_0677,
    "ADMINISTRACION",
    "PLANTILLAS",
    "0590 RESIDENCIAL SUR",
)

#: Dentro de la obra: `PARTES INCIDENCIAS` y tres de trabajo interno (T2), con
#: nombres inventados que no llevan la palabra del tramo.
DENTRO_DE_LA_OBRA_0677 = (
    "DOCUMENTACION",
    INCIDENCIAS,
    "PLANOS",
    "CORRESPONDENCIA",
)

#: Las siete unidades que tiene Posventa, siempre con dos cifras [MEDIDO, T2].
UNIDADES_EN_POSVENTA_0677 = tuple(f"VILLA {n:02d}" for n in range(1, 8))

#: Las hojas de cada unidad [MEDIDO, T2; el literal de VILLA 02, humano].
HOJAS_0677 = {
    "VILLA 01": (FIRMADOS,),
    "VILLA 02": (ALTERNATIVA,),
    "VILLA 03": (FIRMADOS,),
    "VILLA 04": (),  # sin subcarpetas: 142 ficheros sueltos que no se ven
    "VILLA 05": (FIRMADOS,),
    "VILLA 06": (FIRMADOS,),
    "VILLA 07": (FIRMADOS,),
}

#: Los partes que Posventa guarda sueltos en VILLA 04 [MEDIDO, T2]. R48: no
#: se listan por su nombre, no se mueven, no se renombran.
FICHEROS_SUELTOS_VILLA_04 = 142

#: Las 15 unidades de posventa de la 0677 en Sigrid [MEDIDO, T3]. Una sola
#: obra; `obra-a` es una referencia **de mentira** (la real es un `ide` del
#: ERP y no entra en el repositorio).
UNIDADES_0677 = tuple(
    UnidadDeObra(
        obra_ref="obra-a",
        obra_codigo="0677",
        unidad_codigo=f"0677.03VILLA {n}.",
        unidad_nombre=f"Viviendas Bloque Villa {n}",
    )
    for n in range(1, 16)
)


def _unir(padre: str, nombre: str) -> str:
    """La ruta de una hija, como la compone el resolutor (base vacía = raíz)."""
    return f"{padre}/{nombre}" if padre else nombre


def _arbol_0677() -> dict[str, tuple[str, ...]]:
    obra = CARPETA_OBRA_0677
    incidencias = _unir(obra, INCIDENCIAS)
    arbol: dict[str, tuple[str, ...]] = {
        "": RAIZ_0677,
        obra: DENTRO_DE_LA_OBRA_0677,
        incidencias: UNIDADES_EN_POSVENTA_0677,
    }
    for villa, hojas in HOJAS_0677.items():
        arbol[_unir(incidencias, villa)] = hojas
    return arbol


def _ficheros_0677() -> dict[str, int]:
    """Los ficheros sueltos medidos en T2, contados y nunca nombrados."""
    incidencias = _unir(CARPETA_OBRA_0677, INCIDENCIAS)
    return {
        "": 7,
        CARPETA_OBRA_0677: 2,
        _unir(incidencias, "VILLA 04"): FICHEROS_SUELTOS_VILLA_04,
        _unir(_unir(incidencias, "VILLA 03"), FIRMADOS): 4,
        _unir(_unir(incidencias, "VILLA 05"), FIRMADOS): 2,
        _unir(_unir(incidencias, "VILLA 06"), FIRMADOS): 2,
        _unir(_unir(incidencias, "VILLA 07"), FIRMADOS): 3,
    }


# --------------------------------------------------------------------------
# ExploradorFalso
# --------------------------------------------------------------------------


class ExploradorFalso:
    """Un `ExploradorBibliotecaPort` sobre un árbol de carpetas en memoria.

    `arbol` es `ruta -> carpetas hijas`, con `""` para la raíz; las hijas que
    no aparecen como clave existen y están vacías. Una ruta que no es de nadie
    **no existe**. `ficheros` cuenta los ficheros sueltos de cada carpeta: el
    explorador no los ve ni los toca (R48), pero siguen ahí para poder afirmar
    que siguen.

    Tres listas para afirmar sobre lo que pasó:

    - `llamadas`: cada llamada con sus argumentos, en orden (listar y crear);
    - `creaciones`: cada `(padre, nombre)` que se **pidió** crear;
    - `carpetas_nuevas`: las rutas que **aparecieron** (una creación de algo
      que ya existía no aparece: es el `409` que cuenta como éxito, R39).

    `fallo_al_listar` y `fallo_al_crear` inyectan el error del proveedor sin
    tocar el árbol; la llamada queda anotada igual.
    """

    def __init__(
        self,
        arbol: Mapping[str, Iterable[str]] | None = None,
        *,
        ficheros: Mapping[str, int] | None = None,
        registro: list[str] | None = None,
        fallo_al_listar: Exception | None = None,
        fallo_al_crear: Exception | None = None,
    ) -> None:
        self._hijas: dict[str, list[str]] = {}
        for ruta, hijas in (arbol if arbol is not None else {"": ()}).items():
            self._hijas.setdefault(ruta, [])
            for hija in hijas:
                self._anadir(ruta, hija)
        self._ficheros: dict[str, int] = dict(ficheros or {})
        self.registro = registro if registro is not None else []
        self.fallo_al_listar = fallo_al_listar
        self.fallo_al_crear = fallo_al_crear
        self.llamadas: list[tuple[str, dict[str, Any]]] = []
        self.creaciones: list[tuple[str, str]] = []
        self.carpetas_nuevas: list[str] = []

    # ----------------------------------------------------------- el puerto
    def listar_carpetas(self, *, carpeta: str) -> tuple[str, ...] | None:
        self.llamadas.append(("listar_carpetas", {"carpeta": carpeta}))
        self.registro.append(f"explorador.listar_carpetas:{carpeta}")
        if self.fallo_al_listar is not None:
            raise self.fallo_al_listar
        hijas = self._hijas.get(carpeta)
        return None if hijas is None else tuple(hijas)

    def crear_subcarpeta(self, *, padre: str, nombre: str) -> None:
        self.llamadas.append(("crear_subcarpeta", {"padre": padre, "nombre": nombre}))
        self.registro.append(f"explorador.crear_subcarpeta:{padre}|{nombre}")
        self.creaciones.append((padre, nombre))
        if self.fallo_al_crear is not None:
            raise self.fallo_al_crear
        if padre not in self._hijas:
            # Como Graph: un `404` del padre, y nunca una intermedia.
            raise ArchivoFallido(
                f"la carpeta padre «{padre}» no existe: no se crea «{nombre}» "
                "ni ninguna intermedia"
            )
        if nombre in self._hijas[padre]:
            return  # el `409` de `conflictBehavior=fail`: ya existe, es éxito
        self._anadir(padre, nombre)
        self.carpetas_nuevas.append(_unir(padre, nombre))

    # -------------------------------------------------------------- ayudas
    @property
    def listados(self) -> list[str]:
        """Las carpetas listadas, en orden."""
        return [args["carpeta"] for nombre, args in self.llamadas if nombre == "listar_carpetas"]

    def ficheros_en(self, carpeta: str) -> int:
        """Cuántos ficheros sueltos hay en la carpeta (el explorador no los ve)."""
        return self._ficheros.get(carpeta, 0)

    def _anadir(self, padre: str, nombre: str) -> None:
        if nombre not in self._hijas[padre]:
            self._hijas[padre].append(nombre)
        self._hijas.setdefault(_unir(padre, nombre), [])


# --------------------------------------------------------------------------
# UbicacionesFalsas
# --------------------------------------------------------------------------


class UbicacionesFalsas:
    """Un `UbicacionPort` en memoria con las dos lecturas de Sigrid (§3.3).

    `ubicaciones` es `código de la reclamación (forma ERP) -> filas`; un código
    que no está devuelve cero filas. `unidades` es lo que devuelve la segunda
    lectura **tal cual**, sin filtrar por número: así un test puede dar filas
    que el SQL preseleccionaría de más (`1677`) y comprobar que el dominio las
    quita.

    Anota cada llamada en `llamadas` y en el `registro` compartido.
    `fallo_al_ubicar` y `fallo_al_leer_unidades` hacen fallar **cada lectura
    por su cuenta**, como la red (R41).
    """

    def __init__(
        self,
        ubicaciones: Mapping[str, Iterable[UbicacionReclamacion]] | None = None,
        *,
        unidades: Iterable[UnidadDeObra] = (),
        registro: list[str] | None = None,
        fallo_al_ubicar: Exception | None = None,
        fallo_al_leer_unidades: Exception | None = None,
    ) -> None:
        self._ubicaciones = {
            codigo: tuple(filas) for codigo, filas in (ubicaciones or {}).items()
        }
        self._unidades = tuple(unidades)
        self.registro = registro if registro is not None else []
        self.fallo_al_ubicar = fallo_al_ubicar
        self.fallo_al_leer_unidades = fallo_al_leer_unidades
        self.llamadas: list[tuple[str, dict[str, Any]]] = []

    def leer_ubicacion(
        self, *, codigo_reclamacion: str
    ) -> tuple[UbicacionReclamacion, ...]:
        self.llamadas.append(
            ("leer_ubicacion", {"codigo_reclamacion": codigo_reclamacion})
        )
        self.registro.append(f"ubicaciones.leer_ubicacion:{codigo_reclamacion}")
        if self.fallo_al_ubicar is not None:
            raise self.fallo_al_ubicar
        return self._ubicaciones.get(codigo_reclamacion, ())

    def leer_unidades_del_numero(
        self, *, codigo_obra: str
    ) -> tuple[UnidadDeObra, ...]:
        self.llamadas.append(("leer_unidades_del_numero", {"codigo_obra": codigo_obra}))
        self.registro.append(f"ubicaciones.leer_unidades_del_numero:{codigo_obra}")
        if self.fallo_al_leer_unidades is not None:
            raise self.fallo_al_leer_unidades
        return self._unidades


# --------------------------------------------------------------------------
# La 0677, montada
# --------------------------------------------------------------------------


def explorador_0677(**opciones: Any) -> ExploradorFalso:
    """Un explorador **nuevo** con el árbol medido de la 0677 (T2)."""
    return ExploradorFalso(_arbol_0677(), ficheros=_ficheros_0677(), **opciones)


def ubicacion_0677(n: int) -> UbicacionReclamacion:
    """La fila de la primera lectura para una reclamación de la villa `n` (T3)."""
    return UbicacionReclamacion(
        obra_codigo="0677",
        obra_nombre=RES_OBRA_0677,
        unidad_codigo=f"0677.03VILLA {n}.",
        unidad_nombre=f"Viviendas Bloque Villa {n}",
    )


def reclamacion_0677(n: int) -> str:
    """El código (forma ERP) de la reclamación de prueba de la villa `n`."""
    return f"RS26.08/{n:04d}"


def ubicaciones_0677(**opciones: Any) -> UbicacionesFalsas:
    """Sigrid para la 0677: una reclamación por villa y las 15 unidades (T3)."""
    return UbicacionesFalsas(
        {reclamacion_0677(n): (ubicacion_0677(n),) for n in range(1, 16)},
        unidades=UNIDADES_0677,
        **opciones,
    )
