import sys

from menus import initial_setup
from dotenv import load_dotenv


def main():
    try:
        load_dotenv()
        initial_setup()
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