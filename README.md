# lingpar

[![Compilation Status](https://compiler-tester.insper-comp.com.br/svg/NicolasVolf/lingpar)](https://compiler-tester.insper-comp.com.br/svg/NicolasVolf/lingpar)



Diagrama sintático que define a gramática das expressões matemáticas suportadas por este projeto:

![Diagrama Sintático da Expressão](imgcomp.png)

```ebnf

EXPRESSION = TERM, { ("+" | "-"), TERM } ;
TERM = FACTOR, { ("*" | "/"), FACTOR } ;
FACTOR = ("+" | "-"), FACTOR | "(", EXPRESSION, ")" | NUMBER ;
NUMBER = DIGIT, {DIGIT} ;
DIGIT = 0 | 1 | ... | 9 ;

```