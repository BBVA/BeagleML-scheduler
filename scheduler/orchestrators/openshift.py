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
import requests
import logging

from .orchestrator import Orchestrator


class OpenShift(Orchestrator):

    def __init__(self, orchestrator_url, orchestrator_token):
        self.url = orchestrator_url
        self.token = orchestrator_token
        self.client = 'oc'
        self.namespace = 'beagleml'
        self.logger = logging.getLogger("SCHEDULER")

    def login(self):
        proc = subprocess.Popen(
            [self.client + ' login ' + ' --token=' + self.token],
            stdout=subprocess.PIPE, shell=True)
        self.logger.info('Trying to login to oc')
        (out, err) = proc.communicate()
        if err:
            self.logger.error('Login failed')
            self.logger.error(out.decode('utf-8'))
        else:
            self.logger.info(out.decode('utf-8'))

    def start_service(self, service_name, service_parameters, service_template):
        """
        Launch one service or rc from one file.

        The "parameters" is a list of dictionaries with two fields,
        name and value.
        """
        self.logger.info("Experiment parameters:")
        self.logger.info(service_parameters)

        label = ' -l ' + self.namespace + '=' + service_name
        parameters_str = ' '
        for param in service_parameters:
            parameters_str = (
                parameters_str + '-p ' + param['name'] + '='
                + param['value'] + ' ')

        proc = subprocess.Popen(
            [self.client + ' new-app ' + "helloWorld" + parameters_str + label],
            stdout=subprocess.PIPE, shell=True)
        # service_template

        (out, err) = proc.communicate()
        if err:
            self.logger.error(
                'Failed to launch service ' + service_name
                + ' with template ' + service_template)
            self.logger.error(out.decode('utf-8'))
            return "error"
        else:
            self.logger.info(out.decode('utf-8'))
            return "success"

    def remove_service(self, service_name):
        """Deletes name-given namespace and its content."""
        label = ' -l ' + self.namespace + '=' + service_name
        proc1 = subprocess.Popen(
            [self.client + ' delete all ' + label],
            stdout=subprocess.PIPE, shell=True)
        (out, err) = proc1.communicate()
        if err:
            self.logger.error(
                'Failed to delete ' + service_name)
            self.logger.error(out.decode('utf-8'))
            return "error"
        else:
            self.logger.info(out.decode('utf-8'))
            return "success"

    # TODO change this method for the equivalent parse_environment_variables. See other orchestrators.
    def retrieve_remote_template(self, template_name, template_namespace):
        """
        Retrieves remote template from Openshift catalog.
        Return: JSON object
        """
        headers = {'Authorization': 'Bearer ' + self.token}
        url_template = (self.url + '/oapi/v1/namespaces/'
                        + template_namespace + '/templates/' + template_name)
        cert = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'

        try:
            r = requests.get(url_template, headers=headers, verify=cert)
        except requests.exceptions.RequestException as e:
            self.logger.error(e)
            raise

        self.logger.info('Json Object obtained for default_parameters')
        return r.json()

    def check_allowed_extensions(self, extension):
        """ """
        return '' if extension in ('yaml', 'yml') else "Error: Openshift doesn't allow "+extension+" files."


if __name__ == "__main__":
    import sys
    import time

    orchestrator = 'OpenShift'
    url = 'https://osos-master-0.osos.com:8443'
    token = sys.argv[1]

    orch = OpenShift(url, token)
    template = 'ml-ex-nn-tf'
    location = 'openshift'

    parameters = [
        {'name': 'NAME', 'value': 'test1'},
        {'name': 'HIDDEN_SIZE', 'value': '50'}
    ]
    name = 'pruebaPablo'

    orch.login()
    print(orch.retrieve_remote_template(template, location))
    orch.start_service(name, parameters, template)
    time.sleep(5)
    orch.remove_service(name)
