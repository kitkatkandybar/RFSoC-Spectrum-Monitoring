import zipfile
import time
import datetime


import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import digital_rf
import orjson


import config as cfg


REQUEST_TIMEOUT = 5000 # 5 seconds

@dash.callback(
    dash.Output("drf-data-finished", 'data'),
    dash.Output('drf-data', 'data'),
    dash.Input('drf-interval', 'n_intervals'),
    dash.State('request-id', 'data'),
    dash.State('session-id', 'data'),
    prevent_initial_call=True
)
def get_next_drf_data(n, req_id, session_id):
    """
    Gets the next digitalRF data point to display, whenever drf-interval is fire
    """

    # TODO: Storing this value inside of redis may not be the smartest idea, but 
    # storing it as a Dash.Store component would also be messy!
    last_r_id = cfg.redis_instance.get(f"{session_id}:last-drf-id").decode()

    # incremement the ID value so redis knows to pick the next value in the stream
    # NOTE: this could be omitted if an "exclusive range" syntax is used in the xrange redis command,
    # however that syntax is only available in newer versions of Redis (>= 6.2) and as such it 
    # is easier to avoid this
    ids       = last_r_id.split('-')
    last_r_id = f'{ids[0]}-{int(ids[1])+1}'

    # get the next value after last_r_id in the stream
    rstrm = cfg.redis_instance.xrange(f'responses:{req_id}:stream', min=f"{last_r_id}", count=1) 
    if (len(rstrm) == 0):
        for i in range(5):
            rstrm = cfg.redis_instance.xrange(f'responses:{req_id}:stream', min=f"{last_r_id}", count=1)
            time.sleep(0.1)
            if len(rstrm) > 0:
                break
        else:
            print(f"Got no new value in the stream responses:{req_id}:stream",)
            raise dash.exceptions.PreventUpdate


    new_r_id = rstrm[0][0].decode()
    cfg.redis_instance.set(f"{session_id}:last-drf-id", new_r_id, ex=cfg.expire_time)

    d = orjson.loads(rstrm[0][1][b'data'])
    if 'status' in d and d['status'] == 'DONE':
        # stream has finished
        print(f"Finished reading all data for stream responses:{req_id}:stream")
        return "True", dash.no_update

    return dash.no_update, d


###################################################################################################
#
#                                   Metadata callbacks
#
###################################################################################################

def convert_to_hz_units(val):
    if val > 1e9:
        s = f"{val / 1e9} GHz"
    elif val > 1e6:
        s = f"{val / 1e6} MHz"
    elif val > 1e3:
        s = f"{val / 1e3} kHz"
    else:
        s = f"{val } Hz"

    return s

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

    ctx = dash.callback_context
    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # reset the metadata whenever the website tabs have been switched
    if prop_id == "content-tabs":
        return None

    # TODO: Check to make sure all of these keys exist before dereferencing them
    try:
        children = [
            dbc.Label("General"),
            html.Table([
                html.Tr([
                    html.Th("Sample Rate:"), 
                    html.Td(convert_to_hz_units(cfg.spec_datas['metadata']['sfreq'])),
                ]),
                html.Tr([
                    html.Th(["Center Frequency:"]), 
                    html.Td(convert_to_hz_units(cfg.spec_datas['metadata']['cfreq'])),
                ]),
                html.Tr([
                    html.Th(["Channel:"]), 
                    html.Td([cfg.spec_datas['metadata']['channel']]),
                ]),
            ]), 
            html.Hr(),
            dbc.Label("Processing"),
            html.Table([
                html.Tr([
                    html.Th("Decimation factor:"), 
                    html.Td(cfg.spec_datas['metadata']['metadata_samples']['processing']['decimation']),
                ]),
                html.Tr([
                    html.Th(["Interpolation:"]), 
                    html.Td(cfg.spec_datas['metadata']['metadata_samples']['processing']['interpolation']),
                ]),
                html.Tr([
                    html.Th(["Scaling:"]), 
                    html.Td(cfg.spec_datas['metadata']['metadata_samples']['processing']['scaling']),
                ]),
            ]), 
            html.Hr(),
            dbc.Label("Receiver"),
            html.Table([
                html.Tr([
                    html.Th(["ID:"]), 
                    html.Td(cfg.spec_datas['metadata']['metadata_samples']['receiver']['id']),
                ]),
                html.Tr([
                    html.Th("Antenna:"), 
                    html.Td(cfg.spec_datas['metadata']['metadata_samples']['receiver']['antenna']),
                ]),
                html.Tr([
                    html.Th(["Clock rate:"]), 
                    html.Td(convert_to_hz_units(cfg.spec_datas['metadata']['metadata_samples']['receiver']['clock_rate'])),
                ]),
                html.Tr([
                    html.Th(["Description:"]), 
                    html.Td(cfg.spec_datas['metadata']['metadata_samples']['receiver']['description']),
                ]),
            ]), 
            html.Hr(),
            dbc.Label("Request Parameters"),
            html.Table([
                html.Tr([
                    html.Th(["File path:"]), 
                    html.Td(cfg.spec_datas['metadata']['req_params']['filepath']),
                ]),
                html.Tr([
                    html.Th("Channel:"), 
                    html.Td(cfg.spec_datas['metadata']['req_params']['channel']),
                ]),
                html.Tr([
                    html.Th(["Start Sample:"]), 
                    html.Td(cfg.spec_datas['metadata']['req_params']['start_sample']),
                ]),
                html.Tr([
                    html.Th(["Stop Sample:"]), 
                    html.Td(cfg.spec_datas['metadata']['req_params']['stop_sample']),
                ]),
                html.Tr([
                    html.Th(["Start Time:"]), 
                    html.Td(datetime.datetime.fromtimestamp(cfg.spec_datas['metadata']['start_time'])),
                ]),
                html.Tr([
                    html.Th(["Stop Time:"]), 
                    html.Td(datetime.datetime.fromtimestamp(cfg.spec_datas['metadata']['end_time'])),
                ]),
                html.Tr([
                    html.Th(["Modulus:"]), 
                    html.Td(cfg.spec_datas['metadata']['req_params']['modulus']),
                ]),
                html.Tr([
                    html.Th(["Integration:"]), 
                    html.Td(cfg.spec_datas['metadata']['req_params']['integration']),
                ]),
                html.Tr([
                    html.Th(["FFT Bins:"]), 
                    html.Td(cfg.spec_datas['metadata']['req_params']['bins']),
                ]),
                html.Tr([
                    html.Th(["Points:"]), 
                    html.Td(cfg.spec_datas['metadata']['req_params']['n_points']),
                ]),
            ], style={'width': '100%'}), 
        ]
    except KeyError as e:
        raise dash.exceptions.PreventUpdate 

    return children


###################################################################################################
#
#                        Digital RF Request form callbacks
#
###################################################################################################

@dash.callback(
    dash.Output('input-dir-button', 'disabled'),
    dash.Input({'type': 'drf-path', 'index': dash.ALL,}, 'value'),
)
def input_dir_button_disabled(drf_path):
    """ Disable the 'Select DigitalRF file' when no path has been specified"""
    if drf_path[0]:
        return False
    return True


@dash.callback(
    dash.Output(component_id='channel-div', component_property='children'),
    dash.Input('input-dir-button', 'n_clicks'),
    dash.State({'type': 'drf-path', 'index': dash.ALL,}, 'value'),
)
def get_drf_channel_info(n, drf_path):
    """
    Get DRF Channel information when the user has supplied an input directory 
    """
    if n < 1: return dash.no_update
    req_id = cfg.redis_instance.incr('request-id')

    print(f"Publishing request for DRF channels on requests:{req_id}:channels for {drf_path[0]}")
    # make a request for the channels from drf_path
    cfg.redis_instance.publish(f'requests:{req_id}:channels', drf_path[0])

    rstrm = cfg.redis_instance.xread({f'responses:{req_id}:channels'.encode(): '0-0'.encode()}, block=REQUEST_TIMEOUT, count=1) 
    if not rstrm:
        print("Channels timed out")
        return "Error, could not load channels, try again"

    cfg.redis_instance.delete(f'responses:{req_id}:channels')
    
    drf_channels = orjson.loads(rstrm[0][1][0][1][b'data'])
    print(f'Got DigitalRF channels from Redis stream responses:{req_id}:channels:\n{drf_channels}')

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
    dash.Output(component_id='bins-div', component_property='children'),
    dash.Input('input-dir-button', 'n_clicks'),
)
def update_bins_slider(n):
    """
    Displays the bins slider once the user has selected a DigitalRF directory
    """

    # TODO: only display the bins once the drf channels have been loaded, ie 
    # when the input has been validated

    if n < 1: return None

    sample_min           = 0
    sample_max           = 1000000
    sample_step          = 10000

    sample_start_default = 300000
    sample_stop_default  = 700000
    sample_mark_width    = 100000

    children = [
        html.Hr(),
        dbc.Label("Number of FFT Bins", html_for="bins-slider"),
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
    dash.Output('drf-n-samples', 'data'),
    dash.Input({'type': 'channel-picker', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'drf-path', 'index': dash.ALL,}, 'value'),
    prevent_initial_call=True
)
def get_drf_sample_range(chan, drf_path):
    if not chan or not drf_path:
        return dash.no_update
    # send a request for samples
    req_id = cfg.redis_instance.incr('request-id')
    cfg.redis_instance.publish(f'requests:{req_id}:samples', orjson.dumps({'path': drf_path[0], 'channel': chan[0]}))
    print(f"publishing request on stream requests:{req_id}:samples for path {drf_path[0]} and channel {chan[0]}")

    # wait for the response in a stream
    rstrm = cfg.redis_instance.xread({f'responses:{req_id}:samples'.encode(): '0-0'.encode()}, block=REQUEST_TIMEOUT, count=1) 
    if not rstrm:
        print("Sample request timed out")
        return dash.no_update
    print(f"Received DRF sample range from stream responses:{req_id}:samples: {rstrm}")
    cfg.redis_instance.delete(f'responses:{req_id}:samples')
    
    n_samples = orjson.loads(rstrm[0][1][0][1][b'data'])

    return n_samples


@dash.callback(
    dash.Output(component_id='sample-div', component_property='children'),
    dash.Input('input-dir-button', 'n_clicks'),
)
def update_sample_input(n):
    """
    Displays the sample slider once the user has selected a DigitalRF directory
    """
    # TODO: only display the slider once the drf channels have been loaded, ie 
    # when the input has been validated

    if n < 1: return None

    children = [
        html.Hr(),
        dbc.Label("Sample Range"),
        dbc.Row([
            dbc.Label("Start", width="auto"),
            dbc.Col(
                dcc.Input(
                    id={
                        'type': 'start-sample-input', 'index': 0, 
                    },
                    type="number",
                    value=0,
                    min=0,
                    max=0,
                    step=1, debounce=True,
                ), 
            ),
            dbc.Label("Stop", width="auto"),
            dbc.Col(
                dcc.Input(
                    id={
                        'type': 'stop-sample-input', 'index': 0, 
                    },
                    type="number",
                    value=0,
                    min=0,
                    max=0,
                    step=1, debounce=True,
                ), 
            ),
            dbc.FormText(
                "Acceptable range: {} - {}",
                color="secondary",
                id="sample-range-formtext"
            ),
        ]),

    ]


    return children

@dash.callback(
    dash.Output('sample-range-formtext', 'children'),
    dash.Input('drf-n-samples', 'data'),
)
def update_sample_formtext(n):
    s = f"Acceptable range: 0 - {n}"
    return s

@dash.callback(
    dash.Output({'type': 'start-sample-input', 'index': 0,}, 'max'),
    dash.Input('drf-n-samples', 'data'),
)
def update_sample_min_range(n):
    return n

@dash.callback(
    dash.Output({'type': 'stop-sample-input', 'index': 0,}, 'max'),
    dash.Input('drf-n-samples', 'data'),
)
def update_sample_max_range(n):
    return n


@dash.callback(
    dash.Output({'type': 'stop-sample-input', 'index': 0,}, 'value'),
    dash.Input('drf-n-samples', 'data'),
)
def update_sample_max_val(n):
    return n

@dash.callback(
    dash.Output(component_id='int-mod-div', component_property='children'),
    dash.Input('input-dir-button', 'n_clicks'),
)
def update_integration_and_modulus(n):
    if n < 1: return None

    children = [
        html.Hr(),
        dbc.Row([
            dbc.Label("Modulus", width="auto"),
            dbc.Col(

            dcc.Input(
                id={
                    'type': 'modulus-input', 'index': 0, 
                },
                type="number",
                value=10000,
                min=1,
                step=1, debounce=True,
            )),
            dbc.Label("Integration", width="auto"),
            dbc.Col(

            dcc.Input(
                id={
                    'type': 'integration-input', 'index': 0, 
                },
                type="number",
                value=1,
                min=1,
                step=1, debounce=True,
            )), 
        ]),
           
    ]

    return children


@dash.callback(
    dash.Output("drf-form-modal", "is_open"),
    dash.Input("open-modal-button", "n_clicks"), 
    dash.Input("close-modal-button", "n_clicks"),
    dash.Input({'type': 'drf-load', 'index': dash.ALL,}, 'n_clicks'),
    dash.State("drf-form-modal", "is_open"),
)
def toggle_modal(n_open, n_close, n_load, is_open):
    """ Toggles open/closed the form modal for DigitalRF playback requests"""
    if n_open or n_close or n_load[0]:
        return not is_open
    return is_open


@dash.callback(
    dash.Output('drf-form-err', 'children'),
    dash.Output('request-id', 'data'),
    dash.Input({'type': 'drf-load', 'index': dash.ALL}, 'n_clicks'),
    dash.State({'type': 'drf-path', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'channel-picker', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'start-sample-input', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'stop-sample-input', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'bins-slider', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'modulus-input', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'integration-input', 'index': dash.ALL,}, 'value'),
    dash.State('session-id', 'data'),
)
def send_redis_request_and_get_metadata(n_clicks, drf_path, channel, start, stop, bins, modulus, integration, session_id):
    """
    Sends a request to the back end for DigitalRF data when "load data" button is clicked, 
    and receives the metadata from the request
    """
    if not n_clicks or n_clicks[0] < 1:
        return None, 0 

    req_id = cfg.redis_instance.incr('request-id')

    n_bins = 2**bins[0]

    req = {
        'drf_path'     : drf_path[0],
        'channel'      : channel[0],
        'start_sample' : start[0],
        'stop_sample'  : stop[0],
        'bins'         : n_bins,
        'modulus'      : modulus[0],
        'integration'  : integration[0],
    }

    print(f"Publishing request requests:{req_id}:data with parameters:\n{req}")
    cfg.redis_instance.publish(f'requests:{req_id}:data', orjson.dumps(req))
    cfg.redis_instance.expire(f'requests:{req_id}:data', cfg.expire_time)


    rstrm = cfg.redis_instance.xread({f'responses:{req_id}:metadata'.encode(): '0-0'.encode()}, block=REQUEST_TIMEOUT, count=1)
    print(f"Received DRF metadata from channel responses:{req_id}:metadata:\n{rstrm}")

    if not rstrm:
        print("Tiemeout")
        return "Error", dash.no_update

    cfg.redis_instance.delete(f'responses:{req_id}:metadata')

    metadata = orjson.loads(rstrm[0][1][0][1][b'data'])

    # Initialize the playback index to the first value in the stream
    cfg.redis_instance.set(f"{session_id}:last-drf-id", "0-0")

    # update internal metadata and parameters
    cfg.spec_datas = {}
    cfg.spec_datas['metadata'] = metadata

    cfg.sa.spectrogram.clear_data()

    y_max     = cfg.spec_datas['metadata']['y_max']
    y_min     = cfg.spec_datas['metadata']['y_min']

    sfreq     = metadata['sfreq']
    n_samples = metadata['n_samples']

    decimation = metadata['metadata_samples']['processing']['decimation']
    cfg.sa.spectrogram.decimation_factor = decimation
    cfg.sa.spec.decimation_factor        = decimation

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


###################################################################################################
#
#                        Digital RF Options callbacks
#
###################################################################################################

@dash.callback(
    dash.Output({'type': 'drf-load', 'index': 0}, 'disabled'),
    dash.Input('input-dir-button', 'n_clicks'),
)
def redis_update_load_data_button(n):
    """
    Let the user load the DRF data once they have chosen an input directory
    """
    if n < 1: return True

    return False


@dash.callback(
    dash.Output({'type': 'drf-play', 'index': 0}, 'disabled'),
    dash.Input({'type': 'drf-load', 'index': dash.ALL,}, 'n_clicks'),
    dash.Input('drf-interval', 'disabled'),
)
def enable_play_data_button(n, interval_disabled):
    """
    Enable the play button when data has been loaded and data isn't currently streaming
    """
    if not interval_disabled:
        return True

    if n and n[0] < 1: return True

    return False

@dash.callback(
    dash.Output({'type': 'drf-rewind', 'index': 0}, 'disabled'),
    dash.Input({'type': 'drf-load', 'index': dash.ALL,}, 'n_clicks'),
)
def enable_rewind_data_button(n):
    """
    Enable the rewind button when data has been loaded
    """
    if n and n[0] < 1: return True

    return False

@dash.callback(
    dash.Output({'type': 'drf-pause', 'index': 0}, 'disabled'),
    dash.Input({'type': 'drf-load', 'index': dash.ALL,}, 'n_clicks'),
    dash.Input('drf-interval', 'disabled'),
)
def enable_pause_data_button(n, interval_disabled):
    """
    Enable the play button when data has been loaded and data *is* currently streaming
    """
    if n and n[0] < 1: return True

    if interval_disabled:
        return True

    return False

@dash.callback(
    dash.Output('placeholder', 'data'),
    dash.Input({'type': 'drf-rewind', 'index': dash.ALL,}, 'n_clicks'),
    dash.State('session-id', 'data'),
)
def handle_rewind_data_button(n, session_id):
    """
    When the rewind button is clicked, reset the last drf data point seen to the beginning
    and clear the spectrogram waterfall plot
    """
    if n and n[0] < 1: raise dash.exceptions.PreventUpdate
    cfg.redis_instance.set(f"{session_id}:last-drf-id", "0-0", ex=cfg.expire_time)

    # TODO: Move this into update_specgram_graph()?
    cfg.sa.spectrogram.clear_data()
    return 0

@dash.callback(
    dash.Output('drf-interval', 'disabled'),
    dash.Input("content-tabs", 'value'),
    dash.Input("drf-data-finished", 'data'),
    dash.Input({'type': 'drf-pause', 'index': dash.ALL}, 'n_clicks'),
    dash.Input({'type': 'drf-play', 'index': dash.ALL}, 'n_clicks'),
    dash.State({'type': 'drf-load', 'index': dash.ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def handle_drf_interval(tab, drf_finished, pause, play, n):
    """
    Enable the drf interval, which gets new DRF data to display at a steady rate,
    when the user has hit "play"

    Disable it when the user has hit pause, or when all of the data has been played through
    """
    ctx = dash.callback_context

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if n and n[0] > 0 and (prop_id == "request-id" or "play" in prop_id) and tab == 'content-tab-1':
        print("Enabling Digital RF interval")
        return False

    print("Disabling Digital RF interval")
    return True
