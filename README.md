# RFSoC-Spectrum-Monitoring

![Project Image](https://www.rfsoc-pynq.io/images/01_rfsoc_2x2_t.png)
---


## Overview

This repository for a web application capable of playing back, and interacting with Digital RF data, as well as tools for interacting with an RFSoC board, which includes live-streaming data as well as downloading data from the board in the DigitalRF format. 

There are four main components to the application:

(1) A [Dash](http://dash.plotly.com/)-based Web application - This is the front end of this app. It is the interface which 

(2) A Redis server - The Dash front end interactions with the RFSoC, as well as the Python back end, through the Redis server.

(3) A Python back-end script - This is housed under the back_end/ folder. It contains code responsible for processing Digital RF requests.

(4) Scripts running on the RFSoC - This is housed under the board/ folder.


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

The front end will read the data from the Redis stream and display it in the Dash web application, which can be accessed in a web browser at http://127.0.0.1:8050/.




## Current State of the Project

- At this point in time, this project was developed and tested only handlng one user at a time. Being able to process multiple users will likely involve having to restructure certain portions of the codebase. Specifically, the global variables found in front_end/config.py will have to be either cached or stored locally per-user for this application to work for multiple users. [This page](https://dash.plotly.com/sharing-data-between-callbacks) may provide ideas for how to make this work. The most difficult challenge will likely be to restructure the Spectrum and Spectrogram classes (or their corresponding data) to be stored/cached. 
 


### Known issues

- The Dash application was developed mostly by one undergraduate student as part of a single course. Please keep that in mind.

- The error handling for this application is not robust. Bugs and errors can and do happen, especially if you misclick or input some invalid values. The best way of dealing with an issue is to refresh the page, or restart any and all of the components involved (the Dash application, the back-end scripts, and so on).

- Sometimes, a Dash callback gets dropped, and as such the action involved does not get completed. This can lead to misaligned graph axes, a data point being missed on the graph, information not being populated, and so on. The fix for this is to just repeat the action again, or to refresh the page if the error is bad enough. We believe this is likely due to Dash throttling callbacks when the rate gets too high, but we are not sure, and have not found a consistent fix. 

- The Redis server currently is running with "protected-mode" off, this should be changed


### Ideas for further improvement


## More information

For more information on the software component of this project, please read README_SOFTWARE.md. For more information on the hardware component of this project, please read README_HARDWARE.md. 