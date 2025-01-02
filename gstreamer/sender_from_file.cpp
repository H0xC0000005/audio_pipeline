#include <gst/gst.h>
#include <iostream>

int main(int argc, char *argv[]) {
    gst_init(&argc, &argv);

    // Create the pipeline
    GstElement *pipeline = gst_pipeline_new("my-pipeline");

    // Create elements
    GstElement *rtpbin = gst_element_factory_make("rtpbin", "rtpbin");
    GstElement *filesrc = gst_element_factory_make("filesrc", "filesrc");
    GstElement *decodebin = gst_element_factory_make("decodebin", "decodebin");
    GstElement *queue1 = gst_element_factory_make("queue", "queue1");
    GstElement *audioconvert1 = gst_element_factory_make("audioconvert", "audioconvert1");
    GstElement *audioresample1 = gst_element_factory_make("audioresample", "audioresample1");
    GstElement *capsfilter1 = gst_element_factory_make("capsfilter", "capsfilter1");
    GstElement *tee = gst_element_factory_make("tee", "tee");

    // First branch elements
    GstElement *queue2 = gst_element_factory_make("queue", "queue2");
    GstElement *rtpL16pay1 = gst_element_factory_make("rtpL16pay", "rtpL16pay1");
    GstElement *udpsink_rtp_0 = gst_element_factory_make("udpsink", "udpsink_rtp_0");
    GstElement *udpsink_rtcp_0 = gst_element_factory_make("udpsink", "udpsink_rtcp_0");
    GstElement *udpsrc_rtcp_0 = gst_element_factory_make("udpsrc", "udpsrc_rtcp_0");

    // Second branch elements
    GstElement *queue3 = gst_element_factory_make("queue", "queue3");
    GstElement *audioconvert2 = gst_element_factory_make("audioconvert", "audioconvert2");
    GstElement *volume = gst_element_factory_make("volume", "volume");
    GstElement *audioconvert3 = gst_element_factory_make("audioconvert", "audioconvert3");
    GstElement *audioresample2 = gst_element_factory_make("audioresample", "audioresample2");
    GstElement *capsfilter2 = gst_element_factory_make("capsfilter", "capsfilter2");
    GstElement *rtpL16pay2 = gst_element_factory_make("rtpL16pay", "rtpL16pay2");
    GstElement *udpsink_rtp_1 = gst_element_factory_make("udpsink", "udpsink_rtp_1");
    GstElement *udpsink_rtcp_1 = gst_element_factory_make("udpsink", "udpsink_rtcp_1");
    GstElement *udpsrc_rtcp_1 = gst_element_factory_make("udpsrc", "udpsrc_rtcp_1");

    if (!pipeline || !rtpbin || !filesrc || !decodebin || !queue1 || !audioconvert1 || !audioresample1 ||
        !capsfilter1 || !tee || !queue2 || !rtpL16pay1 || !udpsink_rtp_0 || !udpsink_rtcp_0 || !udpsrc_rtcp_0 ||
        !queue3 || !audioconvert2 || !volume || !audioconvert3 || !audioresample2 || !capsfilter2 || !rtpL16pay2 ||
        !udpsink_rtp_1 || !udpsink_rtcp_1 || !udpsrc_rtcp_1) {
        std::cerr << "Failed to create one or more GStreamer elements." << std::endl;
        return -1;
    }

    // Set element properties
    g_object_set(filesrc, "location", "CantinaBand60.wav", NULL);

    // Set caps on capsfilter elements
    GstCaps *caps_22050_1 =
        gst_caps_new_simple("audio/x-raw", "rate", G_TYPE_INT, 22050, "channels", G_TYPE_INT, 1, NULL);
    g_object_set(capsfilter1, "caps", caps_22050_1, NULL);
    gst_caps_unref(caps_22050_1);

    GstCaps *caps_22050_1_2 =
        gst_caps_new_simple("audio/x-raw", "rate", G_TYPE_INT, 22050, "channels", G_TYPE_INT, 1, NULL);
    g_object_set(capsfilter2, "caps", caps_22050_1_2, NULL);
    gst_caps_unref(caps_22050_1_2);

    // Set volume
    g_object_set(volume, "volume", 0.5, NULL);

    // Set udpsink properties
    g_object_set(udpsink_rtp_0, "host", "192.168.50.159", "port", 5000, "sync", TRUE, "async", FALSE, NULL);
    g_object_set(udpsink_rtcp_0, "host", "192.168.50.159", "port", 5001, "sync", FALSE, "async", FALSE, NULL);
    g_object_set(udpsrc_rtcp_0, "port", 5005, NULL);

    g_object_set(udpsink_rtp_1, "host", "192.168.50.159", "port", 5002, "sync", TRUE, "async", FALSE, NULL);
    g_object_set(udpsink_rtcp_1, "host", "192.168.50.159", "port", 5003, "sync", FALSE, "async", FALSE, NULL);
    g_object_set(udpsrc_rtcp_1, "port", 5007, NULL);

    // Add elements to pipeline
    gst_bin_add_many(GST_BIN(pipeline), rtpbin, filesrc, decodebin, queue1, audioconvert1, audioresample1, capsfilter1,
                     tee, queue2, rtpL16pay1, udpsink_rtp_0, udpsink_rtcp_0, udpsrc_rtcp_0, queue3, audioconvert2,
                     volume, audioconvert3, audioresample2, capsfilter2, rtpL16pay2, udpsink_rtp_1, udpsink_rtcp_1,
                     udpsrc_rtcp_1, NULL);

    // Link static parts of the pipeline
    // filesrc -> decodebin (decodebin is dynamic)
    if (!gst_element_link(filesrc, decodebin)) {
        std::cerr << "Failed to link filesrc and decodebin." << std::endl;
        return -1;
    }

    // Connect the decodebin pad-added signal
    g_signal_connect(decodebin, "pad-added", G_CALLBACK([](GstElement *dec, GstPad *pad, gpointer user_data) {
                         GstElement *queue1 = (GstElement *)user_data;

                         GstCaps *caps = gst_pad_query_caps(pad, NULL);
                         const GstStructure *str = gst_caps_get_structure(caps, 0);
                         const gchar *name = gst_structure_get_name(str);
                         if (g_str_has_prefix(name, "audio/x-raw")) {
                             // Link decodebin's src pad to queue1 sink pad
                             GstPad *qpad = gst_element_get_static_pad(queue1, "sink");
                             if (gst_pad_link(pad, qpad) != GST_PAD_LINK_OK) {
                                 g_printerr("Failed to link decodebin to queue1\n");
                             }
                             gst_object_unref(qpad);
                         }
                         gst_caps_unref(caps);
                     }),
                     queue1);

    // Now link the rest: queue1 -> audioconvert1 -> audioresample1 -> capsfilter1 -> tee
    if (!gst_element_link_many(queue1, audioconvert1, audioresample1, capsfilter1, tee, NULL)) {
        std::cerr << "Failed to link main branch." << std::endl;
        return -1;
    }

    // First branch:
    if (!gst_element_link_many(tee, queue2, rtpL16pay1, NULL)) {
        std::cerr << "Failed to link first branch." << std::endl;
        return -1;
    }
    // rtpL16pay1 -> rtpbin.send_rtp_sink_0
    // For linking with rtpbin, we link request pads dynamically:
    GstPad *send_rtp_sink_0 = gst_element_get_request_pad(rtpbin, "send_rtp_sink_0");
    GstPad *pay1_src_pad = gst_element_get_static_pad(rtpL16pay1, "src");
    if (gst_pad_link(pay1_src_pad, send_rtp_sink_0) != GST_PAD_LINK_OK) {
        std::cerr << "Failed to link rtpL16pay1 to rtpbin send_rtp_sink_0\n";
    }
    gst_object_unref(pay1_src_pad);
    gst_object_unref(send_rtp_sink_0);

    // rtpbin.send_rtp_src_0 -> udpsink_rtp_0
    GstPad *send_rtp_src_0 = gst_element_get_static_pad(rtpbin, "send_rtp_src_0");
    GstPad *udpsink_rtp_0_sink = gst_element_get_static_pad(udpsink_rtp_0, "sink");
    gst_pad_link(send_rtp_src_0, udpsink_rtp_0_sink);
    gst_object_unref(udpsink_rtp_0_sink);

    // rtpbin.send_rtcp_src_0 -> udpsink_rtcp_0
    GstPad *send_rtcp_src_0 = gst_element_get_static_pad(rtpbin, "send_rtcp_src_0");
    GstPad *udpsink_rtcp_0_sink = gst_element_get_static_pad(udpsink_rtcp_0, "sink");
    gst_pad_link(send_rtcp_src_0, udpsink_rtcp_0_sink);
    gst_object_unref(udpsink_rtcp_0_sink);

    // udpsrc_rtcp_0 -> rtpbin.recv_rtcp_sink_0
    GstPad *recv_rtcp_sink_0 = gst_element_get_request_pad(rtpbin, "recv_rtcp_sink_0");
    GstPad *udpsrc_rtcp_0_src = gst_element_get_static_pad(udpsrc_rtcp_0, "src");
    gst_pad_link(udpsrc_rtcp_0_src, recv_rtcp_sink_0);
    gst_object_unref(udpsrc_rtcp_0_src);
    gst_object_unref(recv_rtcp_sink_0);

    // Second branch:
    if (!gst_element_link_many(tee, queue3, audioconvert2, volume, audioconvert3, audioresample2, capsfilter2,
                               rtpL16pay2, NULL)) {
        std::cerr << "Failed to link second branch." << std::endl;
        return -1;
    }

    GstPad *send_rtp_sink_1 = gst_element_get_request_pad(rtpbin, "send_rtp_sink_1");
    GstPad *pay2_src_pad = gst_element_get_static_pad(rtpL16pay2, "src");
    gst_pad_link(pay2_src_pad, send_rtp_sink_1);
    gst_object_unref(pay2_src_pad);
    gst_object_unref(send_rtp_sink_1);

    GstPad *send_rtp_src_1 = gst_element_get_static_pad(rtpbin, "send_rtp_src_1");
    GstPad *udpsink_rtp_1_sink = gst_element_get_static_pad(udpsink_rtp_1, "sink");
    gst_pad_link(send_rtp_src_1, udpsink_rtp_1_sink);
    gst_object_unref(udpsink_rtp_1_sink);

    GstPad *send_rtcp_src_1 = gst_element_get_static_pad(rtpbin, "send_rtcp_src_1");
    GstPad *udpsink_rtcp_1_sink = gst_element_get_static_pad(udpsink_rtcp_1, "sink");
    gst_pad_link(send_rtcp_src_1, udpsink_rtcp_1_sink);
    gst_object_unref(udpsink_rtcp_1_sink);

    GstPad *recv_rtcp_sink_1 = gst_element_get_request_pad(rtpbin, "recv_rtcp_sink_1");
    GstPad *udpsrc_rtcp_1_src = gst_element_get_static_pad(udpsrc_rtcp_1, "src");
    gst_pad_link(udpsrc_rtcp_1_src, recv_rtcp_sink_1);
    gst_object_unref(udpsrc_rtcp_1_src);
    gst_object_unref(recv_rtcp_sink_1);

    // Start playing
    gst_element_set_state(pipeline, GST_STATE_PLAYING);

    // Wait until error or EOS
    GMainLoop *loop = g_main_loop_new(NULL, FALSE);
    GstBus *bus = gst_element_get_bus(pipeline);
    gst_bus_add_watch(
        bus,
        [](GstBus *bus, GstMessage *msg, gpointer data) -> gboolean {
            GMainLoop *loop = (GMainLoop *)data;
            switch (GST_MESSAGE_TYPE(msg)) {
            case GST_MESSAGE_ERROR: {
                GError *err = NULL;
                gchar *debug = NULL;
                gst_message_parse_error(msg, &err, &debug);
                g_printerr("Error: %s\n", err->message);
                g_error_free(err);
                g_free(debug);
                g_main_loop_quit(loop);
                break;
            }
            case GST_MESSAGE_EOS:
                g_print("End of stream\n");
                g_main_loop_quit(loop);
                break;
            default:
                break;
            }
            return TRUE;
        },
        loop);
    gst_object_unref(bus);

    g_main_loop_run(loop);

    // Free resources
    gst_element_set_state(pipeline, GST_STATE_NULL);
    gst_object_unref(pipeline);
    g_main_loop_unref(loop);

    return 0;
}