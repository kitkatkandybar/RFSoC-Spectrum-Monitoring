#!/usr/bin/env python
"""
"""
import re
import os.path
import yaml
import redis
import numpy as np
import orjson # orjson should be faster than the default json library
import json
import time
import argparse
import traceback

from digital_rf_utils import *

r = None
p = None


expire_time = 600 # seconds after which the redis entry should be automatically deleted

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.longdouble):
            return float(obj)
        if isinstance(obj, np.int64):
            return int(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def drf_requests_handler(msg):
    print(f'Got message:\n\t{msg}\n')

    channel = msg['channel'].decode()
    # get id for request from channel name
    req_id = re.findall(r'\d+', channel)[0] 
    if 'channels' in channel:
        # user is requesting channels from drf file
        drf_path = msg['data'].decode()
        drf_channels = get_drf_channels(drf_path)

        print(f'Adding to stream responses:{req_id}:channels with data: {drf_channels}')
        r.xadd(f'responses:{req_id}:channels', {'data': orjson.dumps(drf_channels)})
        r.expire(f'responses:{req_id}:channels', expire_time)


    if 'samples' in channel:
        # user is requesting the number of samples in a drf channel
        d = orjson.loads(msg['data'])
        path = d['path']
        chan = d['channel']
        n_samples = get_n_samples(path, chan)

        print(f'Adding to stream responses:{req_id}:samples with data: {n_samples}')

        r.xadd(f'responses:{req_id}:samples', {'data': orjson.dumps(n_samples)})
        r.expire(f'responses:{req_id}:samples', expire_time)


    elif 'data' in channel:
        req_params = orjson.loads(msg['data'])
        print(f'Got request for data: {req_params} ')

        start_sample = int(req_params['start_sample'])
        stop_sample  = int(req_params['stop_sample'])
        modulus      = int(req_params['modulus'])
        integration  = int(req_params['integration'])
        bins         = int(req_params['bins'])
        filepath     = req_params['drf_path']
        drf_chan     = req_params['channel']




        r.delete(f'responses:{req_id}:stream')
        try:
            spec_datas = read_digital_rf_data([filepath], plot_file=None, plot_type="spectrum", channel=drf_chan,
                subchan=0, sfreq=0.0, cfreq=None, atime=0,
                start_sample=start_sample, stop_sample=stop_sample, modulus=modulus, integration=integration, 
                zscale=(0, 0), bins=bins, log_scale=False, detrend=False,msl_code_length=0,
                msl_baud_length=0)


            y_max = max([max(d['data']) for d in spec_datas['data']])
            y_min = min([min(d['data']) for d in spec_datas['data']])

            n_data_points = len(spec_datas['data'])

            req_params = {
                'filepath':     filepath,
                'channel':      drf_chan,
                'start_sample': start_sample,
                'stop_sample':  stop_sample,
                'modulus':      modulus,
                'integration':  integration,
                'bins':         bins,
                'n_points':     n_data_points,
            }


            spec_datas['metadata']['y_max']          = float(y_max)
            spec_datas['metadata']['y_min']          = float(y_min)
            spec_datas['metadata']['n_samples']      = spec_datas['data'][0]['data'].shape[0]
            spec_datas['metadata']['n_data_points']  = n_data_points
            spec_datas['metadata']['req_params']     = req_params


            print(f"Adding to stream responses:{req_id}:metadata with data:\n{spec_datas['metadata']}")
            r.xadd(f'responses:{req_id}:metadata', {'data': json.dumps(spec_datas['metadata'], cls=NumpyEncoder)})
            r.expire(f'responses:{req_id}:metadata', expire_time)


            print(f"Going to send {n_data_points} data points on stream responses:{req_id}:stream")
            for i in range(n_data_points):
                d = spec_datas['data'][i]['data']
                r.xadd(f'responses:{req_id}:stream', {'data': orjson.dumps(d.tolist())}, maxlen=100000)
                if (i % 50 == 0):
                    print(f"Finished writing data point #{i} on stream responses:{req_id}:stream")


            # send ending message
            r.xadd(f'responses:{req_id}:stream', {'data': orjson.dumps({'status': 'DONE'})}, maxlen=100000)
            r.expire(f'responses:{req_id}:stream', expire_time)

            print(f'Sent last message for responses:{req_id}:stream')
            

        except Exception as e:
            # output error message
            traceback.print_exc()
            print(e)


def run_drf_stream():
    """Set ups a redis connection and updates data to the stream."""
    
    # subscribe to all requests from the front end
    p.psubscribe(**{'requests:*': drf_requests_handler})

    r.set('request-id', 0)

    print("Waiting for incoming requests...")
    while True:
        p.get_message()
        time.sleep(.01)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cfg', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml"), help='Config file for this application')

    args = parser.parse_args()
    with open(args.cfg, 'r') as f:
        cfg_data = yaml.safe_load(f)

    # initialize redis instance based on cfg params
    print(f"Connecting to redis server at {cfg_data['redis']['host']}:{cfg_data['redis']['port']}...")
    r = redis.Redis(host=cfg_data['redis']['host'], port=cfg_data['redis']['port'], db=0)
    p = r.pubsub(ignore_subscribe_messages=True)

    run_drf_stream()
 