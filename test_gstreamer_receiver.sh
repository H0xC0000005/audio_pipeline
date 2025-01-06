#!/bin/bash

# Port to listen on
LISTEN_PORT="5000"

gst-launch-1.0 -v \
  udpsrc port=$LISTEN_PORT caps="application/x-rtp,media=(string)audio,clock-rate=(int)22050,encoding-name=(string)L16,channels=(int)2" ! \
  rtpL16depay ! audioconvert ! autoaudiosink
