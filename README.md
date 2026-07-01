# Tour de Kyrgyzstan

A static website for planning bikepacking trips in Kyrgyzstan. Interactive maps
and elevation profiles (Leaflet + Chart.js), no backend or build step.

## Pages

- **Routes** — 8 curated routes plus any GPX routes you import, each with a
  day-by-day map, elevation profile, stats and GPX download.
- **Master map** — all routes overlaid with toggleable layers: mountain passes
  (with climb profiles), connector segments, SRMR race segments, resupply
  towns/villages, train stops, and border-permit zones.
- **Silk Road Mountain Race** — real GPS tracks of the 2019–2026 editions with a
  comparison chart and per-edition profiles.
- **Planner** — click the map to route between points (BRouter), append ready-made
  segments, see live distance/climb and elevation, and import/export GPX.

## Run

Serve the folder over HTTP (so the browser can `fetch()` the data):

```bash
python3 -m http.server 8770   # then open http://localhost:8770
```

## Deploy

Static site — push to GitHub and enable Pages ("Deploy from a branch", root
folder). `.nojekyll` is included and all paths are relative, so it works from a
subpath. Map tiles and the BRouter routing API are loaded over HTTPS; no keys.

## Data scripts (`scripts/`)

Only needed to regenerate `data/`; the site serves fine without them.

| Script | Output |
|---|---|
| `generate_routes.py` | Routes from `routes_def.py` → `routes.json`, `geo/`, `gpx/`, passes, connector segments, POIs (via BRouter) |
| `fetch_srmr.py` | Real SRMR tracks → `srmr_geo.json` |
| `srmr_segments.py` | Splits SRMR tracks at crossroads/endpoints → `srmr_segments.json` |
| `enrich_passes.py` | Fills reference-pass profiles from SRMR tracks |
| `fetch_resupply.py` | Towns/villages from OpenStreetMap → `resupply.json` |
| `build_permits.py` | Border-permit polygons from national borders → `permits.json` |
| `add_route.py` | Imports a GPX as a route (10 days) → `custom_routes.json` |

Add your own route:

```bash
python3 scripts/add_route.py my-ride.gpx --name "My Route"
```

## Disclaimer

Planning aids generated from open data, not field-verified. Carry proper maps,
check weather and road/permit status, and ride within your limits.
