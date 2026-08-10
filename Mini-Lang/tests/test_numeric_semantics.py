import copy
import unittest

from minilang import Compiler, Interpreter, Lexer, Optimizer, Parser, SemanticAnalyzer


class NumericSemanticsTests(unittest.TestCase):
    def assert_engines(self, source, expected):
        ast = Parser(Lexer().tokenize(source)).parse()
        SemanticAnalyzer().analyze(ast)

        unoptimized_output = Interpreter().ejecutar(copy.deepcopy(ast))
        optimized_ast = Optimizer().optimize(copy.deepcopy(ast))
        optimized_output = Interpreter().ejecutar(optimized_ast)
        vm_output = Compiler().compile_and_run(source).output

        self.assertEqual(unoptimized_output, expected)
        self.assertEqual(optimized_output, expected)
        self.assertEqual(vm_output, expected)

    def test_float_negation_keeps_float_type(self):
        self.assert_engines("print(-1.5 / 2);", "-0.75")

    def test_float_variable_initializer_promotes_int(self):
        self.assert_engines("float x = 5; print(x); print(x / 2);", "5.0\n2.5")

    def test_float_assignment_promotes_int(self):
        self.assert_engines("float x; x = 5; print(x / 2);", "2.5")

    def test_float_parameter_promotes_int_argument(self):
        source = "float mitad(float x) { return x / 2; } print(mitad(5));"
        self.assert_engines(source, "2.5")

    def test_float_return_promotes_int_expression(self):
        source = "float valor() { return 5; } print(valor() / 2);"
        self.assert_engines(source, "2.5")

    def test_float_array_assignment_promotes_int(self):
        source = "float datos[1]; datos[0] = 5; print(datos[0]); print(datos[0] / 2);"
        self.assert_engines(source, "5.0\n2.5")

    def test_negative_integer_division_and_modulo_are_preserved(self):
        self.assert_engines("print(-3 / 2); print(-3 % 2);", "-2\n1")

    def test_unoptimized_bytecode_contains_float_conversion(self):
        result = Compiler().compile("float x = 5; print(x / 2);")
        self.assertIn("TO_FLOAT", result.unoptimized_assembly)

    def test_dynamic_int_to_float_conversion_runs_in_vm(self):
        source = "float x = inputInt(); print(x); print(x / 2);"
        ast = Parser(Lexer().tokenize(source)).parse()
        SemanticAnalyzer().analyze(ast)

        unoptimized_output = Interpreter(input_provider=lambda prompt: "5").ejecutar(copy.deepcopy(ast))
        optimized_ast = Optimizer().optimize(copy.deepcopy(ast))
        optimized_output = Interpreter(input_provider=lambda prompt: "5").ejecutar(optimized_ast)
        result = Compiler(input_provider=lambda prompt: "5").compile_and_run(source)

        self.assertEqual(unoptimized_output, "5.0\n2.5")
        self.assertEqual(optimized_output, "5.0\n2.5")
        self.assertEqual(result.output, "5.0\n2.5")
        self.assertIn("TO_FLOAT", result.assembly)


if __name__ == "__main__":
    unittest.main()
