"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23878610 placeholder.
Needs only data/ and the figures."""
import subprocess, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_When_the_Ice_Came_South"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))   # shared checks
ST = R["stages"]

# statements made in words in the paper only
assert R["source"]["invalid_in"] > 0 and R["source"]["missing"] == [] and R["countries"]["by_iso"]["UKR"]["lgm_pct"] == 0
assert R["cities"]["London"]["lgm"] > 0 and R["shelves"][0]["m120_ice_free"] > 2e6


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f in ("f1", "f2", "m1", "m2", "abs"): return fmt(v, f)
    return tex(str(v))


m = lambda v: "" if v is None else f"{v / 1e6:.2f}"
rows = "".join(f"{tex(s['label'])} & {tex(s['age'])} & {m(s['area'])} & {s.get('rank', '')} & {m(s['tab_best'])} & {m(s['tab_min'])} & {m(s['tab_max'])} & {'' if s.get('on_sea_pct') is None else f'{s['on_sea_pct']:.1f}'}\\\\\n" for s in [ST[k] for k in SKEYS][::-1])
TA = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{Ice area by time slice, million \\kmq. Measured: the best-estimate outline in an equal-area projection; authors: \\citet{batchelor}'s table (best, minimum, maximum). Over sea: share of the measured ice over today's sea.}\\label{tab:areas}"
      "\\begin{tabular}{llrrrrrr}\\toprule Slice & Age & Measured & Rank & Authors & Min & Max & \\% over sea\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
so = lambda d: "" if not d else f"{d['lat']:.2f} & {tex(d['near'])} ({d['near_km']:,} km)"
rows = "".join(f"{tex(ST[k]['label'])} & {so(ST[k]['south']['na'])} & {so(ST[k]['south']['eu'])}\\\\\n" for k in SKEYS[::-1] if ST[k]["outline"])
TS = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{Southernmost latitude (°N) of outline polygons of 50,000 \\kmq\\ or more, and the nearest Natural Earth place of 50,000 people or more.}\\label{tab:south}"
      "\\begin{tabular}{lrlrl}\\toprule Slice & \\multicolumn{2}{c}{North America} & \\multicolumn{2}{c}{Europe}\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
MK = [k for k in SKEYS if ST[k]["outline"]]
C = sorted(SITE["cities"], key=lambda c: c["d"][SKEYS.index("lgm")])
rows = "".join(f"{tex(c['name'])} & {tex(c['country'])} & {c['d'][SKEYS.index('lgm')]:,.0f} & {sum(c['d'][SKEYS.index(k)] < 0 for k in MK)} & {tex(', '.join(ST[k]['label'] for k in MK if c['d'][SKEYS.index(k)] < 0)) or 'none'}\\\\\n" for c in C)
TC = ("\\begin{table}[tbp]\\centering\\scriptsize\\setlength{\\tabcolsep}{3pt}\\caption{Distance from city centres to the LGM ice edge (km; negative inside the ice) and the slices whose best-estimate outline contains the city.}\\label{tab:cities}"
      "\\begin{tabular}{llrrp{7.2cm}}\\toprule City & Country & km & Slices & Which\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
bx = lambda b: "; ".join(f"{a}..{c}°E, {d}..{e}°N".replace("-", "$-$") for a, d, c, e in b)
rows = "".join(f"{tex(r['region'])} & {tex(r['covers'])} & {r['m60_ice_free']:,} & {r['m120_ice_free']:,} & {r['m120']:,}\\\\\n" for r in R["shelves"])
TH = ("\\begin{table}[tbp]\\centering\\scriptsize\\setlength{\\tabcolsep}{3pt}\\caption{Sea floor exposed by sea levels 60 m and 120 m below today's in the shelf boxes (\\kmq): ice-free at 60 m and 120 m, and all exposed floor at 120 m including that under the LGM ice. Boxes: " + tex("; ".join(f"{r['region']} " + bx(r['boxes']) for r in R['shelves'])).replace("\\$", "$") + ".}\\label{tab:shelves}"
      "\\begin{tabular}{lp{5.6cm}rrr}\\toprule Region & Seas & 60 m & 120 m & 120 m, all\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo", "osf"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = fill(t, R, f=lambda v, f: tfmt(v, f or "raw"))
for k, v in (("AREAS", TA), ("SOUTH", TS), ("CITIES", TC), ("SHELVES", TH)):
    t = t.replace("{{TABLE_%s}}" % k, v)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
for bad in ("DSIT", "DCMS", "civil serv"):
    assert bad not in txt
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
