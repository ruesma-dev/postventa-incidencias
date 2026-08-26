# services/postventa-api/interface_adapters/api/cola.py
"""Handler de `GET /api/cola`: los partes que esperan decisión humana (F-019).

Aquí se **compone el adaptador** y se serializa el resultado, como manda
`docs/CONVENTIONS.md`. El puerto inyectable es la costura de test: con él, la
suite prueba el borde entero sin base de datos.

## Lo que este endpoint cambia en el modelo de amenaza

Es el **primero del servicio que devuelve dato personal acumulado sin que el
llamante aporte el PDF**. Los seis anteriores exigen que tú mandes el parte:
quien no lo tiene no obtiene nada de él. Este devuelve transcripciones
manuscritas de clientes, códigos de obra y números de incidencia sin aportar
nada.

Eso **no** lo deja expuesto a internet: el servicio es backend enlazado de una
Static Web App, la plataforma le activa Easy Auth con el proveedor
`azureStaticWebApps` y sólo acepta lo que entra por el proxy del front, que a
su vez exige `authenticated` en `/*` y pertenencia al grupo de Posventa
(`docs/DESPLIEGUE.md` §5 bis). La amenaza real es otra: **el volumen**. Una
sola llamada no puede convertirse en un volcado de la cola entera contra un
servidor compartido de 1 vCPU.

De ahí la cautela que vive en este fichero: **nada al log** (R18). De aquí
sólo se registra **cuántas** entradas volvieron; cada una lleva texto
manuscrito de un cliente y el log sobrevive al parte.

## No mira `ARCHIVO_HABILITADO` (R34)

Leer la cola no es escribir en un sistema ajeno. Atarla a esa ventana la
dejaría ilegible justo cuando el archivado está cerrado, que es como se
despliega el entorno.
"""

from __future__ import annotations

from typing import Any

from config.settings import obtener_ajustes
from domain.models.errores import PeticionDePersistenciaInvalida
from domain.models.persistencia import EntradaCola
from domain.ports.persistencia import RepositorioPartesPort
from infrastructure.persistencia.fabrica import construir_repositorio

__all__ = ["LIMITE_POR_DEFECTO", "leer_cola"]

#: Cuántas entradas se piden si la petición no dice otra cosa (R15).
#:
#: Es el tamaño de una pantalla de trabajo, no de una exportación: quien mira
#: la cola decide parte a parte.
LIMITE_POR_DEFECTO = 50


def leer_cola(
    limite: Any = None,
    *,
    repositorio: RepositorioPartesPort | None = None,
) -> dict[str, Any]:
    """Devuelve las entradas de la cola, de más antigua a más reciente (R14).

    Levanta `PeticionDePersistenciaInvalida` (→ 400) **antes de consultar
    nada**, y deja subir sin traducir `ConfiguracionPgIncompleta` y
    `PersistenciaNoDisponible` (→ 503).
    """
    pedidas = _limite(limite)

    almacen = (
        repositorio
        if repositorio is not None
        else construir_repositorio(obtener_ajustes())
    )
    entradas = almacen.cola_validacion_humana(limite=pedidas)
    return {
        "total": len(entradas),
        "entradas": [_serializar(entrada) for entrada in entradas],
    }


def _limite(crudo: Any) -> int:
    """Cuántas entradas pedir: el número de la petición, o 50 (R15, R17).

    Un `limite` que no es un entero ≥ 1 es **400 y no se consulta nada**: es
    una petición mal escrita, y dejarla pasar la convertiría en un error de
    PostgreSQL, que manda a mirar el servidor a quien tenía que corregir su
    petición.
    """
    if crudo is None:
        return LIMITE_POR_DEFECTO
    try:
        pedidas = int(str(crudo))
    except (ValueError, TypeError) as mal_formado:
        raise PeticionDePersistenciaInvalida(
            "'limite' tiene que ser un número entero mayor o igual que uno"
        ) from mal_formado
    if pedidas < 1:
        raise PeticionDePersistenciaInvalida(
            "'limite' tiene que ser un número entero mayor o igual que uno"
        )
    return pedidas


def _serializar(entrada: EntradaCola) -> dict[str, Any]:
    """Una entrada de la cola, en JSON. **Ni una clave más que las de R14.**

    `motivos` se serializa **igual que en `POST /api/validar`**: mismo
    concepto, mismo JSON. Inventar aquí una segunda forma obligaría al front a
    escribir dos pintados del mismo dato, que divergirían en la primera
    corrección.

    Las `observaciones` viajan porque **quien decide las necesita delante**:
    es el único dato personal de esta respuesta y la razón de que exista la
    cola. Por eso no entran en ningún log (R18).
    """
    return {
        "hash_parte": entrada.hash_parte,
        "codigo_obra": entrada.codigo_obra,
        "numero_incidencia": entrada.numero_incidencia,
        "observaciones": entrada.observaciones,
        "confianza_observaciones": entrada.confianza_observaciones,
        "clasificacion_firma": entrada.clasificacion_firma,
        "motivos": [
            {"codigo": codigo, "texto": texto}
            for codigo, texto in entrada.motivos
        ],
        "validado_at_utc": entrada.validado_at_utc.isoformat(),
    }
