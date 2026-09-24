AIRES frontend (no build step)
1. Unzip so the folder is named "frontend" in your backend project root (next to "app").
2. Add the small backend edits (CORS, /dashboards mount, clear_eta).
3. Run: uvicorn app.main:app --reload --host 0.0.0.0
4. Open http://<laptop-ip>:8000/dashboards/ on each device.
Demo patient/ambulance/hospital data: edit SCN at the top of js/common.js.
Needs internet for map tiles and fonts (mobile hotspot is fine).
