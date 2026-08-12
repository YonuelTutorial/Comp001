# Plan 8 — Atajos de compilación y ejecución

## Objetivo

Añadir los atajos principales de un IDE para ejecutar y construir el programa actual:

- `F5`: ejecutar.
- `F7`: compilar o construir sin ejecutar.

Los atajos deben invocar las mismas operaciones disponibles en la interfaz y conservar los errores, límites y paneles actuales.

## Base

- Versión de referencia: Mini-Lang v4.2.9 con PLAN7.
- Suite inicial: 128 pruebas aprobadas.
- `Ejecutar` ya compila y ejecuta mediante la máquina virtual.
- PLAN6 permite exportar pseudoensamblador y JavaScript a archivos.
- No existe todavía una compilación interna independiente de la ejecución o exportación.

## Contrato

### F5 — Ejecutar

`F5` utilizará el flujo actual de ejecución:

1. Leer los valores de la pestaña `Entrada`.
2. Compilar el contenido del editor.
3. Ejecutar el bytecode en la máquina virtual.
4. Actualizar todos los paneles.
5. Seleccionar `Salida` o `Errores` según el resultado.
6. Actualizar la barra de estado.

### F7 — Compilar

`F7` construirá el programa sin ejecutarlo:

1. Ejecutar lexer, parser, módulos y análisis semántico.
2. Optimizar y generar bytecode, pseudoensamblador y JavaScript.
3. Actualizar tokens, AST, símbolos y resultados compilados.
4. Dejar `Salida` vacía porque no se ejecutó la máquina virtual.
5. Seleccionar la pestaña `Pseudoensamblador`.
6. Mostrar `Compilación completada` en la barra de estado.

F7 no solicitará datos de entrada y no abrirá un diálogo para guardar archivos.

## Interfaz

### Barra

La barra mostrará:

- `Ejecutar F5`.
- `Compilar F7`.

### Menú Compilar

El menú tendrá esta estructura:

```text
Compilar
├─ Compilar                         F7
├─ Compilar a pseudoensamblador...
└─ Compilar a JavaScript...
```

Las dos últimas opciones continúan siendo exportaciones a archivo.

## Fases

### Fase 1 — Compilación interna

- [x] Crear `build_code()`.
- [x] Compilar sin ejecutar la máquina virtual.
- [x] Actualizar paneles y estado.
- [x] Mostrar errores mediante el flujo existente.

### Fase 2 — Atajos e interfaz

- [x] Asociar `F5` con `run_code()`.
- [x] Asociar `F7` con `build_code()`.
- [x] Añadir aceleradores visibles al menú.
- [x] Añadir el comando Compilar a la barra.

### Fase 3 — Pruebas

- [x] Verificar los bindings de F5 y F7.
- [x] Verificar que F7 no ejecuta ni solicita entrada.
- [x] Verificar panel, estado y resultado de una compilación correcta.
- [x] Verificar errores de F7.
- [x] Confirmar que las exportaciones de PLAN6 permanecen disponibles.

### Fase 4 — Verificación

- [x] Ejecutar toda la suite.
- [x] Ejecutar la autoprueba del código fuente.
- [x] Ejecutar la prueba visual mínima de Tkinter.
- [x] Validar sintaxis Python y diff.
- [x] Confirmar que no se generaron ejecutables.

## Archivos previstos

- `app.py`
- `tests/test_gui_helpers.py`
- `README.md`
- `docs/PLAN8.md`

## Criterios de aceptación

- F5 produce el mismo resultado que el botón Ejecutar.
- F7 compila y actualiza resultados sin ejecutar el programa.
- F7 funciona aunque el código contenga una llamada de entrada que solo se usaría al ejecutar.
- Los errores de compilación aparecen en `Errores`.
- El menú comunica visualmente los atajos.
- Las exportaciones `.asm`, `.txt`, `.bin` simulado y `.js` continúan funcionando.
- PLAN7 y el resto del IDE conservan su comportamiento.
- No se genera ni reconstruye ningún EXE.

## Comandos

```powershell
python -m unittest tests.test_gui_helpers -v
python -m unittest discover -s tests -v
python app.py --self-test
```

## Registro

- [x] Alcance definido.
- [x] Plan de implementación creado.
- [x] F5 y F7 integrados en Tkinter.
- [x] Compilación interna sin ejecución implementada.
- [x] Suite completa: 130 pruebas aprobadas.
- [x] F7 y F5 validados mediante eventos reales de teclado en Tkinter.
- [x] Autoprueba del código fuente aprobada.
- [x] No se generó ni reconstruyó ningún EXE.
