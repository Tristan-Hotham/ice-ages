# When the ice came south: the Northern Hemisphere's ice sheets through the Quaternary

A map and analysis of the best-estimate ice-sheet reconstructions of Batchelor et al. (2019) for 18 time slices, from the late Gauss Chron (2.6 to 3.59 million years ago) to the Last Glacial Maximum (about 26,500 years ago): how big the ice was, how far south it reached, which of today's countries and cities lay under it, and the land a sea 60 m or 120 m lower would uncover.

Interactive page: https://maps.tristanhotham.com/ice-ages/
Paper: https://doi.org/10.5281/zenodo.23878610
Blog post: https://blog.tristanhotham.com/2026/10/31/ice-ages/

## Headline results

- Area (best-estimate outlines, million km², measured in an equal-area projection): MIS 6 33.8, MIS 12 32.4, MIS 16 32.2, LGM 26.2, MIS 4 23.8, MIS 8 23.5, MIS 20 to 24 23.1, Early Matuyama 21.6, MIS 10 21.5, 30 ka 14.3, MIS 5b 12.9, 35 ka 12.8, MIS 5d 12.5, Late Gauss 11.1, 40 ka 10.6, 45 ka 7.2, MIS 5c 6.9, MIS 5a 6.9.
- MIS 6 (132,000 to 190,000 years ago) is the largest, 29% more than the LGM (27% in the authors' table); the LGM ranks 4th. The authors' table gives the same order for the seven largest; my areas are within 4.2% of it except 40 ka (+19.7%). All outlines together: 37.0 million km²; inside every one: 4.8 million km².
- At the LGM 34.4% of the ice lay over today's sea.
- Southernmost ice: North America 37.22°N in MIS 6 and MIS 12 (southern Illinois, 26 km from the Ohio's mouth); LGM 39.02°N near Bloomington, Indiana. Europe 48.3°N in MIS 6 (Dnieper valley, near Dnipro); LGM 50.23°N on the floor of the Celtic Sea, 51.78°N on the mainland.
- Countries under the LGM ice: Canada 97.4%, Ireland, Sweden, Finland, Iceland, Estonia, Latvia 100%, Norway 99.9%, Lithuania 96.3%, Denmark 75.1%, United Kingdom 60.9%, Poland 37.6%, United States 21.2%, Germany 13.5%, Russia 7.1%. In any slice: Poland 94.7%, Belarus 97.6%, Netherlands 60.2%, Germany 46.8%, Russia 43.1%, Ukraine 28.2%.
- Places: 709 of Natural Earth's 7,342 populated places lie inside the LGM outline (27 with a million or more; population figures sum to 140,570,036); 1,050 inside at least one outline (sum 230,083,190).
- Cities, distance to the LGM edge (negative inside): New York -13.3 km, Chicago -112.2, Berlin -42.4, Seattle -17.2, London +152.5 (never inside any outline; 16.0 km from the MIS 12 edge), Moscow +246.0 (inside 3 older outlines), Paris +463.9 (never inside).
- Sea floor exposed by a 120 m fall: 21,174,383 km² (14.2% of today's land), 17,474,989 km² outside the LGM ice; 60 m: 14,257,424 km². Largest ice-free gains (my boxes): Sahul 2,859,872, Sundaland 2,345,574, Siberian Arctic shelf 1,810,593, Beringia 1,641,739, East China and Yellow seas 1,018,450, Patagonian shelf 784,516 km². All 11 land bridges tested are joined at 60 m.

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

- Batchelor, C.L., Margold, M., Krapp, M., Murton, D.K., Dalton, A.S., Gibbard, P.L., Stokes, C.R., Murton, J.B. and Manica, A. (2019) The configuration of Northern Hemisphere ice sheets through the Quaternary. Nature Communications 10, 3713. doi:10.1038/s41467-019-11601-2. Shapefiles and area table from https://osf.io/7jen3/. The README supplied with the shapefiles states no licence; the OSF repository is released under CC BY 4.0. Please cite the paper.
- Amante, C. and Eakins, B.W. (2009) ETOPO1 1 Arc-Minute Global Relief Model. NOAA Technical Memorandum NESDIS NGDC-24. doi:10.7289/V5C8276M. Public domain. Used through ETOPO10 (Garrett Euler, MIT licence).
- AWS Terrain Tiles (Mapzen terrain tiles, Registry of Open Data on AWS), Terrarium encoding, zoom 4, for the relief base; built from open data including ETOPO1, GMTED2010 and SRTM.
- Wikipedia (CC BY-SA 4.0): Last Glacial Maximum, Quaternary glaciation, Beringia, Sundaland, Sahul, Doggerland, British-Irish Ice Sheet, Fennoscandian ice sheet, Laurentide Ice Sheet; revision ids in `data/results.json`. Used for context and quoted figures only.
- Natural Earth countries, land and populated places (https://www.naturalearthdata.com/). Public domain.

## Citation

Hotham, T. (2026) When the ice came south: the Northern Hemisphere's ice sheets through the Quaternary, what lay beneath them and the land the sea gave up. Zenodo. https://doi.org/10.5281/zenodo.23878610

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
