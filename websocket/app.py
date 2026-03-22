from flask import *
from flask_socketio import *
import base64
import speech_recognition as sr
import os
from concurrent.futures import ThreadPoolExecutor
import io
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = "abc"

socketio = SocketIO(app)

executor = ThreadPoolExecutor(max_workers=10)

sessions = {}


def transcribe_audio_chunk(audio_data):
    """Transcribe audio chunk from bytes data"""
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_data)) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"Transcription API Error: {e}")
        return None


@app.route('/')
def index():
    return render_template('socket.html')


@socketio.on('audio_session_start')
def handle_session_start(data):
    """Start a continuous audio streaming session"""
    session_id = data['sessionId']
    sessions[session_id] = {
        'audio_buffer': b'',
        'lock': threading.Lock()
    }
    print(f"[SESSION START] {session_id}")


@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    """Receive continuous audio chunks and transcribe in background"""
    session_id = data['sessionId']
    chunk_data = data['chunk']
    
    if session_id not in sessions:
        return
    
    try:
        # Decode chunk
        decoded_chunk = base64.b64decode(chunk_data)
        
        with sessions[session_id]['lock']:
            sessions[session_id]['audio_buffer'] += decoded_chunk
        
        # Check if buffer is large enough to transcribe (e.g., 2+ seconds of audio)
        # 16kHz * 2 bytes per sample * 2 seconds = ~64KB minimum
        if len(sessions[session_id]['audio_buffer']) >= 65536:
            with sessions[session_id]['lock']:
                audio_to_transcribe = sessions[session_id]['audio_buffer']
                sessions[session_id]['audio_buffer'] = b''
            
            # Transcribe in background without blocking
            def transcribe_background():
                text = transcribe_audio_chunk(audio_to_transcribe)
                if text:
                    print(f"[TRANSCRIBED] {text}")
            
            executor.submit(transcribe_background)
            
    except Exception as e:
        print(f"Error handling audio chunk: {e}")


@socketio.on('audio_session_end')
def handle_session_end(data):
    """End the streaming session (if needed)"""
    session_id = data['sessionId']
    if session_id in sessions:
        del sessions[session_id]
        print(f"[SESSION END] {session_id}")


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)