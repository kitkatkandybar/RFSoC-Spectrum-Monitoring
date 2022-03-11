from spectrum_analyzer import SpectrumAnalyzer
import redis

from collections import deque


# specify some global data needed for various parts of the dashboard
# TODO: Make these into non-global variables

sa         = SpectrumAnalyzer()
spec_datas = None

stream_data_q = deque([], maxlen=10000)
stream_last_id = -1

redis_instance = None
pubsub = None
