"""Real road-graph routing for AIRES.

Replaces the old random / hard-coded routing demo. The city is a small grid of
junctions. Every road has a real length (km), a normal traffic level, and can
get an event (traffic jam, construction, accident, flood). Routes are found with
Dijkstra's shortest-path algorithm, so a re-route only happens when it is
actually faster.
"""
import heapq
import math

from app.services.state import active_dispatch

# ---- Demo road network: 5 x 6 grid of junctions around the hospital area ----
LAT0, LON0 = 10.775, 78.694
ROWS, COLS = 5, 6
DLAT, DLON = 0.0075, 0.0052              # spacing between junctions (degrees)
ROW_NAMES = {0: "Bypass Road", 2: "Main Road", 4: "Ring Road"}  # other rows: Link Road
NORMAL_TRAFFIC = {"Main Road": 1.3, "Bypass Road": 1.0, "Ring Road": 1.0}  # default 1.1
SPEED_KMH = 40

# ---- Road events ----
SLOWDOWN = {"Traffic Jam": 2.5, "Construction": 3.0}   # road stays open but slower
BLOCKING = {"Accident", "Flood"}                        # road closed
DETOUR_PENALTY_MIN = 1.0   # minutes lost when a driver finds a closed road

# Used when no emergency has been dispatched yet (demo defaults)
DEFAULT_START = (10.7900, 78.7040)
DEFAULT_END = (10.8015, 78.7152)


def _node(r, c):
    return r * COLS + c


def _coords(n):
    r, c = divmod(n, COLS)
    return LAT0 + r * DLAT, LON0 + c * DLON


def _km(a, b):
    """Great-circle distance in km between two junctions."""
    (la1, lo1), (la2, lo2) = _coords(a), _coords(b)
    p1, p2 = math.radians(la1), math.radians(la2)
    h = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lo2 - lo1) / 2) ** 2)
    return 2 * 6371 * math.asin(math.sqrt(h))


def _key(a, b):
    return (a, b) if a < b else (b, a)


def _build():
    edges, adj = {}, {n: [] for n in range(ROWS * COLS)}
    for r in range(ROWS):
        for c in range(COLS):
            n = _node(r, c)
            links = []
            if c < COLS - 1:
                links.append((_node(r, c + 1), ROW_NAMES.get(r, "Link Road")))
            if r < ROWS - 1:
                links.append((_node(r + 1, c), f"Cross Road {c + 1}"))
            for m, road in links:
                edges[_key(n, m)] = {"road": road, "km": _km(n, m)}
                adj[n].append(m)
                adj[m].append(n)
    return edges, adj


EDGES, ADJ = _build()
EVENTS = {}  # edge key -> event type (shared by all requests; cleared via API)


def _nearest(lat, lon):
    return min(range(ROWS * COLS),
               key=lambda n: (_coords(n)[0] - lat) ** 2 + (_coords(n)[1] - lon) ** 2)


def _minutes(key, live):
    """Minutes to drive one road. None = closed. live=False ignores events."""
    e = EDGES[key]
    m = e["km"] / SPEED_KMH * 60 * NORMAL_TRAFFIC.get(e["road"], 1.1)
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
            if not plan:                       # no way through: cannot arrive
                return math.inf
            i = 0
            continue
        t += _minutes(k, live=True)
        i += 1
    return t


def _describe(path):
    roads = []
    for a, b in zip(path, path[1:]):
        name = EDGES[_key(a, b)]["road"]
        if not roads or roads[-1] != name:
            roads.append(name)
    return " -> ".join(roads) if roads else "Already at destination"


def _endpoints():
    amb, dest = active_dispatch["ambulance"], active_dispatch["destination"]
    s = (amb["latitude"], amb["longitude"]) if amb else DEFAULT_START
    d = (dest["latitude"], dest["longitude"]) if dest else DEFAULT_END
    return _nearest(*s), _nearest(*d)


def route_status():
    """Current plan vs. best route now. Fields match RouteStatusResponse."""
    src, dst = _endpoints()
    _, planned = _shortest(src, dst, live=False)       # route chosen before events
    new_min, best = _shortest(src, dst, live=True)     # best route right now
    old_min = _eta_without_rerouting(planned, dst)     # if nobody re-routed

    hit = [EVENTS[_key(a, b)] for a, b in zip(planned, planned[1:])
        if _key(a, b) in EVENTS]
    hit_roads = [EDGES[_key(a, b)]["road"] for a, b in zip(planned, planned[1:])
        if _key(a, b) in EVENTS]
    if not hit:
        traffic, event, desc = "Light", "Clear", "Road is clear."
    else:
        worst = next((h for h in hit if h in BLOCKING), hit[0])
        traffic = "Heavy" if worst in BLOCKING else "Moderate"
        event = worst
        desc = f"{worst} detected on {hit_roads[hit.index(worst)]}."
        if math.isinf(new_min) or math.isinf(old_min):
            old_eta = new_eta = 0            # no route found: avoid crash on round(inf)
        else:
            old_eta, new_eta = round(old_min), round(new_min)
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
    }


def inject_event(event_type, road_name=None):
    """Demo control panel: put an event on the ambulance's planned route."""
    if event_type not in SLOWDOWN and event_type not in BLOCKING:
        raise ValueError(f"event_type must be one of {sorted(set(SLOWDOWN) | BLOCKING)}")
    src, dst = _endpoints()
    _, planned = _shortest(src, dst, live=False)
    on_route = [_key(a, b) for a, b in zip(planned, planned[1:])]
    if road_name:
        on_route = [k for k in on_route if EDGES[k]["road"].lower() == road_name.lower()]
    if not on_route:
        raise ValueError("That road is not on the ambulance's planned route.")
    key = on_route[len(on_route) // 2]
    EVENTS[key] = event_type
    return {"event_type": event_type, "road": EDGES[key]["road"]}


def clear_events():
    EVENTS.clear()
    return {"message": "All road events cleared."}