# -*- coding: utf-8 -*-
"""
Derive a *segment library* from the real Silk Road Mountain Race tracks, where a
segment is any uninterrupted stretch of track between two "nodes". A node is
either an endpoint of a track OR a crossroad — a place where two (or more)
routes meet or cross.

How it works (graph edge extraction):
  1. Fetch every edition's real GPS track (lat/lon/ele) and thin it to ~120 m.
  2. Snap each point to a ~CELL_M grid cell.
  3. Build the merged graph over all editions: cells are nodes, consecutive
     cells are edges. A cell's degree = number of distinct neighbour cells.
  4. Node cells = cells with degree >= 3 (a real crossroad / junction) plus the
     first/last cell of every track (endpoints).
  5. Walk each track and cut it at every node cell. Each piece between two
     consecutive node cells is one segment.
  6. De-duplicate segments that different editions ride identically; the most
     recent edition wins. Each end is named after its nearest town/village.

Output: data/srmr_segments.json  (same schema the site already consumes)
"""
import json
import math
import os
from collections import defaultdict

from fetch_srmr import (SOURCES, fetch_rwgps, fetch_komoot_tour,
                        fetch_komoot_collection, haversine)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")

CELL_M = 700         # grid cell size for snapping / junction detection
MIN_SEG_KM = 30      # merge target: pieces grow to about this before a new break
NAME_MAX_M = 25000   # a node is named after a town only if one is this close
LAT0 = 42.0
DLAT = CELL_M / 111320.0
DLON = CELL_M / (111320.0 * math.cos(math.radians(LAT0)))


def cell_of(lat, lon):
    return (int(round(lat / DLAT)), int(round(lon / DLON)))


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


_CYR = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "ң": "ng", "ү": "u", "ө": "o", "і": "i", "қ": "k", "ғ": "g", "һ": "h", "ә": "a",
}


def translit(s):
    if not s:
        return s
    out = []
    for ch in s:
        low = ch.lower()
        if low in _CYR:
            rep = _CYR[low]
            out.append(rep.upper() if ch.isupper() and rep else rep)
        else:
            out.append(ch)
    return "".join(out)


def load_places():
    try:
        with open(os.path.join(DATA, "resupply.json")) as f:
            return json.load(f).get("places", [])
    except Exception:  # noqa: BLE001
        return []


def make_namer(places):
    def label(lat, lon):
        best, bd = None, 1e18
        for p in places:
            d = haversine([lat, lon], [p["lat"], p["lon"]])
            if d < bd:
                bd, best = d, p["name"]
        return translit(best) if bd <= NAME_MAX_M else None
    return label


def main():
    # 1) fetch + thin every edition
    tracks = []
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
        pts = downsample(coords, 120.0)
        cells = [cell_of(p[0], p[1]) for p in pts]
        tracks.append({"year": s["year"], "color": s["color"], "pts": pts, "cells": cells})
        print(f"  {s['year']}: {len(pts)} pts")

    # 2) merged graph over all editions
    neighbors = defaultdict(set)
    node_cells = set()
    for t in tracks:
        coll = [t["cells"][0]]
        for c in t["cells"][1:]:
            if c != coll[-1]:
                coll.append(c)
        node_cells.add(coll[0]); node_cells.add(coll[-1])   # endpoints
        for a, b in zip(coll, coll[1:]):
            neighbors[a].add(b); neighbors[b].add(a)
    for c, nb in neighbors.items():
        if len(nb) >= 3:                                    # crossroads
            node_cells.add(c)

    # representative point for every node cell (mean of all track points that
    # fall in it). Segment ends are welded to this so pieces meeting at a
    # crossroad share the exact same point -> no seam gaps between editions.
    acc = defaultdict(lambda: [0.0, 0.0, 0])
    for t in tracks:
        for p, c in zip(t["pts"], t["cells"]):
            if c in node_cells:
                acc[c][0] += p[0]; acc[c][1] += p[1]; acc[c][2] += 1
    node_pt = {c: (a[0] / a[2], a[1] / a[2]) for c, a in acc.items()}

    # 3) cut every track at node cells (crossroads + endpoints). Every edition is
    #    kept, so corridors ridden by several editions appear as separate
    #    overlapping segments rather than cancelling out.
    label = make_namer(load_places())
    segs = []
    for t in tracks:
        pts, cells = t["pts"], t["cells"]

        # candidate cuts: transitions into a node cell, plus the track ends
        cuts = [0]
        for i in range(1, len(pts)):
            if cells[i] in node_cells and cells[i] != cells[i - 1]:
                cuts.append(i)
        if cuts[-1] != len(pts) - 1:
            cuts.append(len(pts) - 1)
        cuts = sorted(set(cuts))

        # merge slivers so each piece is >= MIN_SEG_KM and the track stays fully
        # tiled (no dropped pieces -> no gaps)
        bounds = [cuts[0]]
        for c in cuts[1:-1]:
            if seg_stats(pts[bounds[-1]:c + 1])[0] >= MIN_SEG_KM:
                bounds.append(c)
        end = cuts[-1]
        if len(bounds) == 1 or seg_stats(pts[bounds[-1]:end + 1])[0] >= MIN_SEG_KM:
            bounds.append(end)
        else:
            bounds[-1] = end          # fold a short tail into the previous piece

        for j in range(len(bounds) - 1):
            i0, i1 = bounds[j], bounds[j + 1]
            sub = [list(c) for c in pts[i0:i1 + 1]]
            if len(sub) < 4:
                continue
            # weld the two ends onto the shared crossroad points
            if cells[i0] in node_pt:
                sub[0] = [node_pt[cells[i0]][0], node_pt[cells[i0]][1], sub[0][2]]
            if cells[i1] in node_pt:
                sub[-1] = [node_pt[cells[i1]][0], node_pt[cells[i1]][1], sub[-1][2]]

            dist, asc, mn, mx = seg_stats(sub)
            a = label(sub[0][0], sub[0][1])
            b = label(sub[-1][0], sub[-1][1])
            if a and b and a != b:
                nm = f"{a} ↔ {b}"
            elif a and b:
                nm = f"near {a}"
            elif a or b:
                nm = f"{a or b} spur"
            else:
                nm = "Remote section"

            segs.append({
                "name": nm, "from": a or "", "to": b or "",
                "year": t["year"], "color": t["color"],
                "distance_km": round(dist, 1), "ascent_m": int(round(asc)),
                "min_ele": int(round(mn)), "max_ele": int(round(mx)),
                "coords": [[round(c[0], 5), round(c[1], 5)] for c in sub],
                "profile": profile(sub),
            })

    segs.sort(key=lambda r: (r["year"], -r["distance_km"]))
    for i, r in enumerate(segs):
        r["id"] = f"srmrseg-{i}"
    with open(os.path.join(DATA, "srmr_segments.json"), "w") as f:
        json.dump({"segments": segs}, f, ensure_ascii=False)
    by_year = {}
    for r in segs:
        by_year[r["year"]] = by_year.get(r["year"], 0) + 1
    print(f"\nWrote {len(segs)} SRMR segments — all editions kept (per year: {by_year})")


if __name__ == "__main__":
    main()
