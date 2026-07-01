# -*- coding: utf-8 -*-
"""
Route definitions for the Tour de Kyrgyzstan bikepacking planner.

Design philosophy: "sleep low, exercise high".
- Camps (day end points) stay low: ideally < 2000 m, hard max ~2500 m. A couple of
  Jyrgalan nights (~2200 m) are the only exception (within the agreed allowance).
- Daytime gravel spurs climb high into the side gorges (2300-3500 m) but turn around
  BEFORE the big >3500 m passes and before permit / mine / border zones (Kumtor mine
  above Barskoon, the Torugart / Chinese border, Kel-Suu).
- Transfers follow real roads; the routes deliberately avoid the long Too-Ashuu tunnel
  (it is on the Bishkek-Osh road, far from any of these routes) and use the open
  Boom Gorge road, not the high Kok-Ayryk hike-a-bike pass.

Each day is a list of `legs`. A leg = {pts, profile, out_back}:
  profile  : "car-fast" (real roads, used for transfers) or "trekking" (gravel/gorge tracks)
  out_back : if true the leg is a there-and-back (climb up a dead-end gorge, then return)
The day's track is the concatenation of its legs.
"""

ROAD = "car-fast"
GRAVEL = "trekking"


def road(*pts):
    return {"pts": list(pts), "profile": ROAD}


def spur(*pts):
    """A there-and-back gravel climb up a gorge."""
    return {"pts": list(pts), "profile": GRAVEL, "out_back": True}


def gravel(*pts):
    """A one-way leg on gravel tracks (e.g. the road up to Jyrgalan)."""
    return {"pts": list(pts), "profile": GRAVEL}


ROUTES = [
    # ============================================================= ROUTE 2
    {
        "id": "issykkol-loop",
        "name": "Issyk-Köl Full Loop",
        "subtitle": "All the way around the lake",
        "start": "Balykchy",
        "color": "#3cb44b",
        "blurb": (
            "A complete circumnavigation of the world's second-largest alpine "
            "lake. The south shore delivers the wild gorges and gravel climbs; "
            "the north shore is gentler, with beaches, petroglyphs and spruce "
            "forests. You sleep beside the water every night (~1600-1800 m) and "
            "return to your start at Balykchy."
        ),
        "days": [
            {"name": "Balykchy → Bokonbayevo", "end_label": "Bokonbayevo",
             "desc": "Roll along the south shore to friendly Bokonbayevo.",
             "legs": [road([76.186, 42.461], [76.986, 42.129])],
             "resupply": [["Balykchy", 76.186, 42.461], ["Bokonbayevo", 76.986, 42.129]]},
            {"name": "Tong valley + → Kaji-Say", "end_label": "Kaji-Say",
             "desc": "Climb the Tong valley among red hills, then to Kaji-Say.",
             "legs": [spur([76.986, 42.129], [76.93, 41.95]),
                      road([76.986, 42.129], [77.168, 42.130])],
             "resupply": [["Bokonbayevo", 76.986, 42.129], ["Kaji-Say", 77.168, 42.130]]},
            {"name": "Skazka & Tosor gorge", "end_label": "Tamga",
             "desc": "Fairytale Canyon and a climb up the Tosor gorge to Tamga.",
             "legs": [road([77.168, 42.130], [77.448, 42.165]),
                      spur([77.448, 42.165], [77.49, 42.06]),
                      road([77.448, 42.165], [77.552, 42.156])],
             "resupply": [["Kaji-Say", 77.168, 42.130], ["Tosor", 77.448, 42.165], ["Tamga", 77.552, 42.156]]},
            {"name": "Barskoon waterfalls → Kyzyl-Suu", "end_label": "Kyzyl-Suu",
             "desc": "The classic Barskoon gorge climb, then on to Kyzyl-Suu.",
             "legs": [road([77.552, 42.156], [77.605, 42.145]),
                      spur([77.605, 42.145], [77.69, 42.04]),
                      road([77.605, 42.145], [77.998, 42.343])],
             "resupply": [["Tamga", 77.552, 42.156], ["Barskoon", 77.605, 42.145], ["Kyzyl-Suu", 77.998, 42.343]]},
            {"name": "Jeti-Ögüz valley", "end_label": "Jeti-Ögüz",
             "desc": "Broken Heart rock and the Valley of Flowers.",
             "legs": [road([77.998, 42.343], [78.205, 42.349]),
                      spur([78.205, 42.349], [78.31, 42.27])],
             "resupply": [["Kyzyl-Suu", 77.998, 42.343], ["Jeti-Ögüz village", 78.205, 42.349]]},
            {"name": "Karakol valley", "end_label": "Karakol",
             "desc": "Climb the Karakol valley to the ski base, then into town.",
             "legs": [road([78.205, 42.349], [78.394, 42.491]),
                      spur([78.394, 42.491], [78.50, 42.40])],
             "resupply": [["Jeti-Ögüz village", 78.205, 42.349], ["Karakol", 78.394, 42.491]]},
            {"name": "Altyn-Arashan springs", "end_label": "Karakol",
             "desc": "Easier day up toward the Altyn-Arashan hot springs and back.",
             "legs": [road([78.394, 42.491], [78.527, 42.486]),
                      spur([78.527, 42.486], [78.60, 42.43]),
                      road([78.527, 42.486], [78.394, 42.491])],
             "resupply": [["Karakol", 78.394, 42.491], ["Ak-Suu", 78.527, 42.486]]},
            {"name": "Karakol → Ananyevo", "end_label": "Ananyevo",
             "desc": "Cross to the north shore at Tüp and ride west above the lake.",
             "legs": [road([78.394, 42.491], [78.36, 42.726], [77.66, 42.72])],
             "resupply": [["Karakol", 78.394, 42.491], ["Tüp", 78.36, 42.726], ["Ananyevo", 77.66, 42.72]]},
            {"name": "Ananyevo → Cholpon-Ata", "end_label": "Cholpon-Ata",
             "desc": "Beaches and the open-air petroglyph museum at Cholpon-Ata.",
             "legs": [road([77.66, 42.72], [77.083, 42.649])],
             "resupply": [["Ananyevo", 77.66, 42.72], ["Cholpon-Ata", 77.083, 42.649]]},
            {"name": "Cholpon-Ata → Balykchy", "end_label": "Balykchy",
             "desc": "Final north-shore cruise back to the start.",
             "legs": [road([77.083, 42.649], [76.78, 42.60], [76.186, 42.461])],
             "resupply": [["Cholpon-Ata", 77.083, 42.649], ["Balykchy", 76.186, 42.461]]},
        ],
    },
    # ============================================================= ROUTE 3
    {
        "id": "eastern-wild",
        "name": "Eastern Wild: Karakol & Jyrgalan",
        "subtitle": "Karakol base + Jyrgalan gravel",
        "start": "Karakol",
        "color": "#4363d8",
        "blurb": (
            "Based out of the adventure hub of Karakol, this loop samples the "
            "best of the wild east: the red cliffs of Jeti-Ögüz, the Karakol "
            "valley, the Altyn-Arashan hot springs, the ancient San-Tash stone "
            "mound, and the emerging gravel paradise of Jyrgalan. Camps are at "
            "Karakol, Tüp and Jyrgalan (the only nights above 2000 m)."
        ),
        "days": [
            {"name": "Jeti-Ögüz valley", "end_label": "Karakol",
             "desc": "Warm-up loop to the Valley of Flowers and back to Karakol.",
             "legs": [road([78.394, 42.491], [78.205, 42.349]),
                      spur([78.205, 42.349], [78.31, 42.27]),
                      road([78.205, 42.349], [78.394, 42.491])],
             "resupply": [["Karakol", 78.394, 42.491], ["Jeti-Ögüz village", 78.205, 42.349]]},
            {"name": "Karakol valley", "end_label": "Karakol",
             "desc": "Climb the Karakol valley to the ski base, then spin back to town.",
             "legs": [spur([78.394, 42.491], [78.50, 42.40])],
             "resupply": [["Karakol", 78.394, 42.491]]},
            {"name": "Altyn-Arashan + → Tüp", "end_label": "Tüp",
             "desc": "Up toward the Altyn-Arashan springs, then north to Tüp.",
             "legs": [road([78.394, 42.491], [78.527, 42.486]),
                      spur([78.527, 42.486], [78.60, 42.43]),
                      road([78.527, 42.486], [78.36, 42.726])],
             "resupply": [["Karakol", 78.394, 42.491], ["Ak-Suu", 78.527, 42.486], ["Tüp", 78.36, 42.726]]},
            {"name": "San-Tash loop", "end_label": "Tüp",
             "desc": "Ride east to the legendary San-Tash stone mound and back.",
             "legs": [road([78.36, 42.726], [78.80, 42.76], [78.36, 42.726])],
             "resupply": [["Tüp", 78.36, 42.726], ["San-Tash", 78.80, 42.76]]},
            {"name": "Tüp → Jyrgalan", "end_label": "Jyrgalan",
             "desc": "Quiet gravel climb up the valley to the old mining village.",
             "legs": [gravel([78.36, 42.726], [79.18, 42.61])],
             "resupply": [["Tüp", 78.36, 42.726], ["Jyrgalan", 79.18, 42.61]]},
            {"name": "Jyrgalan high meadows", "end_label": "Jyrgalan",
             "desc": "Explore the jailoos and trails above Jyrgalan, then back to the guesthouses.",
             "legs": [spur([79.18, 42.61], [79.30, 42.55])],
             "resupply": [["Jyrgalan", 79.18, 42.61]]},
            {"name": "Jyrgalan → Tüp", "end_label": "Tüp",
             "desc": "Long descent back down the valley to the lakeshore at Tüp.",
             "legs": [gravel([79.18, 42.61], [78.36, 42.726])],
             "resupply": [["Jyrgalan", 79.18, 42.61], ["Tüp", 78.36, 42.726]]},
            {"name": "Tüp → Ak-Suu → Karakol", "end_label": "Karakol",
             "desc": "Back south with a stop at the Ak-Suu hot springs.",
             "legs": [road([78.36, 42.726], [78.527, 42.486], [78.394, 42.491])],
             "resupply": [["Tüp", 78.36, 42.726], ["Ak-Suu", 78.527, 42.486], ["Karakol", 78.394, 42.491]]},
            {"name": "Kyzyl-Suu & Juuku mouth", "end_label": "Karakol",
             "desc": "West to Kyzyl-Suu and the mouth of the Juuku gorge, then back.",
             "legs": [road([78.394, 42.491], [78.205, 42.349], [77.998, 42.343], [78.394, 42.491])],
             "resupply": [["Karakol", 78.394, 42.491], ["Kyzyl-Suu", 77.998, 42.343]]},
            {"name": "Karakol → Pristan loop", "end_label": "Karakol",
             "desc": "Gentle final spin to the lake at Pristan-Przhevalsk and back to town.",
             "legs": [road([78.394, 42.491], [78.32, 42.62], [78.30, 42.66], [78.394, 42.491])],
             "resupply": [["Karakol", 78.394, 42.491]]},
        ],
    },
    # ========================================================== ROUTE 6
    {
        "id": "kegety-traverse",
        "name": "Kegety Pass Traverse",
        "subtitle": "Issyk-Köl → Song-Köl → Bishkek",
        "start": "Balykchy",
        "color": "#c026d3",
        "remote": True,
        "blurb": (
            "The big linear one, and a proper adventure. Leave the lake at "
            "Balykchy, climb the 32-Parrots switchbacks of the Kalmak-Ashuu pass "
            "to the vast high lake of Song-Köl, then work north-west and cross "
            "the mighty Kegety Pass (~3780 m) to drop straight into the Chui "
            "valley and finish in Bishkek — perfect if you're flying home from "
            "there. Mostly gravel and old Soviet mountain tracks. NOTE: two "
            "nights are spent high at Song-Köl (~3000 m); everywhere else is low."
        ),
        "days": [
            {"name": "Balykchy → Kochkor", "end_label": "Kochkor",
             "desc": "Leave the lake and climb south over open steppe to Kochkor.",
             "legs": [road([76.186, 42.461], [75.93, 42.33], [75.752, 42.214])],
             "resupply": [["Balykchy", 76.186, 42.461], ["Kochkor", 75.752, 42.214]]},
            {"name": "Kochkor → Kalmak-Ashuu foot", "end_label": "Döng-Alysh jailoo",
             "desc": "Quiet back-valley gravel to the foot of the 32-Parrots climb.",
             "legs": [gravel([75.752, 42.214], [75.63, 42.06], [75.56, 41.99])],
             "resupply": [["Kochkor", 75.752, 42.214]]},
            {"name": "Kalmak-Ashuu → Song-Köl", "end_label": "Song-Köl (NE shore)",
             "desc": "Switchback up the pass onto the huge alpine plateau of Song-Köl.",
             "legs": [gravel([75.56, 41.99], [75.36, 41.96], [75.30, 41.94], [75.35, 41.86])],
             "resupply": [["Song-Köl yurts", 75.35, 41.86]]},
            {"name": "Song-Köl shore", "end_label": "Song-Köl (NE shore)",
             "desc": "Ride the wild lakeshore track past summer yurt camps.",
             "legs": [gravel([75.35, 41.86], [75.15, 41.83], [75.28, 41.87], [75.35, 41.88])],
             "resupply": [["Song-Köl yurts", 75.35, 41.88]]},
            {"name": "Song-Köl → Kochkor", "end_label": "Kochkor",
             "desc": "Descend the 32-Parrots to Sary-Bulak and roll down to Kochkor to resupply.",
             "legs": [gravel([75.35, 41.88], [75.55, 41.92], [75.70, 41.95]),
                      road([75.70, 41.95], [75.752, 42.214])],
             "resupply": [["Sary-Bulak", 75.70, 41.95], ["Kochkor", 75.752, 42.214]]},
            {"name": "Kochkor → Kegety foot", "end_label": "Kegety valley camp",
             "desc": "Turn up the remote Karakol valley toward the foot of the Kegety pass.",
             "legs": [gravel([75.752, 42.214], [75.45, 42.32], [75.15, 42.28])],
             "resupply": [["Kochkor", 75.752, 42.214]]},
            {"name": "Kegety Pass → Kegety village", "end_label": "Kegety village",
             "desc": "Haul over the Kegety Pass (~3780 m), then a huge descent into Chui.",
             "legs": [gravel([75.15, 42.28], [75.28, 42.45], [75.15, 42.60], [75.05, 42.68])],
             "resupply": [["Kegety village", 75.05, 42.68]]},
            {"name": "Kegety → Issyk-Ata → Alamedin", "end_label": "Alamedin gorge",
             "desc": "Roll along the foothills past the Issyk-Ata hot springs.",
             "legs": [road([75.05, 42.68], [74.99, 42.62], [74.80, 42.70], [74.70, 42.62])],
             "resupply": [["Issyk-Ata", 74.99, 42.62], ["Alamedin", 74.70, 42.70]]},
            {"name": "Alamedin → Bishkek", "end_label": "Bishkek",
             "desc": "Drop down into Bishkek and the flight home.",
             "legs": [road([74.70, 42.62], [74.612, 42.840])],
             "resupply": [["Bishkek", 74.612, 42.840]]},
        ],
    },

    # ========================================================== ROUTE 7
    {
        "id": "kokayryk-traverse",
        "name": "Kök-Ayryk Wild Traverse",
        "subtitle": "Karakol → Bishkek (no Boom Gorge)",
        "start": "Karakol",
        "color": "#0e7490",
        "remote": True,
        "blurb": (
            "A traverse from Karakol back to Bishkek that deliberately avoids the "
            "busy Tokmok–Balykchy (Boom Gorge) highway. Instead you climb out of "
            "the Issyk-Köl basin over the rugged Kök-Ayryk Pass (~3350 m) into the "
            "hidden Chong-Kemin valley — one of the most beautiful in the country "
            "— and follow it down to the Chui plain and Bishkek. A hike-a-bike "
            "pass and quiet gravel throughout."
        ),
        "days": [
            {"name": "Karakol → Ananyevo", "end_label": "Ananyevo",
             "desc": "Cross to the north shore and ride west above the lake.",
             "legs": [road([78.394, 42.491], [78.36, 42.726], [77.66, 42.72])],
             "resupply": [["Karakol", 78.394, 42.491], ["Tüp", 78.36, 42.726], ["Ananyevo", 77.66, 42.72]]},
            {"name": "Semenovka gorge → Grigorievka", "end_label": "Grigorievka",
             "desc": "Dip into the spruce-lined Semenovka gorge before the Grigorievka mouth.",
             "legs": [road([77.66, 42.72], [77.52, 42.685]),
                      spur([77.52, 42.685], [77.55, 42.60]),
                      road([77.52, 42.685], [77.466, 42.703])],
             "resupply": [["Semenovka", 77.52, 42.685], ["Grigorievka", 77.466, 42.703]]},
            {"name": "Chong-Ak-Suu → Kök-Ayryk foot", "end_label": "Kök-Ayryk camp",
             "desc": "Climb the spruce-lined gorge to a high camp below the pass.",
             "legs": [gravel([77.466, 42.703], [77.30, 42.64], [77.05, 42.62])],
             "resupply": [["Grigorievka", 77.466, 42.703]]},
            {"name": "Kök-Ayryk Pass → Chong-Kemin", "end_label": "Upper Chong-Kemin",
             "desc": "Over the pass (~3350 m) and down into the upper Chong-Kemin valley.",
             "legs": [gravel([77.05, 42.62], [76.9, 42.62], [76.55, 42.70])],
             "resupply": []},
            {"name": "Chong-Kemin valley", "end_label": "Chong-Kemin (mid)",
             "desc": "Follow the river down the long, green Chong-Kemin valley.",
             "legs": [gravel([76.55, 42.70], [76.30, 42.72], [76.10, 42.73])],
             "resupply": [["Kaindy", 76.00, 42.74]]},
            {"name": "Chong-Kemin → Kemin", "end_label": "Kemin",
             "desc": "Out of the valley mouth to the town of Kemin on the Chui side.",
             "legs": [gravel([76.10, 42.73], [76.00, 42.74]), road([76.00, 42.74], [75.690, 42.785])],
             "resupply": [["Kaindy", 76.00, 42.74], ["Kemin", 75.690, 42.785]]},
            {"name": "Kemin → Burana → Tokmok", "end_label": "Tokmok",
             "desc": "Quiet Chui back-roads and the Burana Tower (never the Boom Gorge highway).",
             "legs": [road([75.690, 42.785], [75.45, 42.80], [75.251, 42.745], [75.300, 42.840])],
             "resupply": [["Kemin", 75.690, 42.785], ["Burana Tower", 75.251, 42.745], ["Tokmok", 75.300, 42.840]]},
            {"name": "Tokmok → Issyk-Ata", "end_label": "Issyk-Ata",
             "desc": "Burana Tower, then south to the Issyk-Ata hot-spring gorge.",
             "legs": [road([75.300, 42.840], [75.251, 42.745], [75.10, 42.70], [74.99, 42.62])],
             "resupply": [["Burana Tower", 75.251, 42.745], ["Issyk-Ata", 74.99, 42.62]]},
            {"name": "Issyk-Ata → Alamedin gorge", "end_label": "Alamedin gorge",
             "desc": "Link the foothill gorges along the edge of the mountains.",
             "legs": [road([74.99, 42.62], [74.80, 42.70], [74.70, 42.62])],
             "resupply": [["Alamedin", 74.70, 42.70]]},
            {"name": "Alamedin → Bishkek", "end_label": "Bishkek",
             "desc": "Final roll down into the capital.",
             "legs": [road([74.70, 42.62], [74.612, 42.840])],
             "resupply": [["Bishkek", 74.612, 42.840]]},
        ],
    },

    # ========================================================== ROUTE 9
    {
        "id": "shamsy-kegety-loop",
        "name": "Shamsy–Kegety Double Pass",
        "subtitle": "Bishkek loop over two big passes",
        "start": "Bishkek",
        "color": "#4d7c0f",
        "remote": True,
        "blurb": (
            "A punchy loop straight out of the capital that strings together two "
            "of the Kyrgyz Ala-Too's classic passes. Head east along the foothills, "
            "climb the Shamsy gorge over the Shamsy Pass (~3560 m) onto the high "
            "Kilemche plateau, then return north over the Kegety Pass (~3780 m) and "
            "down to Bishkek. Big, remote and almost all gravel. NOTE: two high "
            "plateau camps (~2800-2900 m)."
        ),
        "days": [
            {"name": "Bishkek → Tokmok", "end_label": "Tokmok",
             "desc": "Roll east across the Chui plain, with a stop at the Burana Tower.",
             "legs": [road([74.612, 42.840], [74.90, 42.85], [75.251, 42.745], [75.300, 42.840])],
             "resupply": [["Bishkek", 74.612, 42.840], ["Burana Tower", 75.251, 42.745], ["Tokmok", 75.300, 42.840]]},
            {"name": "Tokmok → Shamsy gorge", "end_label": "Shamsy gorge camp",
             "desc": "South to Shamsy village and up into the mouth of the gorge.",
             "legs": [road([75.300, 42.840], [75.62, 42.72]),
                      gravel([75.62, 42.72], [75.58, 42.62])],
             "resupply": [["Shamsy", 75.62, 42.72]]},
            {"name": "Shamsy Pass → plateau", "end_label": "Kilemche plateau",
             "desc": "Climb over the Shamsy Pass (~3560 m) onto the high summer pastures.",
             "legs": [gravel([75.58, 42.62], [75.55, 42.45], [75.48, 42.40])],
             "resupply": []},
            {"name": "Plateau → Kegety foot", "end_label": "Kegety foot",
             "desc": "Traverse the wild plateau west to the foot of the Kegety pass.",
             "legs": [gravel([75.48, 42.40], [75.30, 42.33], [75.15, 42.28])],
             "resupply": []},
            {"name": "Kegety Pass → village", "end_label": "Kegety village",
             "desc": "Over the Kegety Pass (~3780 m) and the long drop back to Chui.",
             "legs": [gravel([75.15, 42.28], [75.28, 42.45], [75.15, 42.60], [75.05, 42.68])],
             "resupply": [["Kegety village", 75.05, 42.68]]},
            {"name": "Kegety → Issyk-Ata", "end_label": "Issyk-Ata",
             "desc": "Foothill roll to the Issyk-Ata hot springs to soak tired legs.",
             "legs": [road([75.05, 42.68], [75.00, 42.75], [74.99, 42.62])],
             "resupply": [["Issyk-Ata", 74.99, 42.62]]},
            {"name": "Issyk-Ata → Bishkek", "end_label": "Bishkek",
             "desc": "Down through the Alamedin gorge mouth back to the capital.",
             "legs": [road([74.99, 42.62], [74.80, 42.70], [74.612, 42.840])],
             "resupply": [["Alamedin", 74.70, 42.70], ["Bishkek", 74.612, 42.840]]},
        ],
    },

    # ========================================================== ROUTE 11
    {
        "id": "central-massif",
        "name": "Central Massif Traverse",
        "subtitle": "Naryn → Song-Köl → Kegety → Bishkek",
        "start": "At-Bashy",
        "color": "#be123c",
        "remote": True, "expert": True,
        "blurb": (
            "A committing, near-straight line across the heart of the Tien Shan, "
            "ending in Bishkek. From At-Bashy you climb to Naryn, cross the Dolon "
            "pass, ride up the 32-Parrots to Song-Köl, then take the wild high "
            "plateau traverse straight to the foot of the Kegety Pass (~3780 m) "
            "and drop to the capital. EXPERT: expect up to 3 days between proper "
            "resupplies and 2-3 nights at 2500-3050 m."
        ),
        "days": [
            {"name": "At-Bashy → Naryn", "end_label": "Naryn",
             "desc": "Warm-up down the At-Bashy valley and along the river to Naryn.",
             "legs": [road([75.80, 41.17], [76.000, 41.428])],
             "resupply": [["At-Bashy", 75.80, 41.17], ["Naryn", 76.000, 41.428]]},
            {"name": "Naryn → Dolon → Sary-Bulak", "end_label": "Sary-Bulak",
             "desc": "Over the Dolon pass (~3030 m) and down toward Sary-Bulak.",
             "legs": [road([76.000, 41.428], [75.79, 41.70], [75.70, 41.95])],
             "resupply": [["Naryn", 76.000, 41.428], ["Sary-Bulak", 75.70, 41.95]]},
            {"name": "Sary-Bulak → Song-Köl", "end_label": "Song-Köl",
             "desc": "The 32-Parrots switchbacks up onto the Song-Köl plateau.",
             "legs": [gravel([75.70, 41.95], [75.56, 41.99], [75.30, 41.94], [75.35, 41.86])],
             "resupply": [["Sary-Bulak", 75.70, 41.95], ["Song-Köl yurts", 75.35, 41.86]]},
            {"name": "Song-Köl → Kegety foot", "end_label": "Kegety valley camp",
             "desc": "A wild, roadless-feeling plateau traverse to the foot of the Kegety pass.",
             "legs": [gravel([75.35, 41.86], [75.15, 42.05], [75.15, 42.28])],
             "resupply": [["Song-Köl yurts", 75.35, 41.86]]},
            {"name": "Kegety Pass → village", "end_label": "Kegety village",
             "desc": "Over the Kegety Pass (~3780 m) and the long descent into Chui.",
             "legs": [gravel([75.15, 42.28], [75.28, 42.45], [75.15, 42.60], [75.05, 42.68])],
             "resupply": [["Kegety village", 75.05, 42.68]]},
            {"name": "Kegety → Bishkek", "end_label": "Bishkek",
             "desc": "Straight foothill roll along the Chui edge into the capital.",
             "legs": [road([75.05, 42.68], [74.85, 42.80], [74.612, 42.840])],
             "resupply": [["Kegety village", 75.05, 42.68], ["Bishkek", 74.612, 42.840]]},
        ],
    },

    # ========================================================== ROUTE 12
    {
        "id": "kokayryk-express",
        "name": "Kök-Ayryk Express",
        "subtitle": "Karakol → Bishkek, the fast wild line",
        "start": "Karakol",
        "color": "#0f766e",
        "remote": True, "expert": True,
        "blurb": (
            "The quickest wild way from Karakol back to Bishkek without the Boom "
            "Gorge: north shore, straight up the Chong-Ak-Suu gorge, over the "
            "Kök-Ayryk Pass (~3350 m) and down the length of the Chong-Kemin "
            "valley to the capital. Six days. EXPERT: one high camp and a "
            "long remote stretch over the pass."
        ),
        "days": [
            {"name": "Karakol → Ananyevo", "end_label": "Ananyevo",
             "desc": "Cross to the north shore and ride west above the lake.",
             "legs": [road([78.394, 42.491], [78.36, 42.726], [77.66, 42.72])],
             "resupply": [["Karakol", 78.394, 42.491], ["Tüp", 78.36, 42.726], ["Ananyevo", 77.66, 42.72]]},
            {"name": "Ananyevo → Kök-Ayryk foot", "end_label": "Chong-Ak-Suu camp",
             "desc": "Through Grigorievka and up the spruce-lined gorge below the pass.",
             "legs": [road([77.66, 42.72], [77.466, 42.703]),
                      gravel([77.466, 42.703], [77.30, 42.64], [77.05, 42.62])],
             "resupply": [["Grigorievka", 77.466, 42.703]]},
            {"name": "Kök-Ayryk Pass → Chong-Kemin", "end_label": "Upper Chong-Kemin",
             "desc": "Over the pass (~3350 m) into the hidden upper Chong-Kemin valley.",
             "legs": [gravel([77.05, 42.62], [76.9, 42.62], [76.55, 42.70])],
             "resupply": []},
            {"name": "Chong-Kemin → Kaindy", "end_label": "Kaindy",
             "desc": "Ride the length of the beautiful Chong-Kemin valley to its mouth.",
             "legs": [gravel([76.55, 42.70], [76.10, 42.73], [76.00, 42.74])],
             "resupply": [["Kaindy", 76.00, 42.74]]},
            {"name": "Kaindy → Kemin → Tokmok", "end_label": "Tokmok",
             "desc": "Out to the Chui plain and quiet back-roads to Tokmok (never the Boom Gorge).",
             "legs": [road([76.00, 42.74], [75.690, 42.785], [75.300, 42.840])],
             "resupply": [["Kemin", 75.690, 42.785], ["Tokmok", 75.300, 42.840]]},
            {"name": "Tokmok → Bishkek", "end_label": "Bishkek",
             "desc": "Final Chui-plain spin to the capital.",
             "legs": [road([75.300, 42.840], [74.90, 42.85], [74.612, 42.840])],
             "resupply": [["Tokmok", 75.300, 42.840], ["Bishkek", 74.612, 42.840]]},
        ],
    },

    # ========================================================== ROUTE 14
    {
        "id": "grand-traverse-xl",
        "name": "Grand Traverse XL",
        "subtitle": "Karakol → Bishkek, the whole country",
        "start": "Karakol",
        "color": "#5b21b6",
        "remote": True, "expert": True,
        "blurb": (
            "The big one: a coast-to-capital expedition line from Karakol all the "
            "way to Bishkek. Ride the wild south shore of Issyk-Köl, cut inland to "
            "Kochkor, climb to Song-Köl, take the high plateau to the Kegety Pass "
            "(~3780 m) and descend to the finish. Ten days, ~760 km, everything "
            "Kyrgyzstan has. EXPERT: a couple of nights at Song-Köl (~3050 m) and "
            "long remote stretches."
        ),
        "days": [
            {"name": "Karakol → Kyzyl-Suu", "end_label": "Kyzyl-Suu",
             "desc": "South-shore start past the red cliffs of Jeti-Ögüz.",
             "legs": [road([78.394, 42.491], [78.205, 42.349], [77.998, 42.343])],
             "resupply": [["Karakol", 78.394, 42.491], ["Jeti-Ögüz village", 78.205, 42.349], ["Kyzyl-Suu", 77.998, 42.343]]},
            {"name": "Kyzyl-Suu → Tamga", "end_label": "Tamga",
             "desc": "Along the shore past the Barskoon gorge mouth to Tamga.",
             "legs": [road([77.998, 42.343], [77.605, 42.145], [77.552, 42.156])],
             "resupply": [["Barskoon", 77.605, 42.145], ["Tamga", 77.552, 42.156]]},
            {"name": "Tamga → Bokonbayevo", "end_label": "Bokonbayevo",
             "desc": "Quiet shore road west past Kaji-Say and the Skazka canyons.",
             "legs": [road([77.552, 42.156], [77.168, 42.130], [76.986, 42.129])],
             "resupply": [["Kaji-Say", 77.168, 42.130], ["Bokonbayevo", 76.986, 42.129]]},
            {"name": "Bokonbayevo → Balykchy", "end_label": "Balykchy",
             "desc": "Finish the south shore at the western tip of the lake.",
             "legs": [road([76.986, 42.129], [76.186, 42.461])],
             "resupply": [["Bokonbayevo", 76.986, 42.129], ["Balykchy", 76.186, 42.461]]},
            {"name": "Balykchy → Kochkor", "end_label": "Kochkor",
             "desc": "Turn inland and climb the steppe to Kochkor.",
             "legs": [road([76.186, 42.461], [75.93, 42.33], [75.752, 42.214])],
             "resupply": [["Kochkor", 75.752, 42.214]]},
            {"name": "Kochkor → Kalmak-Ashuu foot", "end_label": "Döng-Alysh jailoo",
             "desc": "Back-valley gravel to the foot of the 32-Parrots climb.",
             "legs": [gravel([75.752, 42.214], [75.63, 42.06], [75.56, 41.99])],
             "resupply": [["Kochkor", 75.752, 42.214]]},
            {"name": "Kalmak-Ashuu → Song-Köl", "end_label": "Song-Köl",
             "desc": "Switchback onto the great high lake of Song-Köl.",
             "legs": [gravel([75.56, 41.99], [75.30, 41.94], [75.35, 41.86])],
             "resupply": [["Song-Köl yurts", 75.35, 41.86]]},
            {"name": "Song-Köl → Kegety foot", "end_label": "Kegety valley camp",
             "desc": "The wild plateau traverse to the foot of the Kegety pass.",
             "legs": [gravel([75.35, 41.86], [75.15, 42.05], [75.15, 42.28])],
             "resupply": []},
            {"name": "Kegety Pass → village", "end_label": "Kegety village",
             "desc": "Over the Kegety Pass (~3780 m) and the huge drop into Chui.",
             "legs": [gravel([75.15, 42.28], [75.28, 42.45], [75.15, 42.60], [75.05, 42.68])],
             "resupply": [["Kegety village", 75.05, 42.68]]},
            {"name": "Kegety → Bishkek", "end_label": "Bishkek",
             "desc": "Final straight foothill roll to the capital and the flight home.",
             "legs": [road([75.05, 42.68], [74.85, 42.80], [74.612, 42.840])],
             "resupply": [["Kegety village", 75.05, 42.68], ["Bishkek", 74.612, 42.840]]},
        ],
    },
]
