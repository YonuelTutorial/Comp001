import json
from dataclasses import dataclass, field

from .ast_nodes import (
    ArrayAccess,
    ArrayAssign,
    ArrayDecl,
    Assign,
    BinOp,
    BlockStmt,
    BreakStmt,
    CallExpr,
    ContinueStmt,
    ExprStmt,
    ForStmt,
    FuncDecl,
    IfStmt,
    ImportStmt,
    Literal,
    Print,
    ReturnStmt,
    UnaryOp,
    VarAccess,
    VarDecl,
    WhileStmt,
)
from .errors import CodeGenerationError


@dataclass(frozen=True)
class Instruction:
    op: str
    args: tuple = ()
    token: object = None

    def render(self):
        if self.op == "LABEL":
            return f"{self.args[0]}:"
        if self.op == "FUNC":
            name, params = self.args
            return f"FUNC {name}({', '.join(params)}):"
        if self.op == "PUSH_CONST":
            return f"PUSH_CONST {json.dumps(self.args[0], ensure_ascii=False)}"
        if not self.args:
            return self.op
        return f"{self.op} " + ", ".join(str(argument) for argument in self.args)


@dataclass
class BytecodeProgram:
    instructions: list[Instruction] = field(default_factory=list)

    def render(self):
        return "\n".join(instruction.render() for instruction in self.instructions)


class CodeGenerator:
    def __init__(self):
        self.inst = []
        self.temp_c = 0
        self.label_c = 0
        self.loop_stack = []
        self.scope_depth = 0

    def get_label(self, prefix="L"):
        self.label_c += 1
        return f"{prefix}{self.label_c}"

    def get_temp(self):
        self.temp_c += 1
        return f"t{self.temp_c}"

    def generate(self, ast):
        return self.build(ast).render()

    def build(self, ast):
        self.inst = []
        self.temp_c = 0
        self.label_c = 0
        self.loop_stack = []
        self.scope_depth = 0

        functions = [node for node in ast if isinstance(node, FuncDecl)]
        main = [node for node in ast if not isinstance(node, FuncDecl)]
        self.emit("JUMP", "__main")
        for function in functions:
            self.visit(function)
        self.emit("LABEL", "__main")
        for node in main:
            self.visit(node)
        self.emit("HALT")
        return BytecodeProgram(self.inst.copy())

    def emit(self, op, *args, token=None):
        self.inst.append(Instruction(op, tuple(args), token))

    def visit(self, node):
        method = getattr(self, f"visit_{type(node).__name__}", None)
        if method is None:
            raise CodeGenerationError(
                f"nodo no soportado: {type(node).__name__}", getattr(node, "token", None)
            )
        return method(node)

    def visit_FuncDecl(self, node):
        self.emit("FUNC", node.nombre, tuple(parameter.nombre for parameter in node.params), token=node.token)
        for statement in node.body:
            self.visit(statement)
        if node.tipo == "void":
            self.emit("RETURN_VOID", token=node.token)
        self.emit("END_FUNC", node.nombre)

    def visit_VarDecl(self, node):
        if node.valor is None:
            self.emit("PUSH_UNINITIALIZED", token=node.token)
        else:
            self.visit(node.valor)
        self.emit("DECLARE", node.nombre, token=node.token)

    def visit_ArrayDecl(self, node):
        self.emit("ALLOC_ARRAY", node.nombre, node.size, node.tipo, token=node.token)

    def visit_Assign(self, node):
        self.visit(node.valor)
        self.emit("STORE", node.nombre, token=node.token)

    def visit_ArrayAssign(self, node):
        self.visit(node.index)
        self.visit(node.valor)
        self.emit("STORE_ARRAY", node.nombre, token=node.token)

    def visit_IfStmt(self, node):
        else_label = self.get_label("else")
        end_label = self.get_label("endif")
        self.visit(node.cond)
        self.emit("JUMP_IF_FALSE", else_label, token=node.token)
        self._block(node.body)
        self.emit("JUMP", end_label)
        self.emit("LABEL", else_label)
        self._block(node.else_body)
        self.emit("LABEL", end_label)

    def visit_WhileStmt(self, node):
        start_label = self.get_label("while")
        end_label = self.get_label("endwhile")
        loop_scope_base = self.scope_depth
        self.loop_stack.append((start_label, end_label, loop_scope_base))
        self.emit("LABEL", start_label)
        self.visit(node.cond)
        self.emit("JUMP_IF_FALSE", end_label, token=node.token)
        self._block(node.body)
        self.emit("JUMP", start_label)
        self.emit("LABEL", end_label)
        self.loop_stack.pop()

    def visit_ForStmt(self, node):
        start_label = self.get_label("for")
        update_label = self.get_label("for_update")
        end_label = self.get_label("endfor")
        self.emit("ENTER_SCOPE")
        self.scope_depth += 1
        if node.init is not None:
            self.visit(node.init)
        self.loop_stack.append((update_label, end_label, self.scope_depth))
        self.emit("LABEL", start_label)
        self.visit(node.cond)
        self.emit("JUMP_IF_FALSE", end_label, token=node.token)
        self._block(node.body)
        self.emit("LABEL", update_label)
        if node.update is not None:
            self.visit(node.update)
        self.emit("JUMP", start_label)
        self.emit("LABEL", end_label)
        self.loop_stack.pop()
        self.scope_depth -= 1
        self.emit("EXIT_SCOPE")

    def visit_ImportStmt(self, node):
        return

    def visit_ReturnStmt(self, node):
        if node.expr is None:
            self.emit("RETURN_VOID", token=node.token)
        else:
            self.visit(node.expr)
            self.emit("RETURN", token=node.token)

    def visit_BreakStmt(self, node):
        if not self.loop_stack:
            raise CodeGenerationError("break fuera de un ciclo", node.token)
        _, end_label, base_depth = self.loop_stack[-1]
        self._emit_unwind(base_depth)
        self.emit("JUMP", end_label, token=node.token)

    def visit_ContinueStmt(self, node):
        if not self.loop_stack:
            raise CodeGenerationError("continue fuera de un ciclo", node.token)
        start_label, _, base_depth = self.loop_stack[-1]
        self._emit_unwind(base_depth)
        self.emit("JUMP", start_label, token=node.token)

    def visit_Print(self, node):
        self.visit(node.expr)
        self.emit("PRINT", token=node.token)

    def visit_ExprStmt(self, node):
        self.visit(node.expr)
        self.emit("POP", token=node.token)

    def visit_BlockStmt(self, node):
        self._block(node.body)

    def visit_CallExpr(self, node):
        for argument in node.args:
            self.visit(argument)
        self.emit("CALL", node.nombre, len(node.args), token=node.token)

    def visit_BinOp(self, node):
        self.visit(node.izq)
        if node.op in ("&&", "||"):
            end_label = self.get_label("logic_end")
            self.emit("DUP", token=node.token)
            jump = "JUMP_IF_FALSE" if node.op == "&&" else "JUMP_IF_TRUE"
            self.emit(jump, end_label, token=node.token)
            self.emit("POP")
            self.visit(node.der)
            self.emit("LABEL", end_label)
            return
        self.visit(node.der)
        operation = {
            "+": "ADD",
            "-": "SUB",
            "*": "MUL",
            "/": "DIV",
            "%": "MOD",
            "^": "POW",
            "==": "EQ",
            "!=": "NE",
            "<": "LT",
            "<=": "LE",
            ">": "GT",
            ">=": "GE",
        }[node.op]
        self.emit(operation, token=node.token)

    def visit_UnaryOp(self, node):
        self.visit(node.expr)
        self.emit("NEG" if node.op == "-" else "NOT", token=node.token)

    def visit_Literal(self, node):
        self.emit("PUSH_CONST", node.val, token=node.token)

    def visit_VarAccess(self, node):
        self.emit("LOAD", node.nombre, token=node.token)

    def visit_ArrayAccess(self, node):
        self.visit(node.index)
        self.emit("LOAD_ARRAY", node.nombre, token=node.token)

    def _block(self, statements):
        self.emit("ENTER_SCOPE")
        self.scope_depth += 1
        for statement in statements:
            self.visit(statement)
        self.scope_depth -= 1
        self.emit("EXIT_SCOPE")

    def _emit_unwind(self, target_depth):
        for _ in range(self.scope_depth - target_depth):
            self.emit("EXIT_SCOPE")
