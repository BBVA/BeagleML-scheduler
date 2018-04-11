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
import itertools
import datetime
from bson.objectid import ObjectId

from celery import task

from ...heuristics.heuristic import Heuristic
from scheduler.system.dbConnection import DBConnector

from .parameter_generator import *
from scheduler.settings import *


class GridSearch(Heuristic):

    def __init__(self, project_id, model_id, **kwargs):
        self.db = kwargs.get("db")
        self.logger = logging.getLogger("SCHEDULER")
        self.project_id = project_id
        self.model_id = model_id

        self.experiments = list()
        self.project = dict()
        self.model = dict()

        super(GridSearch, self).get_project_definition()
        self.check_heuristic_syntax()
        super(GridSearch, self).get_model_template()

    def check_heuristic_syntax(self):
        """
        Check the heuristic section of the project definition.
        :return: boolean
        """
        pass

    def generate_experiments(self):
        """
        Given a project definition and a model template, it gets "user defined params" and
        "default params" (from both files respectively), and fills the list of experiments.
        """
        # First, merge model template params + project definition params.
        param_names, param_type_values = get_parameters_from_project_definition(self.project['parameters'])

        param_names, param_type_values = get_parameters_from_model_template(
            param_names, param_type_values, self.model)

        # Then, generate combinations.
        cont = 1
        for param in itertools.product(*param_type_values):
            # NOTE: Los nombres de los paramentros deben ser exactamente
            #          los mismos que en los ficheros.
            # NOTE: El name no admite mayusculas
            name = ''.join([self.project['name'], 'model{num}'.format(num=cont)])

            experiment = dict()
            experiment['name'] = name
            experiment['project_name'] = self.project['name']
            experiment['project_id'] = ObjectId(self.project_id)
            experiment['time_out'] = self.project["time_out"]
            experiment['accuracy_limit'] = self.project["accuracy_limit"]
            experiment['parameters'] = []
            for index in range(len(param_names)):
                parameter = dict()
                parameter['name'] = param_names[index]
                # NOTE: Hardcoded for name as parameter
                if param_names[index] == 'NAME':
                    parameter['value'] = name
                elif param_names[index] == 'ROOT_TOPIC':
                    parameter['value'] = name
                else:
                    parameter['value'] = str(param[index])

                experiment['parameters'].append(parameter)

            experiment['create_time'] = datetime.datetime.utcnow()
            experiment['template_name'] = self.project['template']

            self.logger.debug(experiment)
            self.experiments.append(experiment)
            cont += 1

    def evaluate(self):
        pass

    def run(self):
        """
        Generate experiments one-time and send all of them to the queue.
        No need to evaluate results, or take other complex actions.
        """
        self.generate_experiments()
        super(GridSearch, self).send_experiments_to_queue(self.experiments)


@task(name="grid_search")
def start(project_id, model_id):
    db = DBConnector(MONGODB_URL, MONGODB_PORT,
                     MONGODB_DATABASE, MONGODB_USER,
                     MONGODB_PASSWORD)
    heuristic = GridSearch(project_id, model_id, db=db)
    heuristic.run()


