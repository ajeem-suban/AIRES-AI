"""Cut a small Trichy road graph out of a big OSM file (e.g. tamil_nadu.pbf).

Run once:   python build_trichy_graph.py path/to/tamil_nadu.pbf
Output:     trichy_graph.pkl  (small cache the AIRES router loads in a second)

Roads are treated as two-way (one-way rules ignored) to keep the demo simple.
"""
import math
import pickle
import sys
from collections import defaultdict, deque

import osmium

# South, West, North, East. Central Trichy. Edit if you want a bigger/smaller area.
BBOX = (10.76, 78.64, 10.87, 78.74)
OUT = "trichy_graph.pkl"

DRIVABLE = {
    "motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential",
    "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link",
}


def inside(lat, lon):
    s, w, n, e = BBOX
    return s <= lat <= n and w <= lon <= e


def haversine_km(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    h = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2)
    return 2 * 6371 * math.asin(math.sqrt(h))


class Roads(osmium.SimpleHandler):
    """Collects drivable road pieces that lie inside BBOX."""

    def __init__(self):
        super().__init__()
        self.runs = []   # (road_name, [(node_id, lat, lon), ...])

    def way(self, w):
        hw = w.tags.get("highway")
        if hw not in DRIVABLE:                     # skip buildings, footpaths, etc.
            return
        name = (w.tags.get("name:en") or w.tags.get("name") or w.tags.get("ref")
                or hw.replace("_", " ").title() + " road")
        run = []
        try:
            for n in w.nodes:
                lat, lon = n.lat, n.lon            # raises if the location is unknown
                if inside(lat, lon):
                    run.append((n.ref, lat, lon))
                else:                              # left the area: close this piece
                    if len(run) > 1:
                        self.runs.append((name, run))
                    run = []
        except osmium.InvalidLocationError:
            return
        if len(run) > 1:
            self.runs.append((name, run))


def build(path):
    h = Roads()
    print("Reading", path, "(a whole-state file can take a few minutes)...")
    h.apply_file(path, locations=True, idx="sparse_mem_array")
    print("Road pieces inside the area:", len(h.runs))

    # A junction = a node used by 2+ road pieces, or the end of a piece.
    use = defaultdict(int)
    for _, run in h.runs:
        for i, (nid, _, _) in enumerate(run):
            use[nid] += 2 if i in (0, len(run) - 1) else 1
    junction = {nid for nid, c in use.items() if c >= 2}

    # Split each piece at junctions -> one edge per stretch of road
    edges = {}
    for name, run in h.runs:
        start = 0
        for i in range(1, len(run)):
            if run[i][0] not in junction:
                continue
            seg = run[start:i + 1]
            start = i
            u, v = seg[0][0], seg[-1][0]
            if u == v:
                continue
            geom = [(lat, lon) for _, lat, lon in seg]
            km = sum(haversine_km(geom[j], geom[j + 1]) for j in range(len(geom) - 1))
            key = (u, v) if u < v else (v, u)
            if u > v:
                geom.reverse()                    # store geometry from the smaller id to the larger
            if key not in edges or km < edges[key]["km"]:
                edges[key] = {"road": name, "km": km, "geom": geom}

    # Keep only the biggest connected piece (no isolated road fragments)
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    seen, best = set(), set()
    for s in adj:
        if s in seen:
            continue
        comp, q = {s}, deque([s])
        seen.add(s)
        while q:
            for v in adj[q.popleft()]:
                if v not in seen:
                    seen.add(v)
                    comp.add(v)
                    q.append(v)
        if len(comp) > len(best):
            best = comp
    edges = {k: e for k, e in edges.items() if k[0] in best}

    coords = {}
    for (a, b), e in edges.items():
        coords[a], coords[b] = e["geom"][0], e["geom"][-1]

    with open(OUT, "wb") as f:
        pickle.dump({"coords": coords, "edges": edges, "bbox": BBOX}, f)
    total = sum(e["km"] for e in edges.values())
    print(f"Saved {OUT}: {len(coords)} junctions, {len(edges)} road stretches, {total:.0f} km of road")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python build_trichy_graph.py path/to/tamil_nadu.pbf")
    build(sys.argv[1])