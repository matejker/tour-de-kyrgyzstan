# -*- coding: utf-8 -*-
"""
Add your own GPX as a permanent route on the site (Option B).

It parses a GPX, splits it into a fixed number of days (10 by default), computes
stats + display geometry, copies the GPX for download, and registers the route in
data/custom_routes.json — a file the generator never overwrites and the website
merges in alongside the built-in routes (shown in a "User generated" family).

Usage:
    python3 scripts/add_route.py my-ride.gpx --name "My Grand Tour"
        [--subtitle "Bishkek loop"] [--start Bishkek] [--color "#0891b2"]
        [--days 10] [--day-km 80] [--blurb "..."] [--id my-grand-tour]

By default the route is divided into 10 equal-distance days. Pass --day-km to
split by a target distance per day instead.

Then commit & push:  git add data && git commit -m "Add route: My Grand Tour" && git push
"""
import argparse
import json
import os
import re
import xml.etree.ElementTree as ET

from generate_routes import haversine, downsample, downsample_count, stats_for

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
GPXDIR = os.path.join(DATA, "gpx")
GEODIR = os.path.join(DATA, "geo")
CUSTOM = os.path.join(DATA, "custom_routes.json")


def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-") or "route"


def parse_gpx(path):
    """Return coords as [lon, lat, ele] (matching the generator's convention)."""
    root = ET.parse(path).getroot()
    coords = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in ("trkpt", "rtept"):
            try:
                lat = float(el.get("lat")); lon = float(el.get("lon"))
            except (TypeError, ValueError):
                continue
            ele = 0.0
            for ch in el:
                if ch.tag.split("}")[-1] == "ele" and ch.text:
                    try:
                        ele = float(ch.text)
                    except ValueError:
                        pass
            coords.append([lon, lat, ele])
    return coords


def split_days(coords, day_km):
    days, cur, acc = [], [coords[0]], 0.0
    for i in range(1, len(coords)):
        acc += haversine(coords[i - 1], coords[i])
        cur.append(coords[i])
        if acc >= day_km * 1000 and i < len(coords) - 1:
            days.append(cur); cur = [coords[i]]; acc = 0.0
    if len(cur) > 1:
        days.append(cur)
    elif days:
        days[-1] += cur[1:]
    return days


def split_days_n(coords, n):
    """Split the track into exactly n days of roughly equal distance."""
    n = max(1, min(n, len(coords) - 1))
    cum = [0.0]
    for i in range(1, len(coords)):
        cum.append(cum[-1] + haversine(coords[i - 1], coords[i]))
    total = cum[-1]
    if n == 1 or total == 0:
        return [coords]
    target = total / n
    days, start = [], 0
    for k in range(1, n):
        thr = target * k
        j = start + 1
        while j < len(coords) - 1 and cum[j] < thr:
            j += 1
        days.append(coords[start:j + 1])
        start = j
    days.append(coords[start:])
    return days


def main():
    ap = argparse.ArgumentParser(description="Add a GPX as a permanent site route.")
    ap.add_argument("gpx", help="path to the .gpx file")
    ap.add_argument("--name", required=True)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--start", default="")
    ap.add_argument("--color", default="#0891b2")
    ap.add_argument("--blurb", default="")
    ap.add_argument("--days", type=int, default=10,
                    help="split the route into this many days (default 10)")
    ap.add_argument("--day-km", type=float, default=0.0,
                    help="alternative: split by distance per day instead of a day count")
    ap.add_argument("--id", default="")
    args = ap.parse_args()

    if not args.gpx.lower().endswith(".gpx"):
        raise SystemExit("Please pass a .gpx file.")
    coords = parse_gpx(args.gpx)
    if len(coords) < 2:
        raise SystemExit("No usable track points found in that GPX.")

    rid = args.id or slugify(args.name)
    os.makedirs(GPXDIR, exist_ok=True); os.makedirs(GEODIR, exist_ok=True)

    days = split_days(coords, args.day_km) if args.day_km > 0 else split_days_n(coords, args.days)
    day_records, geo_days = [], []
    r_dist = r_asc = r_desc = 0.0
    r_min, r_max, max_camp = 99999, -99999, 0
    lats, lons = [], []
    for di, seg in enumerate(days, start=1):
        st = stats_for(seg)
        r_dist += st["distance_km"]; r_asc += st["ascent_m"]; r_desc += st["descent_m"]
        r_min = min(r_min, st["min_ele"]); r_max = max(r_max, st["max_ele"])
        max_camp = max(max_camp, st["end_ele"])
        day_records.append({"day": di, "name": f"Day {di}", "desc": "",
                            "camp": "Camp", "resupply": [], **st})
        disp = downsample_count(downsample(seg, 45.0), 900)
        gc = [[round(c[1], 5), round(c[0], 5), round(c[2], 1)] for c in disp]
        geo_days.append({"day": di, "name": f"Day {di}", "coords": gc})
        lats += [c[0] for c in gc]; lons += [c[1] for c in gc]

    bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
    flat = [c for seg in days for c in seg]
    overview = [[round(c[1], 4), round(c[0], 4)] for c in downsample_count(flat, 260)]

    with open(os.path.join(GEODIR, f"{rid}.json"), "w") as f:
        json.dump({"id": rid, "color": args.color, "bounds": bounds, "days": geo_days}, f)

    # copy the original GPX for download
    with open(args.gpx, "r", encoding="utf-8", errors="ignore") as src:
        gpx_text = src.read()
    with open(os.path.join(GPXDIR, f"{rid}.gpx"), "w", encoding="utf-8") as f:
        f.write(gpx_text)

    rec = {
        "id": rid, "name": args.name,
        "subtitle": args.subtitle or (f"{args.start} · {len(days)} days" if args.start else "Imported route"),
        "start": args.start or "—", "color": args.color,
        "remote": False, "expert": False, "custom": True,
        "blurb": args.blurb or "An imported route, added from a GPX file.",
        "gpx": f"data/gpx/{rid}.gpx", "geo": f"data/geo/{rid}.json",
        "total_distance_km": round(r_dist, 1), "total_ascent_m": int(round(r_asc)),
        "total_descent_m": int(round(r_desc)), "min_ele": r_min, "max_ele": r_max,
        "max_camp_ele": max_camp, "num_days": len(days), "bounds": bounds,
        "overview": overview, "days": day_records,
    }

    store = {"routes": []}
    if os.path.exists(CUSTOM):
        store = json.load(open(CUSTOM))
    store["routes"] = [r for r in store.get("routes", []) if r["id"] != rid] + [rec]
    with open(CUSTOM, "w") as f:
        json.dump(store, f, ensure_ascii=False, indent=1)

    print(f"Added '{args.name}' (id: {rid}) — {rec['total_distance_km']} km, "
          f"+{rec['total_ascent_m']} m, {len(days)} days")
    print("Files: data/custom_routes.json, "
          f"data/geo/{rid}.json, data/gpx/{rid}.gpx")
    print("Commit & push:  git add data && git commit -m \"Add route: "
          f"{args.name}\" && git push")


if __name__ == "__main__":
    main()
