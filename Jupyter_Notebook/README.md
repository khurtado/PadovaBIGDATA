# Jupyter Notebook

The Jupyter Notebook is an open-source web application that allows you to create and share documents that contain live code, equations, visualizations and narrative text. Uses include: data cleaning and transformation, numerical simulation, statistical modeling, data visualization, machine learning, and much more.

## Working sparks in Jupyter notebook

### Working in Padova department of physics

You need to setup a SSH tunnel with:

```
ssh -L localhost:1234:localhost:1234 shoh@10.64.22.66
```

Pick a port number , example 1234 and change to your username. While logged in, execute

```
jupyter notebook --no-browser --port=1234 --ip=127.0.0.1
```

The authentication token will be revealed as an URL, copy and paste it in your browser. To shutdown the kernal, simply issue CTRL-C to the termimal.

### Working remotely

You need to setup a double SSH tunnel with:

```
ssh -L 1234:localhost:1234 hoh@gate.pd.infn.it 
```

Pick a port number, example 1234 and change to	your username. We accessing Padova network via the PD gate. While logged into the gate, issue the next command:

```
ssh -L 1234:localhost:1234 shoh@10.64.22.66
```

While logged inside the cluster, execute

```
jupyter notebook --no-browser --port=1234 --ip=127.0.0.1
```

The authentication token will be revealed as an	URL, copy and paste it in your browser. To shutdown the	kernal,	simply issue CTRL-C to the termimal.

That conclude the workspace preparation, ciao.