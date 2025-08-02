import sounddevice as sd

device_index = 13  # Встановіть потрібний індекс
info = sd.query_devices(device_index)
print(f"Device: {info['name']}")
print(f"Default sample rate: {info['default_samplerate']}")
