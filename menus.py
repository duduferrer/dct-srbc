import sys

import questionary
from srbc import get_fix_from_table, insert_fix_into_db
import config
from about import about
from database import conn_test
from srbc import get_areas, create_area
from utils import load_db_credentials, clear_screen


def initial_setup():
    clear_screen()
    use_default = questionary.confirm("Você deseja utilizar as credenciais padrão?").ask()
    if use_default:
        load_db_credentials("", "", "", "", "")
    else:
        print("Caso deseje que algum dos valores utilize o valor padrão, apenas aperte ENTER para pular.")
        host = questionary.text("Informe o HOST: ").ask()
        user = questionary.text("Informe o USER: ").ask()
        password = questionary.password("Informe a PASSWORD: ").ask()
        database = questionary.text("Informe o DB: ").ask()
        port = questionary.text("Informe o PORT: ").ask()
        load_db_credentials(host, user, password, database, port)
    try:
        conn_test()
    except ConnectionError:
        print("Erro ao conectar no banco de dados. Cheque credenciais.")

    area_selection()


def area_selection():
    areas = get_areas()
    choice_list = []
    for area, _, _, obs in areas:
        title = area + " - " + obs
        choice = questionary.Choice(title, value=area)
        choice_list.append(choice)
    choice_list.append(questionary.Choice("CRIAR ÁREA NOVA", value="New Area"))
    area = questionary.select("Escolha a área que será editada: ", choices=choice_list).ask()
    if area == "New Area":
        create_area()
    else:
        config.AREA = area
    selection_menu()


def selection_menu():
    clear_screen()
    print(f'Editando a área: {config.AREA}')
    choices_list = [questionary.Choice("Adicionar Fixos", "fix"),
                    questionary.Choice("Adicionar Trajetorias", "trj"),
                    questionary.Choice("Adicionar Exercicios", "ex"),
                    questionary.Choice("Adicionar Aeronaves de Exercicios", "acft"),
                    questionary.Choice("Sobre", "about"),
                    questionary.Choice("Sair", "exit")]
    option_selected = questionary.select("Escolha uma opção: ", choices=choices_list).ask()
    match option_selected:
        case "fix":
            df = get_fix_from_table()
            insert_fix_into_db(df)
            selection_menu()
        case "trj":
            pass
        case "ex":
            pass
        case "acft":
            pass
        case "about":
            about()
        case "exit":
            print("Encerrando...")
            sys.exit(0)
        case _:
            print("Escolha uma opção válida.")
            selection_menu()
