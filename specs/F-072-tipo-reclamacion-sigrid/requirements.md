<!-- specs/F-072-tipo-reclamacion-sigrid/requirements.md -->
# F-072 · El tipo de reclamación sale de Sigrid (auxtrcp) de punta a punta — Requisitos

> Escrita el 2026-11-13 por el spec-author en `feature/F-072-tipo-reclamacion-sigrid`
> (desde `dev` `6994cb0`, base fija propuesta). Rigor **`critico`**. **Pendiente de
> aprobación**: decisiones abiertas Q-1..Q-11 en `design.md` §12; los R marcados
> **[Q-n]** dependen de ellas y van escritos con la opción recomendada.
> Solo `services/postventa-api` y documentos (Q-4). Ejemplos siempre ficticios
> (obras `99NN`, tipos `9001`…, «TIPO FICTICIO N»).

## 0 · De dónde sale

Q-3 de F-071 (humano, 2026-11-05): la columna `Listado` ofrece dos valores fijos
del YAML (`primero`/`segundo`), la bandeja los guarda y el volcado manda **siempre**
`0002` (`TIPO_RECLAMACION` en `domain/models/volcado.py`). Decidido entonces: los
tipos salen de `dbo.auxtrcp` (vía `sigrid-api`, solo lectura) al descargar; la
importación valida contra los de ese momento y guarda el código; columna nueva en
la bandeja (DDL solo en `postventa`); la revisión lo enseña y deja cambiarlo; el
volcado manda el código; **en blanco = `0002`**. Orden: F-071 → F-072 → F-040.

`auxtrcp` (`azure-apps/sigrid_tablas.md`): `ide`, `cod` (texto 24), `res` (texto
48), `pos`, `fecbaj` (0 = vigente). `sigrid-api` §8.9 recibe `tipo` = `cod` y
rechaza el parte con `tipo_no_valido` si no existe o está de baja (medido en su
código: `create_partes_reclamacion_use_case.py`, lectura con `fecbaj`).

## 1 · La lectura de Sigrid

- **R1.** CUANDO se descarga la plantilla, se importa un fichero reconocido y no
  importado, se lista la revisión, o se edita o aprueba una incidencia, el sistema
  debe leer los tipos vigentes de `dbo.auxtrcp` por `POST /api/sql/read`, **una vez
  por petición** y sin caché entre peticiones. (capa: unit)
- **R2.** La consulta debe ser, carácter a carácter, `SELECT cod, res, pos FROM
  dbo.auxtrcp WHERE ISNULL(fecbaj, 0) = 0 ORDER BY pos, cod`, sin parámetros. (capa: unit)
- **R3.** SI la lectura falla o agota su tiempo, ENTONCES el sistema debe responder
  como con el catálogo (`CatalogoNoDisponible`, 503): ni plantilla, ni filas en la
  bandeja, ni revisión escrita. (capa: unit)
- **R4.** SI la respuesta llega al techo de filas pedido, ENTONCES el sistema debe
  tratarla como sin verificar (`CatalogoSinVerificar`, 409), sin ofrecer ni validar
  con una lista cortada. (capa: unit)
- **R5.** SI una fila trae el código nulo o en blanco, ENTONCES el sistema debe
  ignorarla; SI dos filas traen el mismo código recortado, ENTONCES debe quedarse
  con la primera en el orden de R2. Los dos casos se cuentan en el log. (capa: unit)

## 2 · La plantilla

- **R6.** La columna `Listado` de la plantilla debe ofrecer una opción por tipo de
  R1, en su orden, con la etiqueta `<res recortado> (<cod recortado>)`, o `<cod>`
  si `res` está vacío [Q-6]. (capa: unit)
- **R7.** SI no hay ningún tipo vigente, ENTONCES la columna `Listado` solo debe
  admitir el blanco (la rama «lista vacía» del generador de F-071). (capa: unit)
- **R8.** La cabecera, el título `Listado`, las hojas, el identificador y
  `VERSION_PLANTILLA = 2` no deben cambiar [Q-5]. (capa: unit)
- **R9.** El YAML `config/plantilla_incidencias.yaml` no debe tener `listados`; SI
  lo trae, ENTONCES la carga debe fallar con `ConfiguracionPlantillaInvalida`
  («`listados`: los tipos de reclamación salen de Sigrid (F-072)»). La urgencia
  sigue en el YAML. (capa: unit)
- **R10.** Los textos de `Listado` (título de entrada ≤ 32, mensajes ≤ 255) y la
  instrucción de los desplegables deben decir que la lista sale de Sigrid y que en
  blanco entra como tipo `0002`; ningún ejemplo de la hoja «Instrucciones» se
  valida contra la lista de `Listado`. (capa: unit)

## 3 · La importación

- **R11.** CUANDO se importa un fichero reconocido y no importado, el sistema debe
  leer los tipos (R1) **después** del catálogo y de las ubicaciones; con
  `ya_importado` o fichero no reconocido, no debe leerlos. (capa: unit)
- **R12.** La celda `Listado` debe casarse con las etiquetas de R6 con la regla de
  F-060/F-071 (`casar_con_lista`: la exacta, o la única con la misma clave, con
  `aviso_valor_tomado`), y la fila debe guardar el **código** del tipo. (capa: unit)
- **R13.** SI la celda no casa —incluidas `Primer listado` y `Segundo listado` de
  una plantilla descargada antes de F-072—, ENTONCES la fila debe volver en el Excel
  de errores con el motivo de fuera de lista, y ese Excel debe llevar en `Listado`
  las etiquetas de los tipos leídos en esa importación [Q-5]. (capa: unit)
- **R14.** CUANDO la celda `Listado` está en blanco, el sistema debe guardar `0002`
  sin comprobarlo contra la lista leída [Q-7]. (capa: unit)
- **R15.** Toda fila nueva de la bandeja debe llevar `tipo_reclamacion` no nulo y
  `listado` a `NULL`. (capa: unit)

## 4 · La base (DDL en el esquema propio)

- **R16.** `17_tipo_reclamacion.sql` debe añadir la columna `tipo_reclamacion text
  CHECK (char_length(tipo_reclamacion) BETWEEN 1 AND 24)`, que admite nulo, a
  `postventa.bandeja_incidencias` y a `postventa.revisiones_bandeja`, con `ALTER
  TABLE postventa.<tabla> ADD COLUMN IF NOT EXISTS`, y la guarda del DDL
  (`infrastructure/persistencia/ddl.py`, sin cambios) debe aceptarlo. (capa: unit)
- **R17.** Aplicado dos veces sobre una base con datos de F-036/F-056, el DDL no
  debe fallar, debe dejar `tipo_reclamacion` nulo en las filas existentes y no debe
  crear nada fuera de `postventa`. (capa: integración; MANUAL con la base efímera)
- **R18.** Ningún DDL de F-072 debe tocar la columna `listado` ni sus `CHECK`, ni
  llevar `UPDATE`, `DELETE`, `DROP` ni `ALTER COLUMN`. (capa: unit)

## 5 · La revisión

- **R19.** El tipo efectivo de una foto debe ser su `tipo_reclamacion`, o `0002` si
  es nulo (filas anteriores a F-072); el `listado` heredado no lo cambia [Q-2]. (capa: unit)
- **R20.** `GET /api/revision` debe devolver en `catalogo.listados` los tipos de R1
  como `{codigo, etiqueta}` (etiqueta de R6), y en `valores.listado` e
  `importados.listado` de cada fila el **tipo efectivo** [Q-4]. (capa: unit)
- **R21.** CUANDO se edita, el sistema debe aceptar en `valores.listado` un código
  que sea exactamente uno de los vigentes leídos en esa petición, o el tipo
  efectivo que ya tiene la incidencia (se conserva aunque esté de baja); SI no,
  ENTONCES 400 con el error en `listado`, sin repetir lo recibido. (capa: unit)
- **R22.** CUANDO se edita con `valores.listado` nulo, el sistema debe guardar
  `0002` [Q-7]. (capa: unit)
- **R23.** Toda revisión nueva (editar, aprobar, descartar, recuperar, y la del
  sistema de F-060) debe copiar el `listado` heredado tal cual; aprobar, descartar,
  recuperar y la del sistema deben copiar además el `tipo_reclamacion` tal cual. (capa: unit)
- **R24.** MIENTRAS el tipo guardado no es nulo y no está entre los vigentes leídos,
  la incidencia debe llevar el motivo `tipo_fuera_de_sigrid` —detrás de
  `proveedor_ambiguo` y delante de `duplicada`— y no debe poder aprobarse [Q-8]. (capa: unit)
- **R25.** El campo lógico `listado` de `cambios` y del historial debe compararse
  por el tipo efectivo: pasar de nulo a `0002` no es un cambio. (capa: unit)
- **R26.** La huella de una foto con `tipo_reclamacion` nulo debe ser la que
  calculaba F-056 sobre sus 13 valores; con tipo, la lista JSON debe llevar el
  código al final. Una incidencia aprobada antes de F-072 conserva la huella. (capa: unit)
- **R27.** Descartar y recuperar no deben leer los tipos (R18 y R19 de F-056). (capa: unit)

## 6 · El volcado

- **R28.** El parte de cada candidata debe llevar `tipo` = su tipo efectivo (R19),
  no una constante. (capa: unit)
- **R29.** El volcado no debe leer `auxtrcp`: un tipo de baja entre la aprobación y
  el envío lo rechaza `sigrid-api` (`tipo_no_valido`) y sale como cualquier
  rechazo de parte de F-059, sin escribir nada. (capa: unit)

## 7 · Transversales

- **R30.** Ningún log debe llevar `res` ni textos de la propiedad: la lectura de
  tipos registra `tipos`, `sin_codigo`, `repetidos`, `al_techo` y `segundos`. (capa: unit)
- **R31.** El sistema no debe escribir en Sigrid (solo `sql/read`; el volcado, como
  F-059) ni los tests deben tocar red, base ni IA. (capa: unit)
- **R32.** El alcance debe quedar cerrado: ni `services/postventa-front/**`, ni las
  consultas existentes de `infrastructure/sigrid/` (iguales carácter a carácter),
  ni `13_`, `15_`, `16_*.sql`, ni `ddl.py`, ni `excel_openpyxl.py` cambian
  (`design.md` §3.3). (capa: unit)
- **R33.** `docs/ARCHITECTURE.md` y `docs/INTEGRACION.md` deben describir el tipo de
  reclamación de punta a punta (lectura, columna, tipo efectivo, contrato de
  `listado`); `azure-apps/` lo pone al día el líder al desplegar. (capa: unit)
- **R34.** Verificado en producción en la 0677 con lecturas y filas de prueba de la
  bandeja, sin ninguna escritura en Sigrid (`tasks.md` T26) [Q-10]. (capa: integración; MANUAL)

## 8 · Fuera de alcance

- El front (textos «Listado», «Sin listado», el motivo nuevo y `TEXTO_TIPO` de
  `js/volcado.js`): al retomar F-040 [Q-11].
- Mapear el `listado` heredado (`primero`/`segundo`) a un código [Q-2].
- Urgencia (sigue en el YAML, Q-2 de F-071), clase (`auxrcp`) y causante.
- Cualquier cambio en `sigrid-api` o en `auxtrcp`.
