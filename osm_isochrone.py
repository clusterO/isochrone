import networkx as nx
import osmnx as ox

place = 'ciudad real, Spain'
trip_times = [10, 15]
travel_speed = 25

print('Downloading graph ...')
G = ox.graph_from_address(place, dist=10000, dist_type='network', network_type='drive', simplify=True)

print('Processing graph ...')
gdf_nodes = ox.graph_to_gdfs(G, edges=False)
x, y = gdf_nodes['geometry'].unary_union.centroid.xy
center_node = ox.nearest_nodes(G, x[0], y[0])

print('Projecting graph ...')
G = ox.project_graph(G)
meters_per_minute = travel_speed * 1000 / 60
for u, v, k, data in G.edges(data=True, keys=True):
    data['time'] = data['length'] / meters_per_minute

print('Rendering graph ...')
iso_colors = ox.plot.get_colors(n=len(trip_times), cmap='Reds', start=0.3, return_hex=True)
node_colors = {}
for trip_time, color in zip(sorted(trip_times, reverse=True), iso_colors):
    subgraph = nx.ego_graph(G, center_node, radius=trip_time, distance='time')
    for node in subgraph.nodes():
        node_colors[node] = color
        nc = [node_colors[node] if node in node_colors else 'none' for node in G.nodes()]
        ns = [40 if node in node_colors else 0 for node in G.nodes()]

print('Plotting graph ...')
fig, ax = ox.plot_graph(G, figsize=(8, 8), node_color=nc, node_size=ns[0], node_alpha=0.8, node_zorder=2)

print('Exporting graph ...')
# fig, ax = plt.subplots()
# nx.draw_networkx_nodes(G, pos=nx.spring_layout(G), node_size=40, node_color=nc, edge_color='k', alpha=.8)
# nx.draw_networkx_edges(G, pos=nx.spring_layout(G), edge_color='gray', alpha=.1)
# edge_labels=nx.draw_networkx_edge_labels(G,pos=nx.spring_layout(G))
# mplleaflet.show()
# nx.write_shp(subgraph, 'testshapefile')
# nx.write_yaml(G, "test.yaml")
# nx.write_graphml(subgraph, "test.graphml")
"""
isochrone_polys = []
for trip_time in sorted(trip_times, reverse=True):
    subgraph = nx.ego_graph(G, center_node, radius=trip_time, distance='time')
    node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]
    bounding_poly = gpd.GeoSeries(node_points).unary_union.convex_hull
    isochrone_polys.append(bounding_poly)

# optimization : http://kuanbutts.com/2017/12/16/osmnx-isochrones/
# visualization : https://github.com/urschrei/Geopython

fig, ax = ox.plot_graph(G, fig_height=8, show=False, close=False, edge_color='k', edge_alpha=0.2, node_color='none')
for polygon, fc in zip(isochrone_polys, iso_colors):
    patch = PolygonPatch(polygon, fc=fc, ec='none', alpha=0.6, zorder=-1)
    ax.add_patch(patch)
"""
