// put in before:
// <button id="startBtn">Start Live Transcription</button>
// <button id="stopBtn" disabled>Stop</button>
// <script src="https://cdn.socket.io/4.6.0/socket.io.min.js"></script>
// then to implement:
// <script src="{{ url_for('static', filename='socket.js') }}"></script>

const socket = io();

const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");

const TARGET_SAMPLE_RATE = 16000;

let audioContext = null;
let processor = null;
let source = null;
let micStream = null;
let isRecording = false;

startBtn.addEventListener("click", async () => {
  try {
    await startRecording();
  } catch (err) {
    console.error("Start recording failed:", err);
    stopRecording();
  }
});

stopBtn.addEventListener("click", () => {
  stopRecording();
});

async function startRecording() {
  if (isRecording) return;

  micStream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: false,
      noiseSuppression: false,
      autoGainControl: false,
    },
    video: false,
  });

  audioContext = new (window.AudioContext || window.webkitAudioContext)();
  source = audioContext.createMediaStreamSource(micStream);
  processor = audioContext.createScriptProcessor(4096, 1, 1); //4096 is buffer size

  processor.onaudioprocess = (event) => {
    if (!isRecording) return;

    const inputData = event.inputBuffer.getChannelData(0); //stores audio as a float list
    const downsampled = downsampleBuffer(
      inputData,
      audioContext.sampleRate,
      TARGET_SAMPLE_RATE,
    );

    const pcm16 = convertFloat32ToInt16(downsampled);
    socket.emit("audio_stream", pcm16.buffer); //sends the chunks to audio_stream IMPORTANT ===============
  };

  source.connect(processor);
  processor.connect(audioContext.destination);

  isRecording = true;
  startBtn.disabled = true;
  stopBtn.disabled = false;
}

function stopRecording() {
  isRecording = false;

  if (processor) {
    processor.disconnect();
    processor.onaudioprocess = null;
    processor = null;
  }

  if (source) {
    source.disconnect();
    source = null;
  }

  if (micStream) {
    micStream.getTracks().forEach((track) => track.stop());
    micStream = null;
  }

  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }

  startBtn.disabled = false;
  stopBtn.disabled = true;
}

function downsampleBuffer(buffer, inputSampleRate, outputSampleRate) {
  if (outputSampleRate === inputSampleRate) {
    return buffer;
  }

  const sampleRateRatio = inputSampleRate / outputSampleRate;
  const newLength = Math.round(buffer.length / sampleRateRatio);
  const result = new Float32Array(newLength);

  let offsetResult = 0;
  let offsetBuffer = 0;

  while (offsetResult < result.length) {
    const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
    let accum = 0;
    let count = 0;

    for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
      accum += buffer[i];
      count++;
    }

    result[offsetResult] = count > 0 ? accum / count : 0;
    offsetResult++;
    offsetBuffer = nextOffsetBuffer;
  }

  return result;
}

function convertFloat32ToInt16(buffer) {
  const l = buffer.length;
  const result = new Int16Array(l);

  for (let i = 0; i < l; i++) {
    let s = Math.max(-1, Math.min(1, buffer[i]));
    result[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }

  return result;
}
