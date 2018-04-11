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
import logging

from scheduler.system.system import System
from scheduler.orchestrators.openshift import OpenShift
from scheduler.orchestrators.dcos import Dcos
from scheduler.orchestrators.dockercompose import DockerCompose
from scheduler.common import common_init

# logging.basicConfig()
logger = logging.getLogger("SCHEDULER")


def main():

    config = common_init()

    # Initialize Orchestrator
    orchestrator = config["ORCHESTRATOR"]
    if str.lower(orchestrator) not in config["ORCHESTRATORS"]:
        logger.error("Orchestrator not recognized")
    elif orchestrator == "OpenShift":
        orch = OpenShift(config["ORCHESTRATOR_URL"], config["ORCHESTRATOR_TOKEN"])
    elif orchestrator == "DCOS":
        orch = Dcos(config["ORCHESTRATOR_URL"], config["ORCHESTRATOR_TOKEN"])
    else:
        orch = DockerCompose(config["ORCHESTRATOR_URL"])

    orch.login()
    config['ORCH'] = orch

    # Initialize System core process.
    system = System(orchestrator=orch, db=config["DB"],
                    kafka_server=config["KAFKA_SERVER"])

    config['SYSTEM'] = system

    system.start()
#    system.join()


if __name__ == '__main__':
    main()
