# Plan 5 — Backend JavaScript

## Objetivo

Añadir JavaScript como segunda salida de compilación sin eliminar el pseudoensamblador ni cambiar la semántica validada por el intérprete y la máquina virtual.

El JavaScript generado debe poder ejecutarse como script en Node.js y en un navegador. Esta fase no ejecutará JavaScript dentro de la ventana principal de Tkinter y no generará ni modificará ejecutables.

## Base

- Versión de referencia: Mini-Lang v4.2.
- Suite inicial: 102 pruebas aprobadas.
- Escenarios avanzados: 20 aprobados.
- El AST semántico contiene conversiones implícitas mediante `CastExpr`.
- La división `int / int` usa piso, equivalente a `//` de Python.
- El módulo conserva la semántica de Python con operandos negativos.

## Flujo

```text
Código Mini-Lang
    -> Lexer
    -> Parser
    -> AST
    -> Análisis semántico
    -> Optimización
    -> Pseudoensamblador y VirtualMachine
    -> JavaScript y runtime Mini-Lang
```

## Contrato del backend

1. Generar desde el AST optimizado.
2. Mantener ámbitos de bloque y funciones.
3. Conservar evaluación de izquierda a derecha y cortocircuito booleano.
4. Conservar promociones `int` a `float`.
5. Usar división de piso para `int / int`.
6. Emular el módulo de Python.
7. Validar índices de arreglos y variables sin inicializar.
8. Imprimir booleanos como `True` y `False`.
9. Conservar la representación decimal de valores `float` enteros, como `5.0`.
10. Mantener límites de instrucciones y profundidad de llamadas.
11. Evitar colisiones con palabras reservadas y nombres internos de JavaScript.
12. Mantener errores en español con línea y columna.
13. Representar `int` mediante `BigInt` para no perder precisión fuera del rango seguro de `Number`.

## Diseño

### Generador

Crear `minilang/js_codegen.py` con `JavaScriptGenerator`.

El generador recorrerá:

- declaraciones de funciones, variables y arreglos;
- asignaciones y accesos a arreglos;
- `if`, `while`, `for`, `break`, `continue` y `return`;
- llamadas, impresión y expresiones;
- conversiones `CastExpr`;
- bloques creados por el optimizador.

Los identificadores se codificarán con prefijos separados para variables y funciones. Esto evita colisiones con JavaScript y conserva el espacio de nombres de llamadas de Mini-Lang.

### Runtime

El código generado incluirá auxiliares para:

- errores y posiciones;
- impresión y formato de tipos;
- división, módulo y potencia;
- arreglos;
- variables sin inicializar;
- entrada en Node.js o navegador;
- strings, conversiones y expresiones regulares;
- límites de instrucciones y recursividad.

### Integración

`CompilationResult` añadirá el campo `javascript`. `Compiler.compile()` producirá el AST optimizado, pseudoensamblador, JavaScript y tabla de símbolos en una sola compilación.

### GUI

La interfaz añadirá una pestaña `JavaScript` junto a `Pseudoensamblador`. Solo mostrará el código para inspección y copia.

## Fases

### Fase 1 — Generador y runtime

- [x] Crear `JavaScriptGenerator`.
- [x] Emitir todos los nodos actuales del AST.
- [x] Implementar runtime compatible.
- [x] Codificar identificadores de usuario de forma segura.

### Fase 2 — Compiler

- [x] Añadir `javascript` a `CompilationResult`.
- [x] Generar JavaScript desde el AST optimizado.
- [x] Mantener la API y resultados actuales.

### Fase 3 — Pruebas

- [x] Añadir pruebas estructurales sin depender de Node.js.
- [x] Ejecutar JavaScript con Node.js cuando esté disponible.
- [x] Comparar salida con VM e intérprete.
- [x] Cubrir errores, módulos, builtins y semántica numérica.

### Fase 4 — GUI

- [x] Añadir la pestaña JavaScript.
- [x] Mostrar el resultado de cada compilación.
- [x] Permitir copiar y limpiar mediante los controles existentes.
- [x] No ejecutar JavaScript dentro de Tkinter.

### Fase 5 — Verificación

- [x] Ejecutar toda la suite.
- [x] Ejecutar los 20 escenarios avanzados.
- [x] Ejecutar la autoprueba del código fuente.
- [x] Confirmar que no se modificaron ejecutables.

## Archivos previstos

- `minilang/js_codegen.py`
- `minilang/compiler.py`
- `minilang/__init__.py`
- `app.py`
- `tests/test_javascript_codegen.py`
- `README.md`
- `docs/PLAN5.md`

## Criterios de aceptación

- JavaScript es una segunda salida y el bytecode actual permanece disponible.
- Los programas deterministas producen la misma salida en Node.js, VM e intérprete.
- Los errores principales conservan fase, línea y columna.
- La GUI muestra el JavaScript sin evaluarlo.
- Las 102 pruebas existentes continúan aprobadas.
- No se genera, reconstruye ni modifica ningún EXE.

## Comandos

```powershell
python -m unittest tests.test_javascript_codegen -v
python -m unittest discover -s tests -v
python app.py --self-test
```

## Registro

- [x] Contrato inicial definido.
- [x] Plan de implementación creado.
- [x] Generador y runtime JavaScript implementados.
- [x] Salida JavaScript integrada en `Compiler` y GUI.
- [x] Suite completa: 114 pruebas aprobadas.
- [x] Los 20 escenarios avanzados coinciden entre Node.js, VM e intérprete.
- [x] Enteros grandes validados mediante `BigInt`.
- [x] Autoprueba del código fuente aprobada.
- [x] Ejecutable v4.1 sin modificaciones.
