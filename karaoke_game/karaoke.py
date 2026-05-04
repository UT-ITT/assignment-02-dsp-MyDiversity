import os
import pyglet
import mido
import numpy as np
import sounddevice as sd
from collections import deque
from pyglet import window, shapes
from pyglet.text import Label
from mido import MidiFile


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

win = window.Window(WINDOW_WIDTH, WINDOW_HEIGHT)

CHUNK_SIZE = 1024 # number of audio frames per buffer
RATE = 44100 # audio sampling rate
CHANNELS = 1 # mono audio

input_device = 2

# Parameters for Note movement
NOTE_SPEED = 320
HIT_X = 100
TRAVEL_TIME = 2

# player parameters
pitch_buffer = deque(maxlen = 5)
player_pitch = 0
score = 0
song_time = 0
player_circle = shapes.Circle(
    x = HIT_X,
    y = 100,
    radius = 10,
    color = (255, 255, 255))

# Labels for score and played notes
score_label = Label("Score: 0", x=10, y=580, font_size=16, color=(255, 255, 255, 255))
target_label = Label("Target: --", x=10, y=560, font_size=16, color=(255, 255, 255, 255))
sung_label = Label("Sung: --", x=10, y=540, font_size=16, color=(255, 255, 255, 255))

# Store every Note of the song as an Event
song = MidiFile('./read_midi/berge.mid')

events = []
t = 0

for note in song:
    t += note.time
    events.append((t, note))

# translate pitch to y position
def pitch_to_y(midi_note):
    MIN_MIDI = 40
    MAX_MIDI = 80

    midi = max(MIN_MIDI,min(MAX_MIDI, midi_note))

    y_min = 50
    y_max = 550

    return y_min + (midi - MIN_MIDI) / (MAX_MIDI - MIN_MIDI) * (y_max - y_min)

# Determine if a note is active or a pause and set timings
total_notes = []
active_notes = {}

for t, event in events:
    if event.type == "note_on" and event.velocity > 0:
        active_notes[event.note] = t

    elif event.type == "note_off":
        start = active_notes.pop(event.note, None)
        if start:
            total_notes.append ({
                "start": start,
                "end": t,
                "midi_note": event.note,
                "scored": False,
            })

for n in total_notes:
    n["spawn"] = n["start"] - TRAVEL_TIME
    n["y"]  = pitch_to_y(n["midi_note"])

def draw_note(n, x):
    shapes.Rectangle(
        x = x,
        y = n["y"],
        width = 20,
        height = 10,
        color = (120,120,120)
    ).draw()

# detect the pitch of the input
def detect_pitch(audio, rate):
    fft = np.fft.rfft(audio)
    frequencies = np.fft.rfftfreq(len(audio), 1 / rate)

    magnitude = np.abs(fft)

    # only keep average vocal range of 80-1000 Hz
    mask = (frequencies >= 80) & (frequencies <= 1000)

    if not np.any(mask):
        return 0
    
    # get array position with the highest value i.e. loudest part
    peak = np.argmax(magnitude[mask])

    # return frequency of the loudest part
    return frequencies[mask][peak]

# audio callback to safe data
def audio_callback(indata, frames, time, status):
    global player_pitch

    audio = indata[:, 0]  # mono

    # reduce player "jitter" due to background noise
    volume_threshold = np.sqrt(np.mean(audio**2))
    if volume_threshold < 0.0003:
        return

    # detect and smoothen pitch
    p = detect_pitch(audio, RATE)
    player_pitch = smooth_hz(p)

# start audio input stream
stream = sd.InputStream(
    device=input_device,
    channels=CHANNELS,
    samplerate=RATE,
    blocksize=CHUNK_SIZE,
    callback=audio_callback,
    latency='low'
)

# log smoothing of the pitch in Hz
def smooth_hz(pitch):
    if pitch > 50:
        pitch_buffer.append(pitch)

    values = np.array(pitch_buffer)
    return np.median(values)

# Map Hz frequency to Midi note
def hz_to_midi(frequency):
    return 69 + 12 * np.log2(frequency / 440)

# Calculate the score
def get_score(note):
    global player_pitch

    player_midi = hz_to_midi(player_pitch)

    if not (note["start"] <= song_time <= note["end"]):
        return 0
    
    error = abs(player_midi - note["midi_note"])
    print(player_midi)
    print(note["midi_note"])
    print(error)

    if error <= 0.4:
        return 100
    if error <= 1:
        return max(int(100 * (0.5-error) / 0.4), 0)
    return 0

# get the current note for the label
def get_current_note():
    for n in total_notes:
        if n["start"] <= song_time <= n["end"]:
            return n["midi_note"]
    # if none is active, get the upcoming note
    upcoming = [n for n in total_notes if n["start"]>song_time]
    if upcoming:
        return min(upcoming, key=lambda x: x["start"])["midi_note"]
    return "--" # if no notes is available
        

def update(dt):
    global song_time, score

    song_time += dt

    # Update player position with smoothing factor to reduce jittering
    target_y = pitch_to_y(hz_to_midi(player_pitch))
    smooth_speed = 8.0  # bigger value increases adjustment speed
    player_circle.y += (target_y - player_circle.y) * smooth_speed * dt

    # move note blocks
    for n in total_notes:

        x = 800 - (song_time - n["spawn"]) * NOTE_SPEED

        # Hit logic
        hit_time = n["spawn"] + (800 - HIT_X) / NOTE_SPEED
        if abs(song_time - hit_time) < 0.1 and not n.get("scored"):
            score += get_score(n)
            n["scored"] = True

    score_label.text = f"Score: {score}"
    target_note = get_current_note()
    target_label.text = f"Target: {target_note}" if target_note != "--" else "Target: --"
    sung_midi = hz_to_midi(player_pitch)
    sung_label.text = f"Sung: {sung_midi:.1f}" if player_pitch > 0 else "Sung: --"

# start game loop
stream.start()
pyglet.clock.schedule_interval(update, 1/60)

@win.event
def on_draw():
    win.clear()
    
    # draw note blocks
    for n in total_notes:
        x = 800 - (song_time - n["spawn"]) * NOTE_SPEED

        if 0 < x < 800:
            draw_note(n, x)
    
    # draw player
    player_circle.draw()

    # draw labels
    score_label.draw()
    target_label.draw()
    sung_label.draw()
            
pyglet.app.run()