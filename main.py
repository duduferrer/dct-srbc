from srbc import get_fix_from_table, insert_fix_into_db
from dotenv import load_dotenv

def main():
    load_dotenv()
    df = get_fix_from_table()
    insert_fix_into_db(df)
if __name__ == '__main__':
    main()