import sys
import re
import os
from typing import Dict


class Code:
    instructions = []

    @staticmethod
    def append(code):
        Code.instructions.append(code)

    @staticmethod
    def dump(filename):
        header = (
            "section .data\n"
            '  format_out: db "%d", 10, 0\n'
            '  format_in: db "%d", 0\n'
            "  scan_int: dd 0\n"
            "\n"
            "section .text\n"
            "  extern printf\n"
            "  extern scanf\n"
            "  global _start\n"
            "\n"
            "_start:\n"
            "  push ebp\n"
            "  mov ebp, esp\n"
            "\n"
        )
        footer = (
            "\n  mov esp, ebp\n  pop ebp\n\n  mov eax, 1\n  xor ebx, ebx\n  int 0x80\n"
        )
        with open(filename, "w") as f:
            f.write(header)
            f.write("\n".join(Code.instructions))
            f.write(footer)


class Token:
    def __init__(self, token_type, value):
        self.type = token_type
        self.value = value


class Variable:
    def __init__(
        self,
        value,
        var_type: str,
        is_mutable: bool = False,
        shift=None,
        is_function: bool = False,
    ):
        self.value = value
        self.type = var_type
        self.is_mutable = is_mutable
        self.shift = shift
        self.is_function = is_function


class ReturnSignal:
    def __init__(self, value):
        self.value = value


class SymbolTable:
    def __init__(self, parent=None):
        self.table: Dict[str, Variable] = {}
        self.next_shift = 0
        self.parent = parent

    def get_value(self, name: str):
        if name in self.table:
            var = self.table[name]
            return Variable(
                var.value,
                var.type,
                var.is_mutable,
                shift=var.shift,
                is_function=var.is_function,
            )
        if self.parent is not None:
            return self.parent.get_value(name)
        raise ValueError(f"[Semantic] Variavel '{name}' nao existe")

    def create_variable(
        self,
        name: str,
        value,
        var_type: str,
        is_mutable: bool = False,
        is_function: bool = False,
    ):
        if name in self.table:
            raise ValueError(f"[Semantic] Variavel '{name}' ja foi declarada")
        if is_function:
            self.table[name] = Variable(
                value.value, var_type, is_mutable, shift=None, is_function=True
            )
            return

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
            and (
                (var_type == "i32" and type(value.value) is int)
                or (var_type == "f64" and type(value.value) is float)
                or (var_type == "bool" and type(value.value) is bool)
                or (var_type == "str" and type(value.value) is str)
            )
        )
        if not is_valid_type:
            raise ValueError(
                f"[Semantic] Tipo invalido para '{name}': esperado {var_type}, recebido {value.type}"
            )
        self.next_shift += 4
        self.table[name] = Variable(
            value.value, var_type, is_mutable, shift=self.next_shift, is_function=False
        )

    def set_value(self, name: str, value):
        if name not in self.table:
            if self.parent is not None:
                self.parent.set_value(name, value)
                return
            raise ValueError(f"[Semantic] Variavel '{name}' nao foi declarada")

        variable = self.table[name]
        if variable.is_function:
            raise ValueError(
                f"[Semantic] '{name}' e uma funcao e nao pode receber atribuicao"
            )
        if not variable.is_mutable:
            raise ValueError(f"[Semantic] Variavel '{name}' nao e mutavel")

        is_valid_type = (
            isinstance(value, Variable)
            and value.type == variable.type
            and (
                (variable.type == "i32" and type(value.value) is int)
                or (variable.type == "f64" and type(value.value) is float)
                or (variable.type == "bool" and type(value.value) is bool)
                or (variable.type == "str" and type(value.value) is str)
            )
        )
        if not is_valid_type:
            raise ValueError(
                f"[Semantic] Tipo invalido para '{name}': esperado {variable.type}, recebido {value.type}"
            )

        variable.value = value.value


class Node:
    id = 0

    @staticmethod
    def new_id():
        Node.id += 1
        return Node.id

    def __init__(self, value, children=None):
        self.value = value
        self.children = children if children is not None else []
        self.id = Node.new_id()

    def evaluate(self, st):
        pass

    def generate(self, st):
        pass


class IntVal(Node):
    def evaluate(self, st):
        return Variable(self.value, "i32")

    def generate(self, st):
        Code.append(f"  mov eax, {self.value}")


class BoolVal(Node):
    def evaluate(self, st):
        return Variable(self.value, "bool")

    def generate(self, st):
        Code.append(f"  mov eax, {1 if self.value else 0}")


class StringVal(Node):
    def evaluate(self, st):
        return Variable(self.value, "str")

    def generate(self, st):
        pass


class Identifier(Node):
    def evaluate(self, st):
        return st.get_value(self.value)

    def generate(self, st):
        shift = st.get_value(self.value).shift
        Code.append(f"  mov eax, [ebp-{shift}]")


class UnOp(Node):
    def evaluate(self, st):
        child_val = self.children[0].evaluate(st)
        if self.value == "+":
            if child_val.type not in ("i32", "f64"):
                raise ValueError("[Semantic] Operador '+' unario exige i32 ou f64")
            return Variable(+child_val.value, child_val.type)
        if self.value == "-":
            if child_val.type not in ("i32", "f64"):
                raise ValueError("[Semantic] Operador '-' unario exige i32 ou f64")
            return Variable(-child_val.value, child_val.type)
        if self.value == "!":
            if child_val.type != "bool":
                raise ValueError("[Semantic] Operador '!' exige bool")
            return Variable(not child_val.value, "bool")
        raise ValueError(f"[Semantic] Operador unario invalido: {self.value}")

    def generate(self, st):
        self.children[0].generate(st)
        if self.value == "-":
            Code.append("  neg eax")
        elif self.value == "!":
            Code.append("  xor eax, 1")


class BinOp(Node):
    def evaluate(self, st):
        left = self.children[0].evaluate(st)
        right = self.children[1].evaluate(st)

        def stringify(var):
            if var.type == "bool":
                return "true" if var.value else "false"
            return str(var.value)

        def both_numeric(a, b):
            return a.type in ("i32", "f64") and b.type in ("i32", "f64")

        def promoted_numeric_type(a, b):
            if a.type == "f64" or b.type == "f64":
                return "f64"
            return "i32"

        if self.value == "+":
            if both_numeric(left, right):
                result_type = promoted_numeric_type(left, right)
                return Variable(left.value + right.value, result_type)
            if left.type == "str" or right.type == "str":
                return Variable(stringify(left) + stringify(right), "str")
            raise ValueError(
                "[Semantic] Operador '+' exige numeros ou concatenacao com str"
            )
        if self.value == "-":
            if both_numeric(left, right):
                result_type = promoted_numeric_type(left, right)
                return Variable(left.value - right.value, result_type)
            raise ValueError("[Semantic] Operador '-' exige i32 ou f64")
        if self.value == "*":
            if both_numeric(left, right):
                result_type = promoted_numeric_type(left, right)
                return Variable(left.value * right.value, result_type)
            raise ValueError("[Semantic] Operador '*' exige i32 ou f64")
        if self.value == "/":
            if not both_numeric(left, right):
                raise ValueError("[Semantic] Operador '/' exige i32 ou f64")
            if right.value == 0:
                raise ValueError("[Semantic] Divisao por zero")
            if left.type == "i32" and right.type == "i32":
                return Variable(left.value // right.value, "i32")
            return Variable(left.value / right.value, "f64")
        if self.value == "^":
            if left.type == "i32" and right.type == "i32":
                return Variable(left.value ^ right.value, "i32")
            raise ValueError("[Semantic] Operador '^' exige i32")
        if self.value == "==":
            if both_numeric(left, right):
                return Variable(left.value == right.value, "bool")
            if left.type != right.type:
                raise ValueError("[Semantic] Operador '==' exige tipos iguais")
            return Variable(left.value == right.value, "bool")
        if self.value == ">":
            if both_numeric(left, right):
                return Variable(left.value > right.value, "bool")
            if left.type == "str" and right.type == "str":
                return Variable(left.value > right.value, "bool")
            raise ValueError("[Semantic] Operador '>' exige i32/f64 ou str")
        if self.value == "<":
            if both_numeric(left, right):
                return Variable(left.value < right.value, "bool")
            if left.type == "str" and right.type == "str":
                return Variable(left.value < right.value, "bool")
            raise ValueError("[Semantic] Operador '<' exige i32/f64 ou str")
        if self.value == "&&":
            if left.type == "bool" and right.type == "bool":
                return Variable(left.value and right.value, "bool")
            raise ValueError("[Semantic] Operador '&&' exige bool")
        if self.value == "||":
            if left.type == "bool" and right.type == "bool":
                return Variable(left.value or right.value, "bool")
            raise ValueError("[Semantic] Operador '||' exige bool")
        raise ValueError(f"[Semantic] Operador binario invalido: {self.value}")

    def generate(self, st):
        self.children[1].generate(st)
        Code.append("  push eax")
        self.children[0].generate(st)
        Code.append("  pop ecx")
        op = self.value
        if op == "+":
            Code.append("  add eax, ecx")
        elif op == "-":
            Code.append("  sub eax, ecx")
        elif op == "*":
            Code.append("  imul ecx")
        elif op == "/":
            Code.append("  cdq")
            Code.append("  idiv ecx")
        elif op == "^":
            Code.append("  xor eax, ecx")
        elif op == "==":
            Code.append("  cmp eax, ecx")
            Code.append("  mov eax, 0")
            Code.append("  mov ecx, 1")
            Code.append("  cmove eax, ecx")
        elif op == "<":
            Code.append("  cmp eax, ecx")
            Code.append("  mov eax, 0")
            Code.append("  mov ecx, 1")
            Code.append("  cmovl eax, ecx")
        elif op == ">":
            Code.append("  cmp eax, ecx")
            Code.append("  mov eax, 0")
            Code.append("  mov ecx, 1")
            Code.append("  cmovg eax, ecx")
        elif op == "&&":
            Code.append("  and eax, ecx")
        elif op == "||":
            Code.append("  or eax, ecx")


class Print(Node):
    def evaluate(self, st):
        value = self.children[0].evaluate(st)
        if value.type == "bool":
            print("true" if value.value else "false")
            return
        print(value.value)

    def generate(self, st):
        self.children[0].generate(st)
        Code.append("  push eax")
        Code.append("  push format_out")
        Code.append("  call printf")
        Code.append("  add esp, 8")


class Assignment(Node):
    def evaluate(self, st):
        var_name = self.children[0].value
        val = self.children[1].evaluate(st)
        st.set_value(var_name, val)

    def generate(self, st):
        self.children[1].generate(st)
        name = self.children[0].value
        shift = st.get_value(name).shift
        Code.append(f"  mov [ebp-{shift}], eax")


class VarDec(Node):
    def evaluate(self, st):
        var_name = self.children[0].value
        value = None
        if len(self.children) == 2:
            value = self.children[1].evaluate(st)
        is_mutable = getattr(self, "is_mutable", False)
        st.create_variable(var_name, value, self.value, is_mutable, is_function=False)

    def generate(self, st):
        var_name = self.children[0].value
        is_mutable = getattr(self, "is_mutable", False)
        st.create_variable(var_name, None, self.value, is_mutable, is_function=False)
        Code.append(f"  sub esp, 4 ; var {var_name} {self.value}")
        if len(self.children) == 2:
            self.children[1].generate(st)
            shift = st.get_value(var_name).shift
            Code.append(f"  mov [ebp-{shift}], eax")


class Return(Node):
    def evaluate(self, st):
        return ReturnSignal(self.children[0].evaluate(st))

    def generate(self, st):
        pass


class FuncDec(Node):
    def evaluate(self, st):
        root = st
        while root.parent is not None:
            root = root.parent

        func_name = self.children[0].value
        root.create_variable(
            func_name,
            Variable(self, self.value),
            self.value,
            is_mutable=False,
            is_function=True,
        )

    def generate(self, st):
        pass


class FuncCall(Node):
    def evaluate(self, st):
        func_name = self.value
        try:
            func_var = st.get_value(func_name)
        except ValueError:
            raise ValueError(f"[Semantic] Funcao '{func_name}' nao foi declarada")

        if not func_var.is_function:
            raise ValueError(f"[Semantic] '{func_name}' nao e uma funcao")

        func_node = func_var.value
        params = func_node.children[1:-1]
        func_block = func_node.children[-1]

        if len(self.children) != len(params):
            raise ValueError(
                f"[Semantic] Funcao '{func_name}' esperava {len(params)} argumento(s), recebeu {len(self.children)}"
            )

        root = st
        while root.parent is not None:
            root = root.parent
        call_st = SymbolTable(parent=root)

        for param_node, arg_node in zip(params, self.children):
            param_name = param_node.children[0].value
            arg_value = arg_node.evaluate(st)
            call_st.create_variable(
                param_name,
                arg_value,
                param_node.value,
                is_mutable=False,
                is_function=False,
            )

        return_signal = func_block.evaluate(call_st)
        expected_type = func_node.value

        if expected_type == "unit":
            if return_signal is not None:
                raise ValueError(
                    f"[Semantic] Funcao '{func_name}' e unit e nao deve retornar valor"
                )
            return Variable(None, "unit")

        if return_signal is None:
            raise ValueError(
                f"[Semantic] Funcao '{func_name}' deve retornar valor do tipo {expected_type}"
            )

        return_value = return_signal.value

        if return_value.type != expected_type:
            raise ValueError(
                f"[Semantic] Retorno invalido em '{func_name}': esperado {expected_type}, recebido {return_value.type}"
            )

        return return_value

    def generate(self, st):
        pass


class Block(Node):
    def evaluate(self, st):
        for child in self.children:
            if isinstance(child, Block):
                nested_st = SymbolTable(parent=st)
                result = child.evaluate(nested_st)
            else:
                result = child.evaluate(st)

            if isinstance(result, ReturnSignal):
                return result

    def generate(self, st):
        for child in self.children:
            child.generate(st)


class If(Node):
    def evaluate(self, st):
        condition = self.children[0].evaluate(st)
        if condition.type != "bool":
            raise ValueError("[Semantic] Condicao do if deve ser bool")
        if condition.value:
            result = self.children[1].evaluate(st)
            if isinstance(result, ReturnSignal):
                return result
        elif len(self.children) == 3:
            result = self.children[2].evaluate(st)
            if isinstance(result, ReturnSignal):
                return result

    def generate(self, st):
        nid = self.id
        self.children[0].generate(st)
        Code.append("  cmp eax, 0")
        if len(self.children) == 3:
            Code.append(f"  je else_{nid}")
            self.children[1].generate(st)
            Code.append(f"  jmp exit_{nid}")
            Code.append(f"  else_{nid}:")
            self.children[2].generate(st)
            Code.append(f"  exit_{nid}:")
        else:
            Code.append(f"  je exit_{nid}")
            self.children[1].generate(st)
            Code.append(f"  exit_{nid}:")


class While(Node):
    def evaluate(self, st):
        while True:
            condition = self.children[0].evaluate(st)
            if condition.type != "bool":
                raise ValueError("[Semantic] Condicao do while deve ser bool")
            if not condition.value:
                break
            result = self.children[1].evaluate(st)
            if isinstance(result, ReturnSignal):
                return result

    def generate(self, st):
        nid = self.id
        Code.append(f"  loop_{nid}:")
        self.children[0].generate(st)
        Code.append("  cmp eax, 0")
        Code.append(f"  je exit_{nid}")
        self.children[1].generate(st)
        Code.append(f"  jmp loop_{nid}")
        Code.append(f"  exit_{nid}:")


class Read(Node):
    def evaluate(self, st):
        try:
            return Variable(int(input()), "i32")
        except ValueError:
            raise ValueError("[Semantic] scanln! esperava um inteiro")

    def generate(self, st):
        Code.append("  push scan_int")
        Code.append("  push format_in")
        Code.append("  call scanf")
        Code.append("  add esp, 8")
        Code.append("  mov eax, dword [scan_int]")


class NoOp(Node):
    def evaluate(self, st):
        return None

    def generate(self, st):
        pass


class PrePro:
    @staticmethod
    def filter(source_code):
        return re.sub(r"//[^\n]*", "", source_code)


class Lexer:
    RESERVED_WORDS = {
        "println!": "PRINT",
        "scanln!": "READ",
        "if": "IF",
        "else": "ELSE",
        "while": "WHILE",
        "let": "LET",
        "mut": "MUT",
        "fn": "FUNC",
        "return": "RETURN",
        "true": "BOOL",
        "false": "BOOL",
        "str": "TYPE",
        "i32": "TYPE",
        "f64": "TYPE",
        "bool": "TYPE",
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

        if char == "+":
            self.next = Token("PLUS", "+")
            self.position += 1
        elif char == "-":
            if (
                self.position + 1 < len(self.source)
                and self.source[self.position + 1] == ">"
            ):
                self.next = Token("ARROW", "->")
                self.position += 2
            else:
                self.next = Token("MINUS", "-")
                self.position += 1
        elif char == "*":
            self.next = Token("MUL", "*")
            self.position += 1
        elif char == "/":
            self.next = Token("DIV", "/")
            self.position += 1
        elif char == "^":
            self.next = Token("XOR", "^")
            self.position += 1
        elif char == "(":
            self.next = Token("OPEN_PAR", "(")
            self.position += 1
        elif char == ")":
            self.next = Token("CLOSE_PAR", ")")
            self.position += 1
        elif char == "{":
            self.next = Token("OPEN_BRA", "{")
            self.position += 1
        elif char == "}":
            self.next = Token("CLOSE_BRA", "}")
            self.position += 1
        elif char == ";":
            self.next = Token("END", ";")
            self.position += 1
        elif char == ",":
            self.next = Token("COMMA", ",")
            self.position += 1
        elif char == ":":
            self.next = Token("COLON", ":")
            self.position += 1
        elif char == ">":
            self.next = Token("GT", ">")
            self.position += 1
        elif char == "<":
            self.next = Token("LT", "<")
            self.position += 1
        elif char == "=":
            if (
                self.position + 1 < len(self.source)
                and self.source[self.position + 1] == "="
            ):
                self.next = Token("EQ", "==")
                self.position += 2
            else:
                self.next = Token("ASSIGN", "=")
                self.position += 1
        elif char == "&":
            if (
                self.position + 1 < len(self.source)
                and self.source[self.position + 1] == "&"
            ):
                self.next = Token("AND", "&&")
                self.position += 2
            else:
                raise ValueError("[Lexer] '&' isolado invalido; use '&&'")
        elif char == "|":
            if (
                self.position + 1 < len(self.source)
                and self.source[self.position + 1] == "|"
            ):
                self.next = Token("OR", "||")
                self.position += 2
            else:
                raise ValueError("[Lexer] '|' isolado invalido; use '||'")
        elif char == "!":
            self.next = Token("NOT", "!")
            self.position += 1
        elif char.isdigit():
            num = char
            self.position += 1
            while (
                self.position < len(self.source)
                and self.source[self.position].isdigit()
            ):
                num += self.source[self.position]
                self.position += 1
            if self.position < len(self.source) and self.source[self.position] == ".":
                num += "."
                self.position += 1
                if (
                    self.position >= len(self.source)
                    or not self.source[self.position].isdigit()
                ):
                    raise ValueError(
                        "[Lexer] Float invalido: digitos esperados apos '.'"
                    )
                while (
                    self.position < len(self.source)
                    and self.source[self.position].isdigit()
                ):
                    num += self.source[self.position]
                    self.position += 1
                self.next = Token("FLOAT", float(num))
            else:
                self.next = Token("INT", int(num))
        elif char.isalpha() or char == "_":
            ident = char
            self.position += 1
            while self.position < len(self.source) and (
                self.source[self.position].isalnum()
                or self.source[self.position] == "_"
            ):
                ident += self.source[self.position]
                self.position += 1
            if self.position < len(self.source) and self.source[self.position] == "!":
                ident += "!"
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
            while (
                self.position < len(self.source) and self.source[self.position] != '"'
            ):
                if self.source[self.position] == "\n":
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

    @staticmethod
    def parse_var_declaration():
        if Parser.lexer.next.type != "LET":
            raise ValueError("[Parser] 'let' esperado na declaracao")
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
        declared_type = Parser.lexer.next.value
        Parser.lexer.select_next()

        children = [ident_node]
        if Parser.lexer.next.type == "ASSIGN":
            Parser.lexer.select_next()
            children.append(Parser.parse_bool_expression())

        if Parser.lexer.next.type != "END":
            raise ValueError("[Parser] ';' esperado no final da declaracao")
        Parser.lexer.select_next()

        vardec_node = VarDec(declared_type, children)
        vardec_node.is_mutable = is_mutable
        return vardec_node

    @staticmethod
    def parse_func_declaration():
        if Parser.lexer.next.type != "FUNC":
            raise ValueError("[Parser] 'fn' esperado na declaracao de funcao")
        Parser.lexer.select_next()

        if Parser.lexer.next.type != "IDEN":
            raise ValueError("[Parser] Nome da funcao esperado")
        func_name = Parser.lexer.next.value
        func_ident = Identifier(func_name, [])
        Parser.lexer.select_next()

        if Parser.lexer.next.type != "OPEN_PAR":
            raise ValueError("[Parser] '(' esperado apos nome da funcao")
        Parser.lexer.select_next()

        params = []
        if Parser.lexer.next.type != "CLOSE_PAR":
            while True:
                if Parser.lexer.next.type != "IDEN":
                    raise ValueError("[Parser] Nome de parametro esperado")
                param_name = Parser.lexer.next.value
                Parser.lexer.select_next()

                if Parser.lexer.next.type != "COLON":
                    raise ValueError("[Parser] ':' esperado em parametro")
                Parser.lexer.select_next()

                if Parser.lexer.next.type != "TYPE":
                    raise ValueError("[Parser] Tipo do parametro esperado")
                param_type = Parser.lexer.next.value
                Parser.lexer.select_next()

                param_node = VarDec(param_type, [Identifier(param_name, [])])
                param_node.is_mutable = False
                params.append(param_node)

                if Parser.lexer.next.type != "COMMA":
                    break
                Parser.lexer.select_next()

        if Parser.lexer.next.type != "CLOSE_PAR":
            raise ValueError("[Parser] ')' esperado ao final dos parametros")
        Parser.lexer.select_next()

        return_type = "unit"
        if Parser.lexer.next.type == "ARROW":
            Parser.lexer.select_next()
            if Parser.lexer.next.type == "TYPE":
                return_type = Parser.lexer.next.value
                Parser.lexer.select_next()
            elif Parser.lexer.next.type == "OPEN_PAR":
                Parser.lexer.select_next()
                if Parser.lexer.next.type != "CLOSE_PAR":
                    raise ValueError("[Parser] ')' esperado em retorno unit")
                Parser.lexer.select_next()
                return_type = "unit"
            else:
                raise ValueError("[Parser] Tipo de retorno esperado apos '->'")

        block = Parser.parse_block()
        return FuncDec(return_type, [func_ident, *params, block])

    @staticmethod
    def parse_program():
        instructions = []
        while Parser.lexer.next.type != "EOF":
            if Parser.lexer.next.type == "LET":
                instructions.append(Parser.parse_var_declaration())
            elif Parser.lexer.next.type == "FUNC":
                instructions.append(Parser.parse_func_declaration())
            else:
                raise ValueError("[Parser] Programa aceita apenas declaracoes globais")
        return Block("BLOCK", instructions)

    @staticmethod
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

    @staticmethod
    def parse_statement():
        tok = Parser.lexer.next

        if tok.type == "OPEN_BRA":
            return Parser.parse_block()

        if tok.type == "LET":
            return Parser.parse_var_declaration()

        if tok.type == "RETURN":
            Parser.lexer.select_next()
            expr = Parser.parse_bool_expression()
            if Parser.lexer.next.type != "END":
                raise ValueError("[Parser] ';' esperado apos return")
            Parser.lexer.select_next()
            return Return("RETURN", [expr])

        if tok.type == "IDEN":
            name = tok.value
            Parser.lexer.select_next()

            if Parser.lexer.next.type == "ASSIGN":
                ident_node = Identifier(name, [])
                Parser.lexer.select_next()
                expr = Parser.parse_bool_expression()
                if Parser.lexer.next.type != "END":
                    raise ValueError("[Parser] ';' esperado no final da atribuicao")
                Parser.lexer.select_next()
                return Assignment("=", [ident_node, expr])

            if Parser.lexer.next.type == "OPEN_PAR":
                Parser.lexer.select_next()
                args = []
                if Parser.lexer.next.type != "CLOSE_PAR":
                    args.append(Parser.parse_bool_expression())
                    while Parser.lexer.next.type == "COMMA":
                        Parser.lexer.select_next()
                        args.append(Parser.parse_bool_expression())
                if Parser.lexer.next.type != "CLOSE_PAR":
                    raise ValueError("[Parser] ')' esperado na chamada de funcao")
                Parser.lexer.select_next()
                if Parser.lexer.next.type != "END":
                    raise ValueError("[Parser] ';' esperado apos chamada de funcao")
                Parser.lexer.select_next()
                return FuncCall(name, args)

            raise ValueError("[Parser] '=' ou '(' esperado apos identificador")

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

        if tok.type == "FUNC":
            raise ValueError("[Parser] Nao e permitido declarar funcao dentro de bloco")

        if tok.type == "END":
            Parser.lexer.select_next()
            return NoOp("NOOP", [])

        raise ValueError(
            f"[Parser] Instrucao invalida, token: {tok.type} = '{tok.value}'"
        )

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

        if tok.type == "OPEN_PAR":
            Parser.lexer.select_next()

            if Parser.lexer.next.type == "TYPE" and Parser.lexer.next.value in (
                "i32",
                "f64",
                "bool",
                "str",
            ):
                cast_type = Parser.lexer.next.value
                Parser.lexer.select_next()
                if Parser.lexer.next.type != "CLOSE_PAR":
                    raise ValueError("[Parser] ')' esperado apos tipo de cast")
                Parser.lexer.select_next()
                return Node(cast_type, [Parser.parse_factor()])

            result = Parser.parse_bool_expression()
            if Parser.lexer.next.type != "CLOSE_PAR":
                raise ValueError("[Parser] ')' esperado para fechar parenteses")
            Parser.lexer.select_next()
            return result

        if tok.type == "INT":
            Parser.lexer.select_next()
            return IntVal(tok.value, [])

        if tok.type == "FLOAT":
            Parser.lexer.select_next()
            return Node(tok.value, [])

        if tok.type == "BOOL":
            Parser.lexer.select_next()
            return BoolVal(tok.value, [])

        if tok.type == "STR":
            Parser.lexer.select_next()
            return StringVal(tok.value, [])

        if tok.type == "IDEN":
            ident = tok.value
            Parser.lexer.select_next()
            if Parser.lexer.next.type == "OPEN_PAR":
                Parser.lexer.select_next()
                args = []
                if Parser.lexer.next.type != "CLOSE_PAR":
                    args.append(Parser.parse_bool_expression())
                    while Parser.lexer.next.type == "COMMA":
                        Parser.lexer.select_next()
                        args.append(Parser.parse_bool_expression())
                if Parser.lexer.next.type != "CLOSE_PAR":
                    raise ValueError("[Parser] ')' esperado na chamada de funcao")
                Parser.lexer.select_next()
                return FuncCall(ident, args)
            return Identifier(ident, [])

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

        raise ValueError(
            f"[Parser] Token invalido em parse_factor: {tok.type} = '{tok.value}'"
        )

    @staticmethod
    def run(code):
        Parser.lexer = Lexer(code)
        Parser.lexer.select_next()
        tree = Parser.parse_program()
        if Parser.lexer.next.type != "EOF":
            raise ValueError("[Parser] EOF esperado no final do programa")
        tree.children.append(FuncCall("main", []))
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
