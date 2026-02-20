import re
import os

from mysql.connector.constants import flag_is_set

import config

'''
VERIFICAR SE:
    AREA EXISTE
    FIXO É UNICO NA AREA
'''

def coordIsValid(coord)->bool:
    pattern = ""
    campo = coord[-1]
    match campo:
        case "N"|"S":
            pattern = r"^\d{4}\.\d{3}[NS]$"
        case "W"|"E":
            pattern = r"^\d{5}\.\d{3}[WE]$"
        case _:
            print("Erro na validação de campo da coord:", coord)
            return False

    if re.match(pattern, coord):
        return True
    else:
        return False

def load_db_credentials(host, user, password, database, port):
    if host == "":
        config.HOST = os.getenv('DB_HOST')
    else:
        config.HOST = host
    if user == "":
        config.USER = os.getenv('DB_USER')
    else:
        config.USER = user
    if password == "":
        config.PASSWORD = os.getenv('DB_PASSWORD')
    else:
        config.PASSWORD = password
    if database == "":
        config.DATABASE = os.getenv('DB_DATABASE')
    else:
        config.DATABASE = database
    if port == "":
        config.PORT = os.getenv('DB_PORT')
    else:
        config.PORT = port

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("******* ACESSO DIRETO AO SRBC ********\n\n")

def validate_size(size):
    def validator(text):
        if len(text) > size:
            return f"Campo nao pode ser maior que {size}"
        return True
    return validator