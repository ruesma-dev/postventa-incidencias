<!-- specs/F-040-volcado-sigrid/requirements.md -->
# F-040 · Volcar a Sigrid las incidencias aprobadas (el panel de volcado) — Requisitos

> **Aprobado por el humano el 2026-10-07**, con D-1 a D-14 como se
> recomendaban y las respuestas Q-1 a Q-8 (todas en
> `specs/F-059-volcado-sigrid-backend/design.md` §20; las que tocan a esta
> ficha, en `design.md` §6).
>
> **Partida por D-1 (decisión del humano del 2026-10-07).** El backend —ensayo,
> volcado, tabla `volcados_sigrid`, estados `volcada` y `en_duda`, ventana
> `VOLCADO_HABILITADO`, verificación de la escritura en producción— es la
> ficha **F-059** (`specs/F-059-volcado-sigrid-backend/`), que va **antes**.
> **Esta ficha es el front**: el panel de volcado en `bandeja.html` y el cierre
> de los restos de F-040 en el portal. **Bloqueada por F-059** (`done`,
> desplegada y verificada) **y por F-038** (`done`: su `bandeja.html`).
>
> Los números de requisito vienen de la spec conjunta: R1–R43 son de F-059;
> los de esta ficha son **R50–R59**. Rama `feature/F-040-volcado-sigrid`.
> Rigor **`critico`**: es el botón que escribe en el ERP de producción.

## 0 · De dónde sale

La ficha pide que lo aprobado en la bandeja se cree en Sigrid **con dry-run
previo y confirmación**, en lote, que **su número vuelva a la bandeja** y que
**reintentar no duplique**. F-059 da las tres rutas que lo hacen
(`GET /api/volcado`, `POST /api/volcado/ensayo`, `POST /api/volcado/volcar`,
su design §11) y los estados nuevos en `GET /api/revision` (su R4). Esta ficha
es lo que una persona de Posventa toca: ver qué se crearía, confirmar,
volcar, ver qué pasó y reintentar.

## 0.1 · Glosario

Los de F-059 (candidata, referencia, ensayo, volcado, llamada, en duda), más:

- **Trozo**: grupo de como mucho `partes_por_llamada` incidencias; un ensayo
  y un volcado por trozo.
- **Ensayo de la obra**: el conjunto de los ensayos de todos los trozos,
  enseñados juntos.

## 1 · El panel (D-2)

- **R50.** `bandeja.html` (de F-038) debe tener un panel **«Volcado a
  Sigrid»** en un componente propio, `js/volcado.js`, que con la obra cargada
  pide `GET /api/volcado` y enseña aprobadas, en duda y volcadas, y el aviso
  de que el ensayo no crea nada.
- **R51.** **«Ver qué se crearía en Sigrid»** debe partir las candidatas en
  trozos de `partes_por_llamada`, pedir los ensayos **de uno en uno** y
  enseñar, juntos, cada parte con su unidad, oficio, proveedor, ubicación,
  descripción, tipo (`0002` PRIMER LISTADO POSTVENTA) y estado (`Se crearía`,
  `Ya estaba creado`, `No se crea` con el texto de su motivo, `No se llegó a
  intentar`) y las excluidas con su motivo. Sin ensayos que terminen todos en
  200, el botón de volcar no se habilita.
- **R52.** **«Volcar N partes a Sigrid»** solo se habilita con al menos un
  `previsto`, con los ensayos sin caducar (cuenta atrás visible) y tras una
  **confirmación explícita** (**D-12**: segundo clic y teclear el número de
  partes). Manda, por cada ensayo, solo sus `previsto`, con su `revision_id`.
  `confirmado: true` aparece en **una sola** función de `js/volcado.js`.
- **R53.** Los volcados se piden **de uno en uno**; ante la primera respuesta
  que no sea 200, el panel **para** (no manda los siguientes), enseña qué quedó
  creado, qué en duda y qué sin mandar, y **no reintenta solo**. Con un 503
  `volcado_deshabilitado` dice que la ventana del volcado está cerrada. Al
  terminar o parar, vuelve a pedir `GET /api/volcado` y la primera página de
  la bandeja.
- **R54.** La lista de la bandeja enseña `volcada` con su código de Sigrid y
  quién y cuándo, y `en_duda` con «Enviada a Sigrid sin respuesta: vuelve a
  ensayar y volcar»; hay texto en castellano para cada código de motivo de
  §8.9 y para cada motivo propio de F-059 (sus R11, R17, R18).
- **R55.** Ni el correo ni el `oid` van a `console` ni al almacenamiento del
  navegador; mientras hay un volcado en marcha, salir de la página pregunta.
- **R56.** Nada sale sin un clic: cargar el panel solo lee; ensayar y volcar
  solo desde `@click`; con una petición en vuelo, ningún botón de ensayo ni de
  volcado.
- **R59.** Tras un volcado con algún `creado`, el panel debe decir que **los
  partes quedan en SAT en Sigrid y que Posventa tiene que pasarlos a PTE a
  mano** (Q-3), que es cuando Sigrid avisa al industrial.

## 2 · El cierre de la ficha en el portal

- **R57.** En **un solo commit** que **también** pone F-040 en `done` (como D-11
  de F-038): fuera los restos de F-040 de la maqueta —el panel de
  `index.html#/bandeja`, `MaquetaDatos.volcado`, las entradas
  `bandeja.verVolcado`, `bandeja.volcar` y `bandeja.reintentarVolcado` de
  `PLACEHOLDERS` y lo que solo les servía— y en su lugar un enlace «Volcar a
  Sigrid» a `bandeja.html`. Las guardias de F-035 siguen en verde; F-039 y
  F-043 conservan sus restos.
- **R58.** `services/postventa-front/README.md` cuenta el panel de volcado.

## 3 · Fuera de alcance

| Qué | Dónde |
|---|---|
| Ensayo, volcado, estados, tabla, ventana, verificación de la escritura | **F-059** |
| Pasar el parte a PTE | **Posventa, a mano en Sigrid** (Q-3); el panel solo lo recuerda (R59) |
| Abrir o cerrar la ventana del volcado | `infra/27_ventana_volcado.ps1` (F-059), no el front |
| Proponer el industrial | **F-039** |
| Aprobar en bloque | **F-043** |
| El primer volcado masivo de la 0677 y el ajuste de `N` | Más adelante (Q-8) |
| Recrear un parte anulado | Nadie (Q-5) |
