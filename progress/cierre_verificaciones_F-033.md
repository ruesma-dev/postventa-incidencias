<!-- progress/cierre_verificaciones_F-033.md -->
# Acta · las verificaciones manuales de F-033, cerradas el 2026-09-22

F-033 se cerró el 2026-09-18 (review **APROBADO**, `progress/review_F-033.md`,
`init.sh` en verde, merge local en `dev` `e42186a`). Quedaban fuera de la rama
sus dos verificaciones MANUAL. Esta acta dice qué se hizo de verdad y qué no,
con el mismo criterio que `progress/cierre_F-009.md`: los huecos se escriben,
no se ocultan.

## La decisión

El responsable, el **2026-09-22**: *«ahora lo esta probando postventa en
produccion. da la feature por cerrada»*.

## T13 · HECHA, y medida (2026-09-18)

`infra/25_mediciones_despliegue.ps1`, solo lectura del schema `postventa`:

| Qué | Medido |
|---|---|
| Trazas de archivo | **133**, todas `archivado` y con biblioteca |
| Trazas `pendiente` (ficheros posiblemente huérfanos) | **0** → R26 cumplido |
| Bibliotecas distintas | **1** (la de IT), del 2026-08-26 al 2026-09-18 |

En la misma pasada, la medición previa de **F-032 (T14, R26)** dio **1 fila**:
el parte `b7e9b037…d1ce` (RS26.09/0178, obra 0626), archivado el 2026-09-17
como `0626 - RS 26.09 - 0178 PARTE FIRMADO.pdf`. Se desplegó igual, con este
motivo escrito: desde F-033 ese parte **no se puede re-archivar** desde el
circuito, así que el nombre nuevo no puede dejar un huérfano. El fichero con el
nombre viejo sigue en la biblioteca de IT; renombrarlo, si se quiere, lo hace
una persona.

## T14 · NO RECORRIDA como está escrita

No hay constancia de:

1. la foto `estado`/`intentos`/`archivado_at_utc` **antes** de re-archivar,
2. un re-archivado ejecutado a propósito sobre un parte ya `archivado`,
3. `AVISO_YA_ARCHIVADO` observado en la respuesta,
4. la comprobación en SharePoint de que no hay un segundo fichero,
5. la foto **después**, igual a la de antes.

Lo que sí consta:

- El **despliegue** de `dev` con F-032 y F-033 dentro, confirmado el
  2026-09-18, y las dos ventanas de escritura abiertas ese día
  (`ARCHIVO_HABILITADO` y `CIERRE_HABILITADO`, leídas con `az`).
- El uso **real por parte de Posventa** a partir del 2026-09-22, según el
  responsable. No se ha medido desde aquí.
- El comportamiento está cubierto por **101 tests**, mutación **21/21** y un
  caso de circuito que falla si se vuelve a subir (`assert 2 == 1` antes del
  arreglo). Lo que falta es la evidencia **contra el sistema real**, que es
  justo lo que un test no puede dar.

## Cómo se cierra el hueco el día que se quiera

Con la ventana `ARCHIVO_HABILITADO` abierta y autorización para un parte
concreto:

```
powershell -ExecutionPolicy Bypass -File infra_mediciones_despliegue.ps1 -NumeroIncidencia "<RS26.xx/nnnn>"
# re-archivar ese parte desde la web
powershell -ExecutionPolicy Bypass -File infra_mediciones_despliegue.ps1 -NumeroIncidencia "<RS26.xx/nnnn>" -FotoAntes "<la linea FOTO de antes>"
```

## Lo que sigue abierto, y no lo cierra esta acta

- **F-034** · adjuntar y cerrar leen «archivado» del cuerpo (hallazgo D-6).
- **F-031** · la carpeta y el nombre salen del cuerpo, no de lo persistido.
- **F-013** · la mudanza a la biblioteca de Posventa, aprobada y en espera de
  las dos anteriores. **Decisión pendiente del humano**: las **133** trazas
  `archivado` apuntan a la biblioteca de IT y, con D-1 de F-033, esos partes no
  se subirán nunca a Posventa. El humano dijo el 2026-09-18 que lo de IT «eran
  pruebas, se puede olvidar»; falta decidir si se olvidan del todo o si al
  desplegar F-013 se les retira la traza para que puedan archivarse allí.
