# Data Engineering with Spark

The following lab utilizes Spark RDDs to perform basic text cleaning of unstructured text data.

## Lab Prerequisites

This lab utilizes a [Jupyter Docker Stacks](https://jupyter-docker-stacks.readthedocs.io/en/latest/index.html) image for experimenting with pyspark locally. These instructions assume docker is already [installed](https://docs.docker.com/get-started/get-docker/) and that some form of unix-like terminal (linux/mac or git bash/wsl on windows) is being used.

### Create a directory for notebooks

```bash
# example directory structure for the course
PROJECT_DIR=~/projects/courses/dataprocessing/notebooks
mkdir -p $PROJECT_DIR
```

**NOTE:** Students already using a different project directory structure do not have to create a new structure. Replace the PROJECT_DIR var in the previous command with the desired path.  

### Start the docker container and initialize a volume for persistance

```bash
# 2. Run Docker without root permission overrides
docker run --name pyspark_notebook --rm \
  --user root \
  -e NB_UID="$(id -u)" \
  -e NB_GID="$(id -g)" \
  -e CHOWN_EXTRA="/home/jovyan/work" \
  -e CHOWN_EXTRA_OPTS="-R" \
  -v "$PROJECT_DIR":/home/jovyan/work \
  --detach \
  -p 8888:8888 -p 4040:4040 -p 4041:4041 \
  quay.io/jupyter/pyspark-notebook
```

**NOTE:** All future runs of the container will use the same command but the notebook will only need to be copied on the first run.

### Copy the lab to the volume

```bash
cp lab_pyspark_jupyter_stand_alone/word_count_pyspark_jupyter_docker.ipynb  $PROJECT_DIR
```

### Obtain jupyterhub link and token

Find the jupyterhub link with token by using a docker command to search the logs. The link can be followed with a `ctrl+click`.

```bash
docker logs pyspark_notebook 2>&1 | grep "token="
#>[I 2026-09-08 16:37:04.898 ServerApp] http://localhost:8888/lab?token=53d1cd265f31f6d90550fa2f216cda13168948107af1c1f9
#>[I 2026-09-08 16:37:04.898 ServerApp]     http://127.0.0.1:8888/lab?token=53d1cd265f31f6d90550fa2f216cda13168948107af1c1f9
#>        http://localhost:8888/lab?token=53d1cd265f31f6d90550fa2f216cda13168948107af1c1f9
#>        http://127.0.0.1:8888/lab?token=53d1cd265f31f6d90550fa2f216cda13168948107af1c1f9
```

## Lab 1: Unstructured data analysis with RDDs

Analyze unstructured data (text) with RDDs and Spark Core Functions.

### Goals

- Get familiar with pyspark
- Get familiar with the most frequently used functions for RDD processing: `map`, `flatMap`, `reduceByKey`
- Learn how to define lambda functions
- Learn when you can use pure Python functionalities and constructs in Spark environment

### Lab resources

- [Notebook](./lab_pyspark_jupyter_docker/word_count.ipynb)
- The text file is obtained from [Project Gutenberg](https://www.gutenberg.org/ebooks/103.txt.utf-8) using the cell magic `!wget` in the ipynotebook.

### Useful links

- [RDD programming guide](https://spark.apache.org/docs/latest/rdd-programming-guide.html)
    - especially chapters `Transformations` and `Actions`

### TO DO

Go through the notebook and follow the instructions in the cells:

1. Open the book obtained from project guttenberg and:

- count the occurrence of each word
- change all capital letters to lower case
- remove stopwords
- sort the words and their counts in alphabetical order
- sort from most to least frequent word
- remove punctuations
- answer questions about code where applicable

2. Look at the given code and try to understand what it does.

- provide line by line code comments

3. Write a simple timing function for the exercise in part 1. Change the order of the chained operations to get different timings and try to find the optimal ordering.
4. Download the French version of the text from project guttenberg. Write a query to compare the word counts between the two versions.
