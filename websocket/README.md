```bash
pyenv install 3.11.8
# WAIT FOR IT TO FINSIH. TAKES A WHILE
rm -rf .venv
~/.pyenv/versions/3.11.8/bin/python -m venv .venv
source .venv/bin/activate
pip install vosk
python app.py
```