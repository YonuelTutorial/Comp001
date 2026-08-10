import unittest
from pathlib import Path

from minilang import Compiler, Interpreter


class AdvancedExamplesTests(unittest.TestCase):
    def test_advanced_file(self):
        source = (Path(__file__).parents[1] / "test_advanced.txt").read_text(encoding="utf-8")
        result = Compiler(max_steps=1_000_000).compile_and_run(source)
        expected = "\n".join(
            [
                "1", "2", "3", "4", "7", "9",
                "720",
                "55",
                "True", "False",
                "True", "True", "False",
                "True", "False",
                "30",
                "1024",
                "6",
                "12", "2", "35", "3",
                "True", "False", "cadena con espacios", "linea", "nueva",
                "True", "False",
                "55",
                "3",
                "5",
                "3", "27",
                "100", "20",
                "True", "False", "True",
                "10",
                "8",
            ]
        )
        self.assertEqual(result.output, expected)
        self.assertEqual(Interpreter(max_steps=1_000_000).ejecutar(result.ast), expected)


if __name__ == "__main__":
    unittest.main()
