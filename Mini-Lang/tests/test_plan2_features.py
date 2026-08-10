import tempfile
import unittest
from pathlib import Path

from minilang import Compiler, Debugger, MiniLangRuntimeError, SemanticError


class OperatorsAndTypesTests(unittest.TestCase):
    def test_operators_and_assignments(self):
        source = """
        int x = 5;
        x++;
        x += 4;
        x %= 7;
        print(x);
        print(2 ^ 3 ^ 2);
        print(17 % 5);
        """
        self.assertEqual(Compiler().compile_and_run(source).output, "3\n512\n2")

    def test_for_break_and_continue(self):
        source = """
        int suma = 0;
        for (int i = 0; i < 10; i++) {
            if (i == 3) { continue; }
            if (i == 7) { break; }
            suma += i;
        }
        print(suma);
        """
        self.assertEqual(Compiler().compile_and_run(source).output, "18")

    def test_float_and_string_operations(self):
        source = """
        float x = 2;
        float y = 3.5;
        print(x + y);
        print(y / 2);
        print("Mini" + "-Lang");
        """
        self.assertEqual(Compiler().compile_and_run(source).output, "5.5\n1.75\nMini-Lang")


class BuiltinTests(unittest.TestCase):
    def test_inputs(self):
        values = iter(["9", "2.5", "texto", "true"])
        source = """
        print(inputInt());
        print(inputFloat());
        print(inputString());
        print(inputBool());
        """
        result = Compiler(input_provider=lambda prompt: next(values)).compile_and_run(source)
        self.assertEqual(result.output, "9\n2.5\ntexto\nTrue")

    def test_string_builtins_and_regex(self):
        source = """
        print(length("Mini-Lang"));
        print(substring("abcdef", 1, 3));
        print(contains("Mini-Lang", "Lang"));
        print(regexMatch("abc123", "[0-9]+"));
        print(toInt("41") + 1);
        print(toFloat("2.5") + 1);
        """
        self.assertEqual(Compiler().compile_and_run(source).output, "9\nbcd\nTrue\nTrue\n42\n3.5")

    def test_missing_input(self):
        with self.assertRaisesRegex(MiniLangRuntimeError, "inputInt"):
            Compiler(input_provider=lambda prompt: "texto").compile_and_run("print(inputInt());")


class ModuleTests(unittest.TestCase):
    def test_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "matematica.mini").write_text(
                "int cuadrado(int n) { return n * n; }", encoding="utf-8"
            )
            source = 'import "matematica.mini"; print(cuadrado(9));'
            result = Compiler().compile_and_run(source, root / "principal.mini")
            self.assertEqual(result.output, "81")

    def test_circular_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.mini").write_text('import "b.mini";', encoding="utf-8")
            (root / "b.mini").write_text('import "a.mini";', encoding="utf-8")
            with self.assertRaisesRegex(SemanticError, "circular"):
                Compiler().compile_and_run('import "a.mini";', root / "main.mini")

    def test_private_module_symbol(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "util.mini").write_text(
                "int _doble(int n) { return n * 2; } int cuatro() { return _doble(2); }",
                encoding="utf-8",
            )
            public = Compiler().compile_and_run(
                'import "util.mini"; print(cuatro());', root / "main.mini"
            )
            self.assertEqual(public.output, "4")
            with self.assertRaisesRegex(SemanticError, "no declarada"):
                Compiler().compile_and_run(
                    'import "util.mini"; print(_doble(2));', root / "main.mini"
                )


class OptimizerAndDebuggerTests(unittest.TestCase):
    def test_constant_branch_is_removed(self):
        result = Compiler().compile_and_run("if (true) { print(1 + 2); } else { print(9); }")
        self.assertEqual(result.output, "3")
        self.assertNotIn("JUMP_IF_FALSE", result.assembly)
        self.assertNotIn("PUSH_CONST 9", result.assembly)

    def test_constant_propagation_reduces_bytecode(self):
        result = Compiler().compile_and_run("int a=2; int b=a+3; print(b);")
        self.assertEqual(result.output, "5")
        self.assertGreater(
            len(result.unoptimized_assembly.splitlines()),
            len(result.assembly.splitlines()),
        )
        self.assertNotIn("ADD", result.assembly)

    def test_debugger(self):
        source = "int x = 1;\nx += 2;\nprint(x);"
        result = Compiler().compile(source)
        debugger = Debugger(result.bytecode)
        debugger.add_breakpoint(2)
        state = debugger.continue_run()
        self.assertTrue(state["paused"])
        self.assertEqual(state["line"], 2)
        state = debugger.continue_run()
        self.assertTrue(state["halted"])
        self.assertEqual(state["output"], ["3"])


if __name__ == "__main__":
    unittest.main()
