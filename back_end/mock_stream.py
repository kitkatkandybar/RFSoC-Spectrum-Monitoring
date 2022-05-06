#!/usr/bin/env python
"""
"""
import re
import redis
import os.path
import yaml
import numpy as np
import json
import time
import argparse


from digital_rf_utils import *

r = None
p = None




def run_mock_live_stream(stream_name, file_path):
    print(f"Running mock stream with name {stream_name} using data from {file_path}")

    spec_datas = read_digital_rf_data(
        [file_path], plot_file=None, plot_type="spectrum", channel='discone',
                subchan=0, sfreq=0.0, cfreq=None, atime=0,
                start_sample=0, stop_sample=1000000, modulus=10000, integration=1, 
                zscale=(0, 0), bins=1024, log_scale=False, detrend=False,msl_code_length=0,
                msl_baud_length=0)

    print("Got frequency data from DigitalRF file...")
    y_max = max([max(d['data']) for d in spec_datas['data']])
    y_min = min([min(d['data']) for d in spec_datas['data']])
    spec_datas['metadata']['y_max']      = y_max
    spec_datas['metadata']['y_min']      = y_min

    # spec_datas['metadata']['n_samples']  = spec_datas['data'][0]['data'].shape[0]
    metadata = {
        'y_max':     y_max,
        'y_min':     y_min,
        'sfreq':     spec_datas['metadata']['sfreq'],
        'cfreq':     spec_datas['metadata']['cfreq'],
        'channel':   spec_datas['metadata']['channel'],
        'n_samples': spec_datas['data'][0]['data'].shape[0],
        'fft_size': 1024, 
        'decimation_factor': 2
    }

    print(f"Metdata: {metadata}")

    r.sadd("active_streams", stream_name)
    print(f"Setting metadata....")
    r.hset(f"metadata:{stream_name}", mapping=metadata)

    try:
        while True:
            for i in range(len(spec_datas['data'])):
                d = spec_datas['data'][i]['data']
                d = 10.0 * np.log10(d + 1e-12)
                r.xadd(f'stream:{stream_name}', {'data': json.dumps(d.tolist())}, maxlen=20000)
                if (i % 10 == 0):
                    print(f"Wrote data with index {i} to redis")
                time.sleep(0.05)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt..")
    finally:
        print("Shutting down...")
    
        r.srem("active_streams", stream_name)
        r.delete(f"metadata:{stream_name}")
        r.delete(f"stream:{stream_name}")






if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cfg', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml"), help='Config file for this application')
    parser.add_argument('--name', default="mock_stream1", help='name of stream')
    parser.add_argument('--file', default="C:/Users/yanag/openradar/openradar_antennas_wb_hf/", help='file to play back')

    args = parser.parse_args()
    with open(args.cfg, 'r') as f:
        cfg_data = yaml.safe_load(f)

    # initialize redis instance based on cfg params
    r = redis.Redis(host=cfg_data['redis']['host'], 
                    port=cfg_data['redis']['port'], 
                    password=cfg_data['redis']['password'],
                    db=0)
    p = r.pubsub(ignore_subscribe_messages=True)

    run_mock_live_stream(args.name, args.file)
