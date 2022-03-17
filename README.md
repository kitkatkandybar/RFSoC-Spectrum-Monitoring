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


To run the application, first start running redis in a terminal. This can be done with the command:
```
redis-server
```

### Back End

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

The location of the redis server as well as the host/port for the Dash application canh be configured in in /front_end/config.py

Run the front end in a third terminal by navigating to the location of the repository and running the following steps:

```
conda activate rfsoc
python ./front_end/app.py
```


Finally, open the application in a web browser at http://127.0.0.1:8050/ .