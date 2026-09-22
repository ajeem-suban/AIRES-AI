"""AIRES simulation: compares 4 ambulance strategies on random emergencies.

Every emergency gets a random city (roads, traffic, roadblocks, accidents,
signals, ambulances, hospitals). All 4 strategies face the SAME emergency,
so the comparison is fair.

Run:  python aires_sim.py            (200 emergencies, seed 42)
      python aires_sim.py --runs 500 --seed 7
Needs only Python 3.9+. matplotlib is optional (for the chart).
"""
import argparse
import csv
import heapq
import math
import random
import statistics as st

# ---- Simulation settings (change these, then re-run) -----------------------
N = 20                  # city = N x N grid of intersections
EVENTS = 30             # roadblocks + accidents per emergency
SIGNAL_MAX = 0.4        # max minutes lost at one red light
GREEN_FACTOR = 0.2      # green corridor leaves only 20% of the signal delay
DETOUR_PENALTY = 1.0    # minutes lost when a driver finds a blocked road
DIVERT_PENALTY = 3.0    # minutes lost when hospital cannot take the patient
ACCIDENT_SLOWDOWN = 4.0 # an accident makes that road 4x slower
TYPES = ["trauma", "cardiac", "general"]

# ---- The 4 strategies ------------------------------------------------------
# dispatch: "nearest" = straight-line nearest, "live" = fastest by live traffic
# hosp:     "nearest" = nearest hospital, "smart" = fastest hospital that has
#           a free bed AND the right specialty
# map:      "static" = road lengths only, "live" = live traffic + blocks
# reroute:  "block" = re-plan only after hitting a blocked road,
#           "continuous" = re-plan at every intersection
METHODS = {
    "1 Baseline": dict(dispatch="nearest", hosp="nearest", map="static",
                       reroute="block", green=False),
    "2 Live navigation": dict(dispatch="live", hosp="nearest", map="live",
                              reroute="block", green=False),
    "3 AIRES (no green corridor)": dict(dispatch="live", hosp="smart", map="live",
                                        reroute="continuous", green=False),
    "4 AIRES (full)": dict(dispatch="live", hosp="smart", map="live",
                           reroute="continuous", green=True),
}


# ---- City grid helpers -----------------------------------------------------
def neighbors(u):
    r, c = divmod(u, N)
    if r > 0:
        yield u - N
    if r < N - 1:
        yield u + N
    if c > 0:
        yield u - 1
    if c < N - 1:
        yield u + 1


def ekey(u, v):
    """Road between u and v, same key in both directions."""
    return (u, v) if u < v else (v, u)


def manhattan(a, b):
    return abs(a // N - b // N) + abs(a % N - b % N)


class Scenario:
    """One random emergency in one random city."""

    def __init__(self, rng):
        while True:  # resample until the emergency is solvable
            self._build(rng)
            if self._connected() and any(self.suitable(h) for h in self.hosps):
                break

    def _build(self, rng):
        self.base, self.traffic = {}, {}
        for u in range(N * N):
            for v in neighbors(u):
                k = ekey(u, v)
                if k not in self.base:
                    self.base[k] = rng.uniform(0.8, 1.5)      # minutes, empty road
                    self.traffic[k] = rng.uniform(1.0, 2.5)   # normal congestion
        roads = list(self.base)
        self.events = {}  # road -> (start_minute, "block" | "accident")
        for _ in range(EVENTS):
            k = rng.choice(roads)
            start = 0.0 if rng.random() < 0.3 else rng.uniform(0, 25)
            kind = "block" if rng.random() < 0.5 else "accident"
            if k not in self.events or start < self.events[k][0]:
                self.events[k] = (start, kind)
        self.signal = [rng.uniform(0, SIGNAL_MAX) for _ in range(N * N)]
        self.patient = rng.randrange(N * N)
        self.ptype = rng.choice(TYPES)
        self.ambs = rng.sample(range(N * N), 6)
        self.hosps = {
            node: dict(beds=rng.randint(0, 3),
                       spec={"general"} | {t for t in ("trauma", "cardiac")
                                           if rng.random() < 0.5})
            for node in rng.sample(range(N * N), 5)
        }

    def _connected(self):
        """True if every intersection is reachable even with all blocks active."""
        seen, stack = {0}, [0]
        while stack:
            u = stack.pop()
            for v in neighbors(u):
                if v not in seen and not self.blocked(ekey(u, v), math.inf):
                    seen.add(v)
                    stack.append(v)
        return len(seen) == N * N

    def suitable(self, h):
        """Hospital has a free bed and the right specialty for this patient."""
        return self.hosps[h]["beds"] > 0 and self.ptype in self.hosps[h]["spec"]

    def blocked(self, k, t):
        e = self.events.get(k)
        return bool(e) and e[1] == "block" and e[0] <= t

    def live_time(self, k, t):
        """Real minutes to drive road k if entered at minute t."""
        e = self.events.get(k)
        slow = ACCIDENT_SLOWDOWN if e and e[1] == "accident" and e[0] <= t else 1.0
        return self.base[k] * self.traffic[k] * slow


# ---- Routing ---------------------------------------------------------------
def cost_fn(sc, mode, t, known):
    """Road cost as the driver/system believes it. None = road not usable."""
    if mode == "static":  # only knows road length + blocks it has seen itself
        return lambda u, v: (None if ekey(u, v) in known
                             else sc.base[ekey(u, v)])
    return lambda u, v: (None if sc.blocked(ekey(u, v), t)
                         else sc.live_time(ekey(u, v), t))


def dijkstra(src, cost):
    dist, prev, pq = {src: 0.0}, {}, [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, math.inf):
            continue
        for v in neighbors(u):
            c = cost(u, v)
            if c is None:
                continue
            if d + c < dist.get(v, math.inf):
                dist[v], prev[v] = d + c, u
                heapq.heappush(pq, (d + c, v))
    return dist, prev


def route(sc, m, src, dst, t, known):
    _, prev = dijkstra(src, cost_fn(sc, m["map"], t, known))
    path, v = [], dst
    while v != src:
        path.append(v)
        v = prev[v]
    return path[::-1]


def travel(sc, m, src, dst, t):
    """Drive src -> dst starting at minute t. Returns arrival minute."""
    known, plan, u = set(), None, src
    while u != dst:
        if plan is None or m["reroute"] == "continuous":
            plan = route(sc, m, u, dst, t, known)
        v = plan.pop(0)
        k = ekey(u, v)
        if sc.blocked(k, t):              # driver finds the road closed
            known.add(k)
            t += DETOUR_PENALTY
            plan = None
            continue
        t += sc.live_time(k, t)
        if v != dst:                      # red light at the next intersection
            t += sc.signal[v] * (GREEN_FACTOR if m["green"] else 1.0)
        u = v
    return t


# ---- One emergency, one strategy ------------------------------------------
def run_case(sc, m):
    """Returns (minutes to reach patient, minutes to final hospital, wasted trip)."""
    if m["dispatch"] == "nearest":
        amb = min(sc.ambs, key=lambda a: manhattan(a, sc.patient))
    else:
        dist, _ = dijkstra(sc.patient, cost_fn(sc, "live", 0.0, set()))
        amb = min(sc.ambs, key=lambda a: dist[a])
    t_patient = travel(sc, m, amb, sc.patient, 0.0)

    if m["hosp"] == "nearest":
        h = min(sc.hosps, key=lambda x: manhattan(x, sc.patient))
    else:
        dist, _ = dijkstra(sc.patient, cost_fn(sc, "live", t_patient, set()))
        h = min((x for x in sc.hosps if sc.suitable(x)), key=lambda x: dist[x])
    t = travel(sc, m, sc.patient, h, t_patient)

    wasted = 0
    if not sc.suitable(h):  # hospital full or wrong specialty -> divert
        wasted = 1
        h2 = min((x for x in sc.hosps if sc.suitable(x)),
                 key=lambda x: manhattan(x, h))
        t = travel(sc, m, h, h2, t + DIVERT_PENALTY)
    return t_patient, t, wasted


# ---- Report ----------------------------------------------------------------
def report(results, runs):
    base_totals = [r[1] for r in results["1 Baseline"]]
    print(f"\nAIRES simulation: {runs} random emergencies, {N}x{N} city grid")
    print("All times in minutes, from emergency call to patient at a suitable hospital.\n")
    head = (f"{'Strategy':<28}{'To patient':>11}{'Total avg':>11}{'Median':>8}"
            f"{'90th pct':>10}{'Wasted trips':>14}{'Time saved (95% CI)':>26}")
    print(head)
    print("-" * len(head))
    for name, rows in results.items():
        resp = [r[0] for r in rows]
        tot = [r[1] for r in rows]
        wasted = 100 * sum(r[2] for r in rows) / len(rows)
        p90 = sorted(tot)[int(0.9 * (len(tot) - 1))]
        diffs = [b - a for b, a in zip(base_totals, tot)]  # paired: same emergency
        half = 1.96 * st.stdev(diffs) / math.sqrt(len(diffs))
        saved = "-" if name == "1 Baseline" else f"{st.mean(diffs):5.2f} (+/-{half:.2f})"
        print(f"{name:<28}{st.mean(resp):>11.2f}{st.mean(tot):>11.2f}"
              f"{st.median(tot):>8.2f}{p90:>10.2f}{wasted:>13.1f}%{saved:>26}")


def save_outputs(results):
    with open("aires_results.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "strategy", "to_patient_min", "total_min", "wasted_trip"])
        for name, rows in results.items():
            for i, (a, b, c) in enumerate(rows):
                w.writerow([i, name, round(a, 3), round(b, 3), c])
    print("\nSaved per-case data to aires_results.csv")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("Install matplotlib (pip install matplotlib) to also get the chart.")
        return
    names = list(results)
    means = [st.mean(r[1] for r in results[n]) for n in names]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar([n.split(" ", 1)[1] for n in names], means,
                  color=["#9e9e9e", "#64b5f6", "#ffb74d", "#e53935"])
    ax.bar_label(bars, fmt="%.1f min")
    ax.set_ylabel("Average minutes to hospital")
    ax.set_title("Emergency response time by strategy")
    plt.xticks(rotation=12)
    plt.tight_layout()
    plt.savefig("aires_chart.png", dpi=200)
    print("Saved chart to aires_chart.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    results = {name: [] for name in METHODS}
    for _ in range(args.runs):
        sc = Scenario(rng)                 # same emergency for every strategy
        for name, m in METHODS.items():
            results[name].append(run_case(sc, m))
    report(results, args.runs)
    save_outputs(results)


if __name__ == "__main__":
    main()