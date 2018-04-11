# Unit tests

```
python -m pytest
```

# Integration tests

## Orchestrators

### Docker-compose

We assume having Docker Compose installed locally. If not, check [docker-compose install guide](https://docs.docker.com/compose/install/).

First, launch scheduler dependencies:
```
$ cd deploy
$ docker-compose up -d up -d rabbitmq mongo kafka
```

Finally, execute tests:
```
python -m pytest -m integration -m dockercompose --capture=no
```



### DCOS

First, launch DCOS containers:
```
$ cd tests/integration/orchestrators/dcos
$ docker-compose up -d
## wait for DCOS to boot ##
## access localhost:8080 in your browser to see Marathon UI
```

Then, launch scheduler dependencies:
```
$ cd deploy
$ docker-compose up -d up -d rabbitmq mongo kafka
```

And finally, execute tests:
```
python -m pytest -m integration -m dcos --capture=no
```

### OpenShift
We assume having MiniShift installed locally. If not, check [minishift install guide](https://docs.openshift.org/latest/minishift/getting-started/installing.html).
Currently tested under:
```
docker-machine-driver-xhyve 0.3.3
minishift v1.14.0+1ec5877
OpenShift version 'v3.7.1'
```

First, start minishift:
```
$ minishift start
# Check UI in https://<generated_IP>:8443
```

Then, get credentials from UI and paste it into tests code.

Finally, execute tests:
```
python -m pytest -m integration -m openshift --capture=no
```
