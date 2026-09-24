// ---- AIRES shared code: backend link, map, demo scenario ----
// API works on any device when the pages are opened from the backend (/dashboards/)
const API = location.protocol.startsWith('http') ? location.origin : 'http://127.0.0.1:8000';
const AMB_ID = 'AMB-01';

// EDIT ME: placeholder demo scenario (backend has no patient data yet)
const SCN = {
  amb: {id: AMB_ID, vehicle: 'TN 45 AB 1234', driver: 'Ravi Kumar', crew: 'Paramedic Priya S.', type: 'ALS'},
  pt: {name: 'Murugan K.', age: 54, sex: 'Male', issue: 'Chest pain, suspected cardiac event', cond: 'Critical', hr: 118, spo2: 91, bp: '150/95'},
  hosp: {name: 'City Care Hospital', dept: 'Cardiac ER', bay: 'Bay 2'}
};

const $ = id => document.getElementById(id);
const hasEv = d => d.road_event && d.road_event !== 'Clear';
const delayOf = d => Math.max(0, d.new_eta - d.clear_eta);   // delay even with AIRES rerouting
const noAiresDelay = d => Math.max(0, d.old_eta - d.clear_eta); // delay if nobody rerouted

// Live route feed with auto-reconnect
function live(cb) {
  (function connect() {
    const s = $('conn'), w = new WebSocket(API.replace('http', 'ws') + '/ws/routing/' + AMB_ID);
    w.onopen = () => { s.textContent = 'LIVE'; s.className = 'pill on'; };
    w.onmessage = e => cb(JSON.parse(e.data));
    w.onclose = () => { s.textContent = 'RECONNECTING'; s.className = 'pill'; setTimeout(connect, 2000); };
  })();
}

const pin = t => L.divIcon({html: '<div class="pin">' + t + '</div>', className: '', iconSize: [34, 34], iconAnchor: [17, 17]});

// Returns a function that redraws the map for each live update
function mkMap() {
  const m = L.map('map', {zoomControl: false});
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19, attribution: '© OpenStreetMap'}).addTo(m);
  const g = L.layerGroup().addTo(m); let fit = '';
  const amb = L.marker([0, 0], {icon: L.divIcon({html: '<div class="amb">✚</div>', className: '', iconSize: [30, 30], iconAnchor: [15, 15]}), zIndexOffset: 1000}); let ambOn = false, anim = 0;
  let lastAmb = '';
  function moveAmb(to, path, secs) {                 // drive along the road shape of the last move
    const key = to.join(',');
    if (!ambOn) { amb.setLatLng(to).addTo(m); ambOn = true; lastAmb = key; return; }
    if (key === lastAmb) return;                     // nothing moved (refresh)
    lastAmb = key; cancelAnimationFrame(anim);
    if (!path || path.length < 2) { amb.setLatLng(to); return; }   // reset / new trip: jump
    const seg = [0];
    for (let i = 1; i < path.length; i++) seg.push(seg[i - 1] + Math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]));
    const tot = seg[seg.length - 1] || 1, t0 = performance.now(), ms = Math.max(300, secs * 900);
    (function step(now) {
      const f = Math.min(1, (now - t0) / ms), dd = f * tot;
      let i = 1; while (i < path.length - 1 && seg[i] < dd) i++;
      const u = Math.min(1, (dd - seg[i - 1]) / ((seg[i] - seg[i - 1]) || 1));
      amb.setLatLng([path[i - 1][0] + (path[i][0] - path[i - 1][0]) * u, path[i - 1][1] + (path[i][1] - path[i - 1][1]) * u]);
      if (f < 1) anim = requestAnimationFrame(step);
    })(t0);
  }
  return d => {
    g.clearLayers();
    const cur = d.current_path || [], rec = d.recommended_path || [];
    if (!rec.length) return;
    if (d.rerouted) L.polyline(cur, {color: '#ff3b30', weight: 5, dashArray: '8 8'}).addTo(g); // old route
    L.polyline(rec, {color: '#2ee59d', weight: 6}).addTo(g);                                   // AIRES route
    moveAmb(d.ambulance && d.ambulance.length ? d.ambulance : rec[0], d.move_path, d.step_seconds || 3);
    L.marker(rec[rec.length - 1], {icon: pin('🏥')}).addTo(g);
    (d.events || []).forEach(e => L.marker([e.lat, e.lon], {icon: pin('⚠️')}).bindTooltip(e.type + ' - ' + e.road).addTo(g));
    const k = rec[rec.length - 1] + '';
    if (k !== fit) { fit = k; m.fitBounds(L.polyline(cur.concat(rec)).getBounds().pad(.3)); }
  };
}

// Patient card (vitals jitter is simulated for the demo)
function patientHTML() {
  const p = SCN.pt;
  return `<div class="k">Patient</div><div class="big">${p.name}, ${p.age} ${p.sex[0]}</div><div>${p.issue}</div>
  <div class="row"><span class="tag ${p.cond.toLowerCase()}">${p.cond}</span><span class="dim">simulated vitals</span></div>
  <div class="vit"><div><b id="hr">${p.hr}</b><i>HEART RATE</i></div><div><b id="spo2">${p.spo2}</b><i>SpO2 %</i></div><div><b>${p.bp}</b><i>BP</i></div></div>`;
}
setInterval(() => {
  if ($('hr')) $('hr').textContent = SCN.pt.hr + Math.round(Math.random() * 6 - 3);
  if ($('spo2')) $('spo2').textContent = SCN.pt.spo2 + Math.round(Math.random() * 2 - 1);
}, 2000);
