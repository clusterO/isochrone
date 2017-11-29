import urllib
import json
import time
import logging
import geocoder
# import osmnx as ox

from math import cos, sin, pi, radians, degrees, asin, atan2
from geopy.geocoders import Nominatim


def geo_coding(address=''):
    geolocator = Nominatim()
    location = geolocator.geocode(address)
    # print(location.raw)
    return [location.latitude, location.longitude]


def get_response(url=''):
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


def calc_isochrone(origin='', duration=60, angles=12):
    rad1 = [duration / 12] * angles # init radius based on 5 km/h speed
    phi1 = [i * (360 / angles) for i in range(angles)]
    data0 = [0] * angles
    rad0 = [0] * angles
    rmin = [0] * angles
    rmax = [1.25 * duration] * angles # rmax based on 75 km/h speed
    iso = [[0, 0]] * angles
    earth_rad = 6371 # Earth Radius km
    geocode_origin = geo_coding(origin)
    lat1 = radians(geocode_origin[0])
    lng1 = radians(geocode_origin[1])

    # isochrone search
    while sum([a - b for a, b in zip(rad0, rad1)]) != 0:
        rad2 = [0] * angles
        for i in range(angles): # Haversines
            bearing = radians(phi1[i]) # ^(northline, OP) clockwise direction
            lat2 = asin(sin(lat1) * cos(rad1[i] / earth_rad) + cos(lat1) * sin(rad1[i] / earth_rad)
                        * cos(bearing))
            lng2 = lng1 + atan2(sin(bearing) * sin(rad1[i] / earth_rad) * cos(lat1),
                                cos(rad1[i] / earth_rad) - sin(lat1) * sin(lat2))
            lat2 = degrees(lat2)
            lng2 = degrees(lng2)
            print([lat2, lng2])
            iso[i] = [lat2, lng2]
            time.sleep(0.1)

        # OSM request URL for distance matrix
        base_url = 'http://router.project-osrm.org/table/v1/driving/'
        destination = ''
        for element in iso:
            destination = '{0};{1}'.format(destination, ','.join(map(str, element)))

        url = urllib.parse.urlparse('{0}{1},{2};{3}?sources=0'
                                    .format(base_url,
                                            geocode_origin[0],
                                            geocode_origin[1],
                                            destination))
        full_url = url.scheme + '://' + url.netloc + url.path + url.params + '?' + url.query

        data = get_response(full_url)

        for i in range(angles):
            if (data[1][i] < duration) & (data0[i] != data[0][i]):
                rad2[i] = (rmax[i] + rad1[i]) / 2
                rmin[i] = rad1[i]
            elif (data[1][i] > duration) & (data0[i] != data[0][i]):
                rad2[i] = (rmin[i] + rad1[i]) / 2
                rmax[i] = rad1[i]
            else:
                rad2[i] = rad1[i]
                data0[i] = data[0][i]
        rad0 = rad1
        rad1 = rad2

    for i in range(angles):
        try:
            iso[i] = data[0][i]
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
    ordred_isochrone = [point[1] for point in ordred_points]

    isochrone = []
    for i in ordred_isochrone:
        alt = geocoder.elevation(i)
        if alt.meters is None or alt.meters > 0:
            isochrone.append(i)

    return isochrone


def generate_map(origin, duration, angles):
    origin_geocode = geo_coding(origin)
    iso = calc_isochrone(origin, duration, angles)
    print(origin_geocode)

    htmltext = """
    <!doctype html>
    <html lang="en">
    <head>
        <link rel="stylesheet" href="https://openlayers.org/en/v4.6.4/css/ol.css" type="text/css">
        <style>
        .map {
            height: 700px;
            width: 100%;
        }
        </style>
        <script src="https://openlayers.org/en/v4.6.4/build/ol.js" type="text/javascript"></script>
        <title>Isochrone</title>
    </head>
    <body>
        <div id="map" class="map"></div>
        <script type="text/javascript">
        var vectorSource = new ol.source.Vector({});
        
        var ring = ["""

    for i in iso:
        if i is not None:
            htmltext += '[{},{}], \n'.format(i[1], i[0])

    htmltext += """
        ];

        var map = new ol.Map({
            target: 'map',
            layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            }),

            new ol.layer.Vector({
                source: vectorSource
            })

        ],
            view: new ol.View({
            center: ol.proj.fromLonLat([1.3970063, 47.8344855]),
            zoom: 8
            })
        });
        
        var polygon = new ol.geom.Polygon([ring]);
        polygon.transform('EPSG:4326', 'EPSG:3857');
        var feature = new ol.Feature(polygon);
        vectorSource.addFeature(feature);
        map.addLayer(vectorLayer);
        
        </script>
    </body>
    </html>
    """

    with open('isochrone_OSMv2.html', 'w') as text:
        text.write(htmltext)


generate_map('vendôme, France', 60, 22)
