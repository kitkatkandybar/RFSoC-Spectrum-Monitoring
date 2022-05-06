import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import orjson
import time
import shutil
import digital_rf

import os.path
import numpy as np

import config as cfg


###################################################################################################
#
#                                  Live Streaming Callbacks
#
###################################################################################################


@dash.callback(
    dash.Output({'type': 'stream-picker', 'index': dash.ALL,}, 'options'),
    dash.Input('stream-picker-div', 'n_clicks'),
    dash.State("content-tabs", 'value'),
)
def get_active_streams(n, tab):
    """
    gets the list of boards available for live streaming when the streams tab is clicked
    """
    if n and tab == 'content-tab-2':
        streams = cfg.redis_instance.smembers("active_streams")
        print(f"Got current active streams: {streams}")
        picker_options = [
            {'label': s.decode(), 'value': s.decode()} for s in streams
        ]

        return [picker_options]

    raise dash.exceptions.PreventUpdate


@dash.callback(
    dash.Output({'type': 'stream-metadata-accordion', 'index': 0,}, 'children'),
    dash.Input({'type': 'stream-picker', 'index': dash.ALL,}, 'value'),
)
def update_stream_metadata(stream_names):
    """
    Updates the sidebar with metadata from a board live stream
    """
    if not stream_names[0]:
        return html.P("Metadata will appear here when you pick a stream"),

    print(f"Getting metadata for {stream_names[0]}")
    metadata = cfg.redis_instance.hgetall(f"metadata:{stream_names[0]}")


    if not metadata:
        raise dash.exceptions.PreventUpdate

    metadata = {k.decode(): v.decode() for k,v in metadata.items()}
    metadata['y_max'] = float(metadata['y_max'] )
    metadata['y_min'] = float(metadata['y_min'] )

    cfg.spec_datas = {}
    cfg.spec_datas['metadata'] = metadata

    print("Got stream metadata:\n%s", metadata)

    sfreq     = float(metadata['sfreq'])
    n_samples = int(metadata['n_samples'])
    cfreq     = float(metadata['cfreq'])



    # TODO: Set the decimation factor some other way?
    decimation_factor =  int(metadata['decimation_factor'])
    cfg.sa.spectrogram.decimation_factor = decimation_factor
    cfg.sa.spec.decimation_factor        = decimation_factor


    cfg.sa.spec.sample_frequency        = sfreq
    cfg.sa.spectrogram.sample_frequency = sfreq

    cfg.sa.spec.centre_frequency        = cfreq
    cfg.sa.spectrogram.centre_frequency = cfreq

    cfg.sa.spec.number_samples          = n_samples



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
                html.Th(["Decimation Factor:"]), 
                html.Td([decimation_factor]),
            ]),
            html.Tr([
                html.Th(["FFT Bins:"]), 
                html.Td([metadata['fft_size']]),
            ]),
            html.Tr([
                html.Th(["Channel:"]), 
                html.Td([cfg.spec_datas['metadata']['channel']]),
            ]),
        ], 
        style={'width': '100%'}),
    ]
    return children



@dash.callback(
    dash.Output('stream-data', 'data'),
    dash.Input('stream-graph-interval', 'n_intervals'),
    dash.State({'type': 'stream-picker', 'index': dash.ALL,}, 'value'),
    prevent_initial_call=True
)
def get_next_data(n, stream_name):
    """
    Gets the newest point of data in a live stream and set its to be displayed on the dashboard graphs.

    This function gets called at every tick of 'stream-graph-interval'
    """
    name = stream_name[0]

    # TODO: Make sure we don't get duplicates!
    # get newest data point
    rstrm = cfg.redis_instance.xrevrange(f'stream:{name}', count=1) 

    if (len(rstrm) == 0):
        print(f"Got no new stream data from stream:{name}")
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
    """
    Handles enabling/disabling the Interval which controls when to fetch live stream data
    """
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


###################################################################################################
#
#                                  Data Download Callbacks
#
###################################################################################################


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


@dash.callback(
    dash.Output({'type': 'download-board-picker', 'index': dash.ALL,}, 'options'),
    dash.Input('download-board-picker-div', 'n_clicks'),
    dash.State("content-tabs", 'value'),
)
def get_active_download_boards(n, tab):
    """
    Gets the list of boards available for downloading data from Redis 
    """
    if n and tab == 'content-tab-2':
        boards = cfg.redis_instance.smembers("active_command_boards")
        print("Got list of boards from active_command_boards: {boards}")

        picker_options = [
            {'label': s.decode(), 'value': s.decode()} for s in boards
        ]

        return [picker_options]


    raise dash.exceptions.PreventUpdate


def write_drf_file(rstrm_real, rstrm_imag, metadata):
    """
    Writes raw IQ to a digitalRF file

    Note: This was done very last minute. It needs heavy reworking
    """
    n_points = len(rstrm_real)
    print(f"n points: {n_points}")

    datadir = os.path.join(os.path.dirname(__file__), "drf_data")
    chdir = os.path.join(datadir, "channel0")

    # writing parameters
    sample_rate_numerator   = metadata['sample_rate_numerator']
    sample_rate_denominator = metadata['sample_rate_denominator']
    sample_rate             = np.longdouble(sample_rate_numerator) / sample_rate_denominator
    dtype_str               = metadata['dtype_str']
    sub_cadence_secs        = metadata['sub_cadence_secs'] 
    file_cadence_seconds = metadata['file_cadence_seconds'] 
    compression_level    = metadata['compression_level'] 
    checksum             = metadata['checksum'] 
    is_complex           = metadata['is_complex'] 
    is_continuous        = metadata['is_continuous'] 
    num_subchannels      = metadata['num_subchannels'] 
    marching_periods     = metadata['marching_periods'] 
    uuid                 = metadata['uuid'] 
    vector_length        = metadata['number_samples'] # number of samples written for each call - typically MUCH longer
    
    # create short data in r/i to test using that to write
    arr_data = np.ones(
        (vector_length*n_points,), dtype=[("r", np.float), ("i", np.float)]
    )

    start_global_index = int(np.uint64(metadata['start_time']* sample_rate)) + 1

    # set up top level directory
    shutil.rmtree(chdir, ignore_errors=True)
    os.makedirs(chdir)


    # init
    dwo = digital_rf.DigitalRFWriter(
        chdir,
        dtype_str,
        sub_cadence_secs,
        file_cadence_seconds*1000, #it's in miliseconds
        start_global_index,
        sample_rate_numerator,
        sample_rate_denominator,
        uuid,
        compression_level,
        checksum,
        is_complex,
        num_subchannels,
        is_continuous,
        marching_periods,
    )

    # write
    for i in range(n_points):
        arr_data["r"][i*vector_length:i*vector_length+vector_length] = orjson.loads(rstrm_real[i][1][b'data'])
        arr_data["i"][i*vector_length:i*vector_length+vector_length] = orjson.loads(rstrm_imag[i][1][b'data'])
    result = dwo.rf_write(arr_data)    

    # close
    dwo.close()


    #METADATA
    #metadata parameters
    file_name = "metadata"
    metadata_dir = os.path.join(chdir, "metadata")

    shutil.rmtree(metadata_dir, ignore_errors=True)
    os.makedirs(metadata_dir)

    dmw = digital_rf.DigitalMetadataWriter(
        metadata_dir,
        sub_cadence_secs,
        file_cadence_seconds,
        sample_rate_numerator,
        sample_rate_denominator,
        file_name,
    )
    print("first create okay")

    data_dict = {}
    # To save an array of data, make sure the first axis has the same length
    # as the samples index
    idx_arr = np.arange(10, dtype=np.int64) + start_global_index

    # TODO: This may not be the best way of setting the center frequency
    # but this is the only way we were able to get accurate bounds from the board's data
    data_dict["center_frequencies"] = [metadata['sfreq'] /4 ] #  [metadata['cfreq'] ]


    sub_dict_processing = metadata['processing']
    data_dict["processing"] = sub_dict_processing

    #Not real values for receiver, copied them for digital rf we already
    sub_dict_receiver                        = metadata['receiver']
    data_dict["receiver"]                    = sub_dict_receiver

    data_dict["sample_rate_denominator"] = metadata['sample_rate_denominator']
    data_dict["sample_rate_numerator"] = metadata['sample_rate_numerator']
    data_dict["uuid_str"] = metadata['uuid_str']

    dmw.write(idx_arr, data_dict)

    return datadir


@dash.callback(
    dash.Output('download-board-data', 'data'),
    dash.Input({'type': 'download-button', 'index': dash.ALL,}, 'n_clicks'),
    dash.State({'type': 'download-board-picker', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'duration-download-input', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'download-time-unit-dropdown', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'download-name-input', 'index': dash.ALL,}, 'value'),
)
def handle_download_request(n, board, duration, time_unit, name):
    """
    Handles a board data request once the user hits submit on the board request form. 


    NOTE: This function was put together last minute. It's very sloppy and needs heavy reworking. 
    """
    if not n or n[0] < 1:
        raise dash.exceptions.PreventUpdate

    if time_unit[0] == 's':
        dur = duration[0]
    elif time_unit[0] == "ms":
        dur = duration[0] / 1e3
    else: # usec
        dur = duration[0] / 1e6

    board_name = board[0]

    req = {
        'duration'     : dur
    }

    req_id = cfg.redis_instance.incr(f'board-request-id:{board_name}')

    res_prefix = f'board-responses:{board_name}:{req_id}'


    print(f"DOWNLOAD REQ ID: {req_id} for BOARD NAME: {board_name}")
    cfg.redis_instance.publish(f'board-requests:{board_name}:{req_id}', orjson.dumps(req))

    time.sleep(1)


    # get data
    # poll data status
    status = cfg.redis_instance.get(f'{res_prefix}:complete').decode()
    print(f"Got status: {status}")
    while status != "True":
        time.sleep(0.5)
        status = cfg.redis_instance.get(f'{res_prefix}:complete').decode()
        print(f"Got status: {status}")
    print("Status is complete")


    # get entire stream
    # TODO: if the data is large, this should likely be broken into multiple steps
    rstrm_real = cfg.redis_instance.xrange(f'{res_prefix}:real') 
    rstrm_imag = cfg.redis_instance.xrange(f'{res_prefix}:imag')

    # get metadata
    rstrm = cfg.redis_instance.xread({f'{res_prefix}:metadata'.encode(): '0-0'.encode()}, block=10000, count=1) 
    metadata = orjson.loads(rstrm[0][1][0][1][b'data'])
    print(f"received download metadata:\n{metadata}")


    # create the Digital RF file using this data
    datadir = write_drf_file(rstrm_real, rstrm_imag, metadata)
    print("Done writing")


    # Delete the data from Redis
    cfg.redis_instance.delete(f'{res_prefix}:real')
    cfg.redis_instance.delete(f'{res_prefix}:imag')
    cfg.redis_instance.delete(f'{res_prefix}:metadata')

    print("Making zip file...")

    # Zip up the DigitalRF directory and send to the user's browser
    zip_file_name = name[0]
    # TODO: Delete the zip file from the web server after some amount of time???
    zip_path = shutil.make_archive(zip_file_name, 'zip', datadir)
    shutil.rmtree(datadir, ignore_errors=True)


    print("Sending file to user...")
    return dcc.send_file(zip_path)