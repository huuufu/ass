import os
import re
import dash
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from dash import dcc, html
from dash.dependencies import Input, Output
from scipy.ndimage import gaussian_filter1d

def tsec(s):
    m=int(s)//60
    ss=int(s)%60
    h=m//60
    m=m%60
    return f"{h:02d}:{m:02d}:{ss:02d}"

def build_figure(x):
    idx=np.argsort(x[0])
    times=np.array(x[0])[idx]
    txts=np.array(x[1])[idx]
    d=np.zeros(len(times))
    hovers=[]
    for i,v in enumerate(times):
        mask=(times>=v-15)&(times<=v+15)
        d[i]=np.sum(mask)
        seg=txts[mask]
        hovers.append("<br>".join(seg[:50]))
    d=gaussian_filter1d(d,sigma=2)
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=times,y=d,mode="lines",fill="tozeroy",hoverinfo="text",text=[tsec(tt)+"<br>"+hovers[j]for j,tt in enumerate(times)]))
    fig.update_layout(hovermode="x",height=700,yaxis_title="弹幕密度")
    if len(times)>0:
        mx=int(times[-1])+1800
        tickvals=list(range(0,mx,1800))
        fig.update_xaxes(tickvals=tickvals,ticktext=[tsec(a)for a in tickvals])
    return fig

def parse_ass(a):
    import re
    r=[]
    with open(a,"r",encoding="utf-8-sig")as f:
        for line in f:
            if line.startswith("Dialogue:"):
                p=line.split(",")
                if len(p)<10:continue
                c=datetime.strptime(p[1],"%H:%M:%S.%f")
                txt=",".join(p[9:])
                txt=re.sub(r"\{.*?\}","",txt)
                r.append((c.hour*3600+c.minute*60+c.second+c.microsecond/1e6,txt))
    return [list(x)for x in zip(*r)] if r else[[],[]]

l=[i for i in os.listdir(".") if re.match(r"^\d{8}\.ass$",i)]
l.sort()
app=dash.Dash(__name__)
app.layout=html.Div([
    dcc.Dropdown(id="dd",options=[{"label":x,"value":x}for x in l],value=l[-1] if l else None),
    dcc.Graph(id="gr")
])

@app.callback(Output("gr","figure"),[Input("dd","value")])
def cb(v):
    if not v:return go.Figure()
    d=parse_ass(v)
    if not d[0]:return go.Figure()
    return build_figure(d)

if __name__=="__main__":
    app.run_server(debug=False)
