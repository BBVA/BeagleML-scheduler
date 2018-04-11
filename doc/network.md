# Network

The scheduler, when launched using Docker-Compose, needs to know in which ```network```
has been deployed, to force experiments' containers to be plugged into the same network.
Moreover, these containers need to communicate with Kafka, Mongo, or other dependencies.

To retrieve the network used, it is needed to launch the scheduler with the following option in docker-compose.yml:
```
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```
to retrieve all networks information by doing (in code):
```
curl -sS --unix-socket /var/run/docker.sock "http:/v1.24/networks"
```
and filter the correct network based on a network name (ej: 'beagleml').

At the beginning of the scheduler's log, the network retrieved is shown:
```
...
SCHEDULER.DOCKERCOMPOSE 2017-09-05 15:20:47,035 INFO - Network used: deploy_beagleml
...
```
