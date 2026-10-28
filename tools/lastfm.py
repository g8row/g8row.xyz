#!/usr/bin/env python3
# writes the listening data the site shows (recent tracks, top artists this week, totals) as a small json file.
# runs on the server from cron so the api key never reaches the browser. stdlib only.
#   LASTFM_API_KEY=... python3 tools/lastfm.py /var/www/g8row.xyz/lastfm.json
# with no path it refreshes tools/lastfm.json, the snapshot baked into the page by build.py.
import json, os, sys, urllib.parse, urllib.request

USER = os.environ.get("LASTFM_USER", "pluwak")
KEY = os.environ["LASTFM_API_KEY"]
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "lastfm.json")

def call(method, **kw):
    q = urllib.parse.urlencode(dict(method=method, user=USER, api_key=KEY, format="json", **kw))
    with urllib.request.urlopen("https://ws.audioscrobbler.com/2.0/?" + q, timeout=15) as r:
        return json.load(r)

recent = call("user.getrecenttracks", limit=6)["recenttracks"]["track"]
top = call("user.gettopartists", period="7day", limit=5)["topartists"]["artist"]
info = call("user.getinfo")["user"]

now = bool(recent) and recent[0].get("@attr", {}).get("nowplaying") == "true"
data = {
    "now": now,
    "recent": [{"t": r["name"], "a": r["artist"]["#text"], "u": int(r["date"]["uts"]) if "date" in r else None} for r in recent][:5],
    "top": [{"a": a["name"], "n": int(a["playcount"])} for a in top],
    "scrobbles": int(info["playcount"]),
    "artists": int(info.get("artist_count", 0)),
    "since": int(info["registered"]["unixtime"]),
    "at": int(__import__("time").time()),
}
tmp = OUT + ".tmp"
with open(tmp, "w") as f:
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
os.replace(tmp, OUT)
