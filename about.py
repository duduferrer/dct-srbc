from utils import clear_screen


def about():
    clear_screen()
    print('Criado por Eduardo Ferrer')
    print('Contato: duduferrer7@gmail.com\n\n')
    print('''A ideia do projeto é facilitar a inserção de dados no SRBC 5.3, usando planilhas.
Para mais informações, como os formatos das planilhas, acesse: https://github.com/duduferrer/dct-srbc''')
    input("\nAperte enter para continuar...")
    from menus import selection_menu
    selection_menu()