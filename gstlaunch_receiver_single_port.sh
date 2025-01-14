IP="127.0.0.1"

gst-launch-1.0 -v rtpbin name=rtpbin latency=50 \
    udpsrc port=5000 caps="application/x-rtp,media=audio,clock-rate=16000,encoding-name=L16,channels=2" \
        ! rtpbin.recv_rtp_sink_0 \
    rtpbin. ! rtpL16depay \
        ! audioconvert \
        ! audioresample \
        ! autoaudiosink \
    udpsrc port=5001 ! rtpbin.recv_rtcp_sink_0 \
    rtpbin.send_rtcp_src_0 ! udpsink host=$IP port=5005 sync=false async=false


# gst-launch-1.0 -v rtpbin name=rtpbin \
#     udpsrc port=5000 caps="application/x-rtp,media=audio,clock-rate=16000,encoding-name=L16,channels=2" \
#         ! rtpjitterbuffer \
#         ! rtpbin.recv_rtp_sink_0 \
#     rtpbin. ! rtpL16depay ! queue \
#         ! audioconvert \
#         ! audioresample \
#         ! autoaudiosink \
#     udpsrc port=5001 ! rtpbin.recv_rtcp_sink_0 \
#     rtpbin.send_rtcp_src_0 ! udpsink host=$IP port=5005 sync=false async=false