gst-launch-1.0 alsasrc device=hw:1,0 ! \
audioconvert ! \
audioresample ! \
audio/x-raw, rate=16000, channels=1 ! \
autoaudiosink 
