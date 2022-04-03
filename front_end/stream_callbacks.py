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

    cfg.sa.spec.sample_frequency        = sfreq
    cfg.sa.spectrogram.sample_frequency = sfreq
    # cfg.sa.spec.centre_frequency        = sfreq/2
    cfg.sa.spec.centre_frequency        = sfreq/4
    

    # cfg.sa.spectrogram.centre_frequency = sfreq/2
    cfg.sa.spectrogram.centre_frequency = sfreq/4
    # cfg.sa.spectrogram.centre_frequency        = sfreq/4
    
    cfg.sa.spec.number_samples          = n_samples
    cfg.sa.spectrogram.number_samples   = n_samples
    # TODO: Set the decimation factor some other way?
    cfg.sa.spectrogram.decimation_factor = 2
    cfg.sa.spec.decimation_factor        = 2


    print(cfg.sa.spec)



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


@dash.callback(
            dash.Output({'type': 'download-board-picker', 'index': dash.ALL,}, 'options'),
            dash.Input('download-board-picker-div', 'n_clicks'),
            dash.State("content-tabs", 'value'))
def get_active_download_boards(n, tab):
    """
    get the currently active streams from Redis when the streams tab is clicked
    """
    if n and tab == 'content-tab-2':
        boards = cfg.redis_instance.smembers("active_command_boards")
        print(f"GOT STREAMS: {boards}")
        picker_options = [
            {'label': s.decode(), 'value': s.decode()} for s in boards
        ]

        return [picker_options]


    raise dash.exceptions.PreventUpdate


@dash.callback(
    dash.Output('download-placeholder', 'data'),
    dash.Input({'type': 'download-button', 'index': dash.ALL,}, 'n_clicks'),
    dash.State({'type': 'download-board-picker', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'duration-download-input', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'download-time-unit-dropdown', 'index': dash.ALL,}, 'value'),
    dash.State({'type': 'download-name-input', 'index': dash.ALL,}, 'value'),
)
def handle_download_request(n, board, duration, time_unit, name):
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



    # get metadata
    # try:
    rstrm = cfg.redis_instance.xread({f'{res_prefix}:metadata'.encode(): '0-0'.encode()}, block=10000, count=1) 
    print(rstrm)
    metadata = orjson.loads(rstrm[0][1][0][1][b'data'])
    print(f"received download metadata:\n{metadata}")

    # except Exception as e:
    #     print(e)
    #     return dash.no_update


    start = time.time()


    # get data
    # wait until stream has been marked as complete
    # rstrm = cfg.redis_instance.xread(
    #     {f'board-responses:{board_name}:{req_id}:metadata'.encode(): '0-0'.encode()},
    #     block=(duration+5)*1000, count=1) 

    # poll data status

    status = cfg.redis_instance.get(f'{res_prefix}:complete').decode()
    print(f"Got status: {status}")
    while status == "False":
        time.sleep(0.5)
        status = cfg.redis_instance.get(f'{res_prefix}:complete').decode()
        print(f"Got status: {status}")


    print("Status is complete")


    # get entire stream
    rstrm_real = cfg.redis_instance.xrange(f'{res_prefix}:real') 
    rstrm_imag = cfg.redis_instance.xrange(f'{res_prefix}:imag')

    n_points = len(rstrm_real)
    print(f"n points: {n_points}")

    datadir = os.path.join("/Users/yanag/Documents", "drf_ex")
    chdir = os.path.join(datadir, "channel")

    # writing parameters
    sample_rate_numerator = int(25000000)  # 100 Hz sample rate - typically MUCH faster
    sample_rate_denominator = 1
    sample_rate = np.longdouble(sample_rate_numerator) / sample_rate_denominator
    dtype_str = "i2"  # short int
    sub_cadence_secs = (
        3600  # Number of seconds of data in a subdirectory - typically MUCH larger
    )
    file_cadence_seconds = 1  # Each file will have up to 400 ms of data
    compression_level    = 1  # low level of compression
    checksum         = False  # no checksum
    is_complex       = True  # complex values
    is_continuous    = True
    num_subchannels  = 1  # only one subchannel
    marching_periods = False  # no marching periods when writing
    uuid             = "Fake UUID - use a better one!"
    vector_length    = metadata['number_samples'] #25000000  # number of samples written for each call - typically MUCH longer

    # create short data in r/i to test using that to write
    arr_data = np.ones(
        # (vector_length, num_subchannels), dtype=[("r", np.int16), ("i", np.int16)]
        (vector_length, ), dtype=[("r", np.int16), ("i", np.int16)]
    )


   


    # start 2014-03-09 12:30:30 plus one sample
    start_global_index = int(np.uint64(18000000 * sample_rate)) + 1

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
        arr_data["r"] = np.array(orjson.loads(rstrm_real[i][1][b'data']))
        arr_data["i"] = np.array(orjson.loads(rstrm_imag[i][1][b'data']))
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

    data_dict["center_frequencies"] = [15000000.]


    sub_dict_processing = {}
    sub_dict_processing["channelizer_filter_taps"] = []#array([], dtype=float64)
    sub_dict_processing["decimation"] = 1
    sub_dict_processing["interpolation"] = 1
    sub_dict_processing["resampling_filter_taps"] = [] #array([], dtype=float64)
    sub_dict_processing["scaling"] = 1.0
    data_dict["processing"] = sub_dict_processing

    #Not real values for receiver, copied them for digital rf we already
    sub_dict_receiver = {}
    sub_dict_receiver["antenna"] = 'ADC0' #
    sub_dict_receiver["bandwidth"] = 100000000.0
    sub_dict_receiver["center_freq"] = 15000000.0
    sub_dict_receiver["clock_rate"] = 125000000.0
    sub_dict_receiver["clock_source"] = 'external'
    sub_dict_receiver["dc_offset"] = False
    sub_dict_receiver["description"] = 'UHD USRP source using GNU Radio'
    sub_dict_receiver["gain"] = 50.0
    sub_dict_receiver["id"] = '192.168.20.2'
    sub_dict_receiver_info= {}
    sub_dict_receiver_info["mboard_id"] = 'ni-n3xx-316A5C0'
    sub_dict_receiver_info["mboard_name"] = 'n/a'
    sub_dict_receiver_info["mboard_serial"] = '316A5C0'
    sub_dict_receiver_info["rx_antenna"] = 'RX2'
    sub_dict_receiver_info["rx_id"] = '336'
    sub_dict_receiver_info["rx_serial"] = '3168E23'
    sub_dict_receiver_info["rx_subdev_name"] = 'Magnesium'
    sub_dict_receiver_info["rx_subdev_spec"] = 'A:0 A:1 B:0 B:1'
    sub_dict_receiver["info"] = sub_dict_receiver_info
    sub_dict_receiver["iq_balance"] = ''
    sub_dict_receiver["lo_export"] = ''
    sub_dict_receiver["lo_offset"] = 0.0
    sub_dict_receiver["lo_source"] = ''
    sub_dict_receiver["otw_format"] = 'sc16' #
    sub_dict_receiver["stream_args"] = ''
    sub_dict_receiver["subdev"] = 'B:0'
    sub_dict_receiver["time_source"] = 'external'
    data_dict["receiver"] = sub_dict_receiver

    data_dict["sample_rate_denominator"] = 1
    data_dict["sample_rate_numerator"] = 25000000
    data_dict["uuid_str"] = 'a8012bf59eeb49d6a71fbfdcddf1efbb' #randomly chosen

    dmw.write(idx_arr, data_dict)
    print("Done writing")


    cfg.redis_instance.delete(f'{res_prefix}:real')
    cfg.redis_instance.delete(f'{res_prefix}:imag')
    cfg.redis_instance.delete(f'{res_prefix}:metadata')




    return 0


# @dash.callback(
#     dash.Output({'type': 'download-name-input', 'index': 0}, 'disabled'),
#     dash.Input('input-dir-button', 'n_clicks'),
# )
# def redis_update_download_data_button(n):
#     """
#     Let the user load the DRF data once they have chosen an input directory
#     """
#     if n < 1: return True

#     return False

















