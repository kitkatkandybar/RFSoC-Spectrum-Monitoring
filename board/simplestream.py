from pynq.overlays.base import BaseOverlay
base = BaseOverlay('base.bit')

base.init_rf_clks()

import redis
import numpy as np
import json
import time

def run_stream():
    """Set ups a redis connection and updates data to the stream."""
    streamname = 'example'
    r = redis.Redis(host='128.197.173.66', port=6379, db=0)
    
    number_samples = 1024
    cdata = []

    while True:

        cdata = base.radio.receiver.channel[0].transfer(number_samples)
        xreal=cdata[0].real
        xreal_json = json.dumps(xreal.tolist())
        r.xadd(streamname, {'data': xreal_json})
        ximag=cdata[0].imag
        ximag_json = json.dumps(ximag.tolist())
        r.xadd('example2', {'data': ximag_json})       
        
        print("Wrote to Redis")
        time.sleep(5)

if __name__ == '__main__':
    run_stream()

    
