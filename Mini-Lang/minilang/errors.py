class MiniLangError(Exception):
    """Base para errores que deben mostrarse al usuario."""

    phase = "Mini-Lang"

    def __init__(self, message, token=None):
        self.message = message
        self.token = token
        super().__init__(self.__str__())

    def __str__(self):
        if self.token is not None:
            return f"{self.phase} [línea {self.token.line}, columna {self.token.column}]: {self.message}"
        return f"{self.phase}: {self.message}"


class LexerError(MiniLangError):
    phase = "Error léxico"


class ParserError(MiniLangError):
    phase = "Error sintáctico"


class SemanticError(MiniLangError):
    phase = "Error semántico"


class OptimizationError(MiniLangError):
    phase = "Error de optimización"


class MiniLangRuntimeError(MiniLangError):
    phase = "Error de ejecución"


class CodeGenerationError(MiniLangError):
    phase = "Error de generación"
