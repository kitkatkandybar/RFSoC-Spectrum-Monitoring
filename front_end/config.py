from spectrum_analyzer import SpectrumAnalyzer

# specify some global data needed for various parts of the dashboard
# TODO: Make these into non-global variables

sa             = SpectrumAnalyzer()
spec_datas     = None
redis_instance = None

# the seconds after which to delete redis keys
expire_time    = 3600
