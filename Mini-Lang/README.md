# Mini-Lang

Mini-Lang es un lenguaje educativo con análisis léxico, parser, AST, análisis semántico, optimización, bytecode, máquina virtual, depurador e interfaz Tkinter.

## Requisitos

- Python 3.10 o superior.
- Tkinter.

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
- Ejecución paso a paso.
- Puntos de interrupción.
- Entrada de datos desde la pestaña `Entrada`.

## Documentación

- [Plan](docs/PLAN.md)
- [Plan 2](docs/PLAN2.md)
- [Gramática](docs/GRAMMAR.md)
- [Bytecode](docs/BYTECODE.md)
- [Errores](docs/ERRORS.md)

## Módulos

```text
import "utilidades.mini";
```

Los nombres que comienzan con `_` son privados al módulo.
