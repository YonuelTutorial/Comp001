from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    column: int

    # Compatibilidad
    def __getitem__(self, index):
        return (self.kind, self.value, self.line, self.column)[index]

    def __iter__(self):
        yield self.kind
        yield self.value
