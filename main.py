class Token:
    def __init__(self, token_type, value):
        self.type = token_type 
        self.value = value   


class Lexer:
    def __init__(self, source):
        self.source = source
        self.position = 0
        self.next = None

    def select_next(self):
        while self.position < len(self.source) and self.source[self.position]:
            self.position += 1
            char = self.source[self.position]

            if self.position >= len(self.source):
                self.next = Token("EOF", "")
                return

            if char == '+':
                self.next = Token("PLUS", "+")
                self.position += 1
            elif char == '-':
                self.next = Token("MINUS", "-")
                self.position += 1
                
            elif char.isdigit():
                num_str = char
                self.position += 1
                self.next = Token("INT", num_str)
                
            else:
                raise ValueError(f"Simbolo invalido no lexer")


class Parser:
    lexer = None

    def parse_expression():
        if Parser.lexer.next.type != "INT":
            raise ValueError(f"Erro no parser: tem que ser inteiro no começo da expressao")
        
        resultado = Parser.lexer.next.value
        
        Parser.lexer.select_next()

        while Parser.lexer.next.type in ["PLUS", "MINUS"]:
            operador = Parser.lexer.next.type
            
            Parser.lexer.select_next()
            
            if Parser.lexer.next.type != "INT":
                raise ValueError(f"Erro no parser: tem que ser inteiro depois do operador")
            
            if operador == "PLUS":
                resultado += Parser.lexer.next.value
            elif operador == "MINUS":
                resultado -= Parser.lexer.next.value
                
            Parser.lexer.select_next()
            
        return resultado

    def run(code):
        Parser.lexer = Lexer(code)
        
        Parser.lexer.select_next()
        
        resultado_final = Parser.parse_expression()
        
        if Parser.lexer.next.type != "EOF":
             raise ValueError(f"Erro no parser: tem que ser EOF no final da expressao")
             
        return resultado_final