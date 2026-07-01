# Tour de Kyrgyzstan 🇰🇬🚲

Fifteen hand-built **bikepacking routes** through Kyrgyzstan, plus a **master
planning map**, with an interactive website showing the **map + elevation
profile** for each route (à la komoot / Ride with GPS), a day-by-day plan and
resupply points.

The routes are inspired by the [Silk Road Mountain Race](https://www.themountainraces.cc/silk-road-mountain-race)
but re-tuned for self-supported touring. They come in three families:

- **Lake & valley routes** (1–5): gentler, every camp low (≤ ~2000 m), no pass
  over 3500 m.
- **High-pass loops** (6–10): wilder, remote and gravel-first, using the classic
  passes (Kegety, Kök-Ayryk, Shamsy, Kalmak-Ashuu into Song-Köl). A few nights high.
- **Expert straight-line traverses** (11–15): long point-to-point lines that
  prioritise a *straight* route over the passes rather than dodging them — up to
  3 days between resupplies and several nights at 2500–3050 m. Most finish in
  **Bishkek** (handy for the flight home) and none use the busy Tokmok–Balykchy
  (Boom Gorge) highway.

The **master map** overlays all routes and adds every mountain pass (with its
climb profile and the routes that cross it), the reusable connector segments, all
resupply towns and the railway stops — so you can also design your own line.

There's also a **Silk Road Mountain Race** page comparing the 2019–2026 editions.
It opens with an **all-editions overlay map** showing the **real official tracks**
(toggle each year on/off), followed by a distance-vs-climbing comparison chart and
per-edition cards with the real elevation profile, stats and links.

The tracks are pulled straight from the organisers' public routes by
`scripts/fetch_srmr.py` — Ride with GPS route JSON for 2025–2026 and komoot
tour/collection geometry for 2019–2024 — into `data/srmr_geo.json` (edition
metadata lives in `data/srmr.json`). Re-run it with `python3 scripts/fetch_srmr.py`.

`scripts/srmr_segments.py` then slices those real tracks at the major hubs into a
deduplicated segment library (`data/srmr_segments.json`) that feeds the master
map's "SRMR race segments" layer.

## Riding philosophy: *sleep low, ride high*

| Constraint | How it's handled |
|---|---|
| ~70–80 km/day, **max 100 km** | No day on any route exceeds 100 km; most are 60–90 km |
| Camp **low** | Lake & valley routes (1–5): every camp ≤ ~2066 m (bar two Jyrgalan nights ~2582 m). High-pass routes (6–10): camps stay low where possible but include some high nights (e.g. Song-Köl ~3050 m) — flagged on the site |
| Passes | Lake & valley routes stay under 3500 m. High-pass routes cross the classics: Kegety ~3783 m, Shamsy ~3562 m, Kök-Ayryk ~3350 m, Kalmak-Ashuu into Song-Köl — all under the 4000 m ceiling |
| Avoid long tunnels & the Boom Gorge road | No route touches the dangerous Töö-Ashuu tunnel. Route 7 deliberately links Issyk-Köl to Bishkek over the Kök-Ayryk pass instead of the busy Tokmok–Balykchy (Boom Gorge) highway |
| Avoid military / permit zones | We turn back below the Kumtor mine (Barskoon) and stay clear of the Torugart border and Kel-Suu permit areas |
| Minimise busy roads; flag resupply | High-pass routes are gravel-first (BRouter `trekking`); tarmac (`car-fast`) is used only for unavoidable approach corridors. Resupply towns are flagged on every map and day card |

## The routes

**Lake & valley routes** — low camps, no pass over 3500 m:

| # | Route | Start → End | Days | Distance | Climb | Highest | Highest camp |
|---|---|---|---|---|---|---|---|
| 1 | **Grand Traverse** | Bishkek → Karakol | 10 | 773 km | 10,785 m | 3472 m | 2066 m |
| 2 | **Issyk-Köl Full Loop** | Balykchy loop | 10 | 725 km | 8,859 m | 3472 m | 2066 m |
| 3 | **Eastern Wild: Karakol & Jyrgalan** | Karakol loop | 10 | 737 km | 7,439 m | 2786 m | 2582 m |
| 4 | **Kochkor & Naryn Highlands** | Balykchy loop | 10 | 677 km | 7,499 m | 3026 m | 2318 m |
| 5 | **Chong-Kemin & North Shore** | Bishkek → Karakol | 10 | 683 km | 5,855 m | 2492 m | 1966 m |

**High-pass routes** — remote, gravel-first, some high camps:

| # | Route | Start → End | Days | Distance | Climb | Highest | Highest camp |
|---|---|---|---|---|---|---|---|
| 6 | **Kegety Pass Traverse** | Balykchy → Bishkek | 9 | 624 km | 8,252 m | **3783 m** (Kegety) | 3081 m (Song-Köl) |
| 7 | **Kök-Ayryk Wild Traverse** | Karakol → Bishkek | 10 | 592 km | 7,733 m | 3348 m (Kök-Ayryk) | 3000 m |
| 8 | **Song-Köl High Loop** | Kochkor loop | 6 | 401 km | 5,727 m | 3542 m | 3081 m (Song-Köl) |
| 9 | **Shamsy–Kegety Double Pass** | Bishkek loop | 7 | 476 km | 9,582 m | **3783 m** (Kegety) | 2445 m |
| 10 | **Naryn Backcountry** | Kochkor loop | 10 | 609 km | 9,475 m | 3026 m (Dolon) | 2755 m |

**Expert straight-line traverses** — point-to-point, up to 3 days between resupplies:

| # | Route | Start → End | Days | Distance | Highest | Highest camp |
|---|---|---|---|---|---|---|
| 11 | **Central Massif Traverse** | At-Bashy → Bishkek | 6 | 451 km | **3783 m (Kegety)** | 3043 m (Song-Köl) |
| 12 | **Kök-Ayryk Express** | Karakol → Bishkek | 6 | 460 km | 3348 m (Kök-Ayryk) | 3000 m |
| 13 | **Southern Silk Line** | Balykchy → Tash-Rabat | 6 | 418 km | 3077 m | 3077 m (Tash-Rabat) |
| 14 | **Grand Traverse XL** | Karakol → Bishkek | 10 | 706 km | **3783 m (Kegety)** | 3043 m (Song-Köl) |
| 15 | **Song-Köl Skyline** | Balykchy → At-Bashy | 6 | 358 km | 3542 m | 3043 m (Song-Köl) |

Route 5 is the gentlest; Route 14 is the biggest expedition (coast-to-capital);
Routes 6, 11 & 14 tackle the Kegety Pass; Routes 7 & 12 link Issyk-Köl to Bishkek
without touching the Boom Gorge.

## Route planner

A **Route planner** page lets you build your own line:

- **Click the map** to drop points — it routes between them live via the BRouter
  web API (a "Gravel / mixed" or "Road" profile), returning real road/trail
  geometry with elevation.
- **Add ready-made segments** — the hand-made connectors and the real SRMR race
  sections — from a list; it auto-connects them to your current end point.
- A running **total distance + climbing** and a combined **elevation profile**
  (on top of the map) update as you build; **hovering the profile shows the spot
  on the map**. Undo / Clear as you go.
- **Download the result as GPX**, and **upload a saved `.gpx`** back in to view or
  keep editing it.
- Segments are **toggles** (click again to remove) and are auto-oriented, so a
  segment is reversed if its far end is nearer your current route end.

No API key or backend needed — routing is done client-side against BRouter.

## Master planning map

The **Master map** page overlays everything and lets you build your own line:

- **Mountain passes** — 12 of them, as triangle markers coloured by height.
  **Eight have real climb profiles**: five routed via BRouter (Kalmak-Ashuu,
  Kegety, Shamsy, Kök-Ayryk, Dolon) and three (Tosor, Barskoon, Juuku) recovered
  from the real SRMR tracks by `scripts/enrich_passes.py`. The remaining four
  (Chong-Ashuu, Moldo-Ashuu, Kyzart, San-Tash) are reference markers, since no
  race passes near them. Each pass also lists the **routes that cross it**.
- **Clicking any pass or segment** draws its exact geometry on the map (a
  highlighted casing line) and shows the matching **elevation profile**.
- The map sits full-width at the bottom of the page with a **fullscreen** button,
  and every layer (routes, passes, segments, SRMR segments, resupply + trains)
  can be toggled.
- **Segments** — ~16 reusable connectors between the hubs (each with distance,
  climb, surface and profile) so you can mix and match your own route.
- **SRMR race segments** — a library of real hub-to-hub sections cut from the
  actual Silk Road Mountain Race tracks (deduplicated by hub pair, tagged with the
  year they're from), each with its real elevation profile. Its own toggle layer.
- **Resupply towns** and **train stops** (the Bishkek–Balykchy line through the
  Boom Gorge + Chui-plain stations).
- Toggle any layer on/off.

## Run the website

It's a static site — just serve the folder over HTTP (needed so the browser can
`fetch()` the data):

```bash
cd tour-de-kyrgyzstan
python3 -m http.server 8770
# open http://localhost:8770
```

### What you get
- **Route cards** (three families) → a **per-route view**: day-coloured track,
  an **elevation profile that syncs with the map on hover**, summary stats, a
  **GPX download**, and a day-by-day breakdown (distance/climb/high point, the
  night's camp + altitude, resupply towns). Click a day to isolate it.
- The **Master map**, the **Silk Road Mountain Race** editions page, and the
  **Route planner** (see above). CyclOSM is the default base layer, with Terrain,
  Satellite, Esri Topo, a light map and plain OSM selectable on every map.

## Deploy to GitHub Pages

It's a fully static site (HTML/CSS/JS + pre-generated `data/`), so no build step
is required:

1. Push the repo to GitHub.
2. **Settings → Pages → Build and deployment → Source: "Deploy from a branch"**,
   pick your branch (e.g. `main`) and the **`/ (root)`** folder.
3. The site publishes at `https://<user>.github.io/<repo>/`.

A `.nojekyll` file is included so GitHub serves the files as-is (no Jekyll). All
asset/data references are **relative**, so it works from a project subpath. The
route planner calls the public BRouter API over HTTPS (CORS-enabled), and map
tiles/libraries load from HTTPS CDNs — no API keys or backend needed. The Python
scripts in `scripts/` are only used to (re)generate `data/` and are not needed to
serve the site.

## Regenerate the routes

Route geometry and elevation are produced by snapping waypoints to real roads/tracks
with the open-source [BRouter](https://brouter.de) engine (real SRTM elevation).

```bash
python3 scripts/generate_routes.py
```

This writes:
- `data/routes.json` — metadata, per-day stats, markers, light overview polylines
- `data/geo/<id>.json` — display geometry (per-day lat/lon/elevation) for the site
- `data/gpx/<id>.gpx` — downloadable GPX (one track segment per day + waypoints)
- `data/passes.json`, `data/segments.json`, `data/pois.json` — the master-map data
  (passes with auto-found summits + profiles, connector segments, resupply + trains)

Edit the routes in **`scripts/routes_def.py`** and the master-map data (passes,
segments, train stops) in **`scripts/master_data.py`**. Each day is a list of *legs*; a leg
is either a `road(...)` transfer (`car-fast` profile → real roads), a `gravel(...)`
one-way track, or a there-and-back `spur(...)` gorge climb (`trekking` profile).
Responses are cached in `scripts/.brouter_cache/`, so re-runs are fast.

The Silk Road Mountain Race data has its own pipeline (run in order):
`scripts/fetch_srmr.py` (real tracks → `data/srmr_geo.json`) →
`scripts/srmr_segments.py` (hub-to-hub segment library → `data/srmr_segments.json`) →
`scripts/enrich_passes.py` (fills reference-pass profiles from the real tracks).

## Tech
- [Leaflet](https://leafletjs.com/) + OpenTopoMap / OpenStreetMap tiles
- [Chart.js](https://www.chartjs.org/) for the elevation profile
- [BRouter](https://brouter.de) for routing + elevation (build step only)
- No framework, no build step — plain HTML/CSS/JS

## ⚠️ Disclaimer
These are planning aids generated from open data and have **not been ridden or
field-verified**. Mountain conditions change fast — carry proper maps, check the
weather and seasonal road status, confirm current permit/border rules, treat your
water, and ride within your limits.
