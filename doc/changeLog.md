# CHANGELOG

0.4.0

FEAT:
- Use DockerCompose to launch local experiments.

MAJOR:
- OpenShift and DockerCompose clients (binaries) in container PATH.
- Experiment definition: change templateNamespace for templateLocation.
- Network discovery: using curl to '/var/run/docker.sock' to retrieve and filter networks.
- Volume required to include model definitions inside the container.
- New base image (automodeling-base:0.2.1-3) with curl>7.40 and libdkafka versioned.

MINOR:
- REFACTOR: Strong isolation of components (Orchestrator, DDBB and Kafka) from Launcher.
Create orchestrator folder
- CREATE deploy folder with OpenShift and DockerCompose yml files.
- CREATE examples folder with model and project definitions.
'Fraud' (OpenShift only) and 'Neural networks' (OpenShift and DockerCompose) included.
- DELETE legacy tools and templates folder.

0.3.0

- DELETE all Rancher-based templates and examples.
- DELETE old-labeled files.
- DELETE current ```@app.errorhandler``` methods.
- Some refactor and error handling.
