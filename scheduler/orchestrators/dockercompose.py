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
import subprocess
import json
import yaml
import logging
from celery import Celery

from .orchestrator import Orchestrator

app = Celery('scheduler')
app.config_from_object('scheduler.settings')


class DockerCompose(Orchestrator):
    """Class to interact with Docker Compose."""

    def __init__(self, host):
        self.host = host
        self.client = 'docker-compose'
        self.logger = logging.getLogger("SCHEDULER")
        self.working_dir = '/tmp'
        self.models_dir = '/tmp/models'
        self.network = self.retrieve_network('beagleml') #automodeling

    def login(self):
        self.logger.info('Login not needed for Docker Compose.')

    def retrieve_network(self, regexp):
        """
        Gets automodeling network name, which is needed to launch containers and
        communicate among them.
        'regexp' is the name of the network defined in automodeling docker-compose.yml,
        in which all automodeling containers are launched.
        Ex: regexp=automodeling --> network_name=<path_>automodeling
        """
        proc = subprocess.Popen(
            ['curl -sS --unix-socket /var/run/docker.sock "http:/v1.24/networks" '],
            stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        # convert output (bytes) to string and then to list of jsons
        tostring = out.decode("utf-8")
        tolist = json.loads(tostring)

        network_name = "network_not_found_using_regexp="+regexp
        for network in tolist:
            if regexp in network['Name']:
                network_name = network['Name']

        self.logger.info('Network used: ' + network_name)
        return network_name

    def start_service(self, service_name, service_parameters, service_template):
        """
        Launch services from docker-compose definition.
        """
        self.logger.info('Start service for Docker Compose')
        print(service_parameters)
        print(" ")
        print(service_template)
        model_template_copy = dict(service_template)
        folder_path, err = self.create_experiment_folder(service_name)
        file_path, err = self.create_temp_file(folder_path, service_parameters, model_template_copy)

        proc = subprocess.Popen(
            [self.client + ' -f ' + file_path + ' up -d'],
            stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        error_message = 'Failed to launch service ' + service_name + ' with template ' + service_template['filename']
        return self.check_error(out, err, error_message)

    def create_experiment_folder(self, name):
        """
        Creates a folder in disk for a particular experiment.
        """
        folder_path = self.working_dir + '/' + name
        self.logger.debug('Creating experiment folder in ' + folder_path)
        proc = subprocess.Popen(['mkdir -p ' + folder_path],
            stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        error_message = 'Failed to create folder ' + folder_path
        return folder_path, self.check_error(out, err, error_message)

    def create_temp_file(self, folder_path, service_parameters, model_template):
        """
        Each experiment has its own docker-compose.yml file stored in disk
        with its particular parameters and general network.
        """
        file_path = folder_path + '/docker-compose.yml'
        self.logger.debug('Creating temporal file in ' + file_path)

        # Substitute parameters into model template
        services = model_template.get('services')
        for service in services:
            env_vars = services.get(service)['environment']
            for param in service_parameters:
                if param['name'] in env_vars.keys():
                    env_vars[param['name']] = param['value']

        # Add automodeling network to each experiment template to launch.
        model_template['networks'] = self.generate_docker_compose_network_structure()
        # Remove model's DDBB extra information. Useless for creating experiment file.
        model_template.pop('_id')
        model_template.pop('filename')
        model_template.pop('create_time')
        # Save modified experiment template to disk.
        with open(file_path, 'w') as yaml_file:
            yaml.dump(model_template, yaml_file, default_flow_style=False)

        return file_path, "success"

    def generate_docker_compose_network_structure(self):
        """
        # From https://docs.docker.com/compose/networking/#using-a-pre-existing-network
        # Expected output:
        # networks:
        #   default:
        #     external:
        #       name: my-pre-existing-network
        """
        network = dict()
        network['name'] = self.network
        external = dict()
        external['external'] = network
        default = dict()
        default['default'] = external
        return default

    def remove_service(self, service_name):
        """
        Once the experiment has finished, it is mandatory to stop its containers.
        Moreover, its docker-compose.yml file stored in disk is not neccesary anymore.
        """
        self.logger.info('Remove service for Docker Compose')
        folder_path = self.working_dir + '/' + service_name
        file_path = folder_path + '/docker-compose.yml'
        proc = subprocess.Popen(
            [self.client + ' -f ' + file_path + ' down '],
            stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()

        # TODO check errors
        err2 = self.remove_experiment_folder(folder_path)

        error_message = 'Failed to delete ' + service_name
        return self.check_error(out, err, error_message)

    def remove_experiment_folder(self, path):
        """
        Removes a path from disk recursively.
        """
        self.logger.debug('Removing experiment folder in '+ path)
        proc = subprocess.Popen(['rm -r ' + path],
            stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        error_message = 'Failed to remove folder ' + path
        return self.check_error(out, err, error_message)

    def check_error(self, out, err, error_message):
        if err:
            self.logger.error(error_message)
            if out:
                self.logger.error(out.decode('utf-8'))
            return "error"
        else:
            if out:
                self.logger.info(out.decode('utf-8'))
            return "success"

    def parse_environment_variables(self, template: object) -> object:
        """
        DockerCompose definition is not similar to Openshift definition.

        This function gets environment variables from each DockerCompose service,
        and stores them into a dictionary within "parameters" key.
        """
        self.logger.debug(template)
        services = template.get('services')
        template_parsed = dict()
        for service_name, service_info in services.items():
            try:
                environment_variables = services[service_name].get('environment')
                self.logger.info(environment_variables)
            except KeyError:
                self.logger.warning('Remote template: service '
                                    + service_name + ' does not contain environment section.')
                continue

            service_parsed = dict()
            service_parsed['parameters'] = []
            for item in environment_variables.items():
                env_var = dict()
                env_var['name'] = item[0]
                env_var['value'] = item[1]
                service_parsed['parameters'].append(env_var)

            self.logger.debug(service_parsed)
            self.logger.info('Model template: service %s parsed.', service_name)
            template_parsed[service_name] = service_parsed

        self.logger.info('Model template parsed!')
        return template_parsed

    def check_allowed_extensions(self, extension):
        """ """
        return '' if extension in ('yaml', 'yml') else "Error: Docker Compose doesn't execute " + extension + " files."


if __name__ == "__main__":
    import time
    orch = DockerCompose('localhost')
    template = 'dockercompose_model_template_neural-networks.yml'
    location = '../../../examples'

    parameters = [
        {'name': 'LEARNING_RATE', 'value': '0.02'},
        {'name': 'KAFKA_SERVICE', 'value': 'localhost'}
    ]
    name = 'testOrchestratorDockerCompose'

    orch.login()
    orch.start_service(name, parameters, template)
    time.sleep(10)
    orch.remove_service(name)
