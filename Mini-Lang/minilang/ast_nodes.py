from dataclasses import dataclass, field
from typing import Optional

from .tokens import Token


@dataclass
class Param:
    tipo: str
    nombre: str
    token: Optional[Token] = None


@dataclass
class FuncDecl:
    tipo: str
    nombre: str
    params: list[Param]
    body: list
    token: Optional[Token] = None

    @property
    def param_tipo(self):
        return self.params[0].tipo if len(self.params) == 1 else None

    @property
    def param_nombre(self):
        return self.params[0].nombre if len(self.params) == 1 else None


@dataclass
class VarDecl:
    tipo: str
    nombre: str
    valor: Optional[object] = None
    token: Optional[Token] = None


@dataclass
class ArrayDecl:
    tipo: str
    nombre: str
    size: int
    token: Optional[Token] = None


@dataclass
class Assign:
    nombre: str
    valor: object
    token: Optional[Token] = None


@dataclass
class ArrayAssign:
    nombre: str
    index: object
    valor: object
    token: Optional[Token] = None


@dataclass
class IfStmt:
    cond: object
    body: list
    else_body: list = field(default_factory=list)
    token: Optional[Token] = None


@dataclass
class WhileStmt:
    cond: object
    body: list
    token: Optional[Token] = None


@dataclass
class ForStmt:
    init: Optional[object]
    cond: object
    update: Optional[object]
    body: list
    token: Optional[Token] = None


@dataclass
class ImportStmt:
    path: str
    token: Optional[Token] = None


@dataclass
class ReturnStmt:
    expr: Optional[object]
    token: Optional[Token] = None


@dataclass
class BreakStmt:
    token: Optional[Token] = None


@dataclass
class ContinueStmt:
    token: Optional[Token] = None


@dataclass
class Print:
    expr: object
    token: Optional[Token] = None


@dataclass
class ExprStmt:
    expr: object
    token: Optional[Token] = None


@dataclass
class BlockStmt:
    body: list
    token: Optional[Token] = None


@dataclass
class CallExpr:
    nombre: str
    args: list
    token: Optional[Token] = None

    @property
    def arg(self):
        return self.args[0] if len(self.args) == 1 else None


@dataclass
class BinOp:
    izq: object
    op: str
    der: object
    token: Optional[Token] = None


@dataclass
class UnaryOp:
    op: str
    expr: object
    token: Optional[Token] = None


@dataclass
class CastExpr:
    expr: object
    tipo: str
    token: Optional[Token] = None


@dataclass
class Literal:
    val: object
    tipo: str
    token: Optional[Token] = None


@dataclass
class VarAccess:
    nombre: str
    token: Optional[Token] = None


@dataclass
class ArrayAccess:
    nombre: str
    index: object
    token: Optional[Token] = None
