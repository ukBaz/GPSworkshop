# Standard Python Imports
from time import sleep
import serial
import threading
import re
import os
import datetime

# Raspberry-Pi specific imports
# Provides interface to GPIO pins
import RPi.GPIO as GPIO

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

    print 'Use CTRL-C to end loop'
    try:
        while 1:
            LD1.toggle()
            # BTN.isPressed()
            print "Button has been pressed %s times" % BTN.getCount()
            if BTN.isOdd():
                LD2.on()
            else:
                LD2.off()
            print "GPS has fix? %s" % GPS1.hasFix()
            if  not GPS1.hasFix():
                DISP.setMsg('no SignAL yEt')
            elif BTN.mode == 0:
                DISP.setClock(GPS1.getClock())
            elif BTN.mode == 1:
                DISP.setMsg('tAPE')
            elif BTN.mode == 2:
                DISP.setMsg('oFF-')
                if (datetime.datetime.now() - BTN.BTNtime).seconds > 5:
                    BTN.mode = 0
                elif (BTN.modeTime - BTN.BTNtime).seconds < 0:
                    print '\n\n\n\n *******  Going Down **********\n\n\n\n'
                    os.system("shutdown -Ph now")
            print "GPS module is awake: %s" % GPS1.isAwake()
            print "Satalites in view is: %s" % GPS1.getSIV()
            print "Time is : " + GPS1.getLocalTime()
            print "Latitude is: {0} {1}".format(GPS1.latDeg, GPS1.latMin)
            print "Longitude is: {0} {1}".format(GPS1.longDeg, GPS1.longMin)
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
