import numpy as np
import spectrum_graph
from specgram_graph import Spectrogram
import matplotlib

import digital_rf


class SpectrumAnalyzer():

    def __init__(self,
                 sample_frequency = 4096e6,
                 update_frequency = 6,
                 centre_frequency = 0,
                 decimation_factor = 2,
                 nyquist_stopband = 1,
                 plot_width = 800,
                 plot_height = 400,
                 number_samples=None):
        self._spectrum_fftselector = 6

        self._sample_frequency = int(sample_frequency)
        self._number_samples   = int(2**(self._spectrum_fftselector+6))
        if number_samples is None:
          self._number_samples   = int(2**(self._spectrum_fftselector+6))
        else:
          self._number_samples = number_samples
        self._centre_frequency = centre_frequency
        self._nyquist_stopband = nyquist_stopband
        self._width            = plot_width
        self._height           = plot_height
        
 


        self.spec = spectrum_graph.Spectrum(
              plot_data=np.zeros((self._number_samples,), dtype=np.single),
              sample_frequency=self._sample_frequency,
              decimation_factor=2, # TODO what should this be
              number_samples=self._number_samples,
              centre_frequency=self._centre_frequency,
              nyquist_stopband=self._nyquist_stopband,
              xlabel='Frequency (Hz)',
              ylabel='Power Spectrum',
              plot_width=self._width,
              plot_height=self._height,
              display_mode=0,
              spectrum_mode=True)

     
        self.spectrogram = Spectrogram(sample_frequency=self._sample_frequency,
                                       centre_frequency=self._centre_frequency,
                                       nyquist_stopband=self._nyquist_stopband,
                                       # width=self._width,
                                       height=self._height,
                                       decimation_factor=2, # TODO what should this be

                                       plot_time=10)

        self.plot = self.spec.get_plot()

        self.spec.hide_data()


    @property
    def centre_frequency(self):
        """The centre frequency of the spectrum and spectrogram plots.
        """
        return self._centre_frequency
    
    @centre_frequency.setter
    def centre_frequency(self, centre_frequency):
        self._centre_frequency = centre_frequency
        self.spec.centre_frequency = centre_frequency
        self.spectrogram.centre_frequency = centre_frequency






class FunctionTimer():
    """A thread timer class for updating the spectrum analyser
    plots.
    
    Attributes:
    ----------
    update_frequency : The frequency in Hz that the timer updates
        the spectrum analyser plots.
    
    stopping : If true, the timer is in the process of halting,
        else false.
        
    stopped : If true, the timer has completely stopped, else
        false.
        
    """
    
    def __init__(self,
                 plot,
                 dma,
                 update_frequency):
        """Construct an instance of the thread timer class for
        spectrum analyser plot updates.
        """
        self._plot = plot
        self._time = float(1/update_frequency)
        self._dma = dma
        self.stopping = True
        self.stopped = True
        
    @property
    def update_frequency(self):
        """The frequency in Hz that the timer updates
        the spectrum analyser plots.
        """
        return float(1/self._time)
    
    @update_frequency.setter
    def update_frequency(self, update_frequency):
        self._time = float(1/update_frequency)
        
    def _do(self):
        """Perform the threading operation until the
        user calls the stop() method."""
        while not self.stopping:
            next_timer = time.time() + self._time
            data = self._dma.get_frame()
            if data.any():
                for plot in self._plot:
                    plot.data = data
            sleep_time = next_timer - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
        self.stopped = True
                
    def start(self):
        """Initiate the threading operation by setting
        stopping and stopped to False."""
        if self.stopping:
            self.stopping = False
            self.stopped = False
            thread = threading.Thread(target=self._do)
            thread.start()
            
    def stop(self):
        """Stop the threading operation, set stopping
        to true."""
        self.stopping = True