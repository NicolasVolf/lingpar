# Testes

Programas de exemplo usados para exercitar o interpretador/compilador. Rode qualquer um
com `python ../main.py <arquivo>.rs` a partir desta pasta (ou `python main.py tests/<arquivo>.rs`
a partir da raiz do projeto).

| Arquivo | O que exercita | Resultado esperado |
|---|---|---|
| `teste_funcao.rs` | função com parâmetros, retorno tipado e chamada | imprime `13` |
| `teste_ordem_args.rs` | ordem de avaliação dos argumentos | imprime `7` |
| `teste_param_str.rs` | parâmetro do tipo `str` | imprime `1` (interpretação), depois erro na geração de assembly — `str` como parâmetro de função não é suportado pelo codegen |
| `teste_struct_erro.rs` | caso de **falha esperada**: acessa um campo inexistente da struct | erro semântico em tempo de execução |
