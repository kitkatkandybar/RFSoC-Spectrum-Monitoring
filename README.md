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

A Redis server is necessary to run this application. Redis requires a UNIX machine. Downloading and installation instructions can be found here: https://redis.io/download.


To run the application, first start running redis in a terminal. This can be done with the command:
```
redis-server
```

The board has to be connected to a PC via USB and to the power. It also needs to be connected to the Internet: via a router or a computer with an Ethernet cable.
To access the board and open JupyterLab, on the computer connected to the board browse to http://192.168.3.1/lab 
Run the iPython Notebook called "simplestream.py"

Make sure that the IP addresses of the receiver and the sender of the data (front_end/config.py and simplestream.py) match the IP of the device in which the redis-server is running


Run the front end in another terminal by navigating to the location of the repository and running the following steps:

```
conda activate rfsoc
python ./front_end/app.py
```
The first line activates the Anaconda environment we created earlier. 
The front end will read the data from the Redis stream and display it in the Dash web application, which can be accessed in a web browser at http://127.0.0.1:8050/
