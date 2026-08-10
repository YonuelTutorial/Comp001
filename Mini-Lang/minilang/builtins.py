import re
from dataclasses import dataclass

from .errors import MiniLangRuntimeError


@dataclass(frozen=True)
class BuiltinSpec:
    params: tuple
    return_type: str


BUILTINS = {
    "inputInt": BuiltinSpec((), "int"),
    "inputFloat": BuiltinSpec((), "float"),
    "inputString": BuiltinSpec((), "string"),
    "inputBool": BuiltinSpec((), "bool"),
    "length": BuiltinSpec(("string",), "int"),
    "substring": BuiltinSpec(("string", "int", "int"), "string"),
    "toString": BuiltinSpec(("any",), "string"),
    "toInt": BuiltinSpec(("any",), "int"),
    "toFloat": BuiltinSpec(("any",), "float"),
    "contains": BuiltinSpec(("string", "string"), "bool"),
    "regexMatch": BuiltinSpec(("string", "string"), "bool"),
}


def execute_builtin(name, args, input_provider=None, token=None):
    provider = input_provider or input
    try:
        if name == "inputInt":
            return int(provider("int> "))
        if name == "inputFloat":
            return float(provider("float> "))
        if name == "inputString":
            return str(provider("string> "))
        if name == "inputBool":
            value = str(provider("bool> ")).strip().lower()
            if value not in ("true", "false"):
                raise ValueError("se esperaba true o false")
            return value == "true"
        if name == "length":
            return len(args[0])
        if name == "substring":
            text, start, count = args
            if start < 0 or count < 0 or start + count > len(text):
                raise ValueError("rango inválido para substring")
            return text[start:start + count]
        if name == "toString":
            return str(args[0])
        if name == "toInt":
            return int(args[0])
        if name == "toFloat":
            return float(args[0])
        if name == "contains":
            return args[1] in args[0]
        if name == "regexMatch":
            return re.search(args[1], args[0]) is not None
    except (ValueError, TypeError, re.error) as error:
        raise MiniLangRuntimeError(f"{name}: {error}", token) from error
    raise MiniLangRuntimeError(f"función incorporada desconocida '{name}'", token)
