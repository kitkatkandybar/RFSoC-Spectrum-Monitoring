"""
This file was modified from StrathSDR's sdr_plot.py Spectrogram class. It defines a plotly spectrogram waterfall plot

"""

import plotly.graph_objs as go
import numpy as np
from PIL import Image
from scipy import signal
import matplotlib.pyplot as plt


class Spectrogram():
    """
    

    """
    def __init__(self,
                 width=800,
                 height=400,
                 image_width=400,
                 image_height=200,
                 centre_frequency=0,
                 sample_frequency=4096e6,
                 decimation_factor=2,
                 nyquist_stopband=1,
                 ypixel=2,
                 plot_time=20,
                 zlabel='Power (dB)',
                 zmin=-80,
                 zmax=0,
                 cmap='jet'):
        
        self._width             = width
        self._height            = height
        self._image_width       = image_width
        self._image_height      = image_height
        self._sample_frequency  = sample_frequency
        self._decimation_factor = decimation_factor
        self._centre_frequency  = centre_frequency
        self._nyquist_stopband  = nyquist_stopband
        self._ypixel            = ypixel
        self._data              = np.ones((self._image_height, self._image_width, 3), dtype=np.uint8)*128
        self._data_status       = False
        self._cmap               = cmap
        self._zlabel = zlabel

        
        # the data of this plot is represented as a background image
        self._image_x = -(self._sample_frequency/self._decimation_factor)/2 + self._centre_frequency
        self._image_y = 0
        self._lower_limit = (-(self._sample_frequency/self._decimation_factor)/2) * \
            self._nyquist_stopband + self._centre_frequency
        self._upper_limit = ((self._sample_frequency/self._decimation_factor)/2) * \
            self._nyquist_stopband + self._centre_frequency
        
        self._plot_time = self._image_height
        self._zmin = zmin
        self._zmax = zmax
        # self.enable_updates = False
        self.enable_updates = True

        cm = plt.get_cmap(self.cmap)
        cm = self.matplotlib_to_plotly(cm, 255)

        # dummy trace needed to add color bar to plot
        self.dummy_trace = {
            'x': [None],
            'y': [None],
            'mode': 'markers',
            'marker': {
                'colorscale': cm,
                'cmin': self._zmin,
                'cmax': self._zmax,
                'showscale':True,
                'colorbar': {
                    'thickness':20,
                    'title': {'text': self._zlabel},
                    
                },
            }
        }


        self._plot = go.FigureWidget(data=[self.dummy_trace], layout={
            'height': self._height,
            'width' : self._width,
            'yaxis' : {
                'showgrid' : False,
                'range' : [-self._plot_time, 0],
                'autorange' : False,
                'title' : 'Frame Number',
                'showticklabels' : True,
                'visible' : True
            },
            'xaxis' : {
                'zeroline':   False,
                'showgrid' :  False,
                'range' :    [self._lower_limit, self._upper_limit],
                'autorange' : False,
                'title' :    'Frequency (Hz)',
            },
            'margin' : {
                't':25,
                'b':25,
                'l':25,
                'r':25,},

        })
        
        img = Image.fromarray(self._data, 'RGB')
        self._plot.add_layout_image(
            dict(
                source=img,
                xref="x",
                yref="y",
                x=self._image_x,
                y=self._image_y,
                sizex=(self._sample_frequency/self._decimation_factor),
                sizey=self._plot_time,
                sizing='stretch',
                opacity=1,
                layer="below",
                )
        )

        # self._plot.add_trace(go.Histogram2d(
        #     x=self._data[:,:,0],
        #     y=self_data[:,:,1],
        #     colorscale='YlGnBu',
        #     zmax=10,
        #     nbinsx=14,
        #     nbinsy=14,
        #     zauto=False,
        # ))
        
        
        self._update_image()


    # Taken from https://stackoverflow.com/questions/55447131/how-to-add-a-colorbar-to-an-already-existing-plotly-figure
    def matplotlib_to_plotly(self,cmap, pl_entries):
        h = 1.0/(pl_entries-1)
        pl_colorscale = []

        for k in range(pl_entries):
            C = list(map(np.uint8, np.array(cmap(k*h)[:3])*255))
            pl_colorscale.append([k*h, 'rgb'+str((C[0], C[1], C[2]))])

        return pl_colorscale
            
    @property
    def template(self):
        return self._plot.layout.template
    
    @template.setter
    def template(self, template):
        self._plot.layout.template = template
        
    @property
    def data(self):
        return self._data[0][:]
    
    @data.setter
    def data(self, data):
        if self.enable_updates:
            self._data_status = True
            # value = np.fft.fftshift(data) # FFT Shift

            value = data
            value = np.array(np.interp(value, (self.zmin, self.zmax), (0, 1)), dtype=np.single) # Scale Z-Axis
            value = np.resize(signal.resample(value, self._image_width), (1, self._image_width)) # Resample X-Axis
            value = np.repeat(value, self._ypixel, 0) # Repeat Y-Axis
            cm    = plt.get_cmap(self._cmap)
            value = cm(value)
            self._data = np.roll(self._data, self._ypixel, 0) # Roll data
            self._data[0:self._ypixel, :, :] = (value[:, :, :3]*255).astype(np.uint8) # Update first line
            img = Image.fromarray(self._data, 'RGB') # Create image
            self._plot.update_layout_images({'source' : img}) # Set as background
            self._data_status = False

    @property
    def ypixel(self):
        return self._ypixel
    
    @ypixel.setter
    def ypixel(self, ypixel):
        if self.enable_updates:
            self.enable_updates = False
            while self._data_status:
                pass
            self._ypixel = ypixel
            self.enable_updates = True
        else:
            self._ypixel = ypixel
        
    @property
    def sample_frequency(self):
        return self._sample_frequency
    
    @sample_frequency.setter
    def sample_frequency(self, sample_frequency):
        self._sample_frequency = sample_frequency
        self._update_image()
        
    @property
    def decimation_factor(self):
        return self._decimation_factor
    
    @decimation_factor.setter
    def decimation_factor(self, decimation_factor):
        self._decimation_factor = decimation_factor
        self._update_image()
        
    @property
    def nyquist_stopband(self):
        return self._nyquist_stopband
    
    @nyquist_stopband.setter
    def nyquist_stopband(self, nyquist_stopband):
        self._nyquist_stopband = nyquist_stopband
        self._update_image()
        
    @property
    def centre_frequency(self):
        return self._centre_frequency
    
    @centre_frequency.setter
    def centre_frequency(self, centre_frequency):
        self._centre_frequency = centre_frequency
        self._update_image()

    @property
    def width(self):
        return self._plot.layout.width
    
    @width.setter
    def width(self, width):
        self._plot.layout.width = width

    @property
    def height(self):
        return self._plot.layout.height
    
    @height.setter
    def height(self, height):
        self._plot.layout.height = height

    @property
    def cmap(self):
        return self._cmap
    
    @cmap.setter
    def cmap(self, cmap):
        self._cmap = cmap
        cm = plt.get_cmap(cmap)
        cm = self.matplotlib_to_plotly(cm, 255)

        self._plot.update_traces(
            {'marker': {
                'colorscale': cm
                }
            }
        )

    @property
    def quality(self):
        return int(101-self._ypixel)
    
    @quality.setter
    def quality(self, quality):
        if quality in range(80, 101):
            self._ypixel = int(101-quality)
            self._plot_time = np.ceil(self._image_height/self._ypixel)
            self._plot.update_layout({'yaxis': {
                'range' : [-self._plot_time, 0]
            }})
            self._plot.update_layout_images({'sizey' : self._plot_time})
            self._update_image()

    @property
    def zlabel(self):
        return self._zlabel
        
    @zlabel.setter
    def zlabel(self, zlabel):
        self._zlabel = zlabel
        self._plot.update_traces(
            {'marker': {
                'colorbar': {
                    'title': {'text': zlabel},
            }}}
        )
        
    @property
    def zmin(self):
        return self._zmin
        
    @zmin.setter
    def zmin(self, zmin):
        self._zmin = zmin
        self._plot.update_traces(
            {'marker': {
               'cmin': self._zmin,
            }}
        )   
        

    @property
    def zmax(self):
        return self._zmax
        
    @zmax.setter
    def zmax(self, zmax):
        self._zmax = zmax
        self._plot.update_traces(
            {'marker': {
               'cmax': self._zmax,
            }}
        )   

    def clear_data(self):
        self._data = np.ones((self._image_height, self._image_width, 3), dtype=np.uint8)*128


    def _update_image(self):
        self._lower_limit = (-(self._sample_frequency/self._decimation_factor)/2) * self._nyquist_stopband + self._centre_frequency 
        self._upper_limit = ((self._sample_frequency/self._decimation_factor)/2) * self._nyquist_stopband + self._centre_frequency
        self._image_x = -(self._sample_frequency/self._decimation_factor)/2 + self._centre_frequency
        self._plot.update_layout({'xaxis': {
            'range' : [self._lower_limit ,self._upper_limit]
        }})
        self._data = np.ones((self._image_height, self._image_width, 3), dtype=np.uint8)*128
        img = Image.fromarray(self._data, 'RGB')
        self._plot.update_layout_images({'source' : img,
                                         'x' : self._image_x,
                                         'sizex' : (self._sample_frequency/self._decimation_factor)})

    def get_plot(self):
        return self._plot


    def __str__(self):
        s = f"y_data: {self.data}\n" + \
            f"sample_frequency: {self._sample_frequency }\n" + \
            f"decimation_factor: {self.decimation_factor}\n" + \
            f"centre_frequency: {self.centre_frequency}\n" + \
            f"upper limit: {self._upper_limit}\n" + \
            f"lower limit: {self._lower_limit}\n" + \
            f"nyquist_stopband: {self.nyquist_stopband}"
            
        

        return s