"""Read the best-estimate ice-sheet outlines of Batchelor et al. (2019) and the authors' area table.

For each of the 18 time slices: check the file is a shapefile and read its projection; reproject the LGM file (the
only one in geographic coordinates) to the North Pole Lambert azimuthal equal-area projection used by all the others,
after adding vertices every 0.05 degrees; repair invalid rings; keep Northern Hemisphere parts only (two files, 45 ka
and the late Gauss Chron, also carry present-day glaciers of the whole world, Antarctica included); dissolve to one
outline. Areas are measured in the equal-area projection.

Writes WORK/ice_laea.pkl (full detail, for 03), data/ice_outlines.geojson (WGS84, simplified to 1.5 km),
data/ice_page.json (WGS84, simplified to 7 km without parts or holes under 250 km2, for the page), data/batchelor_area_table.csv (the authors' table,
best, minimum and maximum hypotheses) and WORK/clean.json (checks)."""
import pickle, warnings
import numpy as np, pandas as pd, shapely, geopandas as gpd
from shapely import make_valid
from shapely.geometry import box, mapping, shape
from shapely.ops import unary_union
from pyproj import CRS, Transformer
from common import *
warnings.filterwarnings("ignore")

TOLL = Transformer.from_crs(LAEA, 4326, always_xy=True)
CHECK = {"files": {}, "dropped_sh": {}, "invalid_in": {}}


def shp_path(k):
    i = SINFO[k]
    d = os.path.join(RAW, "bat19", i["folder"])
    sub = [x for x in os.listdir(d) if x.startswith("hypothesised")]
    assert len(sub) == 1, (k, sub)
    return os.path.join(d, sub[0], f"{i['stem']}_best_estimate.shp")


def is_shapefile(p):
    with open(p, "rb") as f:
        head = f.read(4)
    return head == b"\x00\x00\x27\x0a"


def read_stage(k):
    p = shp_path(k)
    assert is_shapefile(p), p
    g = gpd.read_file(p)
    crs = g.crs
    CHECK["files"][k] = {"ok": True, "features": len(g), "crs": crs.name, "geographic": crs.is_geographic}
    if crs.is_geographic:
        assert crs.to_epsg() == 4326, crs
        g["geometry"] = g.geometry.segmentize(0.05)
    else:   # North_Pole_Lambert_Azimuthal_Equal_Area on WGS84: check it is the same projection as LAEA
        assert CRS(crs).equals(CRS(LAEA)) or (crs.to_dict().get("proj") == "laea" and crs.to_dict().get("lat_0") == 90 and crs.to_dict().get("lon_0") == 0), crs.to_dict()
    g = g.to_crs(LAEA)
    CHECK["invalid_in"][k] = int((~g.is_valid).sum())
    keep, drop = [], []
    for geom in g.geometry:
        for p_ in flat_polys(make_valid(geom)):
            if p_.area < 1: continue
            lon, lat = TOLL.transform(*p_.representative_point().coords[0])
            (keep if lat > 0 else drop).append(p_)
    CHECK["dropped_sh"][k] = {"n": len(drop), "km2": round(sum(p_.area for p_ in drop) / 1e6)}
    u = make_valid(unary_union(keep))
    u = unary_union(list(flat_polys(u)))
    assert not u.contains(shapely.Point(0, 0)), k          # no outline covers the pole: the antimeridian split below is enough
    return u


def to_lonlat(geom, step=4000):
    """LAEA (lon_0 = 0, north polar) to WGS84. The antimeridian is the ray x = 0, y > 0: cut out a 1 m strip along it
    (and nowhere else, so no false edge appears along 0 degrees), densify, transform, and pin longitudes next to the
    cut to +180 or -180 according to the side each piece lies on."""
    out = []
    cut = geom.difference(box(-0.5, 0, 0.5, 2e7))
    for p in flat_polys(cut):
        p = p.segmentize(step)
        c = p.representative_point()
        east = c.x > 0
        def tr(ring):
            a = np.asarray(ring.coords)
            lon, lat = TOLL.transform(a[:, 0], a[:, 1])
            near = (np.abs(a[:, 0]) < 1.0) & (a[:, 1] > 0)
            lon = np.where(near, 180.0 if east else -180.0, lon)
            return np.column_stack([lon, lat])
        q = shapely.Polygon(tr(p.exterior), [tr(r) for r in p.interiors])
        if not q.is_valid: q = make_valid(q)
        out.extend(flat_polys(q))
    return shapely.MultiPolygon(out) if out else shapely.MultiPolygon()


def rnd_poly(poly, k):
    """Round a polygon's rings to k decimals, dropping repeated points and rings that collapse."""
    out = []
    for ring in poly:
        r = []
        for x, y in ring:
            q = [round(x, k), round(y, k)]
            if not r or q != r[-1]: r.append(q)
        if len(r) >= 4 and r[0] == r[-1]: out.append(r)
        elif not out: return None          # the exterior collapsed: drop the polygon
    return out


def rnd(coords, k):
    return [q for q in (rnd_poly(p, k) for p in coords) if q]


def lonlat_feature(k, g, tol, min_km2, k_dec, area, step):
    keep = []
    for p in flat_polys(g.simplify(tol, preserve_topology=True)):
        if p.area < min_km2 * 1e6: continue
        keep.append(shapely.Polygon(p.exterior, [r for r in p.interiors if shapely.Polygon(r).area >= min_km2 * 1e6]))
    s = shapely.MultiPolygon(keep)
    ll = to_lonlat(s, step)
    gm = mapping(ll)
    i = SINFO.get(k, {"label": "", "name": "", "age": ""})
    return {"type": "Feature", "properties": {"key": k, "label": i["label"], "name": i["name"], "age": i["age"],
            "area_km2": area, "source": BAT_SHORT + ", best estimate"},
            "geometry": {"type": "MultiPolygon", "coordinates": rnd(gm["coordinates"], k_dec)}}


# ---- authors' table
X = pd.read_excel(os.path.join(RAW, "bat19", "Quaternary_Ice_sheets_areas.xlsx"), header=None).dropna(how="all").dropna(axis=1, how="all")
assert list(X.iloc[0]) == ["Time step", "EIS area (km2)", "GIS area (km2)", "LIS area (km2)", "CIS area (km2)", "Others area (km2)", "Total area (km2)"], list(X.iloc[0])
X = X.iloc[1:].copy()
X.columns = ["step", "EIS", "GIS", "LIS", "CIS", "Others", "Total"]
X["step"] = X["step"].astype(str).str.replace(" ", "")
rows = []
for k in SKEYS:
    for hyp in ("best", "min", "max"):
        m = X[X["step"] == XLSX_ROW[k].replace(" ", "") + hyp]
        if hyp != "best" and k == "lgm":
            assert m.empty; continue
        assert len(m) == 1, (k, hyp)
        r = m.iloc[0]
        assert abs(r[["EIS", "GIS", "LIS", "CIS", "Others"]].sum() - r["Total"]) < 2, (k, hyp)      # the table adds up
        rows.append({"stage": k, "label": SINFO[k]["label"], "hypothesis": hyp, **{c: int(r[c]) for c in ["EIS", "GIS", "LIS", "CIS", "Others", "Total"]}})
T = pd.DataFrame(rows)
T.to_csv(f"{DATA}/batchelor_area_table.csv", index=False)

# ---- outlines
ICE, feats, pagef = {}, [], []
for k in SKEYS:
    g = read_stage(k)
    ICE[k] = g
    a = round(g.area / 1e6)
    best = int(T[(T.stage == k) & (T.hypothesis == "best")].Total.iloc[0])
    print(f"{k:7s} {a:>11,} km2   authors' table {best:>11,}   diff {100 * (a - best) / best:+.1f}%   parts {len(list(flat_polys(g)))}")
    feats.append(lonlat_feature(k, g, 1500, 2, 3, a, 6000))
    pagef.append(lonlat_feature(k, g, 7000, 250, 2, a, 40000))

# the furthest the ice reached in any slice: the union of every outline
UN = make_valid(unary_union(list(ICE.values())))
UN = unary_union(list(flat_polys(UN)))
ua = round(UN.area / 1e6)
for lst, args in ((feats, (1500, 2, 3, ua, 6000)), (pagef, (7000, 250, 2, ua, 40000))):
    f = lonlat_feature("max", UN, *args)
    f["properties"].update(label="Any slice", name="Furthest extent of any slice", age="all slices")
    lst.append(f)
pickle.dump(ICE, open(f"{WORK}/ice_laea.pkl", "wb"))
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/ice_outlines.geojson")
jsave({"type": "FeatureCollection", "features": pagef}, f"{DATA}/ice_page.json")
# check the WGS84 version keeps the area (reprojected back to LAEA)
TOL = Transformer.from_crs(4326, LAEA, always_xy=True)
for f in feats:
    if f["properties"]["key"] == "max": continue
    g = shapely.transform(shape(f["geometry"]).segmentize(.05), lambda a: np.column_stack(TOL.transform(a[:, 0], a[:, 1])))
    d = 100 * (g.area / 1e6 - f["properties"]["area_km2"]) / f["properties"]["area_km2"]
    assert abs(d) < 1.0, (f["properties"]["key"], d)
    CHECK.setdefault("wgs84_area_diff_pct", {})[f["properties"]["key"]] = round(d, 3)
jsave(CHECK, f"{WORK}/clean.json", indent=1)
print({k: v for k, v in CHECK["dropped_sh"].items() if v["n"]})
print("outlines", os.path.getsize(f"{DATA}/ice_outlines.geojson") // 1024, "KB; page", os.path.getsize(f"{DATA}/ice_page.json") // 1024, "KB")
