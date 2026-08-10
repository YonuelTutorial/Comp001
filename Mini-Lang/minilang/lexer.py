import re

from .errors import LexerError
from .tokens import Token


KEYWORDS = {
    "print": "PRINT",
    "int": "INT_T",
    "bool": "BOOL_T",
    "string": "STRING_T",
    "void": "VOID_T",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "return": "RETURN",
    "break": "BREAK",
    "continue": "CONTINUE",
    "true": "TRUE",
    "false": "FALSE",
}


TOKEN_REGEX = [
    ("STRING", r'"(?:\\.|[^"\\\r\n])*"|\'(?:\\.|[^\'\\\r\n])*\''),
    ("COMMENT", r"//[^\r\n]*"),
    ("EQ", r"=="),
    ("NE", r"!="),
    ("LE", r"<="),
    ("GE", r">="),
    ("AND", r"&&"),
    ("OR", r"\|\|"),
    ("ASSIGN", r"="),
    ("LT", r"<"),
    ("GT", r">"),
    ("NOT", r"!"),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("STAR", r"\*"),
    ("SLASH", r"/"),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LBRACKET", r"\["),
    ("RBRACKET", r"\]"),
    ("COMMA", r","),
    ("SEMI", r";"),
    ("NUM", r"\d+"),
    ("ID", r"[A-Za-z_]\w*"),
    ("NEWLINE", r"\r\n|\r|\n"),
    ("SKIP", r"[ \t\f]+"),
    ("MISMATCH", r"[\s\S]"),
]


MASTER_REGEX = re.compile("|".join(f"(?P<{kind}>{pattern})" for kind, pattern in TOKEN_REGEX))


class Lexer:
    def tokenize(self, code):
        tokens = []
        line = 1
        column = 1

        for match in MASTER_REGEX.finditer(code):
            kind = match.lastgroup
            value = match.group()
            token = Token(kind, value, line, column)

            if kind == "NEWLINE":
                line += 1
                column = 1
                continue
            if kind in ("SKIP", "COMMENT"):
                column += len(value)
                continue
            if kind == "MISMATCH":
                raise LexerError(f"token no reconocido: {value!r}", token)
            if kind == "ID":
                token = Token(KEYWORDS.get(value, "ID"), value, line, column)

            tokens.append(token)
            column += len(value)

        tokens.append(Token("EOF", "", line, column))
        return tokens
