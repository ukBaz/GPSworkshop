"""
Module for controlling 4tronix Display module
"""
# Python standard libraries
import time
import threading
import sys
import socket
import fcntl
import struct


# Raspberry Pi specific libraries
import smbus
import RPi.GPIO as GPIO


class IPD:
    """
    Class for 4tronix display module
    """
    def __init__(self):
        """
        Instantiate IPD object

        :return:
        """
        # Define list for digits 0..9, space, dash and DP in 7-segment (active High)
        # Display for length of time
        self.brightness = 0.0000005
        self.scrollSpeed = 90
        self.clock = False
        self.to_display = '----'
        self.digits2 = {'0': 0b00111111,
                        '1': 0b00000110,
                        '2': 0b01011011,
                        '3': 0b01001111,
                        '4': 0b01100110,
                        '5': 0b01101101,
                        '6': 0b01111101,
                        '7': 0b00000111,
                        '8': 0b01111111,
                        '9': 0b01101111,
                        ' ': 0b00000000,
                        '-': 0b01000000,
                        '.': 0b10000000,
                        'A': 0b01110111,
                        'r': 0b01010000,
                        'E': 0b01111001,
                        'n': 0b01010100,
                        'o': 0b01011100,
                        'F': 0b01110001,
                        'i': 0b00000100,
                        'y': 0b01101110,
                        't': 0b01111000,
                        'S': 0b01101101,
                        'g': 0b01101111,
                        'L': 0b00111000,
                        'P': 0b01110011,
                        'c': 0b01011000,
                        '*': 0b01100011,
                        '?': 0b01010011}
        self.location = {'1': 0b00000001,
                         '2': 0b00000010,
                         '3': 0b00000100,
                         '4': 0b00001000}
        # For revision 1 Raspberry Pi bus =smbus.SMBus(0)
        # change to bus = smbus.SMBus(1) for revision 2.
        if GPIO.RPI_REVISION > 1:
            self.bus = smbus.SMBus(1)
        else:
            self.bus = smbus.SMBus(0)
        self.addr = 0x20  # I2C address of MCP23017
        self.IODIRA = 0x00  # Pin direction register bank A
        self.IODIRB = 0x01  # Pin direction register bank B
        self.OUTPIN = 0x00  # Set as output pins
        self.bus.write_byte_data(self.addr, 0x00, 0x00)  # Set all of bank 0 to outputs
        self.bus.write_byte_data(self.addr, 0x01, 0x00)  # Set all of bank 1 to outputs
        self.bus.write_byte_data(self.addr, 0x13, 0xff)  # Set all of bank 1 to High (Off)
        self.receiver_thread = None  # To store thread information
        self._display_start()

    def _send_digit(self, digit, pos):
        """
        Send code to chosen digit location
        :param digit: binary code of segments to display
        :param pos: binary code to choose digit
        :return:
        """
        # print '**** Digit: {0} -+- Location: {1:8b}'.format(digit, self.location[pos])
        # Clear data before selecting position
        self.bus.write_byte_data(self.addr, 0x12, 0x00)
        # Select position
        # self.bus.write_byte_data(self.addr, 0x13, ~self.location[pos])
        self.bus.write_byte_data(self.addr, 0x13, ~pos)
        # Send digit information
        self.bus.write_byte_data(self.addr, 0x12, digit)
        time.sleep(self.brightness)
        # Unselect position
        self.bus.write_byte_data(self.addr, 0x13, 0xff)

    def _send4digits(self, digits):
        """
        Send four text characters to be displayed
        :param digits: Four characters to display
        :return:
        """
        # print 'Send digits: {0} '.format(self.digits2[str(digits[3])])
        self._send_digit(int(self.digits2[str(digits[3])]), self.location['1'])
        self._send_digit(int(self.digits2[str(digits[2])]), self.location['2'])
        if self.clock:
            self._send_digit(int(self.digits2[str(digits[1])] | 0b10000000), self.location['3'])
            self._send_digit(int(self.digits2[str(digits[0])] | 0b10000000), self.location['4'])
        else:
            self._send_digit(int(self.digits2[str(digits[1])]), self.location['3'])
            self._send_digit(int(self.digits2[str(digits[0])]), self.location['4'])

    def _display_start(self):
        """
        Start thread that will write to the display
        :return:
        """
        self.receiver_thread = threading.Thread(target=self._writer)
        self.receiver_thread.setDaemon(1)
        self.receiver_thread.start()


    def _writer(self):
        """
        Run by the thread and will display
        :return:
        """
        while 1:
            if len(self.to_display) == 4:
                self._send4digits(self.to_display)
            elif len(self.to_display) < 4:
                pad_string = ' ' * (4 - len(self.to_display)) + self.to_display
                self._send4digits(pad_string)
            else:
                pad_string = ' ' * 4 + self.to_display + ' ' * 4
                for i in range(0, len(pad_string) - 3):
                    for s in range(0, self.scrollSpeed):
                        loc1 = pad_string[i]
                        loc2 = pad_string[(i + 1)]
                        loc3 = pad_string[(i + 2)]
                        loc4 = pad_string[(i + 3)]
                        visible = loc1 + loc2 + loc3 + loc4
                        self._send4digits(visible)

    def show_clock(self, value):
        """
        Will display values passed with a colon in the middle.
        e.g. '1200' will be displayed as '12:00'
        If more than four characters passed then nothing will be displayed
        If less than four characters then leading zeros are added
        :param value: Input string
        :return:
        """
        self.clock = True
        if len(value) < 4:
            need2add = 4 - len(value)
            value = '0' * need2add + value
        self.to_display = str(value)

    def show_msg(self, value):
        """
        Will display the value passed.
        If less than four characters leading spaces will be added
        If more than four characters are passed then will scroll message
        :param value: Input string
        :return:
        """
        self.clock = False
        self.to_display = value

    @staticmethod
    def _get_ip_address(ifname):
        """
        Will return the ip address for this computer
        :param ifname: the interface of interest e.g. eth0
        :return: The IP address of the given interface
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])

    def show_ip_address(self):
        """
        Gets the IP address for eth0 and display it
        :return:
        """
        words = ''
        ip_address = self._get_ip_address('eth0')
        print ip_address
        for x in ip_address:
            words += x.replace('.', '-')
        print words
        self.to_display = words

    def _clear_display(self):
        """
        Used to clean up the display on exit from program
        :return:
        """
        self.bus.write_byte_data(self.addr, 0x13, 0xff)

    def _test_display(self):
        """
        Scroll through test sequence.
        Needs to stop display thread to work correctly
        :return:
        """
        for x in sorted(self.digits2):
            for y in sorted(self.location):
                for s in range(0, self.scrollSpeed):
                    self._send_digit(self.digits2[x], self.location[y])
        for x in sorted(self.digits2):
            disp_string = x, x, x, x
            for s in range(0, self.scrollSpeed):
                self._send4digits(disp_string)
        for x in range(0, 255):
            for s in range(0, self.scrollSpeed):
                self._send_digit(x, 1)
                self._send_digit(x, 2)
                self._send_digit(x, 4)
                self._send_digit(x, 8)


if __name__ == '__main__':
    IPD1 = IPD()
    try:
        if len(sys.argv) > 1:
            allChars = list(IPD1.digits2.keys())
            word = '-'.join(allChars)
            print word
            print 'change'
            IPD1.show_msg('')
            IPD1._test_display()
        else:
            IPD1.show_ip_address()

    except KeyboardInterrupt:
        print '\nInterrupt caught'

    finally:
        IPD1._clear_display()
