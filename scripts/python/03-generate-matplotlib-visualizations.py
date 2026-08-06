from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/processed/03-gene-expression.csv"
OUT = ROOT / "results/figures"
OUT.mkdir(parents=True, exist_ok=True); DATA.parent.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20260806)
genes = ["TP53", "BRCA1", "EGFR", "MYC", "PTEN", "KRAS"]
rows=[]
for i,gene in enumerate(genes):
    for condition,shift in [("Control",0),("Treatment",[1.8,.9,1.5,2.2,-1.0,.7][i])]:
        for replicate in range(1,7):
            rows.append((gene,condition,replicate,round(6+i*.45+shift+rng.normal(0,.32),2)))
df=pd.DataFrame(rows,columns=["gene","condition","replicate","log2_expression"]); df.to_csv(DATA,index=False)
colors={"Control":"#64748B","Treatment":"#DC2626"}
fig,ax=plt.subplots(figsize=(9,5.2))
for c in colors:
    d=df[df.condition==c]; x=np.array([genes.index(g) for g in d.gene])+(-.14 if c=="Control" else .14)
    ax.scatter(x,d.log2_expression,label=c,color=colors[c],alpha=.72,s=35)
ax.set(xticks=range(len(genes)),xticklabels=genes,ylabel="log2 expression",xlabel="Gene",title="Expression by condition and replicate")
ax.legend(frameon=False); ax.spines[['top','right']].set_visible(False); fig.tight_layout(); fig.savefig(OUT/"03-expression-replicates.png",dpi=180); plt.close(fig)
summary=df.groupby(["gene","condition"],sort=False).log2_expression.agg(['mean','std']).reset_index()
fig,ax=plt.subplots(figsize=(9,5.2)); x=np.arange(len(genes)); w=.36
for j,c in enumerate(colors):
    d=summary[summary.condition==c]; ax.bar(x+(j-.5)*w,d['mean'],w,yerr=d['std'],capsize=4,label=c,color=colors[c])
ax.set(xticks=x,xticklabels=genes,ylabel="Mean log2 expression",title="Mean expression with replicate variability"); ax.legend(frameon=False); ax.spines[['top','right']].set_visible(False); fig.tight_layout(); fig.savefig(OUT/"03-expression-summary.png",dpi=180); plt.close(fig)
pd.DataFrame([{"figure":"03-expression-replicates.png","purpose":"show replicate-level variation"},{"figure":"03-expression-summary.png","purpose":"compare group means and standard deviations"}]).to_csv(ROOT/"results/03-matplotlib-figure-manifest.csv",index=False)
print(f"Wrote {len(df)} rows and 2 figures")
