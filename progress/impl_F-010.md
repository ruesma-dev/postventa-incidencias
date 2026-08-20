# F-010 · Despliegue en Azure y tarjeta en el portal — informe de implementación

> Rama `feature/F-010-despliegue`. Rigor **`estandar`**. Informe **incremental**:
> se escribe y se commitea tarea a tarea, no al final.
>
> **Ni un valor real en este fichero**: ni FQDN, ni GUID, ni identificador de
> suscripción, inquilino, sitio o aplicación. Solo nombres de recurso y nombres
> de variable.

---

## Estado de las tareas

| Tarea | Estado | Nota |
|---|---|---|
| T1 · MANUAL | Pendiente (humano) | Crear `posventa-usuarios` en Entra |
| T2 · MANUAL, alimenta **D2** | **MEDIDA** — ver abajo | La ejecutó el implementer a petición del líder |
| T3 | Pendiente | |
| T4 | Pendiente | |
| T5 | **Bloqueada por D2** | Fija `IA_TIMEOUT_S` y `GRAPH_TIMEOUT_S` |
| T6 | Pendiente | |
| T7 | Pendiente | |
| T8 | Pendiente | |
| T9 | **Bloqueada por D2** | Fija `TIMEOUT_PETICION_MS` |
| T10–T12 | Pendiente | |
| T13–T19 · MANUAL | Pendientes (humano) | |
| T20–T21 | Pendientes | Cierre |

---

## T2 · La medición de D2 · los 45 s del proxy

**Qué se midió y cómo.** Contra la Function arrancada **en local**
(`localhost:7073`, ya en marcha en el puesto: el puerto estaba ocupado y
respondía `GET /api/health` con `200`), con un guion de biblioteca estándar
—**no se añadió ninguna dependencia al proyecto**— que llama a los endpoints
por HTTP igual que lo hace el front. El guion vive en el directorio temporal de
la sesión, **no en el repositorio**.

Entrada: la remesa escaneada real que ya está en el árbol de trabajo sin
versionar (5.286 KB, **22 partes** tras el troceado). No se imprimió ni se
guardó **ningún** campo del parte: solo segundos y códigos HTTP, como exige la
verificación de T2 («sin nombres de obra, sin códigos de incidencia y sin
DNI»).

**Salida real del guion:**

```
remesa: 5286 KB
split: 2.4s -> 200
partes troceados: 22
--- secuencial (2 partes, una peticion viva) ---
extraer: 5.5s -> 200
firma: 4.1s -> 200
extraer: 5.2s -> 200
firma: 4.1s -> 200
--- concurrente (3 partes = 6 peticiones vivas, como el front) ---
extraer: 6.2s -> 200
firma: 5.1s -> 200
extraer: 6.1s -> 200
firma: 5.2s -> 200
extraer: 6.5s -> 200
firma: 5.5s -> 200
lote completo: 6.5s
```

**Los tres números que pedía T2 (peor caso observado de cada endpoint):**

| Endpoint | Peor caso, 1 petición viva | Peor caso, 6 peticiones vivas |
|---|---|---|
| `POST /api/split` (22 partes, 5,2 MB) | **2,4 s** | — (se llama una sola vez) |
| `POST /api/extraer` | 5,5 s | **6,5 s** |
| `POST /api/firma` | 4,1 s | **5,5 s** |

El segundo bloque es el que importa: reproduce lo que hace el front de verdad
con `CONCURRENCIA_PARTES: 3` —tres partes vivos, seis peticiones simultáneas—
contra **un solo worker** de `func start`. La concurrencia sube el peor caso
de 5,5 s a 6,5 s, un 18 %.

**Lectura contra el criterio de decisión de T2.** El criterio escrito era: *«si
el peor `/api/extraer` queda holgadamente por debajo de 35 s, se sigue con la
opción (a) de D2»*. El peor `/api/extraer` medido es **6,5 s**, un **14 % del
presupuesto de 45 s** del proxy y menos de la quinta parte de los 35 s
propuestos. Cabe con holgura.

**Matices que el humano debe tener delante antes de decidir, porque la
medición es en local y el despliegue no lo es:**

1. **No incluye el salto de región.** Se midió puesto → Function local. En
   producción hay un tramo más: navegador → Static Web App (`westeurope`) →
   Function (`spaincentral`). `design.md` §4 ya avisa de que ese salto se paga
   y se descuenta del presupuesto. Con 6,5 s medidos contra 45 s de tope, el
   margen absorbe ese tramo sin discusión.
2. **No incluye el arranque en frío** de una Function App en Flex Consumption,
   que la primera petición del día sí paga.
3. **La latencia del proveedor de IA no la controlamos**: 6,5 s es lo medido
   hoy con `gemini-3.7-flash`; un día malo del proveedor o un parte con más
   páginas sube ese número, y por eso el tiempo de espera sigue haciendo falta.
4. **`split` no escala con el tamaño como se podría temer**: 22 partes de una
   remesa de 5,2 MB en 2,4 s. No es el endpoint en riesgo.

**Decisión pendiente, y por eso esta feature está parada aquí.** El implementer
**no fija los valores nuevos**: T5 (`IA_TIMEOUT_S`, `GRAPH_TIMEOUT_S`) y T9
(`TIMEOUT_PETICION_MS`) quedan sin tocar hasta que el humano decida con estos
números delante. Lo que la spec propone es la opción (a): 35 s y 40000 ms.

**Coste de la medición**: diez llamadas reales al proveedor de IA
(cuatro secuenciales y seis concurrentes) más un troceado. Ninguna escritura,
ningún recurso de Azure tocado, nada subido a SharePoint.
