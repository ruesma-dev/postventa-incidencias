<!-- progress/review_F-005.md -->
# F-005 · Persistencia en el PostgreSQL compartido — informe de review

> Rama `feature/F-005-persistencia` (HEAD `ba56704`). Revisado el 2026-08-19.
> Contrato: `specs/F-005-persistencia/` (los tres ficheros), `CHECKPOINTS.md`,
> `docs/CONVENTIONS.md` y las reglas duras de `CLAUDE.md`.
>
> **Ni un dato real en este informe.** El único identificador con forma de DNI
> que aparece es `00000000T`, un número no emitido y de uso convencional.

## Veredicto

**APPROVED (APROBADO)** — segunda pasada, 2026-08-20.

Los dos cambios que requerí en la primera pasada están aplicados y
**verificados uno a uno por mí** (sección «Segunda pasada»). La feature queda
aprobada, con **una condición de merge** que el líder no debe pasar por alto
—es de estrategia de merge, no de código— y con la deuda de T26 anotada.

> **Historial de la primera pasada (2026-08-19): CHANGES_REQUESTED.** Se
> conserva íntegro más abajo porque es el rastro de qué se pidió y por qué. Los
> dos cambios requeridos fueron: (1) sacar de git el FQDN real del servidor
> compartido, y (2) decidir por escrito qué se hace con el valor crudo del
> modelo en `avisos` (la observación O1 heredada de F-004).

Lo que dije en la primera pasada y sostengo ahora con más motivo: **esta
feature es, con diferencia, la mejor verificada del proyecto hasta hoy**. Cero
supervivientes de mutación comprobados por mí, 97 % de cobertura de lo
cambiado, fases RED con traza real, controles negativos en los dos barridos de
dato personal, una guarda de DDL construida como lista blanca y no como lista
negra, y las tres manuales ejecutadas de verdad contra Docker y contra el
servidor real.

### Condición de merge (para el líder)

**El árbol está limpio, pero el historial de la rama no.** El arreglo del FQDN
cambia el fichero en `HEAD`; los **24 commits anteriores de la rama** siguen
conteniendo el valor, porque eso es precisamente lo que significa que el
historial de git no suelta lo que entra.

- **Preferible: merge con squash** a `dev`. Con un solo commit del árbol final,
  el valor no entra nunca en `dev`.
- **Si se hace un merge normal**, el valor entra en el historial de `dev`. Mi
  valoración honesta de la gravedad de ese caso está en «Segunda pasada §1»:
  es **baja**, y no lo convierto en bloqueo.

Lo que **no** propongo es reescribir la historia de una rama de 31 commits: el
coste y el riesgo superan con mucho al beneficio, por las razones que explico
abajo.

## Nivel de rigor y puertas que exige

`harness/features.json` declara `"rigor": "critico"` para F-005. Es el nivel
más exigente y el correcto para esta feature: infraestructura **compartida**
con la producción de otros tres proyectos y dato personal directo en base.

Según `harness/rigor.json` y la tabla de `CHECKPOINTS.md`, `critico` exige:

| Puerta | Exigida | Estado |
|---|---|---|
| Fase RED en los requisitos centrales | sí | **cumplida**, con traza real pegada |
| Cobertura de las líneas cambiadas ≥ 80 % | sí | **97,0 %** (573/591), `[OK]` |
| Campaña de mutación | sí | 104 mutantes, verificados por mí |
| Cero supervivientes sin justificación escrita | sí | **0 supervivientes** |
| Manuales listadas con comando exacto y resultado real | sí | las tres, con salida real |

## Lo que he ejecutado yo (no me he fiado del informe)

- **`bash harness/init.sh`**, tal cual, sin pipes ni decoración → exit 0,
  `ENTORNO LISTO`, `PUERTA COBERTURA: 97.0% de 591 líneas cambiadas cubiertas
  (573/591, umbral 80%, nivel critico)`.
- **La suite del servicio, relanzada por mí** para no depender de la caché del
  portero (`init.sh` la dio por buena con «caché: árbol sin cambios»):
  `./.venv/Scripts/python.exe -m pytest -q` → **678 passed, 10 skipped in
  23.84s**. Coincide con lo que declara el informe.
- **Recálculo independiente del alcance y del número de mutantes** con
  `harness.alcance` y `harness.mutacion.generar_mutantes` (cálculo puro).
- **Verificación empírica de los tres timeouts**, cargando `ddl.py` mutado en
  un espacio de nombres aparte y bajo reloj.
- **Barrido propio de DNI/NIE** sobre todos los ficheros del diff.
- **Barrido propio de secretos** (FQDN de Azure, `password=`, GUID, IPv4).
- Comprobación del historial de git en busca de PDF u ofimática versionados.

## Checkpoints

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0. Verificado por mí.
- [x] Existen los nueve ficheros obligatorios. Los lista el propio `init.sh`.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: `['F-005']`.
- [x] Rama actual `feature/F-005-persistencia`, la de la feature en curso.
- [x] `progress/current.md` describe solo la sesión activa de F-005.
- [x] Toda feature `done` (F-001 a F-004) tiene su resumen en
      `progress/history.md`. Comprobado: las cuatro aparecen.

### C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal respetada.** `grep` de imports sobre `domain/` y
      `application/` no encuentra ni `psycopg` ni `infrastructure`. Las dos
      apariciones de «psycopg» en `domain/` son **prosa** de docstring
      (`domain/models/persistencia.py:4`, `domain/ports/persistencia.py:10`).
      Ningún SQL fuera de `infrastructure/persistencia/`.
- [x] **Primera línea con la ruta relativa** en los 34 `.py` del diff.
      Comprobado fichero a fichero: cero fallos.
- [x] **Sin secretos hardcodeados.** En la primera pasada **fallaba**
      (`tests/test_f005_conexion.py:65` metía en git el FQDN real del servidor
      compartido). **Corregido en `9284e79` y verificado por mí**: en `HEAD` no
      queda ninguna aparición en todo el árbol, y `.env` —que sí lo tiene, como
      es su función— está en `.gitignore` y sin trackear. Queda la condición de
      merge sobre el historial de la rama, arriba. Sin `print()` de debug en
      producción (verificado) y sin dependencias nuevas fuera de lo previsto
      (`psycopg` estaba en la spec, T3).
- [x] La unidad de trabajo es el **parte**: la clave primaria es
      `hash_parte`, no el fichero (R13, `03_partes.sql`).
- [x] Nada se archiva ni se cierra sin validar; F-005 no escribe en Sigrid.
- [x] Lo manuscrito no se descarta: `dni_cliente` y `observaciones` se
      persisten con su `confianza_pct`.
- [x] «Firmado no es conforme» lo sostiene el `CHECK` de `destino` en
      `04_validaciones.sql`, comparado contra los `Enum` del dominio por test.
- [x] **Reprocesar no duplica**: R13–R17, con la comprobación contra motor
      real en M1 y M2.
- [x] Ningún estado de Sigrid hardcodeado: F-005 no toca Sigrid.
- [x] **Ningún PDF ni documento con datos personales en el historial.**
      Verificado con `git log --all --diff-filter=A`: cero `.pdf`, `.docx`,
      `.xlsx`, `.pptx`.

### C3 bis — Documentos que entran de fuera

**N/A, justificado**: F-005 no añade ni modifica ningún fichero en
`docs/referencia/`. `docs/INTEGRACION.md` es documentación **producida por
este proyecto**, no un documento que llegue de fuera, así que no le aplica la
plantilla de origen y fecha de `docs/referencia/README.md`.

Aun así he pasado mi propio barrido de secretos sobre él —FQDN de Azure,
GUID, `VARIABLE=valor`, `password=`, URI con credencial, IPv4 no local— y
**está limpio**.

### C4 — La verificación es real

- [x] **Cada requisito EARS tiene test y todos pasan.** Tabla completa abajo.
      Cuatro requisitos (R32, R33, R34, R40) no tienen test con el nombre
      `test_f005_rN_*` pero sí cobertura real por mecanismo o por tests de su
      requisito gemelo; queda detallado en la tabla y lo doy por trazable.
- [x] **Los unit tests no tocan red ni BBDD.** Lo garantiza el fixture de
      sesión `sin_red` de `services/postventa-api/tests/conftest.py`, que
      sustituye `socket.socket.connect` durante toda la sesión. No es una
      promesa: es imposible abrir una conexión.
- [x] Las verificaciones `MANUAL (humano)` estaban listadas en
      `progress/current.md` con su comando exacto, y las tres se han
      ejecutado (T24, T25) o resuelto parcialmente por decisión del humano
      (T26).

### C4 bis — El rigor declarado se cumple

- [x] **La feature declara `rigor`** con valor válido: `critico`.
- [x] **Fase RED.** El informe trae cuatro trazas reales, no resúmenes:
      RED 1 (T5, `ModuleNotFoundError: No module named
      'domain.ports.persistencia'`), RED 2 (T8, el módulo de la guarda del
      DDL no existía), RED 3 (T19, el caso que `CHECKPOINTS.md` contempla
      cuando el entregable **es** el test: se rompió a propósito lo vigilado
      y se pegó el fallo con el valor filtrado), y RED 4 (T22, el barrido
      escrito antes que el documento). Las cuatro son salida de consola.
- [x] **Cobertura.** `PUERTA COBERTURA` en `[OK]` con 97,0 %, muy por encima
      del umbral del 80 %.
- [x] **Mutación, verificada de forma independiente por mí.** Recalculé el
      alcance con `harness.alcance` y el número de mutantes con
      `harness.mutacion.generar_mutantes` (cálculo puro, sin ejecutar la
      suite ni escribir en disco). Coincide **exactamente**, fichero a
      fichero:

      | Métrica | Informe | Mi recálculo |
      |---|---|---|
      | Ficheros en alcance | 14 | **14** |
      | Líneas en alcance | 2206 | **2206** |
      | Mutantes generados | 104 | **104** |
      | Ref. base del diff | `e3f5fcda…` | **`e3f5fcda…`** |

      **Segunda pasada**: la campaña se relanzó tras tocar producción y la
      volví a recalcular. También coincide exactamente:

      | Métrica | Informe | Mi recálculo |
      |---|---|---|
      | Líneas en alcance | 2242 | **2242** |
      | Mutantes generados | 106 | **106** |
      | Muertos / supervivientes / timeouts | 103 / **0** / 3 | — |
      | Tiempo total | 330,4 s (5,5 min) | — |

      La campaña **no declara cero mutantes**, así que no procede la prueba de
      control sobre la exclusión de alcance.

- [x] **Los muertos, comprobados.** El informe declara un «Tiempo total» de
      **395,0 s = 6,6 minutos**, **por encima del umbral de 5 minutos** de
      C4 bis, así que la reejecución de la campaña **no es obligatoria** y
      vale el recálculo puro. **Lo digo explícitamente, como exige el
      checkpoint: la campaña completa no se ha reejecutado hasta el final.**

      Aun así intenté reejecutarla (`--salida` a mi scratchpad, nunca a
      `progress/`). Se cortó en el mutante 25 de 104 por una caída de
      conexión ajena a la feature. Lo que alcanzó a evaluar —17 muertos, todos
      coherentes— no contradice el informe. **Un dato que sí merece anotarse**:
      esa ejecución parcial marcó como `timeout` seis mutantes que no pueden
      colgarse jamás (`_RECORTE = 80 -> 81`, `normalizado[1:-1] -> [1:-2]`…).
      Es decir, **la etiqueta `timeout` de la herramienta también se dispara
      por lentitud de la máquina bajo carga**, no solo por no-terminación. Eso
      no afecta al veredicto —los tres timeouts del informe los he verificado
      uno a uno por otra vía, ver abajo— pero es una limitación real de
      `harness/mutacion.py` que conviene conocer (observación O-C).

      Dejé el árbol como estaba: `git status` limpio y los 16 worktrees que
      creó mi campaña retirados con `git worktree remove`.

- [x] **Cada superviviente con su análisis completado.** **Cero
      supervivientes**, que es lo que `critico` exige. Ninguna sección en
      `PENDIENTE`. Los 31 supervivientes de la primera vuelta se mataron con
      tests, no se justificaron: el detalle de qué test mató a cuál está en
      el informe y es comprobable.
- [x] **Sección «Evidencias»** presente, con los cuatro números: tests
      (678 passed / 10 skipped), cobertura (97,0 %), mutantes y
      supervivientes (104 / 0) y tiempo de la suite (20,22 s).
- [x] Ningún punto de este bloque marcado N/A.

### C4 ter — Rutas sensibles

**N/A, justificado**: este repositorio **no tiene**
`harness/rutas_sensibles.json`, y sin esa declaración el bloque es N/A por la
propia redacción del checkpoint («Sin esa declaración este bloque es N/A y no
hay nada que justificar»). Lo verifiqué en el árbol, y además `init.sh` no
señaló ninguna ruta tocada.

No es un descuido: la decisión **D5** del humano, del 2026-08-19, es
explícitamente no declararlo en F-005 —hacerlo cambiaría el arnés para todas
las features y obligaría a portarlo a `arnes-base` en el mismo trabajo— y
deja `infrastructure/persistencia/sql/**` como candidato reconocido, con la
decisión asignada a **F-017**. Es una deferencia razonada y con dueño.

### C5 — La sesión se cerró bien

- [ ] **`tasks.md` con todas las tareas `[x]`.** → **T26 está `[~]`**, no
      `[x]`. Mi juicio detallado está en «El caso de T26» más abajo: lo
      considero **deuda aceptable con dueño, no un bloqueo**. Marco el
      checkbox vacío por honestidad con la letra del checkpoint, pero **este
      punto no es motivo del rechazo**. Las otras 27 tareas están `[x]` y
      cada una tiene su commit `F-005 Tn: ...`.
- [x] **Sin ficheros temporales ni artefactos sin trackear.** `git status`
      completamente limpio.
- [x] `features.json` refleja el estado real: `in_progress`. Correcto — el
      paso a `done` es del líder, después de este veredicto.

## Trazabilidad: requisito → test

| Req. | Cubierto por | Nº |
|---|---|---|
| R1 | `test_f005_r1_*` (`ddl_orden`, `ddl_seguro`) | 27 |
| R2 | `test_f005_r2_*` (`arranque`) | 3 |
| R3 | `test_f005_r3_*` (`ddl_seguro`, `ddl_idempotente_texto`) | 3 |
| R4 | `test_f005_r4_*` + M1/M2 contra motor real | 2 |
| R5 | `test_f005_r5_*` (`ddl_seguro`) | 8 |
| R6 | `test_f005_r6_*` (`ddl_seguro`) | 6 |
| R7 | `test_f005_r7_*` (incl. `bbdd_aislamiento`) | 5 |
| R8 | `test_f005_r8_*` (`conexion`, `bbdd_aislamiento`) | 10 |
| R9 | `test_f005_r9_*` (`conexion`, `bbdd_aislamiento`) | 11 |
| R10 | `test_f005_r10_*` (`arranque`) | 3 |
| R11 | `test_f005_r11_*` (`conexion`, `arranque`) | 8 |
| R12 | `test_f005_r12_*` (`ddl_seguro`, `sentencias`) | 5 |
| R13 | `test_f005_r13_*` (`repositorio`, `sentencias`) | 5 |
| R14 | `test_f005_r14_*` | 4 |
| R15 | `test_f005_r15_*` | 2 |
| R16 | `test_f005_r16_*` + `bbdd_reproceso` | 3 |
| R17 | `test_f005_r17_*` | 2 |
| R18 | `test_f005_r18_*` (`mapeo`) | 9 |
| R19 | `test_f005_r19_*` | 2 |
| R20 | `test_f005_r20_*` (`ddl_idempotente_texto`) | 10 |
| R21 | `test_f005_r21_*` | 3 |
| R22 | `test_f005_r22_*` (`repositorio`) | 11 |
| R23 | `test_f005_r23_*` | 5 |
| R24 | `test_f005_r24_*` | 2 |
| R25 | `test_f005_r25_*` | 3 |
| R26 | `test_f005_r26_*` | 3 |
| R27 | `test_f005_r27_*` (`preferencias`) | 10 |
| R28 | `test_f005_r28_*` (`preferencias`) | 3 |
| R29 | `test_f005_r29_*` (`logs_sin_datos_personales`) | 5 |
| R30 | `test_f005_r30_*` (`arquitectura`) | 12 |
| R31 | `test_f005_r31_*` (`arquitectura`) | 5 |
| R32 | **por mecanismo**: fixture de sesión `sin_red` en `tests/conftest.py`, que sustituye `socket.socket.connect` durante toda la suite. Más fuerte que un test: no es que ningún test abra red, es que **no puede**. | — |
| R33 | **por mecanismo**: marcador `requiere_base` (`skipif` sobre `POSTVENTA_PG_TEST_DSN`) en `tests_bbdd/tests/conftest.py`. Los 10 `skipped` de `init.sh` son la prueba viva. | — |
| R34 | **por mecanismo**: `dsn_de_pruebas()` hace `pytest.exit(returncode=1)` si el host no es local. Refuerzo: los 8 tests `test_f005_r11_*` de `es_host_local`, que es la función de la que depende. | — |
| R35 | `test_f005_r35_*` (`scripts_infra`) + salida real con Docker parado (exit 3) | 2 |
| R36 | `test_f005_r36_*` (`scripts_infra`) | 1 |
| R37 | `test_f005_r37_*` (`logs_sin_datos_personales`), con control negativo | 1 |
| R38 | `test_f005_r38_*` (`repo_sin_datos_personales`) | 6 |
| R39 | `test_f005_r39_*` | 1 |
| R40 | **por requisito gemelo**: es la misma prohibición que R12 aplicada al PDF. La cubren seis tests cuyo docstring cita «R12, R40» en `ddl_seguro`, `ddl_idempotente_texto`, `repositorio`, `sentencias` y `bbdd_ddl_idempotente`. | 6 |

Los cinco criterios `acceptance` de `harness/features.json` quedan cubiertos
por sus requisitos según la tabla de trazabilidad de `requirements.md`, y los
tres que necesitaban motor real (idempotencia, no duplicar, base efímera) están
además comprobados contra PostgreSQL 16 en M1 y contra la base real en M2.

## Los seis puntos que se me pidió mirar con lupa

### 1 · La campaña de mutación y el umbral de los 5 minutos

**Decidido y escrito**: el informe declara **395,0 s (6,6 min)**, por encima
del umbral de 5 minutos de C4 bis, de modo que **la reejecución no es
obligatoria** y el recálculo puro basta. La intenté igualmente y se cortó por
una caída de conexión; el árbol quedó limpio y sin worktrees míos. Consta
arriba, en C4 bis, con el detalle y con el hallazgo lateral sobre la etiqueta
`timeout` bajo carga.

### 2 · Los tres timeouts del troceador: el razonamiento se sostiene

Lo he verificado en tres pasos, y **ninguno de ellos consiste en creerme el
informe**.

**Paso 1 — ¿existen esos mutantes?** Regeneré los mutantes de `ddl.py` y
muestreé las tres líneas. Existen, con **el mismo operador y el mismo texto
original→mutado** que declara el informe:

| Línea | Operador | Original → mutado | ¿Coincide? |
|---|---|---|---|
| 131 | `entero` | `salto == -1` → `salto == -2` | sí |
| 158 | `aritmetico` | `posicion += 1` → `posicion -= 1` | sí |
| 162 | `aritmetico` | `posicion += 1` → `posicion -= 1` | sí |

**Paso 2 — ¿de verdad no terminan?** Cargué `ddl.py` con cada mutación
aplicada en un espacio de nombres aparte —sin tocar el repositorio— y llamé a
`sentencias()` bajo `timeout 15`, con el caso que el informe señala:

```
--- CONTROL: sin mutar, linea 131, caso con -- final ---
TERMINO: ('CREATE SCHEMA IF NOT EXISTS postventa',)
exit=0
--- MUTANTE 131: == -1 -> == -2 ---   exit=124
--- MUTANTE 158: += 1 -> -= 1 ---     exit=124
--- MUTANTE 162: += 1 -> -= 1 ---     exit=124
```

Los tres devuelven **124**, y el control sin mutar termina en menos de un
segundo. La no-terminación es real, no una excusa.

**Paso 3 — ¿esconden un agujero de cobertura?** No, y el razonamiento es el
inverso del que preocupa. Un mutante **superviviente** es peligroso porque
significa «lo cambié y nadie se enteró». Un **timeout** significa lo
contrario: la suite **sí entró por esa línea** y se quedó dando vueltas. Si
ningún test recorriera ese camino, el mutante habría terminado limpiamente y
habría salido como superviviente, no como timeout. El timeout es, por
construcción, prueba de que la línea está ejercitada.

Y verifiqué el matiz más fino, que es donde podía esconderse el truco: el
mutante de la línea 131 **solo** se cuelga si el `--` final no lleva salto de
línea detrás. Lo comprobé con las dos entradas:

```
--- MUTANTE 131 con salto de linea final (caso comun) ---
TERMINO: ('CREATE SCHEMA IF NOT EXISTS postventa',)   exit=0
```

Es decir: con la entrada corriente el mutante es **equivalente** y no se
distingue; solo el caso de borde lo delata. Que la campaña lo detectara
demuestra que **existe un test que ejercita ese borde exacto** — justamente
uno de los 13 que T23 añadió en `test_f005_ddl_troceado.py`. La explicación
del implementer sobre por qué apareció un tercer timeout al añadir tests
(«antes nadie entraba por ahí») queda confirmada.

**Conclusión: los tres timeouts no son supervivientes disfrazados y no tapan
ningún agujero.** Acepto los tres.

### 3 · T26 marcada `[~]`: deuda aceptable con dueño, no bloqueo

**Mi respuesta explícita, como se me pidió: es deuda aceptable con dueño (el
humano), y NO bloquea el cierre de F-005.**

Los motivos, en orden de peso:

- **Lo que depende de este repositorio está hecho y verificado.**
  `docs/INTEGRACION.md` existe, tiene su barrido de secretos como test (22
  tests, 9 controles negativos y 8 positivos) y está enlazado desde
  `docs/ARCHITECTURE.md:212`. La copia en `azure-apps` está escrita, con
  cabecera de origen y fecha, y su barrido pasa limpio.
- **Lo que falta es un commit en OTRO repositorio.** `azure-apps` no es este
  repo: ni su rama, ni su historial, ni su política están bajo el alcance de
  F-005 ni bajo la autoridad de ningún agente de este arnés.
- **Hay una decisión expresa, fechada y del dueño legítimo.** El humano
  decidió el 2026-08-19 dejarlo sin commitear. Un reviewer no revoca una
  decisión del humano sobre su propio repositorio.
- **El implementer hizo exactamente lo correcto**: no marcó `[x]` una tarea a
  medias. Marcó `[~]`, explicó qué falta, y —esto es lo que más peso tiene—
  **escribió cuál es la consecuencia práctica**: sin commit no hay fecha
  comprobable ni diff, y un `git checkout` en `azure-apps` se lo lleva por
  delante. Premiar eso con un rechazo enseñaría a marcar `[x]` y callarse.

**Pero la deuda tiene que sobrevivir al cierre**, y aquí sí pongo una
condición al líder: el riesgo real no es que falte el commit, es que **la
base `postventa` ya existe en el servidor compartido** (M2 se ejecutó y creó
rol, base y esquema). El ecosistema ya cambió; el único registro de ese cambio
es un fichero sin versionar. Ese es justo el fallo que `CLAUDE.md` documenta
con nombre y fecha —las cinco mejoras del arnés perdidas el 2026-08-08 por
vivir en una carpeta suelta—. Por tanto, **al cerrar F-005 la deuda debe
quedar escrita en `progress/history.md`** con su dueño (el humano) y no solo
en `tasks.md`, que deja de leerse en cuanto la feature se cierra.

### 4 · La observación O1 heredada de F-004: NO se resolvió

**Se persiste el valor crudo sin más, y sin que nadie lo decidiera.** Es el
cambio requerido 1.

`progress/current.md` lo dejó encargado sin ambigüedad: «*O1 de F-004, que
F-005 debía atender […] Al persistir los avisos había que decidir si ese valor
se guarda o se recorta. **Comprobar en la review de F-005 que quedó
resuelto.***»

Lo he comprobado, y el resultado es que **no se resolvió ni se mencionó**.
Busqué «O1» y «crudo» en `requirements.md`, `design.md`, `tasks.md` y
`progress/impl_F-005.md`: **ni una aparición** referida a este asunto. No es
que se decidiera guardarlo y se justificara; es que la decisión no se tomó.

Y el valor sí llega a la base. La cadena completa:

- `application/pipelines/paso_firma.py:116` compone el aviso con
  `f"…el modelo devolvió '{bruto.valor}'…"` — texto libre del modelo, sin
  cota de longitud.
- `infrastructure/persistencia/mapeo.py:134-136`:
  `json_de_avisos()` hace `json.dumps(list(avisos), ensure_ascii=False)`,
  **sin recorte de ningún tipo**.
- `sql/04_validaciones.sql` lo guarda en `avisos jsonb NOT NULL DEFAULT '[]'`.

Lo que convierte esto en algo más que un detalle es **dónde** aterriza. El
comentario de cabecera de `04_validaciones.sql` proclama, en mayúsculas:

> `-- LAS OBSERVACIONES NO SE COPIAN AQUI (R21, R39).`

y explica que una segunda copia de texto manuscrito de un cliente «dobla la
exposición y diverge». El razonamiento es impecable. Pero la columna `avisos`,
en esa misma tabla, es un canal de texto libre **sin cota** que viene del
modelo, y es exactamente la vía por la que un texto no previsto podría acabar
duplicado ahí. No viola la letra de R21 —el campo `observaciones` no se
copia—, pero deja abierta la puerta que R21 quiere cerrar, en la tabla en la
que R21 está escrito.

Hay además un segundo motivo, menor pero real y ya identificado por la propia
spec: `design.md` §fila 20 fija como restricción «**sin JSON crudo gigante**»
porque el servidor es un `Standard_B1ms` con 32 GB de disco compartidos.

El propio `ddl.py` ya tiene el patrón resuelto (`_RECORTE = 80` para los
mensajes de `DdlInseguro`, con su test a cada lado del borde). El arreglo es
de una línea.

### 5 · La decisión D2 y las salvaguardas del DNI: los dos barridos muerden

**Verificado, y los dos barridos muerden de verdad.** Este es el punto mejor
resuelto de la feature.

**Barrido 1 · el log (R29, R37).**
`tests/test_f005_logs_sin_datos_personales.py` no se limita a comprobar que
el log está limpio —eso lo cumpliría un logger mal configurado que no
escribiera nada—. Tiene un **control negativo explícito**,
`test_f005_r29_el_test_veria_una_fuga_si_la_hubiera`, que escribe el DNI a
propósito y **exige que la comprobación falle**:

```python
with pytest.raises(AssertionError) as detectado:
    _sin_datos_personales(caplog.text)
assert DNI_INVENTADO in str(detectado.value)
```

Y la fase RED 3 del informe enseña el barrido mordiendo sobre el código real:
se añadió a mano el volcado de parámetros que uno escribe depurando y el test
cayó nombrando el valor filtrado. Eso es un guardián que se ha visto gritar.
Cubre cinco valores, no solo el DNI: DNI, observaciones, descripción,
promoción y unidad.

**Barrido 2 · el repositorio (R38).**
`tests/test_f005_repo_sin_datos_personales.py` tiene las tres piezas que hacen
falta y que casi nadie pone las tres: un **control positivo** (que el barrido
mire ficheros de verdad y no una lista vacía), **controles negativos** (DNI y
NIE inyectados, compuestos en memoria para no escribirlos en ningún fichero) y
un **control de falsos positivos** (que un hash, una versión o un UUID no
disparen la alarma). El patrón excluye correctamente `I`, `Ñ`, `O` y `U`, que
no se usan como letra de control.

**No me he fiado: pasé mi propio barrido** de DNI y NIE sobre los 60 ficheros
del diff, con mis propios patrones. Único valor encontrado en todo el diff:
`00000000T`, el número no emitido y de uso convencional, y siempre declarado
como inventado en el propio fichero. **Cero DNI reales.**

**R39 y R40** también se sostienen: `dni_cliente` existe en una sola columna
(`03_partes.sql`) y ninguna otra tabla lo copia; y la guarda rechaza cualquier
tipo binario (`TIPOS_PROHIBIDOS`), de modo que los bytes del PDF —que llevan
el DNI manuscrito— no pueden entrar en la base ni por descuido.

### 6 · La guarda del DDL y el `search_path`: impiden de verdad

**Verificado, y la construcción es la correcta.**

**El `search_path` va sin `public`.** `conexion.py:105` emite literalmente
`f"SET search_path TO {ajustes.pg_esquema}"` — un solo esquema, sin `public`
en el camino. El nombre pasa antes por `validar_nombre_de_esquema()`, que
exige `^[a-z_][a-z0-9_]{0,62}$`: sin comillas, sin espacios y sin `;`, así que
un `PG_SCHEMA` hostil no puede inyectar. Y no es solo teoría: **M2 lo confirmó
contra la base real** con una consulta de solo lectura al catálogo —
`NUESTRAS TABLAS EN 'public': ninguna (correcto)`.

**La guarda impide el DDL fuera del esquema propio.** Lo importante es que
está construida como **lista blanca, no como lista negra**, y eso es lo que la
hace sólida. `_validar_forma()` solo reconoce cinco formas —`CREATE SCHEMA`,
`CREATE TABLE`, `CREATE [UNIQUE] INDEX`, `CREATE OR REPLACE VIEW` y
`ALTER TABLE … ADD COLUMN IF NOT EXISTS`— y **todo lo demás cae** en el `else`
con `DdlInseguro`. Las tres consecuencias que importan:

- **Ámbito de servidor imposible**: los 15 `VERBOS_PROHIBIDOS` (`CREATE
  DATABASE`, `CREATE ROLE`, `ALTER SYSTEM`, `GRANT`, `DROP SCHEMA`…) se
  rechazan por nombre, y aunque alguien inventara uno nuevo, la lista blanca
  ya lo habría rechazado por no tener forma reconocida.
- **Fuera del esquema imposible**: `_exigir_cualificado()` obliga a que cada
  objeto empiece por `<esquema>.`; un `CREATE SCHEMA` de otro esquema se
  rechaza comparando el nombre creado con el configurado.
- **Todo antes de abrir la conexión.** `ddl.py` **no importa `psycopg`** —lo
  comprobé— y `asegurar_esquema()` llama a `puede_aplicar_ddl()` y a
  `cargar_ddl()` **antes** de pedir el bloqueo. Cuando esto falla, la base de
  datos de los demás no se ha enterado de que existimos.

Dos detalles que me parecen aciertos y merecen constar: `CREATE EXTENSION`
está en la lista negra (por eso los UUID se generan en Python), y
`ficheros_ddl()` **rechaza** un `.sql` que no siga `NN_nombre.sql` en vez de
ignorarlo en silencio — un fichero de DDL que nadie aplica es peor que uno que
falla, porque el fallo se ve.

También verifiqué la elección de poner el intérprete del DDL en `.py` y no en
`.sql`: es deliberada y está explicada en la cabecera de `ddl.py`. La razón es
buena — `harness/alcance.py` solo mide y muta `.py`, así que un `.sql` con la
lógica dentro escaparía entero a la cobertura y a la mutación, justo en el
fichero más peligroso de la feature.

## Segunda pasada (2026-08-20) · verificación de los dos arreglos

Reviso **solo los dos cambios requeridos**; el resto de la feature ya quedó
dado por bueno en la primera pasada y no lo repito.

Cuatro commits nuevos: `9284e79` (FQDN), `882d3c6` (la cota), `6543c28` (se
versiona mi informe) y `fa22690` (informe con los arreglos).

**Lo que he ejecutado yo en esta pasada**: `bash harness/init.sh` tal cual
(exit 0, `PUERTA COBERTURA: 97.0% de 596 líneas cambiadas`, 578/596); la suite
del servicio relanzada por mí sin fiarme de la caché → **682 passed, 10
skipped in 15.91s** (los 4 nuevos son los de la cota); recálculo independiente
del alcance y de los mutantes; medición propia de los textos de aviso del
pipeline; y barrido del FQDN sobre árbol, historial y mensajes de commit.
`git status` limpio.

### 1 · El FQDN — RESUELTO en `HEAD`, con una condición de merge

**Verificado**: en el árbol de trabajo **no queda ninguna aparición** del FQDN
real. El test usa ahora el host inventado `psql-inventado-0000.…`, el mismo
que ya usaba `test_f005_integracion_sin_secretos.py`, y lleva un docstring que
explica por qué y que nombra el recurso **a secas, sin sufijo de dominio**. El
test no pierde nada: lo que comprueba es que un host que no es esta máquina se
rechaza.

Comprobé también los tres sitios que pedía el encargo:

| Dónde | Resultado |
|---|---|
| Árbol de trabajo (todo el repo) | **limpio** |
| Informes de `progress/` | **limpio** — incluido el mío, que lo redacté al detectar que yo mismo lo estaba reintroduciendo |
| Mensajes de commit de la rama | **limpio** |
| `services/postventa-api/.env` | lo tiene, **y es correcto**: es su función. Está en `.gitignore:27` y **sin trackear** (`git ls-files` no lo conoce). No lo he tocado. |

**Lo que queda, y por qué no bloquea.** Los **24 commits anteriores** de la
rama siguen conteniendo el valor. Eso no tiene arreglo sin reescribir la
historia, y aquí debo ser honesto sobre la gravedad, incluso en contra de cómo
formulé la urgencia en la primera pasada:

- **El nombre del recurso ya está en `dev` por diseño**: lo trae `CLAUDE.md`,
  y también `BACKLOG.md`, `docs/ARCHITECTURE.md` y `harness/features.json`.
- **El sufijo `.postgres.database.azure.com` es determinista** para cualquier
  PostgreSQL flexible de Azure. Es decir: dado el nombre del recurso, que ya
  está publicado en el repo a propósito, **el FQDN es derivable por cualquiera**.
- Por tanto la información marginal que revela el FQDN sobre lo que `dev` ya
  contiene es **prácticamente nula**.

**Rectifico en parte mi primera pasada**: sobrevaloré la dimensión de secreto.
Lo que sí sostengo, y es lo que justificaba el arreglo, es el argumento de
**coherencia**: la feature se prohibía ese patrón a sí misma en tres sitios y
lo violaba en un cuarto; una regla que el propio código incumple deja de ser
una regla. Ese argumento se ha atendido, y bien.

De ahí la condición de merge del principio: **squash preferible**, merge normal
aceptable, **reescribir la historia de 31 commits, no** — el riesgo de una
reescritura sobre una rama con 27 tareas y tres verificaciones manuales
ejecutadas supera con creces el beneficio de ocultar un dato derivable.

### 2 · La cota de los avisos (O1 / D7) — RESUELTO, y bien resuelto

**La decisión existe, con fecha y dueño**: D7, 2026-08-19, el humano decide
**recortar**. Ya no hay una opción permisiva elegida por omisión, que era el
fondo de mi objeción.

**La implementación es correcta** (`mapeo.py`):

- El recorte es **por aviso, no sobre el JSON entero**, con un test dedicado
  que prueba que dos avisos cortos sobreviven a un tercero largo. Es el detalle
  que más fácil habría sido hacer mal: aplicado al conjunto, un aviso largo se
  llevaría por delante a los cortos que van detrás, que son justo los que
  explican qué le falta al parte.
- Deja la señal `…`, como `ddl.py`. Sin ella, quien lea la cola creería estar
  viendo el aviso entero.
- El borde es `<=`, de modo que 240 exactos entran completos.

**¿Está bien elegido el 240? Sí, y lo he verificado por mi cuenta**, que era lo
que se me pidió juzgar. Medí los textos fijos de los avisos que emite el
pipeline, sin fiarme de la tabla del informe:

```
 111  firma/etiqueta desconocida (con el valor del modelo vacío)
  76  firma+extraccion/campo fuera del contrato
  66  persistencia/parte ya procesado
  51  firma/el modelo no devolvió el campo
  37  troceado/PDF sin páginas
  36  ingesta/no es un PDF ni un ZIP
```

El esqueleto fijo más largo son **111 caracteres**, exactamente lo que declara
el informe. Con la cota en 240 quedan **129 libres** para la parte variable.
Eso es lo que hace que el número esté bien puesto:

- **Por abajo**, ningún aviso legítimo se mutila. La parte variable más grande
  no es el valor del modelo sino el nombre del documento, que dentro de un ZIP
  es una ruta; 129 caracteres la cubren con holgura.
- **Por arriba**, acota de verdad: una decena de avisos por parte × 240 son
  unos pocos KB por fila, no un volcado del modelo. Cierra el canal de texto
  libre sin cota hacia una base compartida, que era el problema.
- **El 80 de `ddl.py` no valía**, y el informe lo razona bien: cortaría por la
  mitad el aviso legítimo de 111. Reutilizar el patrón no es reutilizar el
  número.

**¿Los tests fijan de verdad el borde? Sí, y hay prueba independiente de que
muerden.** Los dos casos de borde están escritos con la constante **a mano y
no importada de `mapeo.py`** —un test que leyera la constante se movería con
ella y dejaría de vigilar nada—, y la campaña de mutación lo confirma: los dos
mutantes nuevos que caen justo ahí **están muertos**.

| Mutante nuevo | Lo mata |
|---|---|
| `mapeo.py:67` `_RECORTE_AVISO = 240 → 241` | el test del borde de 241 |
| `mapeo.py:170` `len(aviso) <= _RECORTE_AVISO → <` | el test del borde de 240 |

Ese primer mutante es la demostración de que escribir el 240 a mano fue la
decisión correcta: con la constante importada, **habría sobrevivido**.

**Fase RED presente**, con traza real en rojo de los cuatro tests antes de
existir el recorte, incluido el `AssertionError` que enseña el aviso sin la
señal `…`.

**La campaña relanzada**: 106 mutantes (recalculados por mí: 106), 103
muertos, **0 supervivientes**, 3 timeouts. Los tres timeouts son **los mismos
tres de `ddl.py`** que ya verifiqué empíricamente uno a uno en la primera
pasada (exit 124 bajo reloj, control sin mutar terminando): no hay ninguno
nuevo, y el análisis sobrevivió en `progress/impl_F-005.md`. Con 330,4 s
(5,5 min) sigue por encima del umbral de 5 minutos de C4 bis, así que **la
reejecución no me era obligatoria y no la he hecho; lo hago constar
explícitamente**, como exige el checkpoint.

Una observación menor, sin consecuencias: si el nombre de un documento dentro
de un ZIP superara los ~129 caracteres, el aviso se recortaría y se perdería
la cola de la ruta. El `…` lo señala, así que nadie se engañaría, y el
compromiso me parece el correcto.

---

## Cambios requeridos (primera pasada, 2026-08-19 — AMBOS RESUELTOS)

> Se conservan tal y como se escribieron, como rastro de qué se pidió. La
> verificación de los arreglos está en la sección anterior.

Dos. Los dos son concretos, localizados y de arreglo corto.

### 1 · Sacar de git el FQDN real del servidor compartido

**Fichero**: `services/postventa-api/tests/test_f005_conexion.py`, **línea 65**.

La línea afirma `not es_host_local(...)` sobre **el FQDN completo y real del
servidor compartido**: el nombre del recurso que ya conoce `CLAUDE.md`,
seguido del sufijo de dominio de PostgreSQL en Azure. **No lo transcribo aquí
a propósito**, por la misma razón por la que pido quitarlo de allí: este
informe también se versiona. La referencia por fichero y línea es suficiente
para localizarlo.

**El problema.** `CLAUDE.md` es taxativo: «Nunca secretos en un repositorio.
Ni contraseñas, ni cadenas de conexión, ni claves, ni IDs de suscripción o
tenant, ni IPs internas. Da igual que el repositorio sea privado: **el
historial de git no suelta lo que entra**».

Lo que convierte esto en un defecto y no en una opinión mía es que **la propia
F-005 se prohíbe a sí misma este patrón en otros tres sitios**:

- `tests/test_f005_ajustes.py:155-156` afirma
  `assert ".postgres.database.azure.com" not in ejemplo` sobre
  `.env.example` y `local.settings.json.example`.
- `tests/test_f005_integracion_sin_secretos.py:161` usa el host **inventado**
  `psql-inventado-0000.postgres.database.azure.com` como control negativo,
  precisamente para no escribir el real.
- El informe declara el FQDN de Azure como la primera de las seis familias
  que el documento de integración no puede contener.

Comprobé además que **es nuevo**: `git grep` sobre `dev` no encuentra ni una
aparición de `postgres.database.azure.com`. El nombre del recurso a secas
(`psql-albaranes-rs9k2`) sí está en `dev` por diseño —lo trae `CLAUDE.md`—,
pero el FQDN completo lo introduce esta rama, en este único punto.

**El arreglo**: sustituir por un host inventado, como ya hace el fichero
hermano. El test no pierde absolutamente nada — lo que comprueba es que un
host **que no es local** se rechaza, y para eso sirve igual
`psql-inventado-0000.postgres.database.azure.com`. Si se prefiere conservar la
intención de «este es el servidor que de verdad nos preocupa», basta un
comentario en prosa nombrando el recurso, sin el sufijo de dominio.

**Por qué bloquea y no es una observación**: porque después del merge a `dev`
el valor queda en el historial para siempre y sacarlo exige reescribirlo. Es
el único hallazgo de esta review cuyo coste crece si se pospone.

### 2 · Decidir por escrito qué se hace con el valor crudo del modelo en `avisos` (O1)

**Ficheros**: `infrastructure/persistencia/mapeo.py:134-136`
(`json_de_avisos`), con origen en
`application/pipelines/paso_firma.py:116`.

**El problema.** Está desarrollado en el punto 4 de la sección anterior: F-005
tenía encargado decidir si ese valor se guarda o se recorta, y lo persiste
verbatim sin que la decisión se tomara ni se escribiera en ningún sitio.

**El arreglo**, cualquiera de los dos, pero **escrito**:

- **Recortar**, que es lo que yo recomendaría por coherencia interna: aplicar
  una cota de longitud a cada aviso en `json_de_avisos()` —el patrón ya existe
  en `ddl.py` con `_RECORTE = 80` y su test a cada lado del borde— y añadir un
  test que fije el límite. Un aviso es un diagnóstico, no un almacén.
- **Guardarlo entero**, si el humano lo prefiere: entonces hay que decirlo con
  todas las letras en `progress/impl_F-005.md` como decisión **D7**, con su
  fecha, y anotar por qué se acepta que un texto libre del modelo entre sin
  cota en la tabla cuyo DDL declara que ahí no se copia texto del cliente.

Lo que no puede quedar es el estado actual: la opción permisiva elegida por
omisión, en una feature de rigor `critico` sobre una base compartida con dato
personal, cuando el arnés había encargado explícitamente lo contrario.

**Nota para el líder**: si el humano decide que esto no toca a F-005 y prefiere
llevarlo a una feature propia, me parece defendible — pero entonces la decisión
tiene que quedar escrita **y** la deuda dada de alta en `harness/features.json`
con dueño, no de vuelta a `progress/current.md`, que es de donde ya se cayó una
vez.

## Observaciones que no bloquean

**O-A · `progress/current.md` declara «675 passed» y son 678.** Línea 18. Se
quedaron atrás los tests añadidos en la segunda tanda de T23. El informe
`impl_F-005.md` sí trae el número correcto. Cosmético.

**O-B · 16 worktrees huérfanos de una campaña anterior.** `git worktree list`
lista 16 entradas en `%TEMP%\mutacion_F-005_zllkg8wf\wk_*`, ancladas en
`48fb104`, que no son mías —las mías las retiré—. Viven fuera del repositorio
y no ensucian `git status`, pero siguen registradas en `.git/worktrees`. Se
limpian con `git worktree prune` una vez borrado el directorio. Sugiere que
`harness/mutacion.py` no siempre retira sus worktrees cuando la campaña se
interrumpe; si se confirma, es una mejora **genérica** y su sitio es
`arnes-base`.

**O-C · La etiqueta `timeout` de `harness/mutacion.py` también se dispara por
lentitud.** Detallado en C4 bis: en mi reejecución parcial bajo carga salieron
como `timeout` mutantes que no pueden colgarse (`_RECORTE = 80 -> 81`). No
afecta a F-005 —sus tres timeouts los verifiqué uno a uno por otra vía— pero
significa que un `timeout` **no** es por sí solo prueba de no-terminación. Si
el análisis de timeouts va a seguir siendo la vía para justificarlos, conviene
que sea la herramienta quien distinguya ambos casos, o que `CHECKPOINTS.md`
exija al implementer la comprobación con reloj externo que aquí se hizo a mano
y bien. Es mejora genérica: `arnes-base`.

**O-D · R32, R33 y R34 no tienen test con el nombre `test_f005_rN_*`.** Están
cubiertos por mecanismo, y por mecanismos **más fuertes** que un test (un
fixture que hace imposible abrir red; un `pytest.exit` que aborta la sesión).
No lo cuento como incumplimiento de C4 —lo importante es que el requisito esté
garantizado, no el nombre del test—, pero lo anoto porque la letra del
checkpoint pide `test_fXXX_rN_*` y a un lector rápido le parecerán huecos.

**O-E · Elogio, para que no se pierda: el movimiento de `tests_bbdd/` a
`tests_bbdd/tests/` (T20) NO es un truco para bajar el número de mutantes.**
Lo verifiqué porque tenía toda la pinta de serlo: la campaña pasó de 163 a 104
mutantes justo después. Pero la razón es correcta y está escrita sin
disimulo en `tests_bbdd/__init__.py`: `harness/alcance.py` excluye del alcance
las rutas con `tests` como segmento completo, y con los ficheros colgando
directamente de `tests_bbdd/` se estaban **mutando los propios tests** —59
mutantes que caían sobre tests que se saltan solos y sobrevivían todos, puro
ruido—. La solución no toca el arnés, mantiene la suite fuera de la guarda
`sin_red` que necesita, y deja el arreglo de fondo (que `alcance.py` reconozca
cualquier suite) declarado para **F-017**. Es exactamente cómo se hace.

## Propuesta de mejora del protocolo (no aplicada)

Como pide la sección «Automejora» de `.claude/agents/reviewer.md`, propongo —
sin aplicarlo — un cambio a `CHECKPOINTS.md`, para que lo apruebe el humano:

**C4 bis debería tratar los `timeout` de la campaña como una categoría propia,
con su propia carga de prueba.** Hoy el checkpoint habla de supervivientes y
de muertos, y los timeouts caen en tierra de nadie: ni son supervivientes (no
cuentan contra el límite de `critico`) ni están comprobados como muertos. En
F-005 el implementer hizo espontáneamente lo correcto —verificar cada uno con
un reloj externo y pegar el `exit 124`—, pero eso fue mérito suyo, no
exigencia del arnés. Y mi observación O-C demuestra que la etiqueta no es
fiable por sí sola.

Redacción propuesta, como viñeta nueva de C4 bis:

> - [ ] **Cada `timeout` de la campaña está justificado como no-terminación
>   real**, no como lentitud de la máquina: el informe del implementer trae,
>   por cada uno, el caso concreto que lo cuelga y la salida de haberlo
>   ejecutado bajo reloj externo. Un `timeout` sin esa prueba se cuenta como
>   **superviviente**, y en nivel `critico` bloquea.

Si se acepta, es mejora **genérica** y hay que portarla a `arnes-base` en el
mismo trabajo, junto con la de O-B y O-C.

## Resumen para el líder

| | |
|---|---|
| **Veredicto** | **APPROVED** (segunda pasada, 2026-08-20) |
| **Cambios requeridos** | los 2 de la primera pasada, **aplicados y verificados por mí** |
| **Condición de merge** | **squash preferible** a `dev`: el árbol está limpio, pero 24 commits de la rama conservan el FQDN. Merge normal es aceptable (gravedad baja, ver Segunda pasada §1). No reescribir la historia. |
| **Deuda con dueño** | T26 `[~]`: el commit en `azure-apps` es del humano. **Trasladar a `progress/history.md` al cerrar**, no dejarla solo en `tasks.md` |
| **Puertas de rigor** | todas cumplidas y verificadas por mí de forma independiente |
| **Suite** | 682 passed, 10 skipped (relanzada por mí, sin caché) |
| **Cobertura** | 97,0 % (578/596), umbral 80 % |
| **Mutación** | 106 mutantes, **0 supervivientes**, 3 timeouts verificados uno a uno |

**F-005 queda aprobada y lista para cerrarse.** Al hacerlo, dos cosas que no
pueden caerse: la **condición de merge** y la **deuda de T26 en
`history.md`** — esta última precisamente porque la base `postventa` ya existe
en el servidor compartido y su único registro fuera de este repo sigue sin
versionar.

Las observaciones O-A a O-E y la propuesta de mejora de `CHECKPOINTS.md` sobre
los timeouts siguen abiertas y sin bloquear; O-C y la propuesta son mejoras
genéricas y su sitio es `arnes-base`.
