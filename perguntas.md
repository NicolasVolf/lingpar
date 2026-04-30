---

## Roteiro 6

**Q1. Por que `||` é parseado em `parse_bool_expression` e `&&` em `parse_bool_term`?**
`&&` tem maior precedência que `||`. Na gramática descendente recursiva, maior precedência = mais fundo na hierarquia de chamadas. `parse_bool_expression` chama `parse_bool_term`, então `&&` é sempre agrupado dentro de um operando de `||`. Se invertêssemos, `a && b || c` viraria `a && (b || c)` em vez de `(a && b) || c` — semântica errada.

---

**Q2. Por que `If` foi modelado com número variável de filhos (2 ou 3) em vez de sempre 3 com um `else` vazio?**
Com filhos sempre-3 seria necessário criar um `NoOp` como terceiro filho toda vez que não há `else`. Isso: (a) polui o AST com nós sem sentido, (b) obrigaria o `generate()` a emitir labels e um `jmp` extra mesmo quando não há código no else. Na gramática EBNF: `[ "else" Block ]` vs `"else" Block` — a versão opcional elimina um token obrigatório desnecessário. No `generate()`, a verificação `len(self.children) == 3` decide se emite `je else_N + bloco + jmp exit_N` ou apenas `je exit_N`. Isso afeta **tanto o AST quanto o NASM**: a versão com NoOp obrigatório emitiria instruções de salto extras mesmo para if-sem-else.

Em resumo, modelar com filhos opcionais simplifica a semântica (não há `NoOp` para avaliar no caminho do else ausente) e a geração de código (não há salto morto que pule um else inexistente). A árvore reflete exatamente o que o programa expressa.

---

**Q3. Se o lexer não tratasse `scanln!` como palavra reservada, o que aconteceria?**
O lexer separaria `scanln` e `!` em dois tokens distintos (identificador + operador). A construção `scanln!(...)` perderia a representação unificada e o token reservado READ nunca seria produzido. Sem READ, o parser nunca chegaria na regra que cria o nó `Read` — a leitura de terminal simplesmente deixaria de existir como construção da linguagem. O erro não é sintático no sentido estrito: é a **ausência** de uma construção, não uma forma inválida dela.

---

**Q4. Desenhe a AST da condição `i < n || i == n`**
```
BinOp("||")
├── BinOp("<")
│   ├── Identifier("i")
│   └── Identifier("n")
└── BinOp("==")
    ├── Identifier("i")
    └── Identifier("n")
```
`||` fica no nível de `BoolExpression`, `<` e `==` ficam em `RelExpression` (mais interno = maior precedência). O nó `||` só é criado depois que ambos os operandos de `<` e `==` são completamente parseados.

---

## Roteiro 7

**Q5. Se unificássemos `create_variable` e `set_value` em um único `put(name, value)`, quais validações seriam perdidas?**
Três validações ficariam ambíguas:
- **"Variável já declarada"** — `put` não saberia distinguir primeira criação de re-declaração. Errado classificar: **semântico** (a sintaxe `let x: i32 = 1; let x: i32 = 2;` é sintaticamente válida).
- **"Variável não declarada"** — `put` criaria a variável em qualquer chamada, eliminando o erro. Também **semântico**.
- **"Variável não mutável"** — a mutabilidade é definida na criação; um `put` unificado precisaria de lógica extra para saber se é a primeira chamada. **Semântico**.

Isso afeta **o R8**: `create_variable` é quem incrementa `next_shift` e atribui `shift` à `Variable`. Se unificássemos, teríamos que decidir se `put` sempre aloca espaço na pilha (errado: reatribuição não precisa de novo espaço) ou nunca (errado: declarações precisam). O layout da pilha quebraria.

---

**Q6. O que o compilador faz com `let x: i32 = true;`?**
O conflito — tipo declarado `i32` vs valor `bool` — só é visível na fase **semântica**, porque é lá que as duas informações se encontram pela primeira vez: o parser armazenou o tipo declarado no nó `VarDec`, e o `evaluate` do filho direito produziu um `Variable` com campo `.type`. Antes disso, nenhuma fase tem as duas pontas: o lexer só vê tokens isolados (`TYPE("i32")`, `BOOL("true")`), o parser produz a árvore sem executar expressões. A verificação é semântica por **dependência de informação**, não por escolha arbitrária — ela só pode acontecer quando tipo declarado e tipo avaliado coexistem no mesmo escopo de execução.

---

**Q7. A verificação `is_mutable` é feita em `set_value` (fase semântica). Poderia ser detectada antes?**
- **Fase léxica:** impossível. O lexer vê apenas caracteres. `x` é sempre IDEN — o lexer não sabe se foi declarado com `mut`.
- **Fase sintática:** impossível. O parser vê `IDEN = expr;` — sintaxe válida independentemente de mutabilidade. O parser não consulta a SymbolTable.
- **Fase semântica:** sim, e é exatamente onde acontece (`set_value`, linha 105). Só lá temos acesso ao campo `is_mutable` da `Variable` armazenada.

Rust real detecta isso em tempo de compilação (como nosso `evaluate`/`generate`). Python detecta em tempo de execução. Nosso compilador é **estático**: o erro para antes de o programa compilado rodar, o que é mais seguro. Esse tipo de verificação antecipada é o principal benefício de um compilador com análise semântica.

---

**Q8. Na expressão `1 + "a"`, qual método decide o que fazer e como chega à conclusão de concatenação?**
`BinOp.evaluate()` decide (linha 220). Ele avalia ambos os filhos e obtém `Variable(1, "i32")` e `Variable("a", "str")`. Então verifica em ordem:
1. `both_numeric(left, right)` → falso (`"str"` não é numérico)
2. `left.type == "str" or right.type == "str"` → verdadeiro (direito é `"str"`)

Conclui: concatenação. Chama `stringify(1)` → `"1"` e retorna `Variable("1a", "str")`. A ordem das verificações importa: se testássemos str antes de numeric, `"a" + 1.0` poderia ser ambíguo, mas a gramática atual trata qualquer `str` + qualquer coisa como concatenação.

---

**Q9. Se `BoolVal.evaluate` retornasse `True`/`False` (Python puro) em vez de `Variable`, em que fase o compilador quebraria?**
Quebraria na **fase semântica**, toda vez que um nó-pai tentasse inspecionar o tipo do valor recebido. O contrato entre nós da AST é: *"`evaluate` devolve um objeto que carrega valor **e** tipo"*. Esse contrato é usado por quem precisa decidir compatibilidade — o avaliador de `&&` precisa confirmar `bool`, o avaliador do `if` precisa confirmar que a condição é booleana, a atribuição precisa casar tipo com variável. Se o retorno perder o campo de tipo, nada disso pode ser verificado.

O ponto importante: o código-fonte permanece lexicamente e sintaticamente correto. O que quebra é o **protocolo interno da árvore**, não o programa do usuário. Isso ilustra por que a fase semântica precisa de uma representação uniforme de valores — sem ela, cada operador teria que reinspecionar o Python nativo e recriar a noção de tipo do zero. A uniformidade do retorno é o que permite compor nós livremente.

---

## Roteiro 8

**Q10. Por que o `BinOp` gera o filho direito primeiro?**
Para operações não-comutativas como `-`, precisamos de `EAX = esquerdo` e `ECX = direito` antes de `sub eax, ecx`. Com **direito primeiro**:
1. Direito (3) → EAX = 3; `push eax` → pilha: [3]
2. Esquerdo (10) → EAX = 10; `pop ecx` → ECX = 3
3. `sub eax, ecx` → EAX = 10 - 3 = 7 ✓

Com **esquerdo primeiro** (ordem invertida):
1. Esquerdo (10) → EAX = 10; `push eax` → pilha: [10]
2. Direito (3) → EAX = 3; `pop ecx` → ECX = 10
3. `sub eax, ecx` → EAX = 3 - 10 = -7 ✗

A pilha funciona como memória temporária para o operando que ainda não está sendo computado.

---

**Q11. Por que qualquer gerador de código precisa de identificadores únicos por estrutura de controle? `Node.id` é local ou um padrão geral?**
O problema é universal: uma instrução `jmp` ou `goto` precisa de um alvo. Se dois blocos `while` declaram `loop:`, o montador/linker não sabe para qual `loop:` saltar — ambiguidade fatal. Isso não é limitação do NASM; é inerente a qualquer sequência plana de instruções com saltos.

Outras plataformas resolvem de formas diferentes:
- **JVM bytecode**: usa offsets numéricos (`goto 42` = salte para instrução #42). Não há labels de string — a posição no array de bytecodes é o identificador.
- **LLVM IR**: usa blocos básicos com nomes únicos (`%then.1:`, `%exit.1:`), gerados por contadores internos do compilador — análogo ao `Node.id`.
- **WebAssembly**: elimina o problema com fluxo estruturado (`if/block/loop` aninhados, `br` com índice de profundidade). Nenhum label necessário.

`Node.id` é uma **implementação local de uma necessidade universal**. O padrão geral é: identificadores únicos para alvos de salto, seja via string+contador (nosso caso e LLVM), offset numérico (JVM), ou estrutura hierárquica (Wasm).

---

**Q12. Por que `next_shift` cresce em passos de 4 bytes? O que mudaria com `f64`?**
O passo de 4 bytes reflete o **tamanho do tipo armazenado** — `i32` = 32 bits = 4 bytes. O princípio que generaliza: o tamanho da célula na pilha é determinado pelo tipo, e o tipo determina também qual instrução de movimentação é usada (em x86 32-bit, `mov` para i32; em outras arquiteturas, a instrução correspondente ao tipo).

Com `f64` (8 bytes), a SymbolTable precisaria guardar o tamanho (não apenas o tipo), e `VarDec.generate` teria que consultar esse tamanho em vez de escrever `4` literal. Além disso, `Identifier.generate` e `Assignment.generate` precisariam escolher a instrução correta para o tipo (`movsd` para f64, `mov` para i32).

A decisão vive no **back-end** porque é ele que conhece a representação física; o front-end lida apenas com o tipo abstrato. É por isso que adicionar `f64` muda `generate` e a parte de alocação da SymbolTable, mas não toca em Lexer, Parser, AST, nem `evaluate`.

---

**Q13. Explique `cmp eax, 0` + `je exit_33`**
`cmp eax, 0` subtrai 0 de EAX e seta as flags de status (sem alterar EAX). Se EAX = 0 (falso), a flag ZF = 1. `je exit_33` ("jump if equal") salta se ZF = 1, ou seja, se EAX == 0. Como booleanos são representados como 0 (falso) ou 1 (verdadeiro), o salto ocorre **exatamente quando a condição é falsa** — pulando o corpo do loop/if. Quando a condição é verdadeira (EAX = 1), ZF = 0, não há salto, e o corpo é executado.

---

**Q14. A ordem de emissão em `VarDec.generate` é: (1) `create_variable`, (2) `sub esp, 4`, (3) gerar valor → EAX, (4) `mov [ebp-shift], eax`. Justifique cada dependência de ordem.**
As 4 etapas preservam três invariantes que compõem a correção:

**(i) Invariante da SymbolTable**: qualquer acesso a `shift` exige que a variável já esteja registrada. Passo 1 antes de 4 garante isso — inverter produziria erro de "variável não encontrada" no próprio código gerado pelo compilador.

**(ii) Invariante da pilha**: o slot da variável deve existir antes que outras operações mexam em `esp`. Passo 2 antes de 3 protege o slot de ser sobrescrito por pushes/pops internos à avaliação do valor — especialmente relevante quando o valor envolve chamadas que usam a pilha, como `printf`/`scanf`.

**(iii) Invariante do registrador**: EAX deve conter o valor correto no momento do armazenamento. Passo 3 antes de 4 é o que garante isso — caso contrário, o `mov [ebp-shift], eax` grava o EAX deixado pela instrução anterior.

A ordem, portanto, não é convenção estética — é uma **cadeia de pré-condições** entre três estruturas de estado diferentes (tabela, pilha, registrador). É o mesmo tipo de raciocínio que valida a ordem de execução em qualquer pipeline com estado compartilhado.

---

**Q15. O contrato "EAX é o registrador de retorno" não está escrito em nenhuma checagem. Como é garantido e o que quebraria se um filho o violasse?**
O contrato é **garantido por convenção de chamada**, não por verificação. Todo nó que emite código termina deixando o resultado da sua sub-expressão no mesmo lugar acordado (o registrador de retorno). Os nós-pai, por sua vez, assumem esse lugar sem checar. É um acordo coletivo: cada rotina cumpre a sua parte, e cada consumidor confia que as rotinas cumpriram.

Se um filho violasse o acordo — devolvesse o resultado em outro registrador —, o efeito seria **silencioso e propagado**. O montador não reclama: instruções como `sub` e `add` operam sobre registradores de verdade; se um deles contém lixo, o cálculo prossegue com lixo. O erro só aparece como resultado errado em tempo de execução, sem nenhum aviso de tradução.

Conceitualmente, isso é análogo a **tipos de retorno em linguagens tipadas**: em Java ou Rust, o compilador garante que uma função declarada como `int` sempre devolve `int`. Aqui a mesma garantia existe, mas é sustentada por disciplina humana em vez de um verificador. A moral de prova é: geradores de código dependem de **contratos implícitos entre rotinas** — convenção de chamada, alocação de registradores, layout de pilha. Esses contratos fazem o papel de um sistema de tipos informal; violá-los corrompe a saída sem que a cadeia de compilação perceba.

---

**Q16. Para gerar código Windows em vez de Linux, quais partes do compilador mudariam?**
Só a camada que conversa com o sistema operacional — a parte do back-end que define convenções de nomes externos, chamada de saída do programa e formato do executável gerado. Lexer, Parser, AST e avaliação semântica permanecem intactos, porque nenhum deles sabe (ou precisa saber) em qual sistema o código final vai rodar.

Esse fato revela o princípio da **separação entre front-end e back-end**: o front-end lida com a linguagem, o back-end lida com a máquina. Tudo que diz respeito a "o que o programa significa" é independente de plataforma; tudo que diz respeito a "como ele se apresenta ao SO" é dependente. Trocar o alvo é reconfigurar apenas a segunda camada.

É exatamente o modelo LLVM: o front-end (clang) traduz C++ para uma representação intermediária independente de máquina (LLVM IR), e o back-end traduz IR para x86, ARM ou RISC-V sem pedir alteração nenhuma ao front-end. Aqui é a mesma ideia em escala menor: a AST faz o papel da IR, e o gerador de NASM faz o papel do back-end de plataforma.

---

## Perguntas Integradoras

**QI1. Para `let mut i: i32 = 2;` em cada modo:**
- **R7 (interpretador):** `VarDec.evaluate(st)` avalia `IntVal(2)` → `Variable(2, "i32")`, depois chama `st.create_variable("i", Variable(2,"i32"), "i32", True)`. Cria entrada `"i" → Variable(value=2, type="i32", is_mutable=True, shift=None)` no dicionário Python da SymbolTable. Nada mais acontece — o valor existe em memória Python.
- **R8 (geração):** `VarDec.generate(st)` chama `create_variable("i", None, "i32", True)` (registra shift=4), emite `sub esp, 4 ; var i i32`, chama `IntVal(2).generate()` que emite `mov eax, 2`, e por fim emite `mov [ebp-4], eax`.

---

**QI2. Por que a SymbolTable do R8 ainda guarda o `type` de cada variável?**
O `type` é usado em `create_variable` (linha 75–91) para criar o valor default correto quando nenhum inicializador é dado (`None` → `Variable(0, "i32")` para i32, `Variable(False, "bool")` para bool, etc.). Sem isso não sabemos qual valor padrão inserir. Além disso, o `shift` só é atribuído dentro de `create_variable` — se o tipo for inválido e a criação falhar, o shift não é gerado e `get_value().shift` lançaria erro em `generate()`.

Extensão: se a linguagem tivesse `f64`, o `type` precisaria ser consultado em `generate()` também para escolher a instrução correta (`fadd` vs `add`, `movsd` vs `mov`). Hoje o Assembly gerado é sempre de inteiros — `type` em `generate()` seria necessário apenas se houvesse instruções distintas por tipo.

---

**QI3. Adicionando `for (i=0; i<n; i=i+1) {...}` ao R6:**
- **Nó novo:** `For(value, children=[init, cond, increment, body])` — 4 filhos.
- **Parser:** nova função `parse_for_statement()` em `parse_statement` que consome `for`, `(`, um statement de atribuição (init), `;`, uma `BoolExpression` (cond), `;`, um statement de atribuição (increment), `)`, um block (body).
- **`generate()`:**
```asm
<init.generate()>
loop_<id>:
<cond.generate()>
  cmp eax, 0
  je exit_<id>
<body.generate()>
<increment.generate()>
  jmp loop_<id>
exit_<id>:
```
O incremento ocorre **após** o corpo e **antes** do salto para o loop, tal qual um `while` com um statement extra ao final.

---

**QI4. Por que `Node.id` estático e único globalmente não é um problema?**
Se dois nós tivessem o mesmo `id`, seus labels colidiriam no Assembly (`loop_5:` apareceria duas vezes), causando erro de montagem ou saltos para o ponto errado. O `id` estático é **seguro** porque: (a) dentro de uma execução do compilador, `new_id()` só incrementa — nunca repete; (b) entre execuções, o processo Python reinicia do zero — `Node.id = 0` é o estado inicial. Não há estado compartilhado entre compilações de arquivos diferentes. Cada nó da AST representa um único ponto do programa, e dois nós com o mesmo ID seria impossível por construção do contador.

---

## Integração de Fases

**QF1. Rastreie o operador `==` pelas 5 fases do compilador:**

**Léxica** (`select_next`, linha 523): encontra `=`, verifica se o próximo caractere também é `=` (lookahead de 1). Se sim: `Token("EQ", "==")`. Se não: `Token("ASSIGN", "=")`. O lookahead é o que diferencia os dois tokens.

**Sintática** (`parse_rel_expression`, linha 753): após parsear uma `Expression`, verifica `if Parser.lexer.next.type == "EQ"`. Consome o token, parseia outra `Expression`, cria `BinOp("==", [left, right])`. EBNF: `RelExpression → Expression [ "==" Expression ]`. Importante: usa `if`, não `while` — só uma comparação por expressão.

**AST**: nó `BinOp` com `self.value = "=="` e dois filhos (as duas expressões comparadas).

**Semântica** (`BinOp.evaluate`, linha 249): avalia ambos os filhos, verifica `both_numeric(left, right)` (ok) ou `left.type != right.type` (erro: tipos devem ser iguais se não numéricos). Retorna `Variable(left.value == right.value, "bool")`.

**Código** (`BinOp.generate`, linha 295):
```asm
cmp eax, ecx      ; compara (seta ZF se iguais)
mov eax, 0        ; assume falso
mov ecx, 1
cmove eax, ecx    ; se ZF=1 (iguais), move 1 para EAX
```
Usa `cmove` (move condicional) em vez de `je` para manter o resultado em EAX sem branch, seguindo o contrato de que expressões terminam com resultado em EAX.

---

**QF2. Rastreie `let mut x: i32 = 5 + y;` pelas 5 fases:**

**Tokens**: `LET MUT IDEN("x") COLON TYPE("i32") ASSIGN INT(5) PLUS IDEN("y") END`

**Sintática**: `parse_statement` vê LET → MUT (is_mutable=True) → IDEN → COLON → TYPE("i32") → ASSIGN → chama `parse_bool_expression` → ... → `parse_expression`: parseia `IntVal(5)`, vê PLUS, parseia `Identifier("y")`. Cria `BinOp("+", [IntVal(5), Identifier("y")])`. Cria `VarDec("i32", [Identifier("x"), BinOp(...)], is_mutable=True)`.

**AST**:
```
VarDec(value="i32", is_mutable=True)
├── Identifier("x")
└── BinOp("+")
    ├── IntVal(5)
    └── Identifier("y")
```

**Semântica** (`VarDec.evaluate`): avalia filho 1 → `BinOp("+").evaluate` → busca `y` na SymbolTable (erro se não declarada), obtém `Variable(y_val, "i32")`, verifica `both_numeric` → ok, retorna `Variable(5+y_val, "i32")`. Chama `create_variable("x", Variable(5+y_val,"i32"), "i32", True)`. Valida tipo.

**Código** (`VarDec.generate`): chama `create_variable("x", None, "i32", True)` (shift=N), emite `sub esp, 4 ; var x i32`. Chama `BinOp.generate`: gera `y` (direito) → `mov eax, [ebp-shift_y]`; push; gera `5` → `mov eax, 5`; pop ecx; `add eax, ecx`. Emite `mov [ebp-N], eax`.

---

**QF3. Rastreie `if (a && b) { x = 1; }` pelas 5 fases:**

**Tokens**: `IF OPEN_PAR IDEN("a") AND IDEN("b") CLOSE_PAR OPEN_BRA IDEN("x") ASSIGN INT(1) END CLOSE_BRA`

**Sintática**: `parse_statement` vê IF → OPEN_PAR → `parse_bool_expression` → `parse_bool_term`: parseia `Identifier("a")`, vê AND, parseia `Identifier("b")` → cria `BinOp("&&", [Identifier("a"), Identifier("b")])`. Nenhum OR → retorna. CLOSE_PAR → `parse_block` → `Assignment("=", [Identifier("x"), IntVal(1)])`. Sem ELSE → `If("IF", [BinOp("&&",...), Block([Assignment...])])` — 2 filhos.

**AST**:
```
If
├── BinOp("&&")
│   ├── Identifier("a")
│   └── Identifier("b")
└── Block
    └── Assignment("=", [Identifier("x"), IntVal(1)])
```

**Semântica** (`If.evaluate`): avalia filho 0 → `BinOp("&&").evaluate`: busca `a` e `b`, verifica ambos `"bool"` (linha 267 — erro se não), retorna `Variable(a.value and b.value, "bool")`. `If.evaluate` verifica `condition.type == "bool"` (linha 377). Executa filho 1 se verdadeiro.

**Código** (`If.generate`, nid=self.id): chama `children[0].generate()` → `BinOp("&&").generate`: gera `b` (direito) → push; gera `a` → pop ecx; `and eax, ecx`. Emite `cmp eax, 0`, `je exit_N`. Chama `children[1].generate()` → Block → Assignment → `mov eax, 1; mov [ebp-shift_x], eax`. Emite `exit_N:`. (2 filhos → sem labels else.)

---

## Gramática Formal

**QG1. Escreva a EBNF das 3 regras superiores. A gramática é ambígua?**

```ebnf
BoolExpression → BoolTerm { "||" BoolTerm }
BoolTerm       → RelExpression { "&&" RelExpression }
RelExpression  → Expression [ ("==" | "<" | ">") Expression ]
```

**Não é ambígua.** Derivação de `a || b && c`:
- `BoolExpression` → `BoolTerm "||" BoolTerm`
- BoolTerm esquerdo → `RelExpression` → `Identifier("a")`
- BoolTerm direito → `RelExpression "&&" RelExpression` → `Identifier("b") && Identifier("c")`
- Única árvore possível: `a || (b && c)` ✓

Se `BoolExpression` e `BoolTerm` fossem a mesma regra (`Expr → Expr "&&" Expr | Expr "||" Expr | atom`), a gramática seria **ambígua**: `a || b && c` poderia ser `(a || b) && c` OU `a || (b && c)`. O parser não saberia qual precedência aplicar — precisaria de regras de associatividade externas (como yacc/bison fazem com `%left`).

---

**QG2. O parser é LL(1) — por quê? Um parser bottom-up conseguiria parsear a mesma gramática?**

**LL(1)** = Left-to-right, Leftmost derivation, 1 token de lookahead. Cada decisão de parse usa exatamente 1 token adiante (`Parser.lexer.next`). Exemplos no código:
- `parse_bool_expression` verifica `Parser.lexer.next.type == "OR"` — 1 token decide se há mais termos.
- `parse_statement` verifica `tok.type == "LET"` vs `"IDEN"` vs `"IF"` — 1 token decide qual construção parsear.

A gramática habilita isso porque **as alternativas de cada regra começam com tokens distintos**. Não há conflito de primeiro token entre branches — condição necessária para LL(1).

**LR(1) (bottom-up)** conseguiria parsear a mesma gramática — LR é estritamente mais poderoso que LL. A gramática não teria que mudar. O parser construiria a árvore de baixo para cima usando um autômato shift-reduce. A diferença prática: LL(1) recursivo descendente é mais simples de escrever e depurar manualmente; LR(1) é gerado automaticamente (yacc/bison) e lida com gramáticas maiores.

---

**QG3. Por que `parse_rel_expression` usa `if` e `parse_expression` usa `while`?**

`parse_expression` usa `while` porque `a + b + c + d` é válido — múltiplas somas encadeadas, associativas à esquerda. EBNF: `Expression → Term { ("+" | "-") Term }`.

`parse_rel_expression` usa `if` porque a linguagem **proíbe encadeamento relacional**: `a < b < c` é inválido. EBNF: `RelExpression → Expression [ ("<" | ">" | "==") Expression ]`. A decisão de design: `a < b < c` é semanticamente ambíguo — em Python significa `a < b and b < c`, mas em C significa `(a < b) < c` (compara um bool com c). Para evitar confusão e seguir o estilo Rust, apenas uma comparação por expressão é permitida.

Se aceitássemos `a < b < c` (usando `while`), a gramática continuaria não-ambígua (o `{...}` é sempre associativo à esquerda). Mas o **tipo** quebraria: `(a < b)` retorna `bool`, e então `bool < c` tentaria comparar bool com i32 — erro semântico que precisaria de regra especial ou coerção.

---

## Classificação de Erros

**QE1. Classifique cada erro como léxico, sintático ou semântico:**

| # | Código | Fase | Onde em `main.py` |
|---|--------|------|-------------------|
| a | `let x: i32 = true;` | **Semântico** | `create_variable` linha 93: `is_valid_type` falha (`"bool" != "i32"`). O parser aceita a sintaxe sem reclamar. |
| b | `& foo` | **Léxico** | `select_next` linha 534: `"'&' isolado invalido; use '&&'"`. O caractere `&` sozinho não pertence a nenhum token válido. |
| c | `let x: i32 = 1 +;` | **Sintático** | `parse_factor` linha 855: token `;` aparece onde se esperava um fator (número, identificador, etc.). |
| d | `x = 5;` sem declaração | **Semântico** | `set_value` linha 101: `"Variavel 'x' nao foi declarada"`. Sintaxe válida; só a SymbolTable sabe que x não existe. |
| e | `let x: i32 = 1; x = 2;` sem mut | **Semântico** | `set_value` linha 105: `"Variavel 'x' nao e mutavel"`. Requer conhecer o `is_mutable` da variável. |
| f | `"abc` sem fechamento | **Léxico** | `select_next` linha 587: `"String sem aspas de fechamento"`. O problema aparece dentro do próprio consumo do token STR. |
| g | `1 && 2` | **Semântico** | `BinOp.evaluate` linha 267: `"Operador '&&' exige bool"`. Os tokens e a sintaxe são válidos; o tipo só é conhecido após evaluate. |
| h | `if (5) { ... }` | **Semântico** | `If.evaluate` linha 377: `"Condicao do if deve ser bool"`. O parser aceita qualquer expressão como condição. |

**Por que erros b e f não podem ser detectados depois?** → São erros na tokenização — o lexer não consegue nem produzir um token válido para o parser processar. Não há token para repassar.

**Por que d, g, h não podem ser detectados antes?** → O parser vê estruturas sintaticamente corretas (`IDEN = expr;`, `expr && expr`, `if (expr) block`). Só a SymbolTable (d) ou o tipo retornado por `evaluate` (g, h) revela o problema.

---

## Perguntas Teóricas

**QT1. Por que o compilador constrói uma AST em vez de executar os comandos diretamente durante o parsing?**
Três razões fundamentais:

**(a) Separação de responsabilidades**: o parser só reconhece estrutura — ele sabe que `let x: i32 = 5 + y` é uma declaração de variável com uma expressão, mas não sabe o valor de `y` nem se `5 + y` é válido. Executar semântica no parser misturaria as duas fases, tornando o código impossível de testar separadamente.

**(b) Reutilização da representação**: a mesma AST alimenta `evaluate()` (Roteiro 7 — interpretador em Python) e `generate()` (Roteiro 8 — compilador para NASM). Sem AST, seria necessário construir dois parsers distintos — um para cada modo. Com AST, só o "consumidor" final muda.

**(c) Análise que requer visão global**: um interpretador de 1 passada só enxerga o que já foi lido. Verificações como "variável usada antes de declarada", escopo de variáveis em blocos aninhados, ou otimizações que olham para frente no código são impossíveis sem uma estrutura intermediária. Interpretadores de 1 passada existem (shells, Forth), mas são limitados a linguagens que dispensam análise de contexto.

---

**QT2. Por que os nós da AST têm dois métodos (`evaluate` e `generate`) em vez de uma única função de execução?**
Os dois métodos representam **duas semânticas diferentes aplicadas à mesma sintaxe**. `evaluate` interpreta (produz um valor em Python), `generate` traduz (emite texto em NASM). A árvore é a mesma; o que muda é o que cada visitante faz com ela.

Isso é uma instância do padrão **Visitor**: a estrutura (AST) é separada das operações (semânticas) que se aplicam a ela. Consequências práticas:

- **Extensibilidade**: adicionar um novo backend (ex.: emitir LLVM IR, ou gerar JavaScript) não exige tocar no Lexer, Parser, nem nas regras semânticas — basta implementar `generate_llvm()` em cada nó.
- **Testabilidade**: é possível verificar a semântica (`evaluate`) independentemente da corretude do código gerado (`generate`). Um bug em `BinOp.generate` não contamina os testes de `BinOp.evaluate`.
- **Princípio da separação sintaxe-semântica**: a mesma notação pode ter múltiplas interpretações. Na teoria de linguagens formais, isso é a distinção entre sintaxe (a árvore) e semântica (o significado atribuído a ela). Dois métodos tornam essa separação explícita e executável.

---

**QE2. Seria possível mover a verificação de tipos do `BinOp` para o parser?**
 
**Parcialmente** — para literais: o parser poderia rejeitar `true + 5` (vê BoolVal antes de PLUS antes de IntVal). Mas **impossível** para qualquer expressão envolvendo variáveis: em `x + 5`, o parser vê `IDEN PLUS INT` — não tem como saber o tipo de `x` sem consultar a SymbolTable, que só existe durante `evaluate`.

**O que seria perdido se movêssemos**:
- `x + 5` onde x é bool → não detectável no parser
- `"a" == x` onde x é i32 → não detectável
- Qualquer erro de tipo envolvendo variáveis

**Por que "variável não declarada" precisa estar na mesma fase?** Porque a ordem importa: em `y = x + 1; let x: i32 = 5;`, o parser veria a declaração de `x` mais adiante no código. Para detectar "x não declarada" no momento do uso, precisamos da execução sequencial de `evaluate` — o parser processa a estrutura toda antes de executar qualquer semântica. A verificação de declaração é inerentemente **dinâmica em relação à posição no arquivo**, o que requer a fase semântica.
