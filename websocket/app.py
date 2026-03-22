from flask import *
from flask_socketio import *

app = Flask(__name__)
app.config['SECRET_KEY'] = "abc"

socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('socket.html')

@socketio.on('sent_data')
def handle_join(data):
    print("DATA RECIEVED:", data)
    

if __name__ == '__main__':
    app.run(debug=True)