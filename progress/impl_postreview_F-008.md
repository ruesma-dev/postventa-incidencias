<!-- progress/impl_postreview_F-008.md -->
# F-008 · Correcciones tras el review

> `implementer` · 2026-08-26 · rama `feature/F-008-modelo-sigrid`
> (worktree `agent-a31450ce7b55c4c8d`)
> Encargo acotado: los **dos** cambios requeridos de `progress/review_F-008.md`
> §4. Nada más.

## Resumen

Los dos cambios están hechos. **Ni una consulta al ERP**: los dos se resolvían
con lo que ya estaba medido en el documento y en el informe, tal y como
anticipaba el reviewer. No se ha tocado código de producción, ni tests, ni
`harness/features.json`, ni `infra/`. `bash harness/init.sh` en verde.

## Cambio 1 · Las cifras que se contradecían

### 1.a · El «2.105» de §2.5

**Diagnóstico.** El 2.105 no estaba mal medido: estaba **mal etiquetado**. Es la
cifra de la tabla de §2.2 —reclamaciones **creadas** desde 2025 que **hoy** están
en `CER`, contadas por fecha de alta—, y la frase lo presentaba como «cierres con
Cerrar parte desde 2025», que es la población de §3 y se cuenta por **año de
cierre y proceso** (1.968 + 138 = 2.106, más 32 de RPV en 2025).

Son dos poblaciones distintas y ninguna contiene a la otra: una reclamación
creada en 2024 y cerrada en 2025 entra en la de §3 y no en la de §2.2; una
creada y cerrada en 2025 entra en las dos.

**Qué se ha escrito.** `docs/referencia/03_modelo_posventa_sigrid.md` §2.5 nombra
ahora la población explícita («las 2.105 reclamaciones creadas desde 2025 que hoy
están en `CER`, exactamente la población de la tabla de §2.2, contada por fecha
de alta») y añade una nota que deja las dos poblaciones separadas, con el 2.106
escrito y con el criterio de cada una. El hallazgo —29 cierres directos desde
PENDIENTE— no se ha tocado, solo se declara sobre qué denominador está medido.

**Lo que NO se ha hecho, y por qué.** No se ha recalculado el 29 sobre la
población de §3: eso exigiría volver al ERP, y el encargo lo prohíbe
explícitamente. La nota lo dice sin disimulo («el **29** está medido sobre la
primera, la de §2.2») en vez de dejar al lector suponiéndolo.

### 1.b · «Cerrar Preventas»: 4.899 frente a 4.892

**Diagnóstico.** También dos poblaciones, y de la misma clase que el desfase
6.843 / 6.590 que el propio reviewer dio por explicado en su §3.4: **4.899 son
ejecuciones** registradas en `dbo.log`, y **4.892 son reclamaciones** que hoy
están en `CER` cerradas por ese proceso, que es lo único sobre lo que se puede
medir «con gráfico» (el gráfico cuelga de la reclamación, no de la fila de log).

**Qué se ha escrito.** La nota de §3 declara las dos poblaciones con su unidad
—ejecuciones frente a reclamaciones—, mantiene las dos cifras y dice
expresamente que el desfase de 7 **no se ha investigado**, enumerando las causas
posibles (reejecuciones, cierres deshechos, cambios de estado posteriores) como
hipótesis y no como explicación medida.

### 1.c · La misma corrección en el informe

`progress/impl_F-008.md`, hallazgos **#10** y **#14**, reescritos para contar lo
mismo que el documento.

> **Discrepancia con el review, dicha en voz alta**: el review pide corregir
> «#10 y #12». El **#12 no contiene el 2.105** —su cifra es el 2.365 de «Cerrar
> parte» desde 2023, que cuadra con su tabla y que el propio reviewer validó en
> §3.4—. La segunda cifra descuadrada del informe es la del hallazgo **#14** (el
> 4.899 de «Cerrar Preventas»), que es la que se corresponde con el segundo punto
> del cambio requerido. Se ha corregido **#14** y se ha dejado **#12** intacto.
> Si el reviewer quería decir otra cosa en #12, aquí queda señalado para que lo
> confirme en la siguiente ronda.

## Cambio 2 · El hallazgo del `con.cod` sube a `docs/referencia/`

Nueva subsección **§1.1 · `con.cod`, el código que identifica la reclamación**,
justo detrás del catálogo de estados y antes de §2. Recoge:

- **Unicidad**, con el recuento que la sostiene: 23.063 conceptos `tip = 708`,
  23.063 códigos distintos, sin repetición entre obras ni entre años.
- **Formato** `RS{AA}.{MM}/{NNNN}`, desglosado, con el ejemplo `RS26.08/0123`.
- **No codifica la obra**: el secuencial es global del mes. Para saber la obra
  hay que ir a los datos de la reclamación, no a su código.
- **Es la clave de localización** para F-009: un solo filtro por `con.cod`, sin
  conocer obra ni unidad de postventa.
- **La trampa barra/guion**, enlazada —no reescrita— a
  `docs/referencia/01_cierre_incidencia_sigrid.md`, sección «La ficha de la
  reclamación», con un «no se repite aquí» explícito.

**Un matiz de rigor que se ha añadido, y que no estaba en el informe.** El
informe decía «único y **global**». Lo medido es la unicidad **dentro del tipo
708**; que un código no pueda repetirse en otro `con.tip` **no se comprobó**. El
documento lo dice así y saca la consecuencia práctica: el filtro por `cod` se
acota siempre con `con.tip = 708`. Se ha alineado el informe (hallazgos #21 y el
punto 5 de las recomendaciones para F-009), que era el sitio donde la palabra
«global» podía llevar a que F-009 buscara por `cod` a secas contra producción.

**De paso**: la fila de `03_modelo_posventa_sigrid.md` en
`docs/referencia/README.md` menciona ahora el `con.cod` como clave de
localización, para que el hallazgo se encuentre desde el índice. Es una línea,
no cambia la estructura de la tabla (verificado: la fila sigue en un solo
renglón).

## Ficheros tocados

| Fichero | Qué cambia |
|---|---|
| `docs/referencia/03_modelo_posventa_sigrid.md` | §1.1 nueva (`con.cod`); §2.5 con la población explícita y la nota de las dos poblaciones; nota de «Cerrar Preventas» en §3 reescrita |
| `docs/referencia/README.md` | La fila del documento 03 menciona el `con.cod` |
| `progress/impl_F-008.md` | Hallazgos #10, #14 y #21 cuadrados con el documento; punto 5 de las recomendaciones para F-009 |

Ni un fichero de código. Ni un test. Ni `harness/`. Ni `infra/`.

## Verificación

### Fase RED

**N/A por el nivel declarado.** F-008 es `rigor: "documental"`
(`fase_red: false` en `harness/rigor.json`), y además esta ronda **no toca
código**: no hay comportamiento que pueda fallar antes de existir. Escribir un
test para un párrafo de Markdown sería teatro.

### La comprobación que sí se puede hacer sobre un documento: que las cifras cuadren

Hecha a mano, releyendo las tablas que ya estaban en el documento:

| Comprobación | Resultado |
|---|---|
| §2.2: 85 + 839 + 1.474 + 258 + 2.105 | **4.761**, el total declarado. Cuadra |
| §3, «Cerrar parte» 2025 + 2026: 1.968 + 138 | **2.106**, la cifra que ahora aparece escrita en la nota de §2.5 |
| §1: 23.063 − 21.554 | **1.509**, el hueco declarado. El 23.063 de §1.1 es el mismo número de §1, no uno nuevo |
| Barrido de `2.105 / 2.106 / 4.899 / 4.892` en documento e informe | 8 apariciones, todas con su población escrita al lado. Ninguna cifra suelta |

### `bash harness/init.sh`

Ejecutado **tal cual**, sin pipes ni decoración, en el worktree. Última ejecución
(después del último cambio):

```
[OK] Arnés v1.5.2 (2026-08-18)
     20 features, 12 abiertas, en curso: ['F-008'], bloqueadas: ninguna
[OK] features.json válido
[OK] BACKLOG.md al día
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 58 avisos (deuda previa, no bloquea).
17 passed in 0.81s
[OK] pytest en verde (con medición de cobertura)
[OK] servicio api (services/postventa-api): pytest en verde
[OK] servicio front (services/postventa-front): pytest en verde
[OK] PUERTA COBERTURA: N/A (F-008 es de nivel documental: no exige cobertura)
[OK] Rama actual: feature/F-008-modelo-sigrid
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

El aviso de `ruff: 58` es **deuda previa idéntica a la de antes de esta ronda**:
esta ronda no añade ni un fichero de código.

## Evidencias

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** | 17 del arnés + suites de los servicios `api` y `front`. **Todos en verde**. Los dos servicios resueltos por caché de árbol sin cambios: esta ronda no toca ni un fichero suyo |
| **Tiempo de la suite** | `17 passed in 0.81s` (arnés). Servicios, desde caché |
| **Cobertura de las líneas cambiadas** | **N/A, con motivo impreso por el propio portero**: `PUERTA COBERTURA: N/A (F-008 es de nivel documental: no exige cobertura)`. Y materialmente no hay líneas de código cambiadas que cubrir: los tres ficheros tocados son Markdown |
| **Mutantes generados y supervivientes** | **N/A**: `mutacion: false` para el nivel `documental`, y no hay código de producción en el diff de esta ronda. No existe `progress/mutacion_F-008.md` **y no debe existir**, por el mismo motivo que razonó el reviewer en su §1 |
| **Consultas al ERP** | **cero**, que era la restricción dura del encargo. Los dos cambios salen de cifras ya medidas en `03_modelo_posventa_sigrid.md` y en `impl_F-008.md` |

## Verificaciones MANUAL (humano) pendientes

Las cuatro de `progress/impl_F-008.md` §7 siguen abiertas: **esta ronda no
resuelve ninguna y no añade ninguna nueva**. Se suman dos puntos de decisión que
nacen de esta ronda:

1. **Confirmar la lectura del «2.105»** — se ha fijado como la población de §2.2
   (creadas desde 2025, hoy en `CER`) porque es la cifra que coincide
   exactamente. Si quien hizo la medición recuerda que la consulta del «29» fue
   sobre los cierres y no sobre las creadas, el denominador correcto sería el
   2.106 y habría que remedirlo **contra el ERP**, cosa que este encargo
   prohibía. Queda escrito para que la decisión sea consciente.
2. **El «#12» del review** — ver la nota del cambio 1.c: el hallazgo corregido
   ha sido el #14, porque el #12 no contiene la cifra en disputa.

## Qué queda fuera de esta ronda

- Recalcular cualquier cifra contra Sigrid.
- Los seis puntos no confirmados de §5 del documento, que siguen igual de no
  confirmados y así declarados.
- Marcar F-008 `done` y tocar `harness/features.json`: es del líder, tras el
  APROBADO del reviewer.
