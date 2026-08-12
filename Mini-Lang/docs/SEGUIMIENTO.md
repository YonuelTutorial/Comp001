# Seguimiento general de Mini-Lang

Última actualización: **2026-08-12**  
Zona horaria: **America/Santo_Domingo**  
Versión visible del IDE: **v4.3**  
Rama verificada: **main**  
Commit verificado: **`bc6c278` — Bump app window title to v4.3**

## 1. Resumen ejecutivo

Mini-Lang es un lenguaje de programación educativo y un IDE de escritorio construido en Python con Tkinter. Su propósito es mostrar, de manera inspeccionable, las etapas principales de un compilador:

```text
Código Mini-Lang
    -> Lexer y tokens
    -> Parser y AST
    -> Análisis semántico y tipos
    -> Optimización
    -> Pseudoensamblador y bytecode
    -> Máquina virtual
    -> Salida del programa

AST optimizado
    -> Backend JavaScript
    -> Script .js para Node.js o navegador
```

El proyecto no es solamente un intérprete. Incluye análisis estático, una representación intermedia propia, una máquina virtual, un intérprete del AST usado como referencia, optimizaciones, depuración, módulos, generación de JavaScript, exportación de artefactos y una interfaz de estilo IDE.

El estado actual es funcional y estable para el alcance educativo definido. La verificación realizada para este documento produjo **130 pruebas aprobadas**, autoprueba correcta y sintaxis Python válida.

## 2. Estado verificado

| Elemento | Estado actual |
|---|---|
| IDE | Tkinter, versión visible v4.3 |
| Compilación interna | Funcional con F7 |
| Ejecución en VM | Funcional con F5 |
| Pseudoensamblador | Generado, mostrado y exportable |
| Backend JavaScript | Funcional y comprobado con Node.js |
| Explorador de proyecto | Funcional, lateral derecho y carga incremental |
| Depurador | Pasos, continuación y puntos de interrupción |
| Pruebas | 130 aprobadas el 2026-08-12 |
| Autoprueba | Aprobada con `python app.py --self-test` |
| Validación de sintaxis | Aprobada con `compileall` |
| Node.js verificado | v24.19.0 |
| Ejecutable distribuible actual | Generado y verificado en `release-v4.3` |
| Estado Git | Hay documentación y artefactos locales pendientes de integrar |

Comandos usados para confirmar el estado:

```powershell
python -m unittest discover -s tests -v
python app.py --self-test
python -m compileall -q app.py minilang tests
node --version
```

## 3. Qué permite hacer Mini-Lang

### 3.1 Tipos

- `int`
- `float`
- `bool`
- `string`
- `void`, solamente como retorno de funciones
- arreglos de tamaño fijo de tipos básicos

Las variables pueden declararse sin inicializador. Usarlas antes de inicializarlas produce un error controlado.

### 3.2 Control de flujo

- `if`
- `else`
- `else if`
- `while`
- `for`
- `break`
- `continue`
- `return`

Los bloques crean ámbitos locales. `break` y `continue` restauran correctamente los ámbitos al salir o continuar un ciclo.

### 3.3 Operadores

```text
+  -  *  /  %  ^
==  !=  <  <=  >  >=
&&  ||  !
=  +=  -=  *=  /=  %=
++  --
```

La potencia usa `^` en Mini-Lang. Los operadores lógicos implementan cortocircuito.

### 3.4 Funciones

- cero o varios parámetros;
- retorno básico o `void`;
- llamadas adelantadas;
- recursividad directa;
- recursividad mutua;
- validación de cantidad y tipos de argumentos;
- validación de retorno en todas las rutas de una función no `void`;
- límite configurable de profundidad de llamadas.

Las funciones solamente pueden declararse en el nivel global.

### 3.5 Arreglos

- tamaño fijo indicado mediante un literal entero;
- lectura y escritura por índice;
- validación semántica de índices constantes;
- validación en ejecución de índices dinámicos;
- rechazo de índices negativos y fuera de rango;
- soporte para `int`, `float`, `bool` y `string`.

### 3.6 Funciones incorporadas

| Función | Resultado |
|---|---|
| `inputInt()` | Lee un `int` |
| `inputFloat()` | Lee un `float` |
| `inputString()` | Lee un `string` |
| `inputBool()` | Lee `true` o `false` |
| `length(texto)` | Longitud del string |
| `substring(texto, inicio, cantidad)` | Extrae una sección válida |
| `toString(valor)` | Convierte a string |
| `toInt(valor)` | Convierte a entero |
| `toFloat(valor)` | Convierte a decimal |
| `contains(texto, búsqueda)` | Comprueba si contiene texto |
| `regexMatch(texto, patrón)` | Evalúa una expresión regular |

Los errores de entrada, conversión, substring o expresión regular se presentan como errores de ejecución de Mini-Lang.

### 3.7 Módulos

```text
import "utilidades.mini";
```

- Los imports solamente se permiten en el nivel global.
- Las rutas se resuelven respecto al archivo que importa.
- Se detectan importaciones circulares.
- Un mismo módulo no se carga dos veces.
- Los nombres que comienzan con `_` se consideran privados al módulo y se codifican internamente para evitar colisiones.

## 4. Semántica importante

### 4.1 Números

- `int / int` usa división de piso, equivalente a `//` de Python.
- Una operación con al menos un `float` produce `float` cuando corresponde.
- La promoción implícita `int -> float` es real, no solamente una aprobación del analizador.
- El AST utiliza `CastExpr` y el bytecode utiliza `TO_FLOAT`.
- La negación conserva el tipo del operando.
- El módulo conserva la semántica de Python con números negativos.

Ejemplos del contrato:

```text
print(-3 / 2);     // -2
print(-3 % 2);     // 1
float x = 5;
print(x / 2);      // 2.5
```

### 4.2 Strings y booleanos

- Se aceptan strings con comillas simples o dobles.
- Escapes admitidos: nueva línea, retorno, tabulación, barra invertida y comillas.
- La concatenación de strings usa `+`.
- Las comparaciones de strings son sensibles a mayúsculas.
- La salida muestra booleanos como `True` y `False` para mantener paridad entre motores.

### 4.3 Límites de ejecución

Los motores aceptan límites configurables para detener:

- ciclos posiblemente infinitos;
- recursividad excesiva;
- acceso inválido a arreglos;
- variables sin declarar o sin inicializar;
- división y módulo por cero.

Los valores predeterminados del núcleo son 100 000 instrucciones y 500 llamadas. La GUI eleva el límite de instrucciones a 1 000 000 para ejecutar, compilar y depurar programas interactivos.

## 5. Arquitectura del código

### 5.1 Orquestación

`minilang/compiler.py`

- `Compiler.compile()` tokeniza, analiza, resuelve imports, valida tipos, genera pseudoensamblador sin optimizar, optimiza el AST y genera bytecode, pseudoensamblador optimizado y JavaScript.
- `Compiler.compile_and_run()` llama a `compile()` y luego ejecuta el bytecode en `VirtualMachine`.
- `CompilationResult` transporta tokens, AST optimizado, salida, pseudoensamblador, bytecode, símbolos, pseudoensamblador previo a la optimización y JavaScript.

### 5.2 Frontend

| Archivo | Responsabilidad |
|---|---|
| `minilang/tokens.py` | Modelo de token con línea y columna |
| `minilang/lexer.py` | Palabras reservadas, literales, operadores y comentarios `//` |
| `minilang/parser.py` | Gramática y creación del AST |
| `minilang/ast_nodes.py` | Nodos del lenguaje, incluido `CastExpr` |
| `minilang/semantic.py` | Tipos, ámbitos, funciones, retornos, arreglos y promociones |
| `minilang/ast_printer.py` | Representación legible del AST |

### 5.3 Optimización y ejecución

| Archivo | Responsabilidad |
|---|---|
| `minilang/optimizer.py` | Plegado de constantes, propagación, ramas y simplificación |
| `minilang/codegen.py` | Bytecode y pseudoensamblador determinista |
| `minilang/vm.py` | Máquina virtual, pila, marcos, ámbitos y llamadas |
| `minilang/interpreter.py` | Intérprete del AST usado como referencia semántica |
| `minilang/debugger.py` | Paso, continuar, puntos de interrupción y snapshot |
| `minilang/builtins.py` | Entrada, strings, conversiones y regex |
| `minilang/errors.py` | Jerarquía de errores del lenguaje |

El intérprete del AST no es el camino principal de ejecución de la GUI. Se mantiene para comprobar que la VM conserva la semántica esperada.

### 5.4 Backend JavaScript

`minilang/js_codegen.py` genera JavaScript desde el AST optimizado. El script incluye un runtime propio para:

- formato de salida;
- errores con posición;
- límites de instrucciones y recursividad;
- entrada en Node.js o mediante `prompt` en navegador;
- división, módulo y potencia;
- arreglos;
- funciones incorporadas;
- variables no inicializadas;
- conversiones;
- protección contra colisiones de identificadores.

Los `int` se representan mediante `BigInt`, lo que evita perder precisión fuera del rango seguro de `Number`.

No se usa `eval` para ejecutar JavaScript dentro de Tkinter.

### 5.5 IDE

`app.py` contiene:

- editor con números de línea;
- resaltado de sintaxis;
- abrir, guardar y guardar como;
- confirmación de cambios sin guardar;
- búsqueda y reemplazo;
- control del tamaño de fuente;
- pestañas de salida, errores, tokens, AST, símbolos, pseudoensamblador, JavaScript, depuración y entrada;
- ejecución con F5;
- compilación interna con F7;
- exportación de pseudoensamblador y JavaScript;
- depuración paso a paso;
- explorador de proyecto lateral derecho;
- barra de estado con archivo, posición y resultado de operaciones.

## 6. Pseudoensamblador y máquina virtual

El pseudoensamblador es una representación textual de las instrucciones ejecutadas por `VirtualMachine`. Incluye, entre otras:

```text
LABEL, JUMP, JUMP_IF_FALSE, JUMP_IF_TRUE
FUNC, CALL, RETURN, RETURN_VOID, END_FUNC, HALT
PUSH_CONST, PUSH_UNINITIALIZED, DUP, POP
DECLARE, LOAD, STORE, ENTER_SCOPE, EXIT_SCOPE
ALLOC_ARRAY, LOAD_ARRAY, STORE_ARRAY
ADD, SUB, MUL, DIV, MOD, POW
NEG, NOT, EQ, NE, LT, LE, GT, GE
TO_FLOAT, PRINT
```

Este formato se puede guardar como `.asm`, `.txt` o `.bin` simulado. Incluso con extensión `.bin`, sigue siendo texto UTF-8: no es código máquina, un objeto enlazable ni un ejecutable nativo.

La pestaña de pseudoensamblador muestra la salida anterior y posterior a la optimización. La exportación guarda la versión optimizada.

## 7. Formas de compilar y ejecutar

### 7.1 Ejecutar el IDE

```powershell
cd C:\Repositorios\Comp001\Mini-Lang
python app.py
```

### 7.2 Ejecutar Mini-Lang

- Botón `Ejecutar F5` o tecla `F5`.
- Lee un valor por línea desde la pestaña `Entrada`.
- Compila y ejecuta en la VM.
- Muestra el resultado en `Salida`.

### 7.3 Compilar dentro del IDE

- Botón `Compilar F7`, menú `Compilar > Compilar` o tecla `F7`.
- No ejecuta la VM.
- No pide datos de entrada.
- No guarda archivos.
- Actualiza todos los paneles y selecciona `Pseudoensamblador`.

### 7.4 Exportar pseudoensamblador

```text
Compilar > Compilar a pseudoensamblador...
```

Extensiones ofrecidas:

- `.asm`, recomendada;
- `.txt`;
- `.bin`, simulada y textual.

### 7.5 Exportar y ejecutar JavaScript

```text
Compilar > Compilar a JavaScript...
```

Después:

```powershell
node .\programa.js
```

Con una entrada:

```powershell
"42" | node .\programa.js
```

Con varias entradas:

```powershell
Get-Content .\entrada.txt | node .\programa.js
```

La ejecución de JavaScript no está integrada como terminal dentro del IDE.

## 8. Explorador de proyecto

PLAN7 añadió un panel derecho similar al explorador de un editor moderno:

- `Archivo > Abrir carpeta...` selecciona la raíz;
- doble clic o Enter abre un archivo UTF-8;
- las carpetas aparecen antes que los archivos;
- las subcarpetas se cargan bajo demanda;
- se ocultan `.git`, `__pycache__` y `.pytest_cache`;
- se excluyen enlaces simbólicos y puntos de reanálisis;
- `Ver > Mostrar/Ocultar explorador` controla el panel;
- abrir el primer archivo adopta su carpeta como proyecto;
- se conserva la confirmación de cambios sin guardar.

El explorador es deliberadamente de solo navegación. No crea, renombra, mueve ni elimina archivos.

## 9. Depuración

El IDE permite:

- iniciar una sesión de depuración;
- avanzar una instrucción;
- continuar hasta terminar o alcanzar un punto de interrupción;
- introducir un número de línea como breakpoint;
- resaltar la línea actual;
- inspeccionar salida, pila, llamadas, variables visibles y estado de la VM mediante el snapshot mostrado como JSON.

Los breakpoints no se colocan todavía haciendo clic en el margen del editor.

## 10. Trabajo realizado por etapas

| Etapa | Resultado |
|---|---|
| Núcleo inicial | Lexer, parser, AST, semántica, intérprete, bytecode y VM |
| PLAN2 | IDE, operadores, `for`, entrada, floats, strings, depuración, módulos y optimización |
| PLAN4 | Corrección integral de semántica numérica y promociones `int -> float` |
| PLAN5 | Backend JavaScript con runtime y paridad con VM/intérprete |
| PLAN6 | Exportación de pseudoensamblador y JavaScript |
| PLAN7 | Explorador de proyecto a la derecha |
| PLAN8 | F5 para ejecutar y F7 para compilar sin ejecutar |
| v4.3 | Integración en Git del explorador, exportación, pruebas y actualización de versión |

### Decisión descartada

Durante PLAN6 se exploró un ejecutor HTML autocontenido. El usuario cambió el objetivo hacia guardar artefactos reales del compilador. La implementación HTML se retiró intencionalmente y no forma parte de v4.3.

No debe reintroducirse un `web_runner.py` o una página HTML salvo que se apruebe como una nueva fase independiente.

## 11. Cobertura automatizada

La suite actual utiliza `unittest` y no requiere instalar un framework de pruebas externo.

| Archivo | Casos | Cobertura principal |
|---|---:|---|
| `test_language_matrix.py` | 50 | Matriz de operadores y construcciones |
| `test_minilang.py` | 26 | Lexer, parser, semántica, VM y ejemplos originales |
| `test_gui_helpers.py` | 13 | GUI, PLAN6, F5/F7 y JavaScript exportado |
| `test_plan2_features.py` | 12 | Builtins, módulos, optimización y depuración |
| `test_javascript_codegen.py` | 11 | Estructura y paridad del backend JavaScript |
| `test_numeric_semantics.py` | 9 | Promociones y casos numéricos |
| `test_file_explorer.py` | 8 | Árbol, rutas y apertura segura |
| `test_advanced_examples.py` | 1 | Programa avanzado completo |
| **Total** | **130** | **Suite completa aprobada** |

Las pruebas de JavaScript usan Node.js cuando está disponible y comparan la salida con la VM. También cubren enteros grandes, módulos, entradas, errores y límites de ejecución.

## 12. Diagnósticos

Existe una jerarquía diferenciada:

- error léxico;
- error sintáctico;
- error semántico;
- error de optimización;
- error de generación de código;
- error de ejecución.

Los mensajes se mantienen en español e incluyen fase, línea y columna cuando existe un token de origen. Esta convención debe conservarse en cualquier ampliación.

## 13. Limitaciones actuales

Estas limitaciones no son fallos de las pruebas; son fronteras del diseño actual.

### Lenguaje

- Los arreglos son fijos y su tamaño debe ser un literal entero.
- No existen matrices dinámicas, listas, mapas, registros, clases, interfaces o genéricos.
- No existen parámetros o retornos de tipo arreglo.
- No existe `null`.
- No existen comentarios de bloque `/* ... */`; solo `//`.
- Las funciones se declaran únicamente en el nivel global.
- Los imports son archivos locales relativos; no existe gestor de paquetes.
- No se produce código máquina nativo ni bytecode persistente ejecutable fuera de la VM del proyecto.

### IDE

- Solo hay un buffer/editor visible; no existen pestañas para varios archivos abiertos.
- El proyecto abierto no se restaura automáticamente al reiniciar el IDE.
- El explorador no permite crear, renombrar, mover o borrar.
- No existe terminal integrada.
- No existe ejecución de JavaScript desde el IDE.
- No hay navegación desde un diagnóstico hacia la línea correspondiente con un clic.
- Los breakpoints se introducen mediante diálogo, no desde el margen.
- No existe autocompletado, renombrado semántico ni servidor de lenguaje.

### Distribución

- `MiniLang.spec` conserva la receta histórica de PyInstaller.
- La build final autorizada de v4.3 está en `release-v4.3`.
- `MiniLang.exe` fue generado con Python 3.12.10 y PyInstaller 6.14.2.
- La autoprueba del EXE terminó con código de salida 0.
- El release incluye `MiniLang.exe`, `MiniLang-v4.3.zip`, `RELEASE_NOTES.md` y `SHA256SUMS.txt`.
- El EXE no está firmado digitalmente; Windows puede mostrar una advertencia.
- Cualquier reconstrucción o publicación posterior debe volver a verificarse.

### Navegador y juegos

El traspaso histórico proponía una biblioteca gráfica y juegos de navegador, pero no se implementaron:

- no existe API Canvas;
- no existen `gameInit`, `gameRect`, `gameText` o entrada de teclado para juegos;
- no existe ciclo `requestAnimationFrame`;
- no existe `examples/pong.mini`;
- no existe runner HTML incluido.

El backend JavaScript sí está terminado y constituye una base para retomar esa idea en un plan futuro.

## 14. Qué falta realmente

### Prioridad 0 — Cerrar la entrega actual

1. Revisar y confirmar los cambios locales de documentación.
2. Incorporar a Git los documentos PLAN4, PLAN5, PLAN6, PLAN8 y este seguimiento.
3. Resolver qué documentos antiguos deben versionarse: `PLAN2.md`, `GRAMMAR.md`, `BYTECODE.md`, `ERRORS.md` y `ContextoOtraPC.txt` existen localmente, pero continúan ignorados.
4. Eliminar o conservar conscientemente `programa.js`, que es un artefacto local no versionado.
5. Crear un commit limpio de documentación sin mezclar artefactos generados.

### Prioridad 1 — Pulir el IDE

1. Pestañas de edición para varios archivos.
2. Crear, renombrar y eliminar desde el explorador con confirmaciones seguras.
3. Persistencia de carpeta reciente y preferencias.
4. Breakpoints haciendo clic en el margen.
5. Navegación directa desde errores, tokens o símbolos al código.
6. Terminal integrada o comando explícito para ejecutar el `.js` exportado.

### Prioridad 2 — Calidad y automatización

1. Añadir integración continua para ejecutar las 130 pruebas.
2. Añadir medición de cobertura.
3. Incorporar formateo, lint y análisis estático de Python.
4. Probar proyectos grandes y carga incremental del explorador.
5. Ampliar comparaciones automáticas entre intérprete, VM y JavaScript.

### Prioridad 3 — Nuevas capacidades opcionales

1. Runner seguro para navegador como proyecto separado.
2. Biblioteca gráfica Canvas para juegos.
3. Ejemplo Pong.
4. Formato de bytecode serializado real, si se desea ejecutar fuera del IDE.
5. Firma digital, instalador o publicación remota de v4.3, si se desean como una fase posterior.

## 15. Estado de Git y documentación

En el momento de esta revisión:

- `main` coincidía con `origin/main` en `bc6c278`;
- `.gitignore`, `README.md` y `docs/PLAN7.md` tenían cambios locales;
- `docs/PLAN4.md`, `PLAN5.md`, `PLAN6.md` y `PLAN8.md` estaban sin versionar;
- `programa.js` estaba sin versionar;
- este documento se añade como nuevo archivo;
- no se creó commit;
- posteriormente se autorizó y generó la distribución final local `release-v4.3`.

El README enlaza documentos que están presentes localmente pero ignorados por Git. Antes de clonar el proyecto en otra PC, hay que versionarlos o quitar esos enlaces. De lo contrario, el README puede apuntar a archivos que no llegarán al clon.

## 16. Reglas para continuar el proyecto

1. Ejecutar la suite completa antes y después de cada cambio.
2. Añadir pruebas para cada comportamiento nuevo o error corregido.
3. No reducir validaciones para hacer pasar una prueba.
4. Mantener diagnósticos en español con línea y columna.
5. Generar JavaScript desde el AST optimizado, no desde tokens.
6. Conservar la VM como motor principal y el intérprete como referencia.
7. Mantener paridad entre VM, intérprete y JavaScript.
8. Preservar la división entera de piso y el módulo con semántica de Python.
9. No confundir `.bin` simulado con un binario real.
10. No reintroducir el runner HTML descartado sin un objetivo nuevo y explícito.
11. No atravesar enlaces o puntos de reanálisis desde el explorador.
12. No reconstruir, modificar o publicar EXE sin autorización explícita.
13. No sobrescribir cambios ajenos ni limpiar el repositorio destructivamente.

## 17. Archivos de referencia

### Código

- `app.py`
- `minilang/compiler.py`
- `minilang/lexer.py`
- `minilang/parser.py`
- `minilang/semantic.py`
- `minilang/optimizer.py`
- `minilang/codegen.py`
- `minilang/vm.py`
- `minilang/interpreter.py`
- `minilang/js_codegen.py`
- `minilang/debugger.py`
- `minilang/builtins.py`

### Pruebas

- `tests/test_minilang.py`
- `tests/test_plan2_features.py`
- `tests/test_numeric_semantics.py`
- `tests/test_javascript_codegen.py`
- `tests/test_language_matrix.py`
- `tests/test_file_explorer.py`
- `tests/test_gui_helpers.py`
- `tests/test_advanced_examples.py`

### Planes

- `docs/PLAN.md`
- `docs/PLAN2.md`
- `docs/PLAN4.md`
- `docs/PLAN5.md`
- `docs/PLAN6.md`
- `docs/PLAN7.md`
- `docs/PLAN8.md`

No existe actualmente `PLAN3.md`. La numeración salta de PLAN2 a PLAN4 debido a la evolución histórica de las tareas.

## 18. Checklist de relevo

Antes de empezar una nueva fase:

- [ ] Leer este documento y el plan más reciente.
- [ ] Revisar `git status` para proteger cambios locales.
- [ ] Ejecutar las 130 pruebas.
- [ ] Ejecutar `python app.py --self-test`.
- [ ] Confirmar si Node.js está disponible cuando se toque el backend JavaScript.
- [ ] Crear un PLAN nuevo si la ampliación requiere varias fases.
- [ ] Definir criterios de aceptación antes de editar.
- [ ] No generar EXE salvo autorización explícita.

Antes de entregar una fase:

- [ ] Ejecutar la suite completa.
- [ ] Ejecutar `compileall`.
- [ ] Validar el flujo afectado con una prueba real de Tkinter o Node.js cuando corresponda.
- [ ] Revisar `git diff --check`.
- [ ] Actualizar README, plan y este seguimiento.
- [ ] Informar claramente archivos modificados, pruebas y pendientes.

## 19. Conclusión

Mini-Lang v4.3 ya cumple bien su propósito como lenguaje educativo y laboratorio de compiladores. Tiene un frontend completo, semántica estática, optimización, dos backends utilizables, ejecución segura, depuración, módulos, pruebas amplias y una interfaz cercana a un IDE pequeño.

No hay una corrección funcional crítica conocida pendiente dentro del alcance actual. El trabajo inmediato más importante es cerrar la documentación y el estado de Git. Las ampliaciones posteriores deberían concentrarse en experiencia de IDE, automatización de calidad o, si se aprueba expresamente, el entorno de navegador y juegos planteado históricamente.
