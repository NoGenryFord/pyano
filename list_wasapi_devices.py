import sounddevice as sd

print("Available WASAPI output devices:")
wasapi_index = None
for i, api in enumerate(sd.query_hostapis()):
    if api['name'].lower().startswith('windows wasapi'):
        wasapi_index = i
        break
if wasapi_index is not None:
    for i, dev in enumerate(sd.query_devices()):
        if dev['hostapi'] == wasapi_index and dev['max_output_channels'] > 0:
            print(f"  {i}: {dev['name']} (max output channels: {dev['max_output_channels']})")
else:
    print("WASAPI hostapi not found! Using default device.")
