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

Pasos 3–6 (importar las tres filas de prueba, editar, aprobar, ensayo y
descartar): escriben en la base propia de producción; **pendientes** de la
autorización concreta del humano.
