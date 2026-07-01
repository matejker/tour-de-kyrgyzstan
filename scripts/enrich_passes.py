# -*- coding: utf-8 -*-
"""
Fill in elevation profiles for the reference-only passes (Tosor, Barskoon, Juuku,
Chong-Ashuu, Moldo-Ashuu, Kyzart, San-Tash …) using the *real* Silk Road Mountain
Race tracks, which actually cross most of them.

For each pass without a profile we find the SRMR track that passes closest to it,
snap the pass to the real high point nearby, and cut a window of the track around
the summit → a genuine climb profile + geometry for the map.

Run after `generate_routes.py`:  python3 scripts/enrich_passes.py
"""
import json
import math
import os

from fetch_srmr import (SOURCES, fetch_rwgps, fetch_komoot_tour,
                        fetch_komoot_collection, haversine)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
NEAR_M = 7000       # pass must lie within this of an SRMR track to enrich
HALF_KM = 15.0      # half-window either side of the summit


def load_tracks():
    tracks = []
    for s in SOURCES:
        try:
            if "rwgps" in s:
                c, _ = fetch_rwgps(s["rwgps"])
            elif "komoot_tour" in s:
                c, _ = fetch_komoot_tour(s["komoot_tour"])
            else:
                c, _ = fetch_komoot_collection(s["komoot_collection"])
            if c and len(c) > 50:
                tracks.append((s["year"], c))
        except Exception as e:  # noqa: BLE001
            print(f"  {s['year']}: fetch error {e}")
    return tracks


def nearest(track, lat, lon):
    bi, bd = -1, 1e18
    for i in range(0, len(track), 2):
        d = haversine([track[i][0], track[i][1]], [lat, lon])
        if d < bd:
            bd, bi = d, i
    return bi, bd


def window(track, ci):
    i = ci
    d = 0.0
    while i > 0 and d < HALF_KM * 1000:
        d += haversine(track[i - 1], track[i]); i -= 1
    j = ci
    d = 0.0
    while j < len(track) - 1 and d < HALF_KM * 1000:
        d += haversine(track[j], track[j + 1]); j += 1
    return track[i:j + 1]


def profile_and_coords(sub):
    pts, km = [], 0.0
    for k, c in enumerate(sub):
        if k:
            km += haversine(sub[k - 1], c) / 1000.0
        pts.append([round(km, 2), round(c[2], 1)])
    if len(pts) > 180:
        step = len(pts) / 180.0
        pts = [pts[int(i * step)] for i in range(180)] + [pts[-1]]
    coords = [[round(c[0], 5), round(c[1], 5)] for c in sub]
    if len(coords) > 200:
        step = len(coords) / 200.0
        coords = [coords[int(i * step)] for i in range(200)] + [coords[-1]]
    return pts, coords


def main():
    path = os.path.join(DATA, "passes.json")
    passes = json.load(open(path))["passes"]
    tracks = load_tracks()

    enriched = 0
    for p in passes:
        if p.get("profile"):
            continue  # already has one (routable passes)
        best = None
        for year, tr in tracks:
            ci, d = nearest(tr, p["lat"], p["lon"])
            if d < NEAR_M and (best is None or d < best[2]):
                best = (year, tr, d, ci)
        # diagnostic: closest of any track
        allnear = min((nearest(tr, p["lat"], p["lon"])[1] for _, tr in tracks), default=1e18)
        if not best:
            print(f"  {p['name']}: nearest SRMR track {int(allnear)} m (> {NEAR_M}) — left as marker")
            continue
        year, tr, d, ci = best
        sub = window(tr, ci)
        # snap the pass to the real high point in the window
        si = max(range(len(sub)), key=lambda i: sub[i][2])
        prof, coords = profile_and_coords(sub)
        p["ele"] = int(round(sub[si][2]))
        p["lat"] = round(sub[si][0], 5)
        p["lon"] = round(sub[si][1], 5)
        p["profile"] = prof
        p["coords"] = coords
        p["source"] = f"SRMR {year}"
        enriched += 1
        print(f"  {p['name']:22s} ← SRMR {year} (within {int(d)} m)  summit {p['ele']} m")

    json.dump({"passes": passes}, open(path, "w"), ensure_ascii=False, indent=1)
    print(f"Enriched {enriched} passes; wrote {path}")


if __name__ == "__main__":
    main()
