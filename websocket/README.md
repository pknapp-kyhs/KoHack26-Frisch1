```bash
pyenv install 3.11.8
# WAIT FOR IT TO FINSIH. TAKES A WHILE
rm -rf .venv
~/.pyenv/versions/3.11.8/bin/python -m venv .venv
source .venv/bin/activate
pip install vosk
Download vosk-model-small-en-us-0.15 from https://alphacephei.com/vosk/models\
Create "model" folder in same dir as app.py
unzip into the folder
move all files in the vosk-model-small-en-us-0.15 folder into the model folder (move one folder up)
python app.py
```

