"""Results: every number used in the page, paper, blog, collage and post goes into data/results.json, with the data
tables (data/*.csv) and the page data (data/site.json).

Reads WORK/ice_laea.pkl (01), WORK/grid.npz, WORK/rast_ice.npz and WORK/grid_checks.json (02), data/ files, Natural
Earth countries and populated places, and raw/wiki_pages.json (only to check that the figures quoted from Wikipedia
are there, with their revision ids).

Methods in brief:
- Areas: measured on each best-estimate outline in the source's polar equal-area projection (01). The authors' own
  table (best, minimum and maximum) is reported beside them.
- Countries: Natural Earth 1:10m countries, Northern Hemisphere parts, intersected with each outline in the same
  equal-area projection; whole-country areas in Equal Earth (also equal-area).
- Places: Natural Earth populated places (point in outline). Population = Natural Earth's pop_max, a rough figure
  for the city or town and its built-up area. Sums over places are a rough guide, not a census.
- Distance to the ice edge: inside or outside from the outline in the equal-area projection; the distance itself in an
  azimuthal equidistant projection centred on the place, so it is a true distance on the WGS84 ellipsoid (to within a
  kilometre or so of the 1.5 km generalisation of the edge used here).
- Southernmost reach: the lowest latitude on any outline part of 50,000 km2 or more (the authors' threshold for an
  ice sheet) between 170 W and 50 W (North America) or 12 W and 60 E (Europe).
- Exposed land: ETOPO10 grid (02). Shelf regions are boxes I drew round the named seas (common.SHELVES)."""
import pickle, warnings, html as _html
import numpy as np, pandas as pd, shapely
from scipy import ndimage
from shapely import make_valid
from shapely.geometry import shape, Point, box, mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree
from pyproj import Transformer, Geod
from common import *
warnings.filterwarnings("ignore")

ICE = pickle.load(open(f"{WORK}/ice_laea.pkl", "rb"))
G = np.load(f"{WORK}/grid.npz"); RI = dict(np.load(f"{WORK}/rast_ice.npz"))
GCH = jload(f"{WORK}/grid_checks.json"); CLEAN = jload(f"{WORK}/clean.json")
T = pd.read_csv(f"{DATA}/batchelor_area_table.csv")
TOL = Transformer.from_crs(4326, LAEA, always_xy=True); TOLL = Transformer.from_crs(LAEA, 4326, always_xy=True)
TEQ = Transformer.from_crs(4326, EQAREA, always_xy=True)
GEOD = Geod(ellps="WGS84")
MAPPED = [k for k in SKEYS if k in ICE]
R = {"meta": {"page": PAGE, "repo": REPO, "doi": DOI, "bat_doi": BAT_DOI, "osf": BAT_OSF}}
r1 = lambda v: round(float(v), 1)


def tab(k, hyp="best", col="Total"):
    m = T[(T.stage == k) & (T.hypothesis == hyp)]
    return int(m[col].iloc[0]) if len(m) else None


def ll2laea(g):
    return shapely.transform(g, lambda a: np.column_stack(TOL.transform(a[:, 0], a[:, 1])))


# ======================= 1. areas =======================
ST = {}
for k in SKEYS:
    i = SINFO[k]
    a = round(ICE[k].area / 1e6) if k in ICE else None
    ST[k] = {"key": k, "label": i["label"], "name": i["name"], "age": i["age"], "ka0": i["ka"][0], "ka1": i["ka"][1], "warm": i["warm"],
             "outline": k in ICE, "area": a, "tab_best": tab(k), "tab_min": tab(k, "min"), "tab_max": tab(k, "max"),
             "tab_regions": {c: tab(k, "best", c) for c in ("EIS", "GIS", "LIS", "CIS", "Others")}}
    if a: ST[k]["diff_pct"] = round(100 * (a - ST[k]["tab_best"]) / ST[k]["tab_best"], 1)
rank = sorted(MAPPED, key=lambda k: -ST[k]["area"])
for j, k in enumerate(rank): ST[k]["rank"] = j + 1
rank_t = sorted(SKEYS, key=lambda k: -ST[k]["tab_best"])
for j, k in enumerate(rank_t): ST[k]["rank_tab"] = j + 1
# ice on today's land and on today's sea floor (grid), and the grid's check on the vector area
land, A = G["land"], np.repeat(G["area_row"][:, None], G["land"].shape[1], axis=1)
for k in MAPPED:
    m = RI[k]
    ST[k]["on_land"] = round(float(A[m & land].sum())); ST[k]["on_sea"] = round(float(A[m & ~land].sum()))
    ST[k]["grid_check_pct"] = round(100 * (A[m].sum() - ST[k]["area"]) / ST[k]["area"], 2)
    assert abs(ST[k]["grid_check_pct"]) < 2.5, (k, ST[k]["grid_check_pct"])
    ST[k]["on_sea_pct"] = round(100 * ST[k]["on_sea"] / (ST[k]["on_land"] + ST[k]["on_sea"]), 1)
R["stages"] = ST
R["order"] = SKEYS
R["rank"] = rank
R["rank_tab"] = rank_t
L, M6 = ST["lgm"], ST["mis6"]
UN = make_valid(unary_union([ICE[k] for k in MAPPED]))
EVERY = ICE[MAPPED[0]]
for k in MAPPED[1:]: EVERY = make_valid(EVERY.intersection(ICE[k]))
def area_in(g, lo0, lo1, la0=0, la1=90):
    bx = ll2laea(box(lo0, la0, lo1, la1).segmentize(.5))
    return g.intersection(bx).area / 1e6
grl = make_valid(ll2laea(make_valid(unary_union([shape(f["geometry"]) for f in jload(f"{GEO}/ne_50m_admin_0_countries.geojson")["features"] if f["properties"]["ADM0_A3"] == "GRL"])).buffer(.5).segmentize(.1)))
ka40_asia = area_in(ICE["ka40"], 60, 180) + area_in(ICE["ka40"], -180, -170)
ka40_excess = ICE["ka40"].area / 1e6 - ST["ka40"]["tab_best"]
EVERY_GRL = EVERY.intersection(grl).area / 1e6
R["checks"] = {"ka40_asia_km2": round(ka40_asia), "ka40_excess_km2": round(ka40_excess), "ka40_tab_others": ST["ka40"]["tab_regions"]["Others"],
               "every_greenland_km2": round(EVERY_GRL), "every_greenland_pct": round(100 * EVERY_GRL / (EVERY.area / 1e6))}
print("checks:", R["checks"])
R["areas"] = {"largest": rank[0], "largest_tab": rank_t[0], "lgm_rank": L["rank"], "lgm_rank_tab": L["rank_tab"], "n_mapped": len(MAPPED), "n_stages": len(SKEYS),
              "mis6_over_lgm_pct": round(100 * (M6["area"] / L["area"] - 1)), "mis6_over_lgm_pct_tab": round(100 * (M6["tab_best"] / L["tab_best"] - 1)),
              "mis6_minus_lgm": M6["area"] - L["area"], "union": round(UN.area / 1e6), "every": round(EVERY.area / 1e6),
              "union_over_lgm_pct": round(100 * (UN.area / 1e6 / L["area"] - 1)),
              "smallest": rank[-1], "top7_same": rank[:7] == rank_t[:7],
              "max_abs_diff_pct": max(abs(ST[k]["diff_pct"]) for k in MAPPED if k != "ka40"), "ka40_diff_pct": ST["ka40"]["diff_pct"],
              "mis12_over_lgm_pct": round(100 * (ST["mis12"]["area"] / L["area"] - 1)), "mis16_over_lgm_pct": round(100 * (ST["mis16"]["area"] / L["area"] - 1)),
              "lgm_on_sea_pct": L["on_sea_pct"], "mis6_on_sea_pct": M6["on_sea_pct"]}
# 40 ka: the outline holds ice in north-east Asia that the table's "others" column does not seem to count
print("areas:", {k: ST[k]["area"] for k in rank}); print("ranks agree on top 7:", R["areas"]["top7_same"], rank[:9], rank_t[:9])

# ======================= 2. countries =======================
C10 = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]
NH = box(-180, 0, 180, 90)
SEL = {k: ICE[k] for k in MAPPED}; SEL["union"] = UN
SELB = {k: g.bounds for k, g in SEL.items()}
CROWS = []
for f in C10["features"]:
    p = f["properties"]; iso = iso_of(p)
    g = make_valid(shape(f["geometry"]))
    tot = shapely.transform(g, lambda a: np.column_stack(TEQ.transform(a[:, 0], np.clip(a[:, 1], -89.9, 89.9)))).area / 1e6
    gn = g.intersection(NH)
    if gn.is_empty: continue
    gl = make_valid(ll2laea(gn.segmentize(.1)))
    row = {"country": p.get("NAME_EN") or p["NAME"], "iso": iso, "area_km2": round(tot), "pop_est": int(p.get("POP_EST") or 0)}
    bb = gl.bounds; anyhit = False
    for k, ig in SEL.items():
        b2 = SELB[k]
        if bb[0] > b2[2] or bb[2] < b2[0] or bb[1] > b2[3] or bb[3] < b2[1]:
            row[k] = 0; continue
        a = gl.intersection(ig).area / 1e6
        row[k] = round(a); anyhit |= a > 0
    if anyhit: CROWS.append(row)
CD = pd.DataFrame(CROWS)
CD["country"] = CD["country"].replace({"People's Republic of China": "China", "United States of America": "United States"})
for k in list(SEL):
    CD[k + "_pct"] = (100 * CD[k] / CD["area_km2"]).round(1)
CD = CD.sort_values("lgm", ascending=False)
CD.to_csv(f"{DATA}/countries_under_ice.csv", index=False)
cl = CD.set_index("iso")
def ctry(iso):
    if iso not in cl.index: return {"name": iso, "area": None, "lgm": 0, "lgm_pct": 0.0, "union": 0, "union_pct": 0.0}
    r = cl.loc[iso]; return {"name": r.country, "area": int(r.area_km2), "lgm": int(r.lgm), "lgm_pct": float(r.lgm_pct), "union": int(r.union), "union_pct": float(r.union_pct)}
R["countries"] = {
    "lgm_any": int((CD.lgm_pct >= 1).sum()), "union_any": int((CD.union_pct >= 1).sum()),
    "lgm_ge90": sorted(CD[CD.lgm_pct >= 90].country.tolist()), "union_ge90": sorted(CD[CD.union_pct >= 90].country.tolist()),
    "lgm_ge90_n": int((CD.lgm_pct >= 90).sum()), "union_ge90_n": int((CD.union_pct >= 90).sum()),
    "lgm_top_area": [{"name": r.country, "iso": r.iso, "km2": int(r.lgm), "pct": float(r.lgm_pct)} for r in CD.sort_values("lgm", ascending=False).head(12).itertuples()],
    "lgm_top_pct": [{"name": r.country, "iso": r.iso, "km2": int(r.lgm), "pct": float(r.lgm_pct)} for r in CD[CD.area_km2 > 20000].sort_values("lgm_pct", ascending=False).head(25).itertuples()],
    "union_top_pct": [{"name": r.country, "iso": r.iso, "km2": int(r.union), "pct": float(r.union_pct)} for r in CD[CD.area_km2 > 20000].sort_values("union_pct", ascending=False).head(30).itertuples()],
    "by_iso": {iso: ctry(iso) for iso in ("CAN", "USA", "GBR", "IRL", "DEU", "POL", "RUS", "NOR", "SWE", "FIN", "DNK", "NLD", "BLR", "UKR", "EST", "LVA", "LTU", "ISL", "GRL", "KAZ", "FRA", "BEL", "CZE")}}
print("countries ≥1% LGM:", R["countries"]["lgm_any"], "≥90% LGM:", R["countries"]["lgm_ge90"])

# ======================= 3. places =======================
PP = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")["features"]
PL = pd.DataFrame([{"name": dash(re.sub(r"\s+", " ", f["properties"]["name"])), "country": dash(f["properties"]["adm0name"]), "iso": f["properties"]["adm0_a3"],
                    "lat": f["properties"]["latitude"], "lon": f["properties"]["longitude"], "pop": int(f["properties"]["pop_max"] or 0)} for f in PP])
px, py = TOL.transform(PL.lon.values, PL.lat.values)
pts = shapely.points(px, py)
for k, g in SEL.items():
    shapely.prepare(g)
    PL[k] = shapely.contains(g, pts)
PL["n_stages"] = PL[MAPPED].sum(1)
PL.sort_values("pop", ascending=False).to_csv(f"{DATA}/places_under_ice.csv", index=False)
def plist(mask, n=12):
    return [{"name": r.name, "country": r.country, "pop": int(r.pop), "lat": r.lat, "lon": r.lon} for r in PL[mask].sort_values("pop", ascending=False).head(n).itertuples()]
PS = {}
for k in list(SEL):
    m = PL[k]
    PS[k] = {"n": int(m.sum()), "pop": int(PL["pop"][m].sum()), "n_100k": int((m & (PL["pop"] >= 1e5)).sum()), "n_1m": int((m & (PL["pop"] >= 1e6)).sum()), "top": plist(m, 8)}
R["places"] = {"total_n": len(PL), "total_pop": int(PL["pop"].sum()), **{k: PS[k] for k in ("lgm", "union")},
               "lgm_pop_m": round(PS["lgm"]["pop"] / 1e6, 1), "union_pop_m": round(PS["union"]["pop"] / 1e6, 1),
               "lgm_top": plist(PL.lgm, 15), "union_not_lgm_top": plist(PL.union & ~PL.lgm, 12),
               "most_stages_big": plist((PL.n_stages >= 12) & (PL["pop"] >= 1e6), 12)}
for k in MAPPED: ST[k]["places"] = PS[k]
print("places under LGM ice:", PS["lgm"]["n"], f"{PS['lgm']['pop']:,}", "; union:", PS["union"]["n"], f"{PS['union']['pop']:,}")

# ======================= 4. distance to the ice edge =======================
BND = {k: make_valid(ICE[k]).boundary for k in MAPPED}
for b in BND.values(): shapely.prepare(b)


def edge_km(lon, lat, k):
    """Signed distance (km) from a place to the stage's ice edge: negative inside the ice."""
    x, y = TOL.transform(lon, lat); P = Point(x, y)
    inside = ICE[k].contains(P)
    d0 = BND[k].distance(P)
    seg = BND[k].intersection(P.buffer(d0 * 1.6 + 150e3)).segmentize(2000)
    aeqd = Transformer.from_crs(LAEA, f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m", always_xy=True)
    sa = shapely.transform(seg, lambda a: np.column_stack(aeqd.transform(a[:, 0], a[:, 1])))
    d = sa.distance(Point(0, 0)) / 1000
    return round(-d if inside else d, 1)


PICK = []
for nm, iso in CITY_PICKS:
    c = PL[(PL.name == nm) & (PL.iso == iso)].sort_values("pop", ascending=False)
    assert len(c), nm
    c = c.iloc[0]
    row = {"name": CITY_SHOW.get(nm, nm), "iso": iso, "country": c.country, "lat": round(c.lat, 3), "lon": round(c.lon, 3), "pop": int(c["pop"])}
    for k in MAPPED: row[k] = edge_km(c.lon, c.lat, k)
    row["stages_under"] = [k for k in MAPPED if row[k] < 0]
    row["n_under"] = len(row["stages_under"])
    row["nearest_stage"] = min(MAPPED, key=lambda k: row[k]) if not row["stages_under"] else None
    PICK.append(row)
pd.DataFrame(PICK).drop(columns=["stages_under"]).to_csv(f"{DATA}/city_distance_to_ice.csv", index=False)
CP = {r["name"]: r for r in PICK}
R["cities"] = {r["name"]: {"lgm": r["lgm"], "under": r["stages_under"], "n_under": r["n_under"], "pop": r["pop"], "country": r["country"],
                           "closest": (None if r["n_under"] else {"stage": r["nearest_stage"], "km": r[r["nearest_stage"]]}),
                           **{k: r[k] for k in MAPPED}} for r in PICK}
R["city_list"] = [r["name"] for r in sorted(PICK, key=lambda r: r["lgm"])]
for r in PICK: print(f"  {r['name']:16s} LGM {r['lgm']:8.1f} km   under {r['n_under']:2d}: {','.join(r['stages_under'])}")
# the LGM check against Wikipedia ("eastward to Manhattan"): New York sits near the LGM edge
R["cities_extra"] = {"ny_lgm_abs": abs(CP["New York"]["lgm"])}

# ======================= 5. southernmost reach =======================
SECT = {"na": (-170, -50), "eu": (-12, 60)}
SOUTH = {}
big = PL[PL["pop"] >= 50000]
bpx, bpy = TOL.transform(big.lon.values, big.lat.values)
for k in MAPPED:
    SOUTH[k] = {}
    parts = [p for p in flat_polys(ICE[k]) if p.area >= 5e10]
    for sk, (lo0, lo1) in SECT.items():
        best = None
        for p in parts:
            a = np.asarray(p.exterior.segmentize(3000).coords)
            lon, lat = TOLL.transform(a[:, 0], a[:, 1])
            m = (lon >= lo0) & (lon <= lo1)
            if not m.any(): continue
            j = np.argmin(np.where(m, lat, 99))
            if best is None or lat[j] < best[1]: best = (float(lon[j]), float(lat[j]), p.area / 1e6)
        if best is None: SOUTH[k][sk] = None; continue
        _, _, dd = GEOD.inv(np.full(len(big), best[0]), np.full(len(big), best[1]), big.lon.values, big.lat.values)
        j = int(np.argmin(dd)); nb = big.iloc[j]
        SOUTH[k][sk] = {"lon": round(best[0], 2), "lat": round(best[1], 2), "part_km2": round(best[2]), "near": nb["name"], "near_country": nb.country, "near_km": round(dd[j] / 1000)}
    ST[k]["south"] = SOUTH[k]
SR = [{"stage": k, "label": SINFO[k]["label"], **{f"{s}_{f}": (SOUTH[k][s] or {}).get(f) for s in SECT for f in ("lat", "lon", "near", "near_country", "near_km")}} for k in MAPPED]
pd.DataFrame(SR).to_csv(f"{DATA}/southern_reach.csv", index=False)
na_min = min(MAPPED, key=lambda k: SOUTH[k]["na"]["lat"]); eu_min = min((k for k in MAPPED if SOUTH[k]["eu"]), key=lambda k: SOUTH[k]["eu"]["lat"])
def south_in(k, lo0, lo1):
    best = 99
    for p in flat_polys(ICE[k]):
        if p.area < 5e10: continue
        a = np.asarray(p.exterior.segmentize(3000).coords); lon, lat = TOLL.transform(a[:, 0], a[:, 1])
        m = (lon >= lo0) & (lon <= lo1)
        if m.any(): best = min(best, float(lat[m].min()))
    return round(best, 2)
_, _, d_cairo = GEOD.inv(SOUTH["mis12"]["na"]["lon"], SOUTH["mis12"]["na"]["lat"], -89.176, 37.005)   # Cairo, Illinois: the Ohio meets the Mississippi
R["south_extra"] = {"lgm_eu_mainland_lat": south_in("lgm", 5, 40), "na_min_to_ohio_mouth_km": round(d_cairo / 1000)}
R["south"] = {"na_min_stage": na_min, "na_min": SOUTH[na_min]["na"], "eu_min_stage": eu_min, "eu_min": SOUTH[eu_min]["eu"],
              "lgm_na": SOUTH["lgm"]["na"], "lgm_eu": SOUTH["lgm"]["eu"], "mis6_eu": SOUTH["mis6"]["eu"], "mis6_na": SOUTH["mis6"]["na"],
              "mis12_eu": SOUTH["mis12"]["eu"], "na_min_label": SINFO[na_min]["label"], "eu_min_label": SINFO[eu_min]["label"],
              "na_min_same": sorted(k for k in MAPPED if abs(SOUTH[k]["na"]["lat"] - SOUTH[na_min]["na"]["lat"]) < .05)}
for k in MAPPED: print(f"  south {k:7s} NA {SOUTH[k]['na']['lat']:6.2f} {SOUTH[k]['na']['near']:15s} EU {SOUTH[k]['eu']['lat'] if SOUTH[k]['eu'] else None} {(SOUTH[k]['eu'] or {}).get('near')}")

# ======================= 6. exposed land =======================
ocean, bed = G["ocean"], G["bed"].astype(int)
lat_c, lon_c = G["lat_c"], G["lon_c"]
LON, LAT = np.meshgrid(lon_c, lat_c)
lgm_ice = RI["lgm"]
X = {}
for S, key in ((SEA_HALF, "exp60"), (SEA_LGM, "exp120")):
    m = G[key]
    X[S] = {"km2": round(float(A[m].sum())), "ice_free": round(float(A[m & ~lgm_ice].sum())), "under_lgm_ice": round(float(A[m & lgm_ice].sum()))}
    X[S]["pct_of_land"] = round(100 * X[S]["km2"] / GCH["land_km2"], 1)
    X[S]["ice_free_pct_of_land"] = round(100 * X[S]["ice_free"] / GCH["land_km2"], 1)
R["exposed"] = {"m60": X[SEA_HALF], "m120": X[SEA_LGM], "land_today": GCH["land_km2"], "ocean_today": GCH["sea_kept_km2"], "earth": GCH["earth_km2"],
                "m120_ocean_pct": round(100 * X[SEA_LGM]["km2"] / GCH["sea_kept_km2"], 1),
                "half_share_pct": round(100 * X[SEA_HALF]["km2"] / X[SEA_LGM]["km2"])}
SH = []
for nm, desc, boxes in SHELVES:
    inb = np.zeros_like(ocean)
    for lo0, la0, lo1, la1 in boxes: inb |= (LON >= lo0) & (LON <= lo1) & (LAT >= la0) & (LAT <= la1)
    row = {"region": nm, "covers": desc, "boxes": boxes}
    for S, key in ((SEA_HALF, "exp60"), (SEA_LGM, "exp120")):
        m = G[key] & inb
        row[f"m{-S}"] = round(float(A[m].sum())); row[f"m{-S}_ice_free"] = round(float(A[m & ~lgm_ice].sum()))
    row["land_today"] = round(float(A[inb & land].sum()))
    SH.append(row)
SH.sort(key=lambda r: -r["m120_ice_free"])
pd.DataFrame([{k: v for k, v in r.items() if k != "boxes"} for r in SH]).to_csv(f"{DATA}/exposed_shelves.csv", index=False)
R["shelves"] = SH; SHD = {r["region"]: r for r in SH}
R["shelf"] = {r["region"].split(" ")[0].lower(): r for r in SH}
R["exposed"]["boxes_share_pct"] = round(100 * sum(r["m120_ice_free"] for r in SH) / X[SEA_LGM]["ice_free"])
# land bridges: which of today's landmasses are joined at 0, -60 and -120 m (land today plus exposed sea floor)
def comp(mask):
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    for r_ in range(lab.shape[0]):              # join across the 180 degree seam
        for rr in (r_ - 1, r_, r_ + 1):
            if 0 <= rr < lab.shape[0] and lab[r_, 0] and lab[rr, -1] and lab[r_, 0] != lab[rr, -1]:
                a_, b_ = lab[r_, 0], lab[rr, -1]; lab[lab == b_] = a_
    return lab
cell = lambda lo, la: (int(round((90 - la) * 6)), int(round((lo + 180) * 6)) % len(lon_c))
LABS = {0: comp(land), SEA_HALF: comp(land | G["exp60"]), SEA_LGM: comp(land | G["exp120"])}
JO = []
for a_, b_, pa, pb in JOINS:
    ca, cb = cell(*pa), cell(*pb)
    assert land[ca] and land[cb], (a_, b_)
    JO.append({"a": a_, "b": b_, **{f"m{-S}": bool(LABS[S][ca] == LABS[S][cb]) for S in (0, SEA_HALF, SEA_LGM)}})
assert not any(j["m0"] for j in JO), [j for j in JO if j["m0"]]     # nothing joined at today's sea level
R["joins"] = JO; JD = {j["a"]: j for j in JO}
# the Bering land bridge: north-south extent of land at -120 m along the strait's meridian (168.75 W)
col = cell(-168.75, 65.75)[1]; r0 = cell(-168.75, 65.75)[0]
L120 = land | G["exp120"]
assert L120[r0, col]
up = r0
while up > 0 and L120[up - 1, col]: up -= 1
dn = r0
while dn < len(lat_c) - 1 and L120[dn + 1, col]: dn += 1
_, _, wkm = GEOD.inv(-168.75, lat_c[dn] - 1 / 12, -168.75, lat_c[up] + 1 / 12)
R["bering"] = {"width_km": round(wkm / 1000), "south_lat": round(float(lat_c[dn] - 1 / 12), 2), "north_lat": round(float(lat_c[up] + 1 / 12), 2),
               "strait_bed": int(bed[r0, col])}
# Sahul and Sunda totals (today's land plus exposed, in the boxes) against the Wikipedia figures
for nm in ("Sahul", "Sundaland", "Beringia", "Doggerland"):
    r = SHD[nm]; r["total_m120"] = r["land_today"] + r["m120"]
print("exposed:", R["exposed"]); print("shelves:", [(r["region"], r["m120_ice_free"]) for r in SH]); print("joins:", JO); print("bering", R["bering"])

# ======================= 7. Wikipedia figures (checked against the saved pages) =======================
WK = jload(f"{RAW}/wiki_pages.json")
def wtext(t):
    s = re.sub(r"<style.*?</style>|<sup.*?</sup>", "", WK[t]["html"], flags=re.S)
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", "", s)))
QUOTES = {"lgm_window": ("Last Glacial Maximum", "at their greatest extent between 26,000 and 20,000 years ago"),
          "lgm_sea": ("Last Glacial Maximum", "the sea level was about 125 meters (about 410 feet) lower than it is today"),
          "quat_sea": ("Quaternary glaciation", "sea level about 120 metres (394 ft) lower than present"),
          "manhattan": ("Last Glacial Maximum", "extended roughly to the Missouri and Ohio Rivers, and eastward to Manhattan"),
          "beringia_wide": ("Beringia", "up to 1,000 km (620 mi) wide"), "beringia_area": ("Beringia", "totaling about 1.6 million km"),
          "bering_depth": ("Beringia", "the average water depth of the Bering Strait is 40–50 m"),
          "sunda_area": ("Sundaland", "the area of Sundaland is approximately 1,800,000 km"),
          "sunda_120": ("Sundaland", "The extent of the Sunda Shelf is approximately equal to the 120-meter isobath"),
          "sahul_area": ("Sahul", "approximately 10,600,000 square kilometres"),
          "sahul_split": ("Sahul", "New Guinea separated from mainland Australia about 8,000 years ago, and Tasmania about 6,000 years ago"),
          "dogger_flood": ("Doggerland", "Between 10,000 and 7,000 years ago, Doggerland was inundated by rising sea levels"),
          "bis_anglian": ("British-Irish Ice Sheet", "It probably reached its maximum extent during the Anglian Glaciation"),
          "fis_lgm": ("Fennoscandian ice sheet", "The Last Glacial Maximum extent was first reached 22 ka BP in the southern boundary of the ice sheet in Denmark, Germany and Western Poland"),
          "lis_dome": ("Laurentide Ice Sheet", "Keewatin Dome: 3,200 metres")}
R["wiki"] = {}
for k, (t, q) in QUOTES.items():
    assert q in wtext(t), (k, t, q)
    R["wiki"][k] = {"article": t, "revid": WK[t]["revid"]}
R["wiki_revs"] = {t: WK[t]["revid"] for t in WK}

# ======================= 8. source notes and checks =======================
R["source"] = {"n_stages": len(SKEYS), "n_mapped": len(MAPPED), "missing": [k for k in SKEYS if k not in ICE],
               "dropped_sh_km2": CLEAN["dropped_sh"]["ka45"]["km2"], "dropped_sh_stages": [k for k, v in CLEAN["dropped_sh"].items() if v["n"]],
               "lgm_geographic": CLEAN["files"]["lgm"]["geographic"], "invalid_in": sum(1 for v in CLEAN["invalid_in"].values() if v),
               "grid_land": GCH["land_km2"], "caspian_km2": GCH["caspian_km2"], "black_sea_kept": list(GCH["other_seas_kept_km2"].values())[0] if GCH["other_seas_kept_km2"] else 0}
R["warm"] = [k for k in SKEYS if SINFO[k]["warm"]]

# ---- convenience values for the text
R["x"] = {"lgm_area_m": round(L["area"] / 1e6, 1), "mis6_area_m": round(M6["area"] / 1e6, 1), "union_m": round(R["areas"]["union"] / 1e6, 1),
          "lgm_on_land_m": round(L["on_land"] / 1e6, 1), "lgm_on_sea_m": round(L["on_sea"] / 1e6, 1),
          "exp120_m": round(X[SEA_LGM]["km2"] / 1e6, 1), "exp120_free_m": round(X[SEA_LGM]["ice_free"] / 1e6, 1), "exp60_m": round(X[SEA_HALF]["km2"] / 1e6, 1),
          "smallest_area_m": round(ST[rank[-1]]["area"] / 1e6, 1),
          "lgm_places_pct": round(100 * PS["lgm"]["pop"] / R["places"]["total_pop"], 1), "every_m": round(R["areas"]["every"] / 1e6, 1),
          "mis6_south_na_lat": SOUTH["mis6"]["na"]["lat"], "warm_max_m": round(max(ST[k]["area"] for k in R["warm"] if k in ICE) / 1e6, 1),
          "doggerland_free_k": round(SHD["Doggerland"]["m120_ice_free"] / 1000), "joined60_n": sum(j["m60"] for j in JO), "joins_n": len(JO)}
for k in MAPPED: ST[k]["lgm_ratio_pct"] = round(100 * ST[k]["area"] / L["area"])

# ======================= site.json: page data =======================
SITE = {"stages": [{k2: v for k2, v in ST[k].items() if k2 not in ("places",)} | {"places_n": ST[k].get("places", {}).get("n"), "places_pop": ST[k].get("places", {}).get("pop"),
                    "places_top": [[p["name"], p["country"], p["pop"]] for p in ST[k].get("places", {}).get("top", [])[:6]],
                    "countries_top": [[r.country, int(r[k]), float(r[k + "_pct"])] for r in [rw for _, rw in CD.sort_values(k, ascending=False).head(6).iterrows()] if r[k] > 0] if k in MAPPED else []}
                   for k in SKEYS],
        "cities": [{"name": r["name"], "country": r["country"], "lat": r["lat"], "lon": r["lon"], "pop": r["pop"], "d": [r.get(k) for k in SKEYS]} for r in PICK],
        "shelves": [{"name": r["region"], "covers": r["covers"], "m60": r["m60_ice_free"], "m120": r["m120_ice_free"], "boxes": r["boxes"]} for r in SH],
        "joins": JO}
jsave(SITE, f"{DATA}/site.json")
pd.DataFrame([{"stage": k, "label": SINFO[k]["label"], "age": SINFO[k]["age"], "outline_in_this_copy": k in ICE, "warm_slice_minimum_ice": SINFO[k]["warm"],
               "area_km2_measured": ST[k]["area"], "rank_measured": ST[k].get("rank"), "authors_best_km2": ST[k]["tab_best"], "authors_min_km2": ST[k]["tab_min"],
               "authors_max_km2": ST[k]["tab_max"], "rank_authors": ST[k]["rank_tab"], "on_todays_land_km2": ST[k].get("on_land"), "on_todays_sea_km2": ST[k].get("on_sea"),
               "places_under_ice": ST[k].get("places", {}).get("n"), "places_pop_max_sum": ST[k].get("places", {}).get("pop")} for k in SKEYS]).to_csv(f"{DATA}/stage_areas.csv", index=False)
jsave(R, f"{DATA}/results.json", indent=1)
print("results.json", os.path.getsize(f"{DATA}/results.json") // 1024, "KB; site.json", os.path.getsize(f"{DATA}/site.json") // 1024, "KB")
