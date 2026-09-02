<!-- progress/impl_utillaje_F-023.md -->
# Utillaje y documentación para desbloquear F-023

> **Qué es esto y qué NO es.** El informe del encargo de utillaje del
> 2026-09-02: un script de lecturas, la petición a Posventa, una referencia rota
> y el rastro en `progress/`. **No es la implementación de F-023**, que sigue
> `blocked` y **sin spec**, y por eso el fichero no se llama `impl_F-023.md`:
> un reviewer que viera ese nombre daría por hecho que la feature está hecha.
>
> **No se ha ejecutado ni una consulta** contra Sigrid, `sigrid-api`, la
> Function desplegada, el PostgreSQL compartido ni SharePoint. Se entrega el
> script, no sus resultados.
>
> Rama: `feature/F-009-cierre-sigrid`. **No se ha tocado `services/`, ni sus
> tests, ni el estado de ninguna feature en `harness/features.json`.**

---

## 1 · Ficheros tocados

| Fichero | Qué se hizo | Commit |
|---|---|---|
| `infra/13_caracterizacion_grafico_url.ps1` | **Nuevo.** Q1, Q3, Q4, Q5, Q8, Q9 del §5 de `explore_grafico_url.md`, y Q10 cuando Posventa haya hecho la prueba | `f74084d` |
| `infra/08_lectura_sigrid_comun.ps1` | Switch **`-Tolerante`** en `Invoke-SigridLectura`, apagado por defecto | `f74084d` |
| `progress/peticion_posventa_prueba_url_F-023.md` | **Nuevo.** La petición a Alicia Echevarría, reenviable tal cual | `6831926` |
| `specs/F-009-cierre-sigrid/design.md` | 3 correcciones `F-013` → `F-023` (§1 D4, §10, §11) | `ee691d9` |
| `specs/F-009-cierre-sigrid/requirements.md` | 1 corrección `F-013` → `F-023` (alcance) | `ee691d9` |
| `progress/spec_F-009.md` | Nota de corrección fechada; **la frase original no se toca** | `ee691d9` |
| `progress/current.md` | Bloque nuevo al principio | `<este commit>` |

---

## 2 · Decisiones de diseño

### 2.1 · El `-Tolerante` va en el módulo común, y no en un envoltorio local

**El problema.** Dos de las seis consultas pueden fallar **sin que nada esté
mal**: Q5 lleva un nombre de base **a tres partes** en el `FROM` —el propio
informe prevé que la pasarela lo rechace y da una variante en dos pasos— y Q9
consulta `dog`/`condog`, que **esta instalación puede no tener**. Con el módulo
tal y como estaba, cualquiera de las dos llamaba a `Salir-Con`, que hace `exit`:
se llevaría por delante las consultas siguientes **y el veredicto de las que sí
habían salido**. En una sesión contra producción que alguien lanza una vez, eso
es perder la mitad del viaje por un motivo que ni siquiera es un problema.

**Las tres salidas y por qué esta.**

| Opción | Por qué no |
|---|---|
| Duplicar el HTTP en el `13` con su propio `try` | Es exactamente lo que el `08` existe para evitar, y el encargo lo prohíbe |
| Ordenar las frágiles al final y rezar | Q5 es **la importante**; dejarla donde su fallo no duela es enterrarla |
| **Un switch en el módulo común** | Es un cambio de **cinco líneas**, **apagado por defecto**, y los `09`–`12` no cambian de comportamiento: no le pasan el switch |

Q9 lleva **además** su propia red antes de tolerancia: se pregunta a
`INFORMATION_SCHEMA.TABLES` si las tablas existen, y si no existen **no se
lanza la consulta**, se anota y se sigue. Un aviso amarillo que no es un fallo
acaba tratándose como ruido; mejor no producirlo.

### 2.2 · El nombre de la base documental se interpola, y eso hay que justificarlo

Q5 cruza contra la otra base, y **un identificador no cabe en un marcador `?`**.
La única forma es interpolarlo en el `FROM`. Lo que hace segura esa
interpolación **no es la confianza en quien lanza el script**, sino una lista
blanca estricta —`^[A-Za-z0-9_]+$`— comprobada **antes de la primera llamada**;
si no pasa, el script para con un mensaje que dice que **no se resuelve
relajando la comprobación**. Y el valor **no está en el repositorio**: entra por
`-SigridBaseDocumental`. Sin él, Q5 se lanza igual contra la base de negocio e
imprime los dos pasos que faltan.

### 2.3 · Qué se juzga y qué solo se anota

Un script que vuelca datos y deja que la persona decida **no es una
comprobación**. Pero esto es **caracterización**: la mayor parte de lo que sale
son datos que nadie ha visto nunca, y no hay «esperado» contra el que medirlos.
El reparto:

| Se **juzga** (rojo = hay que pararse) | Por qué hay expectativa firme |
|---|---|
| `rcg` tiene **más de 5 columnas** | El diccionario declara 5 y F-008 midió dos más. Si sale rojo, hay que creer al diccionario y no al informe |
| Filas con `vin` en (1,4) **son 2** | Lo midió F-008. Si hay más, alguien crea gráficos en un modo sin caracterizar |
| Total de `gra` **≥ 282.599** | La tabla solo crece. Si sale **menos**, o la medida de F-008 era mala o se están borrando gráficos, y las dos cosas invalidan el informe |
| `gra.cod` **es único** | De ello depende la sentencia 2 del §3.2. Si no lo es, **F-023 necesita otra forma de enlazar** |

Lo demás se **anota**. Con dos excepciones que se imprimen **destacadas en
pantalla** porque cambian el trabajo de quien las lea:

- **Si `gra` tuviera columna `url`**, el script dice que hay que releer el §1.2
  del informe antes de diseñar nada: su conclusión se apoyaba en que no existía.
- **Si `gra.cod` no fuera único**, dice qué sentencia deja de servir.

### 2.4 · Dónde vive la nota para Posventa, y por qué ahí

**`progress/peticion_posventa_prueba_url_F-023.md`.** El precedente exacto en
este repositorio es **`progress/guion_bloque8_F-009.md`**: un procedimiento que
ejecuta **una persona**, atado a una feature, escrito por el arnés. Las
alternativas se descartan por lo que dice el propio repositorio:

- **`docs/referencia/`** es para documentación **que llega de fuera** sobre el
  negocio y los sistemas origen, convertida a Markdown. Esto sale de aquí.
- **`docs/`** es documentación **del proyecto** (arquitectura, convenciones,
  despliegue, integración). Una petición puntual a una persona no lo es.
- **`infra/`** son **scripts PowerShell** re-ejecutables, según `CLAUDE.md`.

> **Detalle para el líder, y no lo he tocado porque no me corresponde:** el
> `blocked_by` de F-023 en `features.json` dice «Consultas y guion de la prueba
> preparados en **`infra/`**». Las **consultas** sí están en `infra/`; el
> **guion** está en `progress/`. Si el líder prefiere que esa frase sea literal,
> es un cambio de `features.json`, que **el implementer no toca**.

### 2.5 · La corrección de la referencia: solo el identificador

`design.md` está aprobado en review. Se cambió **una palabra, cuatro veces**, y
nada más. Se revisaron **una a una** las 30 menciones a `F-013` del repositorio:
todas las demás hablan de **mudar el archivo a la biblioteca de Posventa** y son
correctas. La única que quedaba, `progress/spec_F-009.md`, es un **informe
fechado**: reescribirlo sería falsear lo que un agente concluyó ese día, así que
**se deja la frase** y se le añade debajo la nota de corrección con su fecha
—que es como este mismo repositorio anota las correcciones—.

---

## 3 · Un bug que habría reventado el script, y que se cazó antes de entregarlo

Escrito el `13`, la primera versión usaba **backticks como comillas** dentro de
cadenas —`"la tabla `gra`…"`—, que es como se citan los identificadores en el
Markdown de este repositorio. **En PowerShell el backtick es el carácter de
escape**, así que dentro de una cadena de comillas dobles:

- `` `t `` de «`tex`» es un **tabulador**
- `` `n `` de «`nom`» es un **salto de línea**
- `` `r `` de «`rcg`» es un **retorno de carro**
- `` `v `` de «`vin`» es un **tabulador vertical**

Los mensajes habrían salido rotos, y `` `u `` de «`url`» es directamente un
**error de sintaxis en PowerShell 7**. Se corrigieron **18 líneas** (backtick →
comilla simple), respetando los backticks de continuación de línea y los del
bloque de ayuda, donde son inofensivos.

**Cómo se cazó, y es reproducible sin ejecutar nada:**

```
[System.Management.Automation.Language.Parser]::ParseFile($ruta, [ref]$tokens, [ref]$errores)
```

```
OK infra\08_lectura_sigrid_comun.ps1
OK infra\13_caracterizacion_grafico_url.ps1
```

Parsear **no ejecuta**: valida sintaxis sin abrir una sola conexión. Es la única
verificación automática posible sobre un script cuya ejecución está prohibida
desde aquí.

---

## 4 · Fase RED · por qué no la hay, y no es una excusa

F-023 tiene rigor `critico`, y el rigor `critico` exige la fase RED **con la
traza del fallo pegada**. **Aquí no hay ninguna, y el motivo es que no hay
código que testear:**

- **No se ha tocado `services/`.** Ni una línea de Python, ni un test.
- Lo entregado son **un script PowerShell que no se puede ejecutar desde aquí**
  (ejecutarlo es consultar producción, y el encargo lo prohíbe expresamente),
  **tres documentos Markdown** y **cuatro palabras** en una spec.
- La suite del proyecto **no cubre `infra/`**, y crear un arnés de tests de
  PowerShell para este script sería inventarse una infraestructura que el
  proyecto no tiene, para un fichero que se lanza a mano una vez.

**Esto no exime a F-023.** Cuando la feature se implemente —con su spec, después
de la prueba de Posventa— la fase RED será obligatoria y con traza pegada. Lo
que no se puede es fingirla en un encargo que no escribió código.

Lo que **sí** se verificó, y está arriba: el **parser de PowerShell** en verde
sobre los dos scripts (§3), y `bash harness/init.sh` en verde (§5).

---

## 5 · Evidencias

Números **medidos**, de la ejecución de `bash harness/init.sh` al terminar:

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados** y resultado | **56 passed**, 0 fallos | `pytest` del arnés |
| Suites por servicio | `api` y `front` **en verde** | caché del arnés: **árbol sin cambios** desde el último verde, coherente con no haber tocado `services/` |
| **Cobertura de las líneas cambiadas** | **98,8 %** — 565/572, umbral 80 %, nivel `critico` | línea `PUERTA COBERTURA` de `init.sh` |
| **Tiempo de la suite** | **4,02 s** | el que imprime `pytest` |
| **Mutantes generados / supervivientes** | **No aplica: no se ha cambiado ni una línea de Python.** Lanzar una campaña sobre el código de F-009, que no he tocado, mediría el trabajo de otro | `python -m harness.mutacion` no se ha ejecutado |
| Sintaxis de los scripts | **2 de 2 OK** | parser de PowerShell (§3) |
| Consultas ejecutadas contra sistemas reales | **0** | — |

> **Aviso honesto sobre la cobertura.** Ese 98,8 % es de **las líneas de F-009**,
> que ya estaban ahí: **este encargo no ha añadido ninguna línea de Python**, así
> que el número **no dice nada sobre este trabajo**. Se deja porque es la puerta
> que el arnés mide, no porque me avale.

---

## 6 · Verificaciones MANUALES pendientes

Ninguna de estas la puede hacer un agente.

| # | Qué | Quién | Cuándo |
|---|---|---|---|
| **M1** | **Reenviar la petición a Alicia Echevarría** (`progress/peticion_posventa_prueba_url_F-023.md`, de la línea de guiones en adelante) | El humano | Es **lo único** que bloquea F-023 |
| **M2** | Con su respuesta, lanzar el `13` con `-FechaPruebaPosventa` y `-CodigoReclamacionPrueba` | El humano | Después de M1 |
| **M3** | Lanzar el `13` **sin** esos dos parámetros para la caracterización (Q1…Q9) | El humano | Se puede hacer **ya**, no espera a Posventa |
| **M4** | Decidir si `features.json` debe decir `progress/` donde hoy dice `infra/` (§2.4) | El líder / el humano | — |

Sobre **M3**: el script pide la clave por consola si no está
`$env:SIGRID_API_KEY`, y necesita `-SigridBaseUrl`/`-SigridBaseDatos` o sus
variables de entorno. **Ningún valor de esos está en el repositorio**, y así se
queda.

---

## 7 · Lo que queda fuera, y una advertencia

**Fuera de este encargo, a propósito:**

- **El diseño de F-023 y su spec.** Sigue `blocked`. F-008 dejó escrito que la
  combinación de `vin`/`tex`/`nom` **no se debe diseñar sobre suposiciones**, y
  eso es exactamente lo que sería diseñarla hoy.
- **F-012.** Sus dos bloqueos son de otro repositorio y de su dueño.
- **El bloque 8 de F-009**, que sigue escrito y sin ejecutar.
- **Q2, Q6, Q7 y Q11** del informe. Q2 (¿es `ide` IDENTITY?), Q6 (`rcg.pos`) y
  Q7 (¿cabe la URL en el campo?) **no son de caracterización, son de diseño**:
  se contestan cuando F-023 se diseñe, y el encargo pedía las de
  caracterización. **Q11 no es una consulta**: es la lista de lo que ninguna
  lectura puede responder.

**La advertencia, que va en negrita porque es la que se olvida:** aunque el
script salga **entero en verde**, eso **no autoriza a escribir en `gra` ni en
`rcg`**. La pregunta que decide —qué escribe Sigrid al asociar una URL— **no la
contesta ninguna consulta de lectura**, sólo la prueba manual de Posventa. El
script lo dice en su última línea antes del veredicto, por si alguien llega ahí
sin haber leído esto.
