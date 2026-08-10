from dataclasses import fields, is_dataclass


def format_ast(nodes):
    lines = []
    for node in nodes:
        _format_value(node, lines, 0)
    return "\n".join(lines)


def _format_value(value, lines, depth, name=None):
    prefix = "  " * depth
    label = f"{name}: " if name else ""
    if is_dataclass(value):
        lines.append(f"{prefix}{label}{type(value).__name__}")
        for item in fields(value):
            if item.name == "token":
                continue
            _format_value(getattr(value, item.name), lines, depth + 1, item.name)
    elif isinstance(value, list):
        lines.append(f"{prefix}{label}[{len(value)}]")
        for item in value:
            _format_value(item, lines, depth + 1)
    else:
        lines.append(f"{prefix}{label}{value!r}")
