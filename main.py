import sys

class Token:
    def __init__(self, token_type, value):
        self.type = token_type 
        self.value = value   


class Node:
    def __init__(self, value, children=None):
        self.value = value
        self.children = children if children is not None else []

    def evaluate(self):
        pass


class IntVal(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self):
        return self.value


class UnOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self):
        if len(self.children) != 1:
            raise ValueError("[Semantic] UnOp deve conter exatamente 1 filho")

        child_value = self.children[0].evaluate()

        if self.value == "+":
            return +child_value
        if self.value == "-":
            return -child_value

        raise ValueError("[Semantic] Operador unario invalido")


class BinOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self):
        if len(self.children) != 2:
            raise ValueError("[Semantic] BinOp deve conter exatamente 2 filhos")

        left_value = self.children[0].evaluate()
        right_value = self.children[1].evaluate()

        if self.value == "+":
            return left_value + right_value
        if self.value == "-":
            return left_value - right_value
        if self.value == "*":
            return left_value * right_value
        if self.value == "/":
            if right_value == 0:
                raise ValueError("[Semantic] Divisao por zero")
            return left_value // right_value
        if self.value == "^":
            return left_value ^ right_value

        raise ValueError("[Semantic] Operador binario invalido")


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
        elif char == '^':
            self.next = Token("XOR", "^")
            self.position += 1
        elif char == '*':
            if self.position + 1 < len(self.source) and self.source[self.position + 1] == '*':
                self.next = Token("POWER", "**")
                self.position += 2
            else:
                self.next = Token("MUL", "*")
                self.position += 1
        elif char == '/':
            self.next = Token("DIV", "/")
            self.position += 1
        elif char == '(':
            self.next = Token("OPEN_PAR", "(")
            self.position += 1
        elif char == ')':
            self.next = Token("CLOSE_PAR", ")")
            self.position += 1
            
        elif char.isdigit():
            num_str = char
            self.position += 1
            while self.position < len(self.source) and self.source[self.position].isdigit():
                num_str += self.source[self.position]
                self.position += 1
            self.next = Token("INT", int(num_str))
            
        else:
            raise ValueError("[lexer] Simbolo invalido no lexer")


class Parser:
    lexer = None

    def parse_expression():   
        resultado = Parser.parse_term()

        while Parser.lexer.next.type == "PLUS" or Parser.lexer.next.type == "MINUS" or Parser.lexer.next.type == "XOR":
            operador = Parser.lexer.next.type
            
            Parser.lexer.select_next()
            
            if operador == "PLUS":
                resultado = BinOp("+", [resultado, Parser.parse_term()])
            elif operador == "MINUS":
                resultado = BinOp("-", [resultado, Parser.parse_term()])
            elif operador == "XOR":
                resultado = BinOp("^", [resultado, Parser.parse_term()])
            
        return resultado
    
    def parse_term():
        resultado = Parser.parse_factor()

        while Parser.lexer.next.type == "MUL" or Parser.lexer.next.type == "DIV":
            operador = Parser.lexer.next.type
            
            Parser.lexer.select_next()
            
            if operador == "MUL":
                resultado = BinOp("*", [resultado, Parser.parse_factor()])
            elif operador == "DIV":
                resultado = BinOp("/", [resultado, Parser.parse_factor()])
        
        return resultado

    def parse_factor():
        if Parser.lexer.next.type == "INT":
            resultado = Parser.lexer.next.value
            Parser.lexer.select_next()
            return IntVal(resultado, [])
        
        elif Parser.lexer.next.type == "PLUS":
            Parser.lexer.select_next()
            return UnOp("+", [Parser.parse_factor()])
        
        elif Parser.lexer.next.type == "MINUS":
            Parser.lexer.select_next()
            return UnOp("-", [Parser.parse_factor()])
        
        if Parser.lexer.next.type == "INT":
            resultado = Parser.lexer.next.value
            Parser.lexer.select_next()
        
        elif Parser.lexer.next.type == "OPEN_PAR":
            Parser.lexer.select_next()
            resultado = Parser.parse_expression()
            if Parser.lexer.next.type != "CLOSE_PAR":
                raise ValueError("[parser] Erro no parser: fechamento de parenteses esperado")
            Parser.lexer.select_next()
        
        else:
            raise ValueError("[parser] Erro no parser: token inválido em parse_factor")
    

    def run(code):
        Parser.lexer = Lexer(code)
        
        Parser.lexer.select_next()
        
        resultado_final = Parser.parse_expression()
        
        if Parser.lexer.next.type != "EOF":
               raise ValueError("[parser] Erro no parser: tem que ser EOF no final da expressao")
             
        return resultado_final
    

def main():
    escrita_user = " ".join(sys.argv[1:])
    raiz = Parser.run(escrita_user)
    resultado = raiz.evaluate()
    print(resultado)

if __name__ == "__main__":    
    main()