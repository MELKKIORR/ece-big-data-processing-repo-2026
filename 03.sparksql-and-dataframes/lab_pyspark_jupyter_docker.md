# Data Engineering with Spark

The following lab demonstrates using Spark DataFrames and SparkSQL to perform some basic data engineering and analysis.  

## Lab Prerequisites

This lab utilizes a [Jupyter Docker Stacks](https://jupyter-docker-stacks.readthedocs.io/en/latest/index.html) image for experimenting with pyspark locally. These instructions assume docker is already [installed](https://docs.docker.com/get-started/get-docker/) and that some form of unix-like terminal (linux/mac or git bash/wsl on windows) is being used.

### Start the docker container and initialize a volume for persistance

```bash
docker run --name pyspark_notebook --rm -v pyspark_notebook_volume:/home/jovyan/work --detach -p 8888:8888 -p 4040:4040 -p 4041:4041 quay.io/jupyter/pyspark-notebook
```

**NOTE:** All future runs of the container will use the same command but the notebook will only need to be copied on the first run.

### Copy the lab to the volume

The following command copies the lab resource into the container.  
**NOTE:** The command file order is reversed and file name changed as needed to copy the file from the container to the local host.  

```bash
docker cp lab_pyspark_jupyter_docker/lab_sparksql_and_dataframes.ipynb \ pyspark_notebook:/home/jovyan/work/
```

### Log into JupyterHub

The following Docker command is run to obtain the link to JupyterHub with the correct login credentials. 

```bash
docker logs pyspark_notebook
```

## Lab 2: Structured data analysis with DataFrames and SparkSQL

### Goals

- Get familiar with the most frequently used functions for dataframe processing such as `filter`, `select`, `groupby`, etc...
- Learn when and how to use the functions from the module `pyspark.sql.functions
- Learn how to enrich the data through `joins`

### Lab resources

- Notebook
- The datasets will be loaded into the environment from [nyc.gov TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

### Useful links

- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/index.html)
- [Pyspark SQL Module doc](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql.html)

### TO DO

Go through the notebook and explore the dataset using the questions provided. By the end of the lab you should have gained a better understanding of commuting by taxi in nyc.
