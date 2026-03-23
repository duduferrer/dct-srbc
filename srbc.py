from pathlib import Path
from time import sleep
from typing import Any

import pandas as pd
import questionary
import config
from database import query, execute
from loggerConfig import log
from utils import coordIsValid, clear_screen, validate_size

XLS_PATH = ''

def get_data_from_table(data_type, file=""):
    current_dir = Path.cwd()
    if file != "":
        return get_data_xls(current_dir, data_type, file)
    clear_screen()
    xlsx_files = [f.name for f in current_dir.glob("*.xlsx")]
    if not xlsx_files:
        print(f"Nenhum arquivo XLSX encontrado em: {current_dir}")
        input("Pressione enter para continuar...")
        return None
    choices = xlsx_files + [questionary.Separator(), "Cancelar"]
    selected_file = questionary.select("Selecione o arquivo para importar: ", choices=choices).ask()
    if selected_file is None or selected_file == "Cancelar":
        print("Nenhum arquivo selecionado.")
        sleep(2)
        return None

    return get_data_xls(current_dir, data_type, selected_file)


def get_data_xls(current_dir: Path, data_type, selected_file) -> Any:
    try:
        global XLS_PATH
        XLS_PATH = current_dir / selected_file
        df = pd.read_excel(XLS_PATH, header=0, sheet_name=data_type)
        return df
    except Exception as e:
        log.error(f"Erro ao ler arquivo. {e}")
        input("Pressione enter para continuar...")
        return None


def insert_fix_into_db(df):
    log.info("Iniciando inserção de fixos")
    df=df.rename(columns={"LATITUDE(DMM)":"CAMPOA", "LONGITUDE(DMM)":"CAMPOB", "NUMERO DO FIXO":"NUMERO"})
    numero_fixo = int(get_last_fix_number())
    df["NUMERO"] = df["NUMERO"].fillna(0).astype(int)
    df = df[df["NUMERO"] != 0]
    df["NUMERO"] = (df["NUMERO"].astype(int)+numero_fixo).astype(str).str.zfill(4)
    df = df.where(pd.notnull(df), "")
    df["NOME"] = df["NOME"].str.strip().str.upper()
    old_fix = get_fix_from_area()
    old_fix_df = pd.DataFrame(old_fix, columns=["AREA", "NUMERO", "INDICATIVO", "NOME", "TIPO", "FREQUENCIA", "TIPOCOORD", "CAMPOA", "CAMPOB"])
    df = df.merge(old_fix_df[["NUMERO", "NOME"]], on="NOME", how="left", suffixes=("", "_OLD"))
    mask = df['NUMERO_OLD'].notnull()
    existing_fix = df.loc[mask, ['NOME', 'CAMPOA', 'CAMPOB']].values.tolist()
    print(df)
    input()
    for fix in existing_fix:
        log.info(f"Fixo: {fix[0]} já existente. Atualizado com os valores: {fix[1]}, {fix[2]}")
    df.loc[mask, 'NUMERO'] = df['NUMERO_OLD']
    df["AREA"] = config.AREA
    for row in df.itertuples():
        campo_a = row.CAMPOA
        campo_b = row.CAMPOB
        if not coordIsValid(campo_a) & coordIsValid(campo_b):
            log.error(f"Erro no formato da coordenada de: {row.NOME}\n")
            print(f"Erro no formato da coordenada de: {row.NOME}\n")
            input("Pressione enter para continuar...")
            return False

    queries_list = []
    fixos = df.to_dict(orient="records")
    sql = """
            INSERT INTO a_fixos
            (AREA, NUMERO, INDICATIVO, NOME, TIPO, FREQUENCIA, TIPOCOORD, CAMPOA, CAMPOB)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            INDICATIVO = VALUES(INDICATIVO),
            TIPO = VALUES(TIPO),
            FREQUENCIA = VALUES(FREQUENCIA),
            TIPOCOORD = VALUES(TIPOCOORD),
            CAMPOA = VALUES(CAMPOA),
            CAMPOB = VALUES(CAMPOB);
          """
    for fixo in fixos:
        values = (fixo.get("AREA"), fixo.get("NUMERO"), "", fixo.get("NOME"), "", "",
                  "G", fixo.get("CAMPOA"), fixo.get("CAMPOB"))
        queries_list.append((sql, values))
    count = execute(queries_list)
    if count>0:
        list_inserted_fix = df[['NOME', 'NUMERO']].values.tolist()
        for fix in list_inserted_fix:
            log.info(f"Inserido fixo: {fix[0]} - {fix[1]} no banco de dados.")
        print("Arquivo inserido com sucesso!")
        input("Pressione enter para continuar...")
        return True
    elif count<=0:
        log.warn("Nao houveram alterações no banco. Cheque a tabela com os novos fixos.")
        input("Pressione enter para continuar...")
        return False
    else:
        return False


def get_last_fix_number():
    res = query("SELECT numero FROM a_fixos WHERE area=%s ORDER BY CAST(numero AS UNSIGNED) DESC LIMIT 1;",(config.AREA,))
    if len(res) == 1:
        return res[0][0]
    else:
        return 0
def get_fix_from_area():
    res = query("SELECT * FROM a_fixos WHERE area=%s;",(config.AREA,))
    return res

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
        sql_area = """
                INSERT INTO a_area
                (AREA, DECLMAG, HEMISFERIO, OBSERVACOE)
                VALUES (%s, %s, %s, %s)
                """
        sql_usuario = """
                    INSERT INTO a_usuari (USUARIO, SENHA, GRUPO, AREA)
                    VALUES (%s, %s, %s, %s)
                    """
        values_area = (area.upper(), decl_mag, hems.upper(), obs.upper())
        values_usuario = (area.upper(), area.upper(), '1', area.upper())
        execute([(sql_area, values_area),(sql_usuario, values_usuario)])
        config.AREA = area.upper()

def insert_trj(df: pd.DataFrame):
    df = df.rename(columns={"NOME":"descricao", "STAR?(S/N)":"star"})
    df = df.dropna(how="all")
    df["NUMERO"] = (df["NUMERO"]).astype(int).astype(str).str.zfill(4)
    sql_trj = '''
    INSERT IGNORE INTO a_traje(AREA, NUMERO, DESCRICAO, PROA, STAR)
    VALUES (%s, %s, %s, %s, %s)
    '''
    trjs = df.to_dict("records")
    trj_queries_list = []
    for trj in trjs:
        values_trj = (config.AREA, trj['NUMERO'], trj["descricao"], "", trj["star"])
        trj_queries_list.append((sql_trj, values_trj))
    count_pts = execute(trj_queries_list)
    if count_pts > 0:
        list_inserted_trj = df[['descricao', 'NUMERO']].values.tolist()
        for trj in list_inserted_trj:
            log.info(f"Inserido TRJ: {trj[0]} - {trj[1]} no banco de dados.")
        print("Arquivo inserido com sucesso!")
        input("Pressione enter para continuar...")
    elif count_pts <= 0:
        log.warn("Nao houveram alterações no banco. Cheque a tabela com as novas trjs.")
        input("Pressione enter para continuar...")
    # PONTOS TRJ
    df = get_data_from_table("pts_traje-SCRIPT", XLS_PATH)
    df = df.dropna(how="all")
    df = df[df["Nro do Ponto"]!=0]
    df.fillna(0, inplace=True)
    df[["TRJ","FIXO","DIST(SE POLAR)","RADIAL/GRAUS(SE POLAR)","CAMPO D", "ALTITUDE", "VELOCIDADE(TAS)", "PROCEDIMENTO QUE LIGA"]] = (df[["TRJ","FIXO","DIST(SE POLAR)","RADIAL/GRAUS(SE POLAR)","CAMPO D", "ALTITUDE", "VELOCIDADE(TAS)", "PROCEDIMENTO QUE LIGA"]]).astype(int).astype(str)
    df["TRJ"] = (df["TRJ"]).astype(int).astype(str).str.zfill(4)
    df = df.replace("0", "")
    pts_trjs = df.to_dict("records")
    sql_pts_trj = '''
        INSERT INTO a_bptraj(AREA, TRAJETOR, NUMBKP, TIPOCOORD, CAMPOA, CAMPOB, CAMPOC, CAMPOD, ALTITUDE, VELOCIDADE, PROCEDIMEN)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    pts_queries_list = []
    print(df)
    input()
    for pt in pts_trjs:
        values_pt = (config.AREA, pt["TRJ"], pt["Nro do Ponto"], pt["Tipo Coord(F/D)"], pt["FIXO"] ,pt["DIST(SE POLAR)"], pt["RADIAL/GRAUS(SE POLAR)"], pt["CAMPO D"], pt["ALTITUDE"], pt["VELOCIDADE(TAS)"], pt["PROCEDIMENTO QUE LIGA"])
        pts_queries_list.append((sql_pts_trj, values_pt))
    count_pts = execute(pts_queries_list)
    if count_pts > 0:
        list_inserted_pts = df[['FIXO', 'TRJ']].values.tolist()
        for pt in list_inserted_pts:
            log.info(f"Inserido FIXO: {pt[0]}, da TRJ {pt[1]} no banco de dados.")
        print("Arquivo inserido com sucesso!")
        input("Pressione enter para continuar...")
        return True
    elif count_pts <= 0:
        log.warn("Nao houveram alterações no banco. Cheque a tabela com os fixos das TRJ.")
        input("Pressione enter para continuar...")
        return False
    else:
        return False