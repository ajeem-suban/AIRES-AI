import osmnx as ox
import networkx as nx

ox.settings.use_cache = True

# Centre of the test area (Trichy). Change this to your own area later.
CENTER = (10.8050, 78.6856)
DIST = 5000  # metres around the centre

# 1. Road network (drivable roads only)
G = ox.graph.graph_from_point(CENTER, dist=DIST, network_type="drive")
G = ox.routing.add_edge_speeds(G)
G = ox.routing.add_edge_travel_times(G)
print("Roads loaded:", len(G.nodes), "junctions,", len(G.edges), "road segments")

# 2. Real hospitals from OpenStreetMap
hospitals = ox.features.features_from_point(CENTER, tags={"amenity": "hospital"}, dist=DIST)
points = hospitals.geometry.representative_point()
hospitals["lat"] = points.y
hospitals["lon"] = points.x
hospitals["name"] = hospitals.get("name", "unnamed")
print("Hospitals found:", len(hospitals))

# 3. Quick route test: from the map centre to the first hospital
start = ox.distance.nearest_nodes(G, CENTER[1], CENTER[0])
first = hospitals.iloc[0]
end = ox.distance.nearest_nodes(G, first["lon"], first["lat"])
route = nx.shortest_path(G, start, end, weight="travel_time")
seconds = nx.shortest_path_length(G, start, end, weight="travel_time")
print(f"Route to {first['name']}: {len(route)} junctions, about {seconds/60:.1f} minutes")

# 4. Save the results
ox.io.save_graphml(G, filepath="simulation/results/trichy.graphml")
hospitals[["name", "lat", "lon"]].to_csv("simulation/results/hospitals.csv", index=False)
print("Saved map and hospitals.")