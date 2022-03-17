import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

import time

import orjson

import config as cfg


@dash.callback(
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
        html.Hr(),
        dbc.Label("Sample Range", html_for="range-slider"),
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



@dash.callback(
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
        html.Hr(),
        dbc.Label("Number of Bins", html_for="bins-slider"),
        dcc.Slider(
            id={
                'type': 'bins-slider', 'index': 0, 

            },
            min = 8,
            max = 11,
            step = None,
            value= 10,
            marks= {i: '{}'.format(2 ** i) for i in range(8, 12)},
            included=False,


        )
    ]
    return children




@dash.callback(
    dash.Output('drf-err', 'children'),
    dash.Output('request-id', 'data'),
    dash.Input({'type': 'drf-load', 'index': dash.ALL}, 'n_clicks'),
    dash.State('drf-path', 'value'),
    dash.State({'type': 'channel-picker', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'range-slider', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'bins-slider', 'index': dash.ALL,}, 'value'),
)
def send_redis_request_data(n_clicks, drf_path, channel, sample_range, bins):
    if not n_clicks or n_clicks[0] < 1:
        return None, 0 

    req_id = cfg.redis_instance.incr('request-id')
    print(f'REQ ID: {req_id}')

    n_bins = 2**bins[0]

    req = {
        'drf_path'     : drf_path,
        'channel'      : channel[0],
        'start_sample' : sample_range[0][0],
        'stop_sample'  : sample_range[0][1],
        'bins'         : n_bins

    }

    cfg.redis_instance.publish(f'requests:{req_id}:data', orjson.dumps(req))


    try:
        rstrm = cfg.redis_instance.xread({f'responses:{req_id}:metadata'.encode(): '0-0'.encode()}, block=1000, count=1) 
        print(f"received drf metadata:\n{rstrm}")

    except:
        return "drf timeout?", dash.no_update

    cfg.redis_instance.delete(f'responses:{req_id}:metadata')

    metadata = orjson.loads(rstrm[0][1][0][1][b'data'])
    print(f'got metadata from redis: {metadata}')
    cfg.redis_instance.set("last-drf-id", "0-0")


    # global cfg.spec_datas
    cfg.spec_datas = {}
    cfg.spec_datas['metadata'] = metadata

    cfg.sa.spectrogram.clear_data()

    y_max     = cfg.spec_datas['metadata']['y_max']
    y_min     = cfg.spec_datas['metadata']['y_min']

    sfreq     = metadata['sfreq']
    n_samples = metadata['n_samples']

    # set axes and other basic info for plots
    cfg.sa.spec.yrange      = (y_min, y_max)
    cfg.sa.spectrogram.zmin = y_min
    cfg.sa.spectrogram.zmax = y_max

    cfg.sa.centre_frequency = cfg.spec_datas['metadata']['cfreq']

    cfg.sa.spec.number_samples = n_bins
    cfg.sa.spectrogram.number_samples = n_bins


    cfg.sa.spec.sample_frequency        = sfreq
    cfg.sa.spectrogram.sample_frequency = sfreq
    cfg.sa.spec.number_samples          = n_samples
    cfg.sa.spectrogram.number_samples   = n_samples
    cfg.sa.spec.show_data()

    return dash.no_update, req_id


@dash.callback(
            dash.Output("drf-data-finished", 'data'),
            dash.Output('drf-data', 'data'),
            dash.Input('drf-interval', 'n_intervals'),
            dash.State('request-id', 'data'),
            prevent_initial_call=True)
def get_next_drf_data(n, req_id):
    last_r_id = cfg.redis_instance.get("last-drf-id").decode()

    rstrm = cfg.redis_instance.xrange(f'responses:{req_id}:stream', min=f"({last_r_id}", count=1) 
    if (len(rstrm) == 0):
        for i in range(5):
            rstrm = cfg.redis_instance.xrange(f'responses:{req_id}:stream', min=f"({last_r_id}", count=1)
        print("no update")
        raise dash.exceptions.PreventUpdate


    new_r_id = rstrm[0][0].decode()
    cfg.redis_instance.set("last-drf-id", new_r_id)

    d = orjson.loads(rstrm[0][1][b'data'])
    if 'status' in d and d['status'] == 'DONE':
        # stream has finished
        # unsubscribe from updates
        print(f"FINISHED READING ALL DATA FROM REQUEST: {req_id}")
        return "True", dash.no_update

    return dash.no_update, d



@dash.callback(
    dash.Output('drf-interval', 'disabled'),
    # dash.Input('request-id', 'data'),
    dash.Input("content-tabs", 'value'),
    dash.Input("drf-data-finished", 'data'),
    dash.Input({'type': 'drf-pause', 'index': dash.ALL}, 'n_clicks'),
    dash.Input({'type': 'drf-play', 'index': dash.ALL}, 'n_clicks'),
    dash.State({'type': 'drf-load', 'index': dash.ALL}, 'n_clicks'),

    prevent_initial_call=True
    )
def handle_drf_interval(tab, drf_finished, pause, play, n):
    ctx = dash.callback_context

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # if n and n[0] > 0 and (prop_id == "request-id" or "play" in prop_id) and req_id != -1 and tab == 'content-tab-1':
    if n and n[0] > 0 and (prop_id == "request-id" or "play" in prop_id) and tab == 'content-tab-1':
        return False

    print("Disabling drf interval")
    return True






@dash.callback(
    dash.Output({'type': 'drf-metadata-accordion', 'index': 0,}, 'children'),
    dash.Input('request-id', 'data'),
    dash.Input("content-tabs", 'value'),
)
def update_metadeta_output(req_id, tab):
    """
    update metadata section when new Digital RF data is loaded
    The 'request-id' value gets updated when metadata is loaded
    """
    if not cfg.spec_datas:
        return html.P("Metadata will appear here when you pick a Digital RF File")
        # return None

    ctx = dash.callback_context
    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if prop_id == "content-tabs":
        return None

    children = [
        # html.H4("Metadata:"),
        html.P(f"Sample Rate: {cfg.spec_datas['metadata']['sfreq']} samples/second"),
        html.P(f"Center Frequency: {cfg.spec_datas['metadata']['cfreq']} Hz"),
        html.P(f"Channel: {cfg.spec_datas['metadata']['channel']}"),

    ]
    return children


@dash.callback(
    dash.Output(component_id='channel-div', component_property='children'),
    dash.Input('input-dir-button', 'n_clicks'),
    dash.State('drf-path', 'value'),

)
def start_redis_stream(n, drf_path):
    print("clicked input dir button")
    if n < 1: return dash.no_update
    print("clicked redis button")
    req_id = cfg.redis_instance.incr('request-id')
    print(f'REQ ID: {req_id}')
    
    print(f"publishing request {req_id} for {drf_path}")
    # make a request for the channels from drf_path
    cfg.redis_instance.publish(f'requests:{req_id}:channels', drf_path)


    try:
        rstrm = cfg.redis_instance.xread({f'responses:{req_id}:channels'.encode(): '0-0'.encode()}, block=1000, count=1) 
        print(f"received drf channels:\n{rstrm}")

    except:
        return dash.no_update

    cfg.redis_instance.delete(f'responses:{req_id}:channels')
    
    drf_channels = orjson.loads(rstrm[0][1][0][1][b'data'])
    print(f'got channels from redis: {drf_channels}')

    picker_options = [
        {'label': chan, 'value': chan} for chan in drf_channels
    ]

    children = [
        html.Hr(),
        dbc.Label("Digital RF Channel", html_for="channel-picker"),
        dcc.Dropdown(
            options=picker_options,
            value=drf_channels[0],
            id={
                'type': 'channel-picker', 'index': 0, 

            }
        ),
     ]

    return children




@dash.callback(
    dash.Output({'type': 'drf-load', 'index': 0}, 'disabled'),
    dash.Input('input-dir-button', 'n_clicks'),
)
def redis_update_load_data_button(n):
    if n < 1: return True

    return False



@dash.callback(
    dash.Output({'type': 'drf-play', 'index': 0}, 'disabled'),
    dash.Input({'type': 'drf-load', 'index': dash.ALL,}, 'n_clicks'),
    dash.Input('drf-interval', 'disabled'),

)
def enable_play_data_button(n, interval_disabled):
    if not interval_disabled:
        return True

    if n and n[0] < 1: return True

    return False

@dash.callback(
    dash.Output({'type': 'drf-rewind', 'index': 0}, 'disabled'),
    dash.Input({'type': 'drf-load', 'index': dash.ALL,}, 'n_clicks'),
)
def enable_rewind_data_button(n):
    if n and n[0] < 1: return True

    return False

@dash.callback(
    dash.Output({'type': 'drf-pause', 'index': 0}, 'disabled'),
    dash.Input({'type': 'drf-load', 'index': dash.ALL,}, 'n_clicks'),
    dash.Input('drf-interval', 'disabled'),
)
def enable_pause_data_button(n, interval_disabled):
    if n and n[0] < 1: return True

    if interval_disabled:
        return True

    return False

@dash.callback(
    dash.Output('placeholder', 'data'),
    dash.Input({'type': 'drf-rewind', 'index': dash.ALL,}, 'n_clicks'),
)
def handle_rewind_data_button(n):
    if n and n[0] < 1: raise dash.exceptions.PreventUpdate
    print("resetting drf data?")
    cfg.redis_instance.set("last-drf-id", "0-0")
    cfg.sa.spectrogram.clear_data()
    return 0




@dash.callback(
    dash.Output('reset-button-graph-interval-placeholder', 'n_clicks'),
    dash.Input({'type': 'drf-play', 'index': dash.ALL}, 'n_clicks'),
    dash.Input('reset-val', 'n_clicks'),
)
def handle_play_button(n_clicks):
    if n_clicks[0] < 1:
        return 0

    cfg.sa.spectrogram.clear_data()

    return 1


@dash.callback(
    dash.Output("drf-form-modal", "is_open"),
    dash.Input("open-modal-button", "n_clicks"), 
    dash.Input("close-modal-button", "n_clicks"),
    dash.Input({'type': 'drf-load', 'index': dash.ALL,}, 'n_clicks'),
    dash.State("drf-form-modal", "is_open"),
)
def toggle_modal(n_open, n_close, n_load, is_open):
    if n_open or n_close or n_load[0]:
        return not is_open
    return is_open
