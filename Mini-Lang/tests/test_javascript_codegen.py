import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from minilang import Compiler, Interpreter, MiniLangRuntimeError


NODE = shutil.which("node")


def normalized_output(text):
    return text[:-1] if text.endswith("\n") else text


def run_node(javascript, input_text=""):
    with tempfile.TemporaryDirectory() as directory:
        script = Path(directory) / "program.js"
        script.write_text(javascript, encoding="utf-8")
        return subprocess.run(
            [NODE, str(script)],
            input=input_text,
            capture_output=True,
            encoding="utf-8",
            timeout=30,
        )


class JavaScriptStructureTests(unittest.TestCase):
    def test_compilation_result_contains_javascript(self):
        result = Compiler().compile("float x = 5; print(x / 2);")
        self.assertTrue(result.javascript.startswith('"use strict";'))
        self.assertIn("function __ml_div", result.javascript)
        self.assertIn("__ml_run(() => {", result.javascript)
        self.assertNotIn("eval(", result.javascript)

    def test_generation_is_deterministic_and_uses_safe_names(self):
        source = "int class = 1; int __ml_print = 2; print(class + __ml_print);"
        first = Compiler().compile(source).javascript
        second = Compiler().compile(source).javascript
        self.assertEqual(first, second)
        self.assertNotIn("let class", first)
        self.assertNotIn("let __ml_print =", first)

    def test_gui_result_keeps_bytecode_and_javascript(self):
        result = Compiler().compile("print(1 + 2);")
        self.assertIn("PUSH_CONST 3", result.assembly)
        self.assertIn("__ml_print(3n, \"int\")", result.javascript)


@unittest.skipUnless(NODE, "Node.js no está disponible")
class JavaScriptExecutionTests(unittest.TestCase):
    def assert_js_matches(self, source, input_text="", max_steps=1_000_000):
        values = iter(input_text.splitlines())
        provider = (lambda prompt: next(values)) if input_text else None
        result = Compiler(max_steps=max_steps, input_provider=provider).compile_and_run(source)
        reference_values = iter(input_text.splitlines())
        reference_provider = (lambda prompt: next(reference_values)) if input_text else None
        reference = Interpreter(
            max_steps=max_steps, input_provider=reference_provider
        ).ejecutar(result.ast)
        node = run_node(result.javascript, input_text)

        self.assertEqual(node.returncode, 0, node.stderr)
        self.assertEqual(normalized_output(node.stdout), result.output)
        self.assertEqual(reference, result.output)
        return result

    def test_language_constructs_match(self):
        cases = [
            "print(2 + 3 * 4 ^ 2); print(-3 / 2); print(-3 % 2);",
            "print(1 == 1.0); print(2 < 2.5); print(1 + 2.5); print(5.0 / 2);",
            'print("Mini" + "-Lang"); print(true && !false);',
            "float x = 5; float a[2]; a[0] = x; a[1] = 2.5; print(a[0] / 2); print(a[1]);",
            "int f(int n){if(n<=1){return 1;}return n*f(n-1);}print(f(6));",
            "int s=0;for(int i=0;i<6;i++){if(i==2){continue;}if(i==5){break;}s+=i;}print(s);",
            'bool marca(){print("mal");return true;}print(false&&marca());print(true||marca());',
        ]
        for source in cases:
            with self.subTest(source=source):
                self.assert_js_matches(source)

    def test_builtins_and_inputs_match(self):
        source = """
        print(inputInt());
        print(inputFloat());
        print(inputString());
        print(inputBool());
        print(length("Mini-Lang"));
        print(substring("abcdef", 1, 3));
        print(toString(5.0));
        print(toInt("41") + 1);
        print(toFloat("2.5") + 1);
        print(contains("Mini-Lang", "Lang"));
        print(regexMatch("abc123", "[0-9]+"));
        """
        self.assert_js_matches(source, "9\n2.5\ntexto\ntrue\n")

    def test_identifiers_do_not_collide(self):
        source = """
        int class = 1;
        int __ml_print = 2;
        int valor() { return 3; }
        int prueba() { int valor = 4; return valor; }
        print(class + __ml_print);
        print(valor());
        print(prueba());
        """
        self.assert_js_matches(source)

    def test_large_integers_match(self):
        self.assert_js_matches("print(2 ^ 60); print((2 ^ 60) + 3);")

    def test_module_import_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "util.mini").write_text(
                "int _doble(int n){return n*2;} int cuatro(){return _doble(2);}",
                encoding="utf-8",
            )
            source = 'import "util.mini"; print(cuatro());'
            result = Compiler().compile_and_run(source, root / "main.mini")
            node = run_node(result.javascript)
            self.assertEqual(node.returncode, 0, node.stderr)
            self.assertEqual(normalized_output(node.stdout), result.output)

    def test_advanced_program_matches(self):
        source = (Path(__file__).parents[1] / "test_advanced.txt").read_text(encoding="utf-8")
        self.assert_js_matches(source)

    def test_runtime_errors_match(self):
        cases = [
            ("int x; print(x);", ""),
            ("print(x); int x = 1;", ""),
            ("int x=inputInt(); print(1/x);", "0\n"),
            ("int a[1]; int i=inputInt(); print(a[i]);", "2\n"),
        ]
        for source, input_text in cases:
            with self.subTest(source=source):
                values = iter(input_text.splitlines())
                provider = (lambda prompt, values=values: next(values)) if input_text else None
                with self.assertRaises(MiniLangRuntimeError) as raised:
                    Compiler(input_provider=provider).compile_and_run(source)
                result = Compiler().compile(source)
                node = run_node(result.javascript, input_text)
                self.assertEqual(node.returncode, 1)
                self.assertEqual(normalized_output(node.stderr), str(raised.exception))

    def test_runtime_limits_stop_infinite_execution(self):
        loop = Compiler(max_steps=30).compile("while(true){}")
        loop_node = run_node(loop.javascript)
        self.assertEqual(loop_node.returncode, 1)
        self.assertIn("posible ciclo infinito", loop_node.stderr)

        recursion = Compiler(max_call_depth=10).compile("void f(){f();}f();")
        recursion_node = run_node(recursion.javascript)
        self.assertEqual(recursion_node.returncode, 1)
        self.assertIn("profundidad máxima", recursion_node.stderr)


if __name__ == "__main__":
    unittest.main()
