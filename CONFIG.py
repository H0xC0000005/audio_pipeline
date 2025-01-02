# runtime config
IP = "127.0.0.1"
SRC1_NAME = "SRC1"
SRC2_NAME = "SRC2"
# WARNING: too high refresh rate produce large overhead. better keep tps<=25
CHUNK = 800  # frames per buffer

# respeaker constants
# DO NOT MODIFY!
RESPEAKER_RATE = 16000
RESPEAKER_CHANNELS = 6
RESPEAKER_WIDTH = 2
RESPEAKER_INDEX = 10
VENDOR_ID, PRODUCT_ID = 0x2886, 0x0018  # for respeaker 4mic array
