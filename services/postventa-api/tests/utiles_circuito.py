# services/postventa-api/tests/utiles_circuito.py
"""El mundo de los endpoints que escriben en el ERP, con los puertos inyectados (F-034).

Sin `test_` en el nombre, como `utiles_pg.py` y `utiles_sigrid.py`: es
utillería, no una suite.

## Por qué existe

F-034 mueve **de dónde salen** tres datos con los que `POST /api/adjuntar` (y
en el Bloque 3, `POST /api/cerrar`) escribe en el ERP de producción: el estado
del archivo y los dos códigos. Antes salían del cuerpo; desde F-034 salen de lo
**guardado**, es decir, de la `SituacionParte` que devuelve el repositorio. Los
tests de la feature necesitan, una y otra vez, el mismo mundo: un parte con su
veredicto apto **guardado**, sus dos códigos **guardados** y su traza de
archivo **guardada**, y un cuerpo que diga lo que el caso quiera que diga.

Montarlo aquí una vez tiene dos ventajas que no son de comodidad:

1. **Separa las dos fuentes a propósito.** Lo guardado se escribe con
   `situacion_guardada(...)` y lo declarado con `formulario(...)`, y ninguna de
   las dos copia de la otra. Un ayudante que rellenara el cuerpo a partir de la
   situación —o al revés— haría que los dos coincidieran **por construcción**,
   y con eso ningún test podría ver el defecto que F-034 viene a cerrar.
2. **Llega a la puerta de verdad.** Los cinco puertos van inyectados, así que
   la puerta de entorno (`CIERRE_HABILITADO`) no se evalúa y el 503 no puede
   tapar el 409 que se quiere ver (D-6 de `requirements.md`). Cada caso
   negativo de F-034 tiene además su **control positivo** con el mismo mundo:
   sin él, un test que «pasa» porque el paso revienta antes de la puerta no se
   distinguiría de uno que pasa porque la puerta funciona.

**Sin red, sin base de datos, sin IA y sin tocar el ERP** (R37). Ni un dato
real: el PDF es sintético y ni el login, ni el correo, ni el `oid` son de
nadie.

El Bloque 3 (T8) añade el mundo de `POST /api/cerrar` —`MundoDelCierre` y
`cuerpo_de_cierre`— con las mismas dos reglas: lo guardado y lo declarado se
escriben aparte, y los cuatro puertos van inyectados para que el 503 de la
ventana no tape la puerta.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from domain.models.cierre import CorrespondenciaSigrid, Reclamacion
from domain.models.estado import SituacionParte
from domain.models.grafico import FIRMA_PDF
from domain.models.persistencia import (
    EPOCA_SIN_DECIDIR,
    EstadoArchivo,
    EstadoGrafico,
    PreferenciasUsuario,
    ResultadoGuardado,
    TrazaArchivo,
    TrazaGrafico,
)

from tests.utiles_pg import RepositorioEnMemoria
from tests.utiles_sigrid import ErpEnMemoria, GraficoEnMemoria
from tests.utiles_validacion import veredicto_apto

__all__ = [
    "AHORA",
    "CORREO",
    "LOGIN",
    "OID",
    "PDF",
    "MundoDelAdjuntar",
    "MundoDelCierre",
    "Preferencias",
    "Usuarios",
    "cuerpo_de_cierre",
    "formulario",
    "peticion_json",
    "peticion_multipart",
    "reclamacion",
    "situacion_guardada",
]

AHORA = datetime(2026, 9, 23, 12, 0, 0, tzinfo=UTC)
OID = "oid-inventado-para-el-test"
CORREO = "personainventada@ejemplo.invalido"
LOGIN = "loginraroinventado"

#: Un PDF sintético. **No es un parte**: los de `muestras/` llevan el DNI
#: manuscrito de un cliente y no se versionan ni se copian a la suite.
PDF = FIRMA_PDF + b"1.7\nsintetico para F-034\n%%EOF\n"


class Usuarios:
    """Correspondencia ya confirmada: el login sale sin derivar nada.

    **Apunta cada llamada** en `llamadas` (H-R1 de la review de F-034). Con
    la correspondencia confirmada, resolver el login no deja rastro en el ERP
    —no hace falta verificarlo—, así que sin esta lista ningún test podía ver
    si el login se resolvía **antes o después** de las puertas: una puerta
    movida por debajo del login pasaba la suite entera en verde. En
    producción, para un usuario **sin** correspondencia confirmada, resolver
    el login es una lectura a Sigrid y una escritura en la tabla de
    correspondencias; por eso `nada_ha_tocado_el_erp()` de los dos mundos
    exige esta lista vacía.
    """

    def __init__(self) -> None:
        self.llamadas: list[tuple[str, str]] = []

    def resolver_login(self, *, usuario_oid: str) -> CorrespondenciaSigrid:
        self.llamadas.append(("resolver_login", usuario_oid))
        return CorrespondenciaSigrid(
            usuario_oid=usuario_oid,
            login_sigrid=LOGIN,
            alta_at_utc=AHORA,
            verificado_at_utc=AHORA,
        )

    def guardar_login(self, *, correspondencia):  # pragma: no cover
        self.llamadas.append(("guardar_login", correspondencia.usuario_oid))
        return ResultadoGuardado.CREADO


class Preferencias:
    """Sin auto-cierre: escribir exige `confirmado`."""

    def obtener_preferencias(self, *, usuario_oid: str) -> PreferenciasUsuario:
        return PreferenciasUsuario(
            usuario_oid=usuario_oid,
            auto_cierre=False,
            actualizado_at_utc=EPOCA_SIN_DECIDIR,
        )

    def guardar_preferencias(self, *, preferencias):  # pragma: no cover
        return ResultadoGuardado.CREADO


def reclamacion(codigo: str) -> Reclamacion:
    """Una reclamación abierta y cerrable, inventada, con ese código."""
    return Reclamacion(
        ide=340_034,
        emp=1,
        tip=708,
        est=3,
        codigo=codigo,
        descripcion="REPARACION INVENTADA",
        estado_origen_cod="PTE",
        estado_origen_res="PENDIENTE",
        estado_destino_est=90,
        estado_destino_cod="CER",
        estado_destino_res="CERRADA",
    )


def situacion_guardada(
    *,
    hash_parte: str,
    codigo_obra: str,
    numero_incidencia: str,
    estado_archivo: EstadoArchivo | None = EstadoArchivo.ARCHIVADO,
) -> SituacionParte:
    """Lo que la base tiene de ese parte: veredicto apto, códigos y archivo.

    El veredicto sale de `veredicto_apto`, que es `validar_parte` de verdad
    (F-004), con los dos códigos **guardados** que pida el caso. Un código
    vacío no daría un apto —F-004 no aprueba lo ilegible—, así que para el
    caso de R15 se deja el apto y se vacía el código después: es el mundo de
    una fila de `partes` a la que le falta el código aunque el veredicto que se
    emitió en su día fuera apto.

    `estado_archivo=None` es «no hay traza de archivo»: el `LEFT JOIN` de
    F-033 que no casa.
    """
    validacion = veredicto_apto(
        hash_parte=hash_parte,
        codigo_obra=codigo_obra or "0000",
        numero_incidencia=numero_incidencia or "XX00.00/0000",
    )
    validacion = replace(
        validacion, codigo_obra=codigo_obra, numero_incidencia=numero_incidencia
    )
    archivo = (
        TrazaArchivo(hash_parte=hash_parte, estado=estado_archivo)
        if estado_archivo is not None
        else None
    )
    return SituacionParte(validacion=validacion, archivo=archivo)


def formulario(
    *,
    hash_parte: str,
    codigo_obra: str,
    numero_incidencia: str,
    estado_archivo: str = "archivado",
    **cambios: str,
) -> dict[str, str]:
    """El cuerpo de `POST /api/adjuntar`: **lo declarado**, nada más.

    Se escribe aparte de `situacion_guardada` a propósito (ver la cabecera):
    que los dos coincidan o no lo decide cada caso, nunca este ayudante.
    """
    campos = {
        "hash": hash_parte,
        "codigo_obra": codigo_obra,
        "numero_incidencia": numero_incidencia,
        "veredicto": "apto",
        "destino": "archivo_y_cierre",
        "estado_archivo": estado_archivo,
        "usuario_oid": OID,
        "correo": CORREO,
    }
    campos.update(cambios)
    return campos


class MundoDelAdjuntar:
    """Los cinco puertos de `POST /api/adjuntar`, inyectados y observables.

    `adjuntar(...)` llama al **handler** de verdad
    (`interface_adapters.api.adjuntar.adjuntar_grafico`) y `por_la_ruta(...)`
    llama a la **ruta** de verdad (`function_app.adjuntar`) con el handler
    envuelto para que reciba estos mismos puertos: así se ve el código HTTP que
    sale del `except` real, no el de una excepción fabricada por el test.

    `nada_ha_tocado_el_erp()` es la pregunta de R13: ni el login resuelto, ni
    una lectura de la reclamación, ni una verificación de login, ni una llamada a la pasarela, ni
    una traza escrita, ni siquiera la consulta de la traza local del gráfico.
    """

    def __init__(
        self,
        situacion: SituacionParte,
        *,
        codigo_en_sigrid: str = "RS26.08/0123",
    ) -> None:
        self.erp = ErpEnMemoria(reclamacion(codigo_en_sigrid))
        self.graficos = GraficoEnMemoria()
        self.repositorio = RepositorioEnMemoria(situacion=situacion)
        self.usuarios = Usuarios()
        self.preferencias = Preferencias()

    def _puertos(self) -> dict[str, Any]:
        return {
            "erp": self.erp,
            "graficos": self.graficos,
            "repositorio": self.repositorio,
            "usuarios": self.usuarios,
            "preferencias": self.preferencias,
            "ahora": AHORA,
        }

    def adjuntar(self, campos: dict[str, str], *, contenido: bytes = PDF) -> dict:
        """El handler, con los puertos de este mundo."""
        from interface_adapters.api.adjuntar import adjuntar_grafico

        return adjuntar_grafico(contenido, **self._puertos(), **campos)

    def por_la_ruta(self, monkeypatch, campos: dict[str, str]):
        """La ruta HTTP de verdad, con el handler de verdad y estos puertos."""
        import function_app
        from interface_adapters.api.adjuntar import adjuntar_grafico

        puertos = self._puertos()

        def con_los_puertos(contenido: bytes, **del_formulario: Any) -> dict:
            return adjuntar_grafico(contenido, **puertos, **del_formulario)

        monkeypatch.setattr(function_app, "adjuntar_grafico", con_los_puertos)
        return function_app.adjuntar(peticion_multipart(campos))

    def nada_ha_tocado_el_erp(self) -> bool:
        """R13 · cero llamadas al ERP y a la pasarela, y cero trazas.

        Y **ni siquiera se ha resuelto el login** (`usuarios.llamadas`): es lo
        primero del paso que puede hablar con Sigrid (H-R1 de la review).
        """
        return (
            self.usuarios.llamadas == []
            and self.erp.lecturas == []
            and self.erp.verificaciones == []
            and self.erp.cierres == []
            and self.graficos.llamadas == []
            and self.repositorio.graficos == []
            and self.repositorio.graficos_consultados == []
            and self.repositorio.cierres == []
        )


def peticion_multipart(campos: dict[str, str], *, contenido: bytes = PDF):
    """Una petición `multipart` a `/api/adjuntar` con el fichero y los campos."""
    import azure.functions as func

    frontera = "----frontera-inventada-f034"
    partes = [
        f"--{frontera}\r\n"
        f'Content-Disposition: form-data; name="{nombre}"\r\n\r\n'
        f"{valor}\r\n"
        for nombre, valor in campos.items()
    ]
    cuerpo = "".join(partes).encode("utf-8")
    cuerpo += (
        f"--{frontera}\r\n"
        f'Content-Disposition: form-data; name="fichero"; filename="parte.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode()
    cuerpo += contenido + f"\r\n--{frontera}--\r\n".encode()
    return func.HttpRequest(
        method="POST",
        url="/api/adjuntar",
        headers={"Content-Type": f"multipart/form-data; boundary={frontera}"},
        body=cuerpo,
    )


# --------------------------------------------------------------------------
# Bloque 3 (T8) · el mundo de `POST /api/cerrar`
# --------------------------------------------------------------------------


def cuerpo_de_cierre(
    *,
    hash_parte: str,
    numero_incidencia: str,
    estado_archivo: str = "archivado",
    **cambios: Any,
) -> dict[str, Any]:
    """El cuerpo JSON de `POST /api/cerrar`: **lo declarado**, nada más.

    Sin `codigo_obra`, como el de verdad (`cerrar.py`, R16): el cierre solo
    coteja el número de incidencia. `commit` y `confirmado` van en `cambios`
    como booleanos de JSON, que es lo único que el borde toma por `true`.
    """
    campos: dict[str, Any] = {
        "hash": hash_parte,
        "numero_incidencia": numero_incidencia,
        "veredicto": "apto",
        "destino": "archivo_y_cierre",
        "estado_archivo": estado_archivo,
        "usuario_oid": OID,
        "correo": CORREO,
    }
    campos.update(cambios)
    return campos


class MundoDelCierre:
    """Los cuatro puertos de `POST /api/cerrar`, inyectados y observables.

    Gemelo de `MundoDelAdjuntar`: `cerrar(...)` llama al **handler** de verdad
    (`interface_adapters.api.cerrar.cerrar_incidencia`) y `por_la_ruta(...)` a
    la **ruta** de verdad (`function_app.cerrar`) con el handler envuelto para
    que reciba estos puertos.

    La traza del gráfico **adjuntado** está puesta por defecto: es el mundo en
    el que un cierre con `commit` puede ocurrir (F-012 R2), y sin ella el
    control positivo con `commit` se pararía en `ParteNoAdjuntado` y no
    demostraría nada.

    `nada_ha_tocado_el_erp()` es la pregunta de R13 para el cierre: ni el login
    resuelto, ni una lectura de la reclamación, ni una verificación de login, ni un cierre, ni
    una traza de cierre, ni una fila del histórico, ni siquiera la consulta de
    la traza del gráfico (que en el paso va **después** del dry-run).
    """

    def __init__(
        self,
        situacion: SituacionParte,
        *,
        codigo_en_sigrid: str = "RS26.08/0123",
    ) -> None:
        self.erp = ErpEnMemoria(reclamacion(codigo_en_sigrid))
        self.repositorio = RepositorioEnMemoria(
            situacion=situacion,
            traza_grafico=TrazaGrafico(
                hash_parte="",
                numero_incidencia=codigo_en_sigrid,
                estado=EstadoGrafico.ADJUNTADO,
                adjuntado_at_utc=AHORA,
            ),
        )
        self.usuarios = Usuarios()
        self.preferencias = Preferencias()

    def _puertos(self) -> dict[str, Any]:
        return {
            "erp": self.erp,
            "repositorio": self.repositorio,
            "usuarios": self.usuarios,
            "preferencias": self.preferencias,
            "ahora": AHORA,
        }

    def cerrar(self, cuerpo: dict[str, Any]) -> dict:
        """El handler, con los puertos de este mundo."""
        from interface_adapters.api.cerrar import cerrar_incidencia

        return cerrar_incidencia(cuerpo, **self._puertos())

    def por_la_ruta(self, monkeypatch, cuerpo: dict[str, Any]):
        """La ruta HTTP de verdad, con el handler de verdad y estos puertos."""
        import function_app
        from interface_adapters.api.cerrar import cerrar_incidencia

        puertos = self._puertos()

        def con_los_puertos(del_cuerpo: Any) -> dict:
            return cerrar_incidencia(del_cuerpo, **puertos)

        monkeypatch.setattr(function_app, "cerrar_incidencia", con_los_puertos)
        return function_app.cerrar(peticion_json(cuerpo))

    def nada_ha_tocado_el_erp(self) -> bool:
        """R13 · cero llamadas al ERP, cero trazas y cero filas de estado.

        Y **ni siquiera se ha resuelto el login** (`usuarios.llamadas`): R13
        dice «antes de resolver el login contra el ERP», y sin mirar esta
        lista una puerta movida por debajo del login pasaba en verde (H-R1 de
        la review).
        """
        return (
            self.usuarios.llamadas == []
            and self.erp.lecturas == []
            and self.erp.verificaciones == []
            and self.erp.cierres == []
            and self.repositorio.cierres == []
            and self.repositorio.graficos_consultados == []
            and self.repositorio.decisiones == []
        )


def peticion_json(cuerpo: dict[str, Any], *, ruta: str = "/api/cerrar"):
    """Una petición JSON a la ruta indicada (por defecto, `/api/cerrar`)."""
    import azure.functions as func

    return func.HttpRequest(
        method="POST",
        url=ruta,
        headers={"Content-Type": "application/json"},
        body=json.dumps(cuerpo).encode("utf-8"),
    )
