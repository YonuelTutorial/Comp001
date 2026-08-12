# Plan 4 — Corrección de semántica numérica

## Objetivo

Corregir los casos numéricos en los que la ejecución optimizada no conserva los tipos estáticos de Mini-Lang, sin romper la GUI, el intérprete, el pseudoensamblador, la máquina virtual, el depurador ni los módulos.

Este trabajo no modifica ni reconstruye ejecutables o artefactos de distribución.

## Estado inicial

- Commit de referencia: `b0d9f95` (`v4.1`).
- Suite base: 93 pruebas aprobadas.
- Escenarios avanzados: 20 aprobados.
- Autoprueba del ejecutable v4.1 existente: aprobada.
- El intérprete y la VM deciden actualmente la división entera mediante los tipos de los valores de Python.
- El análisis semántico permite promoción `int` a `float`, pero no inserta una conversión en el AST.
- El optimizador etiqueta toda negación constante como `int`, incluso si el operando es `float`.

## Casos que deben corregirse

```text
print(-1.5 / 2);                                      -> -0.75
float x = 5; print(x / 2);                            -> 2.5
float x; x = 5; print(x / 2);                         -> 2.5
float mitad(float x) { return x / 2; } print(mitad(5)); -> 2.5
float valor() { return 5; } print(valor() / 2);       -> 2.5
float datos[1]; datos[0] = 5; print(datos[0] / 2);    -> 2.5
```

Se conserva el comportamiento existente:

```text
print(-3 / 2); -> -2
print(-3 % 2); -> 1
```

## Contrato numérico

1. `int / int` utiliza división de piso, equivalente a `//` de Python.
2. Una operación numérica con al menos un operando `float` produce `float`.
3. Un valor `int` usado en un contexto que exige `float` se convierte realmente a `float`.
4. La negación unaria conserva el tipo numérico de su operando.
5. El módulo conserva la semántica de Python, incluso con operandos negativos.
6. Las conversiones implícitas conservan el token de origen para los diagnósticos.

## Diseño

### Conversión implícita

Añadir un nodo interno `CastExpr` al AST. No se añadirá sintaxis nueva al lenguaje.

El análisis semántico insertará `CastExpr(..., "float")` cuando un `int` se utilice como:

- inicializador de una variable `float`;
- valor asignado a una variable `float`;
- elemento de un arreglo `float`;
- argumento de un parámetro `float`;
- retorno de una función `float`.

### Ejecución

- `Interpreter` evaluará `CastExpr` con `float(valor)`.
- `CodeGenerator` emitirá `TO_FLOAT`.
- `VirtualMachine` ejecutará `TO_FLOAT` sobre la pila.
- El depurador podrá mostrar la nueva instrucción sin tratamiento especial.

### Optimización

- La negación de un literal conservará `int` o `float` según el operando.
- `CastExpr` aplicado a un literal se plegará a un literal `float`.
- La propagación de constantes conservará el tipo convertido.
- La optimización no cambiará la división de enteros ni el módulo.

## Fases

### Fase 1 — Pruebas de regresión

- [x] Añadir pruebas para todos los casos numéricos de este documento.
- [x] Comparar el intérprete del AST semántico sin optimizar con la VM.
- [x] Comparar también el AST optimizado con ambos resultados.
- [x] Verificar posiciones y mensajes en errores relacionados.

### Fase 2 — AST y semántica

- [x] Crear `CastExpr`.
- [x] Inferir su tipo como `float`.
- [x] Insertar promociones en declaraciones, asignaciones y arreglos.
- [x] Insertar promociones en argumentos y retornos.

### Fase 3 — Motores

- [x] Implementar `CastExpr` en el intérprete.
- [x] Generar la instrucción `TO_FLOAT`.
- [x] Ejecutar `TO_FLOAT` en la VM.
- [x] Mantener compatibilidad con el depurador.

### Fase 4 — Optimizador

- [x] Corregir el tipo de la negación unaria.
- [x] Plegar conversiones constantes.
- [x] Conservar tipos durante propagación y simplificación.

### Fase 5 — Verificación

- [x] Ejecutar la nueva suite numérica.
- [x] Ejecutar las 93 pruebas existentes.
- [x] Ejecutar los 20 escenarios avanzados.
- [x] Ejecutar la autoprueba desde el código fuente.
- [x] Confirmar que no se modificaron ejecutables.

## Archivos previstos

- `minilang/ast_nodes.py`
- `minilang/semantic.py`
- `minilang/optimizer.py`
- `minilang/interpreter.py`
- `minilang/codegen.py`
- `minilang/vm.py`
- `tests/test_numeric_semantics.py`
- `docs/BYTECODE.md`
- `docs/PLAN4.md`

## Criterios de aceptación

- Todos los casos indicados producen la salida esperada.
- El intérprete sin optimizar, el intérprete optimizado y la VM coinciden.
- Las pruebas existentes continúan aprobadas.
- El pseudoensamblador sigue siendo determinista.
- Los errores continúan en español con fase, línea y columna.
- No se genera, reconstruye ni modifica ningún EXE.

## Comandos de verificación

```powershell
python -m unittest tests.test_numeric_semantics -v
python -m unittest discover -s tests -v
python app.py --self-test
```

## Registro

- [x] Diagnóstico inicial completado.
- [x] Contrato numérico definido.
- [x] Plan de implementación creado.
- [x] Pruebas numéricas implementadas.
- [x] Promociones implícitas implementadas en todos los motores.
- [x] Suite completa: 102 pruebas aprobadas.
- [x] Autoprueba del código fuente aprobada.
- [x] Los 20 escenarios avanzados conservan la salida esperada.
- [x] El ejecutable v4.1 conserva su checksum SHA-256 original.
