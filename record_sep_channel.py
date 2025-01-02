import pyaudio
import wave
import numpy as np
from tuning import Tuning
import usb.core
import usb.util
import time

RESPEAKER_RATE = 16000
RESPEAKER_CHANNELS = 6  # change base on firmwares, 1_channel_firmware.bin as 1 or 6_channels_firmware.bin as 6
RESPEAKER_WIDTH = 2
# run getDeviceInfo.py to get index
RESPEAKER_INDEX = 10  # refer to input device id
CHUNK = 1024
RECORD_SECONDS = 4
WAVE_OUTPUT_FILENAME = "shiyishi.wav"

p = pyaudio.PyAudio()
dev: usb.core.Device
dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)


def print_DOA(mic_tuning: Tuning):
    print(f"The current DOA: {mic_tuning.direction}")


if dev:
    Mic_tuning = Tuning(dev)

stream = p.open(
    rate=RESPEAKER_RATE,
    format=p.get_format_from_width(RESPEAKER_WIDTH),
    channels=RESPEAKER_CHANNELS,
    input=True,
    input_device_index=RESPEAKER_INDEX,
)

print("* recording")

frames = []

# len(a) = CHUNK, len(data) = CHUNK*12; int width = 2bytes
for i in range(0, int(RESPEAKER_RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    # extract channel 0 data from 6 channels, if you want to extract channel 1, please change to [1::6]
    a = np.frombuffer(data, dtype=np.int16)[0::6]
    # print(f"a: {a}, type: {type(a)}, length: {len(a)}")
    # print(f"data: {data}, type: {type(data)}, length: {len(data)}")
    frames.append(a.tobytes())
    if i % 10 == 0 and dev:
        print_DOA(Mic_tuning)
    # break

print("* done recording")

stream.stop_stream()
stream.close()
p.terminate()

wf = wave.open(WAVE_OUTPUT_FILENAME, "wb")
wf.setnchannels(1)
wf.setsampwidth(p.get_sample_size(p.get_format_from_width(RESPEAKER_WIDTH)))
wf.setframerate(RESPEAKER_RATE)
wf.writeframes(b"".join(frames))
wf.close()
