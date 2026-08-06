from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/"data/processed/04-cell-markers.csv"; OUT=ROOT/"results/figures"
DATA.parent.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True); rng=np.random.default_rng(404)
types=["T cell","B cell","Monocyte"]; markers=["CD3D","MS4A1","LYZ","MKI67"]
base={"T cell":[7.8,2.4,2.8,3.2],"B cell":[2.5,8.1,2.6,3.0],"Monocyte":[2.1,2.0,8.5,3.5]}
rows=[]
for ct in types:
 for sample in range(1,41):
  vals=rng.normal(base[ct],.75)
  rows.append((ct,sample,*np.round(vals,2)))
df=pd.DataFrame(rows,columns=["cell_type","cell_id",*markers]); df.to_csv(DATA,index=False)
sns.set_theme(style="whitegrid",context="notebook")
long=df.melt(id_vars=["cell_type","cell_id"],value_vars=markers,var_name="marker",value_name="expression")
g=sns.catplot(data=long,x="marker",y="expression",hue="cell_type",kind="violin",inner="quart",cut=0,height=5,aspect=1.7,palette="colorblind")
g.set_axis_labels("Marker","Normalized expression"); g.figure.suptitle("Marker distributions by annotated cell type",y=1.03); g.savefig(OUT/"04-marker-distributions.png",dpi=180,bbox_inches="tight"); plt.close(g.figure)
corr=df[markers].corr(); fig,ax=plt.subplots(figsize=(6.4,5.2)); sns.heatmap(corr,annot=True,cmap="vlag",center=0,vmin=-1,vmax=1,square=True,ax=ax); ax.set_title("Marker-expression correlations"); fig.tight_layout(); fig.savefig(OUT/"04-marker-correlation.png",dpi=180); plt.close(fig)
pd.DataFrame([{"figure":"04-marker-distributions.png","purpose":"compare conditional distributions"},{"figure":"04-marker-correlation.png","purpose":"inspect multivariate association"}]).to_csv(ROOT/"results/04-seaborn-figure-manifest.csv",index=False)
print(f"Wrote {len(df)} rows and 2 figures")
