# One Night in Hackney – night map

The map at onenightinhackney.com: Hackney Nights accredited venues, licensed hours, public toilets, water, help and late-night essentials, buses and safe cycle routes. Four styles: Linocut, Risograph, Pen & ink and Accessible.

## Files

| File | What it does |
| --- | --- |
| `index.html` | The map page. |
| `data/council.json` | Backup copy of Hackney Council's open map data, used only if the council's server is down. |
| `scripts/update_council_data.py` | Refreshes `data/council.json`. |
| `.github/workflows/update-council-data.yml` | Runs the script every Monday at 05:17 UTC and saves any changes. |

## Where the data comes from

Loaded live in the visitor's browser, no API keys needed:

- **Hackney Council** (map2.hackney.gov.uk): accredited venues, licensing register, toilets, fountains, pharmacies, sexual health services, safe cycle routes.
- **OpenStreetMap** via Overpass: opening hours, wheelchair access, police stations, A&E.
- **TfL**: bus routes and nearby stops.
- **OpenFreeMap**: the background map.

## The weekly job

- It only replaces a layer if the new download passes a safety check: enough entries, all with locations. Otherwise it keeps the last good copy and logs a warning.
- To run it now: **Actions** tab → **Update council data** → **Run workflow**.
- If the "Save changes" step fails with a permissions error: **Settings → Actions → General → Workflow permissions** → choose **Read and write permissions**.
- GitHub pauses scheduled jobs in repositories with no activity for 60 days. If that happens, re-enable it from the Actions tab.

## Link to a style

Add `?style=linocut`, `?style=risograph`, `?style=ink` or `?style=access` to the address.
