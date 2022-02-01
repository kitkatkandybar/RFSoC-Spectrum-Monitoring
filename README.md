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

Run the back end in another terminal. This can by navigating to the location of the repository and running the following steps:

```
conda activate rfsoc
python ./back_end/redis_back_end.py
```

The first line activates the Anaconda environment we created earlier. 



Run the front end in a third terminal by navigating to the location of the repository and running the following steps:
```
conda activate rfsoc
python ./front_end/app.py
```


Finally, open the application in a web browser at http://127.0.0.1:8050/ .