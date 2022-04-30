# RFSoC-Spectrum-Monitoring

![Project Image](https://www.rfsoc-pynq.io/images/01_rfsoc_2x2_t.png)
---


## Overview

This repository for a web application capable of playing back, and interacting with Digital RF data, as well as tools for interacting with an RFSoC board, which includes live-streaming data as well as downloading data from the board in the DigitalRF format. 

There are four main components to the application:

(1) A [Dash](http://dash.plotly.com/)-based Web application - This is the front end of this app. It is the interface through which the user interacts with the application. 

(2) A Redis server - The Dash front end interactions with the RFSoC, as well as the Python back end, through the Redis server.

(3) A Python back-end script - This is housed under the back_end/ folder. It contains code responsible for processing Digital RF requests.

(4) Scripts running on the RFSoC - This is housed under the board/ folder.
 
Reports and presentations we made for the Senior Design course can be found under the reports/ folder. 

For information on the software portion of this project, including the setup, installation, and an overview of each module, please read the README_SOFTWARE.md file. 

For information on the hardware portion of this project, please read the README_HARDWARE.md file. 

This documentation structure was required by the course we created this project for, feel free to change it. 


## Getting started

First, clone this repository. This can be done by opening a terminal with git installed, and running

```
git clone https://github.com/kitkatkandybar/RFSoC-Spectrum-Monitoring.git
```

Next, install anaconda at https://anaconda.org/


Once installed, navigate directory of this repository in a command terminal, and run the following command to create the Anaconda environment for this project and to download the necessary packages:

```
conda env create -f environment.yaml
```

### Redis

A Redis server is necessary to run this application. Redis requires a UNIX machine. Downloading and installation instructions can be found here: https://redis.io/download.


To run the application, first start running redis in a terminal on any PC that has the repository code downloaded. From the top directory of the project (/RFSoC-Spectrum-Monitoring) execute the following command:
```
redis-server redis.conf
```
In case you want to change the password of the redis server, it would need to be changed on all three components of the set up: redis.conf file which sets up the server, /front_end/config.yaml file and in the file which will be executed in the board when creating the redis instance:

`r = redis.Redis(host='SERVER_IP', port=6379, db=0, password='NEW_PASSWORD')`

### Board - Streaming data

Connect the board to a PC via USB and to the power. It also needs to be connected to the Internet: via a router or through a computer with an Ethernet cable.

To access the board, open a Jupyter notebook by browsing to http://192.168.3.1/lab on the PC connected to the board.


To enable live streaming the board, copy over ./board/stream.ipynb onto the board and run all three cells. Before running the notebook, make sure that the IP address of the redis connection host (located in variable called 'r' of that file) matches the IP of the device in which the redis-server is running.

### Board - Downloading data

Connect the board to a PC via USB and to the power. It also needs to be connected to the Internet: via a router or through a computer with an Ethernet cable.

To access the board, open a Jupyter notebook by browsing to http://192.168.3.1/lab on the PC connected to the board.

To enable live streaming the board, copy over ./board/download.ipynb onto the board and run all three cells. Before running the notebook, make sure that the IP address of the redis connection host (located in variable called 'r' of that file) matches the IP of the device in which the redis-server is running.


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

The location of the redis server as well as the host/port for the Dash application can be configured in in /front_end/config.yaml. Again, make sure that the IP address matches the one from the previous steps.

Run the front end in a third terminal by navigating to the location of the repository and running the following steps (it can be on any PC, the one you want to display the data on):

```
conda activate rfsoc
python ./front_end/app.py
```

The front end will read the data from the Redis stream and display it in the Dash web application, which can be accessed in a web browser at http://127.0.0.1:8050/.


## Current State of the Project/Known Issues

- The Dash application was developed mostly by one undergraduate student as part of a single course. Please keep that in mind.
 
- The error handling for this application is not robust. Bugs and errors can and do happen, especially if you misclick or input some invalid values. The best way of dealing with an issue is to refresh the page, or restart any and all of the components involved (the Dash application, the back-end scripts, and so on).

- Sometimes, a Dash callback gets dropped, and as such the action involved does not get completed. This can lead to misaligned graph axes, a data point being missed on the graph, information not being populated, and so on. The fix for this is to just repeat the action again, or to refresh the page if the error is bad enough. We believe this is likely due to Dash throttling callbacks when the rate gets too high, but we are not sure, and have not found a consistent fix. 

- The "downloading data" portion of the project is the least well-developed feature. We were unable to find a way to pull large chunks of data from the board at a time. We currently pull data using the method `base.radio.receiver.channel[board_channel].transfer(number_samples)`, with `base` being an instance of the PYNQ `BaseOverlay` class. However, this function only lets you transfer a few tens of thousands of samples at a time, and takes about 200 msec to run, making it a poor candidate for downloading a large chunk of data (eg over 0.5 seconds). A better way of downloading data from the board should be investigated. 

- Currently, live streaming data from the board is entirely "passive". This means that the front end web application is not able to set any parameters for the board (center frequency, etc). These parameters are set by the board in the board/stream.ipynb script. The front end passively receives the data dumped by the board into the Redis server. 

- Sometimes the x-axis values (ie the frequency values) for the live streaming feature is not accurate. We are not exactly sure why. In ./front_end/stream_callbacks.py, in the function update_stream_metadata(), we set the "center frequency" to be 1/4 the sample frequency of the board. This usually results in accurate axis bounds, but not always. A more robust way of handling this should be found

- At the moment, downloading data from the board and live streaming board data require two different scripts for the board. This means that only one of these feature can be available at any given time, depending on which script is being run. In the future, it would be good to combine these features into a single script. 

- At this point in time, this project was developed and tested only handling one user at a time. Being able to process multiple users will likely involve having to restructure certain portions of the codebase. Specifically, the global variables found in front_end/config.py will have to be either cached or stored locally per-user for this application to work for multiple users. [This page](https://dash.plotly.com/sharing-data-between-callbacks) may provide ideas for how to make this work. The most difficult challenge will likely be to restructure the Spectrum and Spectrogram classes (or their corresponding data) to be stored/cached. 