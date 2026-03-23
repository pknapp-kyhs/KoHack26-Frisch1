from flask import *
from extensions import db, socketio  # <-- Use this instance!
import json
import threading
# DO NOT import SocketIO here.

from vosk import Model, KaldiRecognizer
from sefaria_api.prayermodel import PrayerService, PrayerText, HebrewWord, EnglishWord, HebrewPhrase, EnglishPhrase, Line
from werkzeug.security import generate_password_hash, check_password_hash
import re

import sys
import os
websocket_path = os.path.join(os.getcwd(), 'websocket')
print(f"DEBUG: Checking for websocket folder at: {websocket_path}", file=sys.stderr, flush=True)
print(f"DEBUG: Folder exists: {os.path.exists(websocket_path)}", file=sys.stderr, flush=True)

try:
    # Adding the websocket folder to the system path so Python can find wbw_socket.py
    sys.path.append(websocket_path)
    import wbw_socket
    print("DEBUG: wbw_socket successfully imported using sys.path", file=sys.stderr, flush=True)
except Exception as e:
    print(f"DEBUG: Critical Import Error: {e}", file=sys.stderr, flush=True)
    # This will print the full error stack trace to help us see where it died
    import traceback
    traceback.print_exc()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prayertext.db'
app.config['SECRET_KEY'] = 'SecretKey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


model = Model('websocket/model')

db.init_app(app)

# 1. INITIALIZE the existing socketio instance instead of overwriting it
socketio.init_app(
    app,
    cors_allowed_origins="*", 
    async_mode="threading"
)

model = Model('websocket/model')

# Password validation: minimum 8 characters, at least one uppercase letter and one digit
def is_valid_password(password):
    pattern = r'^(?=.*[A-Z])(?=.*\d).{8,}$'
    return re.match(pattern, password)

# User model for authentication
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

# 2. IMPORT your external socket files so their events register!
import websocket.wbw_socket
import websocket.highlight_socket  # If you are using this one too

with app.app_context():
    db.create_all()

# One recognizer + one lock per connected client
recognizers = {}
recognizer_locks = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        # Validate hashed password
        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('index'))

    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))

        if not is_valid_password(password):
            flash('Password must be at least 8 characters long, contain at least one uppercase letter and one number')
            return redirect(url_for('signup'))

        # Store hashed password
        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        session['username'] = username
        return redirect(url_for('index'))

    return render_template("signup.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/delete', methods=['GET', 'POST'])
def delete_account():
    if request.method == 'POST':
        if 'username' in session:
            user = User.query.filter_by(username=session['username']).first()
            if user:
                db.session.delete(user)
                db.session.commit()
            session.clear()
        return redirect(url_for('index'))

    return render_template("delete.html")


@app.route('/wbw', methods=['GET', 'POST'])
def word_by_word():
    if 'username' not in session:
        flash('Please log in to access the word-by-word feature')
        return redirect(url_for('index'))

    services = PrayerService.query.all()
    print('DEBUG: USER VISITED ')
    return render_template("wbw.html", services=services)

@app.route('/highlight', methods=['GET', 'POST'])
def highlight():
    if 'username' not in session:
        flash('Please log in to access the Follow the Chazzan feature')
        return redirect(url_for('index'))

    services = PrayerService.query.all()
    return render_template("highlight.html", services=services)

from sofer_ai.SoferAPIManager import SoferAPIManager
soferManager = SoferAPIManager()
transcription_results = {}
@app.route('/transcribe', methods=['POST', 'GET'])
def transcribe():
    if 'username' not in session:
        flash('Please log in to access the transcription feature')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        import os
        import threading
        if 'audio' in request.files:
            uploadedFile = request.files.get('audio')
            
            if uploadedFile and uploadedFile.filename:
                upload_folder = os.path.join('sofer_ai', 'uploadedFiles')
                os.makedirs(upload_folder, exist_ok=True)
                
                filePath = os.path.join(upload_folder, uploadedFile.filename)
                uploadedFile.save(filePath)

                username = session['username']
                def on_complete(text):
                    transcription_results[username] = text
                    socketio.emit('transcription_ready', {'text': text})
                    
                thread = threading.Thread(target=soferManager.runFullProcessAndCallback, args=(filePath, on_complete))
                thread.daemon = True
                thread.start()
                return render_template("transcribe.html", waiting=True)
        
        # 2. Handle Live Recording POST requests
        elif 'Start_Record' in request.form:
            print("DEBUG: User clicked Start Recording")
            return render_template("transcribe.html")
            
        elif 'Stop_Record' in request.form:
            print("DEBUG: User clicked Stop Recording")
            return render_template("transcribe.html")

    # If it's a GET request (or form fell through), just load the page normally
    return render_template("transcribe.html", transcript=transcription_results.get(session['username']))

@app.route('/siddur', methods=['GET', 'POST'])
def siddur():
    if 'username' not in session:
        flash('Please log in to access the siddur')
        return redirect(url_for('index'))

    # Fetch all available prayer services (e.g., Shacharit, Mincha, Maariv)
    services = PrayerService.query.all()

    # Read selection from form or use defaults.
    selected_service = request.form.get('service', 'Shacharit')
    selected_prayer = request.form.get('prayer', '')
    selected_lang = request.form.get('lang', 'vowel')

    # Find service object and all prayers under that service.
    service = PrayerService.query.filter_by(name_en=selected_service).first()
    prayers = service.prayer_texts if service else []

    # defaults for template rendering
    text = ""
    prayer = None
    next_prayer = None
    prev_prayer = None

    # If a prayer is selected, fetch that prayer row and build output text.
    if selected_prayer and service:
        prayer = PrayerText.query.filter(
            PrayerText.prayer_service_id == service.id,
            PrayerText.en_title == selected_prayer
        ).first()

        if prayer:
            # Determine display text by language choice.
            if selected_lang == 'en':
                # English prayer text from associated EnglishWord rows
                text = " ".join(w.word for w in prayer.english_words if w.word)
            elif selected_lang == 'vowel':
                # Hebrew text with niqqud from HebrewWord rows
                text = " ".join(w.word_vowel for w in prayer.hebrew_words if w.word_vowel)
            else:
                # Hebrew text without niqqud
                text = " ".join(w.word for w in prayer.hebrew_words if w.word)

            # Build navigation links to previous/next prayer in selected service.
            prayer_list = [p.en_title for p in prayers]
            current_idx = prayer_list.index(selected_prayer)

            next_prayer = prayer_list[current_idx + 1] if current_idx + 1 < len(prayer_list) else None
            prev_prayer = prayer_list[current_idx - 1] if current_idx > 0 else None

    # Render siddur page with the computed state.
    return render_template(
        'siddur.html',
        services=services,
        prayers=prayers,
        selected_service=selected_service,
        selected_prayer=selected_prayer,
        selected_lang=selected_lang,
        text=text,
        prayer=prayer,
        next_prayer=next_prayer,
        prev_prayer=prev_prayer,
    )

#socket code ====
@socketio.on('connect')
def handle_connect():
    sid = request.sid
    recognizers[sid] = KaldiRecognizer(model, 16000)
    recognizers[sid].SetWords(True)
    recognizer_locks[sid] = threading.Lock() #ensures no recognizers get mixed up

@socketio.on("audio_stream")
def handle_audio_stream(audio_chunk):
    sid = request.sid
    recognizer = recognizers.get(sid)
    lock = recognizer_locks.get(sid)

    with lock:
        if recognizer.AcceptWaveform(audio_chunk): #check if chunk contains a full word or not
            result = json.loads(recognizer.Result())
            text = result.get("text", "").strip()
            if text:
                #FINAL TRANSCRIPTION = text
                socketio.emit("live_transcription_phrase", {"text": text}, to=sid)

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    recognizers.pop(sid, None)
    recognizer_locks.pop(sid, None)

if __name__ == '__main__':
    import sys
    import jinja2

    # Optional extra template directory
    if len(sys.argv) > 1:
        extra_templates = sys.argv[1]
        app.jinja_loader = jinja2.ChoiceLoader([
            jinja2.FileSystemLoader(extra_templates),
            app.jinja_loader,
        ])
    socketio.run(app, host="0.0.0.0", port=5003, debug=True)
