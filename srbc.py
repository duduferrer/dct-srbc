import pandas as pd
import csv
from database import query
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
    query(queries_list)

def get_last_fix_number():
    res = query("SELECT * FROM a_fixos ORDER BY numero DESC LIMIT 1;")
    return res[0][1]