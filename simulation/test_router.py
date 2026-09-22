"""Test the real AIRES router (graph_router.py) on many random emergencies."""
import random
import sys
from pathlib import Path

import pandas as pd

# The folder that CONTAINS the "app" folder. Change if your backend is elsewhere.
BACKEND_DIR = Path(r"C:\Users\ajeem\AIRES\backend")
sys.path.insert(0, str(BACKEND_DIR))

from app.services import graph_router as gr          # noqa: E402
from app.services.state import active_dispatch       # noqa: E402

RESULTS = Path(__file__).parent / "results"
random.seed(42)                     # same random cases every run
RUNS = 300
EVENT_TYPES = ["Accident", "Flood", "Traffic Jam", "Construction"]

saved_state = {k: active_dispatch.get(k) for k in ("ambulance", "destination")}
nodes = list(range(gr.ROWS * gr.COLS))
rows, attempts = [], 0

while len(rows) < RUNS and attempts < RUNS * 20:
    attempts += 1
    src, dst = random.sample(nodes, 2)
    event = random.choice(EVENT_TYPES)

    # Put the ambulance and the hospital at these two junctions
    (la, lo), (dla, dlo) = gr._coords(src), gr._coords(dst)
    active_dispatch["ambulance"] = {"latitude": la, "longitude": lo}
    active_dispatch["destination"] = {"latitude": dla, "longitude": dlo}

    gr.clear_events()
    _, planned = gr._shortest(src, dst, live=False)
    if len(planned) < 5:            # skip very short trips
        continue
    try:
        gr.inject_event(event)      # real AIRES function: event on the planned route
        aires_min, best = gr._shortest(src, dst, live=True)
        no_reroute_min = gr._eta_without_rerouting(planned, dst)
    except (ValueError, IndexError):
        continue
    if aires_min == float("inf") or no_reroute_min == float("inf"):
        continue

    rows.append({"event": event, "trip_junctions": len(planned),
                "no_reroute_min": no_reroute_min, "aires_min": aires_min,
                "rerouted": best != planned})

gr.clear_events()
active_dispatch.update(saved_state)  # leave the app state as we found it

df = pd.DataFrame(rows)
df["saved_min"] = df.no_reroute_min - df.aires_min
df.to_csv(RESULTS / "router_results.csv", index=False)

summary = df.groupby("event").agg(
    runs=("saved_min", "size"),
    no_reroute=("no_reroute_min", "mean"),
    aires=("aires_min", "mean"),
    saved=("saved_min", "mean"),
    better_pct=("saved_min", lambda s: (s > 0.01).mean() * 100),
).round(2)

print(f"Runs: {len(df)}\n")
print(summary.to_string())
total_less = df.saved_min.sum() / df.no_reroute_min.sum() * 100
print(f"\nOverall: no re-route {df.no_reroute_min.mean():.2f} min, "
    f"AIRES {df.aires_min.mean():.2f} min, {total_less:.0f}% less travel time")
print(f"AIRES worse in: {(df.saved_min < -0.01).mean()*100:.0f}% of cases")