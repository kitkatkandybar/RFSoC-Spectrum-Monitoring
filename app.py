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
                value='off',
                id=f"radio-log-scale",
                labelStyle={"verticalAlign": "middle"},
                className="plot-display-radio-items",
            )
        ],
        className="radio-item-div",
    )
])



def get_data(drf_dir):
    spec_datas = read_digital_rf_data([drf_dir], plot_file=None, plot_type="spectrum", channel="discone",
        subchan=0, sfreq=0.0, cfreq=None, atime=0, start_sample=0, stop_sample=1000000, modulus=10000, integration=1, 
        zscale=(0, 0), bins=1024, log_scale=False, detrend=False,msl_code_length=0,
        msl_baud_length=0)


    spec_data = spec_datas[0]
    print(f"sfreq: {spec_data['sfreq']}")

    sa = SpectrumAnalyzer(number_samples=spec_data['data'].shape[0], sample_frequency=spec_data['sfreq'])
    y_max = max([max(d['data']) for d in spec_datas])
    y_min = min([min(d['data']) for d in spec_datas])
    print(f"range: {y_min}, {y_max}")
    sa.spec.yrange= (y_min, y_max)
    sa.spectrogram.zmin = y_min
    sa.spectrogram.zmax = y_max
    print(f'yrange: {sa.spec.yrange}')

    sa.centre_frequency = spec_data['cfreq']



drf_dir = "C:/Users/yanag/openradar/openradar_antennas_wb_hf/"
# drf_dir = "C:/Users/yanag/openradar/openradar_antennas_wb_uhf/"



spec_datas = read_digital_rf_data([drf_dir], plot_file=None, plot_type="spectrum", channel="discone",
        subchan=0, sfreq=0.0, cfreq=None, atime=0, start_sample=0, stop_sample=1000000, modulus=10000, integration=1, 
        zscale=(0, 0), bins=1024, log_scale=False, detrend=False,msl_code_length=0,
        msl_baud_length=0)


spec_data = spec_datas[0]
print(f"sfreq: {spec_data['sfreq']}")

sa = SpectrumAnalyzer(number_samples=spec_data['data'].shape[0], sample_frequency=spec_data['sfreq'])
y_max = max([max(d['data']) for d in spec_datas])
y_min = min([min(d['data']) for d in spec_datas])
print(f"range: {y_min}, {y_max}")
sa.spec.yrange= (y_min, y_max)
sa.spectrogram.zmin = y_min
sa.spectrogram.zmax = y_max
print(f'yrange: {sa.spec.yrange}')

sa.centre_frequency = spec_data['cfreq']
print(f'center freq: {sa.spec.centre_frequency}')


print(f"yrange: {sa.spec.yrange}")


app.layout = html.Div(children=[
    html.H1(children='Digital RF Dashboard'),
    html.Button('Reset', id='reset-val', n_clicks=0),
    radio,
    # dcc.Input(
    #         id="in",
    #         type="file",
    #         placeholder="input type file"),
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
    # dash.Output('interval-component', 'n_intervals'),
    dash.Output('interval-component', 'disabled'),
    dash.Input('reset-val', 'n_clicks'),
)
def update_interval(reset_clicks):
    if reset_clicks > 0:
        return False
    return True

# reset data back to beginning every time "reset" button gets pressed
@app.callback(
    dash.Output('interval-component', 'n_intervals'),
    dash.Input('interval-component', 'disabled'),
)
def disabled_update(disabled):
    return 0



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
            d = spec_datas[n]['data']
            if log_scale == 'on':
                d = 10.0 * np.log10(d + 1e-12)
            sa.spec.data        = d

    else:
        if log_scale == 'on':
            sa.spec.ylabel          = "Amplitude (dB)" 
            sa.spec.yrange= (10.0 * np.log10(y_min + 1e-12) - 3, 10.0 * np.log10(y_max + 1e-12) + 10)
            
        else:
            sa.spec.ylabel = "Amplitude" 
            sa.spec.yrange         = (y_min, y_max)

    return sa.plot




@app.callback(dash.Output('specgram-graph', 'figure'),
              dash.Input('interval-component', 'n_intervals'),
              dash.Input("radio-log-scale", "value"))
def update_specgram_graph(n, log_scale):
    ctx = dash.callback_context
    if not ctx.triggered:
        return sa.spectrogram.get_plot()

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if prop_id == "interval-component":
        if n < len(spec_datas):
            d = spec_datas[n]['data']
            if log_scale == 'on':
                d = 10.0 * np.log10(d + 1e-12)
            sa.spectrogram.data = d

    else:
        if log_scale == 'on':
            sa.spectrogram.zlabel =  "Power (dB)"
            sa.spectrogram.zmin     = 10.0 * np.log10(y_min + 1e-12) - 3
            sa.spectrogram.zmax     = 10.0 * np.log10(y_max + 1e-12) + 10
            
        else:
            sa.spectrogram.zlabel =  "Power"
            sa.spectrogram.zmin     = y_min
            sa.spectrogram.zmax     = y_max

    return sa.spectrogram.get_plot()





if __name__ == '__main__':
    app.run_server(debug=True)