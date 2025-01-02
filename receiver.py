import gi
import sys

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

from CONFIG import *


def create_pipeline():
    # Initialize GStreamer
    Gst.init(None)
    audio_rate = 22050
    # Use Gst.parse_launch to create the pipeline
    pipeline_description = f"""
        rtpbin name=rtpbin 
        udpsrc caps="application/x-rtp,media=(string)audio,clock-rate=(int){audio_rate},encoding-name=(string)L16,channels=(int)1" port=5000 ! 
        rtpjitterbuffer ! rtpbin.recv_rtp_sink_0 
        rtpbin. ! rtpL16depay ! audioconvert ! audioresample ! audiopanorama panorama=-1.0 ! mix. 
        udpsrc port=5001 ! rtpbin.recv_rtcp_sink_0 
        rtpbin.send_rtcp_src_0 ! udpsink host={IP} port=5005 sync=false async=false 
        udpsrc caps="application/x-rtp,media=(string)audio,clock-rate=(int){audio_rate},encoding-name=(string)L16,channels=(int)1" port=5002 ! 
        rtpjitterbuffer ! rtpbin.recv_rtp_sink_1 
        rtpbin. ! rtpL16depay ! audioconvert ! audioresample ! audiopanorama panorama=1.0 ! mix. 
        udpsrc port=5003 ! rtpbin.recv_rtcp_sink_1 
        rtpbin.send_rtcp_src_1 ! udpsink host={IP} port=5007 sync=false async=false 
        audiomixer name=mix ! audioconvert ! audioresample ! autoaudiosink
    """

    pipeline = Gst.parse_launch(pipeline_description)
    return pipeline


def main():
    pipeline = create_pipeline()

    # Run pipeline
    loop = GLib.MainLoop()

    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except KeyboardInterrupt:
        pass
    finally:
        pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    main()
