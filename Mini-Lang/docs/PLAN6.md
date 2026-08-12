# Plan 6 — Exportación de compilados

## Objetivo

Permitir que el usuario guarde las salidas producidas al compilar un programa Mini-Lang, sin ejecutar el programa y sin confundirlas con el ejecutable del IDE.

La interfaz tendrá un menú superior `Compilar` con dos destinos:

- `Compilar a pseudoensamblador...`
- `Compilar a JavaScript...`

## Formatos

### Pseudoensamblador

Guarda exactamente el pseudoensamblador optimizado de `CompilationResult.assembly`.

- Extensión recomendada: `.asm`.
- Extensión alternativa: `.txt`.
- Extensión opcional: `.bin`, presentada como binario simulado.

El contenido siempre es texto UTF-8. Un archivo `.bin` de esta fase no es código máquina ni un binario nativo; solamente permite representar un artefacto compilado ficticio para fines educativos.

### JavaScript

Guarda exactamente `CompilationResult.javascript` como texto UTF-8.

- Extensión recomendada: `.js`.
- Extensión alternativa: `.txt`.

El archivo `.js` incluye el runtime generado por Mini-Lang y puede ejecutarse con Node.js. Los programas que solicitan entrada la leen desde la entrada estándar.

## Flujo

```text
Editor Mini-Lang
    -> Compilar
       -> Pseudoensamblador -> programa.asm / programa.txt / programa.bin
       -> JavaScript        -> programa.js
```

La compilación realiza lexer, parser, resolución de módulos, análisis semántico, optimización y generación. No ejecuta la máquina virtual ni solicita los valores de la pestaña `Entrada`.

## Interfaz

El menú `Compilar` se coloca entre `Archivo` y `Editar`.

Cada opción:

1. Compila el contenido actual del editor.
2. Detiene la operación y muestra el error si el programa no es válido.
3. Sugiere el nombre del archivo fuente con la extensión correspondiente.
4. Abre el diálogo para elegir la ubicación.
5. Guarda la salida exacta en UTF-8.
6. Actualiza las pestañas de resultados y la barra de estado.

Cancelar el diálogo no crea archivos ni se considera un error.

## Fases

### Fase 1 — Contrato

- [x] Definir las dos salidas compilables.
- [x] Distinguir pseudoensamblador textual de un binario real.
- [x] Mantener JavaScript como artefacto ejecutable.

### Fase 2 — GUI

- [x] Crear el menú superior `Compilar`.
- [x] Añadir la opción de pseudoensamblador.
- [x] Añadir la opción de JavaScript.
- [x] Sugerir nombres y extensiones apropiados.

### Fase 3 — Escritura

- [x] Guardar el pseudoensamblador optimizado sin modificarlo.
- [x] Guardar el JavaScript generado sin modificarlo.
- [x] Usar codificación UTF-8.
- [x] No ejecutar el programa durante la exportación.

### Fase 4 — Pruebas

- [x] Verificar el contenido exacto del archivo `.asm`.
- [x] Verificar el contenido exacto del archivo `.js`.
- [x] Verificar el nombre sugerido y el filtro `.bin` simulado.
- [x] Verificar que un error de compilación no abre el diálogo de guardado.

### Fase 5 — Verificación

- [x] Ejecutar toda la suite.
- [x] Ejecutar la autoprueba del código fuente.
- [x] Validar el JavaScript exportado con Node.js.
- [x] Confirmar que PLAN6 no reconstruyó ejecutables.

## Archivos

- `app.py`
- `tests/test_gui_helpers.py`
- `README.md`
- `docs/PLAN6.md`

## Criterios de aceptación

- Existe el menú superior `Compilar` con las dos opciones solicitadas.
- Compilar no ejecuta el programa.
- Los errores se muestran antes de pedir una ruta de destino.
- El pseudoensamblador guardado coincide con la pestaña `Pseudoensamblador` optimizada.
- El JavaScript guardado coincide con la pestaña `JavaScript`.
- El nombre sugerido reutiliza el nombre del archivo Mini-Lang actual.
- Cancelar no crea un archivo.
- No se genera, reconstruye ni modifica ningún EXE como parte de PLAN6.

## Comandos

```powershell
python -m unittest tests.test_gui_helpers -v
python -m unittest discover -s tests -v
python app.py --self-test
```

## Registro

- [x] Enfoque del ejecutor HTML retirado.
- [x] Plan redefinido como exportación de artefactos compilados.
- [x] Menú y guardado implementados.
- [x] Suite completa: 120 pruebas aprobadas.
- [x] Archivo `.js` exportado y ejecutado correctamente con Node.js.
- [x] Autoprueba del código fuente aprobada.
- [x] No se generó ni reconstruyó ningún EXE.
