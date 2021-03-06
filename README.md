# GPSworkshop

### STEM workshop using H13467 GPS board from CSR

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

# Setup of a new RPi
Add the follwing lines to /etc/modules
```
  i2c-bcm2708
  i2c-dev
```

Edit /etc/modprobe.d/raspi-blacklist.conf to put comment in front of i2c line
```
  # blacklist spi and i2c by default (many users don't need them)
  blacklist spi-bcm2708
  # blacklist i2c-bcm2708
  blacklist snd-soc-pcm512x
  blacklist snd-soc-wm8804
```
install i2c-tools
```
  sudo apt-get install i2c-tools
  sudo apt-get install python-smbus
```
To enable Pi 2 support new kernels (3.18+) include a configuration change to enable Device Tree support by default. This means the above set-up is no longer true.

To enable i2c is now done using 
```
sudo raspi-config
```
Select "Advanced Options" from the menu, then "I2C", and enable the interface there. You will want the driver module to load automatically so then answer "Yes" to the followup question. raspi-config can also be used to disable and re-enable DT.

###Install the utm module for python
```
  download from pypi
  tar -zxvf utm-0.3.1.tar.gz
  cd utm-0.3.1
  sudo python setup.py install
```

Enable UART GPIO pins
```
  sudo cp /boot/cmdline.txt /boot/cmdline.txt.bak
  Remove "console=ttyAMA0, 115200"
  cp /etc/inittab /etc/inittab.bak
  On last lines ensure the following has comments in front
  # Spawn a getty on Raspberry Pi serial line
  # T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100
```

Install from github the workshop code:
```
wget https://github.com/ukBaz/GPSworkshop/archive/master.zip
```

# Display RPi remotely to another Linux/X11 machine
On remote machine from command line
```
ssh -X pi@xxx.xxx.x.xxx
lxsession
```
# Enable checksums
Doing Checksum of NMEA sentences:
http://doschman.blogspot.co.uk/2013/01/calculating-nmea-sentence-checksums.html
# Additional exercise idea
http://sunrise-sunset.org/api
```
import urllib, json
url = "http://api.sunrise-sunset.org/json?lat=52.1862398&lng=0.172065&date=today"
response = urllib.urlopen(url)
data = json.loads(response.read())
data['results']['sunrise']
```
