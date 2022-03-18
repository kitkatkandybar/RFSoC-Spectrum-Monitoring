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

