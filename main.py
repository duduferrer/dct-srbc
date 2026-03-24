import sys

from loggerConfig import log
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