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




app = dash.Dash(__name__)



radio = html.Div([

        html.P(
                "Log Scale:",
                style={"font-weight": "bold", "margin-bottom": "0px"},
                className="plot-display-text",
            ),
         html.Div(
        [
            dcc.RadioItems(
                options=[
                    {
                        "label": "On",
                        "value": 'on',
                    },
                    {
                        "label": "Off",
                        "value": 'off',
                    },
                ],
                value='on',
                id=f"radio-log-scale",
                labelStyle={"verticalAlign": "middle"},
                className="plot-display-radio-items",
            )
        ],
        className="radio-item-div",
    )
])



config = {
    "log_scale": False,
}


# drf_dir = "C:/Users/yanag/openradar/openradar_antennas_wb_hf/"
drf_dir = "C:/Users/yanag/openradar/openradar_antennas_wb_uhf/"
# spec_datas = read_digital_rf_data([drf_dir], plot_file=None, plot_type="spectrum", channel="discone",
#         subchan=0, sfreq=0.0, cfreq=None, atime=0, start_sample=0, stop_sample=1000000, modulus=None, integration=1, 
#         zscale=(0, 0), bins=1024, log_scale=True, detrend=False,msl_code_length=0,
#         msl_baud_length=0)

spec_datas = read_digital_rf_data([drf_dir], plot_file=None, plot_type="spectrum", channel="discone",
        subchan=0, sfreq=0.0, cfreq=None, atime=0, start_sample=0, stop_sample=1000000, modulus=10000, integration=1, 
        zscale=(0, 0), bins=1024, log_scale=True, detrend=False,msl_code_length=0,
        msl_baud_length=0)

specgram_datas = read_digital_rf_data([drf_dir], plot_file=None, plot_type="spectrum", channel="discone",
        subchan=0, sfreq=0.0, cfreq=None, atime=0, start_sample=0, stop_sample=1000000, modulus=10000, integration=1, 
        zscale=(0, 0), bins=1024, log_scale=True, detrend=False,msl_code_length=0,
        msl_baud_length=0)

spec_data = spec_datas[0]
print(f"sfreq: {spec_data['sfreq']}")

sa = SpectrumAnalyzer(number_samples=spec_data['data'].shape[0], sample_frequency=spec_data['sfreq'])

sa.centre_frequency = spec_data['cfreq']
print(f'center freq: {sa.spec.centre_frequency}')
print(f"setting data: { spec_data['data'] }")

sa.spec.data = spec_data['data']
sa.spectrogram.data = spec_data['data']
print(f"max data: {max(spec_data['data'])}")
print(f'data: {sa.spec.data}')

print(sa.spec)


app.layout = html.Div(children=[
    html.H1(children='Digital RF Dashboard'),
    html.Button('Reset', id='reset-val', n_clicks=0),
    html.Button('Play', id='play-val', n_clicks=0),
    radio,
    dcc.Graph(
        id='spectrum-graph',
        figure=sa.plot
    ),
    dcc.Interval(
            id='interval-component',
            interval=1*100, # in milliseconds
            n_intervals=0,
            max_intervals=len(spec_datas),
            disabled=True,
        ),
    dcc.Graph(
        id='specgram-graph',
        figure=sa.spectrogram.get_plot()
    ),
    
])



@app.callback(
    dash.Output('interval-component', 'n_intervals'),
    dash.Input('reset-val', 'n_clicks'),
    dash.Input('play-val', 'n_clicks'),
)
def update_interval(reset_clicks, play_clicks):
    return 0

@app.callback(dash.Output('specgram-graph', 'figure'),
              dash.Input('interval-component', 'n_intervals'))
def update_spec_metrics(n):
    print('data boop')
    if n < len(spec_datas):
        d = spec_datas[n]['data']
        sa.spectrogram.data = d

        zscale_low = np.median(d.min())
        zscale_high = np.median(d.max())
        sa.spectrogram.zmin = zscale_low
        sa.spectrogram.zmax = zscale_high
    return sa.spectrogram.get_plot()



@app.callback(dash.Output('spectrum-graph', 'figure'),
              dash.Input('interval-component', 'n_intervals'),
              dash.Input("radio-log-scale", "value"))
def update_spectrum_graph(n, log_scale):
    ctx = dash.callback_context
    if not ctx.triggered:
        return sa.plot

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if prop_id == "interval-component":
        if n < len(spec_datas):
            sa.spec.data        = spec_datas[n]['data']
            sa.spectrogram.data = spec_datas[n]['data']

    else:
        if log_scale == 'on':
            sa.spec.log_scale = True
        else:
            sa.spec.log_scale = False
    return sa.plot



if __name__ == '__main__':
    app.run_server(debug=True)