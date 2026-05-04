import numpy as np
import sounddevice as sd
import time
from collections import deque
from pynput.keyboard import Controller, Key

RATE = 44100
CHUNK_SIZE = 1024
CHANNELS = 1
MIN_VOLUME = 0.0004
MIN_FREQ = 300
MAX_FREQ = 5000
FREQ_CHANGE_THRESHOLD = 30

input_device = 2

keyboard = Controller()
freq_buffer = deque(maxlen = 25)
prev_freq = None
last_trend = None


# detects the pitch of the input device
def detect_pitch(audio, rate):
    fft =np.fft.rfft(audio)
    freqs = np.fft.rfftfreq(len(audio), 1/ rate)
    magnitude = np.abs(fft)

    mask = (freqs >= MIN_FREQ) & (freqs <= MAX_FREQ)
    if not np.any(mask):
        return 0
    
    peak = np.argmax(magnitude[mask])
    return freqs[mask][peak]

def press_key(key):
    keyboard.press(key)
    keyboard.release(key)

def audio_callback(indata, frames, time, status):
    global prev_freq, last_trend, trend_stability

    audio = indata[:, 0]

    volume = np.sqrt(np.mean(audio ** 2))

    # only pass if input surpasses a certain volume
    if volume < MIN_VOLUME:
        return
    
    pitch = detect_pitch(audio, RATE)

    if pitch <= 0:
        return
    
    freq_buffer.append(pitch)
    current_freq = float(np.median(freq_buffer))
    
    if prev_freq is not None:
        diff = current_freq - prev_freq
        if abs(diff) > FREQ_CHANGE_THRESHOLD:
            trend = "up" if diff > 0 else "down"

            # only click if the trend really changes
            if last_trend and trend != last_trend:
                if trend == "up":
                    press_key(Key.up)
                    print("Key Up pressed")

                elif trend == "down":
                    press_key(Key.down)
                    print("Key Down pressed")

            last_trend = trend

    prev_freq = current_freq

# start audio input stream
stream = sd.InputStream(
    device=input_device,
    channels=CHANNELS,
    samplerate=RATE,
    blocksize=CHUNK_SIZE,
    callback=audio_callback,
    latency='low'
)

# run program for 30 seconds
with stream:
    print("Whistle for Input! - Ctrl + C to Stop")
    time.sleep(30)