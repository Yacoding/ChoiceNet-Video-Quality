#!/usr/bin/python3

import gi
import thread
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, Gtk

# Needed for window.get_xid(), xvimagesink.set_window_handle(), respectively:
from gi.repository import GdkX11, GstVideo


GObject.threads_init()
Gst.init(None)


class Server:
    def __init__(self, ip_address):
         # Create GStreamer pipeline
        self.pipeline = Gst.Pipeline()

        # Create bus to get events from GStreamer pipeline
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::error', self.on_error)


	#entry = raw_input("Enter 'H' for High Quality, or 'L' for low quality:")
	#if entry == "H":
		
	self.pipeline = Gst.parse_launch("rtpbin name=rtpbin v4l2src ! videoscale ! videoconvert ! video/x-raw,format=UYVY,width=640,height=480,framerate=30/1 ! videoscale ! videoconvert ! avenc_mpeg4 bitrate=1000000 ! rtpmp4vpay ! rtpbin.send_rtp_sink_0 rtpbin.send_rtp_src_0 ! udpsink port=5002 host=" + ip_address + " rtpbin.send_rtcp_src_0 ! udpsink port=5003 host=" + ip_address + " sync=false async=false udpsrc port=5007 ! rtpbin.recv_rtcp_sink_0")
	#else:
	#	self.pipeline = Gst.parse_launch('rtpbin name=rtpbin v4l2src ! videoscale ! videoconvert ! video/x-raw,format=UYVY,width=640,height=480,framerate=30/1 ! videoscale ! videoconvert ! avenc_mpeg4 bitrate=1 ! rtpmp4vpay ! rtpbin.send_rtp_sink_0 rtpbin.send_rtp_src_0 ! udpsink port=5002 host=192.168.2.201 rtpbin.send_rtcp_src_0 ! udpsink port=5003 host=192.168.2.201 sync=false async=false udpsrc port=5007 ! rtpbin.recv_rtcp_sink_0')

    def run(self):
        print self.pipeline.set_state(Gst.State.PLAYING)
	Gtk.main()
	
    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())

class Client:
    def __init__(self, ip_address):
        self.window = Gtk.Window()
        self.window.connect('destroy', self.quit)
        self.window.set_default_size(800, 450)

        self.drawingarea = Gtk.DrawingArea()
        self.window.add(self.drawingarea)
	
	
	self.pipeline = Gst.parse_launch("rtpbin name=rtpbin udpsrc port=5012 caps=application/x-rtp,media=video,clock-rate=90000,encoding-name=MP4V-ES,profile-level-id=1,config=000001b001000001b58913000001000000012000c48d8800f514043c1463000001b24c61766335332e33352e30 !rtpbin.recv_rtp_sink_0 rtpbin. ! rtpmp4vdepay ! avdec_mpeg4 ! videoconvert ! autovideosink udpsrc port=5013 ! rtpbin.recv_rtcp_sink_0 rtpbin.send_rtcp_src_0 ! udpsink port=5017 host=" + ip_address + " sync=false async=false")

    def run(self):
        self.window.show_all()
        # You need to get the XID after window.show_all().  You shouldn't get it
        # in the on_sync_message() handler because threading issues will cause
        # segfaults there.
        self.xid = self.drawingarea.get_property('window').get_xid()


        print self.pipeline.set_state(Gst.State.PLAYING)
	#pad = self.udpsink.get_static_pad('sink')
	#print str(pad.get_property('caps'))
	#caps = pad.query_caps(None)
	#cap = caps.get_structure(0)
        Gtk.main()

    def quit(self, window):
        self.pipeline.set_state(Gst.State.NULL)
        Gtk.main_quit()

    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            print('prepare-window-handle')
            msg.src.set_property('force-aspect-ratio', True)
            msg.src.set_window_handle(self.xid)

    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())


def runServer(self, ip_address):
    server = Server(ip_address)
    server.run()
def runClient(self, ip_address):
    client = Client(ip_address)
    client.run()

ip_address = raw_input("Please enter an IP to connect to :")
thread.start_new_thread(runServer, (None, ip_address))
thread.start_new_thread(runClient, (None, ip_address))
ip_address = raw_input("Press Enter to Quit:")

