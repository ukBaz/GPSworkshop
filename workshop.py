# Standard Python Imports
from time import sleep
from math import sqrt, pow
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
    BTN  = H13467.BUT(23)
    LD2 = H13467.LED(24)
    GPS1 = H13467.GPS(18, 22)
    GPS1.dataStart()
    DISP = IPD.IPD()
    DISP.dispStart()
    N1 = 0
    N2 = 0
    E1 = 0
    E2 = 0
    dist = 0
    firstTime = True

    print 'Use CTRL-C to end loop'
    try:
        while 1:
            if BTN.isOdd():
                LD1.on()
                LD2.off()
                N1 = GPS1.utmEast
                E1 = GPS1.utmNorth
                DISP.setMsg('Pt2-')
                print 'Pt2-'
                firstTime = False
            else:
                if firstTime:
                    DISP.setMsg('Pt1-')
                    print 'Pt1-'
                else:
                    LD2.on()
                    LD1.on()
                    N2 = GPS1.utmEast
                    E2 = GPS1.utmNorth
                    dist = sqrt(pow(N1 - N2, 2) + pow(E1 - E2, 2))
                    DISP.setMsg('{0} P{1}'.format(dist, GPS1.precision))
                    print '{0} P{1}'.format(dist, GPS1.precision)
            sleep(1.5)
            # print chr(27) + "[2J"

    except KeyboardInterrupt:
        print '\nInterrupt caught'

    finally:
        print 'Tidy up before exit'
        DISP.clearDisp()
        GPS1.dataStop()
        GPS1.pulseOnOff()
        GPIO.cleanup()
