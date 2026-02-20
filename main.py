import sys

def tradutor():
    texto_usuario = sys.argv[1]
    lista_numeros = []
    lista_operadores = []
    resultado = 0
    numero_atual = ""
    
    for caractere in texto_usuario:
        if caractere.isdigit():
            numero_atual += caractere
        elif caractere in ["+", "-"]:
            if numero_atual:
                lista_numeros.append(int(numero_atual))
                numero_atual = ""
            lista_operadores.append(caractere)
    
    if numero_atual:
        lista_numeros.append(int(numero_atual))
    
    if len(lista_numeros) == 0:
        raise ValueError("Nenhum número encontrado.")
    if len(lista_operadores) == 0:
        raise ValueError("Nenhum operador encontrado.")
    if len(lista_operadores) < 1 or len(lista_numeros) < 2:
        raise ValueError("A expressão deve conter pelo menos dois números e um operador.")
    if len(lista_operadores) != len(lista_numeros) - 1:
        raise ValueError("O número de operadores deve ser um a menos que o número de números.")

    resultado = lista_numeros[0]
    for i in range(len(lista_operadores)):
        if lista_operadores[i] == "+":
            resultado += lista_numeros[i + 1]
        elif lista_operadores[i] == "-":
            resultado -= lista_numeros[i + 1]
    
    print(resultado)
    return resultado

tradutor()