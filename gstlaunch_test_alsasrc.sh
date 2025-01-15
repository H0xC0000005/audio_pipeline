gst-launch-1.0 -v \
    alsasrc device=hw:2,0\
    ! audioconvert\
    ! audio/x-raw,rate=16000,channels=2,format=S16LE,layout=interleaved\
    ! autoaudiosink