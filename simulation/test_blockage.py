import random
import statistics
from pathlib import Path

# Always find the results folder, no matter where you run the script from
RESULTS = Path(__file__).parent / "results"
import networkx as nx
import osmnx as ox
import pandas as pd

random.seed(42)  # same random cases every run, so results are repeatable
RUNS = 200

G = ox.io.load_graphml(RESULTS / "trichy.graphml")
hosp = pd.read_csv(RESULTS / "hospitals.csv").dropna(subset=["name"])
hosp["node"] = ox.distance.nearest_nodes(G, hosp["lon"].values, hosp["lat"].values)


def path_time(path):
    """Total travel time (seconds) along a list of junctions."""
    return sum(min(e["travel_time"] for e in G[u][v].values())
    for u, v in zip(path[:-1], path[1:]))


def nearest_hospital(node):
    """Baseline choice: nearest hospital by straight-line distance."""
    lat, lon = G.nodes[node]["y"], G.nodes[node]["x"]
    d = [ox.distance.great_circle(lat, lon, r.lat, r.lon) for r in hosp.itertuples()]
    return int(hosp.iloc[d.index(min(d))]["node"])


rows = []
nodes = list(G.nodes)
while len(rows) < RUNS:
    start = random.choice(nodes)
    end = nearest_hospital(start)
    try:
        plan = nx.shortest_path(G, start, end, weight="travel_time")
    except nx.NetworkXNoPath:
        continue
    if len(plan) < 8:  # skip very short trips
        continue

    # Block the road in the middle of the planned route
    i = len(plan) // 2
    H = G.copy()
    H.remove_edges_from([(plan[i], plan[i + 1], k) for k in list(H[plan[i]][plan[i + 1]])])

    try:
        # Baseline: driver only finds out when reaching the blocked road
        baseline = path_time(plan[: i + 1]) + nx.shortest_path_length(H, plan[i], end, weight="travel_time")
        # AIRES: told about the block when 1/4 of the way, re-routes immediately
        j = len(plan) // 4
        aires = path_time(plan[: j + 1]) + nx.shortest_path_length(H, plan[j], end, weight="travel_time")
    except nx.NetworkXNoPath:
        continue

    rows.append({"no_block_s": path_time(plan), "baseline_s": baseline, "aires_s": aires})

df = pd.DataFrame(rows)
df["saved_s"] = df["baseline_s"] - df["aires_s"]
df.to_csv(RESULTS / "blockage_results.csv", index=False)

print(f"Runs: {len(df)}")
print(f"Average, no blockage : {df.no_block_s.mean()/60:.1f} min")
print(f"Average, baseline    : {df.baseline_s.mean()/60:.1f} min")
print(f"Average, AIRES       : {df.aires_s.mean()/60:.1f} min")
print(f"Average time saved   : {df.saved_s.mean():.0f} sec")
print(f"AIRES better in      : {(df.saved_s > 1).mean()*100:.0f}% of cases")
print(f"Same (within 1 sec)  : {(df.saved_s.abs() <= 1).mean()*100:.0f}% of cases")
print(f"AIRES worse in       : {(df.saved_s < -1).mean()*100:.0f}% of cases")