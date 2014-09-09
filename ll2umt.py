from math import pi, sin, cos, tan, sqrt, radians, atan2

def ddm2dd(lat, lon):
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

def dd2utm(lat, lon):
    latRad = radians(float(lat)) / 2
    temp1 = cos(latRad)
    print temp1
    
def distHaversine(lat1, lon1, lat2, lon2):
    'Taken from http://www.movable-type.co.uk/scripts/latlong.html'
    latRad1 = radians(float(lat1))
    latRad2 = radians(float(lat2))
    lonRad1 = radians(float(lon1))
    lonRad2 = radians(float(lon2))
    deltaLat = latRad2 - latRad1
    deltaLon = lonRad2 - lonRad1
    vara = sin(deltaLat/2) * sin(deltaLat/2) + cos(latRad1) * cos(latRad2) * sin(deltaLon/2) * sin(deltaLon/2)
    varc = 2 * atan2(sqrt(vara), sqrt(1-vara))
    #Return distance in meters
    print varc * 6371000
    return str(varc * 6371000)

if __name__ == '__main__':
    # Degrees Lat Long  52.2278820, 000.1546780
    # Degrees Minutes   52 13.67292 , 000 09.28068 
    # Degrees Minutes Seconds   52 13'40.3752", 000 09'16.8408"
    # UTM   31U 305680mE 5790199mN  
    # Input is: 5213.67292, 00009.28068
    # Answer is: 52.227882, 0.154678
    ddmVar = ('5213.67292', '00009.28068')
    ddVar2 = ('52.230389', '0.14902')
    print 'DDM Lat: {0} -+- DDM Lon:{1}'.format(ddmVar[0], ddmVar[1])
    ddVar = ddm2dd(ddmVar[0], ddmVar[1])
    print 'DD  Lat: {0} -+- DD  Lon:{1}'.format(ddVar[0], ddVar[1])
    utmVar = dd2utm(ddVar[0], ddVar[1])
    distHav = distHaversine(ddVar[0], ddVar[1], ddVar2[0], ddVar2[1])
    print distHav
