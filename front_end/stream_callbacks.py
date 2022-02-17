import dash
from dash import dcc
from dash import html


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
        streams = redis_instance.smembers("active_streams")
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
    metadata = redis_instance.hgetall(f"metadata:{stream_names[0]}")


    if not metadata:
        raise dash.exceptions.PreventUpdate

    metadata = {k.decode(): v.decode() for k,v in metadata.items()}

    global spec_datas
    spec_datas = {}
    spec_datas['metadata'] = metadata

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
    if not 'value':
        raise dash.exceptions.PreventUpdate


    children = [
        dbc.Button(
            'Play stream data', 
            id='play-stream-data', 
            n_clicks=0, 
            disabled=True,
            color="primary",
        ),
    ]
    return children
