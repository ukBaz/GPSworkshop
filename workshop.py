# Standard Python Imports
from time import sleep
from math import hypot
# import serial
# import threading
# import re
import os
import datetime

# Raspberry-Pi specific imports
# Provides interface to GPIO pins
import RPi.GPIO as GPIO

# Package downloaded from pypi
import utm

# Library for CSR GPS board
import H13467
# Library for 4tronix Display Dongle
import IPD

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    LD1 = H13467.LED(25)
    BTN = H13467.BUT(23)
    LD2 = H13467.LED(24)
    GPS1 = H13467.GPS(18, 22)
    DISP = IPD.IPD()
    N1 = 0
    N2 = 0
    E1 = 0
    E2 = 0
    dist = 0
    needRef = True

    print 'Use CTRL-C to end loop'
    try:
        while 1:
            if BTN.is_odd():
                if needRef:
                    N1 = GPS1.utm_east
                    E1 = GPS1.utm_north
                    needRef = False
                N2 = GPS1.utm_east
                E2 = GPS1.utm_north
                dist = hypot(N1 - N2, E1 - E2)
                DISP.show_msg('{0}'.format(int(dist)))
                print '{0}'.format(int(dist))
            else:
                DISP.show_msg('{0}P{1}'.format(int(dist), int(GPS1.precision)))
                print 'n1 = {0}'.format(N1)
                print 'n2 = {0}'.format(N2)
                print 'e1 = {0}'.format(E1)
                print 'e2 = {0}'.format(N2)
                print '{0} P{1}'.format(int(dist), int(GPS1.precision))
                needRef = True
            sleep(1.5)
            # print chr(27) + "[2J"

    except KeyboardInterrupt:
        print '\nInterrupt caught'

    finally:
        print 'Tidy up before exit'
        DISP._clear_display()
        GPS1.data_stop()
        GPS1.pulse_on_off()
        GPIO.cleanup()
