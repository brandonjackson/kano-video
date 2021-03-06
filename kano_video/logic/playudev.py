#!/usr/bin/env python

# playudev.py
#
# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# Play media using omxplayer, but listening for keyboard events from udev directly
#

import struct
import subprocess
import threading
import csv

from kano.logging import logger

#
# We need to play well with Gtk version 2 and version 3 clients
#
try:
    from gi.repository import Gtk, Gdk, GObject
except ImportError:
    import gtk as Gtk
    import gtk.gdk as Gdk
    import gobject as GObject


def get_keyboard_input_device(fdevice_list='/proc/bus/input/devices'):
    '''
    Most keyboards send data to /dev/input/event0, but some use a different device.
    This function heuristically finds the correct device name that the kernel decides to map.
    We are reading /proc/bus/input/devices in search for an entry H: (handler)
    that says "kbd".

    The name at the end *should* be the device name mapped at /dev/input.
    Any other combination seems to point to other devices (trackpads and various other goodies)

    On pre 4.4.7 linux kernels we were used to see this:

    "H: Handlers=kbd event0"

    But, starting on recent kernel 4.4.7-v7+, we notice that the keyboard is reported with leds support.

    "H: Handlers=kbd leds event1"

    The correct mapping in this case seems to be the last reported one (there are commonly 2 reported).
    Tested on 2 common keyboards, and 3 RT, trackpad based ones, including the official Kano Keyboard.

    https://www.kernel.org/doc/Documentation/input/input.txt
    '''

    # If we can't find the device, we default to most commonly used
    keyboard_input_device = '/dev/input/event0'

    with open(fdevice_list, 'r') as csvfile:
        input_devices = csv.reader(csvfile, delimiter=' ', lineterminator='\n', skipinitialspace=True)
        for ndevice, device_info in enumerate(input_devices):

            try:
                if device_info[1] == 'Handlers=kbd' and \
                   device_info[2] == 'leds' and \
                   device_info[3].startswith('event'):

                    # will iterate until the last reported kbd device is captured
                    keyboard_input_device='/dev/input/{}'.format(device_info[3].strip())
            except:
                pass

    return keyboard_input_device


def wait_for_keys(pomx):
    '''
    Listens for keyboard events from /dev/input
    translates ESC, Q, Space, P, -, + to omxplayer via its stdin.
    pomx is a subprocess Popen object.
    '''

    # Ask the kernel which device is mapping the input keyboard
    infile_path = get_keyboard_input_device()
    logger.info('wait_for_keys is using keyboard input device: %s' % infile_path)

    # long int, long int, unsigned short, unsigned short, unsigned int
    FORMAT = 'llHHI'
    EVENT_SIZE = struct.calcsize(FORMAT)

    # Open the keyboard device file in binary mode
    in_file = open(infile_path, "rb")

    event = in_file.read(EVENT_SIZE)

    while event:
        (tv_sec, tv_usec, type, code, value) = struct.unpack(FORMAT, event)

        # other keys you wish to send to omxplayer should be added here
        # future updates to omxplayer need to be taken into account here

        #print "type {} | code {} | value {}".format(type, code, value)

        try:
            if (type == 1 and code == 1 and value == 0) or (type == 1 and code == 16 and value == 0):

                logger.info('keyboard Esc/Q has been detected, terminating omxplayer')

                # The key "esc" or "q" has been released, quit omxplayer
                pomx.stdin.write('q')
                pomx.stdin.flush()
                
                # finish the thread
                break

            elif (type == 1 and code == 25 and value == 0) or (type == 1 and code == 57 and value == 0):
                # The key "p" or "space" has been released, pause/resume the media
                pomx.stdin.write(' ')
                pomx.stdin.flush()

            elif type == 1 and code == 12 and value == 0:
                # The key "-" has been released, decrease the volume
                pomx.stdin.write('-')
                pomx.stdin.flush()

            elif type == 1 and code == 13 and value == 0:
                # The key "+" has been released, increase the volume
                pomx.stdin.write('+')
                pomx.stdin.flush()

        except IOError:
            # OMXplayer terminated and the pipe is not valid anymore. Terminate this thread
            in_file.close()
            return

        except:
            # We want to attend the user as much as we can, so blindfold on any unrelated problem
            pass

        # read the next event from the keyboard input stream
        event = in_file.read(EVENT_SIZE)

    in_file.close()


def run_video(win, cmdline):
    '''
    Start omxplayer along with a thread to watch and send special keyboard
    keys like Q, Space, etc. If win is not None, it is meant to be a Gtk Window
    which will be sent a "destroy" event asynchronously once omxplayer terminates.
    Returns omxplayer error code.
    '''
    logger.info('playudev starting video Popen object along with Keyboard event thread')
    pomx = subprocess.Popen(cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

    # A thread will listen for key events and send them to OMXPlayer
    t = threading.Thread(target=wait_for_keys, args=(pomx,))
    t.daemon = True
    t.start()

    # Wait for OMXPLayer to terminate
    rc = pomx.wait()

    if win:
        GObject.idle_add(win.destroy)

    logger.info('playudev omxplayer process has terminated')


class VideoKeyboardEngulfer(Gtk.Window):
    '''
    Create a full screen empty window to capture and discard all keyboard and
    mouse events. Omxplayer will be positioned itself on top of it.
    '''
    def __init__(self, cmdline):
        Gtk.Window.__init__(self)
        self.rc = -1
        self.fullscreen()
        self.play_video(cmdline)

    def play_video(self, cmdline):
        '''
        Detach a thread to launch omxplayer and a keyboard event watcher
        '''
        t = threading.Thread(target=run_video, args=(self, cmdline,))
        t.daemon = True
        t.start()


def run_player(cmdline, init_threads=True, keyboard_engulfer=True):
    '''
    This is the main function to play a video, cmdline is the omxplayer command.

    Set init_threads to False if your app is multi-threaded and you 
    already called GObject.threads_init().

    If your app is multi-threaded, you want to set keyboard_engulfer to False
    and provide your own strategy to capture all mouse and keyboard events that
    traverse through the omxplayer video window.

    Otherwise, setting keyboard_engulfer to True will do that for you,
    by creating a fake full screen window that captures and discards all these events.
    '''
    rc = -1

    if init_threads:
        GObject.threads_init()

    if keyboard_engulfer:
        win = VideoKeyboardEngulfer(cmdline)
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        Gtk.main()
        rc = win.rc
    else:
        rc = run_video(None, cmdline)

    return rc
