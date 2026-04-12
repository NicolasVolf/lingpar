import sys
import re
from typing import Dict


class Token:
    def __init__(self, token_type, value):
        self.type = token_type
        self.value = value


class Variable:
    def __init__(self, value, var_type: str, is_mutable: bool = False):
        self.value = value
        self.type = var_type
        self.is_mutable = is_mutable


class SymbolTable:
    def __init__(self):
        self.table: Dict[str, Variable] = {}

    def get_value(self, name: str):
        if name not in self.table:
            raise ValueError(f"[Semantic] Variavel '{name}' nao existe")
        var = self.table[name]
        return Variable(var.value, var.type)

    def create_variable(self, name: str, value, var_type: str, is_mutable: bool = False):
        if name in self.table:
            raise ValueError(f"[Semantic] Variavel '{name}' ja foi declarada")
        if value is None:
            if var_type == "i32":
                value = Variable(0, "i32")
            elif var_type == "bool":
                value = Variable(False, "bool")
            elif var_type == "str":
                value = Variable("", "str")
            else:
                raise ValueError(f"[Semantic] Tipo invalido: {var_type}")

        is_valid_type = (
            isinstance(value, Variable)
            and value.type == var_type
            and ((var_type == "i32" and type(value.value) is int)
                 or (var_type == "bool" and type(value.value) is bool)
                 or (var_type == "str" and type(value.value) is str))
        )
        if not is_valid_type:
            raise ValueError(
                f"[Semantic] Tipo invalido para '{name}': esperado {var_type}, recebido {value.type}"
            )
        self.table[name] = Variable(value.value, var_type, is_mutable)

    def set_value(self, name: str, value):
        if name not in self.table:
            raise ValueError(f"[Semantic] Variavel '{name}' nao foi declarada")

        variable = self.table[name]
        if not variable.is_mutable:
            raise ValueError(f"[Semantic] Variavel '{name}' nao e mutavel")

        is_valid_type = (
            isinstance(value, Variable)
            and value.type == variable.type
            and ((variable.type == "i32" and type(value.value) is int)
                 or (variable.type == "bool" and type(value.value) is bool)
                 or (variable.type == "str" and type(value.value) is str))
        )
        if not is_valid_type:
            raise ValueError(
                f"[Semantic] Tipo invalido para '{name}': esperado {variable.type}, recebido {value.type}"
            )

        variable.value = value.value


class Node:
    def __init__(self, value, children=None):
        self.value = value
        self.children = children if children is not None else []

    def evaluate(self, st):
        pass


class IntVal(Node):
    def evaluate(self, st):
        return Variable(self.value, "i32")


class BoolVal(Node):
    def evaluate(self, st):
        return Variable(self.value, "bool")


class StringVal(Node):
    def evaluate(self, st):
        return Variable(self.value, "str")


class Identifier(Node):
    def evaluate(self, st):
        return st.get_value(self.value)


class UnOp(Node):
    def evaluate(self, st):
        child_val = self.children[0].evaluate(st)
        if self.value == "+":
            if child_val.type != "i32":
                raise ValueError("[Semantic] Operador '+' unario exige i32")
            return Variable(+child_val.value, "i32")
        if self.value == "-":
            if child_val.type != "i32":
                raise ValueError("[Semantic] Operador '-' unario exige i32")
            return Variable(-child_val.value, "i32")
        if self.value == "!":
            if child_val.type != "bool":
                raise ValueError("[Semantic] Operador '!' exige bool")
            return Variable(not child_val.value, "bool")
        raise ValueError(f"[Semantic] Operador unario invalido: {self.value}")


class BinOp(Node):
    def evaluate(self, st):
        left  = self.children[0].evaluate(st)
        right = self.children[1].evaluate(st)
        if self.value == "+":
            if left.type == "i32" and right.type == "i32":
                return Variable(left.value + right.value, "i32")
            if left.type == "str" and right.type == "str":
                return Variable(left.value + right.value, "str")
            raise ValueError("[Semantic] Operador '+' exige i32+i32 ou str+str")
        if self.value == "-":
            if left.type == "i32" and right.type == "i32":
                return Variable(left.value - right.value, "i32")
            raise ValueError("[Semantic] Operador '-' exige i32")
        if self.value == "*":
            if left.type == "i32" and right.type == "i32":
                return Variable(left.value * right.value, "i32")
            raise ValueError("[Semantic] Operador '*' exige i32")
        if self.value == "/":
            if left.type != "i32" or right.type != "i32":
                raise ValueError("[Semantic] Operador '/' exige i32")
            if right.value == 0:
                raise ValueError("[Semantic] Divisao por zero")
            return Variable(left.value // right.value, "i32")
        if self.value == "^":
            if left.type == "i32" and right.type == "i32":
                return Variable(left.value ^ right.value, "i32")
            raise ValueError("[Semantic] Operador '^' exige i32")
        if self.value == "==":
            if left.type != right.type:
                raise ValueError("[Semantic] Operador '==' exige tipos iguais")
            return Variable(left.value == right.value, "bool")
        if self.value == ">":
            if left.type == "i32" and right.type == "i32":
                return Variable(left.value > right.value, "bool")
            raise ValueError("[Semantic] Operador '>' exige i32")
        if self.value == "<":
            if left.type == "i32" and right.type == "i32":
                return Variable(left.value < right.value, "bool")
            raise ValueError("[Semantic] Operador '<' exige i32")
        if self.value == "&&":
            if left.type == "bool" and right.type == "bool":
                return Variable(left.value and right.value, "bool")
            raise ValueError("[Semantic] Operador '&&' exige bool")
        if self.value == "||":
            if left.type == "bool" and right.type == "bool":
                return Variable(left.value or right.value, "bool")
            raise ValueError("[Semantic] Operador '||' exige bool")
        raise ValueError(f"[Semantic] Operador binario invalido: {self.value}")


class Print(Node):
    def evaluate(self, st):
        print(self.children[0].evaluate(st).value)


class Assignment(Node):
    def evaluate(self, st):
        var_name = self.children[0].value
        val = self.children[1].evaluate(st)
        st.set_value(var_name, val)


class VarDec(Node):
    def evaluate(self, st):
        var_name = self.children[0].value
        value = None
        if len(self.children) == 2:
            value = self.children[1].evaluate(st)
        is_mutable = getattr(self, "is_mutable", False)
        st.create_variable(var_name, value, self.value, is_mutable)


class Block(Node):
    def evaluate(self, st):
        for child in self.children:
            child.evaluate(st)


class If(Node):
    def evaluate(self, st):
        condition = self.children[0].evaluate(st)
        if condition.type != "bool":
            raise ValueError("[Semantic] Condicao do if deve ser bool")
        if condition.value:
            self.children[1].evaluate(st)
        elif len(self.children) == 3:
            self.children[2].evaluate(st)


class While(Node):
    def evaluate(self, st):
        while True:
            condition = self.children[0].evaluate(st)
            if condition.type != "bool":
                raise ValueError("[Semantic] Condicao do while deve ser bool")
            if not condition.value:
                break
            self.children[1].evaluate(st)


class Read(Node):
    def evaluate(self, st):
        try:
            return Variable(int(input()), "i32")
        except ValueError:
            raise ValueError("[Semantic] scanln! esperava um inteiro")


class NoOp(Node):
    def evaluate(self, st):
        return None


class PrePro:
    @staticmethod
    def filter(source_code):
        return re.sub(r"//[^\n]*", "", source_code)


class Lexer:
    RESERVED_WORDS = {
        "println!": "PRINT",
        "scanln!":  "READ",
        "if":       "IF",
        "else":     "ELSE",
        "while":    "WHILE",
        "let":      "LET",
        "mut":      "MUT",
        "true":     "BOOL",
        "false":    "BOOL",
        "str":      "TYPE",
        "i32":      "TYPE",
        "bool":     "TYPE",
    }

    def __init__(self, source):
        self.source   = source
        self.position = 0
        self.next     = None

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
        elif char == '*':
            self.next = Token("MUL", "*")
            self.position += 1
        elif char == '/':
            self.next = Token("DIV", "/")
            self.position += 1
        elif char == '^':
            self.next = Token("XOR", "^")
            self.position += 1
        elif char == '(':
            self.next = Token("OPEN_PAR", "(")
            self.position += 1
        elif char == ')':
            self.next = Token("CLOSE_PAR", ")")
            self.position += 1
        elif char == '{':
            self.next = Token("OPEN_BRA", "{")
            self.position += 1
        elif char == '}':
            self.next = Token("CLOSE_BRA", "}")
            self.position += 1
        elif char == ';':
            self.next = Token("END", ";")
            self.position += 1
        elif char == ':':
            self.next = Token("COLON", ":")
            self.position += 1
        elif char == '>':
            self.next = Token("GT", ">")
            self.position += 1
        elif char == '<':
            self.next = Token("LT", "<")
            self.position += 1
        elif char == '=':
            if self.position + 1 < len(self.source) and self.source[self.position + 1] == '=':
                self.next = Token("EQ", "==")
                self.position += 2
            else:
                self.next = Token("ASSIGN", "=")
                self.position += 1
        elif char == '&':
            if self.position + 1 < len(self.source) and self.source[self.position + 1] == '&':
                self.next = Token("AND", "&&")
                self.position += 2
            else:
                raise ValueError("[Lexer] '&' isolado invalido; use '&&'")
        elif char == '|':
            if self.position + 1 < len(self.source) and self.source[self.position + 1] == '|':
                self.next = Token("OR", "||")
                self.position += 2
            else:
                raise ValueError("[Lexer] '|' isolado invalido; use '||'")
        elif char == '!':
            self.next = Token("NOT", "!")
            self.position += 1
        elif char.isdigit():
            num = char
            self.position += 1
            while self.position < len(self.source) and self.source[self.position].isdigit():
                num += self.source[self.position]
                self.position += 1
            self.next = Token("INT", int(num))
        elif char.isalpha() or char == '_':
            ident = char
            self.position += 1
            while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == "_"):
                ident += self.source[self.position]
                self.position += 1
            if self.position < len(self.source) and self.source[self.position] == '!':
                ident += '!'
                self.position += 1
            if ident in Lexer.RESERVED_WORDS:
                token_type = Lexer.RESERVED_WORDS[ident]
                if token_type == "BOOL":
                    self.next = Token("BOOL", ident == "true")
                else:
                    self.next = Token(token_type, ident)
            else:
                self.next = Token("IDEN", ident)
        elif char == '"':
            self.position += 1
            str_val = ""
            while self.position < len(self.source) and self.source[self.position] != '"':
                if self.source[self.position] == '\n':
                    raise ValueError("[Lexer] String nao pode quebrar linha")
                str_val += self.source[self.position]
                self.position += 1
            if self.position >= len(self.source):
                raise ValueError("[Lexer] String sem aspas de fechamento")
            self.position += 1
            self.next = Token("STR", str_val)
        else:
            raise ValueError(f"[Lexer] Simbolo invalido: '{char}'")


class Parser:
    lexer = None

    def parse_program():
        instructions = []
        while Parser.lexer.next.type != "EOF":
            instructions.append(Parser.parse_statement())
        return Block("BLOCK", instructions)

    def parse_block():
        if Parser.lexer.next.type != "OPEN_BRA":
            raise ValueError("[Parser] '{' esperado para iniciar bloco")
        Parser.lexer.select_next()

        instructions = []
        while Parser.lexer.next.type != "CLOSE_BRA":
            if Parser.lexer.next.type == "EOF":
                raise ValueError("[Parser] '}' esperado para fechar bloco")
            instructions.append(Parser.parse_statement())

        Parser.lexer.select_next()
        return Block("BLOCK", instructions)

    def parse_statement():
        tok = Parser.lexer.next

        if tok.type == "OPEN_BRA":
            return Parser.parse_block()

        if tok.type == "LET":
            Parser.lexer.select_next()

            is_mutable = False
            if Parser.lexer.next.type == "MUT":
                is_mutable = True
                Parser.lexer.select_next()

            if Parser.lexer.next.type != "IDEN":
                raise ValueError("[Parser] Identificador esperado na declaracao")

            ident_node = Identifier(Parser.lexer.next.value, [])
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "COLON":
                raise ValueError("[Parser] ':' esperado na declaracao")
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "TYPE":
                raise ValueError("[Parser] Tipo esperado na declaracao")
            type_node = Node(Parser.lexer.next.value, [])
            Parser.lexer.select_next()

            children = [ident_node]
            if Parser.lexer.next.type == "ASSIGN":
                Parser.lexer.select_next()
                children.append(Parser.parse_bool_expression())

            if Parser.lexer.next.type != "END":
                raise ValueError("[Parser] ';' esperado no final da declaracao")
            Parser.lexer.select_next()

            vardec_node = VarDec(type_node.value, children)
            vardec_node.is_mutable = is_mutable
            return vardec_node

        if tok.type == "IDEN":
            name = tok.value
            ident_node = Identifier(name, [])
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "ASSIGN":
                raise ValueError("[Parser] '=' esperado apos identificador")
            Parser.lexer.select_next()

            expr = Parser.parse_bool_expression()

            if Parser.lexer.next.type != "END":
                raise ValueError("[Parser] ';' esperado no final da atribuicao")
            Parser.lexer.select_next()

            return Assignment("=", [ident_node, expr])

        if tok.type == "PRINT":
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "OPEN_PAR":
                raise ValueError("[Parser] '(' esperado apos println!")
            Parser.lexer.select_next()

            expr = Parser.parse_bool_expression()

            if Parser.lexer.next.type != "CLOSE_PAR":
                raise ValueError("[Parser] ')' esperado em println!")
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "END":
                raise ValueError("[Parser] ';' esperado apos println!(...)")
            Parser.lexer.select_next()

            return Print("PRINT", [expr])

        if tok.type == "IF":
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "OPEN_PAR":
                raise ValueError("[Parser] '(' esperado apos 'if'")
            Parser.lexer.select_next()

            cond = Parser.parse_bool_expression()

            if Parser.lexer.next.type != "CLOSE_PAR":
                raise ValueError("[Parser] ')' esperado apos condicao do if")
            Parser.lexer.select_next()

            then_block = Parser.parse_block()

            if Parser.lexer.next.type == "ELSE":
                Parser.lexer.select_next()
                else_block = Parser.parse_block()
                return If("IF", [cond, then_block, else_block])

            return If("IF", [cond, then_block])

        if tok.type == "WHILE":
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "OPEN_PAR":
                raise ValueError("[Parser] '(' esperado apos 'while'")
            Parser.lexer.select_next()

            cond = Parser.parse_bool_expression()

            if Parser.lexer.next.type != "CLOSE_PAR":
                raise ValueError("[Parser] ')' esperado apos condicao do while")
            Parser.lexer.select_next()

            body = Parser.parse_block()
            return While("WHILE", [cond, body])

        if tok.type == "END":
            Parser.lexer.select_next()
            return NoOp("NOOP", [])

        raise ValueError(f"[Parser] Instrucao invalida, token: {tok.type} = '{tok.value}'")

    def parse_bool_expression():
        result = Parser.parse_bool_term()
        while Parser.lexer.next.type == "OR":
            Parser.lexer.select_next()
            result = BinOp("||", [result, Parser.parse_bool_term()])
        return result

    def parse_bool_term():
        result = Parser.parse_rel_expression()
        while Parser.lexer.next.type == "AND":
            Parser.lexer.select_next()
            result = BinOp("&&", [result, Parser.parse_rel_expression()])
        return result

    def parse_rel_expression():
        result = Parser.parse_expression()
        if Parser.lexer.next.type == "EQ":
            Parser.lexer.select_next()
            result = BinOp("==", [result, Parser.parse_expression()])
        elif Parser.lexer.next.type == "GT":
            Parser.lexer.select_next()
            result = BinOp(">", [result, Parser.parse_expression()])
        elif Parser.lexer.next.type == "LT":
            Parser.lexer.select_next()
            result = BinOp("<", [result, Parser.parse_expression()])
        return result

    def parse_expression():
        result = Parser.parse_term()
        while Parser.lexer.next.type in ("PLUS", "MINUS", "XOR"):
            op_tok = Parser.lexer.next.type
            Parser.lexer.select_next()
            if op_tok == "PLUS":
                result = BinOp("+", [result, Parser.parse_term()])
            elif op_tok == "MINUS":
                result = BinOp("-", [result, Parser.parse_term()])
            elif op_tok == "XOR":
                result = BinOp("^", [result, Parser.parse_term()])
        return result

    def parse_term():
        result = Parser.parse_factor()
        while Parser.lexer.next.type in ("MUL", "DIV"):
            op_tok = Parser.lexer.next.type
            Parser.lexer.select_next()
            if op_tok == "MUL":
                result = BinOp("*", [result, Parser.parse_factor()])
            elif op_tok == "DIV":
                result = BinOp("/", [result, Parser.parse_factor()])
        return result

    def parse_factor():
        tok = Parser.lexer.next

        if tok.type == "INT":
            Parser.lexer.select_next()
            return IntVal(tok.value, [])

        if tok.type == "BOOL":
            Parser.lexer.select_next()
            return BoolVal(tok.value, [])

        if tok.type == "STR":
            Parser.lexer.select_next()
            return StringVal(tok.value, [])

        if tok.type == "IDEN":
            Parser.lexer.select_next()
            return Identifier(tok.value, [])

        if tok.type == "PLUS":
            Parser.lexer.select_next()
            return UnOp("+", [Parser.parse_factor()])

        if tok.type == "MINUS":
            Parser.lexer.select_next()
            return UnOp("-", [Parser.parse_factor()])

        if tok.type == "NOT":
            Parser.lexer.select_next()
            return UnOp("!", [Parser.parse_factor()])

        if tok.type == "READ":
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "OPEN_PAR":
                raise ValueError("[Parser] '(' esperado apos scanln!")
            Parser.lexer.select_next()

            if Parser.lexer.next.type != "CLOSE_PAR":
                raise ValueError("[Parser] ')' esperado em scanln!")
            Parser.lexer.select_next()

            return Read("READ", [])

        if tok.type == "OPEN_PAR":
            Parser.lexer.select_next()
            result = Parser.parse_bool_expression()
            if Parser.lexer.next.type != "CLOSE_PAR":
                raise ValueError("[Parser] ')' esperado para fechar parenteses")
            Parser.lexer.select_next()
            return result

        raise ValueError(f"[Parser] Token invalido em parse_factor: {tok.type} = '{tok.value}'")

    def run(code):
        Parser.lexer = Lexer(code)
        Parser.lexer.select_next()
        tree = Parser.parse_program()
        if Parser.lexer.next.type != "EOF":
            raise ValueError("[Parser] EOF esperado no final do programa")
        return tree


def main():
    if len(sys.argv) < 2:
        raise ValueError("[Main] Caminho do arquivo de entrada nao informado")

    input_path = sys.argv[1]
    with open(input_path, "r", encoding="utf-8") as f:
        source_code = f.read() + "\n"

    filtered_code = PrePro.filter(source_code)
    tree = Parser.run(filtered_code)
    st = SymbolTable()
    tree.evaluate(st)


if __name__ == "__main__":
    main()
