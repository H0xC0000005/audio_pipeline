# Respeaker Audio Pipeline Utilities

This repository contains the streaming pipeline to stream from Respeaker USB Mic Array to a PC via network. It is portable across different systems and platforms.

---

## Launch the Pipeline

There are a few utilities that help to test and discover USB and ALSA devices, and for Respeaker Mic Array tests. The scripts are now automated and will dynamically fetch the device, so the pipeline will work fine as long as the device is plugged in.

### Steps to Launch

1. **Install Dependencies**:
   - Install the required dependencies from `requirements.txt` in your global Python environment on the sending machine. This is necessary because the scripts require `sudo` privileges.
   - Install GStreamer on the receiving machine, as the receiver shell script relies on `gst-launch-1.0`. Refer to the [GStreamer website](https://gstreamer.freedesktop.org/documentation/installing/index.html) for installation guidance.

2. **Deactivate Conda Environments**:
   - Deactivate any Conda environment to avoid PATH clashes.
   - Ensure that you are using the global Python interpreter.

3. **Network Configuration**:
   - Ensure both devices are directly accessible via the network.
   - Modify `CONFIG.py` and update the IP and port in the bash script to match your configuration.

4. **Run the Sending Script**:
   On the sending device (the one with the mic plugged in), execute:
   
   ```bash
   sudo python3 sender_appsrc_callback_2channels.py
   ```

   This version offers the best performance. Alternative versions are detailed in the next section.

5. **Run the Receiving Script**:
   On the receiving device, execute:

   ```bash
   bash gstlaunch_receiver_single_port.sh
   ```

   Or, you can run the powershell version on windows:

   ```bash
   .\\gstlaunch_receiver_single_port.ps1
   ```

   Alternatively, you can run a different receiver script that pairs with the sender.

Enjoy the audio!

---

## Launch options

The repository provides some versions of sender-receiver pairs to launch throughout, listed as below:

1. sender_appsrc_callback_2channels.py + gstlaunch_receiver_single_port.sh. This is the pair with the best performance, but with ~260ms latency (though which is also the lowest in the first version).

currently, all other pairs are deprecated. New configurations will appear here along with the development.

