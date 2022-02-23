# README
This is a really simple example using redis to stream data and update a plot. The overall code is an example of the Central limit theorem using uniformly distributed samples and averaging them together.

Make sure redis is installed. This can be done using conda

```bash
conda install redis
```

After redis  is installed you will need open up three windows, two to run the scripts and another to have a redis server run. If you're on Linux you may already have a redis server running.

First start a redis server in your first open terminal

 ```bash
 redis-server
 ```

 This will take up the entire terminal. Now in another open terminal run the stream script. This will be analogous to a radio making data samples.

 ```bash
 python simplestream.py
 ```

 In the last terminal run another script. This is like the dashboard.

 ```bash
 python clientexample.py
 ```
