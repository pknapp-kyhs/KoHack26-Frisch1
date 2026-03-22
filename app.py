from flask import *
from extensions import db, socketio

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prayertext.db'
app.config['SECRET_KEY'] = 'SecretKey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
socketio.init_app(app)

from sefaria_api.prayermodel import PrayerService, PrayerText, Word

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

@app.route('/highlight', methods=['POST'])
def highlight():
    return render_template("highlight.html")

@app.route('/transcribe', methods=['POST', 'GET'])
def transcribe():
    return render_template("transcribe.html")

@app.route('/EN')
def EN():
    return render_template("EN.html")

@app.route('/HE')
def HE():
    return render_template("HE.html")

from websocket import wbw_socket

if __name__ == '__main__':
    socketio.run(app, debug=True)