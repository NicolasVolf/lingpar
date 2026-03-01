import sys

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
        while self.position < len(self.source) and self.source[self.position].isspace():
            self.position += 1
            
        if self.position >= len(self.source):
            self.next = Token("EOF", "")
            return

        char = self.source[self.position]

        if char == '+':
            self.next = Token("PLUS", "+")
            self.position += 1
        elif char == '-':
            self.next = Token("MINUS", "-")
            self.position += 1
            
        elif char.isdigit():
            num_str = char
            self.position += 1
            while self.position < len(self.source) and self.source[self.position].isdigit():
                num_str += self.source[self.position]
                self.position += 1
            self.next = Token("INT", int(num_str))
            
        else:
            raise ValueError(f"[lexer] Simbolo invalido no lexer")


class Parser:
    lexer = None

    def parse_expression():
        if Parser.lexer.next.type != "INT":
            raise ValueError(f"[parser] Erro no parser: tem que ser inteiro no começo da expressao")
        
        resultado = int(Parser.lexer.next.value)
        
        Parser.lexer.select_next()

        while Parser.lexer.next.type == "PLUS" or Parser.lexer.next.type == "MINUS":
            operador = Parser.lexer.next.type
            
            Parser.lexer.select_next()
            
            if Parser.lexer.next.type != "INT":
                raise ValueError(f"[parser] Erro no parser: tem que ser inteiro depois do operador")
            
            if operador == "PLUS":
                resultado += int(Parser.lexer.next.value)
            elif operador == "MINUS":
                resultado -= int(Parser.lexer.next.value)
                
            Parser.lexer.select_next()
            
        return resultado

    def run(code):
        Parser.lexer = Lexer(code)
        
        Parser.lexer.select_next()
        
        resultado_final = Parser.parse_expression()
        
        if Parser.lexer.next.type != "EOF":
             raise ValueError(f"[parser] Erro no parser: tem que ser EOF no final da expressao")
             
        return resultado_final
    

def main():
    escrita_user = " ".join(sys.argv[1:])
    resultado = Parser.run(escrita_user)
    print(resultado)

if __name__ == "__main__":    
    main()