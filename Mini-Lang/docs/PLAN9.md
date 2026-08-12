# Plan 9 — Juegos web con Canvas

## Objetivo

Añadir un destino de compilación específico para crear juegos pequeños de navegador escritos en Mini-Lang.

El IDE guardará un archivo HTML autocontenido que incluirá el JavaScript generado, un `canvas`, el ciclo de animación, el estado del teclado y una zona visible para errores. El archivo podrá abrirse directamente en un navegador sin instalar dependencias ni levantar un servidor.

## Base

- Versión de referencia: Mini-Lang v4.3 con PLAN4–PLAN8.
- Suite inicial: 130 pruebas aprobadas.
- El backend JavaScript y la exportación `.js` ya existen.
- La VM no dispone de pantalla, teclado en tiempo real ni ciclo gráfico.
- El ejecutor HTML genérico de PLAN6 no forma parte del producto actual; este plan crea un artefacto nuevo y limitado a juegos.

## Contrato

### Destino de compilación

El menú `Compilar` añadirá:

```text
Compilar juego web (.html)...
```

Esta opción:

1. Ejecuta lexer, parser, resolución de módulos y análisis semántico.
2. Comprueba el contrato del juego.
3. Genera JavaScript para navegador.
4. Empaqueta el JavaScript y el `canvas` en un solo `.html`.
5. Guarda el archivo elegido sin ejecutarlo ni abrir automáticamente el navegador.

La exportación JavaScript normal continúa generando `.js` y F7 continúa compilando sin guardar.

### Funciones del juego

El lenguaje reconocerá estas funciones nativas:

```text
void gameInit(int ancho, int alto)
void gameClear(string color)
void gameRect(float x, float y, float ancho, float alto, string color)
void gameText(string texto, float x, float y, string color)
bool gameKey(string tecla)
float gameDelta()
int gameWidth()
int gameHeight()
```

Las coordenadas aceptan enteros mediante la promoción numérica existente de `int` a `float`.

### Ciclo de vida

Todo juego web debe declarar exactamente:

```text
void iniciar()
void actualizar(float delta)
void dibujar()
```

El runtime llamará una vez a `iniciar()` y después usará `requestAnimationFrame` para llamar a `actualizar(delta)` y `dibujar()`.

`delta` representa los segundos transcurridos desde el fotograma anterior y tendrá un límite para evitar saltos grandes después de suspender la pestaña.

### Seguridad y límites

- No se usará `eval`.
- El programa Mini-Lang no tendrá acceso directo al DOM.
- El HTML no cargará bibliotecas, scripts ni recursos de red.
- El presupuesto de instrucciones se reiniciará en cada fotograma, manteniendo la detección de ciclos infinitos dentro de un fotograma.
- Los errores detendrán la animación y se mostrarán dentro de la página y en la consola.
- Las teclas de dirección y espacio no desplazarán la página mientras se juega.

### VM y F5

Las funciones `game*` son exclusivas del destino web. El análisis semántico las reconocerá para permitir F7 y la inspección del programa, pero F5 y el depurador mostrarán un error explícito indicando que debe usarse `Compilar juego web (.html)...`.

## Fases

### Fase 1 — Contrato del compilador

- [x] Registrar las funciones nativas del juego y sus tipos.
- [x] Conservar un error explícito cuando se ejecuten en la VM.
- [x] Validar las tres funciones del ciclo de vida.
- [x] Añadir el artefacto `game_html` al resultado de compilación.

### Fase 2 — Runtime Canvas

- [x] Crear y configurar el contexto 2D.
- [x] Implementar limpieza, rectángulos y texto.
- [x] Implementar estado de teclado.
- [x] Implementar tamaño y delta.
- [x] Implementar el ciclo con `requestAnimationFrame`.
- [x] Reiniciar los límites por fotograma y presentar errores.

### Fase 3 — Exportación e interfaz

- [x] Generar HTML autocontenido con codificación UTF-8.
- [x] Escapar cierres de `script` procedentes de cadenas del usuario.
- [x] Añadir la opción al menú `Compilar`.
- [x] Mostrar el JavaScript del juego en el panel existente.

### Fase 4 — Ejemplo y documentación

- [x] Añadir un ejemplo que mueva un cuadrado con las flechas.
- [x] Documentar cómo compilar y abrir el juego.
- [x] Explicar la diferencia entre F5, `.js` y juego web `.html`.

### Fase 5 — Pruebas y verificación

- [x] Probar tipos y errores de las funciones nativas.
- [x] Probar el contrato de las funciones del ciclo de vida.
- [x] Probar la estructura y el aislamiento del HTML.
- [x] Ejecutar un fotograma con un entorno de navegador simulado.
- [x] Verificar la exportación desde el IDE.
- [x] Ejecutar la suite completa y la autoprueba.
- [x] Confirmar que no se generó ni reconstruyó ningún EXE.

## Archivos previstos

- `minilang/builtins.py`
- `minilang/compiler.py`
- `minilang/js_codegen.py`
- `minilang/web_game.py`
- `app.py`
- `examples/cuadrado.mini`
- `tests/test_web_game.py`
- `tests/test_gui_helpers.py`
- `README.md`
- `docs/PLAN9.md`

## Criterios de aceptación

- El ejemplo con `gameInit` deja de producir «función no declarada».
- Un juego sin las tres funciones requeridas no se exporta y explica el contrato incumplido.
- El HTML exportado es autocontenido, no usa `eval` y contiene un `canvas`.
- El cuadrado puede moverse mediante las teclas de dirección en un navegador.
- Un ciclo infinito dentro de `actualizar` se detiene sin congelar indefinidamente el juego.
- F5 informa que las funciones gráficas son exclusivas del juego web.
- La generación JavaScript normal, la VM, el depurador, F5, F7 y las exportaciones anteriores conservan su comportamiento.
- No se genera ni reconstruye ningún EXE.

## Comandos

```powershell
python -m unittest tests.test_web_game -v
python -m unittest tests.test_gui_helpers -v
python -m unittest discover -s tests -v
python app.py --self-test
```

## Registro

- [x] Alcance y contrato definidos.
- [x] Implementación completada.
- [x] Suite completa: 141 pruebas aprobadas.
- [x] Juego de ejemplo compilado y un fotograma validado con Node.js.
- [x] Autoprueba, `compileall` y `git diff --check` aprobados.
- [x] No se generó ni reconstruyó ningún EXE.
- [x] Posteriormente, por autorización separada, se generó `release-v4.4` sin modificar `release-v4.3`.
