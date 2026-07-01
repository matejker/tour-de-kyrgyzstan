/* Tour de Kyrgyzstan — bikepacking route explorer */
(() => {
  "use strict";

  const R = 6371000;
  const haversine = (a, b) => {
    const toR = Math.PI / 180;
    const dLat = (b[0] - a[0]) * toR, dLon = (b[1] - a[1]) * toR;
    const la1 = a[0] * toR, la2 = b[0] * toR;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(la1) * Math.cos(la2) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  };

  // darken/lighten a hex colour by pct (-1..1)
  const shade = (hex, pct) => {
    const n = parseInt(hex.slice(1), 16);
    let r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
    const f = pct < 0 ? 0 : 255, p = Math.abs(pct);
    r = Math.round((f - r) * p + r);
    g = Math.round((f - g) * p + g);
    b = Math.round((f - b) * p + b);
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
  };

  const OSM_ATTR = "© OpenStreetMap contributors";
  const tileLayers = () => ({
    // default — the classic brown/orange topo (kept per request)
    "Terrain": L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
      maxZoom: 17, attribution: "© OpenTopoMap (CC-BY-SA) · " + OSM_ATTR
    }),
    // clean, high-contrast light basemap — easiest to read route lines on
    "Light": L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
      maxZoom: 20, subdomains: "abcd", attribution: "© CARTO · " + OSM_ATTR
    }),
    // cycling-focused: shows tracks, surfaces and gradients — great for bikepacking
    "Cycle": L.tileLayer("https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png", {
      maxZoom: 18, subdomains: "abc", attribution: "CyclOSM · " + OSM_ATTR
    }),
    // Esri topo — relief + labels, lighter than OpenTopoMap
    "Topo (Esri)": L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 19, attribution: "Tiles © Esri — Esri, DeLorme, NAVTEQ, and contributors"
    }),
    // satellite imagery — for scouting terrain, rivers and jailoos
    "Satellite": L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 19, attribution: "Imagery © Esri, Maxar, Earthstar Geographics"
    }),
    // plain OpenStreetMap
    "Streets": L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, attribution: OSM_ATTR
    })
  });

  const $ = (s) => document.querySelector(s);
  const fmtKm = (v) => Math.round(v).toLocaleString() + " km";
  const fmtM = (v) => Math.round(v).toLocaleString() + " m";

  // a toggleable layer of resupply towns/villages (blue dots) + train stops
  function buildPoiLayer(places, trains) {
    const g = L.layerGroup();
    (places || []).forEach((s) => {
      const big = s.kind && s.kind !== "village";
      L.circleMarker([s.lat, s.lon], {
        radius: big ? 5 : 2.5, color: "#fff", weight: big ? 1.5 : 1,
        fillColor: "#2f7fb5", fillOpacity: big ? 1 : .85
      }).bindTooltip(s.name).addTo(g);
    });
    (trains || []).forEach((t) => L.marker([t.lat, t.lon], {
      icon: L.divIcon({ className: "", iconSize: [20, 20], iconAnchor: [10, 10], html: '<div class="train-marker">▤</div>' })
    }).bindPopup(`<b>${t.name}</b><br>${t.note}`).addTo(g));
    return g;
  }

  // a toggleable layer of (approximate) border-permit zones, drawn as polygons
  function buildPermitLayer(zones) {
    const g = L.layerGroup();
    (zones || []).forEach((z) => {
      (z.polygons || []).forEach((ring) => {
        L.polygon(ring, {
          color: "#b3261e", weight: 1.5, fillColor: "#b3261e", fillOpacity: .14, dashArray: "5 4"
        }).bindTooltip(`${z.name} — border permit required`, { sticky: true })
          .bindPopup(`<b>${z.name}</b><br>Border permit required · ${z.border} border<br><span style="color:#666">${z.region} region</span>`)
          .addTo(g);
      });
    });
    return g;
  }

  // pill toggles for map overlays: defs = [[key, label, color, on, layerGroup], ...]
  function buildLayerToggles(bar, map, defs) {
    bar.innerHTML = "";
    defs.forEach(([, label, col, on, layer]) => {
      if (on) layer.addTo(map);
      const el = document.createElement("label");
      el.className = "mt-toggle" + (on ? "" : " off");
      el.innerHTML = `<input type="checkbox" ${on ? "checked" : ""}><span class="dot" style="background:${col}"></span>${label}`;
      el.querySelector("input").addEventListener("change", (e) => {
        el.classList.toggle("off", !e.target.checked);
        if (e.target.checked) layer.addTo(map); else map.removeLayer(layer);
      });
      bar.appendChild(el);
    });
  }

  // show exactly one top-level view, hide the rest
  function showView(id) {
    ["landing", "detail", "master", "srmr", "planner"].forEach((v) => {
      const el = $("#" + v); if (el) el.hidden = (v !== id);
    });
  }

  let ROUTES = [];
  let routeMap = null;
  let dayLayers = [];
  let hoverDot = null;
  let elevChart = null;
  let elevPts = [];
  let currentGeo = null;

  /* ----------------------------- landing ----------------------------- */
  function mergeBounds(list) {
    let s = 90, w = 180, n = -90, e = -180;
    list.forEach((b) => {
      s = Math.min(s, b[0][0]); w = Math.min(w, b[0][1]);
      n = Math.max(n, b[1][0]); e = Math.max(e, b[1][1]);
    });
    return [[s, w], [n, e]];
  }

  function buildCards() {
    const grid = $("#routeGrid");
    const groups = [
      ["AI generated", "Routes designed and routed from open data.", ROUTES.filter((r) => !r.custom)],
      ["User generated", "Routes imported from GPX files.", ROUTES.filter((r) => r.custom)]
    ];
    groups.forEach(([title, sub, list]) => {
      if (!list.length) return;
      const h = document.createElement("div");
      h.className = "grid-heading";
      h.innerHTML = `<h3>${title}</h3><p>${sub}</p>`;
      grid.appendChild(h);
      list.forEach((r) => {
        const card = document.createElement("article");
        card.className = "route-card";
        const badge = r.custom
          ? `<span class="rc-tag remote">＋ Added</span>`
          : r.expert
            ? `<span class="rc-tag remote">◆ Expert line</span>`
            : r.remote
              ? `<span class="rc-tag remote">▲ High passes</span>`
              : `<span class="rc-tag">Camps ≤ 2000 m</span>`;
        card.innerHTML = `
          <div class="rc-map" id="mini-${r.id}">${badge}<span class="rc-tag start">Start · ${r.start}</span></div>
          <div class="rc-body">
            <div>
              <div class="rc-title">${r.name}</div>
              <div class="rc-sub">${r.subtitle}</div>
            </div>
            <div class="rc-stats">
              <div class="rc-stat"><strong>${fmtKm(r.total_distance_km)}</strong>${r.num_days} days</div>
              <div class="rc-stat"><strong>${fmtM(r.total_ascent_m)}</strong>climbing</div>
              <div class="rc-stat"><strong>${fmtM(r.max_ele)}</strong>highest point</div>
            </div>
            <div class="rc-go">View route &amp; elevation →</div>
          </div>`;
        card.addEventListener("click", () => openRoute(r.id));
        grid.appendChild(card);
      });
    });
    // mini maps (static)
    ROUTES.forEach((r) => {
      const m = L.map("mini-" + r.id, {
        zoomControl: false, attributionControl: false, dragging: false,
        scrollWheelZoom: false, doubleClickZoom: false, boxZoom: false,
        keyboard: false, tap: false, touchZoom: false
      });
      L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        { maxZoom: 16, subdomains: "abcd" }).addTo(m);
      L.polyline(r.overview, { color: r.color, weight: 3.5 }).addTo(m);
      m.fitBounds(r.bounds, { padding: [12, 12] });
    });
  }

  /* ------------------------------ detail ------------------------------ */
  async function openRoute(id) {
    const r = ROUTES.find((x) => x.id === id);
    if (!r) return;
    location.hash = "r/" + id;
    const geo = await fetch(r.geo).then((res) => res.json());
    currentGeo = geo;
    showDetailView(r, geo);
    window.scrollTo(0, 0);
  }

  function dayPalette(r, n) {
    const a = r.color, b = shade(r.color, -0.30);
    return Array.from({ length: n }, (_, i) => (i % 2 === 0 ? a : b));
  }

  function showDetailView(r, geo) {
    showView("detail");

    $("#dEyebrow").textContent = `Start · ${r.start}  ·  ${r.num_days} days` +
      (r.custom ? "  ·  Imported from GPX"
        : r.remote ? "  ·  High-pass route (some camps above 2500 m)"
          : "  ·  Camps below ~2000 m");
    $("#dTitle").textContent = r.name;
    $("#dBlurb").textContent = r.blurb;
    $("#dGpx").href = r.gpx;
    $("#dGpx").setAttribute("download", r.id + ".gpx");

    $("#dStats").innerHTML = [
      ["Distance", fmtKm(r.total_distance_km)],
      ["Climbing", fmtM(r.total_ascent_m)],
      ["Highest point", fmtM(r.max_ele)],
      ["Highest camp", fmtM(r.max_camp_ele)],
      ["Avg / day", fmtKm(r.total_distance_km / r.num_days)]
    ].map(([k, v]) => `<div class="dstat"><span>${k}</span><strong>${v}</strong></div>`).join("");

    const colors = dayPalette(r, geo.days.length);

    // ---- map ----
    if (routeMap) { routeMap.remove(); routeMap = null; }
    routeMap = L.map("routeMap", { scrollWheelZoom: true });
    const layers = tileLayers();
    layers["Cycle"].addTo(routeMap);
    L.control.layers(layers, null, { position: "topright" }).addTo(routeMap);

    dayLayers = [];
    const seenShop = new Set();
    geo.days.forEach((d, i) => {
      const latlngs = d.coords.map((c) => [c[0], c[1]]);
      const line = L.polyline(latlngs, { color: colors[i], weight: 4, opacity: .9 })
        .addTo(routeMap)
        .bindTooltip(`Day ${d.day}: ${d.name}`, { sticky: true })
        .on("click", () => selectDay(i));
      dayLayers.push(line);
    });
    // resupply + camp markers from metadata
    r.days.forEach((d, i) => {
      (d.resupply || []).forEach((s) => {
        const key = s.lat.toFixed(3) + "," + s.lon.toFixed(3);
        if (seenShop.has(key)) return;
        seenShop.add(key);
        L.circleMarker([s.lat, s.lon], {
          radius: 5, color: "#fff", weight: 2, fillColor: "#2f7fb5", fillOpacity: 1
        }).addTo(routeMap).bindPopup(`<b>${s.name}</b><br>Resupply`);
      });
    });
    geo.days.forEach((d, i) => {
      const end = d.coords[d.coords.length - 1];
      const dd = r.days[i];
      L.marker([end[0], end[1]], {
        icon: L.divIcon({ className: "", html: '<div class="camp-marker"></div>', iconSize: [16, 16], iconAnchor: [8, 16] })
      }).addTo(routeMap).bindPopup(`<b>Night ${d.day} · ${dd.camp}</b><br>Camp ~${fmtM(dd.end_ele)}`);
    });
    routeMap.fitBounds(geo.bounds, { padding: [20, 20] });
    setTimeout(() => routeMap.invalidateSize(), 60);

    hoverDot = L.circleMarker([geo.days[0].coords[0][0], geo.days[0].coords[0][1]], {
      radius: 6, color: "#fff", weight: 2, fillColor: r.color, fillOpacity: 1, interactive: false
    });

    buildElevation(geo, colors);
    buildDayList(r, geo, colors);
    selectedDay = -1;
  }

  /* --------------------------- elevation chart --------------------------- */
  function buildElevation(geo, colors) {
    elevPts = [];
    let km = 0;
    geo.days.forEach((d, di) => {
      d.coords.forEach((c, idx) => {
        if (di === 0 && idx === 0) { /* start */ }
        else {
          const prev = elevPts[elevPts.length - 1];
          km += haversine([prev.lat, prev.lon], [c[0], c[1]]) / 1000;
        }
        elevPts.push({ x: km, y: c[2], lat: c[0], lon: c[1], day: di });
      });
    });

    const ctx = $("#elevChart").getContext("2d");
    if (elevChart) elevChart.destroy();

    const crosshair = {
      id: "crosshair",
      afterDraw(chart) {
        const idx = chart.$hoverIndex;
        if (idx == null) return;
        const x = chart.scales.x.getPixelForValue(elevPts[idx].x);
        const { top, bottom } = chart.chartArea;
        const c = chart.ctx;
        c.save(); c.beginPath(); c.moveTo(x, top); c.lineTo(x, bottom);
        c.lineWidth = 1; c.strokeStyle = "rgba(28,33,40,.35)"; c.stroke(); c.restore();
      }
    };

    elevChart = new Chart(ctx, {
      type: "line",
      data: {
        datasets: [{
          data: elevPts.map((p) => ({ x: p.x, y: p.y })),
          borderWidth: 2,
          pointRadius: 0,
          fill: true,
          backgroundColor: "rgba(47,127,181,.10)",
          tension: 0,
          segment: { borderColor: (c) => colors[elevPts[c.p1DataIndex].day] }
        }]
      },
      options: {
        animation: false,
        parsing: false,
        maintainAspectRatio: false,
        interaction: { mode: "nearest", axis: "x", intersect: false },
        scales: {
          x: { type: "linear", title: { display: true, text: "Distance (km)" },
               ticks: { maxTicksLimit: 8 }, grid: { color: "rgba(0,0,0,.04)" } },
          y: { title: { display: true, text: "Elevation (m)" },
               grid: { color: "rgba(0,0,0,.05)" } }
        },
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        onHover: (e, active, chart) => {
          if (!active.length) return;
          setHover(active[0].index);
        }
      },
      plugins: [crosshair]
    });

    $("#elevChart").onmouseleave = () => clearHover();
  }

  function setHover(idx) {
    const p = elevPts[idx];
    if (!p) return;
    elevChart.$hoverIndex = idx;
    elevChart.draw();
    if (hoverDot) {
      hoverDot.setLatLng([p.lat, p.lon]);
      if (!routeMap.hasLayer(hoverDot)) hoverDot.addTo(routeMap);
    }
    $("#elevHover").textContent = `${p.x.toFixed(1)} km · ${Math.round(p.y)} m · Day ${p.day + 1}`;
  }
  function clearHover() {
    if (elevChart) { elevChart.$hoverIndex = null; elevChart.draw(); }
    if (hoverDot && routeMap && routeMap.hasLayer(hoverDot)) routeMap.removeLayer(hoverDot);
    $("#elevHover").textContent = "";
  }

  /* ------------------------------ day list ------------------------------ */
  let selectedDay = -1;
  function buildDayList(r, geo, colors) {
    const ol = $("#dayList");
    ol.innerHTML = "";
    r.days.forEach((d, i) => {
      const shops = (d.resupply || []).map((s) => `<span class="chip shop">${s.name}</span>`).join("");
      const li = document.createElement("li");
      li.className = "day-card";
      li.dataset.i = i;
      li.innerHTML = `
        <div class="day-top">
          <span class="day-num" style="color:${colors[i]}">DAY ${d.day}</span>
          <span class="day-name">${d.name}</span>
        </div>
        <div class="day-desc">${d.desc}</div>
        <div class="day-metrics">
          <span><b>${d.distance_km} km</b></span>
          <span>↑ <b>${fmtM(d.ascent_m)}</b></span>
          <span>↓ <b>${fmtM(d.descent_m)}</b></span>
          <span>high <b>${fmtM(d.max_ele)}</b></span>
        </div>
        <div class="day-foot">
          <span class="chip camp">${d.camp} · ${fmtM(d.end_ele)}</span>
          ${shops}
        </div>`;
      li.addEventListener("click", () => selectDay(i));
      ol.appendChild(li);
    });
  }

  function selectDay(i) {
    selectedDay = (selectedDay === i) ? -1 : i;
    document.querySelectorAll(".day-card").forEach((el, idx) => {
      el.classList.toggle("active", idx === selectedDay);
    });
    if (selectedDay === -1) {
      dayLayers.forEach((l) => l.setStyle({ opacity: .9, weight: 4 }));
      routeMap.fitBounds(currentGeo.bounds, { padding: [20, 20] });
      return;
    }
    dayLayers.forEach((l, idx) => l.setStyle({
      opacity: idx === i ? 1 : .2, weight: idx === i ? 6 : 3
    }));
    routeMap.fitBounds(dayLayers[i].getBounds(), { padding: [30, 30] });
    document.querySelectorAll(".day-card")[i].scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  /* ----------------------------- master map ----------------------------- */
  let masterMap = null, masterData = null, masterLayers = {}, mpChart = null, mpHighlight = null;

  function setHighlight(coords) {
    if (mpHighlight) { masterMap.removeLayer(mpHighlight); mpHighlight = null; }
    if (!coords || !coords.length) return;
    mpHighlight = L.layerGroup([
      L.polyline(coords, { color: "#fff", weight: 8, opacity: .9 }),
      L.polyline(coords, { color: "#111827", weight: 4, opacity: .95 })
    ]).addTo(masterMap);
    masterMap.fitBounds(coords, { padding: [40, 40] });
  }
  const passColor = (e) => (e >= 3500 ? "#c0341f" : e >= 3000 ? "#d98324" : "#3cb44b");
  const catColor = { road: "#2f7fb5", gravel: "#d98324", pass: "#c0341f" };

  async function openMaster() {
    showView("master");
    window.scrollTo(0, 0);
    if (masterMap) { setTimeout(() => masterMap.invalidateSize(), 60); return; }

    masterData = {
      passes: await fetch("data/passes.json").then((r) => r.json()),
      segments: await fetch("data/segments.json").then((r) => r.json()),
      pois: await fetch("data/pois.json").then((r) => r.json()),
      srmrSegs: await fetch("data/srmr_segments.json").then((r) => r.json()).catch(() => ({ segments: [] })),
      srmrGeo: await fetch("data/srmr_geo.json").then((r) => r.json()).catch(() => ({ editions: [] })),
      resupply: await fetch("data/resupply.json").then((r) => r.json()).catch(() => ({ places: [] })),
      permits: await fetch("data/permits.json").then((r) => r.json()).catch(() => ({ zones: [] }))
    };

    masterMap = L.map("masterMap", { scrollWheelZoom: true });
    const layers = tileLayers();
    layers["Cycle"].addTo(masterMap);
    L.control.layers(layers, null, { position: "topright" }).addTo(masterMap);

    // routes (faint)
    const gRoutes = L.layerGroup();
    ROUTES.forEach((r) => L.polyline(r.overview, { color: r.color, weight: 2.5, opacity: .55 })
      .bindTooltip(r.name, { sticky: true })
      .on("click", () => { location.hash = "r/" + r.id; })
      .addTo(gRoutes));

    // segments
    const gSegs = L.layerGroup();
    masterData.segments.segments.forEach((s) => {
      const line = L.polyline(s.coords, { color: catColor[s.cat], weight: 4, opacity: .85 })
        .bindTooltip(`${s.name} · ${s.distance_km} km`, { sticky: true })
        .on("click", () => showProfile(s.name, s.profile,
          `<b>${s.distance_km} km</b> · ↑ ${fmtM(s.ascent_m)} · ${s.cat} · high ${fmtM(s.max_ele)}`, null, s.coords));
      gSegs.addLayer(line);
    });

    // passes
    const gPass = L.layerGroup();
    masterData.passes.passes.forEach((p) => {
      const m = L.marker([p.lat, p.lon], {
        icon: L.divIcon({ className: "", iconSize: [16, 15], iconAnchor: [8, 15],
          html: `<div class="pass-tri" style="border-bottom-color:${passColor(p.ele)}"></div>` })
      });
      const stats = p.routable
        ? `<b>${fmtM(p.ele)}</b> summit · climb ${p.climb_km} km, ↑ ${fmtM(p.climb_ascent)} (~${p.avg_grade}%)<br>${p.side}`
        : `<b>${fmtM(p.ele)}</b> · ${p.side}<br><i>Reference marker — track not routed here.</i>`;
      m.bindTooltip(`${p.name} · ${fmtM(p.ele)}`, { direction: "top" });
      m.on("click", () => showProfile(p.name, p.profile, stats, p.routes, p.coords));
      gPass.addLayer(m);
    });

    // resupply towns/villages + trains on one combined layer
    const gPoi = buildPoiLayer(masterData.resupply.places, masterData.pois.trains);

    // SRMR-derived segments (real race sections), off by default
    const gSrmr = L.layerGroup();
    (masterData.srmrSegs.segments || []).forEach((s) => {
      L.polyline(s.coords, { color: s.color, weight: 3.5, opacity: .85 })
        .bindTooltip(`SRMR ${s.year} · ${s.name} · ${s.distance_km} km`, { sticky: true })
        .on("click", () => showProfile(`${s.name}`, s.profile,
          `<b>${s.distance_km} km</b> · ↑ ${fmtM(s.ascent_m)} · high ${fmtM(s.max_ele)} · from SRMR ${s.year}`, null, s.coords))
        .addTo(gSrmr);
    });

    // full Silk Road Mountain Race edition tracks (as on the SRMR page), off by default
    const gSrmrRoutes = L.layerGroup();
    (masterData.srmrGeo.editions || []).forEach((e) => {
      const hi = e.profile && e.profile.length ? Math.max(...e.profile.map((p) => p[1])) : 0;
      L.polyline(e.coords, { color: e.color, weight: 3, opacity: .8 })
        .bindTooltip(`SRMR ${e.year} · ${Math.round(e.distance_km)} km · ↑ ${fmtM(e.ascent_m)}`, { sticky: true })
        .on("click", () => showProfile(`Silk Road Mountain Race ${e.year}`, e.profile,
          `<b>${Math.round(e.distance_km)} km</b> · ↑ ${fmtM(e.ascent_m)}${hi ? ` · high ${fmtM(hi)}` : ""} · full race track`,
          null, e.coords))
        .addTo(gSrmrRoutes);
    });

    // approximate border-permit zones, off by default
    const gPermit = buildPermitLayer(masterData.permits.zones);

    masterLayers = { routes: gRoutes, segments: gSegs, passes: gPass, poi: gPoi, srmrseg: gSrmr, srmr: gSrmrRoutes, permit: gPermit };
    [gRoutes, gPass, gPoi, gSrmr].forEach((g) => g.addTo(masterMap)); // SRMR segments on; connectors + SRMR routes off by default

    addFullscreenControl(masterMap, "masterMapWrap");
    masterMap.fitBounds(mergeBounds(ROUTES.map((r) => r.bounds)), { padding: [24, 24] });
    setTimeout(() => masterMap.invalidateSize(), 60);

    buildMasterToolbar();
    buildMasterLegend();
    buildMasterPanel();
  }

  function addFullscreenControl(map, wrapId) {
    const Fs = L.Control.extend({
      onAdd() {
        const b = L.DomUtil.create("a", "leaflet-bar fs-btn");
        b.href = "#"; b.innerHTML = "⛶"; b.title = "Toggle fullscreen";
        L.DomEvent.on(b, "click", (e) => {
          L.DomEvent.stop(e);
          const el = document.getElementById(wrapId);
          if (document.fullscreenElement) (document.exitFullscreen || document.webkitExitFullscreen).call(document);
          else (el.requestFullscreen || el.webkitRequestFullscreen).call(el);
        });
        return b;
      }
    });
    map.addControl(new Fs({ position: "topleft" }));
    const relayout = () => setTimeout(() => map.invalidateSize(), 120);
    document.addEventListener("fullscreenchange", relayout);
    document.addEventListener("webkitfullscreenchange", relayout);
  }

  function buildMasterToolbar() {
    const defs = [
      ["routes", "Routes", "#e6194B", true], ["passes", "Mountain passes", "#c0341f", true],
      ["segments", "Segments", "#d98324", false], ["srmrseg", "SRMR segments", "#7b1fa2", true],
      ["srmr", "SRMR routes", "#2c6b3f", false],
      ["poi", "Resupply & trains", "#2f7fb5", true],
      ["permit", "Border permits", "#b3261e", false]
    ];
    const bar = $("#masterToolbar");
    bar.innerHTML = "";
    defs.forEach(([key, label, col, on]) => {
      const el = document.createElement("label");
      el.className = "mt-toggle" + (on ? "" : " off");
      el.innerHTML = `<input type="checkbox" ${on ? "checked" : ""}><span class="dot" style="background:${col}"></span>${label}`;
      el.querySelector("input").addEventListener("change", (e) => {
        el.classList.toggle("off", !e.target.checked);
        if (e.target.checked) masterLayers[key].addTo(masterMap);
        else masterMap.removeLayer(masterLayers[key]);
      });
      bar.appendChild(el);
    });
  }

  function buildMasterLegend() {
    $("#masterLegend").innerHTML = `
      <div class="lg"><span class="sw" style="background:#2f7fb5"></span>Road segment</div>
      <div class="lg"><span class="sw" style="background:#d98324"></span>Gravel segment</div>
      <div class="lg"><span class="sw" style="background:#c0341f"></span>Pass segment</div>
      <div class="lg"><span class="sw tri"></span>Mountain pass</div>
      <div class="lg"><span class="sw dot2" style="background:#2f7fb5"></span>Resupply town</div>
      <div class="lg"><span class="train-marker" style="width:14px;height:14px;font-size:9px">▤</span>Train stop</div>`;
  }

  function buildMasterPanel() {
    const pl = $("#passList");
    pl.innerHTML = "";
    masterData.passes.passes.slice().sort((a, b) => b.ele - a.ele).forEach((p) => {
      const li = document.createElement("li");
      li.className = "mp-item" + (p.routable ? "" : " ref");
      li.innerHTML = `<span class="mp-badge" style="background:${passColor(p.ele)}">${p.ele} m</span>
        <span><span class="mp-name">${p.name}</span><br><span class="mp-meta">${p.side}</span></span>`;
      li.addEventListener("click", () => {
        const stats = p.routable
          ? `<b>${fmtM(p.ele)}</b> summit · climb ${p.climb_km} km, ↑ ${fmtM(p.climb_ascent)} (~${p.avg_grade}%)`
          : `<b>${fmtM(p.ele)}</b> · reference marker (track not routed here)`;
        showProfile(p.name, p.profile, stats, p.routes, p.coords);
        if (!p.coords) masterMap.setView([p.lat, p.lon], 11);
      });
      pl.appendChild(li);
    });
    const sl = $("#segList");
    sl.innerHTML = "";
    masterData.segments.segments.forEach((s) => {
      const li = document.createElement("li");
      li.className = "mp-item";
      li.innerHTML = `<span class="mp-badge cat-${s.cat}">${Math.round(s.distance_km)}k</span>
        <span><span class="mp-name">${s.name}</span><br><span class="mp-meta">↑ ${fmtM(s.ascent_m)} · high ${fmtM(s.max_ele)} · ${s.cat}</span></span>`;
      li.addEventListener("click", () => {
        showProfile(s.name, s.profile, `<b>${s.distance_km} km</b> · ↑ ${fmtM(s.ascent_m)} · ${s.cat} · high ${fmtM(s.max_ele)}`, null, s.coords);
      });
      sl.appendChild(li);
    });

    // SRMR race segments
    const ssl = $("#srmrSegList");
    ssl.innerHTML = "";
    (masterData.srmrSegs.segments || []).forEach((s) => {
      const li = document.createElement("li");
      li.className = "mp-item";
      li.innerHTML = `<span class="mp-badge" style="background:${s.color}">${Math.round(s.distance_km)}k</span>
        <span><span class="mp-name">${s.name}</span><br><span class="mp-meta">↑ ${fmtM(s.ascent_m)} · high ${fmtM(s.max_ele)} · SRMR ${s.year}</span></span>`;
      li.addEventListener("click", () => {
        showProfile(s.name, s.profile, `<b>${s.distance_km} km</b> · ↑ ${fmtM(s.ascent_m)} · high ${fmtM(s.max_ele)} · from SRMR ${s.year}`, null, s.coords);
      });
      ssl.appendChild(li);
    });
  }

  function showProfile(title, profile, statsHtml, routes, coords) {
    $("#mpProfile").hidden = false;
    $("#mpProfileTitle").textContent = title;
    $("#mpProfileStats").innerHTML = statsHtml || "";
    setHighlight(coords);
    const rc = $("#mpRoutes");
    rc.innerHTML = "";
    if (routes && routes.length) {
      rc.innerHTML = '<span class="mp-routes-label">Ridden by — tap for its elevation profile:</span>';
      routes.forEach((r) => {
        const chip = document.createElement("button");
        chip.className = "route-chip";
        chip.innerHTML = `<span class="rc-dot" style="background:${r.color}"></span>${r.name}`;
        chip.addEventListener("click", () => { location.hash = "r/" + r.id; });
        rc.appendChild(chip);
      });
    } else if (routes) {
      rc.innerHTML = '<span class="mp-routes-label">No planned route crosses this pass yet.</span>';
    }
    const ctx = $("#mpChart").getContext("2d");
    if (mpChart) mpChart.destroy();
    if (!profile) {
      ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
      $("#mpProfileStats").innerHTML += "<br><i>No elevation profile available.</i>";
      return;
    }
    mpChart = new Chart(ctx, {
      type: "line",
      data: { datasets: [{ data: profile.map((p) => ({ x: p[0], y: p[1] })),
        borderColor: "#c0341f", borderWidth: 2, pointRadius: 0, fill: true,
        backgroundColor: "rgba(192,52,31,.10)", tension: 0 }] },
      options: {
        animation: false, parsing: false, maintainAspectRatio: false,
        interaction: { mode: "nearest", axis: "x", intersect: false },
        scales: { x: { type: "linear", title: { display: true, text: "km" }, ticks: { maxTicksLimit: 6 } },
                  y: { title: { display: true, text: "m" } } },
        plugins: { legend: { display: false } }
      }
    });
  }

  $("#mpProfileClose").addEventListener("click", () => {
    $("#mpProfile").hidden = true;
    if (mpHighlight) { masterMap.removeLayer(mpHighlight); mpHighlight = null; }
  });

  /* ----------------------------- SRMR page ----------------------------- */
  let srmrData = null, srmrGeo = null, srmrCharts = [], srmrMap = null, srmrLayers = {};

  async function openSrmr() {
    showView("srmr");
    window.scrollTo(0, 0);
    if (!srmrData) {
      [srmrData, srmrGeo] = await Promise.all([
        fetch("data/srmr.json").then((r) => r.json()),
        fetch("data/srmr_geo.json").then((r) => r.json()).catch(() => ({ editions: [] }))
      ]);
      srmrGeo = Object.fromEntries((srmrGeo.editions || []).map((e) => [e.year, e]));
      $("#srmrSource").textContent = srmrData.source;
      buildSrmrMap();
      buildSrmrCompare();
      buildSrmrList();
    }
    if (srmrMap) setTimeout(() => srmrMap.invalidateSize(), 80);
  }

  function buildSrmrMap() {
    srmrMap = L.map("srmrMap", { scrollWheelZoom: true });
    const layers = tileLayers();
    layers["Cycle"].addTo(srmrMap);
    L.control.layers(layers, null, { position: "topright" }).addTo(srmrMap);
    addFullscreenControl(srmrMap, "srmrMapWrap");

    const eds = Object.values(srmrGeo).sort((a, b) => a.year - b.year);
    const allpts = [];
    const tog = $("#srmrMapToggles");
    tog.innerHTML = "";
    eds.forEach((e) => {
      allpts.push(...e.coords);
      const g = L.layerGroup();
      L.polyline(e.coords, { color: e.color, weight: 3, opacity: .85 })
        .bindTooltip(`<b>SRMR ${e.year}</b> · ${Math.round(e.distance_km)} km · ↑ ${Math.round(e.ascent_m).toLocaleString()} m`, { sticky: true })
        .addTo(g);
      L.circleMarker(e.start, { radius: 5, color: "#fff", weight: 2, fillColor: "#2c6b3f", fillOpacity: 1 })
        .bindTooltip(`SRMR ${e.year} — start`).addTo(g);
      L.circleMarker(e.finish, { radius: 5, color: "#fff", weight: 2, fillColor: "#b3261e", fillOpacity: 1 })
        .bindTooltip(`SRMR ${e.year} — finish`).addTo(g);
      g.addTo(srmrMap);
      srmrLayers[e.year] = g;

      const chip = document.createElement("label");
      chip.className = "mt-toggle";
      chip.innerHTML = `<input type="checkbox" checked><span class="dot" style="background:${e.color}"></span>SRMR ${e.year}`;
      chip.querySelector("input").addEventListener("change", (ev) => {
        chip.classList.toggle("off", !ev.target.checked);
        if (ev.target.checked) srmrLayers[e.year].addTo(srmrMap);
        else srmrMap.removeLayer(srmrLayers[e.year]);
      });
      tog.appendChild(chip);
    });
    if (allpts.length) srmrMap.fitBounds(allpts, { padding: [30, 30] });
    setTimeout(() => srmrMap.invalidateSize(), 80);
  }

  function buildSrmrCompare() {
    const eds = Object.values(srmrGeo).sort((a, b) => a.year - b.year);
    new Chart($("#srmrCompare").getContext("2d"), {
      type: "bar",
      data: {
        labels: eds.map((e) => e.year),
        datasets: [
          { label: "Distance (km)", data: eds.map((e) => Math.round(e.distance_km)), backgroundColor: "#3cb44b", yAxisID: "y" },
          { label: "Climbing (m)", data: eds.map((e) => e.ascent_m), backgroundColor: "#e8442b", yAxisID: "y1" }
        ]
      },
      options: {
        maintainAspectRatio: false,
        scales: {
          y: { position: "left", title: { display: true, text: "km" }, beginAtZero: true },
          y1: { position: "right", title: { display: true, text: "m climbing" }, beginAtZero: true, grid: { drawOnChartArea: false } }
        },
        plugins: { legend: { position: "bottom" } }
      }
    });
  }

  function buildSrmrList() {
    const wrap = $("#srmrList");
    wrap.innerHTML = "";
    const metaByYear = Object.fromEntries(srmrData.editions.map((e) => [e.year, e]));
    const years = new Set([...srmrData.editions.map((e) => e.year), ...Object.keys(srmrGeo).map(Number)]);

    [...years].sort((a, b) => b - a).forEach((year) => {
      const e = metaByYear[year] || { year };
      const geo = srmrGeo[year];
      const card = document.createElement("article");

      if (e.cancelled) {
        card.className = "srmr-card dim";
        card.innerHTML = `<div class="srmr-card-head"><span class="srmr-year">${year}</span>
          <span class="srmr-badge cancel">Cancelled</span></div><p class="srmr-desc">${e.desc}</p>`;
        wrap.appendChild(card); return;
      }

      const dist = e.distance_km || (geo && geo.distance_km);
      const asc = e.ascent_m || (geo && geo.ascent_m);
      card.className = "srmr-card";

      const stats = [
        dist && ["Distance", fmtKm(dist)],
        asc && ["Climbing", fmtM(asc)],
        (e.start && e.start !== "—") && ["Route", `${e.start} → ${e.finish}`],
        e.duration_h && ["Winning-ish time", `~${e.duration_h} h`]
      ].filter(Boolean).map(([k, v]) => `<div class="s"><span>${k}</span><strong>${v}</strong></div>`).join("");

      const stages = e.stages
        ? `<ul class="srmr-stages">${e.stages.map((s) => `<li><b>${s.n}. ${s.name}</b><br>${s.km} km · ↑ ${fmtM(s.asc)}</li>`).join("")}</ul>` : "";

      const links = [];
      if (e.komootTour) links.push(`<a class="srmr-link" target="_blank" rel="noopener" href="https://www.komoot.com/tour/${e.komootTour}">Open on komoot ↗</a>`);
      if (e.komootCollection) links.push(`<a class="srmr-link" target="_blank" rel="noopener" href="https://www.komoot.com/collection/${e.komootCollection}/${e.komootSlug || ""}">Open on komoot ↗</a>`);
      if (e.rwgps) links.push(`<a class="srmr-link" target="_blank" rel="noopener" href="https://ridewithgps.com/routes/${e.rwgps}">Ride with GPS ↗</a>`);
      if (e.official) links.push(`<a class="srmr-link" target="_blank" rel="noopener" href="${e.official}">Official race page ↗</a>`);

      const chartId = `srmr-chart-${year}`;
      const visual = (geo && geo.profile)
        ? `<div class="srmr-chartwrap"><h4>Elevation profile — official track (${Math.round(geo.distance_km)} km, ↑ ${fmtM(geo.ascent_m)})</h4>
           <canvas id="${chartId}"></canvas></div>` : "";

      card.innerHTML = `
        <div class="srmr-card-head">
          <span class="srmr-year">${year}</span>
          <span class="srmr-title">${e.title || ""}</span>
          ${geo ? '<span class="srmr-badge ok">Real GPS track</span>' : ""}
        </div>
        <div class="srmr-stats">${stats}</div>
        <p class="srmr-desc">${e.desc || ""}</p>
        ${e.highlights ? `<ul class="srmr-stages">${e.highlights.map((h) => `<li>${h}</li>`).join("")}</ul>` : ""}
        ${stages}
        ${visual}
        ${links.length ? `<div class="srmr-links">${links.join("")}</div>` : ""}`;
      wrap.appendChild(card);

      if (geo && geo.profile) {
        const ctx = document.getElementById(chartId).getContext("2d");
        srmrCharts.push(new Chart(ctx, {
          type: "line",
          data: { datasets: [{ data: geo.profile.map((p) => ({ x: p[0], y: p[1] })),
            borderColor: geo.color || "#e8442b", borderWidth: 1.5, pointRadius: 0, fill: true,
            backgroundColor: "rgba(232,68,43,.08)", tension: 0 }] },
          options: { parsing: false, maintainAspectRatio: false, animation: false,
            interaction: { mode: "nearest", axis: "x", intersect: false },
            plugins: { legend: { display: false } },
            scales: { x: { type: "linear", title: { display: true, text: "distance (km)" } },
                      y: { title: { display: true, text: "elevation (m)" } } } }
        }));
      }
    });
  }

  /* ----------------------------- planner ----------------------------- */
  let plannerMap = null, plannerLayer = null, plannerChart = null, plannerData = null;
  let plannerLegs = [], plannerStart = null, plannerLast = null, plannerBusy = false;
  let plannerHoverDot = null, plannerHoverPts = [];

  function plannerSetHover(idx) {
    const p = plannerHoverPts[idx];
    if (!p || !plannerMap) return;
    plannerChart.$hoverIndex = idx; plannerChart.draw();
    if (!plannerHoverDot) plannerHoverDot = L.circleMarker([p.lat, p.lon],
      { radius: 6, color: "#fff", weight: 2, fillColor: "#e8442b", fillOpacity: 1, interactive: false });
    plannerHoverDot.setLatLng([p.lat, p.lon]);
    if (!plannerMap.hasLayer(plannerHoverDot)) plannerHoverDot.addTo(plannerMap);
    const hi = $("#plannerHoverInfo");
    if (hi) hi.textContent = `${p.x.toFixed(1)} km · ${Math.round(p.y).toLocaleString()} m`;
  }
  function plannerClearHover() {
    if (plannerChart) { plannerChart.$hoverIndex = null; plannerChart.draw(); }
    if (plannerHoverDot && plannerMap && plannerMap.hasLayer(plannerHoverDot)) plannerMap.removeLayer(plannerHoverDot);
    const hi = $("#plannerHoverInfo");
    if (hi) hi.textContent = "";
  }
  const plStatus = (t) => { $("#plannerStatus").textContent = t; };
  const plProfile = () => $("#plannerProfile").value;

  function plLegStats(coords) {
    let dist = 0, asc = 0;
    const e = coords.map((c) => c[2]);
    const sm = e.slice();
    for (let i = 1; i < e.length - 1; i++) sm[i] = (e[i - 1] + e[i] + e[i + 1]) / 3;
    for (let i = 1; i < coords.length; i++) {
      dist += haversine(coords[i - 1], coords[i]);
      const de = sm[i] - sm[i - 1];
      if (de > 0) asc += de;
    }
    return { dist_km: dist / 1000, ascent: asc };
  }

  const plEleAt = (profile, km) => {
    if (!profile || !profile.length) return 0;
    if (km <= profile[0][0]) return profile[0][1];
    for (let i = 1; i < profile.length; i++) {
      if (profile[i][0] >= km) {
        const a = profile[i - 1], b = profile[i];
        const t = (km - a[0]) / ((b[0] - a[0]) || 1);
        return a[1] + (b[1] - a[1]) * t;
      }
    }
    return profile[profile.length - 1][1];
  };

  function plInterp(coords2d, profile) {
    const out = [[coords2d[0][0], coords2d[0][1], plEleAt(profile, 0)]];
    let km = 0;
    for (let i = 1; i < coords2d.length; i++) {
      km += haversine(coords2d[i - 1], coords2d[i]) / 1000;
      out.push([coords2d[i][0], coords2d[i][1], plEleAt(profile, km)]);
    }
    return out;
  }

  async function plRouteLeg(a, b) {
    const url = `https://brouter.de/brouter?lonlats=${a[1]},${a[0]}|${b[1]},${b[0]}&profile=${plProfile()}&alternativeidx=0&format=geojson`;
    const r = await fetch(url);
    if (!r.ok) throw new Error("route failed");
    const d = await r.json();
    const c = d.features[0].geometry.coordinates.map((p) => [p[1], p[0], p[2]]);
    return { kind: "route", name: "Routed leg", color: "#e8442b", coords: c, ...plLegStats(c) };
  }

  async function plannerAddPoint(latlng) {
    if (plannerBusy) return;
    const p = [latlng.lat, latlng.lng];
    if (!plannerLast) { plannerStart = p; plannerLast = p; plannerRedraw(false); plStatus("Click the next point — I'll route to it."); return; }
    plannerBusy = true; plStatus("routing…");
    try {
      const leg = await plRouteLeg(plannerLast, p);
      plannerLegs.push(leg);
      plannerLast = [leg.coords[leg.coords.length - 1][0], leg.coords[leg.coords.length - 1][1]];
      plStatus("Added. Keep clicking, or add a segment.");
    } catch (e) {
      plStatus("No route to that spot — try nearer a road or track.");
    }
    plannerBusy = false; plannerRedraw(false);
  }

  const segIdOf = (s) => (s.year ? `srmr:${s.year}:${s.name}` : `seg:${s.name}`);

  function flipName(name) {
    for (const sep of [" ↔ ", " → ", " -> "]) {
      if (name.includes(sep)) { const [a, b] = name.split(sep); return `${b}${sep}${a}`; }
    }
    return name;
  }

  async function plannerAddSegment(seg, segId) {
    if (plannerBusy) return;
    segId = segId || segIdOf(seg);
    let coords3d = plInterp(seg.coords, seg.profile);
    let reversed = false;

    if (plannerLast) {
      // attach to whichever end of the segment is nearest to the current route end
      const dStart = haversine(plannerLast, [coords3d[0][0], coords3d[0][1]]);
      const dEnd = haversine(plannerLast, [coords3d[coords3d.length - 1][0], coords3d[coords3d.length - 1][1]]);
      if (dEnd < dStart) { coords3d = coords3d.slice().reverse(); reversed = true; }
      const gap = Math.min(dStart, dEnd);
      if (gap > 250) {
        plannerBusy = true; plStatus("connecting to segment…");
        try {
          const conn = await plRouteLeg(plannerLast, [coords3d[0][0], coords3d[0][1]]);
          conn.autoFor = segId;               // tie connector to this segment
          plannerLegs.push(conn);
        } catch (e) {
          plStatus("Couldn't connect to that segment."); plannerBusy = false; return;
        }
        plannerBusy = false;
      }
    } else {
      plannerStart = [coords3d[0][0], coords3d[0][1]];
    }

    const st = plLegStats(coords3d);          // distance/ascent for the actual orientation
    const dispName = (reversed ? flipName(seg.name) : seg.name) + (seg.year ? ` · SRMR ${seg.year}` : "");
    plannerLegs.push({ kind: "segment", segId, name: dispName,
      color: "#2f7fb5", coords: coords3d, dist_km: st.dist_km, ascent: st.ascent });
    plannerLast = [coords3d[coords3d.length - 1][0], coords3d[coords3d.length - 1][1]];
    plStatus("Segment added — click it again in the list to remove.");
    plannerRedraw(true);
  }

  function plannerRecompute() {
    if (!plannerLegs.length) { plannerStart = null; plannerLast = null; return; }
    const f = plannerLegs[0].coords[0];
    plannerStart = [f[0], f[1]];
    const lc = plannerLegs[plannerLegs.length - 1].coords;
    plannerLast = [lc[lc.length - 1][0], lc[lc.length - 1][1]];
  }

  function plannerRemoveSegment(segId) {
    plannerLegs = plannerLegs.filter((l) => l.segId !== segId && l.autoFor !== segId);
    plannerRecompute();
    plStatus("Segment removed.");
    plannerRedraw(true);
  }

  function plannerRefreshSegList() {
    const ids = new Set(plannerLegs.map((l) => l.segId).filter(Boolean));
    document.querySelectorAll("#plannerSegList .mp-item").forEach((li) => {
      li.classList.toggle("sel", ids.has(li.dataset.segid));
    });
  }

  function plannerRedraw(fit) {
    plannerLayer.clearLayers();
    const bounds = [];
    plannerLegs.forEach((leg) => {
      const ll = leg.coords.map((c) => [c[0], c[1]]);
      L.polyline(ll, { color: leg.color, weight: 4, opacity: .9 }).addTo(plannerLayer);
      bounds.push(...ll);
    });
    if (plannerStart) L.circleMarker(plannerStart, { radius: 6, color: "#fff", weight: 2, fillColor: "#2c6b3f", fillOpacity: 1 }).bindTooltip("Start").addTo(plannerLayer);
    if (plannerLast && plannerLegs.length) L.circleMarker(plannerLast, { radius: 6, color: "#fff", weight: 2, fillColor: "#b3261e", fillOpacity: 1 }).bindTooltip("End").addTo(plannerLayer);
    if (fit && bounds.length) plannerMap.fitBounds(bounds, { padding: [40, 40] });
    plannerUpdate();
  }

  function plannerUpdate() {
    const all = [];
    plannerLegs.forEach((l) => l.coords.forEach((c, i) => { if (all.length && i === 0) return; all.push(c); }));
    let dist = 0, asc = 0;
    plannerLegs.forEach((l) => { dist += l.dist_km; asc += l.ascent; });
    let maxEle = 0;
    for (const c of all) if (c[2] > maxEle) maxEle = c[2];
    $("#plannerTotals").innerHTML =
      `<div class="s"><span>Distance</span><strong>${dist ? fmtKm(dist) : "0 km"}</strong></div>
       <div class="s"><span>Climbing</span><strong>${fmtM(asc)}</strong></div>
       <div class="s"><span>Highest</span><strong>${all.length ? fmtM(maxEle) : "—"}</strong></div>
       <div class="s"><span>Pieces</span><strong>${plannerLegs.length}</strong></div>`;

    let combo = [], km = 0;
    for (let i = 0; i < all.length; i++) {
      if (i) km += haversine(all[i - 1], all[i]) / 1000;
      combo.push({ x: km, y: all[i][2], lat: all[i][0], lon: all[i][1] });
    }
    if (combo.length > 700) { const st = combo.length / 700; const d = []; for (let i = 0; i < 700; i++) d.push(combo[Math.floor(i * st)]); d.push(combo[combo.length - 1]); combo = d; }
    plannerHoverPts = combo;
    const ctx = $("#plannerChart").getContext("2d");
    if (plannerChart) plannerChart.destroy();
    const crosshair = {
      id: "plCrosshair",
      afterDraw(c) {
        const idx = c.$hoverIndex;
        if (idx == null || !plannerHoverPts[idx]) return;
        const x = c.scales.x.getPixelForValue(plannerHoverPts[idx].x);
        const { top, bottom } = c.chartArea, g = c.ctx;
        g.save(); g.beginPath(); g.moveTo(x, top); g.lineTo(x, bottom);
        g.lineWidth = 1; g.strokeStyle = "rgba(28,33,40,.4)"; g.stroke(); g.restore();
      }
    };
    plannerChart = new Chart(ctx, {
      type: "line",
      data: { datasets: [{ data: combo.map((p) => ({ x: p.x, y: p.y })), borderColor: "#e8442b", borderWidth: 1.5, pointRadius: 0, fill: true, backgroundColor: "rgba(232,68,43,.08)", tension: 0 }] },
      options: { parsing: false, maintainAspectRatio: false, animation: false,
        interaction: { mode: "nearest", axis: "x", intersect: false },
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        scales: { x: { type: "linear", title: { display: true, text: "distance (km)" } }, y: { title: { display: true, text: "elevation (m)" } } },
        onHover: (e, active) => { if (active.length) plannerSetHover(active[0].index); } },
      plugins: [crosshair]
    });
    $("#plannerChart").onmouseleave = () => plannerClearHover();

    const ol = $("#plannerLegs");
    if (!plannerLegs.length) { ol.innerHTML = '<li class="pl-empty">No pieces yet. Click the map to set a start, then keep clicking — or add a segment below.</li>'; }
    else {
      ol.innerHTML = "";
      plannerLegs.forEach((l) => {
        const li = document.createElement("li");
        li.className = "pl-leg";
        li.innerHTML = `<span class="lg-dot" style="background:${l.color}"></span><span class="lg-name">${l.name}</span><span class="lg-meta">${l.dist_km.toFixed(1)} km · ↑ ${fmtM(l.ascent)}</span>`;
        ol.appendChild(li);
      });
    }

    plannerRefreshSegList();

    const gpxA = $("#plannerGpx");
    if (gpxA._url) URL.revokeObjectURL(gpxA._url);
    if (all.length > 1) {
      const blob = new Blob([plannerGpx(all)], { type: "application/gpx+xml" });
      gpxA._url = URL.createObjectURL(blob);
      gpxA.href = gpxA._url; gpxA.download = "my-kyrgyzstan-route.gpx";
      gpxA.classList.add("ready");
    } else gpxA.classList.remove("ready");
  }

  function plannerGpx(coords) {
    let s = '<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" creator="tour-de-kyrgyzstan" xmlns="http://www.topografix.com/GPX/1/1"><trk><name>My planned route</name><trkseg>';
    coords.forEach((c) => { s += `<trkpt lat="${c[0].toFixed(6)}" lon="${c[1].toFixed(6)}"><ele>${(c[2] || 0).toFixed(1)}</ele></trkpt>`; });
    return s + "</trkseg></trk></gpx>";
  }

  function buildPlannerSegList() {
    const ul = $("#plannerSegList");
    ul.innerHTML = "";
    const mk = (s, tag, color) => {
      const segId = segIdOf(s);
      const li = document.createElement("li");
      li.className = "mp-item";
      li.dataset.segid = segId;
      li.innerHTML = `<span class="mp-badge" style="background:${color}">${Math.round(s.distance_km)}k</span>
        <span><span class="mp-name">${s.name}</span><br><span class="mp-meta">↑ ${fmtM(s.ascent_m)}${tag}</span></span>`;
      li.addEventListener("click", () => {
        if (plannerLegs.some((l) => l.segId === segId)) plannerRemoveSegment(segId);
        else plannerAddSegment(s, segId);
      });
      ul.appendChild(li);
    };
    (plannerData.connectors || []).forEach((s) => mk(s, ` · ${s.cat}`, s.cat === "pass" ? "#c0341f" : s.cat === "gravel" ? "#d98324" : "#2f7fb5"));
    (plannerData.srmr || []).forEach((s) => mk(s, ` · SRMR ${s.year}`, s.color || "#7b1fa2"));
  }

  async function openPlanner() {
    showView("planner");
    window.scrollTo(0, 0);
    if (!plannerMap) {
      plannerMap = L.map("plannerMap");
      const layers = tileLayers();
      layers["Cycle"].addTo(plannerMap);
      addFullscreenControl(plannerMap, "plannerMapWrap");
      plannerMap.setView([42.1, 75.8], 7);
      plannerLayer = L.layerGroup().addTo(plannerMap);
      plannerMap.on("click", (e) => plannerAddPoint(e.latlng));
      const [seg, ss, pois, resupply, permits] = await Promise.all([
        fetch("data/segments.json").then((r) => r.json()),
        fetch("data/srmr_segments.json").then((r) => r.json()).catch(() => ({ segments: [] })),
        fetch("data/pois.json").then((r) => r.json()).catch(() => ({ resupply: [], trains: [] })),
        fetch("data/resupply.json").then((r) => r.json()).catch(() => ({ places: [] })),
        fetch("data/permits.json").then((r) => r.json()).catch(() => ({ zones: [] }))
      ]);
      plannerData = { connectors: seg.segments, srmr: ss.segments };

      // base layers only in the corner control; overlays use pill toggles (like the master map)
      L.control.layers(layers, null, { position: "topright" }).addTo(plannerMap);

      const gPoi = buildPoiLayer(resupply.places, pois.trains);
      const gPermit = buildPermitLayer(permits.zones);
      buildLayerToggles($("#plannerLayers"), plannerMap, [
        ["poi", "Resupply & trains", "#2f7fb5", true, gPoi],
        ["permit", "Border permits", "#b3261e", false, gPermit]
      ]);

      buildPlannerSegList();
      plannerRedraw(false);
    }
    setTimeout(() => plannerMap.invalidateSize(), 80);
  }

  function plannerLoadGpx(text) {
    const xml = new DOMParser().parseFromString(text, "application/xml");
    if (xml.querySelector("parsererror")) { plStatus("That doesn't look like a valid GPX file."); return; }
    let pts = Array.from(xml.getElementsByTagName("trkpt"));
    if (!pts.length) pts = Array.from(xml.getElementsByTagName("rtept"));
    let coords = pts.map((p) => {
      const lat = parseFloat(p.getAttribute("lat")), lon = parseFloat(p.getAttribute("lon"));
      const ele = p.getElementsByTagName("ele")[0];
      return [lat, lon, ele ? parseFloat(ele.textContent) : 0];
    }).filter((c) => isFinite(c[0]) && isFinite(c[1]));
    if (coords.length < 2) { plStatus("No usable track points found in that GPX."); return; }
    if (coords.length > 3000) {
      const step = coords.length / 3000, d = [];
      for (let i = 0; i < 3000; i++) d.push(coords[Math.floor(i * step)]);
      d.push(coords[coords.length - 1]); coords = d;
    }
    plannerLegs = [{ kind: "upload", name: "Uploaded GPX", color: "#e8442b", coords, ...plLegStats(coords) }];
    plannerStart = [coords[0][0], coords[0][1]];
    plannerLast = [coords[coords.length - 1][0], coords[coords.length - 1][1]];
    plStatus("GPX loaded — keep clicking or add segments to extend it.");
    plannerRedraw(true);
  }

  $("#plannerUpload").addEventListener("change", (e) => {
    const f = e.target.files && e.target.files[0];
    e.target.value = "";                       // allow re-selecting the same file
    if (!f) return;
    if (!/\.gpx$/i.test(f.name)) { plStatus("Please choose a .gpx file."); return; }
    const reader = new FileReader();
    reader.onload = () => { try { plannerLoadGpx(String(reader.result)); } catch (err) { plStatus("Couldn't read that GPX file."); } };
    reader.onerror = () => plStatus("Couldn't read that file.");
    reader.readAsText(f);
  });

  $("#plannerUndo").addEventListener("click", () => {
    plannerLegs.pop();
    plannerLast = plannerLegs.length
      ? (() => { const c = plannerLegs[plannerLegs.length - 1].coords; return [c[c.length - 1][0], c[c.length - 1][1]]; })()
      : plannerStart;
    plannerRedraw(false);
  });
  $("#plannerClear").addEventListener("click", () => {
    plannerLegs = []; plannerStart = null; plannerLast = null;
    plannerRedraw(false); plStatus("Cleared. Click the map to set your start.");
  });

  /* ----------------------------- navigation ----------------------------- */
  function showLanding() {
    showView("landing");
    if (location.hash.startsWith("#r/") || ["#master", "#srmr", "#planner"].includes(location.hash))
      history.replaceState(null, "", location.pathname);
  }

  function route() {
    const h = location.hash;
    if (h.startsWith("#r/")) {
      const id = h.slice(3);
      if (ROUTES.find((x) => x.id === id)) { openRoute(id); return; }
    }
    if (h === "#master") { openMaster(); return; }
    if (h === "#srmr") { openSrmr(); return; }
    if (h === "#planner") { openPlanner(); return; }
    showLanding();
  }

  $("#backBtn").addEventListener("click", () => { location.hash = ""; });
  $("#masterBack").addEventListener("click", () => { location.hash = ""; });
  $("#srmrBack").addEventListener("click", () => { location.hash = ""; });
  $("#plannerBack").addEventListener("click", () => { location.hash = ""; });
  $("#brandHome").addEventListener("click", () => { location.hash = ""; });
  $("#navMaster").addEventListener("click", (e) => { e.preventDefault(); location.hash = "master"; });
  $("#navSrmr").addEventListener("click", (e) => { e.preventDefault(); location.hash = "srmr"; });
  $("#navPlanner").addEventListener("click", (e) => { e.preventDefault(); location.hash = "planner"; });
  window.addEventListener("hashchange", () => {
    const h = location.hash;
    if (h === "#master") openMaster();
    else if (h === "#srmr") openSrmr();
    else if (h === "#planner") openPlanner();
    else if (h.startsWith("#r/")) route();
    else if (!h || h === "#routes" || h === "#about") {
      if (!$("#detail").hidden || !$("#master").hidden || !$("#srmr").hidden || !$("#planner").hidden) showLanding();
    }
  });

  /* ------------------------------- init ------------------------------- */
  Promise.all([
    fetch("data/routes.json").then((r) => r.json()),
    fetch("data/custom_routes.json").then((r) => r.json()).catch(() => ({ routes: [] }))
  ])
    .then(([data, custom]) => {
      const extra = (custom.routes || []).map((r) => ({ ...r, custom: true }));
      ROUTES = [...data.routes, ...extra];
      buildCards();
      route();
    })
    .catch((err) => {
      document.body.innerHTML = '<p style="padding:40px;font-family:sans-serif">Could not load route data. Run <code>python3 scripts/generate_routes.py</code> and serve the folder over HTTP.</p>';
      console.error(err);
    });
})();
