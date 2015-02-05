__author__ = 'barry'
"""
To switch the GNSS chips uart ouput from the One Socket Protocol (OSP) 115200 to NMEA 4800.
This is required for the H13467 version 3 boards and newer
TODO: Needs to be merged into main H13467.py code
"""
# Raspberry-Pi specific imports
# Provides interface to GPIO pins
import RPi.GPIO as GPIO
import serial
# Import generic Python libraries
import time
import array

on_off_pin = 22
awake = 18
port = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=3.0)
GPIO.setmode(GPIO.BCM)
GPIO.setup(on_off_pin, GPIO.OUT)
GPIO.setup(awake, GPIO.IN)
if not GPIO.input(awake):
    GPIO.output(on_off_pin, GPIO.LOW)
    time.sleep(0.2)
    GPIO.output(on_off_pin, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(on_off_pin, GPIO.LOW)
read_byte = port.read()
while read_byte is not None:
    read_byte = port.read()
    print '{0:02x}'.format(ord(read_byte))
    if ord(read_byte) == 0xA0:
        break

# start_sequence = [0xA0, 0xA2, 0x00, 0x18]
start_sequence = [0xA0, 0xA2]
"""
payload_content = [0x81, 0x02, 0x01, 0x01, 0x00, 0x01, 0x01, 0x01, 0x05, 0x01, 0x01, 0x01, 0x00, 0x01,
0x00, 0x01, 0x00, 0x01, 0x00, 0x01, 0x00, 0x01, 0x01, 0x00, 0x01, 0x25, 0x80]
"""
payload_content = [0x81, 0x02, 0x01, 0x01, 0x00, 0x01, 0x05, 0x01, 0x05, 0x01, 0x01, 0x01, 0x00, 0x01, 0x00, 0x01, 0x00,
                   0x01, 0x00, 0x01, 0x00, 0x01, 0x12, 0xc0]
# end_sequence = [0x01, 0x3A, 0xB0, 0xB3]
end_sequence = [0xb0, 0xb3]

# to_send = array.array('B', start_sequence).tostring()
content_checksum = sum(payload_content) & 0x7fff
checksum2bytes = [content_checksum >> 8, content_checksum & 0xff]
length2bytes = [len(payload_content) >> 8, len(payload_content) & 0xff]
msg = start_sequence + length2bytes + payload_content + checksum2bytes + end_sequence
print array.array('B', msg).tostring()
port.write(array.array('B', msg).tostring())

pack = lambda x: chr(x >> 8) + chr(x & 0xff)
start = "\xa0\xa2"
end = "\xb0\xb3"
payload = "\x81\x02\x01\x01\x00\x01\x05\x01\x05\x01\x00\x01\x00\x01\x00\x01\x00\x01\x00\x01\x00\x01\x12\xc0"
checksum = sum(map(ord, list(payload))) & 0x7fff
length = len(payload)
message = start + pack(length) + payload + pack(checksum) + end
# port.write(message)

port.close()