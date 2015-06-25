__author__ = 'barry'
# Standard Python Imports
from time import sleep
from math import hypot

# Raspberry-Pi specific imports
# Provides interface to GPIO pins
import RPi.GPIO as GPIO

# Library for CSR GPS board
import H13467

# Library for 4tronix Display Dongle
import IPD

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)  # Pin naming mode
    GPS1 = H13467.GPS(18, 22)  # Create GPS object
    BTN = H13467.BUT(23)  # Button Object
    LD2 = H13467.LED(24)  # LED 2 Object
    LD1 = H13467.LED(9)  # Create Object for LED 1
    DISP = IPD.IPD()  # 4-digit 7-Segment display opbject
    # Create variables for storing coordinates and distance
    N1 = 0
    N2 = 0
    E1 = 0
    E2 = 0
    dist = 0
    # Boolean variable
    needRef = True

    print 'Use CTRL-C to end loop'
    try:
        while 1:
            # Test for button press
            if BTN.get_count() == 0:
                # Use LEDs to show change
                LD1.off()
                LD2.off()
                if needRef:
                    # Get reference coordinates
                    E1 = GPS1.utm_east
                    N1 = GPS1.utm_north
                    needRef = False
                # Get current position
                E2 = GPS1.utm_east
                N2 = GPS1.utm_north
                # Use Pythagoras Theorem to find distance
                dist = hypot(N1 - N2, E1 - E2)
                # Show on display
                DISP.show_msg('{0}'.format(int(dist)))
                # Print debug statements
                print '{0}'.format(int(dist))
            if BTN.get_count() == 1:
                # Use LEDs to show change
                LD1.on()
                LD2.off()
                # Show last distance calculation and precision of GPS
                DISP.show_msg('{0}P{1}'.format(int(dist), int(GPS1.precision)))
                # print debug statements
                print 'n1 = {0}'.format(N1)
                print 'n2 = {0}'.format(N2)
                print 'e1 = {0}'.format(E1)
                print 'e2 = {0}'.format(E2)
                print '{0} P{1}'.format(int(dist), int(GPS1.precision))
                # Tell code it will need a new reference point
                # on next button press
                needRef = True

            if BTN.get_count() > 1:
                print 'Reset button count'
                needRef = True
                BTN.count = 0
            # Wait 1.5 seconds before updating
            sleep(1.5)

    except KeyboardInterrupt:
        print '\nInterrupt caught'

    finally:
        print 'Tidy up before exit'
        DISP.clear_display()
        GPS1.data_stop()
        GPS1.pulse_on_off()
        GPIO.cleanup()