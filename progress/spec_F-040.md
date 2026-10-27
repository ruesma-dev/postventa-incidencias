<!-- progress/spec_F-040.md -->
# Spec de F-040 (y de F-059) · resumen para el líder

> spec-author, 2026-10-07. Worktree `postventa-f040`, rama
> `feature/F-040-volcado-sigrid` (desde `dev` `f86d639`). **Aprobada por el
> humano el 2026-10-07**: D-1 a D-14 como se recomendaban y Q-1 a Q-8
> respondidas. Por D-1 la spec está **partida en dos carpetas**:
>
> - `specs/F-059-volcado-sigrid-backend/` — el backend (R1–R43), va **antes**.
> - `specs/F-040-volcado-sigrid/` — el front (R50–R59), bloqueada por F-059 y
>   por F-038.
>
> No se ha ejecutado `init.sh` ni pytest (autorizado). Ni código, ni
> `features.json`, ni `BACKLOG.md`, ni `current.md` tocados.

## Lo que el líder tiene que hacer

1. **Dar de alta F-059** en `harness/features.json` (propuesta abajo) y
   llevar `specs/F-059-volcado-sigrid-backend/` a su rama cuando empiece.
2. **Actualizar F-040**: descripción (es el front, bloqueada por F-059 y
   F-038), `blocked_by`, y que la spec está aprobada.
3. Al desplegar F-059 (su T24), la fila de consumidores de
   `azure-apps/sigrid_api.md` §10 (Q-6).

### Propuesta de ficha F-059

- **id**: `F-059`
- **title**: «Volcado a Sigrid en el backend: ensayo, escritura en lote y
  estado volcada»
- **branch**: `feature/F-059-volcado-sigrid-backend`
- **rigor**: `critico` · **sdd**: `true` · **status**: `spec_ready` (cuando
  F-056 esté `done`) · **priority**: justo antes de F-040
- **blocked_by**: «F-056 (las candidatas al volcado y los estados de
  revisión), que tiene que estar done y mergeada en dev».
- **description**: «Sacada de F-040 el 2026-10-07 por el límite de servicio
  (D-1, decisión del humano). El backend del volcado de la bandeja a Sigrid
  en services/postventa-api: tres endpoints (GET /api/volcado,
  POST /api/volcado/ensayo, POST /api/volcado/volcar) sobre
  POST /api/sigrid/partes-reclamacion de sigrid-api (azure-apps/sigrid_api.md
  §8.9); ensayo guardado obligatorio (misma persona, 30 min); escritura
  anticipada del evento enviado antes de cada commit; referencia
  PVI-<incidencia_id> para que reintentar no duplique; tabla append-only
  postventa.volcados_sigrid (16_volcados_sigrid.sql); estados derivados
  volcada y en_duda que amplían los de F-056 y bloquean la revisión; tipo
  0002 siempre, causante false, sin urgencia ni clase; el parte queda en SAT
  y Posventa lo pasa a PTE a mano; ventana propia VOLCADO_HABILITADO
  publicada cerrada (infra/27_ventana_volcado.ps1) y lectura de verificación
  (infra/28_volcado_lectura_sigrid.ps1); verificación en producción en la
  obra 0626 con una escritura autorizada y anulación posterior. Spec:
  specs/F-059-volcado-sigrid-backend/. El front es F-040.»
- **acceptance**:
  1. «Una incidencia aprobada se crea en Sigrid con sus campos (tipo 0002,
     oficio, ubicación, interviniente sin causante) y su código vuelve a la
     bandeja como volcada»
  2. «No se escribe en Sigrid sin un ensayo guardado de la misma persona de
     menos de 30 minutos, con confirmado true y con la ventana
     VOLCADO_HABILITADO abierta; el despliegue la deja cerrada»
  3. «Reintentar no duplica: la misma referencia PVI- vuelve idempotente;
     un tiempo agotado deja la incidencia en_duda y el reintento la recupera»
  4. «Un lote de N filas crea N partes; si uno falla se sabe cuál y por qué»
  5. «Una incidencia volcada o en duda no se puede editar, descartar ni
     aprobar»
  6. «Ni propietario, ni persona, ni correo, ni oid, ni login, ni textos en
     ningún log»
  7. «Verificado en producción en la obra 0626 con una escritura autorizada,
     anulada después en la UI de Sigrid»
  8. «docs/ y azure-apps/postventa_incidencias.md al día»
  9. «bash harness/init.sh en verde»

### Ajuste propuesto de F-040

- **description** (añadir): «PARTIDA EL 2026-10-07 (D-1, decisión del
  humano): esta ficha es el panel de volcado en bandeja.html (ensayar,
  confirmar con el número de partes, volcar de trozo en trozo, parar al
  primer fallo, aviso de pasar a PTE a mano) y el cierre de sus placeholders
  del portal; el backend es F-059. Spec aprobada:
  specs/F-040-volcado-sigrid/.»
- **blocked_by**: «F-059 (el backend del volcado), done, desplegada y
  verificada; y F-038 (bandeja.html), done.»
- Los acceptance actuales siguen valiendo, cumplidos entre F-059 (backend) y
  F-040 (la página).

## Qué decide la spec (con las respuestas del humano)

- **Flujo**: candidatas → ensayo guardado → confirmación → volcado (solo lo
  `previsto`, misma persona, misma revisión) → resultado de vuelta a la
  bandeja (`volcada` con su `RS…`, `en_duda` o `aprobada` con su motivo).
- **Q-1** tipo `0002` siempre; **Q-2** `causante: false`; **Q-3** el parte
  queda en SAT y Posventa lo pasa a PTE a mano (en la documentación, en el
  panel —R59— y en la verificación, que **no** lo pasa a PTE); **Q-4** obra
  0626; **Q-5** recrear un parte anulado, fuera; **Q-6** sí, la fila de
  `sigrid_api.md` la escribe el líder al desplegar; **Q-7** cualquiera del
  grupo con login de Sigrid; **Q-8** el primer volcado masivo de la 0677 y el
  ajuste de `N`, **pendiente fuera de alcance**.
- **D-3** la ventana `VOLCADO_HABILITADO` se publica **cerrada** en cada
  despliegue y se abre con `27_ventana_volcado.ps1` para cada volcado.

## Riesgos

1. **El coste por parte no está medido**: `N`=5 conservador, App Setting; el
   ajuste es Q-8, más adelante.
2. **Tras nuestro tiempo agotado, `sigrid-api` sigue creando** (150 s): queda
   `en_duda` y el reintento lo recupera.
3. **Depende del código de F-056 tal como quede**: si los nombres difieren de
   su design, el implementer de F-059 para (su T0).
4. **Los partes quedan en SAT** hasta que Posventa los pase a PTE: si no lo
   hace, el industrial no se entera.
5. **Escritura real en una obra en uso** (0626) en las dos verificaciones: una
   cada vez, autorizada, sin PTE, anulada al terminar. El parte de prueba de
   F-006 de `sigrid-api` en la 0626 sigue sin anular.
