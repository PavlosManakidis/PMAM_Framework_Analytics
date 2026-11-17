"""Regenerates Figures 1 and 2 (600 dpi). Usage: python pmam_figures.py pmam_scores.csv outdir"""
import sys, numpy as np, matplotlib
import csv
def load_scores(path):
    J=["Denmark","Flanders","Italy","Greece","Portugal","Ireland"]
    M={(r["jurisdiction"],r["dimension"]):int(r["score"]) for r in csv.DictReader(open(path,encoding="utf8"))}
    return np.array([[M[(j,f"D{k}")] for k in range(1,9)] for j in J])
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
plt.rcParams.update({"font.size":9})
J=["Denmark","Flanders","Italy","Greece","Portugal","Ireland"]
S=load_scores(sys.argv[1])
COL=["#f7fbff","#c6dbef","#6baed6","#2171b5","#08306b"]  # single-hue sequential, colour-blind safe
out=sys.argv[2]
fig,ax=plt.subplots(figsize=(6.45,3.29))
im=ax.imshow(S,cmap=ListedColormap(COL),norm=BoundaryNorm(np.arange(-.5,5.5,1),5),aspect="auto")
ax.set_xticks(range(8),[f"D{i}" for i in range(1,9)]); ax.set_yticks(range(6),J)
ax.set_xticks(np.arange(-.5,8,1),minor=True); ax.set_yticks(np.arange(-.5,6,1),minor=True)
ax.grid(which="minor",color="white",lw=1.5); ax.tick_params(which="minor",length=0)
for i in range(6):
    for j in range(8):
        ax.text(j,i,f"L{S[i,j]}",ha="center",va="center",fontsize=8,fontweight="bold",color="white" if S[i,j]>=3 else "#1f2a36")
for s in ax.spines.values(): s.set_visible(False)
cb=fig.colorbar(im,ax=ax,ticks=range(5),fraction=0.035,pad=0.02); cb.ax.set_yticklabels(["L0","L1","L2","L3","L4"]); cb.outline.set_visible(False)
fig.tight_layout(); fig.savefig(f"{out}/Figure1_PMAM_heatmap.png",dpi=600); plt.close(fig)

x=S[:,0:4].mean(1); y=S[:,4:7].mean(1)
pts={n:[x[i],y[i]] for i,n in enumerate(J)}
mk={"Denmark":("D","#1f4e79"),"Flanders":("s","#d35f2b"),"Italy":("^","#2e7d32"),"Greece":("X","#2a9fd6"),"Portugal":("P","#8e3b8e"),"Ireland":("o","#7a5c00")}
off={"Denmark":(7,0,"left"),"Flanders":(7,0,"left"),"Italy":(-7,0,"right"),"Greece":(0,-11,"center"),"Portugal":(7,0,"left"),"Ireland":(7,0,"left")}
fig,ax=plt.subplots(figsize=(5.89,3.40))
for i,n in enumerate(J):
    m,c=mk[n]; px,py=pts[n]
    ax.scatter(px,py,marker=m,s=46,color=c,zorder=3,edgecolor="white",linewidth=0.5)
    dx,dy,ha=off[n]
    ax.annotate(f"{n} (D8=L{S[i,7]})",(px,py),xytext=(dx,dy),textcoords="offset points",ha=ha,va="center",fontsize=7.5)
ax.set_xlim(1.5,3.5); ax.set_ylim(2.0,3.25); ax.set_xticks(np.arange(1.5,3.51,.25)); ax.set_yticks(np.arange(2.0,3.26,.25))
ax.set_xlabel("Rights and sharing maturity (mean of D1–D4)"); ax.set_ylabel("Market and system integration\n(mean of D5–D7)")
ax.grid(ls="--",lw=0.5,color="#d9d9d9"); ax.set_axisbelow(True)
for s in ["top","right"]: ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(f"{out}/Figure2_rights_vs_integration.png",dpi=600); plt.close(fig)
