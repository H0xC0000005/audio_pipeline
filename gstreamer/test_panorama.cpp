#include <gst/gst.h>

int main(int argc, char *argv[]) {
    GstElement *pipeline, *source, *panorama, *convert, *resample, *sink;
    GstBus *bus;
    GstMessage *msg;

    gst_init(&argc, &argv);

    // Create GStreamer elements
    pipeline = gst_pipeline_new("stereo-test-pipeline");
    source = gst_element_factory_make("audiotestsrc", "audio-source");
    panorama = gst_element_factory_make("audiopanorama", "panner");
    convert = gst_element_factory_make("audioconvert", "converter");
    resample = gst_element_factory_make("audioresample", "resampler");
    sink = gst_element_factory_make("autoaudiosink", "audio-output");

    if (!pipeline || !source || !panorama || !convert || !sink) {
        g_printerr("Not all elements could be created.\n");
        return -1;
    }

    // Set the properties of audiotestsrc
    g_object_set(source, "wave", 0, NULL); // 0 is for sine wave

    // Build the pipeline
    gst_bin_add_many(GST_BIN(pipeline), source, panorama, convert, resample, sink, NULL);
    if (gst_element_link_many(source, panorama, convert, resample, sink, NULL) != TRUE) {
        g_printerr("Elements could not be linked.\n");
        gst_object_unref(pipeline);
        return -1;
    }

    // Set the pipeline to "playing" state
    gst_element_set_state(pipeline, GST_STATE_PLAYING);

    // Pan to the left channel
    g_object_set(panorama, "panorama", -1.0, NULL); // -1.0 pans completely to the left
    g_print("Playing on the left channel...\n");
    g_usleep(5000000); // Play for 5 seconds

    // Pan to the right channel
    g_object_set(panorama, "panorama", 1.0, NULL); // 1.0 pans completely to the right
    g_print("Playing on the right channel...\n");
    g_usleep(5000000); // Play for 5 seconds

    // Pan to the center (both channels)
    g_object_set(panorama, "panorama", 0.0, NULL); // 0.0 is center
    g_print("Playing on both channels...\n");
    g_usleep(5000000); // Play for 5 seconds

    // Wait until error or EOS
    bus = gst_element_get_bus(pipeline);
    msg = gst_bus_timed_pop_filtered(bus, GST_CLOCK_TIME_NONE, (GstMessageType)(GST_MESSAGE_ERROR | GST_MESSAGE_EOS));

    // Parse message
    if (msg != NULL) {
        GError *err;
        gchar *debug_info;

        switch (GST_MESSAGE_TYPE(msg)) {
        case GST_MESSAGE_ERROR:
            gst_message_parse_error(msg, &err, &debug_info);
            g_printerr("Error received from element %s: %s\n", GST_OBJECT_NAME(msg->src), err->message);
            g_printerr("Debugging information: %s\n", debug_info ? debug_info : "none");
            g_clear_error(&err);
            g_free(debug_info);
            break;
        case GST_MESSAGE_EOS:
            g_print("End-Of-Stream reached.\n");
            break;
        default:
            g_printerr("Unexpected message received.\n");
            break;
        }
        gst_message_unref(msg);
    }

    // Free resources
    gst_object_unref(bus);
    gst_element_set_state(pipeline, GST_STATE_NULL);
    gst_object_unref(pipeline);

    return 0;
}