import sys

from menus import initial_setup
from srbc import get_fix_from_table, insert_fix_into_db
from dotenv import load_dotenv


def main():
    try:
        load_dotenv()
        initial_setup()
        df = get_fix_from_table()
        insert_fix_into_db(df)
    except KeyboardInterrupt:
        print("Encerrando...")
        sys.exit(0)
if __name__ == '__main__':
    main()

    # 0 - LIDAR COM DUPLICATAS
    # 1 - AREAS
    # 2 - Fixos
    # 3 - trjs
    # 4 - exercícios
    # 5 - acft exercícios