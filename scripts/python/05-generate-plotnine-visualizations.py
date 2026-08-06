from pathlib import Path
import numpy as np
import pandas as pd
try:
    from plotnine import aes, facet_wrap, geom_hline, geom_point, geom_smooth, ggplot, labs, scale_color_manual, theme, theme_minimal
    HAVE_PLOTNINE = True
except ImportError:
    import matplotlib.pyplot as plt
    HAVE_PLOTNINE = False

ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/"data/processed/05-differential-expression.csv"; OUT=ROOT/"results/figures"
DATA.parent.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True); rng=np.random.default_rng(505)
n=240; pathways=np.resize(["Immune","Cell cycle","Metabolism"],n); effect=rng.normal(0,1.25,n); signal=np.abs(effect)*1.8+rng.gamma(1.5,.8,n); padj=np.clip(10**(-signal),1e-7,1); status=np.where((padj<.05)&(effect>1),"Up",np.where((padj<.05)&(effect< -1),"Down","Not significant"))
df=pd.DataFrame({"gene":[f"GENE{i:03d}" for i in range(1,n+1)],"pathway":pathways,"log2_fold_change":effect.round(3),"adjusted_p":padj,"status":status}); df["minus_log10_p"]=-np.log10(df.adjusted_p); df.to_csv(DATA,index=False)
palette={"Down":"#2563EB","Not significant":"#94A3B8","Up":"#DC2626"}
if HAVE_PLOTNINE:
    p=(ggplot(df,aes("log2_fold_change","minus_log10_p",color="status"))+geom_point(alpha=.72,size=2)+geom_hline(yintercept=-np.log10(.05),linetype="dashed",color="#475569")+scale_color_manual(values=palette)+labs(title="Differential-expression evidence",x="log2 fold change",y="-log10 adjusted p",color="Classification")+theme_minimal()+theme(figure_size=(8.5,5.2)))
    p.save(OUT/"05-volcano-grammar.png",dpi=180,verbose=False)
    p2=(ggplot(df,aes("log2_fold_change","minus_log10_p",color="status"))+geom_point(alpha=.65,size=1.8)+geom_smooth(method="lowess",se=False,color="#0F172A",size=.7)+facet_wrap("~pathway")+scale_color_manual(values=palette)+labs(title="One grammar, repeated by pathway",x="log2 fold change",y="-log10 adjusted p")+theme_minimal()+theme(figure_size=(10,4.5)))
    p2.save(OUT/"05-volcano-faceted.png",dpi=180,verbose=False)
else:
    fig,ax=plt.subplots(figsize=(8.5,5.2))
    for status,color in palette.items():
        d=df[df.status==status]; ax.scatter(d.log2_fold_change,d.minus_log10_p,s=22,alpha=.72,color=color,label=status)
    ax.axhline(-np.log10(.05),ls="--",color="#475569"); ax.set(title="Differential-expression evidence",xlabel="log2 fold change",ylabel="-log10 adjusted p"); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(OUT/"05-volcano-grammar.png",dpi=180); plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(10,4.5),sharex=True,sharey=True)
    for ax,pathway in zip(axes,sorted(df.pathway.unique())):
        for status,color in palette.items():
            d=df[(df.pathway==pathway)&(df.status==status)]; ax.scatter(d.log2_fold_change,d.minus_log10_p,s=16,alpha=.65,color=color)
        ax.axhline(-np.log10(.05),ls="--",color="#475569"); ax.set_title(pathway); ax.set_xlabel("log2 fold change")
    axes[0].set_ylabel("-log10 adjusted p"); fig.suptitle("One grammar, repeated by pathway"); fig.tight_layout(); fig.savefig(OUT/"05-volcano-faceted.png",dpi=180); plt.close(fig)
pd.DataFrame([{"figure":"05-volcano-grammar.png","purpose":"layer marks and reference rules"},{"figure":"05-volcano-faceted.png","purpose":"apply faceting as a grammar operation"}]).to_csv(ROOT/"results/05-plotnine-figure-manifest.csv",index=False)
print(f"Wrote {len(df)} rows and 2 figures")
