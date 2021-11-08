# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import numpy as np

from spectrum_analyzer import SpectrumAnalyzer
from digital_rf_utils import read_digital_rf_data
from receiver_frontend import * 



# def spectrum_playback(sa, spec_datas):
#     for spec_data in spec_datas:
#         print('data boop')
#         sa.spec.data = spec_data['data']
#         print(spec_data['data'])
#         return
#         time.sleep(0.1)



app = dash.Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

drf_dir = "C:/Users/yanag/openradar/openradar_antennas_wb_hf/"
# drf_dir = "C:/Users/yanag/openradar/openradar_antennas_wb_uhf/"
# spec_datas = read_digital_rf_data([drf_dir], plot_file=None, plot_type="spectrum", channel="discone",
#         subchan=0, sfreq=0.0, cfreq=None, atime=0, start_sample=0, stop_sample=1000000, modulus=None, integration=1, 
#         zscale=(0, 0), bins=1024, log_scale=True, detrend=False,msl_code_length=0,
#         msl_baud_length=0)

spec_datas = read_digital_rf_data([drf_dir], plot_file=None, plot_type="spectrum", channel="discone",
        subchan=0, sfreq=0.0, cfreq=None, atime=0, start_sample=0, stop_sample=1000000, modulus=10000, integration=1, 
        zscale=(0, 0), bins=1024, log_scale=True, detrend=False,msl_code_length=0,
        msl_baud_length=0)

spec_data = spec_datas[0]
print(f"sfreq: {spec_data['sfreq']}")

sa = SpectrumAnalyzer(number_samples=spec_data['data'].shape[0], sample_frequency=spec_data['sfreq'])

sa.spec.centre_frequency = spec_data['cfreq']
print(f'center freq: {sa.spec.centre_frequency}')
print(f"setting data: { spec_data['data'] }")

sa.spec.data = spec_data['data']
print(f"max data: {max(spec_data['data'])}")
print(f'data: {sa.spec.data}')

print(sa.spec)

# gui = RadioAnalyserGUI(None,
#                  None,
#                  None,
#                  sa,
#                  None)

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for your data.
    '''),
    html.Button('Reset', id='submit-val', n_clicks=0),
    dcc.Graph(
        id='spectrum-graph',
        figure=sa.plot
    ),
    dcc.Interval(
            id='interval-component',
            interval=1*100, # in milliseconds
            n_intervals=0,
            max_intervals=len(spec_datas)
        )
])



@app.callback(
    dash.Output('interval-component', 'n_intervals'),
    dash.Input('submit-val', 'n_clicks'),
)
def update_output(n_clicks):
    return 0

@app.callback(dash.Output('spectrum-graph', 'figure'),
              dash.Input('interval-component', 'n_intervals'))
def update_metrics(n):
    print('data boop')
    if n < len(spec_datas):
        sa.spec.data = spec_datas[n]['data']
    return sa.plot


if __name__ == '__main__':
    app.run_server(debug=True)