"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, Natural Earth outlines, the ice outlines and the exposed sea floor in two projections:
a north polar Lambert azimuthal equal-area view (central meridian 40 W, so North America sits lower left and Europe
lower right) and Equal Earth for the world. Reads only data/."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly, PathPatch
from matplotlib.path import Path
import numpy as np, shapely
from pyproj import Transformer
from shapely.geometry import shape, box
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72"})
BG, FG, MUT, LAND, RULE, SEA = "#F6F4EF", "#1D2128", "#636A72", "#E4DFD3", "#DDD8CC", "#E3ECF0"
ICEF, ICEE, ICED, SAND, SAND2, HOT, MAXC, NAVY = "#FBFDFF", "#2F6FA8", "#8DB4D6", "#E2C48C", "#C99B52", "#C8322B", "#7B57A8", "#1F3E66"
NA_C, EU_C = "#2F6FA8", "#C8322B"

R_ = jload(f"{DATA}/results.json")
SL = {k: SINFO[k]["label"] for k in SKEYS}
POLAR = Transformer.from_crs(4326, "+proj=laea +lat_0=90 +lon_0=-40 +datum=WGS84 +units=m", always_xy=True)
EE = Transformer.from_crs(4326, "EPSG:8857", always_xy=True)


def tf(geom, T, seg=.25):
    g = geom.segmentize(seg) if seg else geom
    return shapely.transform(g, lambda a: np.column_stack(T.transform(a[:, 0], np.clip(a[:, 1], -89.9, 89.9))))


def patch(ax, geom, **kw):
    """Draw a (multi)polygon with holes as one compound path."""
    verts, codes = [], []
    for p in flat_polys(geom):
        for ring in [p.exterior] + list(p.interiors):
            a = np.asarray(ring.coords)
            if len(a) < 3: continue
            verts.extend(a.tolist()); codes.extend([Path.MOVETO] + [Path.LINETO] * (len(a) - 2) + [Path.CLOSEPOLY])
    if verts:
        ax.add_patch(PathPatch(Path(verts, codes), **kw))


W = jload(f"{DATA}/world.json")
WG = shapely.make_valid(shapely.union_all([shapely.make_valid(shape(f["geometry"])).buffer(0) for f in W["features"]]))
NHB = box(-180, 5, 180, 90)
LAND_P = shapely.make_valid(tf(shapely.make_valid(WG.intersection(NHB)), POLAR))
OUT = {f["properties"]["key"]: shape(f["geometry"]) for f in jload(f"{DATA}/ice_outlines.geojson")["features"]}
_pc = {}


def ice_p(k):
    if k not in _pc: _pc[k] = shapely.make_valid(tf(OUT[k], POLAR, .2))
    return _pc[k]


EXPO = {-f["properties"]["sea_level_m"]: shapely.make_valid(shape(f["geometry"])) for f in jload(f"{DATA}/exposed.json")["features"]}
_ep = {}


def exp_p(s):
    if s not in _ep: _ep[s] = shapely.make_valid(tf(shapely.make_valid(EXPO[s].intersection(NHB)), POLAR, .25))
    return _ep[s]


def gridlines(ax, T=POLAR, lats=(40, 50, 60, 70, 80), lons=range(-180, 180, 30), col="#CFC9BC", lw=.4):
    for la in lats:
        lo = np.linspace(-180, 180, 361); x, y = T.transform(lo, np.full_like(lo, la)); ax.plot(x, y, color=col, lw=lw, zorder=.5)
    for lo in lons:
        la = np.linspace(30, 88, 60); x, y = T.transform(np.full_like(la, lo), la); ax.plot(x, y, color=col, lw=lw, zorder=.5)


POLAR_EXT = (-6.0e6, 6.2e6, -6.6e6, 5.3e6)


def polar_base(ax, ext=POLAR_EXT, land=LAND, sea=SEA, lw=.3, grid=True):
    ax.set_facecolor(sea)
    patch(ax, LAND_P, fc=land, ec="#FFFFFF", lw=lw, zorder=1)
    if grid: gridlines(ax)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal")
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def pxy(lon, lat):
    return POLAR.transform(lon, lat)
