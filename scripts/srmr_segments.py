# -*- coding: utf-8 -*-
"""
Derive a reusable *segment library* from the real Silk Road Mountain Race tracks.

Each edition's genuine GPS track is split at the major hubs it passes (towns and
well-known points). Every hub-to-hub piece becomes a named segment with real
geometry and an elevation profile. Segments are de-duplicated by hub pair, keeping
the most recent edition that rides them.

Output: data/srmr_segments.json
"""
import json
import math
import os

from fetch_srmr import (SOURCES, fetch_rwgps, fetch_komoot_tour,
                        fetch_komoot_collection, haversine)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")

# major hubs the races pass through (name, lat, lon)
HUBS = [
    ("Bishkek", 42.87, 74.61), ("Tokmok", 42.83, 75.30), ("Kegety", 42.68, 75.05),
    ("Balykchy", 42.46, 76.19), ("Cholpon-Ata", 42.65, 77.08), ("Karakol", 42.49, 78.39),
    ("Enilchek", 42.12, 79.35), ("Saruu", 42.30, 77.92), ("Barskoon", 42.15, 77.61),
    ("Kochkor", 42.21, 75.75), ("Song-Köl", 41.83, 75.13), ("Chaek", 41.92, 74.99),
    ("Naryn", 41.43, 76.00), ("At-Bashy", 41.17, 75.80), ("Kel-Suu", 40.66, 76.35),
    ("Baetov", 41.16, 75.44), ("Kazarman", 41.42, 74.05), ("Jalal-Abad", 40.93, 72.98),
    ("Osh", 40.53, 72.80), ("Talas", 42.52, 72.24),
]
HIT_M = 9000        # a hub is "on the route" if the track passes within this
MIN_SEG_KM = 18     # ignore tiny slivers
MAX_SEG_KM = 380    # ignore absurdly long (mis-detected) pieces


def nearest_index(coords, lat, lon):
    best_i, best_d = -1, 1e18
    for i in range(0, len(coords), 3):
        d = haversine([coords[i][0], coords[i][1]], [lat, lon])
        if d < best_d:
            best_d, best_i = d, i
    return best_i, best_d


def seg_stats(sub):
    dist = asc = 0.0
    eles = [c[2] for c in sub]
    sm = eles[:]
    for i in range(1, len(eles) - 1):
        sm[i] = (eles[i - 1] + eles[i] + eles[i + 1]) / 3.0
    for i in range(1, len(sub)):
        dist += haversine(sub[i - 1], sub[i])
        de = sm[i] - sm[i - 1]
        if de > 0:
            asc += de
    return dist / 1000.0, asc, min(eles), max(eles)


def downsample(coords, min_spacing=120.0):
    out = [coords[0]]
    acc = 0.0
    for i in range(1, len(coords)):
        acc += haversine(coords[i - 1], coords[i])
        if acc >= min_spacing:
            out.append(coords[i]); acc = 0.0
    if out[-1] != coords[-1]:
        out.append(coords[-1])
    return out


def profile(sub, max_pts=180):
    pts, km = [], 0.0
    for i, c in enumerate(sub):
        if i:
            km += haversine(sub[i - 1], c) / 1000.0
        pts.append([round(km, 2), round(c[2], 1)])
    if len(pts) <= max_pts:
        return pts
    step = len(pts) / float(max_pts)
    out = [pts[int(i * step)] for i in range(max_pts)]
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


def main():
    kept = {}
    for s in SOURCES:
        try:
            if "rwgps" in s:
                coords, _ = fetch_rwgps(s["rwgps"])
            elif "komoot_tour" in s:
                coords, _ = fetch_komoot_tour(s["komoot_tour"])
            else:
                coords, _ = fetch_komoot_collection(s["komoot_collection"])
        except Exception as e:  # noqa: BLE001
            print(f"  {s['year']}: fetch error {e}"); continue
        if not coords or len(coords) < 50:
            continue

        # find hubs on this track, in track order
        hits = []
        for name, lat, lon in HUBS:
            idx, d = nearest_index(coords, lat, lon)
            if d <= HIT_M:
                hits.append((idx, name))
        hits.sort()
        # drop consecutive duplicates
        dedup = []
        for h in hits:
            if not dedup or dedup[-1][1] != h[1]:
                dedup.append(h)

        for (i0, a), (i1, b) in zip(dedup, dedup[1:]):
            sub = coords[i0:i1 + 1]
            if len(sub) < 6:
                continue
            dist, asc, mn, mx = seg_stats(sub)
            if dist < MIN_SEG_KM or dist > MAX_SEG_KM:
                continue
            key = frozenset((a, b))
            rec = {
                "name": f"{a} → {b}", "from": a, "to": b,
                "year": s["year"], "color": s["color"],
                "distance_km": round(dist, 1), "ascent_m": int(round(asc)),
                "min_ele": int(round(mn)), "max_ele": int(round(mx)),
                "coords": [[round(c[0], 5), round(c[1], 5)] for c in downsample(sub)],
                "profile": profile(sub),
            }
            kept[key] = rec  # SOURCES ascending → most recent edition wins
        print(f"  {s['year']}: {len(dedup)} hubs on route")

    segs = sorted(kept.values(), key=lambda r: (-r["distance_km"]))
    with open(os.path.join(DATA, "srmr_segments.json"), "w") as f:
        json.dump({"segments": segs}, f)
    print(f"Wrote {len(segs)} unique SRMR segments")
    for r in segs:
        print(f"   {r['name']:26s} {r['distance_km']:6.1f} km  +{r['ascent_m']:5d} m  "
              f"max {r['max_ele']:4d}  (SRMR {r['year']})")


if __name__ == "__main__":
    main()
