from pathlib import Path
import numpy as np
import pandas as pd
import json
try:
    import plotly.express as px
    HAVE_PLOTLY = True
except ImportError:
    import matplotlib.pyplot as plt
    HAVE_PLOTLY = False

ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/"data/processed/06-longitudinal-biomarkers.csv"; OUT=ROOT/"results/figures"
DATA.parent.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True); rng=np.random.default_rng(606)
rows=[]
for cohort,offset in [("Control",0),("Treatment",1.1)]:
 for subject in range(1,13):
  for week in range(0,13,2): rows.append((f"{cohort[0]}{subject:02d}",cohort,week,round(5+offset+.18*week+rng.normal(0,.55),2)))
df=pd.DataFrame(rows,columns=["subject","cohort","week","biomarker"]); df.to_csv(DATA,index=False)
summary=df.groupby(["cohort","week"],as_index=False).biomarker.agg(mean="mean",sd="std")
colors={"Control":"#64748B","Treatment":"#DC2626"}
if HAVE_PLOTLY:
    fig=px.line(df,x="week",y="biomarker",color="cohort",line_group="subject",markers=True,hover_data=["subject"],title="Longitudinal biomarker trajectories",color_discrete_map=colors); fig.update_layout(template="plotly_white",xaxis_title="Study week",yaxis_title="Biomarker level"); fig.write_html(OUT/"06-biomarker-trajectories.html",include_plotlyjs="cdn"); fig.write_image(OUT/"06-biomarker-trajectories.png",scale=2)
    fig2=px.line(summary,x="week",y="mean",color="cohort",markers=True,error_y="sd",title="Cohort means with standard-deviation bars",color_discrete_map=colors); fig2.update_layout(template="plotly_white",xaxis_title="Study week",yaxis_title="Mean biomarker"); fig2.write_html(OUT/"06-biomarker-summary.html",include_plotlyjs="cdn"); fig2.write_image(OUT/"06-biomarker-summary.png",scale=2)
else:
    def write_html(path,traces,title,ytitle):
        spec=json.dumps(traces); path.write_text(f'<!doctype html><meta charset="utf-8"><script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script><div id="chart"></div><script>Plotly.newPlot("chart",{spec},{{title:{json.dumps(title)},template:"plotly_white",xaxis:{{title:"Study week"}},yaxis:{{title:{json.dumps(ytitle)}}}}},{{responsive:true}});</script>')
    traces=[]
    for (cohort,subject),d in df.groupby(["cohort","subject"]): traces.append({"x":d.week.tolist(),"y":d.biomarker.tolist(),"customdata":[subject]*len(d),"name":cohort,"legendgroup":cohort,"showlegend":subject.endswith("01"),"mode":"lines+markers","line":{"color":colors[cohort]},"hovertemplate":"Subject: %{customdata}<br>Week: %{x}<br>Biomarker: %{y:.2f}<extra></extra>"})
    write_html(OUT/"06-biomarker-trajectories.html",traces,"Longitudinal biomarker trajectories","Biomarker level")
    traces2=[]
    for cohort,d in summary.groupby("cohort"): traces2.append({"x":d.week.tolist(),"y":d['mean'].round(3).tolist(),"error_y":{"type":"data","array":d.sd.round(3).tolist(),"visible":True},"name":cohort,"mode":"lines+markers","line":{"color":colors[cohort]}})
    write_html(OUT/"06-biomarker-summary.html",traces2,"Cohort means with standard-deviation bars","Mean biomarker")
    fig,ax=plt.subplots(figsize=(9,5.2))
    for (cohort,subject),d in df.groupby(["cohort","subject"]): ax.plot(d.week,d.biomarker,marker='o',ms=3,alpha=.45,color=colors[cohort])
    ax.set(title="Longitudinal biomarker trajectories",xlabel="Study week",ylabel="Biomarker level"); fig.tight_layout(); fig.savefig(OUT/"06-biomarker-trajectories.png",dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5.2))
    for cohort,d in summary.groupby("cohort"): ax.errorbar(d.week,d['mean'],yerr=d.sd,marker='o',capsize=3,label=cohort,color=colors[cohort])
    ax.set(title="Cohort means with standard-deviation bars",xlabel="Study week",ylabel="Mean biomarker"); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(OUT/"06-biomarker-summary.png",dpi=180); plt.close(fig)
pd.DataFrame([{"figure":"06-biomarker-trajectories.html","fallback":"06-biomarker-trajectories.png"},{"figure":"06-biomarker-summary.html","fallback":"06-biomarker-summary.png"}]).to_csv(ROOT/"results/06-plotly-figure-manifest.csv",index=False)
print(f"Wrote {len(df)} rows, 2 HTML charts, and 2 PNG fallbacks")
