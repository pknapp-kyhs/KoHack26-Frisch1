import os
import json
import threading
import faulthandler

from flask import Flask, render_template, request
from flask_socketio import SocketIO
from vosk import Model, KaldiRecognizer

faulthandler.enable()

app = Flask(__name__)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model")

if not os.path.isdir(MODEL_PATH):
    raise FileNotFoundError(
        f"Vosk model folder not found at: {MODEL_PATH}\n"
        "Put the extracted model files inside websocket/model"
    )

print(f"Loading model from: {MODEL_PATH}")
model = Model(MODEL_PATH)

# One recognizer + one lock per connected client
recognizers = {}
recognizer_locks = {}


@app.route("/")
def index():
    return render_template("socket.html")


@socketio.on("connect")
def handle_connect():
    sid = request.sid
    print(f"User connected: {sid}")

    recognizers[sid] = KaldiRecognizer(model, 16000)
    recognizers[sid].SetWords(True)
    recognizer_locks[sid] = threading.Lock()

    print(f"Recognizer created for {sid}")


@socketio.on("audio_stream")
def handle_audio_stream(audio_chunk):
    sid = request.sid
    recognizer = recognizers.get(sid)
    lock = recognizer_locks.get(sid)

    if recognizer is None or lock is None:
        print(f"No recognizer/lock found for {sid}")
        return

    if not isinstance(audio_chunk, (bytes, bytearray)):
        print(f"Unexpected audio type from {sid}: {type(audio_chunk)}")
        return

    # Prevent concurrent calls into Vosk native code
    with lock:
        try:
            if recognizer.AcceptWaveform(audio_chunk):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()

                if text:
                    print(f"Final result for {sid}: {text}")
                    socketio.emit("transcription_result", {"text": text + " "}, to=sid)
            else:
                partial = json.loads(recognizer.PartialResult())
                partial_text = partial.get("partial", "").strip()

                if partial_text:
                    socketio.emit("partial_transcription", {"text": partial_text}, to=sid)

        except Exception as e:
            print(f"Error while processing audio for {sid}: {e}")


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    print(f"User disconnected: {sid}")
    recognizers.pop(sid, None)
    recognizer_locks.pop(sid, None)


if __name__ == "__main__":
    socketio.run(
        app,
        host="127.0.0.1",
        port=5003,
        debug=False,
        use_reloader=False
    )