import urllib.parse
import urllib.request
import urllib.error
import json
import time
import logging

from math import cos, sin, pi, radians, degrees, asin, atan2
from geopy.geocoders import Nominatim


def geo_coding(address=''):
    geolocator = Nominatim(user_agent="isochrone")
    location = geolocator.geocode(address)
    return [location.latitude, location.longitude]


def build_url(origin='', destination=None):
    if destination is None:
        destination = []
    base_url = 'http://router.project-osrm.org/table/v1/driving/'

    destination_str = ''
    for element in destination:
        destination_str = '{0};{1}'.format(destination_str, ','.join(map(str, element)))

    url = urllib.parse.urlparse('{0}{1},{2};{3}?sources=0'
                                .format(base_url, origin[0], origin[1], destination_str))

    full_url = url.scheme + '://' + url.netloc + url.path + url.params + '?' + url.query
    return full_url


def parse_response(url=''):
    req = urllib.request.Request(url)
    load = urllib.request.urlopen(req).read()
    data = json.loads(load.decode('utf-8'))

    i = 0
    addresses = [0] * len(data['destinations'])
    for row in data['destinations']:
        addresses[i] = row['location']
        i += 1

    i = 0
    durations = [0] * len(data['destinations'])
    for row in data['durations'][0]:
        durations[i] = row / 60
        i += 1

    return [addresses, durations]


def calc_isochrone(origin='', duration=60, nbr_of_angles=12, tolerance=0.1):
    rad1 = [duration / 12] * nbr_of_angles  # init radius based on 5 km/h speed
    phi1 = [i * (360 / nbr_of_angles) for i in range(nbr_of_angles)]
    data0 = [0] * nbr_of_angles
    rad0 = [0] * nbr_of_angles
    rmin = [0] * nbr_of_angles
    rmax = [1.25 * duration] * nbr_of_angles  # rmax based on 75 km/h speed
    iso = [[0, 0]] * nbr_of_angles
    earth_rad = 6371  # Earth Radius km
    geocode_origin = geo_coding(origin)
    lat1 = radians(geocode_origin[0])
    lng1 = radians(geocode_origin[1])

    # Binary search
    while sum([a - b for a, b in zip(rad0, rad1)]) != 0:
        rad2 = [0] * nbr_of_angles
        for i in range(nbr_of_angles):
            # Haversine
            bearing = radians(phi1[i])  # ^(north-line, OP) clockwise direction
            lat2 = asin(sin(lat1) * cos(rad1[i] / earth_rad) + cos(lat1) * sin(rad1[i] / earth_rad)
                        * cos(bearing))
            lng2 = lng1 + atan2(sin(bearing) * sin(rad1[i] / earth_rad) * cos(lat1),
                                cos(rad1[i] / earth_rad) - sin(lat1) * sin(lat2))
            lat2 = degrees(lat2)
            lng2 = degrees(lng2)
            print([lat2, lng2])
            iso[i] = [lat2, lng2]
            time.sleep(0.1)

        url = build_url(geocode_origin, iso)
        data = parse_response(url)

        for i in range(nbr_of_angles):
            if (data[1][i] < (duration - tolerance)) & (data0[i] != data[0][i]):
                rad2[i] = (rmax[i] + rad1[i]) / 2
                rmin[i] = rad1[i]
            elif (data[1][i] > (duration + tolerance)) & (data0[i] != data[0][i]):
                rad2[i] = (rmin[i] + rad1[i]) / 2
                rmax[i] = rad1[i]
            else:
                rad2[i] = rad1[i]
                data0[i] = data[0][i]
        rad0 = rad1
        rad1 = rad2

    for i in range(nbr_of_angles):
        try:
            iso[i] = geo_coding(data[0][i])
            time.sleep(0.1)
        except Exception as err:
            logging.error('Failed.', exc_info=err)

    print('isoCoor : ')
    print(iso)

    bearings = []
    for row in iso:
        if row is not None:
            bearing = atan2(sin((row[1] - geocode_origin[1]) * pi / 180) * cos(row[0] * pi / 180),
                            cos(geocode_origin[0] * pi / 180) * sin(row[0] * pi / 180) -
                            sin(geocode_origin[0] * pi / 180) * cos(row[0] * pi / 180) *
                            cos((row[1] - geocode_origin[1]) * pi / 180))
            bearing = bearing * 180 / pi
            bearing = (bearing + 360) % 360
            bearings.append(bearing)
        else:
            bearings.append(0.0)

    print('bearing : ')
    print(bearings)

    points = zip(bearings, iso)
    ordred_points = sorted(points)
    ordred_iso = [point[1] for point in ordred_points]
    print('sorted isoCoord : ')
    print(ordred_iso)

    return ordred_iso


def generate_isochrone_map(origin='', duration=60, nbr_of_angles=12, tolerance=0.1):
    origin_geocode = geo_coding(origin)
    iso = calc_isochrone(origin, duration, nbr_of_angles, tolerance)

    htmltext = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no">
    <meta charset="utf-8">
    <title>Isochrone</title>
    <style>
      html, body, #map-canvas {{
        height: 100%;
        margin: 0px;
        padding: 0px
      }}
    </style>

    <script src="https://maps.googleapis.com/maps/api/js?v=3.exp&signed_in=true"></script>

    <script>
    function initialize() {{
      var mapOptions = {{
        zoom: 14,
        center: new google.maps.LatLng({0},{1}),
        mapTypeId: google.maps.MapTypeId.ROADMAP
      }};

      var map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);

      var marker = new google.maps.Marker({{
          position: new google.maps.LatLng({0},{1}),
          map: map
      }});

      var isochrone;

      var isochroneCoords = [
    """.format(origin_geocode[0], origin_geocode[1])

    for i in iso:
        if i is not None:
            htmltext += 'new google.maps.LatLng({},{}), \n'.format(i[0], i[1])

    htmltext += """
      ];

      map.setZoom(map.getZoom() - 5);

      isochrone = new google.maps.Polygon({
        paths: isochroneCoords,
        strokeColor: '#000',
        strokeOpacity: 0.5,
        strokeWeight: 0,
        fillColor: '#000',
        fillOpacity: 0.25
      });

      isochrone.setMap(map);

    }

    google.maps.event.addDomListener(window, 'load', initialize);
    </script>

    </head>
    <body>
        <div id="map-canvas"></div>
    </body>
    </html>
    """

    with open('isochrone_v2_circle.html', 'w') as text:
        text.write(htmltext)


generate_isochrone_map('Anfa Casablanca', 60, 12, 0.1)
