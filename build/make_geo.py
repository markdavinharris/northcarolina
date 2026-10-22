#!/usr/bin/env -S python3 -I
"""North Carolina county outlines -> compact SVG paths in a 600x? box. Writes ../data/counties.json
{"w":600,"h":H,"paths":{"ALAMANCE":"M..Z",...},"centroids":{"ALAMANCE":[x,y],...}}
Source: Census cb_2023_us_county_20m shapefile (dl/cb/), STATEFP 37. County key = NAME.upper() with periods
removed (NC has none; New Hanover -> NEW HANOVER, McDowell -> MCDOWELL), which equals voters.CountyName."""
import json, math, sys, os
import shapefile
here = os.path.dirname(os.path.abspath(__file__))
sf = shapefile.Reader(os.path.join(here, 'dl', 'cb', 'cb_2023_us_county_20m'))
fields = [f[0] for f in sf.fields[1:]]
recs = [(dict(zip(fields, r.record)), r.shape) for r in sf.shapeRecords()]
nc = [(d, s) for d, s in recs if d['STATEFP'] == '37']
assert len(nc) == 100, len(nc)
# projection: simple equirectangular scaled by cos(mean lat)
lat0 = math.radians(35.5)
pts = [p for _, s in nc for p in s.points]
xs = [p[0]*math.cos(lat0) for p in pts]; ys = [p[1] for p in pts]
minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
W = 600; scale = W/(maxx-minx); H = round((maxy-miny)*scale)
def proj(p):
    return (round((p[0]*math.cos(lat0)-minx)*scale, 1), round((maxy-p[1])*scale, 1))
paths, cents = {}, {}
for d, s in nc:
    name = d['NAME'].upper().replace('.', '')
    parts = list(s.parts) + [len(s.points)]
    segs = []
    sx = sy = n = 0
    for i in range(len(parts)-1):
        ring = s.points[parts[i]:parts[i+1]]
        pp = [proj(p) for p in ring]
        out = [pp[0]]
        for q in pp[1:]:
            if q != out[-1]: out.append(q)
        segs.append('M' + ' '.join(f'{x} {y}' for x, y in out) + 'Z')
        for x, y in out: sx += x; sy += y; n += 1
    paths[name] = ''.join(segs)
    cents[name] = [round(sx/n, 1), round(sy/n, 1)]
out = {'w': W, 'h': H, 'paths': paths, 'centroids': cents}
dst = os.path.join(here, '..', 'data', 'counties.json')
json.dump(out, open(dst, 'w'), separators=(',', ':'))
print('wrote', dst, 'H=', H, 'bytes', os.path.getsize(dst), sorted(paths)[:5])
