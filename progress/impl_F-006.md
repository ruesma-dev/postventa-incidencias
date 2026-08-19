<!-- progress/impl_F-006.md -->
# F-006 · Nombrado y archivo en SharePoint — Informe de implementación

> Rama `feature/F-006-sharepoint`. Rigor **`critico`**: fase RED con traza
> real pegada, cobertura de líneas cambiadas y campaña de mutación con cero
> supervivientes.
>
> Este informe se escribe **conforme avanza el trabajo**, no al final.
>
> **Ni un dato real.** Todos los códigos y nombres que aparecen aquí
> (`0677`, `RS26.08/0123`) son **inventados**, los mismos que usa la spec.
> Ningún identificador de tenant, sitio, drive o aplicación entra en este
> fichero ni en ningún otro del repositorio.

---

## 0 · Las cuatro decisiones del humano del 2026-08-20 que modifican la spec

La spec de F-006 se escribió el 2026-08-19 y se aprobó. El **2026-08-20** el
humano tomó cuatro decisiones que la modifican. Se aplican tal cual y se dejan
escritas aquí, con su fecha, porque la spec no se reescribe.

### D-a · El cliente HTTP es `httpx`, no `msal` + `requests` (2026-08-20)

**Qué cambia**: **T8**. `design.md` §3.2 y la tarea T8 proponían
`msal>=1.28,<2.0` y `requests>=2.31,<3.0`. Era la decisión abierta **D1** de
`design.md` §10 («qué librería de Graph reutilizar»), declarada **no
bloqueante** precisamente porque el puerto aísla al resto del servicio.

**Lo decidido**: el servicio no tiene hoy ningún cliente HTTP, y el repositorio
`partes` ya resuelve esto **en producción** con `httpx`. El humano eligió
alinearse con él. Se declara `httpx` en
`services/postventa-api/requirements.txt` con su rango de versión, al estilo de
las demás dependencias.

**Consecuencia**: cambia **solo `infrastructure/sharepoint/`**, que es
exactamente lo que `design.md` §10 (D1) predijo. Ni el dominio, ni la
aplicación, ni el borde HTTP se enteran. El test de arquitectura R22 ya
vigilaba `httpx` junto a `msal` y `requests`, así que tampoco cambia.

*(La lectura crítica del patrón de `partes` —qué se reutiliza y qué defectos
suyos NO se heredan— está en la sección **T8** de este informe.)*

### D-b · T19 queda N/A (2026-08-20)

**Qué cambia**: **T19**. La tarea pedía copiar la sección nueva de
`docs/INTEGRACION.md` a `azure-apps/postventa_incidencias.md`.

**Lo decidido**: el humano **no hace commits en `azure-apps`**. T19 no es una
tarea pendiente: es una tarea que **ya no aplica**. Se marca **N/A** en
`tasks.md` con esta decisión y su fecha escritas en la propia tarea.

**Lo que NO cambia**: **T15** sí se hace. `docs/INTEGRACION.md` vive en este
repositorio, es la fuente de verdad de lo que consumimos y R32 lo exige.

### D-c · Riesgo aceptado de permisos de Graph, documentado en `design.md` (2026-08-20)

**Verificado en Azure el 2026-08-20**: el app registration del proyecto tiene
consentimiento de administrador para **tres** permisos de aplicación de Graph:
`Sites.Selected` (el que pedía la spec), `Sites.ReadWrite.All` y
`Sites.FullControl.All`. Los dos últimos alcanzan a **todos** los sitios de
SharePoint del tenant y vuelven irrelevante al primero; `Sites.FullControl.All`
es más amplio incluso que `Files.ReadWrite.All`, que la propia spec descartó
por excesivo.

**Lo decidido**: arrancar F-006 con los permisos actuales y **recortar
después**, en **F-018 · Mínimo privilegio en Graph** (ya dada de alta en
`harness/features.json`, prioridad 18), para no mezclar un cambio de
configuración del tenant con una implementación. El recorte lo ejecuta el
humano en Azure: un agente no toca permisos del tenant.

**Dónde queda escrito**: sección nueva en `design.md` §9 (riesgo aceptado, con
fecha y citando a F-018) y en la sección de permisos de `docs/INTEGRACION.md`
(T15). **Ningún appId ni identificador** entra en ningún fichero del
repositorio.

### D-d · D6 está resuelta (2026-08-20)

`design.md` §10, **D6** —«nadie ha creado todavía la biblioteca de dev ni el
app registration»— era la única decisión abierta **bloqueante**, y bloqueaba
T17 y T18.

**Lo decidido/verificado**: la biblioteca, el app registration y los permisos
**ya existen**. Por tanto:

- **T17** deja de estar bloqueada y pasa a ser **ejecutable**: se prepara con
  su script y su comando exacto para que la ejecute el humano.
- **T18 sigue DIFERIDA a F-010** por la decisión **D3** del **2026-08-19**
  (opción (a)): no depende de D6 sino del entorno desplegado, que no existe
  hasta F-010. **No se toca.**

---

## Estado de las tareas

| Tarea | Estado |
|---|---|
| T1 · precondición (F-004 y F-005 en `dev`, rama rebasada) | ✅ hecha por el líder, verificada aquí |
| T2 · RED nombrado | ⏳ |
| T3 · `domain/models/nombrado.py` | ⏳ |
| T4 · RED paso de archivo + dobles | ⏳ |
| T5 · puerto + paso de archivo | ⏳ |
| T6 · RED fábrica | ⏳ |
| T7 · ajustes + fábrica | ⏳ |
| T8 · `httpx` en `requirements.txt` (D-a) | ⏳ |
| T9 · RED adaptador Graph | ⏳ |
| T10 · adaptador Graph | ⏳ |
| T11 · RED borde HTTP | ⏳ |
| T12 · borde HTTP | ⏳ |
| T13 · RED arquitectura (por rotura deliberada) | ⏳ |
| T14 · `docs/ARCHITECTURE.md` | ⏳ |
| T15 · `docs/INTEGRACION.md` | ⏳ |
| T16 · scripts de `infra/` | ⏳ |
| T17 · MANUAL (humano), ya ejecutable (D-d) | ⏳ |
| T18 · MANUAL (humano), DIFERIDA a F-010 (D3, 2026-08-19) | queda `[ ]` a propósito |
| T19 · N/A (D-b, 2026-08-20) | N/A |
| T20 · campaña de mutación | ⏳ |
| T21 · `bash harness/init.sh` en verde | ⏳ |

---

## T1 · Precondición: F-004 y F-005 en `dev`, rama al día

Hecha por el líder antes de lanzar esta implementación. **Verificada aquí**,
que es lo que pedía la tarea:

```
$ git log --oneline dev | head -8
f2e317b F-005: cierre documental y alta de F-018
7c57e52 F-005: persistencia en el PostgreSQL compartido (squash)
e3f5fcd Traer F-004 a la rama de F-005
62e91ed Merge F-004: validacion del parte y clasificacion de la firma
bb3ae58 F-004 CERRADA: revision APROBADA y cierre documental
...
```

Los cinco símbolos que F-006 consume de las dos features importan:

```
$ cd services/postventa-api
$ .venv/Scripts/python.exe -c "from domain.models.validacion import Destino, Veredicto; from domain.models.persistencia import TrazaArchivo, EstadoArchivo; print('ok')"
ok
```

Y el arnés arranca en verde sobre la rama:

```
$ bash harness/init.sh
[OK] Arnés v1.5.2 (2026-08-18)
...
[OK] servicio api (services/postventa-api): pytest en verde
[OK] PUERTA COBERTURA: N/A (F-006 no cambia líneas Python de producción frente a dev)
[OK] Rama actual: feature/F-006-sharepoint
ENTORNO LISTO. Puedes trabajar.
```

**No** se ha inventado ningún modelo gemelo: `ResultadoValidacion`, `Destino`,
`TrazaArchivo`, `EstadoArchivo` y `RepositorioPartesPort.guardar_archivo` se
consumen tal cual los dejaron F-004 y F-005 (`design.md` §1).
