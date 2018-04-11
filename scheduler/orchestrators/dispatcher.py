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
from celery import task
import logging

from .dockercompose import DockerCompose
from .dcos import Dcos
from .openshift import OpenShift
from scheduler.settings import *


logger = logging.getLogger("SCHEDULER")


def _choice_orchestrator(orchestrator, url, token):
    orch = None
    if str.lower(orchestrator) not in ORCHESTRATORS:
        logger.error("Orchestrator not recognized")
    elif orchestrator == "OpenShift":
        orch = OpenShift(url, token)
    elif orchestrator == "DCOS":
        orch = Dcos(url, token)
    else:
        orch = DockerCompose(url)
    return orch


@task(name="orchestrator_extension_check")
def orchestrator_extension_check(url, token, extension, orchestrator=None):
    # Initialize Orchestrator
    orchestrator = orchestrator or ORCHESTRATOR
    orch = _choice_orchestrator(orchestrator, url, token)
    return orch.check_allowed_extensions(extension)


@task(name="parse_environment_variables")
def parse_environment_variables(url, token, template, orchestrator=None):
    # Initialize Orchestrator
    orchestrator = orchestrator or ORCHESTRATOR
    orch = _choice_orchestrator(orchestrator, url, token)
    model_parsed = orch.parse_environment_variables(template)
    return model_parsed
