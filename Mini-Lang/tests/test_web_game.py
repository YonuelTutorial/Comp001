import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from minilang import Compiler, MiniLangRuntimeError, SemanticError
from minilang.web_game import build_game_html


NODE = shutil.which("node")


GAME_SOURCE = """
float jugadorX = 10.0;

void iniciar() {
    gameInit(320, 200);
}

void actualizar(float delta) {
    jugadorX += 5.0;
}

void dibujar() {
    gameClear("black");
    gameRect(jugadorX, 20.0, 30.0, 40.0, "blue");
    gameText("Listo", 5.0, 5.0, "white");
}
"""


def run_game_javascript(javascript):
    browser_stub = r'''
const __test_context = {
    fillStyle: "",
    imageSmoothingEnabled: true,
    textBaseline: "",
    font: "",
    fillRect(x, y, width, height) {
        console.log(`RECT ${x},${y},${width},${height}`);
    },
    fillText(text, x, y) {
        console.log(`TEXT ${text}@${x},${y}`);
    }
};
const __test_canvas = {
    width: 640,
    height: 360,
    getContext(kind) { return kind === "2d" ? __test_context : null; },
    focus() {}
};
const __test_error = { textContent: "", style: { display: "none" } };
global.document = {
    getElementById(id) {
        if (id === "minilang-canvas") return __test_canvas;
        if (id === "minilang-error") return __test_error;
        return null;
    }
};
global.window = { addEventListener() {} };
global.performance = { now() { return 0; } };
let __test_frames = 0;
global.requestAnimationFrame = (callback) => {
    if (__test_frames === 0) {
        __test_frames += 1;
        callback(16);
    }
};
'''
    with tempfile.TemporaryDirectory() as directory:
        script = Path(directory) / "game.js"
        script.write_text(browser_stub + "\n" + javascript, encoding="utf-8")
        return subprocess.run(
            [NODE, str(script)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )


class WebGameCompilationTests(unittest.TestCase):
    def test_game_builtins_are_semantically_available(self):
        result = Compiler().compile_game(GAME_SOURCE)
        self.assertIn("__ml_game_init(320n, 200n", result.javascript)
        self.assertIn("__ml_game_rect", result.javascript)
        self.assertIn("__ml_game_start", result.javascript)

    def test_game_builtin_types_are_checked(self):
        source = GAME_SOURCE.replace("gameInit(320, 200)", "gameInit(320.5, 200)")
        with self.assertRaises(SemanticError) as raised:
            Compiler().compile_game(source)
        self.assertIn("argumento 1 de 'gameInit'", str(raised.exception))

    def test_game_contract_requires_all_lifecycle_functions(self):
        source = "void iniciar(){gameInit(100, 100);} void dibujar(){}"
        with self.assertRaises(SemanticError) as raised:
            Compiler().compile_game(source)
        self.assertIn("void actualizar(float delta)", str(raised.exception))

    def test_game_contract_checks_lifecycle_signature(self):
        source = GAME_SOURCE.replace(
            "void actualizar(float delta)", "void actualizar(int delta)"
        )
        with self.assertRaises(SemanticError) as raised:
            Compiler().compile_game(source)
        self.assertIn("debe declararse como 'void actualizar(float delta)'", str(raised.exception))

    def test_game_builtin_has_clear_vm_error(self):
        with self.assertRaises(MiniLangRuntimeError) as raised:
            Compiler().compile_and_run("gameInit(100, 100);")
        self.assertIn("Compilar juego web (.html)", str(raised.exception))

    def test_game_html_is_self_contained(self):
        result = Compiler().compile_game(GAME_SOURCE)
        self.assertTrue(result.game_html.startswith("<!doctype html>"))
        self.assertIn('<canvas id="minilang-canvas"', result.game_html)
        self.assertIn("requestAnimationFrame", result.game_html)
        self.assertNotIn("eval(", result.game_html)
        self.assertNotIn("<script src=", result.game_html)

    def test_inline_script_escapes_user_closing_tag(self):
        html = build_game_html('console.log("</ScRiPt><script>");')
        self.assertEqual(html.lower().count("</script>"), 1)
        self.assertIn("<\\/script>", html)

    def test_regular_javascript_rejects_game_calls_at_runtime(self):
        result = Compiler().compile("gameInit(100, 100);")
        self.assertIn('__ml_game_target_error("gameInit"', result.javascript)
        self.assertEqual(result.game_html, "")


@unittest.skipUnless(NODE, "Node.js no está disponible")
class WebGameExecutionTests(unittest.TestCase):
    def test_one_frame_draws_with_browser_runtime(self):
        result = Compiler(max_steps=1_000).compile_game(GAME_SOURCE)
        completed = run_game_javascript(result.javascript)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("RECT 0,0,320,200", completed.stdout)
        self.assertIn("RECT 15,20,30,40", completed.stdout)
        self.assertIn("TEXT Listo@5,5", completed.stdout)
        self.assertEqual(completed.stderr, "")

    def test_infinite_update_is_stopped_within_frame(self):
        source = GAME_SOURCE.replace(
            "jugadorX += 5.0;", "while (true) { jugadorX += 1.0; }"
        )
        result = Compiler(max_steps=30).compile_game(source)
        completed = run_game_javascript(result.javascript)
        self.assertEqual(completed.returncode, 0)
        self.assertIn("posible ciclo infinito", completed.stderr)
        self.assertNotIn("TEXT Listo", completed.stdout)


if __name__ == "__main__":
    unittest.main()
