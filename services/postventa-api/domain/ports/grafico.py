# services/postventa-api/domain/ports/grafico.py
"""El puerto del gráfico: adjuntar el parte a la reclamación (F-012).

**Un método y ni uno más.** No es minimalismo: es lo mismo que declara
`domain/ports/erp.py` con sus tres, y por el mismo motivo. Cada método de un
puerto contra el ERP de producción es una capacidad que este servicio se
concede; borrar, sustituir o versionar gráficos está **fuera de alcance por
decisión del humano** (H6), y un puerto que ofreciera esos métodos invitaría a
usarlos.

## Por qué es un puerto aparte y no un método más de `ErpPort`

Son **dos escrituras contra dos endpoints distintos**, con contratos, tiempos y
semántica de idempotencia distintos:

- `sql/write` (el cierre): batch, sin idempotencia, y **la escritura no se
  reintenta jamás** porque un tiempo agotado no dice que el ERP no haya
  escrito.
- `sigrid/concepto-grafico` (esto): endpoint de dominio, **idempotente por
  tamaño y `sha256`**, así que el reintento es seguro y el motivo de un fallo
  lo dice.

Mezclarlas en un puerto obligaría a dos políticas de error en la misma
función, y `ErpPort` dice en su docstring «tres métodos y ni uno más».

## Dry-run y commit son el mismo método, con un booleano

Y eso es deliberado, al revés que en `cliente.py` —donde leer y escribir son
dos métodos privados distintos a propósito—. Aquí la pasarela expone **una**
operación cuyo `commit` decide si escribe, con la **misma forma de respuesta**
en los dos casos; partirla en dos métodos duplicaría el parseo de una respuesta
de trece campos para no ganar ninguna garantía. La garantía de que no se
escribe sin querer está donde tiene que estar: `commit` es de solo palabra
clave, el paso hace **siempre** el dry-run antes (R20) y la autorización se
exige entre uno y otro (R23).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.models.grafico import PeticionGrafico, RespuestaGrafico

__all__ = ["GraficoPort"]


@runtime_checkable
class GraficoPort(Protocol):
    """Quien sabe adjuntar un documento a un concepto de Sigrid."""

    def adjuntar(
        self, *, peticion: PeticionGrafico, commit: bool
    ) -> RespuestaGrafico:
        """Adjunta el parte a la reclamación, o dice qué se adjuntaría.

        Con `commit=False` es una **lectura**: la pasarela solo consulta y
        devuelve las tres filas que escribiría. Con `commit=True` escribe las
        tres en una transacción, y responde `idempotente: true` con
        `committed: false` si ese mismo documento ya colgaba de ese concepto —lo
        cual **es un éxito** (R25, R26).

        Levanta, sin traducir a HTTP:

        - `CierreDeshabilitado` — este entorno no escribe en el ERP, o el
          interruptor está apagado (R38, R39).
        - `EscrituraDocumentalDeshabilitada` — falta una precondición del dueño
          de `sigrid-api` (R32). No es un fallo de quien llama.
        - `GraficoRechazadoPorLaPasarela` — un código de rechazo de la lista
          cerrada; el ERP quedó intacto (R33).
        - `GraficoFallido` — la pasarela falló, no respondió o devolvió algo
          que no se entiende. Lleva `reintento_seguro=True` **siempre**: el
          endpoint es idempotente por contenido (R28, R29, R31, R34).

        **Ninguno lleva el cuerpo crudo de la respuesta** (R35): detrás hay un
        SQL Server de producción con datos de clientes, y de un error solo se
        toma `details.codigo`.
        """
        ...
