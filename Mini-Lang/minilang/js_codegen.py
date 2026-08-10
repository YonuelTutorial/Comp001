import json

from .ast_nodes import (
    ArrayAccess,
    ArrayAssign,
    ArrayDecl,
    Assign,
    BinOp,
    BlockStmt,
    BreakStmt,
    CallExpr,
    CastExpr,
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
from .builtins import BUILTINS
from .errors import CodeGenerationError


class JavaScriptGenerator:
    def __init__(self, max_steps=100_000, max_call_depth=500):
        self.max_steps = max_steps
        self.max_call_depth = max_call_depth

    def generate(self, ast):
        self.lines = self._runtime().splitlines()
        self.indent = 0
        self.functions = {
            node.nombre: (node.tipo, tuple(param.tipo for param in node.params))
            for node in ast
            if isinstance(node, FuncDecl)
        }
        self.global_types = {}
        for node in ast:
            if isinstance(node, VarDecl):
                self.global_types[node.nombre] = node.tipo
            elif isinstance(node, ArrayDecl):
                self.global_types[node.nombre] = f"{node.tipo}[]"

        self._line("")
        self._line("__ml_run(() => {")
        self.indent += 1
        for name in self.global_types:
            self._line(f"let {self._var_name(name)} = __ml_not_declared;")
        if self.global_types:
            self._line("")
        self.in_function = True
        for node in ast:
            if isinstance(node, FuncDecl):
                self._emit_function(node)
        self.in_function = False
        self.scopes = [self.global_types.copy()]
        for node in ast:
            if not isinstance(node, FuncDecl):
                self._emit_statement(node)
        self.indent -= 1
        self._line("});")
        return "\n".join(self.lines)

    def _emit_function(self, node):
        params = ", ".join(self._var_name(param.nombre) for param in node.params)
        self._line(f"function {self._func_name(node.nombre)}({params}) {{")
        self.indent += 1
        self.scopes = [
            self.global_types.copy(),
            {param.nombre: param.tipo for param in node.params},
        ]
        self._line(self._tick(node))
        for statement in node.body:
            self._emit_statement(statement)
        self.indent -= 1
        self._line("}")
        self._line("")

    def _emit_statement(self, node, include_tick=True):
        if include_tick and not isinstance(node, ImportStmt):
            self._line(self._tick(node))

        if isinstance(node, VarDecl):
            self.scopes[-1][node.nombre] = node.tipo
            value = "__ml_uninitialized" if node.valor is None else self._expr(node.valor)
            declaration = "" if self._is_global_scope() else "let "
            self._line(f"{declaration}{self._var_name(node.nombre)} = {value};")
        elif isinstance(node, ArrayDecl):
            self.scopes[-1][node.nombre] = f"{node.tipo}[]"
            default = {"int": "0n", "float": "0.0", "bool": "false", "string": '""'}[node.tipo]
            declaration = "" if self._is_global_scope() else "let "
            self._line(
                f"{declaration}{self._var_name(node.nombre)} = Array({node.size}).fill({default});"
            )
        elif isinstance(node, Assign):
            self._line(f"{self._var_name(node.nombre)} = {self._expr(node.valor)};")
        elif isinstance(node, ArrayAssign):
            line, column = self._position(node)
            self._line(
                "__ml_array_set("
                f"{self._json(node.nombre)}, {self._var_name(node.nombre)}, "
                f"{self._expr(node.index)}, {self._expr(node.valor)}, {line}, {column});"
            )
        elif isinstance(node, IfStmt):
            self._line(f"if ({self._expr(node.cond)}) {{")
            self._emit_block_contents(node.body)
            if node.else_body:
                self._line("} else {")
                self._emit_block_contents(node.else_body)
            self._line("}")
        elif isinstance(node, WhileStmt):
            self._line(f"while ({self._expr(node.cond)}) {{")
            self.indent += 1
            self.scopes.append({})
            self._line(self._tick(node))
            for statement in node.body:
                self._emit_statement(statement)
            self.scopes.pop()
            self.indent -= 1
            self._line("}")
        elif isinstance(node, ForStmt):
            self.scopes.append({})
            init = "" if node.init is None else self._inline_statement(node.init)
            condition = self._expr(node.cond)
            update = "" if node.update is None else self._inline_statement(node.update)
            self._line(f"for ({init}; {condition}; {update}) {{")
            self.indent += 1
            self.scopes.append({})
            self._line(self._tick(node))
            for statement in node.body:
                self._emit_statement(statement)
            self.scopes.pop()
            self.indent -= 1
            self._line("}")
            self.scopes.pop()
        elif isinstance(node, ReturnStmt):
            value = "" if node.expr is None else f" {self._expr(node.expr)}"
            self._line(f"return{value};")
        elif isinstance(node, BreakStmt):
            self._line("break;")
        elif isinstance(node, ContinueStmt):
            self._line("continue;")
        elif isinstance(node, Print):
            self._line(
                f"__ml_print({self._expr(node.expr)}, {self._json(self._expr_type(node.expr))});"
            )
        elif isinstance(node, ExprStmt):
            self._line(f"{self._expr(node.expr)};")
        elif isinstance(node, BlockStmt):
            self._line("{")
            self._emit_block_contents(node.body)
            self._line("}")
        elif isinstance(node, ImportStmt):
            return
        else:
            raise CodeGenerationError(
                f"nodo no soportado por JavaScript: {type(node).__name__}",
                getattr(node, "token", None),
            )

    def _emit_block_contents(self, statements):
        self.indent += 1
        self.scopes.append({})
        for statement in statements:
            self._emit_statement(statement)
        self.scopes.pop()
        self.indent -= 1

    def _inline_statement(self, node):
        if isinstance(node, VarDecl):
            self.scopes[-1][node.nombre] = node.tipo
            value = "__ml_uninitialized" if node.valor is None else self._expr(node.valor)
            return f"let {self._var_name(node.nombre)} = {value}"
        if isinstance(node, Assign):
            return f"{self._var_name(node.nombre)} = {self._expr(node.valor)}"
        if isinstance(node, ArrayAssign):
            line, column = self._position(node)
            return (
                "__ml_array_set("
                f"{self._json(node.nombre)}, {self._var_name(node.nombre)}, "
                f"{self._expr(node.index)}, {self._expr(node.valor)}, {line}, {column})"
            )
        if isinstance(node, ExprStmt):
            return self._expr(node.expr)
        raise CodeGenerationError(
            f"sentencia no soportada en for: {type(node).__name__}",
            getattr(node, "token", None),
        )

    def _expr(self, node):
        if isinstance(node, Literal):
            if node.tipo == "int":
                return f"{node.val}n"
            return self._json(node.val)
        if isinstance(node, VarAccess):
            line, column = self._position(node)
            return (
                f"__ml_load({self._json(node.nombre)}, {self._var_name(node.nombre)}, "
                f"{line}, {column})"
            )
        if isinstance(node, ArrayAccess):
            line, column = self._position(node)
            return (
                f"__ml_array_get({self._json(node.nombre)}, {self._var_name(node.nombre)}, "
                f"{self._expr(node.index)}, {line}, {column})"
            )
        if isinstance(node, CastExpr):
            if node.tipo == "float":
                return f"Number({self._expr(node.expr)})"
            raise CodeGenerationError(
                f"conversión interna desconocida a '{node.tipo}'", node.token
            )
        if isinstance(node, UnaryOp):
            return f"({node.op}{self._expr(node.expr)})"
        if isinstance(node, BinOp):
            left = self._expr(node.izq)
            right = self._expr(node.der)
            left_type = self._expr_type(node.izq)
            right_type = self._expr_type(node.der)
            if left_type in ("int", "float") and right_type in ("int", "float"):
                if left_type != right_type:
                    if left_type == "int":
                        left = f"Number({left})"
                    if right_type == "int":
                        right = f"Number({right})"
            line, column = self._position(node)
            if node.op == "/":
                integer = left_type == right_type == "int"
                return f"__ml_div({left}, {right}, {str(integer).lower()}, {line}, {column})"
            if node.op == "%":
                return f"__ml_mod({left}, {right}, {line}, {column})"
            if node.op == "^":
                integer = left_type == right_type == "int"
                return f"__ml_pow({left}, {right}, {str(integer).lower()}, {line}, {column})"
            operator = {"==": "===", "!=": "!=="}.get(node.op, node.op)
            return f"({left} {operator} {right})"
        if isinstance(node, CallExpr):
            return self._call(node)
        raise CodeGenerationError(
            f"expresión no soportada por JavaScript: {type(node).__name__}",
            getattr(node, "token", None),
        )

    def _call(self, node):
        args = [self._expr(argument) for argument in node.args]
        line, column = self._position(node)
        if node.nombre == "inputInt":
            return f"__ml_input_int({line}, {column})"
        if node.nombre == "inputFloat":
            return f"__ml_input_float({line}, {column})"
        if node.nombre == "inputString":
            return f"__ml_input_string({line}, {column})"
        if node.nombre == "inputBool":
            return f"__ml_input_bool({line}, {column})"
        if node.nombre == "length":
            return f"__ml_length({args[0]})"
        if node.nombre == "substring":
            return f"__ml_substring({', '.join(args)}, {line}, {column})"
        if node.nombre == "toString":
            value_type = self._expr_type(node.args[0])
            return f"__ml_to_string({args[0]}, {self._json(value_type)})"
        if node.nombre == "toInt":
            return f"__ml_to_int({args[0]}, {line}, {column})"
        if node.nombre == "toFloat":
            return f"__ml_to_float({args[0]}, {line}, {column})"
        if node.nombre == "contains":
            return f"__ml_contains({', '.join(args)})"
        if node.nombre == "regexMatch":
            return f"__ml_regex_match({', '.join(args)}, {line}, {column})"
        call = f"{self._func_name(node.nombre)}({', '.join(args)})"
        return f"__ml_call(() => {call}, {line}, {column})"

    def _expr_type(self, node):
        if isinstance(node, Literal):
            return node.tipo
        if isinstance(node, CastExpr):
            return node.tipo
        if isinstance(node, VarAccess):
            return self._lookup_type(node.nombre)
        if isinstance(node, ArrayAccess):
            array_type = self._lookup_type(node.nombre)
            return array_type[:-2]
        if isinstance(node, UnaryOp):
            return "bool" if node.op == "!" else self._expr_type(node.expr)
        if isinstance(node, BinOp):
            left = self._expr_type(node.izq)
            right = self._expr_type(node.der)
            if node.op in ("==", "!=", "<", "<=", ">", ">=", "&&", "||"):
                return "bool"
            if node.op == "+" and left == right == "string":
                return "string"
            if node.op == "%":
                return "int"
            return "float" if "float" in (left, right) else "int"
        if isinstance(node, CallExpr):
            if node.nombre in BUILTINS:
                return BUILTINS[node.nombre].return_type
            return self.functions[node.nombre][0]
        raise CodeGenerationError(
            f"no se puede inferir el tipo JavaScript de {type(node).__name__}",
            getattr(node, "token", None),
        )

    def _lookup_type(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise CodeGenerationError(f"tipo no disponible para '{name}'")

    def _tick(self, node):
        line, column = self._position(node)
        return f"__ml_tick({line}, {column});"

    def _is_global_scope(self):
        return not self.in_function and len(self.scopes) == 1

    def _line(self, text):
        self.lines.append("    " * self.indent + text)

    @staticmethod
    def _position(node):
        token = getattr(node, "token", None)
        return (token.line, token.column) if token is not None else (0, 0)

    @staticmethod
    def _json(value):
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _encoded(name):
        return name.encode("utf-8").hex()

    def _var_name(self, name):
        return f"__ml_v_{self._encoded(name)}"

    def _func_name(self, name):
        return f"__ml_f_{self._encoded(name)}"

    def _runtime(self):
        runtime = r'''"use strict";

const __ml_not_declared = Symbol("no declarado");
const __ml_uninitialized = Symbol("sin inicializar");
const __ml_max_steps = __MAX_STEPS__;
const __ml_max_call_depth = __MAX_CALL_DEPTH__;
let __ml_steps = 0;
let __ml_call_depth = 0;
let __ml_inputs = null;

function __ml_error(message, line, column) {
    const position = line > 0 ? ` [línea ${line}, columna ${column}]` : "";
    throw new Error(`Error de ejecución${position}: ${message}`);
}

function __ml_tick(line, column) {
    __ml_steps += 1;
    if (__ml_steps > __ml_max_steps) {
        __ml_error(`se superó el límite de ${__ml_max_steps} instrucciones; posible ciclo infinito`, line, column);
    }
}

function __ml_call(callback, line, column) {
    if (__ml_call_depth >= __ml_max_call_depth) {
        __ml_error(`se superó la profundidad máxima de ${__ml_max_call_depth} llamadas`, line, column);
    }
    __ml_call_depth += 1;
    try {
        return callback();
    } finally {
        __ml_call_depth -= 1;
    }
}

function __ml_format(value, type) {
    if (type === "bool") {
        return value ? "True" : "False";
    }
    if (type === "float") {
        if (Object.is(value, -0)) {
            return "-0.0";
        }
        if (Number.isInteger(value)) {
            return value.toFixed(1);
        }
    }
    return String(value);
}

function __ml_print(value, type) {
    console.log(__ml_format(value, type));
}

function __ml_load(name, value, line, column) {
    if (value === __ml_not_declared) {
        __ml_error(`'${name}' no está declarado`, line, column);
    }
    if (value === __ml_uninitialized) {
        __ml_error(`'${name}' se usó antes de inicializarse`, line, column);
    }
    return value;
}

function __ml_div(left, right, integer, line, column) {
    if (integer) {
        if (right === 0n) {
            __ml_error("división por cero", line, column);
        }
        let result = left / right;
        if (left % right !== 0n && (left < 0n) !== (right < 0n)) {
            result -= 1n;
        }
        return result;
    }
    if (right === 0) {
        __ml_error("división por cero", line, column);
    }
    return left / right;
}

function __ml_mod(left, right, line, column) {
    if (right === 0n) {
        __ml_error("módulo por cero", line, column);
    }
    let result = left % right;
    if (result !== 0n && (result < 0n) !== (right < 0n)) {
        result += right;
    }
    return result;
}

function __ml_pow(left, right, integer, line, column) {
    if (integer && right < 0n) {
        __ml_error("un exponente entero no puede ser negativo", line, column);
    }
    return left ** right;
}

function __ml_check_index(name, array, index, line, column) {
    if (typeof index !== "bigint" || index < 0n || index >= BigInt(array.length)) {
        __ml_error(`índice ${index} fuera de rango para '${name}' (tamaño ${array.length})`, line, column);
    }
    return Number(index);
}

function __ml_array_get(name, array, index, line, column) {
    const position = __ml_check_index(name, array, index, line, column);
    return array[position];
}

function __ml_array_set(name, array, index, value, line, column) {
    const position = __ml_check_index(name, array, index, line, column);
    array[position] = value;
    return value;
}

function __ml_read_input(name, line, column) {
    if (__ml_inputs === null) {
        if (typeof process !== "undefined" && process.versions && process.versions.node) {
            const data = require("fs").readFileSync(0, "utf8");
            __ml_inputs = data.length === 0 ? [] : data.split(/\r?\n/);
            if (__ml_inputs.length > 0 && __ml_inputs[__ml_inputs.length - 1] === "") {
                __ml_inputs.pop();
            }
        } else {
            __ml_inputs = [];
        }
    }
    if (__ml_inputs.length > 0) {
        return __ml_inputs.shift();
    }
    if (typeof prompt === "function") {
        const value = prompt(`${name}> `);
        if (value !== null) {
            return value;
        }
    }
    __ml_error(`faltan datos de entrada para ${name}`, line, column);
}

function __ml_input_int(line, column) {
    const value = __ml_read_input("inputInt", line, column).trim();
    if (!/^[+-]?\d+$/.test(value)) {
        __ml_error("inputInt: se esperaba un entero", line, column);
    }
    return BigInt(value);
}

function __ml_input_float(line, column) {
    const text = __ml_read_input("inputFloat", line, column).trim();
    const value = Number(text);
    if (text === "" || !Number.isFinite(value)) {
        __ml_error("inputFloat: se esperaba un decimal", line, column);
    }
    return value;
}

function __ml_input_string(line, column) {
    return __ml_read_input("inputString", line, column);
}

function __ml_input_bool(line, column) {
    const value = __ml_read_input("inputBool", line, column).trim().toLowerCase();
    if (value !== "true" && value !== "false") {
        __ml_error("inputBool: se esperaba true o false", line, column);
    }
    return value === "true";
}

function __ml_length(text) {
    return BigInt(Array.from(text).length);
}

function __ml_substring(text, start, count, line, column) {
    const chars = Array.from(text);
    if (typeof start !== "bigint" || typeof count !== "bigint" || start < 0n || count < 0n || start + count > BigInt(chars.length)) {
        __ml_error("substring: rango inválido para substring", line, column);
    }
    return chars.slice(Number(start), Number(start + count)).join("");
}

function __ml_to_string(value, type) {
    return __ml_format(value, type);
}

function __ml_to_int(value, line, column) {
    if (typeof value === "boolean") {
        return value ? 1n : 0n;
    }
    if (typeof value === "bigint") {
        return value;
    }
    if (typeof value === "number" && Number.isFinite(value)) {
        return BigInt(Math.trunc(value));
    }
    if (typeof value === "string" && /^[+-]?\d+$/.test(value.trim())) {
        return BigInt(value.trim());
    }
    __ml_error("toInt: conversión inválida", line, column);
}

function __ml_to_float(value, line, column) {
    if (typeof value === "boolean") {
        return value ? 1.0 : 0.0;
    }
    const text = typeof value === "string" ? value.trim() : value;
    const result = Number(text);
    if (text === "" || !Number.isFinite(result)) {
        __ml_error("toFloat: conversión inválida", line, column);
    }
    return result;
}

function __ml_contains(text, search) {
    return text.includes(search);
}

function __ml_regex_match(text, pattern, line, column) {
    try {
        return new RegExp(pattern).test(text);
    } catch (error) {
        __ml_error(`regexMatch: ${error.message}`, line, column);
    }
}

function __ml_run(main) {
    try {
        main();
    } catch (error) {
        if (typeof process !== "undefined" && process.versions && process.versions.node) {
            console.error(error.message);
            process.exitCode = 1;
            return;
        }
        throw error;
    }
}'''
        return runtime.replace("__MAX_STEPS__", str(self.max_steps)).replace(
            "__MAX_CALL_DEPTH__", str(self.max_call_depth)
        )
