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

## Feature overviews

### Playing back Digital RF Data

This feature involves the Dash front end, the Redis server, as well as the back_end/drf_request_handler.py script. When the user selects a file in the Digital RF request form on the front end, it sends the appropriate requests to the drf_request_handler script through the Redis database. The drf_request_handler is continuously waiting for these requests. Once the drf_request_handler receives a request, it parses the request based on the Redis key and associated values, and responds accordingly. 

Most of the requests from the front end come have the key names "requests:{request id}:{type of request}", and their associated responses have the key name "responses:{request id}:{type of request}", with the same request id for both.

For every request, the front end obtains the request ID by atomically getting the current value in the Redis key 'request-id' and incrementing its value in the database for the next request. 

When a user enters a particular Digital RF path in the request form, the front end sends a request for the channels found within that Digital RF file. It does by publishing a request on the channel 'requests:{req_id}:channels' with file path as the data.  The front end then waits for a response on the stream 'responses:{req_id}:channels'.

Each time a user selects a given channel in the request form, the front end sends a request for the available sample range in the channel file on the redis channel 'requests:{req_id}:samples', and waits for a response on 'responses:{req_id}:samples'. 

Once a user has hit "load data" on the request form, the form should close. The front end sends along the request parameters on the channel 'requests:{req_id}:data'. It waits for the request metadata on 'responses:{req_id}:metadata'. Once the user hits the play button, it begins reading in data for the graph on 'responses:{req_id}:stream' at a regular interval. When this interval fires, the application reads in one data point at a time and outputs it onto the graphs. The application keeps track of the last-displayed data point via a redis key "{session_id}:last-drf-id". Every time the app gets a new data point, it updates this value with the redis ID of this datapoint, so the next time the interval fires it will get the next consecutive data point. The "session_id" value is defined per-user in front_end/app.py. When the user hits the "rewind" button, it sets the "{session_id}:last-drf-id" back to 0.

Most of this functionality is found in front_end/drf_callbacks.py.


### Live Streaming Data
This feature involves the Dash front end, the Redis server, as well as the board/stream.ipynb script, the last of which should be running on the RFSoC board.

The board denotes that it's available for streaming by adding its name to the "active_streams" set in Redis. It dumps its metadata into a Redis set called metadata:{stream_name}. It begins dumping spectrum data into a length-capped Redis stream named "stream:{stream_name}". 

On the front end, to check what boards are available, it checks the values in "active_streams". Once a user hits "play stream data" for a particular stream, the front end gets the metadata from metadata:{stream_name}, and begins reading data from "stream:{stream_name}" at a regular interval. The Dash Interval component called "stream-graph-interval" fires every 200 milliseconds, and when this happens, the front end gets the last datapoint in "stream:{stream_name}" and displays it on the dashboard graphs. This continues until the user hits "pause".  

Most of this functionality is found in front_end/stream_callbacks.py.

### Downloading data
This feature involves the Dash front end, the Redis server, as well as the board/download.ipynb script, the last of which should be running on the RFSoC board.

The board denotes that it's available for data-downloading by adding its name to the "active_command_boards" set in Redis. It then subscribes to all requests with channel names following the pattern "board-requests:{board_name}:\*" and waits for incoming requests. 

The front end sends a request to the board after a user fills out the download request form. It sends this request and its associated data on the channel board-requests:{board_name}:{req_id}'. Currently, the only parameter it sends it the duration of data to be downloaded.

Once the board gets this request, it records data for the appropriate duration of time and dumps the raw data in Redis. The board dumps the real part of its data in a stream called "board-responses:{board_name}:{req_id}:real", and the imaginary part in "board-responses:{board_name}:{req_id}:imag". It also adds metadta on "board-responses:{board_name}:{req_id}:metadata". When all of th data has been dumped, the board marks the request as complete on the channel "board-responses:{board_name}:{req_id}:complete". 

The front end gets the entire real and imaginary streams, creates a DigitalRF directory from them, zips the directory into a single .zip file, and then has the user's browser download it. 

Most of this functionality is found in front_end/stream_callbacks.py.


## Flow charts

### front_end/
<img width="960" alt="image" src="https://user-images.githubusercontent.com/90095970/164514863-944ff05e-b6c8-4229-a2fa-31d390a41d93.png">

### back_end/
<img width="757" alt="image" src="https://user-images.githubusercontent.com/90095970/164515508-1e2b1e9a-021a-45da-8d60-26df1d85b1a7.png">

### Component interactions
<img width="960" alt="image" src="https://user-images.githubusercontent.com/90095970/164515815-5505aee8-cee9-4f86-9069-38737345d7fb.png">

### Live streaming board data feature
<img width="443" alt="image" src="https://user-images.githubusercontent.com/90095970/165988906-b7b768fa-f46e-45d2-9234-01fc5df658e3.png">

### Downloading board data feature
<img width="464" alt="image" src="https://user-images.githubusercontent.com/90095970/165988843-c28daef3-027a-4a11-87a8-a6070f30b97c.png">


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


## Getting Started

Please refer to README.md for information on how to install the software for this project. 