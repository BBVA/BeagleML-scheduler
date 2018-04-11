# BeagleML Scheduler


As part of BeagleML, the scheduler monitors the experiments queue, and launches experiments to the specified orchestrator.
It controls the number of running experiments, taking care of not exceeding the maximum number of running experiments threshold.

## How it works

First of all, someone must provide to the scheduler the 2 required files that describe the project to be executed.

It involves one heuristic and one orchestrator (see below).
The heuristic processes both files and sends experiments to the queue.

Actually, the scheduler has two queues: one for running experiments and other for queued experiments.
Launch an experiment means moving the experiment from queue to running queues, change its state to ```running``` from ```queued```,
and order its execution to the specified orchestrator.

Once the scheduler launches an experiment, it monitors the experiment state by checking:
* *Experiment timeout* : If the experiment exceed the timeout, the scheduler marks it as ````timeout```` in BBDD and stops it.
* *Experiment accuracy* : If the experiment exceed the *max_accuracy threshold*, the scheduler marks it as ```accuracy_limit_reached``` and stops it.

(Experiment states are defined in the [experiment_state section](doc/experiment_states.md)).

##### Networking: how containers see each other.

Read the [network section](doc/network.md).

## Components

#### API

Endpoints exposed to beagleml-front, that handles user-interaction with beagleml: upload files, start/stop/reset system,...

Endpoints are detailed in the [API documentation](doc/api.md).

#### Orchestrators

Module to launch experiments locally or to remote platforms.
There are integrations with DCOS, Openshift (both remote), and Docker-Compose (local).

#### Heuristics

A heuristic defines which experiments will be sent to queue, and what to do with experiments results.

For instance:
* Grid heuristic: Generates combination of experiments and send all of them to the queue. It does nothing special with these results.
* Reinforcement Learning heuristic: Decide which experiment goes first. With the result, it decides the next one and so one...

Anyone can create their own heuristic.
Some info is explained in the [heuristics documentation](doc/heuristics.md).


## Testing

BeagleML has unit and integration tests.
To know more, read the [tests section](doc/tests.md).

