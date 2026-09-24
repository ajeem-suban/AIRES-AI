"""Real-road routing for AIRES (central Trichy, from OpenStreetMap).

Drop-in replacement for graph_router.py: same functions, but the roads are real.
Needs trichy_graph.pkl (made by build_trichy_graph.py) in the backend folder.
Routes are found with Dijkstra, so a re-route only happens when it is faster.
"""
import heapq
import math
import pickle
import random
from functools import lru_cache
from pathlib import Path

from app.services.state import active_dispatch

GRAPH_FILE = Path(__file__).resolve().parents[2] / "trichy_graph.pkl"   # backend/trichy_graph.pkl
if not GRAPH_FILE.exists():
    raise FileNotFoundError(f"{GRAPH_FILE} not found. Run build_trichy_graph.py first.")
with open(GRAPH_FILE, "rb") as _f:
    _G = pickle.load(_f)
COORDS, EDGES, BBOX = _G["coords"], _G["edges"], _G["bbox"]   # node -> (lat, lon), edge -> road info
ADJ = {}
for _a, _b in EDGES:
    ADJ.setdefault(_a, []).append(_b)
    ADJ.setdefault(_b, []).append(_a)

# ---- Settings you can change ----
HOSPITAL = None      # (lat, lon) of the real hospital; None = centre of the map
START_POINTS = {"Short": None, "Medium": None, "Long": None}   # (lat, lon), or None = automatic
TRIP_KM = {"Short": 2.0, "Medium": 4.0, "Long": 8.0}            # automatic start: this far by road
SPEED_KMH = 30
STEP_SECONDS = 1.5   # demo speed: the ambulance moves every 1.5 s ...
STEP_KM = 0.2        # ... by about this many km

# ---- Road events ----
SLOWDOWN = {"Traffic Jam": 2.5, "Construction": 3.0}   # road stays open but slower
BLOCKING = {"Accident", "Flood"}                        # road closed
FOOTPRINT_KM = {"Accident": 0.12, "Flood": 0.8, "Traffic Jam": 0.6, "Construction": 0.5}
DETOUR_PENALTY_MIN = 1.0   # minutes lost when a driver finds a closed road

EVENTS = {}        # edge key -> event type (used for routing)
EVENT_LIST = []    # one entry per injected event (used for the map markers)
CURRENT_TRIP = {"name": None}   # None = real dispatch, else Short / Medium / Long
POS = {"node": None}            # where the moving ambulance is (None = at the start)
MOVE = {"path": []}             # road shape of the last move, for smooth animation
STATE = {"v": 0}                # bumps on every change so results can be cached
_CACHE = {"key": None, "data": None}


def _key(a, b):
    return (a, b) if a < b else (b, a)


@lru_cache(maxsize=256)
def _nearest(lat, lon):
    return min(COORDS, key=lambda n: (COORDS[n][0] - lat) ** 2 + (COORDS[n][1] - lon) ** 2)


def _km_from(src):
    """Road distance (km) from src to every junction."""
    dist, pq = {src: 0.0}, [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v in ADJ[u]:
            nd = d + EDGES[_key(u, v)]["km"]
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def _make_trips():
    hosp = _nearest(*(HOSPITAL or ((BBOX[0] + BBOX[2]) / 2, (BBOX[1] + BBOX[3]) / 2)))
    dist = _km_from(hosp)
    trips = {}
    for name, target in TRIP_KM.items():
        p = START_POINTS.get(name)
        start = _nearest(*p) if p else min(dist, key=lambda n: (abs(dist[n] - target), n))
        trips[name] = {"start": start, "end": hosp}
    return trips


TRIPS = _make_trips()


def _minutes(key, live):
    """Minutes to drive one road stretch. None = closed. live=False ignores events."""
    m = EDGES[key]["km"] / SPEED_KMH * 60
    kind = EVENTS.get(key) if live else None
    if kind in BLOCKING:
        return None
    return m * SLOWDOWN.get(kind, 1.0)


def _shortest(src, dst, live, avoid=frozenset()):
    """Dijkstra. Returns (minutes, [nodes]). live=True uses current events."""
    dist, prev, pq = {src: 0.0}, {}, [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == dst:
            break
        if d > dist.get(u, math.inf):
            continue
        for v in ADJ[u]:
            k = _key(u, v)
            m = None if k in avoid else _minutes(k, live)
            if m is not None and d + m < dist.get(v, math.inf):
                dist[v], prev[v] = d + m, u
                heapq.heappush(pq, (d + m, v))
    if dst not in dist:
        return math.inf, []
    path, v = [dst], dst
    while v != src:
        v = prev[v]
        path.append(v)
    return dist[dst], path[::-1]


def _eta_without_rerouting(path, dst):
    """Minutes for a driver who only learns a road is closed when reaching it."""
    t, known, plan, i = 0.0, set(), path, 0
    while plan[i] != dst:
        u, v = plan[i], plan[i + 1]
        k = _key(u, v)
        if EVENTS.get(k) in BLOCKING:          # finds the closure, turns back
            known.add(k)
            t += DETOUR_PENALTY_MIN
            _, plan = _shortest(u, dst, live=False, avoid=known)
            if not plan:
                return math.inf
            i = 0
            continue
        t += _minutes(k, live=True)
        i += 1
    return t


def _path_coords(path):
    """[[lat, lon], ...] following the real road shape."""
    out = []
    for a, b in zip(path, path[1:]):
        g = EDGES[_key(a, b)]["geom"]
        g = g if a < b else g[::-1]
        out.extend(g if not out else g[1:])
    if not out and path:
        out = [COORDS[path[0]]]
    return [list(p) for p in out]


def _path_km(path):
    return round(sum(EDGES[_key(a, b)]["km"] for a, b in zip(path, path[1:])), 1)


def _describe(path):
    roads = []
    for a, b in zip(path, path[1:]):
        name = EDGES[_key(a, b)]["road"]
        if not roads or roads[-1] != name:
            roads.append(name)
    if not roads:
        return "Already at destination"
    return " -> ".join(roads[:4]) + (" -> ..." if len(roads) > 4 else "")


def _base_endpoints():
    name = CURRENT_TRIP["name"]
    amb, dest = active_dispatch["ambulance"], active_dispatch["destination"]
    if not name and amb and dest:              # a real dispatch is active
        return (_nearest(amb["latitude"], amb["longitude"]),
                _nearest(dest["latitude"], dest["longitude"]))
    t = TRIPS[name or "Medium"]
    return t["start"], t["end"]


def _endpoints():
    src, dst = _base_endpoints()
    return (POS["node"] if POS["node"] is not None else src), dst


def _bump():
    STATE["v"] += 1


def _compute_status():
    src, dst = _endpoints()
    _, planned = _shortest(src, dst, live=False)       # route chosen before events
    new_min, best = _shortest(src, dst, live=True)     # best route right now
    base_min = _shortest(src, dst, live=False)[0]
    old_min = _eta_without_rerouting(planned, dst) if planned else math.inf

    hit = [(EVENTS[k], EDGES[k]["road"])
           for k in (_key(a, b) for a, b in zip(planned, planned[1:])) if k in EVENTS]
    if math.isinf(new_min) or math.isinf(old_min):
        old_eta = new_eta = 0
    else:
        old_eta, new_eta = round(old_min), round(new_min)
    if not hit:
        traffic, event, desc = "Light", "Clear", "Road is clear."
    else:
        worst = next((h for h in hit if h[0] in BLOCKING), hit[0])
        traffic = "Heavy" if worst[0] in BLOCKING else "Moderate"
        event, desc = worst[0], f"{worst[0]} detected on {worst[1]}."
    return {
        "current_route": _describe(planned),
        "recommended_route": _describe(best),
        "traffic_status": traffic,
        "road_event": event,
        "event_description": desc,
        "rerouted": best != planned,
        "old_eta": old_eta,
        "new_eta": new_eta,
        "time_saved": max(0, old_eta - new_eta),
        "clear_eta": 0 if math.isinf(base_min) else round(base_min),
        "hospital": "",                       # "" = the dashboards use their own hospital name
        "distance_km": _path_km(best),
        "clear_km": _path_km(planned),
        "ambulance": list(COORDS[src]),
        "arrived": src == dst,
        "step_seconds": STEP_SECONDS,
        "move_path": MOVE["path"],
        "current_path": _path_coords(planned),
        "recommended_path": _path_coords(best),
        "events": [{"type": e["type"], "road": e["road"], "lat": e["mid"][0], "lon": e["mid"][1]}
                   for e in EVENT_LIST],
    }


def route_status():
    """Current plan vs. best route now. Computed once per change, shared by all screens."""
    key = (STATE["v"], repr(active_dispatch))
    if _CACHE["key"] != key:
        _CACHE["data"], _CACHE["key"] = _compute_status(), key
    return _CACHE["data"]


def inject_event(event_type, road_name=None, position="random"):
    """Demo control panel: put an event on the road ahead of the ambulance."""
    if event_type not in SLOWDOWN and event_type not in BLOCKING:
        raise ValueError(f"event_type must be one of {sorted(set(SLOWDOWN) | BLOCKING)}")
    src, dst = _endpoints()
    _, planned = _shortest(src, dst, live=False)
    route = [_key(a, b) for a, b in zip(planned, planned[1:])]
    if road_name:
        route = [k for k in route if EDGES[k]["road"].lower() == road_name.lower()]
    if not route:
        raise ValueError("That road is not on the ambulance's planned route.")

    # Pick where along the remaining route the event starts, then cover FOOTPRINT_KM of road
    total = sum(EDGES[k]["km"] for k in route)
    frac = {"early": 0.15, "middle": 0.5, "late": 0.8}.get(position) or random.uniform(0.1, 0.85)
    run, i = 0.0, 0
    while i < len(route) - 1 and run + EDGES[route[i]]["km"] < frac * total:
        run += EDGES[route[i]]["km"]
        i += 1
    hit, km = [], 0.0
    while i < len(route) and (not hit or km < FOOTPRINT_KM[event_type]):
        hit.append(route[i])
        km += EDGES[route[i]]["km"]
        i += 1
    for k in hit:
        EVENTS[k] = event_type
    mid = hit[len(hit) // 2]
    g = EDGES[mid]["geom"]
    EVENT_LIST.append({"type": event_type, "road": EDGES[mid]["road"], "mid": g[len(g) // 2]})
    _bump()
    return {"event_type": event_type, "road": EDGES[mid]["road"],
            "roads_affected": len(hit), "km_affected": round(km, 2)}


def advance():
    """Move the ambulance about STEP_KM along the best live route.
    Returns False once it has arrived."""
    src, dst = _endpoints()
    if src == dst:
        MOVE["path"] = []
        return False
    _, best = _shortest(src, dst, live=True)
    if len(best) < 2:                          # every road closed: wait in place
        MOVE["path"] = []
        return True
    km, i = 0.0, 0
    while i < len(best) - 1 and km < STEP_KM:
        km += EDGES[_key(best[i], best[i + 1])]["km"]
        i += 1
    MOVE["path"] = _path_coords(best[:i + 1])
    POS["node"] = best[i]
    _bump()
    return best[i] != dst


def arrived():
    src, dst = _endpoints()
    return src == dst


def reset_position():
    POS["node"] = None
    MOVE["path"] = []
    EVENTS.clear()
    EVENT_LIST.clear()
    _bump()
    return {"message": "Ambulance back at start."}


def set_trip(name):
    """Demo control panel: Short / Medium / Long trip, or Auto (real dispatch)."""
    if name == "Auto":
        CURRENT_TRIP["name"] = None
    elif name in TRIPS:
        CURRENT_TRIP["name"] = name
    else:
        raise ValueError("trip must be Auto, " + ", ".join(TRIPS))
    reset_position()                           # old position and events belong to the old trip
    return {"trip": name}


def clear_events():
    EVENTS.clear()
    EVENT_LIST.clear()
    _bump()
    return {"message": "All road events cleared."}