<!-- progress/impl_F-072_despliegue.md -->
# F-072 · Despliegue y verificación en producción (T24, T26)

`progress/impl_F-072.md` está en su tope de líneas (220/220): las notas del
Bloque 8 van aquí.

## T24 · publicación (humano) y comprobación (líder), 2026-11-18

- **Publicado por el humano** con `publicar_f072.ps1` (push de `dev` y de
  `azure-apps`, y `desplegar_backend.ps1` desde una copia limpia de `dev`).
  `origin/dev` = `a269341` (merge de F-072). La Function se reinició a las
  18:51 UTC.
- **Comprobación del líder**, por el front y con la sesión del humano, solo
  lecturas:
  - `GET /api/health` → 200, `estado: ok`.
  - `GET /api/bandeja?obra=0677` → 200, 200 incidencias, `listado` = `0002`
    en todas (el **tipo efectivo**; nunca `null`). La sentencia ya lee
    `tipo_reclamacion`: el DDL `17_tipo_reclamacion.sql` está aplicado.
  - Application Insights (`appi-postventa-dev`, la última hora): **0
    excepciones**, ninguna traza de nivel aviso o superior. Primera petición
    a la base sin error.

## T26 · pasos de solo lectura (líder), 2026-11-18

1. **Plantilla** (`GET /api/plantilla?obra=0677`, 200, 36 KB, 9,5 s): la
   columna H (`Listado`) valida contra `lista_listados` =
   `_catalogos!$E$2:$E$5`, con `PREVENTA (0001)`, `PRIMER LISTADO POSTVENTA
   (0002)`, `POST VENTA (0003)` y `VISITA DE CORTESIA (0004)`, en ese orden,
   como `<res> (<cod>)`.
2. **Revisión** (`GET /api/revision?obra=0677`): `catalogo.listados` son los
   mismos cuatro como `{codigo, etiqueta}`; en las 200 incidencias de la
   página, `vigentes.listado` e `importados.listado` = `0002` (ninguno
   nulo); `tipo_fuera_de_sigrid` = 0 en el resumen. Tiempos: 13,8 s en frío,
   0,8 s y 5,1 s después (antes de F-072, M2: p50 5,00 s, máximo 13,21 s en
   caliente).
5. (parte de lectura) Application Insights: la línea `F-072 tipos de
   reclamación leídos en Sigrid: tipos=4 sin_codigo=0 repetidos=0
   al_techo=False segundos=…` sale **sin `res`** (entre 0,10 s y 4,37 s).

## T26 · pasos con escritura en la base propia (líder), 2026-11-18

Con la autorización concreta del humano en el chat («si» a la lista de los
pasos 3–6). Por la API del front, con la sesión del humano; **nada en
Sigrid**: solo `POST /api/volcado/ensayo`, nunca `/api/volcado/volcar`.

3. **Importación** de la plantilla de la 0677 con tres filas «PRUEBA F-072 -
   DESCARTAR (A/B/C)» (misma unidad, ubicación y par oficio · proveedor):
   200, `estado: parcial`, `nuevas: 2`, `con_error: 1`. C («Segundo
   listado») vuelve en el Excel de errores: columna `Listado`, «ese valor no
   está en la lista de listados». En la revisión, A con `listado` `0002`
   (en blanco) y B con `0003`, las dos sin motivos.
4. **Editar A** con `listado` `0003`: 200, `editada`, `vigentes.listado`
   `0003`, y `cambios` marca `listado`. **Observación (fuera de F-072):**
   `cambios` marca también `proveedor` sin haberlo tocado: al editar, el
   nombre del proveedor se relee de Sigrid con un espacio al final
   (`proveedor_nombre` termina en espacio) y al importar se guardó recortado.
   F-072 no toca proveedores; queda para una corrección aparte.
5. **Aprobar B**: 200, `aprobada`, `listado` `0003`. **Ensayo** de B: 200 en
   6,3 s, `previstos: 1`, sin excluidas, sin rechazos y sin conflictos de la
   guarda; el `envio` lleva `tipo: "0003"` y el parte sale `previsto`. Sin
   volcado: el ensayo caduca solo a los 30 minutos.
6. **Descartar A y B** (motivo «Prueba de F-072»): 200, las dos
   `descartada`.

Application Insights, después: ninguna traza de aviso o superior de la
aplicación y una sola excepción, `ConnectionAbortedException` del host de
Functions a las 18:57 (corte del stream de logs, sin operación asociada), que
no es de este código. Todas las peticiones, 200.

**T26 en verde.**
