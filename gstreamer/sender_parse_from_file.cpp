#include <gst/gst.h>
#include <iostream>

int main(int argc, char *argv[]) {
    gst_init(&argc, &argv);

    // The pipeline string is essentially the same as what you'd pass to gst-launch-1.0
    const gchar *pipeline_desc =
        "rtpbin name=rtpbin "
        "filesrc location=CantinaBand60.wav ! decodebin name=d "
        "d. ! queue ! audioconvert ! audioresample ! audio/x-raw,rate=22050,channels=1 ! tee name=t "
        "t. ! queue ! rtpL16pay ! rtpbin.send_rtp_sink_0 "
        "rtpbin.send_rtp_src_0 ! udpsink host=192.168.50.159 port=5000 sync=true async=false "
        "rtpbin.send_rtcp_src_0 ! udpsink host=192.168.50.159 port=5001 sync=false async=false "
        "udpsrc port=5005 ! rtpbin.recv_rtcp_sink_0 "
        "t. ! queue ! audioconvert ! volume volume=0.5 ! audioconvert ! audioresample ! "
        "audio/x-raw,rate=22050,channels=1 ! rtpL16pay ! rtpbin.send_rtp_sink_1 "
        "rtpbin.send_rtp_src_1 ! udpsink host=192.168.50.159 port=5002 sync=true async=false "
        "rtpbin.send_rtcp_src_1 ! udpsink host=192.168.50.159 port=5003 sync=false async=false "
        "udpsrc port=5007 ! rtpbin.recv_rtcp_sink_1";

    GError *error = NULL;
    GstElement *pipeline = gst_parse_launch(pipeline_desc, &error);

    if (!pipeline) {
        std::cerr << "Failed to parse pipeline: " << (error ? error->message : "Unknown error") << std::endl;
        if (error)
            g_error_free(error);
        return -1;
    }

    if (error) {
        // You got a pipeline, but there was a warning/error message
        std::cerr << "Pipeline parsing warning/error: " << error->message << std::endl;
        g_error_free(error);
    }

    // Set the pipeline to playing state
    gst_element_set_state(pipeline, GST_STATE_PLAYING);

    // Create a main loop to handle bus messages
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
                std::cerr << "Error: " << err->message << std::endl;
                g_error_free(err);
                g_free(debug);
                g_main_loop_quit(loop);
                break;
            }
            case GST_MESSAGE_EOS:
                std::cout << "End of stream" << std::endl;
                g_main_loop_quit(loop);
                break;
            default:
                break;
            }
            return TRUE;
        },
        loop);
    gst_object_unref(bus);

    // Run the loop
    g_main_loop_run(loop);

    // Cleanup
    gst_element_set_state(pipeline, GST_STATE_NULL);
    gst_object_unref(pipeline);
    g_main_loop_unref(loop);

    return 0;
}