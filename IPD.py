
# Python standard libraries
import smbus, time, subprocess, threading, sys, socket, fcntl, struct

# Raspberry Pi specific libraries
import RPi.GPIO as GPIO


class IPD:

    def __init__(self):
        # Define list for digits 0..9, space, dash and DP in 7-segment (active High)
        # Display for length of time
        self.brightness = 0.005
        self.scrollSpeed = 25
        self.clock = True
        self.toDisp = '----'
        self.digits2 = {"0" : 0b00111111,
                                     "1" : 0b00000110,
                                     "2" : 0b01011011,
                                     "3" : 0b01001111,
                                     "4" : 0b01100110,
                                     "5" : 0b01101101,
                                     "6" : 0b01111101,
                                     "7" : 0b00000111,
                                     "8" : 0b01111111,
                                     "9" : 0b01101111,
                                     " " : 0b00000000,
                                     "-" : 0b01000000,
                                     "." : 0b10000000,
                                     "A" : 0b01110111,
                                     "r" : 0b01010000,
                                     "E" : 0b01111001,
                                     "n" : 0b01010100,
                                     "o" : 0b01011100,
                                     "F" : 0b01110001,
                                     "i" : 0b00000100,
                                     "y" : 0b01101110,
                                     "t" : 0b01111000,
                                     "S" : 0b01101101,
                                     "g" : 0b01101111,
                                     "L" : 0b00111000,
                                     "P" : 0b01110011}
        self.location = {"1" : 0b00000001,
                                         "2" : 0b00000010,
                                         "3" : 0b00000100,
                                         "4" : 0b00001000}
        # For revision 1 Raspberry Pi bus =smbus.SMBus(0)
        # change to bus = smbus.SMBus(1) for revision 2.
        if GPIO.RPI_REVISION > 1:
            self.bus = smbus.SMBus(1)
        else:
            self.bus = smbus.SMBus(0) 
        self.addr = 0x20 # I2C address of MCP23017
        self.IODIRA = 0x00 # Pin direction register bank A
        self.IODIRB = 0x01 # Pin direction register bank B
        self.OUTPIN = 0x00 # Set as output pins
        self.bus.write_byte_data(self.addr, 0x00, 0x00) # Set all of bank 0 to outputs 
        self.bus.write_byte_data(self.addr, 0x01, 0x00) # Set all of bank 1 to outputs 
        self.bus.write_byte_data(self.addr, 0x13, 0xff) # Set all of bank 1 to High (Off) 

    def sendDigit(self, digit, pos):
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

    def send4Digits(self, word):
        # print "Send word: " + word
        self.sendDigit(int(self.digits2[word[3]]), "1")
        self.sendDigit(int(self.digits2[word[2]]), "2")
        if self.clock:
            self.sendDigit(int(self.digits2[word[1]] | 0b10000000), "3")
            self.sendDigit(int(self.digits2[word[0]] | 0b10000000), "4")
        else:
            self.sendDigit(int(self.digits2[word[1]]), "3")
            self.sendDigit(int(self.digits2[word[0]]), "4")

    def dispStart(self):
        self.receiver_thread = threading.Thread(target=self.writer)
        self.receiver_thread.setDaemon(1)
        self.receiver_thread.start()

    def setClock(self, value):
        self.clock = True
        if len(value) < 4:
            need2add = 4 - len(value)
            value = "0" * need2add + value
        self.toDisp = str(value)

    def setMsg(self, value):
        self.clock = False
        self.toDisp = value

    def writer(self):
        while 1:
            if len(self.toDisp) == 4:
                self.send4Digits(self.toDisp)
            else:
                padString = ' ' * 4 + self.toDisp + ' ' * 4
                for i in range(0, len(padString)-3):
                    for s in range(0, self.scrollSpeed):
                        loc1 = padString[i]
                        loc2 = padString[(i + 1)]
                        loc3 = padString[(i + 2)]
                        loc4 = padString[(i + 3)]
                        visible = loc1 + loc2 + loc3 + loc4
                        self.send4Digits(visible)

    def getIPaddress(self, ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])

    def ipDisplay(self):
        words = ''
        ipValue = self.getIPaddress("eth0")
        print ipValue
        for x in ipValue:
            words += x.replace('.', '-')
        print words
        self.toDisp = words
        while 1:
            self.writer()

    def clearDisp(self):
        self.bus.write_byte_data(self.addr, 0x13, 0xff)

    def testDisplay(self):
        for x in sorted(self.digits2):
            for y in sorted(self.location):
                for s in range(0, self.scrollSpeed):
                    self.sendDigit(int(self.digits2[x]), y)
        for x in sorted(self.digits2):
            word = self.digits2[x], self.digits2[x], self.digits2[x], self.digits2[x]
            for s in range(0, self.scrollSpeed):
                self.send4Digits(word)
        for x in range(0, 255):
            word = x, x, x, x
            for s in range(0, self.scrollSpeed):
                self.send4Digits(word)
        while 1:
            self.writer()

if __name__ == '__main__':
    IPD1 = IPD()
    try:
        if len(sys.argv) > 1:
            allChars = list(IPD1.digits2.keys())
            word = '-'.join(allChars)
            print word
            IPD1.setMsg(word)
            IPD1.testDisplay()
        else:
            IPD1.ipDisplay()

    except KeyboardInterrupt:
        print '\nInterrupt caught'

    finally:
        IPD1.clearDisp()
