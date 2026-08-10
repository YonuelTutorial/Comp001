from .ast_nodes import (
    ArrayAccess,
    ArrayAssign,
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
        return self._optimize_block(ast)

    def visit(self, node):
        if isinstance(node, FuncDecl):
            node.body = self._optimize_block(node.body)
        elif isinstance(node, VarDecl) and node.valor is not None:
            node.valor = self.visit(node.valor)
        elif isinstance(node, Assign):
            node.valor = self.visit(node.valor)
        elif isinstance(node, ArrayAssign):
            node.index = self.visit(node.index)
            node.valor = self.visit(node.valor)
        elif isinstance(node, IfStmt):
            node.cond = self.visit(node.cond)
            node.body = self._optimize_block(node.body)
            node.else_body = self._optimize_block(node.else_body)
            if isinstance(node.cond, Literal):
                selected = node.body if node.cond.val else node.else_body
                return BlockStmt(selected, node.token)
        elif isinstance(node, WhileStmt):
            node.cond = self.visit(node.cond)
            node.body = self._optimize_block(node.body)
            if isinstance(node.cond, Literal) and node.cond.val is False:
                return BlockStmt([], node.token)
        elif isinstance(node, ForStmt):
            if node.init is not None:
                node.init = self.visit(node.init)
            node.cond = self.visit(node.cond)
            if node.update is not None:
                node.update = self.visit(node.update)
            node.body = self._optimize_block(node.body)
        elif isinstance(node, BlockStmt):
            node.body = self._optimize_block(node.body)
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
            simplified = self._simplify(node)
            if simplified is not None:
                return simplified
        return node

    def _optimize_block(self, statements):
        optimized = []
        constants = {}
        for statement in statements:
            self._substitute_statement(statement, constants)
            result = self.visit(statement)
            optimized.append(result)
            if isinstance(result, VarDecl):
                if isinstance(result.valor, Literal):
                    constants[result.nombre] = result.valor
                else:
                    constants.pop(result.nombre, None)
            elif isinstance(result, Assign):
                if isinstance(result.valor, Literal):
                    constants[result.nombre] = result.valor
                else:
                    constants.pop(result.nombre, None)
            if isinstance(result, (IfStmt, WhileStmt, ForStmt, BlockStmt)) or self._contains_call(result):
                constants.clear()
            if isinstance(result, (ReturnStmt, BreakStmt, ContinueStmt)):
                break
        return optimized

    def _substitute_statement(self, statement, constants):
        if isinstance(statement, VarDecl) and statement.valor is not None:
            statement.valor = self._substitute(statement.valor, constants)
        elif isinstance(statement, Assign):
            statement.valor = self._substitute(statement.valor, constants)
        elif isinstance(statement, ArrayAssign):
            statement.index = self._substitute(statement.index, constants)
            statement.valor = self._substitute(statement.valor, constants)
        elif isinstance(statement, Print):
            statement.expr = self._substitute(statement.expr, constants)
        elif isinstance(statement, ReturnStmt) and statement.expr is not None:
            statement.expr = self._substitute(statement.expr, constants)
        elif isinstance(statement, ExprStmt):
            statement.expr = self._substitute(statement.expr, constants)

    def _substitute(self, node, constants):
        from .ast_nodes import VarAccess

        if isinstance(node, VarAccess) and node.nombre in constants:
            literal = constants[node.nombre]
            return Literal(literal.val, literal.tipo, node.token)
        if isinstance(node, BinOp):
            node.izq = self._substitute(node.izq, constants)
            node.der = self._substitute(node.der, constants)
        elif isinstance(node, UnaryOp):
            node.expr = self._substitute(node.expr, constants)
        elif isinstance(node, CallExpr):
            node.args = [self._substitute(argument, constants) for argument in node.args]
        elif isinstance(node, ArrayAccess):
            node.index = self._substitute(node.index, constants)
        return node

    def _contains_call(self, node):
        if isinstance(node, CallExpr):
            return True
        if isinstance(node, list):
            return any(self._contains_call(item) for item in node)
        if hasattr(node, "__dataclass_fields__"):
            for name in node.__dataclass_fields__:
                if name != "token" and self._contains_call(getattr(node, name)):
                    return True
        return False

    @staticmethod
    def _simplify(node):
        if isinstance(node.der, Literal):
            if node.der.val == 0 and node.op in ("+", "-"):
                return node.izq
            if node.der.val == 1 and node.op in ("*", "/", "^"):
                return node.izq
        if isinstance(node.izq, Literal):
            if node.izq.val == 0 and node.op == "+":
                return node.der
            if node.izq.val == 1 and node.op == "*":
                return node.der
        return None

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
            result = left / right if "float" in (node.izq.tipo, node.der.tipo) else left // right
        elif node.op == "%":
            if right == 0:
                raise OptimizationError("módulo por cero en una expresión constante", node.token)
            result = left % right
        elif node.op == "^":
            if type(left) is int and type(right) is int and right < 0:
                raise OptimizationError("un exponente entero no puede ser negativo", node.token)
            result = left ** right
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
        if type(result) is bool:
            tipo = "bool"
        elif type(result) is int:
            tipo = "int"
        elif type(result) is float:
            tipo = "float"
        else:
            tipo = "string"
        return Literal(result, tipo, node.token)
