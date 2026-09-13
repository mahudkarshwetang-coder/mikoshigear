#!/usr/bin/env python3
"""Generate adapters.html from cables.html template (dedicated-page split)."""
s = open("/Users/shwetangmahudkar/Desktop/Mikoshi/site/cables.html").read()

s = s.replace("<title>Mikoshi Gear — Cables — Toronto</title>",
              "<title>Mikoshi Gear — Adapters — Toronto</title>")
s = s.replace("<h1>Cables.</h1>", "<h1>Adapters.</h1>")
s = s.replace("100W E-marker braided USB-C cables — copper-core, 5A fast charge, tangle-free. In Toronto, priced wholesale, ready for your counter.",
              "ETL-certified 20W GaN USB-C PD chargers — mini size, five colours, PD 3.0 + QC 3.0. In Toronto, priced wholesale, ready for your counter.")
s = s.replace("<h2>Cable Line</h2>", "<h2>Adapter Line</h2>")
s = s.replace('product.html?id=cable-100w', 'product.html?id=charger-20w-gan')
s = s.replace("cable-100w.png", "charger-20w-gan.png")
s = s.replace("100W USB-C cable", "20W GaN charger")
s = s.replace("USB-C Cable — 100W", "20W GaN Charger — USB-C PD")
s = s.replace("Nylon braided · E-marker chip · 5A fast charge · 1m / 2m / 3m",
              "ETL certified · PD 3.0 + QC3.0 · mini size · 5 colours")
s = s.replace('<a class="active" href="cables.html">Cables</a>',
              '<a href="cables.html">Cables</a>')
s = s.replace('<a href="adapters.html">Adapters</a>',
              '<a class="active" href="adapters.html">Adapters</a>')
s = s.replace("Cables, priced for your counter", "Adapters, priced for your counter")
s = s.replace("Cable pricing is on request", "Adapter pricing is on request")
s = s.replace("Every cable is a real E-marker 100W unit",
              "Every adapter is ETL-certified before it ships")
s = s.replace("feel the braid", "plug them in")
s = s.replace("any mix of lengths", "any mix of colours")
s = s.replace('<a class="btn btn-ghost" href="adapters.html">Adapters</a>',
              '<a class="btn btn-ghost" href="cables.html">Cables</a>')

open("/Users/shwetangmahudkar/Desktop/Mikoshi/site/adapters.html", "w").write(s)
print("adapters.html written:", len(s), "chars")
