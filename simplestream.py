#!/usr/bin/env python
"""
"""
import redis
import numpy as np
import json
import time

def set_transmitter_channel(channel, enable, gain, frequency):
    channel.control.enable = enable
    channel.control.gain = gain
    channel.dac_block.MixerSettings['Freq'] = frequency
    

def run_stream():
    """Set ups a redis connection and updates data to the stream."""
    streamname = 'example'
    #r = redis.Redis(host='128.197.173.66', port=6379, db=0)
    r = redis.Redis(host='168.122.1.151', port=6379, db=0)
    stream_name="bu_rfsoc"
    
    number_samples = 1024
    
    channel = 0
    window = np.array(np.blackman(number_samples)[:]) #take window from data
    fc=base.radio.transmitter.channel[channel].dac_block.MixerSettings['Freq']*1e6
    print(f'{fc}')
    print(base.radio.transmitter.channel)
    fs=base.radio.transmitter.channel[channel].dac_block.BlockStatus['SamplingFreq']*1e9
        
    r.sadd("active_streams", stream_name)
    
    #set_transmitter_channel(base.radio.transmitter.channel[1], True, 0.8,  500)
    #fc=base.radio.transmitter.channel[1].dac_block.MixerSettings['Freq']*1e6

    r.delete(f"stream:{stream_name}")

    try:
        while True:
            
            metadata = {
                'sfreq': fs,'y_max': 100,
                'y_min':0,
                'n_samples':n
                'cfreq': fc,
                'channel': channel,
                umber_samples
            }
            
            r.hset(f"metadata:{stream_name}", mapping=metadata)

                
            cdata = base.radio.receiver.channel[channel].transfer(number_samples) #get complex data from ADCs

           # for (i in range(0, len(base.radio.receiver.channel) - 1)):
           #     wdata.append(cdata[i]*window)
            wdata=cdata*window


          #  for (i in range(0, len(base.radio.receiver.channel) - 1)): #apply FFT to window
           #     fdata.append(np.fft.fftshift(np.fft.fft(wdata[i])))
            fdata=abs(np.fft.fftshift(np.fft.fft(wdata)))
            print(f'{type(fdata)}')

            #fdata_array = np.array(abs(fdata))

            x_json = json.dumps(fdata.tolist())
            r.xadd(f"stream:{stream_name}", {'data': x_json}, maxlen=10000)
                        
            time.sleep(1)
    finally:
        print("ENTER FINALLY")
        r.srem("active_streams", stream_name)
        r.delete(f"metadata:{stream_name}")
        r.delete(f"stream:{stream_name}")
        
if __name__ == '__main__':
    run_stream()
