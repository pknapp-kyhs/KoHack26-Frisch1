# KolText

An interactive siddur designed to improve focus and engagement during davening.

---

## Overview
KolText is a Flask-based web application built to help users who struggle to stay focused during davening. Whether the difficulty comes from following along in the siddur, maintaining concentration, or hearing the chazzan, KolText provides tools to make the experience more accessible and interactive.

---

## Features
- Live chazzan tracking using microphone input to detect where the chazzan is holding and automatically highlight the corresponding text  
- Word-by-word mode that displays text one word at a time to improve focus and comprehension  
- Shiur transcription by uploading audio files and converting them into text  

---

## Tech Stack
- Backend: Python, Flask  
- Database: SQLite (SQLAlchemy)  
- Realtime: Flask-SocketIO  
- Frontend: HTML, CSS, JavaScript  
- Data Source: Sefaria API (preprocessed and stored locally)  

---

## Project Structure
```
project/
├── app.py
├── extensions.py
├── requirements.txt
├── instance/
│   └── prayertext.db
├── sefaria_api/
│   ├── pray.py
│   ├── prayermodel.py
│   ├── seed.py
│   └── texthelperfunctions.py
├── sofer_ai/
│   └── main.py
├── templates/
│   ├── EN.html
│   ├── HE.html
│   ├── highlight.html
│   ├── index.html
│   ├── layout.html
│   ├── login.html
│   ├── signup.html
│   ├── transcribe.html
│   └── wbw.html
└── websocket/
    ├── app.py
    └── wbw_socket.py
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/koltext.git

# Navigate into the folder
cd koltext

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

---

## Usage
1. Start the server  
2. Open your browser and go to http://127.0.0.1:5000  
3. Log in or sign up  
4. Use the available features:
   - Word-by-word mode (/wbw)
   - Hebrew / English views (/HE, /EN)
   - Transcription tool (/transcribe)

---

## Siddur Data Source

This project uses data originally sourced from the Sefaria API.

Instead of making live API requests, the data was:
1. Retrieved once from the Sefaria API  
2. Processed into structured models (words, phrases, etc.)  
3. Stored locally in a SQLite database  

This design allows the application to:
- Run faster (no external API calls)  
- Work offline  
- Avoid repeated API requests  

---

## External Services

- Sofer AI  
  Used to process and transcribe uploaded audio files of shiurim into text.

---

## Notes
- Passwords are currently stored in plain text and should be secured in the future  
- Debug mode is enabled  
- Sefaria data must be reloaded manually if updates are needed  

---

## Authors
Alex Gershuni 
Ariel Weissman  
Eliezer Dimbert  
Kovi Ressler  
Rafi Mintz  