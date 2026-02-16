import re

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