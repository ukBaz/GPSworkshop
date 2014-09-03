
# Python standard libraries
import smbus, time, subprocess, threading, sys

# Raspberry Pi specific libraries
import RPi.GPIO as GPIO


class IPD:

  def __init__(self):
    # Define list for digits 0..9, space, dash and DP in 7-segment (active High)
    self.toDisp = "8888"
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
                   "E" : 0b01111001}
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
    self.speed = 0.005
    # print "**** Digit: {0} -+- Location: {1}".format(digit, pos)
    self.bus.write_byte_data(self.addr, 0x13, ~self.location[pos]) # Set bank 1 Pos to Low 
    self.bus.write_byte_data(self.addr, 0x12, self.digits2[digit])  # Set bank 0 to digit 
    time.sleep(self.speed)
    self.bus.write_byte_data(self.addr, 0x13, 0xff)

  def send4Digits(self, word):
    # print "Send word: " + word
    for x in range(1, 10):
      self.sendDigit(word[3], "1")
      self.sendDigit(word[2], "2")
      self.sendDigit(word[1], "3")
      self.sendDigit(word[0], "4")
      # self.clearDisp()

  def scroll(self, str1, count):
    string = '   ' + str1 + '   '
    for j in range(count):
      for i in range(len(string)-3):
        str2 = string[i:(i+4)]
        # print str2 + "***"
        self.sDisplay2(str2, count)

  def dispStart(self):
    self.receiver_thread = threading.Thread(target=self.writer)
    self.receiver_thread.setDaemon(1)
    self.receiver_thread.start()

  def writer(self):
    while 1:
      if len(self.toDisp) < 4:
        need2add = 4 - len(self.toDisp)
        self.toDisp = " " * need2add + self.toDisp

      self.send4Digits(self.toDisp)
      # time.sleep(0.5)

  def ipDisplay(self):
    arg = 'ip route list'
    waiting = True
    while waiting:
      p = subprocess.Popen(arg, shell = True, stdout = subprocess.PIPE)
      data = p.communicate()
      split_data = data[0].split()
      length = len(split_data)
      # print 'Length', length
    if length > 8:
      waiting = False
    else:
      scroll("0.0.0.0", 2)
      ipaddr = split_data[split_data.index('src')+1]
      print ipaddr
      scroll(ipaddr, 5)
    bus.write_byte_data(addr, 0x13, 0xff) # Set all of bank 1 to High (Off)

  def clearDisp(self):
    self.bus.write_byte_data(self.addr, 0x13, 0xff)

  def testDisplay(self):
    for x in sorted(self.digits2):
      for y in sorted(self.location):
        self.sendDigit(str(x), str(y))
        time.sleep(0.5)
    for x in sorted(self.digits2):
      word = "{0}{1}{2}{3}".format(str(x), str(x), str(x), str(x))
      self.send4Digits(word)

if __name__ == '__main__':
  IPD1 = IPD()
  if len(sys.argv) > 1:
    IPD1.testDisplay()
  else:
    ipDisplay()
  IPD1.clearDisp()
