import app; code = "print(\"hola\");"; tokens = app.Lexer().tokenize(code); print(tokens); ast = app.Parser(tokens).parse(); print(ast[0].__class__.__name__)
