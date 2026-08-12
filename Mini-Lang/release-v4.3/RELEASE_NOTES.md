# Mini-Lang v4.3

Build final para Windows generada el 2026-08-12.

## Contenido

- `MiniLang.exe`: IDE y compilador Mini-Lang para Windows.
- Explorador de proyecto lateral.
- F5 para compilar y ejecutar.
- F7 para compilar sin ejecutar.
- Exportación a pseudoensamblador y JavaScript.
- Backend JavaScript compatible con Node.js.
- Depuración paso a paso y puntos de interrupción.

## Verificación

- Commit fuente: `bc6c278`.
- Python: 3.12.10.
- PyInstaller: 6.14.2.
- Suite: 130 pruebas aprobadas.
- Autoprueba del código fuente: aprobada.
- Autoprueba de `MiniLang.exe`: aprobada con código de salida 0.

## Uso

Ejecuta `MiniLang.exe`. Windows puede mostrar una advertencia porque el archivo no está firmado digitalmente.

El pseudoensamblador exportado es textual. La opción `.bin` es una simulación educativa, no código máquina.
