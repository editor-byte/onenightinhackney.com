"""Refresh data/council.json, the map's backup copy of Hackney Council's open map data.

The map loads council data live from map2.hackney.gov.uk. If that server is down,
it falls back to this file. Run weekly by .github/workflows/update-council-data.yml,
or by hand:  python scripts/update_council_data.py

Safety check: a layer is only replaced if the new download looks sane (enough
features, all with locations). Otherwise the last good copy of that layer is kept.
Personal details in the licensing register (licence holders, supervisors) are
never requested.
"""
import json
import pathlib
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "council.json"
WFS = ("https://map2.hackney.gov.uk/geoserver/ows?service=WFS&version=2.0&request=GetFeature"
       "&outputFormat=application/json&SrsName=EPSG:4326&typeName=")

# Keep these in step with the same lists in index.html
BAR_CATS = ["Pub/Bar", "Night club", "Bar/Restaurant", "Bar/Café", "Café/Bar", "Bar", "Social Club"]
FOOD_CATS = ["Takeaway", "Restaurant", "Cafe", "Bakery"]
SHOP_CATS = ["Off-licence", "Off licence", "Off Licence", "Supermarket", "Large supermarket"]
q = lambda s: "'" + s.replace("'", "''") + "'"
LIC_CQL = (f"licence_status='Issued' AND (category IN ({','.join(map(q, BAR_CATS + SHOP_CATS))}) "
           f"OR (category IN ({','.join(map(q, FOOD_CATS))}) AND latenighttime1 IS NOT NULL))")
LIC_PROPS = ("mauref,premises_name,premises_full_address,category,openinghourstimes1,alcoholtimes1,"
             "alcoholsaletype,latenighttime1,livemusic,performanceofdance,geom")

# key used by the map -> (layer name, properties, filter, minimum sensible number of features)
LAYERS = {
    "amenities:hackney_nights_accredited_venues": ("amenities:hackney_nights_accredited_venues",
        "mauref,premises_name,premises_address,toilet_use_to_public,geom", None, 20),
    "licensing:licensing_act_2003_premises": ("licensing:licensing_act_2003_premises", LIC_PROPS, LIC_CQL, 300),
    "amenities:public_toilet": ("amenities:public_toilet", None, None, 10),
    "amenities:drinking_fountain_combined": ("amenities:drinking_fountain_combined", "name,location,type,geom", None, 10),
    "health:pharmacy": ("health:pharmacy", "trading_name,full_address,geom", None, 30),
    "amenities:sexual_health_service": ("amenities:sexual_health_service", "name,geom", None, 20),
    "cycle": ("enforcement:nte_safe_routes", "source,geom", "source <> 'London bus network'", 20),
}


def rnd(c):
    return [rnd(x) for x in c] if isinstance(c[0], list) else [round(c[0], 5), round(c[1], 5)]


def fetch(name, props, cql):
    url = WFS + urllib.parse.quote(name)
    if props:
        url += "&propertyName=" + urllib.parse.quote(props)
    if cql:
        url += "&cql_filter=" + urllib.parse.quote(cql)
    req = urllib.request.Request(url, headers={"User-Agent": "onenightinhackney.com map data refresh"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    return [{"p": {k: v for k, v in f["properties"].items() if v not in (None, "")},
             "g": {"type": f["geometry"]["type"], "coordinates": rnd(f["geometry"]["coordinates"])}}
            for f in d.get("features", []) if f.get("geometry")]


def main():
    old = json.loads(OUT.read_text()) if OUT.exists() else {"layers": {}, "updated": {}}
    layers, updated = dict(old.get("layers", {})), dict(old.get("updated", {}))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    changed, problems = [], []
    for key, (name, props, cql, minimum) in LAYERS.items():
        try:
            feats = fetch(name, props, cql)
        except Exception as e:  # network or server error: keep last good copy
            problems.append(f"{key}: download failed ({e})")
            continue
        if len(feats) < minimum:
            problems.append(f"{key}: only {len(feats)} features (expected at least {minimum}), kept last good copy")
            continue
        new = {"features": feats}
        if layers.get(key) != new:
            layers[key] = new
            updated[key] = now
            changed.append(f"{key} ({len(feats)})")
        print(f"ok  {key}: {len(feats)} features")

    for p in problems:
        print("WARN " + p)
    if not layers:
        print("No usable council data at all; nothing written.")
        return 1
    if changed:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"source": "Hackney Council open map data (map2.hackney.gov.uk)",
                                   "updated": updated, "layers": layers},
                                  separators=(",", ":"), ensure_ascii=False))
        print("Updated: " + ", ".join(changed))
    else:
        print("No changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
