from .ast_nodes import (
    ArrayAccess,
    ArrayAssign,
    Assign,
    BinOp,
    CallExpr,
    ExprStmt,
    FuncDecl,
    IfStmt,
    Literal,
    Print,
    ReturnStmt,
    UnaryOp,
    VarDecl,
    WhileStmt,
)
from .errors import OptimizationError


class Optimizer:
    def optimize(self, ast):
        return [self.visit(node) for node in ast]

    def visit(self, node):
        if isinstance(node, FuncDecl):
            node.body = [self.visit(statement) for statement in node.body]
        elif isinstance(node, VarDecl) and node.valor is not None:
            node.valor = self.visit(node.valor)
        elif isinstance(node, Assign):
            node.valor = self.visit(node.valor)
        elif isinstance(node, ArrayAssign):
            node.index = self.visit(node.index)
            node.valor = self.visit(node.valor)
        elif isinstance(node, IfStmt):
            node.cond = self.visit(node.cond)
            node.body = [self.visit(statement) for statement in node.body]
            node.else_body = [self.visit(statement) for statement in node.else_body]
        elif isinstance(node, WhileStmt):
            node.cond = self.visit(node.cond)
            node.body = [self.visit(statement) for statement in node.body]
        elif isinstance(node, ReturnStmt) and node.expr is not None:
            node.expr = self.visit(node.expr)
        elif isinstance(node, Print):
            node.expr = self.visit(node.expr)
        elif isinstance(node, ExprStmt):
            node.expr = self.visit(node.expr)
        elif isinstance(node, CallExpr):
            node.args = [self.visit(argument) for argument in node.args]
        elif isinstance(node, ArrayAccess):
            node.index = self.visit(node.index)
        elif isinstance(node, UnaryOp):
            node.expr = self.visit(node.expr)
            if isinstance(node.expr, Literal):
                value = -node.expr.val if node.op == "-" else not node.expr.val
                tipo = "int" if node.op == "-" else "bool"
                return Literal(value, tipo, node.token)
        elif isinstance(node, BinOp):
            node.izq = self.visit(node.izq)

            # Cortocircuito
            if node.op == "&&" and isinstance(node.izq, Literal) and node.izq.val is False:
                return Literal(False, "bool", node.token)
            if node.op == "||" and isinstance(node.izq, Literal) and node.izq.val is True:
                return Literal(True, "bool", node.token)

            node.der = self.visit(node.der)
            if isinstance(node.izq, Literal) and isinstance(node.der, Literal):
                return self._fold(node)
        return node

    @staticmethod
    def _fold(node):
        left = node.izq.val
        right = node.der.val
        if node.op == "+":
            result = left + right
        elif node.op == "-":
            result = left - right
        elif node.op == "*":
            result = left * right
        elif node.op == "/":
            if right == 0:
                raise OptimizationError("división por cero en una expresión constante", node.token)
            result = left // right
        elif node.op == "==":
            result = left == right
        elif node.op == "!=":
            result = left != right
        elif node.op == "<":
            result = left < right
        elif node.op == "<=":
            result = left <= right
        elif node.op == ">":
            result = left > right
        elif node.op == ">=":
            result = left >= right
        elif node.op == "&&":
            result = left and right
        elif node.op == "||":
            result = left or right
        else:
            return node
        tipo = "bool" if type(result) is bool else "int" if type(result) is int else "string"
        return Literal(result, tipo, node.token)
