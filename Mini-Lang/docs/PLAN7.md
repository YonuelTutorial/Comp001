# Plan 7 — Explorador de proyecto

## Objetivo

Añadir al IDE un explorador de archivos similar al de un editor moderno. El panel se mostrará a la derecha y representará como árbol la carpeta abierta como proyecto.

Esta fase permitirá navegar y abrir archivos. No incluirá crear, renombrar, mover ni borrar elementos.

## Base

- Versión de referencia: Mini-Lang v4.2.3 con PLAN6.
- Suite inicial: 120 pruebas aprobadas.
- El editor actual trabaja con un archivo abierto y conserva confirmación de cambios sin guardar.
- El proyecto no tiene todavía un concepto persistente de carpeta de trabajo.

## Interfaz

### Panel derecho

El área principal se dividirá horizontalmente:

```text
+-----------------------------------------+--------------------+
| Editor y paneles de compilación         | EXPLORADOR         |
|                                         | carpeta-proyecto   |
|                                         | ├─ docs            |
|                                         | │  └─ PLAN7.md     |
|                                         | ├─ minilang        |
|                                         | └─ programa.mini   |
+-----------------------------------------+--------------------+
```

El explorador tendrá:

- nombre de la carpeta abierta;
- botón para seleccionar otra carpeta;
- botón para ocultar el panel;
- árbol desplazable con carpetas antes que archivos;
- apertura de archivos mediante doble clic o la tecla Enter.

### Menús

`Archivo > Abrir carpeta...` seleccionará la raíz del proyecto.

`Ver > Mostrar/Ocultar explorador` controlará la visibilidad del panel sin cerrar el archivo actual.

## Comportamiento

1. Al abrir una carpeta, su nodo raíz se expande inmediatamente.
2. Las subcarpetas se cargan solamente cuando se expanden.
3. `.git`, `__pycache__` y `.pytest_cache` no se muestran.
4. Las carpetas aparecen antes que los archivos y cada grupo se ordena por nombre.
5. Un archivo abierto desde el árbol pasa por la confirmación normal de cambios sin guardar.
6. Si todavía no existe un proyecto, abrir un archivo establece su carpeta padre como proyecto.
7. Guardar un archivo nuevo actualiza el árbol cuando pertenece al proyecto.
8. Los archivos que no sean UTF-8 muestran un error y no reemplazan el contenido del editor.

## Límites de seguridad

- No seguir enlaces simbólicos, uniones ni otros puntos de reanálisis desde el árbol.
- No realizar escrituras al explorar una carpeta.
- No añadir operaciones destructivas en esta fase.
- No cargar recursivamente todo el proyecto; cada carpeta se enumera bajo demanda.
- Mantener la ruta asociada a cada nodo fuera del texto visible del árbol.

## Fases

### Fase 1 — Estructura visual

- [ ] Dividir horizontalmente el espacio de trabajo.
- [ ] Mantener editor, paneles y estado actuales.
- [ ] Crear el panel derecho con cabecera y árbol.
- [ ] Permitir ocultar y volver a mostrar el explorador.

### Fase 2 — Modelo del árbol

- [ ] Enumerar carpetas antes que archivos.
- [ ] Excluir carpetas internas conocidas.
- [ ] Cargar subcarpetas bajo demanda.
- [ ] Evitar atravesar puntos de reanálisis.
- [ ] Manejar carpetas sin permisos sin cerrar el IDE.

### Fase 3 — Integración de archivos

- [ ] Añadir `Archivo > Abrir carpeta...`.
- [ ] Abrir archivos con doble clic o Enter.
- [ ] Conservar el flujo de cambios sin guardar.
- [ ] Actualizar título, archivo actual y estado.
- [ ] Adoptar la carpeta del primer archivo abierto cuando no hay proyecto.

### Fase 4 — Pruebas

- [ ] Validar orden y exclusiones del árbol.
- [ ] Validar carga de carpeta y nodos bajo demanda.
- [ ] Validar apertura y rechazo de archivos no UTF-8.
- [ ] Validar los comandos nuevos del menú.
- [ ] Confirmar que PLAN6 continúa funcionando.

### Fase 5 — Verificación

- [ ] Ejecutar toda la suite.
- [ ] Ejecutar la autoprueba del código fuente.
- [ ] Validar sintaxis Python y diff.
- [ ] Confirmar que no se generaron ejecutables.

## Archivos previstos

- `app.py`
- `tests/test_file_explorer.py`
- `tests/test_gui_helpers.py`
- `README.md`
- `docs/PLAN7.md`

## Criterios de aceptación

- El IDE muestra un explorador funcional en el lado derecho.
- Se puede seleccionar una carpeta de proyecto desde el menú o el panel.
- Expandir una carpeta muestra sus hijos sin recorrer todo el proyecto al inicio.
- Doble clic y Enter abren archivos de texto UTF-8.
- Los cambios sin guardar nunca se descartan sin confirmación.
- Ocultar el explorador no pierde la carpeta seleccionada.
- La compilación, ejecución, depuración y exportación de PLAN6 continúan funcionando.
- No se crea, renombra, mueve ni elimina ningún archivo desde el árbol.

## Comandos

```powershell
python -m unittest tests.test_file_explorer -v
python -m unittest discover -s tests -v
python app.py --self-test
```

## Registro

- [x] Alcance definido.
- [x] Plan de implementación creado.
