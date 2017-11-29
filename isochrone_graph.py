import urllib
import json
import time
import logging
import matplotlib as mp
import networkx as nx
import osmnx as ox

from math import cos, sin, pi, radians, degrees, asin, atan2
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt


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


def calc_isochrone(origin='', duration=60):
    Graph = nx.MultiDiGraph()
    Graph = ox.core.graph_from_address('vendôme, France', distance=5000, distance_type='network',
                                network_type='drive', simplify=True, retain_all=False,
                                truncate_by_edge=False, return_coords=False, name='iso', timeout=180,
                                memory=None, max_query_area_size=50*1000*50*1000, clean_periphery=True,
                                infrastructure='way["highway"]')

    origine_point = geo_coding(origin)
    destination_point = (47.810742, 1.057548)
    origine_node = ox.get_nearest_node(Graph, origine_point)
    destination_node = ox.get_nearest_node(Graph, destination_point)
    eg = nx.ego_graph(Graph, origine_node, radius=2000, distance='length')
    route = nx.shortest_path(Graph, source=origine_node, target=destination_node, weight='length')
    stats = ox.basic_stats(Graph)
    print(stats)
    # ec = ox.get_edge_colors_by_attr(Graph, attr='length')
    ec = ['r' if data['oneway'] else 'b' for u, v, key, data in Graph.edges(keys=True, data=True)]
    for u, v, key, data in Graph.edges(keys=True, data=True):
        print(data)
        # print('info : ')
        # print(nx.info(Graph))
        print('---------------------------')
    # ox.plot_graph(Graph, edge_color=ec)

    G_labled = nx.convert_node_labels_to_integers(Graph)
    ox.plot_graph_route(Graph, route, fig_height=20, edge_linewidth=0.3, node_size=0, edge_color=ec)


def generate_map(origin, duration):
    origin_geocode = geo_coding(origin)
    iso = calc_isochrone(origin, duration)
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

    with open('isochrone_OSMvG.html', 'w') as text:
        text.write(htmltext)


calc_isochrone('vendôme, France', 60)
