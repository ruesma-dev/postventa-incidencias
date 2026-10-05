# services/postventa-api/tests/utiles_importacion.py
"""Utilidades de los tests de la importación de F-036 (T17, T18).

Dobles **en memoria** de los puertos que usa la importación —bandeja,
decisiones de equivalencia y catálogo de Sigrid— y dos envoltorios que anotan
las llamadas del lector y del generador de verdad. Todos escriben en una lista
común de `llamadas`, y así un test puede fijar **el orden** de los pasos sin
mirar dentro de ellos.

La bandeja en memoria se porta como la base en lo que importa a la
aplicación: la clave de duplicado es única por obra entre las filas no
duplicadas (R41), un grupo cuya clave ya está entra entero `ya_en_bandeja`
(R38) y una importación **completa** queda como atajo para los mismos bytes
(R39); una parcial, no.

Sin red, sin base, sin IA y sin disco: los libros se generan y se leen en
memoria (R59). Las unidades, oficios y proveedores son los inventados de
`tests/utiles_plantilla.py`; la referencia de obra también es inventada.
"""

from __future__ import annotations

import itertools
from collections.abc import Collection, Mapping
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from domain.models.equivalencias import Catalogo, DecisionPar
from domain.models.importacion import (
    EstadoFilaImportada,
    EstadoImportacion,
    GrupoDeClave,
    IncidenciaEnBandeja,
    LibroLeido,
)
from domain.ports.bandeja import (
    FilaImportada,
    RegistroImportacion,
    ResultadoImportacion,
)
from domain.ports.catalogo_obra import (
    FilaOficioCatalogo,
    FilaUnidadCatalogo,
    LecturaCatalogo,
)
from domain.ports.hoja_calculo import FilaPlantilla
from infrastructure.documentos.excel_openpyxl import (
    GeneradorPlantillaOpenpyxl,
    LectorPlantillaOpenpyxl,
)

from tests.utiles_plantilla import FILAS_OBROFC, OFICIOS, UNIDADES, generar

#: Una referencia de obra (`upv.obride`) **inventada**.
OBRA_REF = "987654321"

#: El instante de las importaciones de prueba: 08:15 en UTC.
AHORA = datetime(2026, 9, 30, 8, 15, tzinfo=UTC)

#: Etiquetas de la plantilla de `utiles_plantilla.catalogo()`.
VILLA_1 = "Viviendas Bloque Villa 1"
VILLA_2 = "Viviendas Bloque Villa 2"


def fila(**valores: str | None) -> FilaPlantilla:
    """Una fila para escribir en la plantilla, con nombres de columna cortos."""
    columnas = {
        "unidad": "Unidad",
        "ubicacion": "Ubicación",
        "descripcion": "Descripción corta",
        "detalle": "Detalle",
        "oficio": "Oficio",
        "proveedor": "Proveedor",
        "urgencia": "Urgencia",
        "listado": "Listado",
    }
    return FilaPlantilla(valores={columnas[c]: v for c, v in valores.items()})


def fichero(*filas: FilaPlantilla, decisiones: tuple[DecisionPar, ...] = ()) -> bytes:
    """Los bytes de una plantilla de la 0677 con esas filas ya escritas."""
    return generar(filas=filas, decisiones=decisiones)


# --- el catálogo de Sigrid ----------------------------------------------------


def filas_de_unidades(obra_ref: str = OBRA_REF) -> tuple[FilaUnidadCatalogo, ...]:
    return tuple(
        FilaUnidadCatalogo(
            obra_ref=obra_ref,
            obra_codigo="0677",
            obra_nombre="Obra Ejemplo",
            unidad_codigo=u.codigo,
            unidad_nombre=u.nombre,
        )
        for u in UNIDADES
    )


def filas_de_oficios() -> tuple[FilaOficioCatalogo, ...]:
    nombres = {o.codigo: o.nombre for o in OFICIOS}
    return tuple(
        FilaOficioCatalogo(
            oficio_codigo=f.oficio_codigo,
            oficio_nombre=nombres[f.oficio_codigo],
            proveedor_codigo=f.proveedor_codigo,
            proveedor_nombre=f.proveedor_nombre,
        )
        for f in FILAS_OBROFC
    )


class CatalogoEnMemoria:
    """Un `CatalogoObraPort` de mentira con la 0677 inventada."""

    def __init__(
        self,
        llamadas: list[str],
        *,
        unidades: tuple[FilaUnidadCatalogo, ...] | None = None,
        oficios: tuple[FilaOficioCatalogo, ...] | None = None,
        fallo: Exception | None = None,
    ) -> None:
        self.llamadas = llamadas
        self._unidades = filas_de_unidades() if unidades is None else unidades
        self._oficios = filas_de_oficios() if oficios is None else oficios
        self._fallo = fallo
        self.codigos_pedidos: list[str] = []

    def leer_unidades(self, *, codigo_obra: str) -> LecturaCatalogo[FilaUnidadCatalogo]:
        self.llamadas.append("catalogo.leer_unidades")
        self.codigos_pedidos.append(codigo_obra)
        if self._fallo is not None:
            raise self._fallo
        return LecturaCatalogo(self._unidades, False)

    def leer_oficios(self, *, obra_ref: str) -> LecturaCatalogo[FilaOficioCatalogo]:
        self.llamadas.append("catalogo.leer_oficios")
        return LecturaCatalogo(self._oficios, False)


# --- las decisiones de equivalencia -------------------------------------------


class EquivalenciasEnMemoria:
    """Un `EquivalenciasPort` que devuelve las decisiones que se le den."""

    def __init__(
        self,
        llamadas: list[str],
        decisiones: tuple[DecisionPar, ...] = (),
        *,
        fallo: Exception | None = None,
    ) -> None:
        self.llamadas = llamadas
        self._decisiones = decisiones
        self._fallo = fallo
        self.pedidas: list[tuple[Catalogo, frozenset[str]]] = []

    def ultimas_decisiones(
        self, *, catalogo: Catalogo, codigos: Collection[str]
    ) -> tuple[DecisionPar, ...]:
        self.llamadas.append("equivalencias.ultimas_decisiones")
        self.pedidas.append((catalogo, frozenset(codigos)))
        if self._fallo is not None:
            raise self._fallo
        return tuple(
            d
            for d in self._decisiones
            if d.catalogo is catalogo and {d.codigo_a, d.codigo_b} <= set(codigos)
        )

    def registrar(self, *, decisiones: tuple[DecisionPar, ...]) -> None:
        raise AssertionError("la importación no registra decisiones")


# --- la bandeja ---------------------------------------------------------------


class BandejaEnMemoria:
    """Un `BandejaPort` que se porta como la base en lo que ve la aplicación."""

    def __init__(
        self,
        llamadas: list[str],
        *,
        fallo_al_registrar: Exception | None = None,
        fallo_al_buscar: Exception | None = None,
        fallo_al_listar: Exception | None = None,
        incidencias: tuple[IncidenciaEnBandeja, ...] = (),
    ) -> None:
        self.llamadas = llamadas
        self._fallo_al_listar = fallo_al_listar
        self.incidencias = incidencias
        self.listados_pedidos: list[tuple[str, int]] = []
        self._fallo_al_registrar = fallo_al_registrar
        self._fallo_al_buscar = fallo_al_buscar
        self.claves: dict[tuple[str, str], UUID] = {}
        self.completas: dict[str, ResultadoImportacion] = {}
        self.registradas: list[
            tuple[RegistroImportacion, tuple[GrupoDeClave, ...]]
        ] = []
        self.hashes_pedidos: list[str] = []
        self._ids = (UUID(int=0x1000 + n) for n in itertools.count())

    def importacion_completa_por_hash(
        self, *, hash_fichero: str
    ) -> ResultadoImportacion | None:
        self.llamadas.append("bandeja.importacion_completa_por_hash")
        self.hashes_pedidos.append(hash_fichero)
        if self._fallo_al_buscar is not None:
            raise self._fallo_al_buscar
        return self.completas.get(hash_fichero)

    def registrar(
        self, *, importacion: RegistroImportacion, grupos: tuple[GrupoDeClave, ...]
    ) -> ResultadoImportacion:
        self.llamadas.append("bandeja.registrar")
        if self._fallo_al_registrar is not None:
            raise self._fallo_al_registrar
        self.registradas.append((importacion, grupos))
        filas: list[FilaImportada] = []
        nuevas = duplicadas = ya = 0
        for grupo in grupos:
            existente = self.claves.get((importacion.obra_codigo, grupo.clave))
            if existente is not None:
                filas.extend(
                    FilaImportada(
                        v.fila, EstadoFilaImportada.YA_EN_BANDEJA, None, None, existente
                    )
                    for v in grupo.filas
                )
                ya += len(grupo.filas)
                continue
            primera = next(self._ids)
            self.claves[(importacion.obra_codigo, grupo.clave)] = primera
            nuevas += 1
            filas.append(
                FilaImportada(
                    grupo.filas[0].fila, EstadoFilaImportada.NUEVA, primera, None, None
                )
            )
            for valida in grupo.filas[1:]:
                duplicadas += 1
                filas.append(
                    FilaImportada(
                        valida.fila,
                        EstadoFilaImportada.DUPLICADA_EN_FICHERO,
                        next(self._ids),
                        grupo.filas[0].fila,
                        None,
                    )
                )
        resultado = ResultadoImportacion(
            importacion=importacion,
            ya_importado=False,
            estado=importacion.estado,
            nuevas=nuevas,
            duplicadas_en_fichero=duplicadas,
            ya_en_bandeja=ya,
            con_error=importacion.filas_con_error,
            filas=tuple(sorted(filas, key=lambda f: f.fila)),
        )
        if importacion.estado is EstadoImportacion.COMPLETA:
            self.completas.setdefault(
                importacion.hash_fichero,
                replace(resultado, ya_importado=True, filas=()),
            )
        return resultado

    def listar(
        self, *, obra_codigo: str, limite: int
    ) -> tuple[IncidenciaEnBandeja, ...]:
        """Las incidencias preparadas, tal cual: la obra se anota y no se mira."""
        self.llamadas.append("bandeja.listar")
        self.listados_pedidos.append((obra_codigo, limite))
        if self._fallo_al_listar is not None:
            raise self._fallo_al_listar
        return self.incidencias


# --- el lector y el generador de verdad, anotando -----------------------------


class LectorQueAnota:
    """El lector de verdad, o un libro preparado, anotando cada lectura."""

    def __init__(self, llamadas: list[str], libro: LibroLeido | None = None) -> None:
        self.llamadas = llamadas
        self._libro = libro
        self._real = LectorPlantillaOpenpyxl()

    def leer(self, *, contenido: bytes) -> LibroLeido:
        self.llamadas.append("lector.leer")
        if self._libro is not None:
            return self._libro
        return self._real.leer(contenido=contenido)


class GeneradorQueAnota:
    """El generador de verdad, anotando cada llamada y sus argumentos."""

    def __init__(self, llamadas: list[str]) -> None:
        self.llamadas = llamadas
        self.argumentos: list[Mapping[str, object]] = []
        self._real = GeneradorPlantillaOpenpyxl()

    def generar(self, **argumentos: object) -> bytes:
        self.llamadas.append("generador.generar")
        self.argumentos.append(argumentos)
        return self._real.generar(**argumentos)  # type: ignore[arg-type]
