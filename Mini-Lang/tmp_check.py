from pathlib import Path
import app
code = 'print("hola");'
tokens = app.Lexer().tokenize(code)
print(tokens)
ast = app.Parser(tokens).parse()
print(type(ast[0]).__name__)
try:
    app.SemanticAnalyzer().analyze(ast)
    ast_opt = app.Optimizer().optimize(ast)
    print(app.Interpreter().ejecutar(ast_opt))
except Exception as e:
    print('ERROR:', e)
