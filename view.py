def generate_isochrone_map(origin='', duration=60, number_of_angles=12, tolerance=0.1):

    origin_geocode = geo_coding(origin)
    iso = get_isochrone(origin, duration, number_of_angles, tolerance)

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

      isochrone = new google.maps.Polygon({
        paths: isochroneCoords,
        strokeColor: '#000',
        strokeOpacity: 0.5,
        strokeWeight: 1,
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

    with open('isochrone_stepper12.html', 'w') as f:
        f.write(htmltext)

    return iso