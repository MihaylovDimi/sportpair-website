"""Build the fifteen sport pages and the sitemap from data/venues.csv.

How to use it:
  1. In Supabase, export the Venue table as CSV.
  2. Run:  python tools/build_sport_pages.py path/to/Venue_rows.csv
     The script copies only the public columns into data/venues.csv,
     then writes sports/<sport>.html for every sport and sitemap.xml.
  3. Commit the changed files.

Run it without a path to rebuild from the data/venues.csv already in the repo.
Only the standard library is used, so plain Python 3 is enough.
"""

import csv
import html
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "venues.csv"
OUT = ROOT / "sports"
SITE = "https://sportpair.co.uk"
PLAY_URL = "https://play.google.com/store/apps/details?id=com.mihaylovdimi.sportmate"

# The ways to play, worded as on the home page.
MODES = {
    "partner": ("FIND", "Find a partner",
                "Browse players for your sport, see their level and when they are free, then start a chat."),
    "match": ("ORGANISE", "Create a match",
              "Set the place, time and number of players. Split teams fairly with one tap and pick team colours."),
    "session": ("JOIN", "Join a session",
                "Join a session someone has set up, or create your own and let others join."),
    "chat": ("PLAY", "Chat and play",
             "Every match and session has its own group chat, so everyone stays in the loop. Then just turn up and play."),
}

# slug: (label, page heading, verb, ways to play)
SPORTS = {
    "badminton": ("Badminton", "Badminton in Cambridge", "play badminton", ["partner", "match"]),
    "basketball": ("Basketball", "Basketball in Cambridge", "play basketball", ["match"]),
    "cycling": ("Cycling", "Cycling in Cambridge", "ride", ["partner", "session"]),
    "football": ("Football", "Football in Cambridge", "play football", ["match"]),
    "gym": ("Gym", "Gym training in Cambridge", "train", ["partner", "session"]),
    "hiking": ("Hiking", "Hiking around Cambridge", "hike", ["partner", "session"]),
    "kayaking": ("Kayaking", "Kayaking in Cambridge", "kayak", ["partner", "session"]),
    "paddleboarding": ("Paddleboarding", "Paddleboarding in Cambridge", "paddleboard", ["partner", "session"]),
    "rowing": ("Rowing", "Rowing in Cambridge", "row", ["partner", "session"]),
    "running": ("Running", "Running in Cambridge", "run", ["partner", "session"]),
    "squash": ("Squash", "Squash in Cambridge", "play squash", ["partner", "match"]),
    "swimming": ("Swimming", "Swimming in Cambridge", "swim", ["partner", "session"]),
    "table-tennis": ("Table tennis", "Table tennis in Cambridge", "play table tennis", ["partner", "match"]),
    "tennis": ("Tennis", "Tennis in Cambridge", "play tennis", ["partner", "match"]),
    "volleyball": ("Volleyball", "Volleyball in Cambridge", "play volleyball", ["match"]),
}

PUBLIC_COLUMNS = ["id", "name", "sport", "latitude", "longitude", "bookingUrl", "membersOnly", "source"]

MARK = """<svg class="mark" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <g transform="translate(100,100) scale(0.82) translate(-100,-100)">
        <circle cx="58" cy="66" r="13" fill="#2563EB"/>
        <path d="M40,132 L72,100 L40,100" fill="none" stroke="#2563EB" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="142" cy="66" r="13" fill="#FFFFFF"/>
        <path d="M160,132 L128,100 L160,100" fill="none" stroke="#FFFFFF" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="100" cy="116" r="9" fill="#6AA0FF"/>
      </g>
    </svg>"""

PLAY_ICON = """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M4 3.5v17c0 .4.4.6.7.4l13.6-8.1c.4-.2.4-.7 0-.9L4.7 3.1c-.3-.2-.7 0-.7.4z" fill="#fff"/></svg>"""


def import_supabase_export(path):
    """Keep only the public columns from a Supabase export.
    Price, slots and taken are internal and the price column is not reliable,
    so they are never published. 'Members only' is kept as a yes/no flag."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    DATA.parent.mkdir(exist_ok=True)
    with open(DATA, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PUBLIC_COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "id": r["id"], "name": r["name"], "sport": r["sport"],
                "latitude": r["latitude"], "longitude": r["longitude"],
                "bookingUrl": r.get("bookingUrl", ""),
                "membersOnly": "yes" if r.get("price") == "Members only" else "",
                "source": r.get("source", ""),
            })
    print(f"Imported {len(rows)} venues into {DATA.relative_to(ROOT)}")


def load_venues():
    with open(DATA, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def esc(text):
    return html.escape(text, quote=True)


def link_label(url):
    return "Book online" if "book" in url.lower() else "Website"


def venue_item(v):
    tag = '<span class="v-tag">Members only</span>' if v["membersOnly"] == "yes" else ""
    links = []
    if v["bookingUrl"]:
        links.append(f'<a href="{esc(v["bookingUrl"])}" target="_blank" rel="noopener">{link_label(v["bookingUrl"])}</a>')
    dest = quote(f'{v["latitude"]},{v["longitude"]}')
    links.append(f'<a href="https://www.google.com/maps/dir/?api=1&amp;destination={dest}" target="_blank" rel="noopener">Directions</a>')
    return (f'        <li class="venue"><div class="v-main"><span class="v-name">{esc(v["name"])}</span>{tag}</div>'
            f'<div class="v-links">{"".join(links)}</div></li>')


def sort_key(v):
    # Open places with a website first, members-only clubs last, then by name.
    return (v["membersOnly"] == "yes", not v["bookingUrl"], v["name"].lower())


def page(slug, venues):
    label, heading, verb, modes = SPORTS[slug]
    n = len(venues)
    if n:
        places = "place" if n == 1 else "places"
        lead = f"{n} {places} to {verb} in Cambridge, and people to {verb} with."
        description = (f"Find people to {verb} with in Cambridge and {n} {places} to {verb}, "
                       f"with booking links and directions. Free on Google Play.")
    else:
        lead = f"Find people to {verb} with around Cambridge."
        description = f"Find people to {verb} with around Cambridge and set up sessions together. Free on Google Play."

    mode_cards = "\n".join(
        f'        <div class="mode"><span class="tag">{MODES[m][0]}</span><h3>{MODES[m][1]}</h3><p>{MODES[m][2]}</p></div>'
        for m in modes + ["chat"])

    if n:
        items = "\n".join(venue_item(v) for v in sorted(venues, key=sort_key))
        osm = any(v["source"] == "osm" for v in venues)
        attrib = ('\n      <p class="attrib">Venue locations &copy; <a href="https://www.openstreetmap.org/copyright" '
                  'target="_blank" rel="noopener">OpenStreetMap contributors</a>.</p>') if osm else ""
        where = (f'      <p class="meta">{n} {places} on the SportPair map. Check opening times and membership on each website.</p>\n'
                 f'      <ul class="venues">\n{items}\n      </ul>{attrib}')
    else:
        where = (f'      <p class="empty">There are no listed places for {label.lower()} yet. '
                 f'When someone sets up a session in the app, they choose the meeting point.</p>')

    others = "\n".join(f'        <a href="{s}.html">{SPORTS[s][0]}</a>' for s in SPORTS if s != slug)

    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(heading)} · SportPair</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{SITE}/sports/{slug}.html">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="sport.css">
</head>
<body>
<!-- Generated by tools/build_sport_pages.py from data/venues.csv. Edit those, not this file. -->

<header>
  <a class="brand" href="../" aria-label="SportPair home">
    {MARK}
    <span class="wordmark">SPORT<span>PAIR</span></span>
  </a>
</header>

<section class="hero">
  <div class="hero-sketch" aria-hidden="true">
    <video muted playsinline loop preload="none" data-src="../images/sketches/{slug}.mp4"></video>
  </div>
  <a class="back" href="../#sports">&larr; All sports</a>
  <span class="pill">Cambridge, UK</span>
  <h1>{esc(heading)}</h1>
  <p class="lead">{esc(lead)}</p>
  <div class="store-row">
    <a class="play-btn" href="{PLAY_URL}">{PLAY_ICON} Get it on Google Play</a>
  </div>
</section>

<main class="doodles">
  <div class="wrap">
    <section class="card">
      <h2>How to {esc(verb)} on SportPair</h2>
      <div class="modes">
{mode_cards}
      </div>
    </section>

    <section class="card">
      <h2>Where to {esc(verb)}</h2>
{where}
    </section>

    <section class="card">
      <h2>Other sports</h2>
      <div class="chips">
{others}
      </div>
    </section>
  </div>

  <section class="cta">
    <h2>Ready to {esc(verb)}?</h2>
    <p>Join SportPair and find your next game in Cambridge.</p>
    <div class="store-row">
      <a class="play-btn" href="{PLAY_URL}">{PLAY_ICON} Get it on Google Play</a>
    </div>
  </section>
</main>

<footer>
  <div class="row">
    <a href="mailto:sportpair@gmail.com">sportpair@gmail.com</a>
    <a href="../privacy.html">Privacy Policy</a>
    <a href="../terms.html">Terms and Conditions</a>
    <a href="../delete-account.html">Delete your account</a>
  </div>
  <div>&copy; 2026 SportPair &middot; Cambridge, UK &middot; 18+</div>
</footer>

<script>
/* Play the sketch in a loop. People who turned animations off see one still
   frame, and people on data saver get no video at all. */
(function () {{
  var v = document.querySelector('.hero-sketch video');
  if (!v) return;
  if (navigator.connection && navigator.connection.saveData) return;
  var still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  v.src = v.dataset.src;
  if (still) {{
    v.preload = 'metadata';
    v.addEventListener('loadedmetadata', function () {{ v.currentTime = v.duration / 2; }}, {{ once: true }});
  }} else {{
    v.preload = 'auto';
    v.play().catch(function () {{}});
  }}
}})();
</script>
</body>
</html>
"""


def sitemap():
    urls = [f"{SITE}/"] + [f"{SITE}/sports/{s}.html" for s in SPORTS]
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'


def main():
    if len(sys.argv) > 1:
        import_supabase_export(sys.argv[1])
    venues = load_venues()
    unknown = sorted({v["sport"] for v in venues} - set(SPORTS))
    if unknown:
        print("Warning: venues for sports with no page were skipped:", ", ".join(unknown))
    OUT.mkdir(exist_ok=True)
    for slug in SPORTS:
        mine = [v for v in venues if v["sport"] == slug]
        (OUT / f"{slug}.html").write_text(page(slug, mine), encoding="utf-8")
        print(f"sports/{slug}.html  {len(mine)} venues")
    (ROOT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    print("sitemap.xml written")


if __name__ == "__main__":
    main()
