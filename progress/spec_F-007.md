<!-- progress/spec_F-007.md -->
# F-007 · Front de carga y revisión — Informe del spec-author

**Fecha**: 2026-08-20 · **Rigor**: `estandar` · **Rama de trabajo**: worktree
aislado `agent-afaf7200115407387` (el humano estaba mergeando F-006 en el
árbol principal; dos operaciones de git sobre el mismo árbol se pisan).

**Entregado**: `specs/F-007-front/requirements.md`, `design.md` y `tasks.md`.
**No se ha escrito ni una línea de código** ni se ha tocado nada fuera de
`specs/F-007-front/` y de este informe.

> **`progress/current.md` NO se ha tocado a propósito.** Lo está usando el
> cierre de F-006 en el árbol principal y editarlo desde aquí produciría un
> conflicto. El líder copia de aquí lo que necesite.

## Base sobre la que se ha diseñado

El worktree venía posicionado en `main` (`bc7350c`), que trae un
`features.json` con una sola feature de plantilla. Se reposicionó en
`feature/F-006-sharepoint` (`73bba0f`), que es lo último real, para leer el
estado verdadero del proyecto: los 18 features, los seis endpoints cerrados
(F-002 … F-006) y el arnés 1.5.2.

Leído antes de diseñar: `specs/SPECS.md`, `docs/ARCHITECTURE.md`,
`docs/CONVENTIONS.md`, `CHECKPOINTS.md`, `harness/{init.sh, cobertura.py,
alcance.py, servicios.py, servicios.json, rigor.json, mutacion.py}`,
`tests/test_servicios_declarados.py`, los seis handlers de
`interface_adapters/api/`, `function_app.py`, el esqueleto del front en
`feature/F-007-front` y el patrón de `front-nominas`.

## Las tres trampas del enunciado, resueltas

### 1 · Concurrencia — límite **3 partes** (= 6 peticiones vivas)

Cinco argumentos, todos con número, en `design.md` §5: 22 partes × 2 llamadas
de IA = 44 llamadas por remesa; 3 × 2 = 6 es el tope de conexiones por origen
de un navegador sobre HTTP/1.1 (lo que sirve `dev_server.py`), así que pedir
más solo encola **invisiblemente** mientras corre el temporizador; `func
start` levanta un solo worker en local; 44 llamadas multimodales de golpe son
un 429 casi seguro; y con 3 la barra de progreso avanza de verdad.

Se implementa como `ejecutarConLimite(tareas, limite)` en `js/cola.js`, pura y
sin DOM, y **la misma cola sirve para la fase de archivo**. Descartado
`Promise.all` por lotes: cada lote iría al ritmo del parte más lento.

### 2 · «Nadie comprueba el front» — con qué se prueba

`node --test` (viene **dentro** de Node 18+; aquí hay Node 24) para el
JavaScript, sin `package.json`, sin `npm install` y sin `node_modules`; y
**pytest** para `dev_server.py`, para el contrato de los ficheros estáticos y
como **puente** que lanza `node --test` y **falla si `node` no está** (nunca
un `skip` silencioso). El front se declara como un servicio `python` en
`harness/servicios.json`, así que el portero ejecuta una sola suite.

Descartados Playwright / Jest / Vitest / navegador headless: desproporcionados
para rigor `estandar` y para una pantalla cuya lógica se ha sacado a propósito
del DOM. Lo que queda fuera lo cubre la verificación MANUAL (T14).

**Detalle que ya juega a favor**: `tests/test_servicios_declarados.py` (raíz)
falla en cuanto `services/postventa-front/` vuelva al árbol sin estar
declarado. El criterio de aceptación 5 ya tiene guardián; ese rojo es la fase
RED de T1.

### 3 · `dev_server.py` y la puerta de cobertura

`harness/alcance.py` trata como producción **cualquier `.py`** fuera de
`tests|specs|progress|docs`, y `dev_server.py` entra **entero como fichero
nuevo** frente a `dev`: **no existe la opción de no tocarlo**.

Cinco opciones evaluadas con su coste en `design.md` §9 (probarlo /
exclusiones configurables en el arnés / esconderlo en una carpeta excluida /
adelgazarlo / cerrar en rojo). **Recomendación clara: probarlo (O1)**, porque
cierra a la vez los criterios 5 y 6, no toca el arnés genérico —que es otro
producto, `arnes-base`, con regla de propagación propia— y no abre la puerta
de «si no lo puedes probar, decláralo script de desarrollo». Además
`dev_server.py` es lo único que reproduce en local el proxy de la Static Web
App: es código que **merece** tests.

## Decisiones abiertas (ninguna bloquea)

| | Qué | Recomendación |
|---|---|---|
| **D1** | Trato de `dev_server.py` frente a la cobertura | **O1**, probarlo |
| **D2** | Valor del límite de concurrencia | **3** partes |
| **D3** | Confianza de un campo corregido a mano | **100**, marcado como editado. Si no, corregir un campo no serviría para nada |
| **D4** | **La remesa no se persiste**: recargar la pestaña pierde el trabajo | Aceptarlo en el piloto y dar de alta una feature de endpoints de persistencia en `postventa-api` |
| **D5** | Navegador soportado | Edge/Chrome (`webkitdirectory`) |

**D4 es la que más conviene mirar antes de enseñar el front a Posventa.**
F-005 dejó `RepositorioPartesPort` con `guardar_remesa`, `guardar_parte`,
`guardar_validacion` y `cola_validacion_humana`, pero **el único endpoint que
escribe hoy es `/api/archivar`** (su traza). No hay forma de persistir la
remesa ni la cola de validación humana, así que la cola guardada entre
sesiones no puede existir todavía. Es del servicio `postventa-api`, no del
front: **no se ha implementado aquí** (límite de microservicio).

## Datos personales

Ni un dato real en la spec: `0677` y `RS26.08/0123` son inventados y van
marcados como tales. En pantalla **sí** se enseñan DNI y observaciones —quien
revisa los necesita delante—, pero R28–R30 los prohíben en consola,
`localStorage`, `sessionStorage`, URL y fixtures, y `/api/archivar` recibe
solo cinco campos, ninguno personal (el backend ya lo impone). El único
registro que el front puede emitir pasa por `js/traza.js`, que acepta cuatro
claves y tira el resto: es un filtro con test, no una buena intención.

## Forma de la spec

- **37 requisitos EARS** numerados, con tabla de trazabilidad requisito →
  test al final de `requirements.md`.
- **16 tareas**, una por commit, **5 con fase RED** y **una `MANUAL
  (humano)`** (T14) con sus comandos de PowerShell en líneas cortas, sin
  `&&`, más el script `dev_front.ps1`.
- Proporcionado a `estandar`: no se exigen cero supervivientes de mutación ni
  fase RED en todo.

## Qué necesita el humano decidir o saber

1. **D1 a D5** de arriba (ninguna bloquea; con silencio se implementa la
   recomendación).
2. **T14 es suya**: es la única verificación que exige levantar `func start` y
   un navegador. Ojo al puerto: `func start --port 7073`, que **no** es el de
   por defecto de `func`.
3. **En local, archivar responde 503 y eso es lo correcto.** La puerta de
   entorno de F-006 está apagada por defecto y **no se toca** para «probar».
