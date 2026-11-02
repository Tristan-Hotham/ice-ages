"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23878610, https://doi.org/10.5281/zenodo.23878610 and https://blog.tristanhotham.com/2026/10/31/ice-ages/ stay as placeholders for the publisher. Needs only data/, code/, the figures and
the paper PDF: raw/ is not used and is not packed."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_When_the_Ice_Came_South"
ST, CI = R["stages"], R["cities"]

# the page build checks the shared facts; these are numbers written in words or alt text in the blog and collage
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
assert 30 < ST["lgm"]["on_sea_pct"] < 37                                                                  # "about a third of it on what is now sea floor"
assert [round(ST[k]["area"] / 1e5) / 10 for k in ("mis6", "mis12", "mis16", "lgm")] == [33.8, 32.4, 32.2, 26.2]
assert all(6.5 < ST[k]["area"] / 1e6 < 7.5 for k in ("ka45", "mis5a", "mis5c"))                           # "about 7 million"
assert (R["south"]["na_min"]["lat"], R["south"]["mis6_eu"]["lat"], R["south"]["lgm_eu"]["lat"]) == (37.22, 48.3, 50.23)
assert all(CI[c]["lgm"] < -500 for c in ("Stockholm", "Helsinki", "Montreal")) and all(-50 < CI[c]["lgm"] < 0 for c in ("Berlin", "Seattle", "New York", "Manchester"))
assert all(0 < CI[c]["lgm"] < 20 for c in ("Hamburg", "Cincinnati")) and 140 < CI["London"]["lgm"] < 160 and 450 < CI["Paris"]["lgm"] < 470
assert CI["Oslo"]["n_under"] == 14 and CI["London"]["n_under"] == 0 and CI["Moscow"]["n_under"] == 3 and len(SITE["cities"]) == 35
assert "mis6" in CI["Kyiv"]["under"] and R["south"]["mis6_eu"]["lat"] < 50.4                              # the furthest ice reaches south of Kyiv
assert R["shelves"][0]["region"] == "Sahul" and R["shelves"][1]["region"] == "Sundaland"

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = fill(post, R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
from PIL import Image
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{[^|}]+\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23878610"}, set(re.findall(r"\{\{[^|}]+\}\}", post))
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
A = R["areas"]
meta = {"title": "When the ice came south: the ice ages mapped, and what lies under them today",
        "slug": "ice-ages",
        "excerpt": f"I mapped the Northern Hemisphere's ice sheets at {A['n_stages']} moments of the last 3.6 million years. The last ice age was only the {A['lgm_rank']}th largest; {R['places']['lgm']['n']:,} of today's cities and towns, New York among them, stand on ground its ice covered.",
        "seo_description": f"The Northern Hemisphere's ice sheets in {A['n_stages']} time slices: their size, how far south they reached, the cities beneath them and the land the sea gave up.",
        "tags": ["ice age", "glaciation", "Quaternary", "maps", "data visualisation", "sea level", "Doggerland", "Beringia"],
        "header_alt": f"Title card reading 'When the ice came south' in black and glacier blue on pale paper, beside a map of the Arctic seen from above the pole with white ice sheets over North America and northern Eurasia at their largest, in MIS 6, a red dashed line for the smaller ice of the Last Glacial Maximum, and sand-coloured shelves where the sea floor would be dry. Text: at their largest, in MIS 6, {ST['mis6']['area'] / 1e6:.1f} million km²."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/ice-ages_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"ice-ages/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"ice-ages/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "ice-ages/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("\\kmq\\ ", "km² ").replace("\\kmq", "km²").replace("\\citet{batchelor}", "Batchelor et al. (2019)")
assert "\\" not in ab, re.findall(r"\\\w+", ab)
zmeta = {"title": "When the Ice Came South: The Northern Hemisphere's Ice Sheets through the Quaternary, What Lay Beneath Them and the Land the Sea Gave Up",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Ice outlines: {BAT_CITE} Data at osf.io/7jen3, CC BY 4.0.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["ice sheets", "Quaternary", "glaciation", "Last Glacial Maximum", "Marine Isotope Stage 6", "sea level", "land bridges", "Doggerland", "Beringia", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": BAT_DOI, "relation": "references", "resource_type": "publication-article", "scheme": "doi"},
                                 {"identifier": BAT_OSF, "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": ETOPO_DOI, "relation": "isDerivedFrom", "resource_type": "dataset", "scheme": "doi"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
