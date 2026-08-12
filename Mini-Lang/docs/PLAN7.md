# Plan 7 — Explorador de proyecto

## Objetivo

Añadir al IDE un explorador de archivos similar al de un editor moderno. El panel se mostrará a la derecha y representará como árbol la carpeta abierta como proyecto.

Esta fase permitirá navegar y abrir archivos. No incluirá crear, renombrar, mover ni borrar elementos.

## Base

- Versión de referencia: Mini-Lang v4.2.9 con PLAN6.
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

- [x] Dividir horizontalmente el espacio de trabajo.
- [x] Mantener editor, paneles y estado actuales.
- [x] Crear el panel derecho con cabecera y árbol.
- [x] Permitir ocultar y volver a mostrar el explorador.

### Fase 2 — Modelo del árbol

- [x] Enumerar carpetas antes que archivos.
- [x] Excluir carpetas internas conocidas.
- [x] Cargar subcarpetas bajo demanda.
- [x] Evitar atravesar puntos de reanálisis.
- [x] Manejar carpetas sin permisos sin cerrar el IDE.

### Fase 3 — Integración de archivos

- [x] Añadir `Archivo > Abrir carpeta...`.
- [x] Abrir archivos con doble clic o Enter.
- [x] Conservar el flujo de cambios sin guardar.
- [x] Actualizar título, archivo actual y estado.
- [x] Adoptar la carpeta del primer archivo abierto cuando no hay proyecto.

### Fase 4 — Pruebas

- [x] Validar orden y exclusiones del árbol.
- [x] Validar carga de carpeta y nodos bajo demanda.
- [x] Validar apertura y rechazo de archivos no UTF-8.
- [x] Validar los comandos nuevos del menú.
- [x] Confirmar que PLAN6 continúa funcionando.

### Fase 5 — Verificación

- [x] Ejecutar toda la suite.
- [x] Ejecutar la autoprueba del código fuente.
- [x] Validar sintaxis Python y diff.
- [x] Confirmar que no se generaron ejecutables.

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
- [x] Explorador derecho y árbol incremental implementados.
- [x] Apertura de carpeta y archivos integrada con el editor.
- [x] Suite completa: 128 pruebas aprobadas.
- [x] Prueba real de creación, carga y visibilidad de Tkinter aprobada.
- [x] Autoprueba del código fuente aprobada.
- [x] No se generó ni reconstruyó ningún EXE.
