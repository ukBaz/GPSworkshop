***GPSworkshop

[x] check box
STEM workshop using H13467 GPS board from CSR

This is python code for interface to run on Raspberry Pi.


References for calculating distances:

From long and lat:
great circle formulae (or Haversine Formula?)
http://andrew.hedges.name/experiments/haversine/
http://www.movable-type.co.uk/scripts/latlong.html

If in UTM:
Using the Pythagorean Theorem to Calculate Distances:
http://support.groundspeak.com/index.php?pg=kb.page&id=211
Distance(meters) = Sqrt((N1-N2)²+(E1-E2)²)

*** Setup of a new RPi
Add the follwing lines to /etc/modules
  i2c-bcm2708
  i2c-dev

Edit /etc/modprobe.d/raspi-blacklist.conf to put comment in front of i2c line
  # blacklist spi and i2c by default (many users don't need them)
  blacklist spi-bcm2708
  # blacklist i2c-bcm2708
  blacklist snd-soc-pcm512x
  blacklist snd-soc-wm8804

install i2c-tools
  sudo apt-get install i2c-tools
  sudo apt-get install python-smbus

Install the utm module for python
  download from pypi
  tar -zxvf utm-0.3.1.tar.gz
  cd utm-0.3.1
  sudo python setup.py install
  
Enable UART GPIO pins
  sudo cp /boot/cmdline.txt /boot/cmdline.txt.bak
  Remove "console=ttyAMA0, 115200"
  cp /etc/inittab /etc/inittab.bak
  On last lines ensure the following has comments in front
  # Spawn a getty on Raspberry Pi serial line
  # T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100
  
wget https://github.com/ukBaz/GPSworkshop/archive/master.zip
