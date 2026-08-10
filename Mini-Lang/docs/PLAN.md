# Plan de evolución de Mini-Lang

Este documento mantiene el hilo técnico del proyecto. Cada fase incluye un criterio verificable de terminación.

## Objetivo

Convertir Mini-Lang en un lenguaje pequeño pero coherente: lexer con posiciones, parser completo, análisis semántico en dos pasadas, intérprete seguro, representación intermedia determinista, diagnósticos útiles y pruebas automatizadas.

## Estado

- [x] Documentar el plan y los criterios de aceptación.
- [x] Fase 1: corregir el núcleo del lenguaje.
- [x] Fase 2: completar construcciones del lenguaje.
- [x] Fase 3: endurecer intérprete, optimizador y código destino.
- [x] Fase 4: automatizar pruebas y limpiar artefactos.
- [x] Fase 5: implementar una VM para ejecutar el código destino.

## Fase 1 — Corrección del núcleo

- Reconocer palabras reservadas únicamente como identificadores completos.
- Añadir línea y columna a cada token y a todos los errores.
- Implementar `else` en AST, parser, semántica, intérprete y código destino.
- Rechazar `return` fuera de funciones.
- Exigir retorno en todas las rutas de funciones no `void`.
- Registrar firmas de funciones antes de analizar cuerpos para permitir llamadas adelantadas y recursividad mutua.
- Usar una regla única para colisiones entre variables, arreglos y funciones.
- Validar tamaños e índices de arreglos.
- Convertir división por cero en un error de Mini-Lang.

### Criterio de aceptación

Todas las pruebas originales 1–15 pasan por separado y existen pruebas negativas para cada error anterior.

**Resultado:** cumplido. Las 15 pruebas originales pasan individualmente; la suite automatizada añade casos positivos y negativos.

## Fase 2 — Lenguaje

- Tipos `int`, `bool`, `string` y `void`.
- Cadenas con comillas simples/dobles y escapes comunes.
- Funciones con cero o varios parámetros y llamadas con varios argumentos.
- Operadores `!=`, `<=`, `>=`, `&&`, `||`, `!` y negación unaria.
- Declaraciones sin inicializador.
- Sentencias `break` y `continue`.
- Llamadas a funciones `void` como sentencias.

### Fuera del alcance inmediato

`for` se mantiene como mejora opcional: `while` ya cubre la misma capacidad expresiva.

## Fase 3 — Ejecución y código destino

- Límite configurable de instrucciones y profundidad de llamadas.
- Ámbito léxico para funciones.
- Restauración segura del entorno ante errores y retornos.
- Generación determinista: reiniciar etiquetas y temporales en cada compilación.
- Punto de entrada que separe funciones del programa principal.
- Escapado correcto de cadenas.
- Instrucciones explícitas de comprobación de arreglos.
- VM propia para ejecutar el código destino y compararlo con el intérprete del AST.

## Fase 4 — Calidad

- Suite `unittest` sin dependencias externas.
- Pruebas de lexer, parser, semántica, ejecución, optimización y código destino.
- `.gitignore` para bytecode, builds y archivos temporales.
- Núcleo separado de la interfaz Tkinter.
- La GUI debe informar la fase, línea y columna del error y limitar programas infinitos.

## Comandos de verificación

Desde `Mini-Lang`:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py minilang
```

## Resultado de implementación

- El núcleo vive en el paquete `minilang/`; `app.py` conserva la GUI y reexporta la API histórica.
- `Compiler.compile_and_run()` ejecuta el bytecode mediante `VirtualMachine`.
- `Interpreter` se conserva para comparar la semántica del AST con la VM.
- La suite está en `tests/test_minilang.py` y utiliza únicamente la biblioteca estándar.
- Última verificación local: 27 pruebas superadas.
- `test_advanced.txt` reúne 20 escenarios adicionales en un programa ejecutable.

## Decisiones de diseño

- Las funciones solo se declaran en el nivel global.
- Variables y funciones comparten el mismo espacio de nombres global.
- Los bloques crean ámbitos locales.
- La división de enteros conserva el comportamiento `//` de la versión original.
- Un índice negativo siempre es inválido, aunque Python normalmente lo permitiría.
- El intérprete del AST se conserva como referencia durante la construcción de la VM.
