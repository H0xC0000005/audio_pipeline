import re

# runtime config
# IP = "192.168.0.130"
IP = "192.168.0.209"
# IP = "127.0.0.1"

SRC1_NAME = "SRC1"
SRC2_NAME = "SRC2"
# WARNING: too high refresh rate produce large overhead
CHUNK = 128  # frames per buffer
USE_DOA = False
USE_PROCESSED = True
RTP_LATENCY = 25

# respeaker constants
# DO NOT MODIFY!
RESPEAKER_DEVICE_NAME = "ReSpeaker 4 Mic Array"
RESPEAKER_RATE = 16000
RESPEAKER_CHANNELS = 6  # two versions of firmware, switch this if possible
RESPEAKER_WIDTH = 2
RESPEAKER_DEVICE_INDEX = None
RESPEAKER_ALSA_INDEX = None
VENDOR_ID, PRODUCT_ID = 0x2886, 0x0018  # for respeaker 4mic array


# utility functions related to constants. they are used to fetch dynamic 
# constants which are settled before runtime.
def get_respeaker_index(p):
    """
    find the index of respeaker mic array. the device name is hardcoded.
    p: pyaudio.PyAudio object.
    """
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get("deviceCount")
    for i in range(0, numdevices):
        cur_device_info = p.get_device_info_by_host_api_device_index(0, i)
        if (cur_device_info.get("maxInputChannels")) > 0:
            print(">>> Input Device id ", i, " - ", cur_device_info.get("name"))
            if RESPEAKER_DEVICE_NAME in cur_device_info.get("name"):
                print(f"<<< looked up respeaker index: {i}. returning")
                return i
    return None

def get_respeaker_alsa_identifier(p):
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get("deviceCount")
    for i in range(0, numdevices):
        cur_device_info = p.get_device_info_by_host_api_device_index(0, i)
        cur_device_name = cur_device_info.get("name")
        print(">>> Input Device id ", i, " - ", cur_device_name)
        if RESPEAKER_DEVICE_NAME in cur_device_name:
            match = re.search(r"hw:\d,\d", cur_device_name)
            if match:
                print(f"<<< looked up respeaker alsa index: {match.group(0)}. returning")
                return match.group(0)
    return None