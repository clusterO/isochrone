rad0 = [0] * 12
rad1 = [60 / 12] * 12

while sum([a - b for a, b in zip(rad0, rad1)]) != 0:
    print(sum([a - b for a, b in zip(rad0, rad1)]))




    """
    bearings = []
    for row in iso:
        bearings.append(get_bearing(geo_coding(origin), row))

    points = zip(bearings, iso)
    sorted_points = sorted(points)
    sorted_iso = [point[1] for point in sorted_points]
    """