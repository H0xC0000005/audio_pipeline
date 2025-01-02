#include <gst/gst.h>
#include <iostream>

void rtpbin_new_pad_cb(GstElement *element, GstPad *pad, gpointer data) {
    GstElement *depay = GST_ELEMENT(data);
    GstPad *sinkpad = gst_element_get_static_pad(depay, "sink");

    std::cout << ">> added pad to rtpbin. get target link name " << gst_element_get_name(depay) << std::endl;
    std::cout << "linking the pad " << gst_pad_get_name(pad) << " and " << gst_pad_get_name(sinkpad) << std::endl;

    if (!gst_pad_is_linked(sinkpad) && GST_PAD_IS_SRC(pad)) {
        GstPadLinkReturn ret = gst_pad_link(pad, sinkpad);
        if (GST_PAD_LINK_FAILED(ret)) {
            std::cerr << "Link failed: " << gst_pad_link_get_name(ret) << std::endl;
        } else {
            std::cout << "Link succeeded" << std::endl;
        }
    } else {
        if (!GST_PAD_IS_SRC(pad)) {
            std::cout << "the added pad is src. returning" << std::endl;
        } else {
            std::cout << "Pad already linked" << std::endl;
        }
    }

    gst_object_unref(sinkpad);
}
// g_object_set(panorama1, "panorama", -1.0, NULL); // -1.0 pans completely to the left
// g_object_set(panorama2, "panorama", 1.0, NULL);  // 1.0 pans completely to the right
int main(int argc, char *argv[]) {
    gst_init(&argc, &argv);

    GstElement *pipeline = gst_pipeline_new("audio-pipeline");
    GstElement *udpsrc_rtp = gst_element_factory_make("udpsrc", "udp_source_rtp");
    GstElement *rtpbin = gst_element_factory_make("rtpbin", "rtpbin");
    GstElement *rtpL16depay = gst_element_factory_make("rtpL16depay", "audio_depay");
    GstElement *audioconvert = gst_element_factory_make("audioconvert", "audio_convert");
    GstElement *audioresample = gst_element_factory_make("audioresample", "audio_resample");
    GstElement *autoaudiosink = gst_element_factory_make("autoaudiosink", "audio_sink");
    GstElement *udpsrc_rtcp = gst_element_factory_make("udpsrc", "udpsrc_rtcp");
    GstElement *udpsink_rtcp = gst_element_factory_make("udpsink", "udpsink_rtcp");

    if (!pipeline || !udpsrc_rtp || !rtpbin || !rtpL16depay || !audioconvert || !audioresample || !autoaudiosink ||
        !udpsrc_rtcp || !udpsink_rtcp) {
        std::cerr << "Not all elements could be created." << std::endl;
        return -1;
    }

    g_object_set(udpsrc_rtp, "port", 6000, NULL);
    g_object_set(udpsrc_rtcp, "port", 6001, NULL);
    g_object_set(udpsink_rtcp, "host", "127.0.0.1", "port", 6005, "async", FALSE, "sync", FALSE, NULL);

    /**
     * BE AWARE OF RTP CAP CAPABILITIES!
     * e.g. check the sampling rate!
     */
    GstCaps *caps = gst_caps_new_simple("application/x-rtp", "media", G_TYPE_STRING, "audio", "clock-rate", G_TYPE_INT,
                                        22050, "encoding-name", G_TYPE_STRING, "L16", "payload", G_TYPE_INT, 96, NULL);
    g_object_set(udpsrc_rtp, "caps", caps, NULL);
    gst_caps_unref(caps);

    gst_bin_add_many(GST_BIN(pipeline), udpsrc_rtp, rtpbin, rtpL16depay, audioconvert, audioresample, autoaudiosink,
                     udpsrc_rtcp, udpsink_rtcp, NULL);

    g_print(">>> linking rtp and rtcp pads\n");
    GstPadLinkReturn ret;

    g_signal_connect(rtpbin, "pad-added", G_CALLBACK(rtpbin_new_pad_cb), rtpL16depay);
    gst_element_set_state(pipeline, GST_STATE_READY);

    GstPad *rtp_sinkpad = gst_element_request_pad_simple(rtpbin, "recv_rtp_sink_0");
    GstPad *udpsrc_rtp_pad = gst_element_get_static_pad(udpsrc_rtp, "src");
    ret = gst_pad_link(udpsrc_rtp_pad, rtp_sinkpad);
    g_print("-- Linking rtpbin sink and rtp src: %s\n", gst_pad_link_get_name(ret));
    gst_object_unref(rtp_sinkpad);
    gst_object_unref(udpsrc_rtp_pad);

    GstPad *recv_rtcp_srcpad = gst_element_request_pad_simple(rtpbin, "recv_rtcp_sink_0");
    GstPad *udpsrc_rtcp_pad = gst_element_get_static_pad(udpsrc_rtcp, "src");
    std::cout << recv_rtcp_srcpad << "|" << std::endl;
    std::cout << udpsrc_rtcp_pad << "|" << std::endl;
    ret = gst_pad_link(udpsrc_rtcp_pad, recv_rtcp_srcpad);
    g_print("-- Linking rtpbin sink and rtcp src: %s\n", gst_pad_link_get_name(ret));
    gst_object_unref(recv_rtcp_srcpad);
    gst_object_unref(udpsrc_rtcp_pad);

    GstPad *send_rtcp_sinkpad = gst_element_get_static_pad(udpsink_rtcp, "sink");
    GstPad *send_rtcp_srcpad = gst_element_request_pad_simple(rtpbin, "send_rtcp_src_0");
    ret = gst_pad_link(send_rtcp_srcpad, send_rtcp_sinkpad);
    g_print("-- Linking rtcp sink and rtpbin src: %s\n", gst_pad_link_get_name(ret));
    gst_object_unref(send_rtcp_srcpad);
    gst_object_unref(send_rtcp_sinkpad);

    // GstPad *send_rtcp_sinkpad = gst_element_get_static_pad(udpsink_rtcp, "sink");
    // GstPad *send_rtcp_srcpad = gst_element_get_request_pad(rtpbin, "send_rtcp_src_0");
    // ret = gst_pad_link(send_rtcp_srcpad, send_rtcp_sinkpad);
    // g_print("-- Linking rtcp sink and rtpbin src: %s\n", gst_pad_link_get_name(ret));
    // gst_object_unref(send_rtcp_srcpad);
    // gst_object_unref(send_rtcp_sinkpad);

    if (gst_element_link_many(rtpL16depay, audioconvert, audioresample, autoaudiosink, NULL) != (gboolean)TRUE) {
        g_printerr("Elements could not be linked.\n");
        gst_object_unref(pipeline);
        return -1;
    }

    gst_element_set_state(pipeline, GST_STATE_PLAYING);
    std::cout << "RTP audio receiver with RTCP is running..." << std::endl;

    // Wait for a signal to stop
    GMainLoop *main_loop = g_main_loop_new(NULL, FALSE);
    g_main_loop_run(main_loop);

    gst_element_set_state(pipeline, GST_STATE_NULL);
    gst_object_unref(pipeline);
    return 0;
}