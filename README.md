# Mini_Rag

This is a minimal implementation of the RAG model for question answering.

## Requirments

Python 3.8 or later

### install Python using miniconda

1. Download and install MiniConda
2. Create a new environment using the following command:

```bash
$ conda create -n mini-rag python=3.11
```

(Optional) Setup you command line interface for better readability

```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```

3. activate enviroment

```bash
$ conda activate mini-rag
```

## Installation

### install Requirements

```bash
$ pip install requirements.txt
```

### set up enviroment variables

```bash
$ cp .env.example .env
```

set your own env variables

## Run Docker Compose Service

```bash
$ cd docker
$ cp .env.example .env
```

### update .env with your credentials

```bash
$ cd docker
$ sudo docker compose up-d
```

## To Run App

```bash
$ uvicorn main:app --reload --host 0.0.0.0 --port 5000
```
