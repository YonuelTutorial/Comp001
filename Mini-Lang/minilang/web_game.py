import html
import re


def build_game_html(javascript, title="Juego Mini-Lang"):
    """Empaqueta el JavaScript generado en una página de juego autocontenida."""
    safe_title = html.escape(str(title), quote=True)
    safe_javascript = re.sub(r"</script", r"<\\/script", javascript, flags=re.IGNORECASE)
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    :root {{ color-scheme: dark; }}
    * {{ box-sizing: border-box; }}
    html, body {{
      width: 100%;
      min-height: 100%;
      margin: 0;
      background: #0d1117;
      color: #e6edf3;
      font-family: system-ui, sans-serif;
    }}
    body {{
      display: grid;
      place-items: center;
      padding: 24px;
    }}
    main {{
      display: grid;
      gap: 12px;
      justify-items: center;
      max-width: 100%;
    }}
    canvas {{
      display: block;
      max-width: 100%;
      height: auto;
      border: 1px solid #30363d;
      background: #000;
      box-shadow: 0 12px 36px rgb(0 0 0 / 35%);
    }}
    #minilang-error {{
      display: none;
      width: min(720px, 100%);
      margin: 0;
      padding: 12px;
      border: 1px solid #f85149;
      border-radius: 6px;
      background: #3d1719;
      color: #ffb3ad;
      white-space: pre-wrap;
    }}
    .hint {{ margin: 0; color: #8b949e; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <main>
    <canvas id="minilang-canvas" width="640" height="360" tabindex="0"
            aria-label="Juego creado con Mini-Lang"></canvas>
    <p class="hint">Haz clic en el juego y usa el teclado.</p>
    <pre id="minilang-error" role="alert"></pre>
  </main>
  <script>
{safe_javascript}
  </script>
</body>
</html>
"""
