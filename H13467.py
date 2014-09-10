# Standard Python Imports
from time import sleep
import serial
import threading
import re
import datetime

# Raspberry-Pi specific imports
# Provides interface to GPIO pins
import RPi.GPIO as GPIO

# Library for pypi.python.org
import utm


class LED:
    'Class for controling LEDs on H13467 board'
    
    def __init__(self, pin):
        self.pin = pin
        self.ledState = 0
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def on(self):
        'turn LED on'
        self.ledState = 1
        GPIO.output(self.pin, GPIO.HIGH)
        print 'LED on'

    def off(self):
        'turn LED off'
        self.ledState = 0
        GPIO.output(self.pin, GPIO.LOW)
        print 'LED off'

    def toggle(self):
        'toggle the selected LED on and off'
        if self.ledState:
            self.off()
        else:
            self.on()


class BUT:
    'Class for sensing button on H13467 board'

    def __init__(self, pin):
        self.pin = pin
        self.BTNtime = 0
        self.modeTime = 0
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self.BTNcallback, bouncetime=300)
        self.count = 0
        self.mode = 0

    def BTNcallback(self, channel):
        if GPIO.input(channel):         # if port 23 == 1
            print "Rising edge detected on {0}".format(channel)
            diff = datetime.datetime.now() - self.BTNtime
            print 'Button held for: {0}'.format(diff.seconds)
        else:                                    # if port 23 != 1
            print "Falling edge detected on {0}".format(channel)
            self.BTNtime = datetime.datetime.now()
            self.count += 1
            tCount = 0
            while not GPIO.input(channel):
                sleep(1)
                tCount += 1
                print tCount
                if tCount > 10:
                    self.mode = 2
                    self.modeTime = datetime.datetime.now()
                elif tCount > 2:
                    self.mode = 1

    def isPressed(self):
        if GPIO.input(self.pin) == False:
            print 'Button Pressed!'
            self.count+=1

    def getCount(self):
        return self.count

    def isOdd(self):
        return self.count % 2 == 1


class GPS:
    'Class for getting information for GPS module on H13467 board'

    def __init__(self, awakePin, onOffPin):
        self.port = serial.Serial("/dev/ttyAMA0", baudrate=4800, timeout=3.0)
        # Store GPS information
        self.gpsSIV = 0 # GPS satellites in view
        self.gloSIV = 0 # GLONASS satellites in view
        self.mode1 = 'M' # Manual or Automatic
        self.mode2 = 1 # 1 = no Fix; 2 = 2D; 3=3D
        self.echoGPS = False # Turn on echoing GPS data to screen
        self.hour = 00 # Hours
        self.mins = 00 # Minutes
        self.secs = 00 # seconds
        self.TMZ    = 1 # offset from UTC
        self.latDD = 0 # Lattitude Decimal Degrees
        self.lonDD = 0 # Longitude Decimal Degrees
        self.utmEast = 0 # UTM WGS84 Easting number
        self.utmNorth = 0 # UTMWGS84 Northing number
        self.utmZone = 0 # UTM WGS84 Zone
        self.utmBand = 'U' # UTM WGS84 Latitude Band
        self.accuracy = 1.5 # Number from originGPS datasheet
        self.HDOP = 50 # Horizontal Dilution of Precision
        self.precision = 50 # Calculate precision of measurement ( HDOP * Accuracy )
        # setup pins
        self.awakePin = awakePin
        self.onOffPin = onOffPin
        GPIO.setup(self.awakePin, GPIO.IN)
        GPIO.setup(self.onOffPin, GPIO.OUT)
        self.pulseOnOff()

    def pulseOnOff(self):
        # send pulse to switch module on __|--|__
        GPIO.output(self.onOffPin, GPIO.LOW)
        sleep(0.2)
        GPIO.output(self.onOffPin, GPIO.HIGH)
        sleep(0.1)
        GPIO.output(self.onOffPin, GPIO.LOW)

    def dataStart(self):
        # start gps->serial thread
        self.receiver_thread = threading.Thread(target=self.reader)
        self.receiver_thread.setDaemon(1)
        self.receiver_thread.start()

    def dataStop(self):
        self.port.close()

    def isAwake(self):
        if GPIO.input(self.awakePin):
            returnVal = True
        else:
            returnVal = False
        return returnVal

    def reader(self):
        'loop and read GPS data'
        try:
            while self.isAwake():
                gpsData = self.port.readline().rstrip("\n\lf")
                if self.echoGPS:
                    self.echoData(gpsData)
                self.processData(gpsData)

        except:
            raise

    def echoData(self, data):
        print(data)

    def processData(self, nmeaData):
        data = re.split(',|\*', nmeaData)
        # $GPGSV,4,1,13,19,63,291,35,11,19,258,29,16,35,181,26,18,39,065,26*7A
        if 'GPGSV' in data[0]:
            self.processGPGSV(data)
        if 'GLGSV' in data[0]:
            self.processGLGSV(data)
        # $GNGSA,A,3,19,11,16,18,07,22,27,15,21,30,,,1.7,1.0,1.4*2E
        if 'GNGSA' in data[0]:
            self.processGNGSA(data)
        if 'GPGGA' in data[0]:
            self.processGPGGA(data)
        if 'GNRMC' in data[0]:
            self.processGNRMC(data)

    def ddm2dd(self, lat, lon):
        'Convert Degree Decimal Minutes to Decimal Degrees'
        latDeg = lat[0:2]
        latMin = lat[2:]
        # print '{0}:{1}'.format(latDeg, latMin)
        lonDeg = lon[0:3]
        lonMin = lon[3:]
        # print '{0}:{1}'.format(lonDeg, lonMin)
        latDD = '{0:.06f}'.format(float(latMin)/60 + int(latDeg))
        # print latDD
        lonDD = '{0:.06f}'.format(float(lonMin)/60 + int(lonDeg))
        # print lonDD
        return (latDD, lonDD)

    def processGNRMC(self, data):
        if (data[3] != '' and data[5] != ''):
            self.latDD, self.lonDD = self.ddm2dd(data[3], data[5])
            # print 'utm.from_latlon({0}, {1})'.format(self.latDD, self.lonDD)
            (self.utmEast, self.utmNorth, self.utmZone, self.utmBand) = utm.from_latlon(float(self.latDD), float(self.lonDD))

    def processGPGSV(self, data):
        self.gpsSIV = data[3]

    def processGLGSV(self, data):
        self.gloSIV = data[3]
        if self.gloSIV == '':
            self.gloSIV = 0

    def processGNGSA(self, data):
        self.mode1 = data[1]
        self.mode2 = data[2]
        self.HDOP = data[16]
        if data[16] != '':
            self.precision = float(self.HDOP) * self.accuracy

    def processGPGGA(self, data):
        self.setTime(data[1])

    def setTime(self, time):
        # print time
        if len(time) > 5:
            self.hour = time[0:2]
            self.mins = time[2:4]
            self.secs = time[4:6]
            # print "Setting time {0}:{1}:{2}".format(self.hour, self.mins, self.secs)

    def setTMZ(self, offset):
        self.TMZ = offset

    def getLocalTime(self):
        localHour = int(self.hour) + self.TMZ 
        if localHour > 23:
            localHour -= 23
        return '{0}:{1}:{2}'.format(localHour, self.mins, self.secs)

    def getClock(self):
        localHour = int(self.hour) + self.TMZ 
        if localHour > 22:
            localHour -= 0
        return '{0}{1}'.format(localHour, self.mins)

    def getSIV(self):
        print "GPS Satillites : " + str(self.gpsSIV)
        print "GLONASS Satillites : " + str(self.gloSIV)
        result = int(self.gpsSIV) + int(self.gloSIV)
        return result

    def hasFix(self):
        if self.mode2 == 1:
            returnVal = False
        else:
            returnVal = True
        return returnVal

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    LD1 = LED(25)
    BTN = BUT(23)
    LD2 = LED(24)
    GPS1 = GPS(18, 22)
    GPS1.echoGPS = True
    GPS1.dataStart()

    print 'Use CTRL-C to end loop'
    try:
        while 1:
            LD1.toggle()
            if BTN.isOdd():
                LD2.on()
            else:
                LD2.off()
            print "Button has been pressed %s times" % BTN.getCount()
            print "GPS module is awake: %s" % GPS1.isAwake()
            print "GPS has fix? %s" % GPS1.hasFix()
            print "Satalites in view is: %s" % GPS1.getSIV()
            print "Time is : " + GPS1.getLocalTime()
            print "Latitude is: {0} -+- Longitude is: {1}".format(GPS1.latDD, GPS1.lonDD)
            print "UTM is: {0}, {1}, {2}, {3}".format(GPS1.utmEast,
                                                      GPS1.utmNorth,
                                                      GPS1.utmZone,
                                                      GPS1.utmBand)
            sleep(5)
            # print chr(27) + "[2J"

    except KeyboardInterrupt:
        print '\nInterrupt caught'

    finally:
        print 'Tidy up before exit'
        GPS1.dataStop()
        GPS1.pulseOnOff()
        GPIO.cleanup()
