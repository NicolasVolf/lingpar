import sys
import re
from typing import Dict

class Token:
    def __init__(self, token_type, value):
        self.type = token_type 
        self.value = value   


class Variable:
    def __init__(self, value: int):
        self.value = value


class SymbolTable:
    def __init__(self):
        self.table: Dict[str, Variable] = {}

    def get_value(self, name: str):
        if not isinstance(name, str):
            raise ValueError("[Semantic] Nome de variavel deve ser string")
        if name not in self.table:
            raise ValueError("[Semantic] Variavel nao existe")

        return self.table[name].value

    def set_value(self, name: str, value: int):
        if not isinstance(name, str):
            raise ValueError("[Semantic] Nome de variavel deve ser string")
        if not isinstance(value, int):
            raise ValueError("[Semantic] Valor da variavel deve ser int")

        self.table[name] = Variable(value)


class Node:
    def __init__(self, value, children=None):
        self.value = value
        self.children = children if children is not None else []

    def evaluate(self, st):
        pass


class IntVal(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st):
        return self.value


class Identifier(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st):
        return st.get_value(self.value)


class UnOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st):
        if len(self.children) != 1:
            raise ValueError("[Semantic] UnOp deve conter exatamente 1 filho")

        child_value = self.children[0].evaluate(st)

        if self.value == "+":
            return +child_value
        if self.value == "-":
            return -child_value

        raise ValueError("[Semantic] Operador unario invalido")


class BinOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st):
        if len(self.children) != 2:
            raise ValueError("[Semantic] BinOp deve conter exatamente 2 filhos")

        left_value = self.children[0].evaluate(st)
        right_value = self.children[1].evaluate(st)

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


class Print(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st):
        if len(self.children) != 1:
            raise ValueError("[Semantic] Print deve conter exatamente 1 filho")

        print(self.children[0].evaluate(st))


class Assignment(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st):
        if len(self.children) != 2:
            raise ValueError("[Semantic] Assignment deve conter exatamente 2 filhos")
        if not isinstance(self.children[0], Identifier):
            raise ValueError("[Semantic] Primeiro filho de Assignment deve ser Identifier")

        variable_name = self.children[0].value
        assigned_value = self.children[1].evaluate(st)
        st.set_value(variable_name, assigned_value)


class Block(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st):
        for child in self.children:
            child.evaluate(st)


class NoOp(Node):
    def __init__(self, value=None, children=None):
        super().__init__(value, children or [])

    def evaluate(self, st):
        return None


class PrePro:
    @staticmethod
    def filter(source_code):
        return re.sub(r"//[^\n]*", "", source_code)


class Lexer:
    RESERVED_WORDS = {
        "println!": "PRINT"
    }

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
        elif char == '=':
            self.next = Token("ASSIGN", "=")
            self.position += 1
        elif char == ';':
            self.next = Token("END", ";")
            self.position += 1
            
        elif char.isdigit():
            num_str = char
            self.position += 1
            while self.position < len(self.source) and self.source[self.position].isdigit():
                num_str += self.source[self.position]
                self.position += 1

            if self.position < len(self.source) and (self.source[self.position].isalpha() or self.source[self.position] == "_"):
                raise ValueError("[lexer] Identificador invalido")


            self.next = Token("INT", int(num_str))

        elif char.isalpha():
            ident = char
            self.position += 1
            while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == "_"):
                ident += self.source[self.position]
                self.position += 1

            if ident == "println" and self.position < len(self.source) and self.source[self.position] == "!":
                ident += "!"
                self.position += 1

            if ident in Lexer.RESERVED_WORDS:
                self.next = Token(Lexer.RESERVED_WORDS[ident], ident)
            else:
                self.next = Token("IDEN", ident)
            
        else:
            raise ValueError("[lexer] Simbolo invalido no lexer")


class Parser:
    lexer = None

    def parse_program():
        instructions = []

        while Parser.lexer.next.type != "EOF":
            instructions.append(Parser.parse_statement())

        return Block("BLOCK", instructions)

    def parse_statement():
        if Parser.lexer.next.type == "IDEN":
            identifier_name = Parser.lexer.next.value
            identifier_node = Identifier(identifier_name, [])
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "ASSIGN":
                raise ValueError("[parser] Erro no parser: '=' esperado")
            Parser.lexer.select_next()

            expression_node = Parser.parse_expression()

            if Parser.lexer.next.type != "END":
                raise ValueError("[parser] Erro no parser: ';' esperado")
            Parser.lexer.select_next()

            return Assignment("=", [identifier_node, expression_node])

        if Parser.lexer.next.type == "PRINT":
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "OPEN_PAR":
                raise ValueError("[parser] Erro no parser: '(' esperado em print")
            Parser.lexer.select_next()

            expression_node = Parser.parse_expression()

            if Parser.lexer.next.type != "CLOSE_PAR":
                raise ValueError("[parser] Erro no parser: ')' esperado em print")
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "END":
                raise ValueError("[parser] Erro no parser: ';' esperado")
            Parser.lexer.select_next()

            return Print("PRINT", [expression_node])

        if Parser.lexer.next.type == "END":
            Parser.lexer.select_next()
            return NoOp()

        raise ValueError("[parser] Erro no parser: instrucao invalida")

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

        elif Parser.lexer.next.type == "IDEN":
            resultado = Parser.lexer.next.value
            Parser.lexer.select_next()
            return Identifier(resultado, [])
        
        elif Parser.lexer.next.type == "PLUS":
            Parser.lexer.select_next()
            return UnOp("+", [Parser.parse_factor()])
        
        elif Parser.lexer.next.type == "MINUS":
            Parser.lexer.select_next()
            return UnOp("-", [Parser.parse_factor()])
        
        elif Parser.lexer.next.type == "OPEN_PAR":
            Parser.lexer.select_next()
            resultado = Parser.parse_expression()
            if Parser.lexer.next.type != "CLOSE_PAR":
                raise ValueError("[parser] Erro no parser: fechamento de parenteses esperado")
            Parser.lexer.select_next()
            return resultado
        
        else:
            raise ValueError("[parser] Erro no parser: token inválido em parse_factor")
    

    def run(code):
        Parser.lexer = Lexer(code)
        
        Parser.lexer.select_next()
        
        resultado_final = Parser.parse_program()
        
        if Parser.lexer.next.type != "EOF":
               raise ValueError("[parser] Erro no parser: tem que ser EOF no final da expressao")
             
        return resultado_final
    

def main():
    if len(sys.argv) < 2:
        raise ValueError("[main] Caminho do arquivo de entrada nao informado")

    input_path = sys.argv[1]
    with open(input_path, "r", encoding="utf-8") as source_file:
        source_code = source_file.read() + "\n"

    filtered_code = PrePro.filter(source_code)
    raiz = Parser.run(filtered_code)
    st = SymbolTable()
    raiz.evaluate(st)

if __name__ == "__main__":    
    main()