import os
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


def insert_fix_into_db():
    log.info("Iniciando inserção de fixos")
    df = get_data_from_table(config.FIX)
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

def insert_trj():
    df = get_data_from_table(config.TRJ)
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
    df = get_data_from_table(config.PTS_TRJ, XLS_PATH)
    df = df.dropna(how="all")
    df = df[df["Nro do Ponto"]!=0]
    df.fillna({'PROCEDIMENTO QUE LIGA':"0"}, inplace=True)
    df.fillna(0, inplace=True)
    df[["TRJ","FIXO","DIST(SE POLAR)","RADIAL/GRAUS(SE POLAR)","CAMPO D", "ALTITUDE", "VELOCIDADE(TAS)", "PROCEDIMENTO QUE LIGA"]] = (df[["TRJ","FIXO","DIST(SE POLAR)","RADIAL/GRAUS(SE POLAR)","CAMPO D", "ALTITUDE", "VELOCIDADE(TAS)", "PROCEDIMENTO QUE LIGA"]]).astype(int).astype(str)
    df["TRJ"] = (df["TRJ"]).astype(int).astype(str).str.zfill(4)
    df["Nro do Ponto"] = (df["Nro do Ponto"]).astype(int).astype(str).str.zfill(3)
    df["FIXO"] = (df["FIXO"]).astype(int).astype(str).str.zfill(4)
    df = df.replace("0", "")
    pts_trjs = df.to_dict("records")
    sql_pts_trj = '''
        INSERT INTO a_bptraj(AREA, TRAJETOR, NUMBKP, TIPOCOORD, CAMPOA, CAMPOB, CAMPOC, CAMPOD, ALTITUDE, VELOCIDADE, PROCEDIMEN)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    pts_queries_list = []
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

def insert_exerc():
    df = get_data_from_table(config.EXERCICIO)
    df = df.dropna(how="all")
    df.fillna(0, inplace=True)
    df = df.replace(0, "")
    df["NUMEXERC"] = (df["NUMEXERC"]).astype(int).astype(str).str.zfill(4)
    sql = '''
        INSERT INTO a_exerc(AREA, NUMEXERC, DESEXERC, HORAINICIO, ALTITRANS, NUMSUBMAP1, NUMSUBMAP2, NUMSUBMAP3, NUMSUBMAP4, QNH, LIMINFQNH,LIMSUPQNH, PENDQNH, INDCONDMET, NUMFORMMET, CONSOLES)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    execs = df.to_dict("records")
    execs_list = []
    for exec in execs:
        values = (config.AREA, exec['NUMEXERC'], exec['DESEXERC'], '09:00', '8500', '001', '', '', '', '1013', '955','1055', '0.1', 'N', '', '01')
        execs_list.append((sql, values))
    count = execute(execs_list)
    if count > 0:
        list_inserted_execs = df[['NUMEXERC', 'DESEXERC']].values.tolist()
        for exec in list_inserted_execs:
            log.info(f"Inserido Exercicio: {exec[0]} - {exec[1]} no banco de dados.")
        print("Arquivo inserido com sucesso!")
        input("Pressione enter para continuar...")
        return True
    elif count <= 0:
        log.warn("Nao houveram alterações no banco. Cheque a tabela com os Exercicios.")
        input("Pressione enter para continuar...")
        return False
    else:
        return False

def insert_exerc_traf():
    df = get_data_from_table(config.ACFT_EXERC)
    df = df.dropna(how="all")
    cols_int = ["EXERCICIO", "TRAF", "SSR", "NIV", "VEL(IAS)",
                "PROA", "FIXO", "DIST(SE POLAR)", "RADIAL/GRAUS(SE POLAR)",
                "PIL", "ATIV"]
    df[cols_int] = df[cols_int].fillna(0)
    cols_str = ["DESIG", "INDICATIVO", "DEP", "ARR", "PROCED",
                "TIPO DE COORD(F/D)", "RMK"]
    df[cols_str] = df[cols_str].fillna("")

    df["EXERCICIO"] = (df["EXERCICIO"]).astype(int).astype(str).str.zfill(4)
    df["TRAF"] = (df["TRAF"]).astype(int).astype(str).str.zfill(4)
    df["FIXO"] = (df["FIXO"]).astype(int).astype(str).str.zfill(4)
    df["PIL"] = (df["PIL"]).astype(int).astype(str).str.zfill(2)
    df["ATIV"] = (df["ATIV"]).astype(int).astype(str).str.zfill(3)
    replace_cols = df.columns.difference(["ATIV"])
    df[replace_cols] = df[replace_cols].replace(0, "")
    df = df[df["EXERCICIO"] != "0000"]
    sql = '''
        INSERT INTO a_trafe(area , numexerc , numtrafego , designador , ssr , indicativo , origem , destino , procedimen , nivel , velocidade , proa , tipocoord , campoa , campob , campoc , pilotagem , temptrafeg, rmk , niveltrj , veltrj)
        VALUES (%s , %s , %s , %s , %s , %s , %s , %s , %s , %s , %s , %s , %s , %s , %s , %s , %s , %s, %s , %s , %s)
    '''

    trafs = df.to_dict("records")
    trafs_list = []
    for traf in trafs:
        values = (config.AREA, traf['EXERCICIO'], traf["TRAF"], traf["DESIG"], traf["SSR"], traf["INDICATIVO"], traf["DEP"], traf["ARR"], traf["PROCED"], traf["NIV"], traf["VEL(IAS)"], traf["PROA"], traf["TIPO DE COORD(F/D)"], traf["FIXO"], traf["DIST(SE POLAR)"], traf["RADIAL/GRAUS(SE POLAR)"], traf["PIL"], traf["ATIV"], traf["RMK"], traf["NIV"], traf["VEL(IAS)"])
        trafs_list.append((sql, values))
    count = execute(trafs_list)
    if count > 0:
        list_inserted_trafs = df[['EXERCICIO', 'INDICATIVO']].values.tolist()
        for traf in list_inserted_trafs:
            log.info(f"Inserido Trafego: {traf[1]}, Exercicio: {traf[0]} no banco de dados.")
        print("Arquivo inserido com sucesso!")
        input("Pressione enter para continuar...")
        return True
    elif count <= 0:
        log.warn("Nao houveram alterações no banco. Cheque a tabela com os Exercicios.")
        input("Pressione enter para continuar...")
        return False
    else:
        return False

def insert_subs():
    df = get_data_from_table(config.SUB)
    df = df.dropna(how="all")
    df.fillna(0, inplace=True)
    df["PISTA"] = (df["PISTA"]).astype(int).astype(str)
    df["NUMERO"] = (df["NUMERO"]).astype(int).astype(str).str.zfill(3)
    sql = '''
        INSERT IGNORE INTO a_subida(area, numero, nome, aerodromo, pista)
        VALUES (%s , %s , %s , %s , %s )
    '''
    subs = df.to_dict("records")
    subs_list = []
    for sub in subs:
        values = (config.AREA, sub["NUMERO"], sub["NOME"], sub["AERODROMO"], sub["PISTA"]+"C")
        subs_list.append((sql, values))
    count = execute(subs_list)
    if count > 0:
        list_inserted_subs = df[['NOME', 'AERODROMO', 'PISTA']].values.tolist()
        for sub in list_inserted_subs:
            log.info(f"Procedimento de Subida adicionado: {sub[0]} - {sub[1]} {sub[2]} no banco de dados.")
        print("Arquivo inserido com sucesso!")
        input("Pressione enter para continuar...")
    elif count <= 0:
        log.warn("Nao houveram alterações no banco. Cheque a tabela com os Exercicios.")
        input("Pressione enter para continuar...")

    # PONTOS SUB
    df = get_data_from_table(config.PTS_SUB, XLS_PATH)
    df = df.dropna(how="all")
    df = df[df["NRO PONTO"] != 0]
    df.fillna({'PROCEDIMENTO QUE LIGA':"0"}, inplace=True)
    df.fillna(0, inplace=True)
    df[["SUB", "NRO PONTO", "DIST(SE POLAR)", "RADIAL/GRAUS(SE POLAR)", "CAMPO D", "ALTITUDE", "GRAD SUB", "VELOCIDADE(IAS)"]] = (
        (df[["SUB", "NRO PONTO", "DIST(SE POLAR)", "RADIAL/GRAUS(SE POLAR)", "CAMPO D", "ALTITUDE", "GRAD SUB", "VELOCIDADE(IAS)",
        ]]).astype(int).astype(str))
    df["SUB"] = (df["SUB"]).astype(int).astype(str).str.zfill(3)
    df["NRO PONTO"] = (df["NRO PONTO"]).astype(int).astype(str).str.zfill(3)
    df["FIXO"] = (df["FIXO"]).astype(int).astype(str).str.zfill(4)
    df = df.replace("0", "")
    pts_sub = df.to_dict("records")
    sql_pts_trj = '''
        INSERT INTO a_bpsub(AREA, NUMSUB, NUMBKP, TIPOCOORD, CAMPOA, CAMPOB, CAMPOC, CAMPOD, ALTITUDE, RAZSUB, VELOCIDADE,PROCEDIMEN)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    pts_queries_list = []
    for pt in pts_sub:
        values_pt = (config.AREA, pt["SUB"], pt["NRO PONTO"], pt["TIPO COORD(F/D)"], pt["FIXO"],
                     pt["DIST(SE POLAR)"], pt["RADIAL/GRAUS(SE POLAR)"], pt["CAMPO D"], pt["ALTITUDE"], pt["GRAD SUB"],
                     pt["VELOCIDADE(IAS)"], pt["PROCEDIMENTO QUE LIGA"])
        pts_queries_list.append((sql_pts_trj, values_pt))
    count_pts = execute(pts_queries_list)
    if count_pts > 0:
        list_inserted_pts = df[['FIXO', 'SUB']].values.tolist()
        for pt in list_inserted_pts:
            log.info(f"Inserido FIXO: {pt[0]}, da SUB {pt[1]} no banco de dados.")
        print("Arquivo inserido com sucesso!")
        input("Pressione enter para continuar...")
        return True
    elif count_pts <= 0:
        log.warn("Nao houveram alterações no banco. Cheque a tabela com os fixos das SUB.")
        input("Pressione enter para continuar...")
        return False
    else:
        return False

def insert_ad():
    clear_screen()
    print("-------- CRIAÇÃO DE AERODROMO --------")
    indicativo = questionary.text("Indicativo: ", validate=validate_size(4)).ask()
    nome = questionary.text("Nome: ", validate=validate_size(15)).ask()
    elev = questionary.text("Elevação: ", validate=validate_size(5)).ask()
    res = query("SELECT * FROM a_aerod WHERE AREA = %s AND indicativo = %s;", (config.AREA, indicativo))
    if len(res) != 0:
        from menus import area_selection
        print("Aerodromo já existe.")
        sleep(2)
        return
    else:
        sql_ad = """
                INSERT INTO a_aerod
                (AREA, INDICATIVO, NOME, ELEVACAO)
                VALUES (%s, %s, %s, %s)
                """
        values_ad = (config.AREA, indicativo.upper(), nome.upper(), elev.upper())
        count = execute([(sql_ad, values_ad)])
        if count > 0:
            log.info(f"Aerodromo: {indicativo} inserido no banco de dados.")
            sleep(2)
            return True
        elif count <= 0:
            log.warn("Nao foi possivel inserir o aerodromo")
            input("Pressione enter para continuar...")
            return False
        else:
            log.warn("Erro desconhecido ao inserir o aerodromo.")
            return False
