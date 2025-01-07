import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib
import time

# Initialize GStreamer
Gst.init(None)

# Configure your IP, audio_rate, etc.
# IP = "192.168.0.209"
IP = "127.0.0.1"

audio_rate = 16000

# This pipeline captures from ALSA (mono, 16kHz) and sends via RTP
pipeline_str = f"""
rtpbin name=rtpbin
    alsasrc device=hw:1,0
        ! audioconvert 
        ! audioresample 
        ! audio/x-raw,rate={audio_rate},channels=1,format=S16LE,layout=interleaved
        ! queue ! audioconvert
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


# Mainloop
loop = GLib.MainLoop()

bus = pipeline.get_bus()
bus.add_signal_watch()
bus.connect("message", on_message)

# Start pipeline
pipeline.set_state(Gst.State.PLAYING)

print("Capturing from ALSA (hw:1,0) and streaming via RTP. Press Ctrl+C to stop...")
try:
    loop.run()
except KeyboardInterrupt:
    print("Interrupt received, stopping...")
finally:
    pipeline.set_state(Gst.State.NULL)
    print("Pipeline stopped.")
