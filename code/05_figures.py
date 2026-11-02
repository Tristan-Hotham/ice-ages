"""Header card, blog figures (release/blog/b_*.png, 1800 px wide) and paper figures (release/paper/f_*.png).
Numbers from data/results.json; outlines from data/ice_outlines.geojson and data/exposed.json. Needs only data/."""
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
ST = R["stages"]; MK = [k for k in SKEYS if ST[k]["outline"]]
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
HALO = [pe.withStroke(linewidth=3.2, foreground=SEA)]
HALOP = [pe.withStroke(linewidth=3.2, foreground=BG)]
HALOI = [pe.withStroke(linewidth=3.2, foreground=ICEF)]


def both(fig, name, blog=True):
    """Paper at 200 dpi; blog at exactly 1800 px wide."""
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=1800 / fig.get_figwidth(), facecolor=fig.get_facecolor())
    plt.close(fig)


def ice_map(ax, k, sea=True, maxline=False, lgmline=False, lw=.7):
    if sea: patch(ax, exp_p(120), fc=SAND, ec="none", zorder=1.2)
    patch(ax, ice_p(k), fc=ICEF, ec=ICEE, lw=lw, alpha=.95, zorder=2)
    if maxline: patch(ax, ice_p("max"), fc="none", ec=MAXC, lw=.9, ls=(0, (3, 2)), zorder=3)
    if lgmline: patch(ax, ice_p("lgm"), fc="none", ec=HOT, lw=.9, ls=(0, (3, 2)), zorder=3)


def city(ax, name, dx, dy, ha="left", col=FG, halo=HALO, size=9.5):
    c = R["cities"][name]; r = [x for x in SITE["cities"] if x["name"] == name][0]
    x, y = pxy(r["lon"], r["lat"])
    ax.plot([x], [y], "o", ms=3.2, color=FG, mec="#fff", mew=.6, zorder=6)
    ax.text(x + dx, y + dy, name, ha=ha, va="center", fontsize=size, color=col, path_effects=halo, zorder=7)


# ---------- 1. the LGM and the furthest ice ----------
fig = plt.figure(figsize=(12, 11.4), facecolor=BG); ax = fig.add_axes([0, .07, 1, .86])
polar_base(ax); ice_map(ax, "lgm", maxline=True)
for nm, dx, dy, ha in (("New York", 1.2e5, -1.2e5, "left"), ("Chicago", -1.2e5, -1.2e5, "right"), ("Seattle", -1.2e5, 0, "right"), ("London", -1.2e5, -1.0e5, "right"),
                       ("Berlin", 1.1e5, -1.0e5, "left"), ("Moscow", 1.2e5, 0, "left"), ("Kyiv", 1.2e5, 0, "left"), ("Toronto", 1.2e5, 1.0e5, "left")):
    city(ax, nm, dx, dy, ha)
for t, lo, la in (("Laurentide", -85, 60), ("Cordilleran", -127, 57), ("Greenland", -40, 74), ("Eurasian", 25, 67)):
    x, y = pxy(lo, la); ax.text(x, y, t.upper(), ha="center", va="center", fontsize=10.5, color=ICEE, family=MONO, fontweight="medium", alpha=.9, zorder=8)
fig.text(.03, .975, f"The ice at the Last Glacial Maximum, about 26,500 years ago: {ST['lgm']['area'] / 1e6:.1f} million km². Dashed purple: the furthest ice of any\nof the {R['areas']['n_mapped']} slices ({R['areas']['union'] / 1e6:.1f} million km²). Sand: sea floor dry with the sea 120 m lower.", fontsize=10.5, color=FG, va="top", linespacing=1.4)
H = [Patch(fc=ICEF, ec=ICEE, label="ice at the LGM (best estimate)"), Line2D([], [], color=MAXC, ls=(0, (3, 2)), label="furthest ice of any slice"), Patch(color=SAND, label="dry with the sea 120 m lower")]
fig.legend(handles=H, loc="lower left", ncol=3, frameon=False, fontsize=9.5, bbox_to_anchor=(.02, .01))
fig.text(.98, .012, "Ice: Batchelor et al. (2019). Sea floor: ETOPO1. Outlines: Natural Earth.", ha="right", fontsize=8.5, color=MUT)
both(fig, "map")

# ---------- 2. every slice ----------
fig, axs = plt.subplots(3, 6, figsize=(12, 7.6), facecolor=BG); fig.subplots_adjust(left=.005, right=.995, top=.93, bottom=.02, wspace=.03, hspace=.2)
EXT2 = (-5.2e6, 5.4e6, -5.6e6, 4.6e6)
for a, k in zip(axs.flat, MK):
    polar_base(a, ext=EXT2, lw=.15, grid=False); ice_map(a, k, sea=False, lw=.45)
    if k != "lgm": patch(a, ice_p("lgm"), fc="none", ec=HOT, lw=.45, ls=(0, (2, 1.5)), zorder=3)
    a.set_title(f"{SL[k]}", fontsize=10, color=FG, pad=2, fontweight="medium")
    a.text(.03, .04, f"{ST[k]['area'] / 1e6:.1f}m km²", transform=a.transAxes, fontsize=8.2, color=FG, path_effects=HALO, zorder=9)
    if SINFO[k]["warm"]: a.text(.97, .04, "warm peak", transform=a.transAxes, ha="right", fontsize=7.6, color=MUT, path_effects=HALO, zorder=9)
assert len(MK) == 18
fig.text(.01, .975, f"The ice in each of the {R['areas']['n_mapped']} time slices of Batchelor et al. (2019), best estimates, oldest first. Red dashes: the LGM ice, for comparison", fontsize=10.5, color=FG, va="top")
both(fig, "stages")

# ---------- 3. areas ----------
rows = [ST[k] for k in SKEYS][::-1]
fig, ax = plt.subplots(figsize=(12, 7.4), facecolor=BG); fig.subplots_adjust(left=.2, right=.9, top=.9, bottom=.08); ax.set_facecolor(BG)
for i, s in enumerate(rows):
    y = len(rows) - 1 - i
    if s["tab_min"]: ax.plot([s["tab_min"] / 1e6, s["tab_max"] / 1e6], [y, y], color=MUT, lw=1, zorder=1); ax.plot([s["tab_min"] / 1e6] * 2, [y - .18, y + .18], color=MUT, lw=1); ax.plot([s["tab_max"] / 1e6] * 2, [y - .18, y + .18], color=MUT, lw=1)
    ax.barh(y, s["area"] / 1e6, height=.62, color=ICEE if s["key"] == "mis6" else ICED, hatch="////" if s["warm"] else None, edgecolor=ICEE if s["warm"] else "none", lw=0, zorder=2, fill=not s["warm"])
    ax.plot([s["tab_best"] / 1e6] * 2, [y - .38, y + .38], color=FG, lw=1.6, zorder=3)
    xe = max(s["area"], s["tab_max"] or 0, s["tab_best"]) / 1e6
    ax.text(xe + .5, y, f"{s['area'] / 1e6:.1f}", va="center", fontsize=9.5, color=FG)
lab = lambda s: s["label"] + ("\n" + (f"{s['ka0'] / 1000:.2f} to {s['ka1'] / 1000:.2f} Ma" if s["ka1"] >= 1000 else (f"{s['ka0']:g} ka" if s["key"] == "lgm" else f"{s['ka0']:g} to {s['ka1']:g} ka")) if s["ka0"] != s["ka1"] or s["key"] == "lgm" else "")
ax.set_yticks(range(len(rows))); ax.set_yticklabels([lab(s) for s in rows][::-1], fontsize=8.6, linespacing=1.0); ax.tick_params(axis="y", length=0)
ax.set_xlim(0, 39); ax.set_xlabel("million km²", fontsize=10, color=MUT); spines(ax); ax.grid(axis="x", color=RULE, lw=.6); ax.set_axisbelow(True)
fig.text(.02, .965, "Ice area in each time slice (best-estimate outlines, measured in an equal-area projection), newest at the top.\nGrey lines: the authors' minimum to maximum; black ticks: their figure for the best estimate. Hatched: drawn at the warm peak.", fontsize=10, color=FG, va="top", linespacing=1.4)
both(fig, "areas")

# ---------- 4. southernmost reach ----------
rows = [ST[k] for k in MK][::-1]
fig, ax = plt.subplots(figsize=(12, 6.6), facecolor=BG); fig.subplots_adjust(left=.14, right=.97, top=.88, bottom=.1); ax.set_facecolor(BG)
for i, s in enumerate(rows):
    y = len(rows) - 1 - i
    ax.plot([36, 60], [y, y], color=RULE, lw=.6, ls=(0, (1, 3)), zorder=0)
    for c, col in (("na", NA_C), ("eu", EU_C)):
        if s["south"][c]: ax.plot(s["south"][c]["lat"], y, "o", ms=8, color=col, mec="#fff", mew=.8, zorder=3)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([s["label"] for s in rows][::-1], fontsize=9.5); ax.tick_params(axis="y", length=0)
ax.set_xlim(36, 60); ax.set_xticks(range(36, 61, 4)); ax.set_xticklabels([f"{v}°N" for v in range(36, 61, 4)]); spines(ax); ax.spines["left"].set_visible(False)
n = R["south"]; yl = len(rows) - 1 - [s["key"] for s in rows].index("mis12")
ax.text(n["na_min"]["lat"] + .45, yl + .5, "MIS 6 and MIS 12: near the mouth of the Ohio", fontsize=8.8, color=NA_C, va="center")
y6 = len(rows) - 1 - [s["key"] for s in rows].index("mis6")
ax.annotate("Dnieper lobe, Ukraine", (n["mis6_eu"]["lat"], y6), (n["mis6_eu"]["lat"] + .6, y6 + .45), fontsize=8.8, color=EU_C, va="center")
yg = len(rows) - 1 - [s["key"] for s in rows].index("lgm")
ax.annotate("Celtic Sea, south of Ireland", (n["lgm_eu"]["lat"], yg), (n["lgm_eu"]["lat"] + .6, yg - .5), fontsize=8.8, color=EU_C, va="center")
fig.legend(handles=[Line2D([], [], ls="", marker="o", ms=8, color=NA_C, label="North America (170°W to 50°W)"), Line2D([], [], ls="", marker="o", ms=8, color=EU_C, label="Europe (12°W to 60°E)")],
           loc="upper right", ncol=2, frameon=False, fontsize=9.5, bbox_to_anchor=(.97, .935))
fig.text(.02, .965, "How far south the ice reached: the lowest latitude on any outline of 50,000 km² or more, by slice (newest at the top)", fontsize=10.5, color=FG, va="top")
both(fig, "south")

# ---------- 5. countries ----------
rows = [r for r in R["countries"]["union_top_pct"] if r["pct"] >= 5]
lg = {r["iso"]: r["pct"] for r in R["countries"]["lgm_top_pct"]}
fig, ax = plt.subplots(figsize=(12, 6.8), facecolor=BG); fig.subplots_adjust(left=.17, right=.95, top=.88, bottom=.08); ax.set_facecolor(BG)
for i, r in enumerate(rows):
    y = len(rows) - 1 - i
    ax.barh(y, r["pct"], height=.66, color="#C9DCEC"); ax.barh(y, lg.get(r["iso"], 0), height=.66, color=ICEE)
    ax.text(r["pct"] + 1, y, f"{r['pct']:.0f}%", va="center", fontsize=9)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r["name"] for r in rows][::-1], fontsize=9.5); ax.tick_params(axis="y", length=0)
ax.set_xlim(0, 108); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(["0", "25%", "50%", "75%", "100%"]); spines(ax); ax.grid(axis="x", color=RULE, lw=.6); ax.set_axisbelow(True)
fig.legend(handles=[Patch(color=ICEE, label="under the LGM ice"), Patch(color="#C9DCEC", label="under the ice in at least one slice")], loc="upper right", ncol=2, frameon=False, fontsize=9.5, bbox_to_anchor=(.95, .935))
fig.text(.02, .965, "Share of each country's area under the ice (countries over 20,000 km² with at least 5% in any slice)", fontsize=10.5, color=FG, va="top")
both(fig, "countries")

# ---------- 6. cities ----------
C = sorted(SITE["cities"], key=lambda c: c["d"][SKEYS.index("lgm")])
fig, ax = plt.subplots(figsize=(12, 9.2), facecolor=BG); fig.subplots_adjust(left=.15, right=.71, top=.92, bottom=.07); ax.set_facecolor(BG)
for i, c in enumerate(C):
    y = len(C) - 1 - i; d = c["d"][SKEYS.index("lgm")]
    ax.plot([0, d], [y, y], color=ICEE if d < 0 else MUT, lw=1.4, zorder=2); ax.plot(d, y, "o", ms=6.5, color=ICEE if d < 0 else "#fff", mec=ICEE if d < 0 else MUT, mew=1.2, zorder=3)
    nu = sum(1 for k in MK if c["d"][SKEYS.index(k)] < 0)
    ax.text(1.03, y, f"{nu:>2} of {len(MK)}", transform=ax.get_yaxis_transform(), va="center", fontsize=9, color=FG)
    for j, k in enumerate(MK):
        on = c["d"][SKEYS.index(k)] < 0
        ax.add_patch(plt.Rectangle((1.175 + j * .0145, y - .32), .0125, .64, transform=ax.get_yaxis_transform(), clip_on=False, fc=ICEE if on else "none", ec=ICEE if on else RULE, lw=.6))
ax.axvline(0, color=FG, lw=.8); ax.set_yticks(range(len(C))); ax.set_yticklabels([c["name"] for c in C][::-1], fontsize=9.2); ax.tick_params(axis="y", length=0)
ax.set_xlabel("km from the edge of the LGM ice (negative: under the ice)", fontsize=10, color=MUT); spines(ax); ax.spines["left"].set_visible(False); ax.grid(axis="x", color=RULE, lw=.6); ax.set_axisbelow(True)
ax.text(1.03, len(C) + .3, "slices with ice over it,\noldest to LGM", transform=ax.get_yaxis_transform(), fontsize=8.6, color=MUT, va="bottom")
fig.text(.02, .975, "Big cities and the ice: distance from the city centre to the edge of the LGM ice, and the slices whose ice covered it", fontsize=10.5, color=FG, va="top")
both(fig, "cities")

# ---------- 7. land from the sea ----------
fig = plt.figure(figsize=(12, 6.9), facecolor=BG); ax = fig.add_axes([0, .06, 1, .84]); ax.set_facecolor(BG)
NHW = box(-180, -56, 180, 84)
patch(ax, tf(shapely.make_valid(box(-180, -56, 180, 84)), EE, 1), fc=SEA, ec="none", zorder=0)
patch(ax, tf(shapely.make_valid(WG.intersection(NHW)), EE, .5), fc=LAND, ec="#fff", lw=.25, zorder=1)
patch(ax, tf(shapely.make_valid(EXPO[120].intersection(NHW)), EE, .5), fc=SAND, ec="none", zorder=1.5)
patch(ax, tf(shapely.make_valid(EXPO[60].intersection(NHW)), EE, .5), fc=SAND2, ec="none", zorder=1.6)
patch(ax, tf(shapely.make_valid(OUT["lgm"].intersection(NHW)), EE, .2), fc=ICEF, ec=ICEE, lw=.5, zorder=2)
SHX = {r["region"]: r for r in R["shelves"]}
LAB = [("Sahul", 133, -14, 108, -33, "center"), ("Sundaland", 107, 3, 92, -14, "center"), ("Siberian Arctic shelf", 118, 76, 118, 93, "center"),
       ("Beringia", -172, 63, -150, 47, "center"), ("East China and Yellow seas", 124, 31, 158, 22, "center"), ("Patagonian shelf", -62, -48, -38, -44, "left"),
       ("Doggerland", 3, 54, -24, 44, "right"), ("Persian Gulf", 51, 27, 58, 8, "center")]
for nm, lo, la, tlo, tla, ha in LAB:
    x, y = EE.transform(lo, la); tx, ty = EE.transform(tlo, min(tla, 89.9)); r = SHX[nm]
    if tla > 90: ty += (tla - 90) * 1.6e5          # label in the margin above the map
    ax.annotate(f"{nm.replace('East China and Yellow seas', 'East China and\nYellow seas')}\n{r['m120_ice_free'] / 1e6:.2f}m km²" if r["m120_ice_free"] >= 1e6 else f"{nm}\n{r['m120_ice_free'] / 1e3:,.0f},000 km²", (x, y), (tx, ty), ha=ha, va="center", fontsize=8.8, color=FG,
                path_effects=HALOP, zorder=6, arrowprops=dict(arrowstyle="-", color=FG, lw=.6, shrinkA=1, shrinkB=2))
x0, _ = EE.transform(-180, 0); x1, _ = EE.transform(180, 0); _, y0 = EE.transform(0, -56); _, y1 = EE.transform(0, 90); y1 += 9e5
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.axis("off")
fig.text(.02, .975, f"Land from the sea: a fall of 120 m uncovers {R['exposed']['m120']['km2'] / 1e6:.1f} million km² of sea floor, {R['exposed']['m120']['ice_free'] / 1e6:.1f} million of it outside the LGM ice.\nDark sand: already dry at 60 m lower. Figures: ice-free land at 120 m lower in boxes drawn round each shelf.", fontsize=10.5, color=FG, va="top", linespacing=1.4)
fig.legend(handles=[Patch(color=SAND2, label="dry at 60 m lower"), Patch(color=SAND, label="dry at 120 m lower"), Patch(fc=ICEF, ec=ICEE, label="LGM ice")], loc="lower left", ncol=3, frameon=False, fontsize=9.5, bbox_to_anchor=(.02, .0))
fig.text(.98, .015, "Sea floor: ETOPO1 (ETOPO10). Ice: Batchelor et al. (2019).", ha="right", fontsize=8.5, color=MUT)
both(fig, "exposed")

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.42, .0, .58, 1]); polar_base(ax, ext=(-5.4e6, 5.6e6, -5.9e6, 4.6e6), lw=.2); ice_map(ax, "mis6", lw=.5); patch(ax, ice_p("lgm"), fc="none", ec=HOT, lw=.8, ls=(0, (3, 2)), zorder=3)
fig.text(.04, .86, "When the", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.04, .70, "ice came", fontproperties=DISP, fontsize=50, color=ICEE, va="top")
fig.text(.04, .54, "south", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.04, .35, f"The Northern Hemisphere's ice sheets\nat {R['areas']['n_stages']} moments of 3.6 million years.\nAt their largest, in MIS 6: {ST['mis6']['area'] / 1e6:.1f} million km²\n(map; red dashes: the LGM).", fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.35)
fig.text(.04, .05, "maps.tristanhotham.com/ice-ages", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
