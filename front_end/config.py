from spectrum_analyzer import SpectrumAnalyzer
import redis


# specify some global data needed for various parts of the dashboard
# TODO: Make these into non-global variables

data_queue = []
data_q_idx = 0
sa         = SpectrumAnalyzer()
spec_datas = None

redis_instance = redis.Redis(host='localhost', port=6379, db=0)
pubsub = redis_instance.pubsub(ignore_subscribe_messages=True)
