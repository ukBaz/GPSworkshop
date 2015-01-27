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
    def __init__(self):
        # Define list for digits 0..9, space, dash and DP in 7-segment (active High)
        # Display for length of time
        self.brightness = 0.005
        self.scrollSpeed = 25
        self.clock = True
        self.toDisp = '----'
        self.digits2 = {"0": 0b00111111,
                        "1": 0b00000110,
                        "2": 0b01011011,
                        "3": 0b01001111,
                        "4": 0b01100110,
                        "5": 0b01101101,
                        "6": 0b01111101,
                        "7": 0b00000111,
                        "8": 0b01111111,
                        "9": 0b01101111,
                        " ": 0b00000000,
                        "-": 0b01000000,
                        ".": 0b10000000,
                        "A": 0b01110111,
                        "r": 0b01010000,
                        "E": 0b01111001,
                        "n": 0b01010100,
                        "o": 0b01011100,
                        "F": 0b01110001,
                        "i": 0b00000100,
                        "y": 0b01101110,
                        "t": 0b01111000,
                        "S": 0b01101101,
                        "g": 0b01101111,
                        "L": 0b00111000,
                        "P": 0b01110011,
                        "?": 0b01010011}
        self.location = {"1": 0b00000001,
                         "2": 0b00000010,
                         "3": 0b00000100,
                         "4": 0b00001000}
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
        self.display_start()

    def send_digit(self, digit, pos):
        # print "**** Digit: {0} -+- Location: {1:8b}".format(digit, self.location[pos])
        # Clear data before selecting position
        self.bus.write_byte_data(self.addr, 0x12, 0x00)
        # Select position
        self.bus.write_byte_data(self.addr, 0x13, ~self.location[pos])
        # Send digit information
        self.bus.write_byte_data(self.addr, 0x12, digit)
        time.sleep(self.brightness)
        # Unselect position
        self.bus.write_byte_data(self.addr, 0x13, 0xff)

    def send4digits(self, digits):
        # print "Send digits: " + digits
        self.send_digit(int(self.digits2[digits[3]]), "1")
        self.send_digit(int(self.digits2[digits[2]]), "2")
        if self.clock:
            self.send_digit(int(self.digits2[digits[1]] | 0b10000000), "3")
            self.send_digit(int(self.digits2[digits[0]] | 0b10000000), "4")
        else:
            self.send_digit(int(self.digits2[digits[1]]), "3")
            self.send_digit(int(self.digits2[digits[0]]), "4")

    def display_start(self):
        self.receiver_thread = threading.Thread(target=self.writer)
        self.receiver_thread.setDaemon(1)
        self.receiver_thread.start()

    def set_clock(self, value):
        self.clock = True
        if len(value) < 4:
            need2add = 4 - len(value)
            value = "0" * need2add + value
        self.toDisp = str(value)

    def set_msg(self, value):
        self.clock = False
        self.toDisp = value

    def writer(self):
        while 1:
            if len(self.toDisp) == 4:
                self.send4digits(self.toDisp)
            elif len(self.toDisp) < 4:
                pad_string = ' ' * (4 - len(self.toDisp)) + self.toDisp
                self.send4digits(pad_string)
            else:
                pad_string = ' ' * 4 + self.toDisp + ' ' * 4
                for i in range(0, len(pad_string) - 3):
                    for s in range(0, self.scrollSpeed):
                        loc1 = pad_string[i]
                        loc2 = pad_string[(i + 1)]
                        loc3 = pad_string[(i + 2)]
                        loc4 = pad_string[(i + 3)]
                        visible = loc1 + loc2 + loc3 + loc4
                        self.send4digits(visible)

    @staticmethod
    def get_ip_address(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])

    def show_ip_address(self):
        words = ''
        ip_address = self.get_ip_address("eth0")
        print ip_address
        for x in ip_address:
            words += x.replace('.', '-')
        print words
        self.toDisp = words
        while 1:
            self.writer()

    def clear_display(self):
        self.bus.write_byte_data(self.addr, 0x13, 0xff)

    def test_display(self):
        for x in sorted(self.digits2):
            for y in sorted(self.location):
                for s in range(0, self.scrollSpeed):
                    self.send_digit(int(self.digits2[x]), y)
        for x in sorted(self.digits2):
            disp_string = self.digits2[x], self.digits2[x], self.digits2[x], self.digits2[x]
            for s in range(0, self.scrollSpeed):
                self.send4digits(disp_string)
        for x in range(0, 255):
            disp_string = x, x, x, x
            for s in range(0, self.scrollSpeed):
                self.send4digits(disp_string)
        while 1:
            self.writer()


if __name__ == '__main__':
    IPD1 = IPD()
    try:
        if len(sys.argv) > 1:
            allChars = list(IPD1.digits2.keys())
            word = '-'.join(allChars)
            print word
            IPD1.set_msg(word)
            IPD1.test_display()
        else:
            IPD1.show_ip_address()

    except KeyboardInterrupt:
        print '\nInterrupt caught'

    finally:
        IPD1.clear_display()
