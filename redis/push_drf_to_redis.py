import time

import redis
import json

from digital_rf_utils import read_digital_rf_data



def push_drf_to_redis():
	"""Set ups a redis connection and updates data to the stream."""
	streamname = 'example'
	r = redis.Redis(host='localhost', port=6379, db=0)

	drf_path="C:/Users/yanag/openradar/openradar_antennas_wb_hf/"

	spec_datas = read_digital_rf_data([drf_path], plot_file=None, plot_type="spectrum", #channel="discone",
	        subchan=0, sfreq=0.0, cfreq=None, atime=0, start_sample=0, stop_sample=1000000, modulus=10000, integration=1, 
	        zscale=(0, 0), bins=1024, log_scale=False, detrend=False,msl_code_length=0,
	        msl_baud_length=0)


	metadata = json.dumps(spec_datas['metadata'])
	r.xadd('drf-metadata', {'data': metadata})


	for d in spec_datas['data']:
	    # x = make_data()
	    print(d['data'])
	    d = json.dumps(d['data'].tolist())
	    r.xadd(streamname, {'data': d})
	    print("Wrote to Redis")
	    time.sleep(5)




if __name__ == '__main__':
    push_drf_to_redis()
