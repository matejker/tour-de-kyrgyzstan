# -*- coding: utf-8 -*-
"""
Build a country-wide resupply dataset: one point per town/village in Kyrgyzstan,
pulled from OpenStreetMap via the Overpass API. Villages in Kyrgyzstan almost
always have at least a small shop (magazin), so settlements are a good proxy for
"where you can resupply".

Writes data/resupply.json  ->  {"places": [{name, lat, lon, kind}, ...]}
Run:  python3 scripts/fetch_resupply.py
"""
import json
import os
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")

QUERY = """
[out:json][timeout:120];
area["ISO3166-1"="KG"][admin_level=2]->.kg;
(
  node["place"~"^(city|town|village)$"]["name"](area.kg);
);
out qt;
"""

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def fetch():
    data = urllib.parse.urlencode({"data": QUERY}).encode()
    last = None
    for ep in ENDPOINTS:
        try:
            req = urllib.request.Request(ep, data=data,
                                         headers={"User-Agent": "tour-de-kyrgyzstan/1.0"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            print(f"  {ep} failed: {e}")
            last = e
    raise last


def main():
    js = fetch()
    places = []
    for el in js.get("elements", []):
        t = el.get("tags", {})
        name = t.get("name:en") or t.get("name")
        if not name or "lat" not in el:
            continue
        places.append({
            "name": name,
            "lat": round(el["lat"], 5),
            "lon": round(el["lon"], 5),
            "kind": t.get("place"),
        })
    # de-duplicate by rounded coordinate
    seen, uniq = set(), []
    for p in places:
        k = (round(p["lat"], 3), round(p["lon"], 3))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(p)
    uniq.sort(key=lambda p: (p["kind"] != "city", p["kind"] != "town", p["name"]))
    with open(os.path.join(DATA, "resupply.json"), "w") as f:
        json.dump({"places": uniq}, f, ensure_ascii=False)
    kinds = {}
    for p in uniq:
        kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
    print(f"Wrote {len(uniq)} places -> data/resupply.json  {kinds}")


if __name__ == "__main__":
    main()
