## Running Stable Diffusion LoRA tasks remotely on the shared GPUs

LoRA Runner should be started on the machine with GPUs,
and will provide APIs to execute training, fine-tuning and inference
tasks of Stable Diffusion models for other applications.


Given a remote LoRA Runner node, the users could run the supported applications
on the laptops, iPads and even mobile phones where powerful GPUs are not available.

### Build the docker images
The docker images are built using Dockerfiles which are all located under the ```build``` folder.
The building commands, however, should be executed under the root folder of the project.

#### The server container

The building process of the server container is divided into 2 parts for faster dev workflow.

1. Build the base image for the server:
   
```shell
$ docker build -t server_base:dev -f build/server_base.Dockerfile .
```

2. Build the server image:

```shell
$ docker build -t server:dev -f build/server.Dockerfile .
```


#### The worker container

The building process of the worker container is divided into 3 parts:

1. Build the base image for the worker:
   
```shell
$ docker build -t worker_base:dev -f build/worker_base.Dockerfile .
```

2. Build the base image for the runner:

```shell
$ docker build -t worker_runner_base:dev -f build/worker_runner_base.Dockerfile .
```

3. Build the worker image:

```shell
$ docker build -t worker:dev -f build/worker.Dockerfile .
```

### Start LoRA Runner using the docker images

Go to the ```build``` folder, the config files and data files are located
under ```data``` folder. Check the config files and edit them according to
your own need.

Then start all the related docker containers
using docker compose:

```shell
$ cd build
$ docker compose up -d
```

Docker compose will start 3 containers: the server, the worker, and a redis instance.
The server and worker containers are started using the images we just built before.
The redis container is started using the official image.

After successfully startup, the server container will expose port ```5025``` to accept inbound requests.