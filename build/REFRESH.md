# North Carolina Early Vote 2026 dashboard — daily refresh runbook

Published artifact (update in place, never create a new one):
**https://claude.ai/artifact/8nzejmni9MqSKvx3yKztpi** — title "North Carolina Early Vote 2026". First published 2026-10-22
with data through 2026-10-21.

The page is a single self-contained HTML file built by `build.py` from `template.html`, `app.js`, seven JSON
data files and one static geometry file `data/counties.json` (NC county outlines as SVG paths, made once from the
Census cb_2023_us_county_20m shapefile by `geo/make_geo.py`; it never changes). All source files plus `SPEC.md`,
the merge helpers and `counties.json` are stored in this Project under `claude/northcarolina-ev-dashboard/`.

## Steps (about 20 minutes; the BigQuery queries are the slow part)

1. Make a working folder in the scratchpad, e.g. `northcarolina/` with `data/` and `bq/` subfolders. Fetch the project docs
   `claude/northcarolina-ev-dashboard/{SPEC.md,build.py,template.html,app.js,merge_county.py,merge_precinct.py,heat_merge.py,make_daily.py,cte.py,counties.json,REFRESH.md}`
   with `project_read` and write each to the working folder under its own file name (`build.py` expects
   `template.html` and `app.js` beside it, and `counties.json` inside `data/` with the query outputs; `cte.py` goes in `bq/`).
2. Re-run the queries in `SPEC.md`. Only 2026 data changes day to day, but `voters` is rebuilt occasionally, so
   re-run everything each time. Run the queries yourself with `mcp__Google_Cloud_BigQuery__execute_sql_readonly`
   (parameter name is `query`). Every result must be SAVED TO A FILE by the harness (automatic for results with a
   `pad` column; the harness names them `.../tool-results/mcp-Google_Cloud_BigQuery-execute_sql_readonly-<id>.txt`,
   copy each to `bq/` under a clear name), then converted with the helper scripts — never retype numbers:
   - `daily.json`: Query S ×3 years (+ pad) and the totals query → paste the three totals rows into `make_daily.py`'s TOT dict, then `make_daily.py data/daily.json bq/S_2026.json bq/S_2024.json bq/S_2022.json`
   - `county_daily_{2026,2024,2022}.json`: Query C in 4 county chunks each (`bq/cte.py YEAR "<chunk>"` prints the SQL) → `merge_county.py out.json c1 c2 c3 c4`
   - `heat_2026.json`, `heat_2022.json`: Query H, one query each (ASOF = the as-of day; 13 on 2026-10-22) → `heat_merge.py out.json result`
   - `precinct_2026.json`: Query P in 2 chunks → `merge_precinct.py out.json c1 c2`
   Cross-check: merge_county.py's sums for 2026 must equal make_daily.py's (they did exactly on 2026-10-22, including UNKNOWN).
   build.py WARNs that county sums differ from statewide for 2024 and 2022 — EXPECTED: the difference is the UNKNOWN-county
   rows (blank DT_Regid, NULL Jurisname: 11,041 rows in 2024, 23,669 in 2022) that are dropped from the county file.
   Any other difference is a problem.
3. `python3 build.py` → `dashboard.html` and `index.html`. It prints the as-of date (last complete day). If the
   as-of date did not move since the last run, the feed has not updated — republishing is harmless, but say so.
4. Spot-check one number independently, e.g.
   `SELECT COUNTIF(Rejected=0 AND ReturnDate BETWEEN '2026-01-01' AND '<asof>') + COUNTIF(EarlyVoted BETWEEN '2026-01-01' AND '<asof>') FROM abev_2026 WHERE State='NC'`
   must equal the "Early votes cast" tile (1,101,686 on 2026-10-21; Wake County 136,670).
5. Screenshot once with Playwright (`shot.py index.html out.png`, light, 1200 wide; it also prints the KPI tiles) and look
   at it; then publish with the Artifact tool:
   `action: publish`, `url: https://claude.ai/artifact/8nzejmni9MqSKvx3yKztpi`, `file_path: <dashboard.html>`,
   `label: "Data through <as-of date>"`, and `files: {"site/index.html": {"from": "<abs path to index.html>", "contentType": "text/html"}}`.
   Read the artifact first if the tool says it has not been read in this conversation. Do not pass `icon`.
   A publish that passes only these keeps the 100 `precincts/*.json` files already on the artifact.
6. If `template.html` or `app.js` had to change, write the changed file back to the Project at the same path
   (the Ohio, Iowa, Texas, Michigan and North Carolina kits share them; only `build.py`'s STATE block differs).
7. Report: as-of date, statewide early votes (and change vs 2024 and 2022 at the same point), net R−D, anything odd
   (rejected rows jumping, a change in the county list, a query that hit the 3,000-row cap).

## Data notes that matter
- North Carolina has party registration: party = `PartyRollUp` (`Republican` / `Democrat`; `Unaffiliated/DTS` and
  `Independent/Other` both go to the "Unaffiliated / other" bucket), from the voter file of each year. Do not use the
  ABEV party flags (zero on about a third of NC rows). NC registration on 2026-10-22: 3,145,425 unaffiliated, 2,328,931 R,
  2,320,607 D, 51,403 other, 7,846,366 total.
- NC's ABEV feed records a mail ballot only when returned: `RequestDate` = `ReturnDate` on every row, so requested =
  returned and there are no outstanding ballots (`STATE['no_requests'] = True` swaps that tile for "Mail share of early vote").
  Mail is a small share of NC's early vote (5% on 2026-10-21; 7% in 2024, 9% in 2022 at the same point).
- In-person early voting ("one-stop") runs from the third Thursday before Election Day through the last Saturday before it:
  2026-10-15 to 2026-10-31 (d=19 to d=3), 2024-10-17 to 2024-11-02, 2022-10-20 to 2022-11-05. The first EV day is d=19 in all
  three years, so same-point comparisons line up. The feed has a handful of in-person votes dated 2026-10-14 (d=20).
- The as-of day on 2026-10-22 was d=13 (2026-10-21); the feed's latest EarlyVoted was 2026-10-21 and the latest ReturnDate
  2026-10-22 (4 rows, dropped as the partial day). The feed appears to land with the previous day complete.
- ABEV `Jurisname` is "<Name> County" (title case): the CTE strips " COUNTY" after upper-casing. Rows with a blank
  `DT_Regid` (4,213 in 2026, 11,041 in 2024, 23,669 in 2022) have a NULL Jurisname and are kept as `UNKNOWN` statewide only.
- `Rejected`: 874 NC rows in 2026, 12,908 in 2024, 45,473 in 2022; excluded from request/return counts as usual.
- Unmatched ABEV rows (no voter in that year's file): 8,813 of 1,102,149 in 2026 (0.8%), 12,756 in 2024, 16,170 in 2022;
  counted as "Unaffiliated / other".
- County spelling: no aliases needed. `voters.CountyName`, the stripped Jurisname and Census NAME.upper() all agree
  (NEW HANOVER, MCDOWELL).
- Build checks: `precinct_2026.json` and every `county_daily_*.json` must have exactly 100 counties after UNKNOWN is dropped.

## Precinct maps
100 files on the artifact (`precincts/<COUNTY>.json`, spaces as underscores, e.g. `NEW_HANOVER.json`; 2.4 MB total), built once
by `geo/match_precincts.py` from the NYT 2024 precinct map (`NC-precincts-with-results.geojson.gz`, 2,655 shapes, downloaded
from `https://int.nyt.com/newsgraphics/elections/map-data/2024/national/` — the GitHub repo
`nytimes/presidential-precinct-map-2024` holds only a README linking there) matched to `voters.PrecinctCode` via each
precinct's top-8 Census 2020 blocks (`voter_contact.CensusBlock2020`, Query B in SPEC.md, 2 county chunks; interior points
from TIGER `tl_2020_37_tabblock20`, 348 MB, downloaded from www2.census.gov — both census.gov downloads worked from the cloud
session on 2026-10-22). NC's NYT precinct IDs are `37<county FIPS>-<board precinct code>`, and 2,509 of the 2,657 current codes
match a shape by name directly; the block match agreed with the name match on every one of them and placed the other 148
(Gaston renumbered all 40 precincts after 2024; Wake, Rockingham, Haywood, Harnett, Columbus, Pender, Richmond are the others).
Result on 2026-10-22: all 2,657 codes placed; 27 weak (<60% of voters' blocks in the chosen shape); 40 shapes hold more than one
code; 146 NYT shapes have no current code (mostly the counties above). Rebuild only if NC precinct codes change materially.

## Hand-off to the public site
After republishing the artifact, the standalone page is also published as the artifact FILE `site/index.html` (step 5 above,
same publish call). No GitHub Pages site exists yet for North Carolina. If one is set up (e.g. northcarolina.coldspark.com,
repo `markdavinharris/northcarolina`), follow `claude/early-vote-sites-publish.md`: the refresh task pushes `index.html` to
the repo through the session's git proxy (`add_repo` with access `push`, shallow clone, copy, commit "Data through <date>",
push to main), and the cloud-only safety-net task compares the artifact's `site/index.html` with the live site. Add the
state's row to the table in that runbook when the repo exists. The repo's first commit also needs `precincts/*.json`
(copied from `data/precincts/`), a `CNAME`, `.nojekyll` and `build/` holding this kit.
