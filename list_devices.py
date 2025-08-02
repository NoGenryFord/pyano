import sounddevice as sd

# --- List available WASAPI output devices
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


# --- List available host APIs and ASIO devices
print("\nAvailable audio devices:")
print("Available hostapis:")
for i, api in enumerate(sd.query_hostapis()):
    print(f"{i}: {api['name']}")

asio_index = None
for i, api in enumerate(sd.query_hostapis()):
    if "asio" in api['name'].lower():
        asio_index = i
        print(f"ASIO hostapi index: {asio_index}")

if asio_index is not None:
    print("Available ASIO output devices:")
    for i, dev in enumerate(sd.query_devices()):
        if dev['hostapi'] == asio_index and dev['max_output_channels'] > 0:
            print(f"  {i}: {dev['name']} (max output channels: {dev['max_output_channels']})")
else:
    print("ASIO hostapi not found!")


# --- List available host APIs and ASIO devices
print("HostAPIs:")
for i, api in enumerate(sd.query_hostapis()):
    print(f"{i}: {api['name']}")

asio_index = None
for i, api in enumerate(sd.query_hostapis()):
    if "asio" in api['name'].lower():
        asio_index = i
        print(f"ASIO hostapi index: {asio_index}")

if asio_index is not None:
    print("Available ASIO output devices:")
    for i, dev in enumerate(sd.query_devices()):
        if dev['hostapi'] == asio_index and dev['max_output_channels'] > 0:
            print(f"  {i}: {dev['name']} (max output channels: {dev['max_output_channels']})")
else:
    print("ASIO hostapi not found!")