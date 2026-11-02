"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json. Needs only data/."""
from common import *

R = jload(f"{DATA}/results.json")
ST, A, C, P, CI, X, SO = R["stages"], R["areas"], R["countries"], R["places"], R["cities"], R["exposed"], R["south"]
B = C["by_iso"]
N = lambda v: f"{round(v):,}"
M = lambda v: f"{v / 1e6:.1f}"
order = ", ".join(f"{ST[k]['label']} {M(ST[k]['area'])}" for k in R["rank"])
readme = f"""# When the ice came south: the Northern Hemisphere's ice sheets through the Quaternary

A map and analysis of the best-estimate ice-sheet reconstructions of Batchelor et al. (2019) for {A['n_stages']} time slices, from the late Gauss Chron (2.6 to 3.59 million years ago) to the Last Glacial Maximum (about 26,500 years ago): how big the ice was, how far south it reached, which of today's countries and cities lay under it, and the land a sea 60 m or 120 m lower would uncover.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Area (best-estimate outlines, million km², measured in an equal-area projection): {order}.
- MIS 6 ({SINFO['mis6']['age']}) is the largest, {A['mis6_over_lgm_pct']}% more than the LGM ({A['mis6_over_lgm_pct_tab']}% in the authors' table); the LGM ranks {A['lgm_rank']}th. The authors' table gives the same order for the seven largest; my areas are within {A['max_abs_diff_pct']}% of it except 40 ka (+{A['ka40_diff_pct']}%). All outlines together: {M(A['union'])} million km²; inside every one: {M(A['every'])} million km².
- At the LGM {ST['lgm']['on_sea_pct']}% of the ice lay over today's sea.
- Southernmost ice: North America {SO['na_min']['lat']}°N in MIS 6 and MIS 12 (southern Illinois, {R['south_extra']['na_min_to_ohio_mouth_km']} km from the Ohio's mouth); LGM {SO['lgm_na']['lat']}°N near Bloomington, Indiana. Europe {SO['mis6_eu']['lat']}°N in MIS 6 (Dnieper valley, near Dnipro); LGM {SO['lgm_eu']['lat']}°N on the floor of the Celtic Sea, {R['south_extra']['lgm_eu_mainland_lat']}°N on the mainland.
- Countries under the LGM ice: Canada {B['CAN']['lgm_pct']}%, Ireland, Sweden, Finland, Iceland, Estonia, Latvia 100%, Norway {B['NOR']['lgm_pct']}%, Lithuania {B['LTU']['lgm_pct']}%, Denmark {B['DNK']['lgm_pct']}%, United Kingdom {B['GBR']['lgm_pct']}%, Poland {B['POL']['lgm_pct']}%, United States {B['USA']['lgm_pct']}%, Germany {B['DEU']['lgm_pct']}%, Russia {B['RUS']['lgm_pct']}%. In any slice: Poland {B['POL']['union_pct']}%, Belarus {B['BLR']['union_pct']}%, Netherlands {B['NLD']['union_pct']}%, Germany {B['DEU']['union_pct']}%, Russia {B['RUS']['union_pct']}%, Ukraine {B['UKR']['union_pct']}%.
- Places: {N(P['lgm']['n'])} of Natural Earth's {N(P['total_n'])} populated places lie inside the LGM outline ({P['lgm']['n_1m']} with a million or more; population figures sum to {N(P['lgm']['pop'])}); {N(P['union']['n'])} inside at least one outline (sum {N(P['union']['pop'])}).
- Cities, distance to the LGM edge (negative inside): New York {CI['New York']['lgm']} km, Chicago {CI['Chicago']['lgm']}, Berlin {CI['Berlin']['lgm']}, Seattle {CI['Seattle']['lgm']}, London +{CI['London']['lgm']} (never inside any outline; {CI['London']['mis12']} km from the MIS 12 edge), Moscow +{CI['Moscow']['lgm']} (inside {CI['Moscow']['n_under']} older outlines), Paris +{CI['Paris']['lgm']} (never inside).
- Sea floor exposed by a 120 m fall: {N(X['m120']['km2'])} km² ({X['m120']['pct_of_land']}% of today's land), {N(X['m120']['ice_free'])} km² outside the LGM ice; 60 m: {N(X['m60']['km2'])} km². Largest ice-free gains (my boxes): {", ".join(f"{r['region']} {N(r['m120_ice_free'])}" for r in R['shelves'][:6])} km². All {len(R['joins'])} land bridges tested are joined at 60 m.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded; `data/ice_page.json` and `data/exposed.json` loaded by the page; relief tiles in `img/relief/`). |
| `header.png` | Social card, 1200 x 630. |
| `data/ice_outlines.geojson` | The best-estimate outline of each mapped slice (WGS84, generalised to 1.5 km), with the authors' slice name and age and the measured area, plus the union of all slices (`max`). |
| `data/ice_page.json` | The same, generalised to 7 km, for the page. |
| `data/batchelor_area_table.csv` | The authors' area table (best, minimum, maximum; by ice sheet). |
| `data/stage_areas.csv` | Per slice: measured area and rank, the authors' best, minimum and maximum, area over today's land and sea, places under the ice. |
| `data/countries_under_ice.csv` | Per country: area, and km² and % under each slice's ice and under any slice. |
| `data/places_under_ice.csv` | Every Natural Earth populated place with its population figure and a flag per slice. |
| `data/city_distance_to_ice.csv` | Distance from selected city centres to each slice's ice edge (km, negative inside). |
| `data/southern_reach.csv` | The southernmost point of the ice in North America and Europe per slice, with the nearest city. |
| `data/exposed.json`, `data/exposed_shelves.csv` | Sea floor exposed at 60 m and 120 m below today's sea level (polygons; areas by shelf box). |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/world.json`, `data/countries.json`, `data/cities.json` | Page and figure data. |
| `img/relief/` | Shaded relief tiles (zoom 0 to 4) made from AWS Terrain Tiles. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Ice: best-estimate shapefiles of Batchelor et al. (2019) from osf.io/7jen3. Slices and ages as in the authors' README. All in the North Pole Lambert azimuthal equal-area projection except the LGM (geographic, reprojected). Invalid polygons repaired, each slice dissolved, areas measured in the equal-area projection. The 45 ka and late Gauss files also carry today's glaciers worldwide; parts south of the equator are dropped. The minimum and maximum outlines exist but are used only through the authors' area table. The outlines are generalised, partly subjective reconstructions of maximum extent within each slice (45 ka, MIS 5a and MIS 5c: peak warmth), not for local use; MIS 8 and MIS 10 are highly uncertain.
- Countries: Natural Earth 1:10m, intersected in the equal-area projection. Places: Natural Earth populated places and their pop_max (approximate). Distances: true distances to the outline (azimuthal equidistant projection centred on each city).
- Southernmost reach: lowest latitude on outline polygons of 50,000 km² or more in 170°W to 50°W and 12°W to 60°E.
- Sea floor: ETOPO10 (10 arc-minute ETOPO1). Land today: ice surface above 0 m or Natural Earth land. Sea: water joined to the world ocean or over 50,000 km², not the Caspian. Depth: bedrock version. Exposed at S: sea with floor at or above S. No isostasy or sediment. Shelf boxes are my own (see `code/common.py`).

## How to rerun

Needs Python 3 with numpy, pandas, scipy, shapely, geopandas, pyproj, rasterio, openpyxl, Pillow, matplotlib and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Scripts 01 to 03 read the raw inputs (`raw/`, not part of the release: `bat19/` shapefiles and area table from osf.io/7jen3, `etopo10/`, `terrarium_z4/` and `wiki_pages.json`) and Natural Earth (`/home/claude/newdata/raw/geo/`, set `IA_GEO`). Everything after 03 needs only `data/`. Intermediate files go to `/dev/shm/iceages/work` (set `IATMP`).

```
python3 code/01_clean.py        # read and clean the outlines, measure areas, authors' table
python3 code/02_geo.py          # outlines and labels, exposed sea floor, relief tiles
python3 code/03_results.py      # results.json, data tables, page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- {BAT_CITE}. Shapefiles and area table from {BAT_OSF}. The README supplied with the shapefiles states no licence; the OSF repository is released under CC BY 4.0. Please cite the paper.
- Amante, C. and Eakins, B.W. (2009) ETOPO1 1 Arc-Minute Global Relief Model. NOAA Technical Memorandum NESDIS NGDC-24. doi:{ETOPO_DOI}. Public domain. Used through ETOPO10 (Garrett Euler, MIT licence).
- AWS Terrain Tiles (Mapzen terrain tiles, Registry of Open Data on AWS), Terrarium encoding, zoom 4, for the relief base; built from open data including ETOPO1, GMTED2010 and SRTM.
- Wikipedia (CC BY-SA 4.0): Last Glacial Maximum, Quaternary glaciation, Beringia, Sundaland, Sahul, Doggerland, British-Irish Ice Sheet, Fennoscandian ice sheet, Laurentide Ice Sheet; revision ids in `data/results.json`. Used for context and quoted figures only.
- Natural Earth countries, land and populated places (https://www.naturalearthdata.com/). Public domain.

## Citation

Hotham, T. (2026) When the ice came south: the Northern Hemisphere's ice sheets through the Quaternary, what lay beneath them and the land the sea gave up. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = """MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ and img/ are released under CC BY 4.0.

The ice outlines and the area table are derived from Batchelor et al. (2019),
Nature Communications 10, 3713, doi:10.1038/s41467-019-11601-2, data at
osf.io/7jen3, released under CC BY 4.0 (the README supplied with the files
states no licence). The sea-floor depths come from NOAA's ETOPO1
(doi:10.7289/V5C8276M, public domain) via ETOPO10 (Garrett Euler, MIT
licence). The relief tiles in img/relief are derived from AWS Terrain Tiles
(Mapzen), open data with attribution to their sources (ETOPO1, GMTED2010,
SRTM and others). Natural Earth is public domain. Figures quoted from
Wikipedia are CC BY-SA 4.0.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] When the ice came south: the Northern Hemisphere's ice sheets at {A['n_stages']} moments of the last 3.6 million years. The last ice age wasn't the biggest: {M(ST['mis6']['area'])} million km² of ice 132,000 to 190,000 years ago, {A['mis6_over_lgm_pct']}% more than the {M(ST['lgm']['area'])} million of 26,500 years ago

## Body

I measured the best-estimate ice-sheet reconstructions of Batchelor et al. (2019, Nature Communications) for {A['n_mapped']} time slices and laid them over today's map. The Last Glacial Maximum ranks only {A['lgm_rank']}th by area; MIS 6 (132,000 to 190,000 years ago), MIS 12 and MIS 16 were all bigger, and older ice reached {SO['na_min']['lat']}°N in southern Illinois and {SO['mis6_eu']['lat']}°N in Ukraine. Under the LGM ice: {B['CAN']['lgm_pct']:.0f}% of Canada, all of Ireland, Sweden and Finland, {B['GBR']['lgm_pct']:.0f}% of the UK, and {N(P['lgm']['n'])} of Natural Earth's cities and towns, New York {abs(CI['New York']['lgm']):.0f} km inside the edge. London was never under the ice in any slice ({CI['London']['mis12']:.0f} km from it in MIS 12). A sea 120 m lower uncovers {M(X['m120']['ice_free'])} million km² of ice-free land, biggest on the Sahul and Sunda shelves. Caveats: the outlines are generalised reconstructions, the older ones highly uncertain, not for local detail; ice thickness is not known from them; populations are Natural Earth's place figures. Interactive map with a slider through the slices, a sea-level toggle and click-anywhere ice history: {PAGE}

## Source comment

Source: Batchelor, C.L. et al. (2019) The configuration of Northern Hemisphere ice sheets through the Quaternary, Nature Communications 10, 3713, doi:10.1038/s41467-019-11601-2, best-estimate outlines from osf.io/7jen3 (CC BY 4.0). Areas measured in the source's polar equal-area projection. Sea floor: NOAA ETOPO1 via ETOPO10. Places and countries: Natural Earth.

Tools: Python (geopandas, shapely, pyproj, rasterio, matplotlib); MapLibre for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
assert SINFO["mis6"]["ka"] == (132, 190)
for t in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in t.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
