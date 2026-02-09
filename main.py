from database import query
from srbc import get_fix_from_table, insert_fix_into_db


def main():
    df = get_fix_from_table()
    insert_fix_into_db(df)
if __name__ == '__main__':
    main()
