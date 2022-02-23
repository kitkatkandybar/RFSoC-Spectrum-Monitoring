"""
"""
import numpy as np
import redis
import json
import matplotlib.pyplot as plt

def main():
    streamname = 'example'
    r = redis.Redis(host='localhost', port=6379, db=0)

    rstrm = r.xread({streamname: '$'}, None, 0)

    xlist = json.loads(rstrm[0][1][0][1][b'data'])
    x = np.array(xlist)
    HIST_BINS = np.linspace(-2, 2, 200)
    n, _ = np.histogram(x, HIST_BINS,density=True)
    fig, ax1 = plt.subplots(nrows=1)
    line1 = ax1.plot(HIST_BINS[:-1],n/n.max())[0]
    line2 = ax1.plot(HIST_BINS[:-1],n/n.max())[0]
    x_accume = x+0
    ncount =0
    plt.ion()
    for i in range(1000):
        rstrm = r.xread({streamname: '$'}, None, 0)

        xlist = json.loads(rstrm[0][1][0][1][b'data'])
        xnew = np.array(xlist)
        if np.all(np.isclose(xnew,x)):
            continue

        ncount += 1
        x_accume += xnew
        x = xnew
        n, _ = np.histogram(x_accume/ncount, HIST_BINS,density=True)
        line2.set_data(HIST_BINS[:-1],n/n.max())
        plt.pause(0.1)
    plt.ioff()
    plt.show()

if __name__ == '__main__':
    main()
