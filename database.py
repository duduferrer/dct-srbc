import os

import mysql.connector

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
        print("Erro SELECT:", e)
        return []

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
    query("SHOW tables")