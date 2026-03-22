import os
import json
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from vosk import Model, KaldiRecognizer

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 1. Load the Vosk model ONCE when the server starts
# Make sure you have a folder named "model" in your project directory
model_path = "model" 
if not os.path.exists(model_path):
    print(f"Model not found at {model_path}. Please download and unpack a Vosk model.")
    exit(1)

model = Model(model_path)

# Dictionary to hold a recognizer for each connected user
recognizers = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    print(f"User connected: {sid}")
    # 2. Create a new recognizer for this user
    # The sample rate (16000) must match the audio from the frontend
    recognizers[sid] = KaldiRecognizer(model, 16000)

@socketio.on('audio_stream')
def handle_audio_stream(audio_chunk):
    sid = request.sid
    recognizer = recognizers.get(sid)

    if not recognizer:
        return

    # 3. Feed the audio chunk into the recognizer
    if recognizer.AcceptWaveform(audio_chunk):
        # User has likely paused. Get the final result.
        result_json = recognizer.Result()
        result_text = json.loads(result_json).get("text", "")
        if result_text:
            print(f"Final result for {sid}: {result_text}")
            socketio.emit('transcription_result', {'text': result_text + " "}, to=sid)
    else:
        # User is still speaking. Get a partial result.
        partial_json = recognizer.PartialResult()
        partial_text = json.loads(partial_json).get("partial", "")
        if partial_text:
            # You can optionally send these back for an "as-you-type" experience
            print(f"Partial result for {sid}: {partial_text}")
            pass

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    print(f"User disconnected: {sid}")
    # 4. Clean up the recognizer for the disconnected user
    if sid in recognizers:
        del recognizers[sid]

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)