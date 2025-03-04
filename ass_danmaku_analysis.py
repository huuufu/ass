import os
import re
import dash
import numpy as np
import webbrowser
from datetime import datetime
from dash import dcc, html
from scipy.ndimage import gaussian_filter1d

def parse_ass_time_to_seconds(time_str):
    parts = time_str.strip().split(":")
    if len(parts) != 3:
        return 0.0
    try:
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    except:
        return 0.0

def tsec(s):
    h = int(s) // 3600
    m = (int(s) % 3600) // 60
    ss = int(s) % 60
    return f"{h:02d}:{m:02d}:{ss:02d}"

def read_ass_files():
    times, texts = [], []
    pattern = re.compile(r'^(\d{6})\.ass$')
    all_files = []
    for filename in os.listdir('.'):
        if pattern.match(filename):
            prefix = filename[:6]
            try:
                dt = datetime.strptime(prefix, '%H%M%S')
                st_sec = dt.hour * 3600 + dt.minute * 60 + dt.second
                if st_sec < 72000:
                    st_sec += 86400
                all_files.append((filename, st_sec))
            except:
                continue
    all_files.sort(key=lambda x: x[1])
    for filename, offset_sec in all_files:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            for line in f:
                if not line.startswith('Dialogue:'):
                    continue
                parts = line.split(',', 9)
                if len(parts) < 10:
                    continue
                time = parse_ass_time_to_seconds(parts[1])
                text = parts[9].strip()
                if '}' in text:
                    text = text.split('}')[-1].strip()
                times.append(time + offset_sec)
                texts.append(text)
    return np.array(times), np.array(texts)

def build_figure(times, texts):
    idx = np.argsort(times)
    times = times[idx]
    texts = texts[idx]
    density = np.zeros(len(times))
    for i, t in enumerate(times):
        mask = (times >= t - 15) & (times <= t + 15)
        density[i] = np.sum(mask)
    density = gaussian_filter1d(density, sigma=2)
    app = dash.Dash(__name__)
    app.layout = html.Div([
        dcc.Graph(
            figure={
                'data': [{
                    'x': times,
                    'y': density,
                    'mode': 'lines',
                    'fill': 'tozeroy'
                }],
                'layout': {
                    'height': 700,
                    'xaxis': {
                        'title': '时间',
                        'tickvals': list(range(0, int(max(times)) + 1, 1800)),
                        'ticktext': [tsec(t) for t in range(0, int(max(times)) + 1, 1800)]
                    },
                    'yaxis': {'title': '弹幕密度'}
                }
            }
        )
    ])
    webbrowser.open('http://127.0.0.1:8050/')
    app.run_server(debug=False)

if __name__ == "__main__":
    times, texts = read_ass_files()
    if len(times) > 0:
        build_figure(times, texts)
    else:
        print("没有找到有效的弹幕文件") 
