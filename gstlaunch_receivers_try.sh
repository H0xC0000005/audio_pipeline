# # test receiver with dual channel and panorama
# # this is the same regardless the source type (mic or test)
# # be aware of inserted guys such as volume comonent
# gst-launch-1.0 -v rtpbin name=rtpbin \
#     udpsrc caps="application/x-rtp,media=(string)audio,clock-rate=(int)22050,encoding-name=(string)L16,channels=(int)1" port=5000 ! \
#     rtpjitterbuffer ! rtpbin.recv_rtp_sink_0 \
#     rtpbin. ! rtpL16depay ! audioconvert ! audioresample ! audiopanorama panorama=-1.0 ! queue ! mix. \
#     udpsrc port=5001 ! rtpbin.recv_rtcp_sink_0 \
#     rtpbin.send_rtcp_src_0 ! udpsink host=192.168.0.45 port=5005 sync=false async=false \
#     udpsrc caps="application/x-rtp,media=(string)audio,clock-rate=(int)22050,encoding-name=(string)L16,channels=(int)1" port=5002 ! \
#     rtpjitterbuffer ! rtpbin.recv_rtp_sink_1 \
#     rtpbin. ! rtpL16depay ! audioconvert ! audioresample ! audiopanorama panorama=1.0 ! volume volume=0.6 ! queue ! mix. \
#     udpsrc port=5003 ! rtpbin.recv_rtcp_sink_1 \
#     rtpbin.send_rtcp_src_1 ! udpsink host=192.168.0.45 port=5007 sync=false async=false \
#     audiomixer name=mix ! audioconvert ! audioresample ! autoaudiosink

# rtpbin. ! rtpL16depay ! audioconvert ! audioresample ! audiopanorama panorama=1.0 ! volume volume=0.6 ! mix. \
#-----------------------------------------------------------
# band audio clk rate: 22050
# respeaker mic array clk rate: 16000
#-----------------------------------------------------------

gst-launch-1.0 -v rtpbin name=rtpbin \
    udpsrc caps="application/x-rtp,media=(string)audio,clock-rate=(int)22050,encoding-name=(string)L16,channels=(int)1" port=5000 ! \
    rtpjitterbuffer ! rtpbin.recv_rtp_sink_0 \
    rtpbin. ! rtpL16depay ! audioconvert ! audioresample ! audiopanorama panorama=-1.0 ! mix. \
    udpsrc port=5001 ! rtpbin.recv_rtcp_sink_0 \
    rtpbin.send_rtcp_src_0 ! udpsink host=127.0.0.1 port=5005 sync=false async=false \
    udpsrc caps="application/x-rtp,media=(string)audio,clock-rate=(int)22050,encoding-name=(string)L16,channels=(int)1" port=5002 ! \
    rtpjitterbuffer ! rtpbin.recv_rtp_sink_1 \
    rtpbin. ! rtpL16depay ! audioconvert ! audioresample ! audiopanorama panorama=1.0 ! mix. \
    udpsrc port=5003 ! rtpbin.recv_rtcp_sink_1 \
    rtpbin.send_rtcp_src_1 ! udpsink host=127.0.0.1 port=5007 sync=false async=false \
    audiomixer name=mix ! audioconvert ! audioresample ! autoaudiosink



# gst-launch-1.0 -v \
#     udpsrc port=5000 caps="application/x-rtp,media=(string)audio,clock-rate=(int)22050,encoding-name=(string)L16,channels=(int)1" ! \
#     rtpjitterbuffer ! identity sync=true ! rtpL16depay ! audioconvert ! audioresample ! audiopanorama panorama=-1.0 ! \
#     audiomixer name=mix \
#     udpsrc port=5002 caps="application/x-rtp,media=(string)audio,clock-rate=(int)22050,encoding-name=(string)L16,channels=(int)1" ! \
#     rtpjitterbuffer ! identity sync=true ! rtpL16depay ! audioconvert ! audioresample ! audiopanorama panorama=1.0 ! mix. \
#     mix. ! audioconvert ! audioresample ! autoaudiosink


# gst-launch-1.0 -v \
#   udpsrc port=5000 caps="application/x-rtp,media=(string)audio,clock-rate=(int)22050,encoding-name=(string)L16,channels=(int)1" ! \
#   rtpL16depay ! audioconvert ! audioresample ! audiopanorama panorama=-1.0 !  queue ! \
#   audiomixer name=mix \
#   udpsrc port=5002 caps="application/x-rtp,media=(string)audio,clock-rate=(int)22050,encoding-name=(string)L16,channels=(int)1" ! \
#   rtpL16depay ! audioconvert ! audioresample ! audiopanorama panorama=1.0 ! queue ! mix. \
#   mix. ! audioconvert ! audioresample ! autoaudiosink


# gst-launch-1.0 -v \
#   udpsrc port=5000 caps="application/x-rtp,media=(string)audio,clock-rate=(int)22050,encoding-name=(string)L16,channels=(int)1" ! \
#   rtpL16depay ! queue! audioconvert ! audioresample ! audiopanorama panorama=-1.0 ! audioconvert ! audioresample ! autoaudiosink

# gst-launch-1.0 -v \
#     udpsrc port=5000 caps="application/x-rtp,media=(string)audio,clock-rate=(int)22050,encoding-name=(string)L16" ! \
#     rtpjitterbuffer ! rtpL16depay ! audioconvert ! audioresample ! autoaudiosink


# gst-launch-1.0 -v \
#     udpsrc port=5000 caps="application/x-rtp,media=audio,encoding-name=OPUS,payload=96" ! rtpopusdepay ! opusdec ! \
#     audioconvert ! audioresample ! autoaudiosink

# LOCAL TEST
# gst-launch-1.0 -v \
#     filesrc location=CantinaBand60.wav ! wavparse ! audioconvert ! audioresample ! \
#     autoaudiosink 
