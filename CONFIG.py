# runtime config
IP = "127.0.0.1"
SRC1_NAME = "SRC1"
SRC2_NAME = "SRC2"
# WARNING: too high refresh rate produce large overhead. better keep tps<=25
CHUNK = 400  # frames per buffer
USE_DOA = False
USE_PROCESSED = True

# respeaker constants
# DO NOT MODIFY!
RESPEAKER_DEVICE_NAME = "ReSpeaker 4 Mic Array"
RESPEAKER_RATE = 16000
RESPEAKER_CHANNELS = 1  # two versions of firmware, switch this if possible
RESPEAKER_WIDTH = 2
RESPEAKER_INDEX = None
VENDOR_ID, PRODUCT_ID = 0x2886, 0x0018  # for respeaker 4mic array
