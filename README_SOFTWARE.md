# Software Overview

This project consists of three separate applications: the back end, the front end, and the board code. 

## Module Descriptions

### ./back_end/

This folder contains all of the code for python back end of the project. This mostly contains code for processing Digital RF data to send to the front end. 

- **config.yaml**
	- This is a YAML configuration file for the back end portion of the application. Currently, it contains the host/port values for the Redis server the application should connect to. 

- **digital_rf_utils.py**
	- This file contains functions for reading DigitalRF data and converting it to frequency domain, which is necessary for displaying it on the spectrum graphs in the front end. It was originally modified from drf_plot.py from the DigitalRF library, which can be found [here](https://github.com/MITHaystack/digital_rf/blob/master/python/tools/drf_plot.py).

- **drf_request_handler.py**
	- This file contains the main entry point for running the back end to the Digital RF playback portion of the application. It contains code which waits for requests from the front end via the Redis server, and responds to them accordingly. It uses ./back_end/digital_rf_utils.py to convert the raw Digital RF data into spectrum data. 

- **mock_stream.py**
	- This file contains code which simulates a live stream coming from a board. It exists for testing and debugging purposes.  It simulates a live stream by reading in data coming from a stored Digital RF file, converts it to the frequency spectrum using ./back_end/digital_rf_utils.py, and outputs it into a Redis stream in a loop.

### ./front_end/

This folder contains all of the code for the Dash-based Web application part of this project.

- **app.py**
	- This is the main program which runs the Dash application. This file contains code which handles initializing the Dash application, as well as some Dash components and callbacks necessary to the overall layout and function of the application, including the main graphs. You should run this script to run the Dash application. 

- **config.py**
	- This file contains global variables which are used across the various front end files. It is a Python convention to name this kind of file "config.py". 

- **config.yaml**
	- This is a YAML configuration file for the Dash application. Currently, it contains the host/port values for where the Dash application should be hosted, as well as the host/port values for the Redis server the Dash application should connect to.

- **drf_callbacks.py**
	- This file contains Dash callbacks for the Digital RF playback portion of the web application. This includes the logic for the DigitalRF playback request form, sending requests and receiving data to and from the back end via the Redis Server, and populating the necessary information on the sidebar. 

- **drf_components.py**
	- This file contains Dash components specific to the Digital RF playback portion of the web application. This includes the components necessary for populating the sidebar options, including all of the accordion tabs, the DigitalRF playback request form, and so on.

- **shared_callbacks.py**
	- This file contains Dash callbacks used in both the Digital RF playback and streaming portions of the web application.

- **shared_components.py**
	- This file contains Dash components used in both the Digital RF playback and streaming portions of the web application. This includes the components necessary for populating the sidebar options, including all of the accordion tabs, the data download request form, and so on.

- **specgram_graph.py**
	- This file contains the Spectrogram class, which contains the logic for waterfall Spectrogram plot used in all portions of the web application. This file was originally modified from the Spectrogram class found in the StrathSDR RFSoC Spectrum Analyzer file sdr_plot.py (which can be found [here](https://github.com/strath-sdr/rfsoc_sam/blob/master/rfsoc_sam/sdr_plots.py)).

- **spectrum_analyzer.py**
	- This file contains the Spectrum Analyzer class, which is a wrapper around the Spectrogram and Spectrum classes. This file was originally modified from the SpectrumAnalyzer class found in the StrathSDR RFSoC Spectrum Analyzer file spectrum_analyser.py (which can be found [here](https://github.com/strath-sdr/rfsoc_sam/blob/master/rfsoc_sam/spectrum_analyser.py)).

- **spectrum_graph.py**
	- This file contains the Spectrum class, which contains the logic for Spectrum plot used in all portions of the web application. This file was originally modified from the Spectum class found in the StrathSDR RFSoC Spectrum Analyzer file sdr_plot.py (which can be found [here](https://github.com/strath-sdr/rfsoc_sam/blob/master/rfsoc_sam/sdr_plots.py)).

- **stream_callbacks.py**
	- This file contains Dash callbacks for the streaming portion of the web application.

- **stream_components.py**
	- This file contains Dash components specific to the streaming portion of the web application.

## ./board/

This folder contains Jupter Notebook files written for the RFSoC board for this project.

- **download.ipynb**
	- This file contains the Jupyter Notebook for the "downloading data" feature of the application. When this script is running, the board waits for a request to come into the Redis server, pulls raw data according to the request, and then dumps the data into the Redis server for the front end to handle. 

- **stream.ipynb**
	- This file contains the Jupyter Notebook for the live streaming feature of the application. When this script is running, at a regular interval, raw data from the board is converted into spectrum data using FFTs, and then dumped into Redis server for the front end to handle.  

## Flow charts

### front_end/
<img width="960" alt="image" src="https://user-images.githubusercontent.com/90095970/164514863-944ff05e-b6c8-4229-a2fa-31d390a41d93.png">

### back_end/
<img width="757" alt="image" src="https://user-images.githubusercontent.com/90095970/164515508-1e2b1e9a-021a-45da-8d60-26df1d85b1a7.png">

### Component interactions
<img width="960" alt="image" src="https://user-images.githubusercontent.com/90095970/164515815-5505aee8-cee9-4f86-9069-38737345d7fb.png">

## Dev/Build information

This project was tested using the following package versions on PC running Windows 11:

- python                    3.9.7
- dash                      2.0.0      
- dash-bootstrap-components 1.0.1      
- dash-core-components      2.0.0      
- dash-html-components      2.0.0
- digital_rf                2.6.7
- matplotlib                3.4.3
- numpy                     1.21.2
- orjson                    3.6.7
- pyyaml                    6.0
- redis                     3.5.3
- scipy                     1.7.1

The Dash application has been tested running on a Windows PC as well as a Mac computer. 
