from dataclasses import dataclass, field

from .errors import MiniLangRuntimeError
from .interpreter import UNINITIALIZED


@dataclass
class Frame:
    scopes: list[dict] = field(default_factory=lambda: [{}])

    def declare(self, name, value, token=None):
        if name in self.scopes[-1]:
            raise MiniLangRuntimeError(f"'{name}' ya existe en este ámbito", token)
        self.scopes[-1][name] = value

    def find_scope(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope
        return None


class VirtualMachine:
    def __init__(self, max_steps=100_000, max_call_depth=500):
        self.max_steps = max_steps
        self.max_call_depth = max_call_depth

    def execute(self, program):
        self.instructions = program.instructions
        self.labels = {}
        self.functions = {}
        for index, instruction in enumerate(self.instructions):
            if instruction.op == "LABEL":
                self.labels[instruction.args[0]] = index + 1
            elif instruction.op == "FUNC":
                name, params = instruction.args
                self.functions[name] = (index + 1, params)

        self.stack = []
        self.output = []
        self.global_frame = Frame()
        self.frame = self.global_frame
        self.call_stack = []
        self.ip = 0
        self.steps = 0

        while self.ip < len(self.instructions):
            instruction = self.instructions[self.ip]
            self.ip += 1
            self.steps += 1
            if self.steps > self.max_steps:
                raise MiniLangRuntimeError(
                    f"se superó el límite de {self.max_steps} instrucciones; posible ciclo infinito",
                    instruction.token,
                )
            if self._execute_instruction(instruction):
                break
        return "\n".join(self.output)

    def _execute_instruction(self, instruction):
        op = instruction.op
        args = instruction.args
        token = instruction.token

        if op in ("LABEL", "FUNC", "END_FUNC"):
            return False
        if op == "HALT":
            return True
        if op == "JUMP":
            self.ip = self._label(args[0], token)
        elif op in ("JUMP_IF_FALSE", "JUMP_IF_TRUE"):
            value = self._pop(token)
            should_jump = (not value) if op == "JUMP_IF_FALSE" else bool(value)
            if should_jump:
                self.ip = self._label(args[0], token)
        elif op == "PUSH_CONST":
            self.stack.append(args[0])
        elif op == "PUSH_UNINITIALIZED":
            self.stack.append(UNINITIALIZED)
        elif op == "DUP":
            self.stack.append(self._peek(token))
        elif op == "POP":
            self._pop(token)
        elif op == "DECLARE":
            self.frame.declare(args[0], self._pop(token), token)
        elif op == "LOAD":
            self.stack.append(self._load(args[0], token))
        elif op == "STORE":
            self._store(args[0], self._pop(token), token)
        elif op == "ALLOC_ARRAY":
            name, size, tipo = args
            default = {"int": 0, "bool": False, "string": ""}[tipo]
            self.frame.declare(name, [default for _ in range(size)], token)
        elif op == "LOAD_ARRAY":
            array = self._load(args[0], token)
            index = self._pop(token)
            self._check_bounds(args[0], array, index, token)
            self.stack.append(array[index])
        elif op == "STORE_ARRAY":
            value = self._pop(token)
            index = self._pop(token)
            array = self._load(args[0], token)
            self._check_bounds(args[0], array, index, token)
            array[index] = value
        elif op == "ENTER_SCOPE":
            self.frame.scopes.append({})
        elif op == "EXIT_SCOPE":
            if len(self.frame.scopes) <= 1:
                raise MiniLangRuntimeError("desbalance interno de ámbitos", token)
            self.frame.scopes.pop()
        elif op == "PRINT":
            self.output.append(str(self._pop(token)))
        elif op in ("NEG", "NOT"):
            value = self._pop(token)
            self.stack.append(-value if op == "NEG" else not value)
        elif op in ("ADD", "SUB", "MUL", "DIV", "EQ", "NE", "LT", "LE", "GT", "GE"):
            right = self._pop(token)
            left = self._pop(token)
            self.stack.append(self._binary(op, left, right, token))
        elif op == "CALL":
            self._call(args[0], args[1], token)
        elif op in ("RETURN", "RETURN_VOID"):
            value = self._pop(token) if op == "RETURN" else None
            self._return(value, token)
        else:
            raise MiniLangRuntimeError(f"instrucción desconocida '{op}'", token)
        return False

    def _call(self, name, argument_count, token):
        if name not in self.functions:
            raise MiniLangRuntimeError(f"función '{name}' no declarada", token)
        if len(self.call_stack) >= self.max_call_depth:
            raise MiniLangRuntimeError(
                f"se superó la profundidad máxima de {self.max_call_depth} llamadas", token
            )
        entry, params = self.functions[name]
        if argument_count != len(params):
            raise MiniLangRuntimeError(f"cantidad de argumentos inválida para '{name}'", token)
        values = [self._pop(token) for _ in range(argument_count)][::-1]
        self.call_stack.append((self.ip, self.frame))
        self.frame = Frame()
        for parameter, value in zip(params, values):
            self.frame.declare(parameter, value, token)
        self.ip = entry

    def _return(self, value, token):
        if not self.call_stack:
            raise MiniLangRuntimeError("return fuera de una llamada", token)
        self.ip, self.frame = self.call_stack.pop()
        self.stack.append(value)

    def _load(self, name, token):
        scope = self.frame.find_scope(name)
        if scope is None and self.frame is not self.global_frame:
            scope = self.global_frame.find_scope(name)
        if scope is None:
            raise MiniLangRuntimeError(f"'{name}' no está declarado", token)
        value = scope[name]
        if value is UNINITIALIZED:
            raise MiniLangRuntimeError(f"'{name}' se usó antes de inicializarse", token)
        return value

    def _store(self, name, value, token):
        scope = self.frame.find_scope(name)
        if scope is None and self.frame is not self.global_frame:
            scope = self.global_frame.find_scope(name)
        if scope is None:
            raise MiniLangRuntimeError(f"'{name}' no está declarado", token)
        scope[name] = value

    def _label(self, name, token):
        if name not in self.labels:
            raise MiniLangRuntimeError(f"etiqueta '{name}' no declarada", token)
        return self.labels[name]

    def _pop(self, token):
        if not self.stack:
            raise MiniLangRuntimeError("desbordamiento inferior de la pila", token)
        return self.stack.pop()

    def _peek(self, token):
        if not self.stack:
            raise MiniLangRuntimeError("desbordamiento inferior de la pila", token)
        return self.stack[-1]

    @staticmethod
    def _binary(op, left, right, token):
        if op == "ADD":
            return left + right
        if op == "SUB":
            return left - right
        if op == "MUL":
            return left * right
        if op == "DIV":
            if right == 0:
                raise MiniLangRuntimeError("división por cero", token)
            return left // right
        if op == "EQ":
            return left == right
        if op == "NE":
            return left != right
        if op == "LT":
            return left < right
        if op == "LE":
            return left <= right
        if op == "GT":
            return left > right
        if op == "GE":
            return left >= right

    @staticmethod
    def _check_bounds(name, array, index, token):
        if type(index) is not int or not 0 <= index < len(array):
            raise MiniLangRuntimeError(
                f"índice {index!r} fuera de rango para '{name}' (tamaño {len(array)})", token
            )
