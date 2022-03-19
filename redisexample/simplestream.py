#!/usr/bin/env python
"""
"""
import redis
import numpy as np
import json
import time
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
if __name__ == '__main__':
    run_stream()
