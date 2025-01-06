#!/bin/bash

# IP address of the receiver
RECEIVER_IP="192.168.0.209"
RECEIVER_PORT="5000"

gst-launch-1.0 -v \
  audiotestsrc is-live=true ! audioconvert ! audio/x-raw,rate=44100,channels=2 ! rtpL16pay ! \
  udpsink host=$RECEIVER_IP port=$RECEIVER_PORT