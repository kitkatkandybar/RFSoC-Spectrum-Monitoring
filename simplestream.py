#!/usr/bin/env python
"""
"""
import re
import redis
import numpy as np
import json
import time

from digital_rf_utils import *

r = redis.Redis(host='localhost', port=6379, db=0)
p = r.pubsub(ignore_subscribe_messages=True)

def make_data(nsamps=10000, mu=.5,sigma=1.):
    """Makes data and puts it into a serialized format"""
    x = np.sqrt(sigma)*np.random.rand(int(nsamps))-mu
    # Serialize the data into a json format. Can use different formats like arrow.
    x_json = json.dumps(x.tolist())
    return x_json

def run_stream():
    """Set ups a redis connection and updates data to the stream."""
    streamname = 'example'
    r = redis.Redis(host='localhost', port=6379, db=0)


    while True:
        x = make_data()
        r.xadd(streamname, {'data': x})
        print("Wrote to Redis")
        time.sleep(5)

def drf_requests_handler(msg):
    print(f'got message: {msg}')

    channel = msg['channel'].decode()
    # get id for request from channel name
    req_id = re.findall(r'\d+', channel)[0] 
    if 'channels' in channel:
        # user is requesting channels from drf file
        drf_path = msg['data'].decode()
        drf_channels = get_drf_channels(drf_path)

        print(f'sending: responses:{req_id}:channels, {json.dumps(drf_channels)}')
        r.publish(f'responses:{req_id}:channels', json.dumps(drf_channels))
    elif 'data' in channel:
        req_params = json.loads(msg['data'])
        print(f'got request for data: {req_params} ')

        try:
            spec_datas = read_digital_rf_data([req_params['drf_path']], plot_file=None, plot_type="spectrum", channel=req_params['channel'],
                subchan=0, sfreq=0.0, cfreq=None, atime=0,
                start_sample=int(req_params['start_sample']), stop_sample=int(req_params['stop_sample']), modulus=10000, integration=1, 
                zscale=(0, 0), bins=int(req_params['bins']), log_scale=False, detrend=False,msl_code_length=0,
                msl_baud_length=0)


            y_max = max([max(d['data']) for d in spec_datas['data']])
            y_min = min([min(d['data']) for d in spec_datas['data']])

            spec_datas['metadata']['y_max'] = y_max
            spec_datas['metadata']['y_min'] = y_min

            spec_datas['metadata']['n_samples']  = spec_datas['data'][0]['data'].shape[0]


            r.publish(f'responses:{req_id}:metadata', json.dumps(spec_datas['metadata']))


            for i in range(len(spec_datas['data'])):
                d = spec_datas['data'][i]['data']
                r.xadd(f'responses:{req_id}:stream', {'data': json.dumps(d.tolist())}, maxlen=1000)
                print("Wrote to Redis")
                time.sleep(0.05)


        except Exception as e:
            # output error message
            print(e)


def run_drf_stream():
    """Set ups a redis connection and updates data to the stream."""
    streamname = 'example'
    
    p.psubscribe(**{'requests:*': drf_requests_handler})

    drf_path = "C:/Users/yanag/openradar/openradar_antennas_wb_hf/"

    r.set('request-id', 0)

    while True:
        p.get_message()
        time.sleep(.01)

    # try:
    #     spec_datas = read_digital_rf_data([drf_path], plot_file=None, plot_type="spectrum", channel="discone",
    #         subchan=0, sfreq=0.0, cfreq=None, atime=0, start_sample=0, stop_sample=1000000, modulus=10000, integration=1, 
    #         zscale=(0, 0), bins=1024, log_scale=False, detrend=False,msl_code_length=0,
    #         msl_baud_length=0)


    #     y_max = max([max(d['data']) for d in spec_datas['data']])
    #     y_min = min([min(d['data']) for d in spec_datas['data']])

    #     spec_datas['metadata']['y_max'] = y_max


    #     r.set('metadata', json.dumps(spec_datas['metadata']))


    #     for i in range(len(spec_datas['data'])):
    #         d = spec_datas['data'][i]['data']
    #         r.xadd(streamname, {'data': json.dumps(d.tolist())}, maxlen=100)
    #         print("Wrote to Redis")
    #         time.sleep(0.1)



    # except Exception as e:
    #     # output error message
    #     print(e)

    
    




if __name__ == '__main__':
    run_drf_stream()
