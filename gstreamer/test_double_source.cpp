#include <gst/gst.h>

int main(int argc, char *argv[]) {
    GstElement *pipeline, *source_left, *source_right, *panorama_left, *panorama_right, *mixer, *convert, *sink;
    GstBus *bus;
    GstMessage *msg;

    gst_init(&argc, &argv);

    // Create GStreamer elements
    pipeline = gst_pipeline_new("stereo-test-pipeline");
    source_left = gst_element_factory_make("audiotestsrc", "left-source");
    source_right = gst_element_factory_make("audiotestsrc", "right-source");
    panorama_left = gst_element_factory_make("audiopanorama", "panorama-left");
    panorama_right = gst_element_factory_make("audiopanorama", "panorama-right");
    mixer = gst_element_factory_make("audiomixer", "mixer");
    convert = gst_element_factory_make("audioconvert", "converter");
    sink = gst_element_factory_make("autoaudiosink", "audio-output");

    if (!pipeline || !source_left || !source_right || !panorama_left || !panorama_right || !mixer || !convert ||
        !sink) {
        g_printerr("Not all elements could be created.\n");
        return -1;
    }

    // Set the properties of the left source to produce a sine wave
    g_object_set(source_left, "wave", 8, "tick-interval", (guint64)300000000, NULL);

    // Set the properties of the right source to produce pulses
    g_object_set(source_right, "wave", 8, "tick-interval", (guint64)400000000, NULL);

    // Pan the left source to the left channel
    g_object_set(panorama_left, "panorama", -1.0, NULL); // -1.0 pans completely to the left

    // Pan the right source to the right channel
    g_object_set(panorama_right, "panorama", 1.0, NULL); // 1.0 pans completely to the right

    // Build the pipeline
    gst_bin_add_many(GST_BIN(pipeline), source_left, panorama_left, source_right, panorama_right, mixer, convert, sink,
                     NULL);

    if (!gst_element_link_many(source_left, panorama_left, mixer, NULL) ||
        !gst_element_link_many(source_right, panorama_right, mixer, NULL) ||
        !gst_element_link_many(mixer, convert, sink, NULL)) {
        g_printerr("Elements could not be linked.\n");
        gst_object_unref(pipeline);
        return -1;
    }

    // Set the pipeline to "playing" state
    gst_element_set_state(pipeline, GST_STATE_PLAYING);

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