import sys
import re
from typing import Dict


# ─── TOKEN ────────────────────────────────────────────────────────────────────

class Token:
    def __init__(self, token_type, value):
        self.type = token_type
        self.value = value


# ─── SYMBOL TABLE ─────────────────────────────────────────────────────────────

class Variable:
    def __init__(self, value: int):
        self.value = value


class SymbolTable:
    def __init__(self):
        self.table: Dict[str, Variable] = {}

    def get_value(self, name: str):
        if name not in self.table:
            raise ValueError(f"[Semantic] Variavel '{name}' nao existe")
        return self.table[name].value

    def set_value(self, name: str, value: int):
        self.table[name] = Variable(value)


# ─── AST NODES ────────────────────────────────────────────────────────────────

class Node:
    def __init__(self, value, children=None):
        self.value = value
        self.children = children if children is not None else []

    def evaluate(self, st):
        pass


class IntVal(Node):
    """Nó folha: representa um inteiro literal."""
    def evaluate(self, st):
        return self.value


class Identifier(Node):
    """Nó folha: representa uma variável. Busca seu valor na SymbolTable."""
    def evaluate(self, st):
        return st.get_value(self.value)


class UnOp(Node):
    """
    Operação unária com 1 filho.
    Operadores suportados: + , - , ! (NOT lógico)
    """
    def evaluate(self, st):
        child_val = self.children[0].evaluate(st)

        if self.value == "+":
            return +child_val
        if self.value == "-":
            return -child_val
        if self.value == "!":
            return 0 if child_val != 0 else 1   # NOT: 0→1, qualquer coisa→0

        raise ValueError(f"[Semantic] Operador unario invalido: {self.value}")


class BinOp(Node):
    """
    Operação binária com 2 filhos.
    Operadores aritméticos : + - * / ^
    Operadores relacionais  : == > <
    Operadores lógicos      : && ||
    """
    def evaluate(self, st):
        left  = self.children[0].evaluate(st)
        right = self.children[1].evaluate(st)

        # Aritmética
        if self.value == "+":  return left + right
        if self.value == "-":  return left - right
        if self.value == "*":  return left * right
        if self.value == "/":
            if right == 0:
                raise ValueError("[Semantic] Divisao por zero")
            return left // right
        if self.value == "^":  return left ^ right

        # Relacionais (retornam 1 ou 0)
        if self.value == "==": return 1 if left == right else 0
        if self.value == ">":  return 1 if left >  right else 0
        if self.value == "<":  return 1 if left <  right else 0

        # Lógicos (retornam 1 ou 0)
        if self.value == "&&": return 1 if (left != 0 and right != 0) else 0
        if self.value == "||": return 1 if (left != 0 or  right != 0) else 0

        raise ValueError(f"[Semantic] Operador binario invalido: {self.value}")


class Print(Node):
    """Imprime o valor do único filho."""
    def evaluate(self, st):
        print(self.children[0].evaluate(st))


class Assignment(Node):
    """Atribui o valor do filho direito à variável do filho esquerdo."""
    def evaluate(self, st):
        var_name = self.children[0].value
        val      = self.children[1].evaluate(st)
        st.set_value(var_name, val)


class Block(Node):
    """Sequência de instruções. Avalia todos os filhos em ordem."""
    def evaluate(self, st):
        for child in self.children:
            child.evaluate(st)


class If(Node):
    """
    Condicional IF / IF-ELSE.
    children[0] → condição
    children[1] → bloco THEN
    children[2] → bloco ELSE  (opcional)
    """
    def evaluate(self, st):
        condition = self.children[0].evaluate(st)
        if condition != 0:
            self.children[1].evaluate(st)
        elif len(self.children) == 3:
            self.children[2].evaluate(st)


class While(Node):
    """
    Laço WHILE.
    children[0] → condição
    children[1] → bloco do corpo
    """
    def evaluate(self, st):
        while self.children[0].evaluate(st) != 0:
            self.children[1].evaluate(st)


class Read(Node):
    """Lê um inteiro do terminal e o retorna."""
    def evaluate(self, st):
        try:
            return int(input())
        except ValueError:
            raise ValueError("[Semantic] scanln! esperava um inteiro")


class NoOp(Node):
    """Instrução vazia (ponto e vírgula sozinho)."""
    def evaluate(self, st):
        return None


# ─── PRE-PROCESSOR ────────────────────────────────────────────────────────────

class PrePro:
    @staticmethod
    def filter(source_code):
        return re.sub(r"//[^\n]*", "", source_code)


# ─── LEXER ────────────────────────────────────────────────────────────────────

class Lexer:
    RESERVED_WORDS = {
        "println!": "PRINT",
        "scanln!":  "READ",
        "if":       "IF",
        "else":     "ELSE",
        "while":    "WHILE",
    }

    def __init__(self, source):
        self.source   = source
        self.position = 0
        self.next     = None

    def select_next(self):
        # Pula espaços em branco
        while self.position < len(self.source) and self.source[self.position].isspace():
            self.position += 1

        if self.position >= len(self.source):
            self.next = Token("EOF", "")
            return

        char = self.source[self.position]

        # ── Operadores de 1 caractere ──────────────────────────────────────────
        if char == '+':
            self.next = Token("PLUS",  "+")
            self.position += 1

        elif char == '-':
            self.next = Token("MINUS", "-")
            self.position += 1

        elif char == '*':
            self.next = Token("MUL",   "*")
            self.position += 1

        elif char == '/':
            self.next = Token("DIV",   "/")
            self.position += 1

        elif char == '^':
            self.next = Token("XOR",   "^")
            self.position += 1

        elif char == '(':
            self.next = Token("OPEN_PAR",  "(")
            self.position += 1

        elif char == ')':
            self.next = Token("CLOSE_PAR", ")")
            self.position += 1

        elif char == '{':
            self.next = Token("OPEN_BRA",  "{")
            self.position += 1

        elif char == '}':
            self.next = Token("CLOSE_BRA", "}")
            self.position += 1

        elif char == ';':
            self.next = Token("END", ";")
            self.position += 1

        # ── = ou == ───────────────────────────────────────────────────────────
        elif char == '=':
            if self._peek() == '=':
                self.next = Token("EQ", "==")
                self.position += 2
            else:
                self.next = Token("ASSIGN", "=")
                self.position += 1

        # ── > ─────────────────────────────────────────────────────────────────
        elif char == '>':
            self.next = Token("GT", ">")
            self.position += 1

        # ── < ─────────────────────────────────────────────────────────────────
        elif char == '<':
            self.next = Token("LT", "<")
            self.position += 1

        # ── && ────────────────────────────────────────────────────────────────
        elif char == '&':
            if self._peek() == '&':
                self.next = Token("AND", "&&")
                self.position += 2
            else:
                raise ValueError("[Lexer] '&' isolado invalido; use '&&'")

        # ── || ────────────────────────────────────────────────────────────────
        elif char == '|':
            if self._peek() == '|':
                self.next = Token("OR", "||")
                self.position += 2
            else:
                raise ValueError("[Lexer] '|' isolado invalido; use '||'")

        # ── ! (NOT ou parte de scanln!) ───────────────────────────────────────
        elif char == '!':
            self.next = Token("NOT", "!")
            self.position += 1

        # ── Inteiros ──────────────────────────────────────────────────────────
        elif char.isdigit():
            num = char
            self.position += 1
            while self.position < len(self.source) and self.source[self.position].isdigit():
                num += self.source[self.position]
                self.position += 1
            self.next = Token("INT", int(num))

        # ── Identificadores e palavras reservadas ─────────────────────────────
        elif char.isalpha() or char == '_':
            ident = char
            self.position += 1
            while self.position < len(self.source) and (
                self.source[self.position].isalnum() or self.source[self.position] == "_"
            ):
                ident += self.source[self.position]
                self.position += 1

            # Captura o '!' de println! e scanln!
            if self.position < len(self.source) and self.source[self.position] == '!':
                ident += '!'
                self.position += 1

            if ident in Lexer.RESERVED_WORDS:
                self.next = Token(Lexer.RESERVED_WORDS[ident], ident)
            else:
                self.next = Token("IDEN", ident)

        else:
            raise ValueError(f"[Lexer] Simbolo invalido: '{char}'")

    def _peek(self):
        """Retorna o caractere seguinte sem avançar a posição."""
        nxt = self.position + 1
        return self.source[nxt] if nxt < len(self.source) else ""


# ─── PARSER ───────────────────────────────────────────────────────────────────

class Parser:
    lexer = None

    # ── Programa principal ────────────────────────────────────────────────────
    def parse_program():
        instructions = []
        while Parser.lexer.next.type != "EOF":
            instructions.append(Parser.parse_statement())
        return Block("BLOCK", instructions)

    # ── Bloco entre chaves ────────────────────────────────────────────────────
    def parse_block():
        """{ statement* }"""
        if Parser.lexer.next.type != "OPEN_BRA":
            raise ValueError("[Parser] '{' esperado para iniciar bloco")
        Parser.lexer.select_next()

        instructions = []
        while Parser.lexer.next.type != "CLOSE_BRA":
            if Parser.lexer.next.type == "EOF":
                raise ValueError("[Parser] '}' esperado para fechar bloco")
            instructions.append(Parser.parse_statement())

        Parser.lexer.select_next()  # consome '}'
        return Block("BLOCK", instructions)

    # ── Instrução ─────────────────────────────────────────────────────────────
    def parse_statement():
        tok = Parser.lexer.next

        # ── Atribuição:  var = expr;
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

        # ── Print:  println!(expr);
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

        # ── IF:  if (cond) block  [else block]
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

        # ── WHILE:  while (cond) block
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

        # ── Instrução vazia:  ;
        if tok.type == "END":
            Parser.lexer.select_next()
            return NoOp()

        raise ValueError(f"[Parser] Instrucao invalida, token: {tok.type} = '{tok.value}'")

    # ── Expressão booleana:  boolTerm (|| boolTerm)* ─────────────────────────
    def parse_bool_expression():
        result = Parser.parse_bool_term()

        while Parser.lexer.next.type == "OR":
            Parser.lexer.select_next()
            result = BinOp("||", [result, Parser.parse_bool_term()])

        return result

    # ── Termo booleano:  relExpr (&& relExpr)* ───────────────────────────────
    def parse_bool_term():
        result = Parser.parse_rel_expression()

        while Parser.lexer.next.type == "AND":
            Parser.lexer.select_next()
            result = BinOp("&&", [result, Parser.parse_rel_expression()])

        return result

    # ── Expressão relacional:  expr [(== | > | <) expr] ──────────────────────
    def parse_rel_expression():
        result = Parser.parse_expression()

        if Parser.lexer.next.type in ("EQ", "GT", "LT"):
            op_map = {"EQ": "==", "GT": ">", "LT": "<"}
            op = op_map[Parser.lexer.next.type]
            Parser.lexer.select_next()
            result = BinOp(op, [result, Parser.parse_expression()])

        return result

    # ── Expressão aritmética:  term ((+ | - | ^) term)* ──────────────────────
    def parse_expression():
        result = Parser.parse_term()

        while Parser.lexer.next.type in ("PLUS", "MINUS", "XOR"):
            op_tok = Parser.lexer.next.type
            Parser.lexer.select_next()
            op_map = {"PLUS": "+", "MINUS": "-", "XOR": "^"}
            result = BinOp(op_map[op_tok], [result, Parser.parse_term()])

        return result

    # ── Termo aritmético:  factor ((* | /) factor)* ──────────────────────────
    def parse_term():
        result = Parser.parse_factor()

        while Parser.lexer.next.type in ("MUL", "DIV"):
            op_tok = Parser.lexer.next.type
            Parser.lexer.select_next()
            op_map = {"MUL": "*", "DIV": "/"}
            result = BinOp(op_map[op_tok], [result, Parser.parse_factor()])

        return result

    # ── Fator ─────────────────────────────────────────────────────────────────
    def parse_factor():
        tok = Parser.lexer.next

        # Inteiro literal
        if tok.type == "INT":
            Parser.lexer.select_next()
            return IntVal(tok.value, [])

        # Identificador
        if tok.type == "IDEN":
            Parser.lexer.select_next()
            return Identifier(tok.value, [])

        # Unário positivo
        if tok.type == "PLUS":
            Parser.lexer.select_next()
            return UnOp("+", [Parser.parse_factor()])

        # Unário negativo
        if tok.type == "MINUS":
            Parser.lexer.select_next()
            return UnOp("-", [Parser.parse_factor()])

        # NOT lógico
        if tok.type == "NOT":
            Parser.lexer.select_next()
            return UnOp("!", [Parser.parse_factor()])

        # Leitura do terminal
        if tok.type == "READ":
            Parser.lexer.select_next()
            return Read("READ", [])

        # Expressão entre parênteses
        if tok.type == "OPEN_PAR":
            Parser.lexer.select_next()
            result = Parser.parse_bool_expression()
            if Parser.lexer.next.type != "CLOSE_PAR":
                raise ValueError("[Parser] ')' esperado para fechar parenteses")
            Parser.lexer.select_next()
            return result

        raise ValueError(f"[Parser] Token invalido em parse_factor: {tok.type} = '{tok.value}'")

    # ── Ponto de entrada ──────────────────────────────────────────────────────
    def run(code):
        Parser.lexer = Lexer(code)
        Parser.lexer.select_next()
        tree = Parser.parse_program()

        if Parser.lexer.next.type != "EOF":
            raise ValueError("[Parser] EOF esperado no final do programa")

        return tree


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        raise ValueError("[Main] Caminho do arquivo de entrada nao informado")

    input_path = sys.argv[1]
    with open(input_path, "r", encoding="utf-8") as f:
        source_code = f.read() + "\n"

    filtered_code = PrePro.filter(source_code)
    tree = Parser.run(filtered_code)
    st   = SymbolTable()
    tree.evaluate(st)


if __name__ == "__main__":
    main()
