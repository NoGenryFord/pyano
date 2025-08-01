import numpy as np
import sounddevice as sd
import keyboard as kb
import time
import os

""" --- ADSR Envelope Block ---
Attack, Decay, Sustain, Release times (seconds) and sustain level
"""
ADSR = {
    'attack': 0.05,   # fast attack
    'decay': 0.1,     # fast decay
    'sustain': 0.7,   # sustain level
    'release': 0.2    # slow release
}


def envelope_adsr(note_on, note_off, t):
    """
    note_on: time when the key is pressed (seconds)
    note_off: time when the key is released (None if still pressed)
    t: time array for the block
    Returns envelope for each sample
    """
    env = np.zeros_like(t)
    for i in range(len(t)):
        time_since_on = t[i] - note_on
        if note_off is None or t[i] < note_off:
            # key is pressed
            if time_since_on < ADSR['attack']:
                env[i] = time_since_on / max(ADSR['attack'], 1e-6)
            elif time_since_on < ADSR['attack'] + ADSR['decay']:
                env[i] = 1 - (time_since_on - ADSR['attack']) / \
                    max(ADSR['decay'], 1e-6) * (1 - ADSR['sustain'])
            else:
                env[i] = ADSR['sustain']
        else:
            # key is released
            time_since_off = t[i] - note_off
            if time_since_off < ADSR['release']:
                # Release
                # Initial level — sustain
                env[i] = ADSR['sustain'] * \
                    (1 - time_since_off / max(ADSR['release'], 1e-6))
            else:
                env[i] = 0.0
    return env
# --- END ADSR Envelope Block ---


# Constants
FS = 44100  # Sample rate

# Frequencies of the sine waves for different notes
# First octave
FREQUENCY_C1 = 261.63  # Frequency of the sine wave (C1 note)
FREQUENCY_C1_Diesis = 277.18  # Frequency of the sine wave (C1# note)
FREQUENCY_D1 = 293.66  # Frequency of the sine wave (D1 note)
FREQUENCY_D1_Diesis = 311.13  # Frequency of the sine wave (D1# note)
FREQUENCY_E1 = 329.63  # Frequency of the sine wave (E1 note)
FREQUENCY_F1 = 349.23  # Frequency of the sine wave (F1 note)
FREQUENCY_F1_Diesis = 369.99  # Frequency of the sine wave (F1# note)
FREQUENCY_G1 = 392.00  # Frequency of the sine wave (G1 note)
FREQUENCY_G1_Diesis = 415.30  # Freqency of the sine wave (G1# note)
FREQUENCY_A1 = 440.00  # Frequency of the sine wave (A1 note)
FREQUENCY_A1_Diesis = 466.16  # Frequency of the sine wave (A1# note)
FREQUENCY_B1 = 493.88  # Frequency of the sine wave (B1 note)
# Second octave
FREQUENCY_C2 = 523.25  # Frequency of the sine wave (C2 note)
FREQUENCY_C2_Diesis = 554.37  # Frequency of the sine wave (C2# note)
FREQUENCY_D2 = 587.33  # Frequency of the sine wave (D2 note)
FREQUENCY_D2_Diesis = 622.25  # Frequency of the sine wave (D2# note)
FREQUENCY_E2 = 659.25  # Frequency of the sine wave (E2 note)
FREQUENCY_F2 = 698.46  # Frequency of the sine wave (F2 note)
FREQUENCY_F2_Diesis = 739.99  # Frequency of the sine wave (F2# note)
FREQUENCY_G2 = 783.99  # Frequency of the sine wave (G2 note)
FREQUENCY_G2_Diesis = 830.61  # Frequency of the sine wave (G2# note)
FREQUENCY_A2 = 880.00  # Frequency of the sine wave (A2 note)
FREQUENCY_A2_Diesis = 932.33  # Frequency of the sine wave (A2# note)
FREQUENCY_B2 = 987.77  # Frequency of the sine wave (B2 note)

# --- Polyphonic Note State Block ---
NOTE_KEYS = {
    # First octave (white keys)
    'z': FREQUENCY_C1,
    'x': FREQUENCY_D1,
    'c': FREQUENCY_E1,
    'v': FREQUENCY_F1,
    'b': FREQUENCY_G1,
    'n': FREQUENCY_A1,
    'm': FREQUENCY_B1,
    # First octave (black keys)
    's': FREQUENCY_C1_Diesis,
    'd': FREQUENCY_D1_Diesis,
    'g': FREQUENCY_F1_Diesis,
    'h': FREQUENCY_G1_Diesis,
    'j': FREQUENCY_A1_Diesis,
    # Second octave (white keys)
    'q': FREQUENCY_C2,
    'w': FREQUENCY_D2,
    'e': FREQUENCY_E2,
    'r': FREQUENCY_F2,
    't': FREQUENCY_G2,
    'y': FREQUENCY_A2,
    'u': FREQUENCY_B2,
    # Second octave (black keys)
    '2': FREQUENCY_C2_Diesis,
    '3': FREQUENCY_D2_Diesis,
    '5': FREQUENCY_F2_Diesis,
    '6': FREQUENCY_G2_Diesis,
    '7': FREQUENCY_A2_Diesis
}

note_states = {k: {'is_pressed': False, 'time_on': 0.0,
                   'time_off': None} for k in NOTE_KEYS}

# --- END Polyphonic Note State Block ---

# Volume of the sine wave

AMPLITUDE = [0.5]  # Volume of the sine wave (mutable for threads)
INSTRUCTION = (
    "Controls:\n"
    "  First octave (white): z x c v b n m ,\n"
    "  First octave (black): s d g h j\n"
    "  Second octave (white): q w e r t y u i\n"
    "  Second octave (black): 2 3 5 6 7\n"
    "  Volume: up/down arrows\n"
    "  Wave type: NumPad 1 — sine, 2 — square, 3 — triangle, 4 — sawtooth\n"
    "  Exit: esc\n"
    "\n"
    "Press and hold keys for notes. Arrow keys — change volume. Exit — 'esc'."
)
print(INSTRUCTION)

phase = 0.0  # Initial phase for the save phase of the sine wave
blocksize = 64  # Size of the audio block to process at a time


last_debug = {'notes': [], 'amp': None, 'wave': None}
WAVE_TYPE = ['sine']  # 'sine', 'square', 'triangle', 'sawtooth'


def callback(outdata, frames, time_info, status):
    global phase, last_debug
    t = (np.arange(frames) + phase) / FS
    # Оновлюємо стан нот
    now = time.time()
    active_notes = []
    for k, freq in NOTE_KEYS.items():
        if kb.is_pressed(k):
            if not note_states[k]['is_pressed']:
                note_states[k]['is_pressed'] = True
                note_states[k]['time_on'] = now
                note_states[k]['time_off'] = None
            active_notes.append((freq, k))
        else:
            if note_states[k]['is_pressed']:
                note_states[k]['is_pressed'] = False
                note_states[k]['time_off'] = now
    # Generate the signal for the active notes
    signal = np.zeros(frames)
    notes_for_debug = []
    for freq, k in active_notes:
        notes_for_debug.append(freq)
        env = envelope_adsr(note_states[k]['time_on'],
                            note_states[k]['time_off'],
                            t + now)
        if WAVE_TYPE[0] == 'sine':
            wave = np.sin(2 * np.pi * freq * t)
        elif WAVE_TYPE[0] == 'square':
            wave = np.sign(np.sin(2 * np.pi * freq * t))
        elif WAVE_TYPE[0] == 'triangle':
            wave = 2 * np.abs(2 * (freq * t - np.floor(freq * t + 0.5))) - 1
        elif WAVE_TYPE[0] == 'sawtooth':
            wave = 2 * (freq * t - np.floor(0.5 + freq * t))
        else:
            wave = np.sin(2 * np.pi * freq * t)
        signal += wave * env
    # Add the waves of notes that have just been released but still have a release
    for k, freq in NOTE_KEYS.items():
        if not note_states[k]['is_pressed'] and note_states[k]['time_off'] is not None:
            # envelope has not yet faded
            env = envelope_adsr(
                note_states[k]['time_on'],
                note_states[k]['time_off'],
                t + now
            )
            if np.any(env > 0):
                if WAVE_TYPE[0] == 'sine':
                    wave = np.sin(2 * np.pi * freq * t)
                elif WAVE_TYPE[0] == 'square':
                    wave = np.sign(np.sin(2 * np.pi * freq * t))
                elif WAVE_TYPE[0] == 'triangle':
                    wave = 2 * \
                        np.abs(2 * (freq * t - np.floor(freq * t + 0.5))) - 1
                elif WAVE_TYPE[0] == 'sawtooth':
                    wave = 2 * (freq * t - np.floor(0.5 + freq * t))
                else:
                    wave = np.sin(2 * np.pi * freq * t)
                signal += wave * env
    if len(active_notes) > 0 or np.any(signal != 0):
        signal = AMPLITUDE[0] * signal
        signal = np.tanh(signal)
        outdata[:, 0] = signal
        real_amp = np.max(np.abs(signal)) if signal.size > 0 else 0.0
        notes = notes_for_debug
    else:
        outdata[:, 0] = 0
        real_amp = 0.0
        notes = []
    phase += frames

    # Debug print only if notes, volume, or wave type changed
    rounded_amp = round(AMPLITUDE[0], 2)
    notes_changed = notes != last_debug['notes']
    amp_changed = rounded_amp != last_debug['amp']
    wave_changed = WAVE_TYPE[0] != last_debug.get('wave')
    if notes_changed:
        phase = 0  # reset phase to avoid click when notes change
    if notes_changed or amp_changed or wave_changed:
        # Form lines for notes, volume, wave
        if notes:
            note_names = []
            freq_to_name = {
                FREQUENCY_C1: 'C1', FREQUENCY_C1_Diesis: 'C#1', FREQUENCY_D1: 'D1', FREQUENCY_D1_Diesis: 'D#1',
                FREQUENCY_E1: 'E1', FREQUENCY_F1: 'F1', FREQUENCY_F1_Diesis: 'F#1', FREQUENCY_G1: 'G1',
                FREQUENCY_G1_Diesis: 'G#1', FREQUENCY_A1: 'A1', FREQUENCY_A1_Diesis: 'A#1', FREQUENCY_B1: 'B1',
                FREQUENCY_C2: 'C2', FREQUENCY_C2_Diesis: 'C#2', FREQUENCY_D2: 'D2', FREQUENCY_D2_Diesis: 'D#2',
                FREQUENCY_E2: 'E2', FREQUENCY_F2: 'F2', FREQUENCY_F2_Diesis: 'F#2', FREQUENCY_G2: 'G2',
                FREQUENCY_G2_Diesis: 'G#2', FREQUENCY_A2: 'A2', FREQUENCY_A2_Diesis: 'A#2', FREQUENCY_B2: 'B2',
                1046.50: 'C3'
            }
            for freq in notes:
                note_names.append(freq_to_name.get(
                    round(freq, 2), freq_to_name.get(freq, str(freq))))
            notes_line = f"Notes: {', '.join(note_names)} | Real amplitude: {real_amp:.2f}"
        else:
            notes_line = "Notes: (none) | Real amplitude: 0.00"
        volume_line = f"Volume: {rounded_amp}"
        wave_names = {
            'sine': 'Sine',
            'square': 'Square',
            'triangle': 'Triangle',
            'sawtooth': 'Sawtooth'
        }
        wave_line = f"Wave: {wave_names.get(WAVE_TYPE[0], WAVE_TYPE[0])}"
        os.system('cls')
        print(INSTRUCTION)
        print(notes_line)
        print(volume_line)
        print(wave_line)
        last_debug['notes'] = notes.copy()
        last_debug['amp'] = rounded_amp
        last_debug['wave'] = WAVE_TYPE[0]


with sd.OutputStream(channels=1, callback=callback, samplerate=FS, blocksize=blocksize, latency='low'):
    while True:
        if kb.is_pressed('esc'):
            break
        # Change volume with arrow keys
        if kb.is_pressed('up'):
            if AMPLITUDE[0] < 1.0:
                AMPLITUDE[0] = min(1.0, AMPLITUDE[0] + 0.05)
                time.sleep(0.08)
        if kb.is_pressed('down'):
            if AMPLITUDE[0] > 0.00:
                AMPLITUDE[0] = max(0.00, AMPLITUDE[0] - 0.05)
                time.sleep(0.08)
        # Switch wave type with NumPad 1/2/3/4
        if kb.is_pressed('num 1'):
            if WAVE_TYPE[0] != 'sine':
                WAVE_TYPE[0] = 'sine'
                phase = 0
                time.sleep(0.15)
        if kb.is_pressed('num 2'):
            if WAVE_TYPE[0] != 'square':
                WAVE_TYPE[0] = 'square'
                phase = 0
                time.sleep(0.15)
        if kb.is_pressed('num 3'):
            if WAVE_TYPE[0] != 'triangle':
                WAVE_TYPE[0] = 'triangle'
                phase = 0
                time.sleep(0.15)
        if kb.is_pressed('num 4'):
            if WAVE_TYPE[0] != 'sawtooth':
                WAVE_TYPE[0] = 'sawtooth'
                phase = 0
                time.sleep(0.15)
        time.sleep(0.005)
