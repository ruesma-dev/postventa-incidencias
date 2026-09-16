<!-- progress/propuesta_C5_F-017.md -->
# Insumo para F-017 · la excepcion de C5 para cierres con verificaciones abiertas

> **Esto NO esta aplicado.** El humano decidio el **2026-09-16** dejar F-017 en
> el backlog y no tocar `CHECKPOINTS.md` hoy. Este documento existe para que
> quien ejecute F-017 no vuelva a empezar de cero: trae los casos reales, la
> redaccion ya corregida y lo que hay que descartar.
>
> Origen: al cerrar F-009 (2026-09-16) el reviewer propuso la mejora por su
> cuenta, sin saber que F-017 ya existia. Su texto original esta en
> `progress/review_cierre_F-009.md` §9; el de aqui lo corrige.

## 1 · El problema, con los cuatro casos

`CHECKPOINTS.md` C5 (lineas 223-228) exige en su primera vinuta «todas las
tareas `[x]`». No contempla el cierre honesto con huecos documentados, asi que
**cada reviewer resuelve la excepcion a mano**. Ya han divergido:

| Feature | Fecha | Como se resolvio |
|---|---|---|
| F-003 | 2026-08-19 | Caso que dio origen a F-017 |
| F-006 | — | Idem |
| F-012 | 2026-09-11 | `review_F-012.md` §C5: «no un rechazo, **segun el encargo**». Cerro con **13 casillas `[ ]`**, quedo `in_progress` y el lider la paso a `done` despues |
| F-009 | 2026-09-16 | `review_cierre_F-009.md` §7 C5: usa `[~]` y otro razonamiento. Va a `done` directo |

Dos features, dos criterios, dos estados finales distintos. El riesgo no es
teorico: ya se materializo.

Matiz que ni C5 ni la propuesta original recogen: las 13 casillas de F-012
mezclan **precondiciones P0-P7** (que nunca son tareas de agente) con **tareas
T26-T31 no ejecutadas**. No es lo mismo y C5 no lo distingue.

## 2 · Redaccion propuesta (sustituye al primer punto de C5)

Corrige tres agujeros del texto original del reviewer, senalados abajo.

> - [ ] `tasks.md` con todas las tareas `[x]` y un commit `F-XXX Tn: ...` por
>   tarea. **Excepcion tasada — cierre con verificaciones abiertas.** Una tarea
>   puede quedar `[ ]` al cerrar **solo si es una verificacion `MANUAL
>   (humano)`, una precondicion externa o una tarea bloqueada por un tercero**:
>   una tarea de agente sin ejecutar es trabajo incompleto y sigue siendo
>   CHANGES_REQUESTED. Y solo si ademas: (a) hay **decision escrita y fechada
>   del humano**, citada literal; (b) cada hueco consta **uno a uno, con su
>   requisito y su motivo**, en un acta bajo `progress/`; (c) la `description`
>   de la ficha en `features.json` remite a esa acta —no `blocked_by` ni
>   `acceptance`, que no llegan a `BACKLOG.md`—; y (d) **todo hueco recuperable
>   tiene ficha propia en el backlog**, citada en el acta. El reviewer
>   **comprueba las cuatro y las enumera** en su informe. Si falta una, el `[ ]`
>   es CHANGES_REQUESTED.

### Los tres agujeros que corrige

1. **«Quien puede tomarla» no esta definido en ningun sitio del arnes.** Ni el
   `CLAUDE.md` de aqui ni el de `arnes-base` definen «responsable» ni ninguna
   figura de autoridad; el termino de todo el arnes es **«el humano»**. Dejarlo
   vago invita a que un agente se autoconceda la autoridad.
2. **Faltaba la distincion agente / no-agente**, que es justo lo que el criterio
   1 de F-017 ya pedia. Sin ella la clausula es la puerta por la que toda
   feature se cierra a medias: basta un «cierrala» y un acta bien escrita.
3. **Faltaba la ficha de deuda con id propio.** Escribir el hueco no lo mantiene
   vivo; una ficha en el backlog si. Es lo que hizo bien el cierre de F-009 con
   **F-029**, y F-012 con F-025/F-026.

El criterio 2 de F-017 —que el motivo se vea sin depender de una nota en
`progress/`— **ya esta resuelto de hecho**: la constancia va en `description`,
que es lo unico que `harness/backlog.py::construir()` proyecta a `BACKLOG.md`.

## 3 · Lo que NO hay que hacer: el apunte de C4 bis

El reviewer propuso ademas que C4 bis admitiera el nº de workers de la campana
de mutacion en `tasks.md` o en el commit cuando el informe sea anterior a la
1.7.8. **Descartado, y conviene que siga descartado:**

- **El dato esta mal.** La fila «Workers» existe en `arnes-base` **desde la
  1.7.2**, no desde la 1.7.8 (`arnes-base/CHECKPOINTS.md` linea 222). El
  «anteriores a la 1.7.8» solo vale para la importacion local de este repo.
- **Cubre una ventana de 18 minutos** irrepetible (informe de F-009 a las 14:05,
  commit a las 14:23 del mismo dia). De los 14 `progress/mutacion_F-*.md`, 10 no
  llevan la fila y todos son de features ya cerradas y revisadas.
- **Es lo unico de todo esto que puede romper tests en `arnes-base`**, que
  trocea C4 bis por cabeceras (`test_documentos_del_arnes.py:109,139,157`) y por
  literales dentro de RM2 (`test_mutacion_honestidad.py:432ss`).

Anadir una via alternativa de evidencia debilita un checkpoint que hoy es
tajante, a cambio de un fosil. Lo correcto es lo que ya se hizo: citar el hueco
en el informe de review.

## 4 · Que hay que tocar cuando se ejecute

**En este repo:** `CHECKPOINTS.md` (C5), `.claude/agents/reviewer.md` (su linea
31 repite la regla y quedaria contradiciendo a C5), `harness/features.json`
(cerrar F-017) y `BACKLOG.md` **regenerado**, nunca a mano. Unas 25 lineas
netas.

**En `arnes-base` (regla de propagacion, en el mismo trabajo):**
`CHECKPOINTS.md`, `.claude/agents/reviewer.md`, `GUIA_INSTALACION.md` (cada
version anade su seccion) y `harness/VERSION` (1.7.10 -> 1.7.11).

Tres avisos para ese trabajo:

- **C5 es hoy la unica seccion identica en los dos repos** (`arnes-base` lineas
  291-296): el cambio aplica limpio y literal. C3, C4, C4 bis y el nivel por
  defecto ya divergieron. El coste de portar no volvera a ser tan bajo.
- **Aqui NO se sube `harness/VERSION`**: esta en 1.5.2 a proposito, con parches
  a mano (ver `harness/ARNES_VERSION.md`). La entrega generica y el parche local
  son **dos trabajos distintos** aunque vayan en el mismo encargo.
- `politica_ficheros.json` clasifica `CHECKPOINTS.md` como `adaptado`
  («conservar por defecto»): el instalador no lo propaga solo, hay que portarlo
  a mano.

**Riesgo tecnico, bajo.** En este repo ningun test parsea `CHECKPOINTS.md`;
`harness/init.sh` solo comprueba que existe (linea 100) y busca la marca
`[ADAPTAR]` (linea 473). El riesgo real es de proceso: que la clausula se use
como atajo. Lo conjuran las condiciones (a)-(d) y, sobre todo, la acotacion a
tareas que un agente no puede ejecutar.
