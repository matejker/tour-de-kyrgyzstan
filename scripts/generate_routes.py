# -*- coding: utf-8 -*-
"""
Fetch road-snapped tracks with real elevation from the public BRouter web API,
compute per-day and per-route statistics, and emit:

    data/routes.json        -> metadata + daily breakdown + markers for the site
    data/gpx/<id>.gpx       -> one GPX per route (a <trkseg> per day, plus waypoints)

Run:  python3 scripts/generate_routes.py
"""

import json
import math
import os
import time
import urllib.parse
import urllib.request

from routes_def import ROUTES
from master_data import PASSES_ROUTED, PASSES_REF, SEGMENTS, TRAIN_STOPS

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
GPXDIR = os.path.join(DATA, "gpx")
CACHE = os.path.join(HERE, ".brouter_cache")

ROAD = "car-fast"              # follows real main/secondary roads (realistic distance)
GRAVEL = "trekking"            # routes onto gravel tracks / gorge roads
MIN_SPACING_M = 25.0           # downsample tracks to ~1 point / 25 m
EARTH_R = 6371000.0


def haversine(a, b):
    lon1, lat1 = math.radians(a[0]), math.radians(a[1])
    lon2, lat2 = math.radians(b[0]), math.radians(b[1])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_R * math.asin(math.sqrt(h))


def fetch_brouter(pts, profile=ROAD):
    """Return list of [lon, lat, ele] for a chain of [lon,lat] control points."""
    lonlats = "|".join(f"{p[0]:.6f},{p[1]:.6f}" for p in pts)
    key = lonlats + "|" + profile
    os.makedirs(CACHE, exist_ok=True)
    cpath = os.path.join(CACHE, str(abs(hash(key))) + ".json")
    if os.path.exists(cpath):
        with open(cpath) as f:
            data = json.load(f)
    else:
        url = "https://brouter.de/brouter?" + urllib.parse.urlencode({
            "lonlats": lonlats,
            "profile": profile,
            "alternativeidx": 0,
            "format": "geojson",
        })
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=60) as resp:
                    data = json.loads(resp.read().decode())
                break
            except Exception as e:  # noqa: BLE001
                if attempt == 3:
                    raise
                print(f"   retry {attempt+1} after error: {e}")
                time.sleep(3)
        with open(cpath, "w") as f:
            json.dump(data, f)
        time.sleep(0.8)  # be polite to the public server
    return data["features"][0]["geometry"]["coordinates"]


def fetch_day(day):
    """A day is a list of legs. Each leg: {pts, profile?, out_back?}.
    Returns the concatenated [lon,lat,ele] track for the whole day."""
    coords = []
    for leg in day["legs"]:
        seg = fetch_brouter(leg["pts"], leg.get("profile", ROAD))
        if leg.get("out_back"):
            seg = seg + list(reversed(seg))[1:]
        if coords and seg and coords[-1][:2] == seg[0][:2]:
            seg = seg[1:]
        coords.extend(seg)
    return coords


def downsample(coords, min_spacing=MIN_SPACING_M):
    if not coords:
        return coords
    out = [coords[0]]
    acc = 0.0
    for i in range(1, len(coords)):
        acc += haversine(coords[i - 1], coords[i])
        if acc >= min_spacing:
            out.append(coords[i])
            acc = 0.0
    if out[-1] != coords[-1]:
        out.append(coords[-1])
    return out


def downsample_count(coords, max_pts):
    """Evenly thin a coordinate list down to at most max_pts points."""
    if len(coords) <= max_pts:
        return coords
    step = len(coords) / float(max_pts)
    out = [coords[int(i * step)] for i in range(max_pts)]
    if out[-1] != coords[-1]:
        out.append(coords[-1])
    return out


def stats_for(coords):
    """distance(km), ascent(m), descent(m), min_ele, max_ele, start_ele, end_ele"""
    dist = 0.0
    asc = 0.0
    desc = 0.0
    eles = [c[2] for c in coords]
    # smooth elevation a little to avoid noise inflating ascent
    sm = eles[:]
    for i in range(1, len(eles) - 1):
        sm[i] = (eles[i - 1] + eles[i] + eles[i + 1]) / 3.0
    for i in range(1, len(coords)):
        dist += haversine(coords[i - 1], coords[i])
        de = sm[i] - sm[i - 1]
        if de > 0:
            asc += de
        else:
            desc += -de
    return {
        "distance_km": round(dist / 1000.0, 1),
        "ascent_m": int(round(asc)),
        "descent_m": int(round(desc)),
        "min_ele": int(round(min(eles))),
        "max_ele": int(round(max(eles))),
        "start_ele": int(round(eles[0])),
        "end_ele": int(round(eles[-1])),
    }


GEODIR = os.path.join(DATA, "geo")


def main():
    os.makedirs(GPXDIR, exist_ok=True)
    os.makedirs(GEODIR, exist_ok=True)
    out_routes = []
    route_geoms = {}

    for route in ROUTES:
        print(f"\n=== {route['name']} ===")
        day_records = []
        all_segments = []  # list of coord-lists, one per day
        r_dist = r_asc = r_desc = 0.0
        r_min = 99999
        r_max = -99999
        max_camp = 0

        for di, day in enumerate(route["days"], start=1):
            coords = downsample(fetch_day(day))
            st = stats_for(coords)
            all_segments.append(coords)
            r_dist += st["distance_km"]
            r_asc += st["ascent_m"]
            r_desc += st["descent_m"]
            r_min = min(r_min, st["min_ele"])
            r_max = max(r_max, st["max_ele"])
            max_camp = max(max_camp, st["end_ele"])
            print(f"  Day {di:2d} {day['name'][:34]:34s} "
                  f"{st['distance_km']:5.1f} km  +{st['ascent_m']:5d} m  "
                  f"max {st['max_ele']:4d}  camp {st['end_ele']:4d}")
            day_records.append({
                "day": di,
                "name": day["name"],
                "desc": day["desc"],
                "camp": day["end_label"],
                "resupply": [{"name": r[0], "lon": r[1], "lat": r[2]} for r in day["resupply"]],
                **st,
            })

        # display geometry: per-day tracks (lat,lon,ele) for the elevation/map view
        geo_days = []
        lats, lons = [], []
        for di, seg in enumerate(all_segments, start=1):
            disp = downsample_count(downsample(seg, 45.0), 900)
            coords = [[round(c[1], 5), round(c[0], 5), round(c[2], 1)] for c in disp]
            geo_days.append({"day": di, "name": route["days"][di - 1]["name"], "coords": coords})
            lats += [c[0] for c in coords]
            lons += [c[1] for c in coords]
        bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
        with open(os.path.join(GEODIR, f"{route['id']}.json"), "w") as f:
            json.dump({"id": route["id"], "color": route["color"],
                       "bounds": bounds, "days": geo_days}, f)

        # light overview polyline for the landing map
        flat = [c for seg in all_segments for c in seg]
        overview = [[round(c[1], 4), round(c[0], 4)]
                    for c in downsample_count(flat, 260)]
        # coarse geometry ([lon,lat]) for pass-proximity checks
        route_geoms[route["id"]] = [[c[0], c[1]] for c in downsample_count(flat, 500)]

        route_rec = {
            "id": route["id"],
            "name": route["name"],
            "subtitle": route["subtitle"],
            "start": route["start"],
            "color": route["color"],
            "remote": route.get("remote", False),
            "expert": route.get("expert", False),
            "blurb": route["blurb"],
            "gpx": f"data/gpx/{route['id']}.gpx",
            "geo": f"data/geo/{route['id']}.json",
            "total_distance_km": round(r_dist, 1),
            "total_ascent_m": int(round(r_asc)),
            "total_descent_m": int(round(r_desc)),
            "min_ele": r_min,
            "max_ele": r_max,
            "max_camp_ele": max_camp,
            "num_days": len(route["days"]),
            "bounds": bounds,
            "overview": overview,
            "days": day_records,
        }
        out_routes.append(route_rec)
        write_gpx(route, all_segments)
        print(f"  TOTAL {route_rec['total_distance_km']} km  "
              f"+{route_rec['total_ascent_m']} m  highest {r_max} m  "
              f"highest camp {max_camp} m")

    with open(os.path.join(DATA, "routes.json"), "w") as f:
        json.dump({"routes": out_routes}, f, ensure_ascii=False, indent=1)
    print(f"\nWrote {os.path.join(DATA, 'routes.json')}")

    build_master(out_routes, route_geoms)


def profile_of(coords, max_pts=140):
    """[[cum_km, ele], ...] from [lon,lat,ele] coords, downsampled."""
    pts = []
    km = 0.0
    for i, c in enumerate(coords):
        if i:
            km += haversine(coords[i - 1], c) / 1000.0
        pts.append([round(km, 2), round(c[2], 1)])
    return downsample_count(pts, max_pts)


def routes_near(lon, lat, route_geoms, out_routes, radius_m=3000):
    """Which routes pass within radius_m of a point."""
    meta = {r["id"]: r for r in out_routes}
    hits = []
    for rid, geom in route_geoms.items():
        d = min(haversine([lon, lat], pt) for pt in geom)
        if d <= radius_m:
            r = meta[rid]
            hits.append({"id": rid, "name": r["name"], "color": r["color"], "dist_m": int(d)})
    hits.sort(key=lambda h: h["dist_m"])
    return [{"id": h["id"], "name": h["name"], "color": h["color"]} for h in hits]


def build_master(out_routes, route_geoms):
    print("\n=== Master map data ===")
    # ---- passes ----
    passes = []
    for p in PASSES_ROUTED:
        coords = downsample(fetch_brouter([p["base"], p["over"]], GRAVEL))
        # summit = highest point along the crossing
        si = max(range(len(coords)), key=lambda i: coords[i][2])
        summit = coords[si]
        climb = coords[: si + 1]
        st = stats_for(climb)
        prof = profile_of(coords)  # full crossing, so the pass shape shows
        summit_km = profile_of(climb, 10000)[-1][0] if len(climb) > 1 else 0
        rts = routes_near(summit[0], summit[1], route_geoms, out_routes)
        passes.append({
            "name": p["name"], "side": p["side"],
            "lat": round(summit[1], 5), "lon": round(summit[0], 5),
            "ele": int(round(summit[2])),
            "climb_km": st["distance_km"], "climb_ascent": st["ascent_m"],
            "avg_grade": round(st["ascent_m"] / (st["distance_km"] * 10.0), 1) if st["distance_km"] else 0,
            "summit_km": round(summit_km, 1),
            "routable": True, "profile": prof, "routes": rts,
            "coords": [[round(c[1], 5), round(c[0], 5)] for c in downsample_count(coords, 200)],
        })
        print(f"  pass {p['name'][:26]:26s} summit {int(summit[2]):4d} m  "
              f"climb {st['distance_km']:.1f} km +{st['ascent_m']} m  "
              f"routes: {', '.join(r['id'] for r in rts) or '—'}")
    for p in PASSES_REF:
        passes.append({
            "name": p["name"], "side": p["side"],
            "routes": routes_near(p["at"][0], p["at"][1], route_geoms, out_routes),
            "lat": p["at"][1], "lon": p["at"][0], "ele": p["ele"],
            "routable": False, "profile": None,
        })
    with open(os.path.join(DATA, "passes.json"), "w") as f:
        json.dump({"passes": passes}, f, ensure_ascii=False, indent=1)

    # ---- segments ----
    segs = []
    for s in SEGMENTS:
        prof = GRAVEL if s["cat"] in ("gravel", "pass") else ROAD
        coords = downsample(fetch_brouter(s["pts"], prof))
        st = stats_for(coords)
        geo = [[round(c[1], 5), round(c[0], 5)] for c in downsample_count(coords, 200)]
        segs.append({
            "name": s["name"], "cat": s["cat"],
            "distance_km": st["distance_km"], "ascent_m": st["ascent_m"],
            "max_ele": st["max_ele"], "min_ele": st["min_ele"],
            "coords": geo, "profile": profile_of(coords),
        })
        print(f"  seg  {s['name'][:34]:34s} {st['distance_km']:6.1f} km  +{st['ascent_m']} m")
    with open(os.path.join(DATA, "segments.json"), "w") as f:
        json.dump({"segments": segs}, f, ensure_ascii=False, indent=1)

    # ---- POIs: resupply (aggregated from all routes) + train stops ----
    seen = {}
    for r in out_routes:
        for d in r["days"]:
            for s in d.get("resupply", []):
                key = (round(s["lon"], 2), round(s["lat"], 2))
                if key not in seen:
                    seen[key] = {"name": s["name"], "lon": s["lon"], "lat": s["lat"]}
    resupply = list(seen.values())
    with open(os.path.join(DATA, "pois.json"), "w") as f:
        json.dump({"resupply": resupply, "trains": TRAIN_STOPS}, f, ensure_ascii=False, indent=1)
    print(f"  {len(passes)} passes, {len(segs)} segments, "
          f"{len(resupply)} resupply, {len(TRAIN_STOPS)} train stops")


def write_gpx(route, segments):
    esc = lambda s: (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="tour-de-kyrgyzstan" '
        'xmlns="http://www.topografix.com/GPX/1/1">',
        f"  <metadata><name>{esc(route['name'])}</name></metadata>",
    ]
    # waypoints: camp at each day end + resupply towns (deduped)
    seen = set()
    for day, seg in zip(route["days"], segments):
        end = seg[-1]
        cname = f"Camp Day {route['days'].index(day)+1}: {day['end_label']}"
        lines.append(
            f'  <wpt lat="{end[1]:.6f}" lon="{end[0]:.6f}">'
            f'<ele>{end[2]:.0f}</ele><name>{esc(day["end_label"])}</name>'
            f'<sym>Campground</sym><type>camp</type></wpt>')
        for r in day["resupply"]:
            k = (round(r[1], 3), round(r[2], 3))
            if k in seen:
                continue
            seen.add(k)
            lines.append(
                f'  <wpt lat="{r[2]:.6f}" lon="{r[1]:.6f}">'
                f'<name>{esc(r[0])}</name><sym>Shopping Center</sym>'
                f'<type>resupply</type></wpt>')
    # one track, one segment per day
    lines.append(f"  <trk><name>{esc(route['name'])}</name>")
    for seg in segments:
        lines.append("    <trkseg>")
        for c in seg:
            lines.append(
                f'      <trkpt lat="{c[1]:.6f}" lon="{c[0]:.6f}">'
                f'<ele>{c[2]:.1f}</ele></trkpt>')
        lines.append("    </trkseg>")
    lines.append("  </trk>")
    lines.append("</gpx>")
    path = os.path.join(GPXDIR, f"{route['id']}.gpx")
    with open(path, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
