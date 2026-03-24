from utils import clear_screen


def about():
    clear_screen()
    print('Criado por Eduardo Ferrer')
    print('Contato: duduferrer7@gmail.com\n\n')
    print('''A ideia do projeto é facilitar a inserção de dados no SRBC 5.3, usando planilhas.
Para mais informações, como os formatos das planilhas, acesse: https://github.com/duduferrer/dct-srbc
ATENÇÃO: O SCRIPT NAO EVITA CONFLITOS! CUIDE PARA NAO CONFLITAR COM O EXISTENTE NO BANCO DE DADOS.
OS FIXOS SAO ALTERADOS PARA NAO CONFLITAR. A NUMERAÇÃO DOS FIXOS SERÁ ACRESCIDA DO VALOR DO ULTIMO FIXO CADASTRADO ATUALMENTE NO BANCO DE DADOS."
''')
    input("\nAperte enter para continuar...")
    from menus import selection_menu
    selection_menu()