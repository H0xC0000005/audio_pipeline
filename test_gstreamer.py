import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

# Initialize GStreamer
Gst.init(None)

# Define the gst-launch command as a string (excluding `gst-launch-1.0` and `-v`)
gst_command = """
    rtpbin name=rtpbin \
    filesrc location=CantinaBand60.wav ! decodebin name=d \
    d. ! queue ! audioconvert ! audioresample ! audio/x-raw,rate=22050,channels=1 ! tee name=t \
      t. ! queue ! rtpL16pay ! rtpbin.send_rtp_sink_0 \
        rtpbin.send_rtp_src_0 ! udpsink host=192.168.50.159 port=5000 sync=true async=false \
        rtpbin.send_rtcp_src_0 ! udpsink host=192.168.50.159 port=5001 sync=false async=false \
        udpsrc port=5005 ! rtpbin.recv_rtcp_sink_0 \
      t. ! queue ! audioconvert ! volume volume=0.5 ! audioconvert ! audioresample ! audio/x-raw,rate=22050,channels=1 ! rtpL16pay ! rtpbin.send_rtp_sink_1 \
        rtpbin.send_rtp_src_1 ! udpsink host=192.168.50.159 port=5002 sync=true async=false \
        rtpbin.send_rtcp_src_1 ! udpsink host=192.168.50.159 port=5003 sync=false async=false \
        udpsrc port=5007 ! rtpbin.recv_rtcp_sink_1
"""


# Parse the gst-launch command to create the pipeline
pipeline = Gst.parse_launch(gst_command)

# Set the pipeline state to PLAYING
pipeline.set_state(Gst.State.PLAYING)

# Run a main loop to keep the pipeline running
try:
    from gi.repository import GLib

    loop = GLib.MainLoop()
    print("Pipeline is running... Press Ctrl+C to stop.")
    loop.run()
except KeyboardInterrupt:
    print("Exiting...")
    pipeline.set_state(Gst.State.NULL)
