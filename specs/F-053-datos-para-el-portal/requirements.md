<!-- specs/F-053-datos-para-el-portal/requirements.md -->
# F-053 · Dos datos que pide el portal — Requisitos

> Rama `feature/F-053-datos-para-el-portal`, desde `dev` en `349ba06`. Rigor
> **`critico`**. Solo backend (`services/postventa-api`). Origen: D-13 de la
> enmienda de F-035 y `specs/F-035-portal-posventa/design.md` §16.6. El portal
> publicado (F-035) ya consume los dos datos **de forma tolerante**: sin ellos
> rotula sin fecha y no pinta «Decididos como distintos». Esta ficha los hace
> salir, con el contrato que el front ya da por hecho, escrito en
> `progress/review_F-035.md`: «Review del bloque 12 → Contrato para F-053»
> (`importado_at_utc`) y «Review del bloque 13 → 3 · Contrato para F-053»
> (`oficio.distintos`).
>
> **Solo aditiva.** Ningún campo existente cambia de nombre, tipo ni valor.
> Sin DDL, sin variables de entorno, sin lecturas nuevas a la base ni a Sigrid.

## 1 · `importado_at_utc` en `POST /api/importaciones`

La fecha ya existe: `postventa.importaciones.importado_at_utc` (`timestamptz
NOT NULL`, `12_importaciones.sql`), que se escribe con `ContextoImportacion.
ahora` (`paso_registro`) y que el atajo de R39 de F-036 ya lee
(`select_importacion_completa_por_hash` → `fila_a_resultado_ya_importado`,
columna 6). En las dos rutas llega a `ResultadoImportacion.importacion.
importado_at_utc`; hoy no se serializa.

- **R1** · CUANDO `POST /api/importaciones` responde **200** con una
  importación recién registrada (completa o parcial, `ya_importado: false`), el
  cuerpo debe llevar `importado_at_utc` con el instante de **esa** importación:
  el mismo que se guarda en `postventa.importaciones.importado_at_utc`.
- **R2** · CUANDO responde **200** con `ya_importado: true`, `importado_at_utc`
  debe ser el de la importación **original** —la que devuelve
  `importacion_completa_por_hash`, la primera completa con esos bytes—, nunca
  el instante de la petición que repite la subida.
- **R3** · El valor debe ser un texto con la forma exacta
  `AAAA-MM-DDTHH:MM:SS.ffffff+00:00`: el instante **en UTC**, con `T`, con
  segundos, **siempre** con seis cifras de microsegundos y con el desfase
  `+00:00` de cuatro cifras (expresión regular
  `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00$`). Es la forma del caso
  de Node «con +00:00 y microsegundos (isoformat de Python)» de
  `services/postventa-front/tests_js/f035_paginas.test.js`.
- **R4** · SI el instante llega con otra zona horaria (por ejemplo, el que
  devuelve psycopg en la zona de la sesión), ENTONCES el sistema debe
  **convertirlo** a UTC conservando el instante; nunca debe quitarle la zona
  ni escribir la hora local con `+00:00` (contrato del bloque 12, punto 2: el
  único fallo que daría al rótulo una fecha **equivocada**).
- **R5** · SI el instante no lleva zona horaria, ENTONCES `importado_at_utc`
  debe ser `null` —nunca un texto sin desfase— y la respuesta debe seguir
  siendo la 200 de siempre. (El front rotula entonces sin fecha.)
- **R6** · CUANDO el mismo fichero de una importación **parcial** se sube otra
  vez (R39 de F-036: se procesa de nuevo, `ya_importado: false`),
  `importado_at_utc` debe ser el de la importación **nueva**, no el de la
  parcial anterior.
- **R7** · La clave `importado_at_utc` debe ir en **todas** las respuestas 200
  de `POST /api/importaciones` (completa, parcial, `ya_importado`), y en
  **ninguna** de error: los cuerpos 400/409/413/503 siguen siendo `{error,
  codigo}`.

## 2 · `oficio.distintos` en `GET /api/catalogos/propuestas`

- **R8** · CUANDO `GET /api/catalogos/propuestas?obra=` responde **200**, el
  objeto `oficio` debe llevar la clave `distintos`: una lista JSON de objetos
  con **exactamente** dos claves, `codigo_a` y `codigo_b`. Sin `decidido_por`,
  `decidido_at_utc`, `obra_codigo`, `motivos` ni ningún `oid` (R47 de F-036).
  Va **dentro** de `oficio`, nunca en la raíz de la respuesta.
- **R9** · Un par debe salir en `distintos` si y solo si **sus dos códigos**
  son oficios de la obra (los de `oficio.oficios[]`) y su **última** decisión
  en el catálogo `oficio` es `distinto`. «Última» es la regla de F-036
  (`domain/models/equivalencias.py`, `_ultimas`): manda la fecha y, a igual
  fecha, la que llega después.
- **R10** · CUANDO sobre un par se decide «distinto» y después «mismo», el par
  **no** debe salir; CUANDO se decide «mismo» y después «distinto», **sí**
  (contrato del bloque 13, punto 8: es lo que el front espera tras pulsar «Son
  el mismo» y recargar).
- **R11** · Los dos códigos deben ir como **textos JSON**, idénticos carácter a
  carácter a `oficio.oficios[].codigo`, con sus ceros a la izquierda: el par de
  la 0677 sale `{"codigo_a": "0033", "codigo_b": "0133"}`, nunca `33` ni
  `"33"`.
- **R12** · Cada par debe ir con `codigo_a < codigo_b` (dos códigos distintos)
  y la lista ordenada por (`codigo_a`, `codigo_b`), sin repetidos, sea cual sea
  el orden en que lleguen las decisiones.
- **R13** · Las decisiones de **otro catálogo** (por ejemplo `proveedor`) con
  los mismos códigos no deben contar.
- **R14** · SI la obra no tiene ningún par cuya última decisión sea
  `distinto` (o no tiene oficios), ENTONCES `distintos` debe ser `[]`: la clave
  va **siempre** en la respuesta 200.
- **R15** · Un par debe poder salir **a la vez** en `distintos` y entre los
  códigos de un aviso (`oficio.avisos`, R82 de F-036): el aviso existe porque
  hay un «distinto» (contrato del bloque 13, punto 9). Ninguna de las dos
  listas debe cambiar por la otra.
- **R16** · `GET /api/catalogos/propuestas` debe seguir haciendo **las mismas
  lecturas** que hoy: una llamada a `ultimas_decisiones` y la lectura del
  catálogo de la obra en Sigrid. `distintos` sale de las decisiones que ya se
  leen; ni una consulta nueva.

## 3 · Solo aditiva

- **R17** · Ningún campo existente de las respuestas 200 de los dos endpoints
  debe cambiar de nombre, tipo ni valor. `POST /api/catalogos/decisiones`
  (incluido `grupos_vigentes`), `GET /api/plantilla` y `GET /api/bandeja` **no**
  deben cambiar en nada.
- **R18** · Los tests de F-036 deben seguir en verde. Los únicos cambios
  admitidos en ellos son **tres líneas añadidas**, ninguna quitada ni
  modificada (D-3 de `design.md`): la clave `"importado_at_utc"` en el conjunto
  `CLAVES` de `test_f036_importar_http.py`, y `"distintos": []` en las dos
  igualdades completas de `oficio` de `test_f036_catalogos_http.py`.
- **R19** · La feature no debe añadir DDL, ni variables de entorno, ni tocar
  `services/postventa-front/`, `infra/`, `infrastructure/persistencia/` ni
  `function_app.py`.

## 4 · Documentación

- **R20** · `docs/INTEGRACION.md` §8 («Qué exponemos nosotros») debe describir
  los dos campos nuevos con su contrato: `importado_at_utc` (forma de R3, UTC,
  `null` sin zona, la original con `ya_importado`) y `oficio.distintos` (forma
  de R8, códigos como texto, orden, última decisión, solo oficios de la obra,
  y que los códigos no deben llevar guiones porque el front identifica el par
  con `a-b`).
- **R21** · `azure-apps/postventa_incidencias.md` debe decir lo mismo, con
  commit local en ese repositorio (regla de mantenimiento de `azure-apps/`).

## 5 · Verificación en producción (MANUAL, humano)

Tras la review APROBADA, el merge a `dev` y el despliegue del backend desde una
copia limpia de `dev`:

- **V1** · En `importar.html`, reimportar el fichero `v2` de la 0677 (ya
  importado y **completo**): el resumen dice «Resumen de la importación
  original del DD/MM/AAAA», con la fecha de la importación original en hora de
  Madrid. Sin escribir nada (`ya_importado`).
- **V2** · En `oficios.html`, obra 0677, **sin pulsar nada**: aparece la
  sección «Decididos como distintos» con el par **0033 · 0133** (Solados y
  Alicatados M.O. · Solados y Alicatados).
