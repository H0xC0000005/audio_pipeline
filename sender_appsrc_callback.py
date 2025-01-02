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

# Initialize GStreamer
Gst.init(None)

# Constants
RESPEAKER_RATE = 16000
RESPEAKER_CHANNELS = 6
RESPEAKER_WIDTH = 2
RESPEAKER_INDEX = 10
# WARNING: too high refresh rate produce large overhead. better keep tps<=25
CHUNK = 800  # frames per buffer

src1_name = "SRC1"
src2_name = "SRC2"

# Find the USB device for DOA tuning
vendor_id, product_id = 0x2886, 0x0018
dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
if not dev:
    raise RuntimeError(
        f"Cannot fetch usb device. current config: \n"
        f"vendor: {vendor_id}, product: {product_id}"
    )
mic_tuning = Tuning(dev)

# Prepare PyAudio
p = pyaudio.PyAudio()

# We create the GStreamer pipeline
pipeline_str = f"""
rtpbin name=rtpbin \
    appsrc name={src1_name} is-live=true format=time do-timestamp=true \
            ! audioconvert ! audioresample ! audio/x-raw,rate={RESPEAKER_RATE},channels=1 \
            ! queue ! rtpL16pay ! rtpbin.send_rtp_sink_0 \
        rtpbin.send_rtp_src_0 ! udpsink host=192.168.50.159 port=5000 sync=true async=false \
        rtpbin.send_rtcp_src_0 ! udpsink host=192.168.50.159 port=5001 sync=false async=false \
        udpsrc port=5005 ! rtpbin.recv_rtcp_sink_0 \
    appsrc name={src2_name} is-live=true format=time do-timestamp=true \
            ! audioconvert ! audioresample ! audio/x-raw,rate={RESPEAKER_RATE},channels=1 \
            ! queue ! volume volume=0.5 ! audioconvert ! audioresample ! audio/x-raw,rate={RESPEAKER_RATE},channels=1 \
            ! rtpL16pay ! rtpbin.send_rtp_sink_1 \
        rtpbin.send_rtp_src_1 ! udpsink host=192.168.50.159 port=5002 sync=true async=false \
        rtpbin.send_rtcp_src_1 ! udpsink host=192.168.50.159 port=5003 sync=false async=false \
        udpsrc port=5007 ! rtpbin.recv_rtcp_sink_1
"""

pipeline = Gst.parse_launch(pipeline_str)
appsrc1 = pipeline.get_by_name(src1_name)
appsrc2 = pipeline.get_by_name(src2_name)

# Set caps for the appsrc elements (16-bit, mono, 16kHz)
caps = Gst.Caps.from_string(
    f"audio/x-raw,format=S16LE,channels=1,rate={RESPEAKER_RATE},layout=interleaved"
)
appsrc1.set_property("caps", caps)
appsrc2.set_property("caps", caps)

print(f">>>Appsrc1 caps: {appsrc1.get_property('caps')}")
print(f">>>Appsrc2 caps: {appsrc2.get_property('caps')}")


# Simple helper to print the DOA
def print_DOA(mic_tuning: Tuning):
    print(f"The current DOA: {mic_tuning.direction}")


# GStreamer bus message handler
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


# We keep a global counter for demonstration (so we can print every N frames)
callback_counter = 0
start_time = time.time()
_print_interval = 10


def audio_callback(in_data, frame_count, time_info, status_flags):
    """
    Called by PyAudio whenever CHUNK frames are available.
    in_data:  raw byte string of length (frame_count * RESPEAKER_CHANNELS * 2 bytes)
    frame_count: how many frames (samples) in this chunk
    time_info: dictionary with timing information
    status_flags: PaCallbackStatus flags
    """
    global callback_counter, start_time
    times = [time.perf_counter()]

    try:
        # Convert the raw audio to a NumPy int16 array
        raw_samples = np.frombuffer(in_data, dtype=np.int16)

        # We only pan channel 0 (index 0 of 6) in your example
        # ch0: processed audio for ASR; ch1-4: mic's raw audio; ch5: playback(?)
        # NOTE: ch0 has an ~85-105ms delay. use it carefully
        n0 = raw_samples[1::6]
        times.append(time.perf_counter())

        # Get current DOA angle
        cur_DOA_angle = mic_tuning.direction
        times.append(time.perf_counter())

        # Calculate panning gains
        pan_value = math.cos(math.radians(cur_DOA_angle))
        phase_theta = math.pi / 4 * (pan_value + 1)
        left_gain = math.sin(phase_theta)
        right_gain = math.cos(phase_theta)
        times.append(time.perf_counter())

        # Multiply, clip, cast to int16
        left_sig_array = np.clip(n0 * left_gain, -32768, 32767).astype(np.int16)
        right_sig_array = np.clip(n0 * right_gain, -32768, 32767).astype(np.int16)
        times.append(time.perf_counter())

        # Convert to bytes for GStreamer
        left_sig = left_sig_array.tobytes()
        right_sig = right_sig_array.tobytes()
        times.append(time.perf_counter())

        # Occasionally print debug info
        callback_counter += 1
        if callback_counter % _print_interval == 1:
            elapsed = time.time() - start_time
            print(
                f"cnt: {callback_counter}, elapsed: {elapsed:.3f}, emit len: {len(left_sig)}"
            )
            print_DOA(mic_tuning)

        # Push to GStreamer appsrc1 (left) and appsrc2 (right)
        buf_s1 = Gst.Buffer.new_allocate(None, len(left_sig), None)
        buf_s1.fill(0, left_sig)
        buf_s2 = Gst.Buffer.new_allocate(None, len(right_sig), None)
        buf_s2.fill(0, right_sig)

        appsrc1.emit("push-buffer", buf_s1)
        appsrc2.emit("push-buffer", buf_s2)
        times.append(time.perf_counter())
        if callback_counter % _print_interval == 2:
            print(
                f"elapsed times: {[times[i] - times[i-1] for i in range(1, len(times))]}"
            )

    except Exception as e:
        print(f"Audio push error (callback): {e}")

    # We are only recording, not playing, so we return None for out_data
    return (None, pyaudio.paContinue)


if __name__ == "__main__":
    # Main GStreamer loop
    loop = GLib.MainLoop()

    # Attach bus message handler
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", on_message)

    # Start the pipeline
    pipeline.set_state(Gst.State.PLAYING)

    # Open the PyAudio stream in callback mode
    stream = p.open(
        rate=RESPEAKER_RATE,
        format=p.get_format_from_width(RESPEAKER_WIDTH),
        channels=RESPEAKER_CHANNELS,
        input=True,
        input_device_index=RESPEAKER_INDEX,
        frames_per_buffer=CHUNK,
        stream_callback=audio_callback,  # <-- The important part
    )

    # Start the PyAudio stream
    stream.start_stream()

    print("Recording with callback. Press Ctrl+C to stop...")

    try:
        loop.run()
    except KeyboardInterrupt:
        print("Interrupt received, stopping...")
    finally:
        pipeline.set_state(Gst.State.NULL)

        # Clean up PyAudio
        if stream.is_active():
            stream.stop_stream()
        stream.close()
        p.terminate()

        print("Terminated.")