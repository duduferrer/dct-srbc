import os

import mysql.connector
def connect():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_DATABASE'),
            port=os.getenv('DB_PORT')
        )
        return conn
    except Exception as e:
        print(e)
        raise

def query(query_objects):
    conn = None
    cursor = None
    try:
        conn = connect()
        cursor = conn.cursor(buffered=True)
        if isinstance(query_objects, list):
            for q in query_objects:
                cursor.execute(q[0], q[1])
                print(q[1])
        else:
            cursor.execute(query_objects)
            print(query_objects)
        conn.commit()
        return cursor.fetchall()
    except Exception as e:
        conn.rollback()
        print(e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
