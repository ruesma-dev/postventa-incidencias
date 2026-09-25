<!-- specs/F-049-villa-tres-cifras/tasks.md -->
# F-049 · Las villas que crea el archivo, siempre con tres cifras — Tareas

> Una tarea = un commit `F-049 Tn: ...`. Rigor `critico`: fase RED
> obligatoria, cobertura del 100 % de lo cambiado y mutación. Rama
> `feature/F-049-villa-tres-cifras`. Sin push.

- [x] T1: esta spec (`requirements.md`, `design.md`, `tasks.md`)  |  Verificación: lectura
- [x] T2: RED — `tests/test_f049_villa_tres_cifras.py` con R1–R4, en rojo por
  el ancho y por la documentación, y en verde lo que ya cumple el casado (R2)
  |  Verificación: `python -m pytest tests/test_f049_villa_tres_cifras.py`, traza del fallo en `progress/impl_F-049.md`
- [x] T3: `nombre_derivado_de_unidad` con `:03d` y la cascada de tests de
  F-013 que fijaban dos cifras, **solo** donde fijan el ancho del nombre
  creado  |  Verificación: suite del servicio en verde; la lista de tests tocados, en el informe
- [x] T4: recuadros fechados en `specs/F-013-archivo-posventa/`
  (`requirements.md`, `design.md`, `tasks.md`)  |  Verificación: R4 en verde
- [ ] T5: recuadros en `docs/INTEGRACION.md` §3 y `docs/DESPLIEGUE.md` §9; el
  gemelo `azure-apps/postventa_incidencias.md`, commit local allí  |  Verificación: R4 en verde; `test_f006_repo_sin_identificadores.py` en verde
- [ ] T6: mutación `python -m harness.mutacion --feature F-049 --timeout 900 --workers 6`, sola; cada superviviente, test o justificación  |  Verificación: `progress/mutacion_F-049.md`
- [ ] T7: `bash harness/init.sh` en verde e informe `progress/impl_F-049.md`  |  Verificación: `bash harness/init.sh`
