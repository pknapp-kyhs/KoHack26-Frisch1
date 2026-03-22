from flask import *
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.secret_key = 'SecretKey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = 'superSecret123'

db = SQLAlchemy(app)

# Define Classes and Databases
# User class to store user information
#code example:
#   new_user = User(username=u, password=p) # Create a new user instance with the provided username and password
#   db.session.add(new_user) # Add the new user to the session
#   db.session.commit() # Commit the session to save the user to the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    balance = db.Column(db.Float, default=10000.0)
    holdings = db.relationship('Holding', backref='owner', lazy=True)
    @staticmethod
    def findByUsername(username: str):
        return User.query.filter_by(username=username).first()
    # Now what we can do is to get the user obj of the user who just signed in
    # we can just do: session['user'] = User.findByUsername(usernameFromForm)\
    @staticmethod
    def findByID(id: str):
        return User.query.filter_by(id=id).first()

class Holding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    symbol = db.Column(db.String(10))
    quantity = db.Column(db.Integer)

# Make the tables
with app.app_context():
    db.create_all()


@app.route('/')
def main_page():
    logout = request.args.get('logout')
    if logout:
        session.pop('user', None) # Log out the user by removing their ID from the session
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')

        existingUser = User.findByUsername(u)
        if existingUser: # TODO: Find a way to tell user that username is taken
            flash('Username is already taken.', 'error') 
            return render_template('signup.html')
        elif p == '' or u == '':
            flash('Please fill out both username and password.', 'error')
            return render_template('signup.html')

        newUser = User(username=u, password=p)
        db.session.add(newUser)
        db.session.commit()
        session['user'] = newUser.id # Log in the user to flask via ID
        return redirect('/trade')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.findByUsername(username)
        if user and user.password == password:
            session['user'] = user.id # Log in the user to flask via ID
            return redirect('/trade')
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/trade', methods=['GET', 'POST'])
def trade():
    if request.method == 'POST':
        pass
    return render_template('trade.html', user=User.findByID(session['user']))

if __name__ == '__main__':
    app.run(debug=True, port=5001)