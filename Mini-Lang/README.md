# Mini-Lang

Mini-Lang es un lenguaje educativo con análisis léxico, parser, AST, análisis semántico, optimización, bytecode, máquina virtual, depurador e interfaz Tkinter.

## Requisitos

- Python 3.10 o superior.
- Tkinter.
- Node.js opcional para ejecutar y comparar la salida JavaScript.
- Un navegador moderno para los juegos web.

## Inicio

```powershell
python app.py
```

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

## Programa

```text
int potencia(int base, int exponente) {
    if (exponente == 0) {
        return 1;
    }
    return base * potencia(base, exponente - 1);
}

for (int i = 0; i < 5; i++) {
    print(potencia(2, i));
}
```

## Tipos

- `int`
- `float`
- `bool`
- `string`
- `void`
- Arreglos de tipos básicos

## Herramientas

- Abrir y guardar `.mini`.
- Resaltado de sintaxis.
- Tokens, AST y tabla de símbolos.
- Pseudoensamblador ejecutable por la máquina virtual.
- JavaScript ejecutable en Node.js o navegador.
- Menú `Compilar` para guardar pseudoensamblador o JavaScript.
- Destino `Juego web (.html)` con Canvas, teclado y animación.
- Explorador de proyecto con árbol de carpetas y archivos.
- Atajos `F5` para ejecutar y `F7` para compilar sin ejecutar.
- Ejecución paso a paso.
- Puntos de interrupción.
- Entrada de datos desde la pestaña `Entrada`.

## Compilados

El menú `Compilar` permite guardar el programa sin ejecutarlo:

- `Compilar a pseudoensamblador...` genera texto `.asm`, `.txt` o `.bin` simulado.
- `Compilar a JavaScript...` genera un script `.js` ejecutable con Node.js.
- `Compilar juego web (.html)...` genera un juego de navegador autocontenido.

La extensión `.bin` representa pseudoensamblador textual educativo; no es código máquina ni un ejecutable nativo.

## Juego web

Abre [`examples/cuadrado.mini`](examples/cuadrado.mini) desde el IDE y selecciona `Compilar > Compilar juego web (.html)...`. Guarda el archivo y ábrelo con doble clic en Edge, Chrome o Firefox. No necesita servidor ni archivos adicionales.

Un juego declara este ciclo de vida:

```text
void iniciar() {
    gameInit(640, 360);
}

void actualizar(float delta) {
    // Actualizar posiciones según el teclado y el tiempo.
}

void dibujar() {
    gameClear("black");
    gameRect(20.0, 20.0, 40.0, 40.0, "blue");
}
```

Funciones disponibles: `gameInit`, `gameClear`, `gameRect`, `gameText`, `gameKey`, `gameDelta`, `gameWidth` y `gameHeight`.

F5 ejecuta la VM y no dispone de gráficos. Para ejecutar llamadas `game*`, exporta el juego como `.html`. F7 sí puede analizar el programa y mostrar sus resultados compilados, pero no abre el navegador.

## Explorador de proyecto

Usa `Archivo > Abrir carpeta...` para seleccionar un proyecto. El árbol aparece a la derecha y abre archivos de texto UTF-8 con doble clic o Enter.

Las carpetas se cargan al expandirlas. `Ver > Mostrar/Ocultar explorador` permite recuperar el espacio del editor sin cerrar el proyecto.

Los botones `Nuevo`, `Renombrar` y `Eliminar`, también disponibles con clic derecho, operan solamente sobre archivos del proyecto. `Eliminar` es recuperable: mueve el archivo a la carpeta oculta `.minilang-trash` y nunca sobrescribe lo que ya exista allí. Las carpetas, rutas externas y enlaces del sistema no se modifican.

## Pestañas de edición

Cada archivo se abre en su propia pestaña y conserva por separado el contenido, la ruta y el indicador `*` de cambios pendientes. Volver a abrir la misma ruta selecciona la pestaña existente. Todas las acciones de ejecución, compilación, exportación, búsqueda y depuración trabajan sobre la pestaña activa.

Cerrar una pestaña o salir del IDE solicita confirmación por cada documento modificado. No se puede retirar desde el explorador un archivo abierto que todavía tenga cambios sin guardar.

## Atajos principales

- `F5`: compila y ejecuta el programa con los valores de la pestaña `Entrada`.
- `F7`: compila sin ejecutar, actualiza los paneles y muestra el pseudoensamblador.
- `Ctrl+N`: crea una pestaña vacía.
- `Ctrl+W`: cierra la pestaña activa.

F7 no guarda un archivo. Para exportar se mantienen las opciones `Compilar a pseudoensamblador...` y `Compilar a JavaScript...`.

F7 y todas las opciones del menú `Compilar` muestran primero una ventana modal con `Compilando...`. La espera interna es breve y configurable, pero el número y la duración no aparecen en pantalla. La barra continúa animada y el IDE no se congela.

## Documentación

- [Plan](docs/PLAN.md)
- [Plan 2](docs/PLAN2.md)
- [Plan 4 — Semántica numérica](docs/PLAN4.md)
- [Plan 5 — Backend JavaScript](docs/PLAN5.md)
- [Plan 6 — Exportación de compilados](docs/PLAN6.md)
- [Plan 7 — Explorador de proyecto](docs/PLAN7.md)
- [Plan 8 — Atajos de compilación y ejecución](docs/PLAN8.md)
- [Plan 9 — Juegos web con Canvas](docs/PLAN9.md)
- [Plan 10 — Espera visual de compilación](docs/PLAN10.md)
- [Plan 11 — Pestañas y operaciones de archivos](docs/PLAN11.md)
- [Seguimiento general del proyecto](docs/SEGUIMIENTO.md)
- [Gramática](docs/GRAMMAR.md)
- [Bytecode](docs/BYTECODE.md)
- [Errores](docs/ERRORS.md)

## Módulos

```text
import "utilidades.mini";
```

Los nombres que comienzan con `_` son privados al módulo.
