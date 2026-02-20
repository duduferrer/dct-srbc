from time import sleep
import pandas as pd
import questionary
import config
from config import AREA
from database import query, execute
from utils import coordIsValid, clear_screen, validate_size


def get_fix_from_table():
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        print("Tkinter não está instalado. Instale-o no sistema.")
        exit(1)
    root = tk.Tk()
    root.withdraw()
    csv_path = filedialog.askopenfilename(
        title="Selecione o arquivo CSV",
        filetypes=[("Arquivos CSV", "*.csv")],
    )
    filename = csv_path
    if not csv_path:
        print("Nenhum arquivo selecionado. Encerrando.")
        exit()
    df = pd.read_csv(filename, header=0, sep=",")
    return df

def insert_fix_into_db(df):
    numero_fixo = int(get_last_fix_number())
    df = df.where(pd.notnull(df), "")
    df["NUMERO"] = df["NUMERO"]+numero_fixo
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
    execute(queries_list)

def get_last_fix_number():
    res = query("SELECT * FROM a_fixos WHERE area=%s ORDER BY CAST(numero AS UNSIGNED) DESC LIMIT 1;",(AREA,))
    return res[0][1]
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