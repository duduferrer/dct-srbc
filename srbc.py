from pathlib import Path
from time import sleep
import pandas as pd
import questionary
import config
from database import query, execute
from utils import coordIsValid, clear_screen, validate_size


def get_fix_from_table():
    clear_screen()
    current_dir = Path.cwd()
    csv_files = [f.name for f in current_dir.glob("*.csv")]
    if not csv_files:
        print(f"Nenhum arquivo CSV encontrado em: {current_dir}")
        input("Pressione enter para continuar...")
        return None
    choices = csv_files + [questionary.Separator(), "Cancelar"]
    selected_file = questionary.select("Selecione o arquivo para importar: ", choices=choices).ask()
    if selected_file is None or selected_file == "Cancelar":
        print("Nenhum arquivo selecionado.")
        sleep(2)
        return None
    try:
        csv_path = current_dir / selected_file
        df = pd.read_csv(csv_path, header=0, sep=",")
        return df
    except:
        print(f"Erro ao ler arquivo.")
        input("Pressione enter para continuar...")
        return None

def insert_fix_into_db(df):
    numero_fixo = int(get_last_fix_number())
    df = df.where(pd.notnull(df), "")
    df["NUMERO"] = (df["NUMERO"]+numero_fixo).astype(str).str.zfill(4)
    df["AREA"] = config.AREA
    for row in df.itertuples():
        campo_a = row.CAMPOA
        campo_b = row.CAMPOB
        if not coordIsValid(campo_a) & coordIsValid(campo_b):
            print(f"Erro no formato da coordenada de: {row.NOME}\n")
            input("Pressione enter para continuar...")
            return False

    queries_list = []
    fixos = df.to_dict(orient="records")
    # print(fixos)
    sql = """
            INSERT INTO a_fixos
            (AREA, NUMERO, INDICATIVO, NOME, TIPO, FREQUENCIA, TIPOCOORD, CAMPOA, CAMPOB)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
          """
    for fixo in fixos:
        values = (fixo.get("AREA"), fixo.get("NUMERO"), fixo.get("INDICATIVO"), fixo.get("NOME"), fixo.get("TIPO"), fixo.get("FREQUENCIA"),
                  fixo.get("TIPOCOORD"), fixo.get("CAMPOA"), fixo.get("CAMPOB"))
        queries_list.append((sql, values))
    count = execute(queries_list)
    if count>0:
        print("Arquivo inserido com sucesso!")
        input("Pressione enter para continuar...")
        return True
    elif count<=0:
        print("Nao houveram alterações no banco")
        input("Pressione enter para continuar...")
        return False
    else:
        return False


def get_last_fix_number():
    res = query("SELECT * FROM a_fixos WHERE area=%s ORDER BY CAST(numero AS UNSIGNED) DESC LIMIT 1;",(config.AREA,))
    if len(res) == 1:
        return res[0][1]
    else:
        return 0
def get_areas():
    res = query("SELECT * FROM a_area;")
    return res
def create_area():
    clear_screen()
    print("-------- CRIAÇÃO DE AREA --------")
    area = questionary.text("Área: ", validate=validate_size(4)).ask()
    decl_mag = questionary.text("Declinação Magnética: ", validate=validate_size(2)).ask()
    hems = questionary.text("Hemisfério(W ou E): ", validate=validate_size(1)).ask()
    obs = questionary.text("Observação: ", validate=validate_size(50)).ask()
    res = query("SELECT * FROM a_area WHERE AREA = %s;", (area,))
    if len(res) != 0:
        from menus import area_selection
        print("Área já existe.")
        sleep(2)
        area_selection()
    else:
        sql = """
                INSERT INTO a_area
                (AREA, DECLMAG, HEMISFERIO, OBSERVACOE)
                VALUES (%s, %s, %s, %s)
              """
        values = (area.upper(), decl_mag, hems.upper(), obs.upper())
        execute([(sql, values)])
        config.AREA = area.upper()