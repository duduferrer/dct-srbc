from time import sleep

from loggerConfig import log

import mysql.connector
import sys
import config


def connect():
    try:
        conn = mysql.connector.connect(
            host=config.HOST,
            user=config.USER,
            password=config.PASSWORD,
            database=config.DATABASE,
            port=config.PORT
        )
        return conn
    except Exception as e:
        print(e)
        raise

def query(sql, params=None):
    conn = None
    cursor = None
    try:
        conn = connect()
        cursor = conn.cursor(buffered=True)

        cursor.execute(sql, params)
        return cursor.fetchall()

    except Exception as e:
        log.error(f"Erro SELECT: {e}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def execute(sql, params=None):
    conn = None
    cursor = None
    try:
        conn = connect()
        cursor = conn.cursor()

        if isinstance(sql, list):
            for sql_statement, params in sql:
                cursor.execute(sql_statement, params)
        else:
            cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount

    except Exception as e:
        if conn:
            conn.rollback()
        print("Erro DML:", e)
        return 0

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def conn_test():
    try:
        query("SHOW tables")
    except Exception as e:
        log.error(f"Erro ao conectar no banco de dados. Erro: {e}")
        print("Cheque as credenciais de acesso ao banco de dados e se o Banco de dados está rodando.")
        print("Encerrando...")
        sleep(2)
        sys.exit(-1)