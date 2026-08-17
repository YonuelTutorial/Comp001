# Mini-Lang v4.5

Build para Windows generada el 2026-08-17.

## Contenido

- `MiniLang.exe`: IDE y compilador Mini-Lang para Windows.
- Título personalizado: `Mini-Lang v4.5 — Yonuel Peña — 2190790 — 17/08/2026`.
- Ventana modal `Compilando...` para F7 y todas las opciones del menú `Compilar`.
- Espera interna configurable, actualmente de 1000 ms, sin mostrar el número ni la duración.
- Exportación a pseudoensamblador y JavaScript.
- Compilación de juegos web HTML con Canvas, teclado y `requestAnimationFrame`.
- Explorador de proyecto, depurador, F5 y F7.
- El IDE inicia con el editor vacío.
- Corrección de tipado opcional de eventos del explorador para Pylance.

## Verificación

- Commit base de la fuente: `e56a373`; v4.5 incluye cambios locales posteriores.
- Python: 3.12.10.
- PyInstaller: 6.14.2.
- Suite completa: 144 pruebas aprobadas.
- Autoprueba del código fuente: aprobada.
- Autoprueba de `MiniLang.exe`: aprobada con código de salida 0.
- Módulos `app`, `minilang.compiler`, `minilang.js_codegen` y `minilang.web_game`: presentes en el paquete.
- `docs/PLAN10.md`: presente en el paquete.

## Uso

Ejecuta `MiniLang.exe`.

Para un programa normal puedes utilizar F5, F7 o exportar JavaScript. Para un juego usa `Compilar > Compilar juego web (.html)...`, guarda el archivo y ábrelo en un navegador moderno.

## Distribuciones anteriores

La build se generó en `release-v4.5`. No se utilizó ni sobrescribió `release-v4.3` o `release-v4.4`.

El EXE no está firmado digitalmente y Windows puede mostrar una advertencia.
