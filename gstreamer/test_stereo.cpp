#include <gst/gst.h>

int main(int argc, char *argv[]) {
    gst_init(&argc, &argv);

    GstElement *pipeline, *source1, *source2, *pan1, *pan2, *mixer, *sink;

    // Create elements
    pipeline = gst_pipeline_new("audio-stereo-pipeline");
    source1 = gst_element_factory_make("audiotestsrc", "left-source");
    source2 = gst_element_factory_make("audiotestsrc", "right-source");
    pan1 = gst_element_factory_make("audiopanorama", "left-pan");
    pan2 = gst_element_factory_make("audiopanorama", "right-pan");
    mixer = gst_element_factory_make("audiomixer", "mixer");
    sink = gst_element_factory_make("autoaudiosink", "audio-output");

    if (!pipeline || !source1 || !source2 || !pan1 || !pan2 || !mixer || !sink) {
        g_printerr("Not all elements could be created.\n");
        return -1;
    }

    // Set the properties of audiotestsrc
    g_object_set(source1, "wave", 8, NULL); // 8 is for pulses
    g_object_set(source2, "wave", 8, NULL); // 8 is for pulses

    // Set properties for panning
    g_object_set(pan1, "panorama", -1.0, NULL); // Fully left
    g_object_set(pan2, "panorama", 1.0, NULL);  // Fully right

    // // Introduce a latency on the right channel (0.5 milliseconds = 500 microseconds)
    // g_object_set(delay, "silent", FALSE, "sync", TRUE, "ts-offset", 30000000, NULL);
    g_object_set(sink, "ts-offset", 500000000, NULL);

    // Build the pipeline
    gst_bin_add_many(GST_BIN(pipeline), source1, source2, pan1, pan2, mixer, sink, NULL);

    // Link the elements
    if (!gst_element_link(source1, pan1) || !gst_element_link(source2, pan2) || !gst_element_link(pan1, mixer) ||
        !gst_element_link(pan2, mixer) || !gst_element_link(mixer, sink)) {
        g_printerr("Elements could not be linked.\n");
        gst_object_unref(pipeline);
        return -1;
    }

    // Start playing the pipeline
    gst_element_set_state(pipeline, GST_STATE_PLAYING);

    // Wait until error or EOS
    GstBus *bus = gst_element_get_bus(pipeline);
    GstMessage *msg = gst_bus_timed_pop_filtered(bus, GST_CLOCK_TIME_NONE,
                                                 static_cast<GstMessageType>(GST_MESSAGE_ERROR | GST_MESSAGE_EOS));

    // Free resources
    if (msg != NULL) {
        gst_message_unref(msg);
    }
    gst_object_unref(bus);
    gst_element_set_state(pipeline, GST_STATE_NULL);
    gst_object_unref(pipeline);

    return 0;
}