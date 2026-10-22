#!/usr/bin/env -S python3 -I
"""Convert the saved STRING_AGG block queries into precinct_blocks.json
{"COUNTY":{"code":{"tot":N,"blocks":[[blockGEOID,n],...]}}} and read block interior points from the TIGER dbf
into block_pts.json {blockGEOID:[lon,lat]} (only blocks referenced by a precinct)."""
import json, sys, os, shapefile
here = os.path.dirname(os.path.abspath(__file__))
pb = {}
for p in sys.argv[1:]:
    d = json.load(open(p)); assert d['jobComplete']; assert len(d['rows']) < 3000, (p, len(d['rows']))
    cols = [f['name'] for f in d['schema']['fields']]; assert cols[:4] == ['county','precinct','voters_with_block','blocks'], cols
    for r in d['rows']:
        v = [f['v'] for f in r['f']]
        pb.setdefault(v[0], {})[v[1]] = {'tot': int(v[2]), 'blocks': [[b.split(':')[0], int(b.split(':')[1])] for b in v[3].split(',')]}
    print(p[-10:], len(d['rows']))
json.dump(pb, open(os.path.join(here, 'precinct_blocks.json'), 'w'), separators=(',', ':'))
need = {b for c in pb.values() for info in c.values() for b, _ in info['blocks']}
print('counties', len(pb), 'precincts', sum(len(c) for c in pb.values()), 'blocks needed', len(need))
sf = shapefile.Reader(os.path.join(here, 'dl', 'tl', 'tl_2020_37_tabblock20'))
fields = [f[0] for f in sf.fields[1:]]
iG, iLat, iLon = fields.index('GEOID20'), fields.index('INTPTLAT20'), fields.index('INTPTLON20')
pts = {}
for rec in sf.iterRecords(fields=['GEOID20', 'INTPTLAT20', 'INTPTLON20']):
    g = rec[0]
    if g in need: pts[g] = [float(rec[2]), float(rec[1])]
json.dump(pts, open(os.path.join(here, 'block_pts.json'), 'w'), separators=(',', ':'))
print('block points found', len(pts), 'missing', len(need - set(pts)), list(need - set(pts))[:5])
