# -*- coding: utf-8 -*-
"""
Build actual border-permit ZONE POLYGONS for Kyrgyzstan.

The official frontier zone is roughly a 50 km strip inland from the Chinese
border (and the Tajik border in the Alay). We compute that strip from the real
national boundaries: take the shared border line with each neighbour, buffer it
~50 km, and clip to Kyrgyzstan. A few discrete zones near the Kazakh border
(Karkara, upper Chong-Kemin, Ala-Archa) are added as their own polygons.

Sources: per-country GeoJSON from the public `world.geo.json` dataset.

Output: data/permits.json  ->  {note, zones:[{name,border,region,polygons:[[[lat,lon],...]]}]}
Run:  python3 scripts/build_permits.py
"""
import json
import os
import urllib.request

from pyproj import Transformer
from shapely.geometry import shape, mapping, LineString, MultiLineString, box
from shapely.ops import transform, unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")

BASE = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries"
STRIP_KM = 50.0

# metric projection for Kyrgyzstan (UTM 43N works well for the whole country)
TO_M = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True).transform
TO_DEG = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True).transform


def fetch_country(iso3):
    url = f"{BASE}/{iso3}.geo.json"
    with urllib.request.urlopen(url, timeout=60) as r:
        js = json.load(r)
    geom = js["features"][0]["geometry"]
    return shape(geom)


def shared_border(country, neighbour_m, kg_m):
    """Border line of KG that runs along `neighbour` (both already in metres)."""
    nb = neighbour_m.buffer(1500)          # 1.5 km tolerance for coincident borders
    line = kg_m.boundary.intersection(nb)
    return line


def strip_polygon(border_line_m, kg_m):
    strip = border_line_m.buffer(STRIP_KM * 1000).intersection(kg_m)
    return strip.simplify(800)             # ~0.8 km simplification


def to_latlon_rings(geom_m):
    """Return list of rings [[lat,lon],...] for a (Multi)Polygon in metres."""
    g = transform(TO_DEG, geom_m)
    rings = []
    polys = g.geoms if g.geom_type == "MultiPolygon" else [g]
    for p in polys:
        if p.is_empty:
            continue
        rings.append([[round(y, 4), round(x, 4)] for x, y in p.exterior.coords])
    return rings


def discrete(name, border, region, lat, lon, half_km):
    """A small square polygon zone around a point (still a polygon, not a circle)."""
    x, y = TO_M(lon, lat)
    b = box(x - half_km * 1000, y - half_km * 1000, x + half_km * 1000, y + half_km * 1000)
    return {"name": name, "border": border, "region": region, "polygons": to_latlon_rings(b)}


def main():
    kg = fetch_country("KGZ")
    cn = fetch_country("CHN")
    tj = fetch_country("TJK")
    kg_m = transform(TO_M, kg)
    cn_m = transform(TO_M, cn)
    tj_m = transform(TO_M, tj)

    zones = []

    cn_border = shared_border(kg, cn_m, kg_m)
    if not cn_border.is_empty:
        zones.append({
            "name": "China border zone (~50 km frontier strip)",
            "border": "China", "region": "Issyk-Köl · Naryn · Osh",
            "polygons": to_latlon_rings(strip_polygon(cn_border, kg_m)),
        })

    tj_border = shared_border(kg, tj_m, kg_m)
    if not tj_border.is_empty:
        zones.append({
            "name": "Tajikistan border zone (Alay / Batken)",
            "border": "Tajikistan", "region": "Osh · Batken",
            "polygons": to_latlon_rings(strip_polygon(tj_border, kg_m)),
        })

    # discrete zones near the Kazakh border (not a blanket strip)
    zones.append(discrete("Karkara Valley", "Kazakhstan", "Issyk-Köl", 42.83, 79.20, 16))
    zones.append(discrete("Upper Chong-Kemin", "Kazakhstan", "Chüy", 42.75, 76.60, 14))
    zones.append(discrete("Ala-Archa (Ak-Sai glacier)", "—", "Chüy", 42.50, 74.48, 9))

    out = {
        "note": ("Border-permit (frontier) zones. A permit obtained in advance (via a local "
                 "tour operator, ~5-12 working days) is required to enter these areas. The China "
                 "and Tajikistan zones are computed as a ~50 km strip inland from the real border; "
                 "boundaries are indicative for planning, not legal limits."),
        "zones": zones,
    }
    with open(os.path.join(DATA, "permits.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False)
    for z in zones:
        pts = sum(len(r) for r in z["polygons"])
        print(f"  {z['name']:48s} {len(z['polygons'])} ring(s), {pts} pts")
    print(f"Wrote data/permits.json ({len(zones)} zones)")


if __name__ == "__main__":
    main()
