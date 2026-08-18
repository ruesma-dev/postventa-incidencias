<!-- progress/current.md -->
# Sesión activa

**Feature en curso**: F-001 · Esqueleto del monorepo y `/health`
**Rama**: `feature/F-001-esqueleto`
**Fecha**: 2026-08-18

## Estado

Implementación terminada, primera review **RECHAZADA** y correcciones
aplicadas. Pendiente: segunda review y cierre.

Detalle en `progress/impl_F-001.md`, `progress/review_F-001.md` (la primera) y
`progress/mutacion_F-001.md`.

## Verificaciones MANUAL (humano) — comandos exactos

Las automáticas las corre el portero. Estas las ejecutó el implementer y
puede repetirlas el humano; **ninguna es requisito para cerrar**, pero son la
prueba de que el servicio arranca de verdad y no solo en los tests:

```bash
# 1. Levantar la Function (OJO: hay que activar el venv del servicio, o func
#    coge el Python global y falla con ModuleNotFoundError: pydantic)
cd services/postventa-api
VIRTUAL_ENV="$PWD/.venv" PATH="$PWD/.venv/Scripts:$PATH" func start --port 7073

# 2. En otra terminal, comprobar el endpoint
curl -s -w "\nHTTP %{http_code}\n" http://localhost:7073/api/health
# Esperado: HTTP 200 y
# {"servicio": "postventa-api", "version": "0.1.0", "entorno": "local", "estado": "ok"}
```

Resultado obtenido el 2026-08-18: **HTTP 200** con ese cuerpo exacto.

El front y su proxy también se verificaron (incluida la página en Chrome),
pero **el front ya no forma parte de F-001**: ver abajo.

## Decisiones del humano en esta sesión

1. **El front sale de F-001 y va a F-007.** Sus 114 líneas de `dev_server.py`
   hundían la puerta de cobertura sin proteger nada desplegable. El trabajo
   está guardado en la rama `feature/F-007-front`.
2. **F-001 se cierra con la fase RED como excepción anotada.** No se
   fabricará una traza roja retroactiva.
3. **Usar siempre subagentes** a partir de ahora.

## Contexto que conviene no perder

- Esta sesión arrancó con `CLAUDE_CODE_CHILD_SESSION=1`: los agentes del
  arnés (`spec-author`, `implementer`, `reviewer`) **no están cargados**. Se
  usan agentes genéricos a los que se les pasa `.claude/agents/*.md`. Con un
  Claude Code arrancado en limpio estarían disponibles.
- Hallazgos de dominio que mandan sobre el diseño, en `docs/ARCHITECTURE.md` y
  `docs/referencia/`: «Cerrar parte» de Sigrid **exige documento adjunto**, y
  un parte firmado con observaciones manuscritas **no** es un parte conforme.
