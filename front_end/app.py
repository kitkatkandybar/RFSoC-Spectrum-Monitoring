"""
This file represents the core interface of the web application -
running it starts the web app.

It also defines the layout and functionality of the app.

"""

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import re
import time
import json

import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import numpy as np
import redis

from spectrum_analyzer import SpectrumAnalyzer



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
y_max      = 0
y_min      = 0
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
                    id='input-dir-button', 
                    n_clicks=0,
                    color="primary",
                ),
                html.Br(),
                html.Div(id='drf-err'),
                dcc.Loading(
                    id="channel-loading",
                    children=[
                        html.Div(id='channel-div', style={'width': '100%'}),
                        
                    ],
                    type="circle",
                ),
                
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
                            id='graph-interval',
                            interval=1*150, # in milliseconds
                            n_intervals=0,
                            # max_intervals=100,
                            disabled=True,
                        ),
                    dcc.Graph(
                        id='specgram-graph',
                        figure=sa.spectrogram.get_plot()
                    ),
                    html.P(id='placeholder', n_clicks=0)

                ],
            ),

        ], width=True,),
    ]),
    html.Div(id='reading-stream-graph-interval-placeholder', n_clicks=0,),
    html.Div(id='spectrum-graph-interval-placeholder', n_clicks=0,),
    html.Div(id='reset-button-graph-interval-placeholder', n_clicks=0,),
    html.Div(id='reset-button-placeholder', n_clicks=0,),
    html.Div(id='graph_data_index', n_clicks=0,),

], fluid=True)


def reset_graph_data():

    global data_q_idx
    data_q_idx = 0



@app.callback(
    dash.Output(component_id='channel-div', component_property='children'),
    dash.Input('input-dir-button', 'n_clicks'),
    dash.State('drf-path', 'value'),

)
def start_redis_stream(n, drf_path):
    # if (n % 2) == 1:
    print("clicked input dir button")
    if n > 0:
        print("clicked redis button")
        global req_id
        req_id = redis_instance.get('request-id').decode()
        print('boop')
        next_req_id = int(req_id) + 1
        redis_instance.set('request-id', next_req_id)

        pubsub.subscribe(f'responses:{req_id}:channels')

        print(f"publishing request {req_id} for {drf_path}")
        # make a request for the channels from drf_path
        redis_instance.publish(f'requests:{req_id}:channels', drf_path)

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

                pubsub.unsubscribe(f'responses:{req_id}:channels')

                return children


    
        global redis_data
        # for drf files, we want to push all data we haven't into a queue which gets outputted
        redis_data = []


        return None

    return None


@app.callback(
    dash.Output(component_id='load-val', component_property='disabled'),
    dash.Input('input-dir-button', 'n_clicks'),
)
def redis_update_load_data_button(n):
    if n < 1: return True

    return False

@app.callback(
    dash.Output(component_id='reset-val', component_property='disabled'),
    dash.Input('load-val', 'n_clicks'),
)
def enable_replay_data_button(n):
    if n < 1: return True

    return False

@app.callback(
    dash.Output('reading-stream-graph-interval-placeholder', 'n_clicks'),
    dash.Input('load-val', 'n_clicks'))
def enable_graph_interval_after_clicking_load(n_clicks):
    if n_clicks < 1:
        return 0

    return 1




@app.callback(
    dash.Output('drf-err', 'children'),
    dash.Input('load-val', 'n_clicks'),
    dash.State('drf-path', 'value'),
    dash.State({'type': 'channel-picker', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'range-slider', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'bins-slider', 'index': dash.ALL,}, 'value'),
)
def send_redis_request_data(n_clicks, drf_path, channel, sample_range, bins):
    if n_clicks < 1:
        return None

    global req_id
    req_id = redis_instance.get('request-id').decode()
    next_req_id = int(req_id) + 1
    redis_instance.set('request-id', next_req_id)

    pubsub.psubscribe(f'responses:{req_id}:*')

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
            break

    last_r_id = None
    finished = False
    while not finished:
        time.sleep(0.1)
        if last_r_id is None:
            rstrm = redis_instance.xrange(f'responses:{req_id}:stream')
        else:
            rstrm = redis_instance.xrange(f'responses:{req_id}:stream', min=f'({last_r_id}')

        if (len(rstrm) == 0):
            print("no update")
            continue
        
        last_r_id = rstrm[-1][0].decode()
        print(f"number of new data: {len(rstrm)}")
        for d in rstrm:
            datum = json.loads(d[1][b'data'])
            if 'status' in datum:
                # stream has finished
                if datum['status'] == 'DONE':
                    # unsubscribe from updates
                    finished = True
                    pubsub.punsubscribe(f'responses:{req_id}:*')
                    print(f"FINISHED READING ALL DATA FROM REQUEST: {req_id}")
                    break
            else:
                data_queue.append(datum)

    stream_len = redis_instance.xlen(f'responses:{req_id}:stream')
    print(f"LENGTH OF STREAM: {stream_len}")

    return None


@app.callback(
    dash.Output(component_id='sample-div', component_property='children'),
    dash.Input('input-dir-button', 'n_clicks'),
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

        ),
      


    ]
    return children



@app.callback(
    dash.Output(component_id='bins-div', component_property='children'),
    dash.Input('input-dir-button', 'n_clicks'),
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
    dash.Input('graph-interval', 'max_intervals'),
)
def update_metadeta_output(n):
    """
    update metadata section when new Digital RF data is loaded
    The 'max-intervals' value gets updated when metadata is loaded
    """
    if spec_datas is None:
        return None

    children = [
        html.H4("Metadata:"),
        html.P(f"Sample Rate: {spec_datas['metadata']['sfreq']} samples/second"),
        html.P(f"Center Frequency: {spec_datas['metadata']['cfreq']} Hz"),
        html.P(f"Channel: {spec_datas['metadata']['channel']}"),

    ]
    return children



@app.callback(
    dash.Output('reset-button-graph-interval-placeholder', 'n_clicks'),
    dash.Input('reset-val', 'n_clicks'),
)
def handle_reset_button(n_clicks):
    if n_clicks < 1:
        return 0

    global data_q_idx
    data_q_idx = 0

    sa.spectrogram.clear_data()

    return 1


@app.callback(
    dash.Output('graph-interval', 'disabled'),
    dash.Input('reading-stream-graph-interval-placeholder', 'n_clicks'),
    dash.Input('spectrum-graph-interval-placeholder', 'n_clicks'),
    dash.Input('reset-button-graph-interval-placeholder', 'n_clicks'),
)
def update_graph_interval(reading_interval, spectrum_interval, reset_button_interval):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if prop_id == "reading-stream-graph-interval-placeholder":
        disabled = not bool(reading_interval)
        if not disabled:
            sa.spec.show_data()

    if prop_id == "spectrum-graph-interval-placeholder":
        disabled = not bool(spectrum_interval)

    if prop_id == 'reset-button-graph-interval-placeholder':
        disabled = not bool(reset_button_interval)

    print(f'Graph interval component is disabled: {disabled}')

    return disabled


@app.callback(
            dash.Output('spectrum-graph-interval-placeholder', 'n_clicks'),
            dash.Output('graph_data_index', 'n_clicks'),
            dash.Input('graph-interval', 'n_intervals'))
def handle_graph_interval(n):
    if n < 1: raise dash.exceptions.PreventUpdate
    global data_q_idx
    print(f"handle_graph_interval: data_q_idx: {data_q_idx}")
    if data_q_idx < len(data_queue):
        print(f"\tboop: data_q_idx: {data_q_idx}")

        data_q_idx += 1
        return dash.no_update, data_q_idx-1
    elif len(data_queue) > 0:
        print("Reached the end of the data queue, disabling graph interval")
        return 0, dash.no_update # disable future updates to graph

    raise dash.exceptions.PreventUpdate

# @app.callback(
#     dash.Output('graph_data_index', 'n_clicks'),
# )
# def handle_graph_update_loop(n):

#     while data_q_idx < len(data_queue):
#         data_q_idx += 1

#         return data_q_idx-1

#         time.sleep(0.1)


@app.callback(dash.Output('spectrum-graph', 'figure'),
              dash.Input('graph_data_index', 'n_clicks'),
              dash.Input("radio-log-scale", "value"))
def update_spectrum_graph(n, log_scale):
    """ update the spectrum graph with new data, every time
    the Interval component fires"""

    ctx = dash.callback_context
    if not ctx.triggered: # or not spec_datas:
        return sa.plot

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print("called update spectrum graph")
    if prop_id == "graph_data_index": # interval component has fired
        if n == 0:
            if log_scale == 'on':
                sa.spec.ylabel = "Amplitude (dB)" 
                sa.spec.yrange = (10.0 * np.log10(y_min + 1e-12) - 3, 10.0 * np.log10(y_max + 1e-12) + 10)
                sa.spec.data   =  10.0 * np.log10(sa.spec.data + 1e-12)  
                
            else:
                sa.spec.ylabel = "Amplitude" 
                sa.spec.yrange = (y_min, y_max)
                
        if n < len(data_queue):
            d = np.asarray(data_queue[n])
            if log_scale == 'on':
                d = 10.0 * np.log10(d + 1e-12)
            sa.spec.data        = d
            return sa.plot
        else:
            print(f"update_spectrum_graph: gone past the length of the data queue? data_queue len: {len(data_queue)}, idx: {n}")
            raise dash.exceptions.PreventUpdate


    else:
        # log scale option has been modified
        print("modifying log scale")
        if log_scale == 'on':
            sa.spec.ylabel = "Amplitude (dB)" 
            sa.spec.yrange = (10.0 * np.log10(y_min + 1e-12) - 3, 10.0 * np.log10(y_max + 1e-12) + 10)
            sa.spec.data   =  10.0 * np.log10(sa.spec.data + 1e-12)  
            
        else:
            sa.spec.ylabel = "Amplitude" 
            sa.spec.yrange = (y_min, y_max)

    return sa.plot




@app.callback(dash.Output('specgram-graph', 'figure'),
              dash.Input('graph_data_index', 'n_clicks'),
              dash.Input("radio-log-scale", "value"))
def update_specgram_graph(n, log_scale):
    """ update the spectogram plot with new data, every time
    the Interval component fires"""
    ctx = dash.callback_context
    if not ctx.triggered or not spec_datas:
        return sa.spectrogram.get_plot()

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if prop_id == "graph_data_index": # interval component has fired
        print(f"update_specgram_graph: data_queue len: {len(data_queue)}, idx: {n}")

        if n == 0:
            if log_scale == 'on': # log scale option has changed
                sa.spectrogram.zlabel =  "Power (dB)"
                sa.spectrogram.zmin   = 10.0 * np.log10(y_min + 1e-12) - 3
                sa.spectrogram.zmax   = 10.0 * np.log10(y_max + 1e-12) + 10
                
            else:
                sa.spectrogram.zlabel = "Power"
                sa.spectrogram.zmin   = y_min
                sa.spectrogram.zmax   = y_max


        if n < len(data_queue):
            d = np.asarray(data_queue[n])
            if log_scale == 'on':
                d = 10.0 * np.log10(d + 1e-12)

            sa.spectrogram.data = d
            return sa.spectrogram.get_plot()
        else:
            return dash.no_update

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
