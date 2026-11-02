"""Geography: outlines and labels (Natural Earth), the land a lower sea would expose (ETOPO10) and the shaded relief
base for the page (AWS Terrain Tiles).

1. data/world.json: Natural Earth 1:50m countries, simplified, for the page and figures; data/countries.json label
   points and names; data/cities.json: Natural Earth populated places (pop_max 200,000 or more, or a capital).
2. Exposed land, on the ETOPO10 10 arc-minute grid (the last column, 180 E, repeats 180 W and is dropped).
   Land today: ice-surface elevation above 0 m, or inside Natural Earth's land (so that dry land below sea level, such
   as the Caspian depression, counts as land). Sea today: everything else, but only water bodies joined to the world
   ocean or larger than 50,000 km2, which leaves out lakes, and never the Caspian Sea, whose level does not follow the
   ocean's. Depth of the sea floor: the bedrock version, so that floating ice shelves are not read as shallow sea.
   Exposed at a sea level S: sea today with a sea floor at or above S. Cell areas on the authalic sphere.
   Writes WORK/grid.npz (masks and cell areas, for 03), data/exposed.json (exposed land at -60 m and -120 m as
   simplified polygons) and WORK/rast_ice.npz (each stage's ice rasterised on the same grid).
3. img/relief/{z}/{x}/{y}.jpg, zoom 0 to 4: a pale shaded relief in Web Mercator from the Terrarium tiles, for the
   page's base map. Also WORK/merc_z3.npz for the figures' optional relief."""
import numpy as np, shapely, shapely.ops, rasterio.features as rf
from affine import Affine
from scipy import ndimage
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from PIL import Image
from common import *

iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]
FIX = {"CNM": "CYP", "ESB": "CYP", "WSB": "CYP", "PSX": "PSE", "SAH": "ESH", "KAS": "IND", "SOL": "SOM"}


def rnd(c, k=2):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


# ---------------- 1. outlines, labels, cities ----------------
W50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
feats, meta = [], {}
for f in W50["features"]:
    p = f["properties"]; iso = FIX.get(iso_of(p), iso_of(p))
    gs = shape(f["geometry"]).simplify(0.04, preserve_topology=True)
    if gs.is_empty: continue
    gm = mapping(gs)
    feats.append({"type": "Feature", "properties": {"iso": iso}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
    if iso not in meta:
        nm = (p.get("NAME_EN") or p["NAME"]).replace("People's Republic of China", "China").replace("United States of America", "United States")
        meta[iso] = {"name": nm, "lx": round(p["LABEL_X"], 2), "ly": round(p["LABEL_Y"], 2), "pop": float(p.get("POP_EST") or 0)}
meta.get("CYP", {}).update(name="Cyprus")
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")
jsave(meta, f"{DATA}/countries.json")

P = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")
cities = []
for f in P["features"]:
    p = f["properties"]; pop = p.get("pop_max") or 0
    if pop >= 200000 or p.get("adm0cap") == 1:
        cities.append({"name": CITY_SHOW.get(re.sub(r"\s+", " ", p["name"]), re.sub(r"\s+", " ", p["name"])), "country": p["adm0name"], "iso": p["adm0_a3"], "lat": round(p["latitude"], 3),
                       "lon": round(p["longitude"], 3), "pop": int(pop)})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")
print("countries", len(meta), "cities", len(cities), "world", os.path.getsize(f"{DATA}/world.json") // 1024, "KB")

# ---------------- 2. exposed land on the ETOPO10 grid ----------------
NR, NC = 1081, 2161
ice = np.fromfile(f"{RAW}/etopo10/etopo10_ice_g_i2.bin", "<i2").reshape(NR, NC)
bed = np.fromfile(f"{RAW}/etopo10/etopo10_bed_g_i2.bin", "<i2").reshape(NR, NC)
for nm in ("ice", "bed"):
    hdr = open(f"{RAW}/etopo10/etopo10_{nm}_g_i2.hdr").read()
    assert "NCOLS         2161" in hdr and "NROWS         1081" in hdr and "LSBFIRST" in hdr and "CELLSIZE      0.16666666667" in hdr
assert (ice[:, 0] == ice[:, -1]).all() and ice[0].mean() < -3000 and ice[-1].mean() > 2000      # row 0 is 90 N; 180 repeats -180
ice, bed = ice[:, :-1].astype(np.int32), bed[:, :-1].astype(np.int32)
NC -= 1
D = 1 / 6
lat_c = 90 - np.arange(NR) * D; lon_c = -180 + np.arange(NC) * D
RA = 6371.0072                                   # authalic radius of WGS84, km
top = np.radians(np.clip(lat_c + D / 2, -90, 90)); bot = np.radians(np.clip(lat_c - D / 2, -90, 90))
cell_km2 = RA ** 2 * np.radians(D) * (np.sin(top) - np.sin(bot))          # per row
AREA = np.repeat(cell_km2[:, None], NC, axis=1)
assert abs(AREA.sum() / (4 * np.pi * RA ** 2) - 1) < 1e-9
TR = Affine(D, 0, -180 - D / 2, 0, -D, 90 + D / 2)                         # grid cells centred on the nodes

LAND50 = jload(f"{GEO}/ne_50m_land.geojson")
ne_land = rf.rasterize(((f["geometry"], 1) for f in LAND50["features"]), out_shape=(NR, NC), transform=TR, dtype="uint8").astype(bool)
land = (ice > 0) | ne_land
sea = ~land
lab, n = ndimage.label(sea, structure=np.ones((3, 3)))
# join labels across the 180 degree seam
for r in range(NR):
    for rr in (r - 1, r, r + 1):
        if 0 <= rr < NR and lab[r, 0] and lab[rr, -1] and lab[r, 0] != lab[rr, -1]:
            a, b = lab[r, 0], lab[rr, -1]; lab[lab == b] = a
sizes = ndimage.sum(AREA, lab, index=np.arange(n + 1))
ocean_lab = int(np.argmax(sizes[1:]) + 1)
casp = lab[int(round((90 - 42) * 6)), int(round((51 + 180) * 6))]
keep = [i for i in range(1, n + 1) if (sizes[i] >= 50000 or i == ocean_lab) and i != casp]
ocean = np.isin(lab, keep)
other = {}
for i in keep:
    if i == ocean_lab: continue
    rr, cc = np.argwhere(lab == i).mean(0)
    other[f"{90 - rr * D:.1f}N {-180 + cc * D:.1f}E"] = round(float(sizes[i]))
CH = {"world_ocean_km2": round(float(sizes[ocean_lab])), "other_seas_kept_km2": other, "caspian_km2": round(float(sizes[casp])),
      "lakes_dropped_km2": round(float(sum(sizes[i] for i in range(1, n + 1) if i not in keep))),
      "land_km2": round(float(AREA[land].sum())), "sea_kept_km2": round(float(AREA[ocean].sum())), "earth_km2": round(float(AREA.sum()))}
print("grid:", CH)

EXP = {}
for S in (SEA_HALF, SEA_LGM):
    EXP[S] = ocean & (bed >= S)

# every stage's ice on the same grid (outlines in WGS84, rasterised at cell centres)
OUT = jload(f"{DATA}/ice_outlines.geojson")
RI = {}
for f in OUT["features"]:
    if f["properties"]["key"] == "max": continue
    RI[f["properties"]["key"]] = rf.rasterize([(f["geometry"], 1)], out_shape=(NR, NC), transform=TR, dtype="uint8").astype(bool)
np.savez_compressed(f"{WORK}/rast_ice.npz", **RI)
np.savez_compressed(f"{WORK}/grid.npz", land=land, ocean=ocean, ne_land=ne_land, bed=bed.astype(np.int16), ice=ice.astype(np.int16),
                    exp60=EXP[SEA_HALF], exp120=EXP[SEA_LGM], area_row=cell_km2, lat_c=lat_c, lon_c=lon_c)
jsave(CH, f"{WORK}/grid_checks.json", indent=1)

# exposed land as polygons for the page and figures (display only; areas come from the 10' grid above). The bed is
# interpolated onto a grid three times finer before the threshold, so the outlines follow the depth contour instead of
# the cell edges.
def chaikin(ring, n=2):
    """Corner-cutting smoothing of a closed ring (removes the grid's staircase)."""
    a = np.asarray(ring)[:-1]
    for _ in range(n):
        b = np.roll(a, -1, axis=0)
        a = np.column_stack([.75 * a + .25 * b, .25 * a + .75 * b]).reshape(-1, 2)
    return np.vstack([a, a[:1]])


from shapely import make_valid
LANDU = make_valid(unary_union([shape(f["geometry"]) for f in LAND50["features"]]))
UP = 3
bed_up = ndimage.zoom(bed.astype(np.float32), UP, order=1)
ocean_up = ndimage.zoom(ocean.astype(np.uint8), UP, order=0).astype(bool)
TRU = Affine(D / UP, 0, -180 - D / 2, 0, -D / UP, 90 + D / 2)
efeats = []
for S in (SEA_HALF, SEA_LGM):
    mask = ocean_up & (bed_up >= S)
    polys = [shape(g) for g, v in rf.shapes(mask.astype("uint8"), mask=mask, transform=TRU, connectivity=8) if v == 1]
    u = unary_union(polys).simplify(.02, preserve_topology=True)
    sm = []
    for p in flat_polys(u):
        if p.area <= .01: continue
        q = shapely.Polygon(chaikin(p.exterior.coords), [chaikin(r.coords) for r in p.interiors if shapely.Polygon(r).area > .01])
        sm.extend(flat_polys(make_valid(q)))
    u = make_valid(unary_union(sm)).difference(LANDU)          # stop at today's coast
    u = shapely.MultiPolygon([p for p in flat_polys(u.simplify(.01, preserve_topology=True)) if p.area > .005])
    gm = mapping(u)
    efeats.append({"type": "Feature", "properties": {"sea_level_m": S, "area_km2": round(float(AREA[EXP[S]].sum()))},
                   "geometry": {"type": "MultiPolygon", "coordinates": rnd(gm["coordinates"], 2)}})
del bed_up, ocean_up
jsave({"type": "FeatureCollection", "features": efeats}, f"{DATA}/exposed.json")
print("exposed.json", os.path.getsize(f"{DATA}/exposed.json") // 1024, "KB", [(f["properties"]["sea_level_m"], f["properties"]["area_km2"]) for f in efeats])

# ---------------- 3. shaded relief tiles ----------------
TI = os.path.join(RAW, "terrarium_z4", "4")
Z = 4; N = 2 ** Z; PX = 256 * N
E = np.zeros((PX, PX), np.float32)
for x in range(N):
    for y in range(N):
        a = np.asarray(Image.open(f"{TI}/{x}/{y}.png").convert("RGB")).astype(np.float32)
        E[y * 256:(y + 1) * 256, x * 256:(x + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
yy = (np.arange(PX) + .5) / PX
lat_m = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * yy))))              # latitude of each Mercator row
print("terrarium elevation range", E.min(), E.max())
# check against ETOPO10 at a few places
for nm, lo, la in (("Everest", 86.925, 27.988), ("Dogger Bank", 2, 55), ("Bering Strait", -169, 65.75)):
    px = int((lo + 180) / 360 * PX); py = int((1 - np.arcsinh(np.tan(np.radians(la))) / np.pi) / 2 * PX)
    print(f"  {nm}: terrarium {E[py, px]:.0f} m, etopo10 {ice[int(round((90 - la) * 6)), int(round((lo + 180) * 6))]} m")
# Natural Earth land in Mercator pixels (so the relief agrees with the outlines drawn over it)
def merc_xy(lon, lat):
    return (np.asarray(lon) + 180) / 360 * PX, (1 - np.arcsinh(np.tan(np.radians(np.clip(lat, -85.05, 85.05)))) / np.pi) / 2 * PX
def to_px(geom):
    return shapely.transform(geom, lambda a: np.column_stack(merc_xy(a[:, 0], a[:, 1])))
LANDM = rf.rasterize(((to_px(shape(f["geometry"]).segmentize(.5)), 1) for f in LAND50["features"]), out_shape=(PX, PX), dtype="uint8").astype(bool)
landm = (E > 0) | LANDM
# hillshade with real ground spacing (Mercator: same scale both ways, shrinking with cos(lat))
g = 40075016.7 / PX * np.cos(np.radians(lat_m))[:, None]
dzdy, dzdx = np.gradient(E)
VE = 9.0
sx, sy = VE * dzdx / g, VE * dzdy / g
az, alt = np.radians(315), np.radians(45)
nx, ny, nz = -sx, sy, np.ones_like(sx)
nn = np.sqrt(nx ** 2 + ny ** 2 + 1)
lx, ly, lz = np.cos(alt) * np.sin(az), np.cos(alt) * np.cos(az), np.sin(alt)
hs = np.clip((nx * lx + ny * ly + nz * lz) / nn, 0, 1)
hs = hs / np.sin(alt)                                    # flat ground = 1
def ramp(v, stops):
    xs = [s[0] for s in stops]; out = np.zeros(v.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(v, xs, [s[1][c] for s in stops])
    return out
hexc = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
LAND_STOPS = [(0, hexc("#EEEAE0")), (300, hexc("#E7E1D3")), (1000, hexc("#DDD5C3")), (2500, hexc("#CFC6B3")), (5000, hexc("#C2B9A6"))]
SEA_STOPS = [(-11000, hexc("#9FBCCC")), (-4000, hexc("#B5CDD9")), (-1000, hexc("#C8DBE4")), (-200, hexc("#D7E5EB")), (0, hexc("#E1ECF0"))]
rgb = np.where(landm[..., None], ramp(np.clip(E, 0, 6000), LAND_STOPS), ramp(np.clip(E, -11000, 0), SEA_STOPS))
shade = np.where(landm, .58 + .42 * np.clip(hs, 0, 1.25), .86 + .14 * np.clip(hs, 0, 1.15))
rgb = np.clip(rgb * shade[..., None], 0, 255).astype(np.uint8)
RD = os.path.join(IMG, "relief")
import shutil
if os.path.isdir(RD): shutil.rmtree(RD)
im = Image.fromarray(rgb)
tot = 0
for z in range(Z, -1, -1):
    n = 2 ** z; imz = im if z == Z else im.resize((256 * n, 256 * n), Image.LANCZOS)
    for x in range(n):
        os.makedirs(f"{RD}/{z}/{x}", exist_ok=True)
        for y in range(n):
            fn = f"{RD}/{z}/{x}/{y}.jpg"
            imz.crop((x * 256, y * 256, (x + 1) * 256, (y + 1) * 256)).save(fn, quality=80, optimize=True, progressive=False)
            tot += os.path.getsize(fn)
im.resize((2048, 2048), Image.LANCZOS).save(f"{WORK}/relief_z3.png")
print("relief tiles", tot // 1024, "KB")
