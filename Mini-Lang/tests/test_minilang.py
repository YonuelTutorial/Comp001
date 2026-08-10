import re
import unittest
from pathlib import Path

from minilang import (
    CodeGenerator,
    Compiler,
    Lexer,
    MiniLangRuntimeError,
    OptimizationError,
    Parser,
    SemanticAnalyzer,
    SemanticError,
    Interpreter,
    ParserError,
)


def run(source, **kwargs):
    return Compiler(**kwargs).compile_and_run(source)


class LexerTests(unittest.TestCase):
    def test_keywords_only_match_complete_words(self):
        tokens = Lexer().tokenize("int integer = 1; int printer = 2; int whileCount = 3;")
        identifiers = [token.value for token in tokens if token.kind == "ID"]
        self.assertEqual(identifiers, ["integer", "printer", "whileCount"])

    def test_tokens_include_line_and_column(self):
        tokens = Lexer().tokenize("int x = 1;\nprint(x);")
        print_token = next(token for token in tokens if token.kind == "PRINT")
        self.assertEqual((print_token.line, print_token.column), (2, 1))

    def test_parser_error_reports_position(self):
        with self.assertRaisesRegex(ParserError, r"línea 2, columna 8"):
            run("int x = 1;\nprint(x;")


class LanguageTests(unittest.TestCase):
    def test_else_and_else_if(self):
        source = """
        int x = 2;
        if (x == 1) { print("uno"); }
        else if (x == 2) { print("dos"); }
        else { print("otro"); }
        """
        self.assertEqual(run(source).output, "dos")

    def test_string_variables_escapes_and_codegen(self):
        source = r'''string mensaje = "Él dijo \"hola\"\nfin"; print(mensaje);'''
        result = run(source)
        self.assertEqual(result.output, 'Él dijo "hola"\nfin')
        self.assertIn(r'\"hola\"\nfin', result.assembly)

    def test_zero_and_multiple_parameters(self):
        source = """
        string saludo() { return "hola"; }
        int suma(int a, int b, int c) { return a + b + c; }
        print(saludo());
        print(suma(1, 2, 3));
        """
        self.assertEqual(run(source).output, "hola\n6")

    def test_forward_call_and_mutual_recursion(self):
        source = """
        print(par(8));
        bool par(int n) {
            if (n == 0) { return true; }
            return impar(n - 1);
        }
        bool impar(int n) {
            if (n == 0) { return false; }
            return par(n - 1);
        }
        """
        self.assertEqual(run(source).output, "True")

    def test_void_function(self):
        source = 'void saluda() { print("hola"); return; } saluda();'
        self.assertEqual(run(source).output, "hola")

    def test_extended_operators(self):
        source = "print(!(2 >= 3) && 4 != 5); print(2 <= 2 || false); print(-5 + 7);"
        self.assertEqual(run(source).output, "True\nTrue\n2")

    def test_declaration_without_initializer(self):
        self.assertEqual(run("int x; x = 7; print(x);").output, "7")
        with self.assertRaisesRegex(MiniLangRuntimeError, "antes de inicializarse"):
            run("int x; print(x);")

    def test_break_and_continue(self):
        source = """
        int i = 0;
        while (true) {
            i = i + 1;
            if (i == 2) { continue; }
            print(i);
            if (i >= 3) { break; }
        }
        """
        self.assertEqual(run(source).output, "1\n3")

    def test_scope_is_unwound_by_continue_and_break(self):
        source = """
        int exterior = 10;
        int i = 0;
        while (true) {
            int exterior = i;
            i = i + 1;
            if (i == 1) { continue; }
            if (i == 2) { break; }
        }
        print(exterior);
        """
        self.assertEqual(run(source).output, "10")


class SemanticTests(unittest.TestCase):
    def assert_semantic_error(self, source, text):
        with self.assertRaisesRegex(SemanticError, text):
            run(source)

    def test_return_outside_function(self):
        self.assert_semantic_error("return 1;", "solo puede utilizarse dentro")

    def test_missing_return(self):
        self.assert_semantic_error("int f(int n) { int x = n; }", "todas sus rutas")

    def test_partial_return(self):
        self.assert_semantic_error("int f(int n) { if (n > 0) { return n; } }", "todas sus rutas")

    def test_break_path_prevents_guaranteed_return(self):
        source = "int f(bool salir) { while (true) { if (salir) { break; } return 1; } }"
        self.assert_semantic_error(source, "todas sus rutas")

    def test_global_function_variable_collision(self):
        self.assert_semantic_error("int f = 1; int f(int n) { return n; }", "ya está en uso")

    def test_invalid_array_size_and_constant_index(self):
        self.assert_semantic_error("int a[0];", "mayor que cero")
        self.assert_semantic_error("int a[2]; print(a[-1]);", "fuera de rango")
        self.assert_semantic_error("int a[2]; print(a[2]);", "fuera de rango")

    def test_break_outside_loop(self):
        self.assert_semantic_error("break;", "dentro de un ciclo")


class RuntimeAndOptimizationTests(unittest.TestCase):
    def test_dynamic_array_bounds(self):
        with self.assertRaisesRegex(MiniLangRuntimeError, "fuera de rango"):
            run("int a[2]; int i = 0 - 1; print(a[i]);")

    def test_constant_division_by_zero(self):
        with self.assertRaisesRegex(OptimizationError, "división por cero"):
            run("print(1 / 0);")

    def test_dynamic_division_by_zero(self):
        with self.assertRaisesRegex(MiniLangRuntimeError, "división por cero"):
            run("int cero = inputInt(); print(1 / cero);", input_provider=lambda prompt: "0")

    def test_instruction_limit(self):
        with self.assertRaisesRegex(MiniLangRuntimeError, "posible ciclo infinito"):
            run("while (true) { }", max_steps=30)

    def test_codegen_is_deterministic_and_has_entrypoint(self):
        tokens = Lexer().tokenize("int x = 1 + 2; print(x);")
        ast = Parser(tokens).parse()
        SemanticAnalyzer().analyze(ast)
        generator = CodeGenerator()
        first = generator.generate(ast)
        second = generator.generate(ast)
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("JUMP __main\n"))
        self.assertTrue(first.endswith("HALT"))

    def test_vm_matches_reference_interpreter(self):
        source = """
        int factorial(int n) {
            if (n <= 1) { return 1; }
            return n * factorial(n - 1);
        }
        int valores[3];
        valores[0] = factorial(3);
        valores[1] = factorial(4);
        valores[2] = valores[0] + valores[1];
        print(valores[2]);
        """
        result = run(source)
        reference = Interpreter().ejecutar(result.ast)
        self.assertEqual(result.output, reference)
        self.assertIn("FUNC factorial(n):", result.assembly)


class OriginalExamplesTests(unittest.TestCase):
    def test_all_original_examples_individually(self):
        test_file = Path(__file__).parents[1] / "test.txt"
        content = test_file.read_text(encoding="utf-8")
        starts = list(re.finditer(r"(?m)^// PRUEBA (\d+):", content))
        expected = {
            1: "20",
            2: "False",
            3: "1",
            4: "0\n1\n2\n3\n4",
            5: "90",
            6: "8",
            7: "120",
            8: "1\n2\n2\n4",
            9: "100",
            10: "",
            11: "13",
            12: "149",
            13: "16",
            14: "25",
            15: "1",
        }
        self.assertEqual(len(starts), 15)
        for index, match in enumerate(starts):
            number = int(match.group(1))
            end = starts[index + 1].start() if index + 1 < len(starts) else len(content)
            source = content[match.start():end]
            with self.subTest(prueba=number):
                self.assertEqual(run(source, max_steps=1_000_000).output, expected[number])


if __name__ == "__main__":
    unittest.main()
