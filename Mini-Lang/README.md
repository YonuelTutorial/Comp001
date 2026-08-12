# Mini-Lang

Mini-Lang es un lenguaje educativo con análisis léxico, parser, AST, análisis semántico, optimización, bytecode, máquina virtual, depurador e interfaz Tkinter.

## Requisitos

- Python 3.10 o superior.
- Tkinter.
- Node.js opcional para ejecutar y comparar la salida JavaScript.

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
- Explorador de proyecto con árbol de carpetas y archivos.
- Atajos `F5` para ejecutar y `F7` para compilar sin ejecutar.
- Ejecución paso a paso.
- Puntos de interrupción.
- Entrada de datos desde la pestaña `Entrada`.

## Compilados

El menú `Compilar` permite guardar el programa sin ejecutarlo:

- `Compilar a pseudoensamblador...` genera texto `.asm`, `.txt` o `.bin` simulado.
- `Compilar a JavaScript...` genera un script `.js` ejecutable con Node.js.

La extensión `.bin` representa pseudoensamblador textual educativo; no es código máquina ni un ejecutable nativo.

## Explorador de proyecto

Usa `Archivo > Abrir carpeta...` para seleccionar un proyecto. El árbol aparece a la derecha y abre archivos de texto UTF-8 con doble clic o Enter.

Las carpetas se cargan al expandirlas. `Ver > Mostrar/Ocultar explorador` permite recuperar el espacio del editor sin cerrar el proyecto.

## Atajos principales

- `F5`: compila y ejecuta el programa con los valores de la pestaña `Entrada`.
- `F7`: compila sin ejecutar, actualiza los paneles y muestra el pseudoensamblador.

F7 no guarda un archivo. Para exportar se mantienen las opciones `Compilar a pseudoensamblador...` y `Compilar a JavaScript...`.

## Documentación

- [Plan](docs/PLAN.md)
- [Plan 2](docs/PLAN2.md)
- [Plan 4 — Semántica numérica](docs/PLAN4.md)
- [Plan 5 — Backend JavaScript](docs/PLAN5.md)
- [Plan 6 — Exportación de compilados](docs/PLAN6.md)
- [Plan 7 — Explorador de proyecto](docs/PLAN7.md)
- [Plan 8 — Atajos de compilación y ejecución](docs/PLAN8.md)
- [Seguimiento general del proyecto](docs/SEGUIMIENTO.md)
- [Gramática](docs/GRAMMAR.md)
- [Bytecode](docs/BYTECODE.md)
- [Errores](docs/ERRORS.md)

## Módulos

```text
import "utilidades.mini";
```

Los nombres que comienzan con `_` son privados al módulo.
