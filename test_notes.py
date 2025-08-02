
import numpy as np
import sounddevice as sd
import keyboard as kb
import time
import os

FS = 44100
AMPLITUDE = 0.5
FREQ_MIN = 1
FREQ_MAX = 25000
FREQ_STEP = 1
FREQ_STEP_FAST = 10
frequency = [440.0]  # mutable for callback
print(sd.query_devices())


def callback(outdata, frames, time_info, status):
    t = (np.arange(frames) + callback.phase) / FS
    outdata[:, 0] = AMPLITUDE * np.sin(2 * np.pi * frequency[0] * t)
    callback.phase += frames


callback.phase = 0


def print_freq():
    print(f"Frequency: {frequency[0]:.2f} Hz", end='\r', flush=True)


with sd.OutputStream(channels=1, callback=callback, samplerate=FS, blocksize=1024):
    print_freq()
    while True:
        if kb.is_pressed('esc'):
            break
        step = FREQ_STEP_FAST if kb.is_pressed('ctrl') else FREQ_STEP
        if kb.is_pressed('up'):
            if frequency[0] < FREQ_MAX:
                frequency[0] = min(FREQ_MAX, frequency[0] + step)
                callback.phase = 0  # reset phase to avoid click
                print_freq()
                time.sleep(0.03)
        if kb.is_pressed('down'):
            if frequency[0] > FREQ_MIN:
                frequency[0] = max(FREQ_MIN, frequency[0] - step)
                callback.phase = 0  # reset phase to avoid click
                print_freq()
                time.sleep(0.03)
        time.sleep(0.005)
