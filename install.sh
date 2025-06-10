#!/bin/bash

main() {
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y python3 python3-venv python3-pip

    sudo apt-get install libffi-dev
    sudo apt-get install build-essential
    sudo apt-get install python3-dev

    python3 -m venv ./venv

    ./venv/bin/python -m pip install --upgrade pip
    ./venv/bin/pip install "uvicorn[standard]"
    ./venv/bin/pip install -r requirements.txt

    echo "To start the project run:\nsource ./venv/bin/activate\nuvicorn main:app --reload --port 8001"
}

main