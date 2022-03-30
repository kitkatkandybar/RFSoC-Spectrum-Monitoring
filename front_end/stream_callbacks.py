import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import orjson
import time

import config as cfg



@dash.callback(
            dash.Output({'type': 'stream-picker', 'index': dash.ALL,}, 'options'),
            dash.Input('stream-picker-div', 'n_clicks'),
            dash.State("content-tabs", 'value'))
def get_active_streams(n, tab):
    """
    get the currently active streams from Redis when the streams tab is clicked
    """
    print(f'getting active streams? {n}')
    if n and tab == 'content-tab-2':
        streams = cfg.redis_instance.smembers("active_streams")
        print(f"GOT STREAMS: {streams}")
        picker_options = [
            {'label': s.decode(), 'value': s.decode()} for s in streams
        ]

        return [picker_options]


    raise dash.exceptions.PreventUpdate


@dash.callback(
            dash.Output({'type': 'stream-metadata-accordion', 'index': 0,}, 'children'),
            dash.Input({'type': 'stream-picker', 'index': dash.ALL,}, 'value'))
def update_stream_metadata(stream_names):
    if not stream_names[0]:
        return html.P("Metadata will appear here when you pick a stream"),
        # raise dash.exceptions.PreventUpdate

    print(f"Getting metadata for {stream_names[0]}")
    metadata = cfg.redis_instance.hgetall(f"metadata:{stream_names[0]}")


    if not metadata:
        raise dash.exceptions.PreventUpdate

    metadata = {k.decode(): v.decode() for k,v in metadata.items()}
    metadata['y_max'] = float(metadata['y_max'] )
    metadata['y_min'] = float(metadata['y_min'] )

    cfg.spec_datas = {}
    cfg.spec_datas['metadata'] = metadata

    print(f"got streaming metadata:\n{metadata}")

    sfreq     = float(metadata['sfreq'])
    n_samples = int(metadata['n_samples'])

    cfreq = float(metadata['cfreq'])

    cfg.sa.spec.centre_frequency        = cfreq
    cfg.sa.spectrogram.centre_frequency = cfreq
    cfg.sa.spec.sample_frequency        = sfreq
    cfg.sa.spectrogram.sample_frequency = sfreq
    cfg.sa.spec.number_samples          = n_samples
    cfg.sa.spectrogram.number_samples   = n_samples

    # TODO: Set the decimation factor some other way?
    cfg.sa.spectrogram.decimation_factor = 2
    cfg.sa.spec.decimation_factor        = 2



    if sfreq > 1e9:
        sfreq = f"{sfreq / 1e9} GHz"
    elif sfreq > 1e6:
        sfreq = f"{sfreq / 1e6} MHz"
    elif sfreq > 1e3:
        sfreq = f"{sfreq / 1e3} kHz"
    else:
        sfreq = f"{sfreq } Hz"


    if cfreq > 1e9:
        cfreq = f"{cfreq / 1e9} GHz"
    elif cfreq > 1e6:
        cfreq = f"{cfreq / 1e6} MHz"
    elif sfreq > 1e3:
        cfreq = f"{cfreq / 1e3} kHz"
    else:
        cfreq = f"{cfreq } Hz"

    children = [
        html.Table([
            html.Tr([
                html.Th("Name:"), 
                html.Td(stream_names[0]),
            ]),
            html.Tr([
                html.Th("Sample Rate:"), 
                html.Td(sfreq),
            ]),
            html.Tr([
                html.Th(["Center Frequency:"]), 
                html.Td([cfreq]),
            ]),
            html.Tr([
                html.Th(["Channel:"]), 
                html.Td([cfg.spec_datas['metadata']['channel']]),
            ]),
        ], 
        style={'width': '100%'}),
    ]
    return children



@dash.callback(dash.Output('stream-data', 'data'),
            dash.Input('stream-graph-interval', 'n_intervals'),
            dash.State({'type': 'stream-picker', 'index': dash.ALL,}, 'value'),
            prevent_initial_call=True)
def get_next_data(n, stream_name):
    name = stream_name[0]
    # TODO: Make sure we don't get duplicates!
    # get newest data point
    rstrm = cfg.redis_instance.xrevrange(f'stream:{name}', count=1) 

    if (len(rstrm) == 0):
        print("no update")
        raise dash.exceptions.PreventUpdate

    d = orjson.loads(rstrm[0][1][b'data'])
    return d
        
@dash.callback(
    dash.Output('stream-graph-interval', 'disabled'),
    dash.Input({'type': 'play-stream-data', 'index': dash.ALL,}, 'n_clicks'),
    dash.Input({'type': 'pause-stream-data', 'index': dash.ALL,}, 'n_clicks'),
    dash.Input("content-tabs", 'value'),

    prevent_initial_call=True
    )
def handle_graph_stream_interval(play_n, pause_n, tab):
    ctx = dash.callback_context

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if 'play' in prop_id and play_n[0] > 0 and tab == 'content-tab-2':
        cfg.sa.spectrogram.clear_data()
        return False

    return True


@dash.callback(
    dash.Output({'type': 'play-stream-data', 'index': 0,}, 'disabled'),
    dash.Input({'type': 'stream-picker', 'index': dash.ALL,}, 'value'),
)
def handle_disable_play_stream_button(stream_val):
    if not stream_val[0]:
        return True

    return False

@dash.callback(
    dash.Output({'type': 'pause-stream-data', 'index': 0,}, 'disabled'),
    dash.Input({'type': 'play-stream-data', 'index': dash.ALL,}, 'disabled'),
    dash.Input({'type': 'stream-picker', 'index': dash.ALL,}, 'value'),
)
def handle_disable_pause_stream_button(play_disabled, stream_val):
    if not stream_val[0]:
        return True

    return False


@dash.callback(
    dash.Output("download-modal", "is_open"),
    dash.Input("open-download-modal-button", "n_clicks"), 
    dash.Input("close-download-modal-button", "n_clicks"),
    dash.Input({'type': 'download-button', 'index': dash.ALL,}, 'n_clicks'),
    dash.State("download-modal", "is_open"),
)
def toggle_download_modal(n_open, n_close, n_load, is_open):
    if n_open or n_close or n_load[0]:
        return not is_open
    return is_open














