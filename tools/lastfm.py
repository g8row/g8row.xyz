#!/usr/bin/env python3
# writes the listening data the site shows (now playing, recent tracks, top artists this week,
# six genres over three months, totals) as a small json file. runs on the server from cron so the
# api key never reaches the browser. stdlib only.
#   LASTFM_API_KEY=... python3 tools/lastfm.py /var/www/g8row.xyz/lastfm.json
# with no path it refreshes tools/lastfm.json, the snapshot baked into the page by build.py.
import json, math, os, sys, time, urllib.parse, urllib.request

USER = os.environ.get("LASTFM_USER", "pluwak")
KEY = os.environ["LASTFM_API_KEY"]
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "lastfm.json")
# artist -> top tags, refreshed weekly, so most cron runs make four api calls
TAGS = os.path.expanduser("~/.cache/g8row-lastfm-tags.json")
# tags that say nothing about the sound
SKIP = {"seen live", "favorites", "favourite", "favorite", "albums i own", "male vocalists", "female vocalists",
        "american", "british", "uk", "usa", "irish", "brazilian", "brazil", "english", "canadian", "french", "german",
        "00s", "10s", "20s", "2020s", "2010s", "90s", "80s", "70s", "60s", "spotify", "all", "under 2000 listeners"}

def call(method, **kw):
    q = urllib.parse.urlencode(dict(method=method, api_key=KEY, format="json", **kw))
    with urllib.request.urlopen("https://ws.audioscrobbler.com/2.0/?" + q, timeout=15) as r:
        return json.load(r)

def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(path + ".tmp", path)

recent = call("user.getrecenttracks", user=USER, limit=6)["recenttracks"]["track"]
top = call("user.gettopartists", user=USER, period="7day", limit=5)["topartists"]["artist"]
info = call("user.getinfo", user=USER)["user"]

# genres: each of the top artists of the last three months gives its two strongest tags
# (the second counts 0.7), weighted by plays; six biggest, square-root scaled so small ones still show
try:
    cache = json.load(open(TAGS))
except (OSError, ValueError):
    cache = {}
weights = {}
for a in call("user.gettopartists", user=USER, period="3month", limit=15)["topartists"]["artist"]:
    name, plays = a["name"], int(a["playcount"])
    hit = cache.get(name)
    if not hit or time.time() - hit["at"] > 7 * 86400:
        tags = [t["name"].lower() for t in call("artist.gettoptags", artist=name)["toptags"].get("tag", [])
                if int(t.get("count", 0)) >= 10 and t["name"].lower() not in SKIP]
        hit = cache[name] = {"at": int(time.time()), "tags": tags[:2]}
    for i, tag in enumerate(hit["tags"]):
        weights[tag] = weights.get(tag, 0) + plays * (1, 0.7)[i]
write(TAGS, cache)
best = sorted(weights.items(), key=lambda kv: -kv[1])[:6]
most = best[0][1] if best else 1

now = bool(recent) and recent[0].get("@attr", {}).get("nowplaying") == "true"
data = {
    "now": now,
    "recent": [{"t": r["name"], "a": r["artist"]["#text"], "u": int(r["date"]["uts"]) if "date" in r else None} for r in recent][:5],
    "top": [{"a": a["name"], "n": int(a["playcount"])} for a in top],
    "genres": [{"g": g, "v": round(math.sqrt(w / most), 2)} for g, w in best],
    "scrobbles": int(info["playcount"]),
    "artists": int(info.get("artist_count", 0)),
    "since": int(info["registered"]["unixtime"]),
    "at": int(time.time()),
}
write(OUT, data)
