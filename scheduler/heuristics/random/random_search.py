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
import datetime
import random
import time
from bson.objectid import ObjectId
from celery import task

from ...heuristics.heuristic import Heuristic
from scheduler.system.dbConnection import DBConnector

from scheduler.settings import *


class RandomSearch(Heuristic):
    def __init__(self, project_id, model_id, total_n_experiments, **kwargs):
        self.db = kwargs.get("db")
        self.logger = logging.getLogger("SCHEDULER")
        self.project_id = project_id
        self.model_id = model_id

        self.total_n_experiments = total_n_experiments
        self.experiments_counter = 0

        self.project = dict()
        self.model = dict()
        self.running_experiments = list()

        super(RandomSearch, self).get_project_definition()
        super(RandomSearch, self).get_model_template()

    def run(self):
        """
        Launch the full heuristic search process.
        :return: void
        """
        self.logger.info('Starting Random Search Heuristic...')
        self.check_heuristic_syntax()
        self.init_queue()

        while self.experiments_counter < self.total_n_experiments:
            time.sleep(3)
            self.evaluate()

    def init_queue(self):
        """
        Initialize the queue following the heuristic rules.
        :return: list
        """
        self.logger.info('Generating Initial Experiment...')
        self.generate_experiments()

    def evaluate(self):
        """
        Manage the heuristic process until the search is finished.
        :return: void
        """
        for experiment_id in self.running_experiments:
            status_completed = self.check_completed(experiment_id)

            if status_completed:
                self.generate_experiments()

    def generate_experiments(self):
        """
        Generate new experiments to be sent to the queue and executed.
        :return: list
        """
        experiments_to_queue = list()

        # Generate Experiments
        name = ''.join([self.project['name'], 'model{num}'.format(num=self.experiments_counter)])

        experiment = dict()
        experiment['name'] = name
        experiment['project_name'] = self.project['name']
        experiment['project_id'] = ObjectId(self.project_id)
        experiment['parameters'] = []
        experiment['create_time'] = datetime.datetime.utcnow()
        experiment['template_name'] = self.project['template']
        experiment['time_out'] = self.project["time_out"]
        experiment['accuracy_limit'] = self.project["accuracy_limit"]

        for param in self.project['parameters']:

            parameter = dict()

            if param['type'] == 'lineal':

                parameter['name'] = param['name']
                parameter['value'] = random.uniform(param['value']['initial_value'],
                                                    param['value']['final_value'])

            elif param['type'] == 'absolute':

                parameter['name'] = param['name']
                parameter['value'] = random.choice(param['value'])

            else:
                raise Exception("Parameter type not accepted")

            experiment['parameters'].append(parameter)
        experiments_to_queue.append(experiment)

        # Send to the queue
        experiment_ids = super(RandomSearch, self).send_experiments_to_queue(experiments_to_queue)

        # Append to running experiments
        self.running_experiments = self.running_experiments + experiment_ids

        # Increase the counter
        self.experiments_counter += 1

    def check_heuristic_syntax(self):
        """
        Check the heuristic section of the project definition.
        :return: boolean
        """
        self.logger.info('Checking project syntax definition...')
        for param in self.project['parameters']:
            if param['type'] == 'lineal':
                pass
            elif param['type'] == 'absolute':
                pass
            elif param['type'] == 'layers':
                raise Exception("Layers parameter still not implemented")
            else:
                raise Exception("Parameter type not accepted")

    def check_completed(self, experiment_id):
        """
        Check the status of the running experiments
        :return: boolean
        """
        # Check status
        state = str(self.db.get_document({'_id': ObjectId(experiment_id)}, "experiments")['state'])
        experiment_completed = \
            state == 'completed' \
            or state == 'accuracy_limit_reached' \
            or state == 'timeout'

        # If it is completed, delete from experiment list
        if experiment_completed:
            self.running_experiments.remove(experiment_id)

        # return true if it is completed
        return experiment_completed


@task(name="random_search")
def start(project_id, model_id, total_n_experiments):
    db = DBConnector(MONGODB_URL, MONGODB_PORT,
                     MONGODB_DATABASE, MONGODB_USER,
                     MONGODB_PASSWORD)
    heuristic = RandomSearch(project_id, model_id, total_n_experiments, db=db)
    heuristic.run()
