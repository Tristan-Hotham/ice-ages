"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, world.json, country labels, cities) is embedded; data/ice_page.json
and data/exposed.json are loaded by the page, and the relief tiles come from img/relief/. Facts stated in words are
checked here. The full-screen map snippet (code/fullscreen_snippet.html) is pasted before </body>. 10.5281/zenodo.23878610 and
https://blog.tristanhotham.com/2026/10/31/ice-ages/ stay as placeholders for the publisher. Needs only data/ (not raw/)."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
ST, A, C, P, CI, SO = R["stages"], R["areas"], R["countries"], R["places"], R["cities"], R["south"]

# ---- facts stated in words (page, blog, paper, collage)
assert A["largest"] == "mis6" and A["largest_tab"] == "mis6" and A["lgm_rank"] == 4 and A["lgm_rank_tab"] == 4
assert R["rank"][1:3] == ["mis12", "mis16"] and A["top7_same"]                                       # "MIS 12 and MIS 16 close behind"; "same order for the seven largest"
assert set(R["rank"][-3:]) == set(R["warm"]) == {"ka45", "mis5a", "mis5c"}                             # warm slices are the three smallest
assert all(abs(ST[k]["diff_pct"]) <= A["max_abs_diff_pct"] for k in R["rank"] if k != "ka40") and A["ka40_diff_pct"] > 10
ck = R["checks"]; assert (ck["ka40_asia_km2"] - ck["ka40_tab_others"]) / ck["ka40_excess_km2"] > .5     # 40 ka excess "mostly ice masses in north-east Asia"
assert 45 <= ck["every_greenland_pct"] <= 55                                                           # "about half of it Greenland"
assert R["source"]["missing"] == [] and R["areas"]["n_mapped"] == R["areas"]["n_stages"] == 18 and R["source"]["dropped_sh_stages"] == ["lgauss", "ka45"]
assert ST["lgm"]["on_sea_pct"] > 30
assert SO["na_min_same"] == ["mis12", "mis6"] and R["south_extra"]["na_min_to_ohio_mouth_km"] < 40       # MIS 6 and MIS 12 to 37.2 N near the Ohio's mouth
assert SO["lgm_na"]["near"] == "Bloomington" and -87 < SO["lgm_na"]["lon"] < -85.5                     # Bloomington, Indiana
assert SO["lgm_eu"]["near"] == "Cork" and SO["lgm_eu"]["lat"] < 51 and SO["lgm_eu"]["near_km"] > 100   # on the floor of the Celtic Sea south of Ireland
assert 51 < R["south_extra"]["lgm_eu_mainland_lat"] < 53                                               # mainland: northern Germany and Poland
assert SO["mis6_eu"]["near"] == "Dnipro" and SO["eu_min_stage"] == "mis6"                              # down the Dnieper
assert ST["mis16"]["south"]["eu"]["near"] == "Kamensk Shakhtinskiy" and ST["mis16"]["south"]["eu"]["lat"] < 49.5   # Don basin
B = C["by_iso"]
assert all(B[i]["lgm_pct"] >= 99.5 for i in ("IRL", "SWE", "FIN", "ISL", "EST", "LVA")) and 95 < B["NOR"]["lgm_pct"] < 99.95 and 95 < B["LTU"]["lgm_pct"] < 99.5
assert B["CAN"]["lgm_pct"] > 95 and B["NLD"]["lgm_pct"] == 0
assert P["lgm_top"][0]["name"] == "New York" and CI["New York"]["lgm"] < 0 and CI["New York"]["lgm"] > -30   # "reached Manhattan"
for c in ("Chicago", "Toronto", "Berlin", "Seattle"): assert CI[c]["lgm"] < 0, c
assert {"Moscow", "Philadelphia", "Kyiv", "Birmingham", "Warsaw"} <= {x["name"] for x in P["union_not_lgm_top"]}
assert CI["London"]["n_under"] == 0 and CI["London"]["closest"]["stage"] == "mis12" and CI["London"]["mis12"] < 30
assert CI["Moscow"]["lgm"] > 0 and CI["Moscow"]["n_under"] == 3
assert CI["Paris"]["n_under"] == 0 and CI["Prague"]["n_under"] == 0 and CI["Amsterdam"]["under"] == ["mis6"] and CI["Amsterdam"]["lgm"] > 0
SH = R["shelves"]; assert SH[0]["region"] == "Sahul" and SH[1]["region"] == "Sundaland" and SH[2]["region"].startswith("Siberian") and SH[3]["region"] == "Beringia"
assert all(j["m60"] and j["m120"] and not j["m0"] for j in R["joins"]) and len(R["joins"]) == 11
assert R["shelf"]["doggerland"]["m120"] > R["shelf"]["doggerland"]["m120_ice_free"]                   # "its northern part lay under the ice"
assert abs(R["exposed"]["m120"]["km2"] / R["exposed"]["land_today"] * 100 - R["exposed"]["m120"]["pct_of_land"]) < .05


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    left = re.findall(r"\{\{[^}]*\}\}", html)
    assert set(left) <= {"10.5281/zenodo.23878610", "https://blog.tristanhotham.com/2026/10/31/ice-ages/"}, left[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*COUNTRIES*/", J({k: v for k, v in jload(f"{DATA}/countries.json").items() if v["pop"] > 2e5}))
    html = html.replace("/*CITIES*/", J([{"name": c["name"], "country": c["country"], "lat": c["lat"], "lon": c["lon"], "pop": c["pop"]} for c in jload(f"{DATA}/cities.json")]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
