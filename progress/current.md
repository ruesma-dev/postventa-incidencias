<!-- progress/current.md -->
# Sesión activa

**Feature en curso**: F-001 · Esqueleto del monorepo y `/health`
**Rama**: `feature/F-001-esqueleto`
**Fecha**: 2026-08-18

## Estado

Implementación **terminada y verificada de punta a punta** (Function real
levantada con `func start`, proxy del front y página comprobada en Chrome).
Detalle en `progress/impl_F-001.md`.

Pendiente: review contra `CHECKPOINTS.md` y cierre (merge a `dev`, resumen en
`history.md`).

## Contexto que conviene no perder

- Esta sesión arrancó con `CLAUDE_CODE_CHILD_SESSION=1`. Los agentes del
  arnés se instalaron hoy, en esta misma sesión, así que puede que no estén
  cargados hasta reiniciar Claude Code.
- El humano ha pedido **usar siempre subagentes** a partir de ahora.
- Decisiones de producto y hallazgos del dominio: `docs/ARCHITECTURE.md` y
  `docs/referencia/`. Lo más importante que salió al definir el proyecto:
  «Cerrar parte» de Sigrid exige documento adjunto, y un parte firmado con
  observaciones manuscritas **no** es un parte conforme.
