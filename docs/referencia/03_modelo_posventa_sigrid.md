<!-- docs/referencia/03_modelo_posventa_sigrid.md -->
# El modelo de posventa en Sigrid, confirmado contra el ERP

> Origen: **consultas de solo lectura contra el ERP de producción**, a través de
> `sigrid-api` (`POST /api/sql/read`), bases `ruesma` y `ruesma_rep`.
> Fecha de las consultas: 2026-08-25 (F-008).
> No llegó como documento: **no hubo conversión con `markitdown`** porque no hay
> original que convertir. Lo que hay aquí se midió; la sección final dice qué
> quedó sin confirmar.
> **Redactado**: los logins de usuario de Sigrid aparecen como `<usuario>`. No
> se recoge ningún nombre, DNI ni dato de propietario: las consultas se
> diseñaron para no traerlos.

**Ni una escritura.** Toda la información de este documento sale de sentencias
`SELECT`. `sigrid-api` sirve la lectura con un usuario SQL de solo lectura
(`ro_user`), que no tiene permisos de escritura en el propio SQL Server.

## Qué no está aquí

El modelo de datos general de Sigrid y el contrato de la pasarela **no se
copian**: viven en el repositorio del ecosistema y esta es la única referencia.

| Para | Ve a |
|---|---|
| Diccionario de tablas, campos, tipos e índices | `azure-apps/sigrid_tablas.md` |
| La pasarela, sus endpoints y sus límites (1.000 filas, 230 s) | `azure-apps/sigrid_api.md` |
| Conceptos, `ide`, `con.tip`, `con.est` y `conest` | `azure-apps/sigrid_api.md` §9.1–9.3 |
| El procedimiento de negocio, tal y como lo hace Posventa | `docs/referencia/01_cierre_incidencia_sigrid.md` |

Este documento añade **solo lo que no estaba en ninguno de los tres**: los
valores reales de esta instalación y qué escribe de verdad cada proceso.

---

## 1 · El tipo de concepto y sus estados

**`con.tip = 708`** es la reclamación de posventa. La extensión 1:1 es `rcp`
(«Reclamación»), que cuelga de `upv` («Unidad Postventa») por `rcp.upvide`.

Verificado: 21.554 filas en `rcp`, todas con `con.tip = 708`; 23.063 conceptos
de tipo 708 en `con` (1.509 sin fila en `rcp`, resto histórico no investigado).

Los estados salen de `conest` con el join estándar
`con.tip = conest.tip AND con.est = conest.est`:

| `est` | `cod` | `res` | `edi` | Reclamaciones (todas) |
|---:|---|---|---:|---:|
| 1 | `SAT` | SIN ATENDER | 0 | 1.989 |
| 3 | `PTE` | PENDIENTE | 0 | 1.011 |
| 5 | `TER` | TERMINADA | 1 | 3.757 |
| 7 | `NPR` | NO PROCEDE | 1 | 656 |
| **9** | **`CER`** | **CERRADA** | 1 | **14.141** |

- **El estado de cierre es `CER` / `CERRADA`.** Hoy vale `9`, pero el número es
  configurable por instalación: se resuelve consultando `conest` por **`cod`**,
  nunca escribiendo el 9.
- Se **confirma** que el estado pendiente es `3 / PTE`, como decía la guía de
  Posventa.
- `conest.edi` es «Editable 0 sí / 1 no». Los tres estados finales (`TER`,
  `NPR`, `CER`) están marcados **no editables**: una vez cerrada, Sigrid bloquea
  la edición de la ficha en pantalla.

## 2 · Qué escribe de verdad «Cerrar parte»

La respuesta corta: **`con.est` y una fila en `dbo.log`. Nada más.**

### 2.1 · La comparación fila a fila

Se compararon una reclamación **CERRADA** y una **PENDIENTE** de la misma obra
(0677, Mirasierra) y del mismo mes, columna a columna sobre `con` y `rcp`, más
el recuento de todas las tablas que cuelgan de la reclamación.

Todo lo que difiere y **no** es intrínseco a ser dos reclamaciones distintas
(`ide`, `cod`, `fec`, `hor`, `pos`, `upvide`, ubicación, oficio):

| Qué | CERRADA | PENDIENTE |
|---|---:|---:|
| `con.est` | 9 | 3 |
| Filas en `rcg` (gráficos) | 1 | 0 |

Idénticos en las dos: `emp`, `tip`, `subtip`, `cee`, `fecbaj`, `serie`, `doc`,
`ico`, `hor`, y en `rcp` todos los campos de contenido. Igual número de
intervinientes (`rcpint`) y de tareas (`tar`), y cero actuaciones (`act`) en
ambas.

### 2.2 · Y el mismo resultado sobre toda la población

La pareja sola no probaría nada, así que se repitió como agregado sobre las
**4.761 reclamaciones creadas desde 2025**, agrupando por estado:

| Estado | Total | Con gráfico | Con actuación (`act`) | Con interviniente | Con solución (`rcp.solrcp`) | Con `fecpre` |
|---|---:|---:|---:|---:|---:|---:|
| `SAT` | 85 | 1 | 0 | 85 | 0 | 0 |
| `PTE` | 839 | 11 | 0 | 839 | 0 | 0 |
| `TER` | 1.474 | 19 | 0 | 1.469 | 0 | 0 |
| `NPR` | 258 | 173 | 0 | 254 | 0 | 0 |
| `CER` | 2.105 | **2.102** | 0 | 2.105 | 0 | 0 |

- `act` (actuaciones/seguimiento) está **vacía** para reclamaciones: el proceso
  no escribe seguimiento.
- `rcp.solrcp` («Solución de la reclamación») y `rcp.fecpre` **nunca** se
  rellenan, en ningún estado.
- `rcpint` y `tar` existen desde el alta, no desde el cierre; y en `tar` ningún
  campo de avance (`fecreaini`, `fecreafin`, `porcen`, `blofin`, `tiphit`) se
  mueve con el estado de la reclamación.
- `con.fecbaj` está a 0 en las 21.554 reclamaciones: cerrar **no** es dar de baja.

### 2.3 · `con.tiemod` NO se actualiza al cerrar

Contraintuitivo y verificado: `tiemod` es el campo de auditoría estándar de
Sigrid, pero **el proceso no lo toca**.

En los **138 cierres registrados en 2026**, la fecha de `con.tiemod` es
**estrictamente anterior** al día del cierre. Ni uno igual, ni uno posterior.

> En la reclamación de ejemplo, `tiemod` marca `2026-08-06 09:26:33` y el cierre
> ocurrió el `2026-08-18 a las 11:46:33`.

Consecuencia: **no se puede fechar un cierre mirando la ficha**. La única marca
temporal del cierre está en el log.

### 2.4 · La fila de `dbo.log`, que es la otra mitad del proceso

Sigrid registra cada proceso ejecutado en la tabla `dbo.log`. Es lo que un
`UPDATE` directo se dejaría por el camino, y por eso importa.

Forma de la fila que escribe «Cerrar parte» (6.843 filas, todas idénticas en
estructura):

| Columna | Valor |
|---|---|
| `tab` | `con` |
| `tip` | `708` |
| `cod` | el código de la reclamación (p. ej. `RS26.08/0123`) |
| `res` | la descripción de la reclamación, copiada de `con.res` |
| `ope` | `5` (= proceso ejecutado) |
| `tex` | **`Cerrar parte`** |
| `est` | `1` |
| `emp` | `1` |
| `ori` | `0` |
| `usu` | el login de quien lo ejecuta (`<usuario>`) |
| `fec` / `hor` | fecha `AAAAMMDD` y hora `HHMMSS` |

Códigos de `ope` observados para `tip = 708`: `1` alta, `2` baja, `3`
modificación de campo (con `tex` = `campo: [nuevo] <= [viejo]`), `5` proceso,
`6` acción, `30` **DESHACER** proceso.

**Los cierres se pueden deshacer**: hay 81 filas `DESHACER proceso (Cerrar
parte)`, la última de 2025-10-06. F-009 no puede asumir que un cierre es
irreversible ni que el estado que dejó sigue ahí.

### 2.5 · Desde qué estado se lanza

No exige pasar por TERMINADA. De los **2.105** cierres con «Cerrar parte» desde
2025, **29 se hicieron directamente desde PENDIENTE** sin que la reclamación
hubiera pasado nunca por «Pasar a terminada».

La reclamación de ejemplo de la guía de Posventa es una de ellas: su log
completo son tres filas —alta, `Pasar a pendiente`, `Cerrar parte`—, y la ficha
mostraba `3 (PTE : PENDIENTE)` el mismo día en que se cerró.

El camino mayoritario, aun así, es `PTE → «Pasar a terminada» → TER → «Cerrar
parte» → CER`.

## 3 · «Cerrar parte sin archivo (RPV)», la opción 6

**Termina en el mismo sitio**: `con.est = 9` (`CER`). No deja la reclamación en
un estado distinto ni escribe columnas distintas. Lo único que cambia es que
**se salta la comprobación del gráfico**, y los datos lo demuestran.

Reclamaciones que hoy están en `CER`, según el proceso que las cerró y el año:

| Proceso | Año | Reclamaciones | Con gráfico | **Sin gráfico** |
|---|---:|---:|---:|---:|
| Cerrar parte | 2021 | 1.849 | 1.807 | 42 |
| Cerrar parte | 2022 | 2.376 | 1.295 | 1.081 |
| Cerrar parte | 2023 | 241 | 241 | **0** |
| Cerrar parte | 2024 | 18 | 18 | **0** |
| Cerrar parte | 2025 | 1.968 | 1.968 | **0** |
| Cerrar parte | 2026 | 138 | 138 | **0** |
| Cerrar parte sin archivo (RPV) | 2022 | 636 | 149 | 487 |
| Cerrar parte sin archivo (RPV) | 2023 | 553 | 277 | 276 |
| Cerrar parte sin archivo (RPV) | 2024 | 1.457 | 1.348 | 109 |
| Cerrar parte sin archivo (RPV) | 2025 | 32 | 24 | 8 |

Cómo se lee:

- **Desde 2023, «Cerrar parte» tiene cero excepciones**: 2.365 cierres, 2.365
  con gráfico. La comprobación que anuncia el mensaje de confirmación se cumple
  en los datos. (Las excepciones de 2021–2022 son anteriores y no se ha
  investigado si el gráfico se borró después o si el control se introdujo más
  tarde.)
- **RPV sí deja reclamaciones cerradas sin ningún gráfico**, todos los años en
  que se usó. Es la prueba empírica de que se salta el control.
- **RPV está abandonado**: última ejecución el **2025-03-11**. Desde entonces
  Posventa cierra siempre con «Cerrar parte» (última, 2026-08-18).

En el log el nombre completo es `Proceso ejecutado (Cerrar parte sin archivo
(RPV))`, con la misma forma de fila que en §2.4.

> Hay un tercer proceso de cierre, **«Cerrar Preventas»** (4.899 ejecuciones,
> ninguna desde 2024-11-27): cierre masivo de preventa que también deja `est = 9`
> y prácticamente nunca lleva gráfico (3 de 4.892). No es el camino de Posventa.

## 4 · El gráfico: dónde vive y de qué está hecho

### 4.1 · Son DOS tablas `gra`, en dos bases distintas

Esto es lo que más fácil se malinterpreta:

```
ruesma                                    ruesma_rep
├── con      (la reclamación, tip=708)    └── gra   357.901 filas
├── rcg      con → gra   (el enlace)            └── ima  ← EL BINARIO, siempre
└── gra      282.599 filas
      └── ima  VACÍO para posventa
```

- **`ruesma.gra`** guarda los **metadatos** del documento. Es la que enlaza
  `rcg` (`rcg.con` → la reclamación, `rcg.gra` → el gráfico).
- **`ruesma_rep.gra`** guarda el **binario** en `ima`. Las 357.901 filas tienen
  contenido; ninguna está vacía.
- **Los `ide` de las dos tablas son espacios independientes.** El mismo `ide` en
  una y otra es documentos distintos. Comprobado con un caso: `ide` 296221 es el
  parte firmado en `ruesma`, y un PDF ajeno de junio de 2025 en `ruesma_rep`.
- **La pareja se localiza por `gra.cod`**, no por `ide`. De los 13.450 gráficos
  de reclamaciones, **13.399 (99,6 %)** tienen su binario en `ruesma_rep.gra`
  con el mismo `cod`.

`gra.vin` («Vinculado») indica el modo de almacenamiento. Para **los 13.450
gráficos de posventa vale siempre `3`** — el «[INCRUSTADO EXTERNO]» que enseña
la pantalla — y en ese modo `ruesma.gra.ima` y `ruesma.gra.tex` («Camino») están
**vacíos**. Reparto en toda la tabla: `vin=3` 282.405, `vin=2` 154, `vin=0` 38
(los únicos con binario dentro de `ruesma`), `vin=1` y `vin=4` uno cada uno.

### 4.2 · Cómo queda un parte firmado, campo a campo

La ficha de la reclamación de ejemplo, ya cerrada, confirma exactamente lo que
la guía de Posventa dedujo de la pantalla:

| Columna | Valor | Campo de la pantalla |
|---|---|---|
| `gra.cod` | `202608181140392614.<usuario>` | Código (sello de tiempo `AAAAMMDDHHMMSS` + 4 dígitos + login) |
| `gra.res` | `PARTE FIRMADO` | **Descripción** ← lo teclea Posventa |
| `gra.nom` | `RS26.08 - 0123 PARTE FIRMADO.pdf` | Archivo / Ubicación / URL |
| `gra.gratipide` | `35` → `auxgra` `PV002` `POSTVENTA:Fotos Reparaciones` | **Tipo gráfico** ← lo elige Posventa |
| `gra.fec` | `20260818` | Fecha de incorporación |
| `gra.vin` | `3` | (incrustado externo) |
| `gra.ima`, `gra.tex`, `gra.guid`, `gra.cla` | vacíos | Clave, Revisión, Descripción larga |
| `ruesma_rep.gra.ima` | 242.534 bytes | el PDF de verdad |
| `rcg.con` / `rcg.gra` | la reclamación / el gráfico | el enlace |
| `rcg.pos` | `64` (múltiplos de 64, 52 posiciones distintas en uso) | orden |
| `rcg.cla`, `rcg.fecalt`, `rcg.feclee` | `0` en los 13.450 enlaces | — |

**El orden del procedimiento queda datado**: el gráfico se dio de alta a las
`11:40:39` y el proceso «Cerrar parte» corrió a las `11:46:33` del mismo día.
Primero el documento, después el cierre.

Los tipos de documento de Posventa en `auxgra`, todos activos (`fecbaj = 0`) y
sin límite de tamaño configurado (`tammax = 0`):

| `ide` | `cod` | `res` | `tipaso` (a qué se puede asociar) |
|---:|---|---|---|
| 34 | `PV001` | POSTVENTA: Fotos de incidencias | `UPV,RCP,TAR` |
| **35** | **`PV002`** | **POSTVENTA:Fotos Reparaciones** | `UPV,RCP,TAR` |
| 36 | `PV003` | POSTVENTA:Manual Post Venta | `UPV,RCP,TAR` |
| 37 | `PV004` | POSTVENTA: Informes | `UPV,RCP,TAR` |
| 38 | `PV005` | POSTVENTA: Plano tipo inmueble | `UPV,OBR` |
| 39 | `PV006` | POSTVENTA: Ficha de inmueble | `UPV` |

`tipaso` incluye `RCP`, que es lo que autoriza a colgar el documento de una
reclamación.

### 4.3 · ¿Puede un gráfico ser una URL a SharePoint?

**Respuesta honesta: no se puede afirmar que sí, y no hay ni un precedente.**

Lo buscado y lo encontrado, sobre las **282.599** filas de `ruesma.gra`:

| Búsqueda | Resultado |
|---|---:|
| `cod` que empieza por `http` | **0** |
| `tex` («Camino») que empieza por `http` | **0** |
| `nom` que empieza por `http` | **1** |
| Cualquier campo que mencione `sharepoint` | **0** |

Esa única coincidencia **no es una URL asociada**: es un nombre de fichero
derivado de una dirección web (los puntos y barras eliminados, terminado en
`.png`), guardado con `vin = 3`, es decir, como binario externo normal. Es una
captura de pantalla con un nombre feo, no un enlace.

Conclusión: la opción **«Asociar URL de Internet…» existe en el menú *Importa***
(la documenta la guía de Posventa, §«Lo que se rellena al importar el gráfico»),
pero **no se ha usado nunca en esta instalación**, así que no hay ninguna fila
de la que deducir con qué combinación de `vin`, `tex` y `nom` se guardaría.

**Deducido, no verificado**: lo razonable sería que el modo se distinga por
`gra.vin` (los valores `1` y `4` tienen un único uso cada uno y no se han
inspeccionado a fondo) y que la dirección viaje en `gra.tex` («Camino», texto
ilimitado) o en `gra.nom`. **No se debe diseñar F-009 sobre esta suposición.**
Confirmarla exige una prueba en un entorno de pruebas de Sigrid, o preguntar al
proveedor del ERP. Y aunque se confirmara, quedaría abierto si «Cerrar parte»
acepta un gráfico-URL como documento válido para su comprobación.

---

## 5 · Lo que NO se ha podido confirmar

Explícito, porque F-009 va a escribir en producción y una suposición vestida de
dato es lo que provoca un desastre:

1. **Qué hace el proceso por dentro.** Aquí se ha medido su **efecto
   observable** comparando estados y poblaciones, no leído su código. Si «Cerrar
   parte» escribiera en una tabla que no se ha mirado, no se habría visto. Se
   revisaron `con`, `rcp`, `rcg`, `gra`, `rcpint`, `tar`, `act` y `log`.
2. **Si la comprobación del gráfico es bloqueante o solo un aviso.** Se sabe que
   desde 2023 no hay ni un cierre con «Cerrar parte» sin gráfico —lo que es
   consistente con que bloquee— pero eso no se ha provocado: habría hecho falta
   intentar cerrar, y eso es una escritura.
3. **Cómo se guarda una URL asociada** (§4.3): sin precedentes en la base.
4. **Si «Cerrar parte» dispara efectos fuera de la base de datos** (correos,
   avisos). «Rechazar reclamación» tiene dos variantes explícitas, *envía email*
   y *NO enviar email*, así que el ERP sí manda correos en algunos procesos.
   Para «Cerrar parte» no hay ninguna señal en la base, ni a favor ni en contra.
5. **Los 1.509 conceptos `tip = 708` sin fila en `rcp`**: no se ha investigado
   qué son.
6. **Si la escritura de `sigrid-api` está habilitada hoy** para esta instalación.
   Va apagada por defecto (`azure-apps/sigrid_api.md` §7.2) y comprobarlo con
   una escritura queda fuera del alcance de F-008.
