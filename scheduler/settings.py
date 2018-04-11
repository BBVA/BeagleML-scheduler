"""
Copyright 2018 Banco Bilbao Vizcaya Argentaria, S.A.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
import logging

# LOGGING CONFIGURATION
logging.basicConfig(level=logging.DEBUG,
                    datefmt='%d-%m-%Y:%H:%M:%S',
                    format='[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s')

# GLOBAL VARIABLES
ALLOWED_EXTENSIONS = set(['txt', 'yaml', 'yml', 'json'])
EXPERIMENT_STATES = ['queue', 'pool', 'completed', "timeout", "accuracy_limit_reached", 'stopped', 'failed']
ORCHESTRATORS = (str.lower("OpenShift"), str.lower("DockerCompose"), str.lower("DCOS"))


# ENVIRONMENT VARIABLES
ORCHESTRATOR = os.environ.get("ORCHESTRATOR")
ORCHESTRATOR_TOKEN = os.environ.get("ORCHESTRATOR_TOKEN")
ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL")
MONGODB_URL = os.environ.get("MONGODB_URL")
MONGODB_PORT = os.environ.get("MONGODB_PORT")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE")
MONGODB_USER = os.environ.get("MONGODB_USER")
MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD")
KAFKA_SERVER = os.environ.get("KAFKA_SERVERS")
CELERY_AMQP_BROKER = os.environ.get("CELERY_AMQP_BROKER")

# CELERY
broker_url = "amqp://"+CELERY_AMQP_BROKER
result_backend = 'rpc://'
