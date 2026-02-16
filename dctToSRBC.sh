#!/bin/bash
cd "$(dirname "$0")" || exit 1
source .venv/bin/activate
pip install -r requirements.txt
python main.py
read -p "Pressione Enter para continuar..."