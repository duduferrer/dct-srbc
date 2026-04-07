import os
import sys

import questionary
from srbc import get_data_from_table, insert_fix_into_db, insert_trj, insert_exerc, insert_exerc_traf, insert_subs, \
    insert_ad, insert_maps, insert_acft_fmly, insert_acft_type
import config
from about import about
from database import conn_test
from srbc import get_areas, create_area
from utils import load_db_credentials, clear_screen, unavailable
from loggerConfig import log


def initial_setup():
    clear_screen()
    use_default = questionary.confirm("Você deseja utilizar login e senha padrão, para acessar o banco?").ask()
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
    conn_test()
    area_selection()


def area_selection():
    areas = get_areas()
    choice_list = []
    for area, _, _, obs in areas:
        title = area + " - " + obs
        choice = questionary.Choice(title, value=area)
        choice_list.append(choice)
    choice_list.append(questionary.Separator())
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
                    questionary.Choice("Adicionar Submapas", "maps"),
                    questionary.Choice("Adicionar Trajetorias", "trj"),
                    questionary.Choice("Adicionar Subidas", "sub"),
                    questionary.Choice("Adicionar Exercicios", "ex"),
                    questionary.Choice("Adicionar Aeronaves de Exercicios", "acft"),
                    questionary.Choice("Adicionar Aerodromo", "ad"),
                    questionary.Choice("Adicionar Familias de ACFT", "fmly"),
                    questionary.Choice("Adicionar Tipos de ACFT", "acft_type"),
                    questionary.Choice("Sobre", "about"),
                    questionary.Separator(),
                    questionary.Choice("Sair", "exit")]
    option_selected = questionary.select("Escolha uma opção: ", choices=choices_list).ask()
    match option_selected:
        case "fix":
            insert_fix_into_db()
            selection_menu()
        case "trj":
            insert_trj()
            selection_menu()
        case "ex":
            insert_exerc()
            selection_menu()
        case "acft":
            insert_exerc_traf()
            selection_menu()
        case "sub":
            insert_subs()
            selection_menu()
        case "ad":
            unavailable()
            # insert_ad()
            selection_menu()
        case "maps":
            insert_maps()
            selection_menu()
        case "fmly":
            insert_acft_fmly()
            selection_menu()
        case "acft_type":
            insert_acft_type()
            selection_menu()
        case "about":
            about()
        case "exit":
            print("Encerrando...")
            sys.exit(0)
        case _:
            print("Escolha uma opção válida.")
            selection_menu()
