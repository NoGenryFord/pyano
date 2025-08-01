import numpy as np
import sounddevice as sd
import keyboard as kb
import time
import os


# Constants
FS = 44100  # Sample rate

# Frequencies of the sine waves for different notes
FREQUENCY_C1 = 261.63  # Frequency of the sine wave (C1 note)
FREQUENCY_C1_Diesis = 277.18  # Frequency of the sine wave (C1# note)
FREQUENCY_D1 = 293.66  # Frequency of the sine wave (D1 note)
FREQUENCY_D1_Diesis = 311.13  # Frequency of the sine wave (D1# note)
FREQUENCY_E1 = 329.63  # Frequency of the sine wave (E1 note)
FREQUENCY_F1 = 349.23  # Frequency of the sine wave (F1 note)
FREQUENCY_F1_Diesis = 369.99  # Frequency of the sine wave (F1# note)
FREQUENCY_G1 = 392.00  # Frequency of the sine wave (G1 note)
FREQUENCY_G1_Diesis = 415.30  # Frequency of the sine wave (G1# note)
FREQUENCY_A1 = 440.00  # Frequency of the sine wave (A1 note)
FREQUENCY_A1_Diesis = 466.16  # Frequency of the sine wave (A1# note)
FREQUENCY_B1 = 493.88  # Frequency of the sine wave (B1 note)
FREQUENCY_C2 = 523.25  # Frequency of the sine wave (C2 note)


# Volume of the sine wave

AMPLITUDE = [0.5]  # Volume of the sine wave (mutable for threads)
INSTRUCTION = "Press and hold keys for notes. Arrow keys — change volume. Exit — 'esc'."
print(INSTRUCTION)

phase = 0.0  # Initial phase for the save phase of the sine wave
blocksize = 64  # Size of the audio block to process at a time


last_debug = {'notes': [], 'amp': None, 'wave': None}
WAVE_TYPE = ['sine']  # 'sine', 'square', 'triangle', 'sawtooth'


def callback(outdata, frames, time_info, status):
    global phase, last_debug
    t = (np.arange(frames) + phase) / FS
    notes = []  # List to hold frequencies of pressed keys

    # Check which keys are pressed and append their frequencies
    if kb.is_pressed('a'):
        notes.append(FREQUENCY_C1)
    if kb.is_pressed('w'):
        notes.append(FREQUENCY_C1_Diesis)
    if kb.is_pressed('s'):
        notes.append(FREQUENCY_D1)
    if kb.is_pressed('e'):
        notes.append(FREQUENCY_D1_Diesis)
    if kb.is_pressed('d'):
        notes.append(FREQUENCY_E1)
    if kb.is_pressed('f'):
        notes.append(FREQUENCY_F1)
    if kb.is_pressed('t'):
        notes.append(FREQUENCY_F1_Diesis)
    if kb.is_pressed('g'):
        notes.append(FREQUENCY_G1)
    if kb.is_pressed('y'):
        notes.append(FREQUENCY_G1_Diesis)
    if kb.is_pressed('h'):
        notes.append(FREQUENCY_A1)
    if kb.is_pressed('u'):
        notes.append(FREQUENCY_A1_Diesis)
    if kb.is_pressed('j'):
        notes.append(FREQUENCY_B1)
    if kb.is_pressed('k'):
        notes.append(FREQUENCY_C2)

    if notes:
        # Sum all waves, normalize volume
        signal = np.zeros(frames)
        for freq in notes:
            if WAVE_TYPE[0] == 'sine':
                signal += np.sin(2 * np.pi * freq * t)
            elif WAVE_TYPE[0] == 'square':
                signal += np.sign(np.sin(2 * np.pi * freq * t))
            elif WAVE_TYPE[0] == 'triangle':
                signal += 2 * \
                    np.abs(2 * (freq * t - np.floor(freq * t + 0.5))) - 1
            elif WAVE_TYPE[0] == 'sawtooth':
                signal += 2 * (freq * t - np.floor(0.5 + freq * t))
        # signal = AMPLITUDE[0] * signal / max(len(notes), 1)  # normalize by number of notes
        signal = AMPLITUDE[0] * signal
        # Soft clipping using tanh
        signal = np.tanh(signal)
        outdata[:, 0] = signal
        # Calculate real amplitude for debug
        real_amp = np.max(np.abs(signal)) if signal.size > 0 else 0.0
    else:
        outdata[:, 0] = 0
        real_amp = 0.0
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
                FREQUENCY_C1: 'C', FREQUENCY_C1_Diesis: 'C#', FREQUENCY_D1: 'D', FREQUENCY_D1_Diesis: 'D#',
                FREQUENCY_E1: 'E', FREQUENCY_F1: 'F', FREQUENCY_F1_Diesis: 'F#', FREQUENCY_G1: 'G',
                FREQUENCY_G1_Diesis: 'G#', FREQUENCY_A1: 'A', FREQUENCY_A1_Diesis: 'A#', FREQUENCY_B1: 'B', FREQUENCY_C2: 'C2'
            }
            for freq in notes:
                note_names.append(freq_to_name.get(freq, str(freq)))
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
