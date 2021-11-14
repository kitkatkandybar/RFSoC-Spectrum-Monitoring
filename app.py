# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
from dash import dcc
from dash import html
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
                        # "disabled": True,
                    },
                    {
                        "label": "Off",
                        "value": 'off',
                        # "disabled": True,

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


spec_datas = None
y_max      = None
y_min      = None
sa         = SpectrumAnalyzer()



app.layout = html.Div(children=[
    html.H1(children='Spectrum Monitoring Dashboard'),
    dcc.Input(
        id="drf-path", type="text",value="C:/Users/yanag/openradar/openradar_antennas_wb_hf/",
        style={'width': 400}
    ),
    html.Button('Load Data', id='load-val', n_clicks=0),
    html.Br(),
    html.Div(id='drf-err'),
    html.Div(id='metadata-output'),
    html.Button(
        'Playback data from beginning', 
        id='reset-val',
        n_clicks=0,
        disabled=True,
    ),
    radio,

    html.Div(
        className="graph-section",
        children=[
            dcc.Graph(
                id='spectrum-graph',
                figure=sa.plot
            ),
            dcc.Interval(
                    id='interval-component',
                    interval=1*100, # in milliseconds
                    n_intervals=0,
                    # max_intervals=len(spec_datas),
                    max_intervals=100,
                    disabled=True,
                ),
            dcc.Graph(
                id='specgram-graph',
                figure=sa.spectrogram.get_plot()
            ),
            html.P(id='placeholder', n_clicks=0)

        ],
    )

    
])


# 
@app.callback(
    dash.Output('interval-component', 'max_intervals'),
    dash.Output('drf-err', 'children'),
    dash.Input('load-val', 'n_clicks'),
    dash.State('drf-path', 'value'),
)
def update_drf_data(n_clicks, drf_path):
    """
    Load metadata for Digital RF file when "load data" button is clicked
    """
    global spec_datas

    # clear spectrogram plot when reset is clicked
    print(f"called update drf data, n: {n_clicks}")
    if n_clicks < 1:
        return 100, None

    try:
        spec_datas = read_digital_rf_data([drf_path], plot_file=None, plot_type="spectrum", #channel="discone",
            subchan=0, sfreq=0.0, cfreq=None, atime=0, start_sample=0, stop_sample=1000000, modulus=10000, integration=1, 
            zscale=(0, 0), bins=1024, log_scale=False, detrend=False,msl_code_length=0,
            msl_baud_length=0)
    except Exception as e:
        return dash.no_update, str(e)


    # set metadata for plots
    print("loading drf data...")
    sa.spectrogram.clear_data()

    spec_data  = spec_datas['data'][0]
    sfreq      = spec_datas['metadata']['sfreq']
    n_samples  = spec_data['data'].shape[0]

    global y_min
    global y_max
    y_max = max([max(d['data']) for d in spec_datas['data']])
    y_min = min([min(d['data']) for d in spec_datas['data']])

    sa.spec.yrange= (y_min, y_max)
    sa.spectrogram.zmin = y_min
    sa.spectrogram.zmax = y_max
    print(f'yrange: {sa.spec.yrange}')

    sa.centre_frequency = spec_datas['metadata']['cfreq']
    print(f'center freq: {sa.spec.centre_frequency}')



    sa.spec.sample_frequency        = sfreq
    sa.spectrogram.sample_frequency = sfreq
    sa.spec.number_samples          = n_samples
    sa.spectrogram.number_samples   = n_samples


    return len(spec_datas['data']), None


@app.callback(
    dash.Output(component_id='metadata-output', component_property='children'),
    dash.Output(component_id='reset-val', component_property='disabled'),
    dash.Input('interval-component', 'max_intervals'),
)
def update_metadeta_output(n):
    """ update metadata section when Digital RF data is loaded"""
    if spec_datas is None:
        return None, True

    children = [
        html.H4("Metadata:"),
        html.P(f"Sample Rate: {spec_datas['metadata']['sfreq']} samples/second"),
        html.P(f"Center Frequency: {spec_datas['metadata']['cfreq']} Hz"),
        html.P(f"Channel: {spec_datas['metadata']['channel']}"),

    ]
    return children, False





@app.callback(
    dash.Output('interval-component', 'disabled'),
    dash.Input('reset-val', 'n_clicks'),
    dash.State("radio-log-scale", "value")
)
def update_interval(reset_clicks, log_scale):
    # clear spectrogram plot when reset is clicked
    sa.spectrogram.clear_data()

    if log_scale == 'on':
        sa.spec.ylabel          = "Amplitude (dB)" 
        sa.spec.yrange= (10.0 * np.log10(y_min + 1e-12) - 3, 10.0 * np.log10(y_max + 1e-12) + 10)
        sa.spectrogram.zlabel =  "Power (dB)"
        sa.spectrogram.zmin     = 10.0 * np.log10(y_min + 1e-12) - 3
        sa.spectrogram.zmax     = 10.0 * np.log10(y_max + 1e-12) + 10
        
    else:
        sa.spec.ylabel        = "Amplitude" 
        sa.spec.yrange        = (y_min, y_max)
        sa.spectrogram.zlabel = "Power"
        sa.spectrogram.zmin   = y_min
        sa.spectrogram.zmax   = y_max


    if reset_clicks > 0:
        return False
    return True

# reset data back to beginning every time "reset" button gets pressed
@app.callback(
    dash.Output('interval-component', 'n_intervals'),
    dash.Input('interval-component', 'disabled'),
)
def disabled_update(disabled):
    if not disabled:
        # pass
        sa.spec.show_data()
    return 0



@app.callback(dash.Output('spectrum-graph', 'figure'),
              dash.Input('interval-component', 'n_intervals'),
              dash.Input("radio-log-scale", "value"))
def update_spectrum_graph(n, log_scale):
    print("updating spectrum graph...")
    ctx = dash.callback_context
    if not ctx.triggered or not spec_datas:
        return sa.plot

    print(f"int comp: {n}")
    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if prop_id == "interval-component":
        if n < len(spec_datas['data']):
            print(f"data {n}")
            d = spec_datas['data'][n]['data']
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
    if not ctx.triggered or not spec_datas:
        return sa.spectrogram.get_plot()

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if prop_id == "interval-component":
        if n < len(spec_datas['data']):
            d = spec_datas['data'][n]['data']
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