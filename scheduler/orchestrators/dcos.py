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
"""Module for manage the connection with DCOS."""
import requests
import logging

from .orchestrator import Orchestrator


class Dcos(Orchestrator):
    """Class to interact with DCOS."""

    def __init__(self, orchestrator_url, orchestrator_token, **kwargs):
        self.url = orchestrator_url
        self.token = orchestrator_token

        self.marathon_url = kwargs.get("marathon_url", "http://default.marathon.url:8080")
        self.app_group = '/automodeling/'
        self.logger = logging.getLogger("SCHEDULER")

    def login(self):
        self.logger.info('Login not needed for DCOS.')

    def start_service(self, name, parameters, model_template):
        self.logger.info('Starting service ' + name + ' in group ' + self.app_group + " in DCOS.")

        model_template_copy = dict(model_template)

        service_dict = self.create_json(parameters, model_template_copy)
        service_dict['id'] = self.app_group+name
        self.logger.debug(service_dict)

        url = self.marathon_url+'/v2/apps'
        try:
            r = requests.post(url, json=service_dict)
            self.logger.info("Start operation status code: ", r.status_code)
        except requests.exceptions.RequestException as e:
            self.logger.error(e)

        return r.status_code in (200, 201)

    def create_json(self, parameters, model_template):
        """
        Each experiment has its own JSON file stored in ¿disk?
        with its particular parameters and general network.
        Return: JSON object
        """
        # Substitute parameter into template definition
        try:
            env_vars = model_template.get('env')
            for param in parameters:
                if param['name'] in env_vars.keys() :
                    env_vars[param['name']] = param['value']
        except Exception as error:
            self.logger.error(error)
        # Remove model's DDBB extra information. Useless for creating experiment file.
        model_template.pop('_id')
        model_template.pop('filename')

        return model_template

    def remove_service(self, name):
        """Deletes name-given service."""
        self.logger.info('Removing service ' + name + ' from group ' + self.app_group)
        url = self.marathon_url+'/v2/apps/'+self.app_group+name
        try:
            r = requests.delete(url)
            self.logger.info("Remove operation status code: ", r.status_code)
        except requests.exceptions.RequestException as e:
            self.logger.error(e)

        return r.status_code == 200

    def parse_environment_variables(self, template: object) -> object:
        """
        DCOS definition is not similar to other orchestrators definitions.

        This function gets environment variables from each DCOS service,
        and stores them into a dictionary within "parameters" key.
        """
        self.logger.debug(template)

        service_name = template.get('id')
        try:
            environment_variables = template.get('env')
        except KeyError:
            self.logger.warning('Remote template: service ' + service_name + ' does not contain environment section.')

        service_parsed = dict()
        service_parsed['parameters'] = []
        for item in environment_variables.items():
            env_var = dict()
            env_var['name'] = item[0]
            env_var['value'] = item[1]
            service_parsed['parameters'].append(env_var)

        self.logger.debug(service_parsed)
        self.logger.info('Model template: service %s parsed.', service_name)
        template_parsed = dict()
        template_parsed[service_name] = service_parsed

        self.logger.info('Model template parsed.')
        return template_parsed

    def check_allowed_extensions(self, extension):
        """ """
        return '' if extension in ('json') else "Error: DCOS doesn't allow "+extension+" files."


if __name__ == "__main__":
    import time

    orchestrator = 'DCOS'
    url = 'https://osos-master-0.osos.com:8443'
    token = "no_token"
    orch = Dcos(url, token)

    template = 'dcos_model_template_neural-networks.json'
    template_path = './'

    parameters = [
        {'name': 'NAME', 'value': 'test1'},
        {'name': 'HIDDEN_SIZE', 'value': '50'}
    ]
    name = 'test_service'

    orch.login()
    orch.start_service(name, parameters, template)
    time.sleep(5)
    orch.remove_service(name)
