#!/usr/bin/python3

import gi
import thread
import threading
import socket
import sys
import time
import WebcamUI
import scipy.misc
import metrikz
#a=scipy.misc.imread('test.bmp')
#b=scipy.misc.imread('test2.bmp')
#print "THE SNR!!!!! : " + str(metrikz.snr(a,b))


gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, Gtk, Gdk


# Needed for window.get_xid(), xvimagesink.set_window_handle(), respectively:
from gi.repository import GdkX11, GstVideo


GObject.threads_init()
Gst.init(None)
Gdk.threads_init()

# Define Globals
mutex = threading.Lock()
caps = "False"
webui = False

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class Server:
    def __init__(self, ip_address, partners_quality):
        # Create GStreamer pipeline
        self.pipeline = Gst.Pipeline()

        partners_quality = partners_quality.rstrip()
	if partners_quality.lower() == "h":	
	    self.pipeline = Gst.parse_launch("rtpbin name=rtpbin v4l2src ! videoscale ! videoconvert ! video/x-raw,format=UYVY,width=640,height=480,framerate=30/1 ! videoscale ! videoconvert ! avenc_mpeg4 bitrate=1000000 ! tee name=t ! rtpmp4vpay ! rtpbin.send_rtp_sink_0 t. ! queue ! xvimagesink rtpbin.send_rtp_src_0 ! udpsink name=udpsink_video port=5002 host=" + ip_address + " rtpbin.send_rtcp_src_0 ! udpsink port=5003 host=" + ip_address + " sync=false async=false udpsrc port=5007 ! rtpbin.recv_rtcp_sink_0")
            print "You've sent High Quality data"
	else:
            self.pipeline = Gst.parse_launch("rtpbin name=rtpbin v4l2src ! videoscale ! videoconvert ! video/x-raw,format=UYVY,width=640,height=480,framerate=30/1 ! videoscale ! videoconvert ! avenc_mpeg4 bitrate=150000 ! tee name=t ! rtpmp4vpay ! rtpbin.send_rtp_sink_0 t. ! queue ! xvimagesink rtpbin.send_rtp_src_0 ! udpsink name=udpsink_video port=5002 host=" + ip_address + " rtpbin.send_rtcp_src_0 ! udpsink port=5003 host=" + ip_address + " sync=false async=false udpsrc port=5007 ! rtpbin.recv_rtcp_sink_0")
            print "You've sent Low Quality data"

   

    def run(self):
        try:
            global mutex, caps
            # Create bus to get events from GStreamer pipeline
            self.bus = self.pipeline.get_bus()
            print "1"
            self.bus.enable_sync_message_emission()
            print "2"
            self.bus.connect('message::error', self.on_error)
            print "3"
            #self.bus.connect('sync-message::element', self.on_message)
            print self.pipeline.set_state(Gst.State.PLAYING)
            print "4"
            time.sleep(10)
            print "5"
            source = self.pipeline.get_by_name("udpsink_video")
            print "6"
            pad = source.get_static_pad('sink')
            print "7"
	    udpcaps = pad.get_property('caps').to_string()
            print "8"
            mutex.acquire()
            caps = udpcaps
            mutex.release()

        except: 
            e = sys.exc_info()[0]
            print "Error in run method of Server: " + str(e)



    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())
	

class Client:
    def __init__(self, ip_address, partners_caps):
        print "IP_ADDRESS: " + ip_address
        print "PARTNERS_CAPS: " + partners_caps

	partners_caps = partners_caps.replace(" ", "")
	self.pipeline = Gst.parse_launch("rtpbin name=rtpbin udpsrc port=5012 caps=" + partners_caps + " ! rtpbin.recv_rtp_sink_0 rtpbin. ! rtpmp4vdepay ! tee name=t ! queue ! avdec_mpeg4 ! videoconvert ! xvimagesink name=imagesink t. ! queue ! filesink location=client.mpeg udpsrc port=5013 ! rtpbin.recv_rtcp_sink_0 rtpbin.send_rtcp_src_0 ! udpsink port=5017 host=" + ip_address + " sync=false async=false")

    def run(self):
        global webui
        #self.window.show_all()
        # You need to get the XID after window.show_all().  You shouldn't get it
        # in the on_sync_message() handler because threading issues will cause
        # segfaults there.
        Gdk.threads_enter()
        self.xid = webui.movie_window.get_property('window').get_xid()
        imagesink = self.pipeline.get_by_name("imagesink")
        imagesink.set_window_handle(self.xid)
        print self.pipeline.set_state(Gst.State.PLAYING)
        Gdk.threads_leave()
    def quit(self, window):
        t = True
        #self.pipeline.set_state(Gst.State.NULL)
        #Gtk.main_quit()

    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            print('prepare-window-handle')
            msg.src.set_property('force-aspect-ratio', True)
            msg.src.set_window_handle(self.xid)

    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())

def runServer(self, ip_address, partners_quality):
    server = Server(ip_address, partners_quality)
    server.run()
def runClient(self, ip_address, partners_caps):
    client = Client(ip_address, partners_caps)
    client.run()

def determineQuality(ip_address, quality):
    global mutex, caps
    #  First try connecting as a client
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip_address, 3000))
        s.send(quality) # Send partner your quality
        partners_quality = s.recv(1024) # Get partner's quality
        thread.start_new_thread(runServer, (None, ip_address, partners_quality)) # Actually start your server to determine caps
        while(True):
            mutex.acquire()
            if (caps != "False"):
                mutex.release()
                break
            mutex.release()
        print "YOUR THREADED CAPS!:" + caps
        mutex.acquire()
        s.send(caps) # Send your caps
        mutex.release()
        partners_caps = s.recv(1024) # Recieve partner's caps
        print "Partner choose :" + partners_quality
        print "Partners Caps:" + partners_caps
        s.close()
        return partners_caps
    except:
        e = sys.exc_info()[0]
        print "Entered Server Exception Block: " + str(e)
        serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serv.bind(("192.168.2.139", 3000))
        serv.listen(1)
        conn, addr = serv.accept()
        partners_quality = conn.recv(1024) # Get partner's quality
        conn.send(quality)  # Send partner your quality
        thread.start_new_thread(runServer, (None, ip_address, partners_quality)) # Actually start your server to determine caps
        while(True):
            mutex.acquire()
            if (caps != "False"):
                mutex.release()
                print caps
                break
            mutex.release()
        print "YOUR THREADED CAPS!:" + caps
        partners_caps = conn.recv(1024) # Recieve partner's caps
        mutex.acquire()
        conn.send(caps) # Send partner your caps
        mutex.release()
        print "Partner choose :" + partners_quality
        print "Partners Caps:" + partners_caps
        conn.close()
        return partners_caps

def startUI(self):
    Gdk.threads_enter()
    Gtk.main()
    Gdk.threads_leave()
webui = WebcamUI.WebcamUI()
thread.start_new_thread(startUI, (None,))
print "Started UI waiting for mutex..."
webui.mutex2.acquire()
print "Got the Mutex!"
ip_address = webui.ip_address
quality = webui.quality
print "GOT IP = " + ip_address
print "GOT QUALITY = " + quality
partners_caps = determineQuality(ip_address, quality)

thread.start_new_thread(runClient, (None, ip_address, partners_caps))
dummy_input = raw_input("Press Enter to Quit:")
