from dataclasses import dataclass

from .codegen import CodeGenerator
from .interpreter import Interpreter
from .lexer import Lexer
from .optimizer import Optimizer
from .parser import Parser
from .semantic import SemanticAnalyzer
from .vm import VirtualMachine


@dataclass
class CompilationResult:
    tokens: list
    ast: list
    output: str
    assembly: str
    bytecode: object


class Compiler:
    def __init__(self, max_steps=100_000, max_call_depth=500):
        self.max_steps = max_steps
        self.max_call_depth = max_call_depth

    def compile_and_run(self, source):
        tokens = Lexer().tokenize(source)
        ast = Parser(tokens).parse()
        SemanticAnalyzer().analyze(ast)
        optimized = Optimizer().optimize(ast)
        generator = CodeGenerator()
        bytecode = generator.build(optimized)
        assembly = bytecode.render()
        output = VirtualMachine(self.max_steps, self.max_call_depth).execute(bytecode)
        return CompilationResult(tokens, optimized, output, assembly, bytecode)
