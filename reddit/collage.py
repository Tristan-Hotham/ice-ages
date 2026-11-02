"""r/dataisbeautiful collage for ice-ages: 2400 x 3200 px, light background. Numbers from data/results.json.
Map labels sit on open sea or on the paper around the map, with a halo, and are checked against land, the ice, the
exposed sea floor and each other; a leader line, where needed, must not cross another label or leader."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from shapely.geometry import box as _box, Point as _Pt, LineString as _LS
from shapely.ops import unary_union, nearest_points
from shapely.prepared import prep as _prep

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
ST = R["stages"]; MK = [k for k in SKEYS if ST[k]["outline"]]
BGc = "#F7F5F0"; SEAc = "#E4ECF0"; LANDc = "#E3DED2"
HALO = [pe.withStroke(linewidth=4, foreground=SEAc)]
CI = R["cities"]

fig = plt.figure(figsize=(12, 16.0), dpi=200, facecolor=BGc)
fig.text(.045, .985, "When the ice came south", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(.045, .938, f"The Northern Hemisphere's ice sheets at {R['areas']['n_stages']} moments of the last 3.6 million years. The last ice age was not\n"
         f"the biggest: {ST['mis6']['area'] / 1e6:.1f} million km² of ice {SINFO['mis6']['age'].replace('years ago', 'years ago,')} {R['areas']['mis6_over_lgm_pct']}% more than\n"
         f"the {ST['lgm']['area'] / 1e6:.1f} million km² of the Last Glacial Maximum 26,500 years ago.",
         fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.3)

# ---- map
ax = fig.add_axes([0, .455, 1, .405]); ax.set_facecolor(SEAc)
EXT = (-6.3e6, 6.3e6, -6.7e6, 4.35e6)
polar_base(ax, ext=EXT, land=LANDc, sea=SEAc, lw=.25); ax.set_aspect("equal", adjustable="datalim")
patch(ax, exp_p(120), fc=SAND, ec="none", zorder=1.2)
patch(ax, ice_p("max"), fc="#C9DCEC", ec="none", zorder=1.8)
patch(ax, ice_p("mis6"), fc="none", ec=NAVY, lw=.9, ls=(0, (3, 2)), zorder=3)
patch(ax, ice_p("lgm"), fc=ICEF, ec=ICEE, lw=.9, zorder=2)

# ---- obstacles in map metres
fig.canvas.draw(); REN = fig.canvas.get_renderer()
EXT = (*ax.get_xlim(), *ax.get_ylim())
OBST = unary_union([LAND_P.buffer(3e4), ice_p("max").buffer(3e4), exp_p(120).buffer(3e4)])
OBSTP = _prep(OBST)
PLACED, LINES = [], []


def tbox(t):
    bb = t.get_window_extent(REN)
    (x0, y0), (x1, y1) = ax.transData.inverted().transform([[bb.x0 - 6, bb.y0 - 4], [bb.x1 + 6, bb.y1 + 4]])
    return _box(x0, y0, x1, y1)


def bad(b):
    if not _box(EXT[0] + 1e5, EXT[2] + 1e5, EXT[1] - 1e5, EXT[3] - 1e5).contains(b): return True
    return OBSTP.intersects(b) or any(b.intersects(o) for _, _, o in PLACED) or any(b.intersects(l) for _, l in LINES)


def place(name, txt, lon, lat, pref, ha="center", col=FG, size=9.5, w="medium", step=1.2e5, maxr=45):
    tx, ty = pxy(lon, lat); tx, ty = float(tx), float(ty)
    t = ax.text(0, 0, txt, ha=ha, va="center", fontsize=size, color=col, family=MONO, linespacing=1.15, zorder=10, path_effects=HALO, fontweight=w)
    px0, py0 = pxy(*pref)
    cands = [(px0 + i * step, py0 + j * step) for r in range(0, maxr + 1) for i in range(-r, r + 1) for j in range(-r, r + 1) if max(abs(i), abs(j)) == r]
    for x, y in cands:
        t.set_position((x, y)); b = tbox(t)
        if bad(b): continue
        c = _Pt(tx, ty); ln = None
        if b.distance(c) > 6e4:
            pb, _ = nearest_points(b, c)
            ln = _LS([(pb.x, pb.y), (c.x, c.y)])
            if any(ln.intersects(o) for _, _, o in PLACED) or any(ln.crosses(l) for _, l in LINES): continue
        PLACED.append((name, t, b))
        if ln is not None:
            LINES.append((name, ln)); ax.plot(*ln.xy, color=FG, lw=.7, zorder=9)
        ax.plot([tx], [ty], "o", ms=4, color=FG, mec="#fff", mew=.8, zorder=11)
        return
    t.remove(); raise RuntimeError(f"no clean spot for {name}")


def km(v): return f"{abs(v):,.0f} km"


place("ny", f"NEW YORK\n{km(CI['New York']['lgm'])} inside\nthe LGM ice", -73.98, 40.75, (-62, 36))
place("chicago", f"CHICAGO\nunder ice in\n{CI['Chicago']['n_under']} of {len(MK)} slices", -87.75, 41.83, (-110, 33))
place("london", f"LONDON\nnever under ice;\n{CI['London']['mis12']:.0f} km from it\nin MIS 12", -0.12, 51.5, (-22, 46))
place("moscow", f"MOSCOW\n{CI['Moscow']['lgm']:.0f} km clear of\nthe LGM ice; under\n{CI['Moscow']['n_under']} older slices", 37.6, 55.75, (60, 86))
for nm, t, b in PLACED:
    assert not OBSTP.intersects(b), nm
    assert not any(b.intersects(o) for n2, _, o in PLACED if n2 != nm), nm
for nm, l in LINES:
    assert not any(l.intersects(o) for n2, _, o in PLACED if n2 != nm), nm
print("labels ok:", len(PLACED), "leaders:", [n for n, _ in LINES])

H = [Patch(fc=ICEF, ec=ICEE, label="ice at the LGM, 26,500 years ago"), Line2D([], [], color=NAVY, ls=(0, (3, 2)), label="edge of the ice in MIS 6, the largest"),
     Patch(color="#C9DCEC", label=f"ice in at least one of the {len(MK)} slices"), Patch(color=SAND, label="sea floor dry with the sea 120 m lower")]
fig.legend(handles=H, loc="upper left", bbox_to_anchor=(.035, .447), ncol=2, frameon=False, prop=SERP.copy(), fontsize=11.5, handletextpad=.5, columnspacing=1.6)
for t in fig.legends[-1].get_texts(): t.set_fontsize(11.5)

# ---- numbers row
nums = [(f"{ST['mis6']['area'] / 1e6:.1f}m", ICEE, "km² of ice in MIS 6,\nthe largest slice"),
        (f"{R['places']['lgm']['n']:,}", HOT, "cities and towns now\non LGM ice ground"),
        (f"{R['south']['na_min']['lat']:.1f}°N", NAVY, "furthest south: southern\nIllinois, MIS 6 and 12"),
        (f"{R['exposed']['m120']['ice_free'] / 1e6:.1f}m", SAND2, "km² of new dry land\nwith the sea 120 m lower")]
for i, (big, col, sm) in enumerate(nums):
    xx = .045 + i * .235
    fig.text(xx, .393, big, fontproperties=DISP, fontsize=33, color=col, va="top")
    fig.text(xx, .352, sm, family=MONO, fontsize=10.5, color=FG, va="top", linespacing=1.25)

# ---- small multiples: six slices
SIX = ["lgauss", "mis16", "mis12", "mis6", "mis5a", "lgm"]
fig.text(.045, .298, f"Six of the {len(MK)} slices, oldest first (red dashes: the LGM, for comparison)", family=MONO, fontsize=12, color=FG, va="bottom")
for j, k in enumerate(SIX):
    a = fig.add_axes([.03 + j * .157, .19, .155, .1]); polar_base(a, ext=(-5.2e6, 5.4e6, -5.6e6, 4.6e6), land=LANDc, sea=SEAc, lw=.12, grid=False)
    patch(a, ice_p(k), fc=ICEF, ec=ICEE, lw=.4, zorder=2)
    if k != "lgm": patch(a, ice_p("lgm"), fc="none", ec=HOT, lw=.35, ls=(0, (2, 1.5)), zorder=3)
    fig.text(.03 + j * .157 + .0775, .186, f"{SINFO[k]['label']}\n{ST[k]['area'] / 1e6:.1f}m km²", ha="center", va="top", fontsize=9.5, color=FG, linespacing=1.2)

# ---- strip: area of every slice
a = fig.add_axes([.075, .072, .89, .06]); a.set_facecolor(BGc)
xs = np.arange(len(MK)); v = [ST[k]["area"] / 1e6 for k in MK]
a.bar(xs, v, color=[ICEE if k == "mis6" else (HOT if k == "lgm" else ICED) for k in MK], width=.75)
for x, vv in zip(xs, v): a.text(x, vv + .8, f"{vv:.0f}", ha="center", fontsize=8.5)
a.set_xticks(xs); a.set_xticklabels([SINFO[k]["label"].replace("Late Gauss", "Gauss").replace("Early Matuyama", "Matuy.").replace("MIS 20 to 24", "MIS 20+").replace("MIS ", "") for k in MK], fontsize=8.2)
spines(a); a.set_yticks([]); a.spines["left"].set_visible(False); a.set_ylim(0, 39)
fig.text(.045, .142, "Ice area in each slice, million km², oldest to newest (numbers: Marine Isotope Stages)", family=MONO, fontsize=12, color=FG, va="bottom")

fig.text(.045, .004, "Source: Batchelor et al. (2019), Nature Communications 10, 3713, best-estimate outlines (CC BY 4.0).\n"
         "Sea floor: ETOPO1 (NOAA). Places: Natural Earth. Areas measured in an equal-area projection; outlines are generalised.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/ice-ages", family=MONO, fontsize=8.4, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "when_the_ice_came_south.png")
fig.savefig(out, facecolor=BGc, dpi=200)
from PIL import Image
assert Image.open(out).size == (2400, 3200)
print("ok", out)
