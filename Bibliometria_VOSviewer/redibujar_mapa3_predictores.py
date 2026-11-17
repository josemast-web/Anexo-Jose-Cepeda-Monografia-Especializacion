# Redraws the predictor network using the layout (x, y, clusters) computed by VOSviewer 1.6.21. Python 3.13+
import csv, math, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
for f in fm.findSystemFonts():
    if "Inter-Regular" in f: fm.fontManager.addfont(f)
plt.rcParams["font.family"] = "Inter"
D, OUT = sys.argv[1], sys.argv[2]
nodes = {r["id"]: r for r in csv.DictReader(open(f"{D}/mapa3_predictores.txt", encoding="utf-8-sig"), delimiter="\t")}
links = [l.split("\t") for l in open(f"{D}/red_predictores_network.txt", encoding="utf-8").read().splitlines() if l.strip()]
FILL = {"1": "#F4C7C3", "2": "#C8E6C9", "3": "#C9DDF2"}; EDGE = {"1": "#C98A84", "2": "#86B48A", "3": "#86A8CF"}
# Manual label offsets (tuned for the 58-study layout of 19/10/2026) (dx, dy, horizontal alignment); node positions are VOSviewer's, unchanged
LAB = {"1": (0, .1, "center"), "2": (-.06, -.1, "right"), "3": (.03, .11, "center"), "4": (-.075, 0, "right"),
       "5": (0, .085, "center"), "6": (0, -.085, "center"), "7": (.06, 0, "left"), "8": (-.055, 0, "right"),
       "9": (0, -.11, "center"), "10": (0, -.075, "center"), "11": (0, .11, "center"), "12": (-.05, 0, "right"),
       "13": (.05, 0, "left")}
WRAP = {"9": "Variables climáticas y ambientales\nsin desglose", "11": "Movilidad /\nbúsquedas digitales"}
fig, ax = plt.subplots(figsize=(11, 7.6), dpi=220); ax.axis("off")
X = {k: float(v["x"]) for k, v in nodes.items()}; Y = {k: -float(v["y"]) for k, v in nodes.items()}
wmax = max(int(l[2]) for l in links)
for a, b, w in sorted(links, key=lambda l: int(l[2])):
    w = int(w); ax.plot([X[a], X[b]], [Y[a], Y[b]], color="#A8A8A8", lw=0.4 + 3.6 * w / wmax, alpha=0.30 + 0.45 * w / wmax, zorder=1, solid_capstyle="round")
for k, n in nodes.items():
    s = int(float(n["weight<Estudios>"]))
    ax.scatter(X[k], Y[k], s=60 + 1100 * math.sqrt(s / 50), color=FILL[n["cluster"]], edgecolor=EDGE[n["cluster"]], lw=1.0, zorder=2)
    dx, dy, ha = LAB[k]
    ax.text(X[k] + dx, Y[k] + dy, f"{WRAP.get(k, n['label'])} ({s})", fontsize=11 if s >= 15 else 9.5,
            color="black", ha=ha, va="center", zorder=3, linespacing=1.15)
leg = [Line2D([0], [0], marker="o", lw=0, markersize=10, markerfacecolor=FILL[c], markeredgecolor=EDGE[c], label=t)
       for c, t in (("1", "Climáticos"), ("2", "Epidemiológicos"), ("3", "Otros (demográficos, calendario, vegetación, movilidad, localidades)"))]
ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=3, frameon=False, fontsize=9.5)
ax.set_xlim(-1.25, 1.42); ax.set_ylim(-0.92, 0.9)
fig.savefig(OUT, bbox_inches="tight", facecolor="white"); print("ok")
