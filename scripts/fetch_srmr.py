# -*- coding: utf-8 -*-
"""
Pull the *real* Silk Road Mountain Race tracks and write data/srmr_geo.json.

Sources (all fetchable without a login):
  - Ride with GPS public route JSON:      https://ridewithgps.com/routes/<id>.json
  - komoot single tour coordinates:       https://api.komoot.de/v007/tours/<id>/coordinates
  - komoot collection stage geometry:     https://api.komoot.de/v007/collections/<id>/compilation_lines_extended/

Output per edition: downsampled [lat,lon,ele] track, an elevation profile
([[cum_km, ele]]) and computed distance / ascent.
"""
import json
import math
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
R = 6371000.0

SOURCES = [
    {"year": 2019, "color": "#e6194B", "komoot_collection": "887966"},
    {"year": 2021, "color": "#f58231", "komoot_collection": "896205"},
    {"year": 2022, "color": "#3cb44b", "komoot_tour": "625327436"},
    {"year": 2023, "color": "#e8442b", "komoot_collection": "1883607"},
    {"year": 2024, "color": "#4363d8", "komoot_collection": "3118292"},
    {"year": 2025, "color": "#911eb4", "rwgps": "51995776"},
    {"year": 2026, "color": "#0f766e", "rwgps": "53318000"},
]

UA = {"User-Agent": "Mozilla/5.0 (tour-de-kyrgyzstan route viewer)"}


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def haversine(a, b):
    la1, lo1, la2, lo2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def downsample(coords, min_spacing=120.0):
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


def fetch_rwgps(rid):
    d = get_json(f"https://ridewithgps.com/routes/{rid}.json")
    tp = d.get("track_points") or d.get("route", {}).get("track_points")
    coords = [[p["y"], p["x"], p.get("e", 0.0)] for p in tp if "x" in p and "y" in p]
    return coords, d.get("name")


def fetch_komoot_tour(tid):
    d = get_json(f"https://api.komoot.de/v007/tours/{tid}/coordinates")
    its = d.get("items") or d.get("_embedded", {}).get("items")
    return [[p["lat"], p["lng"], p.get("alt", 0.0)] for p in its], None


def fetch_komoot_collection(cid):
    d = get_json(f"https://api.komoot.de/v007/collections/{cid}/compilation_lines_extended/?hl=en")
    items = d.get("_embedded", {}).get("items", [])
    coords = []
    for it in items:
        for p in it.get("geometry", []):
            coords.append([p["lat"], p["lng"], p.get("alt", 0.0)])
    return coords, None


def stats(coords):
    dist = asc = 0.0
    eles = [c[2] for c in coords]
    sm = eles[:]
    for i in range(1, len(eles) - 1):
        sm[i] = (eles[i - 1] + eles[i] + eles[i + 1]) / 3.0
    for i in range(1, len(coords)):
        dist += haversine(coords[i - 1], coords[i])
        de = sm[i] - sm[i - 1]
        if de > 0:
            asc += de
    return dist / 1000.0, asc


def profile(coords, max_pts=400):
    pts, km = [], 0.0
    for i, c in enumerate(coords):
        if i:
            km += haversine(coords[i - 1], c) / 1000.0
        pts.append([round(km, 2), round(c[2], 1)])
    if len(pts) <= max_pts:
        return pts
    step = len(pts) / float(max_pts)
    out = [pts[int(i * step)] for i in range(max_pts)]
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


def main():
    editions = []
    for s in SOURCES:
        try:
            if "rwgps" in s:
                coords, name = fetch_rwgps(s["rwgps"])
            elif "komoot_tour" in s:
                coords, name = fetch_komoot_tour(s["komoot_tour"])
            else:
                coords, name = fetch_komoot_collection(s["komoot_collection"])
            if not coords or len(coords) < 10:
                print(f"  {s['year']}: no track ({len(coords) if coords else 0} pts) — skipped")
                continue
            dist_km, asc = stats(coords)
            ds = downsample(coords)
            editions.append({
                "year": s["year"], "color": s["color"],
                "distance_km": round(dist_km, 1), "ascent_m": int(round(asc)),
                "start": [round(coords[0][0], 5), round(coords[0][1], 5)],
                "finish": [round(coords[-1][0], 5), round(coords[-1][1], 5)],
                "coords": [[round(c[0], 5), round(c[1], 5)] for c in ds],
                "profile": profile(coords),
            })
            print(f"  {s['year']}: {len(coords):6d} pts → {len(ds):4d}  "
                  f"{dist_km:6.0f} km  +{int(asc):6d} m")
        except Exception as e:  # noqa: BLE001
            print(f"  {s['year']}: ERROR {e}")
    with open(os.path.join(DATA, "srmr_geo.json"), "w") as f:
        json.dump({"editions": editions}, f)
    print(f"Wrote {os.path.join(DATA, 'srmr_geo.json')} ({len(editions)} editions)")


if __name__ == "__main__":
    main()
