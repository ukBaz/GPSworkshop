# Standard Python Imports
from time import sleep
from math import hypot

# Raspberry-Pi specific imports
# Provides interface to GPIO pins
import RPi.GPIO as GPIO

# Library for CSR GPS board
import H13467

# Library for 4tronix display
import IPD


def read_temp():
    cpu_temp = ''
    try:
        cpu_temp_file = open('/sys/class/thermal/thermal_zone0/temp', 'r')
        lines = cpu_temp_file.readlines()
        cpu_temp = round(float(lines[0]) / 1000, 0)
        cpu_temp_file.close()
    except IOError:
        cpu_temp = '-.-'

    return cpu_temp


if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    GPS1 = H13467.GPS(18, 22)
    BTN = H13467.BUT(23)
    LD2 = H13467.LED(24)
    LD1 = H13467.LED(25)
    DISP = IPD.IPD()

    N1 = 0
    N2 = 0
    E1 = 0
    E2 = 0
    dist = 0

    needRef = True
    GPS1.set_time_zone_offset(0)
    # BTN.count = 2

    print 'Use CTRL-C to end loop. Cheers.'
    try:
        while 1:
            if BTN.get_count() == 0:
                LD1.off()
                LD2.off()
                print 'Temperature of CPU'
                temperature = int(read_temp())
                print '{0}*c'.format(temperature)
                DISP.set_msg('{0}*c'.format(temperature))

            if BTN.get_count() == 1:
                LD1.on()
                LD2.off()
                print 'Show time'
                gps_time = GPS1.get_local_clock()
                print gps_time
                DISP.set_clock(gps_time)

            if BTN.get_count() == 2:
                LD1.off()
                LD2.on()
                print 'Show satellite count'
                print '{0:02}:{1:02}'.format(GPS1.gps_siv, GPS1.glo_siv)
                DISP.set_clock('{0:02}{1:02}'.format(GPS1.gps_siv, GPS1.glo_siv))

            if BTN.get_count() == 3:
                print 'Show Tapemeasure'
                LD1.on()
                LD2.on()
                if needRef:
                    E1 = GPS1.utm_east
                    N1 = GPS1.utm_north
                    needRef = False
                E2 = GPS1.utm_east
                N2 = GPS1.utm_north
                dist = hypot(N1 - N2, E1 - E2)
                DISP.set_msg('{0}'.format(int(dist)))
                print '{0}'.format(int(dist))

            if BTN.get_count() > 3:
                print 'Reset button count'
                needRef = True
                BTN.count = 0

            sleep(2)

    except KeyboardInterrupt:
        print '\nInterrupt caught'

    finally:
        print 'Tidy up before exit'
        DISP.clear_display()
        GPS1.data_stop()
        GPS1.pulse_on_off()
        GPIO.cleanup()
