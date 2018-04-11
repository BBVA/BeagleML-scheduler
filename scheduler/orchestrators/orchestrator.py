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
"""
Base class for orchestrators

Every orchestrator must extend Orchestarators class
"""


class Orchestrator:
    """
    Orchestrator interface
    Orchestrators are responsible for scheduling jobs that executes attacks

    :param url:      Orchestrator url
    :param token:    Orchestrator token
    """

    url = None  # must override
    token = None  # must override

    def __init__(self, url, token, **kwargs):
        self.url = url
        self.token = token

    def login(self):
        """
        Log into an orchestrator.
        This method should use the url and token to log in.
        """
        raise NotImplementedError("Orchestrators should implement this!")

    def start_service(self, service_name, parameters, model_template):
        """
        Start a single service.
        This method should use the config to schedule jobs based on the
        configuration for the planner

        :param service_name:    name of the service
        :param planner_config:    configuration related to the scheduler
        :param attack_config:   configuration related to the attack
        """
        raise NotImplementedError("Orchestrators should implement this!")

    def remove_service(self, service_name):
        """
        Remove a single service the jobs.
        This method should use the config to schedule jobs based on the
        configuration for the planner

        :param service_name:    name of the service
        """
        raise NotImplementedError("Orchestrators should implement this!")

    def check_allowed_extensions(self, extension) -> str:
        """
        Check if the orchestrator works with the specified model_template extension.

        :param extension:    extension of the model template
        """
        raise NotImplementedError("Orchestrators should implement this!")
