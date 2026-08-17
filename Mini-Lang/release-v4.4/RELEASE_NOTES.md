# Mini-Lang v4.4

Build para Windows generada el 2026-08-12.

## Contenido

- `MiniLang.exe`: IDE y compilador Mini-Lang para Windows.
- Todo lo incluido previamente en v4.3.
- Nuevo destino `Compilar juego web (.html)...`.
- API Canvas: `gameInit`, `gameClear`, `gameRect` y `gameText`.
- Teclado y estado del juego mediante `gameKey`, `gameDelta`, `gameWidth` y `gameHeight`.
- Ciclo de vida `iniciar`, `actualizar(float delta)` y `dibujar` con `requestAnimationFrame`.
- HTML autocontenido que no requiere servidor ni archivos adicionales.
- Límite de instrucciones reiniciado por fotograma y presentación de errores en la página.

## Verificación

- Commit base de la fuente: `bc6c278`;
- Python: 3.12.10.
- PyInstaller: 6.14.2.
- Suite: 141 pruebas aprobadas.
- Prueba de un fotograma del runtime Canvas: aprobada con Node.js 24.19.0.
- Autoprueba del código fuente: aprobada.
- Autoprueba de `MiniLang.exe`: aprobada con código de salida 0.
- Módulos `minilang.compiler`, `minilang.js_codegen` y `minilang.web_game`: presentes en el paquete.

## Probar el juego

1. Ejecuta `MiniLang.exe`.
2. Abre un programa Mini-Lang que declare `iniciar`, `actualizar` y `dibujar`.
3. Selecciona `Compilar > Compilar juego web (.html)...`.
4. Guarda el archivo y ábrelo con doble clic en un navegador moderno.

F5 continúa ejecutando la máquina virtual y no ofrece gráficos. Para ejecutar llamadas `game*`, utiliza la exportación de juego web.
