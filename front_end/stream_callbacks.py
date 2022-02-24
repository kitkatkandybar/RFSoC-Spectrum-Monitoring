import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import json
import time

import config as cfg



@dash.callback(
            dash.Output({'type': 'stream-picker', 'index': dash.ALL,}, 'options'),
            dash.Input("content-tabs", 'value'))
def get_active_streams(tab):
    """
    get the currently active streams from Redis when the streams tab is clicked
    """
    print("boop")
    print('getting active streams?')
    if tab == 'content-tab-2':
        streams = cfg.redis_instance.smembers("active_streams")
        print(f"GOT STREAMS: {streams}")
        picker_options = [
            {'label': s.decode(), 'value': s.decode()} for s in streams
        ]

        return [picker_options]


    raise dash.exceptions.PreventUpdate



@dash.callback(
            dash.Output('stream-metadata-div', 'children'),
            dash.Input({'type': 'stream-picker', 'index': dash.ALL,}, 'value'))
def update_stream_metadata(stream_names):
    if not 'value':
        raise dash.exceptions.PreventUpdate

    print(f"Getting metadata for {stream_names[0]}")
    metadata = cfg.redis_instance.hgetall(f"metadata:{stream_names[0]}")


    if not metadata:
        raise dash.exceptions.PreventUpdate

    metadata = {k.decode(): v.decode() for k,v in metadata.items()}

    cfg.spec_datas = {}
    cfg.spec_datas['metadata'] = metadata

    print(f"got streaming metadata:\n{metadata}")


    children = [
        html.H4("Metadata:"),
        html.P(f"Name: {stream_names[0]}"),
        html.P(f"Sample Rate: {metadata['sfreq']} samples/second"),
        html.P(f"Center Frequency: {metadata['cfreq']} Hz"),
        html.P(f"Channel: {metadata['channel']}"),

    ]
    return children



@dash.callback(
            dash.Output('play-stream-div', 'children'),
            dash.Input('stream-metadata-div', 'children'))
def display_play_stream_button(s):
    if not s:
        raise dash.exceptions.PreventUpdate

    children = [
        dbc.Button(
            'Play stream data', 
            id={
                'type': 'play-stream-data', 'index': 0, 
            },
            n_clicks=0, 
            disabled=False,
            color="primary",
        ),
        dbc.Button(
            'Pause', 
            id={
                'type': 'pause-stream-data', 'index': 0, 
            },
            n_clicks=0, 
            disabled=False,
            color="secondary",
        ),

    ]
    return children


@dash.callback(dash.Output('stream-last-id', 'data'),
            dash.Input('stream-interval', 'n_intervals'),
            dash.State({'type': 'stream-picker', 'index': dash.ALL,}, 'value'),
            dash.State('stream-last-id', 'data'), prevent_initial_call=True)
def stream_data(n, stream_name, last_id):
    """ call this once a second to get redis data"""
    if n < 1: 
        raise dash.exceptions.PreventUpdate

    name = stream_name[0]
    print(f'CALLED STREAM_DATA, last id: {last_id}')

    if last_id == -1:
        rstrm = cfg.redis_instance.xrange(f'stream:{name}', min=f'{int(time.time() - 5)}')
    else:
        rstrm = cfg.redis_instance.xrange(f'stream:{name}', min=f'({last_id}')

    if (len(rstrm) == 0):
        print("no update")
        raise dash.exceptions.PreventUpdate
    
    new_id = rstrm[-1][0].decode()
    print(f"number of new data: {len(rstrm)}")
    for d in rstrm:
        datum = json.loads(d[1][b'data'])
        cfg.stream_data_q.append(datum)

    return new_id

@dash.callback(dash.Output('stream-data', 'data'),
            dash.Input('stream-graph-interval', 'n_intervals'), prevent_initial_call=True)
def get_next_data(n):
    print("popping data")
    if cfg.stream_data_q:
        datum = cfg.stream_data_q.pop()

        return datum
    else:
        raise dash.exceptions.PreventUpdate
        

# @dash.callback(dash.Output('play-stream-interval', 'data'),
#             dash.Output('pause-stream-graph-interval', 'disabled'),
#             dash.Input({'type': 'play-stream-data', 'index': dash.ALL,}, 'n_clicks'), 
#             prevent_initial_call=True)
# def click_play_stream(n):
#     if n == 0: return 'True', 'True'

#     return 'False', 'False'

# @dash.callback(dash.Output('pause-stream-interval', 'data'),
#             dash.Output('pause-stream-graph-interval', 'disabled'),
#             dash.Input({'type': 'pause-stream-data', 'index': dash.ALL,}, 'n_clicks'))
# def click_pause_stream(n):

#     return 'True', 'True'

@dash.callback(
    dash.Output('stream-interval', 'disabled'),
    dash.Input({'type': 'play-stream-data', 'index': dash.ALL,}, 'n_clicks'),
    dash.Input({'type': 'pause-stream-data', 'index': dash.ALL,}, 'n_clicks'),
    prevent_initial_call=True
    )
def handle_stream_interval(play_n, pause_n):

    ctx = dash.callback_context

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(f"handle_stream_interval: prop_id {prop_id}")
    # if prop_id['type'] == 'play-stream-data':
    if 'play' in prop_id and play_n[0] > 0:   
        return False

    return True

@dash.callback(
    dash.Output('stream-graph-interval', 'disabled'),
    dash.Input({'type': 'play-stream-data', 'index': dash.ALL,}, 'n_clicks'),
    dash.Input({'type': 'pause-stream-data', 'index': dash.ALL,}, 'n_clicks'),
    prevent_initial_call=True
    )
def handle_graph_stream_interval(play_n, pause_n):
    ctx = dash.callback_context

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if 'play' in prop_id and play_n[0] > 0:
        return False

    return True














