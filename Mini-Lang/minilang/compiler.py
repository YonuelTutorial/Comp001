from dataclasses import dataclass, fields, is_dataclass
from hashlib import sha1
from pathlib import Path

from .codegen import CodeGenerator
from .interpreter import Interpreter
from .js_codegen import JavaScriptGenerator
from .lexer import Lexer
from .optimizer import Optimizer
from .parser import Parser
from .semantic import SemanticAnalyzer
from .vm import VirtualMachine
from .ast_nodes import ImportStmt
from .errors import SemanticError


@dataclass
class CompilationResult:
    tokens: list
    ast: list
    output: str
    assembly: str
    bytecode: object
    symbols: dict
    unoptimized_assembly: str
    javascript: str = ""


class Compiler:
    def __init__(self, max_steps=100_000, max_call_depth=500, input_provider=None):
        self.max_steps = max_steps
        self.max_call_depth = max_call_depth
        self.input_provider = input_provider

    def compile_and_run(self, source, source_path=None):
        result = self.compile(source, source_path)
        result.output = VirtualMachine(
            self.max_steps, self.max_call_depth, self.input_provider
        ).execute(result.bytecode)
        return result

    def compile(self, source, source_path=None):
        tokens = Lexer().tokenize(source)
        ast = Parser(tokens).parse()
        base_dir = Path(source_path).resolve().parent if source_path else Path.cwd()
        ast = self._resolve_imports(ast, base_dir, set(), [])
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        unoptimized_assembly = CodeGenerator().generate(ast)
        optimized = Optimizer().optimize(ast)
        generator = CodeGenerator()
        bytecode = generator.build(optimized)
        assembly = bytecode.render()
        javascript = JavaScriptGenerator(self.max_steps, self.max_call_depth).generate(optimized)
        return CompilationResult(
            tokens=tokens,
            ast=optimized,
            output="",
            assembly=assembly,
            bytecode=bytecode,
            symbols=analyzer.symbol_table(),
            unoptimized_assembly=unoptimized_assembly,
            javascript=javascript,
        )

    def _resolve_imports(self, ast, base_dir, loaded, stack):
        resolved = []
        for node in ast:
            if not isinstance(node, ImportStmt):
                resolved.append(node)
                continue
            module_path = (base_dir / node.path).resolve()
            if module_path in stack:
                chain = " -> ".join(path.name for path in [*stack, module_path])
                raise SemanticError(f"importación circular: {chain}", node.token)
            if module_path in loaded:
                continue
            if not module_path.is_file():
                raise SemanticError(f"no se encontró el módulo '{node.path}'", node.token)
            try:
                module_source = module_path.read_text(encoding="utf-8")
            except OSError as error:
                raise SemanticError(f"no se pudo leer '{node.path}': {error}", node.token) from error
            module_tokens = Lexer().tokenize(module_source)
            module_ast = Parser(module_tokens).parse()
            self._mangle_private(module_ast, module_path)
            loaded.add(module_path)
            resolved.extend(
                self._resolve_imports(module_ast, module_path.parent, loaded, [*stack, module_path])
            )
        return resolved

    def _mangle_private(self, ast, module_path):
        private_names = {
            node.nombre for node in ast
            if hasattr(node, "nombre") and node.nombre.startswith("_")
        }
        if not private_names:
            return
        prefix = sha1(str(module_path).encode("utf-8")).hexdigest()[:10]
        mapping = {name: f"__{prefix}{name}" for name in private_names}

        def rename(value):
            if isinstance(value, list):
                for item in value:
                    rename(item)
                return
            if not is_dataclass(value):
                return
            for item in fields(value):
                current = getattr(value, item.name)
                if item.name == "nombre" and current in mapping:
                    setattr(value, item.name, mapping[current])
                else:
                    rename(current)

        rename(ast)
