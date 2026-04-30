# lingpar

[![Compilation Status](https://compiler-tester.insper-comp.com.br/svg/NicolasVolf/lingpar)](https://compiler-tester.insper-comp.com.br/svg/NicolasVolf/lingpar)



Diagrama sintatico e EBNF final (Roteiro 9):

![Diagrama Sintático da Expressão](Screenshot_1.png)

```ebnf
PROGRAM = { FUNCDEC | VARDEC } ;
FUNCDEC = "fn", IDENTIFIER, "(", ( | IDENTIFIER, ":", TYPE, { ",", IDENTIFIER, ":", TYPE }), ")", ("->", (TYPE | "(", ")") | ), BLOCK ;
VARDEC = "let", "mut", IDENTIFIER, ":", TYPE, ( | "=", BOOLEXPRESSION ), ";" ;
BLOCK = "{", { STATEMENT }, "}" ;
STATEMENT = ( | (IDENTIFIER, ("=", BOOLEXPRESSION | "(", (BOOLEXPRESSION, { ",", BOOLEXPRESSION } | ), ")")) | ("println!", "(", BOOLEXPRESSION, ")") | "return", BOOLEXPRESSION | ), ";"
          | ("if", "(", BOOLEXPRESSION, ")", STATEMENT, ( | "else", STATEMENT))
          | ("while", "(", BOOLEXPRESSION, ")", STATEMENT)
          | VARDEC
          | BLOCK ;
BOOLEXPRESSION = BOOLTERM, { "||", BOOLTERM } ;
BOOLTERM = RELEXPRESSION, { "&&", RELEXPRESSION } ;
RELEXPRESSION = EXPRESSION, {("==" | "<" | ">"), EXPRESSION} ;
EXPRESSION = TERM, { ("+" | "-"), TERM } ;
TERM = FACTOR, { ("*" | "/"), FACTOR } ;
FACTOR = NUMBER
       | STRING
       | BOOLEAN
       | IDENTIFIER, ("(", (BOOLEXPRESSION, { ",", BOOLEXPRESSION } | ), ")" | )
       | ("+" | "-" | "!"), FACTOR
       | "(", BOOLEXPRESSION, ")"
       | "scanln!", "(", ")" ;
TYPE = "i32" | "str" | "bool" ;
NUMBER = DIGIT, { DIGIT } ;
IDENTIFIER = LETTER, {LETTER | DIGIT | "_"} ;
STRING = '"..."' ;
DIGIT = "0" | "..." | "9" ;
LETTER = "a" | "..." | "z" | "A" | "..." | "Z" ;
BOOLEAN = "true" | "false" ;

```
