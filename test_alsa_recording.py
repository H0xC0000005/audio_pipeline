import subprocess


def record_from_alsa(device_hw_str="hw:1,0", duration=5, filename="test.wav"):
    """
    Record audio from an ALSA device using `arecord`.

    :param device_hw_str: The ALSA hw device string, e.g. "hw:1,0"
    :param duration: Duration of the recording in seconds
    :param filename: Output filename, e.g. "test.wav"
    """
    # The `-D` parameter selects the device, `-f S16_LE` sets the format,
    # `-r 16000` sets the sample rate to 16 kHz, `-c 1` is for mono, `-d` is duration in seconds.
    command = [
        "arecord",
        "-D",
        device_hw_str,
        "-f",
        "S16_LE",
        "-r",
        "16000",
        "-c",
        "1",
        filename,
        "-d",
        str(duration),
    ]
    print(f"Recording {duration}s from ALSA device {device_hw_str} to {filename} ...")
    subprocess.run(command, check=True)
    print("Done recording.")


if __name__ == "__main__":
    # Record 5 seconds from ReSpeaker Mic Array "hw:1,0"
    record_from_alsa(device_hw_str="hw:1,0", duration=5, filename="respeaker_test.wav")
