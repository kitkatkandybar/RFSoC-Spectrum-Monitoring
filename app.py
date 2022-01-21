"""
This file represents the core interface of the web application -
running it starts the web app.

It also defines the layout and functionality of the app.

"""

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import re
import time

import dash
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd
import numpy as np
import redis
import json


import dash_bootstrap_components as dbc

from spectrum_analyzer import SpectrumAnalyzer
from digital_rf_utils import *





# create a Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY], suppress_callback_exceptions=True)

redis_instance = redis.Redis(host='localhost', port=6379, db=0)
pubsub = redis_instance.pubsub(ignore_subscribe_messages=True)




# create radio option components
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
                        {'label': 'Log Scale', 'value': 'on'},
                        {'label': 'Linear Scale', 'value': 'off'}
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


# specify some global data needed for various parts of the dashboard
# TODO: Make these into non-global variables
spec_datas = None
data_queue = None
data_q_idx = 0
# metadata   = None
y_max      = None
y_min      = None
r_data     = None
last_r_id  = None
req_id     = None
sa         = SpectrumAnalyzer()


# specify the main layout of the application
app.layout = dbc.Container([
    dbc.Row(
        [
        dbc.Col(
            [
                html.H1(children='Spectrum Monitoring Dashboard'),
            ],
            width=True,
        ),
    ]),
    html.Hr(),
    dbc.Row([
        dbc.Col([
                dcc.Input(
                    id="drf-path", 
                    type="text",
                    value="C:/Users/yanag/openradar/openradar_antennas_wb_hf/",
                    style={'width': '100%'}
                ),
                dbc.Button(
                    'Choose input directory', 
                    id='input-dir-val', 
                    n_clicks=0,
                    color="primary",
                ),
                dbc.Button(
                    'redis', 
                    id='redis-button', 
                    n_clicks=0,
                    color="primary",
                ),
                html.Br(),
                html.Div(id='drf-err'),
                html.Div(id='channel-div', style={'width': '100%'}),
                html.Div(id='sample-div', style={'width': '100%'},),
                        
                html.Div(id='bins-div', style={'width': '100%'},),
                html.Div(id='metadata-output'),
                dbc.Button(
                    'Load Data', 
                    id='load-val', 
                    n_clicks=0, 
                    disabled=True,
                    color="primary",
                ),
                dbc.Button(
                    'Playback data from beginning', 
                    id='reset-val',
                    n_clicks=0,
                    disabled=True,
                    color="secondary",
                ),
                radio,
        ], width=3),
        dbc.Col([
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
                            max_intervals=100,
                            disabled=True,
                        ),
                    dcc.Graph(
                        id='specgram-graph',
                        figure=sa.spectrogram.get_plot()
                    ),
                    html.P(id='placeholder', n_clicks=0)

                ],
            ),
            dcc.Interval(
                    id='redis-interval',
                    interval=100, # in milliseconds
                    n_intervals=0,
                    max_intervals=1000,
                    disabled=True,
                ),
        ], width=True,),
    ]),

], fluid=True)


def drf_responses_handler(msg):
    print(f"got response message: {msg}")
    channel = msg['channel'].decode()
    if 'channels' in channel:
        drf_channels = json.loads(msg['data'])
        print(f'got channels from redis: {drf_channels}')



@app.callback(
    dash.Output(component_id='channel-div', component_property='children'),
    dash.Input('redis-button', 'n_clicks'),
    dash.State('drf-path', 'value'),
)
def start_redis_stream(n, drf_path):
    # if (n % 2) == 1:
    if n == 1:
        print("clicked redis button")
        global req_id
        req_id = redis_instance.get('request-id').decode()
        next_req_id = int(req_id) + 1
        redis_instance.set('request-id', next_req_id)

        # pubsub.psubscribe(**{f'responses:{req_id}:*': drf_responses_handler})
        pubsub.psubscribe(f'responses:{req_id}:*')

        print(f"publishing request for {drf_path}")
        # make a request for the channels from drf_path
        redis_instance.publish(f'requests:{req_id}:channels', drf_path)

        # thread = pubsub.run_in_thread(sleep_time=0.01)
        for msg in pubsub.listen():
            print(f"got response message: {msg}")
            channel = msg['channel'].decode()
            if 'channels' in channel:
                drf_channels = json.loads(msg['data'])
                print(f'got channels from redis: {drf_channels}')

                picker_options = [
                    {'label': chan, 'value': chan} for chan in drf_channels
                ]

                children = [
                    html.H4("Choose the channel:"),
                    dcc.Dropdown(
                        options=picker_options,
                        value=drf_channels[0],
                        id={
                            'type': 'channel-picker', 'index': 0, 

                        }
                    ),
                 ]

                return children
                break


        # time.sleep(5)

        # thread.stop()
        # redis_instance.rpush('channel-requests', json.dumps({'req_id': req_id, 'drf_path': drf_path}))

        global redis_data
        # for drf files, we want to push all data we haven't into a queue which gets outputted
        redis_data = []


        return None

    return None


@app.callback(
    dash.Output(component_id='load-val', component_property='disabled'),
    dash.Input('redis-button', 'n_clicks'),
)
def redis_update_load_data_button(n):
    if n < 1: return True

    return False



@app.callback(
    dash.Output('interval-component', 'disabled'),
    dash.Output('interval-component', 'max_intervals'),
    dash.Output('drf-err', 'children'),
    dash.Output('redis-interval', 'disabled'),
    dash.Input('load-val', 'n_clicks'),
    dash.State('drf-path', 'value'),
    dash.State({'type': 'channel-picker', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'range-slider', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'bins-slider', 'index': dash.ALL,}, 'value'),
)
def send_redis_request_data(n_clicks, drf_path, channel, sample_range, bins):
    if n_clicks < 1:
         return True, 0, None, True
    req = {
        'drf_path'     : drf_path,
        'channel'      : channel[0],
        'start_sample' : sample_range[0][0],
        'stop_sample'  : sample_range[0][1],
        'bins'         : 2**bins[0]

    }

    redis_instance.publish(f'requests:{req_id}:data', json.dumps(req))

    for msg in pubsub.listen():
        print(f"got response message: {msg}")
        channel = msg['channel'].decode()
        if 'metadata' in channel:
            metadata = json.loads(msg['data'])
            print(f'got metadata from redis: {metadata}')

            global spec_datas
            spec_datas = {}
            spec_datas['metadata'] = metadata

            sa.spectrogram.clear_data()

            global y_min
            global y_max
            y_max = spec_datas['metadata']['y_max']
            y_min = spec_datas['metadata']['y_min']

            sfreq     = metadata['sfreq']
            n_samples = metadata['n_samples']

            # set axes and other basic info for plots
            sa.spec.yrange      = (y_min, y_max)
            sa.spectrogram.zmin = y_min
            sa.spectrogram.zmax = y_max

            sa.centre_frequency = spec_datas['metadata']['cfreq']


            sa.spec.sample_frequency        = sfreq
            sa.spectrogram.sample_frequency = sfreq
            sa.spec.number_samples          = n_samples
            sa.spectrogram.number_samples   = n_samples
            sa.spec.show_data()

            global data_queue
            data_queue = []
            global data_q_idx
            data_q_idx = 0
            return False, 100, None, False


    return True, 0, None, True



@app.callback(dash.Output('placeholder', 'n_clicks'),
              dash.Input('redis-interval', 'n_intervals'))
def read_redis_stream(n_intervals):
    if n_intervals == 0: return None

    streamname = 'example'
    print("reading redis stream!")
    # rstrm = redis_instance.xread({streamname: '$'}, None, 0)
    global last_r_id
    global data_queue
    print(f'last_r_id: {last_r_id}')
    if last_r_id is None:
        # rstrm = redis_instance.xrevrange(f'responses:{req_id}:stream', count=1)
        rstrm = redis_instance.xrange(f'responses:{req_id}:stream')
        if (len(rstrm) == 0):
            print("no update")
            return dash.no_update
        print(f'rstrm: {rstrm}')
        print(f'foo {rstrm[0][0]}')
        last_r_id = rstrm[-1][0].decode()
        print(f'last_r_id: {last_r_id}')

    else:
        rstrm = redis_instance.xrevrange(f'responses:{req_id}:stream', min=f'({last_r_id}')
        if (len(rstrm) == 0):
            print("no update")
            return dash.no_update
        last_r_id = rstrm[-1][0].decode()


    print(f"data is: {len(rstrm)}")
    # xlist = json.loads(rstrm[0][1][0][1][b'data'])
    xlist = json.loads(rstrm[0][1][b'data'])
    print(f"data is: {len(xlist)}")

    global r_data
    r_data = xlist
    data_queue.extend([json.loads(d[1][b'data']) for d in rstrm])
    
    # sa.spec.data = xlist
    # sa.spectrogram.data = xlist


    return None


# @app.callback(
#     dash.Output('interval-component', 'max_intervals'),
#     dash.Output('drf-err', 'children'),
#     dash.Input('load-val', 'n_clicks'),
#     dash.State('drf-path', 'value'),
#     dash.State({'type': 'channel-picker', 'index': dash.ALL,}, 'value'),
#     dash.State({'type': 'range-slider', 'index': dash.ALL,}, 'value'),
#     dash.State({'type': 'bins-slider', 'index': dash.ALL,}, 'value'),
# )
# def update_drf_data(n_clicks, drf_path, channel, sample_range, bins):
#     """
#     Load metadata for Digital RF file when "load data" button is clicked,
#     update the "max intervals" component with the length of the data, 
#     or alternatively output an an error message if the specified path
#     does not contain Digital RF data
#     """
#     global spec_datas

#     # clear spectrogram plot when reset is clicked
#     print(f"called update drf data, n: {n_clicks}, chan: {channel}, samp range: {sample_range}")
#     if n_clicks < 1:
#         return 100, None

#     try:
#         spec_datas = read_digital_rf_data([drf_path], plot_file=None, plot_type="spectrum", channel=channel[0],
#             subchan=0, sfreq=0.0, cfreq=None, atime=0, start_sample=sample_range[0][0], stop_sample=sample_range[0][1], modulus=10000, integration=1, 
#             zscale=(0, 0), bins=2**bins[0], log_scale=False, detrend=False,msl_code_length=0,
#             msl_baud_length=0)


#     except Exception as e:
#         # output error message
#         print(e)
#         return dash.no_update, str(e)


#     # get metadata from redis
#     # print("reading redis stream?")
#     # rstrm = redis_instance.xread({streamname: '$'}, None, 0)
#     # print("foo")
#     # xlist = json.loads(rstrm[0][1][0][1][b'data'])
#     # print(f"data is: {xlist}")



#     # set metadata for plots
#     sa.spectrogram.clear_data()

#     spec_data  = spec_datas['data'][0]
#     sfreq      = spec_datas['metadata']['sfreq']
#     n_samples  = spec_data['data'].shape[0]

#     global y_min
#     global y_max
#     y_max = max([max(d['data']) for d in spec_datas['data']])
#     y_min = min([min(d['data']) for d in spec_datas['data']])

#     # set axes and other basic info for plots
#     sa.spec.yrange      = (y_min, y_max)
#     sa.spectrogram.zmin = y_min
#     sa.spectrogram.zmax = y_max

#     sa.centre_frequency = spec_datas['metadata']['cfreq']


#     sa.spec.sample_frequency        = sfreq
#     sa.spectrogram.sample_frequency = sfreq
#     sa.spec.number_samples          = n_samples
#     sa.spectrogram.number_samples   = n_samples


#     return len(spec_datas['data']), None

# @app.callback(
#     dash.Output(component_id='load-val', component_property='disabled'),
#     dash.Input('input-dir-val', 'n_clicks'),
# )
# def update_load_data_button(n):
#     if n < 1: return True

#     return False



@app.callback(
    dash.Output(component_id='sample-div', component_property='children'),
    dash.Input('redis-button', 'n_clicks'),
)
def update_sample_slider(n):
    if n < 1: return None

    sample_min  = 0
    sample_max  = 1000001
    sample_step = 10000

    sample_start_default = 300000
    sample_stop_default  = 700000
    sample_mark_width    = 200000

    children = [
        html.H4('Select the sample range:'),
        dcc.RangeSlider(
            id={
                'type': 'range-slider', 'index': 0, 

            },
            min=sample_min,
            max=sample_max,
            step=sample_step,
            value=[sample_start_default, sample_stop_default],
            marks={i: '{}k'.format(int(i/1000)) for i in range(sample_min, sample_max, sample_mark_width)},

        )

    ]
    return children

@app.callback(
    dash.Output(component_id='bins-div', component_property='children'),
    dash.Input('redis-button', 'n_clicks'),
)
def update_bins_slider(n):
    if n < 1: return None

    sample_min  = 0
    sample_max  = 1000000
    sample_step = 10000

    sample_start_default = 300000
    sample_stop_default  = 700000
    sample_mark_width    = 100000

    children = [
        html.H4(children='Select the number of bins:'),
        dcc.Slider(
            id={
                'type': 'bins-slider', 'index': 0, 

            },
            min = 8,
            max = 10,
            step = None,
            value= 10,
            marks= {i: '{}'.format(2 ** i) for i in range(8, 11)},
            included=False,


        )
    ]
    return children


@app.callback(
    dash.Output(component_id='metadata-output', component_property='children'),
    dash.Output(component_id='reset-val', component_property='disabled'),
    dash.Input('interval-component', 'max_intervals'),
)
def update_metadeta_output(n):
    """
    update metadata section when new Digital RF data is loaded
    The 'max-intervals' value gets updated when metadata is loaded
    """
    if spec_datas is None:
        return None, True

    children = [
        html.H4("Metadata:"),
        html.P(f"Sample Rate: {spec_datas['metadata']['sfreq']} samples/second"),
        html.P(f"Center Frequency: {spec_datas['metadata']['cfreq']} Hz"),
        html.P(f"Channel: {spec_datas['metadata']['channel']}"),

    ]
    # return children, False
    return children, True





# @app.callback(
#     dash.Output('interval-component', 'disabled'),
#     dash.Input('reset-val', 'n_clicks'),
#     dash.State("radio-log-scale", "value")
# )
# def update_interval(reset_clicks, log_scale):
#     """
#     Enable playback of digital RF file when reset is clicked

#     """
#     # clear spectrogram plot when reset is clicked
#     sa.spectrogram.clear_data()

#     # handle the log scales
#     if log_scale == 'on':
#         sa.spec.ylabel          = "Power Spectrum (dB)" 
#         sa.spec.yrange= (10.0 * np.log10(y_min + 1e-12) - 3, 10.0 * np.log10(y_max + 1e-12) + 10)
#         sa.spectrogram.zlabel   =  "Power (dB)"
#         sa.spectrogram.zmin     = 10.0 * np.log10(y_min + 1e-12) - 3
#         sa.spectrogram.zmax     = 10.0 * np.log10(y_max + 1e-12) + 10
        
#     else:
#         sa.spec.ylabel        = "Power Spectrum" 
#         sa.spec.yrange        = (y_min, y_max)
#         sa.spectrogram.zlabel = "Power"
#         sa.spectrogram.zmin   = y_min
#         sa.spectrogram.zmax   = y_max


#     if reset_clicks > 0:
#         return False

#     # playback should be disabled before reset button is clicked
#     return True

@app.callback(
    dash.Output('interval-component', 'n_intervals'),
    dash.Input('interval-component', 'disabled'),
)
def disabled_update(disabled):
    """ reset data back to beginning every time "reset" button gets pressed """

    if not disabled:
        # make sure data isn't hidden if playback is going on
        sa.spec.show_data()

    return 0



@app.callback(dash.Output('spectrum-graph', 'figure'),
              dash.Input('interval-component', 'n_intervals'),
              dash.State('placeholder', 'n_clicks'),
              dash.Input("radio-log-scale", "value"))
def update_spectrum_graph(n, placeholder, log_scale):
    """ update the spectrum graph with new data, every time
    the Interval component fires"""

    ctx = dash.callback_context
    if not ctx.triggered or not spec_datas:
        return sa.plot

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if prop_id == "interval-component": # intervale component has fired
        global data_q_idx

        print("updating spectrum graph using redis data")
        if data_q_idx < len(data_queue):
            d = np.asarray(data_queue[data_q_idx])
            if log_scale == 'on':
                d = 10.0 * np.log10(d + 1e-12)
            print(f"redis data is : {d}")
            sa.spec.data        = d
            data_q_idx += 1
            return sa.plot
        else:
            return dash.no_update



        # if n < len(spec_datas['data']):
        #     print(f"data {n}")
        #     d = spec_datas['data'][n]['data']
        #     if log_scale == 'on':
        #         d = 10.0 * np.log10(d + 1e-12)
            # sa.spec.data        = d

    elif prop_id == "placeholder":
        print("updating spectrum graph using redis data")
        d = np.asarray(r_data)
        if log_scale == 'on':
            d = 10.0 * np.log10(d + 1e-12)
        print(f"redis data is : {d}")
        sa.spec.data        = d

    else:
        # log scale option has been modified
        if log_scale == 'on':
            sa.spec.ylabel = "Amplitude (dB)" 
            sa.spec.yrange = (10.0 * np.log10(y_min + 1e-12) - 3, 10.0 * np.log10(y_max + 1e-12) + 10)
            
        else:
            sa.spec.ylabel = "Amplitude" 
            sa.spec.yrange = (y_min, y_max)

    return sa.plot



@app.callback(dash.Output('specgram-graph', 'figure'),
              dash.Input('interval-component', 'n_intervals'),
              dash.Input('placeholder', 'n_clicks'),

              dash.Input("radio-log-scale", "value"))
def update_specgram_graph(n, placeholder, log_scale):
    """ update the spectogram plot with new data, every time
    the Interval component fires"""

    ctx = dash.callback_context
    if not ctx.triggered or not spec_datas:
        return sa.spectrogram.get_plot()

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if prop_id == "interval-component": # interval component has fired
        global data_q_idx

        print("updating spectrum graph using redis data")
        if data_q_idx < len(data_queue):
            d = np.asarray(data_queue[data_q_idx])
            if log_scale == 'on':
                d = 10.0 * np.log10(d + 1e-12)
                
            sa.spectrogram.data = d
            data_q_idx += 1
        else:
            return dash.no_update

        # if n < len(spec_datas['data']):
        #     d = spec_datas['data'][n]['data']
        #     if log_scale == 'on':
        #         d = 10.0 * np.log10(d + 1e-12)

        #     sa.spectrogram.data = d
    elif prop_id == "placeholder":
        print("updating specgram graph using redis data")
        d = np.asarray(r_data)
        if log_scale == 'on':
            d = 10.0 * np.log10(d + 1e-12)
        sa.spectrogram.data = d

    else:
        if log_scale == 'on': # log scale option has changed
            sa.spectrogram.zlabel =  "Power (dB)"
            sa.spectrogram.zmin   = 10.0 * np.log10(y_min + 1e-12) - 3
            sa.spectrogram.zmax   = 10.0 * np.log10(y_max + 1e-12) + 10
            
        else:
            sa.spectrogram.zlabel = "Power"
            sa.spectrogram.zmin   = y_min
            sa.spectrogram.zmax   = y_max

    return sa.spectrogram.get_plot()





if __name__ == '__main__':
    app.run_server(debug=True)