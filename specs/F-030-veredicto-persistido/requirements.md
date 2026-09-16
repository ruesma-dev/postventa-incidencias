<!-- specs/F-030-veredicto-persistido/requirements.md -->
# F-030 · La aprobación humana no sobrevive a la puerta de F-028 — Requisitos

> Notación EARS (`specs/SPECS.md`). Cada requisito se traduce a **al menos un
> test trazable** `test_f030_rN_*`. Rigor **`critico`** (`harness/rigor.json`):
> fase RED obligatoria, puerta de cobertura sobre las líneas cambiadas (80 %) y
> campaña de mutación con **cero supervivientes** —cada uno exige un test nuevo
> o una justificación escrita aceptada por el humano—.
>
> Es `critico` por lo que hay al otro lado de la puerta que se toca: un PDF con
> el DNI manuscrito de un cliente subido a SharePoint y una reclamación cerrada
> en el ERP de producción.

## Alcance

**Una regresión en producción, y nada más.** F-030 no añade ninguna capacidad:
devuelve al circuito la garantía que F-028 rompió sin darse cuenta.

**Entra**: que las tres puertas del circuito —`paso_archivo`, `paso_grafico` y
`paso_cierre`— juzguen el **veredicto guardado en la base** en vez de uno
fabricado con lo que traiga el cuerpo de la petición; la lectura de ese
veredicto, metida en la consulta de situación que esas puertas ya hacen; la
retirada del `ResultadoValidacion` de pega de `archivar.py`, `adjuntar.py` y
`cerrar.py`; y los tests de borde a borde que faltaron.

**No entra**, y se declara porque cada una de estas cosas se ha considerado y
se ha dejado fuera a propósito:

- **ningún DDL**: ni tabla nueva, ni columna nueva, ni índice nuevo. §2 de
  `design.md` demuestra **[MEDIDO]** que lo persistido basta para recomponer la
  huella;
- **ni una clave del contrato HTTP**: `/api/archivar`, `/api/adjuntar` y
  `/api/cerrar` siguen aceptando exactamente el mismo cuerpo, con las mismas
  validaciones de 400. `services/postventa-front/` **no se toca**;
- **`huella_de_veredicto` y `_normalizar` no se tocan** (F-026 D9, F-028 D9).
  Cambiar el valor de la huella invalidaría todas las decisiones ya guardadas,
  incluida la que esta feature viene a rescatar;
- **`POST /api/estado` y `POST /api/parte` no cambian su forma de emitir el
  veredicto**: los dos reciben la extracción entera, emiten el veredicto con
  las reglas de F-004 (R28 de F-028, R8 de F-019) y lo guardan en la misma
  llamada. Son **productores** legítimos; los tres del circuito no lo son;
- **ninguna escritura nueva** en Sigrid ni en SharePoint, y **ninguna
  verificación contra el ERP** como parte de esta spec: el cierre de una
  incidencia exige autorización expresa del humano por incidencia y no se hace
  desde local (`CLAUDE.md`, reglas duras);
- **no se reabre la decisión del arreglo.** El parche por destino quedó
  descartado por escrito el 2026-09-16 (§3).

---

## 0 · Lo que pasa hoy, medido

Todo **[MEDIDO]** contra el código de `dev` desplegado el **2026-09-16 a las
07:33 UTC**, con su fuente al lado.

1. **`POST /api/estado` apunta la huella del veredicto completo.**
   `interface_adapters/api/estado.py:162` emite el veredicto con
   `validar_parte(extraccion, lectura)` —el cuerpo trae la extracción entera—
   y `:198` escribe `huella_veredicto=huella_de_veredicto(validacion)` en la
   fila del histórico. Esa huella lleva dentro el destino, los códigos de
   motivo ordenados, la clasificación de firma, **las observaciones
   normalizadas**, el código de obra y el número de incidencia
   (`domain/models/aprobacion.py:151-160`). **[MEDIDO]**

2. **`POST /api/archivar` no recibe la extracción y fabrica un veredicto de
   pega.** `archivar.py:190-198` construye un `ResultadoValidacion` con
   `motivos=()`, `clasificacion_firma=ClasificacionFirma.HUMANA` fija,
   `observaciones=None`, `confianza_observaciones=0` y —por omisión del
   dataclass— `codigo_obra=""` y `numero_incidencia=""`. Del parte real solo
   conserva el `veredicto` y el `destino` que vengan en el formulario.
   **[MEDIDO]**

3. **El mismo stub está en las otras dos puertas**: `adjuntar.py:244-249` y
   `cerrar.py:212-217`, letra por letra. **[MEDIDO]**

4. **La puerta recomputa la huella sobre ese objeto falso.**
   `application/pipelines/puerta_de_estado.py:112` llama a `estado_del_parte`,
   que en `domain/models/estado.py:325-328` exige
   `_aprueba_lo_que_hay(decision, validacion)`, y ahí `:355-357` compara
   `decision.huella_veredicto == huella_de_veredicto(validacion)`. Como la
   validación es el stub, no coincide nunca, la aprobación no cuenta, se cae a
   `estado_de_la_maquina` y el parte vuelve a `pendiente`. **[MEDIDO]**

5. **La huella del stub es una de tres constantes de todo el sistema.** No
   depende del parte: solo del `destino` que venga en el cuerpo, porque los
   otros cinco campos de la cadena canónica son fijos. Calculadas hoy
   **[MEDIDO]**:

   | destino del cuerpo | huella del stub |
   |---|---|
   | `archivo_y_cierre` | `371a85e5…` |
   | `cola_validacion_humana` | `9d8596a0…` |
   | `revision_manual` | `e647e345…` |

   La segunda es exactamente la que midió el humano sobre la incidencia
   **RS26.09/0178** (`9d8596a0…` contra la real `44aeec3e…`). Que la huella con
   la que se juzga sea la misma para los 22 partes de una remesa es la forma
   más corta de decir que no se está juzgando nada.

6. **Es regresión de F-028 T11 (commit `51fbe77`).** Hasta F-026 la puerta era
   `admite_circuito(validacion, aprobacion)` y comparaba **solo el destino
   aprobado**, con esta docstring literal, que está en
   `git show 51fbe77^:services/postventa-api/application/pipelines/paso_archivo.py`:
   *«lo que hace que la puerta sirva de algo **sin poder recomputar la
   huella**»*. F-026 sabía que `/api/archivar` no puede rehacer el veredicto;
   F-028 la sustituyó por `estado_del_parte`, que sí lo recomputa, y no migró
   los tres endpoints. **[MEDIDO]**

7. **El contrato ya decía que esto había que arreglarlo algún día.** La
   cabecera de `archivar.py:23-29` dice, literal: *«Leerlo de la base sería más
   fuerte, pero exige un método nuevo en `RepositorioPartesPort`, que es de
   F-005, y F-006 no cambia specs ajenas»* (decisión D4 de F-006). F-030 es ese
   día. **[MEDIDO]**

8. **El test que había no podía cazarlo.**
   `tests/test_f028_puertas.py:737` —`test_f028_r9_un_parte_no_apto_que_una_persona_aprobo_pasa`—
   construye la decisión con `_decision(EstadoParte.APROBADO, validacion=ctx.validacion)`:
   la huella apuntada y la huella recomputada salen **del mismo objeto**, así
   que coinciden por construcción. No hay ni un test que recorra
   decidir → archivar con el cuerpo real de los endpoints. **[MEDIDO]**

9. **El defecto tiene una segunda cara, y es de seguridad.** Como la puerta
   deriva el estado del veredicto del cuerpo, quien llame a `/api/archivar` con
   `veredicto=apto` y `destino=archivo_y_cierre` pasa la puerta **aunque la
   validación guardada haya mandado ese parte a `revision_manual`**: sin
   decisión humana, `estado_de_la_maquina(stub)` devuelve `aprobado`. Hoy lo
   único que lo impide es que el front mande la verdad. Es justo lo que R33 de
   F-028 —«del repositorio y nunca del cuerpo»— venía a cerrar, y quedó abierto
   en los tres endpoints. **[MEDIDO]** — esta feature lo cierra de paso (R6).

10. **Lo que sí funciona hoy, y no se puede romper**: los verdes automáticos
    —el parte apto pasa las tres puertas sin que nadie apruebe nada— y los
    rechazos —un parte rechazado a mano no pasa ninguna, porque el rechazo no
    necesita huella (`estado.py:323-324`)—. **[MEDIDO]**

11. **Alcance del daño**: todos los partes aprobados a mano, en los tres pasos,
    desde el despliegue del 2026-09-16 07:33 UTC. En producción hay al menos
    uno vivo: el parte `b7e9b037` de la incidencia **RS26.09/0178**, aprobado
    por el humano a las **18:09:33** y sin archivar. **[MEDIDO por el humano]**

---

## 1 · Qué hay guardado, y qué no

**[MEDIDO]** sobre `sql/03_partes.sql` y `sql/04_validaciones.sql`.

`postventa.validaciones` (1:1 con el parte, la revalidación sustituye la fila)
guarda: `hash_parte`, `veredicto`, `destino`, `clasificacion_firma`, `motivos`
(jsonb con `codigo` y `texto`), `avisos` (jsonb) y `validado_at_utc`.

**No guarda las observaciones, y es deliberado**: su propio DDL lo dice —*«LAS
OBSERVACIONES NO SE COPIAN AQUI (R21, R39) … Una segunda copia de texto
manuscrito de un cliente dobla la exposicion y diverge. Quien las necesite las
trae con un JOIN a partes»*—. Tampoco guarda `codigo_obra` ni
`numero_incidencia`, que son de la extracción y viven en `postventa.partes`.

De los seis campos de la cadena canónica de la huella, **tres salen de
`validaciones` y tres de `partes`**, y los seis están guardados. La tabla y la
comprobación **[MEDIDA]** están en `design.md` §2.

---

## 2 · Requisitos

### La regla, en una línea

- **R1** (Ubicuo). El sistema debe derivar el estado de un parte en las tres
  puertas del circuito a partir del **veredicto guardado en
  `postventa.validaciones`**, y nunca a partir de un veredicto construido con
  datos que vengan en el cuerpo de la petición.

- **R2** (Ubicuo). El sistema debe reunir en **`SituacionParte`** los tres
  hechos que consume `estado_del_parte` —el veredicto guardado, la última
  decisión humana y el estado de la traza de cierre—, de modo que quien deriva
  el estado no pueda mezclar una fuente con otra.

- **R3** (Ubicuo). Ningún módulo de `interface_adapters/api/` debe construir un
  `ResultadoValidacion` salvo llamando a `validar_parte` con la extracción
  recibida. *(Es el centinela estructural del defecto: lo que falló fue una
  construcción a mano, no un cálculo mal hecho.)*

### El circuito vuelve a funcionar

- **R4** (Dirigido por evento). CUANDO una persona aprueba un parte no apto por
  `POST /api/estado` y a continuación se llama a `POST /api/archivar` con el
  cuerpo real que manda el front, el sistema debe **archivar el parte**.

- **R5** (Dirigido por evento). CUANDO ese mismo parte llega a
  `POST /api/adjuntar` con el cuerpo real del front, el sistema debe
  **adjuntarlo** a su reclamación.

- **R6** (Dirigido por evento). CUANDO ese mismo parte llega a
  `POST /api/cerrar` con el cuerpo real del front, el sistema debe **dejar
  pasar la puerta del estado** y seguir con el resto de sus comprobaciones
  (archivado, gráfico, dry-run, login, ventana).

### El cuerpo deja de mandar

- **R7** (Comportamiento no deseado). SI el cuerpo de `/api/archivar`,
  `/api/adjuntar` o `/api/cerrar` declara un `veredicto` o un `destino`
  distintos de los guardados, ENTONCES el sistema debe decidir con **los
  guardados**, y un cuerpo que mienta con `veredicto=apto` y
  `destino=archivo_y_cierre` sobre un parte que la validación mandó a
  `revision_manual` **no debe pasar** ninguna de las tres puertas.

- **R8** (Comportamiento no deseado). SI no consta fila de validación para ese
  parte, ENTONCES cada puerta debe levantar `ParteNoApto` con **su** mensaje de
  «no consta que este parte haya pasado la validación», antes de cualquier otra
  comprobación y sin escribir nada en ningún sistema externo.

- **R9** (Comportamiento no deseado). SI no consta ni la ficha del parte,
  ENTONCES el sistema debe comportarse igual que en R8 —sin veredicto y sin
  estado de cierre— y **no** fallar con un error de base de datos.

### La huella sigue protegiendo

- **R10** (Ubicuo). El veredicto recompuesto desde lo guardado debe producir
  **exactamente la misma huella** que el `ResultadoValidacion` en memoria del
  que salió, para cualquier parte: mismos motivos en cualquier orden, mismas
  observaciones con cualquier espaciado o caja, y con los campos vacíos
  expresados como `NULL` o como cadena de espacios.

- **R11** (Dirigido por estado). MIENTRAS la huella apuntada en la aprobación
  humana sea la del veredicto **guardado ahora**, el parte debe estar
  `aprobado` y pasar las tres puertas.

- **R12** (Comportamiento no deseado). SI el veredicto guardado cambia después
  de que una persona aprobara el parte —una revalidación que lee otra cosa,
  una corrección del número de incidencia o del código de obra—, ENTONCES la
  aprobación **deja de contar**, el parte vuelve a `pendiente` y no pasa
  ninguna de las tres puertas.

- **R13** (Ubicuo). El valor de `huella_de_veredicto` no debe cambiar: ni su
  cadena canónica, ni su orden, ni su normalización.

### Lo que funciona hoy sigue funcionando

- **R14** (Dirigido por evento). CUANDO un parte apto con destino
  `archivo_y_cierre` recorre el circuito sin que nadie haya decidido nada, el
  sistema debe dejarlo pasar por las tres puertas, igual que hoy.

- **R15** (Dirigido por estado). MIENTRAS la última decisión humana de un parte
  sea `rechazado`, el sistema debe impedirle las tres puertas **aunque el
  veredicto guardado sea apto** y **aunque la huella apuntada sea otra**: el
  rechazo no caduca.

- **R16** (Dirigido por estado). MIENTRAS la traza de cierre esté en firme, el
  sistema debe dar el parte por `cerrado` y no dejarlo pasar, por encima de
  cualquier decisión humana.

- **R17** (Ubicuo). Los tres mensajes de error de las puertas deben seguir
  diciendo lo mismo que hoy, cada uno con su final propio —«no se archiva»,
  «no se adjunta a la reclamación», «no se cierra la incidencia»— y el de
  `pendiente` debe seguir nombrando **el destino guardado**.

### El coste y el contrato

- **R18** (Ubicuo). El sistema no debe hacer **ninguna consulta más por parte y
  paso** que las que hace hoy: la lectura del veredicto viaja dentro de la
  consulta de situación que las puertas ya ejecutan.

- **R19** (Ubicuo). El contrato HTTP de los tres endpoints no debe cambiar: las
  mismas claves obligatorias, las mismas validaciones contra las enumeraciones
  de F-004 y los mismos 400. `services/postventa-front/` no se modifica.

- **R20** (Ubicuo). El sistema no debe ejecutar DDL nuevo: ni columna, ni tabla,
  ni índice, ni migración de datos.

### Dato personal

- **R21** (Ubicuo). Ni las observaciones manuscritas, ni el DNI, ni ningún otro
  campo del papel deben aparecer en la respuesta HTTP de los tres endpoints ni
  en ninguna línea de log, incluida la de la consulta nueva.

- **R22** (Ubicuo). El texto manuscrito que se lea de la base para recomponer
  el veredicto debe quedarse en memoria, dentro de la pasada: no se escribe en
  ninguna tabla, no se serializa y no se copia a ninguna segunda columna.

### El test que faltó

- **R23** (Ubicuo). Debe existir un test de **borde a borde** que recorra
  `POST /api/estado` → `POST /api/archivar` **con el cuerpo real de los dos
  endpoints** y contra un doble de repositorio que guarde y devuelva **columnas**
  —no los objetos que recibió—, de modo que falle si alguien vuelve a fabricar
  el veredicto desde el cuerpo o si la recomposición deriva.

- **R24** (Ubicuo). Debe existir el equivalente de R23 para `/api/adjuntar` y
  para `/api/cerrar`.

---

## 3 · Decisiones tomadas (no se reabren)

- **D1 · Las tres puertas usan el veredicto persistido.** Lo eligió el humano
  el **2026-09-16**. Es lo que R33 de F-028 ya exigía para la situación, dicho
  ahora también del veredicto.

- **D2 · El parche por destino queda descartado, por escrito.** «Que la puerta
  compare solo el destino aprobado, como hacía F-026» arreglaría el síntoma y
  reabriría lo que R19 cerró con la huella: una aprobación volvería a
  sobrevivir a que alguien cambie el número de incidencia del parte y acabaría
  cerrando **otra** reclamación del ERP (la enmienda H-1 de F-026, 2026-09-12).

- **D3 · Sin columna nueva.** Lo guardado basta: `design.md` §2 lo demuestra
  **[MEDIDO]**. La alternativa —guardar la huella en `postventa.validaciones`—
  se estudia y se descarta en `design.md` §10.2, con su motivo principal: las
  filas ya escritas tendrían la huella a `NULL` y la aprobación de
  RS26.09/0178 dejaría de contar hasta revalidar el parte.

- **D4 · La lectura viaja en `consultar_situacion`.** Sin viaje nuevo a un
  PostgreSQL **compartido** (§11.1 de F-028). El detalle, en `design.md` §3.

- **D5 · `POST /api/estado` no se toca.** Sigue emitiendo el veredicto y
  apuntando su huella. Es el escritor, funciona, y tocarlo sería tocar el único
  camino que hoy hace bien su trabajo. La alternativa considerada —que también
  leyera de vuelta— está en `design.md` §10.3 con su porqué.

- **D6 · Las claves `veredicto` y `destino` se siguen aceptando y validando, y
  se dejan de usar para decidir.** Quitarlas del contrato obligaría a tocar el
  front en la misma sesión que arregla una regresión de producción. Se declara
  en el código que ya no deciden nada, y R7 lo vigila con un test.

---

## 4 · Trazabilidad requisito → verificación

| Req | Verificación |
|---|---|
| R1 | `test_f030_r1_*` · las tres puertas con un doble cuyo veredicto guardado contradice al del cuerpo |
| R2 | `test_f030_r2_*` · `SituacionParte` trae el veredicto; `estado_del_parte` se alimenta solo de ella en la puerta |
| R3 | `test_f030_r3_*` · centinela estructural sobre `interface_adapters/api/` (AST) |
| R4, R5, R6 | `test_f030_r4_*`, `r5`, `r6` · borde a borde decidir → archivar / adjuntar / cerrar |
| R7 | `test_f030_r7_*` · cuerpo que miente, tres puertas, ninguna pasa |
| R8 | `test_f030_r8_*` · sin fila de validación, `ParteNoApto` con su mensaje, y nada ha salido |
| R9 | `test_f030_r9_*` · sin ficha de parte, mismo comportamiento |
| R10 | `test_f030_r10_*` · ida y vuelta de la huella, tabla de casos borde |
| R11 | `test_f030_r11_*` · aprobación con la huella del veredicto guardado → pasa |
| R12 | `test_f030_r12_*` · el veredicto guardado cambia → deja de pasar |
| R13 | `test_f028_huella_intacta.py` (existente, **no se toca**) |
| R14 | `test_f030_r14_*` y los control-negativo de `test_f028_puertas.py` |
| R15 | `test_f030_r15_*` y los de F-028, intactos |
| R16 | `test_f030_r16_*` y los de F-028, intactos |
| R17 | `test_f030_r17_*` · los tres mensajes, con el destino guardado dentro |
| R18 | `test_f030_r18_*` · cuenta de consultas del adaptador con un doble de conexión |
| R19 | `test_f006_archivar_http.py`, `test_f012_adjuntar_http.py`, `test_f009_cerrar_http.py` en verde sin cambios de contrato + `npm test` del front |
| R20 | `test_f030_r20_*` · el diff no toca `sql/` (control de ficheros) |
| R21 | `test_f030_r21_*` · log de la consulta nueva sin texto del papel; los `test_*_logs_sin_datos_personales.py` existentes en verde |
| R22 | `test_f030_r22_*` · el veredicto recompuesto no se escribe en ninguna tabla |
| R23, R24 | los de R4, R5 y R6, que son ese test |

Verificaciones **MANUAL (humano)**, listadas en `tasks.md` y en
`progress/current.md`: la del parte `b7e9b037` de RS26.09/0178 contra `dev`, y
la cuenta real de consultas de una tanda contra el PostgreSQL compartido.
