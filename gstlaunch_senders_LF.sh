#!/bin/bash


#-----------------------------------------------------------
# band audio clk rate: 22050
# respeaker mic array clk rate: 16000
#-----------------------------------------------------------

IP="192.168.0.209"

gst-launch-1.0 -v \
  rtpbin name=rtpbin \
  filesrc location=CantinaBand60.wav ! decodebin name=d \
    d. ! queue ! audioconvert ! audioresample ! audio/x-raw,rate=22050,channels=1 ! tee name=t \
      t. ! queue ! rtpL16pay ! rtpbin.send_rtp_sink_0 \
        rtpbin.send_rtp_src_0 ! udpsink host=$IP port=5000 sync=true async=false \
        rtpbin.send_rtcp_src_0 ! udpsink host=$IP port=5001 sync=false async=false \
        udpsrc port=5005 ! rtpbin.recv_rtcp_sink_0 \
      t. ! queue ! audioconvert ! volume volume=1.0 ! audioconvert ! audioresample ! audio/x-raw,rate=22050,channels=1 ! rtpL16pay ! rtpbin.send_rtp_sink_1 \
        rtpbin.send_rtp_src_1 ! udpsink host=$IP port=5002 sync=true async=false \
        rtpbin.send_rtcp_src_1 ! udpsink host=$IP port=5003 sync=false async=false \
        udpsrc port=5007 ! rtpbin.recv_rtcp_sink_1
