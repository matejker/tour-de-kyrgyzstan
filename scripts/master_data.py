# -*- coding: utf-8 -*-
"""
Data for the Master Map: mountain passes, reusable route segments, and train stops.

- PASSES with a `base`+`over` pair are routed by the generator, which finds the
  true summit (highest point) along the crossing and builds a real climb profile.
- PASSES with only `at` are reference markers (their tracks aren't reliably mapped
  for routing, but riders should still know they're there).
- SEGMENTS are the reusable building blocks used across the routes, so riders can
  mix and match their own line. Each is routed and given a profile.
"""

# ---------------------------------------------------------------- passes
# base/over: ride from `base` across the pass to `over`; the summit is auto-found.
PASSES_ROUTED = [
    {"name": "Kalmak-Ashuu (32 Parrots)", "base": [75.56, 41.99], "over": [75.20, 41.90],
     "side": "Kochkor / Sary-Bulak ↔ Song-Köl"},
    {"name": "Kegety Pass", "base": [75.15, 42.28], "over": [75.05, 42.68],
     "side": "Kilemche plateau ↔ Chui (Kegety village)"},
    {"name": "Shamsy Pass", "base": [75.62, 42.72], "over": [75.45, 42.35],
     "side": "Chui (Shamsy) ↔ Kilemche plateau"},
    {"name": "Kök-Ayryk Pass", "base": [77.20, 42.66], "over": [76.55, 42.70],
     "side": "Issyk-Köl (Grigorievka) ↔ Chong-Kemin"},
    {"name": "Dolon Pass", "base": [75.70, 41.95], "over": [76.00, 41.55],
     "side": "Kochkor ↔ Naryn"},
]

# reference-only passes (known, but tracks not reliably routable in open data)
PASSES_REF = [
    {"name": "Tosor Pass", "at": [77.50, 41.88], "ele": 3893, "side": "Issyk-Köl (Tosor) ↔ Arabel / Song-Köl"},
    {"name": "Barskoon Pass", "at": [77.72, 41.93], "ele": 3819, "side": "above the Barskoon falls (Kumtor mine beyond — restricted)"},
    {"name": "Juuku Pass", "at": [77.95, 41.92], "ele": 3635, "side": "Juuku gorge ↔ Arabel plateau"},
    {"name": "Chong-Ashuu Pass", "at": [78.75, 42.28], "ele": 3822, "side": "Karakol ↔ Enilchek (remote)"},
    {"name": "Moldo-Ashuu Pass", "at": [75.55, 41.55], "ele": 3346, "side": "Song-Köl ↔ Naryn (Ak-Kya)"},
    {"name": "Kyzart Pass", "at": [75.33, 41.92], "ele": 2664, "side": "Song-Köl ↔ Jumgal (Kyzart)"},
    {"name": "San-Tash Pass", "at": [79.05, 42.85], "ele": 2000, "side": "Tüp ↔ Karkyra"},
]

# ---------------------------------------------------------------- segments
# cat: "road" (paved/main), "gravel" (quiet gravel), "pass" (crosses a high pass)
SEGMENTS = [
    {"name": "Balykchy ↔ Kochkor", "cat": "road",
     "pts": [[76.186, 42.461], [75.93, 42.33], [75.752, 42.214]]},
    {"name": "Kochkor ↔ Song-Köl (Kalmak-Ashuu)", "cat": "pass",
     "pts": [[75.752, 42.214], [75.63, 42.06], [75.56, 41.99], [75.30, 41.94], [75.35, 41.86]]},
    {"name": "Song-Köl ↔ Sary-Bulak", "cat": "gravel",
     "pts": [[75.35, 41.88], [75.55, 41.92], [75.70, 41.95]]},
    {"name": "Song-Köl ↔ Kegety foot (plateau)", "cat": "gravel",
     "pts": [[75.35, 41.88], [75.15, 42.05], [75.15, 42.28]]},
    {"name": "Kegety Pass (foot ↔ village)", "cat": "pass",
     "pts": [[75.15, 42.28], [75.28, 42.45], [75.15, 42.60], [75.05, 42.68]]},
    {"name": "Kochkor ↔ Naryn (Dolon Pass)", "cat": "road",
     "pts": [[75.752, 42.214], [75.70, 41.95], [75.79, 41.70], [76.00, 41.428]]},
    {"name": "Naryn ↔ At-Bashy", "cat": "road",
     "pts": [[76.00, 41.428], [75.80, 41.17]]},
    {"name": "Naryn ↔ Eki-Naryn", "cat": "gravel",
     "pts": [[76.00, 41.428], [76.20, 41.50], [76.35, 41.55]]},
    {"name": "Shamsy Pass (Shamsy ↔ plateau)", "cat": "pass",
     "pts": [[75.62, 42.72], [75.55, 42.45], [75.45, 42.35]]},
    {"name": "Kök-Ayryk Pass (Grigorievka ↔ Chong-Kemin)", "cat": "pass",
     "pts": [[77.20, 42.66], [76.9, 42.62], [76.55, 42.70]]},
    {"name": "Chong-Kemin ↔ Kemin", "cat": "gravel",
     "pts": [[76.55, 42.70], [76.10, 42.73], [76.00, 42.74], [75.690, 42.785]]},
    {"name": "Bishkek ↔ Kemin (Chui)", "cat": "road",
     "pts": [[74.612, 42.840], [75.251, 42.745], [75.300, 42.840], [75.690, 42.785]]},
    {"name": "Balykchy ↔ Karakol (south shore)", "cat": "gravel",
     "pts": [[76.186, 42.461], [76.986, 42.129], [77.552, 42.156], [77.998, 42.343], [78.394, 42.491]]},
    {"name": "Balykchy ↔ Karakol (north shore)", "cat": "road",
     "pts": [[76.186, 42.461], [77.083, 42.649], [77.66, 42.72], [78.36, 42.726], [78.394, 42.491]]},
    {"name": "Karakol ↔ Jyrgalan", "cat": "gravel",
     "pts": [[78.36, 42.726], [78.7, 42.62], [79.18, 42.61]]},
    {"name": "Kegety village ↔ Bishkek (foothills)", "cat": "road",
     "pts": [[75.05, 42.68], [74.99, 42.62], [74.70, 42.62], [74.612, 42.840]]},
]

# ---------------------------------------------------------------- train stops
# The Bishkek–Balykchy line (through the Boom Gorge) + Chui plain stations.
# The Balykchy leg runs mainly as a seasonal tourist service.
TRAIN_STOPS = [
    {"name": "Bishkek-2 (main station)", "lon": 74.585, "lat": 42.862, "note": "Main railway station; bike-friendly platforms"},
    {"name": "Alamedin", "lon": 74.68, "lat": 42.86, "note": "Chui plain halt"},
    {"name": "Kant", "lon": 74.85, "lat": 42.885, "note": "Chui plain station"},
    {"name": "Ivanovka", "lon": 75.08, "lat": 42.88, "note": "Chui plain halt"},
    {"name": "Tokmok", "lon": 75.29, "lat": 42.82, "note": "Chui station near Burana Tower"},
    {"name": "Bystrovka (Kemin)", "lon": 75.70, "lat": 42.78, "note": "Gateway to Chong-Kemin"},
    {"name": "Boomskoe (Boom)", "lon": 75.85, "lat": 42.55, "note": "In the Boom Gorge"},
    {"name": "Kök-Moinok", "lon": 76.03, "lat": 42.50, "note": "Boom Gorge halt"},
    {"name": "Balykchy (Rybachye)", "lon": 76.19, "lat": 42.46, "note": "Line terminus at Lake Issyk-Köl (seasonal service)"},
    {"name": "Kara-Balta", "lon": 73.85, "lat": 42.83, "note": "Western Chui terminus"},
]
