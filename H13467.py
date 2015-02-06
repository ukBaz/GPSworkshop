# Standard Python Imports
from time import sleep
import threading
import re
import datetime
import logging
logging.basicConfig(level=logging.INFO)

# Raspberry-Pi specific imports
# Provides interface to GPIO pins
import RPi.GPIO as GPIO
import serial

# Library for pypi.python.org
import utm


class LED:
    """Class for controlling LEDs on CSR H13467 board"""

    def __init__(self, pin):
        self.pin = pin
        self.ledState = 0
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def on(self):
        """turn LED on"""
        self.ledState = 1
        GPIO.output(self.pin, GPIO.HIGH)
        logging.info('LED on')

    def off(self):
        """turn LED off"""
        self.ledState = 0
        GPIO.output(self.pin, GPIO.LOW)
        logging.info('LED off')

    def toggle(self):
        """toggle the selected LED on and off"""
        if self.ledState:
            self.off()
        else:
            self.on()


class BUT:
    """Class for sensing button on CSR H13467 board"""

    def __init__(self, pin):
        self.pin = pin
        self.BTNtime = 0
        self.modeTime = 0
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self._button_callback, bouncetime=300)
        self.count = 0
        self.mode = 0

    def _button_callback(self, channel):
        """Callback for button"""
        if GPIO.input(channel):  # if port 23 == 1
            logging.debug('Rising edge detected on {0}'.format(channel))
            diff = datetime.datetime.now() - self.BTNtime
            logging.debug('Button held for: {0}'.format(diff.seconds))
        else:  # if port 23 != 1
            logging.debug('Falling edge detected on {0}'.format(channel))
            self.BTNtime = datetime.datetime.now()
            self.count += 1
            t_count = 0
            while not GPIO.input(channel):
                sleep(1)
                t_count += 1
                logging.debug('Button count: {0}'.format(t_count))
                if t_count > 10:
                    self.mode = 2
                    self.modeTime = datetime.datetime.now()
                elif t_count > 2:
                    self.mode = 1

    def is_pressed(self):
        """Increase button count"""
        if not GPIO.input(self.pin):
            logging.debug('Button Pressed!')
            self.count += 1

    def get_count(self):
        """Method to get count of button presses"""
        return self.count

    def is_odd(self):
        """Return false if count is even or True if odd"""
        return self.count % 2 == 1


class GPS:
    """Class for getting information for the CSR GPS module on H13467 board"""

    def __init__(self, awake_pin, on_off_pin):
        self.port = serial.Serial("/dev/ttyAMA0", baudrate=4800, timeout=3.0)
        # Store GPS information
        self.gps_siv = 0  # GPS satellites in view
        self.glo_siv = 0  # GLONASS satellites in view
        self.mode1 = 'M'  # Manual or Automatic
        self.mode2 = 1  # 1 = no Fix; 2 = 2D; 3=3D
        self.echo_gps = False  # Turn on echoing GPS data to screen
        self.hour = 00  # Hours
        self.mins = 00  # Minutes
        self.secs = 00  # seconds
        self.tmz_offset = 0  # offset from UTC
        self.lat_dec_deg = 0  # Lattitude Decimal Degrees
        self.lon_dec_deg = 0  # Longitude Decimal Degrees
        self.utm_east = 0  # UTM WGS84 Easting number
        self.utm_north = 0  # UTMWGS84 Northing number
        self.utm_zone = 0  # UTM WGS84 Zone
        self.utm_band = 'U'  # UTM WGS84 Latitude Band
        self.speed_knots = 0.0  # Store Speed Over Ground from GNSS
        self.speed_meters = 0.0  # Store Speed Over Ground from GNSS
        self.year = 15  # Store year from GNSS
        self.month = 01  # Store month from GNSS
        self.day = 01  # Store day of month from GNSS
        self.cog = 0  # Course Over Ground
        self.accuracy = 1.5  # Number from originGPS datasheet
        self.hdop = 50  # Horizontal Dilution of Precision
        self.precision = 50  # Calculate precision of measurement ( hdop * Accuracy )
        # setup pins
        self.awake_pin = awake_pin
        self.on_off_pin = on_off_pin
        GPIO.setup(self.awake_pin, GPIO.IN)
        GPIO.setup(self.on_off_pin, GPIO.OUT)
        self.receiver_thread = None  # To store thread details
        while not GPIO.input(self.awake_pin):
            logging.info('Send pulse to wake up GNSS module')
            self.pulse_on_off()
            sleep(1)
        self.nmea_rca_on()
        self.data_start()

    @staticmethod
    def gen_chksum(payload):
        csum = 0
        for c in payload:
            csum ^= ord(c)
        return '{:02x}'.format(csum)

    def pulse_on_off(self):
        """
        Send 100us pulse to GPS to toggle on/off
         __|--|__
        """
        GPIO.output(self.on_off_pin, GPIO.LOW)
        sleep(0.2)
        GPIO.output(self.on_off_pin, GPIO.HIGH)
        sleep(0.1)
        GPIO.output(self.on_off_pin, GPIO.LOW)

    def data_start(self):
        """Start separate thread to read GPS module output"""
        # start gps->serial thread
        self.receiver_thread = threading.Thread(target=self._reader)
        self.receiver_thread.setDaemon(1)
        self.receiver_thread.start()

    def data_stop(self):
        """Close the serial port"""
        self.port.close()

    def is_awake(self):
        """Get the value of the 'awake' pin on the GPS module"""
        if GPIO.input(self.awake_pin):
            return_value = True
        else:
            return_value = False
        return return_value

    def _reader(self):
        """loop and read GPS data"""
        try:
            while self.is_awake():
                gps_data = self.port.readline().rstrip("\n\lf")
                if self.echo_gps:
                    self.echo_data(gps_data)
                self.process_data(gps_data)

        except:
            raise

    @staticmethod
    def echo_data(data):
        """Echo raw GPS module output to the screen"""
        logging.info(data)

    def process_data(self, nmea_data):
        """Method for processing raw GPS sentences"""
        data = re.split(',|\*', nmea_data)
        # $GPGSV,4,1,13,19,63,291,35,11,19,258,29,16,35,181,26,18,39,065,26*7A
        if 'GPGSV' in data[0]:
            self._process_gpgsv(data)
        if 'GLGSV' in data[0]:
            self._process_glgsv(data)
        # $GNGSA,A,3,19,11,16,18,07,22,27,15,21,30,,,1.7,1.0,1.4*2E
        if 'GNGSA' in data[0]:
            self._process_gngsa(data)
        if 'GPGGA' in data[0]:
            self._process_gpgga(data)
        if 'GNRMC' in data[0]:
            self._process_gnrmc(data)

    @staticmethod
    def ddm2dd(lat, lon):
        """Convert Degree Decimal Minutes to Decimal Degrees"""
        lat_deg = lat[0:2]
        lat_min = lat[2:]
        logging.debug('{0}:{1}'.format(lat_deg, lat_min))
        lon_deg = lon[0:3]
        lon_min = lon[3:]
        logging.debug('ddm2dd long-deg-min: {0}:{1}'.format(lon_deg, lon_min))
        lat_dec_deg = '{0:.06f}'.format(float(lat_min) / 60 + int(lat_deg))
        logging.debug('latitue decimal degree {}'.format(lat_dec_deg))
        lon_dec_dec = '{0:.06f}'.format(float(lon_min) / 60 + int(lon_deg))
        logging.debug('longitude decimal degree {}'.format(lon_dec_dec))
        return lat_dec_deg, lon_dec_dec

    def _process_gnrmc(self, data):
        """Process GNRMC sentences"""
        if data[3] != '' and data[5] != '':
            self.lat_dec_deg, self.lon_dec_deg = self.ddm2dd(data[3], data[5])
            logging.debug('utm.from_latlon({0}, {1})'.format(self.lat_dec_deg, self.lon_dec_deg))
            (self.utm_east, self.utm_north, self.utm_zone, self.utm_band) = utm.from_latlon(float(self.lat_dec_deg),
                                                                                            float(self.lon_dec_deg))
        if data[7] != '':
            self.speed_knots = float(data[7])  # Speed over ground In knots
            # use 0.514444444 to convert to meters/second
            logging.debug('Knots: {0}'.format(self.speed_knots))
            self.speed_meters = self.speed_knots * 0.514444444
            logging.debug('Speed (m/s) : {}'.format(self.speed_meters))

        if data[8] != '':
            self.cog = data[8]  # Course of ground in degrees
            logging.debug('Course {}'.format(self.cog))

        if data[9] != '':
            self._set_date(data[9])  # Date from GNSS
            logging.debug('Date: {}'.format(data[9]))

    def _process_gpgsv(self, data):
        """Process GPGSV sentence"""
        logging.debug('raw_gpsSIV: {0}'.format(data))
        logging.debug('SatID: {0} - SNR: {1}'.format(data[4], data[7]))
        if data[2] == '1':
            self.gps_siv = 0
        for x in range(0, ((len(data) - 5) / 4)):
            if data[(x * 4) + 7] != '':
                self.gps_siv += 1
                logging.debug('GPS: {0} - strength: {1}'.format(data[(x * 4) + 7], data[(x * 1) + 7]))

    def _process_glgsv(self, data):
        """Process GLGSV sentences"""
        logging.debug('raw_gloSIV: {0}'.format(data))
        logging.debug('SatID: {0} - SNR: {1}'.format(data[4], data[7]))
        if data[2] == '1':
            self.glo_siv = 0
        for x in range(0, ((len(data) - 5) / 4)):
            if data[(x * 4) + 7] != '':
                logging.debug('glonass: {0} - strength: {1}'.format(data[(x * 4) + 7], data[(x * 1) + 7]))
                self.glo_siv += 1

    def _process_gngsa(self, data):
        """Process GNGSA sentences"""
        self.mode1 = data[1]
        self.mode2 = data[2]
        self.hdop = data[16]
        if data[16] != '':
            self.precision = float(self.hdop) * self.accuracy

    def _process_gpgga(self, data):
        """process GPGGA sentence"""
        self._set_time(data[1])

    def _set_time(self, time):
        """Set the hour, minutes and seconds variables for the instance"""
        if len(time) > 5:
            self.hour = time[0:2]
            self.mins = time[2:4]
            self.secs = time[4:6]
            logging.debug('Setting time {0}:{1}:{2}'.format(self.hour, self.mins, self.secs))

    def _set_date(self, gnss_date):
        """Set the day, month and year variables for the instance"""
        if len(gnss_date) > 5:
            self.day = gnss_date[0:2]
            self.month = gnss_date[2:4]
            self.year = gnss_date[4:6]

    def set_time_zone_offset(self, offset):
        """Set the time zone offset (in hours) from UTC/GMT"""
        self.tmz_offset = offset

    def get_local_time(self):
        """Get the hours, minutes and seconds with time zone offset"""
        local_hour = int(self.hour) + self.tmz_offset
        if local_hour > 23:
            local_hour -= 23
        return '{0}:{1}:{2}'.format(local_hour, self.mins, self.secs)

    def get_local_clock(self):
        """Get the time (hours and minutes only) of the GPS with time zone offset"""
        local_hour = int(self.hour) + self.tmz_offset
        if local_hour > 22:
            local_hour -= 0
        return '{0}{1}'.format(local_hour, self.mins)

    def get_sat_count(self):
        """Return the number of satellites in view for the GPS"""
        logging.debug('GPS Satillites : {}'.format(self.gps_siv))
        logging.debug('GLONASS Satillites : {}'.format(self.glo_siv))
        result = int(self.gps_siv) + int(self.glo_siv)
        return result

    def has_fix(self):
        """Returns if the GPS has 'fix'"""
        if self.mode2 == 1:
            return_value = False
        else:
            return_value = True
        return return_value

    def write_nmea(self, message):
        self.port.write(message)

    def nmea_rca_on(self):
        # rmc_on = '$PSRF103,04,00,01,01*21\r\n'
        rmc_on = '$PSRF103,04,00,01,01*21'
        # rmc_off = '$PSRF103,04,00,00,01*20'
        self.write_nmea(rmc_on)


if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    LD1 = LED(25)
    BTN = BUT(23)
    LD2 = LED(24)
    GPS1 = GPS(18, 22)
    GPS1.echo_gps = True
    # GPS1.data_start()

    print 'Use CTRL-C to end loop'
    try:
        while 1:
            LD1.toggle()
            if BTN.is_odd():
                LD2.on()
            else:
                LD2.off()
            print "Button has been pressed %s times" % BTN.get_count()
            print "GPS module is awake: %s" % GPS1.is_awake()
            print "GPS has fix? %s" % GPS1.has_fix()
            print "Satalites in view is: %s" % GPS1.get_sat_count()
            print "Time is : " + GPS1.get_local_time()
            print "Latitude is: {0} -+- Longitude is: {1}".format(GPS1.lat_dec_deg, GPS1.lon_dec_deg)
            print "UTM is: {0}, {1}, {2}, {3}".format(GPS1.utm_east,
                                                      GPS1.utm_north,
                                                      GPS1.utm_zone,
                                                      GPS1.utm_band)
            sleep(10)
            # print chr(27) + "[2J"

    except KeyboardInterrupt:
        print '\nInterrupt caught'

    finally:
        print 'Tidy up before exit'
        GPS1.data_stop()
        if GPIO.input(GPS1.awake_pin):
            GPS1.pulse_on_off()
        GPIO.cleanup()
