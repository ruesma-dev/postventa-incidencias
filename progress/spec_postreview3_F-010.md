<!-- progress/spec_postreview3_F-010.md -->
# F-010 · Corrección de spec tras la review 3 (§9.2)

- **Rama:** `feature/F-010-despliegue` · **Fecha:** 2026-08-26 · Rol:
  `spec-author`.
- **Origen:** punto **9.2** de `progress/review3_F-010.md`, reportado antes
  como residuo en `progress/impl_defectos13-15_F-010.md`.
- **Alcance:** dos ficheros de `specs/F-010-despliegue/`. **Ni código, ni
  tests, ni `infra/`, ni `tasks.md`.** Nada ejecutado contra Azure, SharePoint
  ni PostgreSQL. Ninguna URL, GUID ni identificador entra al repositorio.

## El hecho que invalidaba la spec

Desde que la Function App es **backend enlazado** de la Static Web App, la
plataforma le activa Easy Auth y el backend solo acepta lo que entra por el
proxy del front. Su nombre de host devuelve
`400 Login not supported for provider azureStaticWebApps` a **toda** ruta,
`GET /api/health` incluida. La vía que sí funciona —y con la que se completó
T18 con dos `200`— es `/api/archivar` desde la consola del navegador en el
front, con sesión iniciada y mismo origen: `docs/DESPLIEGUE.md` §5 bis.

## Cambio 1 · `requirements.md` — R29

**Antes** decía que T18 de F-006 se ejecuta con
`infra/verificar_archivo_dev.ps1 -BaseUrl <url del despliegue>`. Ese mecanismo
no funciona.

**Ahora** R29 mantiene lo que siempre garantizó —que existe una forma de
ejercitar la subida real **solo desde el entorno desplegado**— y cambia por
dónde se entra: por el front, con sesión, desde la consola y contra la ruta
relativa `/api/archivar`, sin ninguna URL que escribir, con el procedimiento
en `docs/DESPLIEGUE.md` §5 bis. Formato EARS conservado (`CUANDO … el sistema
debe …`) y verificación `MANUAL (humano)` intacta.

Bajo el requisito queda una nota que dice por qué **no** por el host de la
Function, y que el script **no se retira**: sigue valiendo el día que el
backend vuelva a ser alcanzable por su host —su listado de la carpeta en solo
lectura no depende del proxy— y ahora reconoce ese `400`, explica la vía buena
y sale con código propio en vez de morir con un error opaco.

**Tabla de trazabilidad, fila R29**: sigue apuntando a T18 como `MANUAL
(humano)`, y añade los tests de contrato que ya existen sobre el script
(`test_f010_scripts_infra.py`, los cuatro `defecto13`). No se promete ningún
test que no esté escrito.

## Cambio 2 · `design.md` — la fila del verificador

La fila de `infra/verificar_archivo_dev.ps1` estaba en **§6.3, ficheros que NO
se tocan**, con la frase «Se ejecuta en T18, no se modifica». **Se modificó**,
en el commit `7ff86d7`.

Se mueve a **§6.2, A modificar**, que es donde dice la verdad, marcada como
corrección de este diseño, con el commit, el motivo (el `400` del backend
enlazado y el traslado de T18 a la consola del front, R29) y por qué el script
se conserva. Ninguna otra fila de las dos tablas tocada.

## Verificación

- `bash harness/init.sh` **en verde**, tal cual, al terminar: `PUERTA
  COBERTURA [OK] 98.5%`, `17 passed` en el arnés y los dos servicios en verde.
- Ningún test lee `specs/F-010-despliegue/`: `grep -rln "F-010-despliegue"`
  sobre `services/*/tests` y `tests/` no devuelve nada. Los cuatro tests
  `defecto13` que ahora cita la trazabilidad **existen** y están verdes
  (`test_f010_scripts_infra.py:1117,1127,1140,1151`).

## Decisiones abiertas para el humano

- Ninguna nueva. Los otros dos puntos del rechazo —**§9.1**, el test de
  contrato de `staticwebapp.config.json`, y **§9.3**, los «once secretos» de
  `infra/cargar_secretos_postventa.ps1`— son del `implementer` y quedan fuera
  de este encargo; §9.3 necesita permiso del humano para tocar `infra/`.
- **`progress/review3_F-010.md` está sin versionar** en el árbol. No es de este
  encargo y no lo he tocado, pero C5 exige `git status` limpio: alguien tiene
  que commitearlo antes de cerrar.
- Sigue sin resultado anotado **T14 bis** (tope de gasto y alerta), que es del
  humano y no bloquea el cierre según §7 de la review.
