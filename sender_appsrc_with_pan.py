import math
import gi
import numpy as np
import threading

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst, GLib
import time
import pyaudio
import usb.core
import usb.util

from tuning import Tuning

# GObject.threads_init()
Gst.init(None)

RESPEAKER_RATE = 16000
RESPEAKER_CHANNELS = 6
RESPEAKER_WIDTH = 2
RESPEAKER_INDEX = 10
CHUNK = 1600

src1_name = "SRC1"
src2_name = "SRC2"

p = pyaudio.PyAudio()
dev: usb.core.Device
vendor_id, product_id = 0x2886, 0x0018
dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
if dev:
    mic_tuning = Tuning(dev)
else:
    raise RuntimeError(
        f"Cannot fetch usb device. current config: \n\
                       vendor: {vendor_id}, product: {product_id}"
    )

stream = p.open(
    rate=RESPEAKER_RATE,
    format=p.get_format_from_width(RESPEAKER_WIDTH),
    channels=RESPEAKER_CHANNELS,
    input=True,
    input_device_index=RESPEAKER_INDEX,
)

pipeline_str = f"""
rtpbin name=rtpbin \
    appsrc name={src1_name} is-live=true format=time do-timestamp=true \
            ! audioconvert ! audioresample ! audio/x-raw,rate={RESPEAKER_RATE},channels=1 ! queue ! rtpL16pay ! rtpbin.send_rtp_sink_0 \
        rtpbin.send_rtp_src_0 ! udpsink host=192.168.50.159 port=5000 sync=true async=false \
        rtpbin.send_rtcp_src_0 ! udpsink host=192.168.50.159 port=5001 sync=false async=false \
        udpsrc port=5005 ! rtpbin.recv_rtcp_sink_0 \
    appsrc name={src2_name} is-live=true format=time do-timestamp=true \
            ! audioconvert ! audioresample ! audio/x-raw,rate={RESPEAKER_RATE},channels=1 \
        ! queue ! volume volume=0.5 ! audioconvert ! audioresample ! audio/x-raw,rate={RESPEAKER_RATE},channels=1 ! rtpL16pay ! rtpbin.send_rtp_sink_1 \
        rtpbin.send_rtp_src_1 ! udpsink host=192.168.50.159 port=5002 sync=true async=false \
        rtpbin.send_rtcp_src_1 ! udpsink host=192.168.50.159 port=5003 sync=false async=false \
        udpsrc port=5007 ! rtpbin.recv_rtcp_sink_1 
"""

pipeline = Gst.parse_launch(pipeline_str)
appsrc1 = pipeline.get_by_name(src1_name)
appsrc2 = pipeline.get_by_name(src2_name)

caps = Gst.Caps.from_string(
    f"audio/x-raw,format=S16LE,channels=1,rate={RESPEAKER_RATE},layout=interleaved"
)
appsrc1.set_property("caps", caps)
appsrc2.set_property("caps", caps)

print(f">>>Appsrc1 caps: {appsrc1.get_property('caps')}")
print(f">>>Appsrc2 caps: {appsrc2.get_property('caps')}")


def print_DOA(mic_tuning: Tuning):
    print(f"The current DOA: {mic_tuning.direction}")


# Bus message handler
def on_message(bus, message):
    t = message.type
    if t == Gst.MessageType.EOS:
        print("End-of-stream")
        pipeline.set_state(Gst.State.NULL)
        loop.quit()
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(f"Error: {err}, {debug}")
        pipeline.set_state(Gst.State.NULL)
        loop.quit()


# Audio pushing thread
def audio_pusher():
    cnt = 1
    start_time = time.time()
    while True:
        try:
            data = stream.read(CHUNK)
            n0 = np.frombuffer(data, dtype=np.int16)[0::6]
            cur_DOA_angle = mic_tuning.direction  # in degree

            pan_value = math.cos(math.radians(cur_DOA_angle))
            phase_theta = math.pi / 4 * (pan_value + 1)
            left_gain = math.cos(phase_theta)
            right_gain = math.sin(phase_theta)

            left_sig_array = np.clip(n0 * left_gain, -32768, 32767).astype(np.int16)
            left_sig = left_sig_array.tobytes()

            right_sig_array = np.clip(n0 * right_gain, -32768, 32767).astype(np.int16)
            right_sig = right_sig_array.tobytes()

            if cnt % 50 == 1:
                print(
                    f"cnt: {cnt}, elapsed: {time.time() - start_time}, emit len: {len(left_sig)}",
                    flush=True,
                )
                print_DOA(mic_tuning)

            buf_s1 = Gst.Buffer.new_allocate(None, len(left_sig), None)
            buf_s1.fill(0, left_sig)
            appsrc1.emit("push-buffer", buf_s1)

            buf_s2 = Gst.Buffer.new_allocate(None, len(right_sig), None)
            buf_s2.fill(0, right_sig)
            appsrc2.emit("push-buffer", buf_s2)
            cnt += 1
        except Exception as e:
            print(f"Audio push error: {e}")
            break


# Create GStreamer main loop
loop = GLib.MainLoop()

# Attach bus message handler
bus = pipeline.get_bus()
bus.add_signal_watch()
bus.connect("message", on_message)

# Start pipeline
pipeline.set_state(Gst.State.PLAYING)

# Start audio pusher in a separate thread
pusher_thread = threading.Thread(target=audio_pusher, daemon=True)
pusher_thread.start()

try:
    loop.run()
except KeyboardInterrupt:
    print("Interrupt received, stopping...")
finally:
    pipeline.set_state(Gst.State.NULL)
    stream.close()
    p.terminate()
