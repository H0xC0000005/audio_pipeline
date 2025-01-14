import math
import sys
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
from CONFIG import *

# Initialize GStreamer
Gst.init(None)

dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
if not dev:
    raise RuntimeError(
        f"Cannot fetch usb device. current config: \n"
        f"vendor: {VENDOR_ID}, product: {PRODUCT_ID}"
    )
mic_tuning = Tuning(dev)

# Prepare PyAudio
p = pyaudio.PyAudio()

SRC_NAME = "stereo_src"
audio_rate = RESPEAKER_RATE
if USE_PROCESSED:
    VOLUMN = 1.0
else:
    VOLUMN = 2.0

# pipeline_str = f"""
# rtpbin name=rtpbin latency={RTP_LATENCY}
#     appsrc name={SRC_NAME} is-live=true format=time do-timestamp=true
#         ! audioconvert ! audioresample ! audio/x-raw,rate={audio_rate},channels=2,format=S16LE,layout=interleaved
#         ! queue ! audioconvert ! audioresample 
#         ! rtpL16pay
#         ! rtpbin.send_rtp_sink_0
#     rtpbin.send_rtp_src_0
#         ! udpsink host={IP} port=5000 sync=true async=false
#     rtpbin.send_rtcp_src_0
#         ! udpsink host={IP} port=5001 sync=false async=false
#     udpsrc port=5005
#         ! rtpbin.recv_rtcp_sink_0
# """

pipeline_str = f"""
rtpbin name=rtpbin latency={RTP_LATENCY}
    appsrc name={SRC_NAME} is-live=true format=time do-timestamp=true
        ! audioconvert ! audioresample ! audio/x-raw,rate={audio_rate},channels=2,format=S16LE,layout=interleaved
        ! queue max-size-time=30000000 max-size-buffers=0 max-size-bytes=0 leaky=2 
        ! audioconvert ! audioresample 
        ! rtpL16pay
        ! rtpbin.send_rtp_sink_0
    rtpbin.send_rtp_src_0
        ! udpsink host={IP} port=5000 sync=true async=false
    rtpbin.send_rtcp_src_0
        ! udpsink host={IP} port=5001 sync=false async=false
    udpsrc port=5005
        ! rtpbin.recv_rtcp_sink_0
"""

print(f">>>> launching pipeline:\n{pipeline_str}")

pipeline = Gst.parse_launch(pipeline_str)
appsrc = pipeline.get_by_name(SRC_NAME)

# We have 2 channels, 16-bit, same sample rate as mic
caps = Gst.Caps.from_string(
    f"audio/x-raw,format=S16LE,channels=2,rate={RESPEAKER_RATE},layout=interleaved"
)
appsrc.set_property("caps", caps)


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
        try:
            # err, debug = message.parse_error()
            # print(f"Error: {err}, {debug}")
            pipeline.set_state(Gst.State.NULL)
            loop.quit()
        except SystemError as e:
            print(f"got system error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"got error received: {e}")
            raise e


callback_counter = 0
start_time = time.time()
_print_interval = 100


def audio_callback(in_data, frame_count, time_info, status_flags):
    global callback_counter, start_time
    times = [time.perf_counter()]
    try:
        # Convert the raw audio to a NumPy int16 array
        raw_samples = np.frombuffer(in_data, dtype=np.int16)

        # ch0: processed audio; ch1-4: mic raw audio, etc.
        # pick a single channel for "source data"
        if USE_PROCESSED or RESPEAKER_CHANNELS < 2:
            n0 = raw_samples[
                0::RESPEAKER_CHANNELS
            ]  # processed channel or the single channel
        else:
            n0 = raw_samples[1::RESPEAKER_CHANNELS]  # raw mic channel

        # If DOA is used, compute left/right
        if USE_DOA:
            cur_DOA_angle = mic_tuning.direction
            pan_value = math.cos(math.radians(cur_DOA_angle))
            phase_theta = math.pi / 4 * (pan_value + 1)
            left_gain = math.cos(phase_theta) * VOLUMN
            right_gain = math.sin(phase_theta) * VOLUMN
            left_sig_array = np.clip(n0 * left_gain, -32768, 32767).astype(np.int16)
            right_sig_array = np.clip(n0 * right_gain, -32768, 32767).astype(np.int16)
        else:
            left_sig_array = n0
            right_sig_array = n0
        times.append(time.perf_counter())

        # Interleave [L, R, L, R, ...]
        interleaved = np.zeros(2 * len(left_sig_array), dtype=np.int16)  # 2 channels
        interleaved[0::2] = left_sig_array
        interleaved[1::2] = right_sig_array
        interleaved_bytes = interleaved.tobytes()

        # Occasionally print debug info
        callback_counter += 1
        if callback_counter % _print_interval == 1:
            elapsed = time.time() - start_time
            print(
                f"cnt: {callback_counter}, elapsed: {elapsed:.3f}, push len: {len(interleaved_bytes)}"
            )
            if USE_DOA:
                print_DOA(mic_tuning)
            else:
                print("not using DOA. just streaming single mic (2-ch identical)")
            if USE_PROCESSED or RESPEAKER_CHANNELS < 2:
                print(f"using processed audio or the single channel firmware.")
            else:
                print(f"using raw record of mic 1.")

        times.append(time.perf_counter())
        # Push one 2-channel buffer to GStreamer
        buf_s = Gst.Buffer.new_allocate(None, len(interleaved_bytes), None)
        buf_s.fill(0, interleaved_bytes)
        appsrc.emit("push-buffer", buf_s)
        times.append(time.perf_counter())

        if callback_counter % _print_interval == 2:
            print(
                f"elapsed times: {[times[i] - times[i-1] for i in range(1, len(times))]}"
            )

    except Exception as e:
        print(f"Audio push error (callback): {e}")

    return (None, pyaudio.paContinue)


if __name__ == "__main__":
    # Main loop
    loop = GLib.MainLoop()

    # Attach bus message handler
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", on_message)

    # Start pipeline
    pipeline.set_state(Gst.State.PLAYING)

    # Setup PyAudio stream
    rate = RESPEAKER_RATE
    format = p.get_format_from_width(RESPEAKER_WIDTH)
    channels = RESPEAKER_CHANNELS
    frames_per_buffer = CHUNK
    if RESPEAKER_DEVICE_INDEX is None:
        RESPEAKER_DEVICE_INDEX = get_respeaker_index(p)
        if RESPEAKER_DEVICE_INDEX is None:
            raise RuntimeError(f"invalid RESPEAKER_INDEX: {RESPEAKER_DEVICE_INDEX}")

    print(
        f"""got stats: 
    rate: {rate}, format: {format}, channels: {channels}, input_device_idx: {RESPEAKER_DEVICE_INDEX}, frames_per_buffer: {CHUNK}
    """
    )
    device_info = p.get_device_info_by_index(RESPEAKER_DEVICE_INDEX)

    stream = p.open(
        rate=rate,
        format=format,
        channels=channels,
        input=True,
        input_device_index=RESPEAKER_DEVICE_INDEX,
        frames_per_buffer=CHUNK,
        stream_callback=audio_callback,
    )

    stream.start_stream()
    print("Recording with callback. Press Ctrl+C to stop...")

    try:
        loop.run()
    except KeyboardInterrupt:
        print("Interrupt received, stopping...")
    finally:
        pipeline.set_state(Gst.State.NULL)
        if stream.is_active():
            stream.stop_stream()
        stream.close()
        p.terminate()
        print("Terminated.")
