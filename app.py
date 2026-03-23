from flask import *
from extensions import db, socketio

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prayertext.db'
app.config['SECRET_KEY'] = 'SecretKey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
socketio.init_app(app)

from sefaria_api.prayermodel import PrayerService, PrayerText, HebrewWord, EnglishWord, HebrewPhrase, EnglishPhrase, Line

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
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
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('index'))
    return render_template("signup.html")

@app.route('/wbw', methods=['GET', 'POST'])
def word_by_word():
    services = PrayerService.query.all()
    return render_template("wbw.html", services=services)

@app.route('/highlight', methods=['GET', 'POST'])
def highlight():
    services = PrayerService.query.all()
    return render_template("highlight.html", services=services)

@app.route('/transcribe', methods=['POST', 'GET'])
def transcribe():
    return render_template("transcribe.html")

@app.route('/siddur', methods=['GET', 'POST'])
def siddur():
    services         = PrayerService.query.all()
    selected_service = request.form.get('service', 'Shacharit')
    selected_prayer  = request.form.get('prayer', '')
    selected_lang    = request.form.get('lang', 'vowel')

    service = PrayerService.query.filter_by(name_en=selected_service).first()
    prayers = service.prayer_texts if service else []

    text        = ""
    prayer      = None
    next_prayer = None
    prev_prayer = None

    if selected_prayer and service:
        prayer = PrayerText.query.filter(
            PrayerText.prayer_service_id == service.id,
            PrayerText.en_title == selected_prayer
        ).first()

        if prayer:
            if selected_lang == 'en':
                text = " ".join(w.word for w in prayer.english_words if w.word)
            elif selected_lang == 'vowel':
                text = " ".join(w.word_vowel for w in prayer.hebrew_words if w.word_vowel)
            else:
                text = " ".join(w.word for w in prayer.hebrew_words if w.word)

            prayer_list = [p.en_title for p in prayers]
            current_idx = prayer_list.index(selected_prayer)
            next_prayer = prayer_list[current_idx + 1] if current_idx + 1 < len(prayer_list) else None
            prev_prayer = prayer_list[current_idx - 1] if current_idx > 0 else None

    return render_template('siddur.html',
        services         = services,
        prayers          = prayers,
        selected_service = selected_service,
        selected_prayer  = selected_prayer,
        selected_lang    = selected_lang,
        text             = text,
        prayer           = prayer,
        next_prayer      = next_prayer,
        prev_prayer      = prev_prayer,
    )

# from websocket import wbw_socket, highlight_socket

if __name__ == '__main__':
    socketio.run(app, debug=True)