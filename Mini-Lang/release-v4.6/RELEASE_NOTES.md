# Mini-Lang v4.6

Build para Windows generada el 2026-08-17.

## Contenido

- `MiniLang.exe`: IDE y compilador Mini-Lang para Windows.
- Título personalizado: `Mini-Lang v4.6 — Yonuel Peña — 2190790 — 17/08/2026`.
- Pestañas con contenido, ruta y cambios sin guardar independientes.
- `Ctrl+N` crea una pestaña y `Ctrl+W` cierra la pestaña activa.
- F5, F7, depuración, búsqueda y exportaciones utilizan la pestaña activa.
- Creación y renombrado de archivos desde el explorador.
- Eliminación recuperable hacia `.minilang-trash`, sin sobrescribir archivos anteriores.
- Validación de rutas externas, enlaces, carpetas, nombres reservados y cambios pendientes.
- Exportación a pseudoensamblador, JavaScript y juegos web HTML.
- Ventana modal `Compilando...`, depurador y explorador de proyecto.

## Verificación

- Commit base de la fuente: `8936321`; la build incluye la actualización local de versión y documentación.
- Python: 3.12.10.
- PyInstaller: 6.14.2.
- Suite completa: 157 pruebas aprobadas.
- Autoprueba del código fuente: aprobada.
- Autoprueba de `MiniLang.exe`: aprobada con código de salida 0.
- Módulos `app`, `minilang.compiler`, `minilang.js_codegen` y `minilang.web_game`: presentes en el paquete.
- `docs/PLAN11.md`: presente en el paquete.

## Uso

Ejecuta `MiniLang.exe`.

Para programas normales utiliza F5, F7 o las opciones de exportación. Para juegos usa `Compilar > Compilar juego web (.html)...` y abre el archivo resultante en un navegador moderno.

## Distribuciones anteriores

La build se generó en `release-v4.6`. No se utilizó como destino ni se sobrescribió `release-v4.3`, `release-v4.4` o `release-v4.5`.

El EXE no está firmado digitalmente y Windows puede mostrar una advertencia.
