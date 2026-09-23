# services/postventa-api/tests/test_f034_sin_consultas_de_mas.py
"""La situación no cuesta ninguna sentencia más (F-034 R38, con R2 y R10).

F-034 cambia **de dónde salen** tres datos con los que `POST /api/adjuntar` y
`POST /api/cerrar` escriben en el ERP —el estado del archivo y los dos
códigos— y los toma de la `SituacionParte` que la puerta de aptitud **ya
leía** antes de la feature. El argumento de coste de toda la ficha es ese:
cero columnas, cero sentencias, cero métodos del puerto (`design.md` §1.1).
Este fichero lo convierte en un número.

## Cómo se cuenta

`RepositorioQueCuenta` envuelve el doble de siempre (`RepositorioEnMemoria`) y
apunta **cada** llamada a un método público del puerto, en orden y con su
nombre. No solo `consultar_situacion` y `consultar_grafico`, que son las dos
lecturas que pide `tasks.md` T12: también las escrituras y cualquier otra
lectura, porque «ninguna sentencia más» incluye una consulta de estado de
cierre o una segunda escritura de traza que nadie esperaba. Cada llamada al
puerto es, en el adaptador de verdad, una sentencia contra el PostgreSQL
**compartido** con albaranes.

Se recorre el **handler** de cada endpoint (`adjuntar_grafico`,
`cerrar_incidencia`) con los puertos inyectados, no solo el paso: el borde
también podría preguntar algo, y lo que se promete es por petición.

## De dónde salen los números esperados

**Medidos antes de la feature**, no deducidos: este mismo fichero, sin cambiar
una línea, se ejecutó contra `dev` (commit `e2e5d7a`, la base de la rama) con
`tests/utiles_circuito.py` copiado al lado, y los cinco casos positivos dieron
los mismos números que aquí se escriben a mano (y el control del contador,
verde también). La traza de esa ejecución está en
`progress/impl_F-034.md` (Bloque 5, T12). Los dos handlers tienen la misma
firma antes y después de F-034, y el mundo de los casos positivos es uno en el
que los dos códigos del cuerpo y los guardados coinciden y la traza de
archivo guardada dice `archivado`: el mundo en el que el código de antes y el
de ahora hacen lo mismo.

Los casos **negativos** —un 409 del cotejo o de la puerta de archivo— no
tienen equivalente en `dev`: allí esos cuerpos llegaban al ERP, y en esa
misma ejecución los cuatro dieron `DID NOT RAISE`. Lo que se exige de ellos es
más fuerte: **una sola** llamada, la de la situación, y nada más.

Y el control al revés, también medido: una copia del árbol con una
`consultar_situacion` de más al principio de cada paso pone en rojo nueve de
los diez casos (todos menos el control del contador).

**Sin red, sin base de datos, sin IA y sin tocar el ERP** (R37).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Any

import pytest
from domain.models.errores import CodigosNoCoinciden, ParteNoArchivado
from domain.models.persistencia import EstadoArchivo, EstadoGrafico, TrazaGrafico
from domain.ports.persistencia import RepositorioPartesPort

from tests.utiles_circuito import (
    AHORA,
    MundoDelAdjuntar,
    MundoDelCierre,
    cuerpo_de_cierre,
    formulario,
    situacion_guardada,
)

HASH = "f034c0c0c0c0"
OBRA = "0626"
INCIDENCIA = "RS26.08/0123"


class RepositorioQueCuenta:
    """Un `RepositorioPartesPort` que apunta cada llamada y delega en otro.

    No reimplementa nada: lo que responde lo decide el doble de dentro, que es
    el mismo con el que corren los demás tests de F-034. Así el recuento no
    puede salir distinto porque este doble conteste otra cosa.
    """

    def __init__(self, dentro: Any) -> None:
        self._dentro = dentro
        #: Los métodos del puerto que se han llamado, en orden.
        self.llamadas: list[str] = []

    def __getattr__(self, nombre: str) -> Any:
        atributo = getattr(self._dentro, nombre)
        if nombre.startswith("_") or not callable(atributo):
            return atributo

        def contado(*args: Any, **kwargs: Any) -> Any:
            self.llamadas.append(nombre)
            return atributo(*args, **kwargs)

        return contado

    def veces(self, nombre: str) -> int:
        """Cuántas veces se ha llamado a ese método del puerto."""
        return Counter(self.llamadas)[nombre]


def _contando(mundo: Any) -> RepositorioQueCuenta:
    """Pone el contador delante del repositorio del mundo y lo devuelve.

    Los dos mundos leen `self.repositorio` en el momento de llamar al handler,
    así que basta con sustituirlo antes.
    """
    contador = RepositorioQueCuenta(mundo.repositorio)
    mundo.repositorio = contador
    return contador


def _mundo_del_adjuntar(
    *, estado_archivo: EstadoArchivo | None = EstadoArchivo.ARCHIVADO
) -> MundoDelAdjuntar:
    return MundoDelAdjuntar(
        situacion_guardada(
            hash_parte=HASH,
            codigo_obra=OBRA,
            numero_incidencia=INCIDENCIA,
            estado_archivo=estado_archivo,
        )
    )


def _mundo_del_cierre(
    *, estado_archivo: EstadoArchivo | None = EstadoArchivo.ARCHIVADO
) -> MundoDelCierre:
    return MundoDelCierre(
        situacion_guardada(
            hash_parte=HASH,
            codigo_obra=OBRA,
            numero_incidencia=INCIDENCIA,
            estado_archivo=estado_archivo,
        )
    )


def _cuerpo_del_adjuntar(
    *, numero_incidencia: str = INCIDENCIA, **cambios: str
) -> dict[str, str]:
    return formulario(
        hash_parte=HASH,
        codigo_obra=OBRA,
        numero_incidencia=numero_incidencia,
        **cambios,
    )


def _cuerpo_del_cierre(
    *, numero_incidencia: str = INCIDENCIA, **cambios: Any
) -> dict[str, Any]:
    return cuerpo_de_cierre(
        hash_parte=HASH, numero_incidencia=numero_incidencia, **cambios
    )


# --------------------------------------------------------------------------
# El control del contador: que cuente de verdad y que no se deje nada fuera
# --------------------------------------------------------------------------


def test_f034_r38_el_contador_ve_todos_los_metodos_del_puerto():
    """El control del control: un contador que no viera un método mentiría.

    Si el puerto ganara mañana un método de lectura y el contador no lo
    apuntara, los recuentos de abajo seguirían verdes con una consulta de más.
    Aquí se llama a **cada** método público de `RepositorioPartesPort` a través
    del contador y se exige que aparezca.
    """
    metodos = sorted(
        nombre
        for nombre, valor in vars(RepositorioPartesPort).items()
        if callable(valor) and not nombre.startswith("_")
    )
    llamados: list[str] = []

    class Grabadora:
        def __getattr__(self, nombre: str) -> Callable[..., None]:
            def grabar(*_args: Any, **_kwargs: Any) -> None:
                llamados.append(nombre)

            return grabar

    contador = RepositorioQueCuenta(Grabadora())
    for nombre in metodos:
        getattr(contador, nombre)()

    assert metodos, "el puerto no puede quedarse sin métodos"
    assert contador.llamadas == metodos
    assert llamados == metodos


# --------------------------------------------------------------------------
# `POST /api/adjuntar` · lo mismo que antes de la feature
# --------------------------------------------------------------------------

#: `adjuntar` en dry-run, medido en `dev` (`e2e5d7a`): la situación de la
#: puerta de aptitud, la traza previa del gráfico y la traza `dry_run_ok`.
LLAMADAS_ADJUNTAR_DRY_RUN = [
    "consultar_situacion",
    "consultar_grafico",
    "guardar_grafico",
]

#: `adjuntar` con `commit` y confirmación, medido en `dev`: lo del dry-run más
#: la traza `adjuntado` tras la escritura.
LLAMADAS_ADJUNTAR_COMMIT = [
    "consultar_situacion",
    "consultar_grafico",
    "guardar_grafico",
    "guardar_grafico",
]

#: `adjuntar` de un parte cuyo gráfico ya consta `adjuntado` (la capa 1 de
#: idempotencia de F-012), medido en `dev`: se acaba en la traza local.
LLAMADAS_ADJUNTAR_YA_ADJUNTADO = [
    "consultar_situacion",
    "consultar_grafico",
]


@pytest.mark.parametrize(
    ("cambios", "esperadas"),
    [
        ({}, LLAMADAS_ADJUNTAR_DRY_RUN),
        ({"commit": "true", "confirmado": "true"}, LLAMADAS_ADJUNTAR_COMMIT),
    ],
    ids=["dry_run", "commit"],
)
def test_f034_r38_adjuntar_hace_las_mismas_llamadas_que_antes(cambios, esperadas):
    """R38, R2, R10 · una sola consulta de situación, y ni una llamada más.

    La traza de archivo y los dos códigos salen de esa misma consulta: si el
    cotejo o la puerta de archivo preguntaran algo por su cuenta, aquí
    aparecería un `consultar_situacion` de más (o un método nuevo).
    """
    mundo = _mundo_del_adjuntar()
    contador = _contando(mundo)

    mundo.adjuntar(_cuerpo_del_adjuntar(**cambios))

    assert contador.llamadas == esperadas
    assert contador.veces("consultar_situacion") == 1
    assert contador.veces("consultar_grafico") == 1


def test_f034_r38_adjuntar_ya_adjuntado_hace_las_mismas_llamadas_que_antes():
    """R38, R21 · la capa 1 de idempotencia sigue costando lo mismo."""
    mundo = _mundo_del_adjuntar()
    mundo.repositorio.traza_grafico = TrazaGrafico(
        hash_parte=HASH,
        numero_incidencia=INCIDENCIA,
        estado=EstadoGrafico.ADJUNTADO,
        adjuntado_at_utc=AHORA,
    )
    contador = _contando(mundo)

    respuesta = mundo.adjuntar(_cuerpo_del_adjuntar(commit="true", confirmado="true"))

    assert respuesta["estado"] == "adjuntado"
    assert contador.llamadas == LLAMADAS_ADJUNTAR_YA_ADJUNTADO
    assert mundo.graficos.llamadas == []


# --------------------------------------------------------------------------
# `POST /api/cerrar` · lo mismo que antes de la feature
# --------------------------------------------------------------------------

#: `cerrar` en dry-run, medido en `dev` (`e2e5d7a`): la situación de la puerta,
#: la traza `dry_run_ok` del cierre y la traza del gráfico (que el cierre lee
#: **después** del dry-run, F-012 R49).
LLAMADAS_CERRAR_DRY_RUN = [
    "consultar_situacion",
    "guardar_cierre",
    "consultar_grafico",
]

#: `cerrar` con `commit` y confirmación, medido en `dev`: lo del dry-run, la
#: traza `cerrado` y la fila del histórico de estado (F-028), que reutiliza la
#: situación ya leída (`situacion_leida`) y no vuelve a preguntarla.
LLAMADAS_CERRAR_COMMIT = [
    "consultar_situacion",
    "guardar_cierre",
    "consultar_grafico",
    "guardar_cierre",
    "registrar_decision",
]


@pytest.mark.parametrize(
    ("cambios", "esperadas"),
    [
        ({}, LLAMADAS_CERRAR_DRY_RUN),
        ({"commit": True, "confirmado": True}, LLAMADAS_CERRAR_COMMIT),
    ],
    ids=["dry_run", "commit"],
)
def test_f034_r38_cerrar_hace_las_mismas_llamadas_que_antes(cambios, esperadas):
    """R38, R2, R10 · el cierre tampoco paga nada por decidir con lo guardado."""
    mundo = _mundo_del_cierre()
    contador = _contando(mundo)

    mundo.cerrar(_cuerpo_del_cierre(**cambios))

    assert contador.llamadas == esperadas
    assert contador.veces("consultar_situacion") == 1
    assert contador.veces("consultar_grafico") == 1


# --------------------------------------------------------------------------
# Los rechazos nuevos · una sola llamada, la de la situación
# --------------------------------------------------------------------------


def _adjuntar_con_otra_incidencia() -> tuple[RepositorioQueCuenta, Callable[[], Any]]:
    mundo = _mundo_del_adjuntar()
    contador = _contando(mundo)
    return contador, lambda: mundo.adjuntar(
        _cuerpo_del_adjuntar(
            numero_incidencia="RS26.09/0999", commit="true", confirmado="true"
        )
    )


def _adjuntar_sin_archivo_guardado() -> tuple[RepositorioQueCuenta, Callable[[], Any]]:
    mundo = _mundo_del_adjuntar(estado_archivo=None)
    contador = _contando(mundo)
    return contador, lambda: mundo.adjuntar(
        _cuerpo_del_adjuntar(commit="true", confirmado="true")
    )


def _cerrar_con_otra_incidencia() -> tuple[RepositorioQueCuenta, Callable[[], Any]]:
    mundo = _mundo_del_cierre()
    contador = _contando(mundo)
    return contador, lambda: mundo.cerrar(
        _cuerpo_del_cierre(
            numero_incidencia="RS26.09/0999", commit=True, confirmado=True
        )
    )


def _cerrar_sin_archivo_guardado() -> tuple[RepositorioQueCuenta, Callable[[], Any]]:
    mundo = _mundo_del_cierre(estado_archivo=None)
    contador = _contando(mundo)
    return contador, lambda: mundo.cerrar(
        _cuerpo_del_cierre(commit=True, confirmado=True)
    )


@pytest.mark.parametrize(
    ("montar", "error"),
    [
        (_adjuntar_con_otra_incidencia, CodigosNoCoinciden),
        (_adjuntar_sin_archivo_guardado, ParteNoArchivado),
        (_cerrar_con_otra_incidencia, CodigosNoCoinciden),
        (_cerrar_sin_archivo_guardado, ParteNoArchivado),
    ],
    ids=[
        "adjuntar_codigos",
        "adjuntar_archivo",
        "cerrar_codigos",
        "cerrar_archivo",
    ],
)
def test_f034_r38_un_rechazo_nuevo_cuesta_una_sola_consulta(montar, error):
    """R38, R13 · el 409 sale con la situación ya leída y sin preguntar nada más.

    El cotejo (1 bis) y la puerta de archivo van **antes** de la traza previa
    del gráfico y del dry-run: si alguno de los dos necesitara otra lectura, o
    si la traza local se consultara antes que ellos, aparecería aquí.

    Todos con `commit` y confirmación, que es el caso que escribiría: el
    rechazo tiene que llegar antes de cualquier otra llamada, también ahí.
    """
    contador, llamar = montar()

    with pytest.raises(error):
        llamar()

    assert contador.llamadas == ["consultar_situacion"]
