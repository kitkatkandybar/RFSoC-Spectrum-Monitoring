import dash
from dash import dcc
from dash import html

import time

import json

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




@dash.callback(
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

    req_id = cfg.redis_instance.get('request-id').decode()
    cfg.redis_instance.incr('request-id')

    cfg.pubsub.psubscribe(f'responses:{req_id}:*')

    req = {
        'drf_path'     : drf_path,
        'channel'      : channel[0],
        'start_sample' : sample_range[0][0],
        'stop_sample'  : sample_range[0][1],
        'bins'         : 2**bins[0]

    }

    cfg.redis_instance.publish(f'requests:{req_id}:data', json.dumps(req))

    for msg in cfg.pubsub.listen():
        print(f"got response message: {msg}")
        channel = msg['channel'].decode()
        if 'metadata' in channel:
            metadata = json.loads(msg['data'])
            print(f'got metadata from redis: {metadata}')

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


            cfg.sa.spec.sample_frequency        = sfreq
            cfg.sa.spectrogram.sample_frequency = sfreq
            cfg.sa.spec.number_samples          = n_samples
            cfg.sa.spectrogram.number_samples   = n_samples
            cfg.sa.spec.show_data()

            # global cfg.data_queue
            cfg.data_queue = []
            # global cfg.data_q_idx
            cfg.data_q_idx = 0
            break

    last_r_id = None
    finished = False
    while not finished:
        time.sleep(0.1)
        if last_r_id is None:
            rstrm = cfg.redis_instance.xrange(f'responses:{req_id}:stream')
        else:
            rstrm = cfg.redis_instance.xrange(f'responses:{req_id}:stream', min=f'({last_r_id}')

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
                    cfg.pubsub.punsubscribe(f'responses:{req_id}:*')
                    print(f"FINISHED READING ALL DATA FROM REQUEST: {req_id}")
                    break
            else:
                cfg.data_queue.append(datum)

    print(f"data queue len: {len(cfg.data_queue)}")

    stream_len = cfg.redis_instance.xlen(f'responses:{req_id}:stream')
    print(f"LENGTH OF STREAM: {stream_len}")

    return None




@dash.callback(
    dash.Output(component_id='metadata-output', component_property='children'),
    dash.Input('graph-interval', 'max_intervals'),
)
def update_metadeta_output(n):
    """
    update metadata section when new Digital RF data is loaded
    The 'max-intervals' value gets updated when metadata is loaded
    """
    if cfg.spec_datas is None:
        return None

    children = [
        html.H4("Metadata:"),
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
    # if (n % 2) == 1:
    print("clicked input dir button")
    if n > 0:
        print("clicked redis button")
        req_id = cfg.redis_instance.get('request-id').decode()
        cfg.redis_instance.incr('request-id')
        

        cfg.pubsub.subscribe(f'responses:{req_id}:channels')

        print(f"publishing request {req_id} for {drf_path}")
        # make a request for the channels from drf_path
        cfg.redis_instance.publish(f'requests:{req_id}:channels', drf_path)

        for msg in cfg.pubsub.listen():
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

                cfg.pubsub.unsubscribe(f'responses:{req_id}:channels')

                return children


    
        # global redis_data
        # for drf files, we want to push all data we haven't into a queue which gets outputted
        redis_data = []


        return None

    return None


@dash.callback(
    dash.Output(component_id='load-val', component_property='disabled'),
    dash.Input('input-dir-button', 'n_clicks'),
)
def redis_update_load_data_button(n):
    if n < 1: return True

    return False

@dash.callback(
    dash.Output(component_id='reset-val', component_property='disabled'),
    dash.Input('load-val', 'n_clicks'),
)
def enable_replay_data_button(n):
    if n < 1: return True

    return False

@dash.callback(
    dash.Output('reading-stream-graph-interval-placeholder', 'n_clicks'),
    dash.Input('load-val', 'n_clicks'))
def enable_graph_interval_after_clicking_load(n_clicks):
    if n_clicks < 1:
        return 0

    return 1




@dash.callback(
    dash.Output('reset-button-graph-interval-placeholder', 'n_clicks'),
    dash.Input('reset-val', 'n_clicks'),
)
def handle_reset_button(n_clicks):
    if n_clicks < 1:
        return 0

    # global cfg.data_q_idx
    cfg.data_q_idx = 0

    cfg.sa.spectrogram.clear_data()

    return 1
