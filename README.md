# RFSoC-Spectrum-Monitoring

![Project Image](https://www.rfsoc-pynq.io/images/01_rfsoc_2x2_t.png)
---

### Table of Contents



## Getting started

Install anaconda at https://anaconda.org/


Once installed, navigate directory of this repository in a command terminal, and run the following command to create the Anaconda environment for this project and to download the necessary packages:

```
conda env create -f environment.yaml
```

### Redis

A Redis server is necessary to run this application. Redis requires a UNIX machine. Downloading and installation instructions can be found here: https://redis.io/download.


To run the application, first start running redis in a terminal on any PC. This can be done with the command:
```
redis-server
```

### Board - Streaming data

Connect the board to a PC via USB and to the power. It also needs to be connected to the Internet: via a router or through a computer with an Ethernet cable.

To access the board, open a Jupyter notebook by browsing to http://192.168.3.1/lab on the PC connected to the board

Before running the notebook "simplestream.py" make sure that the IP address of the redis connection host (located in variable called 'r' of that file) matches the IP of the device in which the redis-server is running

### Back End - Digital RF static data

Run the back end in another terminal. There are two versions of the "back end", one which simulates a mock live stream, and one which handles and responds to requests for Digital RF data. 

The location of the redis server can be configured in ./back_end/config.yaml 

To run the Digital RF Handler:
```
conda activate rfsoc
python ./back_end/drf_back_end.py
```

To run the mock livestream:

```
conda activate rfsoc
python ./back_end/mock_stream.py
```

The first line activates the Anaconda environment we created earlier. 

### Front End

The location of the redis server as well as the host/port for the Dash application can be configured in in /front_end/config.yaml. Again, make sure that the IP address matches the one from the previous steps

Run the front end in a third terminal by navigating to the location of the repository and running the following steps (it can be on any PC, the one you want to display the data on):

```
conda activate rfsoc
python ./front_end/app.py
```

The front end will read the data from the Redis stream and display it in the Dash web application, which can be accessed in a web browser at http://127.0.0.1:8050/
.

## Software Overview

This project consists of three separate applications: the back end, the front end, and the board code. 

### ./back_end/

This folder contains all of the code for python back end of the project. This mostly contains code for processing Digital RF data to send to the front end. 

#### ./back_end/config.yaml

This is a YAML configuration file for the back end portion of the application. Currently, it contains the host/port values for the Redis server the application should connect to. 

#### ./back_end/digital_rf_utils.py

This file contains functions for reading DigitalRF data and converting it to frequency domain, which is necessary for displaying it on the spectrum graphs in the front end. It was originally modified from drf_plot.py from the DigitalRF library, which can be found [here](https://github.com/MITHaystack/digital_rf/blob/master/python/tools/drf_plot.py).


#### ./back_end/drf_back_end.py

This file contains the main entry point for running the back end to the Digital RF playback portion of the application. It contains code which waits for requests from the front end via the Redis server, and responds to them accordingly. It uses ./back_end/digital_rf_utils.py to convert the raw Digital RF data into spectrum data. 


#### ./back_end/mock_stream.py

This file contains code which simulates a live stream coming from a board. It simulates a live stream by reading in data coming from a stored Digital RF file, converts it to the frequency spectrum using ./back_end/digital_rf_utils.py, and outputs it into a Redis stream in a loop.


### ./front_end/

This folder contains all of the code for the Dash-based Web application part of this project.

#### ./front_end/app.py

This is the main program which runs the Dash application. This file contains code which handles initializing the Dash application, as well as some Dash components and callbacks necessary to the overall layout and function of the application, including the main graphs.

#### ./front_end/config.py

This file contains global variables which are used across the various front end files. It is a Python convention to name this kind of file "config.py". 

#### ./front_end/config.yaml

This is a YAML configuration file for the Dash application. Currently, it contains the host/port values for where the Dash application should be hosted, as well as the host/port values for the Redis server the Dash application should connect to.

#### ./front_end/drf_callbacks.py

This file contains Dash callbacks for the Digital RF playback portion of the web application.

#### ./front_end/drf_components.py

This file contains Dash components specific to the Digital RF playback portion of the web application.

#### ./front_end/shared_callbacks.py

This file contains Dash callbacks used in both the Digital RF playback and streaming portions of the web application.

#### ./front_end/shared_components.py

This file contains Dash components used in both the Digital RF playback and streaming portions of the web application.

#### ./front_end/specgram_graph.py

This file contains the Spectrogram class, which contains the logic for waterfall Spectrogram plot used in all portions of the web application. This file was originally modified from the Spectrogram class found in the StrathSDR RFSoC Spectrum Analyzer file sdr_plot.py (which can be found [here](https://github.com/strath-sdr/rfsoc_sam/blob/master/rfsoc_sam/sdr_plots.py)).

#### ./front_end/spectrum_analyzer.py

This file contains the Spectrum Analyzer class, which is a wrapper around the Spectrogram and Spectrum classes.

#### ./front_end/spectrum_graph.py

This file contains the Spectrum class, which contains the logic for Spectrum plot used in all portions of the web application. This file was originally modified from the Spectum class found in the StrathSDR RFSoC Spectrum Analyzer file sdr_plot.py (which can be found [here](https://github.com/strath-sdr/rfsoc_sam/blob/master/rfsoc_sam/sdr_plots.py)).

#### ./front_end/stream_callbacks.py

This file contains Dash callbacks for the streaming portion of the web application.

#### ./front_end/stream_components.py

This file contains Dash components specific to the streaming portion of the web application.

