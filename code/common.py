"""Shared paths, stage list and helpers for the ice-ages project.

Raw inputs (read in place by 01 and 02 only, never modified; raw/ is not needed once data/ is built):
  raw/bat19/<time slice>/hypothesised ice-sheet reconstruction(s)/<name>_best_estimate.shp
      Batchelor, C.L., Margold, M., Krapp, M., Murton, D.K., Dalton, A.S., Gibbard, P.L., Stokes, C.R., Murton, J.B.
      and Manica, A. (2019) The configuration of Northern Hemisphere ice sheets through the Quaternary. Nature
      Communications 10, 3713, doi:10.1038/s41467-019-11601-2. Shapefiles from the authors' OSF repository
      (osf.io/7jen3). Only the best-estimate outlines are used; the repository also holds minimum and maximum outlines
      for the 17 slices before the LGM. The README supplied with the files states no licence; the paper points to the
      OSF repository, which is released under CC BY 4.0. Projection: North Pole Lambert azimuthal equal area on WGS84
      (lat 90, lon 0), except the LGM file, which is in geographic WGS84 coordinates.
  raw/bat19/Quaternary_Ice_sheets_areas.xlsx
      The authors' table of ice-sheet areas (km2) per slice and hypothesis (min, max, best), by ice sheet:
      Eurasian (EIS), Greenland (GIS), Laurentide (LIS), Cordilleran (CIS) and others.
  raw/etopo10/etopo10_ice_g_i2.bin, etopo10_bed_g_i2.bin (+ .hdr)
      ETOPO10, a 10 arc-minute resampling of NOAA's ETOPO1 (Amante and Eakins 2009, doi:10.7289/V5C8276M) by Garrett
      Euler; ETOPO1 is public domain, the resampling's repository is MIT licensed. Grid registered: 2161 x 1081 cells,
      centres at -180..180 and -90..90 (the 180 column repeats -180). "ice" is the ice-surface version, "bed" the
      bedrock version (they differ under the Antarctic and Greenland ice and under floating ice shelves).
  raw/terrarium_z4/4/x/y.png
      AWS Terrain Tiles (Mapzen terrain, AWS Open Data), Terrarium encoding, zoom 4, 256 px tiles in Web Mercator:
      elevation (m) = R * 256 + G + B / 256 - 32768. Used only for the shaded relief base image of the page.
  raw/wiki_pages.json
      English Wikipedia parse HTML with revision ids (CC BY-SA 4.0) for eleven articles. Used only for context and the
      figures quoted from them in the text; no Wikipedia text is reproduced.
  /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson, ne_50m_admin_0_countries.geojson, ne_50m_land.geojson,
      ne_10m_populated_places_simple.geojson (Natural Earth, public domain)
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("IA_RAW", os.path.join(ROOT, "raw"))
GEO = os.environ.get("IA_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("IA_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
WORK = os.path.join(os.environ.get("IATMP", "/dev/shm/iceages"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK, IMG):
    os.makedirs(d, exist_ok=True)

SLUG = "ice-ages"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23878610"                # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/ice-ages/"          # filled in by the publisher
BAT_DOI = "10.1038/s41467-019-11601-2"
BAT_OSF = "https://osf.io/7jen3/"
BAT_CITE = ("Batchelor, C.L., Margold, M., Krapp, M., Murton, D.K., Dalton, A.S., Gibbard, P.L., Stokes, C.R., Murton, J.B. "
            "and Manica, A. (2019) The configuration of Northern Hemisphere ice sheets through the Quaternary. "
            "Nature Communications 10, 3713. doi:10.1038/s41467-019-11601-2")
BAT_SHORT = "Batchelor et al. (2019), Nature Communications 10, 3713"
ETOPO_DOI = "10.7289/V5C8276M"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

LAEA = "+proj=laea +lat_0=90 +lon_0=0 +datum=WGS84 +units=m +no_defs"   # the source projection (ESRI:102017)
EQAREA = "EPSG:8857"                                                  # Equal Earth, for whole-country areas
SEA_LGM, SEA_HALF = -120, -60                                         # sea-level falls mapped (m)

# The 18 time slices in Batchelor et al. (2019), oldest first (the order of the time slider). Ages as in the README.
# key, short label, long name, folder, file stem, age text, age range in ka (young, old), warm slice?
# Warm slices (45 ka, MIS 5a, MIS 5c): the authors map ice during peak warmth, not the maximum.
STAGES = [
    ("lgauss", "Late Gauss", "Late Gauss Chron", "Late Gauss Chron", "LateGauss", "2.6 to 3.59 million years ago", (2600, 3590), False),
    ("emat", "Early Matuyama", "Early Matuyama Chron", "Early Matuyama Chron", "EarlyMatuyama", "1.78 to 2.6 million years ago", (1780, 2600), False),
    ("mis20", "MIS 20 to 24", "Marine Isotope Stages 20 to 24", "MIS 20-24", "MIS20-24", "790,000 to 928,000 years ago", (790, 928), False),
    ("mis16", "MIS 16", "Marine Isotope Stage 16", "MIS 16", "MIS16", "622,000 to 677,000 years ago", (622, 677), False),
    ("mis12", "MIS 12", "Marine Isotope Stage 12", "MIS 12", "MIS12", "429,000 to 477,000 years ago", (429, 477), False),
    ("mis10", "MIS 10", "Marine Isotope Stage 10", "MIS 10", "MIS10", "337,000 to 365,000 years ago", (337, 365), False),
    ("mis8", "MIS 8", "Marine Isotope Stage 8", "MIS 8", "MIS8", "243,000 to 279,000 years ago", (243, 279), False),
    ("mis6", "MIS 6", "Marine Isotope Stage 6", "MIS 6", "MIS6", "132,000 to 190,000 years ago", (132, 190), False),
    ("mis5d", "MIS 5d", "Marine Isotope Stage 5d", "MIS 5d", "MIS5d", "108,000 to 117,000 years ago", (108, 117), False),
    ("mis5c", "MIS 5c", "Marine Isotope Stage 5c", "MIS 5c", "MIS5c", "92,000 to 108,000 years ago", (92, 108), True),
    ("mis5b", "MIS 5b", "Marine Isotope Stage 5b", "MIS 5b", "MIS5b", "86,000 to 92,000 years ago", (86, 92), False),
    ("mis5a", "MIS 5a", "Marine Isotope Stage 5a", "MIS 5a", "MIS5a", "72,000 to 86,000 years ago", (72, 86), True),
    ("mis4", "MIS 4", "Marine Isotope Stage 4", "MIS 4", "MIS4", "58,000 to 72,000 years ago", (58, 72), False),
    ("ka45", "45 ka", "45,000 years ago", "45 ka", "45ka", "about 45,000 years ago", (45, 45), True),
    ("ka40", "40 ka", "40,000 years ago", "40 ka", "40ka", "about 40,000 years ago", (40, 40), False),
    ("ka35", "35 ka", "35,000 years ago", "35 ka", "35ka", "about 35,000 years ago", (35, 35), False),
    ("ka30", "30 ka", "30,000 years ago", "30 ka", "30ka", "about 30,000 years ago", (30, 30), False),
    ("lgm", "LGM", "Last Glacial Maximum", "LGM", "LGM", "around 26,500 years ago", (26.5, 26.5), False),
]
SKEYS = [s[0] for s in STAGES]
SINFO = {s[0]: {"label": s[1], "name": s[2], "folder": s[3], "stem": s[4], "age": s[5], "ka": s[6], "warm": s[7]} for s in STAGES}
# rows of the authors' area table (Quaternary_Ice_sheets_areas.xlsx) for each stage, as spelt there
XLSX_ROW = {"lgm": "LGM", "ka30": "30k", "ka35": "35k", "ka40": "40k", "ka45": "45k", "mis4": "MIS4", "mis5a": "MIS5a",
            "mis5b": "MIS5b", "mis5c": "MIS5c", "mis5d": "MIS5d", "mis6": "MIS6", "mis8": "MIS8", "mis10": "MIS10",
            "mis12": "MIS12", "mis16": "MIS16", "mis20": "MIS20-24", "emat": "Early Mat", "lgauss": "Late Gauss"}

# Cities whose distance to the ice edge is reported (Natural Earth name, country ISO). Chosen before the analysis.
CITY_PICKS = [("London", "GBR"), ("Chicago", "USA"), ("New York", "USA"), ("Berlin", "DEU"), ("Moscow", "RUS"),
              ("Toronto", "CAN"), ("Montréal", "CAN"), ("Boston", "USA"), ("Seattle", "USA"), ("Minneapolis", "USA"),
              ("Detroit", "USA"), ("Cleveland", "USA"), ("St. Louis", "USA"), ("Dublin", "IRL"), ("Manchester", "GBR"),
              ("Edinburgh", "GBR"), ("Amsterdam", "NLD"), ("Hamburg", "DEU"), ("Warsaw", "POL"), ("København", "DNK"),
              ("Stockholm", "SWE"), ("Oslo", "NOR"), ("Helsinki", "FIN"), ("St. Petersburg", "RUS"), ("Kyiv", "UKR"),
              ("Paris", "FRA"), ("Vancouver", "CAN"), ("Calgary", "CAN"), ("Winnipeg", "CAN"), ("Philadelphia", "USA"),
              ("Kansas City", "USA"), ("Cincinnati", "USA"), ("Minsk", "BLR"), ("Prague", "CZE"), ("Kraków", "POL")]

CITY_SHOW = {"København": "Copenhagen", "St. Petersburg": "St Petersburg", "St. Louis": "St Louis", "Montréal": "Montreal", "Kraków": "Krakow"}

# Boxes for the shelf regions exposed by a lower sea (lon0, lat0, lon1, lat1; may be several). My own choice, drawn
# round the shelf seas named in the text; see the paper. Order = display order.
SHELVES = [
    ("Sundaland", "Sunda Shelf: Gulf of Thailand, Java Sea, southern South China Sea", [(95, -9, 120, 14)]),
    ("Sahul", "Sahul and Arafura shelves, Gulf of Carpentaria, Bass Strait", [(112, -45, 155, -2)]),
    ("Siberian Arctic shelf", "Laptev, East Siberian and Kara seas", [(55, 66, 180, 82)]),
    ("Beringia", "Bering and Chukchi seas", [(-180, 52, -155, 75), (160, 52, 180, 72)]),
    ("East China and Yellow seas", "Yellow Sea, Bohai, East China Sea, Taiwan Strait", [(117, 22, 131, 41)]),
    ("Patagonian shelf", "Argentine shelf and the Falklands", [(-70, -56, -52, -35)]),
    ("Doggerland", "North Sea, English Channel and the Irish Sea", [(-12, 48, 10, 62)]),
    ("Barents Sea", "Barents and White seas", [(10, 66, 55, 82)]),
    ("Persian Gulf", "the whole Gulf", [(47, 23, 57, 31)]),
    ("Canadian Arctic and Hudson Bay", "Canadian Arctic Archipelago, Hudson Bay, Baffin Bay shelves", [(-125, 50, -60, 84)]),
    ("Grand Banks and New England", "Gulf of Maine, Scotian Shelf, Grand Banks", [(-75, 38, -45, 52)]),
]

# Today's landmasses tested for joins at the lower sea levels (name, lon, lat of a point well inland)
JOINS = [("Great Britain", "mainland Europe", (-1.5, 52.5), (5.0, 50.5)),
         ("Ireland", "Great Britain", (-8.0, 53.3), (-1.5, 52.5)),
         ("Asia", "North America", (130.0, 62.0), (-150.0, 64.5)),
         ("New Guinea", "Australia", (143.0, -6.0), (135.0, -25.0)),
         ("Tasmania", "Australia", (146.6, -42.0), (135.0, -25.0)),
         ("Borneo", "mainland Asia", (114.0, 1.0), (102.0, 15.0)),
         ("Sumatra", "mainland Asia", (101.5, -0.5), (102.0, 15.0)),
         ("Java", "mainland Asia", (110.0, -7.3), (102.0, 15.0)),
         ("Sri Lanka", "India", (80.7, 7.8), (78.0, 20.0)),
         ("Taiwan", "mainland Asia", (121.0, 23.8), (113.0, 28.0)),
         ("Sakhalin", "mainland Asia", (142.8, 50.5), (113.0, 28.0))]


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "m1": return f"{float(v) / 1e6:.1f}"        # km2 to million km2, one decimal
    if f == "m2": return f"{float(v) / 1e6:.2f}"
    if f == "k": return f"{float(v) / 1000:.1f}"
    if f == "abs": return f"{abs(round(float(v))):,}"
    if f == "lat": return f"{abs(float(v)):.1f}°{'N' if float(v) >= 0 else 'S'}"
    raise ValueError(f)


def fill(text, R, f=fmt):
    """Replace {{path|format}} tokens with numbers from R, leaving the publisher's tokens (10.5281/zenodo.23878610, https://doi.org/10.5281/zenodo.23878610,
    https://blog.tristanhotham.com/2026/10/31/ice-ages/), image tokens ({{IMG|...}}) and table tokens ({{TABLE_...}}) alone."""
    return re.sub(r"\{\{(?!IMG\||DOI\}\}|DOI_URL\}\}|BLOG_URL\}\}|TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: f(get(R, m.group(1)), m.group(3)), text)


def flat_polys(g):
    """All polygons inside a geometry, however nested."""
    if g is None or g.is_empty: return
    if g.geom_type == "Polygon":
        yield g
    elif hasattr(g, "geoms"):
        for x in g.geoms:
            yield from flat_polys(x)
