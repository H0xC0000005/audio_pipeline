from tuning import Tuning
import usb.core
import usb.util
import time

dev: usb.core.Device
dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)


def print_DOA(mic_tuning: Tuning):
    print(f"The current DOA: {mic_tuning.direction}")


if dev:
    Mic_tuning = Tuning(dev)
    print(Mic_tuning)
    print_DOA(Mic_tuning)
    while True:
        try:
            print_DOA(Mic_tuning)
            time.sleep(1)
        except KeyboardInterrupt:
            break
