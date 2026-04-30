# lingpar

[![Compilation Status](https://compiler-tester.insper-comp.com.br/svg/NicolasVolf/lingpar)](https://compiler-tester.insper-comp.com.br/svg/NicolasVolf/lingpar)



Diagrama sintático que define a gramática das expressões matemáticas suportadas por este projeto:

![Diagrama Sintático da Expressão](Screenshot_1.png)

```ebnf

PROGRAM = { STATEMENT } ;
STATEMENT = ((IF, "(", BOOLEXPRESSION, ")", BLOCK, ("ELSE", BLOCK) | ε) | (WHILE, "(", BOOLEXPRESSION, ")", BLOCK) | (FOR, "(", IDENTIFIER, "=", BOOLEXPRESSION, ";", BOOLEXPRESSION, ";", IDENTIFIER, "=", BOOLEXPRESSION, ")", BLOCK) | (IDENTIFIER, "=", BOOLEXPRESSION) | (PRINT, "(", BOOLEXPRESSION, ")") | ε), EOL ;
BOOLEXPRESSION = BOOLTERM, { "||", BOOLTERM } ;
BOOLTERM = RELEXPRESSION, { "&&", RELEXPRESSION } ;
RELEXPRESSION = EXPRESSION, ("==" | "<" | ">"), EXPRESSION ;
EXPRESSION = TERM, { ("+" | "-"), TERM } ;
TERM = FACTOR, { ("*" | "/"), FACTOR } ;
FACTOR = ("+" | "-"), FACTOR | "(", BOOLEXPRESSION, ")" | NUMBER | READ, "(", ")" | IF, BOOLEXPRESSION, EXPRBLOCK, ELSE, EXPRBLOCK ;
BLOCK = "{", { STATEMENT }, "}" ;
EXPRBLOCK = "{", BOOLEXPRESSION, "}" ;
NUMBER = DIGIT, {DIGIT} ;
DIGIT = 0 | 1 | ... | 9 ;
IDENTIFIER = LETTER, {LETTER | DIGIT | "_"} ;
LETTER = a | b | ... | z | A | B | ... | Z ;

```
